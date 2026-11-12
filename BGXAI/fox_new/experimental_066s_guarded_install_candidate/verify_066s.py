from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(__file__).parent
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
assert m['schema']==1 and m['game_mutation']==False and len(m['files'])==16
for x in m['files']:
 q=p/x['path'];assert q.is_file() and q.stat().st_size==x['size'] and hashlib.sha256(q.read_bytes()).hexdigest()==x['sha256'], x['path']
from build_066s import build
from generate_receiver import OUT
assert build()==(p/'M_BX43_066S_CASTER_CANDIDATE.lua').read_bytes()
print('BGXAI066S SOURCE HASHES 16/16 PASS; SOURCE ONLY GAME UNCHANGED')