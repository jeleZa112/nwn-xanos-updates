#!/usr/bin/env python3
"""Read-only, SHA-locked forensic audit of the 066S Lua currently on Windows.

No network, no subprocess, no game changes. Only prints JSON.
This audit is NOT evidence of live action queue semantics or manual/EPS origin.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

PIN_LUA_066S='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
PIN_BCS_066S='fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'
SENTINELS = {
  'manual_origin_unproven': r'P\.manualOriginKnown\s*=\s*false',
  'snapshot_origin_unproven': r'origin_verifiable\s*=\s*false',
  'snapshot_queue_unproven': r'queue_verifiable\s*=\s*false',
  'started_listener_registration': r'pcall\(EEex_Action_AddSpriteStartedActionListener\s*,\s*P\.onStarted\)',
  'weapon_hit_listener_registration': r'pcall\(EEex_Sprite_AddBlockWeaponHitListener\s*,\s*P\.onWeaponHit\)',
  'started_action_id_read': r'action\.m_actionID',
  'current_attack_action_read': r'attacker\.m_curAction\.m_actionID',
  'frontline_request_writer': r'best\.sprite:setLocalInt\(',
  'caster_request_writer': r'o:setLocalInt\(',
  'guard_request_dispatch': r'BGX52Bridge\.prepare',
  'caster_hit_support': r'S\.onHit\(hit\)',
}
class Refused(Exception): pass

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def analyze(lua:bytes,bcs:bytes|None=None)->dict:
  if digest(lua)!=PIN_LUA_066S:raise Refused('LIVE_066S_LUA_SHA_MISMATCH_NO_INFERENCE')
  if bcs is not None and digest(bcs)!=PIN_BCS_066S:
    raise Refused('LIVE_066S_BCS_SHA_MISMATCH_NO_INFERENCE')
  src=lua.decode('utf-8','strict')
  found={k:bool(re.search(pattern,src)) for k,pattern in SENTINELS.items()}
  if not all(found.values()):raise Refused('EXPECTED_066S_ACTION_OBSERVER_NOT_PRESENT')
  return {
    'status':'READ_ONLY_066S_LUA_ACTION_CONTRACT_CONFIRMED',
    'lua_sha256':digest(lua),
    'bcs_sha256':digest(bcs) if bcs is not None else None,
    'static_evidence':found,
    'action_started_listener_source_present':True,
    'weapon_hit_listener_source_present':True,
    'current_action_id_read_present':True,
    'manual_command_origin_proven':False,
    'eps_action_queue_empty_proven':False,
    'started_action_implies_queue_empty':False,
    'source_issues_local_requests':True,
    'can_authorize_080_in_game':False,
    'note':'Static source exactness does not prove listener was invoked, current queue is empty, or an action is from a manual order.',
  }

def main():
  p=argparse.ArgumentParser(description='BGXAI 081 SHA pinned read-only 066S action observer contract')
  p.add_argument('--lua',type=Path,required=True,help='Local M_BX43.lua, read only')
  p.add_argument('--bcs',type=Path,help='Optional local BDDEFAI.BCS, read only')
  args=p.parse_args()
  try:
    result=analyze(args.lua.read_bytes(),args.bcs.read_bytes() if args.bcs else None)
  except (OSError,UnicodeError,Refused) as e:
    result={'status':'BLOCKED_NO_GAME_CHANGE','reason':str(e)}
  print(json.dumps(result,indent=2,ensure_ascii=False))
  raise SystemExit(0 if result['status']=='READ_ONLY_066S_LUA_ACTION_CONTRACT_CONFIRMED' else 2)
if __name__=='__main__':main()
