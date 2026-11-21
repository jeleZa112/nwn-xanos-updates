"use strict";
const assert=require("node:assert/strict");
const {choosePriorityWeapon:choose}=require("./BGXAI_WEAPON_PRIORITY_ENGINE_V2.js");
let passed=0;
function test(label,fn){fn();passed++;console.log("PASS",label)}
const prot=()=>({snapshotId:"SNAP1",observed:true,immuneDamageTypes:[],
 minimumEnchantment:0,magicalWeaponsBlocked:false,normalWeaponsBlocked:false,
 missilesBlocked:false,resistance:{PIERCING:0,SLASHING:0,CRUSHING:0,MISSILE:0}});
function sword(id,idx,extra={}){return {id,quickslotIndex:idx,slot:"QUICKSLOT",
 mode:"MELEE",usableVerified:true,equippedWeaponSlotVerified:true,inRange:true,
 finalTHAC0:10,apr:2,avgDamageOnHit:7,damageType:"SLASHING",
 enchantment:1,magical:true,switchCost:0,resourceCost:0,retaliationRisk:0,
 movementCost:0,extraEffectValue:0,combatCostsVerified:true,
 statBasis:"FINAL_EFFECTIVE",allRaceClassKitProficiencyBonusesIncluded:true,
 finalCombatStatsVerified:true,modFingerprint:"EET",snapshotId:"SNAP1",
 weaponGroup:"LONG_SWORD",...extra};}
function scene(extra={}){
 const a={actorId:"KHALID",area:"AR001",currentTargetId:"EN1",handsMode:"SINGLE",
 observationVerified:true,manualOrderActive:false,currentlyCasting:false,
 healingReserved:false,epsBusy:false,originVerified:"AI",
 selectedWeaponId:"SWORD",pathSafeVerified:true,canSustainMelee:true,nearRangedEnemy:false,
 traitProfile:{verified:true,race:"HUMAN",classId:"FIGHTER",kit:"NONE",modFingerprint:"EET",
 snapshotId:"SNAP1",activeClasses:["FIGHTER"],levels:{FIGHTER:8},dualState:"NONE",
 proficiencies:{LONG_SWORD:2,LONG_BOW:1}}};
 const e={enemyId:"EN1",area:"AR001",observationVerified:true,
 hostileVerified:true,visibleVerified:true,armorClass:0,protections:prot()};
 return {frame:{tick:100,area:"AR001",actorId:"KHALID",enemyId:"EN1",
 snapshotId:"SNAP1",equipmentFingerprint:"EQUIP1",protectionFingerprint:"PROT1",
 combatFingerprint:"COMBAT1",selectedWeaponId:"SWORD",captureContract:"COMPLETE_EFFECTIVE_SNAPSHOT",
 completeEquipmentObserved:true,completeQuiverObserved:true,completeTargetObserved:true},
 actor:a,enemy:e,quickslotIds:["SWORD","MACE",null,null],
 weapons:[sword("SWORD",0),sword("MACE",1,{avgDamageOnHit:10,apr:3,damageType:"CRUSHING"})],
 ...extra};}
