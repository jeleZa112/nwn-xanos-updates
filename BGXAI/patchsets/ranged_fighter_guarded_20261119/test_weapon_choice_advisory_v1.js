"use strict";
const assert=require("node:assert/strict");
const {hitChance,evaluateWeapon,chooseWeapon}=require("./BGXAI_WEAPON_CHOICE_ADVISORY_V1.js");
let count=0;
function test(name,fn){fn(); count++; console.log("PASS "+name)}
const actor=()=>({
 observationVerified:true,manualOrderActive:false,currentlyCasting:false,
 healingReserved:false,epsBusy:false,originVerified:"AI",
 selectedWeaponId:"MACE1",pathSafeVerified:true,canSustainMelee:true,nearRangedEnemy:false
});
const enemy=()=>({
 observationVerified:true,hostileVerified:true,visibleVerified:true,armorClass:0,
 protections:{
  observed:true,immuneDamageTypes:[],minimumEnchantment:0,
  magicalWeaponsBlocked:false,normalWeaponsBlocked:false,missilesBlocked:false,
  resistance:{PIERCING:0,SLASHING:0,CRUSHING:0,MISSILE:0}
 }
});
const weapon=(id,delta={})=>({
 id,slot:"QUICKSLOT",mode:"MELEE",usableVerified:true,equippedWeaponSlotVerified:true,
 inRange:true,canReachWithSafeMove:false,finalTHAC0:10,apr:2,
 avgDamageOnHit:7,damageType:"CRUSHING",enchantment:1,magical:true,
 switchCost:0,resourceCost:0,retaliationRisk:0,movementCost:0,extraEffectValue:0,...delta
});
const scene=(newWeapon, delta={})=>({actor:actor(),enemy:enemy(),
 weapons:[weapon("MACE1"),newWeapon],...delta});
