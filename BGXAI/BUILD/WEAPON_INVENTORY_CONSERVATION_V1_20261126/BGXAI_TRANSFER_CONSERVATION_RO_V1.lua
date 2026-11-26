-- BGXAI: a read-only validator for a future *observed* item relocation.
-- It NEVER initiates an item move, never accepts a mock as proof of game LIVE.
local M={schema="BGXAI_WEAPON_TRANSFER_CONSERVATION_RO_V1",installed=false}
local function integer(v,a,b)
 return type(v)=="number" and v==v and v%1==0 and v>=a and v<=b
end
local function ref(v)
 return type(v)=="string" and #v>0 and #v<=8 and not v:find("[^%w_]")
end
local function ret(status,detail)
 local x={schema=M.schema,status=status,readOnly=true,sourceOnly=true,
  ordersSent=0,localsWritten=0,gameModified=false,executable=false,
  dispatchAuthorized=false,inventoryMoveAuthorized=false,
  weaponSwitchAuthorized=false,actionQueueCleared=false,
  manualEpsOriginVerified=false,safeActionBoundaryVerified=false,
  engineTransferSemanticsVerified=false,liveEvidenceVerified=false,
  rollbackAuthorized=false,itemInstanceIdentityVerified=false}
 if type(detail)=="table" then
  for k,v in pairs(detail) do x[k]=v end
 end
 return x
end
local function itemOK(x,slot)
 if type(x)~="table" or x.slot~=slot then return false end
 if x.status=="EMPTY" then return true end
 if x.status~="PRESENT_RAW" then return false end
 return ref(x.resref) and
  integer(x.flagsRaw,0,4294967295) and
  integer(x.useCount1Raw,0,65535) and
  integer(x.useCount2Raw,0,65535) and
  integer(x.useCount3Raw,0,65535)
end
local function fullMap(snapshot)
 if type(snapshot)~="table" or
   snapshot.status~="TOPLEVEL_SLOTS_RAW_NOT_INSTANCE_PROOF" or
   not integer(snapshot.actorId,1,2147483647) or
   type(snapshot.slots)~="table" then return false end
 for s=0,38 do
  if not itemOK(snapshot.slots[s],s) then return false end
 end
 for s in pairs(snapshot.slots) do
  if not integer(s,0,38) then return false end
 end
 return true
end
local function same(a,b)
 if a.status~=b.status then return false end
 if a.status=="EMPTY" then return true end
 for _,k in ipairs({"resref","flagsRaw","useCount1Raw",
     "useCount2Raw","useCount3Raw"}) do
  if a[k]~=b[k] then return false end
 end
 return true
end
-- Run after an independently observed attempt, never as action authorization.
-- expected={actorId, sourceSlot in 18..33, targetSlot in 35..38,
--           resref, minSnapshotSequence, maxSnapshotSequence}.
-- This API intentionally has no dispatch-related input and output authority.
function M.verify(before,after,expected)
 if not fullMap(before) or not fullMap(after) or
   type(expected)~="table" or
   not integer(expected.actorId,1,2147483647) or
   before.actorId~=after.actorId or
   expected.actorId~=before.actorId or
   not integer(expected.sourceSlot,18,33) or
   not integer(expected.targetSlot,35,38) or
   not ref(expected.resref) then
  return ret("HOLD_INCOMPLETE_OR_CROSS_ACTOR") end
 local from,to=expected.sourceSlot,expected.targetSlot
 local src=before.slots[from]
 local dest=before.slots[to]
 if src.status~="PRESENT_RAW" or src.resref~=expected.resref:upper()
    or dest.status~="EMPTY" then
  return ret("HOLD_PRECONDITION_NOT_MET") end
 local matches=0
 for s=0,38 do
  local x=before.slots[s]
  if x.status=="PRESENT_RAW" and x.resref==src.resref then
   matches=matches+1 end
 end
 if matches~=1 then
  return ret("HOLD_DUPLICATE_OR_UNPROVEN_INSTANCE",{matches=matches}) end
 if after.slots[from].status~="EMPTY" then
  return ret("HOLD_SOURCE_NOT_EMPTIED") end
 if not same(after.slots[to],src) then
  return ret("HOLD_DESTINATION_ITEM_CHANGED_OR_MISSING") end
 for s=0,38 do
  if s~=from and s~=to and not same(before.slots[s],after.slots[s]) then
   return ret("HOLD_UNRELATED_ITEM_CHANGED",{unexpectedSlot=s}) end
 end
 -- Reconciliation in a model. Not proof of XEquipItem game semantics or
 -- permission to perform the transfer; only actual game captured evidence can
 -- establish that an engine action really produced this result.
 return ret("OBSERVED_EXACT_TOPLEVEL_CONSERVATION_ADVICE_ONLY",{
  actorId=before.actorId,sourceSlot=from,targetSlot=to,
  itemResref=src.resref,topLevelConservationMatches=true,
  itemFlagsAndChargesUnchanged=true,
  unobservedContainerContentsExcluded=true})
end
return M
