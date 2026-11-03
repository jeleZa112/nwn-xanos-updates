// BGXAI universal arbiter v0.4 scout safety overlay. SHADOW ONLY: proposes, does not execute.
"use strict";
const core=require("./BGX_UNIVERSAL_ARBITER_V03.js");
const scout=require("../scout/BGX_SCOUT_SAFETY_V01.js");
function selectWithScout(cfg,actorKey,snapshot={},memory=null,settings={}){
 const p=core.actor(cfg,actorKey);
 const mission=snapshot.scoutMission;
 if(mission?.enabled!==true||p.enabled!==true||p.stance==="manual"||!snapshot.scoutObservation)
  return {decision:core.select(cfg,actorKey,snapshot),scoutMemory:memory,source:"universal"};
 const canDetect=p.allow.detect===true&&snapshot.capabilities?.detect===true;
 const canDisarm=p.allow.disarm===true&&snapshot.capabilities?.disarm===true;
 const observed={...snapshot.scoutObservation,
  canFindTraps:canDetect&&snapshot.scoutObservation.canFindTraps===true,
  canDisarm:canDisarm&&snapshot.scoutObservation.canDisarm===true};
 const safety={...settings,autoDisarm:mission.autoDisarm===true&&canDisarm&&settings.autoDisarm!==false};
 const r=scout.step(memory,observed,safety);
 const common={source:"scout",scoutMemory:r.memory,scoutResult:r};
 if(r.kind==="DISARM_TRAP")return {...common,decision:{kind:"SCOUT_DISARM_PROPOSAL",
  target:r.target,chance:r.chance,requiresVerifiedExecutor:true,mustRevalidateAtExecution:true}};
 if(r.kind==="DETECT_TRAPS")return {...common,decision:{kind:"SCOUT_DETECT_PROPOSAL",
  requiresVerifiedExecutor:true,mustRevalidateAtExecution:true}};
 if(r.kind==="TRAP_ALERT")return {...common,decision:{kind:"SCOUT_ALERT_TRAP",
  target:r.target,requestPartyRouteHold:true,requiresVerifiedExecutor:true}};
 if(r.kind==="ABORT_DISARM"){
  // Never run blindly across a trapped corridor; a safe destination and route are mandatory.
  const escape=observed.safeRetreatToParty===true&&observed.retreatDestinationVerified===true&&
   observed.retreatPathAvoidsTraps===true&&observed.safePartyPointId!=null&&
   p.allow.retreat===true&&snapshot.capabilities?.mobility===true&&
   !observed.manualOrder&&!observed.actionBusy&&!observed.actorDisabled&&
   !observed.actorDead&&!observed.panicked&&!observed.hidden;
  if(escape)return {...common,decision:{kind:"SCOUT_RETREAT_PROPOSAL",
   target:observed.safePartyPointId,requestPartyRouteHold:true,
   requiresVerifiedExecutor:true,mustRevalidateAtExecution:true}};
  return {...common,decision:{kind:"SCOUT_ABORT_DISARM",
   target:r.target,requestPartyRouteHold:true,suggestSafeFallback:true}};
 }
 if(r.kind==="REQUEST_CONFIRMATION")return {...common,decision:{kind:"SCOUT_ASK_PLAYER",
  target:r.target,chance:r.chance,reason:r.reason}};
 return {...common,decision:{kind:"HOLD",reason:r.reason}};
}
module.exports={selectWithScout};
