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
 if count==0 then
  -- No backpack candidate need not block a superior READY quickslot.
  if readyBest and readyBest.id~=current.id and readyBest.value>selectedScore then
   return result('PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE',{
    v3V4Link='SAME_ACTOR_TARGET_BACKPACK_MODEL_ONLY',
    v3Next=preview.next,selectedScoreModel=selectedScore,
    bestEquippedScoreModel=readyBest.value,
    bestEquippedWeaponId=readyBest.id,
    suggestedQuickslotIndex=readyBest.slotIndex,
    comparisonBasis='BEST_ALREADY_EQUIPPED_QUICKSLOT',
    backpackCandidateCount=0})
  end
  return result('KEEP_CURRENT_NO_BACKPACK_CANDIDATE',{
   v3Next=preview.next,selectedScoreModel=selectedScore,
   comparisonBasis='BEST_ALREADY_EQUIPPED_QUICKSLOT',
   backpackCandidateCount=0})
 end
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

-- ONE discovery pass through the EXISTING R37/R3 source route: read exactly
-- the correct sixteen backpack slots 18..33, rather than hand-entering each
-- weapon. The caller's actor-specific projection must be explicitly modeled.
-- ITM facts are real source bytes; hypothetical effective APR/THAC0 are NOT.
function M.prepare16FromR3(raw,r3,projection)
 if type(raw)~='table' or
    raw.status~='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY' or
    raw.rawInventoryDoubleRead~=true or raw.r37QuickQuiverOffhandMatched~=true or
    type(raw.backpack)~='table' or type(raw.backpack.slots)~='table' or
    type(raw.quick)~='table' or type(raw.other)~='table' or
    type(r3)~='table' or
    r3.inventoryLinkSchema~='BGXAI_R3_R37_TOPLEVEL_ITM_JOIN_SOURCE_ONLY_V1' or
    r3.sourceKind~='CURRENT_GAME' or
    r3.status~='ITM_NATIVE_ALL_ITEMS_RAW_READ' or
    r3.nativeRuntimeInventorySnapshotAuthenticated~=false or
    r3.nativeCurrentAlternativeAPRVerified~=false or
    r3.dispatchAuthorized~=false or r3.inventoryTransferAuthorized~=false or
    type(r3.items)~='table' or type(r3.inventoryRawMap)~='table' or
    type(projection)~='function' then
  return nil,'HOLD_R3_16_SLOT_INPUT_OR_PROVENANCE_INCOMPLETE' end
 -- R3 is an older resource audit, not a same-tick native instance proof.
 -- Compare ALL top-level names, not just the intended source item.
 for slot=0,38 do
  local observed=slot>=18 and slot<=33 and raw.backpack.slots[slot] or
      slot>=35 and raw.quick[slot] or raw.other[slot]
  local archived=r3.inventoryRawMap[slot] or r3.inventoryRawMap[tostring(slot)]
  if type(observed)~='table' or type(archived)~='table' or
     observed.slot~=slot or archived.slot~=slot or
     observed.status~=archived.status or observed.resref~=archived.resref then
   return nil,'HOLD_R3_TOPLEVEL_ITEM_CHANGED_OR_UNMAPPED' end
 end
 local candidates={}
 for slot=18,33 do
  local observed=raw.backpack.slots[slot]
  if observed.status=='PRESENT_RAW' then
   local entry=r3.items[observed.resref]
   if type(entry)~='table' or
      type(entry.item)~='table' or
      entry.item.schema~='BGXAI_ITM_RAW_V1' or
      type(entry.item.abilities)~='table' or
      type(entry.provenance)~='table' or
      (entry.provenance.origin~='CURRENT_GAME_BIFF' and
       entry.provenance.origin~='CURRENT_GAME_OVERRIDE') then
    return nil,'HOLD_R3_ITM_RESOURCE_MISSING' end
   local success,p=pcall(projection,slot,observed,entry.item)
   if not success or type(p)~='table' then
    return nil,'HOLD_R3_PROJECTOR_UNAVAILABLE' end
   if p.status=='CANNOT_USE_OR_NOT_WEAPON' then
    if p.weaponModel~=nil then
     return nil,'HOLD_R3_SKIPPED_ITEM_MODEL_FORGED' end
   elseif p.status=='MODELED_WEAPON_CANDIDATE' then
    local w=p.weaponModel
    local abilityIndex=p.abilityIndex
    if type(w)~='table' or
       not integer(abilityIndex,0,63) or
       type(entry.item.abilities[abilityIndex+1])~='table' or
       w.sourceSlot~=slot or w.slot~='BACKPACK' or
       w.resRef~=observed.resref or
       w.counterfactualBasis~='MODEL_ONLY_NOT_NATIVE_EFFECTIVE' or
       w.alternativeEffectiveStatsLiveVerified~=false or
       p.predictedUtility~=nil then
      return nil,'HOLD_R3_PROJECTED_WEAPON_NOT_SOURCE_BOUND' end
    -- The attack type is read from the actual ITM ability, not guessed from
    -- resref, skill, selected weapon or character's currently shown APR.
    local attack=entry.item.abilities[abilityIndex+1].attackTypeRaw
    if (attack==1 and w.mode~='MELEE') or
       (attack==2 and w.mode~='RANGED') or
       (attack~=1 and attack~=2) then
      return nil,'HOLD_R3_ITEM_ABILITY_MODE_MISMATCH' end
    candidates[#candidates+1]={
     sourceSlot=slot,resref=observed.resref,snapshotId=w.snapshotId,
     modelProvenance='V3_V4_V5',
     usabilityVerified=p.usabilityVerified,
     identifiedVerified=p.identifiedVerified,
     notCursedVerified=p.notCursedVerified,
     notQuestItemVerified=p.notQuestItemVerified,
     offhandCompatibilityVerified=p.offhandCompatibilityVerified,
     ammoAndLauncherVerified=p.ammoAndLauncherVerified,
     protectionsAccountedVerified=p.protectionsAccountedVerified,
     weaponModel=w}
   else
    return nil,'HOLD_R3_PROJECTOR_UNKNOWN_STATUS' end
  elseif observed.status~='EMPTY' then
   return nil,'HOLD_R3_UNSUPPORTED_BACKPACK_SLOT' end
 end
 return candidates,nil
