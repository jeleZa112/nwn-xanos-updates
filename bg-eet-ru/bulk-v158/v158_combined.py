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


# V154 extends the existing V153 guarded module with read-only console capture.
# Captures only outside the game. Does NOT add a Lua hook or edit any game file.
def _v154_parse_console(data:bytes):
    if len(data)>8_000_000:raise Hold('V154_LOG_OVER_8MB')
    raw=[];held=[];old=[]
    for line in data.decode('utf-8','replace').splitlines():
        if 'BG_EET_RU_V150_RAW\t' in line:
            if len(raw)<24:raw.append(line[line.index('BG_EET_RU_V150_RAW\t'):][:1100])
        elif 'BG_EET_RU_V150_HOLD\t' in line:
            if len(held)<24:held.append(line[line.index('BG_EET_RU_V150_HOLD\t'):][:1100])
        elif 'BG_EET_RU_V126_ROW\t' in line:
            if len(old)<8:old.append(line[line.index('BG_EET_RU_V126_ROW\t'):][:1100])
    return {'v150_raw_samples':raw,'v150_hold_samples':held,
            'v126_row_samples':old,'raw_sample_count_capped':len(raw),
            'hold_sample_count_capped':len(held),
            'note':'sample counts capped; runtime counters require explicit Lua access'}

def _v154_capture(game:Path,work:Path,allow_non_windows_test=False):
    ui,raw=_exact_ui(game)
    b=_backup(game,work)
    ledger=_read_ledger(b)
    if ledger.get('state')!='INSTALLED' or ledger.get('game_root')!=str(game):
        raise Hold('V154_V153_LEDGER_NOT_INSTALLED')
    if sha(raw)!=PATCH_SHA or ledger.get('ui_patched_sha256')!=PATCH_SHA:
        raise Hold('V154_V153_UI_SHA_DRIFT')
    side=_find_one(ui.parent,SIDE_FILE)
    if file_sha(side)!=SIDE_SHA or ledger.get('sidecar_sha256')!=SIDE_SHA:
        raise Hold('V154_V153_SIDECAR_SHA_DRIFT')
    _,wei=_weidu(game)
    if sha(wei)!=ledger.get('weidu_log_sha256'):
        raise Hold('V154_WEIDU_CHANGED_AFTER_INSTALL')
    if not allow_non_windows_test:_closed_game()
    exe=_find_one(game,'InfinityLoader.exe')
    if exe.stat().st_size<2 or exe.stat().st_size>70_000_000:
        raise Hold('V154_LOADER_SIZE_HOLD')
    with exe.open('rb') as stream:
        if stream.read(2)!=b'MZ':raise Hold('V154_LOADER_PE_HEADER_HOLD')
    from datetime import datetime,timezone
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    log=work/('BG_EET_RU_V154_CONSOLE_'+stamp+'.log')
    if log.is_symlink() or log.exists():raise Hold('V154_LOG_PATH_COLLISION')
    with log.open('xb') as output:
        process=subprocess.Popen([str(exe)],cwd=str(game),stdin=subprocess.DEVNULL,
                                 stdout=output,stderr=subprocess.STDOUT,close_fds=True)
        exit_code=process.wait()
    size=log.stat().st_size
    if size>8_000_000:
        return _report('V154_LOG_OVERSIZE_HOLD',log_path=str(log),log_bytes=size,game_files_written_this_action=0)
    data=log.read_bytes()
    found=data.count(b'BG_EET_RU_V150_RAW\t')
    held=data.count(b'BG_EET_RU_V150_HOLD\t')
    parsed=_v154_parse_console(data)
    status=('V154_OBSERVER_RAW_CAPTURED' if found else
            'V154_OBSERVER_HOLD_CAPTURED' if held else 'V154_OBSERVER_RUNTIME_UNVERIFIED_HOLD')
    if exit_code!=0:status='V154_LOADER_EXIT_NONZERO_HOLD'
    return _report(status,log_path=str(log),log_sha256=sha(data),log_bytes=len(data),
                   exit_code=exit_code,raw_markers=found,hold_markers=held,
                   v126_row_markers=data.count(b'BG_EET_RU_V126_ROW\t'),
                   runtime_observer_loaded_confirmed=bool(found or held),
                   counters_directly_read=False,game_files_written_this_action=0,**parsed)

