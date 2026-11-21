"use strict";
/**
 * BGXAI priority weapon selection V2. READ-ONLY advice; NEVER a game executor.
 * Composes the existing V1 + verified-traits scorer, rather than replacing it.
 * The full loadout, target, item stats and manual/EPS provenance MUST originate
 * in a separately audited game adapter; a caller-set `verified` is NOT proof.
 * Synthetic tests demonstrate logic, NOT real EEex evidence or live behavior.
 */
const {chooseWeaponWithTraits} = require("./BGXAI_WEAPON_TRAITS_ADVISORY_V1.js");
const validId = x => typeof x === "string" && /^[A-Za-z0-9_+.-]{1,80}$/.test(x);
const tickOK = x => Number.isSafeInteger(x) && x >= 0;
const hold = (status, extra={}) => ({status, executable:false, dispatchAuthorized:false, ...extra});
function signature(scene) {
  const f=scene.frame, a=scene.actor, e=scene.enemy;
  return [f.area,f.actorId,f.enemyId,f.snapshotId,a.selectedWeaponId,
          a.traitProfile.modFingerprint,
          scene.quickslotIds.map(x=>x===null?"-":x).join("/")].join("|");
}
function validate(scene) {
  if (!scene || !scene.frame || !scene.actor || !scene.enemy ||
      !Array.isArray(scene.weapons) || !Array.isArray(scene.quickslotIds) ||
      scene.quickslotIds.length!==4) return "HOLD_INCOMPLETE_LOADOUT";
  const {frame:f,actor:a,enemy:e}=scene;
  if (!tickOK(f.tick) || !validId(f.snapshotId) || !validId(f.area) ||
      !validId(f.actorId) || !validId(f.enemyId) || f.actorId===f.enemyId ||
      f.captureContract!=="COMPLETE_EFFECTIVE_SNAPSHOT" ||
      f.completeEquipmentObserved!==true || f.completeQuiverObserved!==true ||
      f.completeTargetObserved!==true) return "HOLD_CAPTURE_CONTRACT_UNVERIFIED";
  if (a.actorId!==f.actorId || e.enemyId!==f.enemyId ||
      a.area!==f.area || e.area!==f.area ||
      a.currentTargetId!==f.enemyId ||
      a.selectedWeaponId!==f.selectedWeaponId ||
      !validId(a.selectedWeaponId)) return "HOLD_TARGET_OR_SELECTION_CHANGED";
  if (!a.traitProfile || a.traitProfile.snapshotId!==f.snapshotId ||
      !validId(a.traitProfile.modFingerprint)) return "HOLD_STALE_TRAIT_PROFILE";
  if (!e.protections || e.protections.snapshotId!==f.snapshotId ||
      e.protections.observed!==true) return "HOLD_STALE_ENEMY_PROTECTIONS";
  if (a.handsMode!=="SINGLE" && a.handsMode!=="DUAL" &&
      a.handsMode!=="TWO_HANDED") return "HOLD_HANDS_CONFIGURATION_UNKNOWN";
  if (a.manualOrderActive!==false || a.epsBusy!==false ||
      a.healingReserved!==false || a.currentlyCasting!==false ||
      a.originVerified!=="AI") return "HOLD_PRESERVE_MANUAL_OR_EPS";
  const seen=new Set(); let occupied=0;
  for (let slot=0; slot<4; slot++) {
    const id=scene.quickslotIds[slot];
    if (id===null) continue;
    if (!validId(id) || seen.has(id)) return "HOLD_AMBIGUOUS_QUICKSLOT";
    seen.add(id); occupied++;
    const w=scene.weapons.filter(w=>w && w.id===id);
    if (w.length!==1 || w[0].quickslotIndex!==slot ||
        w[0].slot!=="QUICKSLOT" || w[0].snapshotId!==f.snapshotId ||
        w[0].modFingerprint!==a.traitProfile.modFingerprint ||
        w[0].usableVerified!==true || w[0].equippedWeaponSlotVerified!==true ||
        w[0].combatCostsVerified!==true ||
        w[0].finalCombatStatsVerified!==true && w[0].statBasis==="FINAL_EFFECTIVE")
      return "HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE";
    // Effective APR / damage of both hands must be aggregated and verified.
    if (a.handsMode==="DUAL" && w[0].mode==="MELEE" &&
        w[0].dualWieldStatsVerified!==true)
      return "HOLD_DUAL_WIELD_COMBAT_STATS_UNKNOWN";
    if (w[0].mode==="RANGED") {
      if (w[0].ammoVerified!==true ||
          !["QUIVER","SELF"].includes(w[0].ammunitionModel) ||
          !Number.isSafeInteger(w[0].ammoCount) || w[0].ammoCount<1 ||
          (w[0].ammunitionModel==="QUIVER" && !validId(w[0].ammoResRef)))
        return "HOLD_AMMO_OR_THROWABLE_UNVERIFIED";
    }
  }
  if (!occupied || scene.weapons.length!==occupied ||
      seen.size!==scene.weapons.length || !seen.has(a.selectedWeaponId))
    return "HOLD_INCOMPLETE_LOADOUT";
  return null;
}
/** Stateless, deterministic; previous is an advisory-only stabilization token.
 * A token cannot prove EEex data trustworthy or grant execution privileges.
 */
