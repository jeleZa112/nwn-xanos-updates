#!/usr/bin/env python3
"""Source-only R27 R2 identity refresh; NEVER modifies the installed game.

Uses current SHA-pinned R2/R4 cores plus original R27 join tail. Does NOT
modify the already installed/authorized M_BGXR27.lua or its WeiDU installer.
The refresh improves one-callback raw quickslot/quiver/offhand consistency;
it does not measure effective alternate APR, validate native item pointer
lifetimes, grant orders, or install anything.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = 'BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua'
SRC = Path('BGXAI/patchsets/ranged_fighter_guarded_20261119')
HIST = Path('BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123')
CONTEXT81 = Path('BGXAI/fox_new/experimental_081_eeex_action_provenance_readonly_source_only/BGXAI081_ACTION_CONTEXT_READONLY_V3.lua')
FILES = {
  SRC/'BGXAI_WEAPON_SLOTS_R2_READONLY.lua': '317f6fd6ad2beee0e61b7936c65ef35736e825e04d82f330133cc6c791d889af',
  SRC/'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua': '64905835258bf85a30be078ba02967a227ce28d063dee61969ecab89829c43aa',
  HIST/'R27_EVENT_JOIN_TAIL.lua': '39abc118d43d3d9105a5c79341e61a0e4d158c5769944591ff324949bad2bc4b',
  HIST/'M_BGXR27.lua': 'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735',
  CONTEXT81: '25371702bed0a72c21615a1eb505dbc718f4d31107318ce04aeb84f70e6c157b',
}
FORBIDDEN = (
  'ClearActions(', 'SelectWeaponAbility(', 'ActionOverride(', 'SetGlobal(',
  'Attack(', 'Stop(', 'getAbility(', 'getLauncher(',
  'EEex_Action_AddSpriteStartedActionListener(', 'io.open(', 'os.execute(',
  'EEex_Resource_Demand(', 'EEex_Action_QueueScriptFileResponseOnAIBase(',
)


def sha(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()


def checked(root: Path, rel: Path) -> bytes:
  target = root / rel
  if target.is_symlink() or not target.is_file():
    raise ValueError('R27_SOURCE_FILE_MISSING_OR_LINK:' + str(rel))
  contents = target.read_bytes()
  if sha(contents) != FILES[rel]:
    raise ValueError('R27_PINNED_SOURCE_DRIFT:' + str(rel))
  return contents


def replacement(text: str, needle: str, replacement: str) -> str:
  if text.count(needle) != 1:
    raise ValueError('R27_TAIL_ANCHOR_MISSING_OR_DUPLICATE')
  return text.replace(needle, replacement)


def build(root: Path = ROOT) -> bytes:
  root = Path(root)
  r2 = checked(root, SRC/'BGXAI_WEAPON_SLOTS_R2_READONLY.lua')
  r4 = checked(root, SRC/'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua')
  context81 = checked(root, CONTEXT81)
  tail = checked(root, HIST/'R27_EVENT_JOIN_TAIL.lua').decode('ascii')
  legacy = checked(root, HIST/'M_BGXR27.lua')
  if len(legacy) != 28890 or not legacy.endswith(b'P.initialized=start()\n'):
    raise ValueError('R27_INSTALLED_HISTORICAL_SOURCE_UNEXPECTED')
  if not context81.endswith(b'\nreturn M\n'):
    raise ValueError('R27_QUEUE_PROVENANCE_CORE_MISSING_RETURN')
  if not r2.endswith(b'\nreturn M\n') or not r4.endswith(b'\nreturn M\n'):
    raise ValueError('R27_OBSERVER_CORE_MISSING_RETURN')
  if not tail.endswith('return R27\n'):
    raise ValueError('R27_TAIL_END_UNEXPECTED')
  # Re-read the same 9 raw slots after R4 has collected selected active stats;
  # neither read changes the character's selection, game state, or queue.
  needle = " local a=before_after(sprite,action)\n if not same(b,a) then return hold('SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE') end\n"
  inject = """ local ok2later,r2later=pcall(R2_CORE.observe_sprite,sprite)
 if not ok2later or type(r2later)~='table' then return hold('R2_RECHECK_EXCEPTION') end
 local okCmp,stability=pcall(R2_CORE.compare,r2,r2later)
 if not okCmp or type(stability)~='table' then return hold('R2_COMPARE_EXCEPTION') end
 if stability.status=='INVALIDATE_WEAPON_ADVICE_KEEP_ACTION' then
  return hold('EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE') end
 if stability.status~='RAW_FINGERPRINT_SAME_NOT_PROOF_OF_BUFFS' then
  return hold('R2_RECHECK_INCOMPLETE') end
