# -*- coding: utf-8 -*-
"""Guarded one-item dual-RU label pilot: single original V160 callback only.

One-file updater is the ONLY entrypoint. No separate CLI, new hooks, TLK or save
writes. Existing V162 and V163 receipts are immutable. Native bit0 read happens
only in a typed installed pilot and only for the verified AROW01 item.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request

SCHEMA = 'BG_EET_RU_V165_ONE_ITEM_DUAL_NAME_GUARDED_V1'
STATE = 'BG_EET_RU_V165_DUAL_ONE_ITEM_STATE.json'
GAME_REL = 'EEex_scripts/BG_EET_RU_WeaponObserver.lua'
EXPECTED_V163_SHA = 'f5e00e67145fe7b8d4092a44ade20f8b9139c346ffb924298bc4ea247cb87e2e'
EXPECTED_DLL = {
    'EEex.dll': 'b6c7c98804360cb46531db75ab9608e378fd403d60c29c0e29946a60a334276a',
    'LuaBindings.dll': 'ba84c42fb4b045a585ed5cfd38c1dc487bb9d7052d11d5d4fec198f1155b2db7',
}
USER_SEED = 'AROW01' # V111 confirmed different ru names, recheck current both TLKs
APPROVE_INSTALL = 'INSTALL_BG_EET_RU_V165_AROW01_DUAL'
APPROVE_ROLLBACK = 'ROLLBACK_BG_EET_RU_V165_AROW01_DUAL'
MAX_GAME_LUA = 100000
MAX_STATE = 30000
SHA = re.compile(r'[0-9a-f]{64}\Z')
SAFE_RU = re.compile(r'[А-Яа-яЁёA-Za-z0-9 +,.()\-/]{1,90}\Z')


class Hold(RuntimeError): pass


def digest(b):
    return hashlib.sha256(b).hexdigest()


def read(path, limit=MAX_GAME_LUA):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or not 1<=p.stat().st_size<=limit:
        raise Hold('MISSING_SYMLINK_OR_LARGE:'+p.name)
    return p.read_bytes()


def safe_paths(game,workdir):
    game=Path(game);workdir=Path(workdir)
    if game.is_symlink() or workdir.is_symlink() or not (game/'chitin.key').is_file() or not workdir.is_dir():
        raise Hold('GAME_OR_EXTERNAL_WORKDIR_UNSAFE')
    g=game.resolve(strict=True);w=workdir.resolve(strict=True)
    if g==w or g in w.parents or w in g.parents:
        raise Hold('WORKDIR_OVERLAPS_GAME')
    return g,w



def verify_scoped_pins(game,first,second,batch,cumulative,resolver=None,
                       expected_current_weidu=None):
    """Use the V162 exact game pins and V163 123 ITM receipts without
    demanding that today's WeiDU.log equal its months-old install hash.

    Current WeiDU.log is STILL SHA-pinned against approval and final swap.
    The old hash is never overwritten or silently rebaselined.
    If any of the 123 previously installed ITMs or their source drifted,
    fail closed. For rollback, an exact installed WeiDU fingerprint and
    the target's byte-identical SHA guard replace item-source rechecks.
    """
    if not isinstance(first.get('gamePins'),dict) or not first['gamePins']:
        raise Hold('V162_GAME_PINS_MISSING')
    if not isinstance(second.get('itemPins'),dict) or len(second['itemPins'])!=123:
        raise Hold('V163_123_ITEM_PINS_MISSING')
    for rel,expected in first['gamePins'].items():
        if not isinstance(rel,str) or not rel or '\\' in rel or ':' in rel or (
            Path(rel).is_absolute()) or '..' in Path(rel).parts or (
            not isinstance(expected,str) or not SHA.fullmatch(expected)):
            raise Hold('V162_GAME_PIN_FORMAT_INVALID')
        if batch.file_sha(game/rel)!=expected:
            raise Hold('V162_GAME_PIN_DRIFT:'+rel)
    weidu=batch.file_sha(game/'WeiDU.log',10_000_000)
    if expected_current_weidu is not None and weidu!=expected_current_weidu:
        raise Hold('WEIDU_CHANGED_SINCE_V165_PREFLIGHT')
    if resolver is not None:
        for ref,pin in second['itemPins'].items():
            cumulative._verify_item(resolver,ref,pin,batch)
    return {
        'weiduSha256Current':weidu,
        'weiduSha256HistoricalV162':first['weiduSha'],
        'weiduHistoricalDrift':weidu!=first['weiduSha'],
        'all123HistoricalItemPinsRechecked':resolver is not None,
        'priorItemsChecked':len(second['itemPins']) if resolver is not None else 0,
    }

def state_and_pins(game,workdir,batch,cumulative,resolver=None,expected_current_weidu=None):
    first,first_raw=cumulative._read_first_state(game,workdir,batch)
    path=workdir/cumulative.SECOND_STATE
    second=json.loads(read(path,MAX_STATE))
    if second.get('schema')!=cumulative.SCHEMA or second.get('phase')!='INSTALLED' or (
        second.get('baselineSha')!=cumulative.EXPECTED_FIRST_INSTALLED_SHA or
        second.get('firstStateSha')!=digest(first_raw) or
        second.get('candidateSha')!=EXPECTED_V163_SHA or
        second.get('gamePins')!=first.get('gamePins') or
        second.get('weiduSha')!=first.get('weiduSha')):
        raise Hold('V163_RECEIPT_DRIFT')
    if not isinstance(second.get('itemPins'),dict) or len(second['itemPins'])!=123:
        raise Hold('V163_123_ITEM_PINS_MISSING')
    current=read(game/GAME_REL)
    if digest(current)!=EXPECTED_V163_SHA:
        raise Hold('V163_NOT_CURRENT_LAST_MODIFICATION')
    pins=verify_scoped_pins(game,first,second,batch,cumulative,resolver,
                            expected_current_weidu)
    for name,sha in EXPECTED_DLL.items():
        if batch.file_sha(game/name)!=sha: raise Hold('USER_OFFICIAL_EEEX_DLL_DRIFT:'+name)
    return first,second,read(path,MAX_STATE),current,pins


def pairs_from_current(catalog, bridge, expected_tlks):
    result=bridge.dual_russian_names_source_only(catalog)
    if result.get('gameFilesWritten')!=0 or result.get('engineListenersAdded')!=0 or (
        result.get('tlkSha256')!=expected_tlks):
        raise Hold('CURRENT_RU_TLK_SHA_DRIFT')
    item=result.get('pairs',{}).get(USER_SEED)
    if not item or item.get('itmOrigin') not in ('CURRENT_GAME_OVERRIDE','CURRENT_GAME_BIFF') or (
        not isinstance(item.get('itmSha256'),str) or not SHA.fullmatch(item['itmSha256'])):
        raise Hold('AROW01_NOT_CURRENT_TWO_RU_NAMES')
    original=catalog.get('items',{}).get(USER_SEED,{})
    if original.get('itemTypeRaw')!=5 or original.get('resourceSha256')!=item['itmSha256']:
        raise Hold('AROW01_ITEM_TYPE_OR_SHA_HOLD')
    names={k:item[k]['name'] for k in ('identified','unidentified')}
    if any(not SAFE_RU.fullmatch(n) or len(n.encode('utf-8'))>180 for n in names.values()) or (
        names['identified']==names['unidentified']):
        raise Hold('AROW01_NAME_PAIR_UNSAFE')
    return names,item


def compose(existing:bytes,names:dict,v107:bytes):
    if digest(existing)!=EXPECTED_V163_SHA:
        raise Hold('V163_LUA_BASELINE_SHA_MISMATCH')
    if not isinstance(v107,bytes) or not v107.startswith(b'-- BG_EET_RU V107') or (
        b'function BG_EET_RU_V107_ResolveName(ref, item)' not in v107):
        raise Hold('V107_SOURCE_IDENTITY_HOLD')
    a=b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)'
    b=b'BG_EET_RU_V160_name(weapon)'
    c=b'BG_EET_RU_V160_name(launcher)'
    if existing.count(a)!=1 or existing.count(b)!=1 or existing.count(c)!=1 or (
        existing.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(')>1) or (
        b'BG_EET_RU_V165_pick' in existing or b'BG_EET_RU_V107_GUARD' in existing):
        raise Hold('V160_CALLBACK_OR_V163_LUA_DRIFT')
    helper=(b'local function BG_EET_RU_V165_pick(ref,item)\n'
            b' if ref=="AROW01" and type(BG_EET_RU_V107_ResolveName)=="function" then\n'
            b'  local n=BG_EET_RU_V107_ResolveName(ref,item)\n'
            b'  if n then return n end\n'
            b' end\n'
            b' return BG_EET_RU_V160_name(ref)\nend\n')
    candidate=existing.replace(a,helper+a)
    candidate=candidate.replace(b,b'BG_EET_RU_V165_pick(weapon,context.weapon)')
    candidate=candidate.replace(c,b'BG_EET_RU_V165_pick(launcher,context.launcher)')
    def lua_quote(n):return json.dumps(n,ensure_ascii=False).encode('utf-8')
    config=(b'\n-- V165 one-item user-approved bit0 trial, no extra callback/listener.\n'
            b'BG_EET_RU_V107_GUARD.verified_dual_pairs={AROW01={identified='+
            lua_quote(names['identified'])+b',unidentified='+lua_quote(names['unidentified'])+
            b',current_itm_and_tlks_verified=true}}\n')
    for key in ('enabled','native_abi_verified','explicit_native_read_consent',
                'identification_probe_enabled','current_x64_item_flags_binding_verified',
                'callback_citem_flag_lifetime_verified','explicit_identification_read_consent',
                'dual_name_catalog_verified','explicit_dual_name_consent'):
        config+=('BG_EET_RU_V107_GUARD.'+key+'=true\n').encode('ascii')
    candidate+=b'\n'+v107.rstrip()+b'\n'+config
    if not 0<len(candidate)<MAX_GAME_LUA:raise Hold('PILOT_LUA_TOO_LARGE')
    return candidate


def prepare(game,workdir,batch,cumulative,bridge,catalog,resolver,v107):
    first,second,second_raw,existing,pins=state_and_pins(
        game,workdir,batch,cumulative,resolver)
    if not isinstance(catalog,dict) or catalog.get('schema')!='BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1':
        raise Hold('CATALOG_NOT_CURRENT')
    if catalog.get('tlkSha256')!=first['tlkSha256']:
        raise Hold('FIRST64_CURRENT_TLK_DRIFT')
    names,item=pairs_from_current(catalog,bridge,first['tlkSha256'])
    raw,origin=resolver.get(USER_SEED,'.ITM')
    if digest(raw)!=item['itmSha256'] or origin.get('origin')!=item['itmOrigin']:
        raise Hold('AROW01_ITM_CHANGED_AFTER_CATALOG')
    candidate=compose(existing,names,v107)
    report={'schema':SCHEMA,'status':'V165_ONE_ITEM_PREFLIGHT_PASS','gameFilesWritten':0,
            'newNativeHooks':0,'modifiedExistingListenerOnly':True,
            'itemResref':USER_SEED,'names':names,'itmSha256':item['itmSha256'],
            'tlkSha256':first['tlkSha256'],'baselineSha':EXPECTED_V163_SHA,
            'candidateSha':digest(candidate),'externalBackupRequired':True,
            'nativeFlagsRuntimeStillRequiresTypedPilot':True,
            **pins}
    return report,candidate,second,second_raw


def _write_json_new(path,record):
    raw=json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
    if len(raw)>MAX_STATE:raise Hold('V165_STATE_SIZE_EXCEEDED')
    with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    if read(path,MAX_STATE)!=raw:raise Hold('V165_STATE_VERIFY_FAILED')


def run(mode,game,workdir,batch,cumulative,bridge,catalog=None,resolver=None,v107=None,
        typed=None,allow_non_windows_test=False):
    """Only loaded through SAME BG_EET_RU_UPDATE.cmd, never standalone CLI."""
    try:
        g,w=safe_paths(game,workdir)
        state=w/STATE;target=g/GAME_REL
        if mode=='status':
            if not state.exists():return {'schema':SCHEMA,'status':'V165_NOT_INSTALLED','gameFilesWritten':0}
            data=json.loads(read(state,MAX_STATE))
            if data.get('schema')!=SCHEMA:raise Hold('V165_STATE_SCHEMA_INVALID')
            if data.get('phase')=='ROLLED_BACK':
                return {'schema':SCHEMA,'status':'V165_ROLLED_BACK_TO_V163_123','gameFilesWritten':0}
            if data.get('phase')=='PREPARED':
                return {'schema':SCHEMA,'status':'V165_PREPARED_RECOVERY_REQUIRED','gameFilesWritten':0}
            if data.get('phase')!='INSTALLED':raise Hold('V165_STATE_NOT_INSTALLED')
            return {'schema':SCHEMA,'status':'V165_INSTALLED_AWAITING_GAMEPLAY' if digest(read(target))==data.get('candidateSha') else 'V165_SOURCE_DRIFT_HOLD','gameFilesWritten':0}
        if mode in ('preflight','install'):
            if catalog is None or resolver is None or v107 is None:
                raise Hold('CURRENT_CATALOG_AND_PINNED_V107_REQUIRED')
            report,candidate,second,second_raw=prepare(g,w,batch,cumulative,bridge,catalog,resolver,v107)
            if mode=='preflight':return report
            if os.name!='nt' and not allow_non_windows_test:raise Hold('WINDOWS_ONLY_TYPED_GAME_CHANGE')
            if typed!=APPROVE_INSTALL:raise Hold('EXACT_V165_APPROVAL_REQUIRED')
            if state.exists() or state.is_symlink():raise Hold('V165_STATE_ALREADY_EXISTS')
            batch._check_game_closed()
            report2,candidate2,second2,second_raw2=prepare(g,w,batch,cumulative,bridge,catalog,resolver,v107)
            if candidate2!=candidate or second_raw2!=second_raw or report2!=report:
                raise Hold('V165_PREFLIGHT_CHANGED_DURING_CONFIRMATION')
            root=w/'BG_EET_RU_V160_SAFE_BACKUP'
            if root.is_symlink():raise Hold('EXTERNAL_BACKUP_SYMLINK')
            root.mkdir(exist_ok=True)
            folder=root/('DualAROW01_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
            folder.mkdir(exist_ok=False)
            backup=folder/'BG_EET_RU_WeaponObserver.lua.v163'
            previous=read(target)
            if digest(previous)!=EXPECTED_V163_SHA:raise Hold('V163_CHANGED_BEFORE_BACKUP')
            with backup.open('xb') as f:f.write(previous);f.flush();os.fsync(f.fileno())
            if read(backup)!=previous:raise Hold('BACKUP_VERIFY_FAILED')
            record={'schema':SCHEMA,'phase':'PREPARED','baselineSha':EXPECTED_V163_SHA,
                    'weiduSha256Current':report['weiduSha256Current'],
                    'weiduSha256HistoricalV162':report['weiduSha256HistoricalV162'],
                    'candidateSha':report['candidateSha'],'backup':str(backup),
                    'secondStateSha':digest(second_raw),
                    'itemResref':USER_SEED,'itmSha256':report['itmSha256'],
                    'tlkSha256':report['tlkSha256'],'createdUtc':dt.datetime.now(dt.timezone.utc).isoformat()}
            _write_json_new(state,record)
            stage=target.with_name(target.name+'.v165.stage')
            if stage.exists() or stage.is_symlink():raise Hold('V165_STAGE_COLLISION')
            try:
                with stage.open('xb') as f:f.write(candidate);f.flush();os.fsync(f.fileno())
                if read(stage)!=candidate or digest(read(target))!=EXPECTED_V163_SHA:
                    raise Hold('V165_STAGE_OR_BASELINE_DRIFT')
                # Final same-file/tlk/WeiDU and exact AROW01 proof before atomic swap.
                first,second2,second_raw2,_,pins2=state_and_pins(
                    g,w,batch,cumulative,resolver,report['weiduSha256Current'])
                if digest(second_raw2)!=record['secondStateSha']:
                    raise Hold('V163_RECEIPT_CHANGED_BEFORE_SWAP')
                new_raw,new_origin=resolver.get(USER_SEED,'.ITM')
                if digest(new_raw)!=record['itmSha256']:raise Hold('AROW01_CHANGED_BEFORE_SWAP')
                os.replace(stage,target)
                if digest(read(target))!=record['candidateSha']:
                    raise Hold('V165_POST_INSTALL_SHA_MISMATCH')
                record['phase']='INSTALLED'
                new_state=state.with_suffix('.next')
                if new_state.exists() or new_state.is_symlink():raise Hold('V165_STATE_NEXT_COLLISION')
                try:
                    _write_json_new(new_state,record)
                    os.replace(new_state,state)
                finally:
                    if new_state.exists():new_state.unlink()
            finally:
                if stage.exists():stage.unlink()
            return {'schema':SCHEMA,'status':'V165_INSTALLED_AWAITING_GAMEPLAY','gameFilesWritten':1,
                    'changedItems':1,'retainedPriorNames':123,'newNativeHooks':0}
        if mode=='rollback':
            if os.name!='nt' and not allow_non_windows_test:raise Hold('WINDOWS_ONLY_TYPED_GAME_CHANGE')
            batch._check_game_closed()
            if typed!=APPROVE_ROLLBACK:raise Hold('EXACT_V165_ROLLBACK_APPROVAL_REQUIRED')
            record=json.loads(read(state,MAX_STATE))
            if record.get('schema')!=SCHEMA or record.get('phase') not in ('PREPARED','INSTALLED') or (
                record.get('baselineSha')!=EXPECTED_V163_SHA or
                not isinstance(record.get('candidateSha'),str) or not SHA.fullmatch(record['candidateSha'])):
                raise Hold('V165_STATE_INVALID')
            # Only the last installed layer is eligible; never roll back V163.
            current=digest(read(target))
            if record['phase']=='INSTALLED' and current!=record['candidateSha']:
                raise Hold('V165_NOT_LAST_MODIFICATION')
            if record['phase']=='PREPARED' and current not in (EXPECTED_V163_SHA,record['candidateSha']):
                raise Hold('V165_PREPARED_TARGET_DRIFT')
            backup=Path(record.get('backup',''))
            if backup.is_symlink() or not backup.is_file() or (
                w not in backup.resolve(strict=True).parents):
                raise Hold('V165_BACKUP_NOT_EXTERNAL')
            previous=read(backup)
            if digest(previous)!=EXPECTED_V163_SHA:raise Hold('V165_BACKUP_SHA_INVALID')
            first,first_raw=cumulative._read_first_state(g,w,batch)
            second=json.loads(read(w/cumulative.SECOND_STATE,MAX_STATE))
            verify_scoped_pins(g,first,second,batch,cumulative,
                               expected_current_weidu=record.get('weiduSha256Current'))
            for name,sha in EXPECTED_DLL.items():
                if batch.file_sha(g/name)!=sha:raise Hold('V165_ROLLBACK_EEEX_DLL_DRIFT:'+name)
            second_raw=read(w/cumulative.SECOND_STATE,MAX_STATE)
            if digest(second_raw)!=record.get('secondStateSha'):
                raise Hold('V163_RECEIPT_CHANGED_SINCE_PILOT')
            if current==EXPECTED_V163_SHA:
                # A crash before game swap leaves PREPARED state; finalize
                # receipt after typed rollback so a stale PREPARED cannot lock
                # future recovery. V163 bytes remain untouched.
                record['phase']='ROLLED_BACK'
                new=state.with_suffix('.next')
                if new.exists() or new.is_symlink():raise Hold('V165_ROLLBACK_STATE_COLLISION')
                try:
                    _write_json_new(new,record);os.replace(new,state)
                finally:
                    if new.exists():new.unlink()
                return {'schema':SCHEMA,'status':'V165_ROLLED_BACK_TO_V163_123','gameFilesWritten':0}
            stage=target.with_name(target.name+'.v165.restore')
            if stage.exists() or stage.is_symlink():raise Hold('V165_ROLLBACK_STAGE_COLLISION')
            try:
                with stage.open('xb') as f:f.write(previous);f.flush();os.fsync(f.fileno())
                if read(stage)!=previous or digest(read(target))!=current:
                    raise Hold('V165_ROLLBACK_RACE')
                os.replace(stage,target)
                if digest(read(target))!=EXPECTED_V163_SHA:
                    raise Hold('V165_ROLLBACK_VERIFY_FAILED')
            finally:
                if stage.exists():stage.unlink()
            record['phase']='ROLLED_BACK'
            new=state.with_suffix('.next')
            if new.exists() or new.is_symlink():raise Hold('V165_ROLLBACK_STATE_COLLISION')
            try:
                _write_json_new(new,record);os.replace(new,state)
            finally:
                if new.exists():new.unlink()
            return {'schema':SCHEMA,'status':'V165_ROLLED_BACK_TO_V163_123','gameFilesWritten':1}
        raise Hold('INVALID_V165_MODE')
    except Exception as exc:
        return {'schema':SCHEMA,'status':'V165_SAFE_STOP','reason':type(exc).__name__+': '+str(exc)[:155],
                'gameFilesWritten':0 if mode in ('status','preflight') else 'UNKNOWN_AFTER_EXCEPTION'}


# Reuse EXACT V163 V162/R3/V111 chain; these source pins already existed in
# the single onefile updater. This module is invoked ONLY by the same CMD.
V163_DISPATCH_URL = ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'
                     '8ea2895b2e1167e7be8a226367e4b4af37968425/'
                     'bg-eet-ru/hit-only-v160/weapon_names_cumulative_onefile_dispatch.py')
V163_DISPATCH_SHA = 'b24bb80860103f31688d54c9d906b44619e01bcf50be1beb645fe8aa215d7426'
V107_SOURCE_URL = ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'
                   '2685fdf54268c274700a0e0948862d09cad48e9d/'
                   'bg-eet-ru/weapon-identity/BG_EET_RU_V107_GUARDED_CALLBACK_SOURCE_ONLY.lua')
V107_SOURCE_SHA = '335ad3537734a52fd8aed923fe953f8fcda5d6ef54e23586ba90218b95c47d4d'

# PR #129 added the dual-name extractor AFTER the immutable V162 bridge pin.
# V162 must continue to use its original bridge for the 123 installed names.
# Download this verified newer *source-only* bridge separately; never shadow
# the old bridge cache or silently patch the V162 backend.
V167_DUAL_BRIDGE_REF = '4d35d3b7e32b7981865626d098ed816081514c06'
V167_DUAL_BRIDGE_REL = 'bg-eet-ru/weapon-identity/BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py'
V167_DUAL_BRIDGE_SHA = 'f77de7d48adbbd33be8a71e621386d5a72b2a0194d6249e848103b12679aefff'
V167_DUAL_BRIDGE_URL = ('https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'
                        + V167_DUAL_BRIDGE_REF + '/' + V167_DUAL_BRIDGE_REL)


def load_pinned_dual_bridge(cache,offline):
    """Exact source-only PR129 implementation, not V162's pre-PR129 bridge."""
    import types
    raw=_pinned(cache,'V167_DUAL_NAMES_BRIDGE_R3_RO.py',
                V167_DUAL_BRIDGE_URL,V167_DUAL_BRIDGE_SHA,offline)
    if b'def dual_russian_names_source_only(catalog: dict) -> dict:' not in raw:
        raise Hold('V167_PINNED_DUAL_EXTRACTOR_ABSENT')
    dual=types.ModuleType('bg_eet_ru_v167_pinned_real_dual_bridge')
    exec(compile(raw,'V167_DUAL_NAMES_BRIDGE_R3_RO.py','exec'),dual.__dict__)
    if not callable(getattr(dual,'dual_russian_names_source_only',None)):
        raise Hold('V167_DUAL_EXTRACTOR_NOT_CALLABLE')
    return dual




