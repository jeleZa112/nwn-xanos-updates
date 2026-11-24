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
