#!/usr/bin/env python3
"""BGXAI 048: guarded WeiDU update of ONE passive EEex Lua observer.

No AI BCS, UI, TLK, EEex bootstrap, or hotkey module changes.
No automatic install/rollback: explicit YES and verified backup are mandatory.
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
VERSION = '0.3.19-048-CONFIRMED-HIT'
MOD = 'BGX48'
TP2 = 'BGX48/setup-BGX48.tp2'
SRC = 'BGX48/M_BX43.lua'
DEST = 'override/M_BX43.lua'
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
EXECUTABLE = 'setup-BGX48.exe'
BOOTS = ('override/M___EEex.lua', 'lang/ru_RU/dialog.tlk')
BASE = {
 'override/BDDEFAI.BCS': '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0',
 'override/M_BGX43Probe.lua': 'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f',
 'override/M_BGX44Diag.lua': 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f',
 'override/M_BX44.lua': 'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f',
}
OLD = 'c5b72a9bd22e120b38aa0d4f82fc9ce3532c31c8676e52cfdc855ee39521ddfd'
FILES = (SRC, TP2, 'BGXAI48_INSTALL.py', 'README_RU.md',
         'BGX48/tests/test_lua_048.py', 'BGX48/tests/test_installer_048.py')
RE = {n: re.compile(r'^~(?:(?:[^~]*[/\\])?BGX'+n+r'[/\\])?(?:SETUP-)?BGX'+n+r'\.TP2~(?=\s|$)',re.I)
      for n in ('42','43','44','45','46','47','48')}


def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def unsafe(p:Path)->bool:
    try:st=p.lstat()
    except FileNotFoundError:return False
    return p.is_symlink() or bool(getattr(st,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe(root:Path,rel:str)->Path:
    if not rel or rel.startswith('/') or '\\' in rel or ':' in rel or '..' in Path(rel).parts:
        raise RuntimeError('Unsafe relative path: '+rel)
    p=root/rel;at=p
    while True:
        if unsafe(at):raise RuntimeError('Symlink/reparse blocked: '+str(at))
        if at==root or at.parent==at:break
        at=at.parent
    return p


def existing(p:Path,size=1)->Path:
    if unsafe(p) or not p.is_file() or p.stat().st_size<size:
        raise RuntimeError('Missing/unsafe file: '+str(p))
    return p


def entries(root:Path)->list[str]:
    log=existing(safe(root,'WeiDU.log')).read_text(encoding='utf-8-sig',errors='replace')
    return [s.strip() for s in log.splitlines() if s.lstrip().startswith('~')]


def verify_sources(pkg:Path)->dict:
    m=json.loads(existing(safe(pkg,'SOURCE_MANIFEST.json')).read_text(encoding='utf-8'))
    if m.get('version')!=VERSION or m.get('status')!='OPT_IN_PASSIVE_HIT_OBSERVER' or m.get('required_baseline')!=BASE:
        raise RuntimeError('Unexpected source release/baseline')
    if set(m.get('files',{}))!=set(FILES):raise RuntimeError('Unexpected file allowlist')
    for rel,meta in m['files'].items():
        p=existing(safe(pkg,rel))
        if p.stat().st_size!=meta['size'] or digest(p)!=meta['sha256'] or p.stat().st_size>150000:
            raise RuntimeError('Source checksum failure: '+rel)
    source=(pkg/SRC).read_text(encoding='utf-8')
    uncommented='\n'.join(line.split('--',1)[0] for line in source.splitlines())
    for token in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'SetGlobal(',
                  'EEex_Action_Queue','io.open(', 'os.execute(', 'Infinity_DoFile('):
        if token in uncommented:raise RuntimeError('Mutating Lua token blocked: '+token)
    if len(Path(SRC).stem)>8 or digest(pkg/SRC)==OLD:
        raise RuntimeError('Observer resref or version not updated')
    for phrase in ('[134] = true','[105] = true','[3] = true','EEex_Action_AddSpriteStartedActionListener','m_acteeID2.m_Instance',
                   'EEex_Sprite_AddBlockWeaponHitListener', 'return false -- CRITICAL'):
        if phrase not in source:raise RuntimeError('Required action/listener missing: '+phrase)
    tp=(pkg/TP2).read_text(encoding='utf-8')
    if tp.count('COPY ')!=1 or 'COPY ~'+SRC+'~ ~'+DEST+'~' not in tp:
        raise RuntimeError('TP2 may change only '+DEST)
    return m


def baseline(root:Path)->None:
    for rel,expected in BASE.items():
        if digest(existing(safe(root,rel)))!=expected:
            raise RuntimeError('Existing 042B/043P/044/045/046/047 baseline drift: '+rel)


def require_root(root:Path,enforce=True)->Path:
    root=root.resolve()
    if enforce and str(root).casefold()!=str(GAME).casefold():
        raise RuntimeError('Wrong EET game folder: '+str(root))
    existing(safe(root,'chitin.key'),1000)
    existing(safe(root,'InfinityLoader.exe'),10000)
    exe=existing(safe(root,WEIDU),100000)
    with exe.open('rb') as f:
        if f.read(2)!=b'MZ':raise RuntimeError('WeiDU executable invalid')
    for name in BOOTS:existing(safe(root,name),10)
    return root


def preflight(root:Path,*,install:bool=True,enforce=True)->dict:
    root=require_root(root,enforce)
    baseline(root)
    log=entries(root)
    if not log or not RE['47' if install else '48'].search(log[-1]):
        raise RuntimeError('Expected BGX'+('47' if install else '48')+' LAST; observed '+repr(log[-1] if log else '(empty log)'))
    for n in ('42','43','44','45','46','47'):
        if not any(RE[n].search(line) for line in log):raise RuntimeError('BGX'+n+' missing in WeiDU.log')
    if install:
        if any(RE['48'].search(line) for line in log):raise RuntimeError('BGX48 already in WeiDU.log')
        if digest(existing(safe(root,DEST)))!=OLD:raise RuntimeError('047 observer SHA mismatch')
        for rel in (MOD,EXECUTABLE):
            if safe(root,rel).exists():raise RuntimeError('048 staging collision: '+rel)
    hashes={rel:digest(existing(safe(root,rel))) for rel in
            ('WeiDU.log','chitin.key', DEST,*BASE.keys(),*BOOTS)}
    return {'root':str(root),'hashes':hashes}


def guard_processes()->None:
    if os.name!='nt':return
    ps=('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
        'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
                    text=True,capture_output=True,timeout=25)
    if p.returncode:raise RuntimeError('Unable to check game processes')
    if p.stdout.strip():raise RuntimeError('Close game/InfinityLoader/WeiDU: '+p.stdout[:250])


def backup_root()->Path:
    return Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI47_SAFE_BACKUPS'


def backup(root:Path,pre:dict,kind='PRE_INSTALL',base=None)->Path:
    home=backup_root() if base is None else base
    if unsafe(home) or unsafe(home.parent):raise RuntimeError('Unsafe backup folder')
    home.mkdir(parents=True,exist_ok=True)
    path=home/(kind+'_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    path.mkdir(exist_ok=False)
    rels=('WeiDU.log','chitin.key',DEST,*BASE.keys(),*BOOTS)
    if safe(root,'lang/ru_RU/dialogf.tlk').is_file():rels+=('lang/ru_RU/dialogf.tlk',)
    saved={}
    for rel in set(rels):
        src=existing(safe(root,rel))
        out=path/rel;out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,out)
        if digest(src)!=digest(out):raise RuntimeError('Backup checksum failed: '+rel)
        saved[rel]=digest(src)
    (path/'before.json').write_text(json.dumps({'pre':pre,'hashes':saved},indent=2)+'\n',encoding='utf-8')
    return path


def verified_install_backup(root:Path,base=None)->Path:
    home=backup_root() if base is None else base
    if not home.is_dir() or unsafe(home):raise RuntimeError('No 048 install backups')
    for info in sorted(home.glob('PRE_INSTALL_*/before.json'),reverse=True):
        try:
            if unsafe(info) or unsafe(info.parent):continue
            d=json.loads(info.read_text(encoding='utf-8'))
            if d['pre']['root']!=str(root):continue
            if digest(existing(info.parent/DEST))!=OLD:continue
            if any(digest(existing(info.parent/x))!=v for x,v in d['hashes'].items()):continue
            report=json.loads(existing(info.parent/'report.json').read_text(encoding='utf-8'))
            if report['status']=='INSTALLED_PASSIVE_048' and report['backup']==str(info.parent):return info.parent
        except (OSError,RuntimeError,ValueError,KeyError,TypeError):pass
    raise RuntimeError('No verified original WeiDU backup for 048')


def weidu(root:Path,uninstall=False,runner=subprocess.run):
    cmd=[str(root/EXECUTABLE),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
         '--force-uninstall' if uninstall else '--force-install','0']
    return runner(cmd,cwd=str(root),capture_output=True,text=True,
                  encoding='utf-8',errors='replace',timeout=600,check=False)


def install(root:Path,pkg:Path,*,runner=subprocess.run,guard=guard_processes,base=None,enforce=True)->dict:
    root=root.resolve(); pkg=pkg.resolve()
    m=verify_sources(pkg);guard();pre=preflight(root,enforce=enforce)
    folder=backup(root,pre,base=base)
    result={'status':'NOT_STARTED','backup':str(folder),'checks':{}}
    staged=[];started=False
    try:
        (root/MOD).mkdir(exist_ok=False);staged.append(root/MOD)
        shutil.copy2(pkg/TP2,root/TP2)
        shutil.copy2(pkg/SRC,root/MOD/Path(SRC).name)
        if digest(root/MOD/Path(SRC).name)!=m['files'][SRC]['sha256']:
            raise RuntimeError('Staged observer checksum failed')
        with (root/WEIDU).open('rb') as f,(root/EXECUTABLE).open('xb') as g:shutil.copyfileobj(f,g)
        staged.append(root/EXECUTABLE)
        if digest(root/EXECUTABLE)!=digest(root/WEIDU):raise RuntimeError('WeiDU copy checksum failed')
        if not RE['47'].search(entries(root)[-1]) or any(digest(root/n)!=v for n,v in pre['hashes'].items()):
            raise RuntimeError('Game baseline changed after backup')
        started=True
        proc=weidu(root,runner=runner)
        checks={'weidu_ok':proc.returncode==0,
                '048_last':bool(entries(root) and RE['48'].search(entries(root)[-1])),
                'observer_sha':(root/DEST).is_file() and digest(root/DEST)==m['files'][SRC]['sha256'],
                'legacy_untouched':all(digest(root/n)==h for n,h in BASE.items()),
                'key_boot_tlk_unchanged':all(digest(root/n)==pre['hashes'][n] for n in ('chitin.key',*BOOTS))}
        result.update(status='INSTALLED_PASSIVE_048' if all(checks.values()) else 'REVIEW_WEIDU',
                      checks=checks,weidu_output=((proc.stdout or '')+'\n'+(proc.stderr or ''))[-2400:])
    except Exception as exc:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU',error=str(exc))
        if not started:
            for p in reversed(staged):
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
    finally:
        (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def uninstall(root:Path,pkg:Path,*,runner=subprocess.run,guard=guard_processes,base=None,enforce=True)->dict:
    root=root.resolve();pkg=pkg.resolve()
    m=verify_sources(pkg);guard();pre=preflight(root,install=False,enforce=enforce)
    if digest(existing(root/DEST))!=m['files'][SRC]['sha256']:
        raise RuntimeError('048 observer modified; no automatic rollback')
    orig=verified_install_backup(root,base=base)
    if digest(existing(root/'chitin.key'))!=digest(existing(orig/'chitin.key')):
        raise RuntimeError('chitin.key differs from original backup')
    existing(root/EXECUTABLE,100000)
    folder=backup(root,pre,kind='PRE_ROLLBACK',base=base)
    result={'status':'NOT_STARTED','backup':str(folder),'original_backup':str(orig),'checks':{}}
    try:
        p=weidu(root,uninstall=True,runner=runner)
        lines=entries(root)
        checks={'weidu_ok':p.returncode==0,
                '048_removed':not any(RE['48'].search(x) for x in lines),
                '047_last':bool(lines and RE['47'].search(lines[-1])),
                'old_observer_restored':digest(existing(root/DEST))==OLD,
                'legacy_untouched':all(digest(root/n)==h for n,h in BASE.items())}
        result.update(status='UNINSTALLED_PASSIVE_048' if all(checks.values()) else 'REVIEW_ROLLBACK',
                      checks=checks,weidu_output=((p.stdout or '')+'\n'+(p.stderr or ''))[-2400:])
    except Exception as exc:result.update(status='REVIEW_ROLLBACK',error=str(exc))
    finally:(folder/'rollback_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def status(root:Path,pkg:Path)->None:
    print('BGXAI 048 ATTACK FILTER - READ ONLY')
    try:
        m=verify_sources(pkg);root=require_root(root)
        lines=entries(root)
        for n in ('42','43','44','45','46','47','48'):
            print('BGX'+n+' installed:',any(RE[n].search(x) for x in lines))
        print('BGX48 last:',bool(lines and RE['48'].search(lines[-1])))
        print('Observer old 047:',digest(existing(root/DEST))==OLD)
        print('Observer new:',digest(existing(root/DEST))==m['files'][SRC]['sha256'])
        for n,v in BASE.items():print(n+' unchanged:',digest(existing(root/n))==v)
        if lines and RE['48'].search(lines[-1]):
            try:print('Verified install backup:',verified_install_backup(root))
            except RuntimeError as ex:print('BACKUP REVIEW:',ex)
        print('NOTE: Installed file alone does not prove live EEex event capture')
    except Exception as e:print('STATUS REVIEW:',e)
    print('NO GAME FILES CHANGED')


def main(argv=None)->int:
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group()
    for option in ('status','precheck','install','uninstall'):mode.add_argument('--'+option,action='store_true')
    parser.add_argument('--game-root',type=Path,default=GAME)
    args=parser.parse_args(argv);pkg=Path(__file__).resolve().parent
    if args.status or not (args.precheck or args.install or args.uninstall):
        status(args.game_root,pkg);return 0
    if args.precheck:
        try:
            verify_sources(pkg);preflight(args.game_root)
            print('048 PRECHECK PASS. No game writes.');return 0
        except Exception as e:print('048 PRECHECK BLOCKED:',e);return 1
    print('BGXAI 048: ONLY override/M_BX43.lua, via guarded WeiDU. BCS unchanged.')
    if input('Type exact YES to '+('ROLL BACK' if args.uninstall else 'INSTALL')+': ').strip()!='YES':
        print('CANCELLED, no changes');return 0
    try:
        result=(uninstall(args.game_root,pkg) if args.uninstall else install(args.game_root,pkg))
        print('BGXAI 048:',result['status'])
        for key,value in result.get('checks',{}).items():print(key,':',value)
        print('BACKUP:',result['backup'])
        if result.get('error'):print('ERROR:',result['error'])
        return 0 if result['status'] in ('INSTALLED_PASSIVE_048','UNINSTALLED_PASSIVE_048') else 1
    except Exception as e:
        print('BGXAI 048 BLOCKED:',e)
        print('Do not retry blindly or manually overwrite override/M_BX43.lua')
        return 1

if __name__=='__main__':sys.exit(main())
