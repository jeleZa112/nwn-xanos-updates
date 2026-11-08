"""BGXAI 042B conservative experimental WeiDU wrapper, user opt-in only.

Only for exact live EPS 18.4 BCS SHA. Stage in game only after external backup;
no manipulation of savegames, SCS, spell assets, TLK or 041. Never manually
restore after attempted WeiDU installation (state may be uncertain).
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
from build_042b_preview import build
from guard_source_042a import PIN_SHA

GAME=Path(r'C:\Games\BG_EET_FOXX_NEW')
EXE='setup-enhanced-powergaming-scripts.exe'
OWN_EXE='setup-BGX42.exe'
TP2='BGX42/setup-BGX42.tp2'
OWN_DIR='BGX42'
WEIDU_LOG='WeiDU.log'
BCS='override/BDDEFAI.BCS'
OUTPUT_HASH='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
MOD41_RE=re.compile(r'^\s*~[^~]*BGX41[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)',re.I)
MOD42_RE=re.compile(r'^\s*~[^~]*BGX42[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)',re.I)
SOURCE_FILES=('BGXAI42_INSTALL.py','build_042b_preview.py','guard_source_042a.py','setup-BGX42.tp2','SOURCE_MANIFEST.json')


def sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def redirected(p:Path)->bool:
    try: attrs=p.lstat().st_file_attributes
    except AttributeError: attrs=0
    except FileNotFoundError:return False
    return p.is_symlink() or bool(attrs & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400))


def safe(root:Path,rel:str)->Path:
    if not rel or rel.startswith('/') or ':' in rel or '\\' in rel or '..' in Path(rel).parts:
        raise RuntimeError('unsafe relative path: '+rel)
    p=root/rel
    q=p
    while q!=q.parent:
        if redirected(q):raise RuntimeError('symlink/reparse path blocked: '+str(q))
        if q==root:break
        q=q.parent
    return p


def existing(p:Path,min_bytes=1):
    if redirected(p) or not p.is_file() or p.stat().st_size<min_bytes:
        raise RuntimeError('missing/unsafe file: '+str(p))
    return p


def entries(root:Path):
    lines=existing(safe(root,WEIDU_LOG)).read_text(encoding='utf-8-sig',errors='replace').splitlines()
    return [line.strip() for line in lines if line.lstrip().startswith('~')]


def preflight(root:Path,*,uninstall=False,require_exact_path=True,check_process=None):
    root=root.resolve()
    if require_exact_path and str(root).casefold()!=str(GAME).casefold():
        raise RuntimeError('wrong EET game path')
    existing(safe(root,'chitin.key'),1000)
    existing(safe(root,EXE),100000)
    if existing(safe(root,EXE)).read_bytes()[:2]!=b'MZ':raise RuntimeError('WeiDU must be Windows PE')
    cur=existing(safe(root,BCS),10000)
    log=entries(root)
    if not log:raise RuntimeError('WeiDU.log has no active components')
    if not any('ENHANCED-POWERGAMING-SCRIPTS' in l.upper() for l in log):
        raise RuntimeError('Enhanced Powergaming Scripts not installed')
    if not any(MOD41_RE.search(x) for x in log):raise RuntimeError('BGX41 missing')
    if uninstall:
        if not MOD42_RE.search(log[-1]):raise RuntimeError('BGX42 is not last installed WeiDU mod')
        if sha(cur)!=OUTPUT_HASH:raise RuntimeError('live 042B BCS no longer matches preview; cannot safe-uninstall')
    else:
        if not MOD41_RE.search(log[-1]):raise RuntimeError('BGX41 is not last installed WeiDU mod')
        if any(MOD42_RE.search(x) for x in log):raise RuntimeError('BGX42 already installed')
        if sha(cur)!=PIN_SHA:raise RuntimeError('LIVE BCS SHA256 mismatch; refuse install')
        for path in (OWN_DIR,OWN_EXE):
            if safe(root,path).exists():raise RuntimeError('BGX42 path collision: '+path)
    if check_process: check_process()
    return {'game':str(root),'before_sha256':sha(cur),'components':len(log)}


def process_check():
    if os.name!='nt':return
    cmd=('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
         'Where-Object {$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
         'ForEach-Object {"{0} pid={1}" -f $_.Name,$_.ProcessId}')
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],capture_output=True,text=True,timeout=25)
    if p.returncode!=0:raise RuntimeError('process enumeration failed: '+(p.stderr or ''))
    if p.stdout.strip():raise RuntimeError('close game/loader/WeiDU before install: '+p.stdout.strip()[:300])


def backup(root:Path,pre:dict):
    base=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI42_SAFE_BACKUPS'
    if redirected(base) or redirected(base.parent):raise RuntimeError('unsafe backup root')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=base/('PRE_INSTALL_'+stamp)
    out.mkdir(parents=True,exist_ok=False)
    paths=('chitin.key',BCS,WEIDU_LOG,'lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk')
    hashes={}
    for rel in paths:
        src=safe(root,rel)
        if not src.is_file():
            if rel.endswith('dialogf.tlk'):continue
            raise RuntimeError('missing backup source: '+rel)
        existing(src)
        target=out/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if sha(src)!=sha(target):raise RuntimeError('backup checksum mismatch '+rel)
        hashes[rel]=sha(src)
    (out/'before.json').write_text(json.dumps({'preflight':pre,'hashes':hashes},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return out


def package_verify(pkg:Path):
    m=existing(pkg/'SOURCE_MANIFEST.json')
    data=json.loads(m.read_text(encoding='utf-8'))
    if data.get('release')!='042B_OPT_IN_WEIDU_CANDIDATE':raise RuntimeError('not the 042B release package')
    for rel,expected in data['files'].items():
        p=safe(pkg,rel)
        existing(p)
        if sha(p)!=expected:raise RuntimeError('source checksum mismatch: '+rel)
    if not set(SOURCE_FILES[:-1]).issubset(data['files']):raise RuntimeError('missing release sources')
    return data


def run_weidu(root:Path,*,uninstall=False,runner=subprocess.run):
    args=[str(root/OWN_EXE),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',
          '--force-uninstall' if uninstall else '--force-install','0']
    return runner(args,cwd=str(root),capture_output=True,text=True,timeout=600,
                  encoding='utf-8',errors='replace',check=False)


def install(root:Path,pkg:Path,*,check_process=process_check,runner=subprocess.run,require_exact_path=True):
    root=root.resolve();pkg=pkg.resolve()
    package_verify(pkg)
    pre=preflight(root,check_process=check_process,require_exact_path=require_exact_path)
    original=(root/BCS).read_bytes()
    candidate,report=build(original)
    if hashlib.sha256(candidate).hexdigest()!=OUTPUT_HASH:
        raise RuntimeError('preview hash gate failed')
    bkp=backup(root,pre)
    outcome={'status':'NOT_STARTED','preflight':pre,'preview':report,'backup':str(bkp)}
    staged=[]
    wei_du_started=False
    try:
        # All staging writes are explicit opt-in, after independently verified backup.
        mod=root/OWN_DIR
        mod.mkdir(exist_ok=False)
        staged.append(mod)
        (mod/'staged').mkdir()
        (mod/'staged'/'BDDEFAI.BCS').write_bytes(candidate)
        if sha(mod/'staged'/'BDDEFAI.BCS')!=OUTPUT_HASH:raise RuntimeError('stage checksum failed')
        shutil.copy2(pkg/'setup-BGX42.tp2',mod/'setup-BGX42.tp2')
        exe=root/OWN_EXE
        with (root/EXE).open('rb') as f,exe.open('xb') as w:shutil.copyfileobj(f,w)
        staged.append(exe)
        if sha(exe)!=sha(root/EXE):raise RuntimeError('WeiDU executable copy mismatch')
        wei_du_started=True
        r=run_weidu(root,runner=runner)
        outcome['weidu_exit_code']=r.returncode
        outcome['weidu_stdout_tail']=((r.stdout or '')+'\n'+(r.stderr or ''))[-6000:]
        checks={
            'weidu_success':r.returncode==0,
            'installed_as_last':bool(entries(root) and MOD42_RE.search(entries(root)[-1])),
            'exact_preview_in_override':sha(root/BCS)==OUTPUT_HASH,
            'chitin_unchanged':sha(root/'chitin.key')==sha(bkp/'chitin.key')
        }
        outcome['checks']=checks
        outcome['status']='INSTALLED_EXPERIMENTAL' if all(checks.values()) else 'REVIEW_WEIDU'
    except Exception as e:
        outcome['status']='BLOCKED_OR_REVIEW';outcome['error']=repr(e)
        if not wei_du_started:
            for x in reversed(staged):
                if x.is_file():x.unlink()
                elif x.is_dir():shutil.rmtree(x)
            outcome['stage_cleanup_before_weidu']=True
    finally:
        (bkp/'report.json').write_text(json.dumps(outcome,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return outcome


def uninstall(root:Path,pkg:Path,*,check_process=process_check,runner=subprocess.run,require_exact_path=True):
    root=root.resolve();pkg=pkg.resolve()
    package_verify(pkg)
    pre=preflight(root,uninstall=True,check_process=check_process,require_exact_path=require_exact_path)
    existing(root/OWN_EXE,100000)
    r=run_weidu(root,uninstall=True,runner=runner)
    ok=r.returncode==0 and not any(MOD42_RE.search(x) for x in entries(root)) and sha(root/BCS)==PIN_SHA
    return {'status':'UNINSTALLED_AND_RESTORED' if ok else 'REVIEW_UNINSTALL','weidu_exit_code':r.returncode,'post_bcs_sha256':sha(root/BCS),'weidu_tail':((r.stdout or '')+'\n'+(r.stderr or ''))[-5000:]}


def status(root:Path):
    try:
        print('BGXAI 042B status read only:',preflight(root,require_exact_path=True))
        print('BGX42 installed: False; only optional source candidate')
    except Exception as e:
        print('PRECHECK/STATUS:',e)
    print('NO GAME FILES CHANGED')


def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group()
    group.add_argument('--install',action='store_true')
    group.add_argument('--uninstall',action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args()
    if not (a.install or a.uninstall):status(a.game_root);return 0
    print('BGXAI 042B EXPERIMENTAL / EPS18.4 exact hash / 041 must be last')
    print('No game should be running. Offline backup and WeiDU rollback are mandatory.')
    if input('Confirm exact YES: ').strip()!='YES':
        print('CANCELLED. No changes.');return 0
    try:
        pkg=Path(__file__).resolve().parent
        result=uninstall(a.game_root,pkg) if a.uninstall else install(a.game_root,pkg)
        print('BGXAI 042B:',result['status'])
        for k,v in result.get('checks',{}).items():print(' ',k,':',v)
        print('Backup:',result.get('backup',''))
        return 0 if result['status'] in ('INSTALLED_EXPERIMENTAL','UNINSTALLED_AND_RESTORED') else 1
    except Exception as e:
        print('BGXAI 042B BLOCKED:',e)
        print('Do not repeat blindly or manually rewrite WeiDU-managed BCS.');return 1

if __name__=='__main__':sys.exit(main())