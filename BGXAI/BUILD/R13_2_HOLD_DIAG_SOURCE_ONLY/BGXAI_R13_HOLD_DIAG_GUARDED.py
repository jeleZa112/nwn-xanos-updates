#!/usr/bin/env python3
"""BGXAI R13.2 passive diagnostic guarded last-only WeiDU overlay.
Only replacement of existing override/M_BGXD13.lua after explicit typed consent.
The previous TD14 component remains installed; no automatic edit on launch.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

GAME=Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE=Path(__file__).with_name('R15_M_BGXD13.lua')
SOURCE_SHA='040a5df62c84363fd0d566c9509636efba7721439afcc90c72758da094e7f5f8'
PREVIOUS_SHA='c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511'
ORIGINAL_SHA='5c77a460d6b429cec6f9f81e7bf6883ee1f59474cfb95778091ab769302ef414'
MODULE='override/M_BGXD13.lua'
ORIGINAL='override/M_BGXTDEF13.lua'
PROOF_PREVIOUS='BGXTD14/PROOF.json'
DIR='BGXTD15'; STAGED='BGXTD15/staged/M_BGXD13.lua'
TP2='BGXTD15/setup-BGXTD15.tp2';EXE='setup-BGXTD15.exe';PROOF='BGXTD15/PROOF.json'
WEIDU_EXE='setup-enhanced-powergaming-scripts.exe'
OLD_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXTD14[/\\]SETUP-BGXTD14[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
NEW_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXTD15[/\\]SETUP-BGXTD15[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
INSTALL_TOKEN='INSTALL_BGXAI_R13_HOLD_DIAGNOSTIC'
ROLLBACK_TOKEN='ROLLBACK_BGXAI_R13_HOLD_DIAGNOSTIC'
BASELINE={
 'override/M___EEex.lua':'e52ae61c29edb6f4a771184939d6153206f76c20d3e2522dfa158c6c943aa6cf',
 'EEex_scripts/EEex_Action.lua':'7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da',
 'override/M_BGXWP.lua':'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36',
 'override/M_BGXW2.lua':'dab7b3f5e55307088090666cb9d47989385c6895820cdf6a860e4db0f1b6b053',
 'override/M_BGXW4.lua':'79f57787be045732352582d531ce69f2485504947204bf553fa8a04a95c6595e'
}
TP2_TEXT=('BACKUP ~BGXTD15/backup~\n'
 'AUTHOR ~BGXAI guarded read-only R13.2 diagnostic~\n'
 'BEGIN ~BGXTD15 passive R13.2 HOLD reason and fist slot evidence~\n'
 'COPY ~BGXTD15/staged/M_BGXD13.lua~ ~override/M_BGXD13.lua~\n')
BLOCKED=(b'SelectWeaponAbility(',b'ClearActions(',b'ActionOverride(',b'XEquipItem(',
 b'FillSlot(',b'SetGlobal(',b'Attack(',b'Stop(',b'CreateCreature(',b'SetGlobalTimer(')

def alias(p:Path)->bool:
    f=getattr(p,'is_junction',None)
    return p.is_symlink() or bool(f and f())

def regular(root:Path,rel:str)->Path:
    p=root
    for seg in Path(rel).parts:
        if seg in ('','.','..') or '/' in seg or '\\' in seg:raise ValueError('BAD_PATH_COMPONENT:'+rel)
        p=p/seg
        if alias(p):raise ValueError('REPARSE_PATH_STOP:'+rel)
    return p

def sha(p:Path)->str:
    if alias(p) or not p.is_file():raise ValueError('FILE_MISSING_OR_LINK:'+str(p))
    with p.open('rb') as fh:return hashlib.file_digest(fh,'sha256').hexdigest()

def game(root:Path)->None:
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(GAME)):
        raise ValueError('ONLY_EXACT_WINDOWS_GAME_SUPPORTED')
    if alias(root) or not root.is_dir() or not regular(root,'chitin.key').is_file():
        raise ValueError('INVALID_EET_GAME')

def sources()->None:
    if len('M_BGXD13')!=8:raise ValueError('INVALID_8CHAR_RESOURCE')
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('DIAG_SOURCE_SHA_MISMATCH')
    dat=SOURCE.read_bytes()
    if len(dat)>50000 or b'\x00' in dat or any(x in dat for x in BLOCKED):
        raise ValueError('DIAG_SOURCE_NOT_PASSIVE')
    for required in (b'local function safe_reason',b'slot==10',b'"reason"',b'm_nResistMissile',
       b'EEex_Action_AddSpriteStartedActionListener(R.on_started)',b'BGXTargetDefenseR13.registered==true'):
        if required not in dat:raise ValueError('DIAG_SOURCE_REQUIRED_MARKER_ABSENT:'+repr(required))
    if dat.count(b'EEex_Action_AddSpriteStartedActionListener(R.on_started)')!=1:
        raise ValueError('MORE_THAN_ONE_LISTENER')

def processes()->None:
    if os.name!='nt':raise ValueError('WINDOWS_REQUIRED')
    p=subprocess.run(['tasklist','/FO','CSV','/NH'],stdin=subprocess.DEVNULL,
      capture_output=True,text=True,errors='replace',timeout=25)
    if p.returncode:raise ValueError('TASKLIST_FAILED')
    found={r[0].strip().lower() for r in csv.reader(io.StringIO(p.stdout)) if r}
    blocked={'baldur.exe','bgmain.exe','infinityloader.exe','weidu.exe',
       'setup-enhanced-powergaming-scripts.exe','setup-bgxtdef13.exe',
       'setup-bgxtd14.exe','setup-bgxtd15.exe'}
    if found&blocked:raise ValueError('GAME_OR_WEIDU_RUNNING')

def last(root:Path)->str:
    p=regular(root,'WeiDU.log')
    if not p.is_file():raise ValueError('WEIDU_LOG_MISSING')
    lines=[x.strip() for x in p.read_text(encoding='utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('~')]
    return lines[-1] if lines else 'NONE'

def baseline(root:Path)->None:
    for rel,digest in BASELINE.items():
        if sha(regular(root,rel))!=digest:raise ValueError('BASELINE_SHA_MISMATCH:'+rel)
    if sha(regular(root,ORIGINAL))!=ORIGINAL_SHA:raise ValueError('ORIGINAL_R13_SHA_DRIFT')
    p=regular(root,'BGXTDEF13/PROOF.json')
    if not p.is_file():raise ValueError('ORIGINAL_R13_PROOF_MISSING')
    orig=json.loads(p.read_text(encoding='utf-8'))
    if orig.get('sourceSha256')!=ORIGINAL_SHA or orig.get('status')!='BGXTD13_INSTALLED_AWAITING_LIVE_TEST':
        raise ValueError('ORIGINAL_R13_PROOF_CHANGED')
    p=regular(root,PROOF_PREVIOUS)
    if not p.is_file():raise ValueError('BGXTD14_PROOF_MISSING')
    prev=json.loads(p.read_text(encoding='utf-8'))
    if prev.get('sourceSha256')!=PREVIOUS_SHA or prev.get('status')!='BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST':
        raise ValueError('BGXTD14_PROOF_UNVERIFIED')

def weidu(root:Path)->Path:
    p=regular(root,WEIDU_EXE)
    if not p.is_file() or not 50000<p.stat().st_size<70000000:
        raise ValueError('WEIDU_EXE_UNAVAILABLE')
    with p.open('rb') as fh:
        if fh.read(2)!=b'MZ':raise ValueError('WEIDU_EXE_NOT_PE')
    return p

def preflight(root:Path)->dict:
    game(root);sources();baseline(root);processes();weidu(root)
    if not OLD_LAST.match(last(root)):raise ValueError('BGXTD14_NOT_LAST_NO_SAFE_INSTALL')
    if sha(regular(root,MODULE))!=PREVIOUS_SHA:raise ValueError('BGXTD14_SOURCE_SHA_DRIFT')
    for rel in (DIR,STAGED,TP2,EXE,PROOF):
        if regular(root,rel).exists():raise ValueError('BGXTD15_PATH_ALREADY_EXISTS:'+rel)
    return {'schema':'BGXAI_R13_HOLD_DIAGNOSTIC_PREFLIGHT_V1',
      'status':'BGXTD15_PREFLIGHT_PASS_NO_INSTALL','sourceSha256':SOURCE_SHA,
      'installedR13PreviousSha256':PREVIOUS_SHA,'currentWeiDULast':last(root),
      'baselineVerified':len(BASELINE),'gameplayResourcesModified':False,
      'weaponSwitchAuthorized':False,'installAuthorized':False}

def status(root:Path)->dict:
    game(root);sources();baseline(root)
    l=last(root);m=sha(regular(root,MODULE))
    if OLD_LAST.match(l) and m==PREVIOUS_SHA:st='BGXTD15_NOT_INSTALLED'
    elif NEW_LAST.match(l) and m==SOURCE_SHA:st='BGXTD15_INSTALLED_AWAITING_LIVE_TEST'
    else:raise ValueError('BGXTD15_UNKNOWN_INSTALLED_STATE')
    return {'status':st,'currentWeiDULast':l,'moduleSha256':m,
      'gameplayResourcesModifiedByStatus':False,'weaponSwitchAuthorized':False}

def outside_dir()->Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_NOT_SET')
    p=Path(home)/'Documents'/'BGXAI_BACKUPS'
    if alias(p) or alias(p.parent):raise ValueError('BACKUP_REPARSE_STOP')
    return p

def backup(root:Path)->Path:
    parent=outside_dir();parent.mkdir(parents=True,exist_ok=True)
    dest=parent/('PRE_BGXTD15_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    paths=('WeiDU.log','chitin.key',MODULE,ORIGINAL,'BGXTDEF13/PROOF.json',
      PROOF_PREVIOUS,*BASELINE.keys())
    for rel in paths:
        src=regular(root,rel)
        if not src.is_file():raise ValueError('BACKUP_SOURCE_MISSING:'+rel)
        dst=dest/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if sha(dst)!=sha(src):raise ValueError('BACKUP_HASH_MISMATCH:'+rel)
    return dest

def run_weidu(root:Path,uninstall=False)->None:
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
      '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
      text=True,errors='replace',timeout=180)
    tail=((p.stdout or '')+'\n'+(p.stderr or ''))[-1500:]
    if p.returncode or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',tail):
        raise ValueError('WEIDU_FAILED:'+tail)

def install(root:Path,token:str)->dict:
    if token!=INSTALL_TOKEN:raise ValueError('INSTALL_TOKEN_REQUIRED')
    preflight(root)
    b=backup(root)
    baseline(root);processes();sources()
    if not OLD_LAST.match(last(root)) or sha(regular(root,MODULE))!=PREVIOUS_SHA:
        raise ValueError('BGXTD14_CHANGED_AFTER_BACKUP')
    staged=regular(root,STAGED);staged.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SOURCE,staged)
    if sha(staged)!=SOURCE_SHA:raise ValueError('STAGED_SHA_MISMATCH')
    regular(root,TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    exe=regular(root,EXE);shutil.copy2(weidu(root),exe)
    if sha(exe)!=sha(regular(root,WEIDU_EXE)):raise ValueError('WEIDU_BINARY_MISMATCH')
    sources();baseline(root);processes()
    if not OLD_LAST.match(last(root)) or sha(regular(root,MODULE))!=PREVIOUS_SHA:
        raise ValueError('BGXTD14_CHANGED_BEFORE_INSTALL')
    run_weidu(root)
    if sha(regular(root,MODULE))!=SOURCE_SHA or not NEW_LAST.match(last(root)):
        raise ValueError('BGXTD15_POSTINSTALL_VERIFICATION_FAILED')
    baseline(root)
    proof={'schema':'BGXAI_R13_HOLD_DIAG_INSTALL_PROOF_V1',
      'status':'BGXTD15_INSTALLED_AWAITING_LIVE_TEST',
      'externalBackup':str(b),'sourceSha256':SOURCE_SHA,
      'previousSourceSha256':PREVIOUS_SHA,
      'installedUtc':datetime.now(timezone.utc).isoformat()}
    regular(root,PROOF).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {**proof,'gameplayResourcesModified':True,'weaponSwitchAuthorized':False,
      'next':'R13_SESSION_READY_REASON_AND_CANDIDATE_TARGET_RUNTIME_REQUIRED'}

def rollback(root:Path,token:str)->dict:
    if token!=ROLLBACK_TOKEN:raise ValueError('ROLLBACK_TOKEN_REQUIRED')
    game(root);sources();baseline(root);processes()
    if not NEW_LAST.match(last(root)):raise ValueError('BGXTD15_NOT_LAST_NO_ROLLBACK')
    if sha(regular(root,MODULE))!=SOURCE_SHA:raise ValueError('BGXTD15_INSTALLED_SHA_DRIFT')
    f=regular(root,PROOF)
    if not f.is_file():raise ValueError('BGXTD15_PROOF_MISSING')
    proof=json.loads(f.read_text(encoding='utf-8'))
    if proof.get('status')!='BGXTD15_INSTALLED_AWAITING_LIVE_TEST' or proof.get('sourceSha256')!=SOURCE_SHA:
        raise ValueError('BGXTD15_PROOF_INVALID')
    b=Path(proof.get('externalBackup',''))
    parent=outside_dir()
    if not b.is_dir() or alias(b) or b.parent!=parent or not b.name.startswith('PRE_BGXTD15_'):
        raise ValueError('BACKUP_PATH_UNTRUSTED')
    if sha(regular(b,MODULE))!=PREVIOUS_SHA or not OLD_LAST.match(last(b)):
        raise ValueError('BACKUP_TD14_NOT_VERIFIED')
    for rel,d in BASELINE.items():
        if sha(regular(b,rel))!=d:raise ValueError('BACKUP_BASELINE_MISMATCH:'+rel)
    if sha(regular(b,ORIGINAL))!=ORIGINAL_SHA or not regular(b,'chitin.key').is_file():
        raise ValueError('BACKUP_ORIGINAL_MISSING')
    run_weidu(root,uninstall=True)
    if sha(regular(root,MODULE))!=PREVIOUS_SHA or not OLD_LAST.match(last(root)):
        raise ValueError('BGXTD14_NOT_RESTORED')
    baseline(root)
    return {'status':'BGXTD15_ROLLBACK_TD14_RESTORED_VERIFIED',
      'gameplayResourcesModified':True,'weaponSwitchAuthorized':False}

# Read-only captured console in same menu after TD15 overlay.
# Avoid using old TD14 capture (it requires TD14 to be WeiDU last).
def capture_console(root:Path)->dict:
    game(root);sources();baseline(root);processes()
    if not NEW_LAST.match(last(root)) or sha(regular(root,MODULE))!=SOURCE_SHA:
        raise ValueError('BGXTD15_NOT_INSTALLED_FOR_CAPTURE')
    proof_file=regular(root,PROOF)
    if not proof_file.is_file():raise ValueError('BGXTD15_PROOF_MISSING_FOR_CAPTURE')
    proof=json.loads(proof_file.read_text(encoding='utf-8'))
    if proof.get('status')!='BGXTD15_INSTALLED_AWAITING_LIVE_TEST' or proof.get('sourceSha256')!=SOURCE_SHA:
        raise ValueError('BGXTD15_PROOF_INVALID_FOR_CAPTURE')
    exe=regular(root,'InfinityLoader.exe')
    if not exe.is_file() or not 1024<exe.stat().st_size<70000000:
        raise ValueError('INFINITYLOADER_MISSING')
    with exe.open('rb') as fh:
        if fh.read(2)!=b'MZ':raise ValueError('INFINITYLOADER_NOT_PE')
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_MISSING')
    docs=Path(home)/'Documents';reports=docs/'BGXAI_LIVE_REPORTS'
    if alias(docs) or alias(reports):raise ValueError('REPORT_PATH_REPARSE_STOP')
    reports.mkdir(parents=True,exist_ok=True)
    dest=reports/('BGXAI_R13_2_CONSOLE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.log')
    if dest.exists() or alias(dest):raise ValueError('REPORT_PATH_COLLISION')
    with dest.open('xb') as handle:
        proc=subprocess.Popen([str(exe)],cwd=root,stdin=subprocess.DEVNULL,
          stdout=handle,stderr=subprocess.STDOUT,close_fds=True)
        code=proc.wait();handle.flush()
    size=dest.stat().st_size
    return {'schema':'BGXAI_R13_2_CAPTURE_RO_V1',
      'status':'BGXTD15_CAPTURE_CREATED' if size else 'BGXTD15_CAPTURE_EMPTY_HOLD',
      'consoleLog':str(dest),'consoleBytes':size,'gameExitCode':code,
      'gameplayResourcesModified':False,'weaponSwitchAuthorized':False}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--game',default=str(GAME));
    ap.add_argument('--mode',choices=('menu','preflight','install','status','rollback','capture'),default='menu')
    args=ap.parse_args();root=Path(args.game)
    try:
        if args.mode=='menu':
            print('R13.2 HOLD reason/slot10 diagnostics: 1=status RO, 2=preflight RO, 3=install typed, 4=rollback typed, 5=capture console RO, 0=exit')
            pick=input('Choice [2]: ').strip() or '2'
            args.mode={'1':'status','2':'preflight','3':'install','4':'rollback','5':'capture','0':'exit'}.get(pick,'INVALID')
        if args.mode=='exit':print('No game changes.');return 0
        if args.mode=='status':res=status(root)
        elif args.mode=='preflight':res=preflight(root)
        elif args.mode=='install':
            print('Only overlay override/M_BGXD13.lua via WeiDU; previous R13 preserved.')
            token=input('Type '+INSTALL_TOKEN+' exactly; ENTER cancels: ').strip()
            res=install(root,token)
        elif args.mode=='capture':
            print('Start InfinityLoader. When ready, load the test save; exit to save the console. No WeiDU change.')
            res=capture_console(root)
        elif args.mode=='rollback':
            token=input('Type '+ROLLBACK_TOKEN+' exactly; ENTER cancels: ').strip()
            res=rollback(root,token)
        else:raise ValueError('INVALID_MENU_OPTION')
        print(json.dumps(res,ensure_ascii=False,indent=2,sort_keys=True));return 0
    except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as ex:
        print(json.dumps({'status':'BGXTD15_STOP','reason':str(ex),
          'weaponSwitchAuthorized':False},ensure_ascii=False,indent=2));return 2

if __name__=='__main__':sys.exit(main())
