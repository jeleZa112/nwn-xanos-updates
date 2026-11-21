"use strict";
const assert=require("node:assert/strict");
const {chooseWeaponWithTraits}=require("./BGXAI_WEAPON_TRAITS_ADVISORY_V1.js");
let passed=0;
function test(name,fn){fn();passed++;console.log("PASS",name);}
const profile=()=>({verified:true,race:"ELF",classId:"FIGHTER",kit:"BERSERKER",
 modFingerprint:"EET_SCS_35_21",snapshotId:"SNAP_1",activeClasses:["FIGHTER"],
 levels:{FIGHTER:8},dualState:"NONE",proficiencies:{LONG_SWORD:2,LONG_BOW:1,SLING:0,TWO_WEAPON:2}});
const actor=()=>({traitProfile:profile(),observationVerified:true,manualOrderActive:false,
 currentlyCasting:false,healingReserved:false,epsBusy:false,originVerified:"AI",
 selectedWeaponId:"SWORD",pathSafeVerified:true,canSustainMelee:true,nearRangedEnemy:false});
const enemy=()=>({observationVerified:true,hostileVerified:true,visibleVerified:true,armorClass:0,
 targetFamily:"UNDEAD",targetFamilyVerified:true,protections:{observed:true,
 immuneDamageTypes:[],minimumEnchantment:0,magicalWeaponsBlocked:false,
 normalWeaponsBlocked:false,missilesBlocked:false,
 resistance:{PIERCING:0,SLASHING:0,CRUSHING:0,MISSILE:0}}});
const weapon=(id,extra={})=>({id,slot:"QUICKSLOT",mode:"MELEE",usableVerified:true,
 equippedWeaponSlotVerified:true,inRange:true,finalTHAC0:10,apr:2,avgDamageOnHit:7,
 damageType:"SLASHING",enchantment:1,magical:true,switchCost:0,resourceCost:0,
 retaliationRisk:0,movementCost:0,extraEffectValue:0,statBasis:"FINAL_EFFECTIVE",
 allRaceClassKitProficiencyBonusesIncluded:true,finalCombatStatsVerified:true,
 modFingerprint:"EET_SCS_35_21",snapshotId:"SNAP_1",weaponGroup:"LONG_SWORD",...extra});
const effect=(category,effectId,group,extra={})=>({category,effectId,weaponGroup:group,
 observedInGame:true,modFingerprint:"EET_SCS_35_21",snapshotId:"SNAP_1",
 thac0Delta:0,damageDelta:0,aprDelta:0,...extra});
const base=(id,group,bonuses,extra={})=>weapon(id,{weaponGroup:group,
 statBasis:"BASE_PLUS_VERIFIED_BONUSES",baseExcludesRaceClassKitProficiencyBonuses:true,
 bonusesCompleteForSnapshot:true,baseTHAC0:10,baseAPR:2,baseDamageOnHit:7,
 verifiedBonuses:bonuses,...extra});
