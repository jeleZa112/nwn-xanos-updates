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
-- SAME source-only V3 actor→target→backpack scoring, then the ORIGINAL
-- V4 uniqueness / free-slot / hysteresis planner. No predictedUtility supplied
-- by a caller is accepted here; it comes only from V3.scoreBackpackCandidate.
-- This NEVER authenticates live EEex counterfactual stats or authorizes equip.
function M.planWithV3(backpack,quick,other,scene,candidates,v3Scene,previous,v3)
 if type(v3)~='table' or type(v3.preview)~='function' or
    type(v3.scoreBackpackCandidate)~='function' or
    type(scene)~='table' or type(v3Scene)~='table' or
    type(v3Scene.frame)~='table' or type(v3Scene.actor)~='table' or
    type(v3Scene.weapons)~='table' or type(v3Scene.quickslotIds)~='table' or
    type(candidates)~='table' or type(backpack)~='table' or
    type(backpack.slots)~='table' or type(quick)~='table' or
    type(other)~='table' then
  return result('HOLD_V3_V4_BRIDGE_INPUT_INCOMPLETE') end
 local f=v3Scene.frame
 if not integer(scene.actorId,1,2147483647) or
    not integer(scene.targetActorId,1,2147483647) or
    scene.targetActorId==scene.actorId or
    f.actorId~=tostring(scene.actorId) or
    f.enemyId~=tostring(scene.targetActorId) or
    f.tick~=scene.tick or f.snapshotId~=scene.snapshotId or
    v3Scene.actor.currentTargetId~=f.enemyId or
    backpack.actorId~=scene.actorId then
  return result('HOLD_V3_V4_ACTOR_TARGET_FRAME_MISMATCH') end
 local validMap,why=mapValid(backpack,quick,other)
 if not validMap then return result(why) end
 -- Bind V3's IDs to the REAL quickslot resrefs supplied by the R37 raw map.
 for i=1,4 do
  local slot=quick[i+34]
  local id=v3Scene.quickslotIds[i]
  if slot.status=='EMPTY' then
   if id~=false then return result('HOLD_V3_V4_QUICKSLOT_IDENTITY_DRIFT') end
  else
   if type(id)~='string' then
    return result('HOLD_V3_V4_QUICKSLOT_IDENTITY_DRIFT') end
   local count=0
   for _,w in ipairs(v3Scene.weapons) do
    if w.id==id and w.slot=='QUICKSLOT' and
       w.quickslotIndex==i-1 and type(w.resRef)=='string' and
       w.resRef:upper()==slot.resref:upper() then count=count+1 end
   end
   if count~=1 then return result('HOLD_V3_V4_QUICKSLOT_IDENTITY_DRIFT') end
  end
 end
 local ok,preview=pcall(v3.preview,v3Scene,previous)
 if ok and type(preview)=='table' and
    preview.status=='HOLD_STABILIZE_TARGET_AND_EQUIPMENT' and
    preview.executable==false and preview.dispatchAuthorized==false and
    type(preview.next)=='table' then
  return result('HOLD_V3_V4_TARGET_RANKING_UNSTABLE',{v3Next=preview.next})
 end
 if not ok or type(preview)~='table' or preview.executable~=false or
    preview.dispatchAuthorized~=false or preview.passivePreview~=true or
    (preview.status~='KEEP_CURRENT' and
     preview.status~='PASSIVE_RANKING_SUGGESTS_SLOT' and
     preview.status~='HOLD_NO_EFFECTIVE_ATTACK') or
    type(preview.candidates)~='table' then
  return result('HOLD_V3_V4_TARGET_RANKING_UNSTABLE') end
 local current=nil
 for _,w in ipairs(preview.candidates) do
  if w.id==v3Scene.actor.selectedWeaponId then
   if current~=nil then return result('HOLD_V3_V4_SELECTED_AMBIGUOUS') end
   current=w
  end
 end
 if current==nil then return result('HOLD_V3_V4_SELECTED_AMBIGUOUS') end
 local currentScore,currentReason=nil,nil
 if current.available==false then
  currentScore=0
  currentReason=current.reason
 else
  currentScore=current.value
  currentReason=current.ineffectiveReason
 end
 if not finite(currentScore) then
  return result('HOLD_V3_V4_CURRENT_TARGET_SCORE_UNKNOWN') end
 -- V3 has ALREADY scored every occupied quickslot against this actor/target.
 -- Compare a backpack candidate to the BEST READY quickslot, not merely the
 -- selected weapon. Otherwise a weak backpack item can displace a stronger
 -- item that is already equipped and requires no inventory transaction.
 local readyBest=nil
 for _,ready in ipairs(preview.candidates) do
  if ready.available~=false then
   if not finite(ready.value) or type(ready.id)~='string' or
      not integer(ready.slotIndex,0,3) then
    return result('HOLD_V3_V4_READY_QUICKSLOT_SCORE_INVALID') end
   if readyBest==nil or ready.value>readyBest.value then
    readyBest=ready
   end
  end
 end
 local selectedScore=currentScore
 if readyBest~=nil and readyBest.value>currentScore then
  currentScore=readyBest.value
  currentReason=nil -- an already equipped option is better than selected
 end
 local count=0
 for k in pairs(candidates) do
  count=count+1
  if count>16 or not integer(k,1,16) then
   return result('HOLD_V3_V4_CANDIDATE_LIST_AMBIGUOUS') end
 end
 if count==0 then return result('HOLD_NO_CANDIDATE') end
 local computed={}
 for i=1,count do
  local c=candidates[i]
  if type(c)~='table' or c.predictedUtility~=nil or
     type(c.weaponModel)~='table' or
     c.weaponModel.sourceSlot~=c.sourceSlot or
     type(c.resref)~='string' or
     c.weaponModel.resRef~=c.resref:upper() then
   return result('HOLD_V3_V4_EXTERNAL_OR_MISMATCHED_SCORE') end
  local succeeded,rank=pcall(v3.scoreBackpackCandidate,v3Scene,c.weaponModel)
  if not succeeded or type(rank)~='table' or
     rank.status~='BACKPACK_TARGET_UTILITY_MODEL_ONLY' or
     rank.executable~=false or rank.dispatchAuthorized~=false or
     rank.engineFinalAlternativeStatsVerified~=false or
     rank.sourceSlot~=c.sourceSlot or
     rank.candidateResref~=c.resref:upper() or
     rank.snapshotId~=scene.snapshotId or
     rank.actorId~=f.actorId or rank.targetId~=f.enemyId or
     not finite(rank.estimatedUtility) then
   return result('HOLD_V3_V4_BACKPACK_TARGET_MODEL_UNVERIFIED',
    {sourceSlot=type(c.sourceSlot)=='number' and c.sourceSlot or nil}) end
  local cloned={}
  for k,v in pairs(c) do if k~='weaponModel' then cloned[k]=v end end
  cloned.predictedUtility=rank.estimatedUtility
  computed[i]=cloned
 end
 local linked={}
 for k,v in pairs(scene) do linked[k]=v end
 linked.currentWeaponScore=currentScore
 linked.currentWeaponScoreVerified=true
 linked.currentWeaponUnusableReason=currentReason
 linked.currentWeaponUnusableVerified=currentReason and true or nil
 local advice=M.plan(backpack,quick,other,linked,computed)
 -- This is a pure model composition; never set 'proven live' on any input.
 advice.v3V4Link='SAME_ACTOR_TARGET_BACKPACK_MODEL_ONLY'
 advice.v3Next=preview.next
 advice.selectedScoreModel=selectedScore
 advice.bestEquippedScoreModel=readyBest and readyBest.value or nil
 advice.bestEquippedWeaponId=readyBest and readyBest.id or nil
 advice.comparisonBasis='BEST_ALREADY_EQUIPPED_QUICKSLOT'
 if advice.status=='KEEP_CURRENT_NO_MEANINGFUL_GAIN' and
    readyBest~=nil and readyBest.id~=current.id then
  -- The selected weapon may be worse, but the next step is an ordinary
  -- quickslot choice, NOT an item move from the backpack.
  advice.status='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE'
  advice.suggestedQuickslotIndex=readyBest.slotIndex
 end
 advice.engineFinalAlternativeStatsVerified=false
 advice.inventoryMoveAuthorized=false
 advice.dispatchAuthorized=false
 advice.executable=false
 advice.ordersSent=0
 return advice
