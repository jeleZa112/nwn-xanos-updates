-- Standalone native Lua 5.3 source-only tests; NO user game or EEex runtime.
local filename = arg and arg[0] or 'test_weapon_priority_lua_v3.lua'
local root = filename:match('^(.*[/\\])') or './'
local choose = dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').choose
local function deep(v)
 if type(v)~='table' then return v end
 local t={} for k,x in pairs(v) do t[k]=deep(x) end return t
end
local function weapon(id,ix,over)
 local w={id=id,quickslotIndex=ix,slot='QUICKSLOT',mode='MELEE',
 usableVerified=true,equippedWeaponSlotVerified=true,inRange=true,
 finalTHAC0=10,apr=2,avgDamageOnHit=7,damageType='SLASHING',
 enchantment=1,magical=true,switchCost=0,resourceCost=0,retaliationRisk=0,
 movementCost=0,extraEffectValue=0,combatCostsVerified=true,
 statBasis='FINAL_EFFECTIVE',allRaceClassKitProficiencyBonusesIncluded=true,
 finalCombatStatsVerified=true,modFingerprint='EET',snapshotId='SNAP1',
 weaponGroup='LONG_SWORD'}
 for k,v in pairs(over or {}) do w[k]=v end return w
end
local function mk(close,kind)
 local sel=close and 'DART' or 'SWORD'
 return {frame={tick=100,area='AR001',actorId='FIGHTER1',enemyId='EN1',
 snapshotId='SNAP1',equipmentFingerprint='EQUIP1',protectionFingerprint='PROT1',
 combatFingerprint=close and 'CLOSE' or 'FAR',selectedWeaponId=sel,
 captureContract='COMPLETE_EFFECTIVE_SNAPSHOT',completeEquipmentObserved=true,
 completeQuiverObserved=true,completeTargetObserved=true},
 actor={actorId='FIGHTER1',area='AR001',currentTargetId='EN1',handsMode='SINGLE',
 observationVerified=true,manualOrderActive=false,currentlyCasting=false,
 healingReserved=false,epsBusy=false,originVerified='AI',selectedWeaponId=sel,
 pathSafeVerified=true,canSustainMelee=true,nearRangedEnemy=close,
 traitProfile={verified=true,activeClassesVerified=true,raceClassKitBonusesIncluded=true,
 modFingerprint='EET',snapshotId='SNAP1'}},
 enemy={enemyId='EN1',area='AR001',observationVerified=true,
 hostileVerified=true,visibleVerified=true,armorClass=0,
 protections={snapshotId='SNAP1',observed=true,immuneDamageTypes={},
 minimumEnchantment=0,magicalWeaponsBlocked=false,normalWeaponsBlocked=false,
 missilesBlocked=false,resistance={SLASHING=0,CRUSHING=0,PIERCING=0,MISSILE=0}}},
 quickslotIds={'SWORD','DART',false,false},
 weapons={weapon('SWORD',0,close and {} or {inRange=false,canReachWithSafeMove=true,movementCost=8}),
 weapon('DART',1,{mode='RANGED',damageType='MISSILE',weaponGroup='DART',
 ammoVerified=true,ammunitionModel='SELF',ammoCount=30,avgDamageOnHit=5.5,
 apr=3,finalTHAC0=close and 18 or 10,rangedClosePenaltyAccounted=true})}}
end
local function two(s)
 local a=choose(s)
 local changed=deep(s);changed.frame.tick=s.frame.tick+1
 return a,choose(changed,a.next)
end
local count=0
local function check(name,fn) fn();count=count+1;print('PASS '..name) end
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
check('far preferred self-ammo dart',function()
 local a,b=two(mk(false));eq(a.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'DART');eq(b.slotIndex,1)
 eq(b.executable,false);eq(b.dispatchAuthorized,false)
end)
check('close gets sword with native +8 THAC0 already included',function()
 local _,b=two(mk(true));eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'SWORD');eq(b.slotIndex,0)
