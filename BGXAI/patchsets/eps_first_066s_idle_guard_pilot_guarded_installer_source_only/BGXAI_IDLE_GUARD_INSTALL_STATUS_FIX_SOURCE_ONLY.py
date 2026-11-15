#!/usr/bin/env python3
"""Exact 066S -> idle-guardian Lua-only guarded WeiDU pilot.

SOURCE ONLY. Never auto-installs. Default command is read-only status.
Requires explicit command line confirmation, exact hashes, last WeiDU=066S,
no running game / loader / WeiDU, outside-game verified backup, and verified
post-install state. User must separately authorize trying in their real game.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
BASE = Path(__file__).resolve().parent
ORIGINAL_SHA = '50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
CANDIDATE_SHA = '2bf43c6ce4d607c13ce1aaf5a6af34810e0d4e81e2272c7a37dce384b6413e1a'
BCS_SHA = 'fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'
ORIGINAL_SOURCE = 'M_BX43_066S_VERIFIED_ORIGINAL.lua'
CANDIDATE_SOURCE = 'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua'
BCS = 'override/BDDEFAI.BCS'
LUA = 'override/M_BX43.lua'
WEIDU = 'setup-enhanced-powergaming-scripts.exe'
EXE = 'setup-BGXIDLE.exe'
STAGE = 'BGXIDLE/staged/M_BX43.lua'
TP2 = 'BGXIDLE/setup-BGXIDLE.tp2'
TP2_TEXT = (
    'BACKUP ~BGXIDLE/backup~\n'
    'AUTHOR ~BGXAI 066S idle F-guard guarded pilot (Lua only)~\n'
    'BEGIN ~BGXAI 066S idle guardian preference, reversible test~\n'
    'COPY ~BGXIDLE/staged/M_BX43.lua~ ~override/M_BX43.lua~\n'
)
LAST_066S = re.compile(r'^~(?:[^~]*[/\\])?BGX66S[/\\]SETUP-BGX66S\.TP2~\s+#0\s+#0(?:\s|$)', re.I)
LAST_IDLE = re.compile(r'^~(?:[^~]*[/\\])?BGXIDLE[/\\]SETUP-BGXIDLE\.TP2~\s+#0\s+#0(?:\s|$)', re.I)
BACKUP = ('WeiDU.log', 'chitin.key', 'weidu.conf',
          'lang/ru_RU/dialog.tlk', 'lang/ru_RU/dialogf.tlk', LUA, BCS)
APPROVE_INSTALL = 'INSTALL_BGXAI_IDLE_GUARD'
APPROVE_ROLLBACK = 'ROLLBACK_BGXAI_IDLE_GUARD'

class Stop(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    try:
        return bool(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, FileNotFoundError):
        return False


def check_source() -> dict:
    files = ((ORIGINAL_SOURCE, ORIGINAL_SHA), (CANDIDATE_SOURCE, CANDIDATE_SHA))
    for name, expected in files:
        p = BASE / name
        if is_link(p) or not p.is_file() or digest(p.read_bytes()) != expected:
            raise Stop('SOURCE_HASH_MISMATCH_OR_MISSING:' + name)
    old = (BASE / ORIGINAL_SOURCE).read_bytes()
    candidate = (BASE / CANDIDATE_SOURCE).read_bytes()
    if candidate == old or len(candidate) < len(old):
        raise Stop('NOT_THE_TWO_REGION_CANDIDATE')
    # The release verifier provides the exact line diff / hooks check.
    return {'baseline_lua': ORIGINAL_SHA, 'candidate_lua': CANDIDATE_SHA}


def safe_file(root: Path, rel: str, minimum: int = 1) -> Path:
    if not rel or rel.startswith(('/', '\\')) or ':' in rel or '..' in Path(rel).parts or '\\' in rel:
        raise Stop('UNSAFE_RELATIVE_PATH:' + rel)
    p = root / rel
    if is_link(root):
        raise Stop('GAME_ROOT_REPARSE')
    for part in (p, *p.parents):
        if is_link(part):
            raise Stop('PATH_REPARSE:' + str(part))
        if part == root:
            break
    if not p.is_file() or p.stat().st_size < minimum:
        raise Stop('FILE_MISSING_OR_TOO_SMALL:' + rel)
    return p


def last_mod(root: Path) -> str:
    log = safe_file(root, 'WeiDU.log').read_text(encoding='utf-8-sig', errors='replace')
    lines = [x.strip() for x in log.splitlines() if x.lstrip().startswith('~')]
    if not lines:
        raise Stop('WEIDU_LOG_EMPTY')
    return lines[-1]


def live_hash(root: Path, rel: str, expected: str) -> None:
    got = digest(safe_file(root, rel).read_bytes())
    if got != expected:
        raise Stop('LIVE_HASH_MISMATCH:' + rel + ':' + got)


def verify_baseline(root: Path, *, stage_allowed: bool = False) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir() or is_link(root):
        raise Stop('GAME_ROOT_UNSAFE')
    check_source()
    last = last_mod(root)
    if not LAST_066S.match(last):
        raise Stop('WEIDU_LAST_MUST_BE_066S:' + last)
    live_hash(root, LUA, ORIGINAL_SHA)
    live_hash(root, BCS, BCS_SHA)
    # This must be the genuine prior installed component, not just matching files.
    safe_file(root, 'BGX66S/setup-BGX66S.tp2')
    if not stage_allowed and ((root/'BGXIDLE').exists() or (root/EXE).exists()):
        raise Stop('PILOT_STAGE_ALREADY_PRESENT')
    return {'state': 'BASELINE_066S_VERIFIED', 'last_weidu': last,
            'lua_sha256': ORIGINAL_SHA, 'bcs_sha256': BCS_SHA}


def verify_pilot(root: Path) -> dict:
    root = root.resolve(strict=True)
    check_source()
    last = last_mod(root)
    if not LAST_IDLE.match(last):
        raise Stop('WEIDU_LAST_NOT_PILOT:' + last)
    live_hash(root, LUA, CANDIDATE_SHA)
    live_hash(root, BCS, BCS_SHA)
    live_hash(root, STAGE, CANDIDATE_SHA)
    if safe_file(root, TP2).read_text(encoding='utf-8') != TP2_TEXT:
        raise Stop('PILOT_TP2_DRIFT')
    safe_file(root, EXE, 100_000)
    return {'state': 'PILOT_INSTALLED_VERIFIED', 'last_weidu': last,
            'lua_sha256': CANDIDATE_SHA, 'bcs_sha256': BCS_SHA}


def source_status(root: Path) -> dict:
    last = last_mod(root)
    if LAST_066S.match(last):
        # Status is observational: WeiDU+live SHA are authoritative.
        # WeiDU may leave BGXIDLE staging after a successful rollback.
        state = verify_baseline(root, stage_allowed=True)
        state['stale_stage_detected'] = ((root/'BGXIDLE').exists() or (root/EXE).exists())
        return state
    if LAST_IDLE.match(last):
        return verify_pilot(root)
    raise Stop('UNSUPPORTED_WEIDU_LAST:' + last)


def process_guard() -> None:
    if os.name != 'nt':
        raise Stop('WINDOWS_REQUIRED')
    script = (
        '$ErrorActionPreference="Stop";'
        '$p=Get-CimInstance Win32_Process | '
        'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
        'if($p){$p | ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}; exit 3}'
    )
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=25, check=False)
    if p.returncode or p.stdout.strip():
        raise Stop('GAME_OR_WEIDU_RUNNING_OR_PROCESS_QUERY_FAILED:' + (p.stdout+p.stderr)[-400:])


def make_backup(root: Path, state: dict, label: str, *, parent: Path | None = None) -> Path:
    base = parent or (Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Documents' /
                      'BGXAI_IDLE_GUARD_SAFE_BACKUPS')
    if is_link(base) or is_link(base.parent):
        raise Stop('BACKUP_FOLDER_LINK')
    resolved_game = root.resolve(strict=True)
    resolved_base = base.resolve()
    if resolved_base == resolved_game or resolved_game in resolved_base.parents:
        raise Stop('BACKUP_MUST_BE_OUTSIDE_GAME')
    base.mkdir(parents=True, exist_ok=True)
    dest = base / (label + '_' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    dest.mkdir(exist_ok=False)
    sums = {}
    for rel in BACKUP:
        source = safe_file(root, rel)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        h = digest(source.read_bytes())
        if digest(target.read_bytes()) != h:
            raise Stop('BACKUP_COPY_SHA_MISMATCH:' + rel)
        sums[rel] = h
    manifest = {'state': state, 'sha256': sums, 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    (dest/'BACKUP_PROOF.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    check_backup(dest, root)
    return dest


def check_backup(folder: Path, root: Path) -> None:
    proof = json.loads((folder/'BACKUP_PROOF.json').read_text(encoding='utf-8'))
    if not isinstance(proof.get('sha256'), dict) or set(proof['sha256']) != set(BACKUP):
        raise Stop('BACKUP_PROOF_MALFORMED')
    for rel, expected in proof['sha256'].items():
        p = folder / rel
        if not p.is_file() or digest(p.read_bytes()) != expected:
            raise Stop('BACKUP_PROOF_MISMATCH:' + rel)
        if digest(safe_file(root, rel).read_bytes()) != expected:
            raise Stop('BACKUP_VS_LIVE_MISMATCH:' + rel)


def check_non_targets(saved: Path, root: Path) -> None:
    """Only WeiDU.log and override/M_BX43.lua may change in this pilot."""
    proof = json.loads((saved/'BACKUP_PROOF.json').read_text(encoding='utf-8'))
    for rel in BACKUP:
        if rel in ('WeiDU.log', LUA):
            continue
        if digest(safe_file(root, rel).read_bytes()) != proof['sha256'][rel]:
            raise Stop('UNEXPECTED_NON_TARGET_FILE_MUTATION:' + rel)

def call_weidu(root: Path, *, uninstall: bool = False, runner=subprocess.run) -> dict:
    cmd = [str(root/EXE), '--noautoupdate', '--no-exit-pause', '--game', str(root),
           '--use-lang', 'ru_ru', '--force-uninstall' if uninstall else '--force-install', '0']
    result = runner(cmd, cwd=str(root), stdin=subprocess.DEVNULL,
                    capture_output=True, text=True, encoding='utf-8',
                    errors='replace', timeout=180, check=False)
    out = (result.stdout or '') + '\n' + (result.stderr or '')
    if result.returncode or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)', out):
        raise Stop('WEIDU_FAILED_NO_AUTORETRY:' + out[-1200:])
    return {'returncode': result.returncode, 'stdout_tail': out[-2400:]}


def preflight(root: Path) -> dict:
    state = verify_baseline(root)
    weidu = safe_file(root, WEIDU, 100_000)
    with weidu.open('rb') as handle:
        if handle.read(2) != b'MZ':
            raise Stop('INVALID_WEIDU_BINARY_HEADER')
    for rel in BACKUP:
        safe_file(root, rel)
    return {'status': 'READ_ONLY_PREFLIGHT_PASS', 'baseline': state,
            'candidate_sha256': CANDIDATE_SHA, 'authorized_to_install': False}


def install(root: Path, *, guard=process_guard, backup=make_backup,
            runner=subprocess.run) -> dict:
    guard()
    root = root.resolve(strict=True)
    proof = preflight(root)
    before_log = digest(safe_file(root, 'WeiDU.log').read_bytes())
    saved = backup(root, proof['baseline'], 'PRE_INSTALL')
    if not (saved/'BACKUP_PROOF.json').is_file():
        raise Stop('BACKUP_NOT_VERIFIED')
    guard()
    preflight(root)
    if digest(safe_file(root, 'WeiDU.log').read_bytes()) != before_log:
        raise Stop('WEIDU_LOG_CHANGED_BEFORE_STAGING')
    (root/STAGE).parent.mkdir(parents=True, exist_ok=False)
    (root/STAGE).write_bytes((BASE/CANDIDATE_SOURCE).read_bytes())
    (root/TP2).write_text(TP2_TEXT, encoding='utf-8', newline='\n')
    shutil.copy2(safe_file(root, WEIDU, 100_000), root/EXE)
    live_hash(root, STAGE, CANDIDATE_SHA)
    if safe_file(root, TP2).read_text(encoding='utf-8') != TP2_TEXT:
        raise Stop('STAGED_TP2_MISMATCH')
    guard()
    verify_baseline(root, stage_allowed=True)
    if digest(safe_file(root, 'WeiDU.log').read_bytes()) != before_log:
        raise Stop('WEIDU_LOG_CHANGED_BEFORE_INSTALL')
    outcome = call_weidu(root, runner=runner)
    (saved/'weidu_install_result.json').write_text(json.dumps(outcome, indent=2)+'\n', encoding='utf-8')
    after = verify_pilot(root)
    check_non_targets(saved, root)
    return {'status': 'PILOT_INSTALLED_VERIFIED', 'backup': str(saved), 'after': after}


def rollback(root: Path, *, guard=process_guard, backup=make_backup,
             runner=subprocess.run) -> dict:
    guard()
    root = root.resolve(strict=True)
    before = verify_pilot(root)
    saved = backup(root, before, 'PRE_ROLLBACK')
    guard()
    verify_pilot(root)
    outcome = call_weidu(root, uninstall=True, runner=runner)
    (saved/'weidu_rollback_result.json').write_text(json.dumps(outcome, indent=2)+'\n', encoding='utf-8')
    after = verify_baseline(root, stage_allowed=True)
    check_non_targets(saved, root)
    return {'status': 'RETURNED_TO_066S_VERIFIED', 'backup': str(saved), 'after': after}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='BGXAI 066S guard idle pilot, guarded source-only')
    p.add_argument('mode', nargs='?', choices=('status', 'preflight', 'install', 'rollback'), default='status')
    p.add_argument('--game-root', type=Path, default=ROOT)
    p.add_argument('--yes', action='store_true')
    p.add_argument('--confirm', default='')
    args = p.parse_args(argv)
    try:
        source = check_source()
        if args.mode == 'status':
            print(json.dumps({'mode': 'READ_ONLY_STATUS', 'source': source,
                              'game': source_status(args.game_root)}, ensure_ascii=False, indent=2))
            return 0
        if args.mode == 'preflight':
            print(json.dumps(preflight(args.game_root), ensure_ascii=False, indent=2))
            return 0
        phrase = APPROVE_INSTALL if args.mode == 'install' else APPROVE_ROLLBACK
        if not args.yes or args.confirm != phrase:
            raise Stop('EXPLICIT_APPROVAL_REQUIRED:' + phrase)
        if os.name != 'nt' or args.game_root != ROOT:
            raise Stop('LIVE_MUTATION_ONLY_ON_CONFIRMED_WINDOWS_GAME_ROOT')
        result = install(ROOT) if args.mode == 'install' else rollback(ROOT)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Stop, OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as e:
        print('BGXAI_IDLE_GUARD_STOP:', str(e))
        return 2

if __name__ == '__main__':
    sys.exit(main())
