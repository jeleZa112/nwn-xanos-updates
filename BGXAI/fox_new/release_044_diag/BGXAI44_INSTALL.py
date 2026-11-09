#!/usr/bin/env python3
"""BGXAI 044, optional, separate read-only EEex diagnostic. Protected WeiDU install.

Neither status/preflight nor check code modifies game. Install/uninstall require YES.
Only new game asset is override/M_BGX44Diag.lua; source + own WeiDU exe staged.
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
BASE_WEIDU = 'setup-enhanced-powergaming-scripts.exe'
OWN_EXE = 'setup-BGX44.exe'
OWN_TP2 = 'BGX44/setup-BGX44.tp2'
OWN_LUA = 'BGX44/M_BGX44Diag.lua'
OVERRIDE_LUA = 'override/M_BGX44Diag.lua'
LUA43 = 'override/M_BGX43Probe.lua'
LUA43_SHA = 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'
BCS = 'override/BDDEFAI.BCS'
BCS_SHA = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
EEEX = 'override/M___EEex.lua'
MOD43 = re.compile(r'^\s*~[^~]*BGX43[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
MOD44 = re.compile(r'^\s*~[^~]*BGX44[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
SOURCES = ('BGXAI44_INSTALL.py', 'BGXAI44_DIAG.cmd', OWN_LUA, OWN_TP2, 'README_RU.md')
BACKUP_LABEL = 'BGXAI44_SAFE_BACKUPS'


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def is_link(p: Path) -> bool:
    try:st=p.lstat()
    except FileNotFoundError:return False
    return p.is_symlink() or bool(getattr(st,'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe(root: Path, rel: str) -> Path:
    if not rel or rel.startswith('/') or ':' in rel or '\\' in rel or '..' in Path(rel).parts:
        raise RuntimeError('unsafe path: '+rel)
    node = root / rel
    p = node
    while True:
        if is_link(p):raise RuntimeError('symlink/reparse point blocked: '+str(p))
        if p == root or p.parent == p:break
        p=p.parent
    return node


def required(p: Path, size=1) -> Path:
    if is_link(p) or not p.is_file() or p.stat().st_size < size:
        raise RuntimeError('missing / unsafe file: '+str(p))
    return p


def verify_source(pkg: Path) -> dict:
    data=json.loads(required(safe(pkg,'SOURCE_MANIFEST.json')).read_text(encoding='utf-8'))
    if data.get('version')!='0.3.16-044-DIAG' or data.get('status')!='OPT_IN_READ_ONLY':
        raise RuntimeError('invalid release manifest')
    if set(data.get('files',{}))!=set(SOURCES):raise RuntimeError('manifest allowlist mismatch')
    for name,spec in data['files'].items():
        p=required(safe(pkg,name))
        if p.stat().st_size != spec['size'] or digest(p)!=spec['sha256'] or p.stat().st_size>100000:
            raise RuntimeError('source modified: '+name)
    code=(pkg/OWN_LUA).read_text(encoding='utf-8')
    active='\n'.join(ln.split('--',1)[0] for ln in code.splitlines())
    for token in ('ClearActions(', 'QueueResponse(', 'ActionOverride(', 'SetGlobal(',
                  'EEex_Action_Queue', 'io.open(', 'os.execute(', 'Infinity_DoFile('):
        if token in active:raise RuntimeError('unsafe Lua token: '+token)
    return data


def active(root: Path) -> list[str]:
    return [line.strip() for line in required(safe(root,'WeiDU.log')).read_text(encoding='utf-8-sig',errors='replace').splitlines() if line.lstrip().startswith('~')]


def processes():
    if os.name!='nt':return
    ps=('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
        'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    out=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],capture_output=True,text=True,timeout=25)
    if out.returncode:raise RuntimeError('cannot check running game / WeiDU: '+str(out.stderr)[:240])
    if out.stdout.strip():raise RuntimeError('close game, InfinityLoader and WeiDU: '+out.stdout[:250])


def root_probe(root:Path, *, mode:str, guard=processes, exact_path=True) -> dict:
    root=root.resolve()
    if exact_path and str(root).casefold()!=str(GAME).casefold():raise RuntimeError('wrong game directory')
    required(safe(root,'chitin.key'),1000)
    required(safe(root,BASE_WEIDU),100000)
    with (root/BASE_WEIDU).open('rb') as binary:
        if binary.read(2)!=b'MZ':raise RuntimeError('WeiDU is not a Windows PE executable')
    required(safe(root,'InfinityLoader.exe'),10000)
    required(safe(root,EEEX),10)
    if digest(required(safe(root,BCS),10000))!=BCS_SHA:raise RuntimeError('042B BCS hash changed; STOP')
    if digest(required(safe(root,LUA43)))!=LUA43_SHA:raise RuntimeError('043 observer hash changed; STOP')
    installed=active(root)
    if not any(MOD43.search(line) for line in installed):raise RuntimeError('043 WeiDU component absent')
    if mode=='install':
        if not MOD43.search(installed[-1]):raise RuntimeError('043 not last in WeiDU.log; STOP')
        if any(MOD44.search(line) for line in installed):raise RuntimeError('044 already installed')
        for rel in ('BGX44',OWN_EXE,OVERRIDE_LUA):
            if safe(root,rel).exists():raise RuntimeError('conflicting file: '+rel)
    if mode=='uninstall':
        if not MOD44.search(installed[-1]):raise RuntimeError('044 is not last; rollback forbidden')
        required(safe(root,OVERRIDE_LUA))
    if guard:guard()
    return dict(game=str(root),bcs=digest(root/BCS),lua43=digest(root/LUA43),
                chitin=digest(root/'chitin.key'),eeex=digest(root/EEEX),weidu=digest(root/'WeiDU.log'))


def backups_base(base=None)->Path:
    return (base if base is not None else Path(os.environ.get('USERPROFILE',str(Path.home()))) / 'Documents' / BACKUP_LABEL)


def backup(root:Path, pre:dict, *, label='PRE_INSTALL', base=None)->Path:
    base=backups_base(base)
    if is_link(base) or is_link(base.parent):raise RuntimeError('unsafe backup root')
    base.mkdir(parents=True, exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=base/(label+'_'+stamp)
    folder.mkdir(exist_ok=False)
    hashes={}
    for rel in ('chitin.key','WeiDU.log',BCS,LUA43,EEEX,'InfinityLoader.ini',
                'lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk'):
        p=safe(root,rel)
        if not p.exists():
            if rel in ('InfinityLoader.ini','lang/ru_RU/dialogf.tlk'):continue
            raise RuntimeError('backup requirement missing: '+rel)
        required(p)
        dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dst)
        if digest(dst)!=digest(p):raise RuntimeError('backup verification failed: '+rel)
        hashes[rel]=digest(p)
    if (root/OVERRIDE_LUA).is_file():
        src=required(safe(root,OVERRIDE_LUA))
        dst=folder/OVERRIDE_LUA;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if digest(dst)!=digest(src):raise RuntimeError('044 backup verification failed')
        hashes[OVERRIDE_LUA]=digest(src)
    (folder/'before.json').write_text(json.dumps({'pre':pre,'hashes':hashes},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return folder


def weidu(root:Path, *, uninstall=False, runner=subprocess.run):
    args=[str(root/OWN_EXE),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
          '--force-uninstall' if uninstall else '--force-install','0']
    return runner(args,cwd=str(root),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600,check=False)


def install(root:Path,pkg:Path,*,runner=subprocess.run,guard=processes,backup_dir=None,exact_path=True):
    root=root.resolve();pkg=pkg.resolve()
    manifest=verify_source(pkg)
    pre=root_probe(root,mode='install',guard=guard,exact_path=exact_path)
    bkp=backup(root,pre,base=backup_dir)
    result={'status':'NOT_STARTED','backup':str(bkp),'pre':pre}
    staged=[];started=False
    try:
        md=root/'BGX44';md.mkdir(exist_ok=False);staged.append(md)
        for source in (OWN_TP2,OWN_LUA):
            dst=md/Path(source).name
            shutil.copy2(pkg/source,dst)
            if digest(dst)!=manifest['files'][source]['sha256']:raise RuntimeError('stage hash mismatch: '+source)
        with required(root/BASE_WEIDU,100000).open('rb') as f, (root/OWN_EXE).open('xb') as o:
            shutil.copyfileobj(f,o)
        staged.append(root/OWN_EXE)
        if digest(root/OWN_EXE)!=digest(root/BASE_WEIDU):raise RuntimeError('staged WeiDU mismatch')
        if digest(root/BCS)!=BCS_SHA or digest(root/LUA43)!=LUA43_SHA or not MOD43.search(active(root)[-1]):
            raise RuntimeError('game changed after precheck')
        started=True
        out=weidu(root,runner=runner)
        now=active(root)
        checks={
          'weidu_success':out.returncode==0,
          '044_is_last':bool(now and MOD44.search(now[-1])),
          '044_lua_installed':(root/OVERRIDE_LUA).is_file() and digest(root/OVERRIDE_LUA)==manifest['files'][OWN_LUA]['sha256'],
          '042b_unchanged':digest(root/BCS)==BCS_SHA,
          '043_unchanged':digest(root/LUA43)==LUA43_SHA,
          'chitin_unchanged':digest(root/'chitin.key')==pre['chitin'],
          'eeex_unchanged':digest(root/EEEX)==pre['eeex'],
        }
        result.update(status='INSTALLED_READONLY_044' if all(checks.values()) else 'REVIEW_WEIDU',
                      checks=checks,output=((out.stdout or '')+'\n'+(out.stderr or ''))[-5000:])
    except Exception as ex:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU',error=str(ex))
        if not started:
            for p in reversed(staged):
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
    finally:
        (bkp/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def verified_install_backup(root:Path,*,base=None)->Path:
    base=backups_base(base)
    if not base.is_dir() or is_link(base):raise RuntimeError('044 backups missing')
    for info in sorted(base.glob('PRE_INSTALL_*/before.json'),reverse=True):
        try:
            d=json.loads(required(info).read_text(encoding='utf-8'))
            pre=d['pre'];hashes=d['hashes'];folder=info.parent
            if pre['game']!=str(root) or pre['bcs']!=BCS_SHA or pre['lua43']!=LUA43_SHA:continue
            if any(digest(required(folder/p))!=v for p,v in hashes.items()):continue
            report=json.loads(required(folder/'report.json').read_text(encoding='utf-8'))
            if report.get('status')=='INSTALLED_READONLY_044' and report.get('backup')==str(folder):return folder
        except (OSError,ValueError,RuntimeError,KeyError,TypeError):continue
    raise RuntimeError('no verified 044 install backup')


def uninstall(root:Path,pkg:Path,*,runner=subprocess.run,guard=processes,backup_dir=None,exact_path=True):
    root=root.resolve();pkg=pkg.resolve()
    manifest=verify_source(pkg)
    pre=root_probe(root,mode='uninstall',guard=guard,exact_path=exact_path)
    if digest(root/OVERRIDE_LUA)!=manifest['files'][OWN_LUA]['sha256']:
        raise RuntimeError('044 diagnostic Lua modified; cannot rollback')
    orig=verified_install_backup(root,base=backup_dir)
    if digest(root/'chitin.key')!=digest(orig/'chitin.key'):
        raise RuntimeError('chitin changed since original install')
    required(root/OWN_EXE,100000)
    bkp=backup(root,pre,label='PRE_ROLLBACK',base=backup_dir)
    result={'status':'NOT_STARTED','original_backup':str(orig),'backup':str(bkp)}
    try:
        if not MOD44.search(active(root)[-1]):raise RuntimeError('044 no longer last')
        out=weidu(root,uninstall=True,runner=runner)
        now=active(root)
        checks={
          'weidu_success':out.returncode==0,
          '044_absent':not any(MOD44.search(x) for x in now),
          '043_last':bool(now and MOD43.search(now[-1])),
          '044_lua_removed':not (root/OVERRIDE_LUA).exists(),
          '042b_unchanged':digest(root/BCS)==BCS_SHA,
          '043_unchanged':digest(root/LUA43)==LUA43_SHA,
          'chitin_unchanged':digest(root/'chitin.key')==pre['chitin'],
        }
        result.update(status='UNINSTALLED_044' if all(checks.values()) else 'REVIEW_UNINSTALL',checks=checks,
                      output=((out.stdout or '')+'\n'+(out.stderr or ''))[-5000:])
    except Exception as ex:result.update(status='REVIEW_UNINSTALL',error=str(ex))
    finally:(bkp/'uninstall_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def status(root:Path,pkg:Path,*,exact_path=True):
    print('BGXAI 044 READ ONLY PREFLIGHT / STATUS')
    try:
        manifest=verify_source(pkg);root=root.resolve()
        if exact_path and str(root).casefold()!=str(GAME).casefold():raise RuntimeError('wrong game')
        log=active(root)
        print('042B BCS pinned:',digest(required(root/BCS))==BCS_SHA)
        print('043P last:',bool(log and MOD43.search(log[-1])))
        print('043P installed:',any(MOD43.search(v) for v in log))
        print('043P Lua hash OK:',digest(required(root/LUA43))==LUA43_SHA)
        print('EEex present:',(root/EEEX).is_file())
        print('InfinityLoader present:',(root/'InfinityLoader.exe').is_file())
        print('044 installed:',any(MOD44.search(v) for v in log))
        print('044 last:',bool(log and MOD44.search(log[-1])))
        print('044 Lua verified:',(root/OVERRIDE_LUA).is_file() and digest(root/OVERRIDE_LUA)==manifest['files'][OWN_LUA]['sha256'])
        print('044 rollback backup:',end=' ')
        try:print(verified_install_backup(root))
        except RuntimeError:print('not applicable / no verified backup')
    except Exception as ex:print('STATUS BLOCKED:',ex)
    print('NO GAME FILES CHANGED')


def main(argv=None):
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group()
    group.add_argument('--install',action='store_true')
    group.add_argument('--uninstall',action='store_true')
    group.add_argument('--status',action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args(argv);pkg=Path(__file__).resolve().parent
    if not a.install and not a.uninstall:status(a.game_root,pkg);return 0
    print('044 diagnostic is READ ONLY but installation changes WeiDU files. Close game first.')
    if input('Confirm exact YES: ').strip()!='YES':print('CANCELLED, no changes');return 0
    try:
        report=install(a.game_root,pkg) if a.install else uninstall(a.game_root,pkg)
        print('BGXAI 044:',report['status'])
        for key,value in report.get('checks',{}).items():print(' ',key,':',value)
        print('Backup:',report.get('backup',''))
        if report.get('error'):print('ERROR:',report['error'])
        return 0 if report['status'] in ('INSTALLED_READONLY_044','UNINSTALLED_044') else 1
    except Exception as ex:
        print('BGXAI 044 BLOCKED:',ex)
        print('Do NOT retry blindly or copy Lua manually.');return 1

if __name__=='__main__':sys.exit(main())
