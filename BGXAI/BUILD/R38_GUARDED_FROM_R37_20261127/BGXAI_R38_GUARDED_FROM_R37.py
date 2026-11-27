#!/usr/bin/env python3
"""BGXAI R38: guarded passive one-listener identity+inventory observer.

This never dispatches engine actions, arms BGXW3ARM or installs automatically.
Install and rollback require an exact user-entered token, guarded WeiDU and
SHA-verified external backups.  `--mode capture` launches the existing game.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(r'C:\Games\BG_EET_FOXX_NEW')
SCHEMA='BGXAI_R38_R37_PASSIVE_IDENTITY_GUARDED_V1'
OLD_SHA='5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6'
# SOURCE_SHA is exact R37+INV3+ID candidate. Pin is filled by released CI.
SOURCE_SHA='958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c'
SOURCE_BYTES=78927
R37_TOOL_SHA='b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d'
WEIDU_SHA='0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75'
OVERRIDE='override/M_BGXR27.lua'
DIR='BGXR38'
STAGED=DIR+'/staged/M_BGXR27.lua'
TP2=DIR+'/setup-BGXR38.tp2'
SETUP=DIR+'/setup-BGXR38.exe'
PROOF=DIR+'/PROOF.json'
R37_PROOF='BGXR37/PROOF.json'
INSTALL_TOKEN='INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37'
ROLLBACK_TOKEN='ROLLBACK_BGXAI_R38_RESTORE_R37_ONLY'
TP2_TEXT=(
    'BACKUP ~BGXR38/backup~\n'
    'AUTHOR ~BGXAI R38 source-only identity/inventory observer~\n'
    'BEGIN ~BGXR38 passive identity reuse one R37 callback~\n'
    'COPY ~BGXR38/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n'
)
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR38[/\\]SETUP-BGXR38[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
STATUS_PREFIXES=(b'[BGXR27] ',b'[BGXR37] ',b'[BGXINV3] ',b'[BGXID] ')
EXPECTED_SCHEMA=('BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
                 'BGXAI_R37_R33_R36_SINGLE_LISTENER_SOURCE_V1',
                 'BGXAI_BACKPACK16_R37_SINGLE_LISTENER_SOURCE_V1',
                 'BGXAI_XEQUIP_IDENTITY_RO_V1')

class Hold(ValueError):
    pass

def sha_bytes(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def sha(path:Path)->str:
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def load_r37(path:Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=26252:
        raise Hold('HOLD_R37_TOOL_SIZE_OR_PATH')
    if sha(path)!=R37_TOOL_SHA:
        raise Hold('HOLD_R37_TOOL_PIN_DRIFT')
    spec=importlib.util.spec_from_file_location('bgxai_r37_verified_helpers',str(path))
    if spec is None or spec.loader is None:
        raise Hold('HOLD_R37_TOOL_IMPORT_SPEC')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.SOURCE_SHA!=OLD_SHA or module.NATIVE_SHA!=WEIDU_SHA:
        raise Hold('HOLD_R37_TOOL_CONSTANTS_DRIFT')
    return module

def candidate_bytes(path:Path)->bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=SOURCE_BYTES:
        raise Hold('HOLD_R38_CANDIDATE_LENGTH_OR_PATH')
    data=path.read_bytes()
    if sha_bytes(data)!=SOURCE_SHA:
        raise Hold('HOLD_R38_CANDIDATE_SHA256_DRIFT')
    if data.count(b'EEex_Action_AddSpriteStartedActionListener,pilot.listener')!=1:
        raise Hold('HOLD_R38_LISTENER_NOT_EXACTLY_ONE')
    for tag in (b'[BGXR27]',b'[BGXR37]',b'[BGXINV3]',b'[BGXID]',
                b'"armAuthorized":false',b'"safeActionBoundaryVerified":false',
                b'"dispatchAuthorized":false',b'"inventoryMoveAuthorized":false'):
        if tag not in data: raise Hold('HOLD_R38_MISSING_READONLY_GUARD')
    comment_stripped=b'\n'.join(line.split(b'--',1)[0] for line in data.splitlines())
    for bad in (rb'\bXEquipItem\s*\(',rb'\bSetGlobal\s*\(',
                rb'\bClearActions\s*\(',rb'\bFillSlot\s*\(',
                rb'\bActionOverride\s*\(',rb'\bSelectWeaponAbility\s*\(',
                rb'\bos[.]execute\s*\('):
        if re.search(bad,comment_stripped):
            raise Hold('HOLD_R38_GAME_MUTATION_TOKEN')
    return data

def check_processes(old)->None:
    old.verify_processes()
    p=subprocess.run(['tasklist','/FO','CSV','/NH'],stdin=subprocess.DEVNULL,
       capture_output=True,text=True,errors='replace',timeout=25,check=False)
    if p.returncode: raise Hold('HOLD_TASKLIST_UNAVAILABLE')
    running={r[0].strip().lower() for r in csv.reader(io.StringIO(p.stdout)) if r}
    if 'setup-bgxr38.exe' in running:
        raise Hold('HOLD_R38_WEIDU_RUNNING')

def watched(old):
    # Preserve all old R37 watched resources plus the installed R37 proof.
    return (*old.WATCHED,R37_PROOF)

def snapshot(old,root):
    out={}
    for rel in watched(old):
        p=old.safe(root,rel)
        if not p.is_file():raise Hold('HOLD_WATCHED_FILE_MISSING:'+rel)
        out[rel]=old.sha(p)
    return out

def last_r38(old,root):
    old.protected_root(root,True)
    rows,log_sha=old.history(root)
    if len(rows)!=154 or not old.last_r37_history(rows[:-1]) or not LAST.match(rows[-1]):
        raise Hold('HOLD_R38_NOT_WEIDU_LAST_154')
    if old.sha(old.safe(root,OVERRIDE))!=SOURCE_SHA:
        raise Hold('HOLD_R38_ACTIVE_LUA_SHA_DRIFT')
    return rows,log_sha

def installed_proof(old,root):
    p=old.safe(root,PROOF)
    if not p.is_file() or p.stat().st_size>1_000_000:
        raise Hold('HOLD_R38_PROOF_MISSING')
    d=json.loads(p.read_text(encoding='utf-8'))
    if (type(d) is not dict or d.get('schema')!=SCHEMA or
        d.get('status')!='R38_PASSIVE_INSTALLED_AWAITING_RUNTIME' or
        d.get('sourceSha256')!=SOURCE_SHA or
        d.get('typedInstallApproved') is not True or
        d.get('installationPerformed') is not True or
        d.get('dispatchAuthorized') is not False or
        d.get('armAuthorized') is not False):
        raise Hold('HOLD_R38_PROOF_INVALID')
    return d

def preflight(old,root:Path,candidate:Path)->dict:
    old.protected_root(root,True)
    check_processes(old)
    rows,old_log=old.history(root)
    if not old.last_r37_history(rows):
        raise Hold('HOLD_R37_MUST_BE_LAST_153')
    if old.sha(old.safe(root,OVERRIDE))!=OLD_SHA:
        raise Hold('HOLD_R37_LIVE_MODULE_SHA_DRIFT')
    old.installed_proof(root)
    for rel in (DIR,STAGED,TP2,SETUP,PROOF):
        if old.safe(root,rel).exists():
            raise Hold('HOLD_R38_STAGING_COLLISION:'+rel)
    for rel,digest in old.BASELINE_SHA.items():
        if old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R37_BASELINE_DRIFT:'+rel)
    compiler=old.safe(root,'setup-enhanced-powergaming-scripts.exe')
    if not compiler.is_file() or old.sha(compiler)!=WEIDU_SHA:
        raise Hold('HOLD_NATIVE_WEIDU_BINARY_CHANGED')
    data=candidate_bytes(candidate)
    baseline=snapshot(old,root)
    return dict(schema=SCHEMA,status='R38_PREFLIGHT_PASS_NO_INSTALL',
        sourceSha256=sha_bytes(data),sourceBytes=len(data),
        weiduComponents=153,weiDULogSha256=old_log,
        baselineSnapshot=baseline,installed=False,typedInstallApproved=False,
        gameModified=False,ordersSent=0,dispatchAuthorized=False,
        armAuthorized=False,runtimeIdentityVerified=False,
        classKitItmUsabilityVerified=False,safeActionBoundaryVerified=False,
        manualEpsOriginVerified=False,gameplayMoveAuthorized=False)

def backup_to_external(old,root:Path,expected:dict)->Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    parent=Path(home)/'Documents'/'BGXAI_BACKUPS'
    if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):
        raise Hold('HOLD_EXTERNAL_BACKUP_PARENT_REPARSE')
    parent.mkdir(parents=True,exist_ok=True)
    dest=Path(tempfile.mkdtemp(prefix='PRE_BGXR38_',dir=parent))
    for rel,digest in expected.items():
        src=old.safe(root,rel);dst=old.safe(dest,rel)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if old.sha(dst)!=digest:
            raise Hold('HOLD_EXTERNAL_BACKUP_SHA_FAILED:'+rel)
    old.safe(dest,'SHA256.json').write_text(json.dumps(expected,indent=2),encoding='utf-8')
    return dest

def run_weidu(old,root:Path,uninstall:bool=False):
    exe=old.safe(root,SETUP)
    if not exe.is_file() or old.sha(exe)!=WEIDU_SHA:
        raise Hold('HOLD_R38_STAGED_WEIDU_BINARY_CHANGED')
    p=subprocess.run([str(exe),'--noautoupdate','--no-exit-pause',
        '--game',str(root),'--use-lang','ru_ru',
        '--force-uninstall' if uninstall else '--force-install','0'],
        cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
        text=True,errors='replace',timeout=240,check=False)
    transcript=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode or re.search(r'(?mi)^\s*(ERROR:|FATAL ERROR:)',transcript):
        raise Hold('HOLD_R38_WEIDU_MANUAL_REVIEW:'+transcript[-600:])

def install(old,root:Path,candidate:Path,token:str)->dict:
    if token!=INSTALL_TOKEN:
        raise Hold('HOLD_R38_EXACT_INSTALL_TOKEN_REQUIRED')
    ready=preflight(old,root,candidate)
    baseline=ready['baselineSnapshot']
    old.verify_snapshot(root,baseline)
    external=backup_to_external(old,root,baseline)
    check_processes(old)
    old.verify_snapshot(root,baseline)
    # From here: never silently retry or restore WeiDU-managed changes.
    old.safe(root,DIR).mkdir(parents=True,exist_ok=False)
    target=old.safe(root,STAGED)
    target.parent.mkdir(parents=True,exist_ok=False)
    target.write_bytes(candidate_bytes(candidate))
    old.safe(root,TP2).write_text(TP2_TEXT,encoding='ascii',newline='\n')
    shutil.copy2(old.safe(root,'setup-enhanced-powergaming-scripts.exe'),old.safe(root,SETUP))
    if old.sha(target)!=SOURCE_SHA or old.sha(old.safe(root,SETUP))!=WEIDU_SHA:
        raise Hold('HOLD_R38_STAGED_FILES_SHA_DRIFT')
    check_processes(old)
    old.verify_snapshot(root,baseline)
    proof=old.safe(root,PROOF)
    proof.write_text(json.dumps({'schema':SCHEMA,'status':'R38_PENDING_WEIDU',
       'sourceSha256':SOURCE_SHA,'externalBackup':str(external),
       'baselineSnapshot':baseline},indent=2),encoding='utf-8')
    run_weidu(old,root)
    last_r38(old,root)
    for rel,digest in baseline.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R38_UNRELATED_FILE_CHANGED_MANUAL_REVIEW:'+rel)
    result=dict(schema=SCHEMA,status='R38_PASSIVE_INSTALLED_AWAITING_RUNTIME',
        sourceSha256=SOURCE_SHA,sourceBytes=SOURCE_BYTES,
        externalBackup=str(external),baselineSnapshot=baseline,
        typedInstallApproved=True,installationPerformed=True,
        gameModified=True,installed=True,readOnly=True,ordersSent=0,
        dispatchAuthorized=False,armAuthorized=False,
        runtimeIdentityVerified=False,classKitItmUsabilityVerified=False,
        safeActionBoundaryVerified=False,manualEpsOriginVerified=False,
        gameplayMoveAuthorized=False)
    proof.write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def rollback(old,root:Path,token:str)->dict:
    if token!=ROLLBACK_TOKEN:
        raise Hold('HOLD_R38_EXACT_ROLLBACK_TOKEN_REQUIRED')
    last_r38(old,root)
    check_processes(old)
    proof=installed_proof(old,root)
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    parent=Path(home)/'Documents'/'BGXAI_BACKUPS'
    folder=Path(proof.get('externalBackup',''))
    if (folder.parent!=parent or not folder.name.startswith('PRE_BGXR38_') or
        not folder.is_dir() or folder.is_symlink() or
        (hasattr(folder,'is_junction') and folder.is_junction())):
        raise Hold('HOLD_R38_EXTERNAL_BACKUP_PROVENANCE')
    expected=json.loads(old.safe(folder,'SHA256.json').read_text(encoding='utf-8'))
    if expected!=proof.get('baselineSnapshot') or expected.get(OVERRIDE)!=OLD_SHA:
        raise Hold('HOLD_R38_BACKUP_MANIFEST_MISMATCH')
    old.verify_snapshot(folder,expected)
    for rel,digest in expected.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R38_ROLLBACK_UNRELATED_RESOURCE_DRIFT:'+rel)
    if old.sha(old.safe(root,SETUP))!=WEIDU_SHA:
        raise Hold('HOLD_R38_ROLLBACK_WEIDU_BINARY_DRIFT')
    check_processes(old)
    run_weidu(old,root,uninstall=True)
    rows,_=old.history(root)
    if not old.last_r37_history(rows) or old.sha(old.safe(root,OVERRIDE))!=OLD_SHA:
        raise Hold('HOLD_R38_ROLLBACK_MANUAL_REVIEW')
    for rel,digest in expected.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R38_ROLLBACK_RESOURCE_CHANGED:'+rel)
    return dict(schema=SCHEMA,status='R38_ROLLBACK_RESTORED_R37',
       gameModified=True,installed=False,ordersSent=0,
       dispatchAuthorized=False,armAuthorized=False)

def status(old,root:Path)->dict:
    old.protected_root(root,True)
    rows,log_sha=old.history(root)
    current=old.sha(old.safe(root,OVERRIDE))
    installed=(len(rows)==154 and old.last_r37_history(rows[:-1]) and
              LAST.match(rows[-1]) is not None and current==SOURCE_SHA)
    prior=(old.last_r37_history(rows) and current==OLD_SHA)
    if installed: installed_proof(old,root)
    return dict(schema=SCHEMA,
       status='R38_PRESENT_LAST_PASSIVE' if installed else
              'R38_NOT_INSTALLED_R37_PRESENT_LAST' if prior else
              'R38_HOLD_UNKNOWN_WEIDU_OR_LUA',
       weiduComponents=len(rows),weiDULogSha256=log_sha,
       liveModuleSha256=current,sourceSha256=SOURCE_SHA,
       installed=installed,readOnly=True,gameModified=False,
       runtimeIdentityVerified=False,safeActionBoundaryVerified=False,
       ordersSent=0,dispatchAuthorized=False,armAuthorized=False)

def parse_console(log:Path,exit_code:int)->dict:
    # Log may include unrelated engine lines; read only strict four tagged event types.
    if log.stat().st_size>64_000_000:
        raise Hold('HOLD_R38_LOG_OVER_64MB')
    sessions=[0,0,0,0]
    seen=[{}, {}, {}, {}]
    malformed=0
    statuses={}
    with log.open('rb') as stream:
      for raw in stream:
        present=[(i,p) for i,p in enumerate(STATUS_PREFIXES) if p in raw]
        if not present:continue
        if len(present)!=1:
            malformed+=1;continue
        i,tag=present[0]
        try:
            item=json.loads(raw.split(tag,1)[1].decode('utf-8-sig','strict').strip())
        except (UnicodeError,ValueError):
            malformed+=1;continue
        if type(item) is not dict or item.get('schema')!=EXPECTED_SCHEMA[i]:
            malformed+=1;continue
        if item.get('type')=='SESSION':
            sessions[i]+=1
            continue
        expected_type=('R27_SINGLE_CALLBACK','ADVISORY_CONTEXT',
                       'BACKPACK16_ADVISORY','IDENTITY_ADVISORY')[i]
        seq,party=item.get('seq'),item.get('partyIndex')
        if (item.get('type')!=expected_type or type(seq) is not int or
            not 1<=seq<=64 or type(party) is not int or not 0<=party<=5 or
            seq in seen[i] or item.get('readOnly') is not True or
            item.get('dispatchAuthorized') is not False or
            item.get('ordersSent')!=0):
            malformed+=1;continue
        if i==3 and (item.get('armAuthorized') is not False or
                     item.get('safeActionBoundaryVerified') is not False or
                     item.get('localsWritten')!=0):
            malformed+=1;continue
        if i==2 and (item.get('inventoryMoveAuthorized') is not False or
                     item.get('safeActionBoundaryVerified') is not False):
            malformed+=1;continue
        if i==1 and (item.get('weaponSwitchAuthorized') is not False or
                     item.get('safeActionBoundaryVerified') is not False):
            malformed+=1;continue
        seen[i][seq]={'partyIndex':party,'status':item.get('status')}
        if i==3:
            label=item.get('status')
            if type(label) is str and len(label)<90 and re.fullmatch(r'[A-Z0-9_]+',label):
                statuses[label]=statuses.get(label,0)+1
    full=bool(seen[0]) and all(set(x)==set(seen[0]) for x in seen)
    aligned=full and all(len({x[n]['partyIndex'] for x in seen})==1 for n in seen[0])
    jagan=any(x['partyIndex']==1 for x in seen[3].values())
    matched=any(x['partyIndex']==1 and x['status']=='RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM'
                for x in seen[3].values())
    ready=(exit_code==0 and malformed==0 and sessions[:3]==[1,1,1]
           and sessions[3]==0 and aligned and jagan)
    return dict(schema=SCHEMA,
       status='R38_RUNTIME_IDENTITY_OBSERVATIONS_READY_FOR_REVIEW' if ready
              else 'R38_RUNTIME_HOLD_MANUAL_REVIEW',
       counts={'r27':len(seen[0]),'r37':len(seen[1]),
               'inv3':len(seen[2]),'identity':len(seen[3])},
       sessionMarkers=sessions,alignedFourEvents=bool(aligned),
       malformedRows=malformed,jaganEventsObserved=jagan,
       jaganExactItemMatchObserved=matched,
       identityStatuses=statuses,
       originalExitCode=exit_code,readOnly=True,
       runtimeActorIdentityVerified=False,safeActionBoundaryVerified=False,
       manualEpsOriginVerified=False,gameModifiedByCapture=False,
       ordersSent=0,dispatchAuthorized=False,armAuthorized=False)

def capture(old,root:Path)->dict:
    last_r38(old,root)
    installed_proof(old,root)
    check_processes(old)
    loader=old.safe(root,'InfinityLoader.exe')
    if (not loader.is_file() or loader.is_symlink() or
        not 1024<loader.stat().st_size<70_000_000):
        raise Hold('HOLD_R38_LOADER_MISSING_OR_SIZE_INVALID')
    with loader.open('rb') as f:
        if f.read(2)!=b'MZ':raise Hold('HOLD_R38_LOADER_NOT_PE')
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    reports=Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'
    if reports.is_symlink() or (hasattr(reports,'is_junction') and reports.is_junction()):
        raise Hold('HOLD_REPORTS_DIR_REPARSE')
    reports.mkdir(parents=True,exist_ok=True)
    target=reports/('BGXAI_R38_CONSOLE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.log')
    with target.open('xb') as f:
        child=subprocess.Popen([str(loader)],cwd=root,stdin=subprocess.DEVNULL,
              stdout=f,stderr=subprocess.STDOUT,close_fds=True)
        code=child.wait()
        f.flush()
    result=parse_console(target,code)
    result['rawConsoleFile']=str(target)
    result['rawConsoleBytes']=target.stat().st_size
    return result

def save_report(data:dict,mode:str)->dict:
    home=os.environ.get('USERPROFILE')
    if not home:
        return {**data,'reportStatus':'USERPROFILE_MISSING'}
    parent=Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'
    if parent.is_symlink() or (hasattr(parent,'is_junction') and parent.is_junction()):
        return {**data,'reportStatus':'REPORT_DIR_UNSAFE'}
    try:
        parent.mkdir(parents=True,exist_ok=True)
        name='BGXAI_R38_'+mode.upper()+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'
        target=parent/name
        data={**data,'reportFile':str(target)}
        with target.open('x',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
            f.write('\n')
        return data
    except (OSError,ValueError) as err:
        return {**data,'reportStatus':'SAVE_FAILED:'+str(err)}

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,default=ROOT)
    p.add_argument('--candidate',type=Path)
    p.add_argument('--r37-tool',type=Path,required=True)
    p.add_argument('--mode',choices=('preflight','status','install','rollback','capture'),default='preflight')
    a=p.parse_args(argv)
    try:
        old=load_r37(a.r37_tool)
        if a.mode=='status': out=status(old,a.game)
        elif a.mode=='preflight':
            if a.candidate is None:raise Hold('HOLD_R38_CANDIDATE_REQUIRED')
            out=preflight(old,a.game,a.candidate)
        elif a.mode=='install':
            if a.candidate is None:raise Hold('HOLD_R38_CANDIDATE_REQUIRED')
            print('R38 installs passive READ-ONLY observer only, no XEquipItem.',flush=True)
            token=input('Type '+INSTALL_TOKEN+' exactly (ENTER cancels): ').strip()
            out=install(old,a.game,a.candidate,token)
        elif a.mode=='rollback':
            token=input('Type '+ROLLBACK_TOKEN+' exactly (ENTER cancels): ').strip()
            out=rollback(old,a.game,token)
        else:
            print('R38: game will launch; use saved party, then close game to analyze log.',flush=True)
            out=capture(old,a.game)
        status_code=0
        if out['status'] in ('R38_HOLD_UNKNOWN_WEIDU_OR_LUA','R38_RUNTIME_HOLD_MANUAL_REVIEW'):
            status_code=3
    except (Hold,OSError,ValueError,UnicodeError,subprocess.TimeoutExpired,EOFError) as err:
        out=dict(schema=SCHEMA,status='R38_STOP_MANUAL_REVIEW',reason=str(err),
           gameModifiedUnknown=a.mode in ('install','rollback'),
           ordersSent=0,dispatchAuthorized=False,armAuthorized=False,noAutoRetry=True)
        status_code=3
    print(json.dumps(save_report(out,a.mode),ensure_ascii=False,indent=2))
    return status_code

if __name__=='__main__':
    sys.exit(main())