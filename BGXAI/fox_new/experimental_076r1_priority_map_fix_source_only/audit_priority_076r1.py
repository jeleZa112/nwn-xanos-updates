#!/usr/bin/env python3
"""BGXAI 076R1: corrected SHA-pinned, read-only position audit of installed 066S.

Reports marker locations in compiled BCS. DOES NOT infer dynamic scheduling,
interrupt safety, attacker identity, or spell success. No game writes/network.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from verify_066s_live_075 import inspect, blocks, Blocked, BLOCKS_066S, INSERT_AT, INSERT_COUNT, SHA_066S

MARKERS = {
    'EPS_ATTACK_MODE': b'BDAI_ATTACK_MODE',
    'EPS_HEAL_CAST': b'MO_HealCast',
    'BGXAI_F_GUARD': b'BGX38_GUARD',
    'BGXAI_F_KEY_COOLDOWN': b'BGX38_KEY_CD',
    'BGXAI_BG39_TEAM_COOLDOWN': b'BGX39_TEAM_CD',
    'BGXAI_061_RECEIVER': b'BGX52_REQ_SLOT',
    'BGXAI_066S_HEAL': b'BGX66_S_HEAL_SLOT',
    'BGXAI_066S_WARD': b'BGX66_S_WARD',
    'BGXAI_067_EARLY': b'BGX67_EARLY_SLOT',
}

def spans(indices):
    if not indices: return []
    runs=[];a=b=indices[0]
    for n in indices[1:]:
        if n == b+1: b=n
        else: runs.append([a,b]);a=b=n
    runs.append([a,b]);return runs

def analyze(raw: bytes, *, live_pins: bool=True) -> dict:
    proven = inspect(raw,verify_pins=live_pins)
    chunks=blocks(raw,BLOCKS_066S)
    indices={name:[i+1 for i,c in enumerate(chunks) if value in c]
             for name,value in MARKERS.items()}
    # 075 reports only 1077 PRE-EXISTING blocks after removing the 11 new
    # 066S blocks. 076 incorrectly compared that legacy count with ALL 1088
    # blocks (which include NEW F-guard markers) and rejected healthy installs.
    # Compare the same population, then report original/inserted/all separately.
    added_range=set(range(INSERT_AT + 1, INSERT_AT + INSERT_COUNT + 1))
    legacy_indices={name:[position for position in positions if position not in added_range]
                    for name,positions in indices.items()}
    added_indices={name:[position for position in positions if position in added_range]
                   for name,positions in indices.items()}
    observed_legacy={
      'EPS_ATTACK_RULES':len(legacy_indices['EPS_ATTACK_MODE']),
      'EPS_HEAL_RULES':len(legacy_indices['EPS_HEAL_CAST']),
      'F_GUARD_RULES':len(legacy_indices['BGXAI_F_GUARD']),
    }
    if live_pins and (observed_legacy != proven['source_marker_counts']
                      or observed_legacy != {
                        'EPS_ATTACK_RULES':60,
                        'EPS_HEAL_RULES':11,
                        'F_GUARD_RULES':37,
                      }):
        raise Blocked('LEGACY_075_MARKER_COUNTS_DRIFT')
    if live_pins and indices['BGXAI_067_EARLY']:
        raise Blocked('067_UNEXPECTED_IN_066S')
    idx_061=[i+1 for i in range(1031,1051)]
    idx_066=[i+1 for i in range(INSERT_AT,INSERT_AT+INSERT_COUNT)]
    # Check that the pinned source receiver markers exist exactly where expected.
    if any(b'BGX52_REQ_SLOT' not in chunks[i-1] for i in idx_061):
        raise Blocked('061_RECEIVER_POSITION_MISMATCH')
    if any(b'BGX66_S_HEAL_SLOT' not in chunks[i-1] for i in idx_066[4:10]):
        raise Blocked('066S_HEAL_POSITION_MISMATCH')
    if b'BGX66_S_WARD' not in chunks[idx_066[-1]-1]:
        raise Blocked('066S_WARD_POSITION_MISMATCH')
    out={
       'status':'READ_ONLY_066S_PRIORITY_POSITION_MAP_R1' if live_pins else 'SYNTHETIC_066S_POSITION_MAP',
       'bcs_sha256':proven['live_066s_bcs_sha256'],
       'total_blocks':len(chunks),
       'source_validated':live_pins,
       'marker_blocks':{name:{'count':len(pos),'first':pos[0] if pos else None,
                              'last':pos[-1] if pos else None,'runs':spans(pos),
                              'legacy_count':len(legacy_indices[name]),
                              'inserted_066s_count':len(added_indices[name])}
                         for name,pos in indices.items()},
       'legacy_075_marker_counts':observed_legacy,
       'marker_count_explanation':
          '075 counts 1077 legacy blocks; 076R1 reports legacy and 11 inserted separately.',
       'fixed_receivers':{
          'BGXAI_061_receiver_blocks_inclusive':[idx_061[0],idx_061[-1]],
          'BGXAI_066S_cleanup_blocks_inclusive':[idx_066[0],idx_066[3]],
          'BGXAI_066S_healing_blocks_inclusive':[idx_066[4],idx_066[9]],
          'BGXAI_066S_mage_ward_block':idx_066[10],
       },
       'source_order_only':{
          'EPS_heal_marker_appears_before_066S_heal_receiver':
            bool(indices['EPS_HEAL_CAST']) and indices['EPS_HEAL_CAST'][0]<idx_066[4],
          'EPS_attack_marker_appears_before_061_guard_receiver':
            bool(indices['EPS_ATTACK_MODE']) and indices['EPS_ATTACK_MODE'][0]<idx_061[0],
          '061_guard_receiver_precedes_066S_heal_receiver':idx_061[-1] < idx_066[4],
       },
       'critical_limits':[
          'Presence and source order are NOT proof of actual EPS priority or action interruption.',
          'Compiled BCS marker names do not imply an action was executed.',
          'ActionListEmpty in 066S heal BAF can delay a heal while other action remains queued.',
          'The original real attacker cannot be inferred from NearestEnemyOf(PlayerN).',
          'No file was modified; use real EEex runtime observations before an active patch.',
       ],
    }
    return out

def main():
    p=argparse.ArgumentParser(description='BGXAI 076R1 corrected EPS/guard positional audit; read-only')
    p.add_argument('--bcs',required=True,type=Path)
    a=p.parse_args()
    try: result=analyze(a.bcs.read_bytes())
    except (OSError,Blocked,ValueError) as e:
        result={'status':'BLOCKED_NO_GAME_CHANGE','reason':str(e)}
    print(json.dumps(result,indent=2,ensure_ascii=False))
    raise SystemExit(0 if result['status']=='READ_ONLY_066S_PRIORITY_POSITION_MAP_R1' else 2)
if __name__=='__main__': main()
