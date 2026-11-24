-- Native Lua offline: APR proficiency table + final engine APR handoff.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local v5=dofile(folder..'BGXAI_WEAPON_APR_PROVENANCE_V5.lua')
local v4=dofile(folder..'../BGXAI_WEAPON_PRIORITY_V4/BGXAI_WEAPON_EFFECTS_V4.lua')
local v3=dofile(folder..'../BGXAI_WEAPON_PRIORITY_V3/BGXAI_WEAPON_PRIORITY_LUA_V3.lua')
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
local function clone(x) if type(x)~='table' then return x end local c={} for k,v in pairs(x) do c[k]=clone(v) end return c end
local H=string.rep('a',64); local I=string.rep('b',64)
local function weapon(id,index,group,rank,apr,raw,baseDmg)
 local sling=group=='SLING';local str=sling and 6 or 0
 local comps=sling and {{id='B',category='WEAPON',avgDamage=baseDmg,snapshotId='S1',observedInInstalledEET=true},{id='S',category='STRENGTH',avgDamage=str,snapshotId='S1',observedInInstalledEET=true}} or {{id='B',category='WEAPON',avgDamage=baseDmg,snapshotId='S1',observedInInstalledEET=true}}
 local w={id=id,quickslotIndex=index,slot='QUICKSLOT',mode='RANGED',usableVerified=true,equippedWeaponSlotVerified=true,inRange=true,finalTHAC0=10,apr=apr,avgDamageOnHit=baseDmg+str,damageType='MISSILE',enchantment=1,magical=true,switchCost=0,resourceCost=0,retaliationRisk=0,movementCost=0,extraEffectValue=0,combatCostsVerified=true,statBasis='FINAL_EFFECTIVE',allRaceClassKitProficiencyBonusesIncluded=true,finalCombatStatsVerified=true,modFingerprint='EET',snapshotId='S1',weaponGroup=group,dexterityHitBonusIncluded=true,strengthHitBonusExcluded=true,strengthRuleFromInstalledEET=true,strengthDamageApplies=sling,damageTypeSpecialRulesVerified=true,ammunitionModel=sling and 'QUIVER' or 'SELF',ammoVerified=true,ammoCount=30,ammoResRef=sling and 'BULLET1' or nil,launcherResRef=sling and 'SLING1' or nil,launcherAmmoPairVerified=sling and true or nil,resRef=sling and 'SLING1' or 'DART1',specialEffectsComplete=true,specialEffectsSnapshotId='S1',effectSourcesComplete={WEAPON=true,AMMO=true,LAUNCHER=true,ACTIVE_BUFF=true},onHitEffects={},damageBreakdown={snapshotId='S1',complete=true,verifiedInInstalledEET=true,launcherAmmoAndBuffsIncluded=true,conditionalOnHitEffectsExcluded=true,components=comps}}
 w.aprAudit={proficiencyRank=rank,classLevel=8,tableRank=rank,tableLevel=8,proficiencyWeaponGroup=group,weaponGroupMatchedInstalledIds=true,proficiencyRankObservedFromActiveClasses=true,activeClassAprEligibilityVerified=true,classEligibleForProfApr=true,snapshotId='S1',modFingerprint='EET',wspatckSha256=H,clswpbonSha256=I,classOrKitRow='FIGHTER',tableRowAndLevelMatchedInstalledEET=true,rateRule='WSPATCK_APPLIES',wspatckRawValue=raw,decodedTableApr=v5.decode_wspatck(raw),tableAprContributionToEngine=v5.decode_wspatck(raw),finalAprBasis='ENGINE_FINAL_EFFECTIVE',engineFinalAprIncludesTableOnce=true,engineFinalAprIncludesEquipmentAndBuffsOnce=true,activeHasteStateVerified=true,finalAprObserved=apr}
 return w
