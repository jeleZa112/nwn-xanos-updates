-- BGXAI R36: pure Lua raw-context invalidation for the existing R33 callback.
-- SOURCE ONLY. Receives R33 R27.observe() ALREADY-CAPTURED tables, not sprite.
-- No new listener, no EEex calls, no weapon commands, no IO or game writes.
-- Equality of selected stats + nine raw slots does NOT prove active effects,
-- ammo->launcher binding, manual/EPS origin, safe action boundary or alternate APR.
local M={version='BGXAI_R36_R33_ADVICE_INVALIDATION_V1',installed=false}
local STATUS='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE'
local SCHEMA='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1'
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function ref(x)
 return type(x)=='string' and #x>=1 and #x<=8 and
   not x:find('[^A-Z0-9_#%-]')
end
local function safe(status,reason)
 return {schema='BGXAI_R36_R33_ADVICE_INVALIDATION_V1',status=status,
  reason=reason,sourceOnly=true,readOnly=true,installed=false,
  ordersSent=0,localsWritten=0,currentActionPreserved=true,
  actionQueueCleared=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  alternateEffectiveAPRVerified=false,sameBuffContextVerified=false,
  allActiveEffectsVerified=false,manualEpsOriginVerified=false,
  safeActionBoundaryVerified=false,launcherAmmoBindingVerified=false,
  cachedAdvisoryCanBeExecuted=false}
end
local function validSlot(x,slot,kind,ordinal)
 if type(x)~='table' or x.index~=slot or x.kind~=kind or
    x.ordinal~=ordinal then return nil end
 if x.access=='NULL' then
  if x.itemResrefRaw~=nil or x.useCount1Raw~=nil or
     x.useCount2Raw~=nil or x.useCount3Raw~=nil then return nil end
  return {slot,'-',-1,-1,-1,-1,-1}
 end
 if x.access~='OBJECT_RETURNED_UNVERIFIED' or not ref(x.itemResrefRaw) or
    x.resrefAccess~='RAW_RESREF_RETURNED_UNVERIFIED' then return nil end
 local c1,c2,c3=x.useCount1Raw,x.useCount2Raw,x.useCount3Raw
 if not int(c1,0,65535) or not int(c2,0,65535) or
    not int(c3,0,65535) then return nil end
 -- Optional raw fields use sentinel to avoid confusing missing with zero.
 local flags=x.flagsRaw
 if flags~=nil and not int(flags,0,4294967295) then return nil end
 local itemType=x.itemTypeRaw
 if itemType~=nil and not int(itemType,0,65535) then return nil end
 return {slot,x.itemResrefRaw,c1,c2,c3,flags or -1,itemType or -1}
end
local function gear(slots,first,kind)
 if type(slots)~='table' then return nil end
 for k in pairs(slots) do
  if not int(k,1,4) then return nil end
 end
 local out={}
 for i=1,4 do
  local x=validSlot(slots[i],first+i-1,kind,i-1)
  if not x then return nil end
  out[i]=x
 end
 return out
end
local FIELDS={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nSTRExtra',
 'm_nDamageBonus','m_nHitBonus','m_nMeleeTHAC0Bonus','m_nMissileTHAC0Bonus',
 'm_bImprovedHaste','m_nLevel1','m_nLevel2','m_nLevel3','m_nKit'}
-- R33 console JSON exports only a *subset* of these. The Lua contract uses
-- the full R33 sampledStatsRaw subset, so do NOT require stats absent from it.
local SAMPLED={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nSTRExtra',
              'm_bImprovedHaste','m_nHitBonus',
              'm_nLevel1','m_nLevel2','m_nLevel3','m_nKit'}
local LIMITS={
 m_nNumberOfAttacks={0,10},m_nTHAC0={-100,100},
 m_nSTR={0,25},m_nSTRExtra={0,100},m_bImprovedHaste={0,1},
 m_nHitBonus={-100,100},m_nLevel1={0,50},m_nLevel2={0,50},
 m_nLevel3={0,50},m_nKit={0,4294967295}
}
local function equalArray(a,b)
 if type(a)~='table' or type(b)~='table' or #a~=#b then return false end
 for i=1,#a do if a[i]~=b[i] then return false end end
 return true
end
local function equalGear(a,b)
 if type(a)~='table' or type(b)~='table' then return false end
 for i=1,9 do
  if type(a[i])~='table' or type(b[i])~='table' or
     not equalArray(a[i],b[i]) then return false end
 end
 return true
