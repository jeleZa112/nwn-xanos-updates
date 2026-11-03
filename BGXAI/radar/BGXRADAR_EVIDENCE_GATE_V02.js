// BGXAI Radar / EEex evidence gate v0.2 — SHADOW ONLY, no runtime or engine actions.
// An unmodified BG2RadarOverlay does not provide this feed. All inputs are fixtures
// until a separate local, opt-in exporter and matching EEex identity sensor exist.
'use strict';
const {toScoutSnapshot}=require('../eeex/BGX73_READONLY_ADAPTER.js');
const MAX_AGE_MS=750, MAX_SKEW_MS=350;
const okId=x=>typeof x==='string'&&x.length>0&&x.length<=128;
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function empty(reason){return {ready:false,reason,entities:[],untrusted:0,advisoryOnly:true,
 manualOrigin:'UNKNOWN',canIssueGameAction:false,canDisarm:false,canRetreat:false,
 surroundingsChecked:false,visibilitySnapshotFresh:false};}
function gate(radar,eeex,now){
 const out=empty('unverified_sources');
 if(!radar||!eeex||!finite(now)||radar.schema!==2||
    radar.source!=='BG2RadarOverlay-local-export'||eeex.source!=='EEex')return out;
 if(!okId(radar.session)||radar.session!==eeex.session||
    !okId(radar.area)||radar.area!==eeex.area||
    !okId(radar.identityEpoch)||radar.identityEpoch!==eeex.identityEpoch)
    return empty('session_area_or_save_epoch_unverified');
 if(!finite(radar.timeMs)||!finite(eeex.timeMs)||radar.timeMs>now||
    eeex.timeMs>now||now-radar.timeMs>MAX_AGE_MS||now-eeex.timeMs>MAX_AGE_MS||
    Math.abs(radar.timeMs-eeex.timeMs)>MAX_SKEW_MS)
    return empty('stale_future_or_misaligned');
 if(!Array.isArray(radar.entities)||!Array.isArray(eeex.confirmedMatches)||
    radar.entities.length>128||eeex.confirmedMatches.length>128)
    return empty('malformed_or_oversized_snapshot');
 const duplicateRadar=new Set(),duplicateActor=new Set();
 const seenRadar=new Set(),seenActor=new Set();
 for(const ent of radar.entities){if(!ent||!okId(ent.id))continue;
   if(seenRadar.has(ent.id))duplicateRadar.add(ent.id);seenRadar.add(ent.id);}
 for(const m of eeex.confirmedMatches){if(!m||!okId(m.radarId)||!okId(m.actorId))continue;
   if(seenRadar.has(m.radarId)===false)continue;
   if(seenActor.has(m.actorId))duplicateActor.add(m.actorId);
   seenActor.add(m.actorId);
   if(duplicateRadar.has(m.radarId))continue;
 }
 const matchMap=new Map(),seenMatches=new Set();
 for(const m of eeex.confirmedMatches){
   if(!m||!okId(m.radarId)||!okId(m.actorId))continue;
   if(seenMatches.has(m.radarId))duplicateRadar.add(m.radarId);
   seenMatches.add(m.radarId);
 }
 for(const m of eeex.confirmedMatches){
   if(!m||!okId(m.radarId)||!okId(m.actorId)||duplicateRadar.has(m.radarId)||
      duplicateActor.has(m.actorId)||m.sameCreatureVerified!==true||
      m.inGameVisible!==true||m.sameArea!==true||m.alive!==true||
      m.hiddenFromParty===true||!['enemy','party'].includes(m.side))continue;
   matchMap.set(m.radarId,m);
 }
 const result={...out,ready:true,reason:'fresh_snapshots_not_legal_actions',identityEpoch:radar.identityEpoch};
 for(const ent of radar.entities){
   const m=ent&&matchMap.get(ent.id);
   if(!m||!['enemy','party'].includes(ent.side)||ent.side!==m.side){result.untrusted++;continue;}
   const hp=finite(ent.hp)&&ent.hp>=0?ent.hp:null;
   const effects=Array.isArray(ent.effects)?ent.effects.filter(x=>x&&
     typeof x.effect==='string'&&/^[\w -]{1,48}$/.test(x.effect)&&
     finite(x.ms)&&x.ms>=0&&x.ms<=86400000).slice(0,32).map(x=>({effect:x.effect,ms:x.ms})):[];
   const resist={};
   if(ent.resist&&typeof ent.resist==='object'&&!Array.isArray(ent.resist))
     for(const [k,v] of Object.entries(ent.resist).slice(0,32))
       if(/^[a-zA-Z]{2,25}$/.test(k)&&finite(v)&&v>=-200&&v<=500)resist[k]=v;
   result.entities.push({actorId:m.actorId,side:m.side,hp,effects,resist,
     visibilityVerifiedByEEex:true,source:'RADAR_ADVISORY'});
 }
 return result;
}
function scoutEvidence(event,context={},fused=null){
 const obs=toScoutSnapshot(event,context);
 if(obs.valid!==true)return obs;
 const confirmedHostiles=fused?.ready===true&&fused.identityEpoch===context.saveEpoch?fused.entities.filter(e=>e.side==='enemy')
  .map(e=>({hostile:true,sameArea:true,actorId:e.actorId})):[];
 return {...obs,visibleHostiles:[...(Array.isArray(obs.visibleHostiles)?obs.visibleHostiles:[]),...confirmedHostiles],
  // Zero known enemies is never an all-clear. Scanning, traps and routes are UNVERIFIED.
  visibilitySnapshotFresh:false,surroundingsChecked:false,suspectedHostiles:null,
  trap:null,canDisarm:false,safeRetreatToParty:false,mayDisarm:false,mayRetreat:false,
  manualOrder:null,manualOrigin:'UNKNOWN'};
}
module.exports={gate,scoutEvidence,MAX_AGE_MS,MAX_SKEW_MS};