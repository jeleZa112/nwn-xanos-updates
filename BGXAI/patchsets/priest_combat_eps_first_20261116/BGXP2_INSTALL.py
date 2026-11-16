#!/usr/bin/env python3
"""Additive EPS-first combat priest upgrade over verified installed BGXPR. No automatic installs."""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
import BGXP2_BCS_PATCH as PATCH
ROOT=Path(r'C:\Games\BG_EET_FOXX_NEW');BASE=Path(__file__).resolve().parent
BCS='override/BDDEFAI.BCS';LUA='override/M_BX43.lua';WEIDU='setup-enhanced-powergaming-scripts.exe'
STAGE='BGXP2/staged/BDDEFAI.BCS';PROOF='BGXP2/STAGED_PROOF.json';TP2='BGXP2/setup-BGXP2.tp2';EXE='setup-BGXP2.exe'
TP2_TEXT='BACKUP ~BGXP2/backup~\nAUTHOR ~BGXAI EPS first cleric combat roles~\nBEGIN ~BGXAI BGXP2 support battle auto 28 fallback actions~\nCOPY ~BGXP2/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
BASE_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXPRIEST[/\\]SETUP-BGXPRIEST\.TP2~\s+#0\s+#0(?:\s|$)',re.I)
OURS_LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXP2[/\\]SETUP-BGXP2\.TP2~\s+#0\s+#0(?:\s|$)',re.I)
BACKUP=('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk',LUA,BCS)
INSTALL_TOKEN='INSTALL_BGXP2_COMBAT_PRIEST';ROLLBACK_TOKEN='ROLLBACK_BGXP2_COMBAT_PRIEST'
class Stop(RuntimeError):pass
def sha(raw:bytes):return hashlib.sha256(raw).hexdigest()
def no_link(p:Path):
    if p.is_symlink():raise Stop('SYMLINK:'+str(p))
    try:
        if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise Stop('REPARSE:'+str(p))
    except (AttributeError,FileNotFoundError):pass
def file(root:Path,path:str,minsize=1):
    if not path or '\\' in path or ':' in path or '..' in path.split('/') or path.startswith('/'):
        raise Stop('UNSAFE_GAME_PATH:'+path)
    f=root/path
    for e in (f,*f.parents):
        no_link(e)
        if e==root:break
    if not f.is_file() or f.stat().st_size<minsize:raise Stop('MISSING_REQUIRED_FILE:'+path)
    return f
def sources():
    m=json.loads((BASE/'SHA256_FILES.json').read_text(encoding='utf-8'))
    if m['schema']!=1 or set(m['files'])!=set(m['sha256']):raise Stop('SOURCE_MANIFEST_INVALID')
    for n in m['files']:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',n):raise Stop('SOURCE_NAME_INVALID')
        p=BASE/n;no_link(p)
        if not p.is_file() or sha(p.read_bytes())!=m['sha256'][n]:raise Stop('SOURCE_HASH_MISMATCH:'+n)
    baf=(BASE/'BGXP2_LAST_PRIORITY.baf').read_text(encoding='utf-8')
    if baf.count('\nIF\n')!=PATCH.ADDED:raise Stop('BAF_BLOCK_COUNT_DRIFT')
    return m
def last(root:Path):
    lines=[s.strip() for s in file(root,'WeiDU.log').read_text(encoding='utf-8-sig',errors='replace').splitlines() if s.strip().startswith('~')]
    if not lines:raise Stop('EMPTY_WEIDU_LOG')
    return lines[-1]
def base(root:Path,allow_stage=False):
    root=root.resolve(strict=True);no_link(root);line=last(root)
    if not BASE_LAST.match(line):raise Stop('EXACT_BGXPR_LAST_REQUIRED:'+line)
    if sha(file(root,LUA).read_bytes())!=PATCH.LUA_PIN:raise Stop('BGXPR_LUA_CHANGED')
    raw=file(root,BCS).read_bytes()
    if sha(raw)!=PATCH.BCS_PIN:raise Stop('BGXPR_BCS_SHA_CHANGED')
    PATCH.chunks(raw,PATCH.BASE_BLOCKS)
    oldproof=json.loads(file(root,'BGXPRIEST/STAGED_PROOF.json').read_text(encoding='utf-8'))
    if oldproof.get('new_bcs_sha256')!=PATCH.BCS_PIN or oldproof.get('new_lua_sha256')!=PATCH.LUA_PIN:
        raise Stop('BGXPR_INSTALLED_PROOF_CHANGED')
    if not allow_stage and ((root/'BGXP2').exists() or (root/EXE).exists()):
        raise Stop('BGXP2_STAGING_EXISTS')
    return {'state':'BGXPR_INSTALLED_VERIFIED','last_weidu':line,'lua_sha256':PATCH.LUA_PIN,'bcs_sha256':PATCH.BCS_PIN}
