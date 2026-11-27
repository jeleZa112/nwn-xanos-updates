# -*- coding: utf-8 -*-
"""BG_EET_RU V160: guarded hit-only player-visible weapon label.

Use ONLY from the existing one-file BG_EET_RU_UPDATE.cmd. No game writes on
preflight/status, no automatic install, no new native hooks, and no UI/TLK edits.
Appends a SHA-pinned Lua wrapper to the single *already installed* V108 EEex
weapon observer. Previous listener function and return value are preserved.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

SCHEMA = 'BG_EET_RU_V160_HIT_ONLY_GUARDED_V1'
STATE_NAME = 'BG_EET_RU_V160_HIT_ONLY_STATE.json'
APPROVE_INSTALL = 'INSTALL_BG_EET_RU_V160_HIT_ONLY'
APPROVE_ROLLBACK = 'ROLLBACK_BG_EET_RU_V160_HIT_ONLY'
MODULE_REL = 'EEex_scripts/BG_EET_RU_WeaponObserver.lua'
UI_REL = 'override/UI.MENU'
APPEND_SHA = 'ad76b46df1359bfdeeb9400f6b10f2ecd104059bd17a12d737fa60dcd733445c'
APPEND_SIZE = 2218
V106_BASE_SHA = '4130359dc7778e816ad2bbf1cca20152e48fa9df4907d6411a793c0754e09bc6'
V108_TAIL_SHA = '990e2448cc64da1118fbe1dae0cee141bd93bc0a3e54720c8ce49dbd7712ea6c'
V108_TAIL_SIZE = 3160

# Pinned *installed* source bytes, not generic upstream version numbers.
GAME_PINS = {
    'Baldur.exe': 'fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580',
    'InfinityLoader.exe': 'df0d3604cb91c127643126b7960429194f3333bce8bac0e59aecb6a178ac84b9',
    'EEex.dll': 'b6c7c98804360cb46531db75ab9608e378fd403d60c29c0e29946a60a334276a',
    'EEex_scripts/EEex_Main.lua': '5a0cf85af1da9a2c13813f9be03001d8d821addffe137780b74a73b6c4d75618',
    'EEex_scripts/EEex_Sprite.lua': '4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28',
    'EEex_scripts/EEex_Sprite_Patch.lua': 'e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f',
    UI_REL: 'ce4a46cf32058295c221b9124916f46764780752f9611adc8319c4dda9653efe',
    'override/BGCL150.lua': 'deffadc9fa9a0b0b9040127fa30abce2808833532618e4d9e7db7ed98c17d93b',
    'WeiDU.log': '3f838e42236898b63cacb3256e9fff4bcea1b9f2273baba4baff27e8883f4538',
    'lang/ru_RU/dialog.tlk': '7edebcaee0c8fd5ea19128893e6d8be43b58dd8526845ae641fcfa8ce9e9e536',
    'lang/ru_RU/dialogf.tlk': '80ad298977439fdd95f713aa534fa957c54761ce0ea4cad96ade07435775c530',
}

class SafeStop(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_file(path: Path, maximum: int = 70_000_000) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise SafeStop('MISSING_SYMLINK_OR_OVERSIZED_FILE: ' + str(path))
    return path.read_bytes()


def checked_external(game: Path, workdir: Path) -> None:
    gp, wp = game.resolve(), workdir.resolve()
    if wp == gp or gp in wp.parents:
        raise SafeStop('BACKUP_INSIDE_GAME_FORBIDDEN')
    if workdir.is_symlink():
        raise SafeStop('WORKDIR_SYMLINK_FORBIDDEN')


def verify_baseline(module: bytes) -> None:
    if len(module) <= V108_TAIL_SIZE:
        raise SafeStop('V108_MODULE_TOO_SHORT')
    if digest(module[:-V108_TAIL_SIZE]) != V106_BASE_SHA:
        raise SafeStop('V106_EXACT_PREFIX_CHANGED')
    if digest(module[-V108_TAIL_SIZE:]) != V108_TAIL_SHA:
        raise SafeStop('V108_EXACT_ENABLED_SUFFIX_CHANGED')
    # The V108 callback must be reachable by its original global name. Never
    # replace the registered listener or add a new native hook.
    if module.count(b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)') < 2:
        raise SafeStop('V108_GLOBAL_WRAPPER_MISSING')


def build_candidate(module: bytes, addition: bytes) -> bytes:
    verify_baseline(module)
    if len(addition) != APPEND_SIZE or digest(addition) != APPEND_SHA:
        raise SafeStop('V160_PINNED_LUA_CHANGED')
    if b'BG_EET_RU_V160_HIT' in module:
        raise SafeStop('V160_ALREADY_PRESENT')
    if addition.count(b'local BG_EET_RU_V160_previous = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage') != 1:
        raise SafeStop('V160_PREVIOUS_WRAPPER_MISSING')
    if addition.count(b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)') != 1:
        raise SafeStop('V160_DUPLICATE_OR_MISSING_WRAPPER')
    if b'EEex_Sprite_AddAlterBaseWeaponDamageListener(' in addition:
        raise SafeStop('SECOND_LISTENER_FORBIDDEN')
    return module + b'\n' + addition


def _status(game: Path, workdir: Path) -> dict:
    state = workdir / STATE_NAME
    if not state.exists():
        return {'schema': SCHEMA, 'status': 'V160_NOT_INSTALLED', 'game_files_written': 0,
                'gameplay_verified': False, 'misses_supported': False}
    data = json.loads(read_file(state, 20_000))
    if data.get('schema') != SCHEMA:
        raise SafeStop('V160_STATE_SCHEMA_MISMATCH')
    target = game / MODULE_REL
    current_sha = digest(read_file(target, 100_000))
    match = (data.get('phase') == 'INSTALLED' and
             current_sha == data.get('candidate_sha256'))
    return {'schema': SCHEMA,
            'status': 'V160_INSTALLED_AWAITING_GAMEPLAY' if match else 'V160_STATE_HOLD',
            'phase': data.get('phase'), 'module_sha256': current_sha,
            'expected_sha256': data.get('candidate_sha256'),
            'game_files_written': 0, 'gameplay_verified': False, 'misses_supported': False}


def _preflight(game: Path, workdir: Path, mode: str = 'preflight') -> tuple[dict, bytes]:
    checked_external(game, workdir)
    if not (game / 'chitin.key').is_file():
        raise SafeStop('NOT_A_BGS_EET_GAME')
    for rel, expected in GAME_PINS.items():
        if digest(read_file(game / rel)) != expected:
            raise SafeStop('BASELINE_SHA_MISMATCH:' + rel)
    target = game / MODULE_REL
    module = read_file(target, 100_000)
    verify_baseline(module)
    # The V108 state is an additional guard against accidental shadowed paths.
    v108_path = workdir / 'BG_EET_RU_V108_NATIVE_ITEM_STATE.json'
    v108 = json.loads(read_file(v108_path, 20_000))
    if v108.get('phase') != 'INSTALLED' or v108.get('candidate_sha256') != digest(module):
        raise SafeStop('V108_INSTALLED_STATE_DRIFT')
    state = workdir / STATE_NAME
    if state.exists():
        raise SafeStop('V160_EXISTING_STATE_USE_STATUS_OR_ROLLBACK')
    return {'schema': SCHEMA, 'status': 'V160_PREFLIGHT_PASS',
            'current_module_sha256': digest(module),
            'game_files_written': 0, 'new_native_hooks': 0,
            'misses_supported': False, 'same_journal_row_proven': False,
            'gameplay_verified': False,
            'note': 'One separate line for weapon-hit damage-effect events only'}, module


def _game_closed() -> None:
    if os.name != 'nt':
        return
    import subprocess
    completed = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True,
                               text=True, timeout=12, check=True)
    for line in completed.stdout.splitlines():
        name = line.strip().split(',', 1)[0].strip('" ').lower()
        if name in ('baldur.exe', 'infinityloader.exe') or (name.startswith('setup-') and name.endswith('.exe')):
            raise SafeStop('CLOSE_GAME_LOADER_WEIDU_BEFORE_INSTALL')


def atomic_external_json(path: Path, obj: dict) -> None:
    if path.is_symlink() or path.exists():
        raise SafeStop('STATE_ALREADY_EXISTS_OR_SYMLINK')
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8')
    stage = path.with_suffix('.stage')
    if stage.exists() or stage.is_symlink():
        raise SafeStop('STATE_STAGE_COLLISION')
    try:
        with stage.open('xb') as f: f.write(raw)
        if read_file(stage) != raw:
            raise SafeStop('STATE_STAGE_VERIFY_FAILED')
        os.replace(stage, path)
    finally:
        if stage.exists(): stage.unlink()


def replace_state(path: Path, obj: dict) -> None:
    current = json.loads(read_file(path, 20_000))
    if current.get('schema') != SCHEMA:
        raise SafeStop('STATE_REPLACE_SCHEMA_HOLD')
    tmp = path.with_suffix('.next')
    if tmp.exists() or tmp.is_symlink():
        raise SafeStop('STATE_NEXT_COLLISION')
    raw = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8')
    try:
        with tmp.open('xb') as f: f.write(raw)
        if read_file(tmp) != raw: raise SafeStop('STATE_NEXT_VERIFY_FAILED')
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()


def install(game: Path, workdir: Path, addition: bytes, approval: str | None = None) -> dict:
    report, original = _preflight(game, workdir)
    candidate = build_candidate(original, addition)
    _game_closed()
    entered = approval if approval is not None else input('Type '+APPROVE_INSTALL+' to install (Enter cancels): ')
    if entered != APPROVE_INSTALL:
        raise SafeStop('TYPED_APPROVAL_NOT_GIVEN')
    _game_closed()
    target = game / MODULE_REL
    if digest(read_file(target, 100_000)) != digest(original):
        raise SafeStop('BASELINE_CHANGED_DURING_CONFIRMATION')
    workdir.mkdir(parents=True, exist_ok=True)
    folder = workdir / 'BG_EET_RU_V160_SAFE_BACKUP' / ('V160_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if folder.exists() or folder.is_symlink():
        raise SafeStop('BACKUP_ALREADY_EXISTS')
    folder.mkdir(parents=True)
    backed = folder / 'BG_EET_RU_WeaponObserver.lua.before'
    with backed.open('xb') as f: f.write(original)
    if digest(read_file(backed,100_000)) != digest(original):
        raise SafeStop('BACKUP_SHA_FAILED')
    state_path = workdir / STATE_NAME
    state = {'schema':SCHEMA,'phase':'PREPARED', 'backup':str(backed),
             'original_sha256':digest(original), 'candidate_sha256':digest(candidate),
             'pinned_game_hashes': GAME_PINS, 'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'last_only': True}
    atomic_external_json(state_path, state)
    stage = target.with_name(target.name+'.v160.stage')
    if stage.exists() or stage.is_symlink():
        raise SafeStop('GAME_STAGE_COLLISION')
    try:
        with stage.open('xb') as f:f.write(candidate)
        if digest(read_file(stage,100_000)) != digest(candidate):
            raise SafeStop('GAME_STAGE_SHA_FAILED')
        if digest(read_file(target,100_000)) != digest(original):
            raise SafeStop('LIVE_MODULE_DRIFT_BEFORE_SWAP')
        os.replace(stage,target)
        if digest(read_file(target,100_000)) != digest(candidate):
            raise SafeStop('INSTALLED_SHA_MISMATCH_ROLLBACK_REQUIRED')
        state['phase']='INSTALLED'
        replace_state(state_path,state)
    finally:
        if stage.exists():stage.unlink()
    return {'schema':SCHEMA,'status':'V160_INSTALLED_AWAITING_GAMEPLAY',
            'game_files_written':1,'new_native_hooks':0,'weapon_hit_notification_enabled':True,
            'misses_supported':False,'same_journal_row_proven':False,
            'gameplay_verified':False,'backup_path':str(backed),'candidate_sha256':digest(candidate)}


def rollback(game: Path, workdir: Path, approval: str | None = None) -> dict:
    checked_external(game,workdir)
    _game_closed()
    state_path=workdir / STATE_NAME
    state=json.loads(read_file(state_path,20_000))
    if state.get('schema') != SCHEMA or state.get('phase') not in ('PREPARED','INSTALLED'):
        raise SafeStop('V160_NO_ROLLBACKABLE_STATE')
    if state.get('pinned_game_hashes')!=GAME_PINS:
        raise SafeStop('V160_BACKUP_ENVIRONMENT_CHANGED')
    for rel, expected in GAME_PINS.items():
        if digest(read_file(game / rel)) != expected:
            raise SafeStop('ROLLBACK_GAME_BASELINE_DRIFT:'+rel)
    target = game / MODULE_REL
    current_sha = digest(read_file(target,100_000))
    if current_sha not in (state.get('original_sha256'),state.get('candidate_sha256')):
        raise SafeStop('ROLLBACK_NOT_LAST_CHANGE')
    backup = Path(state['backup'])
    if workdir.resolve() not in backup.resolve().parents or game.resolve() in backup.resolve().parents:
        raise SafeStop('ROLLBACK_BACKUP_OUTSIDE_ALLOWED_DIR')
    original = read_file(backup,100_000)
    if digest(original) != state.get('original_sha256'):
        raise SafeStop('ROLLBACK_BACKUP_SHA_HOLD')
    _game_closed()
    entered = approval if approval is not None else input('Type '+APPROVE_ROLLBACK+' to rollback (Enter cancels): ')
    if entered != APPROVE_ROLLBACK:
        raise SafeStop('ROLLBACK_TYPED_APPROVAL_NOT_GIVEN')
    if digest(read_file(target,100_000)) != current_sha:
        raise SafeStop('ROLLBACK_LIVE_MODULE_DRIFT')
    changed = current_sha != state['original_sha256']
    if changed:
        stage=target.with_name(target.name+'.v160.restore')
        if stage.exists() or stage.is_symlink():
            raise SafeStop('ROLLBACK_STAGE_COLLISION')
        try:
            with stage.open('xb') as f:f.write(original)
            if digest(read_file(stage,100_000)) != digest(original):
                raise SafeStop('ROLLBACK_STAGE_SHA_FAILED')
            os.replace(stage,target)
            if digest(read_file(target,100_000)) != digest(original):
                raise SafeStop('ROLLBACK_POST_SHA_FAILED')
        finally:
            if stage.exists():stage.unlink()
    state['phase']='ROLLED_BACK'
    replace_state(state_path,state)
    return {'schema':SCHEMA,'status':'V160_ROLLED_BACK',
            'game_files_written':int(changed),'gameplay_verified':False}


def run(mode: str, game: Path, workdir: Path, addition: bytes | None = None, approval: str | None = None) -> dict:
    game,workdir=Path(game).resolve(),Path(workdir).resolve()
    try:
        if mode=='status': return _status(game,workdir)
        if mode=='preflight':return _preflight(game,workdir)[0]
        if mode=='install':
            if addition is None:
                raise SafeStop('PINNED_LUA_BYTES_MUST_BE_SUPPLIED_BY_ONEFILE_DOWNLOADER')
            return install(game,workdir,addition,approval)
        if mode=='rollback':return rollback(game,workdir,approval)
        raise SafeStop('UNKNOWN_MODE')
    except (SafeStop,OSError,ValueError,TypeError,KeyError,EOFError) as exc:
        return {'schema':SCHEMA, 'status':'V160_SAFE_STOP',
                'reason':type(exc).__name__+': '+str(exc)[:180],
                'game_files_written':'UNKNOWN_AFTER_EXCEPTION' if mode in ('install','rollback') else 0,
                'gameplay_verified':False,'misses_supported':False}

if __name__=='__main__':
    print('SOURCE ONLY: import run() from the existing one-file updater; do not run separately.')