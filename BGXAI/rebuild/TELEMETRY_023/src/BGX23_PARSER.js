'use strict';
// Parse only the line emitted by M_BGX23.lua. No control-plane permissions.
const RX=/^\[BGX23\] OBS seq=(\d{1,8}) actor=A([1-6]) slot=([1-6]) action=(\d{1,4}|\?) hp=(-?\d{1,6}|\?) class=(\d{1,6}|\?) pos=(-?\d{1,6}|\?),(-?\d{1,6}|\?) dest=(-?\d{1,6}|\?),(-?\d{1,6}|\?) target=(SELF|PARTY[1-6]|NONPARTY_UNVERIFIED|UNKNOWN) enemyLOS=(\d{1,4}|\?) selected=(SELECTED|UNKNOWN) skill=(-?\d{1,10}|\?) atkMode=(-?\d{1,10}|\?) manual=UNKNOWN enemyTarget=UNKNOWN weapon=UNKNOWN maxHP=UNKNOWN path=UNKNOWN sessionEpoch=UNKNOWN$/;
const intOrNull=s=>s==='?'?null:Number(s);
function parse(line){
 if(typeof line!=='string'||line.length>600)return null;
 const m=RX.exec(line.trim());if(!m)return null;
 if(m[2]!==m[3])return null;
 const o={schema:23,seq:Number(m[1]),actor:'A'+m[2],slot:Number(m[3]),action:intOrNull(m[4]),
   hp:intOrNull(m[5]),classCode:intOrNull(m[6]),position:[intOrNull(m[7]),intOrNull(m[8])],
   destination:[intOrNull(m[9]),intOrNull(m[10])],targetCategory:m[11],
   visibleHostiles:intOrNull(m[12]),selected:m[13]==='SELECTED',skillMode:intOrNull(m[14]),
   attackMode:intOrNull(m[15]),manual:'UNKNOWN',enemyTarget:'UNKNOWN',weapon:'UNKNOWN',
   maxHP:null,pathSafety:'UNKNOWN',sessionEpoch:'UNKNOWN',source:'EEex_party_started_action',
   canIssueGameAction:false};
 if(!Number.isSafeInteger(o.seq)||o.seq<=0||o.action!==null&&(o.action<0||o.action>9999))return null;
 return Object.freeze(o);
}
function reduceLog(text,maxEvents=300){
 const events=[];const stats={total:0,attacks:0,retreats:0,songs:0,unknownTargets:0};
 for(const line of String(text).split(/\r?\n/)){
   if(events.length>=maxEvents)break;
   const e=parse(line.replace(/^.*?(?=\[BGX23\] OBS )/,''));if(!e)continue;
   events.push(e);stats.total++;
   if([3,105,134].includes(e.action))stats.attacks++;
   if(e.action===355)stats.retreats++;
   if(e.action===296)stats.songs++;
   if(e.enemyTarget==='UNKNOWN')stats.unknownTargets++;
 }
 return {schema:23,readOnly:true,stats,lastEvents:events.slice(-24),
   note:'action-start observation only; enemy aggro, manual origin, save epoch, weapon state not verified'};
}
module.exports={parse,reduceLog};
