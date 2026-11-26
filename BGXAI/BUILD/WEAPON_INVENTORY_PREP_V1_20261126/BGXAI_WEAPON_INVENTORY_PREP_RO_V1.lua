-- BGXAI inventory-aware loadout planning, SOURCE ONLY, not installed.
-- A pure adapter from the existing EEex R2 m_items:get(slot) access pattern.
-- Only observes BACKPACK slots 15..34. It does not register an EEex hook.
-- Nothing here calls an engine action, mutates equipment, or sends orders.
local M={schema='BGXAI_INVENTORY_PREP_SOURCE_RO_V1',installed=false}
local function integer(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function finite(x)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge
end
local function ref(x) return type(x)=='string' and #x>=1 and #x<=8 and not x:find('[^%w_]') end
local function safe(f)
 local ok,v=pcall(f)
 if ok then return v end
 return nil
end
local function field(x,k)
 if x==nil then return nil end
 return safe(function() return x[k] end)
end
local function result(status,detail)
 local o={schema=M.schema,status=status,readOnly=true,executable=false,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,ordersSent=0,
  gameFilesChanged=false,sourceOnly=true,actionQueueCleared=false,
  currentActionPreserved=true}
 if type(detail)=='table' then for k,v in pairs(detail) do o[k]=v end end
 return o
end
local function item_at(items,slot)
 local getter=field(items,'get')
 if type(getter)~='function' then return {slot=slot,status='UNREADABLE_ARRAY'} end
 local ok,item=pcall(function() return getter(items,slot) end)
 if not ok then return {slot=slot,status='READ_ERROR'} end
 if item==nil then return {slot=slot,status='EMPTY'} end
 local cr=field(item,'cResRef')
 local val=cr~=nil and field(cr,'get')
 local id=(type(val)=='function') and safe(function() return val(cr) end) or nil
 local flags=field(item,'m_flags')
 local c1=field(item,'m_useCount1')
 local c2=field(item,'m_useCount2')
 local c3=field(item,'m_useCount3')
 if not ref(id) or not integer(flags,0,4294967295) or
    not integer(c1,0,65535) or not integer(c2,0,65535) or
    not integer(c3,0,65535) then
  return {slot=slot,status='PRESENT_UNVERIFIED'}
 end
 return {slot=slot,status='PRESENT_RAW',resref=id:upper(),
  flagsRaw=flags,useCount1Raw=c1,useCount2Raw=c2,useCount3Raw=c3,
  itemInstanceVerified=false,usableVerified=false,effectsVerified=false}
end
function M.observe(sprite)
 if sprite==nil then return result('HOLD_NO_SPRITE') end
 local actor=field(sprite,'m_id')
 local eq=field(sprite,'m_equipment')
 local items=eq~=nil and field(eq,'m_items') or nil
 if not integer(actor,0,2147483647) or items==nil then
  return result('HOLD_NO_ACTOR_OR_ITEMS') end
 local out={actorId=actor,slots={},presentCount=0,emptyCount=0}
 for slot=15,34 do
  local it=item_at(items,slot)
  out.slots[slot]=it
  if it.status=='PRESENT_RAW' then out.presentCount=out.presentCount+1
  elseif it.status=='EMPTY' then out.emptyCount=out.emptyCount+1
  else return result('HOLD_BACKPACK_SLOT_UNREADABLE',{actorId=actor,slot=slot}) end
 end
 return result('RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN',out)
end
-- Scores are provided by the existing V3/V4/V5-derived model, NOT created by
-- this module. Alternative effective APR/effects are not claimed as game-final.
-- This function intentionally cannot dispatch even with favorable inputs.
function M.plan(backpack,quick,scene,candidates)
 if type(backpack)~='table' or
    backpack.status~='RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN' or
    type(backpack.slots)~='table' or
    type(quick)~='table' or type(scene)~='table' or
    type(candidates)~='table' then return result('HOLD_SNAPSHOT_INCOMPLETE') end
 if not integer(scene.actorId,0,2147483647) or
    scene.actorId~=backpack.actorId or not integer(scene.tick,0,1e12) or
    not ref(scene.targetResref) or
    type(scene.snapshotId)~='string' or #scene.snapshotId<1 or
    #scene.snapshotId>128 or scene.itemModelProvenance~='V3_V4_V5' or
    scene.protectionEvidenceVerified~=true or
    scene.currentWeaponScoreVerified~=true or
    not finite(scene.currentWeaponScore) or
    not integer(scene.weaponSlotCapacity,2,4) then
  return result('HOLD_SCENE_OR_MODEL_NOT_PROVEN') end
 if scene.selectedWeaponStillSame~=true or
    scene.currentEquipmentFingerprintStable~=true then
  return result('HOLD_EQUIPMENT_CONTEXT_DRIFT') end
 local free=nil
 for slot=35,38 do
  local q=quick[slot]
  if type(q)~='table' or q.slot~=slot or
     (q.status~='EMPTY' and q.status~='OCCUPIED') then
   return result('HOLD_QUICKSLOT_SNAPSHOT_INCOMPLETE') end
  if slot<35+scene.weaponSlotCapacity and q.status=='EMPTY' and free==nil then
   free=slot
  end
 end
 for slot=15,34 do
  local v=backpack.slots[slot]
  if type(v)~='table' or v.slot~=slot or
     (v.status~='EMPTY' and v.status~='PRESENT_RAW') then
   return result('HOLD_BACKPACK_INCOMPLETE') end
 end
 local seenSlot,chosen={},nil
 for k,c in pairs(candidates) do
  if not integer(k,1,20) or type(c)~='table' or
     not integer(c.sourceSlot,15,34) or seenSlot[c.sourceSlot] then
   return result('HOLD_CANDIDATE_LIST_AMBIGUOUS') end
  seenSlot[c.sourceSlot]=true
  local item=backpack.slots[c.sourceSlot]
  if item.status~='PRESENT_RAW' or not ref(c.resref) or
     item.resref~=c.resref:upper() or
     c.snapshotId~=scene.snapshotId or
     c.modelProvenance~='V3_V4_V5' or not finite(c.predictedUtility) or
     c.usabilityVerified~=true or c.identifiedVerified~=true or
     c.notCursedVerified~=true or c.notQuestItemVerified~=true or
     c.offhandCompatibilityVerified~=true or
     c.ammoAndLauncherVerified~=true or c.protectionsAccountedVerified~=true then
    return result('HOLD_CANDIDATE_NOT_VERIFIED',{sourceSlot=c.sourceSlot})
  end
  if chosen==nil or c.predictedUtility>chosen.predictedUtility then chosen=c end
 end
 if chosen==nil then return result('HOLD_NO_VERIFIED_BACKPACK_CANDIDATE') end
 local margin=math.max(2,math.abs(scene.currentWeaponScore)*0.15)
 local gain=chosen.predictedUtility-scene.currentWeaponScore
 if gain<=margin then return result('KEEP_CURRENT_NO_MEANINGFUL_GAIN',
   {candidateResref=chosen.resref,estimatedGain=gain,margin=margin}) end
 if free==nil then
  return result('HOLD_ALL_USABLE_QUICKSLOTS_OCCUPIED_NO_OVERWRITE',
   {candidateResref=chosen.resref,sourceSlot=chosen.sourceSlot,
    estimatedGain=gain,fullSlotSwapNotValidated=true}) end
 -- The same resref may occur in multiple backpack stacks or quickslots.
 -- XEquipItem chooses by resource, so it is not a unique instance selector.
 local matches=0
 for slot=15,34 do
  local it=backpack.slots[slot]
  if it.status=='PRESENT_RAW' and it.resref==chosen.resref then matches=matches+1 end
 end
 for slot=35,38 do
  if quick[slot].status=='OCCUPIED' and quick[slot].resref==chosen.resref then
   matches=matches+1
  end
 end
 if matches~=1 then return result('HOLD_RESREF_INSTANCE_AMBIGUITY') end
 -- Even a verified recommendation is not proof of an idle animation or of
 -- safe XEquipItem transfer semantics. Future executor needs its own proof.
 return result('ADVISE_LOAD_BACKPACK_WEAPON_INTO_EMPTY_QUICKSLOT_RO',{
  sourceSlot=chosen.sourceSlot,toSlot=free,candidateResref=chosen.resref,
  estimatedGain=gain,modelMargin=margin,
  provisionalModelOnly=true,engineFinalAlternativeStatsVerified=false,
  itemTransferSemanticsVerified=false,manualEpsOriginVerified=false,
  safeActionBoundaryVerified=false,requiresAtomicInventoryValidation=true})
end
return M
