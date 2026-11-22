#!/usr/bin/env python3
"""BGXAI R13 optional passive target-defense EEex observer.

All user-facing entry points are reached through the *existing* BGXAI_UPDATE.cmd.
Status and preflight read only; installing or uninstalling game resources requires
exact typed confirmation, a verified external backup, and guarded WeiDU.
Never issues an in-game command. SOURCE ONLY until explicitly deployed.
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
SCRIPT = Path(__file__).with_name('M_BGXTDEF13.lua')
SCRIPT_SHA = 'eb764346f0c523790658320938a2739d873dbbdb59a93479e4f47e1f0edac2f3'
INSTALL_TOKEN = 'INSTALL_BGXAI_R13_PASSIVE_TARGET'
ROLLBACK_TOKEN = 'ROLLBACK_BGXAI_R13_PASSIVE_TARGET'
MODULE = 'override/M_BGXTDEF13.lua'
STAGED = 'BGXTDEF13/staged/M_BGXTDEF13.lua'
TP2 = 'BGXTDEF13/setup-BGXTDEF13.tp2'
EXE = 'setup-BGXTDEF13.exe'
PROOF = 'BGXTDEF13/PROOF.json'
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXTDEF13[/\\]SETUP-BGXTDEF13[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
BASELINE = {
    'override/M___EEex.lua': 'e52ae61c29edb6f4a771184939d6153206f76c20d3e2522dfa158c6c943aa6cf',
    'EEex_scripts/EEex_Action.lua': '7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da',
    'override/M_BGXWP.lua': 'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36',
    'override/M_BGXW2.lua': 'dab7b3f5e55307088090666cb9d47989385c6895820cdf6a860e4db0f1b6b053',
    'override/M_BGXW4.lua': '79f57787be045732352582d531ce69f2485504947204bf553fa8a04a95c6595e',
}
TP2_TEXT = (
    'BACKUP ~BGXTDEF13/backup~\n'
    'AUTHOR ~BGXAI passive-only target defense evidence, no battle commands~\n'
    'BEGIN ~BGXTDEF13 read-only target defense observer~\n'
    'COPY ~BGXTDEF13/staged/M_BGXTDEF13.lua~ ~override/M_BGXTDEF13.lua~\n'
)
BLOCKED_COMMANDS = (b'SelectWeaponAbility(', b'ClearActions(', b'ActionOverride(',
                    b'XEquipItem(', b'FillSlot(', b'SetGlobal(', b'Attack(', b'Stop(')

def alias(path: Path) -> bool:
    checker=getattr(path,'is_junction',None)
    return path.is_symlink() or bool(checker and checker())

def digest(path: Path) -> str:
    if alias(path) or not path.is_file():
        raise ValueError('REGULAR_FILE_REQUIRED:'+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_root(root: Path) -> None:
    if os.name != 'nt' or os.path.normcase(os.path.abspath(str(root))) != os.path.normcase(os.path.abspath(str(GAME))):
        raise ValueError('WRONG_WINDOWS_GAME_ROOT')
    if alias(root) or not root.is_dir() or alias(root/'chitin.key') or not (root/'chitin.key').is_file():
        raise ValueError('GAME_ROOT_UNVERIFIED')

def check_source() -> None:
    if digest(SCRIPT) != SCRIPT_SHA: raise ValueError('SOURCE_SHA256_MISMATCH')
    data = SCRIPT.read_bytes()
    if len(data)>50_000 or any(bad in data for bad in BLOCKED_COMMANDS):
        raise ValueError('OBSERVER_FORBIDDEN_COMMAND_OR_SIZE')
    if data.count(b'EEex_Action_AddSpriteStartedActionListener(R.on_started)') != 1:
        raise ValueError('SINGLE_PASSIVE_LISTENER_NOT_VERIFIED')

def check_baseline(root:Path) -> dict:
    result={}
    for relative, expected in BASELINE.items():
        p=root
        for part in Path(relative).parts:
            p=p/part
            if alias(p):raise ValueError('BASELINE_REPARSE_POINT:'+relative)
        found=digest(p)
        if found!=expected:raise ValueError('INSTALLED_BASELINE_CHANGED:'+relative)
        result[relative]=found
    return result

def weidu_last(root:Path) -> str:
    path=root/'WeiDU.log'
    if path.is_symlink() or not path.is_file():raise ValueError('WEIDU_LOG_MISSING')
    data=path.read_text(encoding='utf-8-sig',errors='replace').splitlines()
    entries=[row.strip() for row in data if row.lstrip().startswith('~')]
    return entries[-1] if entries else 'NONE'

def check_processes():
    if os.name!='nt':raise ValueError('WINDOWS_REQUIRED')
    proc=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,
        stdin=subprocess.DEVNULL,timeout=25,errors='replace')
    if proc.returncode!=0:raise ValueError('TASKLIST_FAILED')
    names={row[0].strip().lower() for row in csv.reader(io.StringIO(proc.stdout)) if row}
    blocked={'baldur.exe','bgmain.exe','infinityloader.exe','weidu.exe',
             'setup-enhanced-powergaming-scripts.exe','setup-bgxtdef13.exe'}
    if names & blocked:raise ValueError('GAME_OR_WEIDU_RUNNING')

def check_weidu(root:Path)->Path:
    p=root/WEIDU_EXE
    if alias(p) or not p.is_file() or not 50_000<p.stat().st_size<70_000_000:
        raise ValueError('WEIDU_BINARY_UNAVAILABLE')
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('WEIDU_PE_HEADER_INVALID')
    return p

def backup_dir()->Path:
    h=os.environ.get('USERPROFILE')
    if not h:raise ValueError('USERPROFILE_UNAVAILABLE')
    return Path(h)/'Documents'/'BGXAI_BACKUPS'

def report_dir()->Path:
    h=os.environ.get('USERPROFILE')
    if not h:raise ValueError('USERPROFILE_UNAVAILABLE')
    return Path(h)/'Documents'/'BGXAI_LIVE_REPORTS'

def preflight(root:Path)->dict:
    check_root(root);check_source();check_processes()
    baseline=check_baseline(root)
    check_weidu(root)
    for relative in ('BGXTDEF13',MODULE,STAGED,TP2,EXE,PROOF):
        p=root/relative
        if p.exists() or alias(p):raise ValueError('BGXTD13_PATH_ALREADY_EXISTS:'+relative)
    return {'schema':'BGXAI_R13_GUARDED_PREFLIGHT_V1',
            'status':'BGXTD13_PREFLIGHT_PASS_NO_INSTALL',
            'gameplayResourcesModified':False,'runtimeApiAuthenticated':False,
            'weaponSwitchAuthorized':False,'installAuthorized':False,
            'sourceSha256':SCRIPT_SHA,'baselineVerified':len(baseline),
            'currentWeiDULast':weidu_last(root),
            'optionalAttackInfoRequired':False}

def status(root:Path)->dict:
    check_root(root);check_source()
    baseline=check_baseline(root)
    p=root/MODULE
    if not p.exists():state='BGXTD13_NOT_INSTALLED'
    elif not alias(p) and digest(p)==SCRIPT_SHA:state='BGXTD13_PASSIVE_SOURCE_EXACT'
    else:raise ValueError('INSTALLED_R13_MODULE_UNKNOWN_HOLD')
    return {'schema':'BGXAI_R13_GUARDED_STATUS_V1','status':state,
            'gameplayResourcesModifiedByStatus':False,'weaponSwitchAuthorized':False,
            'baselineVerified':len(baseline),'currentWeiDULast':weidu_last(root),
            'runtimeEvidencePresent':(report_dir()/'BGXAI_R13_TARGET_DEFENSE_RAW.jsonl').is_file()}

def external_backup(root:Path)->Path:
    b=backup_dir()/('PRE_BGXTDEF13_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    if b.exists():raise ValueError('EXTERNAL_BACKUP_EXISTS')
    b.mkdir(parents=True)
    for rel in ('WeiDU.log','chitin.key',*BASELINE.keys()):
        original=root/rel
        if alias(original) or not original.is_file():raise ValueError('BACKUP_INPUT_MISSING:'+rel)
        dest=b/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,dest)
        if digest(original)!=digest(dest):raise ValueError('BACKUP_SHA_MISMATCH:'+rel)
    return b

def weidu(root:Path,uninstall:bool=False)->None:
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,text=True,
        capture_output=True,errors='replace',timeout=180)
    log=((p.stdout or '')+'\n'+(p.stderr or ''))[-1500:]
    if p.returncode or re.search(r'(?im)^\s*(ERROR:|FATAL ERROR:)',log):
        raise ValueError('WEIDU_OPERATION_FAILED:'+log)

def install(root:Path,authorization:str)->dict:
    if authorization!=INSTALL_TOKEN:raise ValueError('INSTALL_EXPLICIT_TOKEN_MISSING')
    check=preflight(root)
    backup=external_backup(root)
    # Preflight again after backup: abort on drift, without undoing any installation.
    check_processes();check_source();check_baseline(root)
    stage=root/STAGED
    stage.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SCRIPT,stage)
    if digest(stage)!=SCRIPT_SHA:raise ValueError('STAGE_HASH_MISMATCH')
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(check_weidu(root),root/EXE)
    if digest(root/EXE)!=digest(root/WEIDU_EXE):raise ValueError('WEIDU_COPY_CHANGED')
    check_baseline(root);check_processes()
    weidu(root)
    if digest(root/MODULE)!=SCRIPT_SHA or not LAST.match(weidu_last(root)):
        raise ValueError('POSTINSTALL_SHA_OR_WEIDU_LAST_STOP')
    check_baseline(root)
    proof={'schema':'BGXAI_R13_PASSIVE_INSTALL_PROOF_V1',
           'status':'BGXTD13_INSTALLED_AWAITING_LIVE_TEST',
           'sourceSha256':SCRIPT_SHA,'externalBackup':str(backup),
           'installationUtc':datetime.now(timezone.utc).isoformat()}
    (root/PROOF).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {**proof,'gameplayResourcesModified':True,'weaponSwitchAuthorized':False,
            'next':'NORMAL_GAME_RUNTIME_VALIDATION_REQUIRED'}

def rollback(root:Path,authorization:str)->dict:
    if authorization!=ROLLBACK_TOKEN:raise ValueError('ROLLBACK_EXPLICIT_TOKEN_MISSING')
    check_root(root);check_source();check_processes();check_baseline(root)
    if not LAST.match(weidu_last(root)):raise ValueError('NOT_LAST_WEIDU_ROLLBACK_FORBIDDEN')
    if digest(root/MODULE)!=SCRIPT_SHA:raise ValueError('INSTALLED_MODULE_DRIFT')
    proofPath=root/PROOF
    if alias(proofPath) or not proofPath.is_file():raise ValueError('INSTALL_PROOF_MISSING')
    proof=json.loads(proofPath.read_text(encoding='utf-8'))
    b=Path(proof.get('externalBackup',''))
    if proof.get('sourceSha256')!=SCRIPT_SHA or not b.is_dir() or alias(b):
        raise ValueError('EXTERNAL_BACKUP_UNTRUSTED')
    for rel,sha in BASELINE.items():
        if digest(b/rel)!=sha:raise ValueError('BACKUP_BASELINE_DRIFT:'+rel)
    if digest(b/'WeiDU.log')=='' or digest(b/'chitin.key')=='':
        raise ValueError('BACKUP_CORE_INVALID')
    weidu(root,uninstall=True)
    if (root/MODULE).exists():raise ValueError('WEIDU_UNINSTALL_INCOMPLETE')
    check_baseline(root)
    return {'status':'BGXTD13_LAST_ONLY_WEIDU_ROLLBACK_VERIFIED',
            'gameplayResourcesModified':True,'weaponSwitchAuthorized':False}

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--game',default=str(GAME))
    parser.add_argument('--mode',choices=('menu','preflight','status','install','rollback'),default='menu')
    args=parser.parse_args();root=Path(args.game)
    try:
        if args.mode=='menu':
            print('BGXAI R13 passive target defense: 1=status (RO), 2=preflight (RO), 3=install (typed), 4=rollback (typed), 0=exit')
            answer=input('Choice [2]: ').strip() or '2'
            args.mode={'1':'status','2':'preflight','3':'install','4':'rollback','0':'exit'}.get(answer,'INVALID')
        if args.mode=='exit':print('BGXTD13: no changes');return 0
        if args.mode=='preflight':out=preflight(root)
        elif args.mode=='status':out=status(root)
        elif args.mode=='install':
            print('This modifies ONLY override/M_BGXTDEF13.lua via WeiDU. Close the game first.')
            auth=input('Type '+INSTALL_TOKEN+' exactly; ENTER cancels: ').strip()
            out=install(root,auth)
        elif args.mode=='rollback':
            print('Last WeiDU only. Type exact token to authorize uninstall.')
            auth=input('Type '+ROLLBACK_TOKEN+' exactly; ENTER cancels: ').strip()
            out=rollback(root,auth)
        else:raise ValueError('INVALID_R13_MODE')
        print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except (ValueError,OSError,subprocess.SubprocessError) as ex:
        print(json.dumps({'status':'BGXTD13_STOP','reason':str(ex),
                          'weaponSwitchAuthorized':False},ensure_ascii=False,indent=2))
        return 2

if __name__=='__main__':sys.exit(main())
