-- BGXAI WEAPON INVENTORY PRIORITY V4: corrected 16-slot dry-run planner.
-- Reuses V1 score/advisory contract, consumes V3 backpack snapshot.
-- No EEex hooks, no engine actions, no actual item movement.
local M={schema="BGXAI_BACKPACK16_PRIORITY_ADVISORY_V4",installed=false}
local function integer(x,lo,hi)
 return type(x)=="number" and x==x and x%1==0 and x>=lo and x<=hi
end
local function finite(x)
 return type(x)=="number" and x==x and x~=math.huge and x~=-math.huge
end
local function ref(x)
 return type(x)=="string" and #x>0 and #x<=8 and not x:find("[^%w_]")
end
local function result(status,detail)
 local x={schema=M.schema,status=status,readOnly=true,sourceOnly=true,
  executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  inventoryMoveAuthorized=false,ordersSent=0,localsWritten=0,
  actionQueueCleared=false,currentActionPreserved=true,
  itemTransferSemanticsVerified=false,engineFinalAlternativeStatsVerified=false,
  manualEpsOriginVerified=false,safeActionBoundaryVerified=false,
  fullItemInstanceIdentityVerified=false,gameModified=false}
 if type(detail)=="table" then for k,v in pairs(detail) do x[k]=v end end
 return x
end
-- Reuse V3's *verified current-unusable* fallback. Normal hysteresis must not
-- preserve a confirmed immune / empty / unreachable weapon against a positive
-- alternative. Source-only advice does NOT authenticate runtime evidence.
local V3_CURRENT_UNUSABLE={
  VERIFIED_TARGET_WEAPON_IMMUNITY=true,
  VERIFIED_NO_EFFECTIVE_DAMAGE_OR_EFFECT=true,
  VERIFIED_EMPTY_AMMUNITION=true,
  VERIFIED_RANGED_OUT_OF_RANGE=true,
  VERIFIED_UNSAFE_TO_TANK=true,
  VERIFIED_NO_SAFE_MELEE_PATH=true
}
local function slotValid(x,s)
 if type(x)~="table" or x.slot~=s then return false end
 if x.status=="EMPTY" then return true end
 if x.status~="PRESENT_RAW" and x.status~="OCCUPIED" then return false end
 return ref(x.resref)
end
local function otherSlot(s)
 return (s>=0 and s<=17) or s==34
end
local function mapValid(backpack,quick,other)
 for s=18,33 do
  local i=backpack.slots[s]
  if not slotValid(i,s) or
   (i.status~="PRESENT_RAW" and i.status~="EMPTY") then
   return false,"HOLD_BACKPACK16_INCOMPLETE" end
 end
 for s=35,38 do
  if not slotValid(quick[s],s) then
   return false,"HOLD_QUICKSLOT_SNAPSHOT_INCOMPLETE" end
 end
 for s=0,17 do
  if not slotValid(other[s],s) then
   return false,"HOLD_REMAINING_EQUIPMENT_INCOMPLETE" end
 end
 if not slotValid(other[34],34) then
  return false,"HOLD_REMAINING_EQUIPMENT_INCOMPLETE" end
 for k in pairs(backpack.slots) do
  if not integer(k,18,33) then return false,"HOLD_BACKPACK16_EXTRA_SLOT" end
 end
 for k in pairs(quick) do
  if not integer(k,35,38) then return false,"HOLD_QUICKSLOT_EXTRA_SLOT" end
 end
 for k in pairs(other) do
  if not integer(k,0,34) or not otherSlot(k) then
   return false,"HOLD_OTHER_EQUIPMENT_EXTRA_SLOT" end
 end
 return true
end
local function countRef(backpack,quick,other,name)
 local n=0
 for s=18,33 do
  if backpack.slots[s].status=="PRESENT_RAW" and
     backpack.slots[s].resref:upper()==name then n=n+1 end
 end
 for s=35,38 do
  if quick[s].status~="EMPTY" and
     quick[s].resref:upper()==name then n=n+1 end
 end
 for s=0,17 do
  if other[s].status~="EMPTY" and other[s].resref:upper()==name then n=n+1 end
 end
 if other[34].status~="EMPTY" and other[34].resref:upper()==name then n=n+1 end
 return n
