#!/usr/bin/env python3
"""BGXAI 045: safe WeiDU additive fix for EEex 8-char M_*.lua resrefs.

Only two READ-ONLY Lua files are added to override. Existing 042B combat BCS,
043P/044 long-named Lua observers, UI, TLK and EEex boot are NOT modified.
Installation and rollback require explicit YES, exact hashes and WeiDU backup.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
MOD = 'BGX45'
TP2 = 'BGX45/setup-BGX45.tp2'
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
OWN_EXE = 'setup-BGX45.exe'
BCS = 'override/BDDEFAI.BCS'
BOOT = 'override/M___EEex.lua'
ORIG43 = 'override/M_BGX43Probe.lua'
ORIG44 = 'override/M_BGX44Diag.lua'
NEW_LUA = {'BGX45/M_BX43.lua':'override/M_BX43.lua',
           'BGX45/M_BX44.lua':'override/M_BX44.lua'}
BASE = {
    BCS: '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0',
    ORIG43: 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f',
    ORIG44: 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f',
}
# SHA256 pins of 044 source and live installed 043P/042B modules.
VERSION = '0.3.16b-045-RESREF-FIX'
SOURCE_FILES = ("BGXAI45_INSTALL.py",TP2,*NEW_LUA,"README_RU.md",
                "BGX45/tests/test_installer_045.py","BGX45/tests/test_lua_045.py")
# WeiDU logs are localized and several versions format language/component IDs
# differently. Authenticate the exact TP2 BASENAME, not the trailing numbers.
# For example, 044 was confirmed installed by WeiDU yet its old numeric-suffix
# regex rejected it. Keep strict mod identity, SHA baselines and last-entry order.
MOD_RE = {i: re.compile(
    r'^~(?:(?:[^~]*[/\\])?BGX'+i+r'[/\\])?(?:SETUP-)?BGX'+i+r'\.TP2~(?=\s|$)', re.I)
    for i in ('42','43','44','45')}



def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as fp:
        for b in iter(lambda:fp.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def reparse(p:Path)->bool:
    try: st=p.lstat()
    except FileNotFoundError: return False
    return p.is_symlink() or bool(getattr(st,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe(root:Path,rel:str)->Path:
    if not rel or rel.startswith('/') or '\\' in rel or ':' in rel or '..' in Path(rel).parts:
        raise RuntimeError('Unsafe relative path: '+rel)
    p=root/rel;cur=p
    while True:
        if reparse(cur): raise RuntimeError('Symlink/reparse prohibited: '+str(cur))
        if cur==root or cur.parent==cur:break
        cur=cur.parent
    return p


def existing(p:Path,min_size=1)->Path:
    if reparse(p) or not p.is_file() or p.stat().st_size<min_size:
        raise RuntimeError('Missing or unsafe file: '+str(p))
    return p


def installed(root:Path)->list[str]:
    return [v.strip() for v in existing(safe(root,'WeiDU.log')).read_text(encoding='utf-8-sig',errors='replace').splitlines()
            if v.lstrip().startswith('~')]


def verify_sources(pkg:Path)->dict:
    m=json.loads(existing(safe(pkg,'SOURCE_MANIFEST.json')).read_text(encoding='utf-8'))
    if m.get('version')!=VERSION or m.get('status')!='OPT_IN_ADDITIVE_LUA_RESREF_FIX':
        raise RuntimeError('Incorrect 045 package version/status')
    if m.get('required_baseline')!=BASE or set(m.get('files',{}))!=set(SOURCE_FILES):
        raise RuntimeError('Unexpected package allowlist/baseline')
    for rel,entry in m['files'].items():
        p=existing(safe(pkg,rel))
        if not 0<p.stat().st_size<120000 or p.stat().st_size!=entry['size'] or digest(p)!=entry['sha256']:
            raise RuntimeError('Invalid source/hash: '+rel)
    for src,dst in NEW_LUA.items():
        if len(Path(src).stem)>8 or len(Path(dst).stem)>8:
            raise RuntimeError('Lua resref exceeds eight characters: '+dst)
        code=(pkg/src).read_text(encoding='utf-8')
        lines='\n'.join(s.split('--',1)[0] for s in code.splitlines())
        for forbidden in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'EEex_Action_Queue',
                          'SetGlobal(', 'Infinity_DoFile(', 'io.open(', 'os.execute('):
            if forbidden in lines:raise RuntimeError('Unexpected mutating Lua token '+forbidden)
    if digest(pkg/'BGX45/M_BX43.lua')!=BASE[ORIG43] or digest(pkg/'BGX45/M_BX44.lua')!=BASE[ORIG44]:
        raise RuntimeError('Additive short-resref code must byte-match existing installed 043P/044')
    tp=(pkg/TP2).read_text(encoding='utf-8')
    if 'COPY ~BGX45/M_BX43.lua~ ~override/M_BX43.lua~' not in tp or 'COPY ~BGX45/M_BX44.lua~ ~override/M_BX44.lua~' not in tp:
        raise RuntimeError('Unexpected WeiDU file destinations')
    return m


def preflight(root:Path,*,must_last:str='44',enforce_root=True)->dict:
    root=root.resolve()
    if enforce_root and str(root).casefold()!=str(GAME).casefold():
        raise RuntimeError('Unexpected game root')
    existing(safe(root,'chitin.key'),1000)
    existing(safe(root,WEIDU_EXE),100000)
    with (root/WEIDU_EXE).open('rb') as f:
        if f.read(2)!=b'MZ':raise RuntimeError('WeiDU is not Windows executable')
    existing(safe(root,'InfinityLoader.exe'),10000)
    existing(safe(root,BOOT),10)
    for rel,expected in BASE.items():
        if digest(existing(safe(root,rel),100))!=expected:
            raise RuntimeError('Live baseline SHA mismatch: '+rel)
    entries=installed(root)
    if not entries or not MOD_RE[must_last].search(entries[-1]):
        # Show a printable, size-capped tail for diagnosing a different layout.
        # No game writes, no automatic fallback to another mod.
        tail = repr(entries[-1][:240]) if entries else '(empty WeiDU log)'
        raise RuntimeError('Expected BGX'+must_last+' as LAST WeiDU component; observed='+tail)
    for k in ('42','43','44'):
        if not any(MOD_RE[k].search(x) for x in entries):
            raise RuntimeError('BGX'+k+' prerequisite missing')
    if must_last=='44':
        if any(MOD_RE['45'].search(x) for x in entries):
            raise RuntimeError('045 already installed')
        for rel in (MOD,OWN_EXE,*NEW_LUA.values()):
            if safe(root,rel).exists():raise RuntimeError('045 file collision: '+rel)
    else:
        for rel in NEW_LUA.values():existing(safe(root,rel),100)
    watch=('chitin.key','WeiDU.log',BOOT,*BASE.keys(),'lang/ru_RU/dialog.tlk')
    return {'game':str(root),'hashes':{rel:digest(existing(safe(root,rel))) for rel in watch}}


def guard_processes()->None:
    if os.name!='nt':return
    cmd=('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
         'Where-Object {$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
         'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],
                     capture_output=True,text=True,timeout=25)
    if p.returncode:raise RuntimeError('Cannot check running processes')
    if p.stdout.strip():raise RuntimeError('Close game/InfinityLoader/WeiDU first: '+p.stdout[:200])


def backup_folder()->Path:
    return Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI45_SAFE_BACKUPS'


def backup(root:Path,pre:dict,*,base=None,kind='PRE_INSTALL')->Path:
    base=backup_folder() if base is None else base
    if reparse(base) or reparse(base.parent):raise RuntimeError('Unsafe backup folder')
    base.mkdir(parents=True,exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=base/(kind+'_'+stamp);dest.mkdir(exist_ok=False)
    rels=('chitin.key',BCS,ORIG43,ORIG44,BOOT,'WeiDU.log','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk')
    if kind=='PRE_ROLLBACK':rels+=tuple(NEW_LUA.values())
    saved={}
    for rel in rels:
        src=safe(root,rel)
        if rel=='lang/ru_RU/dialogf.tlk' and not src.is_file():continue
        existing(src)
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if digest(src)!=digest(target):raise RuntimeError('Backup verification failed: '+rel)
        saved[rel]=digest(src)
    (dest/'before.json').write_text(json.dumps({'pre':pre,'hashes':saved},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dest


def verified_original_backup(root:Path,*,base=None)->Path:
    base=backup_folder() if base is None else base
    if not base.is_dir() or reparse(base):raise RuntimeError('045 original backup unavailable')
    for meta in sorted(base.glob('PRE_INSTALL_*/before.json'),reverse=True):
        try:
            if reparse(meta) or reparse(meta.parent):continue
            data=json.loads(meta.read_text(encoding='utf-8'))
            if data['pre']['game']!=str(root):continue
            if any(digest(existing(meta.parent/rel))!=val for rel,val in data['hashes'].items()):continue
            report=json.loads(existing(meta.parent/'report.json').read_text(encoding='utf-8'))
            if report.get('status')=='INSTALLED_PASSIVE_045' and report.get('backup')==str(meta.parent):
                return meta.parent
        except (OSError,RuntimeError,ValueError,KeyError,TypeError):continue
    raise RuntimeError('No VERIFIED 045 install backup')


def run_weidu(root:Path,*,uninstall=False,runner=subprocess.run):
    command=[str(root/OWN_EXE),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
             '--force-uninstall' if uninstall else '--force-install','0']
    return runner(command,cwd=str(root),capture_output=True,text=True,encoding='utf-8',
                  errors='replace',timeout=600,check=False)


def install_045(root:Path,pkg:Path,*,runner=subprocess.run,guard=guard_processes,
                enforce_root=True,base=None)->dict:
    root=root.resolve();pkg=pkg.resolve()
    m=verify_sources(pkg);guard()
    pre=preflight(root,enforce_root=enforce_root)
    folder=backup(root,pre,base=base)
    result={'status':'NOT_STARTED','backup':str(folder),'checks':{}}
    staged=[];started=False
    try:
        mod=root/MOD;mod.mkdir(exist_ok=False);staged.append(mod)
        shutil.copy2(pkg/TP2,mod/'setup-BGX45.tp2')
        for src in NEW_LUA:
            target=mod/Path(src).name
            shutil.copy2(pkg/src,target)
            if digest(target)!=m['files'][src]['sha256']:raise RuntimeError('Staging Lua mismatch')
        with (root/WEIDU_EXE).open('rb') as src,(root/OWN_EXE).open('xb') as out:shutil.copyfileobj(src,out)
        staged.append(root/OWN_EXE)
        if digest(root/OWN_EXE)!=digest(root/WEIDU_EXE):raise RuntimeError('Weidu copy mismatch')
        if not MOD_RE['44'].search(installed(root)[-1]) or any(digest(root/x)!=pre['hashes'][x] for x in pre['hashes']):
            raise RuntimeError('Baseline changed after backup')
        started=True
        p=run_weidu(root,runner=runner)
        entries=installed(root)
        checks={'weidu_zero':p.returncode==0,'045_last':bool(entries and MOD_RE['45'].search(entries[-1])),
                'short_lua_installed':all((root/dest).is_file() and digest(root/dest)==m['files'][src]['sha256'] for src,dest in NEW_LUA.items()),
                '042b_unchanged':digest(root/BCS)==BASE[BCS],
                '043p_unchanged':digest(root/ORIG43)==BASE[ORIG43],
                '044_unchanged':digest(root/ORIG44)==BASE[ORIG44],
                'chitin_unchanged':digest(root/'chitin.key')==pre['hashes']['chitin.key'],
                'eeex_unchanged':digest(root/BOOT)==pre['hashes'][BOOT],
                'dialog_unchanged':digest(root/'lang/ru_RU/dialog.tlk')==pre['hashes']['lang/ru_RU/dialog.tlk']}
        result.update(checks=checks,status='INSTALLED_PASSIVE_045' if all(checks.values()) else 'REVIEW_WEIDU',
                      weidu_output=((p.stdout or '')+'\n'+(p.stderr or ''))[-3000:])
    except Exception as exc:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU',error=str(exc))
        if not started:
            for item in reversed(staged):
                if item.is_file():item.unlink()
                elif item.is_dir():shutil.rmtree(item)
    finally:(folder/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def rollback_045(root:Path,pkg:Path,*,runner=subprocess.run,guard=guard_processes,
                 enforce_root=True,base=None)->dict:
    root=root.resolve();pkg=pkg.resolve();m=verify_sources(pkg);guard()
    pre=preflight(root,must_last='45',enforce_root=enforce_root)
    for src,dest in NEW_LUA.items():
        if digest(root/dest)!=m['files'][src]['sha256']:
            raise RuntimeError('Installed 045 short Lua was changed: '+dest)
    original=verified_original_backup(root,base=base)
    if digest(root/'chitin.key')!=digest(original/'chitin.key'):
        raise RuntimeError('Chitin differs from 045 original backup')
    existing(root/OWN_EXE,100000)
    folder=backup(root,pre,base=base,kind='PRE_ROLLBACK')
    result={'status':'NOT_STARTED','backup':str(folder),'original_backup':str(original),'checks':{}}
    try:
        if not MOD_RE['45'].search(installed(root)[-1]):raise RuntimeError('045 no longer last')
        p=run_weidu(root,uninstall=True,runner=runner)
        entries=installed(root)
        checks={'weidu_zero':p.returncode==0,
                '045_removed':not any(MOD_RE['45'].search(x) for x in entries),
                '044_last':bool(entries and MOD_RE['44'].search(entries[-1])),
                'short_lua_removed':all(not (root/dest).exists() for dest in NEW_LUA.values()),
                'baselines_unchanged':all(digest(root/rel)==h for rel,h in BASE.items())}
        result.update(checks=checks,status='UNINSTALLED_PASSIVE_045' if all(checks.values()) else 'REVIEW_ROLLBACK',
                      weidu_output=((p.stdout or '')+'\n'+(p.stderr or ''))[-3000:])
    except Exception as exc:result.update(status='REVIEW_ROLLBACK',error=str(exc))
    finally:(folder/'rollback_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def status_045(root:Path,pkg:Path)->None:
    print('BGXAI 045 / EEex 8-CHAR LUA AUTOSTART FIX - READ-ONLY STATUS')
    try:
        m=verify_sources(pkg);root=root.resolve()
        if str(root).casefold()!=str(GAME).casefold():raise RuntimeError('Wrong EET root')
        entries=installed(root)
        print('BGX42 installed:',any(MOD_RE['42'].search(x) for x in entries))
        print('BGX43 installed:',any(MOD_RE['43'].search(x) for x in entries))
        print('BGX44 installed:',any(MOD_RE['44'].search(x) for x in entries))
        print('BGX45 installed:',any(MOD_RE['45'].search(x) for x in entries))
        print('BGX45 last:',bool(entries and MOD_RE['45'].search(entries[-1])))
        for src,dest in NEW_LUA.items():
            f=root/dest
            print(dest,'present=',f.is_file(),'sha256_matches=',f.is_file() and digest(f)==m['files'][src]['sha256'])
        for rel,expected in BASE.items():
            f=root/rel
            print(rel,'unchanged=',f.is_file() and digest(f)==expected)
        if any(MOD_RE['45'].search(x) for x in entries):
            try:print('Verified backup:',verified_original_backup(root))
            except RuntimeError as exc:print('Backup REVIEW:',exc)
        print('NOTE: disk success does not prove EEex callback in live game')
    except Exception as exc:print('STATUS BLOCKED:',exc)
    print('NO GAME FILES CHANGED')


def main(argv=None)->int:
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group()
    for opt in ('status','install','uninstall','precheck'):m.add_argument('--'+opt,action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args(argv);pkg=Path(__file__).resolve().parent
    if a.status or not(a.install or a.uninstall or a.precheck):status_045(a.game_root,pkg);return 0
    if a.precheck:
        try:
            verify_sources(pkg)
            preflight(a.game_root)
            print('BGXAI 045 PRECHECK: BASELINE OK. NOT INSTALLED.');print('NO GAME FILES CHANGED');return 0
        except Exception as e:
            print('BGXAI 045 PRECHECK REVIEW:',e);return 1
    print('BGXAI 045: ADD TWO READ-ONLY LUA MODULES ONLY. No BCS/AI change. Requires YES.')
    if input('Type exact YES to '+('INSTALL' if a.install else 'ROLL BACK')+': ').strip()!='YES':
        print('CANCELLED (no changes)');return 0
    try:
        r=(install_045(a.game_root,pkg) if a.install else rollback_045(a.game_root,pkg))
        print('BGXAI 045:',r['status'])
        for k,v in r.get('checks',{}).items():print(' ',k,':',v)
        print('Backup:',r['backup'])
        if r.get('error'):print('ERROR:',r['error'])
        return 0 if r['status'] in ('INSTALLED_PASSIVE_045','UNINSTALLED_PASSIVE_045') else 1
    except Exception as e:
        print('BGXAI 045 BLOCKED:',e)
        print('Do not retry blindly. Working 042B/043P/044 preserved unless review flagged.');return 1

if __name__=='__main__':sys.exit(main())