end
function M.capture(sample)
 local out=safe('HOLD_R33_CONTEXT_UNVERIFIED','R33_SOURCE_UNKNOWN')
 if type(sample)~='table' or sample.schema~=SCHEMA or
    sample.status~=STATUS or sample.readOnly~=true or
    sample.ordersSent~=0 or sample.localsWritten~=0 or
    sample.dispatchAuthorized~=false or sample.weaponSwitchAuthorized~=false or
    sample.sameLuaListenerInvocation~=true or
    sample.rawInventoryDoubleReadConsistent~=true or
    sample.selectedDerivedStatsDoubleReadConsistent~=true or
    sample.r4Status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or
    sample.alternativeAPRVerified~=false or
    sample.launcherAmmoPairVerified~=false or
    sample.completeActiveEffectsVerified~=false or
    sample.epsManualQueueVerified~=false then return out end
 if not int(sample.actor,1,2147483647) or
    not int(sample.partyIndex,0,5) or
    not int(sample.actionRaw,0,65535) or
    not int(sample.selectedWeaponRaw,0,65535) or
    not int(sample.selectedAbilityRaw,0,65535) or
    not int(sample.selectedAprKeyRaw,0,10) then
  out.reason='R33_SCALARS_INVALID';return out end
 local s=sample.sampledStatsRaw
 if type(s)~='table' then out.reason='R33_STATS_UNAVAILABLE';return out end
 local stats={}
 for i,k in ipairs(SAMPLED) do
  local lohi=LIMITS[k]
  if not int(s[k],lohi[1],lohi[2]) then
   out.reason='R33_STATS_MISSING_'..k;return out
  end
  stats[i]=s[k]
 end
 if stats[1]~=sample.selectedAprKeyRaw then
  out.reason='R33_APR_MISMATCH';return out end
 local p=sample.rawProficiencyStat89to134
 if type(p)~='table' or #p~=46 then
  out.reason='R33_PROF_46_MISSING';return out end
 local prof={}
 for i=1,46 do
  if not int(p[i],-2147483648,2147483647) then
   out.reason='R33_PROF_UNREADABLE';return out end
  prof[i]=p[i]
 end
 local weapon=gear(sample.quickWeaponsRaw,35,'QUICKWEAPON')
 local quiver=gear(sample.quiversRaw,11,'QUIVER')
 local off=validSlot(sample.offhandRaw,9,'OFFHAND_OR_SHIELD',0)
 if weapon==nil or quiver==nil or off==nil then
  out.reason='R33_RAW_GEAR_INCOMPLETE';return out end
 local all={}
 for _,t in ipairs(weapon) do all[#all+1]=t end
 for _,t in ipairs(quiver) do all[#all+1]=t end
 all[#all+1]=off
 local q=sample.queueSnapshotStable==true and sample.queuedActionsRaw or nil
 if q~=nil and not int(q,0,512) then out.reason='R33_QUEUE_INVALID';return out end
 out.status='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY';out.reason=nil
 out.actor=sample.actor
 out.party=sample.partyIndex
 out.selected=sample.selectedWeaponRaw
 out.ability=sample.selectedAbilityRaw
 out.actionRaw=sample.actionRaw
 out.stats=stats;out.profRaw=prof;out.gear=all
 out.queueRaw=q
 out.actionSourceRaw=sample.actionSourceStable==true and sample.actionSourceRaw or nil
 out.actionSourceSemantics='UNKNOWN'
 out.sourceIsSameCallbackR33=true
 return out
end
function M.compare(before,after)
 local out=safe('HOLD_CONTEXT_COMPARISON','CAPTURE_UNVERIFIED')
 if type(before)~='table' or type(after)~='table' or
    before.schema~=out.schema or after.schema~=out.schema or
    before.status~='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY' or
    after.status~='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY' then return out end
 if before.actor~=after.actor or before.party~=after.party then
  out.reason='ACTOR_OR_PARTY_CHANGED';return out end
 out.reason=nil
 local selection=before.selected~=after.selected or before.ability~=after.ability
 local items=not equalGear(before.gear,after.gear)
 local stats=not equalArray(before.stats,after.stats) or
             not equalArray(before.profRaw,after.profRaw)
 local action=before.actionRaw~=after.actionRaw or
   before.queueRaw~=after.queueRaw or
   before.actionSourceRaw~=after.actionSourceRaw
 if selection then out.status='NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE'
 elseif items then out.status='EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE'
 elseif stats then out.status='OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE'
 elseif action then out.status='ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE'
 else out.status='RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF' end
 out.invalidateCachedAdvice=selection or items or stats or action
 out.weaponCommandsAllowed=false
 out.observedAmmoDeltaInR33Raw=false
 -- Raw evidence can say a quantity changed; it cannot prove a shot was fired.
 if items then
  for i=1,9 do
   if before.gear[i][1]>=11 and before.gear[i][1]<=14 and
      before.gear[i][2]==after.gear[i][2] and
      before.gear[i][3]~=after.gear[i][3] then
    out.observedAmmoDeltaInR33Raw=true
   end
  end
 end
 return out
end
return M
