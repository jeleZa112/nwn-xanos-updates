-- BGXAI R2: read-only quickweapon/quiver evidence, EEex 1.1.7 SOURCE ONLY.
-- No listener, calls to action dispatch, queue manipulation, inventory mutation,
-- script/global writes, file/console I/O, APR inference or resource dereference.
-- Based on documented SLOTS.IDS and EEex B3AttackInfo m_equipment.m_items:get().
-- CItem fields remain OPTIONAL raw readings, not proof of valid ITM/ability/ammo.
-- Not installed; does not authorize changing any equipment or combat actions.
local M={version='BGXAI_WEAPON_SLOTS_R2_READONLY',installed=false}
local WEAPON={35,36,37,38}
local QUIVER={11,12,13,14}
local OTHER={9} -- offhand/shield, only for context
local function safe(f)
 local ok,x=pcall(f)
 if ok then return x,true end
 return nil,false
end
local function field(obj,key)
 if obj==nil then return nil end
 local x=select(1,safe(function() return obj[key] end))
 return x
end
local function int(v,min,max)
 return type(v)=='number' and v==v and v%1==0 and v>=min and v<=max
end
local function raw(v,min,max)
 if int(v,min,max) then return v end
 return nil
end
local function result(status,data)
 local s={status=status,schema='BGXAI_WEAPON_SLOTS_R2_READONLY',
   readOnly=true,installed=false,executable=false,dispatchAuthorized=false,
   weaponSwitchAuthorized=false,ordersSent=0,actionQueueCleared=false,
   currentActionPreserved=true,gameFilesChanged=false,
   itemIdentityVerified=false,abilityVerified=false,ammoCountVerified=false,
   perSlotAPRVerified=false,allBuffsVerified=false,manualOrderOriginVerified=false,
   epsQueueVerified=false,weaponPriorityLive=false}
 for k,v in pairs(data or {}) do s[k]=v end
 return s
end
local function resref_raw(item)
 -- EEex CItem inherits CResHelper.cResRef; CResRef:get() is used upstream.
 -- Availability is runtime- and version-dependent, so never infer identity.
 local ref=field(item,'cResRef')
 if ref==nil then return nil,'NO_RESREF_FIELD' end
 local getter=field(ref,'get')
 if type(getter)~='function' then return nil,'NO_RESREF_GETTER' end
 local val,okay=safe(function() return getter(ref) end)
 if not okay or type(val)~='string' then return nil,'RESREF_READ_ERROR' end
 if #val<1 or #val>8 or val:find('[^%w_]') then return nil,'INVALID_RESREF' end
 return val:upper(),'RAW_RESREF_RETURNED_UNVERIFIED'
end
local function take_slot(items,index,kind,ordinal)
 local read={index=index,kind=kind,ordinal=ordinal,access='UNAVAILABLE',
   identityVerified=false,usableVerified=false,selectedAbilityVerified=false,
   itemHeaderEffectsVerified=false,ammoAssociationVerified=false,
   canEquip=false}
 if items==nil then return read end
 local getter=field(items,'get')
 if type(getter)~='function' then return read end
 local item,ok=safe(function() return getter(items,index) end)
 if not ok then read.access='READ_ERROR';return read end
 if item==nil then read.access='NULL';return read end
 read.access='OBJECT_RETURNED_UNVERIFIED'
 read.itemResrefRaw,read.resrefAccess=resref_raw(item)
 -- These CItem fields are raw optional observations, NOT charge/ammo guarantees.
 read.useCount1Raw=raw(field(item,'m_useCount1'),0,65535)
 read.useCount2Raw=raw(field(item,'m_useCount2'),0,65535)
 read.useCount3Raw=raw(field(item,'m_useCount3'),0,65535)
 read.flagsRaw=raw(field(item,'m_flags'),0,4294967295)
 read.itemTypeRaw=raw(field(item,'m_itemType'),0,65535)
 return read
