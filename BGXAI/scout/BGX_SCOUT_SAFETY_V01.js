// BGXAI v0.4 Scout safety. OFFLINE SHADOW; never directly issues game commands.
// All visible/skill/route/enemy observations must come from a verified EEex adapter.
"use strict";
const CLEAR_MS=10000,SCAN_MS=6670;
const DEFAULTS={autoDisarm:false,minChance:0.9,unknownDifficulty:"ask",
 minUnknownSkill:100,minimumHp:70,minClearMs:CLEAR_MS,minScanMs:SCAN_MS};
function validId(x){return typeof x==="string"||Number.isInteger(x)?String(x):null;}
function integer(x){return Number.isInteger(x)&&x>=0;}
function percent(x){return Number.isFinite(x)&&x>=0&&x<=100;}
// EE skill + (d10 - 1) must be > removal difficulty. No Luck modeled.
// Trap with difficulty exactly 100 is inherently non-disarmable under BGEE rules.
// Difficulty is NOT ordinarily observable to the player: missing source => UNKNOWN.
function estimateDisarm(skill,difficulty,source){
 if(!integer(skill))return {known:false,reason:"skill_not_verified"};
 if(!integer(difficulty)||!["observed","manual"].includes(source))
  return {known:false,reason:"difficulty_not_observable"};
 if(difficulty===100)return {known:true,probability:0,reason:"trap_difficulty_100_unremovable"};
 return {known:true,probability:Math.max(0,Math.min(10,skill-difficulty+9))/10,
  reason:"known_difficulty_base_roll_luck_not_modelled"};
}
function newMemory(){return {actor:null,trap:null,lastThreatAt:null,firstClearAt:null,
 firstScanAt:null,clearSamples:0,lastSampleAt:null,attempted:[],status:"IDLE"};}
