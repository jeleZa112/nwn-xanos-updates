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
 local readOK,name=false,nil
 if type(rg)=="function" then readOK,name=pcall(rg,rr) end
 if not readOK then return nil end
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
    r37.rawInventoryDoubleReadConsistent~=true or
    r37.selectedDerivedStatsDoubleReadConsistent~=true or
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
-- Extend the EXISTING R37 stable backpack capture into the 23 remaining
-- top-level inventory slots, ON DEMAND, not in a new listener.
-- Never treats equal resrefs as proof of individual CItem instance identity.
local function same_raw_item(r,x,slot)
 -- Existing R2/R27 fields are {index,kind,ordinal,access,itemResrefRaw};
 -- NOT {slot,resrefRaw}. The offhand is one raw object, not an array.
 if type(r)~='table' or r.index~=slot or
    type(x)~='table' or x.slot~=slot then return false end
 if x.status=='EMPTY' then
  return r.access=='NULL' and r.itemResrefRaw==nil and
         r.useCount1Raw==nil and r.useCount2Raw==nil and
         r.useCount3Raw==nil and r.flagsRaw==nil
 end
 return x.status=='PRESENT_RAW' and
        r.access=='OBJECT_RETURNED_UNVERIFIED' and
        r.resrefAccess=='RAW_RESREF_RETURNED_UNVERIFIED' and
        type(r.itemResrefRaw)=='string' and
        x.resref==r.itemResrefRaw:upper() and
        x.useCount1Raw==r.useCount1Raw and
        x.useCount2Raw==r.useCount2Raw and
        x.useCount3Raw==r.useCount3Raw and
        x.flagsRaw==r.flagsRaw
end

function M.captureTopLevel(sprite,r37,contextReader)
 -- The previously audited capture is reused as the first step. It confirms
 -- actor identity, double-read backpack and stable R37 queue/action context.
 local base=M.capture(sprite,r37,contextReader)
 if base.status~='BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY' then
  return hold('HOLD_TOPLEVEL_PRIOR_R37_BACKPACK_GATE',
              {priorStatus=base.status}) end
 local expected={actorId=r37.actor,actionRaw=r37.actionRaw,
  selectedWeaponRaw=r37.selectedWeaponRaw,
  selectedAbilityRaw=r37.selectedAbilityRaw,
  queuedActionsRaw=r37.queuedActionsRaw,
  currentScriptNumberRaw=r37.currentScriptNumberRaw}
 local eq=field(sprite,'m_equipment')
 local items=field(eq,'m_items')
 if items==nil or type(contextReader)~='function' then
  return hold('HOLD_TOPLEVEL_ITEMS_OR_CONTEXT_UNAVAILABLE') end
 local beforeOk,before=pcall(contextReader,sprite)
 if not beforeOk or not contextOK(before,expected) then
  return hold('HOLD_TOPLEVEL_CONTEXT_BEFORE') end
 local function missing()
  local quick,other={},{}
  for slot=0,17 do
   local x=at(items,slot)
   if x==nil then return nil,nil,slot end
   other[slot]=x
  end
  local magic=at(items,34)
  if magic==nil then return nil,nil,34 end
  other[34]=magic
  for slot=35,38 do
   local x=at(items,slot)
   if x==nil then return nil,nil,slot end
   quick[slot]=x
  end
  return quick,other,nil
 end
 local quick,other,bad=missing()
 if not quick then
  return hold('HOLD_TOPLEVEL_FIRST_READ_UNAVAILABLE',{badSlot=bad}) end
 local quick2,other2,bad2=missing()
 if not quick2 then
  return hold('HOLD_TOPLEVEL_SECOND_READ_UNAVAILABLE',{badSlot=bad2}) end
 for slot=0,17 do
  if not itemEqual(other[slot],other2[slot],slot) then
   return hold('HOLD_TOPLEVEL_ITEM_CHANGED',{badSlot=slot}) end
 end
 if not itemEqual(other[34],other2[34],34) then
  return hold('HOLD_TOPLEVEL_ITEM_CHANGED',{badSlot=34}) end
 for slot=35,38 do
  if not itemEqual(quick[slot],quick2[slot],slot) then
   return hold('HOLD_TOPLEVEL_ITEM_CHANGED',{badSlot=slot}) end
 end
 -- Bind actual selected weapon, quiver and offhand back to ORIGINAL
 -- R27 single-callback raw evidence, instead of inventing an item identity.
 if type(r37.quickWeaponsRaw)~='table' or
    type(r37.quiversRaw)~='table' or
    type(r37.offhandRaw)~='table' then
  return hold('HOLD_TOPLEVEL_R37_GEAR_NOT_SUPPLIED') end
 for i=1,4 do
  if not same_raw_item(r37.quickWeaponsRaw[i],quick[34+i],34+i) or
     not same_raw_item(r37.quiversRaw[i],other[10+i],10+i) then
   return hold('HOLD_TOPLEVEL_R37_GEAR_CHANGED') end
 end
 if not same_raw_item(r37.offhandRaw,other[9],9) then
  return hold('HOLD_TOPLEVEL_R37_OFFHAND_CHANGED') end
 -- A final backpack read closes the window spanning the extra 23 slots.
 local endBag=M.observe(sprite)
 if endBag.status~='BACKPACK16_RAW_NOT_INSTANCE_PROOF' or
    endBag.actorId~=r37.actor then
  return hold('HOLD_TOPLEVEL_BACKPACK_AFTER_UNAVAILABLE') end
 for slot=18,33 do
  if not itemEqual(base.snapshot.slots[slot],endBag.slots[slot],slot) then
   return hold('HOLD_TOPLEVEL_BACKPACK_CHANGED',{badSlot=slot}) end
 end
 local afterOk,after=pcall(contextReader,sprite)
 if not afterOk or not contextOK(after,expected) then
  return hold('HOLD_TOPLEVEL_CONTEXT_AFTER') end
 return hold('TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY',{
  actorId=r37.actor,partyIndex=r37.partyIndex,
  backpack=base.snapshot,quick=quick,other=other,
  topLevelSlotsCount=39,rawInventoryDoubleRead=true,
  r37QuickQuiverOffhandMatched=true,rawSnapshotDriftObserved=false,
  nativeInstanceIdentityVerified=false,
  sameTickProven=false,allBuffsObserved=false,
  targetObserved=false,alternativeAPRVerified=false,
  executorAllowed=false,currentActionPreserved=true})
