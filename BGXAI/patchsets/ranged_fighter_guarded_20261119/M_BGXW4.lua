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

-- BGXW4 runtime wrapper, SOURCE ONLY until an audited, separately approved install.
-- The pure R4 core is embedded above this wrapper as local M.
local CORE=M
if type(BGXWeaponActiveR4)=='table' and BGXWeaponActiveR4.registered then return end
local R={version='BGXW4_ACTIVE_STATS_R4',registered=false,limit=64,recorded=0,
         skipped=0,errors=0,writer='UNINITIALIZED',ordersSent=0}
BGXWeaponActiveR4=R
local function safe(fn)
 local ok,x=pcall(fn)
 if ok then return x end
 return nil
end
local function number(x,lo,hi)
 if type(x)=='number' and x==math.floor(x) and x>=lo and x<=hi then return tostring(x) end
 return 'null'
end
local function party(id)
 if type(id)~='number' or id~=math.floor(id) or id<0 or id>2147483647 then return nil end
 for p=0,5 do
  if safe(function() return EEex_Sprite_GetInPortraitID(p) end)==id then return p end
 end
 return nil
end
local function fields(obj)
 local res={}
 for _,name in ipairs(CORE.fields) do
  local value=type(obj)=='table' and obj[name] or nil
  res[#res+1]='"'..name..'":'..number(value,-2147483648,2147483647)
 end
 return '{'..table.concat(res,',')..'}'
end
local function line(snapshot)
 local allowed={RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS=true,
  HOLD_APR_OR_SELECTED_SLOT_MISSING=true,HOLD_ACTIVE_STATS_ACCESS_FAILED=true,
  HOLD_ACTIVE_STATS_API_MISSING=true,HOLD_ACTOR_ID_UNAVAILABLE=true,
  HOLD_INCOMPLETE_ACTIVE_STATS=true}
 local status=allowed[snapshot.status] and snapshot.status or 'HOLD_UNKNOWN'
 return '{"schema":"BGXAI_WEAPON_ACTIVE_R4","type":"ACTIVE","seq":'..number(R.recorded,1,64)..
  ',"actor":'..number(snapshot.actorId,0,2147483647)..
  ',"partyIndex":'..number(snapshot.partyIndex,0,5)..
  ',"actionRaw":'..number(snapshot.actionRaw,0,65535)..
  ',"selectedWeaponRaw":'..number(snapshot.selectedWeaponRaw,0,65535)..
  ',"selectedAbilityRaw":'..number(snapshot.selectedAbilityRaw,0,65535)..
  ',"presentCount":'..number(snapshot.presentCount,0,100)..
  ',"missingCount":'..number(snapshot.missingCount,0,100)..
  ',"status":"'..status..'","statsRaw":'..fields(snapshot.fields)..
  ',"allBuffsObserved":false,"allEffectsObserved":false,'..
  '"alternateSlotAPRVerified":false,"manualOrderProven":false,'..
  '"epsQueueProven":false,"weaponSwitchAuthorized":false,'..
  '"dispatchAuthorized":false}'
end
local function console(s)
 local wrote=false
 if type(Infinity_Log)=='function' then
  wrote=safe(function() Infinity_Log('[BGXW4] '..s);return true end) or wrote
 end
 if wrote then return true end
 if type(print)=='function' then
  wrote=safe(function() print('[BGXW4] '..s);return true end) or wrote
 end
 return wrote
end
local function write(s)
 if R.handle then
  local ok=pcall(function()
   R.handle:write(s,'\n')
   if R.recorded%8==0 then R.handle:flush() end
  end)
  if ok then return true end
  R.errors=R.errors+1
  safe(function() R.handle:close() end)
  R.handle=nil
 end
 if console(s) then R.writer='CONSOLE_FALLBACK';return true end
 R.writer='NO_OUTPUT_SINK'
 return false
end
function R.on_started(sprite,action)
 local ok=pcall(function()
  if R.recorded>=R.limit then R.skipped=R.skipped+1;return end
  local id=safe(function() return sprite.m_id end)
  local p=party(id)
  if p==nil then return end
  R.recorded=R.recorded+1
  local snap=CORE.observe(sprite,action,p)
  write(line(snap))
 end)
 if not ok then R.errors=R.errors+1 end
end
local function init()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
    type(EEex_Sprite_GetInPortraitID)~='function' or
    type(EEex_Sprite_GetActiveStats)~='function' then
  R.writer='EEEX_REQUIRED_FUNCTION_MISSING';return false
 end
 if type(io)=='table' and type(io.open)=='function' and
     type(os)=='table' and type(os.getenv)=='function' then
  local home=safe(function() return os.getenv('USERPROFILE') end)
  if type(home)=='string' and #home>=4 and #home<=260 then
   R.handle=safe(function()
    return io.open(home..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_WEAPON_ACTIVE_RAW_R4.jsonl','a')
   end)
  end
 end
 if R.handle then R.writer='FILE'
 elseif type(Infinity_Log)=='function' or type(print)=='function' then
  R.writer='CONSOLE_FALLBACK'
 else R.writer='NO_OUTPUT_SINK';return false end
 local stamp=safe(function() return os.date('!%Y-%m-%dT%H:%M:%SZ') end) or 'UNKNOWN'
 if not write('{"schema":"BGXAI_WEAPON_ACTIVE_R4","type":"SESSION","utc":"'..stamp..'","readOnly":true}') then return false end
 local registered=safe(function()
  EEex_Action_AddSpriteStartedActionListener(R.on_started)
  return true
 end)
 if not registered then R.writer='HOOK_FAILED';return false end
 R.registered=true
 write('{"schema":"BGXAI_WEAPON_ACTIVE_R4","type":"READY","hookRegistered":true}')
 return true
end
R.initialized=init()
