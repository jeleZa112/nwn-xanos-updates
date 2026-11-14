"""No-install package source integrity verifier for BGXAI078."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
obj=json.loads((ROOT/'manifest_sha256.json').read_text('utf-8'))
for name,want in obj['files'].items():
 path=ROOT/name
 got=hashlib.sha256(path.read_bytes()).hexdigest()
 if got!=want: raise SystemExit(f'FAIL SHA: {name}: {got}')
 print('SHA PASS:',name)
s=(ROOT/'BGXAI078_HEAL_SELECTOR.lua').read_text()
for key in ('setLocalInt','SetGlobal(', 'AttackReevaluate(', 'Spell(', 'ClearActions(', 'ProtectObject(', 'EEex_'):
 if key in s:raise SystemExit('FAIL source-only: '+key)
print('BGXAI078_SOURCE_ONLY_RELEASE_PASS')
