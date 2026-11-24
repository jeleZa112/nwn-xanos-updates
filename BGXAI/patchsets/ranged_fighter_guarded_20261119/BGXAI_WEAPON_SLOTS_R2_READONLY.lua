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
-- Rechecking the same selected slot does not make cached advice safe: a
-- character can replace BOW05 with another bow (or change quiver/offhand)
-- while all charges and flags stay identical. Invalidate the advice on any
-- changed *observed* identity or count, never interrupt the current action.
local function compare_slot(a,b)
 if type(a)~='table' or type(b)~='table' then return nil end
 if a.access=='READ_ERROR' or a.access=='UNAVAILABLE' or
    b.access=='READ_ERROR' or b.access=='UNAVAILABLE' then return nil end
 if a.index~=b.index or a.kind~=b.kind or a.ordinal~=b.ordinal then
  return nil -- incomparable contract, not an equipment change
 end
 for _,key in ipairs({'access','itemResrefRaw','resrefAccess','useCount1Raw',
    'useCount2Raw','useCount3Raw','flagsRaw','itemTypeRaw'}) do
  if a[key]~=b[key] then return true end
 end
 return false
end
local function compare_slots(a,b,indices,kind)
 if type(a)~='table' or type(b)~='table' then return nil end
 -- Lua # on sparse tables is not a proof that a complete array was read.
 for key in pairs(a) do if not int(key,1,4) then return nil end end
 for key in pairs(b) do if not int(key,1,4) then return nil end end
 local changed=false
 for i=1,4 do
  local x,y=a[i],b[i]
  if type(x)~='table' or type(y)~='table' or
     x.index~=indices[i] or y.index~=indices[i] or
     x.kind~=kind or y.kind~=kind or x.ordinal~=i-1 or y.ordinal~=i-1 then
   return nil
  end
  local different=compare_slot(x,y)
  if different==nil then return nil end
  changed=changed or different
 end
 return changed
end
function M.compare(before,after)
 if type(before)~='table' or type(after)~='table' or
    before.actorId==nil or before.actorId~=after.actorId then
  return result('HOLD_INCOMPARABLE_ACTOR') end
 if not int(before.selectedWeaponRaw,0,65535) or
    not int(after.selectedWeaponRaw,0,65535) or
    before.status=='HOLD_SOME_SLOTS_UNREADABLE' or
    after.status=='HOLD_SOME_SLOTS_UNREADABLE' then
  return result('HOLD_INCOMPLETE_COMPARISON') end
 local w=compare_slots(before.quickWeapons,after.quickWeapons,WEAPON,'QUICKWEAPON')
 local q=compare_slots(before.quivers,after.quivers,QUIVER,'QUIVER')
 local hand=compare_slot(before.offhand,after.offhand)
 if hand~=nil and (before.offhand.index~=OTHER[1] or
      after.offhand.index~=OTHER[1] or
      before.offhand.kind~='OFFHAND_OR_SHIELD' or
      after.offhand.kind~='OFFHAND_OR_SHIELD') then hand=nil end
 if w==nil or q==nil or hand==nil then
  return result('HOLD_INCOMPLETE_COMPARISON') end
 local changed=before.selectedWeaponRaw~=after.selectedWeaponRaw
 local context_changed=w or q or hand or
   before.selectedAbilityRaw~=after.selectedAbilityRaw
 return result((changed or context_changed) and
    'INVALIDATE_WEAPON_ADVICE_KEEP_ACTION' or 'RAW_FINGERPRINT_SAME_NOT_PROOF_OF_BUFFS',
    {actorId=before.actorId,selectedChanged=changed,slotDataChanged=context_changed})
end

return M
