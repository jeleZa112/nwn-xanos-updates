"use strict";
/** Source-only regression for range-aware quickslot choice; must be run with
 * real BGXAI_WEAPON_CHOICE_ADVISORY_V1.js, _TRAITS_ADVISORY_V1.js and _ENGINE_V2.js.
 * No user EET evidence or engine actions, no runtime proof.
 */
const assert=require('node:assert/strict');
const {choosePriorityWeapon:choose}=require('./BGXAI_WEAPON_PRIORITY_ENGINE_V2.js');
const profile=()=>({verified:true,race:'HUMAN',classId:'FIGHTER',kit:'NONE',
 modFingerprint:'EET',snapshotId:'SNAP1',activeClasses:['FIGHTER'],
 levels:{FIGHTER:8},dualState:'NONE',proficiencies:{LONG_SWORD:2,DART:2}});
function weapon(id,index,extra={}) {return {id,quickslotIndex:index,slot:'QUICKSLOT',
 mode:'MELEE',usableVerified:true,equippedWeaponSlotVerified:true,inRange:true,
 finalTHAC0:10,apr:2,avgDamageOnHit:7,damageType:'SLASHING',
 enchantment:1,magical:true,switchCost:0,resourceCost:0,retaliationRisk:0,
 movementCost:0,extraEffectValue:0,combatCostsVerified:true,statBasis:'FINAL_EFFECTIVE',
 allRaceClassKitProficiencyBonusesIncluded:true,finalCombatStatsVerified:true,
 modFingerprint:'EET',snapshotId:'SNAP1',weaponGroup:'LONG_SWORD',...extra};}
function build({close=false,penaltyKnown=true,dartHit=5.5,dartThac0=null}={}) {
 const selected=close?'DART':'SWORD';
 return {frame:{tick:100,area:'AR001',actorId:'FIGHTER1',enemyId:'EN1',
  snapshotId:'SNAP1',equipmentFingerprint:'EQUIP1',protectionFingerprint:'PROT1',
  combatFingerprint:close?'CLOSE':'FAR',selectedWeaponId:selected,
  captureContract:'COMPLETE_EFFECTIVE_SNAPSHOT',completeEquipmentObserved:true,
  completeQuiverObserved:true,completeTargetObserved:true},
 actor:{actorId:'FIGHTER1',area:'AR001',currentTargetId:'EN1',handsMode:'SINGLE',
  observationVerified:true,manualOrderActive:false,currentlyCasting:false,
  healingReserved:false,epsBusy:false,originVerified:'AI',selectedWeaponId:selected,
  pathSafeVerified:true,canSustainMelee:true,nearRangedEnemy:close,
  traitProfile:profile()},
 enemy:{enemyId:'EN1',area:'AR001',observationVerified:true,hostileVerified:true,
  visibleVerified:true,armorClass:0,protections:{snapshotId:'SNAP1',observed:true,
  immuneDamageTypes:[],minimumEnchantment:0,magicalWeaponsBlocked:false,
  normalWeaponsBlocked:false,missilesBlocked:false,
  resistance:{PIERCING:0,SLASHING:0,CRUSHING:0,MISSILE:0}}},
 quickslotIds:['SWORD','DART',null,null],weapons:[
  weapon('SWORD',0,close?{}:{inRange:false,canReachWithSafeMove:true,movementCost:8}),
  weapon('DART',1,{mode:'RANGED',damageType:'MISSILE',weaponGroup:'DART',
   ammoVerified:true,ammunitionModel:'SELF',ammoCount:30,
   avgDamageOnHit:dartHit,apr:3,finalTHAC0:dartThac0===null?(close?18:10):dartThac0,
   rangedClosePenaltyAccounted:penaltyKnown})]};
}
function two(s){const f=choose(s);return choose({...s,frame:{...s.frame,tick:101}},f.next)}
let n=0;function test(label,fn){fn();n++;console.log('PASS '+label)}
test('far: dart APR3 beats melee approach cost',()=>{
 const out=two(build());assert.equal(out.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');
 assert.equal(out.toWeaponId,'DART');assert.equal(out.slotIndex,1);
 assert.equal(out.executable,false);assert.equal(out.dispatchAuthorized,false);
});
test('close: confirmed ranged hit penalty makes sword better',()=>{
 const out=two(build({close:true}));assert.equal(out.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');
 assert.equal(out.toWeaponId,'SWORD');assert.equal(out.slotIndex,0);
});
test('close: unverified penalty never assumes darts are safe',()=>{
 const out=two(build({close:true,penaltyKnown:false}));
 assert.equal(out.status,'HOLD_UNRANKABLE_OCCUPIED_WEAPON');
});
test('close: verified alternative effective stats can retain darts',()=>{
 const out=two(build({close:true,penaltyKnown:true,dartHit:8,dartThac0:10}));
 assert.equal(out.status,'KEEP_CURRENT');
});
test('changed range fingerprint starts stabilization again',()=>{
 const far=build();const first=choose(far),second=two(far);
 assert.equal(second.status,'ADVISE_PRIORITY_QUICKSLOT_ONLY');
 const close=build({close:true});close.frame.tick=101;
 assert.equal(choose(close,first.next).status,'HOLD_STABILIZE_TARGET_AND_EQUIPMENT');
});
console.log('PASS DART DISTANCE REGRESSION '+n+'/'+n+' SOURCE ONLY');
