"""BG_EET_RU V153: exact-UI observer guarded pilot, one-updater module.

No writes into game on import, status or preflight. Two game-file writes are
possible only after an exact typed install acknowledgement and external backup.
Direct SHA-last-only file patch, NOT a native WeiDU component; refuses rollback
if WeiDU.LOG or either target changed after installation.
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ORIG_SHA = 'bf78a54b77959ca8a47afe9d3c13da30340e1353cb7f77ebfc3a4959bbc240ac'
PATCH_SHA = 'ce4a46cf32058295c221b9124916f46764780752f9611adc8319c4dda9653efe'
SIDE_SHA = 'deffadc9fa9a0b0b9040127fa30abce2808833532618e4d9e7db7ed98c17d93b'
SIDE_URL = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/43de0daa510cb1e6c5b2a4feab5ba7b65d0876c6/bg-eet-ru/ui-observer/v153/BGCL150.lua'
INSTALL_WORD = 'INSTALL_BG_EET_RU_V153_OBSERVER_EXACT_UI'
ROLLBACK_WORD = 'ROLLBACK_BG_EET_RU_V153_OBSERVER_EXACT_UI'
BKP_NAME = 'BG_EET_RU_V153_OBSERVER_BACKUP'
SIDE_FILE = 'BGCL150.lua'
LOAD_LINE = b'pcall(function() Infinity_DoFile("BGCL150") end)'
HOOK_LINE = b'  if type(BG_EET_RU_V150_Poll)=="function" then pcall(BG_EET_RU_V150_Poll, combatLog) end'
INIT = b'combatLog = {}'
ROW_FUNC = b'function BG_EET_RU_V126_RowRecord(row,value)'
RETURN = b'  return value -- identical display value, no text modifications'
RENDER = b'text lua "BG_EET_RU_V126_RowRecord(rowNumber, BG_EET_RU_LogView(clean(combatLog[rowNumber])))"'
TOGGLE = b"name 'BG_EET_RU_JOURNAL_TOGGLE'"

class Hold(RuntimeError): pass

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def file_sha(p:Path)->str:return sha(p.read_bytes())

def _find_one(parent:Path,name:str,required:bool=True):
    if not parent.is_dir() or parent.is_symlink():raise Hold('NONLOCAL_DIRECTORY_HOLD')
    hits=[x for x in parent.iterdir() if x.name.casefold()==name.casefold()]
    if len(hits)!=1:
        if len(hits)==0 and not required:return None
        raise Hold('FILE_MISSING_OR_CASE_AMBIGUOUS_'+name)
    p=hits[0]
    if p.is_symlink() or not p.is_file() or p.resolve(strict=True).parent!=parent.resolve(strict=True):
        raise Hold('FILE_SYMLINK_NONREGULAR_OR_NONLOCAL_'+name)
    return p

def _exact_ui(root:Path):
    override=root/'override'
    p=_find_one(override,'UI.MENU')
    a=p.stat()
    if a.st_size<1 or a.st_size>3*1024*1024:raise Hold('UI_SIZE_LIMIT_HOLD')
    raw=p.read_bytes()
    b=p.stat()
    if len(raw)!=a.st_size or (a.st_ino,a.st_size,a.st_mtime_ns)!=(b.st_ino,b.st_size,b.st_mtime_ns):
        raise Hold('UI_CHANGED_DURING_READ_HOLD')
    return p,raw

def patch(raw:bytes):
    if sha(raw)!=ORIG_SHA:raise Hold('EXACT_UI_SHA_DRIFT')
    if b'BGCL150' in raw or b'BG_EET_RU_V150_Poll' in raw:raise Hold('OBSERVER_ALREADY_PRESENT')
    for k,v in [('init',INIT),('function',ROW_FUNC),('return',RETURN),('render',RENDER),('toggle',TOGGLE),
                ('world',b"name 'WORLD_MESSAGES'"),('list',b'table "combatLog"')]:
        if raw.count(v)!=1:raise Hold('ANCHOR_NOT_UNIQUE_'+k.upper())
    i=raw.index(INIT);f=raw.index(ROW_FUNC);r=raw.index(RETURN);e=raw.index(RENDER)
    if not(i<f<r<e and r-f<=2100):raise Hold('ANCHOR_ORDER_OR_SCOPE_HOLD')
    def end(at):
        n=raw.find(b'\n',at)
        if n<0:raise Hold('ANCHOR_LINE_NOT_TERMINATED')
        return n+1, b'\r\n' if n and raw[n-1]==13 else b'\n'
    iend,ie=end(i);rend,re=end(r)
    if rend>e:raise Hold('ROW_SCOPE_HOLD')
    patched=raw[:iend]+LOAD_LINE+ie+raw[iend:r]+HOOK_LINE+re+raw[r:]
    if sha(patched)!=PATCH_SHA:raise Hold('PATCH_GOLDEN_SHA_MISMATCH')
    if patched.replace(LOAD_LINE+ie,b'',1).replace(HOOK_LINE+re,b'',1)!=raw:raise Hold('BYTE_EXACT_ROLLBACK_FAILURE')
    return patched

def _roots(game,work):
    game=Path(game).resolve(strict=True)
    work=Path(work).resolve(strict=True)
    if not game.is_dir() or game.is_symlink():raise Hold('GAME_PATH_UNSAFE')
    if game==work or game in work.parents or work in game.parents:raise Hold('EXTERNAL_BACKUP_LOCATION_UNSAFE')
    return game,work

def _weidu(game):
    path=_find_one(game,'WeiDU.log')
    raw=path.read_bytes()
    if len(raw)<10 or len(raw)>20*1024*1024:raise Hold('WEIDU_LOG_SIZE_LIMIT')
    return path,raw

def _closed_game():
    if sys.platform!='win32':raise Hold('WINDOWS_ONLY_GAME_CHANGE')
    r=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,timeout=15)
    if r.returncode!=0:raise Hold('PROCESS_LIST_UNAVAILABLE')
    import csv,io
    text=r.stdout.decode('utf8','replace')
    procs=[a[0].strip().lower() for a in csv.reader(io.StringIO(text)) if a]
    if any(p in ('baldur.exe','infinityloader.exe','weidu.exe') or p.startswith('setup-') and p.endswith('.exe') for p in procs):
        raise Hold('GAME_OR_WEIDU_RUNNING_CLOSE_FIRST')

def _sidecar(work,offline=False):
    cache=work/'.BG_EET_RU_AUTOFIX_CACHE'
    if cache.is_symlink():raise Hold('SIDE_SOURCE_CACHE_SYMLINK')
    cache.mkdir(exist_ok=True)
    p=cache/'BGCL150_V153_PINNED.lua'
    if p.is_symlink():raise Hold('SIDE_SOURCE_CACHE_FILE_SYMLINK')
    if p.is_file() and file_sha(p)==SIDE_SHA:return p.read_bytes()
    if offline:raise Hold('SIDE_SOURCE_OFFLINE_NOT_CACHED')
    with urllib.request.urlopen(SIDE_URL,timeout=20) as r:data=r.read(15001)
    if len(data)!=7898 or sha(data)!=SIDE_SHA:raise Hold('SIDE_SOURCE_SHA_HOLD')
    _external_atomic(p,data)
    return data

def _external_atomic(p:Path,data:bytes):
    # Only use this for external backup/cache/ledger; not game path.
    if p.is_symlink():raise Hold('EXTERNAL_TARGET_SYMLINK')
    with tempfile.NamedTemporaryFile(dir=str(p.parent),prefix='.v153_',delete=False) as f:
        tmp=Path(f.name)
        try:f.write(data);f.flush();os.fsync(f.fileno())
        except:tmp.unlink(missing_ok=True);raise
    try:os.replace(tmp,p)
    finally:tmp.unlink(missing_ok=True)

def _game_atomic(p:Path,data:bytes):
    # User typed authorization required by caller; check sha again before call.
    with tempfile.NamedTemporaryFile(dir=str(p.parent),prefix='.bg153_',delete=False) as f:
        t=Path(f.name)
        try:f.write(data);f.flush();os.fsync(f.fileno())
        except:t.unlink(missing_ok=True);raise
    try:os.replace(t,p)
    finally:t.unlink(missing_ok=True)

def _backup(game,work):
    b=work/BKP_NAME
    if b.is_symlink():raise Hold('BACKUP_SYMLINK')
    return b

def _read_ledger(b):
    m=b/'manifest.json'
    if b.is_symlink() or m.is_symlink() or not m.is_file():raise Hold('BACKUP_LEDGER_MISSING')
    j=json.loads(m.read_text('utf8'))
    if j.get('schema')!='BG_EET_RU_V153_GUARDED_PILOT_V1':raise Hold('BACKUP_LEDGER_SCHEMA_MISMATCH')
    return j

def _report(status,**kw):
    d=dict(schema='BG_EET_RU_V153_GUARDED_PILOT_V1',status=status,gameplay_verified=False,
           attack_weapon_row_join_verified=False,native_hooks_installed=False,
           weidu_native_component=False,game_files_written_this_action=0,
           installer_type='SHA_GUARDED_DIRECT_FILE_PATCH_NOT_WEIDU',safe_to_install=False)
    d.update(kw)
    return d

def _preflight(game,work,offline=False):
    ui,raw=_exact_ui(game)
    mod=_find_one(ui.parent,SIDE_FILE,False)
    b=_backup(game,work)
    if b.exists():
        j=_read_ledger(b)
        if j.get('game_root')!=str(game):raise Hold('BACKUP_BELONGS_TO_DIFFERENT_GAME')
        if j['state'] in ('PREPARED','INSTALLED'):
            if sha(raw)!=PATCH_SHA and sha(raw)!=ORIG_SHA:raise Hold('CURRENT_UI_CHANGED_AFTER_PREPARED')
            if mod is not None and file_sha(mod)!=SIDE_SHA:raise Hold('SIDECAR_CHANGED_AFTER_PREPARED')
            return _report('V153_ALREADY_PREPARED_OR_INSTALLED_HOLD',backup_state=j['state'],ui_sha256=sha(raw))
        raise Hold('OLDER_BACKUP_EXISTS_REVIEW_REQUIRED')
    if mod is not None:raise Hold('SIDECAR_CONFLICT_NO_OVERWRITE')
    patched=patch(raw)
    _,wraw=_weidu(game)
    side=_sidecar(work,offline)
    if sha(side)!=SIDE_SHA:raise Hold('SIDE_SOURCE_SHA_HOLD')
    return _report('V153_EXACT_PREFLIGHT_PASS_INSTALL_NOT_AUTHORIZED',original_ui_sha256=sha(raw),
                   candidate_ui_sha256=sha(patched),sidecar_sha256=sha(side),weidu_log_sha256=sha(wraw),
                   ui_bytes=len(raw),candidate_bytes=len(patched),sidecar_bytes=len(side),
                   exact_existing_v126_renderer_reused=True,backup_planned_outside_game=str(b),
                   install_requires_typed_confirmation=True)

def _install(game,work,offline=False,input_fn=input,allow_non_windows_test=False):
    pre=_preflight(game,work,offline)
    if pre['status']!='V153_EXACT_PREFLIGHT_PASS_INSTALL_NOT_AUTHORIZED':return pre
    if not allow_non_windows_test:_closed_game()
    if input_fn('Enter exact '+INSTALL_WORD+' (anything else cancels): ').strip()!=INSTALL_WORD:
        return _report('V153_INSTALL_CANCELLED_NO_GAME_WRITES')
    if not allow_non_windows_test:_closed_game()
    ui,raw=_exact_ui(game);patch_bytes=patch(raw)
    side=_sidecar(work,offline)
    if sha(side)!=SIDE_SHA:raise Hold('SIDE_SOURCE_SHA_HOLD')
    weidu_path,weidu_raw=_weidu(game)
    if sha(weidu_raw)!=pre['weidu_log_sha256'] or _find_one(ui.parent,SIDE_FILE,False):
        raise Hold('CHANGED_SINCE_PREFLIGHT')
    b=_backup(game,work)
    b.mkdir(exist_ok=False)
    try:
        with (b/'UI.MENU.original').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        with (b/'WeiDU.log.original').open('xb') as f:f.write(weidu_raw);f.flush();os.fsync(f.fileno())
        j={'schema':'BG_EET_RU_V153_GUARDED_PILOT_V1','state':'PREPARED',
           'game_root':str(game),'ui_name':ui.name,'ui_original_sha256':ORIG_SHA,
           'ui_patched_sha256':PATCH_SHA,'sidecar_sha256':SIDE_SHA,
           'weidu_log_sha256':sha(weidu_raw),'backend':'DIRECT_SHA_LAST_ONLY_NOT_WEIDU'}
        _external_atomic(b/'manifest.json',(json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
        if file_sha(ui)!=ORIG_SHA or _find_one(ui.parent,SIDE_FILE,False):raise Hold('CHANGED_BEFORE_WRITE')
        target=ui.parent/SIDE_FILE
        with target.open('xb') as f:f.write(side);f.flush();os.fsync(f.fileno())
        if file_sha(ui)!=ORIG_SHA:raise Hold('UI_CHANGED_BEFORE_FINAL_REPLACE')
        _game_atomic(ui,patch_bytes)
        if file_sha(ui)!=PATCH_SHA or file_sha(target)!=SIDE_SHA:raise Hold('POSTINSTALL_SHA_HOLD')
        j['state']='INSTALLED'
        _external_atomic(b/'manifest.json',(json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
        return _report('V153_INSTALLED_AWAITING_RUNTIME_TEST',game_files_written_this_action=2,
                       backup_directory=str(b),ui_sha256=PATCH_SHA,sidecar_sha256=SIDE_SHA,
                       last_only_rollback_requires_exact_sha_and_unchanged_weidu=True)
    except Exception as exc:
        return _report('V153_PARTIAL_INSTALL_HOLD_MANUAL_REVIEW',reason=type(exc).__name__+':'+str(exc)[:140],
                       backup_directory=str(b),game_modified_unknown=True)

def _rollback(game,work,input_fn=input,allow_non_windows_test=False):
    b=_backup(game,work)
    j=_read_ledger(b)
    if j.get('game_root')!=str(game) or j['state'] not in ('PREPARED','INSTALLED'):
        raise Hold('LAST_ONLY_BACKUP_NOT_ACTIVE')
    ui,raw=_exact_ui(game)
    original=(b/'UI.MENU.original').read_bytes()
    old_weidu=(b/'WeiDU.log.original').read_bytes()
    if sha(original)!=ORIG_SHA or sha(old_weidu)!=j['weidu_log_sha256']:raise Hold('BACKUP_CONTENT_SHA_DRIFT')
    if ui.name!=j['ui_name'] or sha(raw) not in (ORIG_SHA,PATCH_SHA):raise Hold('LATER_UI_MODIFICATION_ROLLBACK_FORBIDDEN')
    _,actual_weidu=_weidu(game)
    if sha(actual_weidu)!=sha(old_weidu):raise Hold('NEWER_WEIDU_COMPONENT_ROLLBACK_FORBIDDEN')
    side=_find_one(ui.parent,SIDE_FILE,False)
    if side is not None and file_sha(side)!=SIDE_SHA:raise Hold('SIDECAR_EDITED_ROLLBACK_FORBIDDEN')
    if not allow_non_windows_test:_closed_game()
    if input_fn('Enter exact '+ROLLBACK_WORD+' (anything else cancels): ').strip()!=ROLLBACK_WORD:
        return _report('V153_ROLLBACK_CANCELLED_NO_GAME_WRITES')
    if not allow_non_windows_test:_closed_game()
    # Last-only constraints are rechecked immediately before touching live files.
    if file_sha(ui) not in (ORIG_SHA,PATCH_SHA):raise Hold('UI_CHANGED_BEFORE_ROLLBACK')
    if file_sha(_weidu(game)[0])!=sha(old_weidu):raise Hold('WEIDU_CHANGED_BEFORE_ROLLBACK')
    side=_find_one(ui.parent,SIDE_FILE,False)
    if side is not None and file_sha(side)!=SIDE_SHA:raise Hold('SIDECAR_CHANGED_BEFORE_ROLLBACK')
    writes=0
    if file_sha(ui)==PATCH_SHA:
        _game_atomic(ui,original);writes+=1
    if side is not None:side.unlink();writes+=1
    if file_sha(ui)!=ORIG_SHA or _find_one(ui.parent,SIDE_FILE,False) is not None:
        return _report('V153_ROLLBACK_PARTIAL_HOLD',game_files_written_this_action=writes)
    j['state']='ROLLED_BACK'
    _external_atomic(b/'manifest.json',(json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    return _report('V153_ROLLBACK_EXACT_ORIGINAL_RESTORED',game_files_written_this_action=writes,
                   original_ui_sha256=ORIG_SHA,external_backup_preserved=True)

def run(mode,game_root,external_root,offline=False,input_fn=input,allow_non_windows_test=False):
    if mode not in ('preflight','status','install','rollback'):
        return _report('V153_BAD_ACTION_HOLD')
    try:
        game,work=_roots(game_root,external_root)
        if mode=='rollback':return _rollback(game,work,input_fn,allow_non_windows_test)
        if mode=='install':return _install(game,work,offline,input_fn,allow_non_windows_test)
        if mode=='preflight':return _preflight(game,work,offline)
        # Status doesn't fetch sidecar, nor write anywhere.
        ui,raw=_exact_ui(game);side=_find_one(ui.parent,SIDE_FILE,False)
        b=_backup(game,work)
        j=_read_ledger(b) if b.exists() else None
        return _report('V153_STATUS_SOURCE_ONLY',ui_sha256=sha(raw),sidecar_present=side is not None,
                       sidecar_sha256=file_sha(side) if side is not None else None,
                       backup_state=j['state'] if j else None)
    except (Hold,OSError,ValueError,subprocess.SubprocessError) as e:
        return _report('V153_SAFE_STOP_NO_UNAUTHORIZED_WRITE',reason=type(e).__name__+':'+str(e)[:150])