def installed(root:Path):
    if not OURS_LAST.match(last(root)):raise Stop('BGXP2_NOT_LAST_WEIDU')
    if sha(file(root,LUA).read_bytes())!=PATCH.LUA_PIN:raise Stop('NON_TARGET_LUA_CHANGED')
    if file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:raise Stop('BGXP2_TP2_CHANGED')
    proof=json.loads(file(root,PROOF).read_text(encoding='utf-8'))
    if proof.get('old_bcs_sha256')!=PATCH.BCS_PIN or proof.get('new_bcs_sha256') is None:
        raise Stop('BGXP2_PROOF_INVALID')
    raw=file(root,BCS).read_bytes()
    if sha(raw)!=proof['new_bcs_sha256'] or sha(file(root,STAGE).read_bytes())!=sha(raw):
        raise Stop('BGXP2_INSTALLED_BCS_SHA_MISMATCH')
    blocks=PATCH.chunks(raw,PATCH.BASE_BLOCKS+PATCH.ADDED)
    recovered=b'SC\n'+b''.join(blocks[:PATCH.BASE_BLOCKS-1]+[blocks[PATCH.BASE_BLOCKS-1]+b'SC\n'])
    if sha(recovered)!=PATCH.BCS_PIN:raise Stop('ORIGINAL_BGXPR_NOT_RECOVERABLE')
    return {'state':'BGXP2_INSTALLED_VERIFIED','lua_sha256':PATCH.LUA_PIN,'bcs_sha256':sha(raw),'total_blocks':len(blocks)}
def running_guard():
    if os.name!='nt':raise Stop('WINDOWS_ONLY')
    q=('$ErrorActionPreference="Stop"; $p=Get-CimInstance Win32_Process | '
       'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
       'if($p){$p|Select-Object Name,ProcessId|Out-String; exit 3}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',q],capture_output=True,
                     text=True,stdin=subprocess.DEVNULL,timeout=30,check=False)
    if p.returncode or p.stdout.strip():raise Stop('GAME_OR_WEIDU_RUNNING_OR_PROCESS_CHECK_FAILED:'+p.stdout[-400:])
def snapshot(root:Path,state:dict,tag:str):
    out=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI_PRIEST2_SAFE_BACKUPS'
    no_link(out);no_link(out.parent)
    if root.resolve(strict=True)==out.resolve() or root.resolve(strict=True) in out.resolve().parents:
        raise Stop('BACKUP_CANNOT_BE_INSIDE_GAME')
    out.mkdir(parents=True,exist_ok=True)
    d=out/(tag+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    d.mkdir(exist_ok=False);sums={}
    for rel in BACKUP:
        src=file(root,rel);dest=d/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest)
        sums[rel]=sha(src.read_bytes())
        if sha(dest.read_bytes())!=sums[rel]:raise Stop('BACKUP_SHA_MISMATCH:'+rel)
    (d/'PROOF.json').write_text(json.dumps({'state':state,'sha256':sums},indent=2)+'\n',encoding='utf-8')
    return d
def non_targets(root:Path,snapshot_dir:Path):
    hashes=json.loads((snapshot_dir/'PROOF.json').read_text())['sha256']
    for rel in BACKUP:
        if rel not in (BCS,'WeiDU.log') and sha(file(root,rel).read_bytes())!=hashes[rel]:
            raise Stop('UNEXPECTED_OTHER_FILE_CHANGED:'+rel)