end
function M.observe_sprite(sprite)
 if sprite==nil then return result('HOLD_NO_SPRITE') end
 local id=raw(field(sprite,'m_id'),0,2147483647)
 if not id then return result('HOLD_ACTOR_ID_UNAVAILABLE') end
 local eq=field(sprite,'m_equipment')
 if eq==nil then return result('HOLD_EQUIPMENT_UNAVAILABLE',{actorId=id}) end
 local arr=field(eq,'m_items')
 if arr==nil then return result('HOLD_ITEM_ARRAY_UNAVAILABLE',{actorId=id}) end
 local selected=raw(field(eq,'m_selectedWeapon'),0,65535)
 local ability=raw(field(eq,'m_selectedWeaponAbility'),0,65535)
 local r={actorId=id,selectedWeaponRaw=selected,selectedAbilityRaw=ability,
   selectedInventoryKind='UNKNOWN',quickWeapons={},quivers={},offhand=nil,
   observedSlotCount=0,unreadableSlotCount=0,source='EEEX_RUNTIME_RAW_CITEM_ARRAY'}
 for i,slot in ipairs(WEAPON) do
   local x=take_slot(arr,slot,'QUICKWEAPON',i-1)
   r.quickWeapons[i]=x
 end
 for i,slot in ipairs(QUIVER) do
   local x=take_slot(arr,slot,'QUIVER',i-1)
   r.quivers[i]=x
 end
 r.offhand=take_slot(arr,OTHER[1],'OFFHAND_OR_SHIELD',0)
 for _,x in ipairs(r.quickWeapons) do
   if x.access=='READ_ERROR' or x.access=='UNAVAILABLE' then r.unreadableSlotCount=r.unreadableSlotCount+1 end
   if x.access=='OBJECT_RETURNED_UNVERIFIED' then r.observedSlotCount=r.observedSlotCount+1 end
 end
 for _,x in ipairs(r.quivers) do
   if x.access=='READ_ERROR' or x.access=='UNAVAILABLE' then r.unreadableSlotCount=r.unreadableSlotCount+1 end
   if x.access=='OBJECT_RETURNED_UNVERIFIED' then r.observedSlotCount=r.observedSlotCount+1 end
 end
 if selected and selected>=35 and selected<=38 then r.selectedInventoryKind='WEAPON_QUICKSLOT'
 elseif selected and selected>=11 and selected<=14 then r.selectedInventoryKind='AMMO_QUICKSLOT'
 elseif selected==10 then r.selectedInventoryKind='FIST_INDEX'
 end
 if selected==nil then return result('HOLD_SELECTION_NOT_OBSERVED',r) end
 if r.unreadableSlotCount>0 then return result('HOLD_SOME_SLOTS_UNREADABLE',r) end
 return result('RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN',r)
end
function M.observe_portrait(index, getter)
 if not int(index,0,5) then return result('HOLD_INVALID_PORTRAIT') end
 if getter==nil then getter=EEex_Sprite_GetInPortrait end
 if type(getter)~='function' then return result('HOLD_EEEX_PORTRAIT_API_UNAVAILABLE') end
 local sprite,ok=safe(function() return getter(index) end)
 if not ok or sprite==nil then return result('HOLD_PORTRAIT_UNAVAILABLE') end
 local out=M.observe_sprite(sprite)
 out.portraitIndex=index
 return out
