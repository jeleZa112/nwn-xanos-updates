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
-- BGXAI R27 read-only single-callback candidate.
-- This file is *source only*. It does not register a hook by itself.
-- It composes unchanged R2 and R4 observation cores directly in one call.
-- No item:getAbility, getLauncher, Demand, BCS/LOCALS, inventory or actions.
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
 return {actor=actor,action=aid,weapon=weapon,ability=ability}
end
local function same(a,b)
 return a.actor~=nil and a.action~=nil and a.weapon~=nil and
   a.ability~=nil and a.actor==b.actor and a.action==b.action and
   a.weapon==b.weapon and a.ability==b.ability
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
 -- Observe but never turn a selected-only APR into alternative-slot evidence.
 -- The R2 slot data are still only raw candidates, not validated items.
 return {schema=R27.schema,status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  actor=b.actor,partyIndex=partyIndex,actionRaw=b.action,
  selectedWeaponRaw=b.weapon,selectedAbilityRaw=b.ability,
  selectedAprKeyRaw=rawApr,r2Status=r2.status,r4Status=r4.status,
  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,offhandRaw=r2.offhand,
  rawInventoryDoubleReadConsistent=true,
  sampledStatsRaw={m_nNumberOfAttacks=rawApr,
   m_nTHAC0=f.m_nTHAC0,m_nSTR=f.m_nSTR,
   m_nSTRExtra=f.m_nSTRExtra,m_bImprovedHaste=f.m_bImprovedHaste,
   m_nHitBonus=f.m_nHitBonus},
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
-- No resource pointer, arbitrary object or user-supplied string is serialized.
local function jnum(v,lo,hi)
 if int(v,lo,hi) then return tostring(v) end
 return 'null'
end
local function jstr(v)
 if type(v)~='string' or #v<1 or #v>8 or v:find('[^%w_]') then
  return 'null' end
 return '"'..v:upper()..'"'
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
  ',"selectedStatsRaw":'..jstats(sample.sampledStatsRaw)..
  ',"sameLuaListenerInvocation":'..tostring(sample.sameLuaListenerInvocation==true)..
  ',"nativeEventTokenAuthenticated":false,"engineSessionVerified":false,'..
  '"alternativeAPRVerified":false,"launcherAmmoPairVerified":false,'..
  '"completeActiveEffectsVerified":false,"epsManualQueueVerified":false,'..
  '"ordersSent":0,"localsWritten":0,"dispatchAuthorized":false,'..
  '"weaponSwitchAuthorized":false,"readOnly":true}'
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
 return function(sprite,action)
  if R27.recorded>=R27.limit then return end
  local id=scalar(sprite,'m_id',1,2147483647)
  if not id then return end
  local ok,p=pcall(deps.portraitIndex,id)
  if not ok or not int(p,0,5) then return end
  local result=R27.observe(sprite,action,p,deps.getActiveStats)
  R27.recorded=R27.recorded+1
  result.collectorOrdinal=R27.recorded
  -- Results intentionally remain read-only regardless of observer failure.
  local emitted=pcall(deps.emit,result)
  if not emitted then R27.errors=R27.errors+1 end
 end
end
return R27
