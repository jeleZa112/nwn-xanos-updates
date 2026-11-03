const assert=require('node:assert/strict');
const S=require('./BGX_SCOUT_SAFETY_V01.js');let n=0;
function check(name,v,expected){assert.deepEqual(v,expected,name);n++}
const trap={id:"t:1",discovered:true,visible:true,inRange:true,reachable:true,
 lineOfSight:true,verifiedSafePath:true,pathAvoidsOtherTraps:true,questSensitive:false,
 removalDifficulty:80,difficultySource:"observed"};
const base={actorKey:"NPC:17",saveEpoch:"save:1",nowMs:1000,trap,
 canDisarm:true,findTrapsSkill:95,hpPct:95,visibilitySnapshotFresh:true,
 surroundingsChecked:true,visibleHostiles:[],suspectedHostiles:[],
 partyCombat:false,recentDamage:false,recentEnemyAttack:false,
 enemyAudible:false,trapAreaAlert:false,scoutCanRemainStationary:true};
const opt={autoDisarm:true};
function run(patch={},options=opt){
 let a=S.step(null,{...base,...patch},options);
 if(a.kind!=="TRAP_ALERT")return a;
 let b=S.step(a.memory,{...base,...patch,nowMs:2000},options);
 if(b.kind!=="WAIT_SCAN")return b;
 return S.step(b.memory,{...base,...patch,nowMs:13000},options);
}
const first=S.step(null,base,opt);check("trap alert",first.kind,"TRAP_ALERT");
check("request party stop",first.requestPartyRouteHold,true);
check("manual order dominates first trap",S.step(null,{...base,manualOrder:true},opt).kind,"HOLD");
const afterScan=S.step(first.memory,{...base,nowMs:2000},opt);
check("first scan waits",afterScan.kind,"WAIT_SCAN");
const disarmed=S.step(afterScan.memory,{...base,nowMs:13000},opt);
check("disarm granted",disarmed.kind,"DISARM_TRAP");
check("executor must revalidate",disarmed.mustRevalidateAtExecution,true);
check("planner cannot issue game command",disarmed.mayIssueEngineAction,false);
check("no repeat after attempted",S.step(disarmed.memory,{...base,nowMs:14000},opt).kind,"HOLD");
check("certainty above DC",S.estimateDisarm(81,80,"observed").probability,1);
check("90% at exact DC",S.estimateDisarm(80,80,"observed").probability,0.9);
check("10% at DC-8",S.estimateDisarm(72,80,"observed").probability,0.1);
check("0% at DC-9",S.estimateDisarm(71,80,"observed").probability,0);
check("DC 100 impossible",S.estimateDisarm(200,100,"observed").probability,0);
check("hidden difficulty not fair knowledge",S.estimateDisarm(200,90,"hidden").known,false);
check("visible hostile abort",run({visibleHostiles:[{hostile:true}]}).kind,"ABORT_DISARM");
check("hostile other area ignored",run({visibleHostiles:[{hostile:true,sameArea:false}]}).kind,"DISARM_TRAP");
check("suspected hostile abort",run({suspectedHostiles:[{}]}).kind,"ABORT_DISARM");
check("party combat abort",run({partyCombat:true}).kind,"ABORT_DISARM");
check("recent damage abort",run({recentDamage:true}).kind,"ABORT_DISARM");
check("recent attack abort",run({recentEnemyAttack:true}).kind,"ABORT_DISARM");
check("audible enemy abort",run({enemyAudible:true}).kind,"ABORT_DISARM");
check("area alert abort",run({trapAreaAlert:true}).kind,"ABORT_DISARM");
check("no stale sensor",run({visibilitySnapshotFresh:false}).kind,"HOLD");
check("no partial sensor",run({surroundingsChecked:false}).kind,"HOLD");
check("missing enemy list",run({visibleHostiles:null}).kind,"HOLD");
check("missing suspicion list",run({suspectedHostiles:null}).kind,"HOLD");
check("no unsafe approach",run({trap:{...trap,verifiedSafePath:false}}).kind,"HOLD");
check("no other trap crossing",run({trap:{...trap,pathAvoidsOtherTraps:false}}).kind,"HOLD");
check("only if in range",run({trap:{...trap,inRange:false}}).kind,"HOLD");
check("quest trap blocked",run({trap:{...trap,questSensitive:true}}).kind,"HOLD");
check("low HP blocked",run({hpPct:35}).kind,"HOLD");
check("hidden thief not exposed",run({hidden:true}).kind,"HOLD");
check("no trap skill blocked",run({canDisarm:false}).kind,"HOLD");
check("manual command blocks",run({manualOrder:true}).kind,"HOLD");
check("busy command blocks",run({actionBusy:true}).kind,"HOLD");
check("pause blocks",run({gamePaused:true}).kind,"HOLD");
check("unknown probability asks user",run({trap:{...trap,removalDifficulty:undefined}}).kind,"REQUEST_CONFIRMATION");
check("low success asks user",run({findTrapsSkill:75}).kind,"REQUEST_CONFIRMATION");
check("no opt in asks user",run({},{}).kind,"REQUEST_CONFIRMATION");
check("unknown high skill special optin",run({findTrapsSkill:110,trap:{...trap,difficultySource:"unknown"}},{autoDisarm:true,unknownDifficulty:"one_cautious_try"}).kind,"DISARM_TRAP");
check("unknown low skill asks",run({findTrapsSkill:40,trap:{...trap,difficultySource:"unknown"}},{autoDisarm:true,unknownDifficulty:"one_cautious_try"}).kind,"REQUEST_CONFIRMATION");
const hit=S.step(afterScan.memory,{...base,nowMs:4000,visibleHostiles:[{hostile:true}]},opt);
check("enemy interrupts",hit.kind,"ABORT_DISARM");
check("enemy timestamp saved",hit.memory.lastThreatAt,4000);
check("wait after enemy",S.step(hit.memory,{...base,nowMs:8000},opt).kind,"WAIT_CLEAR");
check("reloaded save resets",S.step(afterScan.memory,{...base,nowMs:20000,saveEpoch:"save:2"},opt).kind,"TRAP_ALERT");
check("different actor resets",S.step(afterScan.memory,{...base,nowMs:20000,actorKey:"NPC:19"},opt).kind,"TRAP_ALERT");
check("missing save epoch",S.step(null,{...base,saveEpoch:null},opt).kind,"HOLD");
check("passive trap detect without trap",S.step(null,{...base,trap:null,canFindTraps:true,safeStationaryArea:true},opt).kind,"DETECT_TRAPS");
check("no pathing with unsafe stationary area",S.step(null,{...base,trap:null,canFindTraps:true,safeStationaryArea:false},opt).kind,"HOLD");
check("enemy prevents scan even without spotted trap",S.step(null,{...base,trap:null,
 canFindTraps:true,safeStationaryArea:true,visibleHostiles:[{hostile:true}]},opt).kind,"ABORT_DISARM");
check("missing enemy telemetry prevents scan even without spotted trap",S.step(null,{...base,
 trap:null,canFindTraps:true,safeStationaryArea:true,visibleHostiles:null},opt).kind,"HOLD");
console.log("PASS "+n+" scout/trap safety cases");
