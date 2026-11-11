#!/usr/bin/env python3
"""BGXAI 061 guarded WeiDU upgrade: bounded rescue walk and 20s Lua request TTL.

READ-ONLY by default. Standalone manual invocation is not the user workflow:
use existing BGXAI_UPDATE.cmd menus 65-69. No game write without dual approval.
Preserves every non-BGX60 BCS block, EPS spells and UI; backs up original
060 BCS/Lua, TLKs, WeiDU.log, and chitin.key before WeiDU install.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path
import BGXAI61_BUILDER as builder

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
OLD_BCS_SHA = builder.PIN_060_BCS
OLD_LUA_SHA = '35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'
BAF_SHA = '94b4beca0d9e470ed0cad566a19038566f626c19d53454d590fd409d294fcd1e'
BAF = Path(__file__).with_name('BGX61_RECEIVER.baf')
BCS_REL='override/BDDEFAI.BCS'
LUA_REL='override/M_BX43.lua'
WEIDU='setup-enhanced-powergaming-scripts.exe'
EXE='setup-BGX61.exe'
STAGE='BGX61'
TP2='BGX61/setup-BGX61.tp2'
STAGED_BCS='BGX61/staged/BDDEFAI.BCS'
STAGED_LUA='BGX61/staged/M_BX43.lua'
TP2_TEXT=('BACKUP ~BGX61/backup~\nAUTHOR ~BGXAI guarded rescue executor~\n'
          'BEGIN ~BGXAI 061 move-to-hit-ally with bounded TTL (BCS + Lua)~\n'
          'COPY ~BGX61/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n'
          'COPY ~BGX61/staged/M_BX43.lua~ ~override/M_BX43.lua~\n')
LAST_060=re.compile(r'^~(?:[^~]*[/\\])?BGX60[/\\]SETUP-BGX60\.TP2~(?=\s|$)',re.I)
LAST_061=re.compile(r'^~(?:[^~]*[/\\])?BGX61[/\\]SETUP-BGX61\.TP2~(?=\s|$)',re.I)
BACKUP=('WeiDU.log','chitin.key','weidu.conf','lang/ru_RU/dialog.tlk',
        'lang/ru_RU/dialogf.tlk',BCS_REL,LUA_REL)
OLD_TTL=b'local TTL_TICKS = 90 -- 6 seconds at standard IE game clock; must match BCS time clock.'
NEW_TTL=b'local TTL_TICKS = 300 -- 20 seconds at standard IE game clock; must match BCS time clock.'
OLD_MAX=b'local MAX_GAME_TIME = 2147483556 -- signed-int room for TTL'
NEW_MAX=b'local MAX_GAME_TIME = 2147483346 -- signed-int room for TTL'

class Stop(RuntimeError):pass

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def patch_lua(raw:bytes, source_pin:str|None=None)->bytes:
    pin=OLD_LUA_SHA if source_pin is None else source_pin
    if sha(raw)!=pin:raise Stop('LIVE_060_LUA_SHA_MISMATCH')
    if raw.count(OLD_TTL)!=1 or raw.count(OLD_MAX)!=1:raise Stop('LUA_TTL_PATCH_SOURCE_UNEXPECTED')
    out=raw.replace(OLD_TTL,NEW_TTL).replace(OLD_MAX,NEW_MAX)
    if out==raw or out.count(NEW_TTL)!=1 or out.count(NEW_MAX)!=1:
        raise Stop('LUA_TTL_PATCH_FAILED')
    return out

def reparse(p:Path):
    if p.is_symlink():return True
    try:return bool(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (FileNotFoundError,AttributeError):return False

def safe_file(root:Path,rel:str,min_size=1):
    if not rel or rel.startswith(('/', '\\')) or ':' in rel or '\\' in rel or '..' in Path(rel).parts:
        raise Stop('UNSAFE_PATH:'+rel)
    p=root/rel
    for q in (p,*p.parents):
        if reparse(q):raise Stop('REPARSE_BLOCKED:'+str(q))
        if q==root:break
    if not p.is_file() or p.stat().st_size<min_size:raise Stop('MISSING_OR_EMPTY:'+rel)
    return p

def last_mod(root:Path):
    entries=[x.strip() for x in safe_file(root,'WeiDU.log').read_text(encoding='utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('~')]
    if not entries:raise Stop('EMPTY_WEIDU_LOG')
    return entries[-1]

def source_check():
    if not BAF.is_file() or reparse(BAF) or sha(BAF.read_bytes())!=BAF_SHA:
        raise Stop('UNVERIFIED_061_BAF')
    content=BAF.read_text(encoding='ascii')
    if content.count('\nIF\n')!=20 or content.count('MoveToObject(')!=6 or content.count('InMyArea(')!=18:
        raise Stop('BAF_061_RULES_CHANGED')
    return {'baf_sha256':BAF_SHA}

def preflight(root:Path,expected='060',target_bcs_sha:str|None=None,target_lua_sha:str|None=None):
    root=root.absolute()
    if not root.is_dir() or reparse(root):raise Stop('INVALID_GAME_ROOT')
    safe_file(root,'chitin.key',1000);safe_file(root,'InfinityLoader.exe',10000)
    weidu=safe_file(root,WEIDU,100000)
    with weidu.open('rb') as f:
        if f.read(2)!=b'MZ':raise Stop('WEIDU_EXE_HEADER_INVALID')
    last=last_mod(root)
    if expected not in ('060','061'):raise Stop('UNKNOWN_EXPECTED_STAGE')
    if not (LAST_060 if expected=='060' else LAST_061).search(last):raise Stop('WEIDU_LAST_UNEXPECTED:'+last)
    bcs=sha(safe_file(root,BCS_REL).read_bytes())
    lua=sha(safe_file(root,LUA_REL).read_bytes())
    if bcs!=(OLD_BCS_SHA if expected=='060' else target_bcs_sha):raise Stop('BCS_MISMATCH_OR_MISSING_TARGET_PIN')
    if lua!=(OLD_LUA_SHA if expected=='060' else target_lua_sha):raise Stop('LUA_MISMATCH_OR_MISSING_TARGET_PIN')
    for rel in BACKUP:safe_file(root,rel)
    if expected=='060':
        for rel in (STAGE,EXE):
            if (root/rel).exists() or reparse(root/rel):raise Stop('STAGING_COLLISION:'+rel)
    return {'last':last,'bcs_sha256':bcs,'lua_sha256':lua}

def process_guard():
    if os.name!='nt':raise Stop('WINDOWS_REQUIRED_FOR_INSTALL')
    ps=('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
        'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
                     capture_output=True,text=True,timeout=25)
    if p.returncode or p.stdout.strip():raise Stop('GAME_OR_WEIDU_ACTIVE_OR_QUERY_FAILED:'+p.stdout[:250])

def backup_folder():return Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI61_SAFE_BACKUPS'

def make_backup(root:Path,pre:dict,label:str,parent:Path|None=None):
    base=parent or backup_folder()
    if reparse(base) or reparse(base.parent):raise Stop('UNSAFE_BACKUP_FOLDER')
    base.mkdir(parents=True,exist_ok=True)
    dst=base/(label+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dst.mkdir(exist_ok=False)
    hashes={}
    for rel in BACKUP:
        src=safe_file(root,rel);target=dst/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target);h=sha(src.read_bytes())
        if sha(target.read_bytes())!=h:raise Stop('BACKUP_HASH_FAILED:'+rel)
        hashes[rel]=h
    (dst/'BACKUP_PROOF.json').write_text(json.dumps({'pre':pre,'sha256':hashes},indent=2)+'\n',encoding='utf-8')
    return dst

def weidu_run(root:Path,uninstall=False,runner=subprocess.run):
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    p=runner(cmd,cwd=str(root),stdin=subprocess.DEVNULL,capture_output=True,
             encoding='utf-8',errors='replace',text=True,timeout=180,check=False)
    return {'rc':p.returncode,'stdout':p.stdout[-5000:],'stderr':p.stderr[-2000:]}

def proposal(root:Path):
    source_check()
    old=safe_file(root,BCS_REL).read_bytes();builder.verify_original(old)
    compiled=builder.compile_fragment(root,BAF)
    new,proof=builder.splice(old,compiled)
    updated_lua=patch_lua(safe_file(root,LUA_REL).read_bytes())
    proof['patched_lua_sha']=sha(updated_lua)
    return new,updated_lua,proof

def install(root:Path,*,guard=process_guard,backup=make_backup,runner=subprocess.run,build=proposal):
    guard();source_check();before=preflight(root,'060')
    new,new_lua,proof=build(root)
    if not proof.get('eps_unchanged') or sha(new)!=proof.get('patched_bcs_sha') or sha(new_lua)!=proof.get('patched_lua_sha'):
        raise Stop('PATCH_PROOF_INVALID')
    saved=backup(root,before,'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():raise Stop('BACKUP_NOT_VERIFIED')
    guard();preflight(root,'060')
    (root/STAGE/'staged').mkdir(parents=True,exist_ok=False)
    (root/STAGED_BCS).write_bytes(new)
    (root/STAGED_LUA).write_bytes(new_lua)
    (root/TP2).write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(root/WEIDU,root/EXE)
    if sha((root/STAGED_BCS).read_bytes())!=proof['patched_bcs_sha'] or sha((root/STAGED_LUA).read_bytes())!=proof['patched_lua_sha']:
        raise Stop('STAGING_SHA_FAILED; STOP_WITH_BACKUP='+str(saved))
    r=weidu_run(root,runner=runner)
    (saved/'weidu_install.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if r['rc']!=0:raise Stop('WEIDU_INSTALL_FAILED_DO_NOT_RETRY; BACKUP='+str(saved))
    after=preflight(root,'061',proof['patched_bcs_sha'],proof['patched_lua_sha'])
    return {'status':'INSTALLED_061_EXPERIMENTAL','backup':str(saved),
            'target_bcs_sha256':proof['patched_bcs_sha'],
            'target_lua_sha256':proof['patched_lua_sha'],'after':after}

def rollback(root:Path,*,guard=process_guard,backup=make_backup,runner=subprocess.run):
    guard();source_check()
    target_bcs=sha(safe_file(root,STAGED_BCS).read_bytes())
    target_lua=sha(safe_file(root,STAGED_LUA).read_bytes())
    before=preflight(root,'061',target_bcs,target_lua)
    if safe_file(root,TP2).read_text(encoding='utf-8')!=TP2_TEXT:raise Stop('TP2_DRIFT')
    safe_file(root,EXE,100000)
    saved=backup(root,before,'PRE_ROLLBACK')
    guard();preflight(root,'061',target_bcs,target_lua)
    result=weidu_run(root,uninstall=True,runner=runner)
    (saved/'weidu_rollback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if result['rc']!=0:raise Stop('ROLLBACK_FAILED_DO_NOT_RETRY;BACKUP='+str(saved))
    after=preflight_after_rollback(root)
    return {'status':'ROLLED_BACK_TO_060','backup':str(saved),'after':after}

def preflight_after_rollback(root:Path):
    if not LAST_060.search(last_mod(root)):raise Stop('ROLLBACK_LAST_NOT_060')
    if sha(safe_file(root,BCS_REL).read_bytes())!=OLD_BCS_SHA or sha(safe_file(root,LUA_REL).read_bytes())!=OLD_LUA_SHA:
        raise Stop('ROLLBACK_FILES_NOT_060')
    return {'last_060':True,'bcs_060_sha':OLD_BCS_SHA,'lua_060_sha':OLD_LUA_SHA}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',nargs='?',choices=('status','preflight','install','rollback'),default='status')
    ap.add_argument('--yes',action='store_true');ap.add_argument('--confirm',default='')
    a=ap.parse_args()
    try:
        if a.mode=='status':
            print('BGXAI061 READ-ONLY STATUS',json.dumps({'last':last_mod(ROOT),
                  '060_bcs_sha':sha(safe_file(ROOT,BCS_REL).read_bytes())==OLD_BCS_SHA,
                  '060_lua_sha':sha(safe_file(ROOT,LUA_REL).read_bytes())==OLD_LUA_SHA}))
            return 0
        if a.mode=='preflight':
            print('BGXAI061 READ-ONLY',json.dumps(preflight(ROOT,'060')))
            _,_,report=proposal(ROOT)
            print('COMPILED BAF + PATCHED LUA VERIFIED',json.dumps(report))
            return 0
        if not a.yes or a.confirm!='BGXAI_061_EXPERIMENTAL':
            raise Stop('EXPLICIT_--yes_AND_--confirm_BGXAI_061_EXPERIMENTAL_REQUIRED')
        result=install(ROOT) if a.mode=='install' else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,Stop,UnicodeError,subprocess.TimeoutExpired) as e:
        print('BGXAI061 STOP',e);return 2

if __name__=='__main__':sys.exit(main())
