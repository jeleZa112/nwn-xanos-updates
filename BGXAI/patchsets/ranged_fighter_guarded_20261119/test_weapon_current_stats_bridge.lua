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
local bridge=dofile(folder..'BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua')
local function choose(s,previous)return v5.choose(s,previous,v4.choose,v3.choose)end
local function two(s)local a=choose(s);local s2=clone(s);s2.frame.tick=s2.frame.tick+1;return a,choose(s2,a.next)end
local count=0
local function test(label,f) f();count=count+1;print('PASS '..label) end
local function active_scene()
 local s=scene()
 s.aprSource=nil -- No WSPATCK table needed on this preferred route
 local d={source='EEEX117_ACTIVE_DERIVED_STATS',snapshotId='S1',actorId='ACTOR',tick=100,
   activeFingerprint='ASTATS1',buffFingerprint='BUFFS1',equipmentFingerprint='EQ1',
   selectedWeaponId='DART',activeStatsAccessProven=true,
   allActiveEffectsObserved=true,hasteAndImprovedHasteAccounted=true,
   proficiencyClassKitIncludedOnce=true}
 s.actor.activeStatsEvidence=d
 for _,w in ipairs(s.weapons) do
  local selected=w.id=='DART'
  w.effectiveStatsEvidence={snapshotId='S1',actorId='ACTOR',weaponId=w.id,
   quickslotIndex=w.quickslotIndex,activeFingerprint='ASTATS1',buffFingerprint='BUFFS1',
   equipmentFingerprint='EQ1',weaponAbilityAmmoMatched=true,
   proficiencyAlreadyApplied=true,buffsAlreadyApplied=true,
   completeEffectiveWeaponStats=true,apr=w.apr,thac0=w.finalTHAC0,
   damageOnHit=w.avgDamageOnHit,basis=selected and 'ACTUALLY_SELECTED_WEAPON' or
    'PROJECTED_FROM_SAME_ACTIVE_STATS',selectedStatsObserved=selected,
   otherWeaponRecalculated=not selected}
 end
 return s
end
local function choose(s,prev) return bridge.choose(s,prev,v4.choose,v3.choose) end
local function two(s)
 local first=choose(s)
 local next=clone(s);next.frame.tick=101;next.actor.activeStatsEvidence.tick=101
 return first,choose(next,first.next)
end
test('active derived stats replace table-first APR and rank sling/dart',function()
 local a,b=two(active_scene());eq(a.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SLING')
 eq(b.aprProvenance,'EEEX_ACTIVE_STATS_AND_PER_SLOT_CONTEXT')
end)
test('no complete active effect observation -> HOLD',function()
 local s=active_scene();s.actor.activeStatsEvidence.allActiveEffectsObserved=false
 eq(choose(s).reason,'ACTIVE_DERIVED_STATS_OR_BUFFS_INCOMPLETE')
end)
test('no haste evidence -> HOLD',function()
 local s=active_scene();s.actor.activeStatsEvidence.hasteAndImprovedHasteAccounted=false
 eq(choose(s).reason,'ACTIVE_DERIVED_STATS_OR_BUFFS_INCOMPLETE')
end)
test('cannot reuse selected APR for a different quickslot',function()
 local s=active_scene();s.weapons[1].effectiveStatsEvidence.otherWeaponRecalculated=false
 eq(choose(s).reason,'OTHER_SLOT_RECALCULATION_UNVERIFIED')
end)
test('alternate slot APR different from effective observation -> HOLD',function()
 local s=active_scene();s.weapons[1].apr=5
 eq(choose(s).reason,'PER_SLOT_BUFF_AWARE_STATS_UNVERIFIED')
end)
test('selected slot requires actual engine observation',function()
 local s=active_scene();s.weapons[2].effectiveStatsEvidence.selectedStatsObserved=false
 eq(choose(s).reason,'SELECTED_WEAPON_STATS_UNVERIFIED')
end)
test('expired buff invalidates previous two-frame choice',function()
 local s=active_scene();local _,result=two(s)
 local n=clone(s);n.frame.tick=102;n.actor.activeStatsEvidence.tick=102
 n.actor.activeStatsEvidence.buffFingerprint='EXPIRED2'
 for _,w in ipairs(n.weapons) do w.effectiveStatsEvidence.buffFingerprint='EXPIRED2' end
 eq(choose(n,result.next).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
test('new haste with old per-slot projection is rejected',function()
 local s=active_scene();s.actor.activeStatsEvidence.buffFingerprint='HASTE2'
 eq(choose(s).reason,'PER_SLOT_BUFF_AWARE_STATS_UNVERIFIED')
end)
test('changed active stats invalidates previously stable result',function()
 local s=active_scene();local _,prior=two(s)
 local n=clone(s);n.frame.tick=103;n.actor.activeStatsEvidence.tick=103
 n.actor.activeStatsEvidence.activeFingerprint='ACTIVE2'
 for _,w in ipairs(n.weapons) do w.effectiveStatsEvidence.activeFingerprint='ACTIVE2' end
 eq(choose(n,prior.next).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
test('manual and EPS remain protected',function()
 local s=active_scene();s.actor.epsBusy=true
 local _,r=two(s);eq(r.status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
test('no executable game action from new bridge',function()
 local _,r=two(active_scene());eq(r.executable,false);eq(r.dispatchAuthorized,false)
end)
print('PASS ACTIVE STATS BRIDGE '..count..'/'..count..' SOURCE ONLY')