end

-- Native EEex 1.1.7 ITM source view, on demand in the SAME existing R37
-- callback. No Python can execute inside InfinityLoader Lua: this closes the
-- missing runtime item-resource channel for the FIRST ability only.
-- EEex_Resource.lua uses WRONG Item_Header_st.sizeof stride for ability
-- indices >=1; NEVER dereference those. For >1 abilities, HOLD THAT ITEM.
-- CItem pRes.pHeader is obtained from the engine's own live inventory.
-- R3 still owns full ITM/BIFF/effects validation, NOT this native probe.
-- api is optional and defaults to EEex's real UDToPtr/Read8 functions.
function M.captureNativeAbility0(sprite,r37,contextReader,api)
 if type(r37)~='table' or r37.queuedActionsRaw~=0 or
    type(contextReader)~='function' then
  return hold('HOLD_NATIVE_ITM_EVENT_OR_QUEUE_NOT_QUIET') end
 local base=M.captureTopLevel(sprite,r37,contextReader)
 if base.status~='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY' then
  return hold('HOLD_NATIVE_ITM_R37_MAP_NOT_READY',
              {priorStatus=base.status}) end
 local toPtr=type(api)=='table' and api.toPtr or EEex_UDToPtr
 local read8=type(api)=='table' and api.read8 or EEex_Read8
 if type(toPtr)~='function' or type(read8)~='function' then
  return hold('HOLD_NATIVE_ITM_EEEX117_READER_MISSING') end
 local expected={actorId=r37.actor,actionRaw=r37.actionRaw,
  selectedWeaponRaw=r37.selectedWeaponRaw,
  selectedAbilityRaw=r37.selectedAbilityRaw,
  queuedActionsRaw=r37.queuedActionsRaw,
  currentScriptNumberRaw=r37.currentScriptNumberRaw}
 local eq=field(sprite,'m_equipment')
 local items=field(eq,'m_items')
 if items==nil or type(field(items,'get'))~='function' then
  return hold('HOLD_NATIVE_ITM_ITEM_GETTER_MISSING') end
 local beforeOK,before=pcall(contextReader,sprite)
 if not beforeOK or not contextOK(before,expected) then
  return hold('HOLD_NATIVE_ITM_ACTION_DRIFT_BEFORE') end
 local rows={};local total=0;local single=0;local unsupported=0
 for slot=18,38 do
  if slot~=34 then -- backpack 18..33 plus quickweapons 35..38
   local raw=slot<=33 and base.backpack.slots[slot] or base.quick[slot]
   if type(raw)~='table' or raw.slot~=slot then
    return hold('HOLD_NATIVE_ITM_R37_SLOT_UNTRUSTED',{badSlot=slot}) end
   if raw.status=='PRESENT_RAW' then
    total=total+1
    -- Item instance identity is NOT proven by a stable resref or pointer.
    local x=at(items,slot)
    if not itemEqual(x,raw,slot) then
     return hold('HOLD_NATIVE_ITM_INVENTORY_CHANGED',{badSlot=slot}) end
    local get=field(items,'get')
    local got,item=pcall(get,items,slot)
    if not got or item==nil then
     return hold('HOLD_NATIVE_ITM_ITEM_GONE',{badSlot=slot}) end
    local resource=field(item,'pRes')
    local header=field(resource,'pHeader')
    local count=field(header,'abilityCount')
    if header==nil or not valid(count,0,64) then
     return hold('HOLD_NATIVE_ITM_HEADER_UNREADABLE',{badSlot=slot}) end
    local row={slot=slot,resref=raw.resref,abilityCountRaw=count,
     status='NOT_A_SINGLE_ATTACK_ABILITY',firstAbilityAttackTypeRaw=nil,
     proficiencyIdRaw=nil,engineFinalAlternateAPRVerified=false}
    if count==1 then
     -- Only index 0: the documented EEex 1.1.7 getAbility stride bug
     -- multiplies by zero for index 0, so no wrong stride is traversed.
     local getter=field(header,'getAbility')
     local ok,ability=false,nil
     if type(getter)=='function' then ok,ability=pcall(getter,header,0) end
     if not ok or ability==nil then
      return hold('HOLD_NATIVE_ITM_ABILITY_ZERO_UNREADABLE',{badSlot=slot}) end
     local ok1,p1=pcall(toPtr,ability)
     local ok2,p2=pcall(toPtr,header)
     if not ok1 or not ok2 or not valid(p1,1,9007199254740991) or
        not valid(p2,1,9007199254740991) then
      return hold('HOLD_NATIVE_ITM_USERDATA_POINTER_UNKNOWN',{badSlot=slot}) end
     local a1Ok,a1=pcall(read8,p1)
     local a2Ok,a2=pcall(read8,p1)
     local profOk,prof=pcall(read8,p2+0x31)
     local prof2Ok,prof2=pcall(read8,p2+0x31)
     if not a1Ok or not a2Ok or not profOk or not prof2Ok or
        not valid(a1,0,4) or a1~=a2 or
        not valid(prof,0,255) or prof~=prof2 then
      return hold('HOLD_NATIVE_ITM_ATTACK_OR_PROF_DRIFT',{badSlot=slot}) end
     row.firstAbilityAttackTypeRaw=a1
     row.proficiencyIdRaw=prof
     row.status=(a1==1 or a1==2) and
       'SINGLE_PHYSICAL_ATTACK_ABILITY_RAW' or
       'SKIP_NONPHYSICAL_ABILITY_RAW'
     single=single+1
    elseif count>1 then
     row.status='SKIP_MULTIPLE_ABILITIES_UNSAFE_EEEX117_STRIDE'
     unsupported=unsupported+1
    else
     row.status='SKIP_NO_WEAPON_ABILITY'
    end
    rows[slot]=row
   elseif raw.status~='EMPTY' then
    return hold('HOLD_NATIVE_ITM_UNKNOWN_SLOT_STATE',{badSlot=slot}) end
  end
 end
 local afterOK,after=pcall(contextReader,sprite)
 if not afterOK or not contextOK(after,expected) then
  return hold('HOLD_NATIVE_ITM_ACTION_DRIFT_AFTER') end
 -- No source can authenticate the actor's *unselected* final APR from ITM
 -- bytes alone, even when all item names, first ability and proficiency match.
 base.nativeAbility0=rows
 base.nativeAbility0Source='EEEX117_ENGINE_CITEM_FIRST_ABILITY_RAW'
 base.nativeAbility0Count=total
 base.nativeAbility0SingleCount=single
 base.nativeAbility0MultiUnsafeCount=unsupported
 base.nativeAbility0EEexVersionAssumed='v1.1.7'
 base.engineFinalAlternateAPRVerified=false
 base.nativeItemInstanceAuthenticated=false
 base.nativeResourceShaVerified=false
 base.dispatchAuthorized=false
 base.inventoryMoveAuthorized=false
 base.ordersSent=0
 return base
end


return M
