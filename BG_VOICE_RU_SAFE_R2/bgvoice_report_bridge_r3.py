"""BG Voice RU source-only R3: transactional adapter for existing movie and V70 writers.

No import-time side effects, no game writes, no GPU, no remote downloads.
Requires sibling bgvoice_safeguards_r2.py. Current live updater DOES NOT load this file.

The bridge never changes the historical literary-TTS HOLD and does not call TTS.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Mapping, Iterable
import os
import shutil
import tempfile
import zipfile

from bgvoice_safeguards_r2 import SafetyHold, _safe_relname, _zip_verified, exclusive_lock, file_sha256

MOVIE_CORE_COMPAT = '1.11.0'
V70_CORE_COMPAT = '1.2.0'
MOVIE_REPORT_BASENAME = 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
DEFAULT_FULL_PRODUCTION = Path.home() / 'Documents' / 'BG_VOICE_RU' / 'FULL_PRODUCTION'


def _strict_prefixes(prefixes: Iterable[str]) -> tuple[str, ...]:
    result = []
    for prefix in prefixes:
        if not isinstance(prefix, str) or not prefix.endswith('/'):
            raise SafetyHold('REPORT_REMOVE_PREFIX_INVALID_HOLD')
        _safe_relname(prefix[:-1])
        result.append(prefix)
    return tuple(result)


def merge_report_transaction(report: Path | str, replacements: Mapping[str, bytes],
                             *, remove_exact: Iterable[str] = (),
                             remove_prefixes: Iterable[str] = (),
                             max_members: int = 25000) -> dict:
    """Preserve report bytes on HOLD; serialize cooperative writers.

    Deprecated files are removed only if explicitly named or under explicit
    prefixes; V70 uses the same historical RESULT_PREFIX deletion semantics.
    Cross-writer safety is effective only once every writer cooperates.
    """
    target = Path(report)
    if target.name != MOVIE_REPORT_BASENAME or not target.is_file() or target.is_symlink():
        raise SafetyHold('ONE_REPORT_LOCATION_INVALID_HOLD')
    if not isinstance(replacements, Mapping):
        raise SafetyHold('REPORT_REPLACEMENTS_TYPE_HOLD')
    removal = frozenset(_safe_relname(n) for n in remove_exact)
    prefixes = _strict_prefixes(remove_prefixes)
    for name, payload in replacements.items():
        _safe_relname(name)
        if (not isinstance(payload, bytes) or len(payload) > 100 * 1024 * 1024):
            raise SafetyHold('REPORT_PAYLOAD_INVALID_HOLD:' + str(name))
    with exclusive_lock(target, timeout_s=15.0):
        original_sha = file_sha256(target)
        with zipfile.ZipFile(target, 'r') as original:
            if len(original.infolist()) > max_members:
                raise SafetyHold('REPORT_ENTRY_LIMIT_HOLD')
            _zip_verified(original)
            names = original.namelist()
            # Check all surviving bytes would be exactly the same before rewriting.
            removed_only = [n for n in names if n not in replacements and
                            (n in removal or any(n.startswith(p) for p in prefixes))]
            all_targets_current = all(name in names and original.read(name) == payload
                                      for name, payload in replacements.items())
            if not removed_only and all_targets_current:
                return {'status': 'UNCHANGED', 'sha256': original_sha,
                        'entry_count': len(names), 'game_write': False}
            fd, tmp = tempfile.mkstemp(prefix='.bgvoice_r3_', suffix='.pending', dir=str(target.parent))
            os.close(fd)
            try:
                with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED,
                                     compresslevel=4, allowZip64=True) as out:
                    for meta in original.infolist():
                        name = meta.filename
                        if (name in replacements or name in removal or
                                any(name.startswith(p) for p in prefixes)):
                            continue
                        if name.endswith('/'):
                            out.writestr(meta, b'')
                        else:
                            with original.open(meta) as source, out.open(meta, 'w', force_zip64=True) as dest:
                                shutil.copyfileobj(source, dest, 1024 * 1024)
                    for name, payload in sorted(replacements.items()):
                        out.writestr(name, payload)
                with zipfile.ZipFile(tmp, 'r') as ready:
                    _zip_verified(ready)
                    if len(ready.infolist()) > max_members:
                        raise SafetyHold('REPORT_NEW_ENTRY_LIMIT_HOLD')
                new_count = len(ready.infolist())
                # Fail closed on concurrent legacy writers we can actually detect.
                if file_sha256(target) != original_sha:
                    raise SafetyHold('REPORT_NONCOOPERATING_WRITER_DETECTED_HOLD')
                # fsync before atomic replacement, no in-place ZIP writes.
                with open(tmp, 'rb') as completed:
                    os.fsync(completed.fileno())
                os.replace(tmp, target)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        return {'status': 'MERGED', 'sha256': file_sha256(target),
                'entry_count': new_count,
                'game_write': False}


def movie_merge_main_report(replacements: Mapping[str, bytes], root: Path | str | None = None,
                            remove_names: Iterable[str] = ()) -> str:
    """Signature compatible with BG_VOICE_MOVIE_CORE._merge_main_report."""
    folder = Path(root) if root else Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or DEFAULT_FULL_PRODUCTION)
    result = merge_report_transaction(folder / MOVIE_REPORT_BASENAME,
                                      replacements, remove_exact=remove_names)
    return 'MAIN_REPORT_UPDATED_ATOMIC_R3' if result['status'] == 'MERGED' else 'MAIN_REPORT_UNCHANGED_R3'


def v70_replace_atomic(report: Path | str, replacements: Mapping[str, bytes],
                       *, result_prefix: str) -> str:
    """BG_VOICE_V70_CORE._replace_atomic-compatible deletion of OLD result prefix."""
    result = merge_report_transaction(report, replacements,
                                      remove_prefixes=(result_prefix,))
    return result['status']


def verify_compatible_core_contract(movie_version: str, v70_version: str,
                                   *, literary_gate_present: bool) -> dict:
    """Do not attach adapter to an unknown runtime or unguarded movie code."""
    if movie_version != MOVIE_CORE_COMPAT or v70_version != V70_CORE_COMPAT:
        raise SafetyHold('CORE_VERSION_NOT_AUDITED_HOLD')
    if not literary_gate_present:
        raise SafetyHold('MOVIE_LITERARY_HOLD_NOT_PRESENT')
    return {'status': 'SOURCE_COMPATIBILITY_CONTRACT_PASS',
            'movie_core': movie_version, 'v70_core': v70_version,
            'live_integration': False, 'windows_test': False, 'tts_allowed': False}
