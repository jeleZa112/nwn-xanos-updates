from pathlib import Path
from hashlib import sha256
import difflib
root=Path(__file__).resolve().parent
legacy=(root/'M_BX43_066S_CASTER_CANDIDATE.lua').read_text(encoding='utf-8')
base=(root/'M_BX43_066S_HEAL_PATCH_PREVIOUS.lua').read_text(encoding='utf-8')
assert sha256(legacy.encode()).hexdigest()=='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
assert sha256(base.encode()).hexdigest()=='c4e25bf6de7c3569b03657f3d48b5ddc9730c94ac6f63124bcc3f32cfb471e29'
needle="local FRONTLINE = {[2]=true,[6]=true,[12]=true} -- fighter/paladin/ranger CLASS.IDS\n"
assert base.count(needle)==1
addition='''-- Optional role-verified intercept extension; default OFF keeps 066S byte-for-byte policy.
-- The only valid source is a separately audited live capability/command observer.
-- CLASS.IDS, KIT label and transformed appearance alone are NOT evidence.
T.capabilityVerifier = nil
T.capabilitySourceVerified = false
local function verifiedGuardAbility(sprite, legacyRole, attackerID, victimID, eventSequence)
  if T.capabilitySourceVerified ~= true then return legacyRole=='frontline' end
  if type(T.capabilityVerifier) ~= 'function' then return false end
  local ok, p = pcall(T.capabilityVerifier, sprite, attackerID, victimID, eventSequence)
  if not ok or type(p) ~= 'table' then return false end
  -- All facts must be independently proven in the CURRENT actor state.
  -- Critical heal, occupied casting / song / traps and manual/EPS orders win.
  -- rawget avoids trusting metatable-generated / side-effecting evidence.
  return rawget(p,'verified') == true
     and rawget(p,'actor_id') == safe(function()return sprite.m_id end)
     and rawget(p,'attacker_id') == attackerID
     and rawget(p,'victim_id') == victimID
     and rawget(p,'source_event_sequence') == eventSequence
     and rawget(p,'effective_melee_now') == true
     and rawget(p,'weapon_effective_vs_attacker') == true
     and rawget(p,'active_class_and_kit_verified') == true
     and rawget(p,'transformation_safe_verified') == true
     and rawget(p,'action_idle_verified') == true
     and rawget(p,'eps_queue_empty_verified') == true
     and rawget(p,'manual_order_absent_verified') == true
     and rawget(p,'heal_reservation') == false
     and rawget(p,'spell_casting') == false
     and rawget(p,'bard_singing') == false
     and rawget(p,'detecting_traps') == false
     and rawget(p,'target_attacker_identity_verified') == true
end
'''
base=base.replace(needle,needle+addition,1)
old="if role=='frontline' and validGuardian(obj) and not T.reservations[id] then"
assert base.count(old)==1
base=base.replace(old,"if verifiedGuardAbility(obj,role,attackerID,victimID,seq) and validGuardian(obj) and not T.reservations[id] then",1)
(root/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').write_text(base,encoding='utf-8')
diff=''.join(difflib.unified_diff(legacy.splitlines(keepends=True),base.splitlines(keepends=True),fromfile='LIVE_066S_SHA_50640902',tofile='SOURCE_ONLY_CAPABILITY_GUARD_HEAL'))
(root/'066S_capability_patch.diff').write_text(diff,encoding='utf-8')
print('baseline',sha256(legacy.encode()).hexdigest(),'candidate',sha256(base.encode()).hexdigest(),'diff lines',len(diff.splitlines()))
