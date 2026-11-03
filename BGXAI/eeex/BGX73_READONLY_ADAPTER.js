// BGXAI 0.7.3 shadow-only parser for actual [BGX73] log line format.
// It never converts a sensor result into a disarm/retreat permission.
'use strict';
const OBS=/^\[BGX73\] OBS actor=(A\d{1,6}) slot=([1-6]) class=(\?|\d{1,6}) kit=(\?|\d{1,10}) level=(\?|\d{1,4})\/(\?|\d{1,4})\/(\?|\d{1,4}) hp=(\?|-?\d{1,6}) enemyLOS=(\?|\d{1,6}) selected=(leader|no_or_unknown) BDAI=([\d?,\-]{15,150}) manual=\? trap=\? path=\? identity=SESSION_ONLY$/;
const BDAI=['BDAI_DISABLE_ATTACK','BDAI_DISABLE_ITEMS','BDAI_DISABLE_OFFENSIVE','BDAI_DISABLE_DEFENSIVE','BDAI_DISABLE_SPECIAL','BDAI_SKILL_MODE','BDAI_ATTACK_MODE','BDAI_NO_ARCANE'];
function numberOrNull(s) { return /^-?\d+$/.test(s) ? Number(s) : null; }
function parse(line) {
 if(typeof line!=='string'||line.length>1000)return null;
 const m=OBS.exec(line.trim()); if(!m)return null;
 const flags=m[11].split(',');
 if(flags.length!==8||flags.some(f=>!/^\?$|^-?\d{1,6}$/.test(f)))return null;
 const locals=Object.fromEntries(flags.map((v,i)=>[BDAI[i],numberOrNull(v)]));
 const hostiles=numberOrNull(m[9]);
 return Object.freeze({alias:m[1],slot:Number(m[2]),classCode:numberOrNull(m[3]),
  kitCode:numberOrNull(m[4]),levels:[m[5],m[6],m[7]].map(numberOrNull),
  hpRaw:numberOrNull(m[8]),hostilesLOS:hostiles,selectedLeader:m[10]==='leader',
  locals,identityScope:'process-session-only',manualStatus:'UNKNOWN',
  trapDetectionStatus:'UNVERIFIED',pathSafetyStatus:'UNVERIFIED'});
}
function toScoutSnapshot(event,context={}) {
 if(!event||!/^A\d{1,6}$/.test(event.alias)||
   typeof context.saveEpoch!=='string'||!context.saveEpoch||
   !Number.isFinite(context.monotonicMs)||context.monotonicMs<0)
   return {valid:false,reason:'identity_or_epoch_unverified',mayDisarm:false};
 const count=event.hostilesLOS;
 const enemies=Number.isInteger(count)&&count>=0 ?
   (count>0?[{hostile:true,sameArea:true,count}]:[]) : null;
 return {valid:true,reason:'EEex_obs_partial_read_only',actorKey:'session:'+event.alias,
  saveEpoch:context.saveEpoch,nowMs:context.monotonicMs,
  // A visible enemy is evidence of danger; zero visible enemies is NOT evidence of safety.
  visibleHostiles:enemies,visibilitySnapshotFresh:false,surroundingsChecked:false,
  suspectedHostiles:null,partyCombat:null,recentDamage:null,recentEnemyAttack:null,
  enemyAudible:null,trapAreaAlert:null,
  // Currently not sourced from EEex, MUST NOT be synthesized from class codes.
  trap:null,canFindTraps:false,canDisarm:false,findTrapsSkill:null,
  scoutCanRemainStationary:false,safeStationaryArea:false,hidden:null,
  safeRetreatToParty:false,retreatDestinationVerified:false,
  retreatPathAvoidsTraps:false,mayDisarm:false,mayRetreat:false};
}
module.exports={BDAI,parse,toScoutSnapshot};