#!/usr/bin/env python3
"""BGXAI 064 WeiDU install/rollback candidate, NEVER run outside verified updater.

This is a SOURCE-ONLY engineering candidate, NOT wired to the user's updater.
Live EET remains BGXAI 061. Every mutable action requires opt-in, exact live
SHA/WeiDU baseline, closed-game process guard and verified external backup.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import BGXAI64_PATCH as patch
import BGXAI64_PREFLIGHT_READONLY as read_only

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
BCS_SHA = read_only.BCS_SHA
LUA061_SHA = patch.PIN_061
LUA064_SHA = patch.PIN_064
CANDIDATE = Path(__file__).with_name('M_BX43_064_CANDIDATE.lua')
BCS = 'override/BDDEFAI.BCS'
LUA = 'override/M_BX43.lua'
STAGED_LUA = 'BGX64/staged/M_BX43.lua'
TP2 = 'BGX64/setup-BGX64.tp2'
EXE = 'setup-BGX64.exe'
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
BACKUP = ('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk',
          'lang/ru_RU/dialogf.tlk',BCS,LUA)
TP2_TEXT = (
    'BACKUP ~BGX64/backup~\n'
    'AUTHOR ~BGXAI safe same-area guard patch~\n'
    'BEGIN ~BGXAI 064 same area guard, Lua only~\n'
    'COPY ~BGX64/staged/M_BX43.lua~ ~override/M_BX43.lua~\n'
)
LAST064 = re.compile(r'^~(?:[^~]*[/\\])?BGX64[/\\]SETUP-BGX64\.TP2~(?=\s|$)',re.I)

class Stop(RuntimeError): pass

def digest(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def is_reparse(path: Path) -> bool:
    if path.is_symlink(): return True
    try: return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (FileNotFoundError,AttributeError): return False

def safe_file(root: Path, rel: str, minimum: int=1) -> Path:
    if not rel or rel.startswith(('/', '\\')) or ':' in rel or '\\' in rel or '..' in Path(rel).parts:
        raise Stop('UNSAFE_RELATIVE_PATH:'+rel)
    p=root/rel
    for q in (p,*p.parents):
        if is_reparse(q):raise Stop('REPARSE_POINT_BLOCKED:'+str(q))
        if q==root:break
    if not p.is_file() or p.stat().st_size<minimum:
        raise Stop('MISSING_OR_EMPTY:'+rel)
    return p

def source_check() -> bytes:
    if not CANDIDATE.is_file() or is_reparse(CANDIDATE):raise Stop('SOURCE_CANDIDATE_MISSING_OR_LINK')
    data=CANDIDATE.read_bytes()
    if digest(data)!=LUA064_SHA:raise Stop('CANDIDATE_064_SOURCE_SHA_MISMATCH')
    return data

def last_mod(root: Path) -> str:
    log=safe_file(root,'WeiDU.log').read_text('utf-8-sig',errors='replace')
    mods=[line.strip() for line in log.splitlines() if line.lstrip().startswith('~')]
    if not mods:raise Stop('WEIDU_EMPTY')
    return mods[-1]

def read_status_061(root:Path) -> dict:
    try:proof=read_only.check(root)
    except (ValueError,OSError) as exc:raise Stop('BASELINE_061_PREFLIGHT_STOP:'+str(exc)) from exc
    if proof['game_bcs_sha']!=BCS_SHA or proof['game_lua_sha']!=LUA061_SHA:
        raise Stop('BASELINE_PROOF_DRIFT')
    if (root/'BGX64').exists() or (root/EXE).exists():raise Stop('064_STAGE_COLLISION')
    return proof

def read_status_064(root:Path) -> dict:
    if not LAST064.search(last_mod(root)):raise Stop('WEIDU_LAST_NOT_064')
    if digest(safe_file(root,BCS).read_bytes())!=BCS_SHA:raise Stop('BCS_CHANGED_064')
    if digest(safe_file(root,LUA).read_bytes())!=LUA064_SHA:raise Stop('LUA_NOT_064')
    if safe_file(root,STAGED_LUA).read_bytes()!=safe_file(root,LUA).read_bytes():
        raise Stop('STAGED_LUA_NOT_LIVE')
    if safe_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:
        raise Stop('TP2_CHANGED')
    safe_file(root,EXE,100_000)
    return {'status':'INSTALLED_064_VERIFIED','last_weidu':last_mod(root),
            'bcs_sha256':BCS_SHA,'lua_sha256':LUA064_SHA}

def process_guard():
    if os.name!='nt':raise Stop('WINDOWS_REQUIRED_FOR_INSTALL')
    script=('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
         'Where-Object {$_.Name -match "^(Baldur|BaldursGate.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
         'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
                     capture_output=True,encoding='utf-8',errors='replace',text=True,
                     timeout=25,check=False)
    if p.returncode!=0 or p.stdout.strip():raise Stop('GAME_OR_WEIDU_ACTIVE_OR_QUERY_FAILED:'+p.stdout[:300])

def make_backup(root:Path, before:dict,label:str, parent:Path|None=None) -> Path:
    base=parent or Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI64_SAFE_BACKUPS'
    if is_reparse(base) or is_reparse(base.parent):raise Stop('BACKUP_FOLDER_REPARSE')
    # Backups must remain outside the game root, even if custom paths are injected.
    if root.resolve()==base.resolve() or root.resolve() in base.resolve().parents:
        raise Stop('BACKUP_INSIDE_GAME_BLOCKED')
    base.mkdir(parents=True,exist_ok=True)
    dest=base/(label+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    hashes={}
    for rel in BACKUP:
        src=safe_file(root,rel);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        h=digest(src.read_bytes())
        if digest(target.read_bytes())!=h:raise Stop('BACKUP_VERIFY_FAILURE:'+rel)
        hashes[rel]=h
    (dest/'BACKUP_PROOF.json').write_text(json.dumps({'state':before,'sha256':hashes},indent=2)+'\n',encoding='utf-8')
    return dest

def run_weidu(root:Path,uninstall:bool=False,runner=subprocess.run)->dict:
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(cmd,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
             encoding='utf-8',errors='replace',text=True,timeout=180,check=False)
    return {'rc':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-2000:]}

def install(root:Path,*,guard=process_guard,backup=make_backup,runner=subprocess.run,
            before_check=read_status_061) -> dict:
    guard();expected=source_check();root=root.resolve(strict=True)
    before=before_check(root)
    for rel in BACKUP:safe_file(root,rel)
    weidu=safe_file(root,WEIDU,100000)
    with weidu.open('rb') as exe:
        if exe.read(2)!=b'MZ':raise Stop('WEIDU_EXE_HEADER_INVALID')
    candidate,proof=patch.build_candidate(safe_file(root,LUA).read_bytes())
    if candidate!=expected or digest(candidate)!=LUA064_SHA:raise Stop('SOURCE_PATCH_DIFFERS')
    saved=backup(root,before,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('BACKUP_NOT_VERIFIED')
    guard();before_check(root)
    (root/STAGED_LUA).parent.mkdir(parents=True,exist_ok=False)
    (root/STAGED_LUA).write_bytes(candidate)
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(weidu,root/EXE)
    if digest((root/STAGED_LUA).read_bytes())!=LUA064_SHA:raise Stop('STAGING_SHA_FAILED;BACKUP='+str(saved))
    guard()  # fail if the game or WeiDU started during preparation
    r=run_weidu(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if r['rc']!=0:raise Stop('WEIDU_INSTALL_STOP_DO_NOT_RETRY;BACKUP='+str(saved))
    after=read_status_064(root)
    return {'status':'INSTALLED_064_EXPERIMENTAL','backup':str(saved),
            'patch_proof':proof,'after':after}

def rollback(root:Path,*,guard=process_guard,backup=make_backup,runner=subprocess.run) -> dict:
    guard();source_check();root=root.resolve(strict=True)
    before=read_status_064(root)
    saved=backup(root,before,'PRE_ROLLBACK')
    guard();read_status_064(root)
    guard()  # last no-running-game guard immediately before WeiDU
    r=run_weidu(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if r['rc']!=0:raise Stop('WEIDU_ROLLBACK_FAILED_DO_NOT_RETRY;BACKUP='+str(saved))
    after=read_only.check(root)
    if after['game_lua_sha']!=LUA061_SHA or after['game_bcs_sha']!=BCS_SHA:
        raise Stop('061_NOT_RESTORED')
    return {'status':'ROLLED_BACK_TO_061','backup':str(saved),'after':after}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description='BGXAI 064 SOURCE ONLY guarded WeiDU candidate')
    p.add_argument('mode',nargs='?',choices=('status','preflight','install','rollback'),default='status')
    p.add_argument('--yes',action='store_true')
    p.add_argument('--confirm',default='')
    p.add_argument('--game-root',type=Path,default=ROOT)
    a=p.parse_args(argv)
    try:
        if a.mode=='status':
            last=last_mod(a.game_root)
            if LAST064.search(last): proof=read_status_064(a.game_root)
            elif read_only.LAST061.search(last): proof=read_only.check(a.game_root)  # report restored 061 even if WeiDU left the BGX64 stage directory
            else: raise Stop('UNKNOWN_LAST_WEIDU_FOR_064')
            print(json.dumps({'mode':'READ_ONLY','proof':proof},ensure_ascii=False,indent=2))
            return 0
        if a.mode=='preflight':
            print(json.dumps({'proof':read_status_061(a.game_root),'candidate_sha':digest(source_check()),
                'authorized_to_install':False},indent=2))
            return 0
        phrase={'install':'INSTALL_BGXAI_064','rollback':'ROLLBACK_BGXAI_064'}[a.mode]
        if not a.yes or a.confirm!=phrase:
            raise Stop('EXPLICIT_APPROVAL_REQUIRED:'+phrase)
        # Actual Windows install/rollback MUST target the one user-confirmed EET root.
        # Alternative roots are allowed only in the read-only status/preflight commands,
        # never as a shortcut to another game or filesystem target.
        if a.game_root != ROOT:
            raise Stop('ACTUAL_INSTALL_REQUIRES_FIXED_EET_ROOT')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,Stop,UnicodeError,subprocess.TimeoutExpired) as exc:
        print('BGXAI064 STOP:',exc)
        return 2

if __name__=='__main__':sys.exit(main())