end)
check('unknown point blank penalty HOLD',function()
 local s=mk(true);s.weapons[2].rangedClosePenaltyAccounted=false
 eq(two(s).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
 local _,b=two(s);eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
end)
check('verified alternate effective stats retain darts in melee',function()
 local s=mk(true);s.weapons[2].avgDamageOnHit=8;s.weapons[2].finalTHAC0=10
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
end)
check('guard denies manually ordered action',function()
 local s=mk(true);s.actor.manualOrderActive=true
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('guard denies unknown manual origin',function()
 local s=mk(true);s.actor.originVerified='UNKNOWN'
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('unknown distance context HOLD',function()
 local s=mk(true);s.actor.nearRangedEnemy=nil
 eq(choose(s).status,'HOLD_DISTANCE_OR_PENALTY_CONTEXT_UNKNOWN')
end)
check('guard denies EPS busy',function()
 local s=mk(true);s.actor.epsBusy=true
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('guard denies pending healing',function()
 local s=mk(true);s.actor.healingReserved=true
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('guard denies casting',function()
 local s=mk(true);s.actor.currentlyCasting=true
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('empty quickslot nil unknown; false known empty',function()
 local s=mk(true);s.quickslotIds[4]=nil
 eq(choose(s).status,'HOLD_INCOMPLETE_LOADOUT')
 s.quickslotIds[4]=false
 eq(choose(s).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
check('occupied slot missing weapon HOLD',function()
 local s=mk(true);s.weapons[2]=nil
 eq(choose(s).status,'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE')
end)
check('known empty selected darts switch to ready melee',function()
 local s=mk(true);s.weapons[2].ammoCount=0
 local _,b=two(s);eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'SWORD');eq(b.currentUnusableReason,'VERIFIED_EMPTY_AMMUNITION')
 eq(b.dispatchAuthorized,false)
end)
check('known empty inactive darts keep current sword',function()
 local s=mk(true);s.frame.selectedWeaponId='SWORD';s.actor.selectedWeaponId='SWORD'
 s.weapons[2].ammoCount=0
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
end)
check('unknown ammo HOLD',function()
 local s=mk(true);s.weapons[2].ammoCount=nil
 eq(choose(s).status,'HOLD_AMMO_OR_THROWABLE_UNVERIFIED')
end)
check('empty ammo and unsafe melee does not force engagement',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.actor.canSustainMelee=false
 local _,b=two(s);eq(b.status,'HOLD_NO_EFFECTIVE_ATTACK')
end)
check('zero ammo without observed inventory is unknown HOLD',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.weapons[2].ammoVerified=false
 eq(choose(s).status,'HOLD_AMMO_OR_THROWABLE_UNVERIFIED')
end)
check('unreachable distant melee excludes only melee; ranged can be recommended',function()
 local s=mk(false);s.actor.pathSafeVerified=false
 local _,b=two(s);eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'DART');eq(b.candidates[1].reason,'VERIFIED_NO_SAFE_MELEE_PATH')
end)
check('melee unable to survive excludes sword only, keeps darts',function()
 local s=mk(true);s.actor.canSustainMelee=false
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
 eq(b.candidates[1].reason,'VERIFIED_UNSAFE_TO_TANK')
end)
check('unknown melee survivability keeps HOLD not exclusion',function()
 local s=mk(true);s.actor.canSustainMelee=nil
 local _,b=two(s);eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
end)
check('unknown safe path keeps HOLD not exclusion',function()
 local s=mk(false);s.actor.pathSafeVerified=nil
 local _,b=two(s);eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
end)
check('ranged out of range excluded but does not block current sword',function()
 local s=mk(true);s.frame.selectedWeaponId='SWORD';s.actor.selectedWeaponId='SWORD'
 s.weapons[2].inRange=false
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
 eq(b.candidates[2].reason,'VERIFIED_RANGED_OUT_OF_RANGE')
end)
check('cannot switch away from empty ammo to unsafe negative utility',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.weapons[1].retaliationRisk=200
 local _,b=two(s);eq(b.status,'HOLD_NO_EFFECTIVE_ATTACK')
end)
check('manual or EPS busy blocks even verified no ammo in foreground',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.actor.epsBusy=true
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('passive preview cannot request dispatch even for empty ammo',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.actor.originVerified='UNKNOWN'
 local preview=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').preview
 local first=preview(s);s.frame.tick=101
 local second=preview(s,first.next)
 eq(second.status,'PASSIVE_RANKING_SUGGESTS_SLOT')
 eq(second.dispatchAuthorized,false);eq(second.executable,false)
end)
check('wrong enemy identity HOLD',function()
 local s=mk(true);s.enemy.enemyId='ALLY'
 eq(choose(s).status,'HOLD_TARGET_OR_SELECTION_CHANGED')
end)
check('enemy in other area HOLD',function()
 local s=mk(true);s.enemy.area='AR002'
 eq(choose(s).status,'HOLD_TARGET_OR_SELECTION_CHANGED')
end)
check('stale final combat facts HOLD',function()
 local s=mk(true);s.weapons[2].snapshotId='OLD'
 eq(choose(s).status,'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE')
end)
check('dual wield requires aggregate verified stats',function()
 local s=mk(true);s.actor.handsMode='DUAL'
 eq(choose(s).status,'HOLD_DUAL_WIELD_COMBAT_STATS_UNKNOWN')
 s.weapons[1].dualWieldStatsVerified=true
 eq(choose(s).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
check('switch cooldown',function()
 local s=mk(true);local a,b=two(s)
 local t=deep(s);t.frame.tick=102
 eq(choose(t,b.next).status,'HOLD_ADVISORY_SWITCH_COOLDOWN')
end)
check('combat fingerprint changed between frames restarts',function()
 local s=mk(true);local a=choose(s)
 s.frame.tick=101;s.frame.combatFingerprint='RANGE_CHANGED'
 eq(choose(s,a.next).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
end)
check('capture ID may change if weapons and trait profiles match new ID',function()
 local s=mk(true);local a=choose(s)
 s.frame.tick=101;s.frame.snapshotId='SNAP2'
 s.actor.traitProfile.snapshotId='SNAP2';s.enemy.protections.snapshotId='SNAP2'
 for _,w in ipairs(s.weapons) do w.snapshotId='SNAP2' end
 eq(choose(s,a.next).status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
end)
check('impermeable melee selects ranged if safe',function()
 local s=mk(false);s.enemy.protections.immuneDamageTypes={'SLASHING'}
 local _,b=two(s);eq(b.toWeaponId,'DART')
end)
check('partial resistance changes relative DPS',function()
 local s=mk(true);s.enemy.protections.resistance.SLASHING=0.9
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
end)
check('unknown occupied weapon inRange HOLD',function()
 local s=mk(true);s.weapons[1].inRange=nil
 local _,b=two(s);eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
end)
check('input remains unchanged',function()
 local s=mk(true);local orig=deep(s)
 local _,b=two(s)
 eq(s.weapons[2].finalTHAC0,orig.weapons[2].finalTHAC0)
 eq(s.frame.tick,100);eq(b.executable,false)
end)
check('selected depleted missiles need no invented APR to recommend safe sword',function()
 local s=mk(true);s.weapons[2].ammoCount=0
 s.weapons[2].apr=nil;s.weapons[2].finalTHAC0=nil
 s.weapons[2].avgDamageOnHit=nil;s.weapons[2].combatCostsVerified=false
 s.weapons[2].finalCombatStatsVerified=false
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SWORD')
 eq(b.currentUnusableReason,'VERIFIED_EMPTY_AMMUNITION')
 eq(b.dispatchAuthorized,false)
end)
check('unsafe melee need no hypothetical APR to preserve useful darts',function()
 local s=mk(false);s.actor.canSustainMelee=false
 s.weapons[1].apr=nil;s.weapons[1].finalTHAC0=nil
 s.weapons[1].avgDamageOnHit=nil;s.weapons[1].combatCostsVerified=false
 s.weapons[1].finalCombatStatsVerified=false
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'DART')
 eq(b.candidates[1].reason,'VERIFIED_UNSAFE_TO_TANK')
end)
check('known inaccessible melee can be excluded without virtual stats',function()
 local s=mk(false);s.actor.pathSafeVerified=false
 s.weapons[1].apr=nil;s.weapons[1].combatCostsVerified=false
 s.weapons[1].finalCombatStatsVerified=false
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.candidates[1].reason,'VERIFIED_NO_SAFE_MELEE_PATH')
end)
check('no ammo without verification must not bypass final-stat gates',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.weapons[2].ammoVerified=false
 s.weapons[2].apr=nil;s.weapons[2].finalCombatStatsVerified=false
 eq(choose(s).status,'HOLD_AMMO_OR_THROWABLE_UNVERIFIED')
end)
check('unverified melee survivability and absent APR remain blocked',function()
 local s=mk(false);s.actor.canSustainMelee=nil
 s.weapons[1].apr=nil;s.weapons[1].finalCombatStatsVerified=false
 eq(choose(s).status,'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE')
end)
check('both known unusable candidates cannot cause a switch',function()
 local s=mk(true);s.weapons[2].ammoCount=0;s.actor.canSustainMelee=false
 s.weapons[1].apr=nil;s.weapons[2].apr=nil
 s.weapons[1].finalCombatStatsVerified=false;s.weapons[2].finalCombatStatsVerified=false
 local _,b=two(s)
 eq(b.status,'HOLD_NO_EFFECTIVE_ATTACK');eq(b.dispatchAuthorized,false)
end)

check('selected verified out-of-range dart needs no fake APR for sword fallback',function()
 local s=mk(true);local dead=s.weapons[2]
 dead.inRange=false;dead.apr=nil;dead.finalTHAC0=nil
 dead.avgDamageOnHit=nil;dead.finalCombatStatsVerified=false;dead.combatCostsVerified=false
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SWORD')
 eq(b.currentUnusableReason,'VERIFIED_RANGED_OUT_OF_RANGE')
 eq(b.dispatchAuthorized,false)
end)
check('verified out-of-range alternative cannot block selected sword',function()
 local s=mk(true);s.frame.selectedWeaponId='SWORD';s.actor.selectedWeaponId='SWORD'
 s.weapons[2].inRange=false;s.weapons[2].apr=nil
 s.weapons[2].finalCombatStatsVerified=false;s.weapons[2].combatCostsVerified=false
 local _,b=two(s);eq(b.status,'KEEP_CURRENT')
 eq(b.candidates[2].reason,'VERIFIED_RANGED_OUT_OF_RANGE')
end)
check('unknown ranged reach never implies confirmed exclusion',function()
 local s=mk(true);s.weapons[2].inRange=nil;s.weapons[2].apr=nil
 s.weapons[2].finalCombatStatsVerified=false
 eq(choose(s).status,'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE')
end)
check('known out-of-range cannot launder unknown ammo provenance',function()
 local s=mk(true);s.weapons[2].inRange=false;s.weapons[2].ammoVerified=false
 s.weapons[2].apr=nil;s.weapons[2].finalCombatStatsVerified=false
 eq(choose(s).status,'HOLD_AMMO_OR_THROWABLE_UNVERIFIED')
end)
check('immune set must not accept silently ignored named keys',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={SLASHING=true}
 local _,b=two(s);eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
 eq(b.reason,'IMMUNITY_SET_INCOMPLETE');eq(b.dispatchAuthorized,false)
end)
check('immune set mixed numeric and named keys must HOLD',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={[1]='SLASHING',MISSILE=true}
 local _,b=two(s);eq(b.reason,'IMMUNITY_SET_INCOMPLETE')
end)
check('immune set with sparse array must HOLD',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={[2]='SLASHING'}
 local _,b=two(s);eq(b.reason,'IMMUNITY_SET_INCOMPLETE')
end)
check('immune set repeated damage type must HOLD',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={'SLASHING','SLASHING'}
 local _,b=two(s);eq(b.reason,'IMMUNITY_SET_INCOMPLETE')
end)
check('immune set unsupported damage type must HOLD',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={'UNKNOWN'}
 local _,b=two(s);eq(b.reason,'IMMUNITY_SET_INCOMPLETE')
end)
check('valid two-element immune array excludes sword without false empty map',function()
 local s=mk(false);s.enemy.protections.immuneDamageTypes={'SLASHING','CRUSHING'}
 local _,b=two(s);eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'DART');eq(b.dispatchAuthorized,false)
end)
check('all weapon damage types immune yields HOLD with no false switch',function()
 local s=mk(true);s.enemy.protections.immuneDamageTypes={'SLASHING','MISSILE'}
 local _,b=two(s);eq(b.status,'HOLD_NO_EFFECTIVE_ATTACK')
 eq(b.dispatchAuthorized,false)
end)

-- These are real ranking bugs: current weapon cannot hurt the *verified*
-- target, yet the previous 2-DPR threshold kept attacking futilely.
local function selected_sword_with_weak_dart()
 local s=mk(true)
 s.frame.selectedWeaponId='SWORD';s.actor.selectedWeaponId='SWORD'
 s.weapons[2].apr=0.5;s.weapons[2].avgDamageOnHit=1
 s.weapons[2].finalTHAC0=20 -- ~0.025 expected damage/round
 return s
end
check('fully immune current sword yields to low damage verified dart',function()
 local s=selected_sword_with_weak_dart()
 s.enemy.protections.immuneDamageTypes={'SLASHING'}
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.toWeaponId,'DART');eq(b.slotIndex,1)
 eq(b.currentUnusableReason,'VERIFIED_TARGET_WEAPON_IMMUNITY')
 eq(b.executable,false);eq(b.dispatchAuthorized,false)
end)
check('full damage resistance switches but 99 percent does not force it',function()
 local s=selected_sword_with_weak_dart()
 s.enemy.protections.resistance.SLASHING=1
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(b.currentUnusableReason,'VERIFIED_NO_EFFECTIVE_DAMAGE_OR_EFFECT')
 local p=selected_sword_with_weak_dart()
 p.enemy.protections.resistance.SLASHING=0.999
 local _,c=two(p)
 eq(c.status,'KEEP_CURRENT')
end)
check('missile-blocked selected dart yields to weak safe melee attack',function()
 local s=mk(true)
 s.enemy.protections.missilesBlocked=true
 s.weapons[1].apr=0.5;s.weapons[1].avgDamageOnHit=0.5
 s.weapons[1].finalTHAC0=20
 local _,b=two(s)
 eq(b.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');eq(b.toWeaponId,'SWORD')
 eq(b.currentUnusableReason,'VERIFIED_TARGET_WEAPON_IMMUNITY')
end)
check('blocked current never sends player or EPS order in passive preview',function()
 local s=selected_sword_with_weak_dart()
 s.enemy.protections.immuneDamageTypes={'SLASHING'}
 s.actor.originVerified='UNKNOWN';s.actor.epsBusy=true
 local preview=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').preview
 local first=preview(s);s.frame.tick=101
 local second=preview(s,first.next)
 eq(second.status,'PASSIVE_RANKING_SUGGESTS_SLOT')
 eq(second.dispatchAuthorized,false);eq(second.executable,false)
 eq(choose(s).status,'HOLD_PRESERVE_MANUAL_OR_EPS')
end)
check('fully immune current cannot force switching to net negative alternative',function()
 local s=selected_sword_with_weak_dart()
 s.enemy.protections.immuneDamageTypes={'SLASHING'}
 s.weapons[2].retaliationRisk=2
 local _,b=two(s)
 eq(b.status,'HOLD_NO_EFFECTIVE_ATTACK')
 eq(b.dispatchAuthorized,false)
end)
check('nonphysical verified utility preserves currently selected weapon',function()
 local s=selected_sword_with_weak_dart()
 s.weapons[1].avgDamageOnHit=0;s.weapons[1].extraEffectValue=1
 local _,b=two(s)
 eq(b.status,'KEEP_CURRENT')
 eq(b.dispatchAuthorized,false)
end)
-- Reuse R13 AC modifiers, not a new weapon scorer or action.
local function with_r13_type_ac(s)
 s.enemy.targetArmorClassBaseCandidate=0
 s.enemy.targetArmorClassByAttackTypeCandidate={
   CRUSHING=0,PIERCING=-8,SLASHING=-8,MISSILE=8}
 s.enemy.targetTypeACModelStatus='R13_DERIVED_ATTACK_TYPE_AC_MODEL_ONLY'
 s.enemy.targetTypeACModelSnapshotId='SNAP1'
 s.enemy.targetTypeACNativeAuthenticated=false
 return s
end
check('base-only older advisory remains approximate with no dispatch',function()
 local _,b=two(mk(false))
 eq(b.candidates[2].attackACModel,'BASE_AC_ONLY_APPROXIMATE')
 eq(b.executable,false);eq(b.dispatchAuthorized,false)
end)
check('R13 melee slashing versus ranged missile AC changes target-specific choice',function()
 local s=mk(false)
 s.weapons[1].inRange=true
 s.weapons[1].movementCost=0
 local _,legacy=two(s);eq(legacy.status,'KEEP_CURRENT')
 with_r13_type_ac(s)
 local _,typed=two(s)
 eq(typed.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY')
 eq(typed.toWeaponId,'DART')
 eq(typed.candidates[1].targetACUsed,-8)
 eq(typed.candidates[2].targetACUsed,8)
 eq(typed.candidates[2].attackACType,'MISSILE')
 eq(typed.candidates[2].attackACModel,'R13_TYPE_AC_MODEL_ONLY')
 eq(typed.dispatchAuthorized,false)
end)
check('ranged piercing payload uses missile AC but piercing resistance',function()
 local s=with_r13_type_ac(mk(false))
 s.weapons[2].damageType='PIERCING'
 s.enemy.protections.resistance.PIERCING=0.5
 local _,b=two(s)
 eq(b.candidates[2].attackACType,'MISSILE')
 eq(b.candidates[2].targetACUsed,8)
 eq(b.candidates[2].hitChance,0.95)
 eq(b.candidates[2].dpr,0.95*5.5*3*0.5)
 eq(b.dispatchAuthorized,false)
end)
check('partial R13 AC map is HOLD rather than false weapon choice',function()
 local s=with_r13_type_ac(mk(false))
 s.enemy.targetArmorClassByAttackTypeCandidate.MISSILE=nil
 local _,b=two(s)
 eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
 eq(b.reason,'TARGET_TYPE_AC_EVIDENCE_INCOMPLETE')
 eq(b.dispatchAuthorized,false)
end)
check('different R13 target snapshot cannot score',function()
 local s=with_r13_type_ac(mk(false))
 s.enemy.targetTypeACModelSnapshotId='WRONG'
 local _,b=two(s)
 eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
 eq(b.reason,'TARGET_TYPE_AC_EVIDENCE_INCONSISTENT')
end)
check('R13 AC changed under same external fingerprint restabilizes',function()
 local s=with_r13_type_ac(mk(false))
 local first=choose(s)
 s.frame.tick=101
 s.enemy.targetArmorClassByAttackTypeCandidate.MISSILE=6
 local second=choose(s,first.next)
 eq(second.status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT')
 eq(second.dispatchAuthorized,false)
end)
check('native proof cannot be invented by caller mock flag',function()
 local s=with_r13_type_ac(mk(false))
 s.enemy.targetTypeACNativeAuthenticated=true
 local _,b=two(s)
 eq(b.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON')
 eq(b.reason,'TARGET_TYPE_AC_EVIDENCE_INCONSISTENT')
 eq(b.dispatchAuthorized,false)
end)
local function mk_backpack_weapon()
 local w=weapon('BAG_HAMM',nil,{slot='BACKPACK',sourceSlot=18,
  resRef='HAMM01',modelProvenance='V3_V4_V5',
  counterfactualBasis='MODEL_ONLY_NOT_NATIVE_EFFECTIVE',
  alternativeEffectiveStatsLiveVerified=false,
  identifiedVerified=true,notCursedVerified=true,notQuestItemVerified=true,
  offhandCompatibilityVerified=true,ammoAndLauncherVerified=true,
  protectionsAccountedVerified=true,mode='MELEE',damageType='CRUSHING',
  inRange=true,avgDamageOnHit=12,apr=2,finalTHAC0=10})
 return w
end
check('backpack V3 same-target model reuses existing scorer',function()
 local s=mk(true)
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,mk_backpack_weapon())
 eq(r.status,'BACKPACK_TARGET_UTILITY_MODEL_ONLY')
 eq(r.sourceSlot,18);eq(r.candidateResref,'HAMM01')
 eq(r.estimatedUtility,12*2*0.55)
 eq(r.attackACType,'CRUSHING')
 eq(r.engineFinalAlternativeStatsVerified,false)
 eq(r.dispatchAuthorized,false);eq(r.weaponSwitchAuthorized,false)
end)
check('backpack V3 model requires same target protection snapshot',function()
 local s=mk(true)
 s.enemy.protections.snapshotId='STALE'
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,mk_backpack_weapon())
 eq(r.status,'HOLD_STALE_ENEMY_PROTECTIONS')
end)
check('backpack V3 unknown alternate APR blocks model',function()
 local s=mk(true);local w=mk_backpack_weapon();w.apr=nil
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,w)
 eq(r.status,'HOLD_BACKPACK_TARGET_SCORE_INCOMPLETE')
 eq(r.reason,'ATTACK_STATS_UNVERIFIED');eq(r.dispatchAuthorized,false)
end)
check('backpack V3 cannot claim counterfactual stats are live',function()
 local s=mk(true);local w=mk_backpack_weapon()
 w.alternativeEffectiveStatsLiveVerified=true
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,w)
 eq(r.status,'HOLD_BACKPACK_COUNTERFACTUAL_MODEL_INCOMPLETE')
end)
check('backpack V3 uses same R13 type AC and enemy damage resistance',function()
 local s=with_r13_type_ac(mk(true));local w=mk_backpack_weapon()
 s.enemy.targetArmorClassByAttackTypeCandidate.CRUSHING=-6
 s.enemy.protections.resistance.CRUSHING=0.5
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,w)
 eq(r.attackACType,'CRUSHING');eq(r.hitChanceModel,0.25)
 eq(r.estimatedDpr,0.25*12*2*0.5)
 eq(r.dispatchAuthorized,false)
end)
check('backpack V3 never treats duplicate quickslot ID as inventory',function()
 local s=mk(true);local w=mk_backpack_weapon();w.id='SWORD'
 local r=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua').scoreBackpackCandidate(s,w)
 eq(r.status,'HOLD_BACKPACK_DUPLICATE_QUICKSLOT_ID')
end)
print('PASS WEAPON PRIORITY NATIVE LUA '..count..'/'..count..' SOURCE ONLY')