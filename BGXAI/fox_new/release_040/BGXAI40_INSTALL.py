"""BGXAI 0.3.10 opt-in EET installer. Never duplicates the game.

Only game resource modified BY WeiDU after explicit consent: override/BDDEFAI.BCS.
WeiDU also updates WeiDU.log and its usual mod-backup state; own source BAF is
independent code; never redistributes compiled EPS code. Default = status.
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
import subprocess
import sys

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE_FILES = ('setup-BGX40.tp2', 'BGX40/toggle_feedback.baf', 'BGX40/lang/ru_ru/feedback.tra')
CRITICAL = ('chitin.key', 'override/BDDEFAI.BCS', 'lang/ru_ru/dialog.tlk', 'lang/ru_ru/dialogf.tlk')
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
MOD_EXE = 'setup-BGX40.exe'
LOG_MARKER = re.compile(r'^\s*~[^~]*BGX40[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
VERSION = '0.3.10'
BASE_LOG_MARKER = re.compile(r'^\s*~[^~]*BGX39[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)

def base_installed(lines: list[str]) -> bool:
    return any(BASE_LOG_MARKER.search(x) for x in lines if not x.lstrip().startswith('//'))

def base_is_last(lines: list[str]) -> bool:
    active = [s for s in lines if s.lstrip().startswith('~')]
    return bool(active and BASE_LOG_MARKER.search(active[-1]))



def link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        import stat
        return bool(getattr(path.lstat(), 'st_file_attributes', 0) &
                    getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))
    except FileNotFoundError:
        return False


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def check_file(path: Path, *, min_size=1) -> None:
    if link(path) or not path.is_file() or path.stat().st_size < min_size:
        raise RuntimeError('Unsafe / missing file: ' + str(path))


def snapshot(root: Path) -> dict:
    for item in CRITICAL:
        check_file(root/item)
    return {p:sha(root/p) for p in CRITICAL}


def read_log(root: Path) -> list[str]:
    log = root/'WeiDU.log'
    check_file(log)
    return log.read_text(encoding='utf-8-sig', errors='replace').splitlines()


def installed(lines: list[str]) -> bool:
    return any(LOG_MARKER.search(x) for x in lines if not x.lstrip().startswith('//'))


def last_is_mod(lines: list[str]) -> bool:
    active = [s for s in lines if s.lstrip().startswith('~')]
    return bool(active and LOG_MARKER.search(active[-1]))


def inspect_processes(*, is_windows=None, runner=subprocess.run) -> list[str]:
    """Read-only inspection. No killing tasks; distinguish busy tasks from CIM failure.

    is_windows and runner are injectable solely for offline unit testing.
    """
    if is_windows is None:
        is_windows = os.name == 'nt'
    if not is_windows:
        return []
    ps = ('$ErrorActionPreference="Stop"; '
          'Get-CimInstance Win32_Process | Where-Object { '
          '$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$" '
          '} | ForEach-Object { "{0} (PID {1})" -f $_.Name, $_.ProcessId }')
    try:
        result = runner(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps],
                        capture_output=True, text=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise RuntimeError('Windows process inspection FAILED (not proof of running game): '
                           + str(ex)) from ex
    if result.returncode:
        detail = ((result.stderr or '') or (result.stdout or '')).strip().replace('\r', ' ')
        raise RuntimeError('Windows process inspection FAILED (exit {}): {}'.format(
            result.returncode, detail[:500] or 'no error text'))
    return [line.strip() for line in (result.stdout or '').splitlines() if line.strip()]


def check_processes() -> None:
    """Abort only after listing actual blocking processes (or a distinct query error)."""
    blockers = inspect_processes()
    if blockers:
        raise RuntimeError('Close these processes first: ' + '; '.join(blockers[:20]))


def verify(root: Path, pkg: Path, *, real_root=True, guard=check_processes) -> tuple[dict,list[str]]:
    root, pkg = root.resolve(), pkg.resolve()
    if real_root and os.path.normcase(str(root)).casefold() != os.path.normcase(str(GAME.resolve())).casefold():
        raise RuntimeError('Refusing to modify a different EET game')
    if link(root) or link(pkg) or not root.is_dir() or not pkg.is_dir():
        raise RuntimeError('Unsafe installation directory')
    current = snapshot(root)
    lines = read_log(root)
    exe = root/WEIDU
    check_file(exe, min_size=100000)
    with exe.open('rb') as stream:
        magic = stream.read(2)
    if magic != b'MZ':
        raise RuntimeError('WeiDU source is not a Windows executable')
    if not any('ENHANCED-POWERGAMING-SCRIPTS' in s.upper() for s in lines):
        raise RuntimeError('EPS missing from WeiDU.log; no install')
    for name in SOURCE_FILES:
        check_file(pkg/name)
        if (pkg/name).stat().st_size > 200000:
            raise RuntimeError('Unexpected oversized source in ZIP: '+name)
    if (pkg/'setup-BGX40.exe').exists() or (pkg/'BDDEFAI.BCS').exists():
        raise RuntimeError('This must be SOURCE-ONLY; no external game binary allowed')
    guard()
    return current, lines


def verify_source(pkg: Path):
    m = pkg/'SOURCE_MANIFEST.json'
    check_file(m)
    obj = json.loads(m.read_text(encoding='utf-8'))
    if obj.get('version') != VERSION or set(obj.get('files', {})) != set(SOURCE_FILES):
        raise RuntimeError('Unexpected source manifest')
    for name in SOURCE_FILES:
        rec = obj['files'][name]
        p = pkg/name
        if rec.get('size') != p.stat().st_size or rec.get('sha256') != sha(p):
            raise RuntimeError('Package corrupted: '+name)
    return obj


def backup_folder(root: Path) -> Path:
    """Backup outside the troublesome BGXAI_LOCAL_BUILD directory."""
    base = Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Documents' / 'BGXAI39_SAFE_BACKUPS'
    if not base.is_dir():
        base.mkdir(parents=True, exist_ok=True)
    if link(base) or link(base.parent):
        raise RuntimeError('Unsafe backup destination')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dst = base / ('PRE_INSTALL_'+stamp)
    dst.mkdir(exist_ok=False)
    return dst


def preserve(root: Path, dst: Path, before: dict, weidu_name: str):
    for name in (*CRITICAL,'WeiDU.log'):
        p = root/name
        dest = dst/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
        if sha(p)!=sha(dest):
            raise RuntimeError('Backup SHA mismatch: '+name)
    (dst/'status.json').write_text(json.dumps({'version':VERSION,'root':str(root),
         'original_hashes':before,'weidu_binary':weidu_name,'state':'BACKUP_ONLY'},
         ensure_ascii=False, indent=2)+'\n',encoding='utf-8')


def run_weidu(root: Path, *, uninstall=False, runner=subprocess.run):
    exe=root/MOD_EXE
    action='--force-uninstall' if uninstall else '--force-install'
    cmd=[str(exe),'--noautoupdate','--game',str(root),'--use-lang','ru_ru',action,'0']
    return runner(cmd,cwd=str(root),capture_output=True,text=True,
                  encoding='utf-8',errors='replace',timeout=600,check=False)


def run_install(root: Path, pkg: Path, *, real_root=True,
                guard=check_processes, runner=subprocess.run) -> dict:
    root, pkg = root.resolve(),pkg.resolve()
    before, entries=verify(root,pkg,real_root=real_root,guard=guard)
    verify_source(pkg)
    if not base_installed(entries):
        raise RuntimeError('BGX39 is not installed; refusing independent BGX40 without baseline')
    if installed(entries):
        raise RuntimeError('BGX40 already installed; refusing duplicate installation')
    if not base_is_last(entries):
        raise RuntimeError('BGX39 is not last WeiDU mod; refusing chain reordering')
    # Fail closed if any source / executable name exists already, even partially.
    for name in (*SOURCE_FILES, MOD_EXE):
        if (root/name).exists() or link(root/name):
            raise RuntimeError('Existing BGX40 file at game root; will not overwrite: '+name)
    backup=backup_folder(root)
    preserve(root,backup,before,WEIDU)
    # Excludes all EPS source; only our 3 original files + locally sourced WeiDU.
    staged=[]
    wei_du_started=False
    report={'version':VERSION,'backup':str(backup),'mode':'INSTALL',
            'status':'NOT_STARTED','game':str(root),'live_before':before}
    try:
        for rel in SOURCE_FILES:
            dest=root/rel
            if link(dest.parent):
                raise RuntimeError('Staging directory redirected')
            dest.parent.mkdir(parents=True,exist_ok=True)
            with (pkg/rel).open('rb') as src, dest.open('xb') as out:
                staged.append(rel)
                shutil.copyfileobj(src,out)
            if sha(dest)!=sha(pkg/rel):
                raise RuntimeError('Staged file hash mismatch: '+rel)
        exe=root/MOD_EXE
        with (root/WEIDU).open('rb') as src,exe.open('xb') as dst:
            staged.append(MOD_EXE)
            shutil.copyfileobj(src,dst)
        if sha(exe)!=sha(root/WEIDU):
            raise RuntimeError('WeiDU binary copy hash mismatch')
        wei_du_started=True
        result=run_weidu(root,runner=runner)
        report['weidu_exit_code']=result.returncode
        report['weiDU_output_tail']=((result.stdout or '')+'\n'+(result.stderr or ''))[-9000:]
        state=installed(read_log(root))
        # The modifier must show as installed and must have changed existing BCS.
        after=snapshot(root)
        report['live_after']=after
        report['status']='INSTALLED' if (result.returncode==0 and state and
            after['override/BDDEFAI.BCS']!=before['override/BDDEFAI.BCS'] and
            all(after[k]==before[k] for k in CRITICAL if k!='override/BDDEFAI.BCS')) else 'REVIEW_INSTALL'
        # If installation failed, NEVER overwrite WeiDU-managed game resources.
        # The original files are preserved in backup for diagnosis/WeiDU rollback.
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        report['status']='BLOCKED_OR_REVIEW'
        report['error']=str(e)
        # If WeiDU was never invoked, clean only our own staged bytes (not any
        # installed resource, never the game backup); do not leave an unusable
        # half-staged installer blocking the user's next attempt.
        if not wei_du_started:
            for rel in reversed(staged):
                target=root/rel
                original=(root/WEIDU) if rel==MOD_EXE else (pkg/rel)
                if target.is_file() and not link(target) and sha(target)==sha(original):
                    target.unlink()
            report['staged_files_cleaned_before_weiDU']=True
        report['live_after']=snapshot(root)
    finally:
        (backup/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def find_previous_backup(root: Path):
    base=Path(os.environ.get('USERPROFILE',str(Path.home())))/'Documents'/'BGXAI39_SAFE_BACKUPS'
    if not base.is_dir() or link(base):
        return None
    for item in sorted(base.glob('PRE_INSTALL_*/status.json'),reverse=True):
        try:
            x=json.loads(item.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError):
            continue
        if x.get('root')==str(root) and x.get('version')==VERSION:
            return item.parent,x
    return None


def run_uninstall(root: Path,pkg: Path,*,real_root=True,guard=check_processes,
                  runner=subprocess.run)->dict:
    root=root.resolve()
    before,lines=verify(root,pkg,real_root=real_root,guard=guard)
    if not installed(lines):
        raise RuntimeError('BGX40 is not installed')
    if not last_is_mod(lines):
        raise RuntimeError('Another mod was installed AFTER BGX40. Refuse automated rollback; keep all mods intact.')
    check_file(root/MOD_EXE,min_size=100000)
    old=find_previous_backup(root)
    if old is None:
        raise RuntimeError('BGX40 original pre-install backup not found; refuse auto-uninstall')
    path,meta=old
    p=run_weidu(root,uninstall=True,runner=runner)
    after=snapshot(root)
    still=installed(read_log(root))
    restored=(after['override/BDDEFAI.BCS']==meta['original_hashes']['override/BDDEFAI.BCS'])
    unchanged=all(after[k]==before[k] for k in CRITICAL if k!='override/BDDEFAI.BCS')
    report={'status':'UNINSTALLED_AND_RESTORED' if p.returncode==0 and not still and restored and unchanged else 'REVIEW_UNINSTALL',
            'weiDU_exit_code':p.returncode,'weiDU_output_tail':((p.stdout or '')+'\n'+(p.stderr or ''))[-9000:],
            'original_eps_restored':restored,'tlk_and_chitin_unchanged':unchanged,'backup':str(path)}
    (path/'uninstall_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def status(root: Path,pkg: Path,*,real_root=True):
    root=root.resolve()
    if real_root and str(root).casefold()!=str(GAME.resolve()).casefold():
        raise RuntimeError('Unexpected game')
    print('BGXAI 0.3.10 - STATUS / safe installer')
    print('Game:',root)
    print('Source package:',pkg)
    check_file(root/'override/BDDEFAI.BCS')
    lines=read_log(root)
    print('EPS installed:',any('ENHANCED-POWERGAMING-SCRIPTS' in x.upper() for x in lines))
    print('BGX39 baseline installed:',base_installed(lines))
    print('BGX40 installed:',installed(lines))
    print('Backup directory: Documents/BGXAI39_SAFE_BACKUPS')
    try:
        running = inspect_processes()
        print('Windows process gate:', 'BLOCKED - ' + '; '.join(running) if running else 'CLEAR')
    except RuntimeError as exc:
        print('Windows process gate: CHECK FAILED -', exc)



def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='BGXAI 040 visible F guard status over existing 039')
    p.add_argument('--install',action='store_true')
    p.add_argument('--uninstall',action='store_true')
    p.add_argument('--status',action='store_true')
    args=p.parse_args(argv)
    if sum((args.install,args.uninstall,args.status))>1:
        print('Select only one option');return 2
    root,pkg=GAME,Path(__file__).resolve().parent
    try:
        if not(args.install or args.uninstall or args.status):
            print('BGXAI 0.3.10 / EPS 18.4')
            print('1 - Install mode feedback over existing F guard')
            print('2 - Rollback via WeiDU')
            print('3 - Check status only (no changes)')
            print('0 - Exit')
            selection=input('Choice [3]: ').strip() or '3'
            if selection=='0':return 0
            if selection=='1':args.install=True
            elif selection=='2':args.uninstall=True
            elif selection=='3':args.status=True
            else:raise RuntimeError('Unknown menu option')
        if args.status:
            status(root,pkg);return 0
        print('Target game:',root)
        print('Requires installed BGX39 as LAST WeiDU mod; modifies only BDDEFAI through WeiDU.')
        print('Current BDDEFAI.BCS will be backed up BEFORE installation. No full game clone.')
        if input('Confirm by typing YES: ').strip()!='YES':
            print('CANCELLED: no changes');return 0
        if args.install:
            data=run_install(root,pkg)
        else:
            data=run_uninstall(root,pkg)
        print('BGXAI 040:',data['status'])
        print('Backup:',data.get('backup'))
        if 'weiDU_output_tail' in data:print('WeiDU:',data['weiDU_output_tail'][-2000:])
        return 0 if data['status'] in ('INSTALLED','UNINSTALLED_AND_RESTORED') else 1
    except (RuntimeError,OSError,ValueError,KeyError,json.JSONDecodeError,subprocess.TimeoutExpired) as e:
        print('BGXAI 040 BLOCKED:',str(e))
        print('Do NOT manually restore BDDEFAI: keep backup and installer report for review.')
        return 1

if __name__=='__main__':sys.exit(main())
