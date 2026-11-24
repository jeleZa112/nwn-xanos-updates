-- Native Lua 5.3 regression suite, no game writes and no fake EEex access.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local src=dofile(folder..'BGXAI_WEAPON_EFFECTS_V4.lua')
local choose3=dofile(folder..'../BGXAI_WEAPON_PRIORITY_V3/BGXAI_WEAPON_PRIORITY_LUA_V3.lua').choose
local function clone(t)
 if type(t)~='table' then return t end
 local n={};for k,v in pairs(t) do n[k]=clone(v) end
 return n
end
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
local function comp(cat,amount,ident)
 return {category=cat,avgDamage=amount,id=ident,snapshotId='SNAP1',observedInInstalledEET=true}
end
local function base_weapon(id,slot,group,physical,apr)
 local mode='RANGED'
 return {id=id,quickslotIndex=slot,slot='QUICKSLOT',mode=mode,
  usableVerified=true,equippedWeaponSlotVerified=true,inRange=true,
  finalTHAC0=10,apr=apr,avgDamageOnHit=physical,damageType='MISSILE',
  enchantment=1,magical=true,switchCost=0,resourceCost=0,
  retaliationRisk=0,movementCost=0,extraEffectValue=0,combatCostsVerified=true,
  statBasis='FINAL_EFFECTIVE',allRaceClassKitProficiencyBonusesIncluded=true,
  finalCombatStatsVerified=true,modFingerprint='EET',snapshotId='SNAP1',
  weaponGroup=group,dexterityHitBonusIncluded=true,strengthHitBonusExcluded=true,
  strengthRuleFromInstalledEET=true,strengthDamageApplies=group=='SLING',
  damageTypeSpecialRulesVerified=true,ammunitionModel=group=='SLING' and 'QUIVER' or 'SELF',
  ammoVerified=true,ammoCount=30,ammoResRef=group=='SLING' and 'BULLET01' or nil,
  launcherResRef=group=='SLING' and 'SLING01' or nil,
  launcherAmmoPairVerified=group=='SLING' and true or nil,
  resRef=group=='SLING' and 'SLING01' or 'DART01',
  specialEffectsComplete=true,specialEffectsSnapshotId='SNAP1',
  effectSourcesComplete={WEAPON=true,AMMO=true,LAUNCHER=true,ACTIVE_BUFF=true},
  onHitEffects={},damageBreakdown={snapshotId='SNAP1',complete=true,
  verifiedInInstalledEET=true,launcherAmmoAndBuffsIncluded=true,
  conditionalOnHitEffectsExcluded=true,
  components=group=='SLING' and {
    comp('WEAPON',3.5,'SLING_BASE'),comp('STRENGTH',7,'STR'),comp('AMMO',0,'BULLET')
   } or {comp('WEAPON',2,'DART_BASE')}}}
end
local function scene(str)
 local strength=str==nil and 7 or str
 local sling=base_weapon('SLING',0,'SLING',3.5+strength,1)
 sling.damageBreakdown.components[2].avgDamage=strength
 local dart=base_weapon('DART',1,'DART',2,3)
 return {frame={tick=100,area='AR001',actorId='WARRIOR',enemyId='FOE',
 snapshotId='SNAP1',equipmentFingerprint='GEAR1',protectionFingerprint='PROT1',
 combatFingerprint='COMBAT1',effectStatusFingerprint='EFFECT1',
 completeOnHitEffectsObserved=true,completePhysicalDamageObserved=true,effectStatusSourceVerified=true,
 selectedWeaponId='DART',captureContract='COMPLETE_EFFECTIVE_SNAPSHOT',
 completeEquipmentObserved=true,completeQuiverObserved=true,completeTargetObserved=true},
 actor={actorId='WARRIOR',area='AR001',currentTargetId='FOE',handsMode='SINGLE',
 observationVerified=true,manualOrderActive=false,currentlyCasting=false,
 healingReserved=false,epsBusy=false,originVerified='AI',selectedWeaponId='DART',
 strengthDamageBonus=strength,strengthDamageBonusVerified=true,pathSafeVerified=true,
 canSustainMelee=true,nearRangedEnemy=false,traitProfile={verified=true,
 activeClassesVerified=true,raceClassKitBonusesIncluded=true,modFingerprint='EET',
 snapshotId='SNAP1'}},
 enemy={enemyId='FOE',area='AR001',observationVerified=true,hostileVerified=true,
 visibleVerified=true,armorClass=0,effectStatusVerified=true,effectStatusFingerprint='EFFECT1',
 protections={snapshotId='SNAP1',observed=true,immuneDamageTypes={},
 minimumEnchantment=0,magicalWeaponsBlocked=false,normalWeaponsBlocked=false,
 missilesBlocked=false,resistance={MISSILE=0}}},
 quickslotIds={'SLING','DART',false,false},weapons={sling,dart}}
