#!/usr/bin/env python3
"""Isolated BGXW2 passive weapon/quiver observer for EXACT user EET.

Install/rollback mutate game ONLY with separately typed token, exact SHA,
external verified backup, closed game and WeiDU last-only rollback.
The observer is NOT a combat AI. R1.1, V6, EPS remain untouched.
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

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE = Path(__file__).with_name('M_BGXW2.lua')
SOURCE_SHA = 'dab7b3f5e55307088090666cb9d47989385c6895820cdf6a860e4db0f1b6b053'
R1_SHA = 'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36'
R1_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXWP[/\\]SETUP-BGXWP[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
R2_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXW2[/\\]SETUP-BGXW2[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
TOKEN_INSTALL = 'INSTALL_BGXW2_READONLY_SLOTS'
TOKEN_ROLLBACK = 'ROLLBACK_BGXW2_READONLY_SLOTS'
MODULE = 'override/M_BGXW2.lua'
STAGED = 'BGXW2/staged/M_BGXW2.lua'
TP2 = 'BGXW2/setup-BGXW2.tp2'
PROOF = 'BGXW2/PROOF.json'
EXE = 'setup-BGXW2.exe'
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
BASELINE = {
  'override/DPLAYER.BCS':'4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed',
  'override/BDDEFAI.BCS':'9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e',
  'override/WTASIGHT.BCS':'ec50ad2e91a33aad4e4b6b1bc33ac87f0f02f4af49f9649b5cad6c36faeaa403',
  'override/PRIEST1.BCS':'86a3c63799f09e7b9d51f6a61a893eff36f50ee3d6a3fe7eaa2dae97d2861589',
  'override/M_BX43.lua':'74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c',
  'override/M_BXFR.lua':'0ca56636c80095e1cca3e1191fa89e452aa98f55387f8975c3302cdbead6a6bb',
  'override/M_BGXWP.lua':R1_SHA,
}
# No BCS or incumbent Lua source is copied or edited.
TP2_DATA = ('BACKUP ~BGXW2/backup~\n'
 'AUTHOR ~BGXAI isolated passive read-only weapon slot evidence~\n'
 'BEGIN ~BGXW2 slot and ammo RAW observer (no combat actions)~\n'
 'COPY ~BGXW2/staged/M_BGXW2.lua~ ~override/M_BGXW2.lua~\n')


def digest(p:Path)->str:
    if p.is_symlink() or not p.is_file(): raise ValueError('SOURCE_NOT_REGULAR:'+str(p))
    with p.open('rb') as stream:
        h=hashlib.sha256()
        for block in iter(lambda:stream.read(65536),b''): h.update(block)
    return h.hexdigest()


def guard_root(root:Path):
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(ROOT)):
        raise ValueError('WRONG_WINDOWS_GAME_ROOT')
    if root.is_symlink() or not root.is_dir() or not (root/'chitin.key').is_file():
        raise ValueError('GAME_PATH_OR_KEY_MISSING')


def check_processes():
    if os.name!='nt':raise ValueError('WINDOWS_REQUIRED')
    proc=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,
        errors='replace',timeout=20,stdin=subprocess.DEVNULL)
    if proc.returncode:raise ValueError('CANNOT_VERIFY_GAME_CLOSED')
    names={row[0].strip().lower() for row in csv.reader(io.StringIO(proc.stdout)) if row}
    blocked={'baldur.exe','bgmain.exe','infinityloader.exe','weidu.exe',
      'setup-enhanced-powergaming-scripts.exe','setup-bgxwp.exe','setup-bgxw2.exe','setup-bgxw4.exe'}
    if names & blocked:raise ValueError('GAME_OR_WEIDU_RUNNING')


def check_source():
    if digest(SOURCE)!=SOURCE_SHA: raise ValueError('BGXW2_SOURCE_SHA_MISMATCH')
    b=SOURCE.read_bytes()
    for token in (b'ClearActions(',b'SelectWeaponAbility(',b'SetGlobal(',b'Attack(',b'FillSlot(',b'XEquipItem('):
        if token in b:raise ValueError('DISALLOWED_ACTION_IN_OBSERVER')


def report_dir()->Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_REQUIRED')
    return Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'


def backup_root()->Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_REQUIRED')
    return Path(home)/'Documents'/'BGXAI_BACKUPS'


def last(root:Path)->str:
    p=root/'WeiDU.log'
    if p.is_symlink() or not p.is_file():raise ValueError('WEIDU_LOG_UNAVAILABLE')
    lines=[x.strip() for x in p.read_text(encoding='utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('~')]
    return lines[-1] if lines else 'NONE'


def baseline(root:Path)->dict:
    out={}
    for key,sha in BASELINE.items():
        actual=digest(root/key)
        if actual!=sha:raise ValueError('BASELINE_SHA_DRIFT:'+key)
        out[key]=sha
    return out


def weidu_binary(root:Path)->Path:
    p=root/WEIDU
    if p.is_symlink() or not p.is_file() or p.stat().st_size>70_000_000:raise ValueError('WEIDU_BINARY_MISSING')
    with p.open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('WEIDU_BINARY_NOT_WINDOWS_PE')
    return p


def verify_game_and_r1(root:Path):
    guard_root(root)
    baseline(root)
    proof=root/'BGXWP'/'PROOF.json'
    if proof.is_symlink() or not proof.is_file():raise ValueError('BGXWP_PROOF_MISSING')
    old=json.loads(proof.read_text(encoding='utf-8'))
    if old.get('source_sha256')!=R1_SHA:raise ValueError('BGXWP_R1_PROOF_MISMATCH')


def preflight(root:Path)->dict:
    check_source();guard_root(root);check_processes();verify_game_and_r1(root)
    if not R1_LAST.match(last(root)):raise ValueError('BGXWP_MUST_BE_LAST_WEIDU')
    weidu_binary(root)
    for rel in (MODULE,STAGED,TP2,PROOF,EXE,'BGXW2'):
        p=root/rel
        if p.is_symlink() or p.exists():raise ValueError('BGXW2_PATH_ALREADY_EXISTS:'+rel)
    return {'status':'BGXW2_SOURCE_PREFLIGHT_PASS_NOT_INSTALLED','read_only':True,
        'game_modified':False,'source_sha256':SOURCE_SHA,
        'runtime_item_refs_verified':False,'last_weidu':last(root)}


def external_backup(root:Path)->Path:
    dest=backup_root()/('PRE_BGXW2_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if dest.exists() or dest.is_symlink():raise ValueError('BACKUP_COLLISION')
    dest.mkdir(parents=True)
    manifest={}
    for rel in ('WeiDU.log','chitin.key','BGXWP/PROOF.json',*BASELINE):
        src=root/rel
        if src.is_symlink() or not src.is_file():raise ValueError('BACKUP_INPUT_MISSING:'+rel)
        to=dest/rel;to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,to)
        manifest[rel]=digest(src)
        if digest(to)!=manifest[rel]:raise ValueError('BACKUP_SHA_FAILED:'+rel)
    (dest/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return dest


def run_weidu(root:Path,uninstall=False):
    prog=root/EXE
    cmd=[str(prog),'--noautoupdate','--no-exit-pause','--game',str(root),
        '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,errors='replace',
        stdin=subprocess.DEVNULL,timeout=180)
    msg=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode!=0 or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',msg):
        raise ValueError('WEIDU_R2_FAILED:'+msg[-850:])


def install(root:Path)->dict:
    preflight(root)
    out=report_dir();
    if out.is_symlink():raise ValueError('REPORT_DIR_SYMLINK')
    out.mkdir(parents=True,exist_ok=True)
    backup=external_backup(root)
    old_log=digest(root/'WeiDU.log')
    check_processes();verify_game_and_r1(root);check_source()
    if digest(root/'WeiDU.log')!=old_log or not R1_LAST.match(last(root)):
        raise ValueError('GAME_CHANGED_AFTER_BACKUP')
    stage=root/STAGED
    stage.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SOURCE,stage)
    if digest(stage)!=SOURCE_SHA:raise ValueError('STAGING_SHA_MISMATCH')
    (root/TP2).write_text(TP2_DATA,encoding='utf-8',newline='\n')
    shutil.copy2(weidu_binary(root),root/EXE)
    if digest(root/EXE)!=digest(root/WEIDU):raise ValueError('WEIDU_COPY_SHA_MISMATCH')
    check_processes();verify_game_and_r1(root)
    if digest(root/'WeiDU.log')!=old_log:raise ValueError('WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    # Persist rollback evidence BEFORE WeiDU; a partial native failure must not
    # leave an installed module without the proof required for last-only rollback.
    proof={'status':'BGXW2_INSTALL_PENDING_WEIDU',
           'source_sha256':SOURCE_SHA,'game_root':str(root),
           'external_backup':str(backup),'install_time_utc':datetime.now(timezone.utc).isoformat(),
           'game_modified':False,'weapon_switch_authorized':False}
    (root/PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    run_weidu(root)
    if digest(root/MODULE)!=SOURCE_SHA or not R2_LAST.match(last(root)):
        raise ValueError('POSTINSTALL_SHA_OR_LAST_MISMATCH')
    baseline(root)
    proof['status']='BGXW2_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'
    proof['game_modified']=True
    (root/PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return proof


def status(root:Path)->dict:
    guard_root(root);check_source();verify_game_and_r1(root)
    mod=root/MODULE
    if mod.is_symlink():raise ValueError('R2_OBSERVER_MODULE_SYMLINK')
    installed=mod.is_file() and digest(mod)==SOURCE_SHA
    if mod.exists() and not installed:raise ValueError('R2_OBSERVER_UNKNOWN_SOURCE')
    return {'status':'BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT' if installed else 'BGXW2_NOT_INSTALLED',
      'game_modified':False,'source_sha256':SOURCE_SHA if installed else None,
      'weidu_last':last(root),'runtime_verified':False}


def rollback(root:Path)->dict:
    guard_root(root);check_source();check_processes()
    if not R2_LAST.match(last(root)):raise ValueError('R2_NOT_LAST_WEIDU')
    if status(root)['status']!='BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT':raise ValueError('R2_STATUS_MISMATCH')
    proof=root/PROOF
    if proof.is_symlink() or not proof.is_file():raise ValueError('R2_PROOF_MISSING')
    rec=json.loads(proof.read_text(encoding='utf-8'))
    backup=Path(rec.get('external_backup',''))
    checks=backup/'SHA256.json'
    if not backup.is_dir() or checks.is_symlink() or not checks.is_file():raise ValueError('R2_BACKUP_UNVERIFIED')
    expected=json.loads(checks.read_text(encoding='utf-8'))
    for name,value in expected.items():
        if digest(backup/name)!=value:raise ValueError('R2_BACKUP_DRIFT:'+name)
    if rec.get('source_sha256')!=SOURCE_SHA:raise ValueError('R2_PROOF_SOURCE_MISMATCH')
    check_processes();baseline(root)
    run_weidu(root,uninstall=True)
    if (root/MODULE).exists() or not R1_LAST.match(last(root)):
        raise ValueError('POSTROLLBACK_R1_OR_MODULE_MISMATCH')
    baseline(root)
    return {'status':'BGXW2_LAST_ONLY_ROLLBACK_R1_RESTORED',
       'game_modified':True,'reports_preserved':True}



# The installed R1.1 onefile menu 159->5 already starts the ordinary game with
# BGXAI_WEAPON_CONSOLE_*.log capture; R2 reuses THAT exact channel, not a CMD.
CAPTURE_PREFIX='BGXAI_WEAPON_CONSOLE_'
R2_LOG='BGXAI_WEAPON_SLOTS_RAW_R2.jsonl'
R2_SCHEMA='BGXAI_WEAPON_SLOTS_RAW_R2'
R2_PREFIX='[BGXW2] '
MAX_CAPTURE=12_000_000


def _valid_r2(event:dict)->bool:
    if event.get('type')!='SLOTS' or event.get('schema')!=R2_SCHEMA:return False
    if type(event.get('seq')) is not int or not 1<=event['seq']<=64:return False
    if type(event.get('actor')) is not int or not 0<=event['actor']<=2147483647:return False
    if type(event.get('partyIndex')) is not int or not 0<=event['partyIndex']<=5:return False
    for flag in ('itemIdentityVerified','perSlotAPRVerified',
                 'manualOrderOriginVerified','epsQueueVerified','switchAuthorized'):
        if event.get(flag) is not False:return False
    if not isinstance(event.get('quickWeapons'),list) or len(event['quickWeapons'])!=4:return False
    if not isinstance(event.get('quivers'),list) or len(event['quivers'])!=4:return False
    if not isinstance(event.get('offhand'),dict):return False
    for k,nums in (('quickWeapons',(35,36,37,38)),('quivers',(11,12,13,14))):
        for i,num in enumerate(nums):
            x=event[k][i]
            if not isinstance(x,dict) or x.get('index')!=num:return False
            if x.get('identityVerified') is not False or x.get('ammoVerified') is not False:
                return False
            resref=x.get('resrefRaw')
            if resref is not None and (not isinstance(resref,str) or
                not re.fullmatch(r'[A-Za-z0-9_]{1,8}',resref)):
                return False
    return True


def _latest_capture(folder:Path)->Path|None:
    options=[]
    for p in folder.glob(CAPTURE_PREFIX+'*.log'):
        if p.is_symlink():continue
        if p.is_file():options.append((p.stat().st_mtime_ns,p.name,p))
    return max(options)[2] if options else None


def _r2_raw_direct(folder:Path)->dict|None:
    p=folder/R2_LOG
    if p.is_symlink():raise ValueError('R2_REPORT_SYMLINK')
    if not p.exists():return None
    st=p.stat()
    if not p.is_file() or not 1<=st.st_size<=MAX_CAPTURE:
        return {'status':'R2_DIRECT_REPORT_SIZE_HOLD','report_file':str(p),'game_modified':False}
    with p.open('rb') as f: data=f.read(MAX_CAPTURE+1)
    if len(data)!=st.st_size or p.stat().st_size!=st.st_size:
        raise ValueError('R2_REPORT_CHANGED_DURING_READ')
    session=ready=False
    actions={}
    for line in data.decode('utf-8','replace').splitlines():
        try: e=json.loads(line)
        except ValueError:continue
        if not isinstance(e,dict):continue
        if e.get('type')=='SESSION' and e.get('schema')==R2_SCHEMA and e.get('readOnly') is True:
            session=True;ready=False;actions={}
        elif session and e.get('type')=='READY' and e.get('schema')==R2_SCHEMA and e.get('hookRegistered') is True:
            ready=True
        elif session and ready and _valid_r2(e):
            seq=e['seq']
            if seq in actions and actions[seq]!=e:raise ValueError('R2_RAW_DUPLICATE_SEQ_CONFLICT')
            actions[seq]=e
    return {'status':'R2_DIRECT_RAW_READY' if ready and actions else 'R2_DIRECT_RAW_INCOMPLETE_HOLD',
        'report_file':str(p),'actions':len(actions),'game_modified':False,
        'item_identity_verified':False,'per_slot_apr_verified':False,
        'eps_manual_proven':False,'weapon_switch_authorized':False}


def collect_report(folder:Path)->dict:
    if folder.is_symlink() or not folder.is_dir():raise ValueError('REPORT_DIR_UNAVAILABLE')
    direct=_r2_raw_direct(folder)
    path=_latest_capture(folder)
    if path is None:
        return direct if direct else {'status':'R2_CONSOLE_CAPTURE_ABSENT','game_modified':False}
    st=path.stat()
    if not 1<=st.st_size<=MAX_CAPTURE:
        return {'status':'R2_CONSOLE_CAPTURE_SIZE_HOLD','game_modified':False}
    with path.open('rb') as f: raw=f.read(MAX_CAPTURE+1)
    if len(raw)!=st.st_size or path.stat().st_size!=st.st_size:
        raise ValueError('R2_CONSOLE_CAPTURE_CHANGED_WHILE_READING')
    session=None;ready=False;actions={};malformed=0
    for line in raw.decode('utf-8','replace').splitlines():
        pos=line.find(R2_PREFIX+'{')
        if pos<0:continue
        try:e=json.loads(line[pos+len(R2_PREFIX):])
        except ValueError:malformed+=1;continue
        if not isinstance(e,dict):malformed+=1;continue
        if e.get('type')=='SESSION' and e.get('schema')==R2_SCHEMA:
            if e.get('readOnly') is True:
                session=e;ready=False;actions={}
        elif e.get('type')=='READY' and e.get('schema')==R2_SCHEMA:
            if session and e.get('hookRegistered') is True:ready=True
        elif ready and e.get('type')=='SLOTS':
            if not _valid_r2(e):malformed+=1;continue
            seq=e['seq']
            if seq in actions and actions[seq]!=e:
                raise ValueError('R2_CONSOLE_DUPLICATE_SEQ_CONFLICT')
            actions[seq]=e
    if not session or not ready or not actions:
        return direct if direct else {'status':'R2_CONSOLE_INCOMPLETE_HOLD',
            'console_log':str(path),'malformed':malformed,'game_modified':False}
    if direct:
        return {**direct,'console_log':str(path),'console_actions':len(actions),
                'status':'R2_DIRECT_RAW_PRESERVED'}
    output=folder/R2_LOG
    lines=[session,{'type':'READY','schema':R2_SCHEMA,'hookRegistered':True,'source':'CONSOLE_CAPTURE'}]
    lines.extend(actions[x] for x in sorted(actions))
    # Exclusive-create protects an EEex-written file that appeared mid-collection.
    with output.open('x',encoding='utf-8',newline='\n') as f:
        for item in lines:
            f.write(json.dumps(item,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n')
    return {'status':'R2_CONSOLE_RAW_COLLECTED','report_file':str(output),
      'console_log':str(path),'actions':len(actions),'malformed':malformed,
      'game_modified':False,'item_identity_verified':False,
      'per_slot_apr_verified':False,'eps_manual_proven':False,
      'weapon_switch_authorized':False}


def collect_checked(root:Path)->dict:
    # Only reports are written; no game edits or runtime orders.
    check_processes()
    if status(root)['status']!='BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT':
        raise ValueError('R2_OBSERVER_NOT_INSTALLED')
    return collect_report(report_dir())

# R4 is a separate passive observer component; R2 (and everything before it)
# is immutable. This section adds optional commands to the EXISTING onefile menu.
R4_SOURCE=Path(__file__).with_name('M_BGXW4.lua')
R4_SHA='0d24779ee6cf7071c611c3b3d509ddb71f97e18eb95a6c5839e1a8441ee3f3e8'
R4_MODULE='override/M_BGXW4.lua'
R4_STAGE='BGXW4/staged/M_BGXW4.lua'
R4_TP2='BGXW4/setup-BGXW4.tp2'
R4_PROOF='BGXW4/PROOF.json'
R4_EXE='setup-BGXW4.exe'
R4_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXW4[/\\]SETUP-BGXW4[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
R4_INSTALL_TOKEN='INSTALL_BGXW4_READONLY_ACTIVE'
R4_ROLLBACK_TOKEN='ROLLBACK_BGXW4_READONLY_ACTIVE'
R4_TP2_DATA=('BACKUP ~BGXW4/backup~\n'
 'AUTHOR ~BGXAI separate passive active derived stats observer~\n'
 'BEGIN ~BGXW4 read-only current selected APR and proficiencies~\n'
 'COPY ~BGXW4/staged/M_BGXW4.lua~ ~override/M_BGXW4.lua~\n')

def r4_check_source():
    if digest(R4_SOURCE)!=R4_SHA:raise ValueError('R4_SOURCE_SHA_MISMATCH')
    b=R4_SOURCE.read_bytes()
    for token in (b'ClearActions(',b'SelectWeaponAbility(',b'SetGlobal(',
                  b'Attack(',b'FillSlot(',b'XEquipItem(',b'ActionOverride('):
        if token in b:raise ValueError('R4_FORBIDDEN_GAME_ACTION_IN_SOURCE')
    if len(b)>50000:raise ValueError('R4_SOURCE_TOO_LARGE')

def r4_assert_r2(root:Path):
    verify_game_and_r1(root)
    mod=root/MODULE
    if digest(mod)!=SOURCE_SHA:raise ValueError('R4_REQUIRES_INSTALLED_R2_EXACT')
    proof=root/PROOF
    if proof.is_symlink() or not proof.is_file():raise ValueError('R2_PROOF_MISSING')
    p=json.loads(proof.read_text(encoding='utf-8'))
    if p.get('source_sha256')!=SOURCE_SHA:raise ValueError('R2_PROOF_DRIFT')

def r4_preflight(root:Path)->dict:
    r4_check_source();guard_root(root);check_processes();r4_assert_r2(root)
    if not R2_LAST.match(last(root)):raise ValueError('R4_REQUIRES_R2_LAST_WEIDU')
    weidu_binary(root)
    for rel in (R4_MODULE,R4_STAGE,R4_TP2,R4_PROOF,R4_EXE,'BGXW4'):
        p=root/rel
        if p.is_symlink() or p.exists():raise ValueError('R4_PATH_ALREADY_EXISTS:'+rel)
    return {'status':'BGXW4_SOURCE_PREFLIGHT_PASS_NO_INSTALL',
       'game_modified':False,'source_sha256':R4_SHA,
       'last_weidu':last(root),'runtime_live_verified':False}

def r4_external_backup(root:Path)->Path:
    dst=backup_root()/('PRE_BGXW4_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if dst.exists() or dst.is_symlink():raise ValueError('R4_BACKUP_COLLISION')
    dst.mkdir(parents=True)
    verified={}
    for rel in ('WeiDU.log','chitin.key','BGXWP/PROOF.json',PROOF,MODULE,*BASELINE):
        p=root/rel
        if p.is_symlink() or not p.is_file():raise ValueError('R4_BACKUP_INPUT_INVALID:'+rel)
        x=dst/rel;x.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,x);verified[rel]=digest(p)
        if digest(x)!=verified[rel]:raise ValueError('R4_BACKUP_SHA_MISMATCH:'+rel)
    (dst/'SHA256.json').write_text(json.dumps(verified,indent=2)+'\n',encoding='utf-8')
    return dst

def r4_weidu(root:Path, uninstall=False):
    cmd=[str(root/R4_EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,errors='replace',
                     stdin=subprocess.DEVNULL,timeout=180)
    text=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode!=0 or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',text):
        raise ValueError('R4_WEIDU_FAILED:'+text[-800:])

def r4_install(root:Path)->dict:
    r4_preflight(root)
    directory=report_dir()
    if directory.is_symlink():raise ValueError('R4_REPORT_DIR_SYMLINK')
    directory.mkdir(parents=True,exist_ok=True)
    backup=r4_external_backup(root)
    oldlog=digest(root/'WeiDU.log')
    check_processes();r4_assert_r2(root);r4_check_source()
    if digest(root/'WeiDU.log')!=oldlog or not R2_LAST.match(last(root)):
        raise ValueError('R4_GAME_CHANGED_AFTER_BACKUP')
    stage=root/R4_STAGE
    stage.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(R4_SOURCE,stage)
    if digest(stage)!=R4_SHA:raise ValueError('R4_STAGING_SHA_MISMATCH')
    (root/R4_TP2).write_text(R4_TP2_DATA,encoding='utf-8',newline='\n')
    shutil.copy2(weidu_binary(root),root/R4_EXE)
    if digest(root/R4_EXE)!=digest(root/WEIDU):raise ValueError('R4_WEIDU_BINARY_SHA_MISMATCH')
    check_processes();r4_assert_r2(root)
    if digest(root/'WeiDU.log')!=oldlog:raise ValueError('R4_WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    proof={'status':'BGXW4_INSTALL_PENDING_WEIDU','source_sha256':R4_SHA,
      'external_backup':str(backup),'game_root':str(root),
      'install_time_utc':datetime.now(timezone.utc).isoformat(),
      'weapon_switch_authorized':False,'game_modified':False}
    (root/R4_PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    r4_weidu(root)
    if digest(root/R4_MODULE)!=R4_SHA or not R4_LAST.match(last(root)):
        raise ValueError('R4_POSTINSTALL_SHA_OR_LAST_MISMATCH')
    baseline(root)
    if digest(root/MODULE)!=SOURCE_SHA:raise ValueError('R2_CHANGED_AFTER_R4_INSTALL')
    proof['status']='BGXW4_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'
    proof['game_modified']=True
    (root/R4_PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return proof

def r4_status(root:Path)->dict:
    r4_check_source();guard_root(root);r4_assert_r2(root)
    p=root/R4_MODULE
    if p.is_symlink():raise ValueError('R4_MODULE_SYMLINK')
    exists=p.is_file()
    if exists and digest(p)!=R4_SHA:raise ValueError('R4_INSTALLED_SOURCE_DRIFT')
    return {'status':'BGXW4_PASSIVE_INSTALLED_SOURCE_EXACT' if exists else 'BGXW4_NOT_INSTALLED',
      'game_modified':False,'source_sha256':R4_SHA if exists else None,
      'weidu_last':last(root),'runtime_verified':False}

def r4_rollback(root:Path)->dict:
    r4_check_source();guard_root(root);check_processes()
    if not R4_LAST.match(last(root)):raise ValueError('R4_NOT_LAST_WEIDU')
    if r4_status(root)['status']!='BGXW4_PASSIVE_INSTALLED_SOURCE_EXACT':
        raise ValueError('R4_STATUS_MISMATCH')
    p=root/R4_PROOF
    if p.is_symlink() or not p.is_file():raise ValueError('R4_PROOF_MISSING')
    proof=json.loads(p.read_text(encoding='utf-8'))
    if proof.get('source_sha256')!=R4_SHA:raise ValueError('R4_PROOF_SOURCE_DRIFT')
    backup=Path(proof.get('external_backup',''))
    manifest=backup/'SHA256.json'
    if not backup.is_dir() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError('R4_EXTERNAL_BACKUP_MISSING')
    expected=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(expected,dict) or set(expected)!=set((
         'WeiDU.log','chitin.key','BGXWP/PROOF.json',PROOF,MODULE,*BASELINE)):
        raise ValueError('R4_BACKUP_MANIFEST_UNEXPECTED')
    for name,hashv in expected.items():
        if digest(backup/name)!=hashv:raise ValueError('R4_BACKUP_SHA_DRIFT:'+name)
    check_processes();r4_assert_r2(root)
    r4_weidu(root,uninstall=True)
    if (root/R4_MODULE).exists() or not R2_LAST.match(last(root)):
        raise ValueError('R4_POSTROLLBACK_R2_OR_MODULE_MISMATCH')
    r4_assert_r2(root)
    return {'status':'BGXW4_LAST_ONLY_ROLLBACK_R2_RESTORED',
            'game_modified':True,'reports_preserved':True}

R4_LOG='BGXAI_WEAPON_ACTIVE_RAW_R4.jsonl'
R4_SCHEMA='BGXAI_WEAPON_ACTIVE_R4'
R4_PREFIX='[BGXW4] '
R4_FIELDS={
 'm_nNumberOfAttacks','m_nTHAC0','m_nLevel1','m_nLevel2','m_nLevel3','m_nKit',
 'm_nSTR','m_nSTRExtra','m_nDEX','m_nDamageBonus',
 'm_nMeleeTHAC0Bonus','m_nMeleeDamageBonus','m_nMissileTHAC0Bonus','m_nMissileDamageBonus',
 'm_nHitBonus','m_bImprovedHaste','m_nLuck','m_nLevelDrain',
 'm_THAC0BonusRight','m_THAC0BonusLeft','m_DamageBonusRight','m_DamageBonusLeft',
 'm_nProficiencyLongSword','m_nProficiencyShortBow','m_nProficiencyQuarterStaff',
 'm_nProficiencySwordAndShield','m_nProficiency2Handed','m_nProficiencySingleWeapon',
 'm_nProficiency2Weapon'
}

def r4_valid_active(item:dict)->bool:
    if item.get('schema')!=R4_SCHEMA or item.get('type')!='ACTIVE':return False
    if type(item.get('seq')) is not int or not 1<=item['seq']<=64:return False
    if type(item.get('actor')) is not int or not 0<=item['actor']<=2147483647:return False
    if type(item.get('partyIndex')) is not int or not 0<=item['partyIndex']<=5:return False
    if item.get('status') not in ('RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS',
        'HOLD_APR_OR_SELECTED_SLOT_MISSING','HOLD_ACTIVE_STATS_ACCESS_FAILED'):
        return False
    for key in ('allBuffsObserved','allEffectsObserved','alternateSlotAPRVerified',
                'manualOrderProven','epsQueueProven','weaponSwitchAuthorized','dispatchAuthorized'):
        if item.get(key) is not False:return False
    stats=item.get('statsRaw')
    if not isinstance(stats,dict) or set(stats)!=R4_FIELDS:return False
    for v in stats.values():
        if v is not None and (type(v) is not int or not -2147483648<=v<=2147483647):return False
    apr=stats['m_nNumberOfAttacks']
    if apr is not None and not 0<=apr<=10:return False
    return True

def r4_extract_report(folder:Path)->dict:
    if folder.is_symlink() or not folder.is_dir():raise ValueError('R4_REPORT_FOLDER_INVALID')
    direct=folder/R4_LOG
    if direct.is_symlink():raise ValueError('R4_DIRECT_REPORT_SYMLINK')
    capture=None
    if direct.is_file() and direct.stat().st_size:
        if direct.stat().st_size>MAX_CAPTURE:raise ValueError('R4_DIRECT_REPORT_OVERSIZE')
        data=direct.read_text(encoding='utf-8',errors='replace')
        source='DIRECT_FILE'
        capture=direct
    else:
        capture=_latest_capture(folder)
        if capture is None:return {'status':'R4_LOG_NOT_FOUND','game_modified':False}
        if not 0<capture.stat().st_size<=MAX_CAPTURE:raise ValueError('R4_CONSOLE_SIZE_UNSAFE')
        data=capture.read_text(encoding='utf-8',errors='replace')
        source='CONSOLE_CAPTURE'
    seenSession=ready=False;actions={};malformed=0
    for line in data.splitlines():
        if source=='CONSOLE_CAPTURE':
            if R4_PREFIX not in line:continue
            line=line.split(R4_PREFIX,1)[1].strip()
        try:e=json.loads(line)
        except (ValueError,TypeError):malformed+=1;continue
        if not isinstance(e,dict) or e.get('schema')!=R4_SCHEMA:continue
        if e.get('type')=='SESSION':
            if e.get('readOnly') is not True:raise ValueError('R4_SESSION_NOT_PASSIVE')
            seenSession=True;ready=False;actions={}  # last session only
        elif e.get('type')=='READY':
            if not seenSession or e.get('hookRegistered') is not True:
                raise ValueError('R4_READY_WITHOUT_SESSION')
            ready=True
        elif e.get('type')=='ACTIVE':
            if not seenSession or not ready or not r4_valid_active(e):
                raise ValueError('R4_ACTION_MALFORMED_OR_UNAUTHORIZED')
            key=e['seq']
            if key in actions and actions[key]!=e:raise ValueError('R4_SEQ_CONFLICT')
            actions[key]=e
    if not seenSession or not ready or not actions:
        return {'status':'R4_CAPTURE_INCOMPLETE_HOLD','game_modified':False,
           'source':source,'actions':len(actions),'report_file':str(capture)}
    if sorted(actions)!=list(range(1,len(actions)+1)):
        raise ValueError('R4_SEQ_GAPS_OR_REORDER')
    if source=='CONSOLE_CAPTURE':
        if direct.exists():raise ValueError('R4_DIRECT_REPORT_COLLISION')
        with direct.open('x',encoding='utf-8') as dst:
            dst.write(json.dumps({'schema':R4_SCHEMA,'type':'SESSION','readOnly':True})+'\n')
            dst.write(json.dumps({'schema':R4_SCHEMA,'type':'READY','hookRegistered':True})+'\n')
            for n in sorted(actions):dst.write(json.dumps(actions[n],sort_keys=True)+'\n')
    return {'status':'BGXW4_ACTIVE_RAW_COLLECTED_READONLY',
      'game_modified':False,'report_file':str(direct),'source':source,
      'actions':len(actions),'malformed':malformed,
      'all_buffs_observed':False,'other_weapon_apr_verified':False,
      'manual_eps_proven':False,'weapon_switch_authorized':False}

def r4_collect_checked(root:Path)->dict:
    check_processes()
    if r4_status(root)['status']!='BGXW4_PASSIVE_INSTALLED_SOURCE_EXACT':
        raise ValueError('R4_NOT_INSTALLED')
    return r4_extract_report(report_dir())

def report(data:dict,filename='BGXW2_SETUP_R2.json'):
    out=report_dir();out.mkdir(parents=True,exist_ok=True)
    p=out/filename
    if p.is_symlink():raise ValueError('REPORT_FILE_SYMLINK')
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REPORT_FILE: '+str(p))


def menu(root:Path=ROOT)->int:
    try:
        print('BGXW2 passive fixed weapon/quiver slot reader; no weapon orders')
        print('1 - R2 preflight READ ONLY')
        print('2 - R2 install opt-in, NEW module only')
        print('3 - R2 status READ ONLY')
        print('4 - R2 rollback ONLY if LAST WeiDU')
        print('5 - R2 collect console RAW after exiting game')
        print('6 - R3 native ITM/SPL from KEY/BIFF READ ONLY (no game edits)')
        print('7 - R4 active stats/proficiencies preflight READ ONLY')
        print('8 - R4 install separate passive module (typed approval)')
        print('9 - R4 source status READ ONLY')
        print('10 - R4 collect RAW after leaving game')
        print('11 - R4 rollback LAST WeiDU ONLY')
        print('0 - cancel')
        answer=(input('BGXW2 choice [0]: ').strip() or '0')
        actions={'1':'preflight','2':'install','3':'status','4':'rollback','5':'collect','6':'native_itm',
                 '7':'r4_preflight','8':'r4_install','9':'r4_status',
                 '10':'r4_collect','11':'r4_rollback'}
        if answer=='0':return 0
        if answer not in actions:raise ValueError('UNKNOWN_R2_MENU_CHOICE')
        mode=actions[answer]
        if mode=='install':
            if input('Type '+TOKEN_INSTALL+' exactly: ').strip()!=TOKEN_INSTALL:
                raise ValueError('R2_INSTALL_NOT_AUTHORIZED')
            data=install(root)
        elif mode=='rollback':
            if input('Type '+TOKEN_ROLLBACK+' exactly: ').strip()!=TOKEN_ROLLBACK:
                raise ValueError('R2_ROLLBACK_NOT_AUTHORIZED')
            data=rollback(root)
        elif mode=='preflight':data=preflight(root)
        elif mode=='collect':data=collect_checked(root)
        elif mode=='native_itm':
            check_processes()
            if status(root)['status']!='BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT':
                raise ValueError('R3_REQUIRES_EXACT_R2_SOURCE')
            import BGXAI_WEAPON_NATIVE_ITM_R3_RO as native_itm
            data=native_itm.native_run(root)
        elif mode=='r4_preflight':data=r4_preflight(root)
        elif mode=='r4_install':
            if input('Type '+R4_INSTALL_TOKEN+' exactly: ').strip()!=R4_INSTALL_TOKEN:
                raise ValueError('R4_INSTALL_NOT_AUTHORIZED')
            data=r4_install(root)
        elif mode=='r4_status':data=r4_status(root)
        elif mode=='r4_collect':data=r4_collect_checked(root)
        elif mode=='r4_rollback':
            if input('Type '+R4_ROLLBACK_TOKEN+' exactly: ').strip()!=R4_ROLLBACK_TOKEN:
                raise ValueError('R4_ROLLBACK_NOT_AUTHORIZED')
            data=r4_rollback(root)
        else:data=status(root)
        report(data,'BGXW4_SETUP_R4.json' if mode.startswith('r4_') else 'BGXW2_SETUP_R2.json')
        print('STATUS: '+data['status'])
        return 0
    except Exception as exc:
        data={'status':'BGXW2_STOP','reason':f'{type(exc).__name__}: {exc}',
              'no_automatic_retry':True}
        try:report(data,'BGXW4_SETUP_R4.json' if 'mode' in locals() and mode.startswith('r4_') else 'BGXW2_SETUP_R2.json')
        except Exception as r:print('REPORT_STOP:'+str(r))
        print('BGXW2_STOP:'+str(exc))
        return 2


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--game',default=str(ROOT));arg=ap.parse_args()
    sys.exit(menu(Path(arg.game)))