end

-- Single target-bound decision output for both already-equipped and backpack
-- weapons. The engine dispatcher remains the EXISTING R39/actor-local BAF,
-- which is NOT connected here until manual/EPS/round safety is proven live.
function M.planBattleDecision(advice,r37,scene)
 if type(advice)~='table' or advice.readOnly~=true or
    advice.sourceOnly~=true or advice.executable~=false or
    advice.dispatchAuthorized~=false or advice.inventoryMoveAuthorized~=false or
    type(r37)~='table' or
    r37.schema~='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1' or
    r37.status~='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE' or
    r37.sameLuaListenerInvocation~=true or r37.queueSnapshotStable~=true or
    r37.dispatchAuthorized~=false or r37.ordersSent~=0 or
    r37.manualEpsQueueVerified~=false or r37.actionOriginVerified~=false or
    type(scene)~='table' or scene.actorId~=r37.actor or
    not integer(scene.targetActorId,1,2147483647) or
    scene.targetActorId==scene.actorId or
    type(scene.snapshotId)~='string' or
    not integer(scene.tick,0,1e12) or
    not integer(r37.queuedActionsRaw,0,512) then
  return result('HOLD_BATTLE_EVIDENCE_OR_ACTION_CONTEXT_INCOMPLETE') end
 local kind,target,source,name
 if advice.status=='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE' then
  kind='SELECT_ALREADY_EQUIPPED_QUICKSLOT'
  target=advice.suggestedQuickslotIndex
  name=advice.bestEquippedWeaponId
  if not integer(target,0,3) or type(name)~='string' then
   return result('HOLD_READY_WEAPON_INTENT_INVALID') end
 elseif advice.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY' then
  kind='EQUIP_BACKPACK_TO_EMPTY_QUICKSLOT'
  target=advice.targetSlot
  source=advice.sourceSlot
  name=advice.candidateResref
  if not integer(target,35,38) or not integer(source,18,33) or
     not ref(name) or advice.topLevelResrefOccurrences~=1 or
     advice.topLevelItemMappingComplete~=true then
   return result('HOLD_BACKPACK_ITEM_INTENT_INVALID') end
 else
  return result('KEEP_CURRENT_ACTION_OR_UNPROVEN_GAIN',{
   modelAdviceStatus=advice.status}) end
 local pending={kind=kind,actorId=scene.actorId,
  targetActorId=scene.targetActorId,snapshotId=scene.snapshotId,
  tick=scene.tick,sourceSlot=source,targetSlot=target,
  weaponIdOrResref=name,
  modelOnly=true,manualEpsOriginVerified=false,
  safeRoundBoundaryVerified=false,requireTypedNativeInstall=true}
 local state=r37.queuedActionsRaw>0 and
   'DEFER_KNOWN_NONEMPTY_ACTION_QUEUE' or
   'STAGE_DECISION_AWAIT_INDEPENDENT_MANUAL_EPS_ROUND_PROOF'
 return result(state,{
  pendingWeaponChange=pending,modelAdviceStatus=advice.status,
  queuedActionsRaw=r37.queuedActionsRaw,
  currentlyExecutingActionRaw=r37.actionRaw,
  engineActionCalls=0,
  actionQueueNotCleared=true,
  nativeEmptyQueueNotTreatedAsSafeBoundary=true})
