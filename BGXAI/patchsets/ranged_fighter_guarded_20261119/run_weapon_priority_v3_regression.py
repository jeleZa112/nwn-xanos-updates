#!/usr/bin/env python3
"""Repository SOURCE-only V3/V4/V5/NONINTERRUPT regressions, never touches game."""
from __future__ import annotations
import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CODE = 'BGXAI_WEAPON_PRIORITY_LUA_V3.lua'
TEST = 'test_weapon_priority_lua_v3.lua'


def _static() -> None:
    s = (ROOT / CODE).read_text(encoding='utf-8')
    assert s.startswith('-- BGXAI priority weapon selection V3')
    # The ineligibility fix must remain advisory. No executable engine commands
    # or IO are allowed in the V3 source, even if future refactors add them.
    for forbidden in ('SelectWeaponAbility(', 'Attack(', 'ClearActions(',
                      'ActionOverride(', 'SetGlobal(', 'EEex_Action_Queue',
                      'io.open(', 'os.execute('):
        assert forbidden not in s, forbidden
    for proof in ('VERIFIED_EMPTY_AMMUNITION', 'VERIFIED_NO_SAFE_MELEE_PATH',
                  'VERIFIED_UNSAFE_TO_TANK', 'HOLD_UNRANKABLE_OCCUPIED_WEAPON',
                  'currentUnusableReason', "dispatchAuthorized=false"):
        assert proof in s, proof
    assert "not between(weapon.ammoCount,0,1000000)" in s
    # Verify every executable Lua module in the advisory chain, not only V3.
    # Ignore comments (which intentionally document forbidden engine APIs).
    other = (
        'BGXAI_WEAPON_EFFECTS_V4.lua',
        'BGXAI_WEAPON_APR_PROVENANCE_V5.lua',
        'BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua',
        'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua',
    )
    for name in (CODE,) + other:
        source = (ROOT / name).read_text(encoding='utf-8')
        active = '\n'.join(line.split('--', 1)[0] for line in source.splitlines())
        for pattern in (r'\bSelectWeaponAbility\s*\(', r'\bAttack\s*\(',
                        r'\bClearActions\s*\(', r'\bActionOverride\s*\(',
                        r'\bSetGlobal\s*\(', r'\bEEex_Action_Queue',
                        r'\bio\.open\s*\(', r'\bos\.execute\s*\('):
            assert not re.search(pattern, active), (name, pattern)
    # Preserve original BCS consumer and verify restricted native fallback source.
    # This is NOT a WeiDU compile or installation approval.
    baf = subprocess.run([sys.executable, str(ROOT / 'test_weapon_native_recovery_baf_v1.py')],
                         cwd=ROOT, capture_output=True, text=True, timeout=10)
    if baf.returncode != 0 or 'PASS BAF NATIVE RECOVERY 8/8' not in baf.stdout:
        raise RuntimeError('BAF native recovery source check failed: '+baf.stdout+baf.stderr)
    print(baf.stdout.strip())
    # The native EET compile preflight is SOURCE-ONLY. Its 20 contract tests
    # simulate WeiDU and verify safety/rollbacks, never the user's real game.
    native = subprocess.run([sys.executable, str(ROOT / 'test_weapon_native_compile_ro_v1.py')],
                            cwd=ROOT, capture_output=True, text=True, timeout=20)
    check = re.search(r'PASS NATIVE BAF COMPILER CONTRACT (\d+)/(\d+) SOURCE-ONLY CHECKS; (\d+) SKIPPED', native.stdout)
    if (native.returncode != 0 or not check or
        int(check.group(1)) != int(check.group(2)) or
        int(check.group(1))+int(check.group(3)) != 21 or
        int(check.group(1)) < 19):
        raise RuntimeError('Native read-only preflight contract failed: '+native.stdout+native.stderr)
    print(check.group(0))
    print('PASS V3/V4/V5/CURRENT-STATS/NONINTERRUPT STATIC NO-ENGINE-ACTIONS and UNKNOWN-FAIL-CLOSED')