end
local function scene()
 local sling=weapon('SLING',0,'SLING',2,2,-1,3.5) -- adjust table from 7th level below
 sling.aprAudit.wspatckRawValue=1;sling.aprAudit.decodedTableApr=1;sling.aprAudit.tableAprContributionToEngine=1
 local dart=weapon('DART',1,'DART',1,3,-1,2)
 dart.aprAudit.wspatckRawValue=-1;dart.aprAudit.decodedTableApr=0.5;dart.aprAudit.tableAprContributionToEngine=0.5
 return {frame={tick=100,area='AR1',actorId='ACTOR',enemyId='FOE',snapshotId='S1',equipmentFingerprint='EQ1',protectionFingerprint='PROT1',combatFingerprint='CMB1',effectStatusFingerprint='EF1',completeOnHitEffectsObserved=true,completePhysicalDamageObserved=true,effectStatusSourceVerified=true,selectedWeaponId='DART',captureContract='COMPLETE_EFFECTIVE_SNAPSHOT',completeEquipmentObserved=true,completeQuiverObserved=true,completeTargetObserved=true},actor={actorId='ACTOR',area='AR1',currentTargetId='FOE',handsMode='SINGLE',observationVerified=true,manualOrderActive=false,currentlyCasting=false,healingReserved=false,epsBusy=false,originVerified='AI',selectedWeaponId='DART',strengthDamageBonus=6,strengthDamageBonusVerified=true,pathSafeVerified=true,canSustainMelee=true,nearRangedEnemy=false,aprClassRow='FIGHTER',traitProfile={verified=true,activeClassesVerified=true,raceClassKitBonusesIncluded=true,modFingerprint='EET',snapshotId='S1'}},enemy={enemyId='FOE',area='AR1',observationVerified=true,hostileVerified=true,visibleVerified=true,armorClass=0,effectStatusVerified=true,effectStatusFingerprint='EF1',protections={snapshotId='S1',observed=true,immuneDamageTypes={},minimumEnchantment=0,magicalWeaponsBlocked=false,normalWeaponsBlocked=false,missilesBlocked=false,resistance={MISSILE=0}}},quickslotIds={'SLING','DART',false,false},weapons={sling,dart},aprSource={snapshotId='S1',modFingerprint='EET',source='INSTALLED_EET_RESOURCE_SNAPSHOT',wspatckSha256=H,clswpbonSha256=I,tableContentsComplete=true,classEligibilityComplete=true,classOrKitRow='FIGHTER',activeDualMultiClassVerified=true}}
end
local function choose(s,previous)return v5.choose(s,previous,v4.choose,v3.choose)end
local function two(s)local a=choose(s);local s2=clone(s);s2.frame.tick=s2.frame.tick+1;return a,choose(s2,a.next)end
local count=0;local function test(label,fn)fn();count=count+1;print('PASS '..label)end
-- Core IESDP encoding asserts: raw -1 means +0.5, raw -2 means +1.5.
test('WSPATCK negative half APR representation',function() eq(v5.decode_wspatck(-1),0.5);eq(v5.decode_wspatck(-2),1.5);eq(v5.decode_wspatck(1),1);eq(v5.decode_wspatck(2),2);eq(v5.decode_wspatck(0),0)end)
test('normal complete sling+dart profile passes through V4/V3',function() local a,b=two(scene());eq(a.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT');eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SLING');eq(b.aprProvenance,'WSPATCK_CLSWPBON_FINAL_EFFECTIVE_NO_DOUBLE_COUNT')end)
test('specialist 2 pips at level 1 uses +0.5 from table',function() local s=scene();local p=s.weapons[1].aprAudit;p.classLevel=1;p.tableLevel=1;p.wspatckRawValue=-1;p.decodedTableApr=.5;p.tableAprContributionToEngine=.5;eq(v5.audit(s),nil)end)
test('grandmastery 5 pips level 1 uses +1 from table',function() local s=scene();local p=s.weapons[1].aprAudit;p.proficiencyRank=5;p.tableRank=5;p.classLevel=1;p.tableLevel=1;p.wspatckRawValue=1;p.decodedTableApr=1;p.tableAprContributionToEngine=1;eq(v5.audit(s),nil)end)
test('wspatck encodes fighter level and proficiency together',function() local s=scene();local p=s.weapons[1].aprAudit;p.proficiencyRank=2;p.tableRank=2;p.classLevel=13;p.tableLevel=13;p.wspatckRawValue=-2;p.decodedTableApr=1.5;p.tableAprContributionToEngine=1.5;eq(v5.audit(s),nil)end)
test('cannot add WSPATCK twice over a final APR',function()local s=scene();s.weapons[1].aprAudit.finalAprObserved=3;eq(choose(s).reason,'FINAL_APR_NOT_OBSERVED_OR_DOUBLE_COUNTED')end)
test('cannot claim another table APR than decoded installed row',function()local s=scene();s.weapons[1].aprAudit.tableAprContributionToEngine=1.5;eq(choose(s).reason,'WSPATCK_ALREADY_INCLUDED_OR_OVERRIDDEN')end)
test('level from inactive dual class cannot masquerade as active',function()local s=scene();s.aprSource.activeDualMultiClassVerified=false;eq(choose(s).reason,'INSTALLED_APR_TABLES_OR_CLASS_UNKNOWN')end)
test('kit/clswpbon missing blocks',function()local s=scene();s.aprSource.clswpbonSha256=nil;eq(choose(s).reason,'INSTALLED_APR_TABLES_OR_CLASS_UNKNOWN')end)
test('stale WSPATCK table fingerprint blocks',function()local s=scene();s.weapons[1].aprAudit.wspatckSha256=I;eq(choose(s).reason,'PROFICIENCY_RANK_CLASS_OR_TABLE_STALE')end)
test('changed ability proficiency group blocks',function()local s=scene();s.weapons[1].aprAudit.proficiencyWeaponGroup='DAGGER';eq(choose(s).reason,'PROFICIENCY_RANK_CLASS_OR_TABLE_STALE')end)
test('rate-of-fire exception cannot also credit proficiency APR',function()local s=scene();local t=s.weapons[2].aprAudit;t.rateRule='FIXED_RATE_OVERRIDES';eq(choose(s).reason,'WSPATCK_ALREADY_INCLUDED_OR_OVERRIDDEN')end)
test('verified fixed-rate overrides table contribution',function()local s=scene();local t=s.weapons[2].aprAudit;t.rateRule='FIXED_RATE_OVERRIDES';t.tableAprContributionToEngine=0;eq(v5.audit(s),nil)end)
test('class without proficiency APR cannot claim WSPATCK bonus',function()local s=scene();local t=s.weapons[1].aprAudit;t.classEligibleForProfApr=false;eq(choose(s).reason,'WSPATCK_ALREADY_INCLUDED_OR_OVERRIDDEN');t.tableAprContributionToEngine=0;eq(v5.audit(s),nil)end)
test('haste not accounted means hold, no APR guess',function()local s=scene();s.weapons[2].aprAudit.activeHasteStateVerified=false;eq(choose(s).reason,'FINAL_APR_NOT_OBSERVED_OR_DOUBLE_COUNTED')end)
test('two-hand offhand aggregation unverified means hold',function()local s=scene();s.actor.handsMode='DUAL';s.weapons[1].mode='MELEE';eq(choose(s).reason,'OFFHAND_APR_AGGREGATION_UNKNOWN')end)
test('preserve explicit no dispatch even on recommendation',function()local _,b=two(scene());eq(b.executable,false);eq(b.dispatchAuthorized,false)end)
test('complete V5/V4/V3 chain: selected verified empty darts switches to sling',function()
 local s=scene();s.weapons[2].ammoCount=0
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'SLING')
 eq(b.currentUnusableReason,'VERIFIED_EMPTY_AMMUNITION')
 eq(b.dispatchAuthorized,false)
