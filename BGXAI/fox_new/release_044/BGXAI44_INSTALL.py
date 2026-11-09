#!/usr/bin/env python3
"""BGXAI 044: isolated, opt-in, read-only EEex hotkey diagnostic installer.

Only override/M_BGX44Diag.lua is added via WeiDU. Guards 042B and 043P
hashes, install order, source manifest, process state, and verified rollback.
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
MOD = 'BGX44'
MOD_TP2 = 'BGX44/setup-BGX44.tp2'
MOD_LUA = 'BGX44/M_BGX44Diag.lua'
DEPLOYED = 'override/M_BGX44Diag.lua'
OBSERVER = 'override/M_BGX43Probe.lua'
BCS = 'override/BDDEFAI.BCS'
BOOT = 'override/M___EEex.lua'
EXE_SRC = 'setup-enhanced-powergaming-scripts.exe'
EXE_DST = 'setup-BGX44.exe'
BASE_BCS = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
BASE_OBSERVER = 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
VERSION = '0.3.15-044-DIAG'
FILES = ('BGXAI44_INSTALL.py', MOD_TP2, MOD_LUA, 'README_RU.md',
         'BGX44/tests/test_installer_044.py', 'BGX44/tests/test_lua_044.py')
MOD42 = re.compile(r'BGX42[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
MOD43 = re.compile(r'BGX43[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
MOD44 = re.compile(r'BGX44[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def redirected(p: Path) -> bool:
    try: st = p.lstat()
    except FileNotFoundError: return False
    return p.is_symlink() or bool(getattr(st, 'st_file_attributes', 0) &
                                 getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def safe(root: Path, rel: str) -> Path:
    parts = Path(rel).parts
    if not rel or rel.startswith('/') or '\\' in rel or ':' in rel or '..' in parts:
        raise RuntimeError('Unsafe relative path: '+rel)
    p = root / rel
    cur = p
    while True:
        if redirected(cur): raise RuntimeError('Reparse path blocked: '+str(cur))
        if cur == root or cur.parent == cur: break
        cur = cur.parent
    return p


def exists(p: Path, min_bytes=1) -> Path:
    if redirected(p) or not p.is_file() or p.stat().st_size < min_bytes:
        raise RuntimeError('Missing/unsafe file: '+str(p))
    return p


def log_lines(root: Path) -> list[str]:
    return [x.strip() for x in exists(safe(root,'WeiDU.log')).read_text(
        encoding='utf-8-sig',errors='replace').splitlines() if x.lstrip().startswith('~')]


def source_manifest(pkg: Path) -> dict:
    m = json.loads(exists(safe(pkg,'SOURCE_MANIFEST.json')).read_text(encoding='utf-8'))
    if m.get('version') != VERSION or m.get('status') != 'OPT_IN_READ_ONLY_DIAGNOSTIC':
        raise RuntimeError('Wrong BGX44 package version/status')
    if m.get('bcs_sha256') != BASE_BCS or m.get('observer_sha256') != BASE_OBSERVER:
        raise RuntimeError('Wrong pinned live baseline')
    records = m.get('files')
    if not isinstance(records,dict) or set(records) != set(FILES):
        raise RuntimeError('Unexpected source allowlist')
    for rel, record in records.items():
        f = exists(safe(pkg,rel))
        if not 0 < f.stat().st_size < 100000 or f.stat().st_size != record['size'] or digest(f) != record['sha256']:
            raise RuntimeError('Source mismatch: '+rel)
    lua = (pkg/MOD_LUA).read_text(encoding='utf-8')
    actual = '\n'.join(s.split('--',1)[0] for s in lua.splitlines())
    for token in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'Infinity_DoFile(',
                  'io.open(', 'os.execute(', 'SetGlobal(', 'EEex_Action_Queue'):
        if token in actual: raise RuntimeError('Mutating Lua token forbidden: '+token)
    return m


def check(root: Path, *, state: str, enforce_root=True) -> dict:
    root = root.resolve()
    if enforce_root and str(root).casefold() != str(GAME).casefold():
        raise RuntimeError('Wrong game directory')
    exists(safe(root,'chitin.key'),1000)
    exists(safe(root,EXE_SRC),100000)
    with (root/EXE_SRC).open('rb') as executable:
        if executable.read(2) != b'MZ':
            raise RuntimeError('WeiDU executable is not Windows PE')
    exists(safe(root,'InfinityLoader.exe'),10000)
    exists(safe(root,BOOT),10)
    if digest(exists(safe(root,BCS),10000)) != BASE_BCS:
        raise RuntimeError('Live 042B BCS SHA256 mismatch')
    if digest(exists(safe(root,OBSERVER),100)) != BASE_OBSERVER:
        raise RuntimeError('Live 043P observer SHA256 mismatch')
    lines = log_lines(root)
    if not any(MOD42.search(x) for x in lines) or not any(MOD43.search(x) for x in lines):
        raise RuntimeError('042B/043P WeiDU prerequisite missing')
    if state == 'before':
        if not lines or not MOD43.search(lines[-1]) or any(MOD44.search(x) for x in lines):
            raise RuntimeError('043P must be last, 044 not installed')
        for rel in (MOD,EXE_DST,DEPLOYED):
            if safe(root,rel).exists(): raise RuntimeError('BGX44 name collision: '+rel)
    elif state == 'installed':
        if not lines or not MOD44.search(lines[-1]):
            raise RuntimeError('BGX44 is not last in WeiDU.log')
        exists(safe(root,DEPLOYED))
    else: raise ValueError('Bad state')
    watched = ('chitin.key', BCS, OBSERVER, BOOT)
    return {'game':str(root),'sha':{rel:digest(root/rel) for rel in watched},
            'weidu_sha':digest(root/'WeiDU.log')}


def processes_closed():
    if os.name != 'nt': return
    ps = ('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
          'Where-Object {$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
          'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
                       capture_output=True,text=True,timeout=25)
    if p.returncode != 0: raise RuntimeError('Unable to verify closed game processes')
    if p.stdout.strip(): raise RuntimeError('Close game / InfinityLoader / WeiDU first: '+p.stdout[:220])


def backup_base() -> Path:
    return Path(os.environ.get('USERPROFILE',str(Path.home()))) / 'Documents' / 'BGXAI44_SAFE_BACKUPS'


def backup(root: Path, baseline: dict, *, stage='PRE_INSTALL',base=None) -> Path:
    base = backup_base() if base is None else base
    if redirected(base) or redirected(base.parent): raise RuntimeError('Backup root redirects')
    base.mkdir(parents=True,exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = base/(stage+'_'+stamp)
    folder.mkdir(exist_ok=False)
    saved={}
    for rel in ('chitin.key', BCS, OBSERVER, BOOT,'WeiDU.log',
                'lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk'):
        p=safe(root,rel)
        if rel.endswith('dialogf.tlk') and not p.is_file(): continue
        exists(p)
        target=folder/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        if digest(p)!=digest(target):raise RuntimeError('Backup hash failure '+rel)
        saved[rel]=digest(p)
    if stage=='PRE_ROLLBACK':
        p=exists(safe(root,DEPLOYED))
        target=folder/DEPLOYED;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        if digest(p)!=digest(target):raise RuntimeError('Backup Lua mismatch')
        saved[DEPLOYED]=digest(p)
    (folder/'before.json').write_text(json.dumps({'baseline':baseline,'files':saved},indent=2)+'\n',encoding='utf-8')
    return folder


def get_install_backup(root: Path, *,base=None) -> Path:
    base=backup_base() if base is None else base
    if not base.is_dir() or redirected(base) or redirected(base.parent):
        raise RuntimeError('Verified BGX44 backup missing')
    for meta in sorted(base.glob('PRE_INSTALL_*/before.json'),reverse=True):
        try:
            if redirected(meta) or redirected(meta.parent):continue
            obj=json.loads(meta.read_text(encoding='utf-8'))
            if obj['baseline']['game']!=str(root):continue
            if obj['baseline']['sha'][BCS]!=BASE_BCS:continue
            if obj['baseline']['sha'][OBSERVER]!=BASE_OBSERVER:continue
            if any(digest(exists(meta.parent/rel))!=val for rel,val in obj['files'].items()):continue
            report=json.loads(exists(meta.parent/'report.json').read_text(encoding='utf-8'))
            if report.get('status')=='INSTALLED_PASSIVE_044' and report.get('backup')==str(meta.parent):
                return meta.parent
        except (OSError,ValueError,TypeError,KeyError,RuntimeError): continue
    raise RuntimeError('No verified successful BGX44 installation backup')


def weidu(root: Path, *, uninstall=False, runner=subprocess.run):
    args=[str(root/EXE_DST),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
          '--force-uninstall' if uninstall else '--force-install','0']
    return runner(args,cwd=str(root),capture_output=True,text=True,
                  encoding='utf-8',errors='replace',timeout=600,check=False)


def install(root: Path,pkg: Path,*,runner=subprocess.run,guard=processes_closed,
            enforce_root=True,backup_dir=None):
    root=root.resolve();pkg=pkg.resolve()
    m=source_manifest(pkg)
    guard()
    pre=check(root,state='before',enforce_root=enforce_root)
    folder=backup(root,pre,base=backup_dir)
    result={'status':'NOT_STARTED','backup':str(folder),'checks':{}}
    staged=[];started=False
    try:
        dst=root/MOD;dst.mkdir(exist_ok=False);staged.append(dst)
        shutil.copy2(pkg/MOD_TP2,dst/'setup-BGX44.tp2')
        shutil.copy2(pkg/MOD_LUA,dst/'M_BGX44Diag.lua')
        if digest(dst/'M_BGX44Diag.lua')!=m['files'][MOD_LUA]['sha256']:
            raise RuntimeError('Staged Lua mismatch')
        ex=root/EXE_DST
        with (root/EXE_SRC).open('rb') as src,ex.open('xb') as out:
            shutil.copyfileobj(src,out)
        staged.append(ex)
        if digest(ex)!=digest(root/EXE_SRC):raise RuntimeError('Staged WeiDU mismatch')
        if (not MOD43.search(log_lines(root)[-1]) or
            any(digest(root/rel)!=expected for rel,expected in pre['sha'].items())):
            raise RuntimeError('Game changed after preflight')
        started=True
        p=weidu(root,runner=runner)
        after=log_lines(root)
        checks={'weidu_zero':p.returncode==0,
                '044_last':bool(after and MOD44.search(after[-1])),
                'diagnostic_installed':(root/DEPLOYED).is_file() and digest(root/DEPLOYED)==m['files'][MOD_LUA]['sha256'],
                '043_observer_unchanged':digest(root/OBSERVER)==pre['sha'][OBSERVER],
                '042b_unchanged':digest(root/BCS)==pre['sha'][BCS],
                'chitin_unchanged':digest(root/'chitin.key')==pre['sha']['chitin.key'],
                'eeex_unchanged':digest(root/BOOT)==pre['sha'][BOOT]}
        result.update(checks=checks,status='INSTALLED_PASSIVE_044' if all(checks.values()) else 'REVIEW_WEIDU',
                      weidu_output=((p.stdout or '')+'\n'+(p.stderr or ''))[-2500:])
    except Exception as exc:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU',error=str(exc))
        if not started:
            for f in reversed(staged):
                if f.is_file():f.unlink()
                elif f.is_dir():shutil.rmtree(f)
    finally:
        (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def uninstall(root: Path,pkg: Path,*,runner=subprocess.run,guard=processes_closed,
              enforce_root=True,backup_dir=None):
    root=root.resolve();pkg=pkg.resolve()
    m=source_manifest(pkg)
    guard()
    pre=check(root,state='installed',enforce_root=enforce_root)
    if digest(root/DEPLOYED)!=m['files'][MOD_LUA]['sha256']:
        raise RuntimeError('Installed BGX44 Lua has been modified')
    original=get_install_backup(root,base=backup_dir)
    if digest(root/'chitin.key')!=digest(original/'chitin.key'):
        raise RuntimeError('Game chitin changed after install')
    exists(safe(root,EXE_DST),100000)
    folder=backup(root,pre,stage='PRE_ROLLBACK',base=backup_dir)
    result={'status':'NOT_STARTED','backup':str(folder),'checks':{}}
    try:
        if not MOD44.search(log_lines(root)[-1]):raise RuntimeError('044 no longer last')
        p=weidu(root,uninstall=True,runner=runner)
        after=log_lines(root)
        checks={'weidu_zero':p.returncode==0,
                '044_absent':not any(MOD44.search(x) for x in after),
                '043_last':bool(after and MOD43.search(after[-1])),
                'diagnostic_removed':not (root/DEPLOYED).exists(),
                '042b_unchanged':digest(root/BCS)==pre['sha'][BCS],
                '043_observer_unchanged':digest(root/OBSERVER)==pre['sha'][OBSERVER],
                'chitin_unchanged':digest(root/'chitin.key')==pre['sha']['chitin.key']}
        result.update(checks=checks,status='UNINSTALLED_PASSIVE_044' if all(checks.values()) else 'REVIEW_UNINSTALL',
                      weidu_output=((p.stdout or '')+'\n'+(p.stderr or ''))[-2500:])
    except Exception as exc:result.update(status='REVIEW_UNINSTALL',error=str(exc))
    finally:(folder/'uninstall_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def status(root: Path,pkg: Path,*,enforce_root=True,backup_dir=None):
    print('BGXAI 044 / READ-ONLY STATUS (no game files changed)')
    try:
        m=source_manifest(pkg);root=root.resolve()
        if enforce_root and str(root).casefold()!=str(GAME).casefold():
            raise RuntimeError('Wrong game directory')
        lines=log_lines(root)
        present=any(MOD44.search(x) for x in lines)
        print('BGX42 installed:',any(MOD42.search(x) for x in lines))
        print('BGX43 installed:',any(MOD43.search(x) for x in lines))
        print('BGX44 installed:',present)
        print('BGX44 is last:',bool(lines and MOD44.search(lines[-1])))
        print('BCS 042B unchanged:',digest(exists(root/BCS))==BASE_BCS)
        print('043P Lua SHA256 matches:',digest(exists(root/OBSERVER))==BASE_OBSERVER)
        deployed=root/DEPLOYED
        print('044 Lua file present:',deployed.is_file())
        print('044 Lua hash matches:',deployed.is_file() and digest(deployed)==m['files'][MOD_LUA]['sha256'])
        if present:
            try:print('Verified rollback backup:',get_install_backup(root,base=backup_dir))
            except RuntimeError as exc:print('Rollback REVIEW:',exc)
    except Exception as exc:print('STATUS BLOCKED:',exc)
    print('NOTE: live hotkey/runtime callback remains unverified until in-game test')
    print('NO GAME FILES CHANGED')


def precheck(root: Path,pkg: Path) -> bool:
    print('BGXAI 044 / READ-ONLY LIVE PREFLIGHT')
    source_manifest(pkg)
    root=root.resolve()
    try:
        info=check(root,state='before')
        print('BASELINE OK: BGX42 installed + BGX43 last, pinned 042B/043P hashes verified')
        print('BCS SHA256:',info['sha'][BCS]);print('043P Lua SHA256:',info['sha'][OBSERVER])
        print('044 DIAG NOT INSTALLED')
    except Exception as exc:
        print('PREFLIGHT REVIEW:',exc)
        print('NO GAME FILES CHANGED')
        return False
    print('NO GAME FILES CHANGED')
    return True


def main(argv=None):
    p=argparse.ArgumentParser()
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--precheck',action='store_true')
    modes.add_argument('--status',action='store_true')
    modes.add_argument('--install',action='store_true')
    modes.add_argument('--uninstall',action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args(argv)
    pkg=Path(__file__).resolve().parent
    if a.precheck:
        try:return 0 if precheck(a.game_root,pkg) else 1
        except Exception as exc:
            print('PREFLIGHT BLOCKED:',exc)
            print('NO GAME FILES CHANGED')
            return 1
    if not a.install and not a.uninstall:status(a.game_root,pkg);return 0
    print('BGXAI 044 diagnostic; only extra Lua observer-hotkey; NO AI commands/BCS changes.')
    if input('Type exact YES to '+('INSTALL' if a.install else 'ROLLBACK')+': ').strip()!='YES':
        print('CANCELLED; no game changes');return 0
    try:
        r=install(a.game_root,pkg) if a.install else uninstall(a.game_root,pkg)
        print('BGXAI 044:',r['status'])
        for k,v in r.get('checks',{}).items():print(' ',k,':',v)
        print('Backup:',r.get('backup',''))
        if r.get('error'):print('ERROR:',r['error'])
        if r['status'] in ('INSTALLED_PASSIVE_044','UNINSTALLED_PASSIVE_044'):return 0
        return 1
    except Exception as exc:
        print('BGXAI 044 BLOCKED:',exc)
        print('Do not repeat blindly or copy Lua manually.');return 1

if __name__=='__main__':sys.exit(main())
