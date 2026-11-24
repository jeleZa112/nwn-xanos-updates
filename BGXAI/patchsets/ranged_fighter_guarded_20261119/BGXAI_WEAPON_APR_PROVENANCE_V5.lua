-- BGXAI Weapon Priority V5: proficiency/level APR provenance before V4/V3.
-- Source only; NO game hook, LOCALS, order, filesystem, installation or resource edit.
-- Verified live EET adapter DOES NOT YET EXIST. A caller supplied 'verified'
-- cannot turn this into permission to dispatch. Require installed WSPATCK.2DA
-- and CLSWPBON.2DA + ability/weapon/proficiency mapping; never add their
-- bonus to already-final engine APR. WSPATCK contains LEVEL + PIP effects.
local M={}
local function finite(x) return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge end
local function valid(x,lo,hi) return finite(x) and x>=lo and x<=hi end
local function integer(x,lo,hi) return valid(x,lo,hi) and x%1==0 end
local function sha(s) return type(s)=='string' and #s==64 and not s:find('[^%da-fA-F]') end
local function ident(s) return type(s)=='string' and #s>=1 and #s<=80 and not s:find('[^%w_%.%+%-]') end
local function hold(reason,weapon) return {status='HOLD_APR_PROVENANCE_UNVERIFIED',reason=reason,weaponId=weapon,
 executable=false,dispatchAuthorized=false} end
-- IESDP WSPATCK encoding: -1 means half APR; -2 means 1.5 APR;
-- nonnegative values represent integer APR. Table is not an extra delta
-- over a separately applied fighter-level APR: it includes that already.
function M.decode_wspatck(raw)
 if not integer(raw,-10,10) then return nil end
 if raw<0 then return -raw-0.5 end
 return raw
end
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
local function check(scene)
 if type(scene)~='table' or type(scene.frame)~='table' or
    type(scene.actor)~='table' or type(scene.weapons)~='table' or
    #scene.weapons<1 or #scene.weapons>4 then return 'SCENE_INCOMPLETE' end
 local f,a=scene.frame,scene.actor
 local data=scene.aprSource
 if type(data)~='table' or not sha(data.wspatckSha256) or
    not sha(data.clswpbonSha256) or data.snapshotId~=f.snapshotId or
    data.modFingerprint~=a.traitProfile.modFingerprint or
    data.source~='INSTALLED_EET_RESOURCE_SNAPSHOT' or
    data.tableContentsComplete~=true or data.classEligibilityComplete~=true or
    not ident(data.classOrKitRow) or data.classOrKitRow~=a.aprClassRow or
    data.activeDualMultiClassVerified~=true then
  return 'INSTALLED_APR_TABLES_OR_CLASS_UNKNOWN' end
 for _,w in ipairs(scene.weapons) do
  if type(w)~='table' or type(w.id)~='string' then
   return 'WEAPON_APR_AUDIT_MISSING',w and w.id end
  if not known_ineligible(w,a) then
  if type(w.aprAudit)~='table' then return 'WEAPON_APR_AUDIT_MISSING',w.id end
  local t=w.aprAudit
  if not integer(t.proficiencyRank,0,5) or not integer(t.classLevel,1,50) or
      not integer(t.tableRank,0,5) or t.tableRank~=t.proficiencyRank or
      not integer(t.tableLevel,1,50) or t.tableLevel~=t.classLevel or
      t.proficiencyWeaponGroup~=w.weaponGroup or
      t.weaponGroupMatchedInstalledIds~=true or
      t.proficiencyRankObservedFromActiveClasses~=true or
      t.activeClassAprEligibilityVerified~=true or
      type(t.classEligibleForProfApr)~='boolean' or
      t.snapshotId~=f.snapshotId or t.modFingerprint~=data.modFingerprint or
      t.wspatckSha256~=data.wspatckSha256 or
      t.clswpbonSha256~=data.clswpbonSha256 or
      t.classOrKitRow~=data.classOrKitRow or
      t.tableRowAndLevelMatchedInstalledEET~=true then
   return 'PROFICIENCY_RANK_CLASS_OR_TABLE_STALE',w.id end
  if t.rateRule~='WSPATCK_APPLIES' and t.rateRule~='FIXED_RATE_OVERRIDES' then
   return 'SPECIAL_RATE_OF_FIRE_RULE_UNKNOWN',w.id end
  local tableAPR=M.decode_wspatck(t.wspatckRawValue)
  if tableAPR==nil or not valid(t.decodedTableApr,0,10) or
     math.abs(t.decodedTableApr-tableAPR)>1e-8 then
   return 'WSPATCK_VALUE_INVALID',w.id end
  -- WSPATCK includes both the proficiency and level contributions. It must
  -- never be applied a second time after getting final engine APR.
  local tableUse=(t.rateRule=='WSPATCK_APPLIES' and t.classEligibleForProfApr)
  local expected=tableUse and tableAPR or 0
  if not valid(t.tableAprContributionToEngine,0,10) or
     math.abs(t.tableAprContributionToEngine-expected)>1e-8 then
   return 'WSPATCK_ALREADY_INCLUDED_OR_OVERRIDDEN',w.id end
  if t.finalAprBasis~='ENGINE_FINAL_EFFECTIVE' or
      t.engineFinalAprIncludesTableOnce~=true or
      t.engineFinalAprIncludesEquipmentAndBuffsOnce~=true or
      t.activeHasteStateVerified~=true or
      not valid(t.finalAprObserved,0.5,10) or
      not valid(w.apr,0.5,10) or
      math.abs(t.finalAprObserved-w.apr)>1e-8 then
   return 'FINAL_APR_NOT_OBSERVED_OR_DOUBLE_COUNTED',w.id end
  if a.handsMode=='DUAL' and w.mode=='MELEE' and
      (t.offhandRateAndAccuracyVerified~=true or
       t.offhandDamageRateWeightedVerified~=true) then
   return 'OFFHAND_APR_AGGREGATION_UNKNOWN',w.id end
  end -- only check final APR for candidates capable of attacking
 end
 return nil,nil
end
M.audit=check
function M.choose(scene,previous,chooseV4,chooseV3)
 local reason,which=check(scene)
 if reason then return hold(reason,which) end
 if type(chooseV4)~='function' or type(chooseV3)~='function' then
  return hold('V4_V3_NOT_CONNECTED') end
 local out=chooseV4(scene,previous,chooseV3)
 if type(out)~='table' then return hold('UNDERLYING_PRIORITY_INVALID') end
 out.executable=false;out.dispatchAuthorized=false
 out.aprProvenance='WSPATCK_CLSWPBON_FINAL_EFFECTIVE_NO_DOUBLE_COUNT'
 return out
end
return M