end



-- One batch entry point. Reuses R37, R3 and V3/V4 directly, not a second
-- observer, scorer, item parser, executor or updater. The game's AI action
-- queue is never touched. If known busy, avoid even the 39-slot heavy read.
function M.planAutoBatch(sprite,r37,contextReader,reader,r3,projection,
                         scene,v3Scene,previousV3,v3)
 if type(r37)~='table' or
    r37.schema~='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1' or
    r37.status~='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE' or
    r37.queueSnapshotStable~=true or
    r37.sameLuaListenerInvocation~=true or
    r37.dispatchAuthorized~=false or
    r37.ordersSent~=0 or
    r37.actionOriginVerified~=false or
    r37.manualEpsQueueVerified~=false or
    type(scene)~='table' or
    scene.actorId~=r37.actor or
    type(reader)~='table' or
    type(reader.captureTopLevel)~='function' or
    type(contextReader)~='function' or
    type(v3)~='table' or type(v3.preview)~='function' or
    not integer(r37.queuedActionsRaw,0,512) then
  return result('HOLD_AUTOBATCH_EVENT_CONTRACT_INCOMPLETE') end
 if r37.queuedActionsRaw>0 then
  -- A queue can contain an uninterrupted attack or an EPS/manual order.
  -- Skip both R37 inventory scanning and ranking when known busy.
  return result('PRESERVE_KNOWN_ACTION_QUEUE_NO_SCAN',{
   knownQueuedActions=r37.queuedActionsRaw,
   inventoryCaptureCalls=0,scorerCalls=0})
 end
 local ok,raw=pcall(reader.captureTopLevel,sprite,r37,contextReader)
 if not ok or type(raw)~='table' or
    raw.status~='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY' or
    raw.readOnly~=true or raw.sourceOnly~=true or
    raw.dispatchAuthorized~=false or
    raw.inventoryMoveAuthorized~=false or
    raw.actorId~=scene.actorId then
  return result('HOLD_AUTOBATCH_R37_RAW_SNAPSHOT',{
   r37CaptureStatus=ok and type(raw)=='table' and raw.status or nil}) end
 local candidates,err=M.prepare16FromR3(raw,r3,projection)
 if not candidates then
  return result('HOLD_AUTOBATCH_R3_ITEM_JOIN',{reason=err}) end
 local advice=M.planWithV3(raw.backpack,raw.quick,raw.other,
                           scene,candidates,v3Scene,previousV3,v3)
 if advice.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE' then
  return result('HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE',{
   v3Next=advice.v3Next,candidateCount=#candidates,
   inventoryCaptureCalls=1}) end
 local action=M.planBattleDecision(advice,r37,scene)
 action.v3Next=advice.v3Next
 action.candidateCount=#candidates
 action.inventoryCaptureCalls=1
 action.r3ItemSourcesCrosschecked=true
 action.nativeEffectiveAlternateAprVerified=false
 action.manualEpsOriginVerified=false
 action.safeActionBoundaryVerified=false
 action.executable=false
 action.dispatchAuthorized=false
 action.inventoryMoveAuthorized=false
 action.ordersSent=0
 return action
