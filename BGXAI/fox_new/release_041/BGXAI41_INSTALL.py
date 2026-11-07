"""BGXAI 041 cautious WeiDU installer for existing EET/EPS/0381/039/040.

Default/status is READ ONLY. Installer only stages BGX41-owned files after explicit YES
and creates external preinstall backups. Never clones game, rewrites TLK directly,
or automatically restores WeiDU-managed data after an uncertain WeiDU result.
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

VERSION='0.3.11-041'
GAME=Path(r'C:\Games\BG_EET_FOXX_NEW')
WEIDU='setup-enhanced-powergaming-scripts.exe'
MOD_EXE='setup-BGX41.exe'
OWNED_SOURCE=(
    'setup-BGX41.tp2', 'BGX41/BGX41IC.BAM', 'BGX41/BGX41ON.SPL',
    'BGX41/BGX41OF.SPL', 'BGX41/toggle_icon.baf','BGX41/icon.tra',
)
OWNED_OVERRIDE=('BGX41IC.BAM','BGX41ON.SPL','BGX41OF.SPL')
BASE=('chitin.key','override/BDDEFAI.BCS','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk')
EXTRA='override/STATDESC.2DA'
LOG_RE=re.compile(r'^\s*~[^~]*BGX41[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)',re.I)
BASE_RE=re.compile(r'^\s*~[^~]*BGX40[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)',re.I)


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def link(p:Path)->bool:
    try:
        st=p.lstat()
    except FileNotFoundError:return False
    return p.is_symlink() or bool(getattr(st,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe_path(root:Path,rel:str)->Path:
    if not rel or rel.startswith('/') or '\\' in rel or ':' in rel or '..' in Path(rel).parts:
        raise RuntimeError('Unsafe relative path: '+rel)
    p=root/rel
    cur=p
    while cur!=root and cur!=cur.parent:
        if link(cur):raise RuntimeError('Refusing redirected game/source path: '+str(cur))
        cur=cur.parent
    if link(root):raise RuntimeError('Refusing redirected directory: '+str(root))
    return p


def require_file(p:Path,min_size=1):
    if link(p) or not p.is_file() or p.stat().st_size < min_size:
        raise RuntimeError('Missing / unsafe file: '+str(p))


def snapshot(root:Path)->dict:
    out={}
    for rel in BASE:
        p=safe_path(root,rel);require_file(p);out[rel]=sha(p)
    p=safe_path(root,EXTRA)
    if p.exists():require_file(p);out[EXTRA]=sha(p)
    else:out[EXTRA]=None
    return out


def read_log(root:Path)->list[str]:
    p=safe_path(root,'WeiDU.log');require_file(p)
    return p.read_text(encoding='utf-8-sig',errors='replace').splitlines()


def active_log(lines:list[str])->list[str]:
    return [x.strip() for x in lines if x.lstrip().startswith('~')]


def has_mod(lines:list[str],regex)->bool:
    return any(regex.search(x) for x in active_log(lines))


def is_last(lines:list[str],regex)->bool:
    x=active_log(lines)
    return bool(x and regex.search(x[-1]))


def tlk_count(p:Path)->int:
    require_file(p, 18)
    with p.open('rb') as f: h=f.read(18)
    if h[:8]!=b'TLK V1  ':raise RuntimeError('Unexpected TLK header: '+str(p))
    return int.from_bytes(h[10:14],'little')


def process_check(*,is_windows=None,runner=subprocess.run):
    if is_windows is None:is_windows=(os.name=='nt')
    if not is_windows:return []
    cmd=('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
         'Where-Object { $_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$" } | '
         'ForEach-Object { "{0} (PID {1})" -f $_.Name, $_.ProcessId }')
    try:
        p=runner(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],
                 capture_output=True,text=True,timeout=25,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:raise RuntimeError('Process check failed: '+str(e)) from e
    if p.returncode:raise RuntimeError('Process check failed: '+str((p.stderr or p.stdout or '')[:400]))
    x=[s.strip() for s in (p.stdout or '').splitlines() if s.strip()]
    if x:raise RuntimeError('Close game / loader / WeiDU first: '+', '.join(x[:10]))
    return x


def verify_package(pkg:Path)->dict:
    m=safe_path(pkg,'SOURCE_MANIFEST.json');require_file(m)
    obj=json.loads(m.read_text(encoding='utf-8'))
    if obj.get('status') not in ('SOURCE_ONLY_NOT_INSTALLED_NOT_RUNTIME_VERIFIED','OPT_IN_041_INSTALLER'):
        raise RuntimeError('Unexpected package status')
    if not obj.get('version','').startswith('0.3.11'):
        raise RuntimeError('Wrong version')
    files=obj.get('files',{})
    if not set(OWNED_SOURCE).issubset(files):raise RuntimeError('Package source manifest missing owned files')
    for rel,meta in files.items():
        p=safe_path(pkg,rel);require_file(p)
        if p.stat().st_size > 250_000 or p.stat().st_size != meta['size'] or sha(p)!=meta['sha256']:
            raise RuntimeError('Source checksum mismatch: '+rel)
    return obj


def preflight(root:Path,pkg:Path,*,strict_game=True,process_guard=process_check,require_last=True):
    if strict_game and str(root.resolve()).casefold()!=str(GAME.resolve()).casefold():
        raise RuntimeError('Target game path mismatch')
    if not root.is_dir() or not pkg.is_dir():raise RuntimeError('Missing root/package directory')
    verify_package(pkg)
    before=snapshot(root)
    game_weidu=safe_path(root,WEIDU);require_file(game_weidu,min_size=100000)
    with game_weidu.open('rb') as f:
        if f.read(2)!=b'MZ':raise RuntimeError('Wrong WeiDU executable')
    logs=read_log(root)
    if not any('ENHANCED-POWERGAMING-SCRIPTS' in x.upper() for x in logs):
        raise RuntimeError('EPS is not installed')
    if not has_mod(logs,BASE_RE):raise RuntimeError('BGX40 missing, guard icon must extend working 040')
    if has_mod(logs,LOG_RE):raise RuntimeError('BGX41 already installed; no second installation')
    if require_last and not is_last(logs,BASE_RE):raise RuntimeError('BGX40 not last WeiDU mod; cannot safely append 041')
    for rel in (*OWNED_SOURCE,MOD_EXE):
        if safe_path(root,rel).exists():raise RuntimeError('BGX41 source collision at game root: '+rel)
    for name in OWNED_OVERRIDE:
        if safe_path(root,'override/'+name).exists():raise RuntimeError('BGX41 resource name already in override: '+name)
    process_guard()
    return before,logs


def backup(root:Path,before:dict)->Path:
    base=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI41_SAFE_BACKUPS'
    if link(base) or link(base.parent):raise RuntimeError('Unsafe backup path')
    base.mkdir(parents=True,exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dst=base/('PRE_INSTALL_'+stamp);dst.mkdir(exist_ok=False)
    for rel in (*BASE,EXTRA,'WeiDU.log'):
        if rel==EXTRA and before[EXTRA] is None:continue
        p=safe_path(root,rel);dest=dst/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        if sha(p)!=sha(dest):raise RuntimeError('Backup verification failed: '+rel)
    (dst/'status.json').write_text(json.dumps({'version':VERSION,'game':str(root),'before':before},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return dst


def run_weidu(root:Path,*,uninstall=False,runner=subprocess.run):
    cmd=[str(root/MOD_EXE),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
         '--force-uninstall' if uninstall else '--force-install','0']
    return runner(cmd,cwd=str(root),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600,check=False)


def install(root:Path,pkg:Path,*,strict_game=True,process_guard=process_check,runner=subprocess.run)->dict:
    root=root.resolve();pkg=pkg.resolve()
    before,_=preflight(root,pkg,strict_game=strict_game,process_guard=process_guard)
    original_tlk=[tlk_count(root/x) for x in BASE[-2:]]
    bkp=backup(root,before)
    report={'version':VERSION,'backup':str(bkp),'mode':'INSTALL','status':'NOT_STARTED','before':before}
    staged=[];wei_du_started=False
    try:
        for rel in OWNED_SOURCE:
            p=safe_path(root,rel);p.parent.mkdir(parents=True,exist_ok=True)
            with (pkg/rel).open('rb') as inp,p.open('xb') as out:
                staged.append(rel);shutil.copyfileobj(inp,out)
            if sha(p)!=sha(pkg/rel):raise RuntimeError('Staged source mismatch: '+rel)
        p=safe_path(root,MOD_EXE)
        with (root/WEIDU).open('rb') as inp,p.open('xb') as out:
            staged.append(MOD_EXE);shutil.copyfileobj(inp,out)
        if sha(p)!=sha(root/WEIDU):raise RuntimeError('WeiDU copy mismatch')
        wei_du_started=True
        result=run_weidu(root,runner=runner)
        report['weidu_exit_code']=result.returncode
        report['weiDU_output_tail']=((result.stdout or '')+'\n'+(result.stderr or ''))[-7000:]
        after=snapshot(root);report['after']=after
        checks={
            'weidu_success':result.returncode==0,
            'in_weidu_log':has_mod(read_log(root),LOG_RE),
            'bcs_changed':after['override/BDDEFAI.BCS']!=before['override/BDDEFAI.BCS'],
            'chitin_unchanged':after['chitin.key']==before['chitin.key'],
            'statdesc_updated':after[EXTRA] is not None and after[EXTRA]!=before[EXTRA],
            'tlk_count_allowed':all(0<=tlk_count(root/x)-old<=5 for x,old in zip(BASE[-2:],original_tlk)),
            'owned_override_present':all(safe_path(root,'override/'+name).is_file() for name in OWNED_OVERRIDE),
        }
        report['checks']=checks
        report['status']='INSTALLED' if all(checks.values()) else 'REVIEW_INSTALL'
    except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as e:
        report['error']=str(e);report['status']='BLOCKED_OR_REVIEW'
        if not wei_du_started:
            for rel in reversed(staged):
                p=safe_path(root,rel)
                origin=(root/WEIDU if rel==MOD_EXE else pkg/rel)
                if p.is_file() and not link(p) and sha(p)==sha(origin):p.unlink()
            report['staged_cleaned_before_weidu']=True
    finally:
        (bkp/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def locate_backup(root:Path)->tuple[Path,dict]|None:
    base=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI41_SAFE_BACKUPS'
    if not base.is_dir() or link(base):return None
    for p in sorted(base.glob('PRE_INSTALL_*/status.json'),reverse=True):
        try:x=json.loads(p.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError):continue
        if x.get('game')==str(root) and x.get('version')==VERSION:return p.parent,x
    return None


def uninstall(root:Path,pkg:Path,*,strict_game=True,process_guard=process_check,runner=subprocess.run)->dict:
    root=root.resolve();pkg=pkg.resolve()
    if strict_game and str(root).casefold()!=str(GAME.resolve()).casefold():raise RuntimeError('Target path mismatch')
    verify_package(pkg);before=snapshot(root);lines=read_log(root)
    if not has_mod(lines,LOG_RE):raise RuntimeError('BGX41 not in WeiDU.log')
    if not is_last(lines,LOG_RE):raise RuntimeError('BGX41 not last; do not reorder installation')
    check=safe_path(root,MOD_EXE);require_file(check,100000)
    process_guard()
    b=locate_backup(root)
    if not b:raise RuntimeError('No BGX41 original backup; refusing uninstall')
    location,meta=b
    prior=meta['before']
    result=run_weidu(root,uninstall=True,runner=runner)
    after=snapshot(root)
    checks={
        'weidu_success':result.returncode==0,
        'not_in_weidu_log':not has_mod(read_log(root),LOG_RE),
        'bcs_restored':after['override/BDDEFAI.BCS']==prior['override/BDDEFAI.BCS'],
        'statdesc_restored':after[EXTRA]==prior[EXTRA],
        'chitin_unchanged':after['chitin.key']==before['chitin.key'],
        'tlk_not_decreased':all(tlk_count(root/x)>=tlk_count(location/x) for x in BASE[-2:]),
    }
    report={'version':VERSION,'mode':'UNINSTALL','backup':str(location),
      'checks':checks,'status':'UNINSTALLED_AND_RESTORED' if all(checks.values()) else 'REVIEW_UNINSTALL',
      'weiDU_output_tail':((result.stdout or '')+'\n'+(result.stderr or ''))[-7000:]}
    (location/'uninstall_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def status(root:Path,pkg:Path):
    print('BGXAI 041 / EET Foxx / READ-ONLY STATUS')
    try:
        verify_package(pkg)
        print('Source: SHA256 ALL VERIFIED')
        lines=read_log(root)
        print('BGX40 installed:',has_mod(lines,BASE_RE))
        print('BGX40 is last:',is_last(lines,BASE_RE))
        print('BGX41 installed:',has_mod(lines,LOG_RE))
        print('BGX41 is last:',is_last(lines,LOG_RE))
        print('STATDESC in override:',safe_path(root,EXTRA).exists())
        print('BGX41 original backup:', 'YES' if locate_backup(root) else 'NO')
        print('Game resources changed: NO (read only)')
    except (OSError,ValueError,RuntimeError) as e:print('STATUS BLOCKED:',e)


def main(argv=None):
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group()
    group.add_argument('--status',action='store_true')
    group.add_argument('--install',action='store_true')
    group.add_argument('--uninstall',action='store_true')
    a=p.parse_args(argv)
    root=GAME;pkg=Path(__file__).resolve().parent
    if not a.install and not a.uninstall:
        status(root,pkg);return 0
    print('BGXAI 041 EXPERIMENTAL. Existing 040 F guard must work and be last mod.')
    print('Game and InfinityLoader must be closed. Original backup outside game.')
    if input('Type uppercase YES to modify WeiDU: ').strip()!='YES':
        print('CANCELLED: no changes');return 0
    try:
        report=install(root,pkg) if a.install else uninstall(root,pkg)
        print('BGXAI 041:',report['status'])
        print('Backup:',report.get('backup',''))
        for name,passed in report.get('checks',{}).items():print(' ',name,':','OK' if passed else 'REVIEW')
        if report.get('weiDU_output_tail'):print('WeiDU:',report['weiDU_output_tail'][-1800:])
        return 0 if report['status'] in ('INSTALLED','UNINSTALLED_AND_RESTORED') else 1
    except (OSError,ValueError,RuntimeError,KeyError,subprocess.TimeoutExpired) as e:
        print('BGXAI 041 BLOCKED:',e)
        print('Leave game resources untouched. Do not repeat automatically.')
        return 1

if __name__=='__main__':sys.exit(main())
