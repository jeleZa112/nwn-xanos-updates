#!/usr/bin/env python3
"""BGXAI 067 guarded two-file WeiDU upgrade FROM EXACT INSTALLED 066S.

No game writes by default. Direct live install only through the pinned onefile
updater with typed approval. Always backup both game scripts and core WeiDU state.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
import BGXAI66S_INSTALL as prior
import BGXAI67_BCS_PATCH as patch

ROOT=prior.ROOT
BCS=prior.BCS
LUA=prior.LUA
WEIDU=prior.WEIDU
SOURCE=Path(__file__).parent
BAF=SOURCE/'BGX67_EARLY_GUARD.baf'
CANDIDATE=SOURCE/'M_BX43_067_EARLY_CANDIDATE.lua'
STAGE_BCS='BGX67/staged/BDDEFAI.BCS'
STAGE_LUA='BGX67/staged/M_BX43.lua'
PIN_FILE='BGX67/EXPECTED_BCS_SHA256.txt'
TP2='BGX67/setup-BGX67.tp2'
EXE='setup-BGX67.exe'
LAST067=re.compile(r'^~(?:[^~]*[/\\])?BGX67[/\\]SETUP-BGX67\.TP2~(?=\s|$)',re.I)
TP2_TEXT=('BACKUP ~BGX67/backup~\n'
    'AUTHOR ~BGXAI 067 bounded early defense and 066S healer compatibility~\n'
    'BEGIN ~BGXAI 067 early resolved-threat guard with heal priority~\n'
    'COPY ~BGX67/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
    'COPY ~BGX67/staged/M_BX43.lua~ ~override/M_BX43.lua~\n')
PIN066S='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
PIN067='9df658011da77ee1c7c14f8aa58b2699a712171caa3d2e8ac777158a3e80b2c6'
sha=lambda b:hashlib.sha256(b).hexdigest()
class Stop(RuntimeError):pass

def source_check():
    prior.source_check()   # preserve immutable, tested 066S base and original aid
    for p in (BAF,CANDIDATE,SOURCE/'BGX67_PREHIT_GUARD.lua'):
        if not p.is_file() or prior.old.is_reparse(p):raise Stop('067_SOURCE_MISSING_OR_LINK:'+p.name)
    if sha(BAF.read_bytes())!=patch.PIN_FRAGMENT_BAF:raise Stop('067_BAF_SHA_DRIFT')
    if sha(CANDIDATE.read_bytes())!=PIN067:raise Stop('067_CANDIDATE_SHA_DRIFT')
    from build_067 import build
    if build()!=CANDIDATE.read_bytes():raise Stop('067_CANDIDATE_NOT_DETERMINISTIC')
    if sha((SOURCE/'M_BX43_066S_CASTER_CANDIDATE.lua').read_bytes())!=PIN066S:
        raise Stop('066S_PARENT_LUA_DRIFT')
    return {'lua_sha256':PIN067,'baf_sha256':patch.PIN_FRAGMENT_BAF}

def game066s(root):
    try:proof=prior.status066s(root)
    except (prior.Stop,prior.old.Stop,ValueError,OSError) as e:
        raise Stop('066S_BASELINE_NOT_VERIFIED:'+str(e)) from e
    if proof['bcs_sha256']!=patch.PIN_066S_BCS:raise Stop('066S_BCS_SHA_PIN_MISMATCH')
    return proof

def status067(root):
    source_check()
    if not LAST067.search(prior.old.last_mod(root)):raise Stop('067_NOT_LAST_WEIDU')
    bcs=prior.old.safe_file(root,BCS).read_bytes()
    lua=prior.old.safe_file(root,LUA).read_bytes()
    if sha(lua)!=PIN067:raise Stop('067_LUA_SHA_DRIFT')
    if bcs!=prior.old.safe_file(root,STAGE_BCS).read_bytes():raise Stop('067_STAGED_BCS_DRIFT')
    expected=prior.old.safe_file(root,PIN_FILE).read_text(encoding='ascii').strip()
    if not re.fullmatch(r'[a-f0-9]{64}',expected) or sha(bcs)!=expected:
        raise Stop('067_BCS_SHA_DRIFT')
    if lua!=prior.old.safe_file(root,STAGE_LUA).read_bytes():raise Stop('067_STAGED_LUA_DRIFT')
    if prior.old.safe_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:
        raise Stop('067_TP2_DRIFT')
    prior.old.safe_file(root,EXE,100000)
    if sha(prior.old.safe_file(root,prior.STAGE_BCS).read_bytes())!=patch.PIN_066S_BCS:
        raise Stop('066S_STAGING_DRIFT;ROLLBACK_UNSAFE')
    if sha(prior.old.safe_file(root,prior.STAGE_LUA).read_bytes())!=PIN066S:
        raise Stop('066S_LUA_STAGING_DRIFT;ROLLBACK_UNSAFE')
    patch.verify_installed(bcs)
    return {'status':'INSTALLED_067_VERIFIED','bcs_sha256':sha(bcs),
            'lua_sha256':sha(lua),'last_weidu':prior.old.last_mod(root)}

def guard():prior.guard()

def backup(root,proof,label):
    location=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI67_SAFE_BACKUPS'
    return prior.old.make_backup(root,proof,label,parent=location)

def prepare(root,*,compiler=patch.compile_real_game,process_guard=guard):
    process_guard();source_check();root=root.resolve(strict=True)
    baseline=game066s(root)
    current=prior.old.safe_file(root,BCS).read_bytes()
    if sha(current)!=patch.PIN_066S_BCS:raise Stop('BASELINE_CHANGED_DURING_READONLY')
    patch.before(current)
    exe=prior.old.safe_file(root,WEIDU,100000)
    with exe.open('rb') as f:
        if f.read(2)!=b'MZ':raise Stop('WEIDU_EXE_INVALID')
    compiled=compiler(root,BAF,exe,prior.old.safe_file(root,'lang/ru_RU/dialog.tlk'))
    candidate,report=patch.splice(current,compiled)
    process_guard();game066s(root)
    return {'mode':'READ_ONLY','baseline':baseline,'candidate_lua_sha256':PIN067,
     'candidate_bcs_sha256':sha(candidate),'compiled_bcs_sha256':sha(compiled),
     'patch':report,'authorized_to_install':False},candidate

def call_weidu(root,*,uninstall=False,runner=subprocess.run):
    args=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
      '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(args,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
       text=True,encoding='utf-8',errors='replace',timeout=180,check=False)
    out=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode!=0 or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',out):
        raise Stop('067_WEIDU_FAILED_DO_NOT_RETRY:'+out[-1200:])
    return {'returncode':p.returncode,'stdout':out[-2200:]}

def install(root=ROOT,*,process_guard=guard,compiler=patch.compile_real_game,
            make_backup=backup,runner=subprocess.run):
    process_guard();source_check();root=root.resolve(strict=True)
    if (root/'BGX67').exists() or (root/EXE).exists():raise Stop('067_STAGE_COLLISION')
    pre,new_bcs=prepare(root,compiler=compiler,process_guard=process_guard)
    for rel in prior.old.BACKUP:prior.old.safe_file(root,rel)
    weidu=prior.old.safe_file(root,WEIDU,100000)
    old_log=sha(prior.old.safe_file(root,'WeiDU.log').read_bytes())
    saved=make_backup(root,pre,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('EXTERNAL_BACKUP_NOT_VERIFIED')
    process_guard();game066s(root)
    if sha(prior.old.safe_file(root,'WeiDU.log').read_bytes())!=old_log:
        raise Stop('WEIDU_CHANGED_BEFORE_STAGING')
    (root/'BGX67/staged').mkdir(parents=True,exist_ok=False)
    (root/STAGE_BCS).write_bytes(new_bcs)
    (root/STAGE_LUA).write_bytes(CANDIDATE.read_bytes())
    (root/PIN_FILE).write_text(pre['candidate_bcs_sha256']+'\n',encoding='ascii')
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(weidu,root/EXE)
    if sha(prior.old.safe_file(root,STAGE_BCS).read_bytes())!=pre['candidate_bcs_sha256']:
        raise Stop('BCS_STAGING_VERIFY_FAIL;BACKUP='+str(saved))
    if sha(prior.old.safe_file(root,STAGE_LUA).read_bytes())!=PIN067:
        raise Stop('LUA_STAGING_VERIFY_FAIL;BACKUP='+str(saved))
    process_guard()
    result=call_weidu(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    after=status067(root)
    if after['bcs_sha256']!=pre['candidate_bcs_sha256']:
        raise Stop('AFTER_INSTALL_BCS_SHA_DRIFT;BACKUP='+str(saved))
    return {'status':'INSTALLED_067_EXPERIMENTAL','backup':str(saved),'after':after}

def rollback(root=ROOT,*,process_guard=guard,make_backup=backup,runner=subprocess.run):
    process_guard();source_check();root=root.resolve(strict=True)
    before=status067(root)
    saved=make_backup(root,before,'PRE_ROLLBACK')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('EXTERNAL_BACKUP_NOT_VERIFIED')
    process_guard();status067(root);process_guard()
    result=call_weidu(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    after=game066s(root)
    return {'status':'ROLLED_BACK_TO_066S_VERIFIED','backup':str(saved),'after':after}

def main(argv=None):
    p=argparse.ArgumentParser(description='BGXAI 067 guarded early defense; read-only default')
    p.add_argument('mode',choices=('preflight','status','install','rollback'),nargs='?',default='status')
    p.add_argument('--yes',action='store_true')
    p.add_argument('--confirm',default='')
    p.add_argument('--game-root',type=Path,default=ROOT)
    a=p.parse_args(argv)
    try:
        if a.mode=='preflight':
            proof,_=prepare(a.game_root)
            print(json.dumps(proof,ensure_ascii=False,indent=2));return 0
        if a.mode=='status':
            state=status067(a.game_root) if LAST067.search(prior.old.last_mod(a.game_root)) else game066s(a.game_root)
            print(json.dumps({'mode':'READ_ONLY','proof':state},indent=2));return 0
        phrase={'install':'INSTALL_BGXAI_067','rollback':'ROLLBACK_BGXAI_067'}[a.mode]
        if not a.yes or a.confirm!=phrase:raise Stop('EXPLICIT_APPROVAL_REQUIRED:'+phrase)
        if a.game_root!=ROOT:raise Stop('LIVE_INSTALL_FIXED_ROOT_ONLY')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (Stop,prior.Stop,prior.old.Stop,ValueError,AssertionError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print('BGXAI067 STOP:',str(e));return 2
if __name__=='__main__':sys.exit(main())
