#!/usr/bin/env python3
"""R27 passive single-callback observer: guarded, last-only WeiDU install.

One existing BGXAI_UPDATE.cmd entry only. READ ONLY default. No auto-weapon
selection, no EPS or prior Lua edits, no installation without typed consent.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE = Path(__file__).with_name('M_BGXR27.lua')
SOURCE_SHA = 'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735'
DIR = 'BGXR27'
MODULE = 'override/M_BGXR27.lua'
STAGED = 'BGXR27/staged/M_BGXR27.lua'
TP2 = 'BGXR27/setup-BGXR27.tp2'
EXE = 'setup-BGXR27.exe'
PROOF = 'BGXR27/PROOF.json'
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
TD15_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXTD15[/\\]SETUP-BGXTD15[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
R27_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXR27[/\\]SETUP-BGXR27[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
INSTALL_TOKEN = 'INSTALL_BGXAI_R27_PASSIVE_OBSERVER'
ROLLBACK_TOKEN = 'ROLLBACK_BGXAI_R27_PASSIVE_OBSERVER'
BASELINE = {
    'override/M___EEex.lua': 'e52ae61c29edb6f4a771184939d6153206f76c20d3e2522dfa158c6c943aa6cf',
    'EEex_scripts/EEex_Action.lua': '7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da',
    'override/M_BGXWP.lua': 'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36',
    'override/M_BGXW2.lua': 'dab7b3f5e55307088090666cb9d47989385c6895820cdf6a860e4db0f1b6b053',
    'override/M_BGXW4.lua': '79f57787be045732352582d531ce69f2485504947204bf553fa8a04a95c6595e',
    'override/M_BGXD13.lua': '040a5df62c84363fd0d566c9509636efba7721439afcc90c72758da094e7f5f8',
}
TP2_TEXT = ('BACKUP ~BGXR27/backup~\n'
            'AUTHOR ~BGXAI guarded R27 selected weapon passive observer~\n'
            'BEGIN ~BGXR27 selected-weapon read-only observer only~\n'
            'COPY ~BGXR27/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n')
BLOCKED = (b'SelectWeaponAbility(', b'ClearActions(', b'ActionOverride(',
           b'XEquipItem(', b'FillSlot(', b'SetGlobal(', b'Attack(',
           b'Stop(', b'CreateCreature(', b'SetGlobalTimer(',
           b'EEex_Resource_Demand(', b'getAbility(', b'getLauncher(',
           b'EEex_Action_QueueScriptFileResponseOnAIBase(', b'io.open(',
           b'os.execute(', b'dofile(', b'loadfile(')


def alias(p: Path) -> bool:
    fn = getattr(p, 'is_junction', None)
    return p.is_symlink() or bool(fn and fn())


def regular(root: Path, rel: str) -> Path:
    p = root
    if not rel or rel.startswith(('/', '\\')): raise ValueError('BAD_RELATIVE_PATH')
    for component in rel.replace('\\', '/').split('/'):
        if component in ('', '.', '..'): raise ValueError('BAD_PATH_COMPONENT:' + rel)
        p = p / component
        if alias(p): raise ValueError('REPARSE_PATH_STOP:' + rel)
    return p


def digest(p: Path) -> str:
    if alias(p) or not p.is_file(): raise ValueError('FILE_MISSING_OR_LINK:' + str(p))
    with p.open('rb') as handle: return hashlib.file_digest(handle, 'sha256').hexdigest()


def sources() -> None:
    if len('M_BGXR27') != 8: raise ValueError('INVALID_ENGINE_RESREF')
    if digest(SOURCE) != SOURCE_SHA: raise ValueError('R27_SOURCE_SHA_MISMATCH')
    data = SOURCE.read_bytes()
    if len(data) > 50000 or b'\x00' in data or any(b in data for b in BLOCKED):
        raise ValueError('R27_SOURCE_NOT_PASSIVE')
    for marker in (b'P.initialized=start()', b'P.registered=true',
                   b'R27.prepareConsolePilot', b'nativeEventTokenAuthenticated=false',
                   b'alternativeAPRVerified=false', b'weaponSwitchAuthorized=false',
                   b'dispatchAuthorized=false'):
        if marker not in data: raise ValueError('R27_SOURCE_REQUIRED_MARKER_MISSING:' + repr(marker))
    if data.count(b'pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener)') != 1:
        raise ValueError('R27_LISTENER_COUNT_MISMATCH')


def game(root: Path) -> None:
    if os.name != 'nt' or os.path.normcase(os.path.abspath(root)) != os.path.normcase(os.path.abspath(GAME)):
        raise ValueError('EXACT_WINDOWS_GAME_ROOT_REQUIRED')
    if alias(root) or not root.is_dir() or not regular(root, 'chitin.key').is_file():
        raise ValueError('GAME_ROOT_INVALID')


def processes() -> None:
    if os.name != 'nt': raise ValueError('WINDOWS_REQUIRED')
    p = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, errors='replace', timeout=25)
    if p.returncode: raise ValueError('TASKLIST_FAILED')
    running = {row[0].strip().lower() for row in csv.reader(io.StringIO(p.stdout)) if row}
    blockers = {'baldur.exe', 'bgmain.exe', 'infinityloader.exe', 'weidu.exe',
                'setup-enhanced-powergaming-scripts.exe', 'setup-bgxr27.exe',
                'setup-bgxtd15.exe', 'setup-bgxtd14.exe'}
    if running & blockers: raise ValueError('GAME_OR_WEIDU_RUNNING')


def last(root: Path) -> str:
    p = regular(root, 'WeiDU.log')
    if not p.is_file(): raise ValueError('WEIDU_LOG_MISSING')
    entries = [line.strip() for line in p.read_text(encoding='utf-8-sig', errors='replace').splitlines()
               if line.lstrip().startswith('~')]
    return entries[-1] if entries else 'NONE'


def baseline(root: Path) -> None:
    for rel, expected in BASELINE.items():
        if digest(regular(root, rel)) != expected:
            raise ValueError('BASELINE_SHA_MISMATCH:' + rel)
    proof = regular(root, 'BGXTD15/PROOF.json')
    if not proof.is_file(): raise ValueError('TD15_PROOF_NOT_FOUND')
    data = json.loads(proof.read_text(encoding='utf-8'))
    if data.get('status') != 'BGXTD15_INSTALLED_AWAITING_LIVE_TEST' or data.get('sourceSha256') != BASELINE['override/M_BGXD13.lua']:
        raise ValueError('TD15_PROOF_UNVERIFIED')


def weidu(root: Path) -> Path:
    p = regular(root, WEIDU_EXE)
    if not p.is_file() or not 50000 < p.stat().st_size < 70000000:
        raise ValueError('WEIDU_BINARY_UNAVAILABLE')
    with p.open('rb') as h:
        if h.read(2) != b'MZ': raise ValueError('WEIDU_BINARY_NOT_PE')
    return p


def external_dir() -> Path:
    home = os.environ.get('USERPROFILE')
    if not home: raise ValueError('USERPROFILE_NOT_SET')
    base = Path(home) / 'Documents' / 'BGXAI_BACKUPS'
    if alias(base) or alias(base.parent): raise ValueError('BACKUP_REPARSE_STOP')
    return base


def backup(root: Path) -> Path:
    parent = external_dir(); parent.mkdir(parents=True, exist_ok=True)
    dest = parent / ('PRE_BGXR27_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    paths = ('WeiDU.log', 'chitin.key', 'BGXTD15/PROOF.json', *BASELINE.keys())
    for rel in paths:
        src = regular(root, rel); dst = regular(dest, rel)
        if not src.is_file(): raise ValueError('BACKUP_SOURCE_MISSING:' + rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if digest(dst) != digest(src): raise ValueError('BACKUP_DIGEST_MISMATCH:' + rel)
    return dest


def preflight(root: Path) -> dict:
    game(root); sources(); baseline(root); processes(); weidu(root)
    if not TD15_LAST.match(last(root)): raise ValueError('TD15_NOT_WEIDU_LAST_NO_INSTALL')
    for rel in (DIR, STAGED, TP2, EXE, PROOF, MODULE):
        if regular(root, rel).exists(): raise ValueError('R27_PATH_ALREADY_EXISTS:' + rel)
    return {'schema':'BGXAI_R27_GUARDED_V1', 'status':'R27_PREFLIGHT_PASS_NO_INSTALL',
            'sourceSha256':SOURCE_SHA, 'WeiDULast':last(root),
            'baselineVerified':len(BASELINE), 'gameplayResourcesModified':False,
            'installAuthorized':False, 'weaponSwitchAuthorized':False}


def status(root: Path) -> dict:
    game(root); sources(); baseline(root)
    current = last(root); module = regular(root, MODULE)
    if R27_LAST.match(current) and module.is_file() and digest(module) == SOURCE_SHA:
        p = regular(root, PROOF)
        if not p.is_file(): raise ValueError('R27_PROOF_MISSING')
        proof = json.loads(p.read_text(encoding='utf-8'))
        if proof.get('sourceSha256') != SOURCE_SHA or proof.get('status') != 'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST':
            raise ValueError('R27_PROOF_INVALID')
        result = 'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'
    elif TD15_LAST.match(current) and not module.exists():
        result = 'R27_NOT_INSTALLED'
    else:
        raise ValueError('R27_UNRECOGNIZED_STATE_OR_NOT_LAST')
    return {'status':result, 'WeiDULast':current,
            'gameplayResourcesModifiedByStatus':False, 'weaponSwitchAuthorized':False}


def run_weidu(root: Path, uninstall=False) -> None:
    argv = [str(regular(root, EXE)), '--noautoupdate', '--no-exit-pause',
            '--game', str(root), '--use-lang', 'ru_ru',
            '--force-uninstall' if uninstall else '--force-install', '0']
    p = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, errors='replace', timeout=180)
    output = ((p.stdout or '') + '\n' + (p.stderr or ''))[-2000:]
    if p.returncode or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)', output):
        raise ValueError('WEIDU_FAILED:' + output)


def install(root: Path, token: str) -> dict:
    if token != INSTALL_TOKEN: raise ValueError('INSTALL_TOKEN_REQUIRED')
    preflight(root)
    b = backup(root)
    sources(); baseline(root); processes()
    if not TD15_LAST.match(last(root)): raise ValueError('WEIDU_CHANGED_AFTER_BACKUP')
    stage = regular(root, STAGED); stage.parent.mkdir(parents=True, exist_ok=False)
    shutil.copy2(SOURCE, stage)
    if digest(stage) != SOURCE_SHA: raise ValueError('STAGED_SOURCE_MISMATCH')
    regular(root, TP2).write_text(TP2_TEXT, encoding='utf-8', newline='\n')
    executable = regular(root, EXE)
    shutil.copy2(weidu(root), executable)
    if digest(executable) != digest(regular(root, WEIDU_EXE)):
        raise ValueError('STAGED_WEIDU_MISMATCH')
    sources(); baseline(root); processes()
    if not TD15_LAST.match(last(root)) or regular(root, MODULE).exists():
        raise ValueError('PREINSTALL_DRIFT')
    # Persist a recovery pointer *before* calling WeiDU; it is never permission
    # to perform an unsafe rollback if R27 is not the last installed component.
    p = regular(root, PROOF)
    p.write_text(json.dumps({'schema':'BGXAI_R27_PROOF_V1', 'status':'R27_PENDING_WEIDU',
                             'sourceSha256':SOURCE_SHA, 'externalBackup':str(b)},
                            indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    run_weidu(root)
    if not R27_LAST.match(last(root)) or digest(regular(root, MODULE)) != SOURCE_SHA:
        raise ValueError('R27_POSTINSTALL_CHECK_FAILED')
    baseline(root)
    evidence = {'schema':'BGXAI_R27_PROOF_V1', 'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST',
                'sourceSha256':SOURCE_SHA, 'externalBackup':str(b),
                'installedUtc':datetime.now(timezone.utc).isoformat(),
                'gameplayResourcesModified':True, 'weaponSwitchAuthorized':False,
                'dispatchAuthorized':False}
    p.write_text(json.dumps(evidence, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return evidence


def rollback(root: Path, token: str) -> dict:
    if token != ROLLBACK_TOKEN: raise ValueError('ROLLBACK_TOKEN_REQUIRED')
    game(root); sources(); baseline(root); processes()
    if not R27_LAST.match(last(root)) or digest(regular(root, MODULE)) != SOURCE_SHA:
        raise ValueError('R27_NOT_LAST_NO_SAFE_ROLLBACK')
    p = regular(root, PROOF)
    if not p.is_file(): raise ValueError('R27_PROOF_MISSING')
    proof = json.loads(p.read_text(encoding='utf-8'))
    if proof.get('status') not in {'R27_PENDING_WEIDU', 'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'} or proof.get('sourceSha256') != SOURCE_SHA:
        raise ValueError('R27_PROOF_INVALID')
    b = Path(proof.get('externalBackup', ''))
    parent = external_dir()
    if b.parent != parent or not b.name.startswith('PRE_BGXR27_') or alias(b) or not b.is_dir():
        raise ValueError('UNTRUSTED_BACKUP')
    if not TD15_LAST.match(last(b)) or digest(regular(b, 'chitin.key')) != digest(regular(root, 'chitin.key')):
        raise ValueError('BACKUP_TD15_STATE_UNVERIFIED')
    for rel, expected in BASELINE.items():
        if digest(regular(b, rel)) != expected: raise ValueError('BACKUP_BASELINE_MISMATCH:' + rel)
    run_weidu(root, uninstall=True)
    if not TD15_LAST.match(last(root)) or regular(root, MODULE).exists():
        raise ValueError('R27_WEIDU_ROLLBACK_INCOMPLETE')
    baseline(root)
    return {'status':'R27_ROLLBACK_TD15_RESTORED',
            'weaponSwitchAuthorized':False, 'dispatchAuthorized':False,
            'gameplayResourcesModified':True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', default=str(GAME))
    parser.add_argument('--mode', choices=['menu','status','preflight','install','rollback'], default='menu')
    args = parser.parse_args()
    try:
        root = Path(args.game)
        if args.mode == 'menu':
            print('R27 passive single-callback observer: 1=status, 2=preflight READ ONLY, 3=install typed, 4=rollback typed, 0=exit')
            answer = input('Choice [2]: ').strip() or '2'
            args.mode = {'0':'exit', '1':'status', '2':'preflight', '3':'install', '4':'rollback'}.get(answer, 'invalid')
        if args.mode == 'exit': print('R27: no changes.'); return 0
        if args.mode == 'status': result = status(root)
        elif args.mode == 'preflight': result = preflight(root)
        elif args.mode == 'install':
            print('R27 INSTALL: only passive override/M_BGXR27.lua, never weapon actions. Closes game and requires external backup.')
            token = input('Type ' + INSTALL_TOKEN + ' exactly (ENTER cancels): ').strip()
            result = install(root, token)
        elif args.mode == 'rollback':
            token = input('Type ' + ROLLBACK_TOKEN + ' exactly (ENTER cancels): ').strip()
            result = rollback(root, token)
        else: raise ValueError('INVALID_MENU_OPTION')
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)); return 0
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(json.dumps({'status':'R27_STOP', 'reason':str(exc),
                          'gameplayResourcesModifiedByFailureNotAssumed':None,
                          'weaponSwitchAuthorized':False}, ensure_ascii=False, indent=2)); return 2

if __name__ == '__main__': sys.exit(main())
