// OFFLINE/READ-ONLY PROTOTYPE. NOT WIRED TO EEex OR BGXAI_UPDATE.cmd.
// Pure JS logic. Persistence/telemetry integration has not been implemented.
function createKnowledge() { return {schemaVersion:1,species:{},encounters:{}}; }
function identity(event) {
  if(!event.variant||!event.modFingerprint) throw Error("Need observed variant and mod fingerprint");
  return [event.modFingerprint,event.variant,event.difficulty||"unknown"].join("::");
}
function observe(db,event) {
  if(!event.visibleToParty) return false;
  // Explicitly observed sneak hits affect the particular creature instance, not every species member.
  if(event.kind==="sneak_confirmed"&&event.instanceId&&event.partyId) {
    const k=[event.partyId,event.instanceId].join("::");
    db.encounters[k] ||= {sneakConsumed:false};
    db.encounters[k].sneakConsumed=true;
    return true;
  }
  const key=identity(event);
  if(event.kind!=="hit"&&event.kind!=="explicit_immunity") return false;
  if(!event.damageType) return false;
  if(event.kind==="hit"&&!(event.hpLost>0)) return false;
  if(event.kind==="explicit_immunity"&&event.proof!=="engine") return false;
  const row=db.species[key] ||= {variant:event.variant,observations:0,damage:{}};
  const cell=row.damage[event.damageType] ||= {confirmedHits:0,totalHpLost:0,confirmedImmunity:false};
  if(event.kind==="hit"){cell.confirmedHits++;cell.totalHpLost+=event.hpLost;}
  else cell.confirmedImmunity=true;
  row.observations++;
  return true;
}
function canSneak(db,event) {
  if(!event.partyId||!event.instanceId||!event.melee||!event.flankOrRear||
     !event.safeApproach||event.knownImmune) return false;
  return !db.encounters[[event.partyId,event.instanceId].join("::")]?.sneakConsumed;
}
function suggestDamage(db,event,choices) {
  const known=db.species[identity(event)];
  const scores=choices.filter(c=>c.canUse&&c.safe).map(c=>{
    const evidence=known?.damage[c.type];
    const adjustment=evidence?.confirmedImmunity?-1000:evidence?.confirmedHits?
      Math.min(3,evidence.confirmedHits)*6:0;
    return {type:c.type,score:c.expectedWithoutMemory+adjustment};
  }).sort((a,b)=>b.score-a.score);
  return scores[0]?.type||null;
}
function test() {
  function ok(truth,name){if(!truth)throw Error("FAILED "+name);}
  const db=createKnowledge();
  const sk={variant:"skeleton_a",modFingerprint:"EET_SCS_3521",difficulty:"insane",visibleToParty:true};
  ok(!observe(db,{...sk,kind:"miss",damageType:"piercing"}),"miss not resistance");
  ok(!observe(db,{...sk,kind:"zero",damageType:"crushing",reason:"stoneskin"}),"stoneskin not immunity");
  ok(observe(db,{...sk,kind:"hit",damageType:"crushing",hpLost:9}),"confirmed hit");
  ok(db.species[identity(sk)].damage.crushing.confirmedHits===1,"remember hit");
  ok(!db.species[identity(sk)].damage.piercing,"do not invent resistance");
  ok(suggestDamage(db,sk,[{type:"piercing",canUse:true,safe:true,expectedWithoutMemory:8},{type:"crushing",canUse:true,safe:true,expectedWithoutMemory:8}])==="crushing","prefer observed success");
  ok(!db.species[identity({...sk,variant:"skeleton_b"})],"separate variants");
  ok(!db.species[identity({...sk,difficulty:"legacy_of_bhaal"})],"difficulty fingerprint");
  const rogue={partyId:"team1",instanceId:"wolf7",melee:true,flankOrRear:true,safeApproach:true};
  ok(canSneak(db,rogue),"sneak eligible initially");
  observe(db,{...sk,kind:"sneak_confirmed",partyId:"team1",instanceId:"wolf7"});
  ok(!canSneak(db,rogue),"sneak tracked across rogues");
  ok(canSneak(db,{...rogue,instanceId:"wolf8"}),"other wolf remains eligible");
  const elem={...sk,variant:"fire_elemental_1"};
  observe(db,{...elem,kind:"explicit_immunity",proof:"engine",damageType:"fire"});
  ok(suggestDamage(db,elem,[{type:"fire",canUse:true,safe:true,expectedWithoutMemory:30},{type:"cold",canUse:true,safe:true,expectedWithoutMemory:3}])==="cold","exclude confirmed immunity");
  ok(!observe(db,{...sk,visibleToParty:false,kind:"hit",hpLost:99,damageType:"slashing"}),"no hidden information");
  return {checksPassed:13,species:Object.keys(db.species).length,instances:Object.keys(db.encounters).length};
}
if(typeof module!=="undefined"){
  module.exports={createKnowledge,identity,observe,canSneak,suggestDamage,test};
  if(typeof require!=="undefined"&&require.main===module) console.log(test());
}