def _pinned(root:Path,relative:str,url:str,expected:str,offline:bool)->bytes:
    if not SHA.fullmatch(expected) or not root.is_dir() or root.is_symlink():
        raise Hold('V165_PIN_OR_EXTERNAL_CACHE_INVALID')
    target=root/relative
    if target.is_symlink() or target.exists() and not target.is_file():
        raise Hold('V165_PINNED_FILE_UNSAFE')
    if target.exists():
        data=read(target,30000)
        if digest(data)!=expected: raise Hold('V165_PINNED_CACHE_CHANGED')
        return data
    if offline: raise Hold('V165_PINNED_CACHE_MISSING_OFFLINE')
    with urllib.request.urlopen(url,timeout=12) as response:
        data=response.read(30001)
    if not data or len(data)>30000 or digest(data)!=expected:
        raise Hold('V165_PINNED_UPSTREAM_SHA_HOLD')
    with tempfile.NamedTemporaryFile(dir=root,prefix='.v165_',delete=False) as f:
        stage=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    try:
        if digest(read(stage,30000))!=expected or target.exists():
            raise Hold('V165_CACHE_RACE_OR_HASH_DRIFT')
        os.replace(stage,target)
    finally:
        if stage.exists():stage.unlink()
    return data


def run_from_onefile(game,workdir,mode='status',offline=False):
    """Single existing BG_EET_RU_UPDATE.cmd owns output ZIP and user menu."""
    try:
        g,w=safe_paths(game,workdir)
        if mode not in ('status','preflight','install','rollback'):
            raise Hold('V165_UNKNOWN_ACTION')
        cache=w/'.BG_EET_RU_AUTOFIX_CACHE'
        if cache.is_symlink():raise Hold('V165_CACHE_SYMLINK')
        cache.mkdir(exist_ok=True)
        v163source=_pinned(cache,'V163_CUMULATIVE_DISPATCH.py',V163_DISPATCH_URL,V163_DISPATCH_SHA,offline)
        import types
        v163=types.ModuleType('v165_reused_v163')
        exec(compile(v163source,'v163_pinned.py','exec'),v163.__dict__)
        base,cumulative=v163._load(cache,offline)
        batch=base._module(base._pinned_source(cache,'batch',offline),'batch')
        if mode=='status':
            return run(mode,g,w,batch,cumulative,None)
        if mode=='rollback':
            word=input('Type '+APPROVE_ROLLBACK+' to restore V163 exactly (Enter cancels): ').strip()
            return run(mode,g,w,batch,cumulative,None,typed=word)
        # Old bridge is embedded in _readonly_catalog(), before PR129.
        # Its published callable never existed; load the newer exact function
        # under an independent immutable SHA pin, without changing old cache.
        catalog,resolver=base._readonly_catalog(cache,g,[USER_SEED],offline)
        dual_bridge=load_pinned_dual_bridge(cache,offline)
        v107=_pinned(cache,'V107_GUARDED_CALLBACK_SOURCE_ONLY.lua',
                      V107_SOURCE_URL,V107_SOURCE_SHA,offline)
        if mode=='preflight':
            return run(mode,g,w,batch,cumulative,dual_bridge,catalog,resolver,v107)
        prior=run('preflight',g,w,batch,cumulative,dual_bridge,catalog,resolver,v107)
        if prior.get('status')!='V165_ONE_ITEM_PREFLIGHT_PASS':
            return prior
        word=input('Type '+APPROVE_INSTALL+' to trial only AROW01 (Enter cancels): ').strip()
        return run('install',g,w,batch,cumulative,dual_bridge,catalog,resolver,v107,typed=word)
    except Exception as exc:
        return {'schema':SCHEMA,'status':'V165_SAFE_STOP',
                'reason':type(exc).__name__+': '+str(exc)[:155],
                'gameFilesWritten':0 if mode in ('status','preflight') else 'UNKNOWN_AFTER_EXCEPTION'}



if __name__=='__main__':
    raise SystemExit('INTERNAL SOURCE: use existing BG_EET_RU_UPDATE.cmd only')
