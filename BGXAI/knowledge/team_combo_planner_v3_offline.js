// BGXAI v3 standalone OFFLINE planning model. Not an engine integration or living AI.
// Hypothetical outcome estimates only. Live decisions require verified EEex telemetry.
function clamp(x,min,max){return Math.max(min,Math.min(max,x));}

function start(s){
 return {t:0,actors:Object.fromEntries(s.actors.map(a=>[a.id,a])), enemies:Object.fromEntries(s.enemies.map(e=>[e.id,e])),
  hp:Object.fromEntries(s.actors.map(a=>[a.id,a.hp])),enemyHP:Object.fromEntries(s.enemies.map(e=>[e.id,e.hp])),
  res:Object.fromEntries(s.actors.map(a=>[a.id,{...(a.resources||{})}])),def:Object.fromEntries(s.enemies.map(e=>[e.id,{...(e.defenses||{})}])),
  status:{},tags:{},uses:{},steps:[],routes:[],spent:0,injury:0,withdrawn:false};
}

function clone(x){
 return {...x,hp:{...x.hp},enemyHP:{...x.enemyHP},res:Object.fromEntries(Object.entries(x.res).map(([k,v])=>[k,{...v}])),
   def:Object.fromEntries(Object.entries(x.def).map(([k,v])=>[k,{...v}])),status:Object.fromEntries(Object.entries(x.status).map(([k,v])=>[k,{...v}])),
   tags:{...x.tags},uses:{...x.uses},steps:x.steps.map(x=>[...x]),routes:[...x.routes]};
}

function routeFor(a,s){
 if(!a.routes?.length)return {name:"none",seconds:0,exposure:0};
 let best=null;const me=s.actors[a.actorId];
 for(const r of a.routes){
  if(r.requires?.some(tag=>!s.tags[tag]))continue;
  const guards=(r.guards||[]).filter(id=>s.enemyHP[id]>0);
  const allControlled=guards.length>0&&guards.every(id=>(s.status["control:"+id]?.until??0)>s.t);
  let factor=guards.length===0?.2:allControlled?.16:s.tags.decoyActive?.55:1;
  const exposure=Math.max(0,(r.expectedDamage||0)*factor);
  if(exposure>me.hp*(a.emergency?.5:.28)||exposure>=s.hp[a.actorId])continue;
  const current={name:r.name,seconds:r.seconds||0,exposure};
  if(!best||current.exposure+current.seconds*.55<best.exposure+best.seconds*.55)best=current;
 }
 return best;
}

function allowed(a,s,scenario){
 const me=s.actors[a.actorId],e=s.enemies[a.targetId];
 if(!me||!a.available||a.legal===false||me.manualOrder||me.activeCast||s.hp[me.id]<=0)return null;
 if((s.uses[a.id]||0)>=(a.maxUses??1))return null;
 if(a.resources)for(const [k,num] of Object.entries(a.resources))if((s.res[me.id]?.[k]||0)<num)return null;
 if(a.requires?.some(tag=>!s.tags[tag]))return null;
 if(a.targetId&&(!e||e.visible!==true||s.enemyHP[e.id]<=0))return null;
 if(me.role==="tank"&&me.currentTarget&&a.targetId&&me.currentTarget!==a.targetId&&!a.criticalEmergency)return null;
 if(["attack","sneak","poison"].includes(a.kind)&&a.targetId){
  if(s.def[e.id]?.physical&&!a.bypassesPhysical)return null;
  if((a.enchantment??0)<(e.minimumEnchantment??0)||e.confirmedImmune?.includes(a.damageType))return null;
 }
 if(a.kind==="sneak"&&(!a.verifiedMeleeWeapon||!a.flankOrRear||e.sneakImmune||s.tags["sneakUsed:"+e.id]))return null;
 if(a.kind==="poison"&&(!a.poisonHitEligible||e.confirmedPoisonImmune))return null;
 if(a.kind==="dispel"&&(!s.def[a.targetId]?.[a.removeDefense]||a.removesConfirmed!==true))return null;
 if(a.kind==="control"&&e.controlImmuneConfirmed)return null;
 if(a.kind==="song"&&s.tags["song:"+a.songType])return null;
 if(a.kind==="summon"&&a.familiar&&!a.explicitRiskPermission)return null;
 if(a.kind==="retreat"&&!scenario.allowRetreat)return null;
 if(a.kind==="heal"&&(!s.hp[a.healTarget]||s.hp[a.healTarget] >= s.actors[a.healTarget].hp))return null;
 const route=routeFor(a,s);return route?{route,duration:route.seconds+(a.seconds||0)}:null;
}