def run(mode,game_root,external_root,offline=False,input_fn=input,allow_non_windows_test=False):
    if mode not in ('preflight','status','install','rollback','capture'):
        return _report('V153_BAD_ACTION_HOLD')
    try:
        game,work=_roots(game_root,external_root)
        if mode=='capture':return _v154_capture(game,work,allow_non_windows_test)
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

# V157 additive, one-CMD-only bulk editorial entry. Entire V154 source above is unchanged.
_V154_PRESERVED_RUN=run
_V157_BLOB='eNqtXHmT4kay/78/BXaEH90L20iAEPSYjRA6kAAd6ODymyCELgS60AGIjf3uryRxdjNjO/Y5YrqhjsysrKzMX2ZV+9dff+31lyQpL0WltIcR9KPke8Y/cZYoWYka6oZeWqmxtv4owVDJOKpaXJJHw5Kh23H0LWtbqV5shEVDSeIVESdLND8i3l9eyCPo8VSnFMVqbNRWqrZNAkDeSaulwPY8QDvyk1AzSqs0NqJqyVRt55+a40eG/l7i/JKlukbJtB0jKqmh8aKtVc/KBEpLQWiYjm2t41pGO4neS4wHPjmOGtu+VwqNXWKHYJqdCQeEtvfGWXo1CEJ/rzrvL7/++uuLGfpuabk0kzgJjeWyZLuBH4JBnufHOano5dy0UiOj1ayWtGhfLa3VaO3Yq2rJ9qulTeR71ZIP5I/WSWw74HccJloMficrwEwzoqwvBT9i2zWqpSSx9WrpBAgU/AM1zqhdmAvg68uLhNMki3XL191ZTsDuLHmOXPYwGaeXfQUTCZIAzeUXFuMYipTkZa/V7JYNLoyncLynSb1es5OOKdAje2gnaBLutusmHm7HqNyXxT7p8GvCmsPUDLAOxIW/qvejOc6EbrogLdGf14kRM5onHZfbjgl07FCEbQzGA75nQgI7a2/j9LRzDUZR+P1C9wO9TjEUdkKHzZZuBNre44Nmop2E2Z5odManRV2vVCgkNPfIcNdw4Y7Gh1StUtenswraqkCI3Y5mlBONoqO+omBjz/ltodNR97R8nCZ7Qh/Oj81Gp512korego1FaxKaalKr0f1Qh7iToqVabXbqjwzPOe0nCwOzlcBg3IXmKwvNHkLOhl/3Fgi1Gx8tw9SGk74KbfrJjHXbrIMcmNkwYOFkO9yzvUlzD4238LiNYBRTn7icyUZIZz5TJ96OYaZEorrKYMO24dN8vgjX4ig21EALUAY6JXjkeGY8nI9nrc60EjSSLd5aTGt+x5uZ7slDCaQmdIRQD632adHYDlsnQWtNhvt9R6o0kl0SC6kQGxDR60xrE5bbRZ3djgsEyK8taNQIZn4tHugy3poZdRZ1ZBQeYxW0CRkDbjJlnV0c7/a036xv6z4ptnmEiidCfDDEmOYoRvR0Wu1MKuw+8Co+LnZa8Rrz+WzwTEwa+IbXvWZAwC3XhXFTNA6DjSf1bOYkrSajCnHCRl4PUQOP60unvn+a9g/eIRl32NVkJWhGOq+49sTbQLqgDbxRHZPHdHskWsRJMqdk7C+26EZiWuM+L85a9aZYPySYtvGap6nY0NcpucCNxhZXTpoNo1iTULAdrqYVPBw3mhpUCUfYaWrx681IG+JHwcRSnB3Hbn8/OxB0D6gGxRYGgZJ0fSwsGCs60O3tmlAUesJ0xhZsoAfC3EDbY9STkr2/SmdqpW5jsELBQ6w3wcQDv/KlltgbNTR1KPQ6A2wl1RV91zsREGenjNXUrA4QxVRhdxGOj26LcAVkF+x90hsOBW/IxGoPJzhI5Y+inNoIJKZjYjSv9G13uzj1tFUswsNNukCJvmB5G15yUos5iERDH1Po5KAGo4aFbzhGb8SHFlrX9ICv9aGm4fdQ3mxVnPUm6SFSA+w7B+/bu53ZnEzWru1FZHOzhWqLTX07QYf0jtXQId6CtM1AiRibXkC2uIFoG2ukPHCZrB46I2q7bU1TPrA8STz1QrCSdN5gVpAm6rCIhatg09DFYN+X5N4agxasji3wysxIPYuK5qLu0pDUqOPDfR2K/RrWg4XJdkGl3MpQyFW/eTC2qiE5Rmu9qTTwQIgZmppoNVmLK4cZP7bbhH9YJXqMK6JVE/vD4Y6GViMTm9sNleAEsXGy+8x8K1B0smDwZmx7O0FvDSobyWiOxwMaP8xqA9wIxcm4Hbg6aagbrnkUewuxya9bo9Z2iC6ObWOO2SLDIk3ftYLTrLnf0lNWR+IZ3Zz6wmIaN/gQOnCWeYgbqwqd9Lhjp4NEtR7fqvRPqlRDGx14sseMQ9w0GzsMhp16uJhUhrgZtJrHxm6+YFlDROzAdaOe0xjsTU1TqTaIHoGjpfPRrn5UbMel2UpEDWcWH9sSO56Q9RoqzyEJ6ZCr0wiTpryS9mlV8kUrXHtjhK84Y3qlpvDYmnicjPJTzZ4oq7mfVjAW0dNxiKqt2V5roWLLbm+MjYcw445lNXCKYzwb3wozRtD7pkKvt249mrfSPglbdsrPGH2QpPhInxAJdep1EDiFYApSZpMhgSmWPprXWbvX8zZHlaARyejo9crMDRvCge+HzgmdC/0OEh9os1HncGvSNNDGarraUqtas5/6+kgh1XYdPrb3jQmCRgKSwj0K58iW0NGjmZt0ks6mnaCe21M2o01dNmfDuS1IM7Rm1bSJM+jgzYMATQ/+IJ7WxDFmbiIyWKiburliUIUI1bSHLIj+YLXGklTtyYzFzjuDIEHoGsnBVt+sDObu6iTZxAFyrXFSW1EzAcJmYx9WN5sBqmxJdt4DTBJfb+0WVNA/Qbxujpn1zFfWrMYrkiBw9uAQ8yOUIox+AK08LpV4Lq1w21YzlKlQJYSDC7d9pD85iCNhvRrsDhR9XPTGwLgcFfyielTqTsVxo68ONXW95qQWRHH6BPL4tn3YKw6XzsV6zxqRQ4shkO2GW+3WA02AEg4jdH46IaYJIcEzezsf7rkD5E33cbw3Kg4i6KfOaMWbrrxo+JCg6xUO7R+hxDSEU8tHpnVU6sD1UDBbkAvTg5UKTvHQ23grtIU2jQg2ZjV9prFbwfUjc0QhlWQxrqEepSFDvdnAO8zoKPFkiDdkDe9HKt0haN7nNweRpys9fN/cn/pjrGZpR3++nssjcrfTeQJpKO1gIXmbIG3MWxKnUnX62BwzNDRm/bokRX0UP242DNz2GGMjNqf7UY9nHKI5ZB0doDMrnbiDGgesGOfjxThp+G0RMW2cNQdSv9fQ5d1uD00dP1zUmbVqbE/WRqzXK44ehIq8CY5Hm2xbXtRCeefQgmXXkOZcfPLjqHmYkQObilsphvcdhHBpeZ0OT1KcpM5g5LUmY4/aTo2eb+/HJq1R0MTQeiqesj09UOqEMlKheuIoi7qTxNyUDeDwyLEVkjj2ahZiSWajzbvN1kKyZKbTmDQqC9jQQlpuIQ00nA92cm9USzVspptpgiOHtSTsZ2tm0ZijqYMxbap3IBqqfWh6DgmPPYuvY3GA1Ppzga4EAA+t02iGwL55Os0nDaoy38f8PJmpWNKoDCk1hbDe/EQhR20/X9X2tWNyYBtz1RRSbUS7Jrt3OZdomj45EXdjeWWQEnL0hLm0l3gR2aRb06M2837ArUcp7gO30tYHPrXBhJ3HjpE92t+KLaKtWly93qYGzcOp0cLEyVHatHUVddF4urEmg9kOG0qsSG/aNaRXQwL8oCmRM8AVqmVS9IwarRWrMjKbq1V9KBvezsJsZgatyFihg8OIRtPk1DiNKsZBVna0EJGHoeDWnI4oTHeDGSvRODa0WrwbyMZCJym3KajaULMr7ZMMc3bdQZymSjR7FjfREZY8udZOodYwpbLydkLjJ8seLzykhTLeiA+GW4gRDTcdO9tRGxeGzIYQcGtzgjzWtbfMYXawYnzdaU7ndkCKTXwFa/tBo96Bkg42E5oRNK3PkuHU2McoXNst9p1220GVpjTmoJDF07rPVPrGHq+tlSTGj6apnmZeA4H3J6fdEhq1tTOeoNbIa8f8qn6qB6uDHqy3HRlejRvzCeVKaFix99FYn+BMD/b49KDWQspC3S1cU1aLA7fzJhvgM7G1Xdc1w0LJ8fSI7g/D4XEWHTRx2Le9NpnsFXXP0gBnhQwygxL2uAjGA9/CZkiLTKweU0v8FeQuKgBLpshEb0kGtOJ0FaQ4MgB1KLrm1jhlo0ePrTctpBVSEkfMk4g5mp4sCbDVQnF6xgyULeavgkrQshgPYfnpHK67FX5oeLwmDNrD/rAzWU1iuY3os+DkRFQNdlpJcxv0PP4gusQcUkQJfPex/Zb1WyHGbfkAt1OFGypyIkr9YLvw2oNmME727TbePEVH4JZZad4b7Pppv50S/KynwdLgJMs01pOowe6IDRw+NVnLnfYTllRcLdWlmYwtkv4MyAEPksrK2VicipObXXoKJ/VWJRSsEYLNp8qgI9mM5rKmHzY3YWevKC7StyC+D2OHmnNQWj6h8mQ7iJITGcbWdqenkdKatkasVKEGYa+tS55hzlJkPkWkVqPhesJ+f6rNTEzp4GNHFAeHvpuMafdEV8xpxap5O60mrQ6ITMe6v0Ztod7qrHZEPG/s4/qgpiW1cbRf2KHYcfb+XjRQuW7BrDjXTjK63q9bquSwh+aUEBxoZeOO4+zcmWO76XE47GzGoS+ldGOEsKO5rDbJNJgPrcFCWyCTzYiW2ZY7DYPtcIEiqjul0lNj2qIIpg9vBkiEECe2NmLtSHOwE8sfrV48q+wOw4qy2DYHrgINGmsN9Wq7BJZh4ThzPVNd6dPp1pvpjQpPObvBCeTWWxxkn/vB5uSHDXlFouvY4IHlwEe1DY1bI66+o+2Rve34dh2mW65P97CTCKzfqEm4pu3ZFQuszg7rHUro1/oRdty7fbxnW/IWoYD/q2kxh4o72GvLpHbS0s2Kcxd1TaTEJjGudNgt5hLQxp8c9P0eeDQWU6cnEADQVKgvWGW9aZiSoq9tgupBBDld0Xvd8Pq0mGpH4OWcOQLRzrDfARHZ1H1/7m5bysmNWKWDbvmazeONcS1aKfHuJOxjoAB7CwI+hhygXWe0N2VO8PU2W2ORCT+c4tCRYEDG7CojqmnjI087+GYjkDF3MWm5m54jq5YmTre8zzVJ+qSwa7uFR25z19viJGa7C96BMcUep2O5vvccgsRCtGc4GyHBNga7U44YGmCTKBwPxygkjlUDN4/tvhdJHVZv6VIbaWCDQSQc6NFgfiJJ11x00P6Mn/kkiuwrcDisC4GLmjSyZkzXcxTU7CADwan5jUEoJWF6iEcQi8B8pTPZ2wrAx6eTNvKm6BptNrAGtUAln/SNET3vsBWD48ZYi9d6zMI+bhfTqRtKO0f2Yyk6HYQ2ge0tYMR4e+NsKFm2jzTTpNfr6QAZtFAommiINAo8mzdEeDyqQNy2fXK2UR+DGdflCImdILshY+DScIb6bUoWxnxPMjhRagxkgIkqobKGjLUJNh6zo0GKdhTrAEcsS+uoiEk1XVApudZj44TcOrTb6Rx7EdNR2J2WxKvhgNzGpukflbg/OdYa8xXAhqdVGmr8CFP0vc6cwsNOb7bp2nZgbSek2VsA375Ypx4GuYI9R/Skx59m+w1I5XvqpL41VWllbtA5uZ05FQuNxLi1wSMaOOe4EoYcb28qR7IZkb7X6ayRYLyBqVZlDvYQmvm6LSeD6WotNRQSHnp1ndewmuMF8yhu9wfj7VqsxINAolttxQ7lRiJqaXyYbIUIM3rKWga62yr7sDloBwMGE/2BRLCbqbwbs5YE1V1mNZXUKaIvfGqLW1Nv3iLH9W0v2K16tRPdnDWI3WAKgk5U4wfyAXN0Gmo3GLwn6LV4gEITqOLhLNdoLCppOts5ownwXSQej8SJq+l2YyPUBQKI5lg6nIy5tE3DMbwxfZXcBSlAiuRYiDEU3c7Cw6rP0X64W8RoD510BCadWgMdbQ1Hw/H0kBynIJ4wZM/yWm1xvHBr/bbSSnbo2tcNPkSPpNWopJiCtgkAZfbidDo6jDRpbrjDg8wcbXhbCWpzYdEyjYmrULWY93YbNTluk8P20MHGncWgLa19U0QSluOgw3buzcenUzj2g4qwOgz4OhMiKSvP9Ao/OXK0ulusoV2yqdXwsTk6hBVVCysDPiUnQx+aLE7HE98LdKw/6ePt9ggRN9J6I0Awg0wroxi4TgI29JTYdTqENV0cHXQ24awj5xhjM962h4c6Pd/OPFWlpLSn4GR7B3LCzrSnaax1klikkyoeANHjIJbqvdFwn7qdOtwROhZIkQcjABOnLVZGqQMctzsmPN2zhwbTo+zJFvbsfZ9vIL1oAPxBY5FACKYpWEhMNlajvddUkXbbWzpOIDGtmcpOaGw6PPCvZp8QLIrhzSYBs3y/wuzSFIhUl0x/UGNxfAojp0Njp9QpDmJCQqbI9fZAKr2VxS9YZEcNUsIMUtwTxq43mpnokCS8zRzeph1NB+i37afzFJnNAL4IiJAzNVrCBm7ETYCbtsMNyJfNCnuY8upxMeX10UniAr+TjF1uYAZj4jgYA+RyIpEV1TFnSair3HZi8b36vqHIPU5tEbEPp8c6IQxlZqy29CEZrb1Vr784bkPWmNb5PU+xaYsgeWNrGYMaYpu13mmw8lds91ZH7WY13XfHV/XoNavTvuuG5rtBaETRa1EIfl+1mlmjbrzeF1/f3t7PreUkNv/ZLr+9vcijodR9Leu26vjWe+xsy9XzFzP/9vbCEGBAHW7BHahar6MwAme/6kgz+9WAwK8G3GyCPrRVryPFr1bxC81/gb4GjLRb8NsLycnivFtvvdCE2IXbYEmzJZCgW69DSwjK/xVtM7nbhjv1F4aTAAAcLWV+SHLd8uXrre7cU0bDJQxlVJbkDMPl8ovIj0Y9DB9eJl2//3TWi+aoUVSifUd/FRMvK4aTYeiHbx+lAHS8vOiGWdJty4ji19XbR2jESehdau3v0VqtIy3Q8b42judRb/mU7IZgCbpfs0L628dLad39NOntpXSw43VeaX/3A8N7LYer8ltJjUomGF8C6K+0L9leyY6N8NVR3ZWufpjvoaHqr/Dvv9eht+qqXH77WL8nga7GxuseULzI9yBPLpC2NrTtMhMrF6maX2R0Od8zMulss5DDjpZR6jq2t319KwEBPD++duRzgQpUOzIKhZUpZkQuFU7CKHLJi0uWkSSG63+UK/kcD3B4y2nnlyZ2lJPLWJZUT7/RBibsO3tAO+MSGtl9yd5Yxv5rNu3W+4Q1r8gSQ5DLPsaSj1zzNWeHZQnM+RXoRz0vM+MKzPD3rgM0nrf/3j3bY7bgrOWPj/b3X7qrctY0gUul8gPjzHhoEiNIMVuyxCxIcFpKXjWK1TDuFtcs74kXqJm6Q999Lf/OMOVqRrgKQ29XIaDfvd+7MFT8d9E1kKySn5Z/gM6c4p2gX8SQsR5QwgibAz2Ub7t/lqXQQegflrFxjHMSVVs/Vs/dZ32Alt9z9uDDv7reAw9JFkWSyrS85KmliHH9fK2+aXZvgoJ5LyXTUa3na6fPSweT3v6Avr+UVoZlAxHsk/EnygIzKnD7prCMx//AmajZ5N/zTzmxSvb9X1c1/TNf3hdlgcUA21z2eAXAtztt5TueT6nk1D7uPueUvxeKBJ42UEPjak/V3NDORpXZdyYjOK6Za31g3sMIsFNiH/ggDthpxto4BoYWG3r34qf/KF+alsX1Y8ZmWXiK8vc/Mvrfc07nQ50v9JfuZdLXxdLYkhAZSgan4nwMLxb6eCheSsUNZnQnSsY6uzv1QxARluf+csE/0/K5BfCHc8uJkwB4hsgPgSSvwN7+KIONDQ2z/D13YqAl08tlFpgGYsuDxNdoJeG8QBaC54aWxN3sGlYNQzUt5P0Wq7bT/bTXL/d8znKc2VW3RtotnGfp+HG8iZbtXGbz3QeBvwF5ihbjaEex7VnLMFnmt7Tl7++G9xBGv3nGoRgchH6Q3RD/ZHDGrbDjV+j3TH7A6eJ6ZnLuEIt2QPTWnjvhVfl/jxBUzhYHJn1qAcO/WBtJMDIvMhgIoORMvvDOltYFw3M3V5hRJsMvxRLAxyUQtX01urthmUjnYeDj47AH5jfGOM/JwD/c9jKT4Me+6JcumP9oxcWJyRZwtWSwS69g1tuZXGYKlYvK/tUFQbFR/3ISeIqSAB1+QorUiJ/mopz9Tu51bA8EmsLrAHOrPvg14H6qGZPqhcnbNzCmkikxt8NK99LxUtKjwlajVzCkcFq3kxZlK3y9Ot57GQvvvcTpzLsS5fxAgkh9b/dR/MfH1eK/v708OVXPjRnYZPfzgj7vRBR/2oi/atCPms62SeAlGadJALkoDETnfDHFav4AxD7Av0r7ezf3t7fvuaYKxeVDgQTZiAfqHM9dPGhvLpPSvbYuXjw6x7sMMywzIBDl8CE75jnSyV4wFC03RHENLXlHraytbXDk34HLKL/9APFkSGPJ8fKSyuJILoDvx91ivgP2olwrA52JSvklBzdR99+Z//3IRtXyMJFtXv7hHCv+U+xnkH3PZ7zvVScB6nj7uMdsVatw4+f15iOLFecvWYpRBz/c6nZ4xan5oi+Ntc/vNnI4DJC1TL5nuUU5p1a8iFlm8v5NcjkKzBC3IkjlQjTj/Npmmb/bybVcvRL9ycZ8Ow/qPnD8tHHn5megMXebOXr81Hlb0YPLzGReskqWL5EgM5BJkcNG5S9srtD40emdxy+nvDgkGIAJ5+yI4YZ31nm/8DMsAzB+me/c651Cgu6TzbxaafCeB6XMMs50Myz98gDtweg4TD+i+2wxyJOG4rznhxiEte4tFwS7pBlBXCLzX9lTJZCCGJ+AIDASAPRFgHszzAnSlPyVkJHLFr1bRvxajoAcrloGB7h4J5QjtXNX/iAKzDpjpNeyIJIClgEykHie0ztwnqtlkcQzVz1fiuRYYcSijc86c9Mq52H7XjSFG3L8lCvs+E7l58NxCEH6tFRj37W1ZaaTIvvxV5uMEpDLMrp52pDlYsvsXL5es4hK+T0fcDaE/PN1C/LV5S0/NIxsVWQhWPazAM8rX0+7r/nu6IkbgHCx2lQNL8reeqmRZttdSnUio2p7uuHF3Xo1wzNL4JKirhwmxlul/L8e8E5f0EW260A1eUpZyFXklMdrTmm+58p4zSR4+2a+m04SrcFZ86N3M0o97RU0ARvy/Nc8wIJmgHgdVQPQLqNXzTNZ4KxscKCdnNkXpXwUXxOv0EaxBZ4PoojnZVgqOwevZ8wM6GdK/qVb9uLHDGvKcAQ/lZY8N5rnqd1yKjLF5oIDcn2/9g6ovgK0qkZbB7AHhlKjePATlybZZ44ufwdBTc9A5N0kgRHIrNkIwy/NWfafDYfrxY5nByczpkzVv3ShT/hEGo4Y4DFusS4+xt3gvWD5qeRSLZ91Wf4UvqN9fjhBhm/771IcAi0x/Cug9Pb2cYOMYPSH5nsgOCVG1upmZpsFaug74BfaAcidHf8AqJyhUT6iOGkr1dGTEGyRAaSwPbB9dpxmjsG4NB4MW0/yz7lVv+aT33M8EGX2BM4vUEPwz8yQAEwtug1PP3cWM3NxH04mPuKlIjVfYhyxnJIMoSwpRpQyKJcTuS9NAKwB5LjG7OAcUqeGTShgbVb520+i4a3a8nbvXvNM6oYDinj8GSC85BngOUzn7UW6VTjNApm8PYvaGlCGnVVeLjH+c4ZY0CnyxGcE7kN5kfLeSL6cg3FkgPiVPcHMj815xr8vvvaj8LTVi4P9AO4Q4CM5d5v5QvOXqsvs4MeGV/6AMkPc28YBqDv2Y9UpfzQa7Wq2dcV/t+7iES3ohx4mOVvQ1K6Wz4vV80wRcK5D91SyFNI+v35dgb05D4IBqYLuXYJ567sjcB51pgEWlr3fBcBrOWIm5HLCSEyPGTHyPKvB4Ioo5rnGCKT3mESC4EuWnxA7Z9bnzOXjlvACwBaH6qf+708oXPfnx0QyTWXA+RmVCJxuoIyiXgdUmzn0apFSFU1LDRgdyF7LH0UQyPcQ+I10uTdC27SvPf+51iSKJ8dPodXle/dnMCwzqsy+ug+29i3HId0nKOUSCuOiiJd/+uNif9//bnAvwnnO9FLGLEh1iw0vgic2yoDHfInhMtj9crUQ7hPrt2/n01GQu0bE4nhFoVbNUrSvjuGHAuSgllCyLPpSL16ClVEjpk+DT5gk3YwsP2ZnN/Dvcsay/JFlq3f+5A2c0kcDPGfXQLTriK8Gdin4gCTwE5ncNZXzzPA5ibsBt+n/+eqJrqvIA8ESONsz9+4Xz3wdCqKS0QWJ2V18zp/e5w/xPRCSjKjABnrGRsTY/I3919f5UWw7Tv44v/wjJHrUPn6+R3niIcm8UK6C7QXIqhungfEKJr69L3NMt1xWyuf6Qdb6xwfchr7fwsfZYs7ZlA9ceJEFvWZZUO6/q5cKcrah3Wsydyuc38PCL5X0Z9kGOQPgIa9Dfr4F+IrYisrXnyE2+/OtA8ik76qFz4QAh5GhGByTGZBh34DMXWA6K+WgBgVwzsPUtVapJWGYodS7a4TPfV/K/p9l/Dzha5X/nO2D3IziRbDTU0z4dMXwpzg++yuS5X8F5nM7z1H8ees+ifDX8fdf282H7cwJ/mw/c8GIvOzLMhKb/TFG+Wcg/m8ZS1bXybX+hf7fzgWKv3Qx9NfY3xpeZjKZ3rLjqndtL0hAriiDL6VyJR9QKRd/IeOkpVcQ4UkxA12a4URvHyWQBJ2h781v8FR+eXcmWC7nW51/+aWbE3yE8HMB6AwTBJGfAC9/C0qFrGfs8d+E1i+pz0sWsrs/CNuFNwnvYtovfykKXaoBYOrLTcMPd6jPZbGf1iHyU/qk/UGs+5z8QalFjD4HbhHDi7TtT2Ow/SQN+KWbK+NzVPpUcy7yiouPkBgOJ28KuqRb9/HubK1fou+ZXR7KL3cuf3yK2fdV8VtMfT7zSyx/lLv4u7RPgl+MMY8L58KTm/18zcC2FxdFgGp+xpb+tigJnGuQzyp337JvZwqfJ+VlYND7Z5FK5Hn5vqaV/+1dEQNfC/MEpxVkztlxNLMPr+Xf5r+5v+nyb/Rv7G/Sopwn1u+Wm3e+vVXKYEb2B2fv2Y/ma357nl26vn3LaZ/lzVllS7oAq4fQnI8sYvNtC59lWQVY/EnKdI9WzzoE7Av8lnN5O+dS2ZKL5kcsVDqb6AWy/cBq78Z/AoLF8r4Y5E+QWql89k63TOORys04f0olsa/Tr+GgSLyBDwlDWzfKtbLCvLMkp4A4BkzmJ923knkJuGgjD/n5Bjyran77WpmL4gLZXy8l9e4f36+R9dkxvgGTM8iuXtdd/aLOt29nqu/ARxqe/nqO3D/wPef04mFrf+Z5CCW/Xz673fM900OG0r1Lhn6+/HM864GU7BMWzlZ9VsiDRkDaaYTR9d5TL8oxX8J8dPVYX+zka8jPAKECAFcOwm4XeU+0flVy9QvZfMYXRdyHj5+r4qkuPp4T/ZJeZsMybf2cw3MW+fOfTyUt4Cfk7HbzElufJLTnwvjxUqbO8+tPyTX48DSROT9NulrJEptijJxZVYY+hRE2L1e/VnW69duBvvMK+SVg1M1Ko68MIb1VH3PU7L73J4loVpT4YQr6sxyydHOh3TsP+ljP6V7KOfJtseWHfOzyeMVxMnr/rxjsW/TDukaWqER5MvAAdm4ynvtu4eD7L91rQPh0Z7kcYdLd+m43FD/wN3/B1+SHsKCbFcczYond/aFHzlm9Xh1AYucePLGfOepCgls8eGSvMM9458lwfkUHpt6Fzu93d1Y/feD1DLLcPfj6y8m0gMn0+R1aJtcZW3b//Z9vsRpaRvys6vssnhTy5Ilknt/f15yLvtytF+SLw3CGXQ/V4keAeT+60PInTFl0ZYu9btVZ7PtJXwL+ed6DPq6PHq/7dHsKlGnmmh08vpZ8+/YkO/gBbv7/kzHLDm6infPUvxjzH5hXH3Rc/Ykgue/N2XwGAdHfCk9f4Ew1+tOwHf08Vv0NPqXn6vxZMPrrQejy/3C40iX4rJz+NO6Ao5ph8ifR5okzL7j8N678qeP+9mVpN1d+yYz//Y9/gM47zJ+v9DH85Bcyz1VSrtztXfU+wBXX23eu71yIu9/r+/hxD99+dB2V1zpB+liUwy4PAZduFkiz/PIcwp/iuu7PTuGz7OjMrIg8iXdGj4DJlwjV/Rqhbujss7nfafJcki1qr1nptfWp9HoO9Yn3sN1V19eNbvlaKilfikWFF8p777vviiDPayt3sy5mcHkq8MQwH8Zfb6HOE55Whh5mXIDLdcpzJPODtwwsT5A/Lofn1fDPh/nvFcaf1sXB3tTr0PdnJ/0qGUMtyRlOCnnBGKNkUlxiikzzIrMALqO4pr+oobgLuuiuetPJGXVAxdVLoZ6X/wPy0+aA'
def run(mode,game_root,external_root,offline=False,input_fn=input,allow_non_windows_test=False):
    if mode.startswith('bulk_'):
        import base64 as _b64, zlib as _zl
        ns={'__name__':'bg_eet_ru_v157_embedded'}
        exec(compile(_zl.decompress(_b64.b64decode(_V157_BLOB)), '<pinned-v157-bulk>', 'exec'),ns)
        return ns['run'](game_root,external_root,mode[5:])
    return _V154_PRESERVED_RUN(mode,game_root,external_root,offline,input_fn,allow_non_windows_test)

