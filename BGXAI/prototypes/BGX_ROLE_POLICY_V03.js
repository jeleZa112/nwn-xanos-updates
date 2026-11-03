// BGXAI role-driven tactical core v0.3, offline only. No NPC, kit or party-slot constants.
// Safe by construction: never unlock or disarm without visible, valid target + manual permit.
const validRoles=new Set(["ranged_thief","scout","controller","frontliner","support"]);
function decide(s){
 if(!s||s.paused||s.cutscene||s.scriptDisabled||s.actorDead||s.actorDisabled||s.actorPanicked)return {kind:"HOLD",why:"unavailable"};
 if(s.manualOrder||s.actionQueueBusy)return {kind:"HOLD",why:"preserve_user_action"};
 const role=validRoles.has(s.role)?s.role:"support";
 const foe=s.visibleEnemy?.hostile&&s.visibleEnemy?.alive?s.visibleEnemy:null;
 if(foe){
  if(foe.distance<=7&&(s.hpPct??100)<40&&s.escapeBudget>0&&s.escapeCooldownReady)
    return {kind:"EVADE",target:foe.id,why:"critical_close_threat",requestHelp:true};
  if(role==="controller"&&!s.silenced&&!s.spellCooldown){
   const spells=s.memorizedSpells||[];
   if(s.visibleHostileCount>1&&spells.includes("WIZARD_SLEEP")&&!foe.sleepImmuneKnown)
     return {kind:"CAST",spell:"WIZARD_SLEEP",target:foe.id};
   if(spells.includes("WIZARD_BLINDNESS")&&!foe.blindImmuneKnown)
     return {kind:"CAST",spell:"WIZARD_BLINDNESS",target:foe.id};
   if(spells.includes("WIZARD_MAGIC_MISSILE")&&foe.distance<=16)
     return {kind:"CAST",spell:"WIZARD_MAGIC_MISSILE",target:foe.id};
  }
  if(s.weaponRanged&&foe.distance<=18)return {kind:"ATTACK_RANGED",target:foe.id};
  if(s.canEquipRanged&&foe.distance<=18&&role!=="frontliner")return {kind:"EQUIP_RANGED"};
  if(s.weaponMelee&&foe.distance<=4&&(role==="frontliner"||(role==="scout"&&!s.hidden&&(s.hpPct??100)>=65)))
   return {kind:"ATTACK_MELEE",target:foe.id};
  return {kind:"HOLD",why:"no_safe_combat_action"};
 }
 // Encounter-safe, explicit single-target consent; NEVER open unknown or quest-sensitive locks.
 const trap=s.visibleTrap;
 if(s.disarmIntent&&trap&&s.disarmIntent.target===trap.id&&trap.discovered&&trap.safeReachable&&
    !trap.questSensitive&&s.canDisarm&&(s.hpPct??100)>=40)
   return {kind:"DISARM",target:trap.id,why:"consented_visible_trap"};
 const lock=s.visibleLock;
 if(s.pickLockIntent&&lock&&s.pickLockIntent.target===lock.id&&lock.discovered&&lock.safeReachable&&
    lock.knownTrapsCleared&&!lock.questSensitive&&s.canPickLocks)
   return {kind:"PICK_LOCK",target:lock.id,why:"consented_safe_lock"};
 if(role==="ranged_thief"&&s.canDetectTraps&&!s.detectingTraps&&!s.hidden)
   return {kind:"DETECT_TRAPS"};
 if(role==="scout"&&s.canHide&&!s.hidden&&!s.detectingTraps&&s.noCiviliansInSight)
   return {kind:"HIDE"};
 return {kind:"HOLD",why:"idle"};
}
if(typeof module!=="undefined")module.exports={decide};
