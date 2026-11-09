#!/usr/bin/env python3
"""BGXAI 043 isolated passive EEex Lua observer WeiDU wrapper.

Only M_BGX43Probe.lua gets installed to override via WeiDU. No .BCS, .TLK,
UI.MENU or script-slot modification. All modifications require explicit YES.
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
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
OWN_EXE = 'setup-BGX43.exe'
MOD_DIR = 'BGX43'
MOD_TP2 = 'BGX43/setup-BGX43.tp2'
MOD_LUA = 'BGX43/M_BGX43Probe.lua'
INSTALLED_LUA = 'override/M_BGX43Probe.lua'
BCS = 'override/BDDEFAI.BCS'
WEIDU_LOG = 'WeiDU.log'
EEEX_BOOT = 'override/M___EEex.lua'
BCS_042B_HASH = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
MOD42_RE = re.compile(r'^\s*~[^~]*BGX42[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
MOD43_RE = re.compile(r'^\s*~[^~]*BGX43[^~]*\.TP2~\s+#\d+\s+#0(?:\s|$)', re.I)
OWN_SOURCE = ('BGXAI43_PROBE_INSTALL.py', 'BGX43/setup-BGX43.tp2',
              'BGX43/M_BGX43Probe.lua', 'BGX43/tests/test_installer_043.py',
              'README_RU.md', 'eeex_bridge_043.py', 'intercept_policy.py',
              'test_eeex_bridge_043.py', 'SOURCE_MANIFEST.json')


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def is_redirect(p: Path) -> bool:
    try:
        st = p.lstat()
    except FileNotFoundError:
        return False
    return p.is_symlink() or bool(getattr(st, 'st_file_attributes', 0) &
                                 getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def safe(root: Path, relative: str) -> Path:
    if not relative or relative.startswith('/') or '\\' in relative or ':' in relative or '..' in Path(relative).parts:
        raise RuntimeError('unsafe relative path: ' + relative)
    target = root / relative
    item = target
    while True:
        if is_redirect(item):
            raise RuntimeError('symlink/reparse blocked: ' + str(item))
        if item == root or item.parent == item:
            break
        item = item.parent
    return target


def required(p: Path, minimum=1) -> Path:
    if is_redirect(p) or not p.is_file() or p.stat().st_size < minimum:
        raise RuntimeError('missing/unsafe file: ' + str(p))
    return p


def active(root: Path) -> list[str]:
    lines = required(safe(root, WEIDU_LOG)).read_text(encoding='utf-8-sig', errors='replace').splitlines()
    return [x.strip() for x in lines if x.lstrip().startswith('~')]


def verify_package(pkg: Path) -> dict:
    manifest = json.loads(required(safe(pkg, 'SOURCE_MANIFEST.json')).read_text(encoding='utf-8'))
    if manifest.get('version') != '0.3.14-043-PROBE' or manifest.get('status') != 'OPT_IN_READ_ONLY_EEEX_PROBE':
        raise RuntimeError('wrong observer package version/status')
    if manifest.get('required_bcs_sha256') != BCS_042B_HASH:
        raise RuntimeError('wrong observer baseline')
    hashes = manifest.get('files', {})
    if set(hashes) != set(OWN_SOURCE) - {'SOURCE_MANIFEST.json'}:
        raise RuntimeError('unexpected source allowlist')
    for name, info in hashes.items():
        p = required(safe(pkg, name))
        if p.stat().st_size != info['size'] or p.stat().st_size > 120000 or sha(p) != info['sha256']:
            raise RuntimeError('tampered source file: ' + name)
    code = (pkg / MOD_LUA).read_text(encoding='utf-8')
    for forbidden in ('ClearActions(', 'ActionOverride(', 'QueueResponseString(',
                      'EEex_Action_Queue', 'io.open(', 'os.execute('):
        if forbidden in '\n'.join(line.split('--', 1)[0] for line in code.splitlines()):
            raise RuntimeError('unexpected mutating Lua token: ' + forbidden)
    return manifest


def check_game(root: Path, *, uninstall=False, require_root=True, process_guard=None) -> dict:
    root = root.resolve()
    if require_root and str(root).casefold() != str(GAME).casefold():
        raise RuntimeError('wrong EET game root')
    required(safe(root, 'chitin.key'), 1000)
    required(safe(root, WEIDU_EXE), 100000)
    with (root / WEIDU_EXE).open('rb') as exe_file:
        if exe_file.read(2) != b'MZ':
            raise RuntimeError('WeiDU EXE is not Windows PE')
    required(safe(root, EEEX_BOOT), 10)
    required(safe(root, 'InfinityLoader.exe'), 10000)
    bcs = required(safe(root, BCS), 10000)
    if sha(bcs) != BCS_042B_HASH:
        raise RuntimeError('current BCS not exact live 042B (will not modify)')
    lines = active(root)
    if not lines or not any('ENHANCED-POWERGAMING-SCRIPTS' in x.upper() for x in lines):
        raise RuntimeError('EPS missing')
    if not any(MOD42_RE.search(x) for x in lines):
        raise RuntimeError('042B missing')
    if uninstall:
        if not MOD43_RE.search(lines[-1]):
            raise RuntimeError('043 probe not the last installed WeiDU component')
        deployed = required(safe(root, INSTALLED_LUA))
    else:
        if not MOD42_RE.search(lines[-1]):
            raise RuntimeError('042B not last: refuse to add 043 probe')
        if any(MOD43_RE.search(x) for x in lines):
            raise RuntimeError('043 probe already installed')
        for name in (MOD_DIR, OWN_EXE, INSTALLED_LUA):
            if safe(root, name).exists():
                raise RuntimeError('probe file collision: ' + name)
    if process_guard:
        process_guard()
    return {'game': str(root), 'bcs_sha256': sha(bcs),
            'chitin_sha256': sha(root / 'chitin.key'),
            'eeex_boot_sha256': sha(root / EEEX_BOOT),
            'weidu_log_sha256': sha(root / WEIDU_LOG),
            'installed_lua_sha256': sha(deployed) if uninstall else None}


def check_processes():
    if os.name != 'nt':
        return
    ps = ('$ErrorActionPreference="Stop"; Get-CimInstance Win32_Process | '
          'Where-Object {$_.Name -match "^(Baldur|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
          'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', ps],
                            capture_output=True, text=True, timeout=25)
    if result.returncode != 0:
        raise RuntimeError('process check failed: ' + (result.stderr or '')[:300])
    if result.stdout.strip():
        raise RuntimeError('close game / InfinityLoader / WeiDU before changing scripts: ' + result.stdout[:300])


def backup(root: Path, pre: dict, *, label='PRE_INSTALL', base=None) -> Path:
    if base is None:
        base = Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Documents' / 'BGXAI43_SAFE_BACKUPS'
    if is_redirect(base) or is_redirect(base.parent):
        raise RuntimeError('unsafe backup root')
    base.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = base / (label + '_' + stamp)
    folder.mkdir(exist_ok=False)
    saved = {}
    for rel in ('chitin.key', BCS, WEIDU_LOG, EEEX_BOOT, 'InfinityLoader.ini',
                'lang/ru_RU/dialog.tlk', 'lang/ru_RU/dialogf.tlk'):
        path = safe(root, rel)
        if not path.is_file():
            if rel in ('InfinityLoader.ini', 'lang/ru_RU/dialogf.tlk'):
                continue
            raise RuntimeError('backup file missing: ' + rel)
        required(path)
        dest = folder / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        if sha(path) != sha(dest):
            raise RuntimeError('backup copy mismatch: ' + rel)
        saved[rel] = sha(path)
    if pre['installed_lua_sha256']:
        target = folder / INSTALLED_LUA
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(required(safe(root, INSTALLED_LUA)), target)
        if sha(target) != pre['installed_lua_sha256']:
            raise RuntimeError('installed observer changed during backup')
        saved[INSTALLED_LUA] = sha(target)
    (folder / 'before.json').write_text(json.dumps({'pre': pre, 'hashes': saved}, indent=2,
                                                  ensure_ascii=False) + '\n', encoding='utf-8')
    return folder


def execute_weidu(root: Path, *, uninstall=False, runner=subprocess.run):
    args = [str(root / OWN_EXE), '--noautoupdate', '--game', str(root), '--use-lang', 'ru_ru',
            '--force-uninstall' if uninstall else '--force-install', '0']
    return runner(args, cwd=str(root), capture_output=True, text=True, encoding='utf-8',
                  errors='replace', timeout=600, check=False)


def install(root: Path, pkg: Path, *, runner=subprocess.run, guard=check_processes, require_root=True, backup_dir=None):
    root = root.resolve(); pkg = pkg.resolve()
    manifest = verify_package(pkg)
    pre = check_game(root, process_guard=guard, require_root=require_root)
    bkp = backup(root, pre, base=backup_dir)
    result = {'status': 'NOT_STARTED', 'baseline': pre, 'backup': str(bkp)}
    staged = []
    started = False
    try:
        md = root / MOD_DIR
        md.mkdir(exist_ok=False)
        staged.append(md)
        shutil.copy2(pkg / MOD_TP2, md / 'setup-BGX43.tp2')
        shutil.copy2(pkg / MOD_LUA, md / 'M_BGX43Probe.lua')
        if sha(md / 'M_BGX43Probe.lua') != manifest['files'][MOD_LUA]['sha256']:
            raise RuntimeError('staged Lua hash failure')
        exe = root / OWN_EXE
        with required(root / WEIDU_EXE, 100000).open('rb') as src, exe.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        staged.append(exe)
        if sha(exe) != sha(root / WEIDU_EXE):
            raise RuntimeError('staged WeiDU mismatch')
        if sha(root / BCS) != BCS_042B_HASH or not MOD42_RE.search(active(root)[-1]):
            raise RuntimeError('game changed after preflight')
        started = True
        exe_result = execute_weidu(root, runner=runner)
        after = active(root)
        checks = {
            'weidu_exit_zero': exe_result.returncode == 0,
            '043_last': bool(after and MOD43_RE.search(after[-1])),
            'observer_in_override': ((root / INSTALLED_LUA).is_file() and
                                     sha(root / INSTALLED_LUA) == manifest['files'][MOD_LUA]['sha256']),
            '042b_bcs_unchanged': sha(root / BCS) == BCS_042B_HASH,
            'chitin_unchanged': sha(root / 'chitin.key') == pre['chitin_sha256'],
            'eeex_unchanged': sha(root / EEEX_BOOT) == pre['eeex_boot_sha256'],
        }
        result.update(checks=checks, wei_du_output=((exe_result.stdout or '') + '\n' +
                        (exe_result.stderr or ''))[-6000:],
                      status='INSTALLED_PASSIVE_043' if all(checks.values()) else 'REVIEW_WEIDU')
    except Exception as exc:
        result.update(status='REVIEW_WEIDU' if started else 'BLOCKED_BEFORE_WEIDU', error=str(exc))
        if not started:
            for p in reversed(staged):
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
    finally:
        (bkp / 'report.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return result


def backup_for_uninstall(root: Path, *, base=None):
    if base is None:
        base = Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Documents' / 'BGXAI43_SAFE_BACKUPS'
    if not base.is_dir() or is_redirect(base) or is_redirect(base.parent):
        raise RuntimeError('043 original backup missing')
    for metadata in sorted(base.glob('PRE_INSTALL_*/before.json'), reverse=True):
        try:
            folder = metadata.parent
            if is_redirect(folder) or is_redirect(metadata):continue
            d = json.loads(metadata.read_text(encoding='utf-8'))
            pre = d['pre']; hashes = d['hashes']
            if pre['game'] != str(root) or pre['bcs_sha256'] != BCS_042B_HASH:continue
            if any(sha(required(folder / name)) != value for name, value in hashes.items()):continue
            r = json.loads(required(folder / 'report.json').read_text(encoding='utf-8'))
            if r.get('status') != 'INSTALLED_PASSIVE_043' or r.get('backup') != str(folder):continue
            return folder
        except (OSError, ValueError, RuntimeError, KeyError, TypeError):
            continue
    raise RuntimeError('no verified successful 043 original backup')


def uninstall(root: Path, pkg: Path, *, runner=subprocess.run, guard=check_processes, require_root=True, backup_dir=None):
    root = root.resolve(); pkg = pkg.resolve()
    m = verify_package(pkg)
    pre = check_game(root, uninstall=True, process_guard=guard, require_root=require_root)
    if sha(root / INSTALLED_LUA) != m['files'][MOD_LUA]['sha256']:
        raise RuntimeError('installed observer Lua was changed; refuse rollback')
    original = backup_for_uninstall(root, base=backup_dir)
    if sha(root / 'chitin.key') != sha(original / 'chitin.key'):
        raise RuntimeError('chitin changed since 043 install')
    required(root / OWN_EXE, 100000)
    bkp = backup(root, pre, label='PRE_ROLLBACK', base=backup_dir)
    result = {'status': 'NOT_STARTED', 'original_backup': str(original), 'backup': str(bkp)}
    try:
        if not MOD43_RE.search(active(root)[-1]) or sha(root / BCS) != BCS_042B_HASH:
            raise RuntimeError('game changed during rollback preflight')
        proc = execute_weidu(root, uninstall=True, runner=runner)
        after = active(root)
        checks = {
            'weidu_exit_zero': proc.returncode == 0,
            '043_absent': not any(MOD43_RE.search(line) for line in after),
            '042_last': bool(after and MOD42_RE.search(after[-1])),
            '042b_bcs_unchanged': sha(root / BCS) == BCS_042B_HASH,
            'observer_removed': not (root / INSTALLED_LUA).exists(),
            'chitin_unchanged': sha(root / 'chitin.key') == pre['chitin_sha256'],
        }
        result.update(checks=checks, status='UNINSTALLED_PASSIVE_043' if all(checks.values()) else 'REVIEW_UNINSTALL',
                      wei_du_output=((proc.stdout or '')+'\n'+(proc.stderr or ''))[-6000:])
    except Exception as exc:
        result.update(status='REVIEW_UNINSTALL', error=str(exc))
    finally:
        (bkp/'uninstall_report.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return result


def status(root: Path, pkg: Path, *, require_root=True, backup_dir=None):
    print('BGXAI 043 EEex OBSERVER / READ-ONLY STATUS')
    try:
        manifest=verify_package(pkg)
        root=root.resolve()
        if require_root and str(root).casefold() != str(GAME).casefold():
            raise RuntimeError('wrong EET game root')
        lines=active(root)
        bcs=sha(required(root/BCS))
        lua=root/INSTALLED_LUA
        is43=any(MOD43_RE.search(v) for v in lines)
        print('BGX42 installed:',any(MOD42_RE.search(v) for v in lines))
        print('BGX43 installed:',is43)
        print('BGX43 is last:',bool(lines and MOD43_RE.search(lines[-1])))
        print('Current BCS unchanged:',bcs==BCS_042B_HASH)
        print('EEex boot present:',(root/EEEX_BOOT).is_file())
        print('Observer file present:',lua.is_file())
        print('Observer file SHA256 matches:',lua.is_file() and sha(lua)==manifest['files'][MOD_LUA]['sha256'])
        if is43:
            try:
                verified=backup_for_uninstall(root,base=backup_dir)
                print('Verified rollback backup:',verified)
            except RuntimeError as e:print('Rollback backup REVIEW:',str(e))
        print('NOTE: Live callback firing is NOT established by filesystem status')
    except Exception as e:
        print('STATUS BLOCKED:',str(e))
    print('NO GAME FILES CHANGED')


def main(argv=None):
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group()
    group.add_argument('--status',action='store_true')
    group.add_argument('--install',action='store_true')
    group.add_argument('--uninstall',action='store_true')
    p.add_argument('--game-root',type=Path,default=GAME)
    a=p.parse_args(argv)
    pkg=Path(__file__).resolve().parent
    if not a.install and not a.uninstall:
        status(a.game_root,pkg);return 0
    print('BGXAI 043 PASSIVE OBSERVER. No AI actions, no BCS changes. Experimental WeiDU. Requires YES.')
    if input('Confirm exact YES: ').strip()!='YES':
        print('CANCELLED; no changes');return 0
    try:
        r=(install(a.game_root,pkg) if a.install else uninstall(a.game_root,pkg))
        print('BGXAI 043:',r['status'])
        for name, ok in r.get('checks',{}).items():print(' ',name,':',ok)
        print('Backup:',r.get('backup',''))
        if r.get('error'):print('ERROR:',r['error'])
        return 0 if r['status'] in ('INSTALLED_PASSIVE_043','UNINSTALLED_PASSIVE_043') else 1
    except Exception as exc:
        print('BGXAI 043 BLOCKED:',str(exc))
        print('Do not repeat blindly or manually copy M_ lua files.');return 1

if __name__=='__main__':sys.exit(main())
