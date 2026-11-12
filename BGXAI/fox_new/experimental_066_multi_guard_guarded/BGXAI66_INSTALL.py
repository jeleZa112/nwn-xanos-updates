#!/usr/bin/env python3
"""Guarded 066 WeiDU Lua-only upgrade on verified 064; no automatic mutation.

Uses the EXISTING verified 064 BCS receiver. Safe rollback to 064 via WeiDU,
never manual overwrite of saved game resources. Intended ONLY for Windows 10
and fixed user-confirmed C:\\Games\\BG_EET_FOXX_NEW after opt-in.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import BGXAI64_INSTALL_SOURCE_ONLY as old
from build_066 import build

ROOT=old.ROOT
PIN064=old.LUA064_SHA
PINBCS=old.BCS_SHA
BASE=Path(__file__).with_name('M_BX43_064_BASELINE_READONLY.lua')
CANDIDATE=Path(__file__).with_name('M_BX43_066_CANDIDATE.lua')
LUA=old.LUA
BCS=old.BCS
WEIDU=old.WEIDU
STAGE='BGX66/staged/M_BX43.lua'
TP2='BGX66/setup-BGX66.tp2'
EXE='setup-BGX66.exe'
LAST066=re.compile(r'^~(?:[^~]*[/\\])?BGX66[/\\]SETUP-BGX66\.TP2~(?=\s|$)',re.I)
TP2_TEXT=('BACKUP ~BGX66/backup~\n'
          'AUTHOR ~BGXAI guarded upgrade from proven 064~\n'
          'BEGIN ~BGXAI 066 multi F frontline guard, Lua only~\n'
          'COPY ~BGX66/staged/M_BX43.lua~ ~override/M_BX43.lua~\n')
class Stop(RuntimeError):pass

def sha(raw):return hashlib.sha256(raw).hexdigest()
def source_check():
    if not BASE.is_file() or not CANDIDATE.is_file():raise Stop('SOURCE_MISSING')
    if old.is_reparse(BASE) or old.is_reparse(CANDIDATE):raise Stop('SOURCE_LINK')
    if sha(BASE.read_bytes())!=PIN064:raise Stop('BASE_064_SHA_MISMATCH')
    expected=build()
    if expected!=CANDIDATE.read_bytes():raise Stop('066_SOURCE_REPRODUCTION_FAILED')
    return sha(expected)

PIN066=source_check() # local sources checked before any status/mutation

def read_064(root):
    # The established 064 status check also enforces WeiDU-last BGX64, installed
    # 064 Lua SHA, BCS SHA, TP2, staged Lua SHA and setup-BGX64.exe presence.
    try:return old.read_status_064(root)
    except (OSError,ValueError,old.Stop) as exc:raise Stop('BASE_064_NOT_VERIFIED:'+str(exc)) from exc

def status066(root):
    if not LAST066.search(old.last_mod(root)):raise Stop('066_NOT_LAST_WEIDU')
    if sha(old.safe_file(root,BCS).read_bytes())!=PINBCS:raise Stop('066_BCS_MISMATCH')
    if sha(old.safe_file(root,LUA).read_bytes())!=PIN066:raise Stop('066_LUA_MISMATCH')
    if old.safe_file(root,STAGE).read_bytes()!=old.safe_file(root,LUA).read_bytes():raise Stop('066_STAGE_MISMATCH')
    if old.safe_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:raise Stop('066_TP2_MISMATCH')
    old.safe_file(root,EXE,100000)
    # Preserve 064 baseline stage for exact WeiDU rollback.
    if sha(old.safe_file(root,old.STAGED_LUA).read_bytes())!=PIN064:raise Stop('064_STAGE_DRIFT')
    return {'status':'INSTALLED_066_VERIFIED','last_weidu':old.last_mod(root),
            'bcs_sha256':PINBCS,'lua_sha256':PIN066}

def backup(root,before,label):
    path=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI66_SAFE_BACKUPS'
    return old.make_backup(root,before,label,parent=path)

def guard():old.process_guard()

def run(root,uninstall=False,runner=subprocess.run):
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(cmd,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
             encoding='utf-8',errors='replace',text=True,timeout=180,check=False)
    return {'rc':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-2000:]}

def install(root=ROOT,*,process_guard=guard,make_backup=backup,runner=subprocess.run):
    process_guard();pin=source_check();root=root.resolve(strict=True)
    before=read_064(root)
    if (root/'BGX66').exists() or (root/EXE).exists():raise Stop('066_STAGE_COLLISION')
    for rel in old.BACKUP:old.safe_file(root,rel)
    weidu=old.safe_file(root,WEIDU,100000)
    with weidu.open('rb') as f:
        if f.read(2)!=b'MZ':raise Stop('WEIDU_EXE_HEADER_INVALID')
    beforeLog=sha(old.safe_file(root,'WeiDU.log').read_bytes())
    data=CANDIDATE.read_bytes()
    if sha(data)!=pin:raise Stop('SOURCE_CHANGED')
    saved=make_backup(root,before,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('BACKUP_UNVERIFIED')
    process_guard();read_064(root)
    if sha(old.safe_file(root,'WeiDU.log').read_bytes())!=beforeLog:raise Stop('WEIDU_LOG_DRIFT')
    (root/STAGE).parent.mkdir(parents=True,exist_ok=False)
    (root/STAGE).write_bytes(data)
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(weidu,root/EXE)
    if sha(old.safe_file(root,STAGE).read_bytes())!=pin:raise Stop('STAGING_MISMATCH;BACKUP='+str(saved))
    process_guard()
    res=run(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
    if res['rc']!=0:raise Stop('WEIDU_INSTALL_FAILED_DO_NOT_RETRY;BACKUP='+str(saved))
    after=status066(root)
    return {'status':'INSTALLED_066_EXPERIMENTAL','backup':str(saved),'after':after}

def rollback(root=ROOT,*,process_guard=guard,make_backup=backup,runner=subprocess.run):
    process_guard();source_check();root=root.resolve(strict=True)
    before=status066(root)
    saved=make_backup(root,before,'PRE_ROLLBACK')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('BACKUP_UNVERIFIED')
    process_guard();status066(root)
    process_guard()
    res=run(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
    if res['rc']!=0:raise Stop('WEIDU_ROLLBACK_FAILED_DO_NOT_RETRY;BACKUP='+str(saved))
    after=read_064(root)
    return {'status':'ROLLED_BACK_TO_064_VERIFIED','backup':str(saved),'after':after}

def main(argv=None):
    p=argparse.ArgumentParser(description='BGXAI 066 guarded upgrade on verified 064')
    p.add_argument('mode',choices=('status','preflight','install','rollback'),default='status',nargs='?')
    p.add_argument('--yes',action='store_true')
    p.add_argument('--confirm',default='')
    p.add_argument('--game-root',type=Path,default=ROOT)
    args=p.parse_args(argv)
    try:
        if args.mode=='status':
            last=old.last_mod(args.game_root)
            state=status066(args.game_root) if LAST066.search(last) else read_064(args.game_root)
            print(json.dumps({'mode':'READ_ONLY','proof':state},ensure_ascii=False,indent=2));return 0
        if args.mode=='preflight':
            result={'mode':'READ_ONLY','proof':read_064(args.game_root),
                    'candidate_sha256':source_check(),'authorized_to_install':False}
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0
        phrase={'install':'INSTALL_BGXAI_066','rollback':'ROLLBACK_BGXAI_066'}[args.mode]
        if not args.yes or args.confirm!=phrase:raise Stop('EXPLICIT_APPROVAL_REQUIRED:'+phrase)
        if args.game_root != ROOT:raise Stop('ACTUAL_INSTALL_REQUIRES_FIXED_EET_ROOT')
        result=install(ROOT) if args.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (Stop,old.Stop,ValueError,OSError,UnicodeError,subprocess.TimeoutExpired) as exc:
        print('BGXAI066 STOP:',exc);return 2
if __name__=='__main__':sys.exit(main())
