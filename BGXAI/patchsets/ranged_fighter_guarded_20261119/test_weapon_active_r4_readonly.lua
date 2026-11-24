-- Offline native Lua mocks for BGXAI R4. No EEex/game dependency.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local R=dofile(folder..'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua')
local n=0
local function test(name,fn) fn();n=n+1;print('PASS '..name) end
local function equal(a,b)assert(a==b,tostring(a)..' ~= '..tostring(b))end
local function mock()
 local stats={m_nNumberOfAttacks=2,m_nTHAC0=17,m_nLevel1=3,m_nLevel2=0,m_nLevel3=0,
  m_nKit=0,m_nSTR=15,m_nSTRExtra=0,m_nDEX=16,m_nDamageBonus=0,
  m_nMeleeTHAC0Bonus=0,m_nMeleeDamageBonus=0,m_nMissileTHAC0Bonus=0,
  m_nMissileDamageBonus=0,m_nHitBonus=0,m_bImprovedHaste=0,m_nLuck=0,
  m_nLevelDrain=0,m_THAC0BonusRight=0,m_THAC0BonusLeft=0,m_DamageBonusRight=0,
  m_DamageBonusLeft=0,m_nProficiencyLongSword=1,m_nProficiencyShortBow=2,
  m_nProficiencyQuarterStaff=0,m_nProficiencySwordAndShield=0,
  m_nProficiency2Handed=0,m_nProficiencySingleWeapon=0,m_nProficiency2Weapon=0}
 local s={m_id=139135050,m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0}}
 for _,name in ipairs(R.fields) do if stats[name]==nil then stats[name]=0 end end
 return s,{m_actionID=30},stats