end
-- On-demand bridge from the EXISTING R37 action event to the existing V3
-- actor-target scorer and V4 inventory comparison. No callback registration.
-- A stable raw item map is NOT full item instance identity or final APR.
function M.planWithR37(sprite,r37,contextReader,reader,
                       scene,candidates,v3Scene,previous,v3)
 if type(reader)~='table' or type(reader.captureTopLevel)~='function' or
    type(r37)~='table' or type(contextReader)~='function' or
    type(scene)~='table' then
  return result('HOLD_R37_V4_ADAPTER_INPUT_INCOMPLETE') end
 local ok,raw=pcall(reader.captureTopLevel,sprite,r37,contextReader)
 if not ok or type(raw)~='table' or
    raw.status~='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY' or
    raw.readOnly~=true or raw.sourceOnly~=true or
    raw.dispatchAuthorized~=false or
    raw.inventoryMoveAuthorized~=false or
    raw.fullEquipmentUniquenessVerified~=false or
    raw.engineItemInstanceVerified~=false or
    raw.r37QuickQuiverOffhandMatched~=true or
    raw.alternativeAPRVerified~=false or
    raw.actorId~=scene.actorId or
    type(raw.backpack)~='table' or
    type(raw.quick)~='table' or type(raw.other)~='table' then
  return result('HOLD_R37_TOPLEVEL_RAW_MAP_UNVERIFIED',
                {priorStatus=ok and type(raw)=='table' and raw.status or nil}) end
 local advice=M.planWithV3(raw.backpack,raw.quick,raw.other,
                           scene,candidates,v3Scene,previous,v3)
 -- Even if all simulated V3 inputs are forged, item read can NEVER arm an
 -- engine command or claim complete buffs / current alternate APR.
 advice.r37InventoryMap='ON_DEMAND_TOPLEVEL0_38_SOURCE_ONLY'
 advice.nativeInventoryInstanceAuthenticated=false
 advice.alternativeAPRVerified=false
 advice.safeActionBoundaryVerified=false
 advice.manualEpsOriginVerified=false
 advice.executable=false
 advice.dispatchAuthorized=false
 advice.inventoryMoveAuthorized=false
 advice.ordersSent=0
 return advice
end
return M