def weidu(root:Path,uninstall=False):
    cmd=[str(file(root,EXE,100000)),'--noautoupdate','--no-exit-pause','--game',str(root),'--use-lang','ru_ru',
         '--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200,check=False)
    log=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',log):raise Stop('WEIDU_FAILED_NO_AUTO_RETRY:'+log[-1800:])
    return log[-1900:]
def preflight(root:Path):
    sources();current=base(root)
    exe=file(root,WEIDU,100000)
    if exe.read_bytes()[:2]!=b'MZ':raise Stop('INVALID_WEIDU_EXE')
    for f in BACKUP:file(root,f)
    frag=PATCH.compile_fragment(root,exe,file(root,'lang/ru_RU/dialog.tlk'),BASE/'BGXP2_LAST_PRIORITY.baf')
    merged,delta=PATCH.splice(file(root,BCS).read_bytes(),frag)
    return {'status':'REAL_EET_COMPILE_READ_ONLY_PASS','base':current,'compiled_fragment_sha256':sha(frag),
            'bcs_patch':delta,'authorized_to_install':False}
def install(root:Path):
    running_guard();root=root.resolve(strict=True);ready=preflight(root)
    logsha=sha(file(root,'WeiDU.log').read_bytes());save=snapshot(root,ready['base'],'PRE_INSTALL')
    running_guard();base(root)
    if sha(file(root,'WeiDU.log').read_bytes())!=logsha:raise Stop('WEIDU_LOG_CHANGED_DURING_PREFLIGHT')
    fragment=PATCH.compile_fragment(root,file(root,WEIDU,100000),file(root,'lang/ru_RU/dialog.tlk'),BASE/'BGXP2_LAST_PRIORITY.baf')
    merged,delta=PATCH.splice(file(root,BCS).read_bytes(),fragment)
    if delta['new_sha256']!=ready['bcs_patch']['new_sha256']:raise Stop('NONDETERMINISTIC_COMPILATION')
    stage=root/'BGXP2';stage.mkdir(exist_ok=False);(stage/'staged').mkdir(exist_ok=False)
    (root/STAGE).write_bytes(merged)
    (root/PROOF).write_text(json.dumps({'old_bcs_sha256':PATCH.BCS_PIN,'new_bcs_sha256':sha(merged),
        'fragment_sha256':sha(fragment),'lua_sha256':PATCH.LUA_PIN},indent=2)+'\n',encoding='utf-8')
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(file(root,WEIDU,100000),root/EXE)
    running_guard();base(root,allow_stage=True)
    if sha(file(root,'WeiDU.log').read_bytes())!=logsha:raise Stop('WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    result=weidu(root)
    (save/'weidu_install_log_tail.txt').write_text(result,encoding='utf-8')
    after=installed(root);non_targets(root,save)
    return {'status':'BGXP2_INSTALLED_VERIFIED','backup':str(save),'after':after}
def rollback(root:Path):
    running_guard();root=root.resolve(strict=True);curr=installed(root)
    save=snapshot(root,curr,'PRE_ROLLBACK');running_guard();installed(root)
    result=weidu(root,uninstall=True)
    (save/'weidu_rollback_log_tail.txt').write_text(result,encoding='utf-8')
    after=base(root,allow_stage=True);non_targets(root,save)
    return {'status':'BGXP2_RETURNED_TO_BGXPR_VERIFIED','backup':str(save),'after':after}
def main(args=None):
    p=argparse.ArgumentParser();p.add_argument('mode',nargs='?',default='status',choices=['status','preflight','install','rollback'])
    p.add_argument('--yes',action='store_true');p.add_argument('--confirm',default='');p.add_argument('--game-root',type=Path,default=ROOT)
    a=p.parse_args(args)
    try:
        sources()
        if a.mode=='status':
            state=installed(a.game_root) if OURS_LAST.match(last(a.game_root)) else base(a.game_root,allow_stage=True)
            print(json.dumps({'status':'READ_ONLY_STATUS','game':state},ensure_ascii=False,indent=2));return 0
        if a.mode=='preflight':
            print(json.dumps(preflight(a.game_root),ensure_ascii=False,indent=2));return 0
        token=INSTALL_TOKEN if a.mode=='install' else ROLLBACK_TOKEN
        if not a.yes or a.confirm!=token:raise Stop('EXPLICIT_CONFIRMATION_REQUIRED:'+token)
        if os.name!='nt' or a.game_root!=ROOT:raise Stop('LIVE_GAME_MUTATION_REQUIRES_EXACT_WINDOWS_ROOT')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (Stop,ValueError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print('BGXP2_STOP:',str(e));return 2
if __name__=='__main__':sys.exit(main())
