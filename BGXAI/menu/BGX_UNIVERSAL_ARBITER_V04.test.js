// Run together with v0.3 and scout v0.1 tests in a Node environment.
const assert=require('node:assert/strict');
const core=require('./BGX_UNIVERSAL_ARBITER_V03.js');
const v4=require('./BGX_UNIVERSAL_ARBITER_V04.js');
let n=0;function t(label,a,b){assert.deepEqual(a,b,label);n++}
const cfg=core.config('campaign:11'),p=core.actor(cfg,'cre:91');
const trap={id:'t1',discovered:true,visible:true,inRange:true,reachable:true,lineOfSight:true,
 verifiedSafePath:true,pathAvoidsOtherTraps:true,questSensitive:false,
 removalDifficulty:80,difficultySource:'observed'};
const obs={actorKey:'cre:91',saveEpoch:'s1',nowMs:1000,trap,canFindTraps:true,canDisarm:true,
 findTrapsSkill:95,hpPct:95,visibilitySnapshotFresh:true,surroundingsChecked:true,
 visibleHostiles:[],suspectedHostiles:[],partyCombat:false,recentDamage:false,
 recentEnemyAttack:false,enemyAudible:false,trapAreaAlert:false,scoutCanRemainStationary:true};
const shot={capabilities:{detect:true,disarm:true},
 scoutMission:{enabled:true,autoDisarm:true},scoutObservation:obs};
let a=v4.selectWithScout(cfg,'cre:91',shot);
t('first alert',a.decision.kind,'SCOUT_ALERT_TRAP');
t('first actor no auto disarm by default',p.allow.disarm,false);
core.toggle(p,'disarm',true);
a=v4.selectWithScout(cfg,'cre:91',shot);
let b=v4.selectWithScout(cfg,'cre:91',{...shot,scoutObservation:{...obs,nowMs:2000}},a.scoutMemory);
t('safe scan waits',b.decision.kind,'HOLD');
let c=v4.selectWithScout(cfg,'cre:91',{...shot,scoutObservation:{...obs,nowMs:13000}},b.scoutMemory);
t('safe allowed proposal',c.decision.kind,'SCOUT_DISARM_PROPOSAL');
t('verified executor required',c.decision.requiresVerifiedExecutor,true);
let d=v4.selectWithScout(cfg,'cre:91',{...shot,scoutObservation:{...obs,nowMs:13000,
 visibleHostiles:[{hostile:true}]}},b.scoutMemory);
t('enemy interrupts',d.decision.kind,'SCOUT_ABORT_DISARM');
t('hold party route after threat',d.decision.requestPartyRouteHold,true);
let unknown=v4.selectWithScout(cfg,'cre:91',{...shot,scoutObservation:{...obs,nowMs:13000,
 trap:{...trap,removalDifficulty:undefined}}},b.scoutMemory);
t('unknown difficulty asks',unknown.decision.kind,'SCOUT_ASK_PLAYER');
t('mission auto disarm toggle off',v4.selectWithScout(cfg,'cre:91',{...shot,
 scoutMission:{enabled:true,autoDisarm:false},scoutObservation:{...obs,nowMs:13000}},
 b.scoutMemory).decision.kind,'SCOUT_ASK_PLAYER');
t('settings auto off override',v4.selectWithScout(cfg,'cre:91',{...shot,
 scoutObservation:{...obs,nowMs:13000}},b.scoutMemory,{autoDisarm:false}).decision.kind,'SCOUT_ASK_PLAYER');
core.toggle(p,'disarm',false);
t('independent checkbox prevents disarm',v4.selectWithScout(cfg,'cre:91',
 {...shot,scoutObservation:{...obs,nowMs:13000}},b.scoutMemory).decision.kind,'HOLD');
t('when scout mission off use universal',v4.selectWithScout(cfg,'cre:91',
 {...shot,scoutMission:{enabled:false}}).source,'universal');
t('when actor manual use universal',(()=>{core.stance(p,'manual');let r=v4.selectWithScout(cfg,'cre:91',shot).source;core.stance(p,'balanced');return r})(),'universal');
t('no named companion',!/Imoen|Xzar|Montaron|PartySlot/.test(JSON.stringify(cfg)),true);
t('confirmed safe retreat from enemy',v4.selectWithScout(cfg,'cre:91',
 {...shot,capabilities:{detect:true,disarm:true,mobility:true},
 scoutObservation:{...obs,nowMs:13000,visibleHostiles:[{hostile:true}],
 safeRetreatToParty:true,retreatDestinationVerified:true,retreatPathAvoidsTraps:true,
 safePartyPointId:'ally:1'}},b.scoutMemory).decision.kind,'SCOUT_RETREAT_PROPOSAL');
t('retreat blocked by known trap in path',v4.selectWithScout(cfg,'cre:91',
 {...shot,capabilities:{detect:true,disarm:true,mobility:true},
 scoutObservation:{...obs,nowMs:13000,visibleHostiles:[{hostile:true}],
 safeRetreatToParty:true,retreatDestinationVerified:true,retreatPathAvoidsTraps:false,
 safePartyPointId:'ally:1'}},b.scoutMemory).decision.kind,'SCOUT_ABORT_DISARM');
t('no retreat while hidden',v4.selectWithScout(cfg,'cre:91',
 {...shot,capabilities:{detect:true,disarm:true,mobility:true},
 scoutObservation:{...obs,nowMs:13000,visibleHostiles:[{hostile:true}],hidden:true,
 safeRetreatToParty:true,retreatDestinationVerified:true,retreatPathAvoidsTraps:true,
 safePartyPointId:'ally:1'}},b.scoutMemory).decision.kind,'SCOUT_ABORT_DISARM');
console.log('PASS '+n+' universal/scout integration cases');