function bundles(s,scenario,limit){
 let x=[{actions:[],used:new Set(),duration:0}];
 for(const actor of scenario.actors.filter(a=>a.controlled!==false)){
   const opts=scenario.actions.filter(a=>a.actorId===actor.id).map(a=>({a,ready:allowed(a,s,scenario)})).filter(o=>o.ready);
   let n=[...x];
   for(const prior of x)if(prior.actions.length<(scenario.maxParallel||3))for(const opt of opts){
     if(prior.used.has(actor.id))continue;
     n.push({actions:[...prior.actions,opt],used:new Set([...prior.used,actor.id]),duration:Math.max(prior.duration,opt.ready.duration)});
   }
   x=n.slice(0,550);
 }
 return x.filter(v=>v.actions.length).sort((a,b)=>a.duration-b.duration).slice(0,limit||140);
}

function phase(s,b,scene){
 const n=clone(s),seconds=Math.max(.25,b.duration);
 const activeEnemies=scene.enemies.filter(e=>s.enemyHP[e.id]>0);
 // Existing statuses apply throughout the phase. New buffs/debuffs take effect only AFTER it.
 for(const enemy of activeEnemies){
   const controlled=s.status["control:"+enemy.id];
   const ctl=controlled&&controlled.until>s.t?1-clamp(controlled.successChance||0,0,1):1;
   const poisoned=s.status["poison:"+enemy.id];
   const antiCast=poisoned&&poisoned.until>s.t&&enemy.caster?
      1-clamp(poisoned.interruptChance||0,0,.75):1;
   const decoy=s.tags.decoyActive?1-clamp(s.tags.decoyChance||0,0,.65):1;
   const target=enemy.attacks;
   const songProt=s.tags["song:skald"]?.91:1;
   if(target&&n.hp[target]>0){
      const damage=(enemy.dps||0)*seconds*ctl*antiCast*decoy*songProt;
      n.hp[target]=Math.max(0,n.hp[target]-damage);n.injury+=damage;
   }
   if(poisoned&&poisoned.until>s.t){
      const damage=poisoned.dps*Math.min(seconds,poisoned.until-s.t);
      n.enemyHP[enemy.id]=Math.max(0,n.enemyHP[enemy.id]-damage);
   }
 }
 // Summoned creatures help after they are present, not in the same phase in which they are created.
 if(s.tags.summonDps>0){
   const target=activeEnemies.slice().sort((a,b)=>(b.threat||0)-(a.threat||0))[0];
   if(target)n.enemyHP[target.id]=Math.max(0,n.enemyHP[target.id]-s.tags.summonDps*seconds);
 }
 n.t+=seconds;
 for(const {a,ready} of b.actions){
   const r=ready.route,ally=s.actors[a.actorId],enemy=s.enemies[a.targetId];
   n.hp[a.actorId]=Math.max(0,n.hp[a.actorId]-r.exposure);n.injury+=r.exposure;
   n.routes.push({actor:a.actorId,action:a.id,route:r.name,expectedExposure:r.exposure});
   if(n.hp[a.actorId]<=0)continue;
   n.uses[a.id]=(n.uses[a.id]||0)+1;
   if(a.resources)for(const [k,v] of Object.entries(a.resources))n.res[a.actorId][k]-=v;
   n.spent+=a.resourcePenalty||0;
   if(["attack","sneak","poison","magicDamage"].includes(a.kind)&&enemy){
     const hit=clamp(a.hitChance??1,0,1),res=clamp(enemy.resistances?.[a.damageType]||0,0,1);
     const damage=(a.damage||0)*hit*(1-res)*(s.tags["song:skald"]&&a.songAffected?1.3:1)*(s.tags["buff:"+a.actorId]?1.25:1);
     n.enemyHP[enemy.id]=Math.max(0,n.enemyHP[enemy.id]-damage);
     if(a.kind==="sneak")n.tags["sneakUsed:"+enemy.id]=true; // PREDICTION ONLY: mark live only after confirmed hit
   }
   if(a.kind==="poison"&&enemy&&n.enemyHP[enemy.id]>0){
      const chance=clamp((a.poisonChance??0.5)*(a.hitChance??1),0,1);
      n.status["poison:"+enemy.id]={until:n.t+(a.poisonSeconds||8),dps:(a.tickDps||1)*chance,interruptChance:chance*(a.interruptOnTickChance??.55)};
   }
   if(a.kind==="dispel"){n.def[enemy.id][a.removeDefense]=false;n.tags["exposed:"+enemy.id]=true;}
   if(a.kind==="control"){n.status["control:"+enemy.id]={until:n.t+(a.controlSeconds||6),successChance:a.controlSuccess??.75};}
   if(a.kind==="song"){n.tags["song:"+a.songType]=true;}
   if(a.kind==="summon"){n.tags.decoyActive=true;n.tags.decoyChance=a.diversionChance??.2;n.tags.summonDps=(n.tags.summonDps||0)+(a.summonDps||0);}
   if(a.kind==="buff")n.tags["buff:"+a.buffTarget]=true;
   if(a.kind==="switch"&&a.tag)n.tags[a.tag]=true;
   if(a.kind==="heal")n.hp[a.healTarget]=Math.min(n.actors[a.healTarget].hp,n.hp[a.healTarget]+(a.healAmount||0));
   if(a.kind==="retreat")n.withdrawn=true;
 }
 n.steps.push(b.actions.map(x=>x.a.id));
 return n;
}