def _lua(lua: str) -> None:
    with tempfile.TemporaryDirectory(prefix='bgxai_weapon_v3_source_') as tmp:
        root = Path(tmp)
        p3 = root / 'BGXAI_WEAPON_PRIORITY_V3'
        p4 = root / 'BGXAI_WEAPON_PRIORITY_V4'
        p5 = root / 'BGXAI_WEAPON_APR_PROVENANCE_V5'
        for p in (p3, p4, p5):
            p.mkdir()
        for name in (CODE, TEST):
            shutil.copy2(ROOT / name, p3 / name)
        for name in ('BGXAI_WEAPON_EFFECTS_V4.lua', 'test_weapon_effects_v4.lua'):
            shutil.copy2(ROOT / name, p4 / name)
        for name in ('BGXAI_WEAPON_APR_PROVENANCE_V5.lua', 'test_weapon_apr_provenance_v5.lua'):
            shutil.copy2(ROOT / name, p5 / name)
        suites = [
            (p3 / TEST, r'PASS WEAPON PRIORITY NATIVE LUA 72/72 SOURCE ONLY'),
            (p4 / 'test_weapon_effects_v4.lua', r'PASS TOTAL 34 / 34 NATIVE LUA SOURCE ONLY'),
            (p5 / 'test_weapon_apr_provenance_v5.lua', r'PASS APR V5 25/25 OFFLINE SOURCE ONLY'),
            (ROOT / 'test_weapon_noninterrupt_plan_v1.lua', r'PASS NONINTERRUPT SCHEDULER 26/26 SOURCE ONLY'),
            (ROOT / 'test_weapon_noninterrupt_integration_v1.lua', r'PASS REAL WEAPON PIPELINE INTEGRATION 11/11 OFFLINE'),
            (ROOT / 'test_weapon_failclosed_matrix_v1.lua', r'PASS WEAPON MATRIX 288/288 READONLY CASES SOURCE ONLY'),
            (ROOT.parents[2] / 'BGXAI/BUILD/WEAPON_INVENTORY_PRIORITY_V4_20261126/test_backpack16_priority_v4.lua',
             r'BGXAI BACKPACK16 PRIORITY V4 42 synthetic tests PASS')
        ]
        passed = 0
        for path, marker in suites:
            run_cwd = ROOT.parents[2] if path.name == 'test_backpack16_priority_v4.lua' else ROOT
            result = subprocess.run(([lua, '--luaonly'] if Path(lua).name.lower().startswith('luatex') else [lua]) + [str(path)], cwd=run_cwd, text=True,
                                    capture_output=True, check=False, timeout=20)
            if result.returncode != 0 or marker not in result.stdout:
                print(result.stdout, file=sys.stderr)
                print(result.stderr, file=sys.stderr)
                raise RuntimeError(f'Lua regression failed: {path.name} ({result.returncode})')
            if path.name == 'test_weapon_failclosed_matrix_v1.lua':
                count = 288 # Cross-product scenarios, not 288 game-play cases.
            elif path.name == 'test_backpack16_priority_v4.lua':
                count = 42 # Real Lua model tests; footer has no 'PASS ' prefix.
            else:
                count = len(re.findall(r'^PASS ', result.stdout, re.M)) - 1
            print(f'PASS {path.name}: {count} offline tests / matrix cases')
            passed += count
        assert passed == 498, passed
        print(f'PASS TOTAL {passed}/498 OFFLINE LUA TESTS AND MATRIX CASES; NO GAME DEPLOY')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--static-only', action='store_true')
    parser.add_argument('--lua', default=None)
    args = parser.parse_args()
    _static()
    if not args.static_only:
        selected = args.lua or next((c for c in ('lua5.3','lua5.4','lua','luatex') if shutil.which(c)), None)
        if not selected:
            raise RuntimeError('Lua 5.3/5.4 or LuaTeX required for native regression')
        args.lua = selected
        _lua(selected)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f'SOURCE_REGRESSION_HOLD: {error}', file=sys.stderr)
        sys.exit(1)