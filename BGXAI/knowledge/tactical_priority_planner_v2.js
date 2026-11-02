// BGXAI OFFLINE prototype only. No EEex/WeiDU runtime integration; no I/O, no live commands.
// Inputs must be supported by observed telemetry; projected hitChance/APR etc are estimates.
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));

function estimate(action,enemy){
 if(!action.available||!action.inRange||!enemy.visible)return 0;
 if(enemy.immuneDamageTypes?.includes(action.damageType))return 0;
 const p=action.attack||{};
 if(enemy.enchantmentRequired!=null&&(p.enchantment??0)<enemy.enchantmentRequired)return 0;
 if(enemy.physicalProtectionActive&&action.kind!=="antiMagic")return 0;
 const chance=clamp(p.hitChance??0.5,.05,.95);
 const apr=p.currentAPR??1; const dmg=(p.averageDamage??0)+(action.kind==="sneak"?(p.sneakBonus??0):0);
 const resistance=clamp(enemy.resistance?.[action.damageType]??0,0,1);
 return Math.max(0,dmg*chance*Math.min(apr,p.attackWindowAPRCap??3)*(1-resistance));
}

function eligible(action,actor,enemy,encounter){
 if(!action.available||!action.inRange||!enemy.visible)return false;
 if(actor.manualOrder&&!action.emergency)return false;
 if(actor.casting&&!action.emergency)return false;
 if(actor.role==="tank"&&actor.targetId&&enemy.id!==actor.targetId&&!action.emergency)return false;
 if(action.kind==="sneak"){
  if(!action.melee||!action.eligibleWeaponVerified||!action.flankOrRear||!action.safeRoute||enemy.sneakImmune===true)return false;
  if(encounter.sneakUsed?.[enemy.instanceId])return false;
  if((actor.approachRisk??0)>(actor.hp??1)*.25)return false;
 }
 if(action.kind==="spell"&&action.requiresProtectionDown&&enemy.physicalProtectionActive)return false;
 return true;
}

function utility(action,actor,enemy,encounter,now){
 if(!eligible(action,actor,enemy,encounter))return -Infinity;
 const damage=estimate(action,enemy);
 const hp=Math.max(1,enemy.remainingHP??1);
 const killPotential=clamp(damage/hp,0,1);
 const threat=clamp(enemy.threatScore??0,0,100);
 const exposed=enemy.protectionDownUntil!=null&&enemy.protectionDownUntil>=now?14:0;
 const imminent=enemy.castThreat?22:0;
 const priority=threat*.4+exposed+imminent+(enemy.attackingFragileAlly?18:0);
 const expectedUsefulDamage=Math.min(hp,damage);
 const switchPenalty=actor.targetId&&actor.targetId!==enemy.id?(actor.switchPenalty??15):0;
 const time=(action.travelSeconds??0)*2+(action.castSeconds??0)*2;
 const cost=(action.resourceCost??0)+(action.selfRisk??0)+switchPenalty;
 return expectedUsefulDamage*.6+killPotential*priority+priority*.4-time-cost;
}

function coordinate(party,enemies,proposedActions,encounter,now){
 const results=[],reserved={};
 for(const actor of [...party].sort((a,b)=>(b.assignmentPriority??0)-(a.assignmentPriority??0))){
  const ranked=[];
  for(const action of proposedActions[actor.id]||[]){
   const enemy=enemies.find(e=>e.id===action.targetId);if(!enemy)continue;
   const predicted=estimate(action,enemy);
   const already=reserved[enemy.id]??0;
   let score=utility(action,actor,enemy,encounter,now);
   // A prior actor has already committed a likely finishing blow: don't duplicate until outcome observed.
   if(already>=enemy.remainingHP*.95)score=-Infinity;
   if(actor.targetId===enemy.id)score+=9;
   ranked.push({actor:actor.id,target:enemy.id,action:action.id,score,predicted,kind:action.kind});
  }
  ranked.sort((a,b)=>b.score-a.score);
  const top=ranked[0];const current=ranked.find(r=>r.target===actor.targetId);
  let chosen=top;
  if(top&&current&&current!==top&&top.score<current.score+(actor.changeThreshold??12))chosen=current;
  if(chosen&&Number.isFinite(chosen.score)&&chosen.score>0){
   results.push(chosen);reserved[chosen.target]=(reserved[chosen.target]??0)+chosen.predicted;
  }
 }
 return {orders:results,reserved};
}

function recordObservation(knowledge,observation){
 if(!observation.observedByParty||!observation.combatLogConfirmed||!observation.variantKey)return false;
 const entry=knowledge.enemyVariants[observation.variantKey]??={immunity:{},successfulHits:{},penetrationHistory:[]};
 if(observation.kind==="confirmedImmunity"&&observation.damageType)entry.immunity[observation.damageType]=true;
 else if(observation.kind==="hit"&&observation.damage>0&&observation.damageType){
  const stat=entry.successfulHits[observation.damageType]??={count:0,damage:0};
  stat.count++;stat.damage+=observation.damage;
 }else if(observation.kind==="penetrationFailure"&&Number.isFinite(observation.enchantment)){
  entry.penetrationHistory.push({enchantment:observation.enchantment,actorSignature:observation.actorSignature??"unknown"});
 }else return false;
 return true;
}

function applicableMemory(knowledge,variantKey,actor){
 const v=knowledge.enemyVariants[variantKey];
 if(!v)return {immunities:{},historicalFailures:[],currentBuild:actor.signature};
 return {immunities:v.immunity,historicalFailures:v.penetrationHistory,successfulHits:v.successfulHits,currentBuild:actor.signature};
}

