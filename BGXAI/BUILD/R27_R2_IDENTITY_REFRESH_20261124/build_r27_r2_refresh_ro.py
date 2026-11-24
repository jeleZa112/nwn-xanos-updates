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
FILES = {
  SRC/'BGXAI_WEAPON_SLOTS_R2_READONLY.lua': '317f6fd6ad2beee0e61b7936c65ef35736e825e04d82f330133cc6c791d889af',
  SRC/'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua': '2b618df53566b75f651ae75ce737496e4b24cb18fd754be7eb7c245ccfbbcc40',
  HIST/'R27_EVENT_JOIN_TAIL.lua': '39abc118d43d3d9105a5c79341e61a0e4d158c5769944591ff324949bad2bc4b',
  HIST/'M_BGXR27.lua': 'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735',
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
  tail = checked(root, HIST/'R27_EVENT_JOIN_TAIL.lua').decode('ascii')
  legacy = checked(root, HIST/'M_BGXR27.lua')
  if len(legacy) != 28890 or not legacy.endswith(b'P.initialized=start()\n'):
    raise ValueError('R27_INSTALLED_HISTORICAL_SOURCE_UNEXPECTED')
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
  tail = replacement(tail,
    '  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,\n',
    '  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,offhandRaw=r2.offhand,\n  rawInventoryDoubleReadConsistent=true,\n')
  tail = replacement(tail,
    "  ',\"quiversRaw\":'..jslots(sample.quiversRaw,4)..\n",
    "  ',\"quiversRaw\":'..jslots(sample.quiversRaw,4)..\n  ',\"offhandRaw\":'..jslots(sample.offhandRaw and {sample.offhandRaw},1)..\n  ',\"rawInventoryDoubleReadConsistent\":'..tostring(sample.rawInventoryDoubleReadConsistent==true)..\n")
  # Compose a passive advisory module only: no bootstrap, no EEex registration.
  output = (b'-- BGXAI R27 revised SOURCE ONLY: SHA-pinned R2 identity double-read.\n'
       +b'-- NOT INSTALLED. Does not change original M_BGXR27.lua.\n'
       +b'local R2_CORE = (function()\n'+r2+b'end)()\n'
       +b'local R4_CORE = (function()\n'+r4+b'end)()\n'
       +tail.encode('ascii'))
  if any(word.encode() in output for word in FORBIDDEN):
    raise ValueError('R27_REBUILD_ACTION_DISPATCH_OR_UNSAFE_POINTER')
  if output.count(b'R2_CORE.observe_sprite,sprite') != 2 or output.count(b'R2_CORE.compare,r2,r2later') != 1:
    raise ValueError('R27_R2_DOUBLE_READ_OR_COMPARE_NOT_EXACT')
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
