#!/usr/bin/env python3
"""Static hash/signature checker. No installation, game interaction or hidden network."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest_sha256.json').read_text('utf-8'))
for name,expected in manifest['files'].items():
    got=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    if got!=expected:raise SystemExit('SHA_MISMATCH '+name)
print('BGXAI081 source SHA: %d/%d PASS'%(len(manifest['files']),len(manifest['files'])))
script=(ROOT/'BGXAI081_ACTION_PROVENANCE_READONLY.lua').read_text('utf-8')
for danger in ('setLocalInt','ClearActions','AttackReevaluate','ProtectObject','Spell(', 'EEex_Action_AddSpriteStartedActionListener', 'EEex_Sprite_AddBlockWeaponHitListener','os.','io.'):
    if danger in script:raise SystemExit('FORBIDDEN_LUA_COMMAND '+danger)
checker=(ROOT/'audit_live_081.py').read_text('utf-8')
for danger in ('write_bytes(', 'write_text(', 'os.system(', 'subprocess.run('):
    if danger in checker:raise SystemExit('FORBIDDEN_PYTHON_COMMAND '+danger)
print('BGXAI081 NO_GAME_WRITE: PASS')