end
local function poison(override)
 local e={id='POISON1',kind='POISON_DOT',source='WEAPON',sourceResRef='DART01',
 trigger='ON_HIT',snapshotId='SNAP1',targetStatusFingerprint='EFFECT1',
 evidenceVerifiedInInstalledEET=true,abilityAndAmmoMatched=true,
 targetImmunityVerified=true,targetImmune=false,
 targetAlreadyAffectedVerified=true,targetAlreadyAffected=false,
 procChance=1,saveFailChance=1,magicResistanceBlockChance=0,
 resistanceFraction=0,valueOnApplication=20,valueOnSuccessfulSave=0,
 successfulSaveApplies=false,saveOutcomesVerified=true,
 valueBasis='HP_EQUIVALENT_VERIFIED',
 durationAndSurvivalAdjustedVerified=true,stackPolicy='REFRESH_NONSTACK'}
 for k,v in pairs(override or {}) do e[k]=v end
 return e
end
local function steps(s)
 local first=src.choose(s,nil,choose3)
 local second=clone(s);second.frame.tick=s.frame.tick+1
 return first,src.choose(second,first.next,choose3)
end
local count=0
local function test(label,fn) fn();count=count+1;print('PASS '..label) end
test('sling and throwing axes and daggers get strength, ordinary dart does not',function()
 eq(src.strength_applies({mode='RANGED',weaponGroup='SLING'}),true)
 eq(src.strength_applies({mode='RANGED',weaponGroup='THROWING_AXE'}),true)
 eq(src.strength_applies({mode='RANGED',weaponGroup='THROWING_DAGGER'}),true)
 eq(src.strength_applies({mode='RANGED',weaponGroup='DART'}),false)
 eq(src.strength_applies({mode='MELEE',weaponGroup='DAGGER'}),true)
end)
test('strong character picks sling over three-APR darts',function()
 local a,b=steps(scene(7));eq(a.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SLING')
end)
test('weak character keeps darts when sling strength advantage disappears',function()
 local _,b=steps(scene(0));eq(b.status,'KEEP_CURRENT')
end)
test('poison dart can beat sling if effective damage and saving throws proven',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison()}
 local _,b=steps(s);eq(b.status,'KEEP_CURRENT')
end)
test('poison immunity removes bonus, allowing sling again',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({targetImmune=true})}
 local _,b=steps(s);eq(b.toWeaponId,'SLING')
end)
test('already poisoned nonstack target does not get another full DOT',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({targetAlreadyAffected=true})}
 local _,b=steps(s);eq(b.toWeaponId,'SLING')
end)
test('save chance changes expected poison utility',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({saveFailChance=0.01})}
 local _,b=steps(s);eq(b.toWeaponId,'SLING')
end)
test('unknown poison save probability is HOLD not full value',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison()}
 s.weapons[2].onHitEffects[1].saveFailChance=nil
 eq(src.choose(s,nil,choose3).status,'HOLD_EFFECT_MODEL_INCOMPLETE')
end)
test('unverified immunity status blocks scoring',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({targetImmunityVerified=false})}
 eq(src.choose(s,nil,choose3).status,'HOLD_EFFECT_MODEL_INCOMPLETE')