function out(kind,reason,memory,extra={}){return {kind,reason,memory,...extra};}
function step(memory,ob={},rawOptions={}){
 const opt={...DEFAULTS,...rawOptions};
 let mem=memory?JSON.parse(JSON.stringify(memory)):newMemory();
 const now=ob.nowMs;
 if(!Number.isFinite(now)||now<0)return out("HOLD","missing_monotonic_game_time",mem);
 if(!ob.actorKey||!ob.saveEpoch)return out("HOLD","unverified_actor_or_save_epoch",mem);
 const actorID=String(ob.saveEpoch)+":"+String(ob.actorKey);
 if(mem.actor!==actorID){mem=newMemory();mem.actor=actorID;}
 const trap=ob.trap;
 // No AI may interfere with a manual order, an active action, or game pause.
 if(ob.manualOrder||ob.actionBusy||ob.gamePaused||ob.cutscene){
  mem.clearSamples=0;mem.firstClearAt=null;mem.firstScanAt=null;
  return out("HOLD","manual_or_action_in_progress",mem);
 }
 if(!trap||validId(trap.id)===null||trap.discovered!==true||trap.visible!==true){
  mem.status="SEARCH";mem.trap=null;mem.clearSamples=0;mem.firstClearAt=null;mem.firstScanAt=null;
  // Even without a spotted trap, a scout must NOT tunnel-vision into detection during combat.
  if(ob.visibilitySnapshotFresh!==true||ob.surroundingsChecked!==true||
   !Array.isArray(ob.visibleHostiles)||!Array.isArray(ob.suspectedHostiles))
   return out("HOLD","enemy_scan_unknown_or_stale",mem);
  const approachingThreat=ob.visibleHostiles.some(e=>e?.hostile===true&&e.sameArea!==false)||
   ob.suspectedHostiles.length>0||ob.partyCombat!==false||
   ob.recentDamage===true||ob.recentEnemyAttack===true||
   ob.enemyAudible===true||ob.trapAreaAlert===true;
  if(approachingThreat)
   return out("ABORT_DISARM","danger_during_recon",mem,{requestPartyRouteHold:true});
  if(ob.canFindTraps===true&&ob.safeStationaryArea===true&&!ob.hidden)
   return out("DETECT_TRAPS","passive_scanning",mem);
  return out("HOLD","no_verified_trap_or_unavailable_detection",mem);
 }
 const trapID=validId(trap.id);
 if(mem.trap!==trapID){
  mem.trap=trapID;mem.firstScanAt=null;mem.firstClearAt=null;mem.clearSamples=0;
  mem.lastSampleAt=null;mem.status="TRAP_FOUND";
  return out("TRAP_ALERT","identified_trap_stop_route_and_reassess",mem,
   {target:trapID,requestPartyRouteHold:true});
 }
 // Fail closed on stale, partial or unavailable enemy/surroundings telemetry.
 if(ob.visibilitySnapshotFresh!==true||ob.surroundingsChecked!==true||
    !Array.isArray(ob.visibleHostiles)||!Array.isArray(ob.suspectedHostiles)){
  mem.clearSamples=0;mem.firstClearAt=null;mem.firstScanAt=null;
  return out("HOLD","enemy_scan_unknown_or_stale",mem,{target:trapID});
 }
 const danger=ob.visibleHostiles.some(e=>e?.hostile===true&&e.sameArea!==false)||
  ob.suspectedHostiles.length>0||ob.partyCombat!==false||
  ob.recentDamage===true||ob.recentEnemyAttack===true||
  ob.enemyAudible===true||ob.trapAreaAlert===true;
 if(danger){
  mem.status="ENEMY_RISK";mem.lastThreatAt=now;mem.clearSamples=0;
  mem.firstClearAt=null;mem.firstScanAt=null;
  return out("ABORT_DISARM","visible_or_recent_enemy_threat",mem,
   {target:trapID,requestPartyRouteHold:true});
 }
 if(ob.actorDisabled||ob.actorDead||ob.panicked)
  return out("HOLD","actor_unavailable",mem,{target:trapID});
 if(ob.canDisarm!==true||!integer(ob.findTrapsSkill))
  return out("HOLD","skill_not_active_or_unknown",mem,{target:trapID});
 if(!percent(ob.hpPct)||ob.hpPct<opt.minimumHp)
  return out("HOLD","hp_too_low",mem,{target:trapID});
 if(ob.hidden===true)
  return out("HOLD","preserve_stealth_manual_choice",mem,{target:trapID});
 if(mem.lastThreatAt!==null&&now-mem.lastThreatAt<opt.minClearMs)
  return out("WAIT_CLEAR","cooldown_after_enemy_seen",mem,{target:trapID});
 // Never let RemoveTraps implicitly path through a trap or a suspected hazard.
 if(trap.inRange!==true||trap.reachable!==true||trap.lineOfSight!==true||
    trap.verifiedSafePath!==true||trap.pathAvoidsOtherTraps!==true||
    trap.questSensitive!==false||ob.scoutCanRemainStationary!==true)
  return out("HOLD","no_proven_safe_disarm_position_or_quest_trap",mem,
   {target:trapID,requestPartyRouteHold:true});
 if(mem.firstClearAt===null){
  mem.firstClearAt=now;mem.firstScanAt=now;mem.clearSamples=1;mem.lastSampleAt=now;
  return out("WAIT_SCAN","first_safe_scan",mem,{target:trapID});
 }
 if(now-mem.firstClearAt<opt.minClearMs||now-mem.firstScanAt<opt.minScanMs)
  return out("WAIT_SCAN","observe_surroundings_for_full_round",mem,{target:trapID});
 if(mem.lastSampleAt!==now){mem.clearSamples++;mem.lastSampleAt=now;}
 if(mem.clearSamples<2)
  return out("WAIT_SCAN","need_independent_second_scan",mem,{target:trapID});
 if(mem.attempted.includes(trapID))
  return out("HOLD","already_attempted_wait_for_verified_result",mem,{target:trapID});
 const skill=ob.findTrapsSkill;
 const chance=estimateDisarm(skill,trap.removalDifficulty,trap.difficultySource);
 if(!chance.known){
  if(opt.unknownDifficulty!=="one_cautious_try"||skill<opt.minUnknownSkill)
   return out("REQUEST_CONFIRMATION","chance_unknown_ask_player",mem,{target:trapID,chance});
 }else if(chance.probability<opt.minChance)
  return out("REQUEST_CONFIRMATION","chance_below_auto_threshold",mem,{target:trapID,chance});
 if(opt.autoDisarm!==true)
  return out("REQUEST_CONFIRMATION","auto_disarm_disabled",mem,{target:trapID,chance});
 mem.attempted.push(trapID);mem.status="DISARM_REQUESTED";
 return out("DISARM_TRAP","safe_auto_disarm_candidate",mem,{target:trapID,chance,
  requestPartyRouteHold:true,mustRevalidateAtExecution:true,mayIssueEngineAction:false});
}
module.exports={CLEAR_MS,SCAN_MS,DEFAULTS,estimateDisarm,newMemory,step};