end



-- Use the EXISTING R13 target defense reader in the SAME decision pass.
-- EEex v1.1.7 has GetActiveStats and GameObject_Get, unlike the unsupported
-- newer attack-info API. R13 is raw defense evidence, not immunity / hostility
-- or native counterfactual APR proof. A 105/134 action remains in progress.
-- This wrapper does not register an action listener or execute any action.
function M.planAutoBatchWithR13(p)
 if type(p)~='table' or type(p.r37)~='table' or
    type(p.scene)~='table' or type(p.v3Scene)~='table' or
    type(p.v3Scene.frame)~='table' or
    type(p.v3Scene.enemy)~='table' or
    type(p.v3Scene.enemy.protections)~='table' or
    type(p.r13)~='table' or type(p.r13.inspect)~='function' or
    type(p.context)~='table' or
    type(p.api)~='table' then
  return result('HOLD_AUTOBATCH_R13_INPUT_INCOMPLETE') end
 -- Don't read the target or backpack while an attack / EPS order is queued.
 -- planAutoBatch already verifies the original R27 action/queue contract.
 if integer(p.r37.queuedActionsRaw,1,512) then
  local skip=M.planAutoBatch(p.sprite,p.r37,p.contextReader,p.reader,
     p.r3,p.projection,p.scene,p.v3Scene,p.previousV3,p.v3)
  if skip.status=='PRESERVE_KNOWN_ACTION_QUEUE_NO_SCAN' then
   skip.r13ObserveCalls=0
  end
  return skip
 end
 local c=p.context
 local f=p.v3Scene.frame
 local e=p.v3Scene.enemy
 if not integer(c.actor,1,2147483647) or
    not integer(c.targetActor,1,2147483647) or
    not integer(c.actionRaw,0,65535) or
    not integer(c.selectedSlot,35,38) or
    not integer(c.selectedAbility,0,255) or
    not integer(p.r37.selectedWeaponRaw,35,38) or
    not integer(p.r37.selectedAbilityRaw,0,255) or
    c.actor~=p.r37.actor or c.actor~=p.scene.actorId or
    c.targetActor~=p.scene.targetActorId or
    c.actionRaw~=p.r37.actionRaw or
    c.selectedSlot~=p.r37.selectedWeaponRaw or
    c.selectedAbility~=p.r37.selectedAbilityRaw or
    c.snapshotId~=p.scene.snapshotId or
    c.snapshotId~=f.snapshotId or
    tostring(c.targetActor)~=f.enemyId or
    tostring(c.actor)~=f.actorId or
    tostring(c.targetActor)~=e.enemyId or
    c.readOnlyContextOnly~=true or c.switchAttempted~=false or
    c.manualEPSBoundaryProven~=false then
  return result('HOLD_AUTOBATCH_R13_R27_ACTOR_TARGET_ACTION_MISMATCH') end
 local ok,target=pcall(p.r13.inspect,p.sprite,p.action,p.api,c)
 if not ok or type(target)~='table' or
    target.schema~='BGXAI_R13_TARGET_DEFENSE_OBSERVER_V1' or
    target.status~='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY' or
    target.rawDefenseFieldsComplete~=true or
    target.activeStatsNotTempDoubleRead~=true or
    target.nativeEvidenceAuthenticated~=false or
    target.liveReadVerified~=false or
    target.hostileTargetProven~=false or
    target.alternateSlotAPRVerified~=false or
    target.dispatchAuthorized~=false or
    target.weaponSwitchAuthorized~=false or
    target.sourceActor~=c.actor or target.targetActor~=c.targetActor or
    target.rawActionId~=c.actionRaw or
    target.selectedSlot~=c.selectedSlot or
    target.selectedAbility~=c.selectedAbility or
    target.snapshotId~=c.snapshotId or
    type(target.rawFields)~='table' then
  return result('HOLD_AUTOBATCH_R13_TARGET_DEFENSE_UNSTABLE',{
    r13Status=ok and type(target)=='table' and target.status or nil,
    r13Reason=ok and type(target)=='table' and target.reason or nil}) end
 local d=target.rawFields
 local base=d.m_nArmorClass
 if not integer(base,-50,100) then
  return result('HOLD_AUTOBATCH_R13_TARGET_AC_OUTSIDE_MODEL') end
 local acMap={}
 local mods={CRUSHING='m_nACCrushingMod',PIERCING='m_nACPiercingMod',
             SLASHING='m_nACSlashingMod',MISSILE='m_nACMissileMod'}
 for kind,field in pairs(mods) do
  local modifier=d[field]
  if not integer(modifier,-200,200) or
     not integer(base+modifier,-50,100) then
   return result('HOLD_AUTOBATCH_R13_TYPE_AC_UNSUPPORTED',{acKind=kind}) end
  acMap[kind]=base+modifier
 end
 -- R13 read these specific four fields; percent -> V3 fractional reduction.
 -- Unknown enhanced effects/absorption/immunity must NEVER be inferred.
 local resist={}
 local names={CRUSHING='m_nResistCrushing',PIERCING='m_nResistPiercing',
              SLASHING='m_nResistSlashing',MISSILE='m_nResistMissile'}
 for kind,field in pairs(names) do
  local raw=d[field]
  if not integer(raw,0,100) then
   return result('HOLD_AUTOBATCH_R13_RESISTANCE_OUTSIDE_MODEL',
     {resistanceKind=kind}) end
  resist[kind]=raw/100
 end
 local function copy(src)
  local v={}
  for k,x in pairs(src) do v[k]=x end
  return v
 end
 local cloned=copy(p.v3Scene)
 local newEnemy=copy(e)
 local newProtections=copy(e.protections)
 newProtections.resistance=copy(e.protections.resistance)
 for kind,value in pairs(resist) do newProtections.resistance[kind]=value end
 newEnemy.protections=newProtections
 newEnemy.armorClass=base
 newEnemy.targetArmorClassBaseCandidate=base
 newEnemy.targetArmorClassByAttackTypeCandidate=acMap
 newEnemy.targetTypeACModelStatus='R13_DERIVED_ATTACK_TYPE_AC_MODEL_ONLY'
 newEnemy.targetTypeACModelSnapshotId=f.snapshotId
 newEnemy.targetTypeACNativeAuthenticated=false
 cloned.enemy=newEnemy
 local advice=M.planAutoBatch(p.sprite,p.r37,p.contextReader,p.reader,
  p.r3,p.projection,p.scene,cloned,p.previousV3,p.v3)
 -- Never mutate the caller's scene and never manufacture target protections.
 advice.r13DefensesReadFromSameAttack=true
 advice.r13NativeRuntimeAuthenticated=false
 advice.r13SnapshotId=c.snapshotId
 advice.r13ActorId=c.actor
 advice.r13TargetId=c.targetActor
 advice.r13ActionId=c.actionRaw
 advice.r13AttackTypeACModel=acMap
 advice.r13PhysicalResistancesModel=resist
 advice.r13AllImmunitiesKnown=false
 advice.nativeEffectiveAlternateAprVerified=false
 advice.dispatchAuthorized=false
 advice.inventoryMoveAuthorized=false
 advice.executable=false
 advice.ordersSent=0
 return advice