function runTests(){
 const m={enemyVariants:{}}; const enc={sneakUsed:{}};
 const e=(id,hp,extra={})=>({id,instanceId:id,remainingHP:hp,visible:true,threatScore:40,...extra});
 const w=(id,target,kind,attack,extra={})=>({id,targetId:target,kind,attack,damageType:"piercing",available:true,inRange:true,...extra});
 const ap=(apr=1,damage=10,enchant=1)=>({currentAPR:apr,averageDamage:damage,hitChance:.9,enchantment:enchant});
 const tank={id:"tank",role:"tank",targetId:"guard",assignmentPriority:3,hp:100};
 const rogue={id:"rogue",role:"thief",targetId:"mage",assignmentPriority:2,hp:80};
 const archer={id:"archer",role:"ranger",assignmentPriority:1,hp:70};
 const caster={id:"caster",role:"mage",targetId:"guard",casting:true,hp:30};
 const mage=e("mage",24,{threatScore:95,castThreat:true,protectionDownUntil:120});
 const guard=e("guard",120,{threatScore:45});
 const sneak=w("backstab","mage","sneak",{...ap(1,11),sneakBonus:22},{melee:true,eligibleWeaponVerified:true,flankOrRear:true,safeRoute:true});
 const tests=[]; const ok=(name,pass)=>tests.push({name,pass:!!pass});
 ok("eligible 3E melee",eligible(sneak,rogue,mage,enc));
 ok("refuse non-melee 3E",!eligible({...sneak,melee:false},rogue,mage,enc));
 ok("refuse unverified item suitability",!eligible({...sneak,eligibleWeaponVerified:false},rogue,mage,enc));
 ok("refuse dangerous aggro path",!eligible({...sneak,safeRoute:false},rogue,mage,enc));
 ok("one successful sneak per instance",!eligible(sneak,rogue,mage,{sneakUsed:{mage:true}}));
 ok("new spawn eligible",eligible(sneak,rogue,{...mage,id:"mage2",instanceId:"mage2"},enc));
 ok("hold tank target",!eligible(w("x","mage","attack",ap()),tank,mage,enc));
 ok("critical intercept overrides tank",eligible(w("x","mage","attack",ap(),{emergency:true}),tank,mage,enc));
 ok("preserve mage current cast",!eligible(w("magic","mage","spell",ap()),caster,mage,enc));
 ok("can't attack through unremoved protection",estimate(w("hit","mage","attack",ap()),{...mage,physicalProtectionActive:true})===0);
 ok("cannot hit +3 enemy with +1",estimate(w("hit","mage","attack",ap()),{...mage,enchantmentRequired:3})===0);
 ok("+3 hits old failure",estimate(w("hit","mage","attack",ap(1,10,3)),{...mage,enchantmentRequired:3})>0);
 ok("APR increases expected damage",estimate(w("hit","mage","attack",ap(2)),mage)>estimate(w("hit","mage","attack",ap()),mage));
 ok("resistance matters",estimate(w("hit","mage","attack",ap()),{...mage,resistance:{piercing:.5}})<estimate(w("hit","mage","attack",ap()),mage));
 const proposal={tank:[w("tankhit","guard","attack",ap(2,13))],rogue:[sneak],archer:[w("shotmage","mage","attack",ap(2,15)),w("shotguard","guard","attack",ap(2,11))]};
 const plan=coordinate([tank,rogue,archer],[mage,guard],proposal,enc,100);
 ok("tank stays on guard",plan.orders.some(x=>x.actor==="tank"&&x.target==="guard"));
 ok("rogue strikes vulnerable mage",plan.orders.some(x=>x.actor==="rogue"&&x.target==="mage"));
 ok("archer covers other enemy, no overkill",plan.orders.some(x=>x.actor==="archer"&&x.target==="guard"));
 const missed=coordinate([{...archer,assignmentPriority:1}],[{...mage,remainingHP:9}],{archer:[w("finish","mage","attack",ap(2,10))]},enc,101);
 ok("archer re-evaluates surviving mage after failed sneak",missed.orders.some(x=>x.actor==="archer"&&x.target==="mage"));
 ok("memory records real hit",recordObservation(m,{observedByParty:true,combatLogConfirmed:true,variantKey:"golemX",kind:"hit",damageType:"crushing",damage:12}));
 ok("miss not learned as immunity",!recordObservation(m,{observedByParty:true,combatLogConfirmed:true,variantKey:"golemX",kind:"miss",damageType:"crushing"}));
 ok("failed +1 recorded as historical data",recordObservation(m,{observedByParty:true,combatLogConfirmed:true,variantKey:"golemX",kind:"penetrationFailure",enchantment:1,actorSignature:"lvl5"}));
 ok("new build signature doesn't inherit past incapability",applicableMemory(m,"golemX",{signature:"lvl12+3"}).currentBuild==="lvl12+3"&&!applicableMemory(m,"golemX",{signature:"lvl12+3"}).immunities.crushing);
 ok("no hidden enemy analysis",!recordObservation(m,{observedByParty:false,combatLogConfirmed:true,variantKey:"golemX",kind:"confirmedImmunity",damageType:"fire"}));
 return {total:tests.length,passed:tests.filter(t=>t.pass).length,failed:tests.filter(t=>!t.pass),exampleOrders:plan.orders};
}
if(typeof module!=="undefined"){
 module.exports={estimate,eligible,utility,coordinate,recordObservation,applicableMemory,runTests};
 if(require.main===module){const r=runTests();console.log(JSON.stringify(r,null,2));if(r.failed.length)process.exitCode=1;}
}