end)
test('duplicate poison source effects cannot be double credited',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison(),poison()}
 eq(src.choose(s,nil,choose3).reason,'EFFECT_UNVERIFIED_OR_UNSUPPORTED')
end)
test('incorrect ammo poison resref cannot be credited',function()
 local s=scene(7);s.weapons[1].onHitEffects={poison({source='AMMO',sourceResRef='NOT_CURRENT_BULLET'})}
 eq(src.choose(s,nil,choose3).reason,'AMMO_EFFECT_MISMATCH')
end)
test('launcher effect requires active verified launcher resref',function()
 local s=scene(7);s.weapons[1].onHitEffects={poison({source='LAUNCHER',launcherResRef='WRONG'})}
 eq(src.choose(s,nil,choose3).reason,'LAUNCHER_EFFECT_MISMATCH')
end)
test('melee STR cannot be mixed into darts',function()
 local s=scene(7)
 table.insert(s.weapons[2].damageBreakdown.components,comp('STRENGTH',7,'ERRONEOUS_STR'))
 s.weapons[2].avgDamageOnHit=9
 eq(src.choose(s,nil,choose3).reason,'STRENGTH_OR_BASE_COMPONENT_NOT_ACCOUNTED')
end)
test('missing expected strength on sling blocks',function()
 local s=scene(7);table.remove(s.weapons[1].damageBreakdown.components,2)
 eq(src.choose(s,nil,choose3).reason,'STRENGTH_OR_BASE_COMPONENT_NOT_ACCOUNTED')
end)
test('strength already in final damage cannot be added again',function()
 local s=scene(7);s.weapons[1].avgDamageOnHit=17.5
 eq(src.choose(s,nil,choose3).reason,'DOUBLE_COUNT_OR_INCOMPLETE_PHYSICAL_DAMAGE')
end)
test('no ranged Dexterity to-hit verification blocks',function()
 local s=scene(7);s.weapons[1].dexterityHitBonusIncluded=false
 eq(src.choose(s,nil,choose3).reason,'RANGED_DEX_TO_HIT_NOT_INCLUDED')
end)
test('unknown effect inventory blocks ranking even if one weapon otherwise wins',function()
 local s=scene(7);s.weapons[2].specialEffectsComplete=false
 eq(src.choose(s,nil,choose3).reason,'WEAPON_ON_HIT_EFFECTS_NOT_EXHAUSTIVE')
end)
test('control utility estimate unverified cannot manufacture HP advantage',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({kind='CONTROL'})}
 eq(src.choose(s,nil,choose3).reason,'CONTROL_UTILITY_VALUE_UNKNOWN')
end)
test('delayed poison utility must include survival and duration',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({durationAndSurvivalAdjustedVerified=false})}
 eq(src.choose(s,nil,choose3).reason,'DAMAGE_OVER_TIME_HORIZON_UNKNOWN')
end)
test('target effect change invalidates prior hysteresis token',function()
 local s=scene(7);local a=src.choose(s,nil,choose3)
 local n=clone(s);n.frame.tick=101
 n.frame.effectStatusFingerprint='EFFECT2';n.enemy.effectStatusFingerprint='EFFECT2'
 local out=src.choose(n,a.next,choose3)
 eq(out.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
test('effect target status stale invalidates score',function()
 local s=scene(7);s.enemy.effectStatusFingerprint='OLD'
 eq(src.choose(s,nil,choose3).reason,'TARGET_EFFECT_STATUS_STALE')
end)
test('effects fingerprint or observed full status absent blocks',function()
 local s=scene(7);s.frame.completeOnHitEffectsObserved=false
 eq(src.choose(s,nil,choose3).reason,'SNAPSHOT_EFFECT_EVIDENCE_INCOMPLETE')
end)
test('trigger unsupported critical hit effect fails closed',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({trigger='ON_CRITICAL'})}
 eq(src.choose(s,nil,choose3).reason,'EFFECT_UNVERIFIED_OR_UNSUPPORTED')
end)
test('all recommendations remain nonexecutable and inputs immutable',function()
 local s=scene(7);local prior=clone(s)
 local a,b=steps(s)
 eq(a.executable,false);eq(b.executable,false);eq(b.dispatchAuthorized,false)
 eq(s.weapons[1].avgDamageOnHit,prior.weapons[1].avgDamageOnHit)
 eq(s.frame.combatFingerprint,prior.frame.combatFingerprint)
end)

test('successful saving throw may still deal reduced poison damage',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({saveFailChance=0,
  successfulSaveApplies=true,valueOnSuccessfulSave=20})}
 local _,out=steps(s);eq(out.status,'KEEP_CURRENT')
end)
test('successful save with no effect does not get free value',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({saveFailChance=0,
  successfulSaveApplies=false,valueOnSuccessfulSave=5})}
 eq(src.choose(s,nil,choose3).reason,'EFFECT_UNVERIFIED_OR_UNSUPPORTED')