end
local function snapshot() local s,a,stats=mock();return R.observe(s,a,2,function() return stats end) end
test('actor high-bit-friendly 31-bit raw index',function() local v=snapshot();equal(v.actorId,139135050);equal(v.partyIndex,2)end)
test('selected ammo ID stays selected index, not launcher proof',function()local v=snapshot();equal(v.selectedWeaponRaw,12);equal(v.selectedOnly,true);equal(v.alternateSlotAPRVerified,false)end)
test('selected APR2 decoded as 2, not added twice',function()local v=R.classifyObservedEvidence(snapshot());equal(v.selectedAPRIfStandard,2);equal(v.projectionToOtherSlotsAllowed,false)end)
test('encoded APR7 decoded as one point five',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=7;local v=R.classifyObservedEvidence(R.observe(s,a,2,function()return stats end));equal(v.selectedAPRIfStandard,1.5)end)
test('raw kit levels and 3 weapon proficiency fields available',function()local v=snapshot();equal(v.fields.m_nLevel1,3);equal(v.fields.m_nProficiencyLongSword,1);equal(v.fields.m_nProficiencyShortBow,2);equal(v.fields.m_nProficiencyQuarterStaff,0)end)
test('no completeness permission from raw stats',function()local v=snapshot();equal(v.allBuffsObserved,false);equal(v.manualOrderProven,false);equal(v.epsQueueProven,false);equal(v.dispatchAuthorized,false)end)
test('missing EEex API fails closed',function()local s,a=mock();local v=R.observe(s,a,2,false);equal(v.status,'HOLD_ACTIVE_STATS_API_MISSING')end)
test('stats pointer error fails closed',function()local s,a=mock();local v=R.observe(s,a,2,function()error('TEST')end);equal(v.status,'HOLD_ACTIVE_STATS_ACCESS_FAILED')end)
test('missing current APR fails closed, false not zero',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.status,'HOLD_APR_OR_SELECTED_SLOT_MISSING');equal(v.fields.m_nNumberOfAttacks,false)end)
test('zero APR is a real observed zero not absence',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=0;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nNumberOfAttacks,0);equal(R.classifyObservedEvidence(v).selectedAPRIfStandard,0)end)
test('known haste key invalidates advice without action',function()local a=snapshot();local b=snapshot();b.fields.m_bImprovedHaste=1;local c=R.compare(a,b);equal(c.changeCount,1);equal(c.status,'INVALIDATE_CACHED_WEAPON_ADVICE_KEEP_ACTION');equal(c.dispatchAuthorized,false)end)
test('strength buff invalidates cached proposal',function()local a=snapshot();local b=snapshot();b.fields.m_nSTR=19;equal(R.compare(a,b).changeCount,1)end)
test('proficiency change invalidates cached proposal',function()local a=snapshot();local b=snapshot();b.fields.m_nProficiencyShortBow=3;equal(R.compare(a,b).changeCount,1)end)
test('raw item selection changes invalidate proposal',function()local a=snapshot();local b=snapshot();b.selectedWeaponRaw=35;equal(R.compare(a,b).changedFields[1],'SELECTION_CHANGED')end)
test('unchanged samples do not certify all buffs',function()local c=R.compare(snapshot(),snapshot());equal(c.status,'RAW_SELECTED_STATS_UNCHANGED_NOT_PROOF_OF_ALL_EFFECTS');equal(c.allEffectsObserved,false)end)
test('wrong actor cannot be compared',function()local a=snapshot();local b=snapshot();b.actorId=321;equal(R.compare(a,b).status,'HOLD_UNCOMPARABLE_SNAPSHOTS')end)
test('out-of-range field dropped not clamped to false value 0',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=10000;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nNumberOfAttacks,10000);equal(R.classifyObservedEvidence(v).status,'HOLD_APR_ENCODING_UNKNOWN')end)
test('bad selected weapon holds rather than ranking',function()local s,a,stats=mock();s.m_equipment=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.status,'HOLD_APR_OR_SELECTED_SLOT_MISSING')end)
test('missing class level remains missing only',function()local s,a,stats=mock();stats.m_nLevel1=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nLevel1,false);equal(v.allBuffsObserved,false)end)
test('no game mutation on snapshots',function()local s,a,stats=mock();R.observe(s,a,2,function()return stats end);equal(s.m_equipment.m_selectedWeapon,12);equal(a.m_actionID,30);equal(stats.m_nNumberOfAttacks,2)end)
test('complete 89-134 raw proficiency coverage, no duplicate fields',function()
 equal(#R.fields,68)
 local unique={};for _,name in ipairs(R.fields) do assert(not unique[name]);unique[name]=true end
 for id=89,134 do assert(type(R.proficiencyFieldById[id])=='string');assert(unique[R.proficiencyFieldById[id]]) end
 equal(R.proficiencyFieldById[89],'m_nProficiencyBastardSword')
 equal(R.proficiencyFieldById[115],'m_nProficiencyClub')
 equal(R.proficiencyFieldById[116],'m_nExtraProficiency2')
 equal(R.proficiencyFieldById[134],'m_nExtraProficiency20')
end)
test('dart and sling and axe raw proficiency resolved by item ID',function()
 local v=snapshot()
 local ids={[92]='m_nProficiencyAxe',[106]='m_nProficiencyDart',[107]='m_nProficiencySling'}
 for k,field in pairs(ids) do
  local res=R.lookupProficiencyForItem(v,{proficiencyIdRaw=k})
  equal(res.status,'RAW_STANDARD_PROFICIENCY_ID_MATCH');equal(res.field,field)
  equal(res.dispatchAuthorized,false);equal(res.actorProficiencyRankVerified,false)
 end
end)
test('modded proficiency extra slot observed but no claimed name',function()
 local v=snapshot();v.fields.m_nExtraProficiency8=3
 local res=R.lookupProficiencyForItem(v,{proficiencyIdRaw=122})
 equal(res.rawValue,3);equal(res.status,'HOLD_MODDED_WPROF_NAME_UNVERIFIED')
 equal(res.installedWPROFMappingVerified,false)
end)
test('unknown WPROF ID cannot be silently treated as zero pips',function()
 local res=R.lookupProficiencyForItem(snapshot(),{proficiencyIdRaw=149})
 equal(res.status,'HOLD_PROFICIENCY_FOR_ITEM_UNVERIFIED')
 equal(res.reason,'ITEM_PROFICIENCY_OUTSIDE_AUDITED_IDS')
end)
test('unreadable proficiency is not zero',function()
 local v=snapshot();v.fields.m_nProficiencySling=false
 local res=R.lookupProficiencyForItem(v,{proficiencyIdRaw=107})
 equal(res.reason,'ACTOR_PROFICIENCY_FIELD_UNREADABLE')
end)
test('arrow ammunition ID 0 is not weapon proficiency',function()
 local res=R.lookupProficiencyForItem(snapshot(),{proficiencyIdRaw=0})
 equal(res.status,'HOLD_PROFICIENCY_FOR_ITEM_UNVERIFIED')
end)
test('axe raw change invalidates cached advice without current action abort',function()
 local a=snapshot();local b=snapshot();b.fields.m_nProficiencyAxe=2
 local c=R.compare(a,b)
 equal(c.status,'INVALIDATE_CACHED_WEAPON_ADVICE_KEEP_ACTION')
 equal(c.dispatchAuthorized,false);equal(c.currentActionPreserved,nil)
end)
test('all raw proficiencies still cannot prove other slot APR or dispatch',function()
 local v=snapshot()
 equal(v.presentCount,68);equal(v.missingCount,0)
 equal(v.alternateSlotAPRVerified,false);equal(v.dispatchAuthorized,false)
end)
test('Holy Power-like THAC0 STR 18/00 does not grant fighter APR or proficiencies',function()
 local a=snapshot();local b=snapshot();a.fields.m_nLevel1=9;b.fields.m_nLevel1=9
 a.fields.m_nTHAC0=16;b.fields.m_nTHAC0=12
 b.fields.m_nSTR=18;b.fields.m_nSTRExtra=100
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'CURRENT_SELECTED_COMBAT_SHIFT_RECALCULATE_KEEP_ACTION')
 equal(r.beforeAPRRaw,2);equal(r.afterAPRRaw,2)
 equal(r.fighterAPRNotInferred,true);equal(r.fighterProficienciesGranted,false)
 equal(r.spellIdentityVerified,false);equal(r.currentActionPreserved,true)
 equal(r.dispatchAuthorized,false);equal(r.ordersSent,0)
end)
test('Holy Power-like effect expiration refreshes advice without an action',function()
 local a=snapshot();local b=snapshot()
 a.fields.m_nTHAC0=12;b.fields.m_nTHAC0=16
 a.fields.m_nSTR=18;a.fields.m_nSTRExtra=100
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'CURRENT_SELECTED_COMBAT_SHIFT_RECALCULATE_KEEP_ACTION')
 equal(r.currentActionPreserved,true);equal(r.dispatchAuthorized,false)
