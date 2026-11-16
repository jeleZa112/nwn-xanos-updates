#!/usr/bin/env python3
"""BGXP3 protected BCS-only upgrade over verified installed BGXP2.
No implicit installation, no weakening of F/idle/EPS gates, no automatic retry.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path
import BGXP2_BCS_PATCH as P
import BGXP3_BCS_PREFLIGHT_SOURCE_ONLY as Q
import BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY as BUFFER

GAME=Path(r'C:\Games\BG_EET_FOXX_NEW')
BASE=Path(__file__).resolve().parent
BCS='override/BDDEFAI.BCS'
LUA='override/M_BX43.lua'
WEIDU='setup-enhanced-powergaming-scripts.exe'
STAGED='BGXP3/staged/BDDEFAI.BCS'
OLD='BGXP3/staged/ORIGINAL_BGXP2.BCS'
PROOF='BGXP3/STAGED_PROOF.json'
TP2='BGXP3/setup-BGXP3.tp2'
EXE='setup-BGXP3.exe'
TP2_TEXT='BACKUP ~BGXP3/backup~\nAUTHOR ~BGXAI EPS-first AUTO attack buffer~\nBEGIN ~BGXAI BGXP3 AUTO conservative attack 60 percent~\nCOPY ~BGXP3/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
OLD_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXP2[/\\]SETUP-BGXP2\.TP2~\s+#0\s+#0(?:\s|$)',re.I)
NEW_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXP3[/\\]SETUP-BGXP3\.TP2~\s+#0\s+#0(?:\s|$)',re.I)
BACKUP=('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk',LUA,BCS)
INSTALL_TOKEN='INSTALL_BGXP3_AUTO_BUFFER'
ROLLBACK_TOKEN='ROLLBACK_BGXP3_AUTO_BUFFER'
class Stop(RuntimeError): pass

def sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()

def no_link(p:Path):
    if p.is_symlink(): raise Stop('SYMLINK:'+str(p))
    try:
        if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Stop('REPARSE_POINT:'+str(p))
    except (AttributeError,FileNotFoundError): pass

def file(root:Path,relative:str,minsize:int=1)->Path:
    if not relative or relative.startswith('/') or '\\' in relative or ':' in relative or '..' in relative.split('/'):
        raise Stop('UNSAFE_RELATIVE_PATH:'+relative)
    f=root/relative
    for x in (f,*f.parents):
        no_link(x)
        if x==root: break
    if not f.is_file() or f.stat().st_size<minsize:
        raise Stop('REQUIRED_FILE_MISSING:'+relative)
    return f

def sources():
    m=json.loads(file(BASE,'SHA256_FILES.json').read_text(encoding='utf-8'))
    if m.get('schema')!=1 or set(m.get('files',[]))!=set(m.get('sha256',{})):
        raise Stop('SOURCE_MANIFEST_INVALID')
    needed={'BGXP2_LAST_PRIORITY.baf','BGXP2_BCS_PATCH.py','BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY.py',
            'BGXP3_BCS_PREFLIGHT_SOURCE_ONLY.py','BGXP3_INSTALL.py','README_RU.md',
            'test_bgxp3_auto_attack_buffer.py','test_bgxp3_bcs_preflight.py'}
    if set(m['files'])!=needed: raise Stop('SOURCE_LIST_CHANGED')
    for name in m['files']:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',name): raise Stop('SOURCE_NAME_INVALID')
        if sha(file(BASE,name).read_bytes())!=m['sha256'][name]:
            raise Stop('SOURCE_HASH_CHANGED:'+name)
    original=file(BASE,'BGXP2_LAST_PRIORITY.baf').read_bytes()
    proposed=BUFFER.candidate(original)
    if sha(proposed)!='c3d41f9d046203e8acbb2e8ff3896183b10a12e58eaef743d67eeab77213f378':
        raise Stop('UNEXPECTED_CANDIDATE_BAF_SHA')
    return True

def last(root:Path)->str:
    lines=[s.strip() for s in file(root,'WeiDU.log').read_text(
        encoding='utf-8-sig',errors='replace').splitlines() if s.strip().startswith('~')]
    if not lines: raise Stop('EMPTY_WEIDU_LOG')
    return lines[-1]

def base(root:Path,allow_stage:bool=False)->dict:
    root=root.resolve(strict=True)
    if not OLD_LAST.match(last(root)): raise Stop('BGXP2_MUST_BE_LAST_WEIDU')
    if sha(file(root,LUA).read_bytes())!=Q.LIVE_LUA_SHA: raise Stop('EXISTING_LUA_CHANGED')
    live=file(root,BCS).read_bytes()
    if sha(live)!=Q.LIVE_BCS_SHA: raise Stop('EXISTING_BGXP2_BCS_CHANGED')
    P.chunks(live,1158)
    proof=json.loads(file(root,'BGXP2/STAGED_PROOF.json').read_text(encoding='utf-8'))
    if proof.get('new_bcs_sha256')!=Q.LIVE_BCS_SHA or proof.get('lua_sha256')!=Q.LIVE_LUA_SHA:
        raise Stop('BGXP2_INSTALLED_PROOF_CHANGED')
    if not allow_stage and ((root/'BGXP3').exists() or (root/EXE).exists()):
        raise Stop('BGXP3_STAGE_EXISTS')
    return {'state':'BGXP2_INSTALLED_VERIFIED','last_weidu':last(root),
            'bcs_sha256':Q.LIVE_BCS_SHA,'lua_sha256':Q.LIVE_LUA_SHA,'blocks':1158}

def installed(root:Path)->dict:
    root=root.resolve(strict=True)
    if not NEW_LAST.match(last(root)): raise Stop('BGXP3_NOT_LAST_WEIDU')
    if sha(file(root,LUA).read_bytes())!=Q.LIVE_LUA_SHA: raise Stop('OTHER_LUA_CHANGED')
    if file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT: raise Stop('BGXP3_TP2_CHANGED')
    proof=json.loads(file(root,PROOF).read_text(encoding='utf-8'))
    original=file(root,OLD).read_bytes()
    changed=file(root,BCS).read_bytes()
    if sha(original)!=Q.LIVE_BCS_SHA: raise Stop('OLD_BGXP2_RESTORE_COPY_CHANGED')
    if proof.get('old_bcs_sha256')!=Q.LIVE_BCS_SHA or proof.get('lua_sha256')!=Q.LIVE_LUA_SHA:
        raise Stop('BGXP3_PROOF_INVALID')
    if sha(changed)!=proof.get('new_bcs_sha256') or sha(file(root,STAGED).read_bytes())!=sha(changed):
        raise Stop('BGXP3_LIVE_BCS_SHA_MISMATCH')
    oldchunks=P.chunks(original,1158);newchunks=P.chunks(changed,1158)
    if oldchunks[:1157]!=newchunks[:1157] or oldchunks[-1]==newchunks[-1]:
        raise Stop('BGXP3_MODIFIED_NON_TARGET_BLOCKS')
    return {'state':'BGXP3_INSTALLED_VERIFIED','last_weidu':last(root),
            'bcs_sha256':sha(changed),'lua_sha256':Q.LIVE_LUA_SHA,'blocks':1158,
            'preserved_blocks':1157}

def guard_processes():
    if os.name!='nt': raise Stop('WINDOWS_ONLY')
    ps=('$ErrorActionPreference="Stop"; $p=Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
        'if($p){$p|Select-Object Name,ProcessId|Out-String;exit 3}')
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
             capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=30,check=False)
    if proc.returncode or proc.stdout.strip():
        raise Stop('GAME_OR_WEIDU_RUNNING_OR_PROCESS_CHECK_FAILED:'+proc.stdout[-400:])

def snapshot(root:Path,state:dict,purpose:str)->Path:
    home=Path(os.environ.get('USERPROFILE',str(Path.home())))
    out=home/'Documents'/'BGXAI_PRIEST3_SAFE_BACKUPS'
    no_link(out);no_link(out.parent)
    if root.resolve(strict=True)==out.resolve() or root.resolve(strict=True) in out.resolve().parents:
        raise Stop('BACKUP_INSIDE_GAME')
    out.mkdir(parents=True,exist_ok=True)
    dest=out/(purpose+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    hashes={}
    for name in BACKUP:
        src=file(root,name)
        dst=dest/name
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        hashes[name]=sha(src.read_bytes())
        if sha(dst.read_bytes())!=hashes[name]: raise Stop('BACKUP_SHA_MISMATCH:'+name)
    (dest/'PROOF.json').write_text(json.dumps({'state':state,'sha256':hashes},indent=2)+'\n',encoding='utf-8')
    return dest

def verify_untouched(root:Path,backup:Path):
    sums=json.loads((backup/'PROOF.json').read_text(encoding='utf-8'))['sha256']
    for name in BACKUP:
        if name not in (BCS,'WeiDU.log') and sha(file(root,name).read_bytes())!=sums[name]:
            raise Stop('UNEXPECTED_NON_TARGET_FILE_CHANGE:'+name)

def weidu(root:Path,uninstall:bool=False)->str:
    cmd=[str(file(root,EXE,100000)),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    proc=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
            text=True,encoding='utf-8',errors='replace',timeout=200,check=False)
    log=(proc.stdout or '')+'\n'+(proc.stderr or '')
    if proc.returncode or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',log):
        raise Stop('WEIDU_FAILED_NO_AUTO_RETRY:'+log[-1800:])
    return log[-1900:]

def preflight(root:Path)->dict:
    sources();base(root)
    file(root,WEIDU,100000)
    for name in BACKUP: file(root,name)
    result=Q.preflight(root)
    if result['preserved_blocks_exact']!=1157 or result['total_blocks']!=1158:
        raise Stop('NATIVE_BCS_PROOF_FAILED')
    return {'status':'REAL_EET_COMPILE_READ_ONLY_PASS','base':'BGXP2_INSTALLED_VERIFIED',
            'patch':result,'authorized_to_install':False}

def install(root:Path)->dict:
    guard_processes();root=root.resolve(strict=True)
    ready=preflight(root)
    oldlog=sha(file(root,'WeiDU.log').read_bytes())
    backup=snapshot(root,base(root),'PRE_INSTALL')
    guard_processes();base(root)
    if sha(file(root,'WeiDU.log').read_bytes())!=oldlog:
        raise Stop('WEIDU_LOG_CHANGED_DURING_PREFLIGHT')
    check=preflight(root)
    if check['patch']['proposed_sha256']!=ready['patch']['proposed_sha256']:
        raise Stop('NONDETERMINISTIC_NATIVE_COMPILATION')
    # One temporary recompile after SHA gates. Stage only after successful verification.
    old_baf=file(BASE,'BGXP2_LAST_PRIORITY.baf')
    proposed=BUFFER.candidate(old_baf.read_bytes())
    with __import__('tempfile').TemporaryDirectory(prefix='BGXP3_INSTALL_PREP_') as tmpdir:
        new_baf=Path(tmpdir)/'BGXP3.baf'
        new_baf.write_bytes(proposed)
        compiled_old=P.compile_fragment(root,file(root,WEIDU,100000),file(root,'lang/ru_RU/dialog.tlk'),old_baf)
        compiled_new=P.compile_fragment(root,file(root,WEIDU,100000),file(root,'lang/ru_RU/dialog.tlk'),new_baf)
    merged,delta=Q.assemble(file(root,BCS).read_bytes(),compiled_old,compiled_new)
    if delta['proposed_sha256']!=ready['patch']['proposed_sha256']:
        raise Stop('NONDETERMINISTIC_ASSEMBLY')
    stage=root/'BGXP3'
    stage.mkdir(exist_ok=False)
    (stage/'staged').mkdir(exist_ok=False)
    (root/STAGED).write_bytes(merged)
    shutil.copy2(file(root,BCS),root/OLD)
    (root/PROOF).write_text(json.dumps({'old_bcs_sha256':Q.LIVE_BCS_SHA,
           'new_bcs_sha256':sha(merged),'lua_sha256':Q.LIVE_LUA_SHA},indent=2)+'\n',encoding='utf-8')
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(file(root,WEIDU,100000),root/EXE)
    guard_processes();base(root,allow_stage=True)
    if sha(file(root,'WeiDU.log').read_bytes())!=oldlog:
        raise Stop('WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    report=weidu(root)
    (backup/'weidu_install_log_tail.txt').write_text(report,encoding='utf-8')
    after=installed(root)
    verify_untouched(root,backup)
    return {'status':'BGXP3_INSTALLED_VERIFIED','backup':str(backup),'after':after}

def rollback(root:Path)->dict:
    guard_processes();root=root.resolve(strict=True)
    state=installed(root)
    backup=snapshot(root,state,'PRE_ROLLBACK')
    guard_processes();installed(root)
    report=weidu(root,uninstall=True)
    (backup/'weidu_rollback_log_tail.txt').write_text(report,encoding='utf-8')
    restored=base(root,allow_stage=True)
    verify_untouched(root,backup)
    return {'status':'BGXP3_ROLLED_BACK_TO_BGXP2','backup':str(backup),'after':restored}

def main(args=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',nargs='?',default='status',choices=['status','preflight','install','rollback'])
    ap.add_argument('--yes',action='store_true')
    ap.add_argument('--confirm',default='')
    ap.add_argument('--game-root',type=Path,default=GAME)
    opts=ap.parse_args(args)
    try:
        sources()
        if opts.mode=='status':
            info=installed(opts.game_root) if NEW_LAST.match(last(opts.game_root)) else base(opts.game_root,allow_stage=True)
            print(json.dumps({'status':'READ_ONLY_STATUS','game':info},ensure_ascii=False,indent=2));return 0
        if opts.mode=='preflight':
            print(json.dumps(preflight(opts.game_root),ensure_ascii=False,indent=2));return 0
        required=INSTALL_TOKEN if opts.mode=='install' else ROLLBACK_TOKEN
        if not opts.yes or opts.confirm!=required: raise Stop('EXPLICIT_CONFIRMATION_REQUIRED:'+required)
        if os.name!='nt' or opts.game_root!=GAME: raise Stop('LIVE_MUTATION_REQUIRES_EXACT_WINDOWS_GAME_ROOT')
        report=install(GAME) if opts.mode=='install' else rollback(GAME)
        print(json.dumps(report,ensure_ascii=False,indent=2));return 0
    except (Stop,ValueError,OSError,UnicodeError,subprocess.TimeoutExpired,KeyError) as exc:
        print('BGXP3_STOP:',exc);return 2

if __name__=='__main__':sys.exit(main())
