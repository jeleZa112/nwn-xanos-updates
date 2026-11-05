'use strict';
// BGXAI 024 — per-character ability policy; OFFLINE ADVICE ONLY.
// Does not read or write game memory, queue orders, cast spells, heal, loot or move.
const UNKNOWN = 'UNKNOWN';
function result(kind, reason, targetId=null, abilityId=null) {
  return Object.freeze({version:24,kind,reason,targetId,abilityId,executable:false,source:'OFFLINE_ADVISORY'});
}
function fallback(reason){ return result('NATIVE_FALLBACK',reason); }
function hpOK(a){return a&&a.alive===true&&Number.isFinite(a.hp)&&Number.isFinite(a.maxHp)&&a.maxHp>0&&a.hp>=0&&a.hp<=a.maxHp;}
function abilityOK(a, kind, targetId){
  return !!a&&a.kind===kind&&typeof a.id==='string'&&a.available===true&&a.canUse===true&&
    a.resourceConfirmed===true&&a.cooldownReady===true&&a.inRange===true&&a.legal===true&&
    (!targetId || (Array.isArray(a.verifiedTargets)&&a.verifiedTargets.includes(targetId)));
}
function recommend(scene){
  if(!scene||typeof scene!=='object'||!scene.actor||!scene.toggles)return fallback('Incomplete scene');
  const a=scene.actor,t=scene.toggles;
  if(a.alive!==true||a.isCasting!==false)return fallback('Actor unavailable or spell action in progress/unknown');
  if(a.commandOrigin!=='AI'||a.manualLocked!==false)return fallback('Do not override manual or unknown-origin orders');
  // No song interruption even for level-0 bards; later magic integration must respect this.
  if(a.songStatus==='ACTIVE'||a.songStatus==='UNKNOWN')return fallback('Preserve bard song; do not interrupt its timing');
  const abilities=Array.isArray(scene.abilities)?scene.abilities:[];
  const first=(kind,targetId,check=()=>true)=>abilities.find(x=>abilityOK(x,kind,targetId)&&check(x));
  if(t.items===true && scene.inCombat===true && hpOK(a) && a.hp/a.maxHp<=0.27){
    const p=first('POTION',a.id,x=>x.healAmountVerified===true&&Number.isFinite(x.healAmount)&&x.healAmount>0);
    if(p)return result('EMERGENCY_POTION_ADVICE','Critical HP, confirmed ready and beneficial healing potion',a.id,p.id);
  }
  if(t.healing===true && Array.isArray(scene.allies)){
    const tick=Number.isSafeInteger(scene.tick)?scene.tick:0;
    const limit=Number.isFinite(t.healBelow)&&t.healBelow>0&&t.healBelow<1?t.healBelow:0.55;
    const candidates=[a,...scene.allies].filter(hpOK).filter(x=>x.hp/x.maxHp<limit);
    candidates.sort((x,y)=>x.hp/x.maxHp-y.hp/y.maxHp);
    for(const patient of candidates){
      const p=scene.pendingHeals&&scene.pendingHeals[patient.id];
      // If pending treatment cannot be verified, refuse to infer target availability.
      if(p && p.verified!==true)continue;
      if(p&&p.verified===true&&Number.isFinite(p.expiresTick)&&p.expiresTick>tick)continue;
      const spell=first('HEAL',patient.id,x=>x.healAmountVerified===true&&Number.isFinite(x.healAmount)&&x.healAmount>0);
      if(spell)return result('HEAL_ADVICE','Confirmed low HP, legal ready ability, no confirmed pending heal',patient.id,spell.id);
    }
  }
  if(t.buffs===true&&scene.inCombat===false&&scene.visibleHostiles===0){
    const spell=first('BUFF',a.id,x=>x.effectStatus==='INACTIVE');
    if(spell)return result('BUFF_ADVICE','Quiet scene, verified effect absent and buff available',a.id,spell.id);
  }
  if(t.song===true && a.songStatus==='INACTIVE' && a.isBard===true){
    const song=first('SONG',a.id);
    if(song)return result('SONG_ADVICE','Confirmed inactive bard song, no current cast',a.id,song.id);
  }
  if(t.traps===true&&scene.inCombat===false&&scene.visibleHostiles===0&&scene.areaScanned===true){
    const trap=scene.trap;
    if(trap&&trap.detected===true&&trap.hostilesNearby===false&&trap.trapId&&
       Number.isFinite(trap.successProbability)&&trap.successProbability>=0.85&&
       trap.safeApproach===true&&scene.actorCanDisarm===true){
      const tool=first('DISARM_TRAP',String(trap.trapId));
      if(tool)return result('TRAP_ADVICE','Verified trap, no observed threat, high success and safe approach',String(trap.trapId),tool.id);
    }
  }
  if(t.stealth===true&&scene.inCombat===false&&scene.visibleHostiles===0&&scene.areaScanned===true&&scene.noNearbyThreats===true){
    const stealth=first('STEALTH',a.id);
    if(stealth)return result('STEALTH_ADVICE','Scanned clear area and verified ready skill',a.id,stealth.id);
  }
  return fallback('No safe, permitted and verified ability action');
}
if(typeof module!=='undefined')module.exports={recommend,abilityOK,hpOK};
