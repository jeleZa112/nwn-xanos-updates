-- Native Lua offline: APR proficiency table + final engine APR handoff.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
-- On CI reuse the real modules in the same repository; no vendored duplicates.
local source_folder=folder
local probe=io.open(folder..'../../patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_PRIORITY_LUA_V3.lua','r')
if probe then probe:close();source_folder=folder..'../../patchsets/ranged_fighter_guarded_20261119/' end
local v5=dofile(source_folder..'BGXAI_WEAPON_APR_PROVENANCE_V5.lua')
local v4=dofile(source_folder..'BGXAI_WEAPON_EFFECTS_V4.lua')
local v3=dofile(source_folder..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua')
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

local module=dofile(folder..'BGXAI_R24_SESSION_ADVISORY_BRIDGE_RO.lua')
local deps={noninterrupt=dofile(source_folder..'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua'),
  currentStats=dofile(source_folder..'BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua'),
  apr=v5,effects=v4,priority=v3}
local count=0
local function check(name,fun) fun();count=count+1;print('PASS '..name) end
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
local function advance(s)
 local n=clone(s);n.frame.tick=n.frame.tick+1
 -- Real-world snapshots are per frame; do not treat snapshotId as session ID.
 n.frame.snapshotId='S'..n.frame.tick
 n.actor.activeStatsEvidence.tick=n.frame.tick
 n.actor.activeStatsEvidence.snapshotId=n.frame.snapshotId
 n.actor.traitProfile.snapshotId=n.frame.snapshotId
 n.enemy.protections.snapshotId=n.frame.snapshotId
 n.aprSource=n.aprSource or nil
 for _,w in ipairs(n.weapons) do
  w.snapshotId=n.frame.snapshotId;w.specialEffectsSnapshotId=n.frame.snapshotId
  w.effectiveStatsEvidence.snapshotId=n.frame.snapshotId
  if w.damageBreakdown then
   w.damageBreakdown.snapshotId=n.frame.snapshotId
   for _,item in ipairs(w.damageBreakdown.components or {}) do item.snapshotId=n.frame.snapshotId end
  end
 end
 return n
end
local function run(s,previous,session,mode)
 return module.step({mode=mode or 'OFFLINE_SYNTHETIC_FIXTURE',pipeline='CURRENT_ACTIVE_STATS',
  sessionToken=session or 'RUN_A',scene=s},previous,deps)
end
local function inert(x)
 eq(x.ordersSent,0);eq(x.localsWritten,0);eq(x.dispatchAuthorized,false)
 eq(x.weaponSwitchAuthorized,false);eq(x.actionQueueCleared,false)
 eq(x.currentActionPreserved,true);eq(x.executable,false)
end
check('real R17/R20 reports cannot grant scorer',function()
 local s=active_scene();local called=0
 local fake=setmetatable({}, {__index=function()called=called+1;error('not allowed')end})
 local x=module.step({mode='REAL_READONLY_SOURCES_UNVERIFIED',sessionToken='RUN_A',
  scene=s,verified=true,completeEffects=true,alternatesReady=true},nil,fake)
 eq(x.status,'KEEP_CURRENT_WEAPON_NO_DISPATCH');eq(x.next,nil);eq(called,0);inert(x)
end)
check('empty scene holds',function()
 local x=module.step({mode='OFFLINE_SYNTHETIC_FIXTURE',sessionToken='RUN_A'},nil,deps)
 eq(x.status,'KEEP_CURRENT_WEAPON_NO_DISPATCH');inert(x)
end)
check('first synthetic frame stabilizes, no dispatch',function()
 local x=run(active_scene(),nil,'RUN_A')
 eq(x.status,'OFFLINE_SYNTHETIC_ADVISORY_NO_DISPATCH')
 eq(x.advisoryStatus,'CONTINUE_CURRENT_ACTION_RECALCULATING');inert(x)
end)
check('second synthetic frame proposes better weapon without commands',function()
 local s=active_scene();local x=run(s,nil,'RUN_A');local y=run(advance(s),x.next,'RUN_A')
 eq(y.advisoryStatus,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(y.proposedWeaponId,'SLING');eq(y.proposedSlotIndex,0)
 inert(y)
end)
check('EPS and manual orders remain uninterrupted while scoring',function()
 local s=active_scene();s.actor.manualOrderActive=true;s.actor.epsBusy=true
 s.actor.healingReserved=true;s.actor.currentlyCasting=true;s.actor.originVerified='UNKNOWN'
 local x=run(s,nil,'RUN_A');local y=run(advance(s),x.next,'RUN_A')
 eq(y.advisoryStatus,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING');inert(y)
end)
check('changed session drops old pending despite matching inventory and buffs',function()
 local s=active_scene();local x=run(s,nil,'RUN_A')
 local n=advance(s);local y=run(n,x.next,'RUN_A')
 eq(y.advisoryStatus,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 local z=run(advance(n),y.next,'RUN_B')
 eq(z.previousSessionDiscarded,true);eq(z.proposedWeaponId,nil)
 eq(z.advisoryStatus,'CONTINUE_CURRENT_ACTION_RECALCULATING');inert(z)
end)
check('normal next-frame snapshot change never forces session reset',function()
 local s=active_scene();local x=run(s,nil,'RUN_A')
 local y=run(advance(s),x.next,'RUN_A')
 eq(y.previousSessionDiscarded,false)
 eq(y.proposedWeaponId,'SLING');inert(y)
end)
check('changed actor forces re-evaluation even if sessionToken identical',function()
 local s=active_scene();local x=run(s,nil,'RUN_A')
 local n=advance(s);local y=run(n,x.next,'RUN_A')
 local m=advance(n);m.frame.actorId='DIFFERENT';m.actor.actorId='DIFFERENT'
 m.actor.activeStatsEvidence.actorId='DIFFERENT'
 for _,w in ipairs(m.weapons) do w.effectiveStatsEvidence.actorId='DIFFERENT' end
 local z=run(m,y.next,'RUN_A')
 eq(z.previousSessionDiscarded,true);eq(z.proposedWeaponId,nil);inert(z)
end)
check('missing real typed session token cannot be guessed',function()
 local s=active_scene();local x=run(s,nil,'')
 eq(x.status,'KEEP_CURRENT_WEAPON_NO_DISPATCH');inert(x)
end)
check('untrusted module can never issue commands through this wrapper',function()
 local s=active_scene();local x=module.step({mode='OFFLINE_SYNTHETIC_FIXTURE',sessionToken='R1',
  pipeline='CURRENT_ACTIVE_STATS',scene=s},nil,
  {noninterrupt={step=function()return {installed=false,ordersSent=1}end},
   effects=v4,priority=v3,currentStats=deps.currentStats})
 eq(x.status,'KEEP_CURRENT_WEAPON_NO_DISPATCH');inert(x)
end)
check('existing V5 APR path also produces advisory only',function()
 local s=scene()
 s.actor.activeStatsEvidence={source='SYNTHETIC_ONLY',snapshotId='S1',actorId='ACTOR',
   tick=100,activeFingerprint='ASTAT',buffFingerprint='BUFF'}
 local function next_frame(x)
  local n=clone(x);n.frame.tick=n.frame.tick+1
  n.frame.snapshotId='F'..n.frame.tick
  n.actor.activeStatsEvidence.tick=n.frame.tick
  n.actor.activeStatsEvidence.snapshotId=n.frame.snapshotId
  n.actor.traitProfile.snapshotId=n.frame.snapshotId
  n.enemy.protections.snapshotId=n.frame.snapshotId
  n.aprSource.snapshotId=n.frame.snapshotId
  for _,w in ipairs(n.weapons) do
   w.snapshotId=n.frame.snapshotId;w.aprAudit.snapshotId=n.frame.snapshotId
   w.specialEffectsSnapshotId=n.frame.snapshotId
   w.damageBreakdown.snapshotId=n.frame.snapshotId
   for _,item in ipairs(w.damageBreakdown.components) do item.snapshotId=n.frame.snapshotId end
  end
  return n
 end
 local x=module.step({mode='OFFLINE_SYNTHETIC_FIXTURE',pipeline='APR_PROVENANCE',
  sessionToken='PIP_A',scene=s},nil,deps)
 local y=module.step({mode='OFFLINE_SYNTHETIC_FIXTURE',pipeline='APR_PROVENANCE',
  sessionToken='PIP_A',scene=next_frame(s)},x.next,deps)
 eq(x.advisoryStatus,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 eq(y.advisoryStatus,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(y.proposedWeaponId,'SLING');inert(y)
end)
check('pipeline change invalidates previous candidate',function()
 local s=active_scene();local x=run(s,nil,'RUN_A');local y=run(advance(s),x.next,'RUN_A')
 local z=module.step({mode='OFFLINE_SYNTHETIC_FIXTURE',pipeline='APR_PROVENANCE',
  sessionToken='RUN_A',scene=advance(advance(s))},y.next,deps)
 eq(z.previousSessionDiscarded,true);eq(z.proposedWeaponId,nil);inert(z)
end)
print('PASS R24 SESSION ADVISORY PIPELINE '..count..'/'..count..' SOURCE ONLY')
