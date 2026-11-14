#!/usr/bin/env python3
"""Offline integrity and non-install release gates; no live game access."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
m=json.loads((HERE/'manifest_sha256.json').read_text())
for name,digest in m['files'].items():
    got=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
    if got!=digest:raise SystemExit('SHA_MISMATCH '+name+' got='+got)
# Compare exact originals (imported copies, not modified).
assert m['files']['BGXAI078_HEAL_SELECTOR.lua']=='8369e1c5fd88774a3b26cbe419c09271dfaa2ce76fb4b1f92646c2b515b106f8'
assert m['files']['BGXAI072_EPS_FIRST_ARBITER.lua']=='a8ef70e8d74fc61b54a8eb439686993f33c7e9685771e75778484591e4619ae4'
for name in ('BGXAI080_EPS_FIRST_COORDINATOR.lua','audit_eps_buff_080.py'):
    src=(HERE/name).read_text()
    bad=('setLocalInt(', 'ClearActions(', 'Spell(', 'AttackReevaluate(',
         'EEex_Action_AddSpriteStartedActionListener(', 'EEex_Sprite_AddBlockWeaponHitListener(')
    for pattern in bad:
        if pattern in src:raise SystemExit('FORBIDDEN_ENGINE_OPERATION '+name+': '+pattern)
print('BGXAI 080 SHA '+str(len(m['files']))+'/'+str(len(m['files']))+' PASS; NO_ENGINE_WRITE PASS')
