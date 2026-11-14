"""Reverses ONLY the cross-channel arbitration patch; no game modifications.

This independently proves that the candidate has changed only the five
reviewed code regions relative to the already-tested V2 candidate.
"""
from pathlib import Path
import hashlib

OLD_SHA256='954bb400ccc7e39aa0040460d167b51584892d7bd58237bf78ed05781eb7da70'

def exact_replace(s,old,new):
    assert s.count(old)==1, ('expected one match',old[:70],s.count(old))
    return s.replace(old,new,1)

def revert(new):
    s=new
    s=exact_replace(s,"""BGX52Bridge.prepare=function(hit)
 -- Historical 066S dispatch order is retained until an independently verified
 -- observer enables capability mode. In capability mode emergency heals claim
 -- their caster first; the guard gate then excludes that same actor.
 if T.capabilitySourceVerified == true then
  S.onHit(hit)
  return basePrepare(hit)
 end
 local ok,why=basePrepare(hit)
 S.onHit(hit)
 return ok,why
end""", """BGX52Bridge.prepare=function(hit)
 local ok,why=basePrepare(hit)
 S.onHit(hit)
 return ok,why
end""")
    s=exact_replace(s,"""if m.slot>1 and m.id~=attackerID and not S.reservations[m.id]
     and not guardianOwnsActorNow(m.obj,m.id) then""", """if m.slot>1 and m.id~=attackerID and not S.reservations[m.id] then""")
    s=exact_replace(s,"""-- Capability-mode reservation is shared between guardian and caster requests,
-- including still-pending BCS requests whose short Lua lease has expired.
local function guardianOwnsActorNow(sprite,id)
 if not BGX66Team or BGX66Team.capabilitySourceVerified ~= true then return false end
 if type(BGX66Team.reservations)~='table' then return true end
 if BGX66Team.reservations[id] then return true end
 local req=get(sprite,'BGX52_REQ_SLOT')
 return not integer(req) or req~=0
end
""", "")
    s=exact_replace(s,"""if verifiedGuardAbility(obj,role,attackerID,victimID,seq) and validGuardian(obj)
             and not T.reservations[id] and not casterOwnsActorNow(obj,id) then""", """if verifiedGuardAbility(obj,role,attackerID,victimID,seq) and validGuardian(obj) and not T.reservations[id] then""")
    s=exact_replace(s,"""-- Reserved caster responses and pending BCS slots always outrank a NEW
-- capability-mode guard request. The old 066S class-based path is unchanged.
local function casterOwnsActorNow(sprite,id)
  if T.capabilitySourceVerified ~= true then return false end
  local caster=BGX66Caster
  if type(caster)~='table' or type(caster.reservations)~='table' then return true end
  if caster.reservations[id] then return true end
  local heal=safe(function()return sprite:getLocalInt('BGX66_S_HEAL_SLOT')end)
  local ward=safe(function()return sprite:getLocalInt('BGX66_S_WARD')end)
  return not integer(heal) or not integer(ward) or heal~=0 or ward~=0
end
""", "")
    return s

def verify_exact_revert(root=None):
    root=Path(root or Path(__file__).parent)
    old=(root/'M_BX43_066S_CAPABILITY_PRE_ARBITRATION.lua').read_text(encoding='utf-8')
    new=(root/'M_BX43_066S_CAPABILITY_CANDIDATE.lua').read_text(encoding='utf-8')
    assert hashlib.sha256(old.encode('utf-8')).hexdigest()==OLD_SHA256
    assert revert(new)==old,'UNEXPECTED_CHANGED_CODE_BEYOND_FIVE_APPROVED_REGIONS'
    return True

if __name__=='__main__':
    assert verify_exact_revert()
    print('PASS: only five cross-channel arbitration edits; exact V2 source recovered')