end)
test('known empty current ammo does not need invented V5 APR or V4 damage',function()
 local s=scene();s.weapons[2].ammoCount=0
 s.weapons[2].apr=nil;s.weapons[2].aprAudit=nil
 s.weapons[2].avgDamageOnHit=nil;s.weapons[2].finalTHAC0=nil
 s.weapons[2].finalCombatStatsVerified=false;s.weapons[2].combatCostsVerified=false
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SLING')
 eq(b.currentUnusableReason,'VERIFIED_EMPTY_AMMUNITION')
 eq(b.dispatchAuthorized,false)
end)
test('ineligible exemption never covers unknown empty ammo',function()
 local s=scene();s.weapons[2].ammoCount=0;s.weapons[2].ammoVerified=false
 s.weapons[2].aprAudit=nil
 eq(choose(s).status,'HOLD_APR_PROVENANCE_UNVERIFIED')
 eq(choose(s).reason,'WEAPON_APR_AUDIT_MISSING')
end)
test('ineligible exemption never covers missing effective APR of candidate sling',function()
 local s=scene();s.weapons[2].ammoCount=0;s.weapons[2].aprAudit=nil
 s.weapons[1].aprAudit=nil
 eq(choose(s).reason,'WEAPON_APR_AUDIT_MISSING')
end)

test('V5 verified out-of-range selected dart skips unobservable APR',function()
 local s=scene();local dead=s.weapons[2]
 dead.inRange=false;dead.apr=nil;dead.aprAudit=nil
 dead.avgDamageOnHit=nil;dead.finalTHAC0=nil
 dead.finalCombatStatsVerified=false;dead.combatCostsVerified=false
 local _,b=two(s);eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.currentUnusableReason,'VERIFIED_RANGED_OUT_OF_RANGE')
 eq(b.toWeaponId,'SLING');eq(b.dispatchAuthorized,false)
end)
test('V5 verified out-of-range sling avoids fake alternate APR',function()
 local s=scene();s.weapons[1].inRange=false
 s.weapons[1].aprAudit=nil;s.weapons[1].apr=nil
 s.weapons[1].finalCombatStatsVerified=false;s.weapons[1].combatCostsVerified=false
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
 eq(b.candidates[1].reason,'VERIFIED_RANGED_OUT_OF_RANGE')
end)
test('V5 range unknown with absent APR remains strict hold',function()
 local s=scene();s.weapons[2].inRange=nil;s.weapons[2].aprAudit=nil
 eq(choose(s).reason,'WEAPON_APR_AUDIT_MISSING')
end)
test('V5 cannot exempt out-of-range missile when ammo is unverified',function()
 local s=scene();local w=s.weapons[2]
 w.inRange=false;w.ammoVerified=false;w.aprAudit=nil
 eq(choose(s).reason,'WEAPON_APR_AUDIT_MISSING')
end)
print('PASS APR V5 '..count..'/'..count..' OFFLINE SOURCE ONLY')