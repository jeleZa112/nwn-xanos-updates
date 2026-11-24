-- BGXAI: prefer CURRENT EEex active derived stats to static APR tables.
-- Pure Lua SOURCE ONLY; not installed, no EEex orders, no BCS/LOCALS writes.
-- Requires a separate audited runtime adapter. Synthetic 'verified' fields are
-- a contract for the adapter, NEVER proof of live access or authorization.
local M={}
local function ok(x,lo,hi) return type(x)=='number' and x==x and x>=lo and x<=hi end
local function ident(x) return type(x)=='string' and #x>0 and #x<=80 and not x:find('[^%w_%+%.%-]') end
local function hold(reason,weapon) return {status='HOLD_CURRENT_STATS_UNVERIFIED',reason=reason,weaponId=weapon,executable=false,dispatchAuthorized=false} end
-- Keep this narrow verified exclusion in lockstep with V3.proven_ineligible.
-- A guessed empty quiver, an unknown path, or an unverified class is NOT evidence.
local function known_ineligible(w,a)
 if type(w)~='table' or type(a)~='table' then return false end
 if w.mode=='RANGED' then
  -- Out of range is only a valid exclusion after *all* ammo provenance is
  -- complete; never let a guessed range bypass missing quiver evidence.
  local ammoConfirmed=w.ammoVerified==true and
     (w.ammunitionModel=='QUIVER' or w.ammunitionModel=='SELF') and
     type(w.ammoCount)=='number' and w.ammoCount>=0 and
     w.ammoCount<=1000000 and w.ammoCount%1==0 and
     (w.ammunitionModel~='QUIVER' or ident(w.ammoResRef))
  return ammoConfirmed and (w.ammoCount==0 or w.inRange==false)
 end
 if w.mode=='MELEE' then
  return a.canSustainMelee==false or
    (w.inRange==false and (a.pathSafeVerified==false or w.canReachWithSafeMove==false))
 end
 return false
end
function M.audit(scene)
 if type(scene)~='table' or type(scene.frame)~='table' or
   type(scene.actor)~='table' or type(scene.weapons)~='table' then return 'SCENE_INCOMPLETE' end
 local f,a=scene.frame,scene.actor
 local d=a.activeStatsEvidence
 if type(d)~='table' or d.source~='EEEX117_ACTIVE_DERIVED_STATS' or
   d.snapshotId~=f.snapshotId or d.actorId~=f.actorId or d.tick~=f.tick or
   not ident(d.activeFingerprint) or not ident(d.buffFingerprint) or
   d.equipmentFingerprint~=f.equipmentFingerprint or
   d.selectedWeaponId~=a.selectedWeaponId or
   d.activeStatsAccessProven~=true or d.allActiveEffectsObserved~=true or
   d.hasteAndImprovedHasteAccounted~=true or
   d.proficiencyClassKitIncludedOnce~=true then
  return 'ACTIVE_DERIVED_STATS_OR_BUFFS_INCOMPLETE' end
 if #scene.weapons<1 or #scene.weapons>4 then return 'LOADOUT_INCOMPLETE' end
 local selectedFound=false
 for _,w in ipairs(scene.weapons) do
  if known_ineligible(w,a) then
   -- A confirmed impossible slot needs no fictitious counterfactual APR.
   -- Its observed slot identity / ammunition is validated by V3 below.
   if w.id==a.selectedWeaponId then selectedFound=true end
  else
  local p=type(w)=='table' and w.effectiveStatsEvidence
  if type(p)~='table' or p.snapshotId~=f.snapshotId or
    p.actorId~=f.actorId or p.weaponId~=w.id or
    p.quickslotIndex~=w.quickslotIndex or
    p.activeFingerprint~=d.activeFingerprint or p.buffFingerprint~=d.buffFingerprint or
    p.equipmentFingerprint~=d.equipmentFingerprint or
    p.weaponAbilityAmmoMatched~=true or p.proficiencyAlreadyApplied~=true or
    p.buffsAlreadyApplied~=true or p.completeEffectiveWeaponStats~=true or
    not ok(p.apr,0.5,10) or not ok(p.thac0,-50,100) or
    not ok(p.damageOnHit,0,1000) or
    w.apr~=p.apr or w.finalTHAC0~=p.thac0 or
    w.avgDamageOnHit~=p.damageOnHit then
   return 'PER_SLOT_BUFF_AWARE_STATS_UNVERIFIED',w and w.id end
  if w.id==a.selectedWeaponId then
   selectedFound=true
   if p.basis~='ACTUALLY_SELECTED_WEAPON' or p.selectedStatsObserved~=true then
    return 'SELECTED_WEAPON_STATS_UNVERIFIED',w.id end
  elseif p.basis~='PROJECTED_FROM_SAME_ACTIVE_STATS' or
    p.otherWeaponRecalculated~=true then
   -- Current character-sheet APR is NOT the other weapon's APR.
   return 'OTHER_SLOT_RECALCULATION_UNVERIFIED',w.id
  end
  if a.handsMode=='DUAL' and w.mode=='MELEE' and
    p.offhandAndMainhandRatesVerified~=true then
   return 'OFFHAND_RATE_UNVERIFIED',w.id end
  end -- eligible slot requires complete final stats
 end
 if not selectedFound then return 'CURRENT_WEAPON_NOT_IN_LOADOUT' end
 return nil
end
function M.choose(scene,previous,chooseV4,chooseV3)
 local reason,weapon=M.audit(scene)
 if reason then return hold(reason,weapon) end
 if type(chooseV4)~='function' or type(chooseV3)~='function' then
  return hold('SCORERS_NOT_CONNECTED') end
 local d=scene.actor.activeStatsEvidence
 -- If haste, strength, another temporary effect or effective derived stats
 -- changes, old two-frame evidence must not enable an immediate switch.
 local same=type(previous)=='table' and
   previous.activeFingerprint==d.activeFingerprint and
   previous.buffFingerprint==d.buffFingerprint
 local result=chooseV4(scene,same and previous or nil,chooseV3)
 if type(result)~='table' then return hold('BAD_SCORER_OUTPUT') end
 if type(result.next)=='table' then
  result.next.activeFingerprint=d.activeFingerprint
  result.next.buffFingerprint=d.buffFingerprint
 end
 result.aprProvenance='EEEX_ACTIVE_STATS_AND_PER_SLOT_CONTEXT'
 result.executable=false
 result.dispatchAuthorized=false
 return result
end
return M