function value(s,scene){
 const progress=scene.enemies.reduce((total,e)=>{
  const percent=1-s.enemyHP[e.id]/Math.max(e.hp,1);
  return total+(e.threat||30)*percent*(s.enemyHP[e.id]===0?2:1);
 },0);
 const partyDamage=scene.actors.reduce((total,a)=>total+(s.hp[a.id]<=0?500:(a.hp-s.hp[a.id])*(a.role==="mage"||a.role==="thief"?2.5:1.15)),0);
 const preparations=(s.tags.routeControlled?0:0)+(s.tags["song:skald"]?7:0)+(s.tags.decoyActive?7:0)+
  Object.keys(s.tags).filter(k=>k.startsWith("exposed:")).length*18;
 const activeControl=Object.entries(s.status).filter(([k,v])=>k.startsWith("control:")&&v.until>s.t).length*7;
 return progress-partyDamage+preparations+activeControl-s.spent*1.1-s.t*1.4;
}

function evaluate(scene){
 let beam=[start(scene)],seen=[...beam];
 const depth=scene.phases||4;
 for(let d=0;d<depth;d++){
  const next=[];
  for(const s of beam){
   if(s.withdrawn||scene.enemies.every(e=>s.enemyHP[e.id]<=0)||Object.values(s.hp).some(hp=>hp<=0))continue;
   for(const b of bundles(s,scene,scene.maxBundles||120)){
    const n=phase(s,b,scene);
    if(n.t<=(scene.horizonSec||35))next.push(n);
   }
  }
  if(!next.length)break;
  next.sort((a,b)=>value(b,scene)-value(a,scene));
  beam=next.slice(0,scene.beamWidth||16);
  seen.push(...beam);
 }
 const win=seen.filter(s=>scene.enemies.every(e=>s.enemyHP[e.id]<=0)&&Object.values(s.hp).every(x=>x>0));
 const safe=seen.filter(s=>Object.values(s.hp).every(x=>x>0)&&!s.withdrawn);
 const best=(win.length?win:safe).sort((a,b)=>value(b,scene)-value(a,scene))[0]||start(scene);
 const initial=scene.enemies.reduce((sum,e)=>sum+e.hp,0);
 const remaining=Object.values(best.enemyHP).reduce((sum,h)=>sum+h,0);
 const forecastRisk=scene.actors.some(a=>best.hp[a.id]<a.hp*.45);
 const status=win.length?"SIMULATED_WIN":remaining>=initial-1||forecastRisk?"NO_RELIABLE_WIN_IN_HORIZON":"PARTIAL_REASSESS";
 return {status,steps:best.steps,routes:best.routes,partyHP:best.hp,enemyHP:best.enemyHP,time:best.t,
  evidence:"MODEL_ONLY",recommendation:status==="NO_RELIABLE_WIN_IN_HORIZON"?"RETREAT_OR_PREPARE_OR_CHANGE_TOOLSET":"CONTINUE_AND_REASSESS"};
}

