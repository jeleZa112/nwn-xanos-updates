"""BG Voice RU: fail-closed staging primitives. Not a launcher and never writes to the game.

Safe to import; contains no model loading, shell, GPU, network, or game operations.
Any integration must preserve Movie Core 1.11's HOLD_LITERARY_TEXT_FIRST gate.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Mapping
import io
import json
import os
import re
import shutil
import tempfile
import time
import wave
import zipfile


class SafetyHold(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    h = sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _safe_relname(name: str) -> str:
    """Reject traversal, Windows device aliases and alternate data streams."""
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise SafetyHold('UNSAFE_NAME')
    p = PurePosixPath(name)
    if p.is_absolute():
        raise SafetyHold('PATH_TRAVERSAL_HOLD')
    for component in name.split('/'):
        if (not component or component in ('.', '..') or ':' in component or
            component[-1:] in (' ', '.') or any(ord(ch) < 32 for ch in component)):
            raise SafetyHold('UNSAFE_NAME')
        stem = component.split('.')[0].upper()
        if stem in {'CON','PRN','AUX','NUL','COM1','COM2','COM3','COM4',
                    'COM5','COM6','COM7','COM8','COM9','LPT1','LPT2',
                    'LPT3','LPT4','LPT5','LPT6','LPT7','LPT8','LPT9'}:
            raise SafetyHold('WINDOWS_RESERVED_NAME')
    return name


def verify_model_bundle(root: str | Path, specs: Mapping[str, Mapping], *, strict_inventory: bool = False) -> dict:
    """Verify *all* declared model assets before loading a model.

    specs: {'config.json': {'sha256': '...', 'bytes': N}, ...}
    Model output remains HOLD when even one listed asset is missing or changed.
    Caller must enumerate *all* assets needed by the pinned model fork.
    """
    folder = Path(root)
    if folder.is_symlink() or not folder.is_dir():
        raise SafetyHold('MODEL_ROOT_INVALID')
    if not specs or not isinstance(specs, Mapping):
        raise SafetyHold('EMPTY_MODEL_BUNDLE_MANIFEST')
    if strict_inventory:
        listed = set(specs)
        actual = set()
        for item in folder.rglob('*'):
            if item.is_symlink():
                raise SafetyHold('UNPINNED_MODEL_SYMLINK_HOLD')
            if item.is_file():
                rel = item.relative_to(folder).as_posix()
                _safe_relname(rel)
                actual.add(rel)
            elif not item.is_dir():
                raise SafetyHold('MODEL_SPECIAL_FILE_HOLD')
        if actual != listed:
            raise SafetyHold('MODEL_INVENTORY_NOT_EXACTLY_PINNED_HOLD')
    verified = {}
    for name, meta in specs.items():
        _safe_relname(name)
        target = folder.joinpath(*name.split('/'))
        if not isinstance(meta, Mapping):
            raise SafetyHold('MODEL_META_INVALID')
        digest = str(meta.get('sha256', '')).lower()
        expected_bytes = meta.get('bytes')
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise SafetyHold('MODEL_SHA_NOT_PINNED:' + name)
        if not isinstance(expected_bytes, int) or expected_bytes < 1:
            raise SafetyHold('MODEL_SIZE_NOT_PINNED:' + name)
        # Resolve only after rejecting symlinks in every component.
        current = folder
        for part in name.split('/'):
            current = current / part
            if current.is_symlink():
                raise SafetyHold('MODEL_SYMLINK_FORBIDDEN:' + name)
        if not target.is_file() or target.stat().st_size != expected_bytes:
            raise SafetyHold('MODEL_ABSENT_OR_SIZE_MISMATCH:' + name)
        actual = file_sha256(target)
        if actual != digest:
            raise SafetyHold('MODEL_SHA_MISMATCH:' + name)
        verified[name] = {'sha256': actual, 'bytes': expected_bytes}
    return {'status': 'BUNDLE_INTEGRITY_PASS_NOT_MODEL_SAFETY_CERTIFICATION', 'files': verified}


def verify_signed_manifest(raw: bytes, signature: bytes, trusted_pubkey_hex: str,
                           current_version: str | None = None) -> dict:
    """Verify Ed25519 signature and strict schema, including under python -O.

    WARNING: this is NOT active in the user's live updater. Real project
    signing public key has not been provisioned independently.
    """
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= 65536 or
        not isinstance(signature, bytes) or len(signature) != 64 or
        not isinstance(trusted_pubkey_hex, str) or
        re.fullmatch(r'[0-9a-fA-F]{64}', trusted_pubkey_hex) is None):
        raise SafetyHold('RELEASE_SIGNATURE_OR_TRUST_KEY_MISSING')
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(trusted_pubkey_hex))
        key.verify(signature, raw)
    except Exception as exc:
        raise SafetyHold('RELEASE_SIGNATURE_INVALID_OR_CRYPTO_UNAVAILABLE') from exc
    try:
        obj = json.loads(raw)
        if not isinstance(obj, dict) or obj.get('project') != 'BG_VOICE_RU':
            raise SafetyHold('RELEASE_MANIFEST_SCHEMA_INVALID')
        version = obj.get('version', '')
        commit = obj.get('commit', '')
        digest = obj.get('sha256', '')
        if (not isinstance(version, str) or
            re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)', version) is None or
            not isinstance(commit, str) or re.fullmatch(r'[0-9a-f]{40}', commit) is None or
            not isinstance(digest, str) or re.fullmatch(r'[0-9a-f]{64}', digest) is None or
            obj.get('path','BG_VOICE_CORE.py') != 'BG_VOICE_CORE.py'):
            raise SafetyHold('RELEASE_MANIFEST_SCHEMA_INVALID')
        if current_version:
            if not isinstance(current_version, str) or re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', current_version) is None:
                raise SafetyHold('INVALID_CURRENT_RELEASE_VERSION')
            if tuple(map(int,version.split('.'))) <= tuple(map(int,current_version.split('.'))):
                raise SafetyHold('RELEASE_NOT_NEWER_OR_ROLLBACK')
    except SafetyHold:
        raise
    except Exception as exc:
        raise SafetyHold('RELEASE_MANIFEST_SCHEMA_INVALID') from exc
    return obj


@contextmanager
def exclusive_lock(target: str | Path, *, timeout_s: float = 3.0):
    """Cross-process O_EXCL lock; never auto-steal even if seemingly stale."""
    target = Path(target)
    lock = target.with_name(target.name + '.bgvoice.lock')
    deadline = time.monotonic() + timeout_s
    descriptor = None
    while descriptor is None:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise SafetyHold('LOCK_BUSY_HOLD:' + str(lock))
            time.sleep(0.025)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as f:
            json.dump({'pid': os.getpid(), 'started_unix_s': time.time()}, f)
            f.flush()
            os.fsync(f.fileno())
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def _zip_verified(z: zipfile.ZipFile) -> None:
    names = z.namelist()
    if len(names) != len(set(names)):
        raise SafetyHold('DUPLICATE_ZIP_NAMES_HOLD')
    for n in names:
        _safe_relname(n.rstrip('/'))
    if z.testzip() is not None:
        raise SafetyHold('BAD_ZIP_CRC_HOLD')


def merge_report_locked(path: str | Path, replacements: Mapping[str, bytes],
                        *, expected_sha256: str | None = None) -> str:
    """Serializes read-modify-write against OTHER writers using this lock protocol.

    Integration requirement: ALL live ZIP writers must take the same lock;
    otherwise a legacy process may still race with this one.
    """
    path = Path(path)
    if not path.is_file():
        raise SafetyHold('MAIN_REPORT_MISSING_HOLD')
    for name, payload in replacements.items():
        _safe_relname(name)
        if not isinstance(payload, bytes):
            raise SafetyHold('ZIP_PAYLOAD_NOT_BYTES:' + name)
    with exclusive_lock(path):
        baseline = file_sha256(path)
        if expected_sha256 is not None and baseline != expected_sha256:
            raise SafetyHold('REPORT_BASE_CHANGED_HOLD')
        fd, pending = tempfile.mkstemp(prefix='.bgvoice_zip_', suffix='.pending', dir=path.parent)
        os.close(fd)
        try:
            with zipfile.ZipFile(path, 'r') as src, zipfile.ZipFile(pending, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as dst:
                _zip_verified(src)
                for member in src.infolist():
                    if member.filename in replacements:
                        continue
                    with src.open(member) as inp, dst.open(member, 'w', force_zip64=True) as out:
                        shutil.copyfileobj(inp, out, 1024 * 1024)
                for name, contents in sorted(replacements.items()):
                    dst.writestr(name, contents)
            with zipfile.ZipFile(pending, 'r') as ready:
                _zip_verified(ready)
            # Catch non-cooperating legacy writers between the source read and rename.
            if file_sha256(path) != baseline:
                raise SafetyHold('REPORT_CONCURRENT_UNCOOPERATIVE_WRITE_HOLD')
            os.replace(pending, path)
            return file_sha256(path)
        finally:
            if os.path.exists(pending):
                os.unlink(pending)


def _wave_ok(blob: bytes) -> dict:
    try:
        with wave.open(io.BytesIO(blob), 'rb') as w:
            duration = w.getnframes() / w.getframerate()
            if not (w.getnchannels() == 1 and w.getsampwidth() == 2 and
                    w.getcomptype() == 'NONE' and 0.4 < duration < 90):
                raise SafetyHold('WAV_PCM_FORMAT_HOLD')
            return {'duration_s': round(duration, 3), 'sample_rate': w.getframerate()}
    except (wave.Error, ZeroDivisionError, EOFError) as exc:
        raise SafetyHold('INVALID_WAV_HOLD') from exc


def _publish_no_overwrite(path: Path, data: bytes) -> None:
    fd, pending = tempfile.mkstemp(prefix='.bgvoice_candidate_', suffix='.pending', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.link(pending, path)
        except FileExistsError as exc:
            raise SafetyHold('EXISTING_CANDIDATE_HOLD') from exc
        except OSError as exc:
            # Safe default if hardlink publishing is unavailable: HOLD rather than overwrite.
            raise SafetyHold('ATOMIC_NO_OVERWRITE_NOT_SUPPORTED_HOLD') from exc
    finally:
        if os.path.exists(pending):
            os.unlink(pending)


def publish_candidate_once(path: str | Path, wav: bytes, *, sound_id: str,
                           fingerprint: str) -> dict:
    """Never replace an existing candidate or approved WAV. Sidecar is immutable."""
    target = Path(path)
    if not sound_id or not all(c.isalnum() or c == '_' for c in sound_id):
        raise SafetyHold('SOUND_ID_INVALID_HOLD')
    if len(fingerprint) != 64 or any(c not in '0123456789abcdef' for c in fingerprint):
        raise SafetyHold('FINGERPRINT_INVALID_HOLD')
    if len(wav) > 9 * 1024 * 1024:
        raise SafetyHold('CANDIDATE_WAV_SIZE_HOLD')
    params = _wave_ok(wav)
    if not target.parent.is_dir() or target.is_symlink():
        raise SafetyHold('CANDIDATE_STAGE_INVALID_HOLD')
    sidecar = target.with_suffix('.json')
    digest = sha256(wav).hexdigest()
    with exclusive_lock(target):
        if target.exists() or sidecar.exists():
            if target.is_file() and sidecar.is_file():
                try:
                    prior = json.loads(sidecar.read_text('utf-8'))
                    if prior.get('sha256') == digest and prior.get('fingerprint') == fingerprint and file_sha256(target) == digest:
                        return {'id': sound_id, 'status': 'REUSED_SHA_VERIFIED', 'sha256': digest}
                except (OSError, ValueError):
                    pass
            raise SafetyHold('CANDIDATE_OR_SIDECAR_CONFLICT_HOLD')
        _publish_no_overwrite(target, wav)
        meta = dict({'id': sound_id, 'status': 'NEW_NOT_APPROVED', 'sha256': digest,
                    'fingerprint': fingerprint, 'tts_allowed': False, 'game_install_allowed': False}, **params)
        try:
            _publish_no_overwrite(sidecar, json.dumps(meta, ensure_ascii=False, sort_keys=True).encode('utf-8'))
        except Exception as exc:
            # Never destroy an existing/generated audio file: partial staging remains HOLD.
            raise SafetyHold('PARTIAL_STAGING_HOLD') from exc
        return meta


def summarize_batch(jobs: list[dict], stage_dir: str | Path, *, worker_exit_code: int) -> dict:
    """Exit 0 only means the worker PROCESS ran; not that it made every WAV."""
    root = Path(stage_dir)
    rows = []
    for job in jobs:
        sid = str(job.get('id',''))
        if not re.fullmatch(r'[A-Za-z0-9_]{1,80}',sid):
            raise SafetyHold('BATCH_SOUND_ID_INVALID_HOLD')
        fingerprint = job.get('fingerprint','')
        if not isinstance(fingerprint,str) or re.fullmatch(r'[0-9a-f]{64}',fingerprint) is None:
            raise SafetyHold('BATCH_FINGERPRINT_INVALID_HOLD')
        out = root / (sid + '__SHTORM_MOVIE_DRAFT.wav')
        side = out.with_suffix('.json')
        state = 'HOLD_NOT_CREATED'
        if out.is_file() and side.is_file():
            try:
                meta = json.loads(side.read_text('utf-8'))
                if (meta.get('id') == sid and meta.get('fingerprint') == fingerprint and
                    meta.get('sha256') == file_sha256(out) and
                    meta.get('status') in ('NEW_RU_CANDIDATE_NOT_APPROVED','NEW_NOT_APPROVED')):
                    _wave_ok(out.read_bytes())
                    state = 'CANDIDATE_READY_NOT_APPROVED'
                else:
                    state = 'HOLD_SHA_OR_FINGERPRINT'
            except (OSError, ValueError, SafetyHold):
                state = 'HOLD_CORRUPTED'
        elif out.exists() or side.exists():
            state = 'HOLD_PARTIAL'
        rows.append({'id': sid, 'state': state})
    good = sum(x['state'] == 'CANDIDATE_READY_NOT_APPROVED' for x in rows)
    if worker_exit_code:
        batch_status = 'WORKER_FAILED_HOLD'
    elif good == len(rows) and rows:
        batch_status = 'ALL_CANDIDATES_READY_NOT_APPROVED'
    else:
        batch_status = 'PARTIAL_OR_EMPTY_HOLD'
    return {'process_exit_code': worker_exit_code, 'batch_status': batch_status,
            'expected': len(rows), 'ready': good, 'holds': len(rows) - good,
            'rows': rows, 'game_approved': False}


def create_style_plan(source_rows: list[dict], selected: Mapping[str, str]) -> dict:
    """A/B style *plan* only; cannot run TTS or bypass literary gate."""
    known = {x.get('sound_id', x.get('id')): x for x in source_rows}
    if None in known or len(known) != len(source_rows):
        raise SafetyHold('STYLE_SOURCE_INVALID_OR_DUPLICATE_IDS')
    out = []
    for sid, instruction in selected.items():
        if sid not in known or not instruction or len(instruction) > 170 or '\n' in instruction:
            raise SafetyHold('STYLE_SOURCE_INVALID:' + sid)
        row = known[sid]
        # Preserve original HUMAN accepted status; never silently reset it.
        voice_state = str(row.get('voice_selection_state', row.get('historical_russian_wav_status', '')))
        if 'HUMAN_ACCEPTED' in voice_state or 'LOCKED_APPROVED' in voice_state:
            raise SafetyHold('HUMAN_APPROVED_VOICE_NOT_AN_AB_TARGET:' + sid)
        speech = (row.get('literary_ru_semantic_candidate_v1_4', '') or
                  row.get('literary_ru_source_based_v1_3', '') or
                  row.get('literary_ru_proposal_unapproved', '') or
                  row.get('literary_ru_text', ''))
        if not speech:
            raise SafetyHold('LITERARY_SOURCE_TEXT_MISSING:' + sid)
        out.append({'id': sid, 'status': 'PLANNED_HOLD_TEXT_UNAPPROVED',
                    'speech_text_for_future_review': speech,
                    'A': {'preset': 'reference_only', 'style_control': ''},
                    'B': {'preset': 'style_candidate', 'style_control': instruction},
                    'C': {'preset': 'alternate_same_character_reference', 'status': 'HOLD_REFERENCE_SHA_NOT_VALIDATED'},
                    'tts_allowed': False, 'installed': False, 'user_voice_lock_preserved': True})
    return {'schema': 'BGVOICE_STYLE_EXPERIMENT_PLAN_V1', 'test_windows_gpu_completed': False,
            'all_tts_allowed': False, 'planned': len(out), 'jobs': out}


def build_shtorm_kwargs_for_approved_job(job: dict, *, variant: str,
                                          fork_supports_style_control: bool) -> dict:
    """Pure builder; deliberately refuses to run any unapproved movie generation.

    Caller must separately check model bundle integrity, same-person reference SHA,
    and write through publish_candidate_once (not the current Movie Core producer).
    """
    if job.get('tts_allowed') is not True or job.get('text_approved_by_human') is not True:
        raise SafetyHold('HOLD_LITERARY_TEXT_FIRST_37_NO_GPU')
    text = str(job.get('speech_text', '')).strip()
    if not text or len(text) > 500:
        raise SafetyHold('SPEECH_TEXT_EMPTY_OR_TOO_LONG_HOLD')
    ref = str(job.get('verified_reference_wav_path', ''))
    ref_sha = str(job.get('verified_reference_sha256', ''))
    if not ref or len(ref_sha) != 64:
        raise SafetyHold('REFERENCE_NOT_SHA_PINNED_HOLD')
    if variant == 'B':
        if not fork_supports_style_control:
            raise SafetyHold('SHTORM_LOCAL_FORK_STYLE_CONTROL_NOT_VERIFIED')
        control = str(job.get('style_control', '')).strip()
        if not control or len(control) > 170 or any(c in control for c in '\r\n()'):
            raise SafetyHold('STYLE_CONTROL_INVALID_HOLD')
        text = f'({control}){text}'
    elif variant != 'A':
        raise SafetyHold('UNSUPPORTED_VARIANT_HOLD')
    return {'text': text, 'reference_wav_path': ref, 'cfg_value': 2.0,
            'inference_timesteps': 12, 'normalize': False, 'denoise': False}


def inspect_existing_bundle_readonly(root: str | Path, *, max_files: int = 200) -> dict:
    """Inventory local weights without loading a model; hashes are NOT trust anchors.

    The caller should record hashes as evidence and obtain independent upstream
    provenance before constructing a strict pinset. Never generates audio.
    """
    folder = Path(root)
    if folder.is_symlink() or not folder.is_dir():
        return {'status':'HOLD_MODEL_ROOT_MISSING', 'files':[]}
    actual = []
    try:
        for file in folder.rglob('*'):
            if file.is_symlink():
                raise SafetyHold('MODEL_SYMLINK_IN_INVENTORY_HOLD')
            if file.is_file():
                name = file.relative_to(folder).as_posix()
                _safe_relname(name)
                if len(actual) >= max_files:
                    raise SafetyHold('MODEL_INVENTORY_LIMIT_EXCEEDED')
                actual.append({'relative_path':name, 'bytes':file.stat().st_size,
                               'sha256':file_sha256(file)})
            elif not file.is_dir():
                raise SafetyHold('MODEL_SPECIAL_FILE_HOLD')
    except (OSError, PermissionError, SafetyHold) as e:
        return {'status':'HOLD_MODEL_INVENTORY_ERROR', 'reason':str(e), 'files':[]}
    return {'status':'OBSERVED_NOT_TRUSTED_PINSET_NOT_LOADED',
            'files': sorted(actual, key=lambda x:x['relative_path']),
            'warning':'Actual SHA/size do not prove the model is from the trusted source'}


def inspect_report_readonly(report_path: str | Path, *, max_entries: int = 25000) -> dict:
    """Reads ZIP integrity and statuses without updating the ONE report."""
    target = Path(report_path)
    if not target.is_file():
        return {'status':'HOLD_REPORT_MISSING','path':str(target)}
    try:
        baseline = file_sha256(target)
        with zipfile.ZipFile(target,'r') as z:
            if len(z.infolist()) > max_entries:
                raise SafetyHold('REPORT_TOO_MANY_ENTRIES')
            _zip_verified(z)
            names=set(z.namelist())
        final = file_sha256(target)
        if baseline != final:
            raise SafetyHold('REPORT_CHANGED_DURING_READONLY_SCAN')
        return {'status':'REPORT_INTEGRITY_PASS_NOT_AUDIO_APPROVED',
                'zip_sha256':baseline,'entry_count':len(names),
                'approved_for_game':False,'movie_tts_allowed':False}
    except (OSError, zipfile.BadZipFile, SafetyHold) as e:
        return {'status':'HOLD_REPORT_INTEGRITY', 'reason':str(e)}


def build_strict_style_pair(job: Mapping, *, verified_same_character_ref: Path,
                            expected_ref_sha256: str, fork_style_supported: bool) -> dict:
    """Build two comparable inputs WITHOUT synthesizing; fail closed on human gates."""
    ref = Path(verified_same_character_ref)
    if not ref.is_file() or ref.is_symlink() or file_sha256(ref) != expected_ref_sha256:
        raise SafetyHold('STYLE_REFERENCE_SHA_MISMATCH_HOLD')
    if job.get('voice_reference_human_approved') is not True:
        raise SafetyHold('STYLE_VOICE_IDENTITY_HOLD')
    if job.get('original_en_source_verified') is not True:
        raise SafetyHold('STYLE_EN_SOURCE_HOLD')
    strict_job = dict(job, verified_reference_wav_path=str(ref),
                      verified_reference_sha256=expected_ref_sha256)
    a = build_shtorm_kwargs_for_approved_job(strict_job,variant='A',fork_supports_style_control=False)
    b = build_shtorm_kwargs_for_approved_job(strict_job,variant='B',fork_supports_style_control=fork_style_supported)
    if a['reference_wav_path'] != b['reference_wav_path']:
        raise SafetyHold('STYLE_A_B_REF_DIFFERENCE_HOLD')
    return {'schema':'BGVOICE_AB_STYLE_PAIR_ARGS_ONLY_V2', 'status':'INPUTS_READY_NO_TTS_EXECUTED',
            'variant_A':a,'variant_B':b,'sha256_reference':expected_ref_sha256,
            'game_install_allowed':False}
