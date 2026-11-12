#!/usr/bin/env python3
"""Guarded 066S combined Lua+BCS WeiDU: source-only until explicit live authorization.

Requires VERIFIED installed 064, exact source pins, game closed, external SHA
backup, real installed-game IDS compile, reversible WeiDU install/rollback.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
import BGXAI64_INSTALL_SOURCE_ONLY as old
import BGXAI66S_BCS_PATCH as patch

ROOT=old.ROOT
LUA=old.LUA
BCS=old.BCS
WEIDU=old.WEIDU
SOURCE=Path(__file__).parent
BAF=SOURCE/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'
CANDIDATE=SOURCE/'M_BX43_066S_CASTER_CANDIDATE.lua'
STAGE_LUA='BGX66S/staged/M_BX43.lua'
STAGE_BCS='BGX66S/staged/BDDEFAI.BCS'
PIN_FILE='BGX66S/EXPECTED_BCS_SHA256.txt'
TP2='BGX66S/setup-BGX66S.tp2'
EXE='setup-BGX66S.exe'
LAST066S=re.compile(r'^~(?:[^~]*[/\\])?BGX66S[/\\]SETUP-BGX66S\.TP2~(?=\s|$)',re.I)
TP2_TEXT=('BACKUP ~BGX66S/backup~\n'
          'AUTHOR ~BGXAI 066S guarded Mage Cleric F support~\n'
          'BEGIN ~BGXAI 066S multi-frontline and caster guard~\n'
          'COPY ~BGX66S/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
          'COPY ~BGX66S/staged/M_BX43.lua~ ~override/M_BX43.lua~\n')
# This pin is checked against both source file and the deterministic build.
PIN066S='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
PIN066='c66ebb5190be8103819106a48d3100055b5791adf7c2d1df5f3e54596823540b'
class Stop(RuntimeError):pass
sha=lambda b:hashlib.sha256(b).hexdigest()

def source_check():
    if not CANDIDATE.is_file() or not BAF.is_file() or old.is_reparse(CANDIDATE) or old.is_reparse(BAF):
        raise Stop('SOURCE_MISSING_OR_UNSAFE')
    if sha(CANDIDATE.read_bytes())!=PIN066S:raise Stop('066S_LUA_SOURCE_HASH_MISMATCH')
    if sha(BAF.read_bytes())!=patch.PIN_FRAGMENT_BAF:raise Stop('066S_BAF_SOURCE_HASH_MISMATCH')
    # Source 066S is a fixed concatenation of 066 + support module.
    base=SOURCE/'M_BX43_066_CANDIDATE.lua'
    addon=SOURCE/'BGX66_CASTER_SUPPORT.lua'
    for p in (base,addon):
        if not p.is_file() or old.is_reparse(p):raise Stop('BUILD_SOURCE_MISSING_OR_LINK')
    if sha(base.read_bytes())!=PIN066:raise Stop('066_BASE_HASH_MISMATCH')
    from build_066s import build
    if build()!=CANDIDATE.read_bytes():raise Stop('066S_NONDETERMINISTIC_CANDIDATE')
    return {'lua_sha256':PIN066S,'baf_sha256':patch.PIN_FRAGMENT_BAF}

def game064(root):
    try:proof=old.read_status_064(root)
    except (old.Stop,ValueError,OSError) as e:raise Stop('064_BASELINE_NOT_VERIFIED:'+str(e)) from e
    if proof['bcs_sha256']!=patch.PIN_064_BCS:raise Stop('064_BCS_PIN_DRIFT')
    return proof

def status066s(root):
    last=old.last_mod(root)
    if not LAST066S.search(last):raise Stop('066S_NOT_LAST_WEIDU')
    source_check()
    bcs=old.safe_file(root,BCS).read_bytes()
    lua=old.safe_file(root,LUA).read_bytes()
    if sha(lua)!=PIN066S:raise Stop('066S_LUA_DRIFT')
    if bcs!=old.safe_file(root,STAGE_BCS).read_bytes():raise Stop('066S_STAGED_BCS_DRIFT')
    expected=old.safe_file(root,PIN_FILE).read_text(encoding='ascii').strip()
    if not re.fullmatch(r'[0-9a-f]{64}',expected) or sha(bcs)!=expected:
        raise Stop('066S_BCS_EXPECTED_SHA_DRIFT')
    if lua!=old.safe_file(root,STAGE_LUA).read_bytes():raise Stop('066S_STAGED_LUA_DRIFT')
    if old.safe_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:raise Stop('066S_TP2_DRIFT')
    old.safe_file(root,EXE,100000)
    if sha(old.safe_file(root,old.STAGED_LUA).read_bytes())!=old.LUA064_SHA:
        raise Stop('064_STAGING_DRIFT_CANNOT_ROLLBACK_SAFELY')
    if sha(bcs)==patch.PIN_064_BCS:raise Stop('BCS_NOT_MODIFIED_BY_066S')
    patch.verify_installed(bcs)
    return {'status':'INSTALLED_066S_VERIFIED','bcs_sha256':sha(bcs),
            'lua_sha256':sha(lua),'last_weidu':last}

def backup(root,proof,label):
    path=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI66S_SAFE_BACKUPS'
    return old.make_backup(root,proof,label,parent=path)

def guard():old.process_guard()

def call_weidu(root,*,uninstall=False,runner=subprocess.run):
    args=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
          '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(args,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
          text=True,encoding='utf-8',errors='replace',timeout=180,check=False)
    out=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode!=0 or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',out):
        raise Stop('WEIDU_FAILED_DO_NOT_RETRY:'+out[-1200:])
    return {'returncode':p.returncode,'stdout':out[-2200:]}

def prepare(root,*,compiler=patch.compile_real_game,process_guard=guard):
    """Read-only source/BCS/IDS preflight. Game is never staged or modified."""
    process_guard()
    source_check()
    root=root.resolve(strict=True)
    proof=game064(root)
    current=old.safe_file(root,BCS).read_bytes()
    if sha(current)!=patch.PIN_064_BCS:raise Stop('GAME_BCS_CHANGED_DURING_READONLY')
    patch.prove_original(current)
    exe=old.safe_file(root,WEIDU,100000)
    with exe.open('rb') as f:
        if f.read(2)!=b'MZ':raise Stop('WEIDU_EXE_INVALID')
    compiled=compiler(root,BAF,exe,old.safe_file(root,'lang/ru_RU/dialog.tlk'))
    merged,patch_proof=patch.splice(current,compiled)
    process_guard()
    game064(root)
    return {'mode':'READ_ONLY','baseline':proof,'candidate_lua_sha256':PIN066S,
        'candidate_bcs_sha256':sha(merged),'compile_bcs_sha256':sha(compiled),
        'patch':patch_proof,'authorized_to_install':False},merged

def install(root=ROOT,*,process_guard=guard,compiler=patch.compile_real_game,
            make_backup=backup,runner=subprocess.run):
    process_guard();source_check();root=root.resolve(strict=True)
    if (root/'BGX66S').exists() or (root/EXE).exists():raise Stop('066S_STAGE_COLLISION')
    pre,new_bcs=prepare(root,compiler=compiler,process_guard=process_guard)
    for rel in old.BACKUP:old.safe_file(root,rel)
    weidu=old.safe_file(root,WEIDU,100000)
    before_log=sha(old.safe_file(root,'WeiDU.log').read_bytes())
    saved=make_backup(root,pre,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('EXTERNAL_BACKUP_NOT_VERIFIED')
    process_guard();game064(root)
    if sha(old.safe_file(root,'WeiDU.log').read_bytes())!=before_log:raise Stop('WEIDU_CHANGED_BEFORE_STAGE')
    (root/'BGX66S/staged').mkdir(parents=True,exist_ok=False)
    (root/STAGE_BCS).write_bytes(new_bcs)
    (root/PIN_FILE).write_text(pre['candidate_bcs_sha256']+'\n',encoding='ascii')
    (root/STAGE_LUA).write_bytes(CANDIDATE.read_bytes())
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(weidu,root/EXE)
    if sha(old.safe_file(root,STAGE_BCS).read_bytes())!=pre['candidate_bcs_sha256']:
        raise Stop('BCS_STAGE_VERIFY_FAIL;BACKUP='+str(saved))
    if sha(old.safe_file(root,STAGE_LUA).read_bytes())!=PIN066S:
        raise Stop('LUA_STAGE_VERIFY_FAIL;BACKUP='+str(saved))
    process_guard()
    result=call_weidu(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    after=status066s(root)
    if after['bcs_sha256']!=pre['candidate_bcs_sha256']:
        raise Stop('AFTER_INSTALL_BCS_SHA_MISMATCH;BACKUP='+str(saved))
    return {'status':'INSTALLED_066S_EXPERIMENTAL','backup':str(saved),'after':after}

def rollback(root=ROOT,*,process_guard=guard,make_backup=backup,runner=subprocess.run):
    process_guard();source_check();root=root.resolve(strict=True)
    before=status066s(root)
    saved=make_backup(root,before,'PRE_ROLLBACK')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('EXTERNAL_BACKUP_NOT_VERIFIED')
    process_guard();status066s(root)
    process_guard()
    result=call_weidu(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    after=game064(root)
    return {'status':'ROLLED_BACK_TO_064_VERIFIED','backup':str(saved),'after':after}

def main(argv=None):
    p=argparse.ArgumentParser(description='BGXAI 066S guarded caster support, no automatic install')
    p.add_argument('mode',nargs='?',choices=('preflight','status','install','rollback'),default='status')
    p.add_argument('--yes',action='store_true')
    p.add_argument('--confirm',default='')
    p.add_argument('--game-root',type=Path,default=ROOT)
    a=p.parse_args(argv)
    try:
        if a.mode=='status':
            last=old.last_mod(a.game_root)
            state=status066s(a.game_root) if LAST066S.search(last) else game064(a.game_root)
            print(json.dumps({'mode':'READ_ONLY','proof':state},indent=2,ensure_ascii=False));return 0
        if a.mode=='preflight':
            proof,_=prepare(a.game_root)
            print(json.dumps(proof,indent=2,ensure_ascii=False));return 0
        phrase={'install':'INSTALL_BGXAI_066S','rollback':'ROLLBACK_BGXAI_066S'}[a.mode]
        if not a.yes or a.confirm!=phrase:raise Stop('EXPLICIT_APPROVAL_REQUIRED:'+phrase)
        if a.game_root!=ROOT:raise Stop('LIVE_INSTALL_FIXED_ROOT_ONLY')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,indent=2,ensure_ascii=False));return 0
    except (Stop,old.Stop,ValueError,AssertionError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print('BGXAI066S STOP:',str(e));return 2
if __name__=='__main__':sys.exit(main())