# V158 only extends V157 read-only status; all earlier source preserved.
_V157_RUN_UNCHANGED=run
_V158_RO_Z='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'
def run(mode,game_root,external_root,offline=False,input_fn=input,allow_non_windows_test=False):
    if mode=='bulk_status':
        previous=_V157_RUN_UNCHANGED(mode,game_root,external_root,offline,input_fn,allow_non_windows_test)
        try:
            import base64 as _b64, zlib as _zl
            ns={'__name__':'bg_eet_ru_v158_ro'}
            exec(compile(_zl.decompress(_b64.b64decode(_V158_RO_Z)), '<v158-live-ro>', 'exec'),ns)
            observed=ns['audit_game'](game_root)
            return {'schema':'BG_EET_RU_V158_ONE_BATCH_CURRENT_PROVENANCE','status':observed['status'],
                    'v157_status':previous,'v158_readonly_provenance':observed,
                    'game_files_written':0,'install_allowed':False,'dialogue_mod_installed_proven':False}
        except (OSError,ValueError,RuntimeError) as exc:
            return {'schema':'BG_EET_RU_V158_ONE_BATCH_CURRENT_PROVENANCE','status':'V158_READONLY_SOURCE_HOLD',
                    'reason':type(exc).__name__+':'+str(exc)[:180],
                    'v157_status':previous,'game_files_written':0,'install_allowed':False}
    return _V157_RUN_UNCHANGED(mode,game_root,external_root,offline,input_fn,allow_non_windows_test)
