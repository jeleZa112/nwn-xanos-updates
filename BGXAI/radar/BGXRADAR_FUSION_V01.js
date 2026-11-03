// BGXAI BG Radar fusion v0.1 — offline read-only contract, NOT an installed adapter.
// Stock Radar Overlay has no confirmed local JSON feed. Never send game actions from this file.
"use strict";
function eligible(radar,eeex,now){
 if(!radar||!eeex||!Number.isFinite(now)||radar.schema!==1||
  radar.source!=="BG2RadarOverlay"||eeex.source!=="EEex")return false;
 if(!radar.session||radar.session!==eeex.session||
  !radar.area||radar.area!==eeex.area)return false;
 const t=radar.timeMs,u=eeex.timeMs;
 return Number.isFinite(t)&&Number.isFinite(u)&&t<=now&&u<=now&&
  now-t<=750&&now-u<=750&&Math.abs(t-u)<=350&&
  Array.isArray(radar.entities)&&Array.isArray(eeex.confirmedMatches);
}
function merge(radar,eeex,now){
 const result={ready:false,visible:[],untrusted:0,canDisarm:false,canRetreat:false};
 if(!eligible(radar,eeex,now))return result;
 result.ready=true;
 const matches=new Map();
 for(const x of eeex.confirmedMatches){
  if(!x||typeof x.radarId!=="string"||typeof x.actorId!=="string")continue;
  if(x.sameCreatureVerified===true&&x.inGameVisible===true&&x.sameArea===true&&x.alive===true&&x.hiddenFromParty!==true){
   if(matches.has(x.radarId))matches.set(x.radarId,null);
   else matches.set(x.radarId,x.actorId);
  }
 }
 for(const ent of radar.entities){
  if(!ent||!matches.get(ent.id)||!["enemy","party"].includes(ent.side)){result.untrusted++;continue}
  const effects=Array.isArray(ent.effects)?ent.effects.filter(e=>e&&typeof e.effect==="string"&&
   Number.isFinite(e.ms)&&e.ms>=0).slice(0,50).map(e=>({effect:e.effect,ms:e.ms})):[];
  const resist=ent.resist&&typeof ent.resist==="object"?
   Object.fromEntries(Object.entries(ent.resist).filter(([k,v])=>/^[a-zA-Z]{2,25}$/.test(k)&&Number.isFinite(v)&&v>=-200&&v<=500)):{};
  result.visible.push({actorId:matches.get(ent.id),side:ent.side,
   hp:Number.isFinite(ent.hp)&&ent.hp>=0?ent.hp:null,effects,resist,
   fromRadar:true,visibilityVerifiedByEEex:true});
 }
 return result;
}
if(typeof module!=="undefined")module.exports={eligible,merge};
