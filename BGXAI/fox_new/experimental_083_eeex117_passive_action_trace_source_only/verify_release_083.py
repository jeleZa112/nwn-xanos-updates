#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent
bad=0
items=json.loads((ROOT/'manifest_sha256.json').read_text(encoding='utf-8'))
for name,expected in items.items():
 p=ROOT/name
 got=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'MISSING'
 if got!=expected: bad+=1
 print(('PASS' if got==expected else 'FAIL'),name)
source=(ROOT/'BGXAI083_PASSIVE_TRACE.lua').read_text(encoding='utf-8')
for x in ('virtual_InsertAction(', 'setLocalInt(', 'EEex_Action_AddSpriteStartedActionListener(', 'EEex_Action_QueueResponseStringOnAIBase(', 'io.open(', 'os.execute('):
 if x in source:bad+=1;print('FAIL forbidden token',x)
print('NO_ENGINE_DISPATCH_AND_NO_GAME_WRITE', 'PASS' if not bad else 'FAIL')
sys.exit(1 if bad else 0)