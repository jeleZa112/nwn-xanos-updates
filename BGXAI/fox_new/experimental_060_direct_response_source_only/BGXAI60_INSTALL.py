#!/usr/bin/env python3
"""BGXAI 060 guarded opt-in WeiDU BCS-only receiver upgrade.

Read-only by default. Must pass *two* explicit approvals before game writes.
Requires exact 056 BCS & Lua, BGX56 last, external SHA-verified backups.
Leaves EPS scripts, all Lua, TLK, dialog and other AI untouched.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path
import BGXAI60_BUILDER as builder

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
OLD_BCS_SHA = builder.PIN_056_BCS
LUA_SHA = '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'
BAF_SHA = '518a4c3ad591ce0cd758c6397a304565c38674dbc0ef82d2db0debd8cc096968'
BAF = Path(__file__).with_name('BGX60_RECEIVER.baf')
BCS_REL = 'override/BDDEFAI.BCS'
LUA_REL = 'override/M_BX43.lua'
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
EXE = 'setup-BGX60.exe'
STAGE = 'BGX60'
TP2 = 'BGX60/setup-BGX60.tp2'
STAGED_BCS = 'BGX60/staged/BDDEFAI.BCS'
TP2_TEXT = ('BACKUP ~BGX60/backup~\nAUTHOR ~BGXAI guarded opt-in executor~\n'
            'BEGIN ~BGXAI 060 verified-hit direct defense (BCS-only)~\n'
            'COPY ~BGX60/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n')
LAST_056 = re.compile(r'^~(?:[^~]*[/\\])?BGX56[/\\]SETUP-BGX56\.TP2~(?=\s|$)',re.I)
LAST_060 = re.compile(r'^~(?:[^~]*[/\\])?BGX60[/\\]SETUP-BGX60\.TP2~(?=\s|$)',re.I)
BACKUP = ('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk',
          'lang/ru_RU/dialogf.tlk', BCS_REL,LUA_REL)

class Stop(RuntimeError):pass

def sha(data:bytes):return hashlib.sha256(data).hexdigest()

def reparse(p:Path):
    if p.is_symlink():return True
    try:return bool(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (FileNotFoundError,AttributeError):return False

def safe_file(root:Path,rel:str,min_size=1):
    if not rel or rel.startswith(('/', '\\')) or ':' in rel or '\\' in rel or '..' in Path(rel).parts:
        raise Stop('UNSAFE_PATH:'+rel)
    p=root/rel
    for q in (p,*p.parents):
        if reparse(q):raise Stop('REPARSE_BLOCKED:'+str(q))
        if q==root:break
    if not p.is_file() or p.stat().st_size<min_size:raise Stop('MISSING_OR_EMPTY:'+rel)
    return p

def last_mod(root:Path):
    lines=safe_file(root,'WeiDU.log').read_text(encoding='utf-8-sig',errors='replace').splitlines()
    entries=[x.strip() for x in lines if x.lstrip().startswith('~')]
    if not entries:raise Stop('EMPTY_WEIDU_LOG')
    return entries[-1]

def source_check():
    if not BAF.is_file() or reparse(BAF) or sha(BAF.read_bytes())!=BAF_SHA:
        raise Stop('UNVERIFIED_060_BAF')
    if BAF.read_text(encoding='ascii').count('\nIF\n')!=14:raise Stop('BAF_RULE_COUNT_CHANGED')
    return {'baf_sha256':BAF_SHA}

def preflight(root:Path, expected='056', target_sha:str|None=None):
    root=root.absolute()
    if not root.is_dir() or reparse(root):raise Stop('INVALID_GAME_ROOT')
    safe_file(root,'chitin.key',1000);safe_file(root,'InfinityLoader.exe',10000)
    weidu=safe_file(root,WEIDU,100000)
    with weidu.open('rb') as fh:
        if fh.read(2)!=b'MZ':raise Stop('WEIDU_EXE_HEADER_INVALID')
    last=last_mod(root)
    if not (LAST_056 if expected=='056' else LAST_060).search(last):
        raise Stop('WEIDU_LAST_UNEXPECTED:'+last)
    actual=sha(safe_file(root,BCS_REL).read_bytes())
    if actual!=(OLD_BCS_SHA if expected=='056' else target_sha):raise Stop('BCS_MISMATCH_OR_MISSING_TARGET_PIN')
    if sha(safe_file(root,LUA_REL).read_bytes())!=LUA_SHA:raise Stop('LUA_056_DRIFT')
    for rel in BACKUP:safe_file(root,rel)
    if expected=='056':
        for rel in (STAGE,EXE):
            if (root/rel).exists() or reparse(root/rel):raise Stop('STAGING_COLLISION:'+rel)
    return {'last':last,'bcs_sha256':actual,'lua_sha256':LUA_SHA}

def game_process_guard():
    if os.name!='nt':raise Stop('WINDOWS_REQUIRED_FOR_INSTALL')
    s=('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
       'Where-Object {$_.Name -match "^(Baldur|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
       'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',s],
            capture_output=True,text=True,timeout=25)
    if p.returncode or p.stdout.strip():raise Stop('GAME_OR_WEIDU_ACTIVE_OR_QUERY_FAILED:'+p.stdout[:200])

def backup_folder():return Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI60_SAFE_BACKUPS'

def make_backup(root:Path, pre:dict, label:str, parent:Path|None=None):
    dest=parent or backup_folder()
    if reparse(dest) or reparse(dest.parent):raise Stop('UNSAFE_BACKUP_FOLDER')
    dest.mkdir(parents=True,exist_ok=True)
    folder=dest/(label+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(exist_ok=False)
    hashes={}
    for rel in BACKUP:
        src=safe_file(root,rel);dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst);expected=sha(src.read_bytes())
        if sha(dst.read_bytes())!=expected:raise Stop('BACKUP_HASH_FAILED:'+rel)
        hashes[rel]=expected
    (folder/'BACKUP_PROOF.json').write_text(json.dumps({'pre':pre,'sha256':hashes},indent=2)+'\n',encoding='utf8')
    return folder

def wei_run(root:Path,uninstall=False,runner=subprocess.run):
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(cmd,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
             encoding='utf-8',errors='replace',text=True,timeout=180,check=False)
    return {'rc':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-2000:]}

def proposal(root:Path):
    source_check()
    old=safe_file(root,BCS_REL).read_bytes();builder.verify_original(old)
    compiled=builder.compile_fragment(root,BAF)
    return builder.splice(old,compiled)

def install(root:Path,*,guard=game_process_guard,backup=make_backup,runner=subprocess.run,build=proposal):
    guard();source_check();before=preflight(root,'056')
    new,proof=build(root) # compile entirely in temp, no game modifications
    if not proof.get('eps_unchanged') or sha(new)!=proof.get('patched_bcs_sha'):
        raise Stop('PATCH_PROOF_INVALID')
    saved=backup(root,before,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('BACKUP_NOT_VERIFIED')
    guard();preflight(root,'056')
    (root/STAGE/'staged').mkdir(parents=True,exist_ok=False)
    (root/STAGED_BCS).write_bytes(new)
    (root/TP2).write_text(TP2_TEXT,encoding='utf8',newline='\n')
    shutil.copy2(root/WEIDU,root/EXE)
    if sha((root/STAGED_BCS).read_bytes())!=proof['patched_bcs_sha']:
        raise Stop('STAGING_SHA_FAILED; STOP_WITH_BACKUP='+str(saved))
    r=wei_run(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    if r['rc']!=0:raise Stop('WEIDU_INSTALL_FAILED_DO_NOT_RETRY; BACKUP='+str(saved))
    after=preflight(root,'060',proof['patched_bcs_sha'])
    return {'status':'INSTALLED_060_EXPERIMENTAL','backup':str(saved),'target_bcs_sha256':proof['patched_bcs_sha'],'after':after}

def rollback(root:Path,*,guard=game_process_guard,backup=make_backup,runner=subprocess.run):
    guard();source_check()
    staged=safe_file(root,STAGED_BCS).read_bytes();target_sha=sha(staged)
    before=preflight(root,'060',target_sha)
    if safe_file(root,TP2).read_text(encoding='utf8')!=TP2_TEXT:raise Stop('TP2_DRIFT')
    safe_file(root,EXE,100000)
    saved=backup(root,before,'PRE_ROLLBACK')
    guard();preflight(root,'060',target_sha)
    r=wei_run(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    if r['rc']!=0:raise Stop('ROLLBACK_FAILED_DO_NOT_RETRY;BACKUP='+str(saved))
    after=preflight_after_rollback(root)
    return {'status':'ROLLED_BACK_TO_056','backup':str(saved),'after':after}

def preflight_after_rollback(root:Path):
    # Stage folder may still exist from WeiDU; never delete it automatically.
    if not LAST_056.search(last_mod(root)):raise Stop('ROLLBACK_LAST_NOT_056')
    if sha(safe_file(root,BCS_REL).read_bytes())!=OLD_BCS_SHA or sha(safe_file(root,LUA_REL).read_bytes())!=LUA_SHA:
        raise Stop('ROLLBACK_FILES_NOT_056')
    return {'last_056':True,'bcs_056_sha':OLD_BCS_SHA}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',nargs='?',choices=('status','preflight','install','rollback'),default='status')
    ap.add_argument('--yes',action='store_true');ap.add_argument('--confirm',default='')
    args=ap.parse_args();root=ROOT
    try:
        if args.mode=='status':
            print('BGXAI060 READ-ONLY STATUS',json.dumps({'last':last_mod(root),
               '056_bcs_sha':sha(safe_file(root,BCS_REL).read_bytes())==OLD_BCS_SHA,
               '056_lua_sha':sha(safe_file(root,LUA_REL).read_bytes())==LUA_SHA}))
            return 0
        if args.mode=='preflight':
            print('BGXAI060 READ-ONLY',json.dumps(preflight(root,'056')))
            _,report=proposal(root);print('COMPILED BAF VERIFIED',json.dumps(report))
            return 0
        if not args.yes or args.confirm!='BGXAI_060_EXPERIMENTAL':
            raise Stop('EXPLICIT_--yes_AND_--confirm_BGXAI_060_EXPERIMENTAL_REQUIRED')
        outcome=install(root) if args.mode=='install' else rollback(root)
        print(json.dumps(outcome,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,Stop,UnicodeError,subprocess.TimeoutExpired) as exc:
        print('BGXAI060 STOP',exc);return 2
if __name__=='__main__':sys.exit(main())
