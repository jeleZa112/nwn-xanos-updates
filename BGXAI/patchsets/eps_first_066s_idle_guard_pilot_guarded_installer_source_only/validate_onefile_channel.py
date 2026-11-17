#!/usr/bin/env python3
"""Offline BGXAI one-file updater: immutable base, current pin, three new exact releases.
CI only: reads Git objects; NEVER executes game installers or alters EET.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = 'BGXAI/BGXAI_SYNC.ps1'
CMD = 'BGXAI_UPDATE.cmd'
PIN = 'BGXAI/fox_new/BOOTSTRAP_PIN.json'
OLD_COMMIT = '9ad7249c768bc4770e5adb5b8582d8c0184e32b7'
OLD_SHA = 'bc4b176aaed83852e597cef8b2cc168b9732fbfa31bbb79ca6442b854351a466'
RELEASES = (
    ('BGXAI/patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only/', '0.3.36-066S-IDLE-GUARD-PILOT', 19),
    ('BGXAI/patchsets/priest_modes_eps_first_installable_20261116/', '0.3.37-BGXPR-ONEFILE', 9),
    ('BGXAI/patchsets/team_f_guard_066s_installable_pilot_20261116/', '0.3.38-BGXTEAM-ONEFILE', 3),
    ('BGXAI/patchsets/priest_combat_eps_first_20261116/', '0.3.39-BGXP2-COMBAT-PRIEST', 7),
    ('BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/', '0.3.40-BGXP3-AUTO-BUFFER', 9),
    ('BGXAI/patchsets/priest_auto_priority_guard_source_20261117/', '0.3.41-BGXP5-AUTO-PRIORITY-GUARD', 11),
    ('BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/', '0.3.44-BGXAOE-SAFE-SAVECOPY', 5),
)

def git_bytes(rev: str, path: str) -> bytes:
    p = subprocess.run(['git', 'show', f'{rev}:{path}'], cwd=ROOT, capture_output=True, check=False)
    if p.returncode:
        raise AssertionError(f'missing Git object {rev}:{path}: {p.stderr[-200:]!r}')
    return p.stdout

def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

def menus(raw: bytes):
    text = raw.decode('utf-8-sig')
    labels = [s.strip() for s in text.splitlines() if re.match(r"^\s*Write-Host '\s*\d{1,3} - ", s)]
    choices = [s.strip() for s in text.splitlines() if re.match(r"^\s*'\d{1,3}' \{", s)]
    return labels, choices

def main():
    old = git_bytes(OLD_COMMIT, SCRIPT)
    assert len(old) == 74220 and sha(old) == OLD_SHA, 'prior live updater drift'
    live = git_bytes('HEAD', SCRIPT)
    pin = json.loads(git_bytes('HEAD', PIN))
    assert pin['schema'] == 1 and pin['channel'] == 'bgxai-fox-new-onefile'
    assert pin['branch'] == 'bg-eet-ai' and pin['script_path'] == SCRIPT
    assert re.fullmatch(r'[0-9a-f]{40}', pin['commit'])
    assert pin['script_sha256'] == sha(live)
    assert pin['script_size'] == len(live) and len(live) <= 80000
    assert git_bytes(pin['commit'], SCRIPT) == live, 'immutable pin differs from HEAD'
    assert git_bytes('HEAD', CMD) == git_bytes(OLD_COMMIT, CMD), 'one CMD was replaced'
    oldmenu, oldcase = menus(old)
    menu, case = menus(live)
    assert len(oldmenu) == 97 and len(menu) == 119, 'menu length mismatch'
    assert len(oldcase) == 96 and len(case) == 118, 'dispatch length mismatch'
    assert menu[:96] == oldmenu[:96] and menu[-1] == oldmenu[-1], 'old menu 1..96 changed'
    assert case[:96] == oldcase, 'old dispatch 1..96 changed'
    code = live.decode('utf-8-sig')
    for n in range(97,117):
        assert any(re.match(rf"Write-Host '\s*{n} - ", x) for x in menu), f'menu {n} missing'
        assert case[n-1].startswith(f"'{n}' {{BGXOneFileManaged"), f'dispatch {n} wrong'
    assert case[116].startswith("'117' {BGXAOEReadOnly;break}"), '117 must run AOE READ ONLY'
    assert case[117].startswith("'118' {BGXTest6Safe;break}"), '118 gated clone only'
    assert "function BGXAOEReadOnly" in code and "SyncRelease $releaseAOE" in code
    assert "function BGXTest6Safe" in code and "CREATE_BGXAI_TEST6_NO_PRIEST1" in code
    aoe_spec = re.search(r"\\$releaseAOE=@\\{\\s*id='AOE117';version='([^']+)';", code)
    assert aoe_spec is not None, 'AOE117/118 release spec absent'
    expected_aoe_version = next(v for d,v,n in RELEASES if d.endswith('/aoe_entangle_readonly_onefile_20261117/'))
    assert aoe_spec.group(1) == expected_aoe_version, 'AOE117/118 SCRIPT VERSION DOES NOT MATCH MANIFEST'
    assert "'--game' $GameRoot" in code and "AOE117 READ-ONLY STOP" in code
    for key in ('INSTALL_BGXPRIEST_MODES','ROLLBACK_BGXPRIEST_MODES',
                'INSTALL_BGXAI_TEAM_GUARD','ROLLBACK_BGXAI_TEAM_GUARD',
                'INSTALL_BGXP2_COMBAT_PRIEST','ROLLBACK_BGXP2_COMBAT_PRIEST',
                'INSTALL_BGXP3_AUTO_BUFFER','ROLLBACK_BGXP3_AUTO_BUFFER',
                'INSTALL_BGXP5_EARLY_HEAL_SAFE','ROLLBACK_BGXP5_EARLY_HEAL_SAFE',
                'function BGXOneFileManaged', 'SyncRelease $spec',
                "'--yes' '--confirm' $token", 'AssertNotReparse $file'):
        assert key in code, f'guard missing: {key}'
    m = re.search(r"\$remotePath -notmatch '([^']+)'", code)
    assert m, 'remote source allowlist missing'
    whitelist = re.compile(m.group(1), re.IGNORECASE)
    assert not whitelist.fullmatch('BGXAI/other/evil.ps1')
    assert "-or $remotePath.Contains('..')" in code
    for directory, version, count in RELEASES:
        path = directory + 'manifest_updater.json'
        assert whitelist.fullmatch(path), f'manifest source blocked: {path}'
        data = git_bytes(pin['commit'], path)
        manifest = json.loads(data)
        assert manifest['schema'] == 1 and manifest['channel'] == 'bgxai-fox-new-safe-source'
        assert manifest['version'] == version and len(manifest['files']) == count
        seen = set()
        for f in manifest['files']:
            name = f['dest']
            assert re.fullmatch(r'[A-Za-z0-9_.-]+', name) and name not in seen
            seen.add(name)
            assert f['source'] == directory+name and whitelist.fullmatch(f['source'])
            original = git_bytes(pin['commit'], f['source'])
            assert len(original) == f['size'] and sha(original) == f['sha256'], f'bad source: {name}'
            assert f"'{name}'" in code, f'updater source absent: {name}'
    print('BGXAI_ONEFILE_CHANNEL_PASS: legacy 1-96 unchanged, new 97-118; 63/63 source hashes; pin matched; game untouched')

if __name__ == '__main__':
    main()
