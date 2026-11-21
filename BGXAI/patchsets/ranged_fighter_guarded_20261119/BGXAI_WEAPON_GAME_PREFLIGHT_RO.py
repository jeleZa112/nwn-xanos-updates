#!/usr/bin/env python3
"""BGXAI weapon exact-quickslot native EET preflight. NO GAME WRITES.

Read actual override/2DA/WeiDU status, compile the V3 slot consumer with real
EET IDS in a TEMP directory, and report the remaining EEex runtime gaps.
No Lua injection, EEex callbacks, IDS/ITM modifications, BCS install or rollback.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

EXPECTED_GAME = r'C:\Games\BG_EET_FOXX_NEW'
EXPECTED_BAF_SHA = 'f95086c3bb629aa482a8f99443fee577176b2612393be7ffac0f530c2898bf18'
WEIDU_BINARY = 'setup-enhanced-powergaming-scripts.exe'
READ_ONLY_TARGETS = (
    'chitin.key', 'WeiDU.log', 'override/DPLAYER.BCS',
    'override/BDDEFAI.BCS', 'override/WTASIGHT.BCS',
    'override/PRIEST1.BCS', 'override/M_BX43.lua',
    'override/M_BXFR.lua', 'override/WSPATCK.2DA',
    'override/CLSWPBON.2DA',
)
V6_DPLAYER_EXPECTED = '4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_read(root: Path, name: str, max_size=40_000_000) -> dict:
    p = root / name
    if p.is_symlink():
        return {'state': 'SYMLINK_BLOCKED'}
    if not p.exists():
        return {'state': 'NOT_IN_OVERRIDE_OR_MISSING'}
    if not p.is_file():
        return {'state': 'NOT_REGULAR_FILE'}
    try:
        if p.stat().st_size > max_size:
            return {'state': 'OVERSIZED'}
        data = p.read_bytes()
        if len(data) > max_size:
            return {'state': 'OVERSIZED'}
        return {'state': 'READ', 'sha256': digest(data), 'bytes': len(data)}
    except OSError as e:
        return {'state': 'READ_ERROR', 'reason': type(e).__name__}


def verify_baf(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError('V3_BAF_SOURCE_MISSING_OR_LINK')
    data = path.read_bytes()
    if digest(data) != EXPECTED_BAF_SHA:
        raise ValueError('V3_BAF_SOURCE_SHA_DRIFT')
    text = data.decode('utf-8-sig')
    blocks = re.split(r'(?m)^IF\s*$', text)
    if len(blocks) != 5 or text.count('THEN') != 4 or text.count('END') != 4:
        raise ValueError('V3_BAF_BLOCK_SHAPE_CHANGED')
    for slot in range(4):
        if text.count(f'SelectWeaponAbility(SLOT_WEAPON{slot},0)') != 1:
            raise ValueError('V3_SLOT_SELECT_NOT_EXACT')
        if text.count(f'HasItemSlot(Myself,SLOT_WEAPON{slot})') != 1:
            raise ValueError('V3_SLOT_OCCUPANCY_GUARD_MISSING')
    if re.search(r'\b(?:Stop|ClearActions|Attack|ForceSpell|CreateItem|MoveToPoint)\s*\(', text, re.I):
        raise ValueError('V3_BAF_ACTION_NOT_SLOT_ONLY')
    return {'state': 'SOURCE_SHA_VERIFIED', 'sha256': digest(data), 'blocks': 4}


def run_native(root: Path, source: Path, weidu: Path, runner=subprocess.run) -> dict:
    if weidu.is_symlink() or not weidu.is_file():
        return {'state': 'HOLD_WEIDU_BINARY_MISSING'}
    try:
        with weidu.open('rb') as handle:
            mz = handle.read(2)
        if weidu.stat().st_size > 70_000_000 or mz != b'MZ':
            return {'state': 'HOLD_WEIDU_NOT_VALID_WINDOWS_EXE'}
    except OSError:
        return {'state': 'HOLD_WEIDU_READ_ERROR'}
    with tempfile.TemporaryDirectory(prefix='BGXAI_WEAPON_V3_RO_') as folder:
        tmp = Path(folder)
        exe = tmp / 'weidu.exe'
        baf = tmp / 'BGXW3.BAF'
        result = tmp / 'BGXW3.BCS'
        shutil.copyfile(weidu, exe)
        baf.write_bytes(source.read_bytes())
        cmd = [str(exe), '--game', str(root), '--out', str(result), str(baf)]
        try:
            p = runner(cmd, cwd=tmp, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, errors='replace', timeout=180)
        except (OSError, subprocess.TimeoutExpired) as e:
            return {'state': 'NATIVE_COMPILE_FAILED', 'reason': type(e).__name__}
        logs = ((p.stdout or '') + '\n' + (p.stderr or ''))[-1600:]
        if p.returncode != 0 or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)', logs):
            return {'state': 'NATIVE_COMPILE_FAILED', 'returncode': p.returncode,
                    'reason': logs[-700:]}
        if result.is_symlink() or not result.is_file():
            return {'state': 'NATIVE_COMPILE_FAILED', 'reason': 'MISSING_BCS'}
        contents = result.read_bytes()
        if not contents or len(contents) > 200_000:
            return {'state': 'NATIVE_COMPILE_FAILED', 'reason': 'BAD_BCS_SIZE'}
        return {'state': 'NATIVE_COMPILED_TEMP_ONLY', 'sha256': digest(contents),
                'bytes': len(contents)}


def audit(root: Path, source: Path, *, fixture=False, runner=subprocess.run) -> dict:
    if not fixture and (os.name != 'nt' or os.path.normcase(str(root.resolve())) !=
                        os.path.normcase(os.path.normpath(EXPECTED_GAME))):
        raise ValueError('EXPECTED_WINDOWS_GAME_ROOT_REQUIRED')
    if root.is_symlink() or not root.is_dir():
        raise ValueError('GAME_ROOT_NOT_REGULAR_DIRECTORY')
    source_evidence = verify_baf(source)
    before = {n: safe_read(root, n) for n in READ_ONLY_TARGETS}
    if before['chitin.key']['state'] != 'READ':
        raise ValueError('GAME_CHITIN_KEY_MISSING')
    if before['WeiDU.log']['state'] != 'READ':
        raise ValueError('WEIDU_LOG_MISSING')
    target = before['override/DPLAYER.BCS']
    installed = ('V6_DPLAYER_BINARY_EXACT' if
                 target.get('sha256') == V6_DPLAYER_EXPECTED else 'V6_INSTALL_NOT_CONFIRMED')
    native = run_native(root, source, root / WEIDU_BINARY, runner=runner)
    after = {n: safe_read(root, n) for n in READ_ONLY_TARGETS}
    same = before == after
    return {
        'schema': 'BGXAI_WEAPON_NATIVE_GAME_READONLY_V1',
        'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'game_root': str(root), 'source': source_evidence,
        'v6_status': installed, 'weidu_compile': native,
        'game_files_unchanged': same,
        'resources': before,
        'installed_2da_available_in_override': {
            n: before['override/' + n]['state'] == 'READ'
            for n in ('WSPATCK.2DA', 'CLSWPBON.2DA')
        },
        'limits': {
            'biFF_2da_contents_read': False,
            'live_eeex_character_stats_read': False,
            'all_four_weapon_item_stats_read': False,
            'eps_and_manual_queue_proven_empty': False,
            'priority_weapon_switch_executed': False,
            'game_modified': not same,
        },
        'status': ('READONLY_NATIVE_PREFLIGHT_PASS' if same and
                   native['state'] == 'NATIVE_COMPILED_TEMP_ONLY' else
                   'READONLY_PREFLIGHT_INCOMPLETE_OR_STOP'),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', required=True)
    args = ap.parse_args()
    root = Path(args.game)
    source = Path(__file__).with_name('BGXAI_WEAPON_GAME_PREFLIGHT_V1.baf')
    try:
        report = audit(root, source)
    except Exception as exc:
        report = {'schema': 'BGXAI_WEAPON_NATIVE_GAME_READONLY_V1',
                  'status': 'READONLY_PREFLIGHT_STOP',
                  'reason': f'{type(exc).__name__}: {exc}',
                  'game_modified_by_this_program': False}
    base = os.environ.get('LOCALAPPDATA')
    reportdir = Path(base) / 'BGXAI_UPDATER' / 'reports' if base else Path(tempfile.gettempdir()) / 'BGXAI_UPDATER' / 'reports'
    try:
        reportdir.mkdir(parents=True, exist_ok=True)
        target = reportdir / 'BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json'
        target.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
        print('REPORT_FILE: ' + str(target))
    except OSError as exc:
        print('REPORT_WRITE_ERROR: '+str(exc))
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2
    print('STATUS: ' + report['status'])
    print('WEIDU: ' + report.get('weidu_compile', {}).get('state', 'NOT_RUN'))
    print('GAME_FILES_UNCHANGED: ' + str(report.get('game_files_unchanged', 'NOT_CHECKED')))
    return 0 if report['status'] == 'READONLY_NATIVE_PREFLIGHT_PASS' else 2


if __name__ == '__main__':
    sys.exit(main())
