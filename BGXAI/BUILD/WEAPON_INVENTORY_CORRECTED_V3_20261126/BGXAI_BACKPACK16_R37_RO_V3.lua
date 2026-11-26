-- BGXAI corrected BG(2)EE backpack capture, SOURCE ONLY, NEVER deploy as executor.
-- BG2EE CRE/SLOTS.IDS: QUICK ITEM 15..17, BACKPACK 18..33 (16), MAGIC 34.
-- No EEex listener, action queue writes, equipment movement or order dispatch.
local M={schema="BGXAI_BACKPACK16_R37_DOUBLE_READ_RO_V3",installed=false}
local function valid(v,lo,hi)
 return type(v)=="number" and v==v and v%1==0 and v>=lo and v<=hi
end
local function res(v)
 return type(v)=="string" and #v>=1 and #v<=8 and not v:find("[^%w_]")
end
local function field(o,k)
 if o==nil then return nil end
 local ok,v=pcall(function() return o[k] end)
 return ok and v or nil
end
local function hold(s,more)
 local o={schema=M.schema,status=s,sourceOnly=true,readOnly=true,
  ordersSent=0,localsWritten=0,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,inventoryMoveAuthorized=false,
  gameModified=false,safeActionBoundaryVerified=false,
  manualEpsOriginVerified=false,engineItemInstanceVerified=false,
  fullEquipmentUniquenessVerified=false,cachedAdvisoryCanBeExecuted=false}
 if type(more)=="table" then for k,v in pairs(more) do o[k]=v end end
 return o
end
local function at(items,slot)
 local getter=field(items,"get")
 if type(getter)~="function" then return nil end
 local ok,item=pcall(getter,items,slot)
 if not ok then return nil end
 if item==nil then return {slot=slot,status="EMPTY"} end
 local rr=field(item,"cResRef")
 local rg=field(rr,"get")
 local name=(type(rg)=="function") and select(2,pcall(rg,rr)) or nil
 local flags=field(item,"m_flags")
 local a,b,c=field(item,"m_useCount1"),field(item,"m_useCount2"),field(item,"m_useCount3")
 if not res(name) or not valid(flags,0,4294967295) or
    not valid(a,0,65535) or not valid(b,0,65535) or not valid(c,0,65535) then
   return nil
 end
 return {slot=slot,status="PRESENT_RAW",resref=name:upper(),
  flagsRaw=flags,useCount1Raw=a,useCount2Raw=b,useCount3Raw=c}
end
function M.observe(sprite)
 local id=field(sprite,"m_id")
 local eq=field(sprite,"m_equipment")
 local items=field(eq,"m_items")
 if not valid(id,1,2147483647) or items==nil then
  return hold("HOLD_NO_ACTOR_OR_ITEMS") end
 local slots,present,empty={},0,0
 for slot=18,33 do
  local x=at(items,slot)
  if x==nil then return hold("HOLD_BACKPACK16_UNREADABLE",{badSlot=slot}) end
  slots[slot]=x
  if x.status=="PRESENT_RAW" then present=present+1 else empty=empty+1 end
 end
 return hold("BACKPACK16_RAW_NOT_INSTANCE_PROOF",{
  actorId=id,slots=slots,presentCount=present,emptyCount=empty,
  excludedQuickItemSlots={15,16,17},excludedMagicalWeaponSlot=34,
  mapEvidence="BG2EE_CRE_V1_0_16_INVENTORY_SLOTS"})
end
local function itemEqual(a,b,s)
 if type(a)~="table" or type(b)~="table" or
    a.slot~=s or b.slot~=s or a.status~=b.status then return false end
 if a.status=="EMPTY" then return true end
 if a.status~="PRESENT_RAW" then return false end
 for _,k in ipairs({"resref","flagsRaw","useCount1Raw","useCount2Raw","useCount3Raw"}) do
  if a[k]~=b[k] then return false end
 end
 return true
end
local K={"actorId","actionRaw","selectedWeaponRaw","selectedAbilityRaw",
 "queuedActionsRaw","currentScriptNumberRaw"}
local function contextOK(c,r)
 if type(c)~="table" then return false end
 for _,k in ipairs(K) do
  if c[k]~=r[k] then return false end
 end
 return valid(c.actorId,1,2147483647) and
  valid(c.actionRaw,0,65535) and
  valid(c.selectedWeaponRaw,0,65535) and
  valid(c.selectedAbilityRaw,0,65535) and
  valid(c.queuedActionsRaw,0,512) and
  valid(c.currentScriptNumberRaw,-32768,32767)
end
function M.capture(sprite,r37,contextReader)
 if type(r37)~="table" or type(contextReader)~="function" then
  return hold("HOLD_MISSING_CONTEXT") end
 if r37.schema~="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1" or
    r37.status~="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE" or
    r37.readOnly~=true or r37.ordersSent~=0 or
    r37.dispatchAuthorized~=false or r37.weaponSwitchAuthorized~=false or
    r37.sameLuaListenerInvocation~=true or
    r37.queueSnapshotStable~=true or
    r37.actionContextSnapshotStable~=true or
    not valid(r37.partyIndex,0,5) or not valid(r37.actor,1,2147483647) then
  return hold("HOLD_R37_CONTRACT") end
 local expected={actorId=r37.actor,actionRaw=r37.actionRaw,
  selectedWeaponRaw=r37.selectedWeaponRaw,
  selectedAbilityRaw=r37.selectedAbilityRaw,
  queuedActionsRaw=r37.queuedActionsRaw,
  currentScriptNumberRaw=r37.currentScriptNumberRaw}
 local ok0,c0=pcall(contextReader,sprite)
 if not ok0 or not contextOK(c0,expected) then return hold("HOLD_CONTEXT_BEFORE") end
 local a=M.observe(sprite)
 if a.status~="BACKPACK16_RAW_NOT_INSTANCE_PROOF" or a.actorId~=r37.actor then
  return hold("HOLD_FIRST_CAPTURE") end
 local b=M.observe(sprite)
 if b.status~="BACKPACK16_RAW_NOT_INSTANCE_PROOF" or b.actorId~=r37.actor then
  return hold("HOLD_SECOND_CAPTURE") end
 local ok1,c1=pcall(contextReader,sprite)
 if not ok1 or not contextOK(c1,expected) then return hold("HOLD_CONTEXT_AFTER") end
 local seen,duplicate={},false
 for s=18,33 do
  if not itemEqual(a.slots[s],b.slots[s],s) then
   return hold("HOLD_BACKPACK_CHANGED",{badSlot=s}) end
  local x=a.slots[s]
  if x.status=="PRESENT_RAW" then
   if seen[x.resref] then duplicate=true end
   seen[x.resref]=true
  end
 end
 return hold("BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY",{
  actorId=r37.actor,partyIndex=r37.partyIndex,
  snapshot=a,duplicateBackpackResrefObserved=duplicate,
  fullEquipmentUniquenessVerified=false,
  engineSafeActionBoundaryVerified=false,
  manualEpsOriginVerified=false,
  currentActionPreserved=true})
end
return M
