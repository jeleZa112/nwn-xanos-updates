#!/usr/bin/env python3
"""BGXAI R42: guarded 154(R38)->155(R42) one-listener RO WeiDU replacement.

No equipment movement, BGXW3ARM, manual/EPS origin attribution, or auto-install.
Only explicit TYPE-TO-APPROVE install/rollback; always fail closed on drift.
Reuses existing SHA-pinned R38 and R37 helper implementation/proofs.
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
SCHEMA='BGXAI_R42_R38_LAST_CLASS_BCS_ONE_LISTENER_GUARDED_V1'
R38_TOOL_LEN=21303
R38_TOOL_SHA='f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c'
R38_TOOL_BLOB='aaa9f182fec7e7800e382167d1666d8c85804ef8'
R37_TOOL_LEN=26252
R37_TOOL_SHA='b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d'
CANDIDATE_BYTES=93776
CANDIDATE_SHA='d14bf5f62f7d37663cf77f3305f57fb9631293940ed8ae2d4cb7b488248434b0'
R38_SHA='958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c'
WEIDU_SHA='0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75'
OVERRIDE='override/M_BGXR27.lua'
DIR='BGXR42'
STAGED=DIR+'/staged/M_BGXR27.lua'
TP2=DIR+'/setup-BGXR42.tp2'
SETUP=DIR+'/setup-BGXR42.exe'
PROOF=DIR+'/PROOF.json'
INSTALL_TOKEN='INSTALL_BGXAI_R42_READONLY_CLASS_BCS_AFTER_R38'
ROLLBACK_TOKEN='ROLLBACK_BGXAI_R42_RESTORE_R38_ONLY'
TP2_TEXT=(
    'BACKUP ~BGXR42/backup~\n'
    'AUTHOR ~BGXAI R42 read-only class BCS one-listener observation~\n'
    'BEGIN ~BGXR42 single R38 observer extension - no equipment commands~\n'
    'COPY ~BGXR42/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n'
)
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR42[/\\]SETUP-BGXR42[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
TAGS=(b'[BGXR27]',b'[BGXR37]',b'[BGXINV3]',b'[BGXID]',b'[BGXBCS]')
ONE_LISTENER=b'EEex_Action_AddSpriteStartedActionListener,pilot.listener'

class Hold(ValueError):
    pass

def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def verified_module(path:Path, size:int, sha:str, name:str):
    if (path.is_symlink() or not path.is_file() or
        path.stat().st_size != size or sha_bytes(path.read_bytes()) != sha):
        raise Hold('HOLD_PINNED_HELPER_SHA_OR_SIZE:'+name)
    spec=importlib.util.spec_from_file_location('bgxai_verified_'+name,str(path))
    if spec is None or spec.loader is None:
        raise Hold('HOLD_PINNED_HELPER_IMPORT:'+name)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load(r38_path:Path,r37_path:Path):
    r38=verified_module(r38_path,R38_TOOL_LEN,R38_TOOL_SHA,'R38')
    old=verified_module(r37_path,R37_TOOL_LEN,R37_TOOL_SHA,'R37')
    if (r38.SOURCE_SHA!=R38_SHA or r38.WEIDU_SHA!=WEIDU_SHA or
        r38.OLD_SHA!=old.SOURCE_SHA or old.NATIVE_SHA!=WEIDU_SHA or
        r38.OVERRIDE!=OVERRIDE):
        raise Hold('HOLD_R38_R37_HELPER_CONTRACT_DRIFT')
    return r38,old

def candidate_bytes(path:Path)->bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=CANDIDATE_BYTES:
        raise Hold('HOLD_R42_CANDIDATE_SIZE_OR_PATH')
    data=path.read_bytes()
    if sha_bytes(data)!=CANDIDATE_SHA or data.count(ONE_LISTENER)!=1:
        raise Hold('HOLD_R42_CANDIDATE_SHA_OR_LISTENER')
    if any(tag not in data for tag in TAGS):
        raise Hold('HOLD_R42_READONLY_TAGS_INCOMPLETE')
    for marker in (b'"ordersSent":0',b'"armAuthorized":false',
                   b'"dispatchAuthorized":false',b'"actualBcsExecutionVerified":false',
                   b'"manualEpsActionOriginVerified":false'):
        if marker not in data:
            raise Hold('HOLD_R42_SAFETY_MARKER_MISSING')
    return data

def check_processes(r38,old):
    r38.check_processes(old)
    task=subprocess.run(['tasklist','/FO','CSV','/NH'],stdin=subprocess.DEVNULL,
                        capture_output=True,text=True,errors='replace',
                        timeout=25,check=False)
    if task.returncode:
        raise Hold('HOLD_TASKLIST_UNAVAILABLE')
    names={row[0].strip().lower() for row in csv.reader(io.StringIO(task.stdout)) if row}
    if 'setup-bgxr42.exe' in names:
        raise Hold('HOLD_R42_WEIDU_RUNNING')

def snapshot(r38,old,root):
    original=r38.snapshot(old,root)
    p=old.safe(root,r38.PROOF)
    if not p.is_file():
        raise Hold('HOLD_R38_PROOF_MISSING')
    original[r38.PROOF]=old.sha(p)
    return original

def r38_last(r38,old,root):
    rows,log_sha=r38.last_r38(old,root)
    r38.installed_proof(old,root)
    return rows,log_sha

def r42_last(r38,old,root):
    old.protected_root(root,True)
    rows,log_sha=old.history(root)
    if (len(rows)!=155 or not old.last_r37_history(rows[:153]) or
        not r38.LAST.match(rows[153]) or not LAST.match(rows[154])):
        raise Hold('HOLD_R42_NOT_WEIDU_LAST_155')
    if old.sha(old.safe(root,OVERRIDE))!=CANDIDATE_SHA:
        raise Hold('HOLD_R42_ACTIVE_LUA_SHA_DRIFT')
    return rows,log_sha

def installed_proof(old,root):
    p=old.safe(root,PROOF)
    if not p.is_file() or p.stat().st_size>1_000_000:
        raise Hold('HOLD_R42_PROOF_NOT_FOUND')
    d=json.loads(p.read_text(encoding='utf-8'))
    if (type(d) is not dict or d.get('schema')!=SCHEMA or
        d.get('status')!='R42_READONLY_INSTALLED_AWAITING_LIVE_CLASS' or
        d.get('sourceSha256')!=CANDIDATE_SHA or
        d.get('typedInstallApproved') is not True or
        d.get('installationPerformed') is not True or
        d.get('dispatchAuthorized') is not False or
        d.get('armAuthorized') is not False or
        d.get('ordersSent')!=0):
        raise Hold('HOLD_R42_PROOF_INVALID')
    return d

def preflight(r38,old,root:Path,candidate:Path):
    old.protected_root(root,True)
    check_processes(r38,old)
    rows,log_sha=r38_last(r38,old,root)
    if len(rows)!=154:raise Hold('HOLD_R38_LAST_154_REQUIRED')
    for rel in (DIR,STAGED,TP2,SETUP,PROOF):
        if old.safe(root,rel).exists():
            raise Hold('HOLD_R42_EXISTING_STAGING:'+rel)
    for rel,expected in old.BASELINE_SHA.items():
        if old.sha(old.safe(root,rel))!=expected:
            raise Hold('HOLD_R38_BASELINE_CHANGED:'+rel)
    native=old.safe(root,'setup-enhanced-powergaming-scripts.exe')
    if not native.is_file() or old.sha(native)!=WEIDU_SHA:
        raise Hold('HOLD_R42_NATIVE_WEIDU_CHANGED')
    candidate_bytes(candidate)
    baseline=snapshot(r38,old,root)
    if baseline.get(OVERRIDE)!=R38_SHA:
        raise Hold('HOLD_R38_LIVE_BASELINE_MISMATCH')
    return {
        'schema':SCHEMA,'status':'R42_PREFLIGHT_PASS_NO_INSTALL',
        'weiduComponents':154,'weiDULogSha256':log_sha,
        'sourceSha256':CANDIDATE_SHA,'sourceBytes':CANDIDATE_BYTES,
        'baselineSnapshot':baseline,'gameModified':False,'installed':False,
        'ordersSent':0,'dispatchAuthorized':False,'armAuthorized':False,
        'manualEpsActionOriginVerified':False,
        'actualBcsExecutionVerified':False,
        'classScriptResrefAtLiveJaganVerified':False,
    }

def external_backup(old,root,expected):
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    parent=Path(home)/'Documents'/'BGXAI_BACKUPS'
    if (parent.is_symlink() or
        (hasattr(parent,'is_junction') and parent.is_junction())):
        raise Hold('HOLD_EXTERNAL_BACKUP_REPARSE')
    parent.mkdir(parents=True,exist_ok=True)
    dest=Path(tempfile.mkdtemp(prefix='PRE_BGXR42_',dir=parent))
    for rel,digest in expected.items():
        src=old.safe(root,rel);dst=old.safe(dest,rel)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if old.sha(dst)!=digest:
            raise Hold('HOLD_R42_EXTERNAL_BACKUP_SHA_FAILED:'+rel)
    old.safe(dest,'SHA256.json').write_text(json.dumps(expected,indent=2),encoding='utf-8')
    return dest

def native_weidu(old,root,uninstall=False):
    exe=old.safe(root,SETUP)
    if not exe.is_file() or old.sha(exe)!=WEIDU_SHA:
        raise Hold('HOLD_R42_WEIDU_BINARY_CHANGED')
    result=subprocess.run(
        [str(exe),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru',
         '--force-uninstall' if uninstall else '--force-install','0'],
        cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
        text=True,errors='replace',timeout=240,check=False)
    transcript=(result.stdout or '')+'\n'+(result.stderr or '')
    if result.returncode or re.search(r'(?mi)^\s*(ERROR:|FATAL ERROR:)',transcript):
        raise Hold('HOLD_R42_WEIDU_MANUAL_REVIEW:'+transcript[-500:])

def install(r38,old,root,candidate,token):
    if token!=INSTALL_TOKEN:
        raise Hold('HOLD_EXACT_R42_INSTALL_TOKEN_REQUIRED')
    ready=preflight(r38,old,root,candidate)
    baseline=ready['baselineSnapshot']
    old.verify_snapshot(root,baseline)
    backup=external_backup(old,root,baseline)
    check_processes(r38,old)
    old.verify_snapshot(root,baseline)
    # No automatic retry or rollback after the first game mutation.
    old.safe(root,DIR).mkdir(parents=True,exist_ok=False)
    staged=old.safe(root,STAGED)
    staged.parent.mkdir(parents=True,exist_ok=False)
    staged.write_bytes(candidate_bytes(candidate))
    old.safe(root,TP2).write_text(TP2_TEXT,encoding='ascii',newline='\n')
    shutil.copy2(old.safe(root,'setup-enhanced-powergaming-scripts.exe'),old.safe(root,SETUP))
    if old.sha(staged)!=CANDIDATE_SHA or old.sha(old.safe(root,SETUP))!=WEIDU_SHA:
        raise Hold('HOLD_R42_STAGE_SHA_CHANGED')
    check_processes(r38,old)
    old.verify_snapshot(root,baseline)
    proof=old.safe(root,PROOF)
    proof.write_text(json.dumps({
        'schema':SCHEMA,'status':'R42_PENDING_WEIDU',
        'sourceSha256':CANDIDATE_SHA,'externalBackup':str(backup),
        'baselineSnapshot':baseline},indent=2),encoding='utf-8')
    native_weidu(old,root)
    r42_last(r38,old,root)
    for rel,digest in baseline.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R42_UNRELATED_RESOURCE_CHANGED_MANUAL_REVIEW:'+rel)
    output={
        'schema':SCHEMA,'status':'R42_READONLY_INSTALLED_AWAITING_LIVE_CLASS',
        'sourceSha256':CANDIDATE_SHA,'externalBackup':str(backup),
        'baselineSnapshot':baseline,'typedInstallApproved':True,
        'installationPerformed':True,'installed':True,'gameModified':True,
        'readOnly':True,'ordersSent':0,'localsWritten':0,
        'dispatchAuthorized':False,'armAuthorized':False,
        'actualBcsExecutionVerified':False,
        'classScriptResrefAtLiveJaganVerified':False,
        'manualEpsActionOriginVerified':False,
    }
    proof.write_text(json.dumps(output,indent=2),encoding='utf-8')
    return output

def rollback(r38,old,root,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold('HOLD_EXACT_R42_ROLLBACK_TOKEN_REQUIRED')
    r42_last(r38,old,root)
    check_processes(r38,old)
    proof=installed_proof(old,root)
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    parent=Path(home)/'Documents'/'BGXAI_BACKUPS'
    backup=Path(proof.get('externalBackup',''))
    if (backup.parent!=parent or not backup.name.startswith('PRE_BGXR42_') or
        not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,'is_junction') and backup.is_junction())):
        raise Hold('HOLD_R42_EXTERNAL_BACKUP_PROVENANCE')
    manifest=json.loads(old.safe(backup,'SHA256.json').read_text(encoding='utf-8'))
    if (manifest!=proof.get('baselineSnapshot') or
        manifest.get(OVERRIDE)!=R38_SHA or
        r38.PROOF not in manifest):
        raise Hold('HOLD_R42_BACKUP_MANIFEST_MISMATCH')
    old.verify_snapshot(backup,manifest)
    for rel,digest in manifest.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R42_UNRELATED_RESOURCE_DRIFT:'+rel)
    check_processes(r38,old)
    native_weidu(old,root,uninstall=True)
    r38_last(r38,old,root)
    for rel,digest in manifest.items():
        if rel not in ('WeiDU.log',OVERRIDE) and old.sha(old.safe(root,rel))!=digest:
            raise Hold('HOLD_R42_ROLLBACK_CHANGED_UNRELATED_FILE:'+rel)
    return {'schema':SCHEMA,'status':'R42_ROLLBACK_RESTORED_R38_LAST',
            'weiduComponents':154,'installed':False,
            'gameModified':True,'ordersSent':0,
            'dispatchAuthorized':False,'armAuthorized':False}

def status(r38,old,root):
    old.protected_root(root,True)
    rows,logsha=old.history(root)
    active=old.sha(old.safe(root,OVERRIDE))
    installed=(len(rows)==155 and old.last_r37_history(rows[:153]) and
               r38.LAST.match(rows[153]) is not None and
               LAST.match(rows[154]) is not None and active==CANDIDATE_SHA)
    prior=(len(rows)==154 and old.last_r37_history(rows[:153]) and
           r38.LAST.match(rows[153]) is not None and active==R38_SHA)
    if installed:installed_proof(old,root)
    elif prior:r38.installed_proof(old,root)
    return {
        'schema':SCHEMA,
        'status':'R42_PRESENT_LAST_READONLY' if installed else
                 'R42_NOT_INSTALLED_R38_LAST' if prior else
                 'R42_HOLD_UNEXPECTED_WEIDU_OR_LUA',
        'weiduComponents':len(rows),'weiDULogSha256':logsha,
        'activeLuaSha256':active,'installed':installed,
        'gameModified':False,'ordersSent':0,'armAuthorized':False,
        'dispatchAuthorized':False,
        'classScriptResrefAtLiveJaganVerified':False,
    }


BCS_TAG=b'[BGXBCS] '
BCS_SCHEMA='BGXAI_R42_CLASS_BCS_SINGLE_CALLBACK_RO_V1'

def parse_bcs_console(log:Path,exit_code:int):
    """Reuse the original R38 console format; one sanitized new tag, never infer action ownership."""
    if log.is_symlink() or not log.is_file() or log.stat().st_size>64_000_000:
        raise Hold('HOLD_R42_CAPTURE_LOG_UNTRUSTED')
    parsed=[]
    malformed=0
    with log.open('rb') as stream:
        for raw in stream:
            if BCS_TAG not in raw:continue
            if raw.count(BCS_TAG)!=1 or len(raw)>4096:
                malformed+=1;continue
            try:
                data=json.loads(raw.split(BCS_TAG,1)[1].decode('utf-8-sig','strict').strip())
            except (UnicodeError,ValueError):
                malformed+=1;continue
            if (type(data) is not dict or data.get('schema')!=BCS_SCHEMA or
                data.get('type')!='CLASS_BCS_ONCE' or
                type(data.get('seq')) is not int or
                not 1<=data['seq']<=64 or data.get('partyIndex')!=1 or
                data.get('scrlev')!=4 or data.get('sameR38Listener') is not True or
                data.get('gameModified') is not False or
                data.get('ordersSent')!=0 or data.get('localsWritten')!=0 or
                data.get('armAuthorized') is not False or
                data.get('dispatchAuthorized') is not False or
                data.get('actualBcsExecutionVerified') is not False or
                data.get('manualEpsActionOriginVerified') is not False):
                malformed+=1;continue
            status,name=data.get('status'),data.get('classScriptResref')
            if status=='CLASS_BCS_RESREF_OBSERVED_NO_ARM':
                if (type(name) is not str or len(name)>8 or len(name)<1 or
                    re.fullmatch(r'[A-Z0-9_#*]+',name) is None or name=='NONE'):
                    malformed+=1;continue
            elif status=='HOLD_CLASS_BCS_NOT_READABLE':
                if name is not None:malformed+=1;continue
            else:
                malformed+=1;continue
            parsed.append((status,name))
    if exit_code or malformed or len(parsed)!=1:
        return {'schema':SCHEMA,'status':'R42_CAPTURE_HOLD_MANUAL_REVIEW',
                'reason':'HOLD_BCS_ROW_COUNT_OR_EXIT_OR_FORMAT',
                'validBcsRows':len(parsed),'malformedBcsRows':malformed,
                'originalGameExitCode':exit_code,'ordersSent':0,
                'classScriptResrefAtLiveJaganVerified':False,
                'actualBcsExecutionVerified':False,'manualEpsActionOriginVerified':False,
                'gameModified':False,'dispatchAuthorized':False,'armAuthorized':False}
    status,name=parsed[0]
    proved=status=='CLASS_BCS_RESREF_OBSERVED_NO_ARM'
    return {'schema':SCHEMA,
            'status':'R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM' if proved
                     else 'R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE',
            'classScriptResref':name if proved else None,
            'scrlev':4,'partyIndex':1,'validBcsRows':1,
            'classScriptResrefAtLiveJaganVerified':proved,
            'actualBcsExecutionVerified':False,
            'manualEpsActionOriginVerified':False,
            'ordersSent':0,'localsWritten':0,
            'dispatchAuthorized':False,'armAuthorized':False,
            'gameModified':False}

def capture(r38,old,root):
    r42_last(r38,old,root)
    installed_proof(old,root)
    check_processes(r38,old)
    loader=old.safe(root,'InfinityLoader.exe')
    if (loader.is_symlink() or not loader.is_file() or
        not 1024<loader.stat().st_size<70_000_000):
        raise Hold('HOLD_R42_INFINITY_LOADER_SIZE_OR_PATH')
    with loader.open('rb') as f:
        if f.read(2)!=b'MZ':raise Hold('HOLD_R42_INFINITY_LOADER_NOT_PE')
    home=os.environ.get('USERPROFILE')
    if not home:raise Hold('HOLD_USERPROFILE_MISSING')
    reports=Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'
    if (reports.is_symlink() or
        (hasattr(reports,'is_junction') and reports.is_junction())):
        raise Hold('HOLD_R42_CAPTURE_REPORTS_REPARSE')
    reports.mkdir(parents=True,exist_ok=True)
    file=reports/('BGXAI_R42_CLASS_BCS_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.log')
    with file.open('xb') as fd:
        child=subprocess.Popen([str(loader)],cwd=root,stdin=subprocess.DEVNULL,
                               stdout=fd,stderr=subprocess.STDOUT,close_fds=True)
        exit_code=child.wait()
        fd.flush()
    # Do not silently use a captured name if WeiDU/Lua changed while running.
    r42_last(r38,old,root)
    out=parse_bcs_console(file,exit_code)
    out['rawConsoleFile']=str(file)
    out['rawConsoleBytes']=file.stat().st_size
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,default=ROOT)
    p.add_argument('--r38-tool',type=Path,required=True)
    p.add_argument('--r37-tool',type=Path,required=True)
    p.add_argument('--candidate',type=Path)
    p.add_argument('--mode',choices=('status','preflight','install','rollback','capture'),
                   default='status')
    args=p.parse_args(argv)
    try:
        r38,old=load(args.r38_tool,args.r37_tool)
        if args.mode=='status':
            result=status(r38,old,args.game)
        elif args.mode=='preflight':
            if args.candidate is None:raise Hold('HOLD_CANDIDATE_REQUIRED')
            result=preflight(r38,old,args.game,args.candidate)
        elif args.mode=='install':
            if args.candidate is None:raise Hold('HOLD_CANDIDATE_REQUIRED')
            print('R42: READ-ONLY class script observer; no XEquipItem.',flush=True)
            token=input('Type '+INSTALL_TOKEN+' exactly (ENTER cancels): ').strip()
            result=install(r38,old,args.game,args.candidate,token)
        elif args.mode=='rollback':
            token=input('Type '+ROLLBACK_TOKEN+' exactly (ENTER cancels): ').strip()
            result=rollback(r38,old,args.game,token)
        else:
            print('R42: launches existing game; close after Jagan acts once.',flush=True)
            result=capture(r38,old,args.game)
        rc=3 if result['status'] in (
            'R42_HOLD_UNEXPECTED_WEIDU_OR_LUA',
            'R42_CAPTURE_HOLD_MANUAL_REVIEW',
            'R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE') else 0
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired,EOFError) as error:
        result={'schema':SCHEMA,'status':'R42_STOP_MANUAL_REVIEW',
                'reason':str(error) if isinstance(error,Hold) else 'HOLD_RUNTIME_OR_IO',
                'noAutoRetry':True,
                'gameModifiedUnknown':args.mode in ('install','rollback'),
                'ordersSent':0,'dispatchAuthorized':False,'armAuthorized':False}
        rc=3
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return rc

if __name__=='__main__':
    sys.exit(main())
