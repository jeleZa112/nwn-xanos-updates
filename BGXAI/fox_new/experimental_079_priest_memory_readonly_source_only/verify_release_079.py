import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
m=json.loads((R/'manifest_sha256.json').read_text())
for name,want in m['files'].items():
 got=hashlib.sha256((R/name).read_bytes()).hexdigest()
 if got!=want:raise SystemExit('SHA ERROR '+name)
 print('SHA PASS',name)
s=(R/'BGXAI079_PRIEST_MEMORY_READONLY.lua').read_text()
for bad in ('setLocalInt(', 'AttackReevaluate(', 'Spell(', 'ClearActions(', 'EEex_Action_AddSpriteStartedActionListener('):
 if bad in s:raise SystemExit('UNSAFE ACTION '+bad)
print('BGXAI079_SOURCE_ONLY_RELEASE_PASS')