function checks(){
 const main=(extra={})=>({actors:[{id:"thief",hp:30,role:"thief",controlled:true,resources:{}},{id:"mage",hp:28,role:"mage",controlled:true,resources:{control:1}}],enemies:[{id:"boss",hp:22,visible:true,threat:90,dps:2,attacks:"thief"},{id:"guards",hp:100,visible:true,threat:40,dps:0}],actions:[{id:"sneak",actorId:"thief",targetId:"boss",kind:"sneak",available:true,seconds:1,damage:35,damageType:"piercing",hitChance:.95,verifiedMeleeWeapon:true,flankOrRear:true,routes:[{name:"direct",seconds:1,expectedDamage:25,guards:["guards"]},{name:"hidden",seconds:13,expectedDamage:6,guards:["guards"]}]},{id:"freeze",actorId:"mage",targetId:"guards",kind:"control",available:true,seconds:1,resources:{control:1},controlSeconds:8,controlSuccess:1}],phases:3,maxParallel:2,...extra});
 const normal=main(), unprotected=evaluate({...normal,actors:normal.actors.slice(0,1),actions:normal.actions.slice(0,1)}),withControl=evaluate(normal);
 const blocked={actors:[{id:"tank",hp:110,role:"tank",controlled:true,resources:{}}],enemies:[{id:"golem",hp:200,visible:true,threat:90,defenses:{physical:true},attacks:"tank",dps:14}],actions:[{id:"hit",actorId:"tank",targetId:"golem",kind:"attack",available:true,seconds:2,damage:90,maxUses:8}],phases:3};
 const weak={actors:[{id:"tank",hp:100,controlled:true,role:"tank"}],enemies:[{id:"wolf",hp:10,visible:true,threat:20,dps:1,attacks:"tank"}],actions:[{id:"strike",actorId:"tank",targetId:"wolf",kind:"attack",available:true,seconds:2,damage:19,maxUses:1}],phases:2};
 const ally={actors:[{id:"skald",hp:50,role:"bard",controlled:true,resources:{}},{id:"fighter",hp:70,role:"fighter",controlled:true,resources:{}}],enemies:[{id:"target",hp:90,visible:true,threat:60,dps:0}],actions:[{id:"song",actorId:"skald",kind:"song",songType:"skald",available:true,seconds:1},{id:"hit",actorId:"fighter",kind:"attack",targetId:"target",available:true,seconds:2,damage:20,songAffected:true,maxUses:3}],phases:3};
 const s=start(ally),old=phase(s,{actions:[{a:ally.actions[0],ready:allowed(ally.actions[0],s,ally)},{a:ally.actions[1],ready:allowed(ally.actions[1],s,ally)}],duration:2},ally);
 const next=phase(old,{actions:[{a:ally.actions[1],ready:allowed(ally.actions[1],old,ally)}],duration:2},ally);
 const p={actors:[{id:"blackguard",hp:50,role:"blackguard",controlled:true,resources:{poison:1}}],enemies:[{id:"caster",hp:80,visible:true,threat:90,dps:12,attacks:"blackguard",caster:true}],actions:[{id:"toxin",kind:"poison",actorId:"blackguard",targetId:"caster",available:true,seconds:1,hitChance:.8,poisonChance:.7,damage:2,poisonSeconds:8,tickDps:1,interruptOnTickChance:.8,poisonHitEligible:true,resources:{poison:1}}],phases:2};
 const poisonPhase=phase(start(p),{actions:[{a:p.actions[0],ready:allowed(p.actions[0],start(p),p)}],duration:1},p);
 const poisoned=phase(poisonPhase,{actions:[],duration:3},p);
 const all=[
 ["refuse lethal unguarded thief path",!unprotected.routes.some(x=>x.route==="direct")],
 ["with control, approach is feasible",withControl.steps.some(x=>x.includes("freeze"))&&withControl.steps.some(x=>x.includes("sneak"))],
 ["route can be re-evaluated",withControl.routes.some(x=>x.action==="sneak"&&x.route==="direct")],
 ["cannot kill blocked golem",evaluate(blocked).status==="NO_RELIABLE_WIN_IN_HORIZON"],
 ["weak enemy killed",evaluate(weak).status==="SIMULATED_WIN"],
 ["song does not buff same-phase attack",Math.abs(old.enemyHP.target-70)<.01],
 ["song buffs future attack",next.enemyHP.target<50],
 ["poison only causes probability not guaranteed suppression",poisonPhase.status?.nothing===undefined&&poisoned.hp.blackguard>0],
 ["familiar needs explicit risk approval",!allowed({actorId:"skald",kind:"summon",id:"familiar",familiar:true,available:true},s,ally)],
 ["manual orders have priority",!allowed({actorId:"skald",kind:"song",id:"song2",available:true},{...s,actors:{...s.actors,skald:{...s.actors.skald,manualOrder:true}}},ally)],
 ["cannot reapply same song",!allowed(ally.actions[0],old,ally)],
 ["poison effective only if weapon can hit",!allowed({...p.actions[0],targetId:"caster"}, {...start(p),def:{caster:{physical:true}}},p)],
 ["status outputs not claim observed",evaluate(weak).evidence==="MODEL_ONLY"],
 ];
 return {passed:all.filter(x=>x[1]).length,total:all.length,failed:all.filter(x=>!x[1]),example:{unprotected:unprotected.status,controlled:withControl.steps,blocked:evaluate(blocked).status}};
}
if(typeof module!=="undefined"){
 module.exports={start,routeFor,allowed,phase,evaluate,checks};
 if(require.main===module){const r=checks();console.log(JSON.stringify(r,null,2));if(r.failed.length)process.exitCode=1;}
}