end


-- Complete SOURCE-only join of ACTOR and TARGET in the SAME R27 started
-- action. Reuses existing R35 selected APR/THAC0 and R13 defensive reader.
-- Unlike EEex v1.3 AttackInfo, both use functions documented in EEex 1.1.7.
-- This rejects stale actor APR and actor changes; it does NOT calculate
-- effective APR/THAC0 for every alternative and does NOT authorize a switch.
function M.planAutoBatchWithActorTarget(p)
 if type(p)~='table' or type(p.r35)~='table' or
    type(p.r35.observe)~='function' or
    type(p.r37)~='table' or
    type(p.v3Scene)~='table' or
    type(p.v3Scene.actor)~='table' or
    type(p.v3Scene.weapons)~='table' or
    type(p.statsReader)~='function' then
  return result('HOLD_AUTOBATCH_ACTOR_TARGET_INPUT_INCOMPLETE') end
 if integer(p.r37.queuedActionsRaw,1,512) then
  -- Even actor-stat reads are unnecessary during an ongoing/queued action.
  return M.planAutoBatchWithR13(p)
 end
 local function observed()
  local success,o=pcall(p.r35.observe,p.sprite,p.statsReader)
  if not success or type(o)~='table' or
     o.schema~='BGXAI_R35_SELECTED_ENGINE_STATS_RO_V1' or
     o.status~='SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE' or
     o.source~='EEEX_ACTIVE_DERIVED_STATS_CURRENT_SELECTED' or
     o.actorRaw~=p.r37.actor or
     o.selectedSlotRaw~=p.r37.selectedWeaponRaw or
     o.selectedAbilityRaw~=p.r37.selectedAbilityRaw or
     o.liveSameCallbackDoubleRead~=true or
     o.activeStatsNotTempObserved~=true or
     o.otherSlotEffectiveAPRVerified~=false or
     o.dispatchAuthorized~=false or
     o.weaponSwitchAuthorized~=false or
     o.manualAndEPSOriginVerified~=false or
     o.matchedBuffContextVerified~=false or
     not integer(o.selectedTHAC0Raw,-100,100) or
     type(o.selectedAPRIfStandardDecoder)~='number' then
   return nil
  end
  return o
 end
 local first=observed()
 if not first then return result('HOLD_AUTOBATCH_R35_SELECTED_STATS_UNAVAILABLE') end
 local slot=first.selectedSlotRaw
 if not integer(slot,35,38) then
  return result('HOLD_AUTOBATCH_R35_SELECTED_QUICKSLOT_UNMAPPED') end
 local quick=p.r37.quickWeaponsRaw
 local row=type(quick)=='table' and quick[slot-34] or nil
 local found=nil
 for _,w in ipairs(p.v3Scene.weapons) do
  if type(w)=='table' and w.id==p.v3Scene.actor.selectedWeaponId then
   if found~=nil then
    return result('HOLD_AUTOBATCH_R35_SELECTED_MODEL_AMBIGUOUS') end
   found=w
  end
 end
 if type(row)~='table' or
    row.index~=slot or
    row.access~='OBJECT_RETURNED_UNVERIFIED' or
    type(row.itemResrefRaw)~='string' or
    type(found)~='table' or found.slot~='QUICKSLOT' or
    found.quickslotIndex~=slot-35 or
    found.resRef~=row.itemResrefRaw:upper() or
    type(found.apr)~='number' or
    found.apr~=first.selectedAPRIfStandardDecoder then
  return result('HOLD_AUTOBATCH_SELECTED_WEAPON_APR_OR_IDENTITY_MISMATCH',{
    selectedSlot=slot,
    selectedAprRaw=first.selectedAPRKeyRaw,
    selectedAprDecoded=first.selectedAPRIfStandardDecoder}) end
 local advice=M.planAutoBatchWithR13(p)
 if advice.status~='HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE' and
    advice.status~='STAGE_DECISION_AWAIT_INDEPENDENT_MANUAL_EPS_ROUND_PROOF' and
    advice.status~='KEEP_CURRENT_ACTION_OR_UNPROVEN_GAIN' and
    advice.status~='DEFER_KNOWN_NONEMPTY_ACTION_QUEUE' then
  return advice
 end
 -- An actor whose attack stats changed while R13/R37 looked at the target
 -- must not reuse a now-obsolete V3 preference token.
 local final=observed()
 if not final or first.actorRaw~=final.actorRaw or
    first.selectedSlotRaw~=final.selectedSlotRaw or
    first.selectedAbilityRaw~=final.selectedAbilityRaw or
    first.selectedAPRKeyRaw~=final.selectedAPRKeyRaw or
    first.selectedTHAC0Raw~=final.selectedTHAC0Raw then
  return result('HOLD_AUTOBATCH_ACTOR_STATS_DRIFT_DURING_TARGET_READ') end
 advice.r35SelectedAprObservedUnderEeexV117=true
 advice.r35SelectedAprModelMatched=true
 advice.r35SelectedApr=first.selectedAPRIfStandardDecoder
 advice.r35SelectedThac0Raw=first.selectedTHAC0Raw
 advice.r35OtherWeaponAprVerified=false
 advice.r35OtherWeaponThac0Verified=false
 advice.nativeEffectiveAlternateAprVerified=false
 advice.executable=false
 advice.inventoryMoveAuthorized=false
 advice.dispatchAuthorized=false
 advice.ordersSent=0
 return advice
end

return M
