#!/usr/bin/env python3
"""Reproduce 066S snapshot->080 source bridge using byte-pinned existing repo files.
No game access, network, updater, or installation.
"""
from pathlib import Path
import hashlib, os, shutil, subprocess, tempfile

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ["BGXAI_REPO_ROOT"]) if os.environ.get("BGXAI_REPO_ROOT") else HERE.parents[2]
# In a real checkout: /repo/BGXAI/patchsets/<patchset>/run_bridge_tests.py -> /repo.

def gitblob(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

EXISTING = {
    'M_BX43_066S_VERIFIED_ORIGINAL.lua': (
        'BGXAI/fox_new/experimental_066s_guarded_install_candidate/M_BX43_066S_CASTER_CANDIDATE.lua',
        '7a02e47a02abd534d385dc1a49a1892dc44eaff0'),
    'BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua': (
        'BGXAI/patchsets/eps_first_multi_threat_guard_source_only/BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua',
        'f9c39f3190a005da77eb6dea4720dc93e44d5d8e'),
    'BGXAI072_EPS_FIRST_ARBITER.lua': (
        'BGXAI/fox_new/experimental_080_eps_first_buff_preserving_coordinator_source_only/BGXAI072_EPS_FIRST_ARBITER.lua',
        '23e5f992c572dc12b96c7e303cb7916957cd7e5a'),
    'BGXAI082_QUEUE_GUARD_BRIDGE.lua': (
        'BGXAI/fox_new/experimental_082_eps_080_081_failclosed_integration_source_only/BGXAI082_QUEUE_GUARD_BRIDGE.lua',
        '4f89a15b26e258179806e4474596d3e74dd6aaba'),
}
NEW_FILES = ['BGXAI066S_080_CONFIRMED_HIT_BRIDGE_SOURCE_ONLY.lua',
             'test_066s_snapshot_bridge.lua', 'test_real_066s_snapshot.lua']

def main():
    lua = shutil.which('texlua')
    if not lua: raise RuntimeError('texlua missing')
    source=(HERE/NEW_FILES[0]).read_bytes().decode('utf-8')
    forbidden=['setLocalInt(', 'ClearActions(', 'ProtectObject(', 'Spell(', 'Attack(',
               'EEex_Action_AddSpriteStartedActionListener(', 'EEex_Sprite_AddBlockWeaponHitListener(',
               'os.execute(', 'io.open(']
    # Scan executable Lua code, not explanatory comment lines.
    program='\n'.join(x for x in source.splitlines() if not x.lstrip().startswith('--'))
    for needle in forbidden:
        if needle in program: raise RuntimeError('UNEXPECTED_GAME_ACTION: '+needle)
    with tempfile.TemporaryDirectory(prefix='bgxai_hit_bridge_') as folder:
        d=Path(folder)
        for name in NEW_FILES: shutil.copy2(HERE/name,d/name)
        for name,(rel,blob) in EXISTING.items():
            p=ROOT/rel
            raw=p.read_bytes()
            if gitblob(raw)!=blob: raise RuntimeError('HISTORICAL_SOURCE_BLOB_MISMATCH: '+str(p))
            if name=='M_BX43_066S_VERIFIED_ORIGINAL.lua' and hashlib.sha256(raw).hexdigest()!=\
              '50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f':
                raise RuntimeError('066S_INSTALLED_BASELINE_SHA_MISMATCH')
            (d/name).write_bytes(raw)
        for name in NEW_FILES[1:]:
            v=subprocess.run([lua,name],cwd=d,capture_output=True,text=True,timeout=25)
            if v.returncode: raise RuntimeError(f'{name} failed:\n{v.stdout}\n{v.stderr}')
            print(v.stdout.strip())
        print('BGXAI_BRIDGE_REPLAY_PASS; 066S exact; 080/072/082 exact; game untouched')
if __name__=='__main__': main()
