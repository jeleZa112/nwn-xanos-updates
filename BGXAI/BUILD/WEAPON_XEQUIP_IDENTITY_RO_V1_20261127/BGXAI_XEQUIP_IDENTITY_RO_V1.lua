-- BGXAI XEquip V3 -> R37 identity gate, READ ONLY / SOURCE ONLY.
-- One existing R37 callback may call this function; do not register a new callback.
-- This never writes LOCALS, executes XEquipItem, or authorizes a game install.
local M={schema='BGXAI_XEQUIP_IDENTITY_RO_V1',sourceOnly=true,readOnly=true}

-- Values come from the user's real GAM, but GAM alone is not a runtime identity proof.
local GAM_SHA='7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c'
local WANT={portraitIndex=1,classRaw=3,sourceSlot=20,targetSlot=35,
            resref='STAF01',flagsRaw=1,charges={0,0,0}}

local function int(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function field(o,k)
 if o==nil then return nil end
 local ok,v=pcall(function() return o[k] end)
 if ok then return v end
 return nil
end
local function fail(status,detail)
 return {schema=M.schema,status=status,detail=detail,
         sourceOnly=true,readOnly=true,installed=false,
         gamSha256=GAM_SHA,ordersSent=0,localsWritten=0,
         dispatchAuthorized=false,armAuthorized=false,
         gameModified=false,safeActionBoundaryVerified=false,
         sessionMatchesSavedGamVerified=false,
         manualEpsOriginVerified=false,engineTransferVerified=false}
end
local function resref(item)
 local r=field(item,'cResRef')
 local f=field(r,'get')
 if type(f)~='function' then return nil end
 local ok,v=pcall(f,r)
 if not ok or type(v)~='string' or #v<1 or #v>8 or
    v:find('[^%w_]') then return nil end
 return v:upper()
end
local function getitem(items,slot)
 local f=field(items,'get')
 if type(f)~='function' then return nil,'HOLD_NO_ITEM_GETTER' end
 local ok,item=pcall(f,items,slot)
 if not ok then return nil,'HOLD_ITEM_GET_FAILED' end
 if item==nil then return {status='EMPTY',slot=slot},nil end
 local rr=resref(item)
 local flags=field(item,'m_flags')
 local c1=field(item,'m_useCount1')
 local c2=field(item,'m_useCount2')
 local c3=field(item,'m_useCount3')
 if not rr or not int(flags,0,4294967295) or
    not int(c1,0,65535) or not int(c2,0,65535) or
    not int(c3,0,65535) then
  return nil,'HOLD_UNREADABLE_ITEM_RECORD'
 end
 return {status='PRESENT',slot=slot,resref=rr,
         flagsRaw=flags,charges={c1,c2,c3}},nil
end
local function contextValid(c)
 return type(c)=='table' and int(c.actorId,1,2147483647) and
        int(c.partyIndex,0,5) and int(c.actionRaw,0,65535) and
        int(c.selectedWeaponRaw,0,65535) and
        int(c.selectedAbilityRaw,0,65535) and
        int(c.queuedActionsRaw,0,512) and
        int(c.currentScriptNumberRaw,-32768,32767)
end
local CONTEXT={'actorId','partyIndex','actionRaw','selectedWeaponRaw',
               'selectedAbilityRaw','queuedActionsRaw','currentScriptNumberRaw'}
local function equalContext(a,b)
 if not contextValid(a) or not contextValid(b) then return false end
 for _,k in ipairs(CONTEXT) do if a[k]~=b[k] then return false end end
 return true
end
local function equalItems(a,b)
 if not a or not b or a.slot~=b.slot or a.status~=b.status then return false end
 if a.status=='EMPTY' then return true end
 if a.status~='PRESENT' or a.resref~=b.resref or
    a.flagsRaw~=b.flagsRaw then return false end
 for i=1,3 do if a.charges[i]~=b.charges[i] then return false end end
 return true
end
local function examine(sprite,ports)
 local id=field(sprite,'m_id')
 local ai=field(sprite,'m_typeAI')
 local cl=field(ai,'m_Class')
 local eq=field(sprite,'m_equipment')
 local items=field(eq,'m_items')
 if not int(id,1,2147483647) or not int(cl,0,255) or items==nil then
  return nil,'HOLD_ACTOR_CLASS_OR_EQUIPMENT_UNREADABLE'
 end
 if cl~=WANT.classRaw then return nil,'HOLD_CLASS_NOT_SAVED_CANDIDATE' end
 local seenId=0
 for p=0,5 do
  local ok,pid=pcall(ports.portraitId,p)
  if not ok then return nil,'HOLD_PORTRAIT_READER_EXCEPTION' end
  if pid==id then seenId=seenId+1 end
  if p==WANT.portraitIndex and pid~=id then
   return nil,'HOLD_PORTRAIT_ID_MISMATCH'
  end
 end
 if seenId~=1 then return nil,'HOLD_NONUNIQUE_PORTRAIT_ID' end
 local observed={}
 local copies=0
 for slot=0,38 do
  if slot~=10 then -- 10: implicit fist slot, never label it EMPTY.
   local v,err=getitem(items,slot)
   if err then return nil,err end
   observed[slot]=v
   if v.status=='PRESENT' and v.resref==WANT.resref then copies=copies+1 end
  end
 end
 local src=observed[WANT.sourceSlot]
 local dst=observed[WANT.targetSlot]
 if src.status~='PRESENT' or src.resref~=WANT.resref then
  return nil,'HOLD_SOURCE_ITEM_NOT_AT_EXPECTED_SLOT'
 end
 if src.flagsRaw~=WANT.flagsRaw then
  return nil,'HOLD_SOURCE_FLAGS_CHANGED'
 end
 for i=1,3 do
  if src.charges[i]~=WANT.charges[i] then return nil,'HOLD_SOURCE_CHARGES_CHANGED' end
 end
 if dst.status~='EMPTY' then return nil,'HOLD_TARGET_WEAPON_SLOT_OCCUPIED' end
 if copies~=1 then return nil,'HOLD_ITEM_RESREF_NOT_UNIQUE_ON_ACTOR' end
 return {actorId=id,cl=cl,slots=observed},nil
end
local function compareAll(a,b)
 if a.actorId~=b.actorId or a.cl~=b.cl then return false end
 for slot=0,38 do
  if slot~=10 and not equalItems(a.slots[slot],b.slots[slot]) then return false end
 end
 return true
end

function M.capture(sprite,ports)
 if sprite==nil or type(ports)~='table' or
    type(ports.portraitId)~='function' or
    type(ports.contextReader)~='function' then
  return fail('HOLD_MISSING_READONLY_PORTS') end
 -- One callback is not an idle-state or current-game-session proof.
 local ok0,c0=pcall(ports.contextReader,sprite)
 if not ok0 or not contextValid(c0) then return fail('HOLD_CONTEXT_BEFORE_UNREADABLE') end
 if c0.partyIndex~=WANT.portraitIndex then return fail('HOLD_WRONG_PORTRAIT_CONTEXT') end
 local a,errA=examine(sprite,ports)
 if not a then return fail(errA or 'HOLD_EXAMINE_FIRST') end
 if a.actorId~=c0.actorId then return fail('HOLD_FIRST_ACTOR_ID_CONTEXT_MISMATCH') end
 local b,errB=examine(sprite,ports)
 if not b then return fail(errB or 'HOLD_EXAMINE_SECOND') end
 if not compareAll(a,b) then return fail('HOLD_EQUIPMENT_CHANGED_BETWEEN_READS') end
 local ok1,c1=pcall(ports.contextReader,sprite)
 if not ok1 or not equalContext(c0,c1) then return fail('HOLD_ACTION_CONTEXT_CHANGED') end
 if b.actorId~=c1.actorId then return fail('HOLD_LAST_ACTOR_ID_CONTEXT_MISMATCH') end
 local r=fail('RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM')
 r.actorIdInMemory=a.actorId -- NEVER expose in public logs or treat as session proof.
 r.portraitIndex=WANT.portraitIndex
 r.sourceSlot=WANT.sourceSlot
 r.targetSlot=WANT.targetSlot
 r.resref=WANT.resref
 r.classRaw=WANT.classRaw
 r.topLevelSlotsCompared=38 -- 0..38 except implicit fist slot 10
 r.doubleReadConsistent=true
 r.rawContextStable=true
 r.actorAndPortraitMatchInThisCallback=true
 r.itemUniqueInObservedTopLevelSlots=true
 r.targetEmptyInObservedTopLevelSlots=true
 r.classKitItmUsabilityVerified=false
 r.liveIdentityCorroboratedNotAuthenticated=true
 return r
end
return M