end)
test('druid form or haste APR change is not fighter class promotion',function()
 local a=snapshot();local b=snapshot();b.fields.m_nNumberOfAttacks=7
 b.fields.m_bImprovedHaste=1
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.afterAPRRaw,7)
 equal(r.fighterAPRNotInferred,true);equal(r.status,'CURRENT_SELECTED_COMBAT_SHIFT_RECALCULATE_KEEP_ACTION')
end)
test('druid transformation selection change requires fresh equipment audit',function()
 local a=snapshot();local b=snapshot();b.selectedWeaponRaw=35;b.fields.m_nTHAC0=2
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'HOLD_SELECTION_CHANGED_REAUDIT_ALL_WEAPONS')
 equal(r.dispatchAuthorized,false)
end)
test('unknown buff field does not pretend that unchanged means buff-free',function()
 local a=snapshot();local b=snapshot()
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'NO_OBSERVED_SHIFT_BUFFS_STILL_NOT_EXHAUSTIVE')
 equal(r.allBuffsObserved,false)
end)
test('new unreadable active THAC0 forces hold not fighter approximation',function()
 local a=snapshot();local b=snapshot();b.fields.m_nTHAC0=false
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'HOLD_CURRENT_COMBAT_STAT_UNREADABLE')
 equal(r.fighterAPRNotInferred,true)