function choosePriorityWeapon(scene,previous=null) {
  const problem=validate(scene);
  if (problem) return hold(problem);
  const s=signature(scene), tick=scene.frame.tick;
  const next={signature:s,lastTick:tick,
      lastAdviceTick:previous&&tickOK(previous.lastAdviceTick)?previous.lastAdviceTick:null};
  if (!previous || previous.signature!==s || !tickOK(previous.lastTick) ||
      tick<=previous.lastTick || tick-previous.lastTick>30)
    return hold("HOLD_STABILIZE_TARGET_AND_EQUIPMENT",{next});
  // No automatic rapid back-and-forth when the weapon, target or protection changes.
  if (next.lastAdviceTick!==null && tick-next.lastAdviceTick<45)
    return hold("HOLD_ADVISORY_SWITCH_COOLDOWN",{next});
  const v1=chooseWeaponWithTraits(scene);
  // V1 can return KEEP_CURRENT despite an unknown alternative. It is not
  // proof of a global best: every occupied weapon must be fully rankable.
  if (Array.isArray(v1.candidates) &&
      (v1.candidates.length!==scene.weapons.length ||
       v1.candidates.some(x=>x.qualified!==true)))
    return hold("HOLD_UNRANKABLE_OCCUPIED_WEAPON",{next,score:v1});
  if (v1.status!=="RECOMMEND_VERIFIED_QUICKSLOT_SWITCH")
    return hold(v1.status,{next,reason:v1.reason??null,score:v1});
  if (!Array.isArray(v1.candidates))
    return hold("HOLD_UNRANKABLE_OCCUPIED_WEAPON",{next,score:v1});
  const chosen=scene.weapons.find(x=>x.id===v1.bestWeaponId);
  if (!chosen || !scene.quickslotIds.includes(chosen.id) ||
      chosen.id===scene.actor.selectedWeaponId)
    return hold("HOLD_CHOICE_OR_SLOT_CHANGED",{next});
  next.lastAdviceTick=tick;
  return hold("ADVISE_PRIORITY_QUICKSLOT_ONLY",{
    fromWeaponId:scene.actor.selectedWeaponId,toWeaponId:chosen.id,
    targetId:scene.enemy.enemyId,slotIndex:chosen.quickslotIndex,
    improvement:v1.improvement,threshold:v1.threshold,
    reason:"COMPLETE_VERIFIED_LOADOUT_BEATS_CURRENT_AFTER_STABILITY",
    next,score:v1});
}
module.exports={validate,signature,choosePriorityWeapon};