end)
test('unverified save-success outcome refuses ranking',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({saveOutcomesVerified=false})}
 eq(src.choose(s,nil,choose3).reason,'EFFECT_UNVERIFIED_OR_UNSUPPORTED')
end)
test('nonstack effect not credited three independent times',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({valueOnApplication=20})}
 local _,out=steps(s)
 local darts=out.candidates[2]
 assert(darts.value<3.3+20,'refresh-only poison must be strictly capped')
end)
test('stack-per-hit against already poisoned target needs stacking evidence',function()
 local s=scene(7);s.weapons[2].onHitEffects={poison({stackPolicy='STACK_PER_HIT',targetAlreadyAffected=true})}
 eq(src.choose(s,nil,choose3).reason,'DOT_STACKING_WITH_EXISTING_UNKNOWN')
end)
test('full breakdown must exclude on-hit poison from base damage',function()
 local s=scene(7);s.weapons[1].damageBreakdown.conditionalOnHitEffectsExcluded=false
 eq(src.choose(s,nil,choose3).reason,'PHYSICAL_BREAKDOWN_INCOMPLETE')
end)

test('V4 range exclusion skips unobservable physical and on-hit fields of selected dart',function()
 local s=scene(7);local dead=s.weapons[2]
 dead.inRange=false;dead.apr=nil;dead.finalTHAC0=nil
 dead.avgDamageOnHit=nil;dead.finalCombatStatsVerified=false
 dead.damageBreakdown=nil;dead.specialEffectsComplete=false;dead.combatCostsVerified=false
 local _,b=steps(s);eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.currentUnusableReason,'VERIFIED_RANGED_OUT_OF_RANGE')
 eq(b.toWeaponId,'SLING')
end)
test('V4 nonselectable distant sling with missing effects cannot block useful darts',function()
 local s=scene(0);local dead=s.weapons[1]
 dead.inRange=false;dead.apr=nil;dead.finalCombatStatsVerified=false
 dead.damageBreakdown=nil;dead.specialEffectsComplete=false;dead.combatCostsVerified=false
 local _,b=steps(s);eq(b.status,'KEEP_CURRENT')
 eq(b.candidates[1].reason,'VERIFIED_RANGED_OUT_OF_RANGE')
end)
test('V4 unknown range cannot bypass absent effect evidence',function()
 local s=scene(7);local w=s.weapons[2]
 w.inRange=nil;w.apr=nil;w.finalCombatStatsVerified=false
 eq(src.choose(s,nil,choose3).reason,'FINAL_STATS_NOT_VERIFIED')
end)
test('V4 cannot exempt out-of-range missile with unknown quiver provenance',function()
 local s=scene(7);local w=s.weapons[2]
 w.inRange=false;w.ammoVerified=false;w.finalCombatStatsVerified=false
 eq(src.choose(s,nil,choose3).reason,'FINAL_STATS_NOT_VERIFIED')
end)
print('PASS TOTAL '..count..' / '..count..' NATIVE LUA SOURCE ONLY')