function rec(s){return chooseWeapon(s)}
test("AD&D hit chance bounds and changed AC",()=>{
 assert.equal(hitChance(20,-15),.05);assert.equal(hitChance(-10,20),.95);
 assert.equal(hitChance(10,0),.55);assert.equal(hitChance(NaN,0),null);
});
test("higher useful APR can beat per-hit damage",()=>{
 const s=scene(weapon("SWORD", {avgDamageOnHit:6,apr:4}));
 assert.equal(rec(s).status,"RECOMMEND_VERIFIED_QUICKSLOT_SWITCH");
 assert.equal(rec(s).bestWeaponId,"SWORD");
});
test("do not select big damage but magically blocked",()=>{
 const s=scene(weapon("PLUS3",{avgDamageOnHit:100,enchantment:3}),{
 enemy:{...enemy(),protections:{...enemy().protections,magicalWeaponsBlocked:true}}
 });
 assert.equal(rec(s).status,"HOLD_NO_EFFECTIVE_ATTACK");
 const x=rec(s).candidates.find(v=>v.id==="PLUS3");
 assert.equal(x.dpr,0);assert.deepEqual(x.reasons,["CONFIRMED_PROTECTION_BLOCKS_WEAPON"]);
});
test("enchantment threshold ignores +1 and chooses +3",()=>{
 const s=scene(weapon("PLUS3",{avgDamageOnHit:10,enchantment:3}),{
 enemy:{...enemy(),protections:{...enemy().protections,minimumEnchantment:3}}
 });
 assert.equal(rec(s).bestWeaponId,"PLUS3");
 assert.equal(rec(s).status,"RECOMMEND_VERIFIED_QUICKSLOT_SWITCH");
 assert.equal(rec(s).candidates[0].dpr,0);
});
test("damage type immunity distinguishes crush and slash",()=>{
 const s=scene(weapon("SWORD",{avgDamageOnHit:7,damageType:"SLASHING"}),{
 enemy:{...enemy(),protections:{...enemy().protections,immuneDamageTypes:["CRUSHING"]}}
 });
 assert.equal(rec(s).bestWeaponId,"SWORD");
});
test("resistance affects expected value",()=>{
 const s=scene(weapon("SLASH",{avgDamageOnHit:6,damageType:"SLASHING"}),{
 enemy:{...enemy(),protections:{...enemy().protections,resistance:{...enemy().protections.resistance,CRUSHING:.8}}}
 });
 assert.equal(rec(s).status,"RECOMMEND_VERIFIED_QUICKSLOT_SWITCH");
});
test("retain current when advantage below hysteresis",()=>{
 const s=scene(weapon("SLASH",{avgDamageOnHit:7.1,damageType:"SLASHING"}));
 assert.equal(rec(s).status,"KEEP_CURRENT");
});
test("unknown protections fail closed",()=>{
 const e=enemy();delete e.protections.observed;
 assert.equal(rec(scene(weapon("SLASH"),{enemy:e})).status,"HOLD_CURRENT_WEAPON_UNVERIFIED");
});
test("backpack weapon never treated as available quickslot",()=>{
 const s=scene(weapon("SWORD",{avgDamageOnHit:20,slot:"BACKPACK"}));
 assert.equal(rec(s).status,"KEEP_CURRENT");
 assert.equal(rec(s).candidates.find(x=>x.id==="SWORD").reasons[0],"BACKPACK_NEEDS_SAFE_EQUIP_ADAPTER");
});
test("ranged ammo must be verified",()=>{
 const s=scene(weapon("BOW",{mode:"RANGED",ammoVerified:false,avgDamageOnHit:15}));
 assert.equal(rec(s).status,"KEEP_CURRENT");
});
test("point blank penalty cannot be guessed",()=>{
 const a={...actor(),nearRangedEnemy:true};
 const s=scene(weapon("BOW",{mode:"RANGED",ammoVerified:true,avgDamageOnHit:100}),{actor:a});
 assert.equal(rec(s).status,"KEEP_CURRENT");
 assert.equal(rec(s).candidates[1].reasons[0],"CLOSE_RANGE_THAC0_PENALTY_UNVERIFIED");
});
test("point blank with verified penalty uses adjusted THAC0",()=>{
 const a={...actor(),nearRangedEnemy:true};
 const s=scene(weapon("BOW",{mode:"RANGED",ammoVerified:true,avgDamageOnHit:6,apr:2,finalTHAC0:18,rangedClosePenaltyAccounted:true}),{actor:a});
 assert.equal(rec(s).status,"KEEP_CURRENT");
});
test("melee candidate requires survivability for fragile hybrid",()=>{
 const s=scene(weapon("SWORD",{avgDamageOnHit:100}),{actor:{...actor(),canSustainMelee:false}});
 assert.equal(rec(s).status,"HOLD_CURRENT_WEAPON_UNVERIFIED");
});
test("cannot recommend unsafe melee route",()=>{
 const s=scene(weapon("SWORD",{avgDamageOnHit:100,inRange:false,canReachWithSafeMove:true}),{actor:{...actor(),pathSafeVerified:false}});
 assert.equal(rec(s).status,"KEEP_CURRENT");
});
test("manual, casting, healing, EPS and unknown origin hold",()=>{
 for(const prop of ["manualOrderActive","currentlyCasting","healingReserved","epsBusy"]){
  const s=scene(weapon("SWORD",{avgDamageOnHit:100}),{actor:{...actor(),[prop]:true}});
  assert.equal(rec(s).status,"HOLD_PRESERVE_MANUAL_OR_EPS");
 }
 assert.equal(rec(scene(weapon("SWORD"),{actor:{...actor(),originVerified:"UNKNOWN"}})).status,"HOLD_UNKNOWN_COMMAND_ORIGIN");
});
test("nonparty target proof mandatory",()=>{
 assert.equal(rec(scene(weapon("SWORD"),{enemy:{...enemy(),hostileVerified:false}})).status,"HOLD_UNVERIFIED_ACTOR_OR_TARGET");
});
test("unknown duplicate / no selection fail closed",()=>{
 assert.equal(rec(scene(weapon("MACE1"))).status,"HOLD_DUPLICATE_WEAPON_IDS");
 assert.equal(rec(scene(weapon("SWORD"),{actor:{...actor(),selectedWeaponId:"GHOST"}})).status,"HOLD_CURRENT_WEAPON_UNVERIFIED");
});
test("no hidden mutations and no game executor",()=>{
 const s=scene(weapon("SWORD",{avgDamageOnHit:20}));
 const before=JSON.stringify(s),out=rec(s);
 assert.equal(out.executable,false);
 assert.equal(out.status,"RECOMMEND_VERIFIED_QUICKSLOT_SWITCH");
 assert.equal(JSON.stringify(s),before);
});
console.log("PASS TOTAL "+count+" / "+count+" (OFFLINE ONLY)");
