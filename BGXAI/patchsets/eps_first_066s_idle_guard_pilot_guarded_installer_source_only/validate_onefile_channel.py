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
    ('BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/', '0.3.50-BGX122-IDS-HYPHEN', 13),
    ('BGXAI/patchsets/ranged_fighter_guarded_20261119/', '0.3.52-BGXRANGED-GUARDED', 3),
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
    # The single CMD remains the only launcher; the change is an exact fail-closed
    # embedded-bootstrap recovery for one already proven stale immutable pin.
    old_cmd = git_bytes(OLD_COMMIT, CMD)
    new_cmd = git_bytes('HEAD', CMD)
    marker = bytes([32]*8) + b"$scriptSources=@(" + bytes([13,10])
    assert old_cmd.count(marker) == 1 and new_cmd.count(marker) == 1, 'CMD bootstrap marker drift'
    old_prefix, old_suffix = old_cmd.split(marker)
    assert new_cmd.startswith(old_prefix) and new_cmd.endswith(marker + old_suffix), 'one CMD changed outside pin recovery block'
    recovery = new_cmd[len(old_prefix):-len(marker + old_suffix)]
    assert sha(new_cmd) == '6a94650e2f9e5eda242f4d8a0dd5d84545fbee63906cc3a3e19b2b068bd3b585', 'one CMD full SHA drift'
    for token in (b'711840d55df51c86da9b9464aa2bc22b882cfa1e',
                  b'0c01f9f5c56087b1ff39471c3a06a1409cfe2a14',
                  b'96dcda9cf91d921e9a37d67f7c382b6ba2abe394',
                  b'a77fbae9579d3c192cca3269dae25e0a1b3b2610995e3a97acf5197b65554f39'):
        assert token in recovery, 'one CMD recovery expected SHA or commit absent'
    oldmenu, oldcase = menus(old)
    menu, case = menus(live)
    assert len(oldmenu) == 97 and len(menu) == 127, 'menu length mismatch'
    assert len(oldcase) == 96 and len(case) == 126, 'dispatch length mismatch'
    assert [int(re.search(r"'(\s*\d+) -", item).group(1)) for item in menu[:-1]] == list(range(1,127)) and menu[-1] == oldmenu[-1], 'menu numbering changed'
    assert case[:96] == oldcase, 'old dispatch 1..96 changed'
    code = live.decode('utf-8-sig')
    for n in range(97,117):
        assert any(re.match(rf"Write-Host '\s*{n} - ", x) for x in menu), f'menu {n} missing'
        assert case[n-1].startswith(f"'{n}' {{BGXOneFileManaged"), f'dispatch {n} wrong'
    assert case[116].startswith("'117' {BGXAOEReadOnly;break}"), '117 must run AOE READ ONLY'
    assert case[117].startswith("'118' {BGXTest6Safe;break}"), '118 gated clone only'
    assert case[118].startswith("'119' {SyncRelease $releaseAOE;& py -3"), '119 must use verified READ ONLY script trace'
    assert case[119].startswith("'120' {SyncRelease $releaseAOE;& py -3"), '120 guarded native Entangle installer missing'
    assert case[120].startswith("'121' {SyncRelease $releaseAOE;& py -3"), '121 read-only AOE spatial audit missing'
    assert case[121].startswith("'122' {SyncRelease $releaseAOE;& py -3"), '122 read-only modded projectile EFF audit missing'
    assert case[122].startswith("'123' {SyncRelease $releaseRanged;& py -3"), '123 ranged preflight missing'
    assert case[123].startswith("'124' {SyncRelease $releaseRanged;& py -3"), '124 guarded install missing'
    assert case[124].startswith("'125' {SyncRelease $releaseRanged;& py -3"), '125 ranged status missing'
    assert case[125].startswith("'126' {SyncRelease $releaseRanged;& py -3"), '126 guarded rollback missing'
    assert "function BGXAOEReadOnly" in code and "SyncRelease $releaseAOE" in code
    assert "function BGXTest6Safe" in code and "CREATE_BGXAI_TEST6_NO_PRIEST1" in code
    aoe_chunks = code.split("$releaseAOE=@{")
    assert len(aoe_chunks) == 2, 'AOE117/118 release spec absent or duplicated'
    assert aoe_chunks[1].startswith("\nid='AOE117';version='"), 'AOE117/118 spec shape drift'
    aoe_spec_version = aoe_chunks[1].split("version='", 1)[1].split("'", 1)[0]
    expected_aoe_version = next(v for d,v,n in RELEASES if d.endswith('/aoe_entangle_readonly_onefile_20261117/'))
    assert aoe_spec_version == expected_aoe_version, 'AOE117/118 SCRIPT VERSION DOES NOT MATCH MANIFEST'
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
    print('BGXAI_ONEFILE_CHANNEL_PASS: legacy 1-96 unchanged, new 97-126; 74/74 source hashes; pin matched; game untouched')

if __name__ == '__main__':
    main()
