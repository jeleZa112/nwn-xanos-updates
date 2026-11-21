"use strict";
/**
 * BGXAI WEAPON V1 — source-only, fail-closed advisory comparison.
 * Never calls EEex, WeiDU, engine actions, file/network APIs or mutates inputs.
 * Input fields are observations supplied by a separately verified adapter.
 * A mock PASS is NOT gameplay PASS. All resulting choices are NON-EXECUTABLE.
 */
const finite = x => typeof x === "number" && Number.isFinite(x);
const bounded = (x, a, b) => finite(x) && x >= a && x <= b;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const result = (status, extra={}) => ({status, executable:false, ...extra});

function hitChance(thac0, ac) {
  if (!bounded(thac0,-50,100) || !bounded(ac,-50,100)) return null;
  // Simple AD&D approximation: natural 1 misses, natural 20 hits;
  // caller must supply final context-adjusted THAC0, not base stat.
  return clamp((21 - thac0 + ac)/20, .05, .95);
}
function evaluateWeapon(weapon, actor, enemy) {
  const out = {id:weapon?.id ?? null, slot:weapon?.slot ?? null,
               qualified:false, dpr:null, value:null, reasons:[]};
  const reject = why => {out.reasons.push(why);return out;};
  if (!weapon || typeof weapon.id !== "string" || !/^[A-Za-z0-9_]{1,40}$/.test(weapon.id))
    return reject("INVALID_WEAPON_ID");
  if (weapon.usableVerified !== true || weapon.mode !== "MELEE" && weapon.mode !== "RANGED")
    return reject("USABILITY_OR_MODE_UNVERIFIED");
  if (weapon.slot !== "QUICKSLOT" && weapon.slot !== "BACKPACK")
    return reject("ITEM_LOCATION_UNKNOWN");
  if (weapon.slot === "BACKPACK") return reject("BACKPACK_NEEDS_SAFE_EQUIP_ADAPTER");
  if (weapon.ammoVerified !== true && weapon.mode === "RANGED")
    return reject("RANGED_AMMUNITION_UNVERIFIED");
  if (!bounded(weapon.apr,0.5,10) || !bounded(weapon.avgDamageOnHit,0,1000) ||
      !bounded(weapon.finalTHAC0,-50,100))
    return reject("ATTACK_STATS_UNVERIFIED");
  if (weapon.equippedWeaponSlotVerified !== true) return reject("QUICKSLOT_NOT_VERIFIED");
  if (typeof weapon.damageType !== "string" ||
      !["PIERCING","SLASHING","CRUSHING","MISSILE"].includes(weapon.damageType))
    return reject("DAMAGE_TYPE_UNKNOWN");
  if (!bounded(weapon.enchantment,-5,15) || typeof weapon.magical !== "boolean")
    return reject("ENCHANTMENT_UNKNOWN");
  if (weapon.inRange !== true) {
    if (weapon.mode === "MELEE" && actor.pathSafeVerified === true &&
        weapon.canReachWithSafeMove === true) {
      // Movement risk/time must be explicitly represented below.
    } else return reject("OUT_OF_RANGE_OR_UNVERIFIED_PATH");
  }
  if (weapon.mode === "MELEE" && actor.canSustainMelee !== true)
    return reject("MELEE_SURVIVABILITY_UNVERIFIED");
  if (weapon.mode === "RANGED" && actor.nearRangedEnemy === true &&
      weapon.rangedClosePenaltyAccounted !== true)
    return reject("CLOSE_RANGE_THAC0_PENALTY_UNVERIFIED");
  if (!bounded(weapon.switchCost,0,1000) ||
      !bounded(weapon.resourceCost,0,1000) ||
      !bounded(weapon.retaliationRisk,0,1000) ||
      !bounded(weapon.movementCost,0,1000) ||
      !bounded(weapon.extraEffectValue,0,1000))
    return reject("TACTICAL_COSTS_UNVERIFIED");
  const protections = enemy.protections;
  if (!protections || protections.observed !== true ||
      !Array.isArray(protections.immuneDamageTypes) ||
      !bounded(protections.minimumEnchantment,-5,15) ||
      typeof protections.magicalWeaponsBlocked !== "boolean" ||
      typeof protections.normalWeaponsBlocked !== "boolean" ||
      typeof protections.missilesBlocked !== "boolean" ||
      typeof protections.resistance !== "object" || protections.resistance===null)
    return reject("ENEMY_PROTECTIONS_UNVERIFIED");
  if (!bounded(protections.resistance[weapon.damageType],0,1))
    return reject("DAMAGE_RESISTANCE_UNVERIFIED");
  const chance=hitChance(weapon.finalTHAC0,enemy.armorClass);
  if (chance===null) return reject("ENEMY_AC_UNVERIFIED");
  const immune = protections.immuneDamageTypes.includes(weapon.damageType) ||
    weapon.enchantment < protections.minimumEnchantment ||
    (weapon.magical && protections.magicalWeaponsBlocked) ||
    (!weapon.magical && protections.normalWeaponsBlocked) ||
    (weapon.mode==="RANGED" && protections.missilesBlocked);
  // Do not credit on-hit bonus effects against a weapon that cannot hit.
  const effective=immune ? 0 : chance*weapon.avgDamageOnHit*weapon.apr*
    (1-protections.resistance[weapon.damageType]);
  const extra=immune ? 0 : weapon.extraEffectValue;
  out.qualified=true;
  out.hitChance=chance;
  out.penetrates=!immune;
  out.dpr=Math.round(effective*1000)/1000;
  out.value=Math.round((effective+extra-weapon.switchCost-weapon.resourceCost-
                        weapon.retaliationRisk-weapon.movementCost)*1000)/1000;
  if (immune) out.reasons.push("CONFIRMED_PROTECTION_BLOCKS_WEAPON");
  return out;
}
function chooseWeapon(scene) {
  const actor=scene?.actor, enemy=scene?.enemy, weapons=scene?.weapons;
  if (!actor || !enemy || !Array.isArray(weapons) || weapons.length>32)
    return result("HOLD_INVALID_SCENE");
  if (actor.observationVerified!==true || enemy.observationVerified!==true ||
      enemy.hostileVerified!==true || enemy.visibleVerified!==true)
    return result("HOLD_UNVERIFIED_ACTOR_OR_TARGET");
  if (actor.manualOrderActive!==false || actor.currentlyCasting!==false ||
      actor.healingReserved!==false || actor.epsBusy!==false)
    return result("HOLD_PRESERVE_MANUAL_OR_EPS");
  if (actor.originVerified!=="AI") return result("HOLD_UNKNOWN_COMMAND_ORIGIN");
  if (typeof actor.selectedWeaponId!=="string" || !actor.selectedWeaponId)
    return result("HOLD_SELECTED_SLOT_UNVERIFIED");
  if (new Set(weapons.map(w=>w?.id)).size!==weapons.length)
    return result("HOLD_DUPLICATE_WEAPON_IDS");
  const scored=weapons.map(w=>evaluateWeapon(w,actor,enemy));
  const valid=scored.filter(x=>x.qualified);
  const current=valid.find(x=>x.id===actor.selectedWeaponId);
  if (!current) return result("HOLD_CURRENT_WEAPON_UNVERIFIED",{candidates:scored});
  if (!valid.length) return result("HOLD_NO_VERIFIED_CANDIDATES",{candidates:scored});
  // No claim that a new weapon is selected; module may advise a future executor.
  valid.sort((a,b)=>b.value-a.value || (a.id===current.id?-1:b.id===current.id?1:a.id.localeCompare(b.id)));
  const best=valid[0], improvement=best.value-current.value;
  const threshold=Math.max(2,Math.abs(current.value)*0.15);
  const common={currentWeaponId:current.id,bestWeaponId:best.id,
                currentScore:current.value,bestScore:best.value,
                improvement:Math.round(improvement*1000)/1000,
                threshold:Math.round(threshold*1000)/1000,
                candidates:scored};
  if (best.id===current.id || improvement<=threshold)
    return result("KEEP_CURRENT",{...common,reason:"HYSTERESIS_OR_CURRENT_BEST"});
  if (!best.penetrates && best.dpr===0)
    return result("HOLD_NO_EFFECTIVE_ATTACK",{...common});
  return result("RECOMMEND_VERIFIED_QUICKSLOT_SWITCH",{...common,
    reason:"EXPECTED_EFFECTIVE_VALUE_IMPROVES",
    installationRequired:false});
}
module.exports={hitChance,evaluateWeapon,chooseWeapon};
