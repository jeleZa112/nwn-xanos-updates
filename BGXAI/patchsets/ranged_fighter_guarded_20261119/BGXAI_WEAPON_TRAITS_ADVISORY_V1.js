"use strict";
/* BGXAI WEAPON TRAITS v1: SOURCE ONLY. Never issues game actions or edits items.
 * Racial/class/kit/proficiency bonuses come from a verified EET-specific snapshot.
 * The original final weapon THAC0/APR/damage may ALREADY include these bonuses.
 * Do not add them again; unknown provenance -> HOLD. */
const {chooseWeapon}=require("./BGXAI_WEAPON_CHOICE_ADVISORY_V1.js");
const good=(x,min,max)=>typeof x==="number"&&Number.isFinite(x)&&x>=min&&x<=max;
const id=x=>typeof x==="string"&&/^[A-Z0-9_+.-]{1,80}$/.test(x);
const types=new Set(["RACE","CLASS","KIT","PROFICIENCY","STYLE","DUAL","BUFF","FAVORED_ENEMY"]);
const hold=(status,more={})=>({status,executable:false,...more});
function profileOK(actor){
 const p=actor?.traitProfile;
 if(!p||p.verified!==true||!id(p.race)||!id(p.classId)||!id(p.kit)||
    !id(p.modFingerprint)||!id(p.snapshotId)||!Array.isArray(p.activeClasses)||
    p.activeClasses.length<1||p.activeClasses.length>3||
    new Set(p.activeClasses).size!==p.activeClasses.length||
    p.activeClasses.some(x=>!id(x))||
    !["NONE","INACTIVE_PREVIOUS","REACTIVATED"].includes(p.dualState)||
    (!p.activeClasses.includes(p.classId)&&p.dualState==="NONE"&&p.multiclassVerified!==true)||
    !p.proficiencies||typeof p.proficiencies!=="object"||Array.isArray(p.proficiencies)||
    !p.levels||typeof p.levels!=="object"||Array.isArray(p.levels))return false;
 for(const key of p.activeClasses)if(!Number.isInteger(p.levels[key])||p.levels[key]<1||p.levels[key]>50)return false;
 return true;
}
function applyEffects(bonuses,w,p,enemy){
 if(!Array.isArray(bonuses)||bonuses.length>32)return null;
 const seen=new Set();let hit=0,damage=0,apr=0;
 for(const b of bonuses){
  if(!b||!id(b.effectId)||seen.has(b.effectId)||!types.has(b.category)||
     b.observedInGame!==true||b.modFingerprint!==p.modFingerprint||
     b.snapshotId!==p.snapshotId||b.weaponGroup!==w.weaponGroup||
     !good(b.thac0Delta,-30,30)||!good(b.damageDelta,-100,100)||!good(b.aprDelta,-5,5))return null;
  seen.add(b.effectId);
  if(b.category==="RACE"&&b.race!==p.race)return null;
  if(["CLASS","DUAL","KIT","FAVORED_ENEMY"].includes(b.category)){
   if(!id(b.requiredActiveClass)||!p.activeClasses.includes(b.requiredActiveClass))return null;
   if(b.requiredMinLevel!==undefined&&(!Number.isInteger(b.requiredMinLevel)||
      p.levels[b.requiredActiveClass]<b.requiredMinLevel))return null;
  }
  if(b.category==="KIT"&&b.kit!==p.kit)return null;
  if(b.category==="PROFICIENCY"||b.category==="STYLE"){
   const key=b.category==="STYLE"?w.styleGroup:w.weaponGroup;
   if(!id(key)||!Number.isInteger(p.proficiencies[key])||
      b.proficiencyRank!==p.proficiencies[key])return null;
  }
  if(b.category==="FAVORED_ENEMY"&&(enemy?.targetFamilyVerified!==true||
     !id(enemy.targetFamily)||b.targetFamily!==enemy.targetFamily))return null;
  if(b.category==="BUFF"&&b.effectStillActiveVerified!==true)return null;
  hit+=b.thac0Delta;damage+=b.damageDelta;apr+=b.aprDelta;
 }
 return {hit,damage,apr};
}
function normalize(weapon,actor,enemy){
 if(!weapon||!id(weapon.weaponGroup))return {ok:false,reason:"WEAPON_GROUP_UNVERIFIED"};
 const p=actor.traitProfile;
 if(weapon.modFingerprint!==p.modFingerprint||weapon.snapshotId!==p.snapshotId)
  return {ok:false,reason:"BONUS_EVIDENCE_STALE"};
 if(weapon.statBasis==="FINAL_EFFECTIVE"){
  if(weapon.allRaceClassKitProficiencyBonusesIncluded!==true||
     weapon.finalCombatStatsVerified!==true||
     !good(weapon.finalTHAC0,-50,100)||!good(weapon.apr,.5,10)||
     !good(weapon.avgDamageOnHit,0,1000))
   return {ok:false,reason:"FINAL_COMBAT_STATS_UNVERIFIED"};
  return {ok:true,weapon:{...weapon},reason:"BONUSES_ALREADY_IN_FINAL_STATS"};
 }
 if(weapon.statBasis!=="BASE_PLUS_VERIFIED_BONUSES")
  return {ok:false,reason:"BONUS_OR_STAT_SOURCE_UNKNOWN"};
 if(weapon.baseExcludesRaceClassKitProficiencyBonuses!==true||
    weapon.bonusesCompleteForSnapshot!==true||
    !good(weapon.baseTHAC0,-50,100)||!good(weapon.baseAPR,.5,10)||
    !good(weapon.baseDamageOnHit,0,1000))
  return {ok:false,reason:"BASE_MAY_ALREADY_INCLUDE_BONUSES"};
 const sum=applyEffects(weapon.verifiedBonuses,weapon,p,enemy);
 if(!sum)return {ok:false,reason:"TRAIT_BONUS_INAPPLICABLE_OR_UNVERIFIED"};
 const finalTHAC0=weapon.baseTHAC0+sum.hit;
 const avgDamageOnHit=weapon.baseDamageOnHit+sum.damage;
 const apr=weapon.baseAPR+sum.apr;
 if(!good(finalTHAC0,-50,100)||!good(avgDamageOnHit,0,1000)||!good(apr,.5,10))
   return {ok:false,reason:"BONUS_TOTAL_INVALID"};
 return {ok:true,weapon:{...weapon,finalTHAC0,avgDamageOnHit,apr},
         reason:"VERIFIED_TRAITS_COMPOSED_ONCE"};
}
function chooseWeaponWithTraits(scene){
 if(!profileOK(scene?.actor))return hold("HOLD_TRAIT_PROFILE_UNVERIFIED");
 if(!scene.enemy||!Array.isArray(scene.weapons)||scene.weapons.length>32)
  return hold("HOLD_TRAIT_SCENE_INVALID");
 const prepared=scene.weapons.map(w=>normalize(w,scene.actor,scene.enemy));
 // An unverified quickslot may be superior, so do not rank known subsets.
 const blocked=prepared.findIndex((x,i)=>!x.ok&&scene.weapons[i]?.slot==="QUICKSLOT");
 if(blocked>=0)return hold("HOLD_WEAPON_TRAIT_EVIDENCE_INCOMPLETE",{
  weapon:scene.weapons[blocked]?.id??null,reason:prepared[blocked].reason});
 const candidates=prepared.map((x,i)=>x.ok?x.weapon:{...scene.weapons[i],usableVerified:false});
 const answer=chooseWeapon({...scene,weapons:candidates});
 return {...answer,traitAccounting:"EET_VERIFIED_NO_DOUBLE_COUNT",executable:false};
}
module.exports={profileOK,applyEffects,normalize,chooseWeaponWithTraits};