function two(s){const first=choose(s),second=choose({...s,frame:{...s.frame,tick:s.frame.tick+1}},first.next);return {first,second}}
test("stable target + full loadout advises superior melee quickslot",()=>{
 const x=two(scene());assert.equal(x.first.status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
 assert.equal(x.second.status,"ADVISE_PRIORITY_QUICKSLOT_ONLY");
 assert.equal(x.second.toWeaponId,"MACE");assert.equal(x.second.slotIndex,1);
 assert.equal(x.second.executable,false);assert.equal(x.second.dispatchAuthorized,false);
});
test("one occupied slot is enough to keep current",()=>{
 const s=scene({quickslotIds:["SWORD",null,null,null],weapons:[sword("SWORD",0)]});
 assert.equal(two(s).second.status,"KEEP_CURRENT");
});
test("missing occupied quickslot item cannot be silently omitted",()=>{
 const s=scene({weapons:[sword("SWORD",0)]});assert.equal(choose(s).status,"HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE");
});
test("partial inventory observation rejected",()=>{
 const s=scene();s.frame.completeEquipmentObserved=false;
 assert.equal(choose(s).status,"HOLD_CAPTURE_CONTRACT_UNVERIFIED");
});
test("unknown used slot ordinal rejected",()=>{
 const s=scene();s.weapons[1].quickslotIndex=2;
 assert.equal(choose(s).status,"HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE");
});
test("duplicate inventory slot IDs rejected",()=>{
 const s=scene();s.quickslotIds[1]="SWORD";
 assert.equal(choose(s).status,"HOLD_AMBIGUOUS_QUICKSLOT");
});
test("target identity mismatch blocks regardless of damage",()=>{
 const s=scene();s.enemy.enemyId="ALLY";
 assert.equal(choose(s).status,"HOLD_TARGET_OR_SELECTION_CHANGED");
});
test("area mismatch blocks cross-area target",()=>{
 const s=scene();s.actor.area="AR002";
 assert.equal(choose(s).status,"HOLD_TARGET_OR_SELECTION_CHANGED");
});
test("stale enemy resistance snapshot blocks",()=>{
 const s=scene();s.enemy.protections.snapshotId="OTHER";
 assert.equal(choose(s).status,"HOLD_STALE_ENEMY_PROTECTIONS");
});
test("stale class or kit profile blocks",()=>{
 const s=scene();s.actor.traitProfile.snapshotId="OTHER";
 assert.equal(choose(s).status,"HOLD_STALE_TRAIT_PROFILE");
});
test("manual / EPS / casting / healing blocks",()=>{
 for(const p of ["manualOrderActive","epsBusy","currentlyCasting","healingReserved"]){
   const s=scene();s.actor[p]=true;
   assert.equal(choose(s).status,"HOLD_PRESERVE_MANUAL_OR_EPS");
 }
});
test("unknown command origin blocks",()=>{
 const s=scene();s.actor.originVerified="UNKNOWN";
 assert.equal(choose(s).status,"HOLD_PRESERVE_MANUAL_OR_EPS");
});
test("unaccounted equipment and switching costs block",()=>{
 const s=scene();s.weapons[1].combatCostsVerified=false;
 assert.equal(choose(s).status,"HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE");
});
test("point blank bow must include penalty",()=>{
 const s=scene();s.actor.nearRangedEnemy=true;
 s.weapons[1]=sword("MACE",1,{mode:"RANGED",damageType:"MISSILE",weaponGroup:"LONG_BOW",
 avgDamageOnHit:25,ammoVerified:true,ammunitionModel:"QUIVER",ammoCount:50,ammoResRef:"AROW01",
 rangedClosePenaltyAccounted:false});
 assert.equal(two(s).second.status,"HOLD_UNRANKABLE_OCCUPIED_WEAPON");
});
test("empty quiver cannot support bow choice",()=>{
 const s=scene();s.weapons[1]=sword("MACE",1,{mode:"RANGED",damageType:"MISSILE",
 ammoVerified:true,ammunitionModel:"QUIVER",ammoCount:0,ammoResRef:"AROW01"});
 assert.equal(choose(s).status,"HOLD_AMMO_OR_THROWABLE_UNVERIFIED");
});
test("verified self-ammo thrown weapon is accepted",()=>{
 const s=scene();s.weapons[1]=sword("MACE",1,{mode:"RANGED",damageType:"MISSILE",
 ammoVerified:true,ammunitionModel:"SELF",ammoCount:12,avgDamageOnHit:20,apr:3});
 assert.equal(two(s).second.status,"ADVISE_PRIORITY_QUICKSLOT_ONLY");
});
test("duals require aggregate effective APR and hit",()=>{
 const s=scene();s.actor.handsMode="DUAL";
 assert.equal(choose(s).status,"HOLD_DUAL_WIELD_COMBAT_STATS_UNKNOWN");
 s.weapons.forEach(w=>w.dualWieldStatsVerified=true);
 assert.equal(two(s).second.status,"ADVISE_PRIORITY_QUICKSLOT_ONLY");
});
test("a protection-immune sword must lose to crushing",()=>{
 const s=scene();s.enemy.protections.immuneDamageTypes=["SLASHING"];
 assert.equal(two(s).second.toWeaponId,"MACE");
});
test("unknown alternative final stats blocks ranking all slots",()=>{
 const s=scene();s.weapons[1].statBasis="UNKNOWN";
 assert.equal(two(s).second.status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("small benefit below hysteresis keeps current",()=>{
 const s=scene();s.weapons[1].apr=2;s.weapons[1].avgDamageOnHit=7.1;
 assert.equal(two(s).second.status,"KEEP_CURRENT");
});
test("target or loadout change restarts stabilization",()=>{
 const s=scene(),a=choose(s);const next=scene();next.frame.tick=101;
 next.enemy.enemyId="EN2";next.frame.enemyId="EN2";next.actor.currentTargetId="EN2";
 assert.equal(choose(next,a.next).status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
});
test("new EEex capture ID each frame still allows stable loadout",()=>{
 const s=scene(),a=choose(s),next=scene();next.frame.tick=101;
 next.frame.snapshotId="SNAP2";next.actor.traitProfile.snapshotId="SNAP2";
 next.enemy.protections.snapshotId="SNAP2";
 next.weapons.forEach(w=>w.snapshotId="SNAP2");
 assert.equal(choose(next,a.next).status,"ADVISE_PRIORITY_QUICKSLOT_ONLY");
});
test("changed protections or actual combat stats restart stability",()=>{
 const s=scene(),a=choose(s),e=scene();e.frame.tick=101;
 e.frame.protectionFingerprint="PROT2";
 assert.equal(choose(e,a.next).status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
 e.frame.protectionFingerprint="PROT1";e.frame.combatFingerprint="COMBAT2";
 assert.equal(choose(e,a.next).status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
});
test("repeated tick / excessively old observation restarts stabilization",()=>{
 const s=scene(),a=choose(s);
 assert.equal(choose(s,a.next).status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
 const later=scene();later.frame.tick=140;
 assert.equal(choose(later,a.next).status,"HOLD_STABILIZE_TARGET_AND_EQUIPMENT");
});
test("post-advice cooldown avoids flip-flop",()=>{
 const s=scene(),a=choose(s);const b=scene();b.frame.tick=101;
 const advised=choose(b,a.next);assert.equal(advised.status,"ADVISE_PRIORITY_QUICKSLOT_ONLY");
 const c=scene();c.frame.tick=102;
 assert.equal(choose(c,advised.next).status,"HOLD_ADVISORY_SWITCH_COOLDOWN");
});
test("pure functional, immutable inputs and never claims game switch",()=>{
 const s=scene(),before=JSON.stringify(s);const out=two(s);
 assert.equal(JSON.stringify(s),before);
 assert.equal(out.second.executable,false);assert.equal(out.second.dispatchAuthorized,false);
 assert.equal(out.second.next.lastAdviceTick,101);
});
console.log("PASS TOTAL",passed,"/",passed,"SOURCE ONLY; NO EET GAMEPLAY");