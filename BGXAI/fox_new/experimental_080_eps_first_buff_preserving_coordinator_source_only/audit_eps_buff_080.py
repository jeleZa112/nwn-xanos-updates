#!/usr/bin/env python3
"""SHA-locked historical EPS 18.4 compiled BCS marker evidence, READ ONLY.

This historical 041 BCS is NOT the currently installed 066S. Do not confuse
static marker presence with a cast, queue state, or actual game behavior.
"""
from pathlib import Path
import argparse,hashlib,json,re

PIN_041='86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
EXPECTED_BLOCKS=1057
MARKERS={
 'EPS_BUFF':b'MO_BUFF',
 'EPS_LONG_BUFF':b'MO_LONG_BUFF',
 'EPS_SOLO_BUFFING':b'MO_SOLOBUFFING',
 'EPS_HEAL_CAST':b'MO_HealCast',
 'EPS_ATTACK_MODE':b'BDAI_ATTACK_MODE',
 'BGXAI_F_GUARD':b'BGX38_GUARD',
}
class Blocked(Exception):pass

def parse(raw:bytes)->list[bytes]:
 if hashlib.sha256(raw).hexdigest()!=PIN_041: raise Blocked('HISTORICAL_041_SHA_MISMATCH')
 if not raw.startswith(b'SC\n') or b'\r' in raw or b'\x00' in raw:raise Blocked('HEADER_OR_TEXT_FORMAT_INVALID')
 start=[m.start(1) for m in re.finditer(rb'(?:^|\n)(CR\nCO\n)',raw)]
 if len(start)!=EXPECTED_BLOCKS or start[0]!=3:raise Blocked('HISTORICAL_BLOCK_COUNT_MISMATCH')
 chunks=[raw[i:j] for i,j in zip(start,start[1:]+[len(raw)])]
 if any(not c.startswith(b'CR\nCO\n') or c.count(b'\nRS\n')!=2 for c in chunks):raise Blocked('BCS_BLOCK_STRUCTURE_INVALID')
 if any(not c.endswith(b'CR\n') for c in chunks[:-1]):raise Blocked('BCS_BLOCK_TERMINATOR_INVALID')
 if not chunks[-1].endswith(b'CR\nSC\n') or raw!=b'SC\n'+b''.join(chunks):raise Blocked('BCS_NOT_LOSSLESS')
 return chunks

def audit(raw:bytes)->dict:
 chunks=parse(raw)
 hits={k:[i+1 for i,block in enumerate(chunks) if v in block] for k,v in MARKERS.items()}
 if not all(hits[k] for k in ('EPS_BUFF','EPS_LONG_BUFF','EPS_SOLO_BUFFING','EPS_HEAL_CAST')):
  raise Blocked('EPS_CORE_BUFF_OR_HEAL_MARKER_ABSENT')
 return {'status':'HISTORICAL_041_EPS_BUFF_SOURCE_CONFIRMED',
  'source_sha256':PIN_041,'blocks':len(chunks),
  'markers':{name:{'count':len(pos),'first':pos[0] if pos else None,'last':pos[-1] if pos else None} for name,pos in hits.items()},
  'integrity':'BYTE_EXACT_NON_MUTATING',
  'runtime_proof':False,
  'live_066s_buff_marker_counts_verified':False,
  'important_limit':'This is older 041 BCS; 075/076R1 proved live 066S EPS attack/heal and F markers, not every historical buff marker.'}

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--historical-bcs',required=True,type=Path);a=p.parse_args()
 try: result=audit(a.historical_bcs.read_bytes())
 except (Blocked,OSError) as e:result={'status':'BLOCKED_NO_GAME_CHANGE','reason':str(e)}
 print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if result['status'].startswith('HISTORICAL_') else 2
if __name__=='__main__':raise SystemExit(main())
