# -*- coding: utf-8 -*-
"""SOURCE-ONLY continuation of installed V162 weapon-name catalog.

No CLI, no standalone updater and no implicit game writes. This deliberately
DOES NOT modify V162's module, state JSON or rollback receipt. A future pinned
revision of the *same* BG_EET_RU_UPDATE.cmd would be the sole caller, only
once the existing Windows/Linux tests and release contract are proved.

Preflight reads the real current game with R3+V111-derived catalog. Install
and rollback require exact typed consent and return safely on any mismatch.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re

SCHEMA = 'BG_EET_RU_WEAPON_NAMES_CUMULATIVE_SOURCE_ONLY_V1'
FIRST_STATE = 'BG_EET_RU_WEAPON_NAMES_BATCH_STATE.json'  # immutable V162 state
SECOND_STATE = 'BG_EET_RU_WEAPON_NAMES_CUMULATIVE_STATE.json'
MODULE_REL = 'EEex_scripts/BG_EET_RU_WeaponObserver.lua'
FIRST_STATE_SCHEMA = 'BG_EET_RU_WEAPON_NAMES_BATCH_SOURCE_ONLY_V1'
EXPECTED_FIRST_STATE_SHA = '741c8dd114c281d6cbff9586f8ffd2de33e89b6e47c772c310c6ce1bfb895766'
EXPECTED_V160_BASELINE_SHA = '386980c6c20f36a50ad4c667a2155c8603588651538ebb5484e65913254ecc33'
EXPECTED_FIRST_INSTALLED_SHA = 'a2e79fab744bcd8f66260d90a5a5cfd66e7ef0f05acb538505008820991e453f'
APPROVE_INSTALL = 'INSTALL_BG_EET_RU_CUMULATIVE_NAMES'
APPROVE_ROLLBACK = 'ROLLBACK_BG_EET_RU_CUMULATIVE_NAMES'
MAX_NEXT = 64
MAX_STATE = 30000
MAX_MODULE = 100000
FIRST_COUNT = 64
SHA_RE = re.compile(r'[0-9a-f]{64}\Z')
REF_RE = re.compile(r'[A-Z0-9_]{1,8}\Z')
NAME_RE = re.compile(r'[А-Яа-яЁёA-Za-z0-9 +,.()\-/]{1,90}\Z')

# Selected ONLY from pre-existing archived ITM+RU TLK, excluding effects,
# dummy attack objects and the first 64. Historical names are NEVER used to
# fill a live catalog; R3+V111 must verify current ITM+both current RU TLKs.
HISTORICAL_SECOND_SEEDS_64 = (
    'BDAROW02','BDASDAG1','BDAX1H01','BDAX1H05','BDBULL02','BDGOGH02','BDGOGH2A','BDOGRE03',
    'BDSHSTF1','BDSKGR05','BDSW1H26','BLCKSWD','CBSBMLTM','CDQBOW','CDQSLING','CDQXBOW',
    'CDRDAGG','EHDAG','FGIANT1','FLIND1','GODBOW','HGNYA01','HGWRA01','JARDAG',
    'NPSW02','OHBDORMA','RANAX','RANBSWD','RITDAGG','SW1H02','TTAXE1','TTDAGG1',
    'TTSWOR10','TTSWORD3','TTSWORD4','TTSWORD5','TTSWORD6','TTSWORD7','TTSWORD8','TTSWORD9',
    'XSTAFHMG','XUSSWD3','XVARTIL','XVARTW','Z0CWAXEA','Z0CWAXEE','Z0CWBOWA','Z0CWBOWD',
    'Z0CWBOWG','Z0CWBOWJ','Z0CWBOWK','Z0CWBOWL','Z0CWDAGA','Z0CWDAGB','Z0CWDAGC',
    'Z0CWDAGE','Z0CWFOR3','Z0CWRDE1','Z0CWSHE0','Z0CWSLG1','Z0CWSTAA','Z0CWSTAC',
    'Z0CWSWDM','Z0SWDL09',
)


class Hold(RuntimeError):
    pass


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _validate_path(game: Path, workdir: Path, batch) -> tuple[Path, Path]:
    game = Path(game)
    workdir = Path(workdir)
    batch._secure_workdir(game, workdir)
    if game.is_symlink() or workdir.is_symlink() or not game.is_dir() or not workdir.is_dir():
        raise Hold('GAME_OR_EXTERNAL_WORKDIR_MISSING')
    # Ensure no path outside approved directories is ever used.
    game = game.resolve(strict=True)
    workdir = workdir.resolve(strict=True)
    return game, workdir


def _read_first_state(game: Path, workdir: Path, batch) -> tuple[dict, bytes]:
    p = workdir / FIRST_STATE
    raw = batch.read_file(p, MAX_STATE)
    if _sha(raw) != EXPECTED_FIRST_STATE_SHA:
        raise Hold('FIRST_V162_STATE_SHA_CHANGED')
    state = json.loads(raw)
    if state.get('schema') != FIRST_STATE_SCHEMA or state.get('phase') != 'INSTALLED' \
            or state.get('baselineSha') != EXPECTED_V160_BASELINE_SHA \
            or state.get('candidateSha') != EXPECTED_FIRST_INSTALLED_SHA:
        raise Hold('FIRST_V162_STATE_NOT_INSTALLED_OR_DRIFT')
    items = state.get('itemPins')
    if not isinstance(items, dict) or len(items) != FIRST_COUNT:
        raise Hold('FIRST_V162_64_ITEMS_MISSING')
    for ref, row in items.items():
        if not isinstance(ref, str) or not REF_RE.fullmatch(ref) \
                or not isinstance(row, dict) or set(row) != {'name','origin','sha256'} \
                or row['origin'] not in ('CURRENT_GAME_OVERRIDE','CURRENT_GAME_BIFF') \
                or not isinstance(row['sha256'], str) or not SHA_RE.fullmatch(row['sha256']) \
                or not isinstance(row['name'], str) or not NAME_RE.fullmatch(row['name']):
            raise Hold('FIRST_V162_ITEM_PIN_INVALID')
    tlks = state.get('tlkSha256')
    if not isinstance(tlks, dict) or set(tlks) != {'dialog.tlk','dialogf.tlk'} \
            or any(not isinstance(sha, str) or not SHA_RE.fullmatch(sha) for sha in tlks.values()):
        raise Hold('FIRST_V162_TLK_PINS_INVALID')
    pins = state.get('gamePins')
    if not isinstance(pins, dict) or len(pins) < 5 \
            or any(not isinstance(k, str) or not k or Path(k).is_absolute() \
                   or '\\' in k or ':' in k or '..' in Path(k).parts
                   or not isinstance(v, str) or not SHA_RE.fullmatch(v) for k,v in pins.items()):
        raise Hold('FIRST_V162_GAME_PINS_INVALID')
    if pins.get('lang/ru_RU/dialog.tlk') != tlks['dialog.tlk'] \
            or pins.get('lang/ru_RU/dialogf.tlk') != tlks['dialogf.tlk']:
        raise Hold('FIRST_V162_TLK_GAME_PINS_DISAGREE')
    if not isinstance(state.get('weiduSha'), str) or not SHA_RE.fullmatch(state['weiduSha']):
        raise Hold('FIRST_V162_WEIDU_PIN_MISSING')
    # The V160 backup of the already deployed first batch must still exist.
    backup = Path(state.get('backup', ''))
    resolved_workdir = workdir.resolve(strict=True)
    if backup.is_symlink() or not backup.is_file() \
            or resolved_workdir not in backup.resolve(strict=True).parents \
            or batch.file_sha(backup, MAX_MODULE) != EXPECTED_V160_BASELINE_SHA:
        raise Hold('FIRST_V162_EXTERNAL_BACKUP_MISSING_OR_CHANGED')
    return state, raw


def _line(ref: str, name: str) -> bytes:
    if not isinstance(ref, str) or not REF_RE.fullmatch(ref) \
            or not isinstance(name, str) or not NAME_RE.fullmatch(name) \
            or not re.search(r'[А-Яа-яЁё]', name) or len(name.encode('utf8')) > 180:
        raise Hold('UNSAFE_RESREF_OR_RU_NAME')
    return f"    {ref}='{name}',\n".encode('utf8')


def compose_next(previous: bytes, previous_state: dict, new_entries: dict, batch) -> bytes:
    """Byte-for-byte preserve V160+first64, adding only confirmed new lines."""
    if not isinstance(previous, bytes) or len(previous) > MAX_MODULE \
            or _sha(previous) != EXPECTED_FIRST_INSTALLED_SHA:
        raise Hold('FIRST_INSTALLED_LUA_SHA_DRIFT')
    if not isinstance(previous_state, dict) or not isinstance(previous_state.get('itemPins'), dict) \
            or len(previous_state['itemPins']) != FIRST_COUNT:
        raise Hold('FIRST_STATE_ITEMS_NOT_READY')
    if not isinstance(new_entries, dict) or not 1 <= len(new_entries) <= MAX_NEXT:
        raise Hold('SECOND_BATCH_COUNT_UNSAFE')
    old = batch.OLD_NAMES.encode('utf8')
    end = batch.END_NAMES.encode('utf8')
    expected_first = old + b''.join(_line(k,row['name']) for k,row in sorted(previous_state['itemPins'].items())) + end
    if previous.count(expected_first) != 1 or previous.count(b'BG_EET_RU_V160_names') != 2 \
            or previous.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(') > 1:
        raise Hold('INSTALLED_FIRST_TABLE_DOES_NOT_MATCH_RECEIPT')
    for ref, row in new_entries.items():
        if ref in previous_state['itemPins'] or ref in ('SW1H04','AROW01','BOW05'):
            raise Hold('REDEFINE_OLD_OR_FIRST64_NAME:' + ref)
        if not isinstance(row, dict) or set(row) != {'name','sha256','origin'} \
                or row['origin'] not in ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE') \
                or not isinstance(row['sha256'],str) or not SHA_RE.fullmatch(row['sha256']):
            raise Hold('NEW_NAME_UNVERIFIED')
    additions = b''.join(_line(ref,row['name']) for ref,row in sorted(new_entries.items()))
    extended = expected_first[:-len(end)] + additions + end
    candidate = previous.replace(expected_first, extended, 1)
    if candidate == previous or not 1 <= len(candidate) <= MAX_MODULE \
            or candidate.replace(extended, expected_first, 1) != previous \
            or candidate.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(') != previous.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener('):
        raise Hold('ONLY_ADD_LINES_OR_NATIVE_HOOK_INVARIANT_FAILED')
    return candidate


def _verify_item(get_item, ref: str, pin: dict, batch):
    if not hasattr(get_item,'get'):
        raise Hold('R3_SOURCE_RESOLVER_MISSING')
    raw, provenance = get_item.get(ref,'.ITM')
    if not isinstance(raw,bytes) or not isinstance(provenance,dict) \
            or _sha(raw) != pin['sha256'] or provenance.get('origin') != pin['origin']:
        raise Hold('CURRENT_GAME_ITM_SHA_OR_ORIGIN_CHANGED:' + ref)


def _verify_pins(game: Path, state: dict, batch):
    for rel, expected in state['gamePins'].items():
        if batch.file_sha(game / rel) != expected:
            raise Hold('FIRST_GAME_PIN_DRIFT:' + rel)
    if batch.file_sha(game / 'WeiDU.log',10_000_000) != state['weiduSha']:
        raise Hold('FIRST_WEIDU_LOG_CHANGED')


def preflight(game: Path, workdir: Path, catalog: dict, get_item, batch) -> tuple[dict,bytes,dict,bytes]:
    game, workdir = _validate_path(game,workdir,batch)
    if (workdir/SECOND_STATE).exists() or (workdir/SECOND_STATE).is_symlink():
        raise Hold('SECOND_STATE_ALREADY_EXISTS_NO_REPEAT')
    batch._check_game_closed()
    first, first_raw = _read_first_state(game,workdir,batch)
    _verify_pins(game,first,batch)
    if (game/MODULE_REL).parent.is_symlink():
        raise Hold('LUA_OVERRIDE_DIRECTORY_SYMLINK')
    previous = batch.read_file(game/MODULE_REL,MAX_MODULE)
    if _sha(previous) != EXPECTED_FIRST_INSTALLED_SHA:
        raise Hold('CURRENT_GAME_LUA_NOT_FIRST64')
    names = batch.validate_catalog(catalog)  # proven current RU TLK + both identification states
    if set(names['tlkSha256']) != set(first['tlkSha256']) \
            or names['tlkSha256'] != first['tlkSha256']:
        raise Hold('CURRENT_TLK_DRIFT_VS_FIRST64')
    if set(names['entries']) & set(first['itemPins']):
        raise Hold('NEW_BATCH_REPEATS_FIRST64')
    if not set(names['entries']).issubset(HISTORICAL_SECOND_SEEDS_64):
        raise Hold('UNPLANNED_NEW_RESOURCE_NOT_IN_APPROVED_HISTORICAL_SEEDS')
    for ref,pin in first['itemPins'].items():
        _verify_item(get_item,ref,pin,batch)
    for ref,pin in names['entries'].items():
        _verify_item(get_item,ref,pin,batch)
    candidate = compose_next(previous, first, names['entries'],batch)
    report = {'schema':SCHEMA,'status':'CUMULATIVE_PREFLIGHT_PASS',
              'gameFilesWritten':0,'oldCount':FIRST_COUNT,'newCount':len(names['entries']),
              'totalExtendedNames':FIRST_COUNT+len(names['entries']),
              'nameResrefs':sorted(names['entries']),'baselineSha':_sha(previous),
              'candidateSha':_sha(candidate),'firstStateSha':_sha(first_raw),
              'tlkSha256':first['tlkSha256'],'weiduSha':first['weiduSha']}
    return report,candidate,first,first_raw


def _write_state_new(path:Path,record:dict,batch):
    if path.exists() or path.is_symlink():raise Hold('CUMULATIVE_STATE_ALREADY_EXISTS')
    raw=json.dumps(record,ensure_ascii=False,indent=2,sort_keys=True).encode('utf8')
    with path.open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    if batch.read_file(path,MAX_STATE)!=raw:raise Hold('EXTERNAL_CUMULATIVE_STATE_VERIFY_FAILED')


def _finish_state(path:Path,record:dict,batch):
    stage=path.with_suffix('.next')
    if stage.exists() or stage.is_symlink():raise Hold('CUMULATIVE_STATE_STAGE_COLLISION')
    raw=json.dumps(record,ensure_ascii=False,indent=2,sort_keys=True).encode('utf8')
    try:
        with stage.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        if batch.read_file(stage,MAX_STATE)!=raw:raise Hold('CUMULATIVE_STAGE_STATE_NOT_STABLE')
        os.replace(stage,path)
    finally:
        if stage.exists():stage.unlink()


def _restore_backup(workdir:Path,state:dict,batch)->bytes:
    candidate=Path(state.get('backup',''))
    if candidate.is_symlink() or not candidate.is_file() \
            or workdir.resolve(strict=True) not in candidate.resolve(strict=True).parents:
        raise Hold('CUMULATIVE_BACKUP_NOT_EXTERNAL_OR_MISSING')
    original=batch.read_file(candidate,MAX_MODULE)
    if _sha(original)!=EXPECTED_FIRST_INSTALLED_SHA or _sha(original)!=state.get('baselineSha'):
        raise Hold('CUMULATIVE_BACKUP_SHA_DRIFT')
    return original


def run(mode:str,game:Path,workdir:Path,batch,
        catalog:dict|None=None,get_item=None,typed:str|None=None,
        allow_non_windows_test:bool=False)->dict:
    """Guarded SOURCE model; never dispatch directly or modify any V162 receipt."""
    try:
        game,workdir=_validate_path(game,workdir,batch)
        state_path=workdir/SECOND_STATE
        if mode=='status':
            if not state_path.exists():
                return {'schema':SCHEMA,'status':'CUMULATIVE_NOT_INSTALLED','gameFilesWritten':0}
            state=json.loads(batch.read_file(state_path,MAX_STATE))
            live=batch.file_sha(game/MODULE_REL,MAX_MODULE)
            status='CUMULATIVE_INSTALLED_AWAITING_GAMEPLAY' if state.get('phase')=='INSTALLED' and live==state.get('candidateSha') else 'CUMULATIVE_STATE_HOLD'
            return {'schema':SCHEMA,'status':status,'gameFilesWritten':0}
        if mode in ('preflight','install'):
            if catalog is None or get_item is None:raise Hold('CURRENT_CATALOG_AND_R3_REQUIRED')
            report,candidate,first,first_raw=preflight(game,workdir,catalog,get_item,batch)
            if mode=='preflight':return report
            if os.name!='nt' and not allow_non_windows_test:raise Hold('WINDOWS_ONLY_TYPED_GAME_CHANGE')
            if typed != APPROVE_INSTALL:raise Hold('EXACT_CUMULATIVE_INSTALL_WORD_REQUIRED')
            batch._check_game_closed()
            # After typed approval revalidate all proofs; prevent race or newer mods.
            report2,candidate2,first2,first_raw2=preflight(game,workdir,catalog,get_item,batch)
            if candidate2!=candidate or first_raw2!=first_raw or report2!=report:
                raise Hold('CUMULATIVE_PREFLIGHT_CHANGED_DURING_CONFIRMATION')
            backup_root=workdir/'BG_EET_RU_V160_SAFE_BACKUP'
            if backup_root.is_symlink() or (backup_root.exists() and not backup_root.is_dir()):
                raise Hold('EXTERNAL_BACKUP_ROOT_UNSAFE')
            backup_root.mkdir(parents=True,exist_ok=True)
            folder=backup_root/('CumulativeNames_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
            folder.mkdir(exist_ok=False)
            backup=folder/'BG_EET_RU_WeaponObserver.lua.first64.before'
            previous=batch.read_file(game/MODULE_REL,MAX_MODULE)
            if _sha(previous)!=EXPECTED_FIRST_INSTALLED_SHA:raise Hold('FIRST64_CHANGED_BEFORE_BACKUP')
            with backup.open('xb') as f:
                f.write(previous);f.flush();os.fsync(f.fileno())
            if batch.read_file(backup,MAX_MODULE)!=previous:raise Hold('CUMULATIVE_BACKUP_VERIFY_FAILED')
            record={'schema':SCHEMA,'phase':'PREPARED','baselineSha':_sha(previous),
                    'candidateSha':_sha(candidate),'firstStateSha':_sha(first_raw),
                    'weiduSha':first['weiduSha'],'gamePins':first['gamePins'],
                    'tlkSha256':first['tlkSha256'],'itemPins':{**first['itemPins'],**batch.validate_catalog(catalog)['entries']},
                    'newNameResrefs':report['nameResrefs'],'backup':str(backup),
                    'createdUtc':dt.datetime.now(dt.timezone.utc).isoformat()}
            _write_state_new(state_path,record,batch)
            target=game/MODULE_REL
            staged=target.with_name(target.name+'.cumulative.stage')
            if staged.exists() or staged.is_symlink():raise Hold('CUMULATIVE_GAME_STAGE_COLLISION')
            try:
                with staged.open('xb') as f:f.write(candidate);f.flush();os.fsync(f.fileno())
                if batch.read_file(staged,MAX_MODULE)!=candidate or batch.file_sha(target,MAX_MODULE)!=report['baselineSha']:
                    raise Hold('CUMULATIVE_STAGE_OR_BASELINE_DRIFT')
                _verify_pins(game,first,batch)
                for ref,pin in record['itemPins'].items():
                    _verify_item(get_item,ref,pin,batch)
                if _sha(batch.read_file(workdir/FIRST_STATE,MAX_STATE))!=EXPECTED_FIRST_STATE_SHA:
                    raise Hold('FIRST_STATE_CHANGED_BEFORE_SWAP')
                os.replace(staged,target)
                if batch.file_sha(target,MAX_MODULE)!=report['candidateSha']:
                    raise Hold('POST_CUMULATIVE_INSTALL_SHA_MISMATCH')
                record['phase']='INSTALLED'
                _finish_state(state_path,record,batch)
            finally:
                if staged.exists():staged.unlink()
            return {'schema':SCHEMA,'status':'CUMULATIVE_INSTALLED_AWAITING_GAMEPLAY',
                    'gameFilesWritten':1,'newNamesAdded':report['newCount'],
                    'retainedPriorNames':FIRST_COUNT,'newNativeHooks':0}
        if mode=='rollback':
            if os.name!='nt' and not allow_non_windows_test:raise Hold('WINDOWS_ONLY_TYPED_GAME_CHANGE')
            batch._check_game_closed()
            # Only the most recent cumulative layer is eligible for rollback.
            first,first_raw=_read_first_state(game,workdir,batch)
            state=json.loads(batch.read_file(state_path,MAX_STATE))
            if state.get('schema')!=SCHEMA or state.get('phase') not in ('PREPARED','INSTALLED') \
                    or state.get('baselineSha')!=EXPECTED_FIRST_INSTALLED_SHA \
                    or state.get('firstStateSha')!=_sha(first_raw) \
                    or not isinstance(state.get('candidateSha'),str) or not SHA_RE.fullmatch(state['candidateSha']) \
                    or state.get('gamePins')!=first['gamePins'] or state.get('weiduSha')!=first['weiduSha']:
                raise Hold('CUMULATIVE_ROLLBACK_RECEIPT_DRIFT')
            original=_restore_backup(workdir,state,batch)
            target=game/MODULE_REL
            current=batch.file_sha(target,MAX_MODULE)
            if state['phase']=='INSTALLED' and current!=state['candidateSha']:
                raise Hold('CUMULATIVE_NOT_LAST_MODIFICATION')
            if state['phase']=='PREPARED' and current not in (state['candidateSha'],EXPECTED_FIRST_INSTALLED_SHA):
                raise Hold('CUMULATIVE_PREPARED_UNEXPECTED_GAME_FILE')
            _verify_pins(game,first,batch)
            if typed!=APPROVE_ROLLBACK:raise Hold('CUMULATIVE_ROLLBACK_APPROVAL_REQUIRED')
            if batch.file_sha(target,MAX_MODULE)!=current:raise Hold('CUMULATIVE_TARGET_CHANGED_DURING_APPROVAL')
            change=current!=EXPECTED_FIRST_INSTALLED_SHA
            stage=target.with_name(target.name+'.cumulative.restore')
            if stage.exists() or stage.is_symlink():raise Hold('CUMULATIVE_RESTORE_STAGE_COLLISION')
            try:
                if change:
                    with stage.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
                    if batch.read_file(stage,MAX_MODULE)!=original:raise Hold('CUMULATIVE_RESTORE_BACKUP_BYTES_MISMATCH')
                    os.replace(stage,target)
                    if batch.file_sha(target,MAX_MODULE)!=EXPECTED_FIRST_INSTALLED_SHA:
                        raise Hold('CUMULATIVE_ROLLBACK_POST_SHA_MISMATCH')
                state['phase']='ROLLED_BACK'
                _finish_state(state_path,state,batch)
            finally:
                if stage.exists():stage.unlink()
            return {'schema':SCHEMA,'status':'CUMULATIVE_ROLLED_BACK_TO_FIRST64',
                    'gameFilesWritten':int(change),'original64Preserved':True}
        raise Hold('UNKNOWN_CUMULATIVE_MODE')
    except (Hold,OSError,ValueError,TypeError,KeyError,AttributeError,json.JSONDecodeError) as exc:
        return {'schema':SCHEMA,'status':'CUMULATIVE_SAFE_STOP',
                'reason':type(exc).__name__+': '+str(exc)[:155],
                'gameFilesWritten':0 if mode in ('status','preflight') else 'UNKNOWN_AFTER_EXCEPTION'}

if __name__=='__main__':
    raise SystemExit('SOURCE_ONLY: only the existing BG_EET_RU_UPDATE.cmd may import this')