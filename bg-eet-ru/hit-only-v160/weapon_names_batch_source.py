# -*- coding: utf-8 -*-
"""SOURCE-ONLY guarded batch of RU weapon names into already-installed V160.

NO user-facing CLI or separate updater.  A future SHA-pinned revision of the
existing one-file CMD is the only permitted dispatcher.  Read-only preflight
and isolated tests are safe; no live deployment is authorized by this source.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SCHEMA = 'BG_EET_RU_WEAPON_NAMES_BATCH_SOURCE_ONLY_V1'
STATE_NAME = 'BG_EET_RU_WEAPON_NAMES_BATCH_STATE.json'
APPROVE_INSTALL = 'INSTALL_BG_EET_RU_WEAPON_NAMES_BATCH'
APPROVE_ROLLBACK = 'ROLLBACK_BG_EET_RU_WEAPON_NAMES_BATCH'
MODULE_REL = 'EEex_scripts/BG_EET_RU_WeaponObserver.lua'
V160_STATE = 'BG_EET_RU_V160_HIT_ONLY_STATE.json'
# SHA of installed V160 as observed in the private user's 28-Nov V160 report.
EXPECTED_USER_V160_SHA = '386980c6c20f36a50ad4c667a2155c8603588651538ebb5484e65913254ecc33'
MAX_NEW_NAMES = 64
# Verified IESDP ITM type IDs, limited to weapons/launchers/ammo we know.
WEAPON_ITEM_TYPES = frozenset({5, 14, 15, 16, 18, 19, 20, 25, 26, 27, 31})
MAX_MODULE = 100_000
NAME_RE = re.compile(r"[А-Яа-яЁёA-Za-z0-9 +,.()\-/]{1,90}\Z")
RESREF_RE = re.compile(r'[A-Z0-9_]{1,8}\Z')
PIN_RE = re.compile(r'[0-9a-f]{64}\Z')
# Preserve the original installed V160 names and order byte-for-byte.
OLD_NAMES = ("local BG_EET_RU_V160_names = {\n"
             "    SW1H04='Длинный меч',\n"
             "    AROW01='Стрела',\n"
             "    BOW05='Короткий лук',\n")
END_NAMES = '}\nlocal function BG_EET_RU_V160_ref(item)'

class SafeStop(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_file(path: Path, limit: int = MAX_MODULE) -> bytes:
    if path.is_symlink() or not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise SafeStop('MISSING_SYMLINK_OR_LARGE:' + path.name)
    return path.read_bytes()


def file_sha(path: Path, limit: int = 256_000_000) -> str:
    if path.is_symlink() or not path.is_file() or not 1 <= path.stat().st_size <= limit:
        raise SafeStop('TLK_OR_GAMEFILE_UNSAFE:' + path.name)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_catalog(catalog: dict) -> dict:
    """Only identical identified/unidentified, dialog/dialogf RU names.

    This is a conservative downstream check of the actual R3+V111 catalog,
    never a translation or an assumption of runtime identification state.
    """
    if not isinstance(catalog, dict) or catalog.get('schema') != 'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1' \
            or catalog.get('status') != 'READ_ONLY_SOURCE_CATALOG' \
            or catalog.get('gameFilesWritten') != 0 or catalog.get('engineListenersAdded') != 0 \
            or catalog.get('combatLogRowJoinVerified') is not False:
        raise SafeStop('CATALOG_SOURCE_NOT_PROVEN')
    hashes = catalog.get('tlkSha256')
    if not isinstance(hashes, dict) or set(hashes) != {'dialog.tlk', 'dialogf.tlk'} \
            or any(not isinstance(x, str) or not PIN_RE.fullmatch(x) for x in hashes.values()):
        raise SafeStop('CATALOG_TLK_SHA_MISSING')
    items = catalog.get('items')
    if not isinstance(items, dict) or not 1 <= len(items) <= MAX_NEW_NAMES:
        raise SafeStop('CATALOG_ITEM_COUNT_UNSAFE')
    ready = {}
    for ref, row in items.items():
        if not isinstance(ref, str) or not RESREF_RE.fullmatch(ref) \
                or not isinstance(row, dict):
            raise SafeStop('CATALOG_RESREF_OR_ROW_UNSAFE')
        if ref in ('SW1H04', 'AROW01', 'BOW05'):
            # Never change V160's known live names, including AROW01.
            continue
        if row.get('status') != 'COMMON_RU_NAME_VERIFIED':
            continue
        if type(row.get('itemTypeRaw')) is not int or row['itemTypeRaw'] not in WEAPON_ITEM_TYPES:
            raise SafeStop('CATALOG_NOT_A_WEAPON_OR_AMMO:' + ref)
        name = row.get('autoDisplayName')
        if not isinstance(name, str) or not NAME_RE.fullmatch(name) \
                or not re.search(r'[А-Яа-яЁё]', name) or len(name.encode('utf-8')) > 180:
            raise SafeStop('CATALOG_NAME_NOT_SAFE:' + ref)
        variants = [row.get(variant + 'RuByTlk') for variant in ('unidentified', 'identified')]
        if any(not isinstance(x, dict) or set(x) != {'dialog.tlk', 'dialogf.tlk'} \
                   or any(v != name for v in x.values()) for x in variants):
            raise SafeStop('CATALOG_IDENTIFICATION_VARIANTS_DRIFT:' + ref)
        sha = row.get('resourceSha256')
        if not isinstance(sha, str) or not PIN_RE.fullmatch(sha) \
                or row.get('origin') not in ('CURRENT_GAME_BIFF', 'CURRENT_GAME_OVERRIDE'):
            raise SafeStop('CATALOG_ITM_PROVENANCE_MISSING:' + ref)
        ready[ref] = {'name': name, 'sha256': sha, 'origin': row['origin']}
    if not ready:
        raise SafeStop('NO_NEW_NAMES_VERIFIED')
    if len(ready) > MAX_NEW_NAMES:
        raise SafeStop('TOO_MANY_NEW_NAMES')
    return {'tlkSha256': hashes, 'entries': ready}


def candidate_bytes(installed_v160: bytes, verified_names: dict, expected_base_sha: str = EXPECTED_USER_V160_SHA) -> bytes:
    """Patch ONLY the existing V160 literal dictionary, never an EEex hook."""
    if not isinstance(installed_v160, bytes) or len(installed_v160) > MAX_MODULE \
            or not isinstance(expected_base_sha, str) or not PIN_RE.fullmatch(expected_base_sha) \
            or digest(installed_v160) != expected_base_sha:
        raise SafeStop('V160_EXACT_INSTALLED_SHA_CHANGED')
    original = OLD_NAMES.encode('utf-8')
    end = END_NAMES.encode('utf-8')
    if installed_v160.count(original) != 1 or installed_v160.count(end) != 1 \
            or installed_v160.count(b'BG_EET_RU_V160_names') != 2:
        raise SafeStop('V160_NAMES_CONTRACT_CHANGED')
    if not isinstance(verified_names, dict) or not 1 <= len(verified_names) <= MAX_NEW_NAMES:
        raise SafeStop('BATCH_NAMES_COUNT_UNSAFE')
    additions = []
    for ref, data in sorted(verified_names.items()):
        if ref in ('SW1H04', 'AROW01', 'BOW05') or not RESREF_RE.fullmatch(ref) \
                or not isinstance(data, dict):
            raise SafeStop('BATCH_REDEF_OR_RESREF_UNSAFE')
        name = data.get('name')
        if not isinstance(name, str) or not NAME_RE.fullmatch(name) \
                or not re.search(r'[А-Яа-яЁё]', name):
            raise SafeStop('BATCH_INVALID_LUA_NAME')
        # NAME_RE excludes quotes, backslashes, newlines and Lua syntax.
        additions.append(f"    {ref}='{name}',\n".encode('utf-8'))
    extended = original + b''.join(additions)
    candidate = installed_v160.replace(original, extended, 1)
    if candidate == installed_v160 or len(candidate) > MAX_MODULE \
            or candidate.replace(extended, original, 1) != installed_v160:
        raise SafeStop('BATCH_SPAN_OR_INVERSE_MISMATCH')
    if candidate.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(') \
            != installed_v160.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener('):
        raise SafeStop('BATCH_NATIVE_LISTENER_CHANGED')
    return candidate


def _check_game_closed() -> None:
    if os.name != 'nt':
        return
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, timeout=12, check=True)
    for line in result.stdout.splitlines():
        name = line.strip().split(',', 1)[0].strip('" ').lower()
        if name in ('baldur.exe', 'infinityloader.exe') or (name.startswith('setup-') and name.endswith('.exe')):
            raise SafeStop('CLOSE_GAME_LOADER_WEIDU')


def _secure_workdir(game: Path, workdir: Path) -> None:
    if workdir.is_symlink() or game.is_symlink() or workdir.resolve() == game.resolve() \
            or game.resolve() in workdir.resolve().parents \
            or workdir.resolve() in game.resolve().parents:
        raise SafeStop('EXTERNAL_WORKDIR_REQUIRED')


def _check_baseline(game: Path, workdir: Path, catalog: dict, get_item, existing_pins: dict) -> tuple[dict, bytes, dict]:
    """Read-only preflight, using current R3 resolver supplied by pinned caller."""
    _secure_workdir(game, workdir)
    if not (game / 'chitin.key').is_file():
        raise SafeStop('NO_CHITIN_KEY')
    _check_game_closed()
    state = json.loads(read_file(workdir / V160_STATE, 20000))
    original = read_file(game / MODULE_REL)
    if state.get('schema') != 'BG_EET_RU_V160_HIT_ONLY_GUARDED_V1' \
            or state.get('phase') != 'INSTALLED' \
            or state.get('candidate_sha256') != EXPECTED_USER_V160_SHA \
            or digest(original) != EXPECTED_USER_V160_SHA:
        raise SafeStop('V160_INSTALLED_STATE_DRIFT')
    # The V160 install state already pins the complete game baseline; do not
    # accept a caller-provided subset or a substituted set of SHA values.
    if not isinstance(existing_pins, dict) or not existing_pins \
            or state.get('pinned_game_hashes') != existing_pins:
        raise SafeStop('V160_EXISTING_PIN_CONTRACT_MISMATCH')
    for relative, expected in existing_pins.items():
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() \
                or any(x in ('.', '..') for x in Path(relative).parts) \
                or '\\' in relative or ':' in relative \
                or not isinstance(expected, str) or not PIN_RE.fullmatch(expected) \
                or file_sha(game / relative) != expected:
            raise SafeStop('EXISTING_GAME_PIN_DRIFT:' + str(relative))
    weidu_sha = file_sha(game / 'WeiDU.log', 10_000_000)
    names = validate_catalog(catalog)
    for tlk, expected in names['tlkSha256'].items():
        if file_sha(game / 'lang' / 'ru_RU' / tlk) != expected:
            raise SafeStop('TLK_CHANGED_AFTER_NAME_SCAN:' + tlk)
    if not hasattr(get_item, 'get'):
        raise SafeStop('R3_ITEM_RESOLVER_MISSING')
    for ref, expected in names['entries'].items():
        raw, origin = get_item.get(ref, '.ITM')
        if not isinstance(raw, bytes) or not isinstance(origin, dict) \
                or digest(raw) != expected['sha256'] or origin.get('origin') != expected['origin']:
            raise SafeStop('ITEM_CHANGED_AFTER_NAME_SCAN:' + ref)
    result = {'schema': SCHEMA, 'status': 'BATCH_PREFLIGHT_PASS',
              'gameFilesWritten': 0, 'namesToAdd': sorted(names['entries']),
              'currentV160Sha': digest(original), 'weiduSha': weidu_sha,
              'tlkSha256': names['tlkSha256'],
              'candidateSha': digest(candidate_bytes(original, names['entries'], EXPECTED_USER_V160_SHA))}
    return result, original, names


def _atomic_json_new(path: Path, row: dict):
    if path.exists() or path.is_symlink():
        raise SafeStop('BATCH_STATE_ALREADY_EXISTS')
    raw = json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2).encode('utf-8')
    with path.open('xb') as f:
        f.write(raw)
    if read_file(path, 20000) != raw:
        raise SafeStop('STATE_VERIFY_FAIL')


def run(mode: str, game: Path, workdir: Path, catalog: dict | None = None,
        get_item=None, existing_pins: dict | None = None, typed: str | None = None) -> dict:
    """Import-only source. Never execute against a user's game from a second script."""
    game, workdir = Path(game), Path(workdir)
    try:
        _secure_workdir(game, workdir)
        if mode == 'status':
            path = workdir / STATE_NAME
            if not path.exists():
                return {'schema': SCHEMA, 'status': 'BATCH_NOT_INSTALLED', 'gameFilesWritten': 0}
            state = json.loads(read_file(path, 20000))
            sha = file_sha(game / MODULE_REL)
            status = 'BATCH_INSTALLED_SOURCE_ONLY' if state.get('phase') == 'INSTALLED' and sha == state.get('candidateSha') else 'BATCH_STATE_HOLD'
            return {'schema': SCHEMA, 'status': status, 'gameFilesWritten': 0}
        if mode in ('preflight', 'install'):
            if (workdir / STATE_NAME).exists() or (workdir / STATE_NAME).is_symlink():
                raise SafeStop('BATCH_EXISTING_STATE')
            if not isinstance(catalog, dict) or existing_pins is None:
                raise SafeStop('BATCH_CATALOG_OR_PINS_MISSING')
            report, original, names = _check_baseline(game, workdir, catalog, get_item, existing_pins)
            if mode == 'preflight':
                return report
            # Until integrated by an explicit new release into the SAME CMD,
            # this source has no user-facing installation entrypoint.
            if typed != APPROVE_INSTALL:
                raise SafeStop('BATCH_EXACT_TYPED_APPROVAL_REQUIRED')
            candidate = candidate_bytes(original, names['entries'], EXPECTED_USER_V160_SHA)
            _check_game_closed()
            if file_sha(game / 'WeiDU.log', 10_000_000) != report['weiduSha']:
                raise SafeStop('WEIDU_CHANGED_DURING_CONFIRMATION')
            for tlk, expected in names['tlkSha256'].items():
                if file_sha(game / 'lang' / 'ru_RU' / tlk) != expected:
                    raise SafeStop('TLK_CHANGED_DURING_CONFIRMATION')
            for ref, expected in names['entries'].items():
                raw, provenance = get_item.get(ref, '.ITM')
                if digest(raw) != expected['sha256'] or provenance.get('origin') != expected['origin']:
                    raise SafeStop('ITM_CHANGED_DURING_CONFIRMATION:' + ref)
            if file_sha(game / MODULE_REL) != report['currentV160Sha']:
                raise SafeStop('V160_CHANGED_DURING_CONFIRMATION')
            backdir = workdir / 'BG_EET_RU_V160_SAFE_BACKUP'
            if backdir.is_symlink():
                raise SafeStop('BACKUP_SYMLINK')
            backdir.mkdir(parents=True, exist_ok=True)
            # Preserve the already-installed V160 as the exact rollback baseline.
            name = 'NamesBatch_' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            backup = backdir / name
            backup.mkdir(exist_ok=False)
            b = backup / 'BG_EET_RU_WeaponObserver.lua.before'
            with b.open('xb') as f: f.write(original)
            if read_file(b) != original:
                raise SafeStop('BACKUP_FAILED')
            state = {'schema': SCHEMA, 'phase': 'PREPARED', 'backup': str(b),
                     'baselineSha': digest(original), 'candidateSha': digest(candidate),
                     'weiduSha': report['weiduSha'], 'tlkSha256': names['tlkSha256'],
                     'gamePins': existing_pins, 'itemPins': names['entries'],
                     'createdUtc': dt.datetime.now(dt.timezone.utc).isoformat()}
            _atomic_json_new(workdir / STATE_NAME, state)
            target = game / MODULE_REL
            staged = target.with_name(target.name + '.batch.stage')
            if staged.exists() or staged.is_symlink():
                raise SafeStop('BATCH_STAGE_COLLISION')
            try:
                with staged.open('xb') as f: f.write(candidate)
                if read_file(staged) != candidate or file_sha(target) != report['currentV160Sha']:
                    raise SafeStop('STAGED_BYTES_OR_BASELINE_DRIFT')
                if file_sha(game / 'WeiDU.log', 10_000_000) != report['weiduSha']:
                    raise SafeStop('WEIDU_DRIFT_BEFORE_SWAP')
                os.replace(staged, target)
                if file_sha(target) != digest(candidate):
                    raise SafeStop('POST_INSTALL_SHA_HOLD')
                state['phase'] = 'INSTALLED'
                # Preserve PREPARED on incomplete state transitions, fail closed.
                tmp = (workdir / STATE_NAME).with_suffix('.next')
                with tmp.open('xb') as f: f.write(json.dumps(state, ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8'))
                os.replace(tmp, workdir / STATE_NAME)
            finally:
                if staged.exists(): staged.unlink()
            return {'schema': SCHEMA, 'status': 'BATCH_INSTALLED_AWAITING_GAMEPLAY',
                    'gameFilesWritten': 1, 'namesAdded': len(names['entries']),
                    'newNativeHooks': 0, 'existingV160Preserved': True}
        if mode == 'rollback':
            _check_game_closed()
            state = json.loads(read_file(workdir / STATE_NAME, 20000))
            if state.get('schema') != SCHEMA or state.get('phase') not in ('PREPARED', 'INSTALLED') \
                    or state.get('baselineSha') != EXPECTED_USER_V160_SHA:
                raise SafeStop('BATCH_NOT_ROLLBACKABLE')
            target = game / MODULE_REL
            current = file_sha(target)
            if state['phase'] == 'INSTALLED' and current != state.get('candidateSha'):
                raise SafeStop('BATCH_ROLLBACK_NOT_LAST_CHANGE')
            if state['phase'] == 'PREPARED' and current not in (state.get('candidateSha'),state.get('baselineSha')):
                raise SafeStop('BATCH_PREPARED_GAMEFILE_DRIFT')
            if file_sha(game / 'WeiDU.log', 10_000_000) != state.get('weiduSha'):
                raise SafeStop('BATCH_ROLLBACK_WEIDU_DRIFT')
            if not isinstance(state.get('gamePins'), dict) or not state['gamePins']:
                raise SafeStop('BATCH_ROLLBACK_PINS_MISSING')
            for rel, expected in state['gamePins'].items():
                if file_sha(game / rel) != expected:
                    raise SafeStop('BATCH_ROLLBACK_GAME_DRIFT:' + rel)
            backup = Path(state['backup'])
            if backup.is_symlink() or workdir.resolve() not in backup.resolve().parents:
                raise SafeStop('BATCH_ROLLBACK_BACKUP_OUTSIDE_WORKDIR')
            original = read_file(backup)
            if digest(original) != state['baselineSha']:
                raise SafeStop('BATCH_ROLLBACK_BACKUP_DRIFT')
            if typed != APPROVE_ROLLBACK:
                raise SafeStop('BATCH_ROLLBACK_TYPED_APPROVAL_REQUIRED')
            if file_sha(target) != current:
                raise SafeStop('BATCH_ROLLBACK_LIVE_DRIFT')
            # PREPARED can result from a crash before or after the game swap.
            # When the game still has V160, do not rewrite it unnecessarily.
            changed = current != state['baselineSha']
            staged = target.with_name(target.name + '.batch.restore')
            if staged.exists() or staged.is_symlink():
                raise SafeStop('BATCH_RESTORE_COLLISION')
            try:
                if changed:
                    with staged.open('xb') as f:f.write(original)
                    if read_file(staged) != original:raise SafeStop('BATCH_RESTORE_STAGE_SHA_HOLD')
                    os.replace(staged,target)
                    if file_sha(target) != state['baselineSha']:
                        raise SafeStop('BATCH_RESTORE_SHA_HOLD')
                state['phase'] = 'ROLLED_BACK'
                tmp = (workdir / STATE_NAME).with_suffix('.next')
                with tmp.open('xb') as f:f.write(json.dumps(state, ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8'))
                os.replace(tmp,workdir / STATE_NAME)
            finally:
                if staged.exists():staged.unlink()
            return {'schema': SCHEMA, 'status': 'BATCH_ROLLED_BACK_TO_V160',
                    'gameFilesWritten': int(changed), 'v160RestoredExact': True}
        raise SafeStop('UNKNOWN_MODE')
    except (SafeStop, ValueError, OSError, TypeError, KeyError, AttributeError) as e:
        return {'schema': SCHEMA, 'status': 'BATCH_SAFE_STOP', 'reason': str(e)[:150],
                'gameFilesWritten': 0 if mode in ('preflight', 'status') else 'UNKNOWN_AFTER_EXCEPTION'}

if __name__ == '__main__':
    raise SystemExit('SOURCE_ONLY: import from existing SHA-pinned single CMD; no separate runner')