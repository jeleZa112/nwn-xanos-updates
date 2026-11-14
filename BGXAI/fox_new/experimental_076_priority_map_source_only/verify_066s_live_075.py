#!/usr/bin/env python3
"""BGXAI 075: read-only, SHA-pinned verification of INSTALLED 066S BCS.

Has no write calls or game actions. The audit prints JSON to stdout only.
It does not ask for or collect live game data. No network, subprocess or installer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

SHA_066S='fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'
SHA_064='db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b'
BLOCKS_066S=1088
BLOCKS_064=1077
INSERT_AT=1051
INSERT_COUNT=11
START=re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACTIONS=re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')

class Blocked(Exception): pass

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def blocks(raw:bytes,expected:int)->list[bytes]:
    if not raw.startswith(b'SC\n'):raise Blocked('BCS_HEADER_INVALID')
    if b'\x00' in raw or b'\r' in raw:raise Blocked('BCS_NOT_TEXTUAL_LF_ONLY')
    pos=[m.start(1) for m in START.finditer(raw)]
    if len(pos)!=expected or not pos or pos[0]!=3:
        raise Blocked(f'BLOCK_COUNT_{len(pos)}_EXPECTED_{expected}')
    chunks=[raw[a:b] for a,b in zip(pos,pos[1:]+[len(raw)])]
    if any(not c.startswith(b'CR\nCO\n') or c.count(b'\nRS\n')!=2 for c in chunks):
        raise Blocked('BCS_BAD_STRUCTURE')
    if any(not c.endswith(b'CR\n') for c in chunks[:-1]):
        raise Blocked('NONFINAL_BLOCK_MISSING_CR')
    if not chunks[-1].endswith(b'CR\nSC\n') or raw.count(b'\nSC\n')!=1:
        raise Blocked('BCS_FINAL_SC_INVALID')
    if b'SC\n'+b''.join(chunks)!=raw:
        raise Blocked('NOT_BYTE_EXACT_SEGMENTATION')
    return chunks

def action_ids(chunk:bytes)->list[int]:return [int(x) for x in ACTIONS.findall(chunk)]

EXPECTED_061=([[30,36]]*2+[[30,115,30,30,134]]*6+
              [[115,115,30,30,22]]*6+[[30,115,30,30,87]]*6)
EXPECTED_066S=([[30,36]]*4+[[30,115,31]]*7)

def inspect(raw:bytes,*,verify_pins:bool=True)->dict:
    digest=sha(raw)
    if verify_pins and digest!=SHA_066S:
        raise Blocked('LIVE_066S_SHA_MISMATCH_NO_INFERENCE')
    all_chunks=blocks(raw,BLOCKS_066S)
    added=list(all_chunks[INSERT_AT:INSERT_AT+INSERT_COUNT])
    if [action_ids(c) for c in added]!=EXPECTED_066S:
        raise Blocked('066S_ACTION_LAYOUT_DRIFT')
    if any(b'LOCALSBGX66_S_' not in c for c in added[:4]):
        raise Blocked('066S_CLEANUP_MARKER_MISSING')
    if any(b'BGX66_S_HEAL_SLOT' not in c for c in added[4:10]):
        raise Blocked('066S_HEAL_MARKER_MISSING')
    if b'BGX66_S_WARD' not in added[10]:
        raise Blocked('066S_WARD_MARKER_MISSING')
    old=list(all_chunks[:INSERT_AT]+all_chunks[INSERT_AT+INSERT_COUNT:])
    if len(old)!=BLOCKS_064 or [action_ids(c) for c in old[1031:1051]]!=EXPECTED_061:
        raise Blocked('061_RECEIVER_NOT_PRESERVED')
    if any(b'BGX52_REQ_SLOT' not in c for c in old[1031:1051]):
        raise Blocked('061_RECEIVER_MARKER_MISSING')
    if any(b'BGX61_LAST_BRANCH' not in c for c in old[1033:1051]):
        raise Blocked('061_BRANCH_MARKER_MISSING')
    recovered=b'SC\n'+b''.join(old)
    # The 066S final block carries SC, and old last block already ends with SC.
    if verify_pins and sha(recovered)!=SHA_064:
        raise Blocked('REMOVING_066S_DOES_NOT_RECOVER_PINNED_064')
    if len(blocks(recovered,BLOCKS_064))!=BLOCKS_064:
        raise Blocked('RECOVERED_064_BAD_STRUCTURE')
    found={
      'EPS_ATTACK_RULES':sum(b'BDAI_ATTACK_MODE' in c for c in old),
      'EPS_HEAL_RULES':sum(b'MO_HealCast' in c for c in old),
      'F_GUARD_RULES':sum(b'BGX38_GUARD' in c for c in old)
    }
    if not all(v>0 for v in found.values()):
        raise Blocked('EPS_OR_F_GUARD_MARKERS_MISSING')
    return {'status':'READ_ONLY_066S_STRUCTURE_CONFIRMED' if verify_pins else 'SYNTHETIC_STRUCTURE_ONLY',
      'live_066s_bcs_sha256':digest,'original_064_bcs_sha256':sha(recovered),
      'block_count_live_066s':len(all_chunks),'blocks_inserted_by_066s':len(added),
      'block_count_recovered_064':len(old),'legacy_relative_order_byte_exact':True,
      'source_marker_counts':found,
      'note':'BCS byte integrity does not prove engine action queue timing, dynamic priority or success of a heal/guard.'}

def main():
    p=argparse.ArgumentParser(description='Source-only: verify installed 066S BCS without changing game')
    p.add_argument('--bcs',type=Path,required=True,help='Exact file to READ (not install)')
    a=p.parse_args()
    try:
        result=inspect(a.bcs.read_bytes())
    except (OSError,Blocked) as e:
        result={'status':'BLOCKED_NO_GAME_CHANGE','reason':str(e)}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['status']=='READ_ONLY_066S_STRUCTURE_CONFIRMED' else 2)
if __name__=='__main__':main()