end
function M.compare(before,after)
 if type(before)~='table' or type(after)~='table' or
    before.actorId==nil or before.actorId~=after.actorId then
   return result('HOLD_INCOMPARABLE_ACTOR') end
 local changed=before.selectedWeaponRaw~=after.selectedWeaponRaw
 local context_changed=false
 local function compare_slots(a,b)
  if type(a)~='table' or type(b)~='table' or #a~=#b then return nil end
  for i=1,#a do
   local x,y=a[i],b[i]
   if x.index~=y.index or x.access~=y.access or
      x.useCount1Raw~=y.useCount1Raw or x.useCount2Raw~=y.useCount2Raw or
      x.useCount3Raw~=y.useCount3Raw or x.flagsRaw~=y.flagsRaw then
       return true end
  end
  return false
 end
 local w=compare_slots(before.quickWeapons,after.quickWeapons)
 local q=compare_slots(before.quivers,after.quivers)
 if w==nil or q==nil then return result('HOLD_INCOMPLETE_COMPARISON') end
 context_changed=w or q or before.selectedAbilityRaw~=after.selectedAbilityRaw
 return result((changed or context_changed) and
    'INVALIDATE_WEAPON_ADVICE_KEEP_ACTION' or 'RAW_FINGERPRINT_SAME_NOT_PROOF_OF_BUFFS',
    {actorId=before.actorId,selectedChanged=changed,slotDataChanged=context_changed})
end
local CORE=M

-- BGXW2: EEex passive started-action inventory evidence, not an AI controller.
-- The read-only CORE from BGXAI_WEAPON_SLOTS_R2_READONLY.lua is embedded by
-- an audited source builder. No orders, combat state edits or resource demands.
local M2={version='BGXW2_RUNTIME_R2',registered=false,limit=64,recorded=0,errors=0,
          writer='UNINITIALIZED',installedObserver=true,skipped=0}
if type(BGXWeaponSlotsRuntimeR2)=='table' and BGXWeaponSlotsRuntimeR2.registered then return end
BGXWeaponSlotsRuntimeR2=M2
local function safe2(fn)
 local ok,val=pcall(fn)
 if ok then return val end
 return nil
end
local function integer2(v,lo,hi)
 return type(v)=='number' and v==math.floor(v) and v>=lo and v<=hi
end
local function num2(x,lo,hi)
 if integer2(x,lo,hi) then return tostring(x) end
 return 'null'
end
local function string2(s)
 if type(s)=='string' and #s>=1 and #s<=8 and not s:find('[^%w_]') then
  return '"'..s..'"'
 end
 return 'null'
end
local function party2(id)
 if not integer2(id,0,2147483647) then return nil end
 for slot=0,5 do
  if safe2(function() return EEex_Sprite_GetInPortraitID(slot) end)==id then return slot end
 end
 return nil
end
local function item2(x)
 if type(x)~='table' then return '{}' end
 local validAccess={NULL=true,UNAVAILABLE=true,READ_ERROR=true,OBJECT_RETURNED_UNVERIFIED=true}
 local access=validAccess[x.access] and x.access or 'UNAVAILABLE'
 return '{"index":'..num2(x.index,0,38)..',"access":"'..access..'"'..
   ',"resrefRaw":'..string2(x.itemResrefRaw)..
   ',"useCount1Raw":'..num2(x.useCount1Raw,0,65535)..
   ',"useCount2Raw":'..num2(x.useCount2Raw,0,65535)..
   ',"useCount3Raw":'..num2(x.useCount3Raw,0,65535)..
   ',"flagsRaw":'..num2(x.flagsRaw,0,4294967295)..
   ',"identityVerified":false,"usableVerified":false,"ammoVerified":false}'
end
local function arr2(items,expected)
 if type(items)~='table' or #items~=expected then return '[]' end
 local parts={}
 for i=1,expected do parts[i]=item2(items[i]) end
 return '['..table.concat(parts,',')..']'
