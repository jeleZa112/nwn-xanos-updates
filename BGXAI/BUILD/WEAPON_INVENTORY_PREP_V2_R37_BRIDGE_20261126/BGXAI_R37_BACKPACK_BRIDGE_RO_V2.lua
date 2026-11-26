-- BGXAI R37 -> backpack dual-snapshot bridge V2, SOURCE ONLY.
-- Invoke from the EXISTING R37 makeListener, never register a second listener.
-- Does not load/move/equip/select items or call any engine command.
local M={schema="BGXAI_R37_BACKPACK_BRIDGE_RO_V2",installed=false}
local function ret(s,d)
 local x={schema=M.schema,status=s,readOnly=true,sourceOnly=true,
  ordersSent=0,localsWritten=0,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,inventoryMoveAuthorized=false,
  safeActionBoundaryVerified=false,manualEpsOriginVerified=false}
 if type(d)=="table" then for k,v in pairs(d) do x[k]=v end end
 return x
end
local function integer(v,a,b)
 return type(v)=="number" and v==v and v%1==0 and v>=a and v<=b
end
local function str(v)
 return type(v)=="string" and #v>0 and #v<=8 and not v:find("[^%w_]")
end
local function sameItem(a,b)
 if a.status~=b.status or a.slot~=b.slot then return false end
 if a.status=="EMPTY" then return true end
 if a.status~="PRESENT_RAW" then return false end
 return a.resref==b.resref and a.flagsRaw==b.flagsRaw
  and a.useCount1Raw==b.useCount1Raw
  and a.useCount2Raw==b.useCount2Raw
  and a.useCount3Raw==b.useCount3Raw
end
function M.capture(sprite,r37,inventory)
 if type(r37)~="table" or type(inventory)~="table"
    or type(inventory.observe)~="function" or sprite==nil then
  return ret("HOLD_MISSING_PORTS") end
 if r37.schema~="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1"
    or r37.status~="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE"
    or r37.sameLuaListenerInvocation~=true
    or r37.rawInventoryDoubleReadConsistent~=true
    or r37.selectedDerivedStatsDoubleReadConsistent~=true
    or r37.readOnly~=true or r37.ordersSent~=0
    or r37.dispatchAuthorized~=false
    or r37.weaponSwitchAuthorized~=false
    or not integer(r37.actor,1,2147483647)
    or not integer(r37.partyIndex,0,5) then
  return ret("HOLD_R37_CONTRACT_NOT_MET") end
 local ok1,a=pcall(inventory.observe,sprite)
 local ok2,b=pcall(inventory.observe,sprite)
 if not ok1 or not ok2 or type(a)~="table" or type(b)~="table" then
  return ret("HOLD_BACKPACK_READ_ERROR") end
 if a.status~="RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN"
    or b.status~=a.status or a.actorId~=r37.actor
    or b.actorId~=r37.actor or type(a.slots)~="table"
    or type(b.slots)~="table" then
  return ret("HOLD_BACKPACK_CAPTURE_INVALID") end
 local slots,counts={},{}
 for s=15,34 do
  local x,y=a.slots[s],b.slots[s]
  if type(x)~="table" or type(y)~="table"
     or not sameItem(x,y) then
   return ret("HOLD_BACKPACK_CHANGED_DURING_CAPTURE",{unstableSlot=s}) end
  if x.status=="PRESENT_RAW" then
   if not str(x.resref) then return ret("HOLD_RESREF_INVALID") end
   counts[x.resref]=(counts[x.resref] or 0)+1
   slots[s]={slot=s,status="PRESENT_RAW",resref=x.resref,
    flagsRaw=x.flagsRaw,useCount1Raw=x.useCount1Raw,
    useCount2Raw=x.useCount2Raw,useCount3Raw=x.useCount3Raw}
  elseif x.status=="EMPTY" then
   slots[s]={slot=s,status="EMPTY"}
  else
   return ret("HOLD_UNVERIFIED_ITEM_STATE") end
 end
 -- Important: R37 quickslots/quiver/offhand may also contain this resref;
 -- backpack-only uniqueness does NOT authorize XEquipItem.
 local ambiguous=false
 for _,n in pairs(counts) do if n>1 then ambiguous=true end end
 return ret("R37_BACKPACK_DOUBLE_CAPTURE_STABLE_ADVICE_ONLY",{
  actorId=r37.actor,partyIndex=r37.partyIndex,
  snapshot={actorId=r37.actor,slots=slots,
   status="RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN"},
  duplicateBackpackResrefObserved=ambiguous,
  fullEquipmentUniquenessVerified=false,
  actionQueueBoundaryVerified=false,
  targetSpecificEffectScoreVerified=false,
  xEquipItemTransferVerified=false,
  itemInstanceIdentityVerified=false,
  -- A stable raw observation is evidence, NOT permission to move an item.
  cachedAdvisoryCanBeExecuted=false})
end
return M