end
-- "other" must contain every non-backpack and non-quickweapon slot 0..17,34.
-- These are TOP-LEVEL slots only. Bag-of-holding contents are not inspected.
function M.plan(backpack,quick,other,scene,candidates)
 if type(backpack)~="table" or
   backpack.status~="BACKPACK16_RAW_NOT_INSTANCE_PROOF" or
   type(backpack.slots)~="table" or
   type(quick)~="table" or type(other)~="table" or
   type(scene)~="table" or type(candidates)~="table" then
  return result("HOLD_INPUT_SNAPSHOT_INCOMPLETE") end
 if not integer(scene.actorId,1,2147483647) or
   scene.actorId~=backpack.actorId or
   not integer(scene.tick,0,1e12) or
   not ref(scene.targetResref) or
   scene.targetHostilityVerified~=true or scene.targetIdentityStable~=true or
   scene.sameAreaVerified~=true or
   type(scene.snapshotId)~="string" or #scene.snapshotId<1 or
   #scene.snapshotId>128 or
   scene.itemModelProvenance~="V3_V4_V5" or
   scene.protectionEvidenceVerified~=true or
   scene.currentWeaponScoreVerified~=true or
   not finite(scene.currentWeaponScore) or
   not integer(scene.weaponSlotCapacity,2,4) then
  return result("HOLD_SCENE_OR_MODEL_NOT_PROVEN") end
 if scene.selectedWeaponStillSame~=true or
    scene.currentEquipmentFingerprintStable~=true or
    scene.r37ActionContextStable~=true then
  return result("HOLD_EQUIPMENT_OR_ACTION_CONTEXT_DRIFT") end
 -- A plain flag or an unexplained nonpositive score is not proof of immunity.
 -- These reason names must come from the already existing V3 model, and this
 -- dry-run output remains non-executable even if the caller forges the inputs.
 local currentUnusable=false
 if scene.currentWeaponUnusableReason~=nil or
    scene.currentWeaponUnusableVerified~=nil then
  if scene.currentWeaponUnusableVerified~=true or
     V3_CURRENT_UNUSABLE[scene.currentWeaponUnusableReason]~=true then
   return result("HOLD_CURRENT_WEAPON_UNUSABLE_EVIDENCE_INCOMPLETE") end
  if scene.currentWeaponScore>0 then
   return result("HOLD_CURRENT_WEAPON_STATUS_INCONSISTENT") end
  currentUnusable=true
 end
 local ok,reason=mapValid(backpack,quick,other)
 if not ok then return result(reason) end
 local candidateCount,seenSlots,best=0,{},nil
 for k,c in pairs(candidates) do
  candidateCount=candidateCount+1
  if candidateCount>16 or not integer(k,1,16) or
      type(c)~="table" or not integer(c.sourceSlot,18,33) or
      seenSlots[c.sourceSlot] then
    return result("HOLD_CANDIDATE_LIST_AMBIGUOUS") end
  seenSlots[c.sourceSlot]=true
  local item=backpack.slots[c.sourceSlot]
  if item.status~="PRESENT_RAW" or
     not ref(c.resref) or c.resref:upper()~=item.resref or
     c.snapshotId~=scene.snapshotId or
     c.modelProvenance~="V3_V4_V5" or
     not finite(c.predictedUtility) or
     c.usabilityVerified~=true or
     c.identifiedVerified~=true or
     c.notCursedVerified~=true or
     c.notQuestItemVerified~=true or
     c.offhandCompatibilityVerified~=true or
     c.ammoAndLauncherVerified~=true or
     c.protectionsAccountedVerified~=true then
    return result("HOLD_CANDIDATE_NOT_VERIFIED",{sourceSlot=c.sourceSlot}) end
  if best==nil or c.predictedUtility>best.predictedUtility then
   best=c
  end
 end
 if candidateCount==0 then return result("HOLD_NO_CANDIDATE") end
 for k=1,candidateCount do
  if candidates[k]==nil then return result("HOLD_CANDIDATE_LIST_AMBIGUOUS") end
 end
 local margin=currentUnusable and 0 or
              math.max(2,math.abs(scene.currentWeaponScore)*0.15)
 local gain=best.predictedUtility-scene.currentWeaponScore
 if currentUnusable and best.predictedUtility<=0 then
  return result("HOLD_NO_POSITIVE_BACKPACK_ALTERNATIVE",
   {candidateResref=best.resref,estimatedGain=gain}) end
 if gain<=margin then
  return result("KEEP_CURRENT_NO_MEANINGFUL_GAIN",
   {candidateResref=best.resref,estimatedGain=gain,margin=margin}) end
 local free=nil
 for s=35,34+scene.weaponSlotCapacity do
  if quick[s].status=="EMPTY" then free=s;break end
 end
 if free==nil then
  return result("HOLD_ALL_PERMITTED_QUICKSLOTS_OCCUPIED",
   {candidateResref=best.resref,sourceSlot=best.sourceSlot,estimatedGain=gain,
    occupiedSlotSwapAllowed=false}) end
 local matches=countRef(backpack,quick,other,best.resref)
 if matches~=1 then return result("HOLD_RESREF_DUPLICATED_IN_TOP_LEVEL_SLOTS",
  {candidateResref=best.resref,sourceSlot=best.sourceSlot,observedMatches=matches}) end
 return result("ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY",{
  sourceSlot=best.sourceSlot,targetSlot=free,candidateResref=best.resref,
  estimatedGain=gain,scoreMargin=margin,
  topLevelResrefOccurrences=1,topLevelItemMappingComplete=true,
  entireInventoryUniquenessVerified=false,
  targetSpecificEffectsLiveVerified=false,
  xEquipItemTransactionVerified=false,
  nextStep="REQUIRES_NATIVE_GAME_SAFE_BOUNDARY_AND_CONSERVATION_PROOF"})
end
return M
