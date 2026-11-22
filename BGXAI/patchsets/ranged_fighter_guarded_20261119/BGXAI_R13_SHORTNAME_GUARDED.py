#!/usr/bin/env python3
"""BGXAI R13 short-resref repair. One existing updater entrypoint only.

The original R13 WeiDU component stays installed. This *separate* consent-gated,
last-only WeiDU component adds exactly one engine-loadable M_BGXD13.lua (8-char
resref). Preflight and status are read-only. No automatic installs or rollback.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE = Path(__file__).with_name('M_BGXD13.lua')
SOURCE_SHA = 'c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511'
PREVIOUS_SHA = '5c77a460d6b429cec6f9f81e7bf6883ee1f59474cfb95778091ab769302ef414'
INSTALL_TOKEN = 'INSTALL_BGXAI_R13_SHORTNAME_FIX'
ROLLBACK_TOKEN = 'ROLLBACK_BGXAI_R13_SHORTNAME_FIX'
MODULE = 'override/M_BGXD13.lua'
PREVIOUS = 'override/M_BGXTDEF13.lua'
OLD_PROOF = 'BGXTDEF13/PROOF.json'
DIR = 'BGXTD14'
STAGED = 'BGXTD14/staged/M_BGXD13.lua'
TP2 = 'BGXTD14/setup-BGXTD14.tp2'
EXE = 'setup-BGXTD14.exe'
PROOF = 'BGXTD14/PROOF.json'
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
OLD_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXTDEF13[/\\]SETUP-BGXTDEF13[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
NEW_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXTD14[/\\]SETUP-BGXTD14[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
BASELINE = {
 'override/M___EEex.lua':'e52ae61c29edb6f4a771184939d6153206f76c20d3e2522dfa158c6c943aa6cf',
 'EEex_scripts/EEex_Action.lua':'7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da',
 'override/M_BGXWP.lua':'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36',
 'override/M_BGXW2.lua':'dab7b3f5e55307088090666cb9d47989385c6895820cdf6a860e4db0f1b6b053',
 'override/M_BGXW4.lua':'79f57787be045732352582d531ce69f2485504947204bf553fa8a04a95c6595e',
}
TP2_TEXT = (
 'BACKUP ~BGXTD14/backup~\n'
 'AUTHOR ~BGXAI guarded Lua resource-name correction, passive only~\n'
 'BEGIN ~BGXTD14 passive 8-character M_BGXD13.lua observer~\n'
 'COPY ~BGXTD14/staged/M_BGXD13.lua~ ~override/M_BGXD13.lua~\n'
)
BLOCKED_COMMANDS = (b'SelectWeaponAbility(',b'ClearActions(',b'ActionOverride(',b'XEquipItem(',
 b'FillSlot(',b'SetGlobal(',b'Attack(',b'Stop(',b'CreateCreature(',b'SetGlobalTimer(')

def alias(p:Path)->bool:
    check=getattr(p,'is_junction',None)
    return p.is_symlink() or bool(check and check())

def regular(root:Path,relative:str)->Path:
    p=root
    for piece in Path(relative).parts:
        if piece in ('','.','..') or '/' in piece or '\\' in piece:
            raise ValueError('BAD_PATH_COMPONENT:'+relative)
        p=p/piece
        if alias(p):raise ValueError('REPARSE_PATH_STOP:'+relative)
    return p

def sha(p:Path)->str:
    if alias(p) or not p.is_file():raise ValueError('FILE_MISSING_OR_LINK:'+str(p))
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def game(root:Path)->None:
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(GAME)):
        raise ValueError('ONLY_EXACT_WINDOWS_GAME_SUPPORTED')
    if alias(root) or not root.is_dir() or not regular(root,'chitin.key').is_file():
        raise ValueError('INVALID_EET_GAME')

def sources()->None:
    if len('M_BGXD13')>8 or len('M_BGXD13')<3:
        raise ValueError('SHORT_RESREF_INVALID')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('SHORT_SOURCE_SHA_MISMATCH')
    data=SOURCE.read_bytes()
    if len(data)>50000 or b'\x00' in data or any(b in data for b in BLOCKED_COMMANDS):
        raise ValueError('SOURCE_NOT_PASSIVE')
    if data.count(b'EEex_Action_AddSpriteStartedActionListener(R.on_started)')!=1:
        raise ValueError('LISTENER_NOT_SINGLE')
    if b'm_nResistMissile' not in data or b'BGXTargetDefenseR13.registered==true' not in data:
        raise ValueError('SHORTNAME_OR_MISSILE_GUARD_MISSING')

def baseline(root:Path)->dict:
    out={}
    for rel,digest in BASELINE.items():
        h=sha(regular(root,rel))
        if h!=digest:raise ValueError('BASELINE_SHA_MISMATCH:'+rel)
        out[rel]=h
    if sha(regular(root,PREVIOUS))!=PREVIOUS_SHA:
        raise ValueError('INSTALLED_R13_SOURCE_DRIFT')
    proofPath=regular(root,OLD_PROOF)
    if not proofPath.is_file():raise ValueError('R13_INSTALL_PROOF_MISSING')
    proof=json.loads(proofPath.read_text(encoding='utf-8'))
    if proof.get('sourceSha256')!=PREVIOUS_SHA or proof.get('status')!='BGXTD13_INSTALLED_AWAITING_LIVE_TEST':
        raise ValueError('R13_PREVIOUS_PROOF_UNVERIFIED')
    return out

def weidu_last(root:Path)->str:
    p=regular(root,'WeiDU.log')
    if not p.is_file():raise ValueError('WEIDU_LOG_MISSING')
    entries=[x.strip() for x in p.read_text(encoding='utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('~')]
    return entries[-1] if entries else 'NONE'

def processes()->None:
    if os.name!='nt':raise ValueError('WINDOWS_REQUIRED')
    p=subprocess.run(['tasklist','/FO','CSV','/NH'],stdin=subprocess.DEVNULL,
      capture_output=True,text=True,errors='replace',timeout=25)
    if p.returncode:raise ValueError('TASKLIST_FAILED')
    found={r[0].strip().lower() for r in csv.reader(io.StringIO(p.stdout)) if r}
    blocked={'baldur.exe','bgmain.exe','infinityloader.exe','weidu.exe',
      'setup-enhanced-powergaming-scripts.exe','setup-bgxtdef13.exe','setup-bgxtd14.exe'}
    if found&blocked:raise ValueError('GAME_OR_WEIDU_RUNNING')

def validate_weidu(root:Path)->Path:
    p=regular(root,WEIDU_EXE)
    if not p.is_file() or not 50000<p.stat().st_size<70000000:
        raise ValueError('NATIVE_WEIDU_UNAVAILABLE')
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('WEIDU_NOT_PE_EXE')
    return p

def outside_dir()->Path:
    h=os.environ.get('USERPROFILE')
    if not h:raise ValueError('USERPROFILE_NOT_SET')
    p=Path(h)/'Documents'/'BGXAI_BACKUPS'
    if alias(p) or alias(p.parent):raise ValueError('BACKUP_REPARSE_STOP')
    return p

def preflight(root:Path)->dict:
    game(root);sources();processes();core=baseline(root);validate_weidu(root)
    for rel in (DIR,MODULE,STAGED,TP2,EXE,PROOF):
        p=regular(root,rel)
        if p.exists():raise ValueError('R13_SHORTNAME_FIX_PATH_ALREADY_EXISTS:'+rel)
    last=weidu_last(root)
    if not OLD_LAST.match(last):raise ValueError('R13_NOT_LAST_WEIDU_NO_REPAIR')
    return {'schema':'BGXAI_R13_SHORTNAME_PREFLIGHT_V1',
      'status':'BGXTD14_SHORTNAME_PREFLIGHT_PASS_NO_INSTALL',
      'installedOriginalR13Sha':PREVIOUS_SHA,'sourceSha256':SOURCE_SHA,
      'currentWeiDULast':last,'baselineVerified':len(core),
      'correctedResource':'M_BGXD13.lua','correctedResrefLength':8,
      'gameplayResourcesModified':False,'installAuthorized':False,
      'weaponSwitchAuthorized':False,'runtimeVerified':False}

def status(root:Path)->dict:
    game(root);sources();baseline(root)
    p=regular(root,MODULE)
    last=weidu_last(root)
    if not p.exists():
        status='BGXTD14_NOT_INSTALLED'
    elif sha(p)==SOURCE_SHA and NEW_LAST.match(last):
        status='BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST'
    else:raise ValueError('UNVERIFIED_SHORTNAME_MODULE_OR_WEIDU_LAST')
    return {'schema':'BGXAI_R13_SHORTNAME_STATUS_V1','status':status,
      'sourceSha256':SOURCE_SHA,'currentWeiDULast':last,
      'gameplayResourcesModifiedByStatus':False,'weaponSwitchAuthorized':False}

def backup(root:Path)->Path:
    parent=outside_dir();parent.mkdir(parents=True,exist_ok=True)
    dest=parent/('PRE_BGXTD14_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    for rel in ('WeiDU.log','chitin.key',PREVIOUS,OLD_PROOF,*BASELINE.keys()):
        src=regular(root,rel)
        if not src.is_file():raise ValueError('BACKUP_SOURCE_UNREADABLE:'+rel)
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if sha(target)!=sha(src):raise ValueError('BACKUP_VERIFY_FAIL:'+rel)
    return dest

def run_weidu(root:Path,uninstall:bool=False)->None:
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    done=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
      text=True,errors='replace',timeout=180)
    out=((done.stdout or '')+'\n'+(done.stderr or ''))[-1500:]
    if done.returncode or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',out):
        raise ValueError('WEIDU_FAILED:'+out)

def install(root:Path,token:str)->dict:
    if token!=INSTALL_TOKEN:raise ValueError('INSTALL_TOKEN_NOT_CONFIRMED')
    preflight(root)
    b=backup(root)
    processes();sources();baseline(root)
    if not OLD_LAST.match(weidu_last(root)):
        raise ValueError('WEIDU_ORDER_CHANGED_AFTER_BACKUP')
    stage=regular(root,STAGED);stage.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SOURCE,stage)
    if sha(stage)!=SOURCE_SHA:raise ValueError('STAGED_SCRIPT_SHA_MISMATCH')
    tp=regular(root,TP2);tp.write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    exe=regular(root,EXE);shutil.copy2(validate_weidu(root),exe)
    if sha(exe)!=sha(regular(root,WEIDU_EXE)):
        raise ValueError('WEIDU_EXE_CHANGED')
    sources();baseline(root);processes()
    if not OLD_LAST.match(weidu_last(root)):
        raise ValueError('WEIDU_ORDER_CHANGED_BEFORE_INSTALL')
    run_weidu(root)
    if sha(regular(root,MODULE))!=SOURCE_SHA or not NEW_LAST.match(weidu_last(root)):
        raise ValueError('POSTINSTALL_SHORTNAME_OR_LAST_MISMATCH')
    baseline(root)
    proof={'schema':'BGXAI_R13_SHORTNAME_INSTALL_PROOF_V1',
      'status':'BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST',
      'originalR13Preserved':True,'sourceSha256':SOURCE_SHA,
      'externalBackup':str(b),
      'installationUtc':datetime.now(timezone.utc).isoformat()}
    regular(root,PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return {**proof,'gameplayResourcesModified':True,'weaponSwitchAuthorized':False,
      'next':'VERIFY_SESSION_READY_AND_DEFENSE_IN_GAME'}

def rollback(root:Path,token:str)->dict:
    if token!=ROLLBACK_TOKEN:raise ValueError('ROLLBACK_TOKEN_NOT_CONFIRMED')
    game(root);sources();processes();baseline(root)
    if not NEW_LAST.match(weidu_last(root)):
        raise ValueError('SHORTNAME_FIX_NOT_LAST_WEIDU')
    if sha(regular(root,MODULE))!=SOURCE_SHA:
        raise ValueError('SHORTNAME_INSTALLED_SOURCE_DRIFT')
    proofPath=regular(root,PROOF)
    if not proofPath.is_file():raise ValueError('SHORTNAME_INSTALL_PROOF_MISSING')
    proof=json.loads(proofPath.read_text(encoding='utf-8'))
    b=Path(proof.get('externalBackup',''))
    if not b.is_dir() or alias(b) or proof.get('sourceSha256')!=SOURCE_SHA:
        raise ValueError('SHORTNAME_BACKUP_UNTRUSTED')
    for rel,expected in BASELINE.items():
        if sha(regular(b,rel))!=expected:raise ValueError('BACKUP_BASELINE_CHANGED:'+rel)
    if sha(regular(b,PREVIOUS))!=PREVIOUS_SHA or not OLD_LAST.match(weidu_last(b)):
        raise ValueError('BACKUP_ORIGINAL_R13_NOT_VERIFIED')
    if not regular(b,'chitin.key').is_file():raise ValueError('BACKUP_CHITIN_NOT_FOUND')
    run_weidu(root,uninstall=True)
    if regular(root,MODULE).exists():raise ValueError('WEIDU_UNINSTALL_INCOMPLETE')
    baseline(root)
    if not OLD_LAST.match(weidu_last(root)):
        raise ValueError('ORIGINAL_R13_NOT_LAST_AFTER_FIX_ROLLBACK')
    return {'status':'BGXTD14_ROLLBACK_LAST_ONLY_VERIFIED','weaponSwitchAuthorized':False,
      'gameplayResourcesModified':True,'originalR13Preserved':True}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--game',default=str(GAME))
    ap.add_argument('--mode',choices=('menu','status','preflight','install','rollback'),default='menu')
    args=ap.parse_args();root=Path(args.game)
    try:
        if args.mode=='menu':
            print('BGXTD14 8-char Lua fix: 1=status (RO), 2=preflight (RO), 3=install (typed), 4=rollback (typed), 0=exit')
            option=input('Choice [2]: ').strip() or '2'
            args.mode={'1':'status','2':'preflight','3':'install','4':'rollback','0':'exit'}.get(option,'INVALID')
        if args.mode=='exit':print('No game changes.');return 0
        if args.mode=='status':out=status(root)
        elif args.mode=='preflight':out=preflight(root)
        elif args.mode=='install':
            print('This installs ONLY override/M_BGXD13.lua, preserving the original R13 component.')
            token=input('Type '+INSTALL_TOKEN+' exactly; ENTER cancels: ').strip()
            out=install(root,token)
        elif args.mode=='rollback':
            print('Uninstall ONLY the last BGXTD14 WeiDU component, preserving R13.')
            token=input('Type '+ROLLBACK_TOKEN+' exactly; ENTER cancels: ').strip()
            out=rollback(root,token)
        else:raise ValueError('UNRECOGNIZED_MENU_OPTION')
        print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'BGXTD14_STOP','reason':str(e),
          'weaponSwitchAuthorized':False},ensure_ascii=False,indent=2))
        return 2

if __name__=='__main__':sys.exit(main())
