from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
m=json.loads((D/'manifest_sha256.json').read_text('utf-8'))
for name,expected in m['files'].items():
 if hashlib.sha256((D/name).read_bytes()).hexdigest()!=expected:raise SystemExit('HASH_MISMATCH '+name)
print('BGXAI082 source SHA: %d/%d PASS'%(len(m['files']),len(m['files'])))
for name in ['BGXAI082_QUEUE_GUARD_BRIDGE.lua','BGXAI081_ACTION_PROVENANCE_READONLY.lua']:
 text=(D/name).read_text('utf-8')
 for bad in ('setLocalInt','ClearActions','AttackReevaluate','ProtectObject','Spell(', 'os.','io.'):
  if bad in text:raise SystemExit('FORBIDDEN_GAME_ACTION '+name+' '+bad)
print('BGXAI082 NO_GAME_WRITE: PASS')
