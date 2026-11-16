#!/usr/bin/env python3
"""Guarded manual game install for 066S / BGXTEAM + BGXPR healer-mode fallback.
Existing WeiDU and EPS blocks are preserved exactly. Default entry point is read-only.
No install without typed token, game-closed check, preflight and external verified backup.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,re,shutil,stat,subprocess,sys
from pathlib import Path
import BGXPR_BCS_PATCH as PATCH
ROOT=Path(r'C:\Games\BG_EET_FOXX_NEW')
BASE=Path(__file__).resolve().parent
PINS={'066S':('50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f','M_BX43_066S_PRIEST_MODES.lua'),
      'BGXTEAM':('778987e0fc0fccadab68a01fcbd6ba9b393aefbe409d7496a940209faf35f006','M_BX43_BGXTEAM_PRIEST_MODES.lua')}
LUA='override/M_BX43.lua';BCS='override/BDDEFAI.BCS';WEIDU='setup-enhanced-powergaming-scripts.exe'
STAGELUA='BGXPRIEST/staged/M_BX43.lua';STAGEBCS='BGXPRIEST/staged/BDDEFAI.BCS'
PROOF='BGXPRIEST/STAGED_PROOF.json';TP2='BGXPRIEST/setup-BGXPRIEST.tp2';EXE='setup-BGXPRIEST.exe'
TP2_TEXT='BACKUP ~BGXPRIEST/backup~\nAUTHOR ~BGXAI Priest EPS-first mode fallback~\nBEGIN ~BGXAI Priest Modes 066S EPS fallback~\nCOPY ~BGXPRIEST/staged/M_BX43.lua~ ~override/M_BX43.lua~\nCOPY ~BGXPRIEST/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
BACKUP=('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk',LUA,BCS)
INSTALL_TOKEN='INSTALL_BGXPRIEST_MODES';ROLLBACK_TOKEN='ROLLBACK_BGXPRIEST_MODES'
LAST={'066S':re.compile(r'^~(?:[^~]*[/\\])?BGX66S[/\\]SETUP-BGX66S\.TP2~\s+#0\s+#0(?:\s|$)',re.I),
      'BGXTEAM':re.compile(r'^~(?:[^~]*[/\\])?BGXTEAM[/\\]SETUP-BGXTEAM\.TP2~\s+#0\s+#0(?:\s|$)',re.I),
      'BGXPR':re.compile(r'^~(?:[^~]*[/\\])?BGXPRIEST[/\\]SETUP-BGXPRIEST\.TP2~\s+#0\s+#0(?:\s|$)',re.I)}
class Stop(RuntimeError):pass
def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def no_link(x:Path):
    if x.is_symlink():raise Stop('REPARSE_OR_SYMLINK:'+str(x))
    try:
      if x.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise Stop('REPARSE_POINT:'+str(x))
    except (AttributeError,FileNotFoundError): pass
def game_file(root:Path,rel:str,minsize=1):
    if not rel or rel.startswith(('\\','/')) or ':' in rel or '..' in rel.replace('\\','/').split('/') or '\\' in rel:raise Stop('UNSAFE_PATH')
    f=root/rel
    for x in (f,*f.parents):
        no_link(x)
        if x==root:break
    if not f.is_file() or f.stat().st_size<minsize:raise Stop('MISSING_REQUIRED_FILE:'+rel)
    return f
def source_manifest():
    f=BASE/'SHA256_FILES.json';data=json.loads(f.read_text(encoding='utf-8'))
    for name,digest in data['sha256'].items():
        s=BASE/name
        no_link(s)
        if not s.is_file() or sha(s.read_bytes())!=digest:raise Stop('SOURCE_SHA_FAILURE:'+name)
    if set(data['sha256'])!=set(data['required_files']):raise Stop('SOURCE_MANIFEST_MISMATCH')
    for variant,(original,filename) in PINS.items():
        base_file=BASE/('M_BX43_'+('066S_CASTER_CANDIDATE.lua' if variant=='066S' else '066S_GUARD_TEAM_CANDIDATE.lua'))
        if sha(base_file.read_bytes())!=original:raise Stop('BASE_SOURCE_SHA_DRIFT')
        if not (BASE/filename).read_bytes().startswith(base_file.read_bytes()):raise Stop('CANDIDATE_PREFIX_CHANGED')
    if not (BASE/'BGXPR_LAST_PRIORITY.baf').read_text(encoding='utf-8').count('IF\n')==PATCH.ADDED:raise Stop('BAF_BLOCK_DRIFT')
    return data
def last_mod(root:Path):
    lines=[x.strip() for x in game_file(root,'WeiDU.log').read_text(encoding='utf-8-sig',errors='replace').splitlines() if x.strip().startswith('~')]
    if not lines:raise Stop('EMPTY_WEIDU_LOG')
    return lines[-1]
def exact_base(root:Path, *,staging_allowed:bool=False):
    root=root.resolve(strict=True);no_link(root);line=last_mod(root)
    variant=next((x for x in ('066S','BGXTEAM') if LAST[x].match(line)),None)
    if variant is None:raise Stop('UNRECOGNIZED_LAST_WEIDU:'+line)
    original=PINS[variant][0]
    if sha(game_file(root,LUA).read_bytes())!=original:raise Stop('LIVE_LUA_BASE_SHA_MISMATCH')
    raw=game_file(root,BCS).read_bytes()
    if sha(raw)!=PATCH.BCS_PIN or len(PATCH.chunks(raw,PATCH.BCS_BLOCKS))!=PATCH.BCS_BLOCKS:raise Stop('LIVE_BCS_066S_MISMATCH')
    if not staging_allowed and ((root/'BGXPRIEST').exists() or (root/EXE).exists()):raise Stop('BGXPR_STAGING_ALREADY_EXISTS')
    return {'state':'VERIFIED_BASELINE','variant':variant,'last_weidu':line,'lua_sha256':original,'bcs_sha256':PATCH.BCS_PIN}
def verify_install(root:Path):
    if not LAST['BGXPR'].match(last_mod(root)):raise Stop('BGXPR_NOT_LAST_WEIDU')
    source_manifest();proof=json.loads(game_file(root,PROOF).read_text(encoding='utf-8'))
    if proof.get('base_variant') not in PINS:raise Stop('BAD_INSTALL_PROOF_VARIANT')
    expected_lua=sha((BASE/PINS[proof['base_variant']][1]).read_bytes())
    if proof.get('new_lua_sha256')!=expected_lua:raise Stop('POSTINSTALL_LUA_PROOF_DRIFT')
    for path,exp in ((LUA,expected_lua),(BCS,proof['new_bcs_sha256']),(STAGELUA,expected_lua),(STAGEBCS,proof['new_bcs_sha256'])):
        if sha(game_file(root,path).read_bytes())!=exp:raise Stop('POSTINSTALL_FILE_SHA_MISMATCH:'+path)
    if game_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:raise Stop('INSTALLED_TP2_CHANGED')
    if proof.get('base_bcs_sha256')!=PATCH.BCS_PIN:raise Stop('OLD_BCS_PROOF_MISMATCH')
    src=game_file(root,BCS).read_bytes();seg=PATCH.chunks(src,PATCH.BCS_BLOCKS+PATCH.ADDED)
    restored=b'SC\n'+b''.join(seg[:PATCH.BCS_BLOCKS-1]+[seg[PATCH.BCS_BLOCKS-1]+b'SC\n'])
    # Previous BCS block was nonterminal; last old chunk must have CR\n, not SC\n.
    if sha(restored)!=PATCH.BCS_PIN:raise Stop('LEGACY_EPS_BLOCKS_NOT_RESTORABLE')
    return {'state':'BGXPR_INSTALLED_VERIFIED','base_variant':proof['base_variant'],'bcs_sha256':sha(src),'lua_sha256':expected_lua}
def guard_process():
    if os.name!='nt':raise Stop('WINDOWS_ONLY')
    proc=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',
      '$x=Get-CimInstance Win32_Process | Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"}; if($x){$x|Select-Object Name,ProcessId|Out-String; exit 3}'],
      stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=30,check=False)
    if proc.returncode or proc.stdout.strip():raise Stop('GAME_LOADER_OR_WEIDU_RUNNING_OR_PROCESS_SCAN_FAILURE:'+proc.stdout[-300:])
def backup(root:Path,state:dict,label:str):
    base=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI_PRIEST_SAFE_BACKUPS'
    no_link(base);no_link(base.parent)
    real=base.resolve();game=root.resolve()
    if real==game or game in real.parents:raise Stop('BACKUP_INSIDE_GAME')
    base.mkdir(parents=True,exist_ok=True)
    dest=base/(label+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False);data={}
    for rel in BACKUP:
        a=game_file(root,rel);b=dest/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
        data[rel]=sha(a.read_bytes())
        if sha(b.read_bytes())!=data[rel]:raise Stop('BACKUP_VERIFICATION_FAILED:'+rel)
    (dest/'PROOF.json').write_text(json.dumps({'state':state,'sha256':data},indent=2)+'\n',encoding='utf-8')
    return dest
def check_unchanged(root:Path,bak:Path):
    data=json.loads((bak/'PROOF.json').read_text(encoding='utf-8'))['sha256']
    for rel in BACKUP:
      if rel not in (LUA,BCS,'WeiDU.log') and sha(game_file(root,rel).read_bytes())!=data[rel]:
        raise Stop('UNEXPECTED_GAME_FILE_CHANGED:'+rel)
def weidu_run(root:Path, uninstall=False):
    exe=game_file(root,EXE,100000)
    cmd=[str(exe),'--noautoupdate','--no-exit-pause','--game',str(root),'--use-lang','ru_ru',
      '--force-uninstall' if uninstall else '--force-install','0']
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=200,check=False)
    log=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',log):raise Stop('WEIDU_FAILED_NO_AUTORETRY:'+log[-1700:])
    return log[-1800:]
def preflight(root:Path):
    source_manifest();base=exact_base(root)
    weidu=game_file(root,WEIDU,100000)
    if weidu.read_bytes()[:2]!=b'MZ':raise Stop('INVALID_WEIDU_EXE')
    for rel in BACKUP:game_file(root,rel)
    compiled=PATCH.compile_fragment(root,weidu,game_file(root,'lang/ru_RU/dialog.tlk'),BASE/'BGXPR_LAST_PRIORITY.baf')
    merged,changes=PATCH.splice(game_file(root,BCS).read_bytes(),compiled)
    return {'status':'REAL_EET_COMPILE_READ_ONLY_PASS','base':base,'compiled_fragment_sha256':sha(compiled),
       'candidate_lua_sha256':sha((BASE/PINS[base['variant']][1]).read_bytes()),'bcs_patch':changes,'authorized_to_install':False}
def install(root:Path):
    guard_process();root=root.resolve(strict=True);result=preflight(root)
    pre_sha=sha(game_file(root,'WeiDU.log').read_bytes());bak=backup(root,result['base'],'PRE_INSTALL')
    guard_process();exact_base(root)
    if sha(game_file(root,'WeiDU.log').read_bytes())!=pre_sha:raise Stop('WEIDU_LOG_CHANGED_DURING_PREFLIGHT')
    compiled=PATCH.compile_fragment(root,game_file(root,WEIDU),game_file(root,'lang/ru_RU/dialog.tlk'),BASE/'BGXPR_LAST_PRIORITY.baf')
    merged,changes=PATCH.splice(game_file(root,BCS).read_bytes(),compiled)
    if changes['new_sha256']!=result['bcs_patch']['new_sha256']:raise Stop('COMPILED_BCS_NOT_DETERMINISTIC')
    stage=root/'BGXPRIEST';stage.mkdir(exist_ok=False);(stage/'staged').mkdir(exist_ok=False)
    variant=result['base']['variant'];lua_src=(BASE/PINS[variant][1]).read_bytes()
    (root/STAGELUA).write_bytes(lua_src);(root/STAGEBCS).write_bytes(merged)
    (root/PROOF).write_text(json.dumps({'base_variant':variant,'base_bcs_sha256':PATCH.BCS_PIN,
       'new_bcs_sha256':sha(merged),'new_lua_sha256':sha(lua_src),'fragment_sha256':sha(compiled)},indent=2)+'\n',encoding='utf-8')
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(game_file(root,WEIDU,100000),root/EXE)
    guard_process();exact_base(root,staging_allowed=True)
    if sha(game_file(root,'WeiDU.log').read_bytes())!=pre_sha:raise Stop('WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    log=weidu_run(root)
    (bak/'weidu_install_log_tail.txt').write_text(log,encoding='utf-8')
    after=verify_install(root);check_unchanged(root,bak)
    return {'status':'BGXPR_INSTALLED_VERIFIED','backup':str(bak),'after':after}
def rollback(root:Path):
    guard_process();root=root.resolve(strict=True);current=verify_install(root)
    bak=backup(root,current,'PRE_ROLLBACK');guard_process();verify_install(root)
    log=weidu_run(root,uninstall=True)
    (bak/'weidu_rollback_log_tail.txt').write_text(log,encoding='utf-8')
    after=exact_base(root,staging_allowed=True)
    if after['variant']!=current['base_variant']:raise Stop('ROLLBACK_BASE_VARIANT_MISMATCH')
    check_unchanged(root,bak)
    return {'status':'BGXPR_RETURNED_TO_PREVIOUS_BASE_VERIFIED','backup':str(bak),'after':after}
def main(args=None):
    parser=argparse.ArgumentParser();parser.add_argument('mode',nargs='?',default='status',choices=['status','preflight','install','rollback']);
    parser.add_argument('--yes',action='store_true');parser.add_argument('--confirm',default='');parser.add_argument('--game-root',type=Path,default=ROOT)
    a=parser.parse_args(args)
    try:
        source_manifest()
        if a.mode=='status':
            state=verify_install(a.game_root) if LAST['BGXPR'].match(last_mod(a.game_root)) else exact_base(a.game_root,staging_allowed=True)
            print(json.dumps({'status':'READ_ONLY_STATUS','game':state},ensure_ascii=False,indent=2));return 0
        if a.mode=='preflight':
            print(json.dumps(preflight(a.game_root),ensure_ascii=False,indent=2));return 0
        token=INSTALL_TOKEN if a.mode=='install' else ROLLBACK_TOKEN
        if not a.yes or a.confirm!=token:raise Stop('EXPLICIT_APPROVAL_MISSING:'+token)
        if os.name!='nt' or a.game_root!=ROOT:raise Stop('GAME_MUTATION_ONLY_AT_CONFIRMED_WINDOWS_ROOT')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (Stop,ValueError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print('BGXPR_STOP:',str(e));return 2
if __name__=='__main__':sys.exit(main())