end)
test('weapon proficiency changes are never mistaken for spell buffs',function()
 local a=snapshot();local b=snapshot();b.fields.m_nProficiencyLongSword=3
 local r=R.auditTemporaryCombatShift(a,b)
 equal(r.status,'HOLD_PROFICIENCY_CHANGED_REAUDIT_WEAPON')
end)
-- EEex v1.1.7: EEex_Sprite_GetActiveStats returns m_tempStats when
-- sprite.m_bAllowEffectListCall == 0 (temporary effects processing).
test('R4 strict observer refuses unknown stat origin',function()
 local s,a,stats=mock()
 local got=R.observeStableDerived(s,a,2,function()return stats end)
 equal(got.status,'HOLD_DERIVED_STATS_VIEW_UNVERIFIED')
end)
test('R4 strict observer never calls native stats when temp view flagged',function()
 local s,a=mock();s.m_bAllowEffectListCall=0;local calls=0
 local v=R.observeStableDerived(s,a,2,function()calls=calls+1;return {} end)
 equal(v.status,'HOLD_DERIVED_STATS_VIEW_UNVERIFIED');equal(calls,0)
end)
test('R4 strict observer refuses unexpected non-one flag',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=2
 local v=R.observeStableDerived(s,a,2,function()return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_VIEW_UNVERIFIED')
end)
test('R4 strict derived path reads all 68 stats twice, still selected-only',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local calls=0
 local v=R.observeStableDerived(s,a,2,function()calls=calls+1;return stats end)
 equal(calls,2)
 equal(v.status,'RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS')
 equal(v.derivedStatsDoubleReadConsistent,true)
 equal(v.runtimeEngineAuthenticated,false)
 equal(v.allBuffsObserved,false);equal(v.allEffectsObserved,false)
 equal(v.alternateSlotAPRVerified,false);equal(v.dispatchAuthorized,false)
 equal(v.presentCount,68)
end)
test('R4 rejects flag flip during first stats read',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1
 local v=R.observeStableDerived(s,a,2,function()s.m_bAllowEffectListCall=0;return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_TEMP_VIEW_DURING_READ')
end)
test('R4 rejects flag flip during second stats read',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then s.m_bAllowEffectListCall=0 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_TEMP_VIEW_DURING_RECHECK')
end)
test('R4 rejects APR recalculation between two reads',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then stats.m_nNumberOfAttacks=7 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_CHANGED_DURING_READ')
end)
test('R4 rejects STR buff recalculation between two reads',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then stats.m_nSTR=19 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_CHANGED_DURING_READ')
end)
test('R4 rejects proficiency changes between two reads',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then stats.m_nProficiencyLongSword=3 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_CHANGED_DURING_READ')
end)
test('R4 rejects action changes while reading',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then a.m_actionID=23 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_SELECTION_OR_ACTION_CHANGED')
end)
test('R4 rejects selection changes while reading',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;local reads=0
 local v=R.observeStableDerived(s,a,2,function()
  reads=reads+1;if reads==2 then s.m_equipment.m_selectedWeapon=35 end
  return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_SELECTION_OR_ACTION_CHANGED')
end)
test('R4 rejects unreadable non-APR effect-sensitive stat',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1;stats.m_nSTR=nil
 local v=R.observeStableDerived(s,a,2,function()return stats end)
 equal(v.status,'HOLD_DERIVED_STATS_FIELDS_INCOMPLETE')
end)
test('R4 strict stat errors fail closed',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1
 local v=R.observeStableDerived(s,a,2,function() error('reader failed') end)
 equal(v.status,'HOLD_DERIVED_STATS_FIELDS_INCOMPLETE')
end)
test('R4 stable selected APR never authorizes weapon choice',function()
 local s,a,stats=mock();s.m_bAllowEffectListCall=1
 local v=R.observeStableDerived(s,a,2,function()return stats end)
 equal(R.classifyObservedEvidence(v).status,'HOLD_NO_CURRENT_SELECTED_EVIDENCE')
 equal(v.alternateSlotAPRVerified,false)
 equal(v.dispatchAuthorized,false)
end)
print('BGXAI_R4_CORE_OFFLINE_PASS '..n..'/'..n)
