-- Native Lua offline: APR proficiency table + final engine APR handoff.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local v5=dofile(folder..'BGXAI_WEAPON_APR_PROVENANCE_V5.lua')
local v4=dofile(folder..'BGXAI_WEAPON_EFFECTS_V4.lua')
local v3=dofile(folder..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua')
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

local nonintr=dofile(folder..'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua')
local function readonly(s, prev)
 return bridge.choose(s,prev,v4.choose,v3.preview)
end
local n=0
local function check(label,fn) fn();n=n+1;print('PASS '..label) end
check('V3 preview scores even during manual EPS + cast, foreground holds',function()
 local s=active_scene();s.actor.manualOrderActive=true;s.actor.epsBusy=true
 s.actor.healingReserved=true;s.actor.currentlyCasting=true;s.actor.originVerified='UNKNOWN'
 local fg=bridge.choose(s,nil,v4.choose,v3.choose)
 eq(fg.status,'HOLD_PRESERVE_MANUAL_OR_EPS')
 local fg2=clone(s);fg2.frame.tick=101;fg2.actor.activeStatsEvidence.tick=101
 local fgsecond=bridge.choose(fg2,fg.next,v4.choose,v3.choose)
 eq(fgsecond.status,'HOLD_PRESERVE_MANUAL_OR_EPS')
 local a=nonintr.step(s,nil,readonly)
 eq(a.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 local b=nonintr.step(fg2,a.next,readonly)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(b.proposedWeaponId,'SLING');eq(b.proposedSlotIndex,0)
 eq(b.ordersSent,0);eq(b.actionQueueCleared,false)
end)
check('V3 + V4 + active stats: changed buff recalculates while continuing cast',function()
 local s=active_scene();s.actor.currentlyCasting=true;s.actor.epsBusy=true
 local a=nonintr.step(s,nil,readonly)
 local bscene=clone(s);bscene.frame.tick=101;bscene.actor.activeStatsEvidence.tick=101
 local b=nonintr.step(bscene,a.next,readonly)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 local c=clone(bscene);c.frame.tick=102;c.actor.activeStatsEvidence.tick=102
 c.actor.activeStatsEvidence.buffFingerprint='HASTE_EXPIRED'
 for _,w in ipairs(c.weapons) do w.effectiveStatsEvidence.buffFingerprint='HASTE_EXPIRED' end
 local r=nonintr.step(c,b.next,readonly)
 eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 assert(r.next.pending==nil);eq(r.currentActionPreserved,true)
end)
check('missing per-slot stats fail closed during cast',function()
 local s=active_scene();s.actor.currentlyCasting=true
 s.weapons[1].effectiveStatsEvidence.otherWeaponRecalculated=false
 local r=nonintr.step(s,nil,readonly)
 eq(r.status,'HOLD_SCORER_RESULT_UNTRUSTED')
 eq(r.ordersSent,0)
end)
check('verified empty ammo reaches pending advisory while EPS/manual busy; never dispatched',function()
 local s=active_scene();s.weapons[2].ammoCount=0
 s.actor.manualOrderActive=true;s.actor.epsBusy=true;s.actor.originVerified='UNKNOWN'
 local a=nonintr.step(s,nil,readonly)
 local bscene=clone(s);bscene.frame.tick=101;bscene.actor.activeStatsEvidence.tick=101
 local b=nonintr.step(bscene,a.next,readonly)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(b.proposedWeaponId,'SLING');eq(b.proposedSlotIndex,0)
 eq(b.ordersSent,0);eq(b.dispatchAuthorized,false)
 eq(b.currentActionPreserved,true);eq(b.actionQueueCleared,false)
end)
print('PASS REAL WEAPON PIPELINE INTEGRATION '..n..'/'..n..' OFFLINE')
