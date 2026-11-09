#!/usr/bin/env python3
"""BGXAI 056 explicitly opt-in active guard, guarded WeiDU installer/rollback.

Reads existing exact 049+042B game baseline, compiles BAF using game's own IDS
in temporary directory, inserts 8 blocks at verified 1-based position 1032,
and backs up the two changed override files before staging or WeiDU writes.
NO installer invocation without exact user YES through pinned updater.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path
from BGXAI56_BUILDER import combine, compile_only, PIN_BCS, PIN_BCS_BYTES, verify_old, sha

GAME=Path(r'C:\Games\BG_EET_FOXX_NEW')
VERSION='0.3.22-056-ACTIVE-GUARD-OPTIN'
MOD='BGX56'
TP2='BGX56/setup-BGX56.tp2'
LUA='BGX56/M_BX43.lua'
BAF='BGX56/BGX56_RECEIVER.baf'
BCS='override/BDDEFAI.BCS'
DEST_LUA='override/M_BX43.lua'
WEIDU='setup-enhanced-powergaming-scripts.exe'
EXECUTABLE='setup-BGX56.exe'
OLD_LUA='a1c09d704bf66f054a2099c6496212573d56d185a550fb874fc1a35b1c739912'
OTHER_BASE={
    'override/M_BGX43Probe.lua':'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f',
    'override/M_BGX44Diag.lua':'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f',
    'override/M_BX44.lua':'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f',
}
BACKUP_FILES=('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk',
              BCS,DEST_LUA,*OTHER_BASE.keys())
SOURCES=(LUA,BAF,TP2,'BGXAI56_BUILDER.py','BGXAI56_INSTALL.py','README_RU.md',
         'tests/test_056.py','tests/test_lua_056.py','ci_weidu_056.py',
         'ids/trigger.ids','ids/action.ids','ids/object.ids','ids/modal.ids')
RE49=re.compile(r'(?i)^~(?:[^~]*[/\\])?BGX49[/\\]SETUP-BGX49\.TP2~(?=\s|$)')
RE56=re.compile(r'(?i)^~(?:[^~]*[/\\])?BGX56[/\\]SETUP-BGX56\.TP2~(?=\s|$)')


def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1024*512),b''):h.update(x)
    return h.hexdigest()


def unsafe(path:Path)->bool:
    try:s=path.lstat()
    except FileNotFoundError:return False
    return path.is_symlink() or bool(getattr(s,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe(root:Path,rel:str)->Path:
    if not rel or rel.startswith('/') or '\\' in rel or ':' in rel or '..' in Path(rel).parts:
        raise RuntimeError('PATH_BLOCKED: '+rel)
    p=root/rel;x=p
    while True:
        if unsafe(x):raise RuntimeError('REPARSE_BLOCKED: '+str(x))
        if x==root or x.parent==x:break
        x=x.parent
    return p


def existing(p:Path,min_bytes=1)->Path:
    if unsafe(p) or not p.is_file() or p.stat().st_size<min_bytes:raise RuntimeError('MISSING_OR_UNSAFE: '+str(p))
    return p


def weidu_entries(root:Path)->list[str]:
    s=existing(safe(root,'WeiDU.log')).read_text(encoding='utf-8-sig',errors='replace')
    return [x.strip() for x in s.splitlines() if x.lstrip().startswith('~')]


def verify_package(pkg:Path)->dict:
    m=json.loads(existing(safe(pkg,'SOURCE_MANIFEST.json')).read_text(encoding='utf8'))
    if m.get('version')!=VERSION or m.get('status')!='OPT_IN_ACTIVE_056_TWO_OVERRIDE_FILES':
        raise RuntimeError('UNEXPECTED_RELEASE_STATUS')
    if set(m.get('files',{}))!=set(SOURCES):raise RuntimeError('SOURCE_ALLOWLIST_MISMATCH')
    for name,meta in m['files'].items():
        p=existing(safe(pkg,name))
        if p.stat().st_size>200000 or p.stat().st_size!=meta['size'] or digest(p)!=meta['sha256']:
            raise RuntimeError('UNVERIFIED_SOURCE: '+name)
    lua=(pkg/LUA).read_text(encoding='utf8')
    if 'B.enabled = true' not in lua or 'guard_mode = "F_GATED_BCS_REQUESTS_056"' not in lua:
        raise RuntimeError('ACTIVE_LUA_NOT_ENABLED')
    if 'return false -- CRITICAL' not in lua or 'BGX52Bridge.prepare' not in lua:
        raise RuntimeError('WEAPON_HIT_HOOK_CHANGED')
    for bad in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'EEex_Action_Queue', 'io.open(', 'os.execute('):
        if bad in '\n'.join(line.split('--',1)[0] for line in lua.splitlines()):
            raise RuntimeError('DANGEROUS_LUA_CALL: '+bad)
    tp2=(pkg/TP2).read_text(encoding='utf8')
    expected=('COPY ~BGX56/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~',
              'COPY ~BGX56/M_BX43.lua~ ~override/M_BX43.lua~')
    if tp2.count('COPY ~')!=2 or any(token not in tp2 for token in expected) or 'EXTEND_TOP' in tp2:
        raise RuntimeError('TP2_MUST_COPY_ONLY_TWO_VERIFIED_FILES')
    return m


def require_game(root:Path,enforce:bool=True)->Path:
    root=root.resolve()
    if enforce and str(root).casefold()!=str(GAME).casefold():raise RuntimeError('WRONG_GAME_ROOT')
    existing(safe(root,'chitin.key'),1000)
    existing(safe(root,'InfinityLoader.exe'),10000)
    exe=existing(safe(root,WEIDU),100000)
    if exe.open('rb').read(2)!=b'MZ':raise RuntimeError('WEIDU_NOT_WINDOWS_EXE')
    return root


def preflight(root:Path,*,for_uninstall=False,enforce=True,installed_sha=None)->dict:
    root=require_game(root,enforce)
    log=weidu_entries(root)
    expected=RE56 if for_uninstall else RE49
    if not log or not expected.search(log[-1]):raise RuntimeError('WEIDU_LAST_MOD_UNEXPECTED: '+str(log[-1] if log else 'NONE'))
    if not any(RE49.search(x) for x in log):raise RuntimeError('BGX49_NOT_INSTALLED')
    if not for_uninstall and any(RE56.search(x) for x in log):raise RuntimeError('BGX56_ALREADY_INSTALLED')
    old_bcs=existing(safe(root,BCS),PIN_BCS_BYTES)
    old_lua=existing(safe(root,DEST_LUA))
    if for_uninstall:
        if installed_sha is None or (digest(old_bcs),digest(old_lua))!=installed_sha:
            raise RuntimeError('INSTALLED_056_FILE_DRIFT')
    elif digest(old_bcs)!=PIN_BCS or digest(old_lua)!=OLD_LUA:
        raise RuntimeError('049_042B_BASELINE_SHA_MISMATCH')
    for path,wanted in OTHER_BASE.items():
        if digest(existing(safe(root,path)))!=wanted:raise RuntimeError('LEGACY_HASH_DRIFT: '+path)
    for x in BACKUP_FILES:existing(safe(root,x))
    if not for_uninstall:
        for x in (MOD,EXECUTABLE):
            if safe(root,x).exists():raise RuntimeError('BGX56_STAGING_COLLISION: '+x)
    hashes={x:digest(existing(safe(root,x))) for x in BACKUP_FILES}
    return {'game':str(root),'last_mod':log[-1],'hashes':hashes}


def guard_processes():
    if os.name!='nt':return
    ps=('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
        'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=25)
    if p.returncode or p.stdout.strip():raise RuntimeError('GAME_OR_WEIDU_RUNNING_OR_PROCESS_CHECK_FAILED: '+p.stdout[:240])


def backup_root()->Path:
    return Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI56_SAFE_BACKUPS'


def make_backup(root:Path,pre:dict,*,kind='PRE_INSTALL',base=None):
    home=backup_root() if base is None else base
    if unsafe(home) or unsafe(home.parent):raise RuntimeError('BACKUP_ROOT_REPARSE')
    home.mkdir(parents=True,exist_ok=True)
    target=home/(kind+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    hashes={}
    for name in BACKUP_FILES:
        src=existing(safe(root,name));dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if digest(src)!=digest(dst):raise RuntimeError('BACKUP_SHA_MISMATCH_'+name)
        hashes[name]=digest(src)
    (target/'before.json').write_text(json.dumps({'pre':pre,'hashes':hashes},indent=2)+'\n',encoding='utf8')
    return target


def run_weidu(root:Path,*,uninstall=False,runner=subprocess.run):
    cmd=[str(root/EXECUTABLE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    return runner(cmd,cwd=str(root),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
                  timeout=180,check=False)


def install(root:Path,pkg:Path,*,guard=guard_processes,runner=subprocess.run,base=None,enforce=True,compiler=None)->dict:
    root=root.resolve();pkg=pkg.resolve()
    m=verify_package(pkg);guard();pre=preflight(root,enforce=enforce)
    # Before any game write, verify exact baseline BCS and compile with real IDS.
    old=existing(root/BCS).read_bytes();verify_old(old)
    if compiler is None:
        compiled=compile_only(root,pkg/BAF,root/WEIDU,root/'lang/ru_RU/dialog.tlk')
    else:compiled=compiler(root,pkg/BAF,root/WEIDU,root/'lang/ru_RU/dialog.tlk')
    combined,proof=combine(old,compiled)
    backup_folder=make_backup(root,pre,base=base)
    result={'status':'NOT_STARTED','backup':str(backup_folder),'proposal':proof,'checks':{}}
    staged=[];started=False
    try:
        (root/MOD).mkdir(exist_ok=False);staged.append(root/MOD)
        stage=root/MOD/'staged';stage.mkdir(exist_ok=False)
        shutil.copy2(pkg/TP2,root/TP2)
        shutil.copy2(pkg/LUA,root/LUA)
        (stage/'BDDEFAI.BCS').write_bytes(combined)
        if digest(stage/'BDDEFAI.BCS')!=proof['patched_sha'] or digest(root/LUA)!=m['files'][LUA]['sha256']:
            raise RuntimeError('STAGED_OUTPUT_SHA_MISMATCH')
        exe=root/EXECUTABLE
        with (root/WEIDU).open('rb') as f,exe.open('xb') as g:shutil.copyfileobj(f,g)
        staged.append(exe)
        if digest(exe)!=digest(root/WEIDU):raise RuntimeError('WEIDU_COPY_SHA_MISMATCH')
        if not RE49.search(weidu_entries(root)[-1]) or any(digest(root/x)!=v for x,v in pre['hashes'].items()):
            raise RuntimeError('GAME_CHANGED_DURING_PREPARE')
        started=True
        proc=run_weidu(root,runner=runner)
        output=(proc.stdout or '')+'\n'+(proc.stderr or '')
        checks={
            'weidu_return_0':proc.returncode==0,
            'weidu_no_fatal':not re.search(r'(?im)^\s*(FATAL ERROR:|ERROR:)',output),
            '056_last':bool(weidu_entries(root) and RE56.search(weidu_entries(root)[-1])),
            'bcs_exact_1065_blocks':digest(existing(root/BCS))==proof['patched_sha'],
            'lua_exact':digest(existing(root/DEST_LUA))==m['files'][LUA]['sha256'],
            'legacy_unchanged':all(digest(root/k)==v for k,v in OTHER_BASE.items()),
            'key_and_tlk_unchanged':all(digest(root/k)==pre['hashes'][k]
                for k in ('chitin.key','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk'))}
        result.update(status='INSTALLED_EXPERIMENTAL_056' if all(checks.values()) else 'REVIEW_WEIDU',
                      checks=checks,weidu_output=output[-2500:])
    except Exception as e:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU',error=str(e))
        if not started:
            for p in reversed(staged):
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
    finally:
        (backup_folder/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return result


def verified_backup(root:Path,pkg:Path,base=None)->tuple[Path,dict]:
    home=backup_root() if base is None else base
    if not home.is_dir() or unsafe(home):raise RuntimeError('056_ORIGINAL_BACKUP_MISSING')
    for file in sorted(home.glob('PRE_INSTALL_*/before.json'),reverse=True):
        try:
            if unsafe(file) or unsafe(file.parent):continue
            data=json.loads(file.read_text(encoding='utf8'))
            if data['pre']['game']!=str(root):continue
            if any(digest(existing(file.parent/n))!=wanted for n,wanted in data['hashes'].items()):continue
            rep=json.loads(existing(file.parent/'report.json').read_text(encoding='utf8'))
            if rep.get('status')!='INSTALLED_EXPERIMENTAL_056' or rep.get('backup')!=str(file.parent):continue
            if data['hashes'][BCS]!=PIN_BCS or data['hashes'][DEST_LUA]!=OLD_LUA:continue
            return file.parent,rep
        except (OSError,RuntimeError,ValueError,KeyError,TypeError):continue
    raise RuntimeError('056_NO_VERIFIED_INSTALL_BACKUP')


def uninstall(root:Path,pkg:Path,*,guard=guard_processes,runner=subprocess.run,base=None,enforce=True)->dict:
    root=root.resolve();pkg=pkg.resolve();m=verify_package(pkg)
    guard();orig,report=verified_backup(root,pkg,base)
    pre=preflight(root,for_uninstall=True,enforce=enforce,
          installed_sha=(report['proposal']['patched_sha'],m['files'][LUA]['sha256']))
    folder=make_backup(root,pre,kind='PRE_ROLLBACK',base=base)
    result={'status':'NOT_STARTED','backup':str(folder),'verified_original':str(orig),'checks':{}}
    try:
        proc=run_weidu(root,uninstall=True,runner=runner)
        output=(proc.stdout or '')+'\n'+(proc.stderr or '')
        checks={'weidu_return_0':proc.returncode==0,
                '049_last':bool(weidu_entries(root) and RE49.search(weidu_entries(root)[-1])),
                '056_removed':not any(RE56.search(x) for x in weidu_entries(root)),
                'original_bcs_restored':digest(existing(root/BCS))==PIN_BCS,
                'original_lua_restored':digest(existing(root/DEST_LUA))==OLD_LUA,
                'other_unchanged':all(digest(root/k)==v for k,v in OTHER_BASE.items())}
        result.update(status='UNINSTALLED_RESTORED_049' if all(checks.values()) else 'REVIEW_ROLLBACK',
                      checks=checks,weidu_output=output[-2400:])
    except Exception as e:result.update(status='REVIEW_ROLLBACK',error=str(e))
    finally:(folder/'rollback_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return result


def status(root:Path,pkg:Path)->None:
    print('BGXAI 056 ACTIVE GUARD - STATUS READ-ONLY')
    try:
        m=verify_package(pkg);root=require_game(root)
        log=weidu_entries(root)
        print('049 installed:',any(RE49.search(s) for s in log))
        print('056 installed:',any(RE56.search(s) for s in log))
        print('056 last:',bool(log and RE56.search(log[-1])))
        print('042B unchanged:',digest(existing(root/BCS))==PIN_BCS)
        print('049 observer unchanged:',digest(existing(root/DEST_LUA))==OLD_LUA)
        try:
            folder,rep=verified_backup(root,pkg)
            print('056 verified backup:',str(folder))
            print('056 active BCS expected:',digest(existing(root/BCS))==rep['proposal']['patched_sha'])
            print('056 active Lua expected:',digest(existing(root/DEST_LUA))==m['files'][LUA]['sha256'])
        except RuntimeError:pass
    except Exception as e:print('STATUS_REVIEW:',str(e))
    print('STATUS_CHECK_DID_NOT_CHANGE_GAME')


def main(argv=None):
    p=argparse.ArgumentParser()
    for name in ('precheck','status','install','uninstall'):p.add_argument('--'+name,action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args(argv);pkg=Path(__file__).resolve().parent
    if a.status or not (a.precheck or a.install or a.uninstall):status(a.game_root,pkg);return 0
    if a.precheck:
        try:verify_package(pkg);preflight(a.game_root);print('BASELINE OK; NO INSTALL');return 0
        except Exception as e:print('PRECHECK BLOCKED:',e);return 1
    action='UNINSTALL' if a.uninstall else 'EXPERIMENTAL INSTALL'
    print('This changes exactly 2 override files via WeiDU, only after verified backup.')
    if input('Type YES to '+action+': ').strip()!='YES':print('CANCELLED');return 0
    try:
        r=uninstall(a.game_root,pkg) if a.uninstall else install(a.game_root,pkg)
        print('BGXAI 056:',r['status'])
        for k,v in r.get('checks',{}).items():print(k+':',v)
        print('BACKUP:',r['backup'])
        if r.get('error'):print('ERROR:',r['error'])
        return 0 if r['status'] in ('INSTALLED_EXPERIMENTAL_056','UNINSTALLED_RESTORED_049') else 1
    except Exception as e:print('STOP:',str(e));print('Do not retry blindly.');return 1

if __name__=='__main__':sys.exit(main())