"""
  tail = replacement(tail, needle, needle+inject+" if not same(b,before_after(sprite,action)) then\n  return hold('SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE') end\n")
  # Never turn EEex m_tempStats (effect-list work in progress) into APR evidence.
  # The original historical R27 source/installer remain frozen.
  tail = replacement(tail,
    'pcall(R4_CORE.observe,sprite,action,partyIndex,getActiveStats)',
    'pcall(R4_CORE.observeStableDerived,sprite,action,partyIndex,getActiveStats)')
  tail = replacement(tail,
    " if r2.actorId~=b.actor or r4.actorId~=b.actor or\n",
    " if r4.status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or\n"+
    "    r4.derivedStatsDoubleReadConsistent~=true then\n"+
    "  return hold('R4_DERIVED_STATS_NOT_STABLE') end\n"+
    " if r2.actorId~=b.actor or r4.actorId~=b.actor or\n")
  tail = replacement(tail,
    '  sameLuaListenerInvocation=true,nativeEventTokenAuthenticated=false,\n',
    '  selectedDerivedStatsDoubleReadConsistent=true,\n  sameLuaListenerInvocation=true,nativeEventTokenAuthenticated=false,\n')
  tail = replacement(tail,
    '  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,\n',
    '  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,offhandRaw=r2.offhand,\n  rawInventoryDoubleReadConsistent=true,\n')
  tail = replacement(tail,
    "  ',\"quiversRaw\":'..jslots(sample.quiversRaw,4)..\n",
    "  ',\"quiversRaw\":'..jslots(sample.quiversRaw,4)..\n  ',\"offhandRaw\":'..jslots(sample.offhandRaw and {sample.offhandRaw},1)..\n  ',\"rawInventoryDoubleReadConsistent\":'..tostring(sample.rawInventoryDoubleReadConsistent==true)..\n")
  tail = replacement(tail,
    "  ',\"rawInventoryDoubleReadConsistent\":'..tostring(sample.rawInventoryDoubleReadConsistent==true)..\n",
    "  ',\"rawInventoryDoubleReadConsistent\":'..tostring(sample.rawInventoryDoubleReadConsistent==true)..\n"+
    "  ',\"selectedDerivedStatsDoubleReadConsistent\":'..tostring(sample.selectedDerivedStatsDoubleReadConsistent==true)..\n")
  # Serialize the observed R4 status, not a hard-coded untrusted claim,
  # so the existing R6 offline reader can reject non-stable old log records.
  tail = replacement(tail,
    "  ',\"selectedDerivedStatsDoubleReadConsistent\":'..tostring(sample.selectedDerivedStatsDoubleReadConsistent==true)..\n",
    "  ',\"selectedDerivedStatsDoubleReadConsistent\":'..tostring(sample.selectedDerivedStatsDoubleReadConsistent==true)..\n"+
    "  ',\"r4Status\":'..(sample.r4Status=='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' and\n"+
    "    '\"RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS\"' or 'null')..\n")
  # Safely sample the engine's action queue raw count without walking pointer
  # nodes. Empty count != manual/EPS authorization, and action origin UNKNOWN.
  tail = replacement(tail,
    ' local b=before_after(sprite,action)\n',
    ' local b=before_after(sprite,action)\n'+
    ' local queueBefore=Q81_CORE.observe(sprite,action)\n')
  tail = replacement(tail,
    " if r4.status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or\n",
    " local queueAfter=Q81_CORE.observe(sprite,action)\n"+
    " local qStable=queueBefore.queue_count_observed==true and\n"+
    "  queueAfter.queue_count_observed==true and\n"+
    "  queueBefore.current_action_id==b.action and\n"+
    "  queueAfter.current_action_id==b.action and\n"+
    "  queueBefore.queue_count_raw==queueAfter.queue_count_raw\n"+
    " local qCount=qStable and queueBefore.queue_count_raw or nil\n"+
" local ctxStable=queueBefore.action_context_snapshot_stable==true and\n"+
"  queueAfter.action_context_snapshot_stable==true and\n"+
"  queueBefore.engine_action_execution_raw==queueAfter.engine_action_execution_raw and\n"+
"  queueBefore.engine_no_interrupt_raw==queueAfter.engine_no_interrupt_raw and\n"+
"  queueBefore.current_script_number_raw==queueAfter.current_script_number_raw and\n"+
"  queueBefore.action_count_raw==queueAfter.action_count_raw and\n"+
"  queueBefore.interrupt_raw==queueAfter.interrupt_raw and\n"+
"  queueBefore.ordered_by_instance_raw==queueAfter.ordered_by_instance_raw and\n"+
"  queueBefore.ordered_by_sent_instance_raw==queueAfter.ordered_by_sent_instance_raw\n"+
" local srcStable=queueBefore.action_source_stable==true and\n"+
"  queueAfter.action_source_stable==true and\n"+
"  queueBefore.action_source_raw==queueAfter.action_source_raw\n"+
" local srcStatus=queueBefore.action_source_read_status\n"+
" if srcStatus~=queueAfter.action_source_read_status then\n"+
"  srcStatus='ACTION_SOURCE_STATUS_CHANGED_DURING_CAPTURE' end\n"+
    " if r4.status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or\n")
  tail = replacement(tail,
    '  rawInventoryDoubleReadConsistent=true,\n',
    '  rawInventoryDoubleReadConsistent=true,\n'+
    '  queueSnapshotStable=qStable,queuedActionsRaw=qCount,\n'+
    '  actionOriginVerified=false,manualEpsQueueVerified=false,\n'+
    '  actionContextSnapshotStable=ctxStable,\n'+
    '  engineActionExecutionRaw=ctxStable and queueBefore.engine_action_execution_raw or nil,\n'+
    '  engineNoInterruptRaw=ctxStable and queueBefore.engine_no_interrupt_raw or nil,\n'+
    '  currentScriptNumberRaw=ctxStable and queueBefore.current_script_number_raw or nil,\n'+
    '  actionCountRaw=ctxStable and queueBefore.action_count_raw or nil,\n'+
    '  interruptRaw=ctxStable and queueBefore.interrupt_raw or nil,\n'+
    '  orderedByInstanceRaw=ctxStable and queueBefore.ordered_by_instance_raw or nil,\n'+
    '  orderedBySentInstanceRaw=ctxStable and queueBefore.ordered_by_sent_instance_raw or nil,\n'+
    '  actionSourceStable=srcStable,actionSourceRaw=srcStable and queueBefore.action_source_raw or nil,\n'+
    '  actionSourceReadStatus=srcStatus,\n');
  tail = replacement(tail,
    "  ',\"r4Status\":'..(sample.r4Status==",
    "  ',\"queueSnapshotStable\":'..tostring(sample.queueSnapshotStable==true)..\n"+
    "  ',\"queuedActionsRaw\":'..jnum(sample.queuedActionsRaw,0,512)..\n"+
    "  ',\"queueNonemptyObserved\":'..(sample.queueSnapshotStable==true and\n"+
    "    tostring(sample.queuedActionsRaw>0) or 'null')..\n"+
    "  ',\"actionOriginVerified\":false,\"manualEpsQueueVerified\":false'..\n"+
    "  ',\"r4Status\":'..(sample.r4Status==")
  # Compose a passive advisory module only: no bootstrap, no EEex registration.
  output = (b'-- BGXAI R27 revised SOURCE ONLY: SHA-pinned R2 identity double-read.\n'
       +b'-- NOT INSTALLED. Does not change original M_BGXR27.lua.\n'
       +b'local R2_CORE = (function()\n'+r2+b'end)()\n'
       +b'local R4_CORE = (function()\n'+r4+b'end)()\n'
       +b'local Q81_CORE = (function()\n'+context81+b'end)()\n'
       +tail.encode('ascii'))
  if any(word.encode() in output for word in FORBIDDEN):
    raise ValueError('R27_REBUILD_ACTION_DISPATCH_OR_UNSAFE_POINTER')
  if output.count(b'R2_CORE.observe_sprite,sprite') != 2 or output.count(b'R2_CORE.compare,r2,r2later') != 1:
    raise ValueError('R27_R2_DOUBLE_READ_OR_COMPARE_NOT_EXACT')
  if output.count(b'pcall(R4_CORE.observeStableDerived,sprite,action,partyIndex,getActiveStats)') != 1 or \
     output.count(b'selectedDerivedStatsDoubleReadConsistent=true') != 1:
    raise ValueError('R27_STABLE_DERIVED_STATS_CONTRACT_MISSING')
  if (output.count(b'Q81_CORE.observe(sprite,action)') != 2 or
      output.count(b'queueSnapshotStable=qStable') != 1 or
      output.count(b'queuedActionsRaw=qCount') != 1):
    raise ValueError('R27_ENGINE_ACTION_QUEUE_RAW_OBSERVER_CONTRACT')
  if output.count(b'return R27\n') != 1:
    raise ValueError('R27_SINGLE_EXPORT_REQUIRED')
  return output


def main() -> int:
  p = argparse.ArgumentParser(description='R27 R2 refresh SOURCE ONLY; no game writes')
  p.add_argument('--root', type=Path, default=ROOT)
  p.add_argument('--check', action='store_true')
  args = p.parse_args()
  content = build(args.root)
  out = HERE / OUT if args.root == ROOT else args.root / HIST / OUT
  if args.check:
    if out.is_symlink() or not out.is_file() or out.read_bytes()!=content:
      raise ValueError('R27_R2_REFRESH_CANDIDATE_DRIFT')
  else:
    if out.is_symlink():raise ValueError('OUTPUT_SYMLINK_DENIED')
    out.write_bytes(content)  # standalone source candidate, never game root
  print('SOURCE_ONLY_R27_R2_REFRESH_PASS',len(content),sha(content))
  return 0

if __name__ == '__main__':
  raise SystemExit(main())