const sc=(alternative,a=actor(),e=enemy())=>({actor:a,enemy:e,weapons:[weapon("SWORD"),alternative]});
const choose=s=>chooseWeaponWithTraits(s);
test("final effective stats contain racial bonus already: unchanged THAC0",()=>{
 const s=sc(weapon("BOW",{mode:"RANGED",ammoVerified:true,weaponGroup:"LONG_BOW",
  finalTHAC0:10,damageType:"MISSILE",
  verifiedBonuses:[effect("RACE","ELF_BOW","LONG_BOW",{race:"ELF",thac0Delta:-1})]}));
 const r=choose(s);assert.equal(r.status,"KEEP_CURRENT");
 assert.equal(r.candidates.find(c=>c.id==="BOW").hitChance,.55);
});
test("elf longbow +1 hit and fighter APR from verified contributions",()=>{
 const b=base("BOW","LONG_BOW",[
  effect("RACE","ELF_LONG_BOW","LONG_BOW",{race:"ELF",thac0Delta:-1}),
  effect("CLASS","FIGHTER_LEVEL8","LONG_BOW",{requiredActiveClass:"FIGHTER",requiredMinLevel:7,aprDelta:.5})
 ],{mode:"RANGED",ammoVerified:true,damageType:"MISSILE",baseDamageOnHit:9});
 const r=choose(sc(b));assert.equal(r.status,"RECOMMEND_VERIFIED_QUICKSLOT_SWITCH");
 assert.equal(r.bestWeaponId,"BOW");assert.equal(r.candidates[1].hitChance,.6);
});
test("different race cannot inherit elf bonus",()=>{
 const b=base("BOW","LONG_BOW",[effect("RACE","ELF_BONUS","LONG_BOW",{race:"ELF",thac0Delta:-1})],
  {mode:"RANGED",ammoVerified:true,damageType:"MISSILE"});
 const s=sc(b,{...actor(),traitProfile:{...profile(),race:"HALFLING"}});
 assert.equal(choose(s).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("halfling sling racial hit bonus and observed pips are usable",()=>{
 const b=base("SLING","SLING",[
  effect("RACE","HALFLING_SLING","SLING",{race:"HALFLING",thac0Delta:-1}),
  effect("PROFICIENCY","SLING_PIP","SLING",{proficiencyRank:1,damageDelta:2})
 ],{mode:"RANGED",ammoVerified:true,damageType:"MISSILE",baseAPR:3});
 const a={...actor(),traitProfile:{...profile(),race:"HALFLING",
  proficiencies:{...profile().proficiencies,SLING:1}}};
 assert.equal(choose(sc(b,a)).bestWeaponId,"SLING");
});
test("archer kit bonus only for correct active ranger and level",()=>{
 const b=base("BOW","LONG_BOW",[effect("KIT","ARCHER_L12","LONG_BOW",
  {kit:"ARCHER",requiredActiveClass:"RANGER",requiredMinLevel:12,thac0Delta:-4,damageDelta:4})],
  {mode:"RANGED",ammoVerified:true,damageType:"MISSILE",baseDamageOnHit:8});
 const p={...profile(),classId:"RANGER",kit:"ARCHER",levels:{RANGER:12},activeClasses:["RANGER"]};
 assert.equal(choose(sc(b,{...actor(),traitProfile:p})).bestWeaponId,"BOW");
 assert.equal(choose(sc(b)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
 const low={...p,levels:{RANGER:7}};
 assert.equal(choose(sc(b,{...actor(),traitProfile:low})).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("grandmastery bonus not applied to 2-pip fighter",()=>{
 const b=base("MACE","LONG_SWORD",[effect("PROFICIENCY","GRANDMASTER","LONG_SWORD",
  {proficiencyRank:5,damageDelta:5,aprDelta:1})]);
 assert.equal(choose(sc(b)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("two-weapon style uses style proficiency rather than sword proficiency",()=>{
 const b=base("DUAL","LONG_SWORD",[effect("STYLE","TWO_WEAPON_PIPS","LONG_SWORD",
  {proficiencyRank:2,thac0Delta:-2})],{styleGroup:"TWO_WEAPON",baseDamageOnHit:20});
 assert.equal(choose(sc(b)).bestWeaponId,"DUAL");
});
test("fighter bonus suspended during inactive fighter->mage dual",()=>{
 const b=base("MACE","LONG_SWORD",[effect("CLASS","FIGHTER_BONUS","LONG_SWORD",
   {requiredActiveClass:"FIGHTER",damageDelta:7})]);
 const p={...profile(),classId:"MAGE",activeClasses:["MAGE"],levels:{MAGE:6},dualState:"INACTIVE_PREVIOUS"};
 assert.equal(choose(sc(b,{...actor(),traitProfile:p})).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("fighter bonus restored by verified dual reactivation",()=>{
 const b=base("MACE","LONG_SWORD",[effect("CLASS","FIGHTER_BONUS","LONG_SWORD",
  {requiredActiveClass:"FIGHTER",damageDelta:7})]);
 const p={...profile(),classId:"MAGE",activeClasses:["MAGE","FIGHTER"],
  levels:{MAGE:14,FIGHTER:13},dualState:"REACTIVATED"};
 assert.equal(choose(sc(b,{...actor(),traitProfile:p})).bestWeaponId,"MACE");
});
test("fighter/mage multiclass only accepts verified active fighter",()=>{
 const b=base("MACE","LONG_SWORD",[effect("CLASS","FIGHTER_BONUS","LONG_SWORD",
  {requiredActiveClass:"FIGHTER",damageDelta:7})]);
 const p={...profile(),classId:"FIGHTER_MAGE",multiclassVerified:true,
  activeClasses:["FIGHTER","MAGE"],levels:{FIGHTER:9,MAGE:8},dualState:"NONE"};
 assert.equal(choose(sc(b,{...actor(),traitProfile:p})).bestWeaponId,"MACE");
});
test("ranger favored enemy bonus requires verified enemy identity",()=>{
 const b=base("MACE","LONG_SWORD",[effect("FAVORED_ENEMY","RANGER_UNDEAD","LONG_SWORD",
  {requiredActiveClass:"RANGER",targetFamily:"UNDEAD",thac0Delta:-3,damageDelta:6})]);
 const p={...profile(),classId:"RANGER",activeClasses:["RANGER"],levels:{RANGER:12}};
 const a={...actor(),traitProfile:p};
 assert.equal(choose(sc(b,a)).bestWeaponId,"MACE");
 assert.equal(choose(sc(b,a,{...enemy(),targetFamilyVerified:false})).status,
  "HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
 assert.equal(choose(sc(b,a,{...enemy(),targetFamily:"DRAGON"})).status,
  "HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("buff only if still active at exact snapshot",()=>{
 const b=base("MACE","LONG_SWORD",[effect("BUFF","HASTE","LONG_SWORD",
  {aprDelta:1,effectStillActiveVerified:false})]);
 assert.equal(choose(sc(b)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("unverified base already containing modifiers is not added to",()=>{
 const b=base("MACE","LONG_SWORD",[],{baseExcludesRaceClassKitProficiencyBonuses:false});
 assert.equal(choose(sc(b)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("stale item snapshot, duplicate effect IDs and incomplete list hold",()=>{
 const b=base("MACE","LONG_SWORD",[],{snapshotId:"OLD"});
 assert.equal(choose(sc(b)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
 const eff=effect("RACE","ONE","LONG_SWORD",{race:"ELF",damageDelta:1});
 const repeated=base("MACE","LONG_SWORD",[eff,eff]);
 assert.equal(choose(sc(repeated)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
 const incomplete=base("MACE","LONG_SWORD",[],{bonusesCompleteForSnapshot:false});
 assert.equal(choose(sc(incomplete)).status,"HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE");
});
test("missing class or kit profile holds, no racial guesses",()=>{
 const s=sc(weapon("MACE"));delete s.actor.traitProfile.kit;
 assert.equal(choose(s).status,"HOLD_TRAIT_PROFILE_UNVERIFIED");
});
test("source only, never edits the input or issues executable commands",()=>{
 const s=sc(weapon("MACE",{avgDamageOnHit:18}));const before=JSON.stringify(s);
 const out=choose(s);assert.equal(out.executable,false);assert.equal(JSON.stringify(s),before);
});
console.log("PASS TRAITS "+passed+"/"+passed+" SOURCE ONLY");
