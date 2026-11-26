-- R33 SOURCE ONLY, reused verified installed R31 R4 fields; not installed.
-- R37 source-only: compose R36 into R33's ONE existing action callback.
local R36_CORE = (function()
-- BGXAI R36: pure Lua raw-context invalidation for the existing R33 callback.
-- SOURCE ONLY. Receives R33 R27.observe() ALREADY-CAPTURED tables, not sprite.
-- No new listener, no EEex calls, no weapon commands, no IO or game writes.
-- Equality of selected stats + nine raw slots does NOT prove active effects,
-- ammo->launcher binding, manual/EPS origin, safe action boundary or alternate APR.
local M={version='BGXAI_R36_R33_ADVICE_INVALIDATION_V1',installed=false}
local STATUS='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE'
local SCHEMA='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1'
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function ref(x)
 return type(x)=='string' and #x>=1 and #x<=8 and
   not x:find('[^A-Z0-9_#%-]')
end
local function safe(status,reason)
 return {schema='BGXAI_R36_R33_ADVICE_INVALIDATION_V1',status=status,
  reason=reason,sourceOnly=true,readOnly=true,installed=false,
  ordersSent=0,localsWritten=0,currentActionPreserved=true,
  actionQueueCleared=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  alternateEffectiveAPRVerified=false,sameBuffContextVerified=false,
  allActiveEffectsVerified=false,manualEpsOriginVerified=false,
  safeActionBoundaryVerified=false,launcherAmmoBindingVerified=false,
  cachedAdvisoryCanBeExecuted=false}
end
local function validSlot(x,slot,kind,ordinal)
 if type(x)~='table' or x.index~=slot or x.kind~=kind or
    x.ordinal~=ordinal then return nil end
 if x.access=='NULL' then
  if x.itemResrefRaw~=nil or x.useCount1Raw~=nil or
     x.useCount2Raw~=nil or x.useCount3Raw~=nil then return nil end
  return {slot,'-',-1,-1,-1,-1,-1}
 end
 if x.access~='OBJECT_RETURNED_UNVERIFIED' or not ref(x.itemResrefRaw) or
    x.resrefAccess~='RAW_RESREF_RETURNED_UNVERIFIED' then return nil end
 local c1,c2,c3=x.useCount1Raw,x.useCount2Raw,x.useCount3Raw
 if not int(c1,0,65535) or not int(c2,0,65535) or
    not int(c3,0,65535) then return nil end
 -- Optional raw fields use sentinel to avoid confusing missing with zero.
 local flags=x.flagsRaw
 if flags~=nil and not int(flags,0,4294967295) then return nil end
 local itemType=x.itemTypeRaw
 if itemType~=nil and not int(itemType,0,65535) then return nil end
 return {slot,x.itemResrefRaw,c1,c2,c3,flags or -1,itemType or -1}
end
local function gear(slots,first,kind)
 if type(slots)~='table' then return nil end
 for k in pairs(slots) do
  if not int(k,1,4) then return nil end
 end
 local out={}
 for i=1,4 do
  local x=validSlot(slots[i],first+i-1,kind,i-1)
  if not x then return nil end
  out[i]=x
 end
 return out
end
local FIELDS={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nSTRExtra',
 'm_nDamageBonus','m_nHitBonus','m_nMeleeTHAC0Bonus','m_nMissileTHAC0Bonus',
 'm_bImprovedHaste','m_nLevel1','m_nLevel2','m_nLevel3','m_nKit'}
-- R33 console JSON exports only a *subset* of these. The Lua contract uses
-- the full R33 sampledStatsRaw subset, so do NOT require stats absent from it.
local SAMPLED={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nSTRExtra',
              'm_bImprovedHaste','m_nHitBonus',
              'm_nLevel1','m_nLevel2','m_nLevel3','m_nKit'}
local LIMITS={
 m_nNumberOfAttacks={0,10},m_nTHAC0={-100,100},
 m_nSTR={0,25},m_nSTRExtra={0,100},m_bImprovedHaste={0,1},
 m_nHitBonus={-100,100},m_nLevel1={0,50},m_nLevel2={0,50},
 m_nLevel3={0,50},m_nKit={0,4294967295}
}
local function equalArray(a,b)
 if type(a)~='table' or type(b)~='table' or #a~=#b then return false end
 for i=1,#a do if a[i]~=b[i] then return false end end
 return true
end
local function equalGear(a,b)
 if type(a)~='table' or type(b)~='table' then return false end
 for i=1,9 do
  if type(a[i])~='table' or type(b[i])~='table' or
     not equalArray(a[i],b[i]) then return false end
 end
 return true
end
function M.capture(sample)
 local out=safe('HOLD_R33_CONTEXT_UNVERIFIED','R33_SOURCE_UNKNOWN')
 if type(sample)~='table' or sample.schema~=SCHEMA or
    sample.status~=STATUS or sample.readOnly~=true or
    sample.ordersSent~=0 or sample.localsWritten~=0 or
    sample.dispatchAuthorized~=false or sample.weaponSwitchAuthorized~=false or
    sample.sameLuaListenerInvocation~=true or
    sample.rawInventoryDoubleReadConsistent~=true or
    sample.selectedDerivedStatsDoubleReadConsistent~=true or
    sample.r4Status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or
    sample.alternativeAPRVerified~=false or
    sample.launcherAmmoPairVerified~=false or
    sample.completeActiveEffectsVerified~=false or
    sample.epsManualQueueVerified~=false then return out end
 if not int(sample.actor,1,2147483647) or
    not int(sample.partyIndex,0,5) or
    not int(sample.actionRaw,0,65535) or
    not int(sample.selectedWeaponRaw,0,65535) or
    not int(sample.selectedAbilityRaw,0,65535) or
    not int(sample.selectedAprKeyRaw,0,10) then
  out.reason='R33_SCALARS_INVALID';return out end
 local s=sample.sampledStatsRaw
 if type(s)~='table' then out.reason='R33_STATS_UNAVAILABLE';return out end
 local stats={}
 for i,k in ipairs(SAMPLED) do
  local lohi=LIMITS[k]
  if not int(s[k],lohi[1],lohi[2]) then
   out.reason='R33_STATS_MISSING_'..k;return out
  end
  stats[i]=s[k]
 end
 if stats[1]~=sample.selectedAprKeyRaw then
  out.reason='R33_APR_MISMATCH';return out end
 local p=sample.rawProficiencyStat89to134
 if type(p)~='table' or #p~=46 then
  out.reason='R33_PROF_46_MISSING';return out end
 local prof={}
 for i=1,46 do
  if not int(p[i],-2147483648,2147483647) then
   out.reason='R33_PROF_UNREADABLE';return out end
  prof[i]=p[i]
 end
 local weapon=gear(sample.quickWeaponsRaw,35,'QUICKWEAPON')
 local quiver=gear(sample.quiversRaw,11,'QUIVER')
 local off=validSlot(sample.offhandRaw,9,'OFFHAND_OR_SHIELD',0)
 if weapon==nil or quiver==nil or off==nil then
  out.reason='R33_RAW_GEAR_INCOMPLETE';return out end
 local all={}
 for _,t in ipairs(weapon) do all[#all+1]=t end
 for _,t in ipairs(quiver) do all[#all+1]=t end
 all[#all+1]=off
 local q=sample.queueSnapshotStable==true and sample.queuedActionsRaw or nil
 if q~=nil and not int(q,0,512) then out.reason='R33_QUEUE_INVALID';return out end
 out.status='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY';out.reason=nil
 out.actor=sample.actor
 out.party=sample.partyIndex
 out.selected=sample.selectedWeaponRaw
 out.ability=sample.selectedAbilityRaw
 out.actionRaw=sample.actionRaw
 out.stats=stats;out.profRaw=prof;out.gear=all
 out.queueRaw=q
 out.actionSourceRaw=sample.actionSourceStable==true and sample.actionSourceRaw or nil
 out.actionSourceSemantics='UNKNOWN'
 out.sourceIsSameCallbackR33=true
 return out
end
function M.compare(before,after)
 local out=safe('HOLD_CONTEXT_COMPARISON','CAPTURE_UNVERIFIED')
 if type(before)~='table' or type(after)~='table' or
    before.schema~=out.schema or after.schema~=out.schema or
    before.status~='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY' or
    after.status~='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY' then return out end
 if before.actor~=after.actor or before.party~=after.party then
  out.reason='ACTOR_OR_PARTY_CHANGED';return out end
 out.reason=nil
 local selection=before.selected~=after.selected or before.ability~=after.ability
 local items=not equalGear(before.gear,after.gear)
 local stats=not equalArray(before.stats,after.stats) or
             not equalArray(before.profRaw,after.profRaw)
 local action=before.actionRaw~=after.actionRaw or
   before.queueRaw~=after.queueRaw or
   before.actionSourceRaw~=after.actionSourceRaw
 if selection then out.status='NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE'
 elseif items then out.status='EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE'
 elseif stats then out.status='OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE'
 elseif action then out.status='ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE'
 else out.status='RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF' end
 out.invalidateCachedAdvice=selection or items or stats or action
 out.weaponCommandsAllowed=false
 out.observedAmmoDeltaInR33Raw=false
 -- Raw evidence can say a quantity changed; it cannot prove a shot was fired.
 if items then
  for i=1,9 do
   if before.gear[i][1]>=11 and before.gear[i][1]<=14 and
      before.gear[i][2]==after.gear[i][2] and
      before.gear[i][3]~=after.gear[i][3] then
    out.observedAmmoDeltaInR33Raw=true
   end
  end
 end
 return out
end
return M
end)()
local R27 = (function()
-- BGXAI R27 revised SOURCE ONLY: SHA-pinned R2 identity double-read.
-- NOT INSTALLED. Does not change original M_BGXR27.lua.
local R2_CORE = (function()
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
end)()
local R4_CORE = (function()
-- BGXAI R4: passive EEex derived stats evidence (SOURCE ONLY, NOT INSTALLED).
-- Access only known fields from EEex-Docs CDerivedStatsTemplate (x64).
-- Selected weapon stats apply to the CURRENT selection, NEVER every quickslot.
-- No engine actions, no LOCALS/BCS/WeiDU changes, no queued-activity inference.
local M = {version='BGXAI_WEAPON_ACTIVE_R4_ALL_PROF_SOURCE_ONLY'}
-- Weapon proficiency IDs 89..115 are documented EE WPROF.IDS categories.
-- 116..134 are extra raw stat slots: do NOT claim the mod's names or effective pips.
-- This data only describes the selected character, not an alternate weapon's APR.
local BASE_FIELDS={
 'm_nNumberOfAttacks','m_nTHAC0','m_nLevel1','m_nLevel2','m_nLevel3','m_nKit',
 'm_nSTR','m_nSTRExtra','m_nDEX','m_nDamageBonus',
 'm_nMeleeTHAC0Bonus','m_nMeleeDamageBonus','m_nMissileTHAC0Bonus','m_nMissileDamageBonus',
 'm_nHitBonus','m_bImprovedHaste','m_nLuck','m_nLevelDrain',
 'm_THAC0BonusRight','m_THAC0BonusLeft','m_DamageBonusRight','m_DamageBonusLeft'
}
local PROFICIENCY_BY_ID={
 [89]='m_nProficiencyBastardSword',
 [90]='m_nProficiencyLongSword',
 [91]='m_nProficiencyShortSword',
 [92]='m_nProficiencyAxe',
 [93]='m_nProficiencyTwoHandedSword',
 [94]='m_nProficiencyKatana',
 [95]='m_nProficiencyScimitarWakisashiNinjaTo',
 [96]='m_nProficiencyDagger',
 [97]='m_nProficiencyWarhammer',
 [98]='m_nProficiencySpear',
 [99]='m_nProficiencyHalberd',
 [100]='m_nProficiencyFlailMorningStar',
 [101]='m_nProficiencyMace',
 [102]='m_nProficiencyQuarterStaff',
 [103]='m_nProficiencyCrossbow',
 [104]='m_nProficiencyLongBow',
 [105]='m_nProficiencyShortBow',
 [106]='m_nProficiencyDart',
 [107]='m_nProficiencySling',
 [108]='m_nProficiencyBlackjack',
 [109]='m_nProficiencyGun',
 [110]='m_nProficiencyMartialArts',
 [111]='m_nProficiency2Handed',
 [112]='m_nProficiencySwordAndShield',
 [113]='m_nProficiencySingleWeapon',
 [114]='m_nProficiency2Weapon',
 [115]='m_nProficiencyClub'
}
for profId=116,134 do
 PROFICIENCY_BY_ID[profId]='m_nExtraProficiency'..tostring(profId-114)
end
local FIELDS={}
for _,name in ipairs(BASE_FIELDS) do FIELDS[#FIELDS+1]=name end
for profId=89,134 do FIELDS[#FIELDS+1]=PROFICIENCY_BY_ID[profId] end
M.fields=FIELDS
M.proficiencyFieldById=PROFICIENCY_BY_ID
M.proficiencyIdMin=89
M.proficiencyIdMax=134
M.standardProficiencyIdMax=115
-- Never assign an ID 116..134 to a mod proficiency name without a live WPROF.IDS audit.
function M.lookupProficiencyForItem(snapshot,item)
 local hold={status='HOLD_PROFICIENCY_FOR_ITEM_UNVERIFIED',proficiencyRawOnly=true,
  actorProficiencyRankVerified=false,installedWPROFMappingVerified=false,
  alternateSlotAPRVerified=false,dispatchAuthorized=false,executable=false}
 if type(snapshot)~='table' or type(snapshot.fields)~='table' or
    type(item)~='table' or type(item.proficiencyIdRaw)~='number' or
    item.proficiencyIdRaw%1~=0 then return hold end
 local profId=item.proficiencyIdRaw
 local name=PROFICIENCY_BY_ID[profId]
 if name==nil then hold.reason='ITEM_PROFICIENCY_OUTSIDE_AUDITED_IDS';return hold end
 local value=snapshot.fields[name]
 if type(value)~='number' or value~=math.floor(value) then
  hold.reason='ACTOR_PROFICIENCY_FIELD_UNREADABLE';return hold end
 return {status=profId<=115 and 'RAW_STANDARD_PROFICIENCY_ID_MATCH' or
   'HOLD_MODDED_WPROF_NAME_UNVERIFIED',proficiencyIdRaw=profId,field=name,
   rawValue=value,proficiencyRawOnly=true,actorProficiencyRankVerified=false,
   installedWPROFMappingVerified=false,alternateSlotAPRVerified=false,
   dispatchAuthorized=false,executable=false}
end
local function protected(fn)
 local ok,value=pcall(fn)
 if ok then return value end
 return nil
end
local function integer(x,lo,hi)
 return type(x)=='number' and x==math.floor(x) and x>=lo and x<=hi
end
local function bound(x,lo,hi)
 if integer(x,lo,hi) then return x end
 return nil
end
local function empty(status)
 return {schema='BGXAI_WEAPON_ACTIVE_R4',status=status,readOnly=true,
   selectedOnly=true,allBuffsObserved=false,allEffectsObserved=false,
   alternateSlotAPRVerified=false,manualOrderProven=false,epsQueueProven=false,
   actionable=false,weaponSwitchAuthorized=false,dispatchAuthorized=false}
end
function M.observe(sprite, action, partyIndex, getStats)
 local result=empty('HOLD_INCOMPLETE_ACTIVE_STATS')
 if sprite==nil then return result end
 result.actorId=bound(protected(function() return sprite.m_id end),0,2147483647)
 if result.actorId==nil then result.status='HOLD_ACTOR_ID_UNAVAILABLE';return result end
 result.partyIndex=bound(partyIndex,0,5)
 result.actionRaw=bound(protected(function() return action.m_actionID end),0,65535)
 local eq=protected(function() return sprite.m_equipment end)
 result.selectedWeaponRaw=bound(protected(function() return eq.m_selectedWeapon end),0,65535)
 result.selectedAbilityRaw=bound(protected(function() return eq.m_selectedWeaponAbility end),0,65535)
 if getStats==nil then getStats=EEex_Sprite_GetActiveStats end
 if type(getStats)~='function' then result.status='HOLD_ACTIVE_STATS_API_MISSING';return result end
 local stats=protected(function() return getStats(sprite) end)
 if stats==nil then result.status='HOLD_ACTIVE_STATS_ACCESS_FAILED';return result end
 result.fields={};result.presentCount=0;result.missingCount=0
 for _,name in ipairs(FIELDS) do
  local value=bound(protected(function() return stats[name] end),-2147483648,2147483647)
  if value==nil then
   result.fields[name]=false -- false denotes UNREADABLE, not integer 0
   result.missingCount=result.missingCount+1
  else
   result.fields[name]=value
   result.presentCount=result.presentCount+1
  end
 end
 -- We only have a sample of the engine's active stats. There are more effects,
 -- conditions, time states and action queue contents than these fields capture.
 if result.selectedWeaponRaw and result.fields.m_nNumberOfAttacks~=false then
  result.status='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS'
 else result.status='HOLD_APR_OR_SELECTED_SLOT_MISSING' end
 return result
end
function M.compare(before,after)
 local output=empty('HOLD_UNCOMPARABLE_SNAPSHOTS')
 if type(before)~='table' or type(after)~='table' or
     before.actorId==nil or before.actorId~=after.actorId or
     type(before.fields)~='table' or type(after.fields)~='table' then return output end
 output.actorId=before.actorId
 local changes={}
 if before.selectedWeaponRaw~=after.selectedWeaponRaw or
    before.selectedAbilityRaw~=after.selectedAbilityRaw then
  changes[#changes+1]='SELECTION_CHANGED'
 end
 for _,name in ipairs(FIELDS) do
  if before.fields[name]~=after.fields[name] then changes[#changes+1]=name end
 end
 output.changedFields=changes
 output.changeCount=#changes
 output.status=#changes>0 and 'INVALIDATE_CACHED_WEAPON_ADVICE_KEEP_ACTION' or
  'RAW_SELECTED_STATS_UNCHANGED_NOT_PROOF_OF_ALL_EFFECTS'
 return output
end
-- Holy Power / Champion's Strength / druid form / haste can change derived
-- THAC0, STR or APR without changing class or permanent proficiency. The
-- observed change is evidence for re-ranking only, NEVER identification of a
-- particular spell or a switch authorization. In particular fighter-like THAC0
-- is not proof of fighter specialization or fighter-level APR.
local COMBAT_DYNAMIC={
 'm_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nSTRExtra','m_nDEX',
 'm_nDamageBonus','m_nMeleeTHAC0Bonus','m_nMeleeDamageBonus',
 'm_nMissileTHAC0Bonus','m_nMissileDamageBonus','m_nHitBonus',
 'm_bImprovedHaste','m_nLuck','m_nLevelDrain',
 'm_THAC0BonusRight','m_THAC0BonusLeft','m_DamageBonusRight','m_DamageBonusLeft'
}
local CLASS_DYNAMIC={'m_nLevel1','m_nLevel2','m_nLevel3','m_nKit'}
function M.auditTemporaryCombatShift(before,after)
 local out={status='HOLD_UNCOMPARABLE_COMBAT_BUFF_SNAPSHOTS',
  selectedStatsOnly=true,spellIdentityVerified=false,allBuffsObserved=false,
  fighterClassGranted=false,fighterProficienciesGranted=false,
  fighterAPRNotInferred=true,fullPerSlotAPRVerified=false,
  currentActionPreserved=true,ordersSent=0,executable=false,
  weaponSwitchAuthorized=false,dispatchAuthorized=false}
 if type(before)~='table' or type(after)~='table' or
   not integer(before.actorId,0,2147483647) or
   before.actorId~=after.actorId or
   type(before.fields)~='table' or type(after.fields)~='table' then
  return out end
 out.actorId=before.actorId
 if before.selectedWeaponRaw~=after.selectedWeaponRaw or
    before.selectedAbilityRaw~=after.selectedAbilityRaw then
  out.status='HOLD_SELECTION_CHANGED_REAUDIT_ALL_WEAPONS'
  return out end
 for _,name in ipairs(CLASS_DYNAMIC) do
  local a=before.fields[name];local b=after.fields[name]
  if not integer(a,-2147483648,2147483647) or
     not integer(b,-2147483648,2147483647) then
   out.status='HOLD_CLASS_STAT_UNREADABLE';return out end
  if a~=b then out.status='HOLD_CLASS_OR_KIT_CHANGED_NOT_BUFF_PROOF';return out end
 end
 for id=89,134 do
  local name=PROFICIENCY_BY_ID[id]
  local a=before.fields[name];local b=after.fields[name]
  if not integer(a,-2147483648,2147483647) or
     not integer(b,-2147483648,2147483647) then
   out.status='HOLD_PROFICIENCY_UNREADABLE';return out end
  if a~=b then
   out.status='HOLD_PROFICIENCY_CHANGED_REAUDIT_WEAPON';return out end
 end
 local changes={}
 for _,name in ipairs(COMBAT_DYNAMIC) do
  local a=before.fields[name];local b=after.fields[name]
  if not integer(a,-2147483648,2147483647) or
     not integer(b,-2147483648,2147483647) then
   out.status='HOLD_CURRENT_COMBAT_STAT_UNREADABLE';return out end
  if a~=b then changes[#changes+1]={field=name,fromRaw=a,toRaw=b} end
 end
 out.changed=changes;out.changeCount=#changes
 out.beforeAPRRaw=before.fields.m_nNumberOfAttacks
 out.afterAPRRaw=after.fields.m_nNumberOfAttacks
 out.beforeTHAC0Raw=before.fields.m_nTHAC0
 out.afterTHAC0Raw=after.fields.m_nTHAC0
 out.status=#changes>0 and 'CURRENT_SELECTED_COMBAT_SHIFT_RECALCULATE_KEEP_ACTION' or
  'NO_OBSERVED_SHIFT_BUFFS_STILL_NOT_EXHAUSTIVE'
 return out
end

-- This is an index of the *proven observed fields*, not a proof of pips,
-- ability-specific APR, buff completeness, item usability, or action safety.
function M.classifyObservedEvidence(snapshot)
 if type(snapshot)~='table' or snapshot.status~=
     'RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS' or
     type(snapshot.fields)~='table' then
  return {status='HOLD_NO_CURRENT_SELECTED_EVIDENCE',dispatchAuthorized=false} end
 local APR={ [0]=0,[1]=1,[2]=2,[3]=3,[4]=4,[5]=5,[6]=0.5,[7]=1.5,[8]=2.5,[9]=3.5,[10]=4.5 }
 local k=snapshot.fields.m_nNumberOfAttacks
 return {status=APR[k] and 'PASSIVE_SELECTED_APR_DECODED' or 'HOLD_APR_ENCODING_UNKNOWN',
  selectedWeaponRaw=snapshot.selectedWeaponRaw,aprRaw=k,
  selectedAPRIfStandard=APR[k],projectionToOtherSlotsAllowed=false,
  activeEffectFingerprintComplete=false,dispatchAuthorized=false,
  executable=false}
end
-- EEex 1.1.7 EEex_Sprite_GetActiveStats chooses m_tempStats when
-- m_bAllowEffectListCall == 0. Such work-in-progress stats must NEVER be
-- treated as a stable selected APR for Weapon Priority. Fail closed if the
-- flag is unreadable, nonstandard, or changes during the two read samples.
-- These reads do NOT establish all active effects, event ID or action origin.
function M.observeStableDerived(sprite, action, partyIndex, getStats)
 local function flag()
  return bound(protected(function() return sprite.m_bAllowEffectListCall end),0,255)
 end
 local out=empty('HOLD_DERIVED_STATS_VIEW_UNVERIFIED')
 if sprite==nil or flag()~=1 then return out end
 local a=M.observe(sprite,action,partyIndex,getStats)
 if flag()~=1 then return empty('HOLD_DERIVED_STATS_TEMP_VIEW_DURING_READ') end
 if a.status~='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS' or
    a.missingCount~=0 or a.presentCount~=#FIELDS then
  return empty('HOLD_DERIVED_STATS_FIELDS_INCOMPLETE') end
 local b=M.observe(sprite,action,partyIndex,getStats)
 if flag()~=1 then return empty('HOLD_DERIVED_STATS_TEMP_VIEW_DURING_RECHECK') end
 if b.status~='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS' or
    b.missingCount~=0 or b.presentCount~=#FIELDS then
  return empty('HOLD_DERIVED_STATS_RECHECK_INCOMPLETE') end
 -- A script/action or selection can change *inside* the second getter after
 -- M.observe has sampled its header. Re-read the headers after both calls.
 local eq=protected(function() return sprite.m_equipment end)
 local actorNow=bound(protected(function() return sprite.m_id end),0,2147483647)
 local actionNow=bound(protected(function() return action.m_actionID end),0,65535)
 local selectionNow=bound(protected(function() return eq.m_selectedWeapon end),0,65535)
 local abilityNow=bound(protected(function() return eq.m_selectedWeaponAbility end),0,65535)
 if actorNow~=a.actorId or actionNow~=a.actionRaw or
    selectionNow~=a.selectedWeaponRaw or abilityNow~=a.selectedAbilityRaw then
  return empty('HOLD_DERIVED_STATS_SELECTION_OR_ACTION_CHANGED') end
 if a.actorId~=b.actorId or a.partyIndex~=b.partyIndex or
    a.actionRaw~=b.actionRaw or a.selectedWeaponRaw~=b.selectedWeaponRaw or
    a.selectedAbilityRaw~=b.selectedAbilityRaw then
  return empty('HOLD_DERIVED_STATS_SELECTION_OR_ACTION_CHANGED') end
 local difference=M.compare(a,b)
 if difference.status~='RAW_SELECTED_STATS_UNCHANGED_NOT_PROOF_OF_ALL_EFFECTS' then
  return empty('HOLD_DERIVED_STATS_CHANGED_DURING_READ') end
 a.status='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS'
 a.activeStatsReadPath='EEEX117_M_DERIVEDSTATS_FLAG_NONZERO_SOURCE_CONTRACT'
 a.derivedStatsDoubleReadConsistent=true
 a.runtimeEngineAuthenticated=false
 a.allBuffsObserved=false
 a.allEffectsObserved=false
 a.alternateSlotAPRVerified=false
 a.dispatchAuthorized=false
 return a
end
return M
end)()
local Q81_CORE = (function()
-- BGXAI 081 V3: passive raw action-context evidence, NEVER origin authorization.
-- SOURCE ONLY. No hooks, actions, LOCALS, timers, files or game writes.
-- m_source is recorded as an unclassified candidate, not manual/EPS proof.
local M={version='0.3.51-081-ACTION-CONTEXT-V3',installed=false}

local function integer(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
  x%1==0 and x>=lo and x<=hi
end

local function read_int(obj,key,lo,hi)
 if obj==nil then return nil end
 local ok,value=pcall(function() return obj[key] end)
 if ok and integer(value,lo,hi) then return value end
 return nil
end

local function read_nested_int(obj,parentKey,key,lo,hi)
 if obj==nil then return nil end
 local ok,parent=pcall(function() return obj[parentKey] end)
 if not ok or parent==nil then return nil end
 return read_int(parent,key,lo,hi)
end

local function current_action_id(sprite)
 if sprite==nil then return nil end
 local ok,action=pcall(function() return sprite.m_curAction end)
 if not ok or action==nil then return nil end
 return read_int(action,'m_actionID',0,65535)
end

local function queue_count(sprite)
 if sprite==nil then return nil end
 local function once()
  local q=sprite.m_queuedActions
  if q==nil then return nil end
  return q.m_nCount
 end
 local okA,a=pcall(once)
 if not okA or not integer(a,0,512) then return nil,'QUEUE_COUNT_NOT_READABLE' end
 local okB,b=pcall(once)
 if not okB or not integer(b,0,512) then return nil,'QUEUE_COUNT_NOT_READABLE' end
 if a~=b then return nil,'QUEUE_COUNT_CHANGED_DURING_READ' end
 return a,'RAW_QUEUE_COUNT_STABLE'
end

local function printable_ascii(value)
 if type(value)~='string' or #value<1 or #value>48 then return false end
 for i=1,#value do
  local b=value:byte(i)
  if b<32 or b>126 then return false end
 end
 return true
end

local function read_action_source(action)
 if action==nil then return nil,'ACTION_SOURCE_ACTION_UNAVAILABLE' end
 local ok,source=pcall(function() return action.m_source end)
 if not ok or source==nil then return nil,'ACTION_SOURCE_FIELD_UNAVAILABLE' end
 if type(source)=='string' then
  if printable_ascii(source) then return source,'SOURCE_RAW_OBSERVED' end
  return nil,'ACTION_SOURCE_STRING_INVALID'
 end
 local okPtr,ptr=pcall(function() return source.m_pchData end)
 if not okPtr or not integer(ptr,65536,140737488355327) then
  return nil,'ACTION_SOURCE_POINTER_UNAVAILABLE'
 end
 local reader=rawget(_G,'EEex_ReadLString')
 if type(reader)~='function' then return nil,'EEEX_READLSTRING_UNAVAILABLE' end
 local okRead,value=pcall(reader,ptr,49)
 if not okRead or type(value)~='string' then return nil,'ACTION_SOURCE_READ_FAILED' end
 if #value>48 then return nil,'ACTION_SOURCE_TRUNCATED' end
 if value=='' then return nil,'ACTION_SOURCE_EMPTY' end
 if not printable_ascii(value) then return nil,'ACTION_SOURCE_NONPRINTABLE' end
 return value,'SOURCE_RAW_OBSERVED'
end

local function context_once(sprite,action)
 local source,sourceStatus=read_action_source(action)
 return {
  inActionExecution=read_int(sprite,'m_bInActionExecution',0,1),
  noInterrupt=read_int(sprite,'m_bNoInterrupt',0,1),
  curScriptNum=read_int(sprite,'m_curScriptNum',-32768,32767),
  actionCount=read_int(sprite,'m_actionCount',-32768,32767),
  interrupt=read_int(sprite,'m_interrupt',-2147483648,2147483647),
  orderedByInstance=read_nested_int(sprite,'m_lOrderedBy','m_Instance',0,2147483647),
  orderedBySentInstance=read_nested_int(sprite,'m_lOrderedBySent','m_Instance',0,2147483647),
  actionSource=source,
  actionSourceStatus=sourceStatus,
 }
end

local function context_stable(a,b)
 return a.inActionExecution~=nil and b.inActionExecution==a.inActionExecution and
  a.noInterrupt~=nil and b.noInterrupt==a.noInterrupt and
  a.curScriptNum~=nil and b.curScriptNum==a.curScriptNum and
  a.actionCount~=nil and b.actionCount==a.actionCount and
  a.interrupt~=nil and b.interrupt==a.interrupt and
  a.orderedByInstance==b.orderedByInstance and
  a.orderedBySentInstance==b.orderedBySentInstance
end

function M.observe(sprite,action)
 local idBefore=current_action_id(sprite)
 local q1,q1Status=queue_count(sprite)
 local c1=context_once(sprite,action)
 local q2,q2Status=queue_count(sprite)
 local c2=context_once(sprite,action)
 local idAfter=current_action_id(sprite)
 local callbackId=read_int(action,'m_actionID',0,65535)
 local actionStable=idBefore~=nil and idBefore==idAfter and callbackId==idBefore
 if not actionStable then
  return {
   status='ACTION_UNKNOWN',reason='ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT',
   current_action_id=nil,queue_empty=nil,queue_count_raw=nil,
   queue_count_observed=false,queue_count_read_status='QUEUE_OR_ACTION_UNSTABLE',
   action_context_snapshot_stable=false,action_source_stable=false,
   action_source_raw=nil,action_source_read_status='ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT',
   action_origin='UNKNOWN',action_origin_verified=false,
   manual_command=nil,manual_command_verified=false,eps_queue_empty_verified=false,
   safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0,
  }
 end
 local queueStable=q1~=nil and q2~=nil and q1==q2
 local contextStable=context_stable(c1,c2)
 local sourceStable=c1.actionSourceStatus=='SOURCE_RAW_OBSERVED' and
  c2.actionSourceStatus=='SOURCE_RAW_OBSERVED' and c1.actionSource==c2.actionSource
 local sourceStatus=c1.actionSourceStatus
 if c1.actionSourceStatus~=c2.actionSourceStatus then
  sourceStatus='ACTION_SOURCE_STATUS_CHANGED_DURING_READ'
 elseif c1.actionSourceStatus=='SOURCE_RAW_OBSERVED' and c1.actionSource~=c2.actionSource then
  sourceStatus='ACTION_SOURCE_CHANGED_DURING_READ'
 end
 local qNonempty=nil
 if queueStable then qNonempty=(q1>0) end
 local qStatus=q1Status
 if q1Status~=q2Status then qStatus='QUEUE_COUNT_STATUS_CHANGED_DURING_READ'
 elseif q1~=q2 then qStatus='QUEUE_COUNT_CHANGED_DURING_CAPTURE' end
 return {
  status='CURRENT_ACTION_CONTEXT_OBSERVED',reason='ORIGIN_NOT_PROVEN',
  current_action_id=idBefore,
  queue_empty=nil,
  queue_count_raw=queueStable and q1 or nil,
  queue_count_observed=queueStable,
  queue_count_read_status=queueStable and 'RAW_QUEUE_COUNT_STABLE' or qStatus,
  queue_nonempty_observed=qNonempty,
  action_context_snapshot_stable=contextStable,
  engine_action_execution_raw=contextStable and c1.inActionExecution or nil,
  engine_no_interrupt_raw=contextStable and c1.noInterrupt or nil,
  current_script_number_raw=contextStable and c1.curScriptNum or nil,
  action_count_raw=contextStable and c1.actionCount or nil,
  interrupt_raw=contextStable and c1.interrupt or nil,
  ordered_by_instance_raw=contextStable and c1.orderedByInstance or nil,
  ordered_by_sent_instance_raw=contextStable and c1.orderedBySentInstance or nil,
  action_source_stable=sourceStable,
  action_source_raw=sourceStable and c1.actionSource or nil,
  action_source_read_status=sourceStatus,
  action_source_semantics='UNCLASSIFIED_CAI_ACTION_M_SOURCE',
  eps_queue_empty_verified=false,
  action_origin='UNKNOWN',action_origin_verified=false,
  manual_command=nil,manual_command_verified=false,
  casting=nil,healing=nil,buffing=nil,singing=nil,detecting_traps=nil,
  safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0,
 }
end

function M.arbitrate(advisory,snapshot)
 return {status='HOLD',reason='ACTION_ORIGIN_AND_SAFE_BOUNDARY_NOT_PROVEN',
  allow_engine_action=false,orders_sent=0,locals_written=0,
  verified_queue_empty=false,verified_origin=false}
end
return M
end)()
-- BGXAI R27 read-only single-callback candidate.
-- This file is *source only*. It does not register a hook by itself.
-- It composes unchanged R2 and R4 observation cores directly in one call.
-- No item:getAbility, getLauncher, Demand, BCS/LOCALS, inventory or actions.
-- Inventory V3 embedded source-only, no independent EEex listener.
local INV3=(function()
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
return M

end)()
local R27 = {schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  sourceOnly=true, registered=false, recorded=0, limit=64, errors=0,
  gameModified=false, ordersSent=0}

local function int(v,lo,hi)
 return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge
  and v%1==0 and v>=lo and v<=hi
end
local function scalar(obj,key,lo,hi)
 if obj==nil then return nil end
 local ok,val=pcall(function() return obj[key] end)
 if ok and int(val,lo,hi) then return val end
 return nil
end
local function before_after(sprite,action)
 local actor=scalar(sprite,'m_id',1,2147483647)
 local aid=scalar(action,'m_actionID',0,65535)
 local ok,eq=pcall(function() return sprite.m_equipment end)
 if not ok then eq=nil end
 local weapon=scalar(eq,'m_selectedWeapon',0,65535)
 local ability=scalar(eq,'m_selectedWeaponAbility',0,65535)
 -- An AI object class is only a RAW candidate; it is not an authenticated
 -- active dual/multiclass row or KITLIST / CLASS.IDS mapping.
 local okClass,typeAI=pcall(function()return sprite.m_typeAI end)
 local aiClass=okClass and scalar(typeAI,'m_Class',0,255) or nil
 return {actor=actor,action=aid,weapon=weapon,ability=ability,
  aiClass=aiClass}
end
local function same(a,b)
 return a.actor~=nil and a.action~=nil and a.weapon~=nil and
   a.ability~=nil and a.actor==b.actor and a.action==b.action and
   a.weapon==b.weapon and a.ability==b.ability and
   a.aiClass==b.aiClass
end
local function hold(reason,ord)
 return {schema=R27.schema,status='HOLD_SINGLE_CALLBACK_NO_DISPATCH',
  reason=reason,collectorOrdinal=ord,readOnly=true,sourceOnly=true,
  gameModified=false,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  currentActionPreserved=true,actionQueueCleared=false,
  nativeEventTokenAuthenticated=false,alternativeAPRVerified=false,
  launcherAmmoPairVerified=false,completeActiveEffectsVerified=false,
  epsManualQueueVerified=false,engineSessionVerified=false}
end
R27.hold=hold
-- Safe to use in a controlled unit test; callable from a future separately
-- approved EEex action-start listener. The read-only cores do all raw reads.
function R27.observe(sprite,action,partyIndex,getActiveStats)
 if sprite==nil or action==nil or not int(partyIndex,0,5) then
  return hold('ACTOR_ACTION_OR_PARTY_UNAVAILABLE') end
 local b=before_after(sprite,action)
 local queueBefore=Q81_CORE.observe(sprite,action)
 if not same(b,b) then return hold('START_EVENT_KEYS_UNREADABLE') end
 local ok2,r2=pcall(R2_CORE.observe_sprite,sprite)
 if not ok2 or type(r2)~='table' then return hold('R2_CORE_EXCEPTION') end
 local ok4,r4=pcall(R4_CORE.observeStableDerived,sprite,action,partyIndex,getActiveStats)
 if not ok4 or type(r4)~='table' then return hold('R4_CORE_EXCEPTION') end
 local a=before_after(sprite,action)
 if not same(b,a) then return hold('SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE') end
 local ok2later,r2later=pcall(R2_CORE.observe_sprite,sprite)
 if not ok2later or type(r2later)~='table' then return hold('R2_RECHECK_EXCEPTION') end
 local okCmp,stability=pcall(R2_CORE.compare,r2,r2later)
 if not okCmp or type(stability)~='table' then return hold('R2_COMPARE_EXCEPTION') end
 if stability.status=='INVALIDATE_WEAPON_ADVICE_KEEP_ACTION' then
  return hold('EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE') end
 if stability.status~='RAW_FINGERPRINT_SAME_NOT_PROOF_OF_BUFFS' then
  return hold('R2_RECHECK_INCOMPLETE') end
 if not same(b,before_after(sprite,action)) then
  return hold('SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE') end
 local queueAfter=Q81_CORE.observe(sprite,action)
 local qStable=queueBefore.queue_count_observed==true and
  queueAfter.queue_count_observed==true and
  queueBefore.current_action_id==b.action and
  queueAfter.current_action_id==b.action and
  queueBefore.queue_count_raw==queueAfter.queue_count_raw
 local qCount=qStable and queueBefore.queue_count_raw or nil
 local ctxStable=queueBefore.action_context_snapshot_stable==true and
  queueAfter.action_context_snapshot_stable==true and
  queueBefore.engine_action_execution_raw==queueAfter.engine_action_execution_raw and
  queueBefore.engine_no_interrupt_raw==queueAfter.engine_no_interrupt_raw and
  queueBefore.current_script_number_raw==queueAfter.current_script_number_raw and
  queueBefore.action_count_raw==queueAfter.action_count_raw and
  queueBefore.interrupt_raw==queueAfter.interrupt_raw and
  queueBefore.ordered_by_instance_raw==queueAfter.ordered_by_instance_raw and
  queueBefore.ordered_by_sent_instance_raw==queueAfter.ordered_by_sent_instance_raw
 local srcStable=queueBefore.action_source_stable==true and
  queueAfter.action_source_stable==true and
  queueBefore.action_source_raw==queueAfter.action_source_raw
 local srcStatus=queueBefore.action_source_read_status
 if srcStatus~=queueAfter.action_source_read_status then
  srcStatus='ACTION_SOURCE_STATUS_CHANGED_DURING_CAPTURE'
 elseif queueBefore.action_source_raw~=queueAfter.action_source_raw then
  srcStatus='ACTION_SOURCE_CHANGED_DURING_CAPTURE' end
 if r4.status~='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' or
    r4.derivedStatsDoubleReadConsistent~=true then
  return hold('R4_DERIVED_STATS_NOT_STABLE') end
 if r2.actorId~=b.actor or r4.actorId~=b.actor or
  r2.selectedWeaponRaw~=b.weapon or r4.selectedWeaponRaw~=b.weapon or
  r2.selectedAbilityRaw~=b.ability or r4.selectedAbilityRaw~=b.ability or
  r4.actionRaw~=b.action or r4.partyIndex~=partyIndex then
  return hold('R2_R4_SCALARS_DISAGREE') end
 local f=r4.fields
 local rawApr=type(f)=='table' and f.m_nNumberOfAttacks or nil
 if not int(rawApr,0,10) then return hold('CURRENT_SELECTED_APR_UNAVAILABLE') end
  -- Reuse the EXACT existing R4 double-read for 46 WPROF raw stat slots.
  -- No additional getActiveStats call or listener. False -> JSON null.
  local profRaw={}
  for id=89,134 do
   local field=R4_CORE.proficiencyFieldById[id]
   local v=field and f[field] or nil
   profRaw[#profRaw+1]=int(v,-2147483648,2147483647) and v or false
  end
  -- These are raw values, not actual pips, weapon-to-group mapping or
  -- live-class rights. They must NEVER unlock the existing V5 dispatch.
  -- Observe but never turn a selected-only APR into alternative-slot evidence.
  -- The R2 slot data are still only raw candidates, not validated items.
  return {schema=R27.schema,status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  actor=b.actor,partyIndex=partyIndex,actionRaw=b.action,
  selectedWeaponRaw=b.weapon,selectedAbilityRaw=b.ability,
  selectedAprKeyRaw=rawApr,r2Status=r2.status,r4Status=r4.status,
  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,offhandRaw=r2.offhand,
  rawInventoryDoubleReadConsistent=true,
  queueSnapshotStable=qStable,queuedActionsRaw=qCount,
  actionOriginVerified=false,manualEpsQueueVerified=false,
  actionContextSnapshotStable=ctxStable,
  engineActionExecutionRaw=ctxStable and queueBefore.engine_action_execution_raw or nil,
  engineNoInterruptRaw=ctxStable and queueBefore.engine_no_interrupt_raw or nil,
  currentScriptNumberRaw=ctxStable and queueBefore.current_script_number_raw or nil,
  actionCountRaw=ctxStable and queueBefore.action_count_raw or nil,
  interruptRaw=ctxStable and queueBefore.interrupt_raw or nil,
  orderedByInstanceRaw=ctxStable and queueBefore.ordered_by_instance_raw or nil,
  orderedBySentInstanceRaw=ctxStable and queueBefore.ordered_by_sent_instance_raw or nil,
  actionSourceStable=srcStable,actionSourceRaw=srcStable and queueBefore.action_source_raw or nil,
  actionSourceReadStatus=srcStatus,
  sampledStatsRaw={m_nNumberOfAttacks=rawApr,
   m_nTHAC0=f.m_nTHAC0,m_nSTR=f.m_nSTR,
   m_nSTRExtra=f.m_nSTRExtra,m_bImprovedHaste=f.m_bImprovedHaste,
   m_nHitBonus=f.m_nHitBonus,m_nLevel1=f.m_nLevel1,
   m_nLevel2=f.m_nLevel2,m_nLevel3=f.m_nLevel3,m_nKit=f.m_nKit},
  rawProficiencyStat89to134=profRaw,aiClassRawCandidate=b.aiClass,
  selectedDerivedStatsDoubleReadConsistent=true,
  sameLuaListenerInvocation=true,nativeEventTokenAuthenticated=false,
  engineSessionVerified=false,alternativeAPRVerified=false,
  launcherAmmoPairVerified=false,completeActiveEffectsVerified=false,
  epsManualQueueVerified=false,readOnly=true,sourceOnly=true,
  gameModified=false,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  currentActionPreserved=true,actionQueueCleared=false}
end

-- Strict bounded JSON for the future single existing-updater diagnostic writer.
-- Only bounded, sanitized CAIAction source text is serialized; no raw pointer or origin classification.
local function jnum(v,lo,hi)
 if int(v,lo,hi) then return tostring(v) end
 return 'null'
end
local function jstr(v)
 if type(v)~='string' or #v<1 or #v>8 or v:find('[^%w_]') then
  return 'null' end
 return '"'..v:upper()..'"'
end
local function jrawstr(v)
 if type(v)~='string' or #v<1 or #v>48 then return 'null' end
 for i=1,#v do local b=v:byte(i);if b<32 or b>126 then return 'null' end end
 return '"'..v:gsub('\\','\\\\'):gsub('"','\\"')..'"'
end
local function jstatus(v)
 local allowed={SOURCE_RAW_OBSERVED=true,ACTION_SOURCE_ACTION_UNAVAILABLE=true,
  ACTION_SOURCE_FIELD_UNAVAILABLE=true,ACTION_SOURCE_POINTER_UNAVAILABLE=true,
  EEEX_READLSTRING_UNAVAILABLE=true,ACTION_SOURCE_READ_FAILED=true,
  ACTION_SOURCE_TRUNCATED=true,ACTION_SOURCE_EMPTY=true,
  ACTION_SOURCE_NONPRINTABLE=true,ACTION_SOURCE_STRING_INVALID=true,
  ACTION_SOURCE_STATUS_CHANGED_DURING_READ=true,
  ACTION_SOURCE_CHANGED_DURING_READ=true,
  ACTION_SOURCE_STATUS_CHANGED_DURING_CAPTURE=true,
  ACTION_SOURCE_CHANGED_DURING_CAPTURE=true,
  ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT=true}
 return allowed[v] and ('"'..v..'"') or 'null'
end
local function jslots(arr,n)
 if type(arr)~='table' or #arr~=n then return '[]' end
 local out={}
 for i=1,n do
  local v=arr[i]
  if type(v)~='table' then return '[]' end
  out[i]='{"slot":'..jnum(v.index,0,38)..
    ',"resrefRaw":'..jstr(v.itemResrefRaw)..
    ',"useCount1Raw":'..jnum(v.useCount1Raw,0,65535)..
    ',"useCount2Raw":'..jnum(v.useCount2Raw,0,65535)..
    ',"useCount3Raw":'..jnum(v.useCount3Raw,0,65535)..'}'
 end
 return '['..table.concat(out,',')..']'
end
local function jstats(stats)
 local keys={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR',
  'm_nSTRExtra','m_bImprovedHaste','m_nHitBonus'}
 local out={}
 for _,key in ipairs(keys) do
  local v=type(stats)=='table' and stats[key] or nil
  out[#out+1]='"'..key..'":'..jnum(v,-2147483648,2147483647)
 end
 return '{'..table.concat(out,',')..'}'
end
-- JSON payload emits existing R4 evidence; never infer actor proficiency rank.
local function jrawprof(values)
 if type(values)~='table' or #values~=46 then return 'null' end
 local t={}
 for i=1,46 do t[i]=jnum(values[i],-2147483648,2147483647) end
 return '['..table.concat(t,',')..']'
end
local function jlevels(s)
 if type(s)~='table' then return 'null' end
 return '{"level1":'..jnum(s.m_nLevel1,0,50)..
  ',"level2":'..jnum(s.m_nLevel2,0,50)..
  ',"level3":'..jnum(s.m_nLevel3,0,50)..
  ',"kitRaw":'..jnum(s.m_nKit,0,4294967295)..'}'
end
function R27.toConsoleJson(sample)
 if type(sample)~='table' or sample.schema~=R27.schema or
   sample.readOnly~=true or sample.ordersSent~=0 or
   sample.dispatchAuthorized~=false or sample.weaponSwitchAuthorized~=false then
  return nil end
 local allowed={CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE=true,
  HOLD_SINGLE_CALLBACK_NO_DISPATCH=true}
 if not allowed[sample.status] then return nil end
 local status=sample.status
 return '{"schema":"'..R27.schema..'","type":"R27_SINGLE_CALLBACK",'..
  '"status":"'..status..'","seq":'..jnum(sample.collectorOrdinal,1,64)..
  ',"actor":'..jnum(sample.actor,1,2147483647)..
  ',"partyIndex":'..jnum(sample.partyIndex,0,5)..
  ',"actionRaw":'..jnum(sample.actionRaw,0,65535)..
  ',"selectedWeaponRaw":'..jnum(sample.selectedWeaponRaw,0,65535)..
  ',"selectedAbilityRaw":'..jnum(sample.selectedAbilityRaw,0,65535)..
  ',"selectedAprKeyRaw":'..jnum(sample.selectedAprKeyRaw,0,10)..
  ',"quickWeaponsRaw":'..jslots(sample.quickWeaponsRaw,4)..
  ',"quiversRaw":'..jslots(sample.quiversRaw,4)..
  ',"offhandRaw":'..jslots(sample.offhandRaw and {sample.offhandRaw},1)..
  ',"rawInventoryDoubleReadConsistent":'..tostring(sample.rawInventoryDoubleReadConsistent==true)..
  ',"selectedDerivedStatsDoubleReadConsistent":'..tostring(sample.selectedDerivedStatsDoubleReadConsistent==true)..
  ',"queueSnapshotStable":'..tostring(sample.queueSnapshotStable==true)..
  ',"queuedActionsRaw":'..jnum(sample.queuedActionsRaw,0,512)..
  ',"queueNonemptyObserved":'..(sample.queueSnapshotStable==true and
    tostring(sample.queuedActionsRaw>0) or 'null')..
  ',"actionContextSnapshotStable":'..tostring(sample.actionContextSnapshotStable==true)..
  ',"engineActionExecutionRaw":'..jnum(sample.engineActionExecutionRaw,0,1)..
  ',"engineNoInterruptRaw":'..jnum(sample.engineNoInterruptRaw,0,1)..
  ',"currentScriptNumberRaw":'..jnum(sample.currentScriptNumberRaw,-32768,32767)..
  ',"actionCountRaw":'..jnum(sample.actionCountRaw,-32768,32767)..
  ',"interruptRaw":'..jnum(sample.interruptRaw,-2147483648,2147483647)..
  ',"orderedByInstanceRaw":'..jnum(sample.orderedByInstanceRaw,0,2147483647)..
  ',"orderedBySentInstanceRaw":'..jnum(sample.orderedBySentInstanceRaw,0,2147483647)..
  ',"actionSourceStable":'..tostring(sample.actionSourceStable==true)..
  ',"actionSourceRaw":'..jrawstr(sample.actionSourceRaw)..
  ',"actionSourceReadStatus":'..jstatus(sample.actionSourceReadStatus)..
  ',"actionSourceSemantics":"UNCLASSIFIED_CAI_ACTION_M_SOURCE"'..
  ',"actionOriginVerified":false,"manualEpsQueueVerified":false'..
  ',"r4Status":'..(sample.r4Status=='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS' and
    '"RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS"' or 'null')..
  ',"selectedStatsRaw":'..jstats(sample.sampledStatsRaw)..
  ',"levelsAndKitRaw":'..jlevels(sample.sampledStatsRaw)..
  ',"aiObjectClassRawCandidate":'..jnum(sample.aiClassRawCandidate,0,255)..
  ',"proficiencyStat89to134Raw":'..jrawprof(sample.rawProficiencyStat89to134)..
  ',"classRowVerified":false,"weaponToProficiencyVerified":false,'..
  '"activeDualMultiClassVerified":false,"actorPipsVerified":false'..
  ',"sameLuaListenerInvocation":'..tostring(sample.sameLuaListenerInvocation==true)..
  ',"nativeEventTokenAuthenticated":false,"engineSessionVerified":false,'..
  '"alternativeAPRVerified":false,"launcherAmmoPairVerified":false,'..
  '"completeActiveEffectsVerified":false,"epsManualQueueVerified":false,'..
  '"ordersSent":0,"localsWritten":0,"dispatchAuthorized":false,'..
  '"weaponSwitchAuthorized":false,"readOnly":true}'
end
-- R37 emits a second bounded JSON status in the SAME R33 console file.
-- Never serialize raw actor id, source pointers or inferred action ownership.
function R27.toR37AdviceJson(sample)
 if type(sample)~='table' or sample.schema~=R27.schema or
    sample.readOnly~=true or sample.ordersSent~=0 or
    sample.dispatchAuthorized~=false or sample.weaponSwitchAuthorized~=false then return nil end
 local allowed={R37_FIRST_R33_SAMPLE_NO_PRIOR=true,
   R37_R33_CAPTURE_HOLD_NO_DISPATCH=true,HOLD_CONTEXT_COMPARISON=true,
   NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE=true,
   EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE=true,
   OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE=true,
   ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE=true,
   RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF=true}
 local status=sample.r37AdviceStatus
 if allowed[status]~=true then return nil end
 return '{"schema":"BGXAI_R37_R33_R36_SINGLE_LISTENER_SOURCE_V1",'..
   '"type":"ADVISORY_CONTEXT","seq":'..jnum(sample.collectorOrdinal,1,64)..
   ',"partyIndex":'..jnum(sample.partyIndex,0,5)..
   ',"status":"'..status..'",'..
   '"invalidateCachedAdvice":'..tostring(sample.r37InvalidateCachedAdvice==true)..
   ',"selectedAprRawOnly":true,"actionOrigin":"UNKNOWN",'..
   '"fullActiveEffectsVerified":false,"sameBuffContextVerified":false,'..
   '"launcherAmmoBindingVerified":false,"safeActionBoundaryVerified":false,'..
   '"alternateEffectiveAPRVerified":false,'..
   '"readOnly":true,"ordersSent":0,"localsWritten":0,'..
   '"dispatchAuthorized":false,"weaponSwitchAuthorized":false}'
end
-- Uses original R37 EEex raw readers rather than caller-authored trust bits.
function R27.captureInventoryV3(sprite,action,sample)
 local function contextReader(s)
  local b=before_after(s,action)
  local q=Q81_CORE.observe(s,action)
  if type(q)~='table' or q.queue_count_observed~=true or
     q.action_context_snapshot_stable~=true or
     q.current_action_id~=b.action then return nil end
  return {actorId=b.actor,actionRaw=b.action,
   selectedWeaponRaw=b.weapon,selectedAbilityRaw=b.ability,
   queuedActionsRaw=q.queue_count_raw,
   currentScriptNumberRaw=q.current_script_number_raw}
 end
 return INV3.capture(sprite,sample,contextReader)
end
function R27.toInventoryV3Json(sample)
 if type(sample)~='table' or sample.readOnly~=true or
   sample.ordersSent~=0 or sample.weaponSwitchAuthorized~=false then return nil end
 local s=sample.inventoryV3Status
 local allow={BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY=true,
 HOLD_R37_CONTRACT=true,HOLD_CONTEXT_BEFORE=true,HOLD_FIRST_CAPTURE=true,
 HOLD_SECOND_CAPTURE=true,HOLD_CONTEXT_AFTER=true,HOLD_BACKPACK_CHANGED=true,
 HOLD_INVENTORY_V3_EXCEPTION=true,HOLD_MISSING_CONTEXT=true}
 if not allow[s] then return nil end
 return '{"schema":"BGXAI_BACKPACK16_R37_SINGLE_LISTENER_SOURCE_V1",'..
   '"type":"BACKPACK16_ADVISORY","seq":'..jnum(sample.collectorOrdinal,1,64)..
   ',"partyIndex":'..jnum(sample.partyIndex,0,5)..
   ',"status":"'..s..'",'..
   '"backpackFirstSlot":18,"backpackLastSlot":33,'..
   '"backpackPresentCount":'..jnum(sample.inventoryV3PresentCount,0,16)..','..
   '"backpackEmptyCount":'..jnum(sample.inventoryV3EmptyCount,0,16)..','..
   '"duplicateResrefObserved":'..
    (sample.inventoryV3DuplicateResref==true and 'true' or 'false')..','..
   '"readOnly":true,"ordersSent":0,"localsWritten":0,'..
   '"actionOrigin":"UNKNOWN","safeActionBoundaryVerified":false,'..
   '"dispatchAuthorized":false,"inventoryMoveAuthorized":false,'..
   '"weaponSwitchAuthorized":false}'
end
-- Makes a passive console sink but NEVER calls EEex to register it.
function R27.prepareConsolePilot(ports)
 if type(ports)~='table' or type(ports.portraitIndex)~='function' or
  type(ports.getActiveStats)~='function' or
  type(ports.emitString)~='function' then
  return nil,'CONSOLE_PORTS_MISSING' end
 local listener,err=R27.makeListener({
  portraitIndex=ports.portraitIndex,getActiveStats=ports.getActiveStats,
  emit=function(sample)
   local line=R27.toConsoleJson(sample)
   if line then ports.emitString('[BGXR27] '..line) end
   local advice=R27.toR37AdviceJson(sample)
   if advice then ports.emitString('[BGXR37] '..advice) end
   local inv=R27.toInventoryV3Json(sample)
   if inv then ports.emitString('[BGXINV3] '..inv) end
  end})
 if not listener then return nil,err end
 return {status='SOURCE_ONLY_LISTENER_READY_NOT_REGISTERED',
   registered=false,installAuthorized=false,dispatchAuthorized=false,
   listener=listener}
end

-- This candidate is deliberately NOT auto-registered. A separate typed
-- authorization, preflight, external backup and single-updater install design
-- are required before any game integration.
function R27.makeListener(deps)
 if type(deps)~='table' or type(deps.portraitIndex)~='function' or
    type(deps.getActiveStats)~='function' or type(deps.emit)~='function' then
  return nil,'DEPENDENCIES_UNPROVEN' end
 local priorByParty={} -- local observer cache bounded to 6 party slots
 return function(sprite,action)
  if R27.recorded>=R27.limit then return end
  local id=scalar(sprite,'m_id',1,2147483647)
  if not id then return end
  local ok,p=pcall(deps.portraitIndex,id)
  if not ok or not int(p,0,5) then return end
  local result=R27.observe(sprite,action,p,deps.getActiveStats)
  R27.recorded=R27.recorded+1
  result.collectorOrdinal=R27.recorded
  -- Additional observation only, no dispatch and no second callback.
  local invOK,invSample=pcall(R27.captureInventoryV3,sprite,action,result)
  result.inventoryV3Status=(invOK and type(invSample)=='table' and
    invSample.status) or 'HOLD_INVENTORY_V3_EXCEPTION'
  if invOK and type(invSample)=='table' and
    invSample.status=='BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY' and
    type(invSample.snapshot)=='table' then
    result.inventoryV3PresentCount=invSample.snapshot.presentCount
    result.inventoryV3EmptyCount=invSample.snapshot.emptyCount
    result.inventoryV3DuplicateResref=(invSample.duplicateBackpackResrefObserved==true)
  end
  result.r37AdviceStatus='R37_R33_CAPTURE_HOLD_NO_DISPATCH'
  result.r37InvalidateCachedAdvice=true
  -- Analyze only the already-captured R33 sample; no additional EEex calls.
  local capOk,cap=pcall(R36_CORE.capture,result)
  if capOk and type(cap)=='table' and
     cap.status=='RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY' then
   local prior=priorByParty[p+1]
   if prior==nil then
    result.r37AdviceStatus='R37_FIRST_R33_SAMPLE_NO_PRIOR'
   else
    local cmpOk,cmp=pcall(R36_CORE.compare,prior,cap)
    if cmpOk and type(cmp)=='table' and type(cmp.status)=='string' and
       cmp.dispatchAuthorized==false and cmp.weaponSwitchAuthorized==false and
       cmp.ordersSent==0 then
     result.r37AdviceStatus=cmp.status
     result.r37InvalidateCachedAdvice=(cmp.invalidateCachedAdvice~=false)
    end
   end
   priorByParty[p+1]=cap
  else
   priorByParty[p+1]=nil -- a HOLD invalidates pending advisory context
  end
  -- Existing R33 event line stays identical; extra bounded R37 status follows.
  local emitted=pcall(deps.emit,result)
  if not emitted then R27.errors=R27.errors+1 end
 end
end
return R27

end)()
-- BGXAI R31: passive bootstrap for EXACT R27 ACTION_CONTEXT_V3 source.
-- SOURCE ONLY. Not installed. It may be wrapped around R27 only after a
-- separately approved SHA/WeiDU upgrade; never load in the game directly.
-- Depends on the preceding local R27 produced by the verified builder.
-- Does not issue engine actions, set LOCALS, mutate scripts, or clear queues.
local P={name='M_BGXR27',version='BGXAI_R37_R33_R36_INV3_SINGLE_LISTENER_SOURCE_CANDIDATE',
  registered=false,readOnly=true,ordersSent=0,errors=0,writer='UNAVAILABLE',
  dispatchAuthorized=false,weaponSwitchAuthorized=false}
-- No duplicate listeners in the same session. A fresh game process is required
-- before any future replacement; do not try to unhook the old listener.
if type(BGXAI_R27_ObserverPilot)=='table' and
   BGXAI_R27_ObserverPilot.registered==true then return end
BGXAI_R27_ObserverPilot=P
local function safe(fn)
  local ok,v=pcall(fn)
  if ok then return v end
  return nil
end
local function emit(line)
  if type(Infinity_Log)=='function' and pcall(Infinity_Log,line) then
    P.writer='INFINITY_LOG';return
  end
  if type(print)=='function' and pcall(print,line) then
    P.writer='PRINT_FALLBACK';return
  end
  P.errors=P.errors+1
end
local function portraitIndex(actorId)
  for i=0,5 do
    if safe(function() return EEex_Sprite_GetInPortraitID(i) end)==actorId then
      return i
    end
  end
  return nil
end
local function start()
  if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
     type(EEex_Sprite_GetInPortraitID)~='function' or
     type(EEex_Sprite_GetActiveStats)~='function' then
    P.writer='REQUIRED_EEEX_API_MISSING';return false
  end
  if type(R27)~='table' or type(R27.prepareConsolePilot)~='function' then
    P.writer='R27_V3_CONTRACT_INCOMPLETE';return false
  end
  local ok,pilot=pcall(R27.prepareConsolePilot,{
    portraitIndex=portraitIndex,
    getActiveStats=EEex_Sprite_GetActiveStats,emitString=emit
  })
  if not ok or type(pilot)~='table' or type(pilot.listener)~='function' then
    P.writer='R27_V3_LISTENER_MISSING';return false
  end
  if not pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener) then
    P.writer='LISTENER_REGISTRATION_FAILED';return false
  end
  P.registered=true
  emit('[BGXR27] {"schema":"BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",'..
       '"type":"SESSION","observerCandidate":"R33_R27V3_PASSIVE_PROF_RO",'..
       '"queueBindingLiveVerified":false,"manualEpsOriginVerified":false,'..
       '"alternateEffectiveAPRVerified":false,"readOnly":true,'..
       '"ordersSent":0,"weaponSwitchAuthorized":false,'..
       '"dispatchAuthorized":false}')
  emit('[BGXR37] {"schema":"BGXAI_R37_R33_R36_SINGLE_LISTENER_SOURCE_V1",'..
       '"type":"SESSION","sourceOnly":true,"readOnly":true,'..
       '"actionOrigin":"UNKNOWN","safeActionBoundaryVerified":false,'..
       '"noExtraListener":true,"ordersSent":0,'..
       '"dispatchAuthorized":false,"weaponSwitchAuthorized":false}')
  emit('[BGXINV3] {"schema":"BGXAI_BACKPACK16_R37_SINGLE_LISTENER_SOURCE_V1",'..
       '"type":"SESSION","readOnly":true,"inventoryMoveAuthorized":false,'..
       '"safeActionBoundaryVerified":false,"ordersSent":0,'..
       '"dispatchAuthorized":false,"noExtraListener":true}')
  return true
end
P.initialized=start()