end
local function line2(snapshot,slot,action)
 local statusAllow={RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN=true,
 HOLD_SOME_SLOTS_UNREADABLE=true,HOLD_SELECTION_NOT_OBSERVED=true,
 HOLD_ITEM_ARRAY_UNAVAILABLE=true,HOLD_EQUIPMENT_UNAVAILABLE=true,HOLD_ACTOR_ID_UNAVAILABLE=true}
 local status=statusAllow[snapshot.status] and snapshot.status or 'HOLD_UNKNOWN'
 return '{"type":"SLOTS","schema":"BGXAI_WEAPON_SLOTS_RAW_R2","seq":'..num2(M2.recorded,1,64)..
 ',"partyIndex":'..num2(slot,0,5)..
 ',"actor":'..num2(snapshot.actorId,0,2147483647)..
 ',"actionRaw":'..num2(action,0,65535)..
 ',"selectedWeaponRaw":'..num2(snapshot.selectedWeaponRaw,0,65535)..
 ',"selectedAbilityRaw":'..num2(snapshot.selectedAbilityRaw,0,65535)..
 ',"status":"'..status..'"'..
 ',"quickWeapons":'..arr2(snapshot.quickWeapons,4)..
 ',"quivers":'..arr2(snapshot.quivers,4)..
 ',"offhand":'..item2(snapshot.offhand)..
 ',"itemIdentityVerified":false,"perSlotAPRVerified":false,'..
 '"manualOrderOriginVerified":false,"epsQueueVerified":false,'..
 '"switchAuthorized":false}'
end
local function console2(line)
 local ok=false
 if type(Infinity_Log)=='function' then
  ok=safe2(function() Infinity_Log('[BGXW2] '..line);return true end) or ok
 end
 if type(print)=='function' then
  ok=safe2(function() print('[BGXW2] '..line);return true end) or ok
 end
 return ok
end
local function write2(line)
 if M2.handle~=nil then
  local ok=pcall(function()
   M2.handle:write(line,'\n')
   if M2.recorded%8==0 then M2.handle:flush() end
  end)
  if ok then return true end
  M2.errors=M2.errors+1
  safe2(function() M2.handle:close() end)
  M2.handle=nil
 end
 if console2(line) then M2.writer='CONSOLE_FALLBACK';return true end
 M2.writer='NO_OUTPUT_SINK'
 return false
end
function M2.on_started(sprite,action)
 local ok=pcall(function()
  if M2.recorded>=M2.limit then M2.skipped=M2.skipped+1;return end
  local id=safe2(function() return sprite.m_id end)
  local slot=party2(id)
  if slot==nil then return end
  M2.recorded=M2.recorded+1
  local snap=CORE.observe_sprite(sprite)
  write2(line2(snap,slot,safe2(function() return action.m_actionID end)))
 end)
 if not ok then M2.errors=M2.errors+1 end
end
local function init2()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
    type(EEex_Sprite_GetInPortraitID)~='function' then
  M2.writer='EEEX_HOOK_UNAVAILABLE';return false
 end
 if type(io)=='table' and type(io.open)=='function' and
    type(os)=='table' and type(os.getenv)=='function' then
  local home=safe2(function() return os.getenv('USERPROFILE') end)
  if type(home)=='string' and #home>=4 and #home<=260 then
   M2.handle=safe2(function()
     return io.open(home..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_WEAPON_SLOTS_RAW_R2.jsonl','a')
   end)
  end
 end
 if M2.handle then M2.writer='FILE'
 elseif type(Infinity_Log)=='function' or type(print)=='function' then M2.writer='CONSOLE_FALLBACK'
 else M2.writer='NO_OUTPUT_SINK';return false end
 local stamp=safe2(function() return os.date('!%Y-%m-%dT%H:%M:%SZ') end) or 'UNKNOWN'
 if not write2('{"type":"SESSION","schema":"BGXAI_WEAPON_SLOTS_RAW_R2","utc":"'..stamp..'","readOnly":true}') then
  return false
 end
 local registered=safe2(function()
  EEex_Action_AddSpriteStartedActionListener(M2.on_started)
  return true
 end)
 if not registered then
  M2.writer='HOOK_FAILED';return false
 end
 M2.registered=true
 write2('{"type":"READY","schema":"BGXAI_WEAPON_SLOTS_RAW_R2","hookRegistered":true}')
 return true
end
M2.initialized=init2()
