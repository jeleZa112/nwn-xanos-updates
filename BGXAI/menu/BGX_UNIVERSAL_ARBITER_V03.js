// BGXAI Universal capability + multi-action arbitration v0.3
// OFFLINE/SHADOW ONLY: no EEex hooks, no game writes, no remote executor.
"use strict";
const TASKS=["melee","ranged","sneak","hide","detect","disarm","unlock","control","damageSpell","defenseSpell","healSpell","buff","summon","healingItem","defensiveItem","wand","specialItem","song","retreat"];
const PRESETS={
 universal:["melee","ranged","sneak","hide","detect","control","damageSpell","defenseSpell","healSpell","buff","summon","song","retreat"],
 cautious:["ranged","detect","defenseSpell","healSpell","buff","retreat"],
 scout:["ranged","melee","sneak","hide","detect","retreat"],
 caster:["ranged","control","damageSpell","defenseSpell","healSpell","buff","summon","retreat"],
 tank:["melee","ranged","defenseSpell","healSpell","buff","retreat"],
 healer:["healSpell","buff","ranged","retreat"]
};
const CAP={
 melee:"melee",ranged:"ranged",sneak:"sneak",hide:"hide",detect:"detect",
 disarm:"disarm",unlock:"unlock",control:"spells",damageSpell:"spells",
 defenseSpell:"spells",healSpell:"spells",buff:"spells",summon:"spells",
 healingItem:"items",defensiveItem:"items",wand:"items",specialItem:"items",
 song:"song",retreat:"mobility"
};
function assertKey(k){if(typeof k!=="string"||!/^[-_:A-Za-z0-9.]{1,128}$/.test(k))throw Error("invalid actor key");}
function profile(key){
 assertKey(key);
 const allow=Object.fromEntries(TASKS.map(k=>[k,PRESETS.universal.includes(k)]));
 return {key,allow,stance:"balanced",enabled:true,limits:{retreatHP:30,healHP:55,allyHP:38,spellReserve:1,itemReserve:1}};
}
function config(campaignKey){assertKey(campaignKey);return {version:3,campaignKey,mode:"travel",actors:Object.create(null)};}
function actor(cfg,key){assertKey(key);if(!Object.prototype.hasOwnProperty.call(cfg.actors,key))cfg.actors[key]=profile(key);return cfg.actors[key];}
function toggle(p,task,on){if(!TASKS.includes(task)||typeof on!=="boolean")throw Error("invalid toggle");p.allow[task]=on;return p;}
function preset(p,name){if(!Object.prototype.hasOwnProperty.call(PRESETS,name))throw Error("invalid preset");
 for(const t of TASKS)p.allow[t]=PRESETS[name].includes(t);return p;}
function mode(cfg,value){if(!["travel","combat","boss","stealth","rest"].includes(value))throw Error("invalid mode");cfg.mode=value;return cfg;}
function stance(p,value){if(!["manual","cautious","balanced","aggressive"].includes(value))throw Error("invalid stance");p.stance=value;return p;}
function permitted(p,cap,task){return p.allow[task]===true && cap?.[CAP[task]]===true;}
function clamp(v,lo,hi){return Math.min(hi,Math.max(lo,v));}
function select(cfg,key,s={}){
 const p=actor(cfg,key),cap=s.capabilities||{},world=s.world||{},self=s.self||{};
 const blocked=!p.enabled||p.stance==="manual"||world.paused||world.cutscene||world.manualOrder||world.busy||world.scriptDisabled||self.dead||self.panicked||self.disabled;
 const hold=(why)=>({kind:"HOLD",why,candidates:0});
 if(blocked)return hold("human_or_game_priority");
 const enemy=(s.enemies||[]).filter(x=>x?.id!=null&&x.visible===true&&x.hostile===true&&x.alive===true&&Number.isFinite(x.distance)).sort((a,b)=>(b.threat||0)-(a.threat||0)||a.distance-b.distance)[0]||null;
 const combat=!!enemy||world.combat===true;
 const hp=Number.isFinite(self.hpPct)?self.hpPct:100;
 const candidates=[];
 const add=(kind,score,target,detail)=>{if(Number.isFinite(score)&&score>0)candidates.push({kind,score,target:target??null,detail:detail??null});};
 const ready=(arr)=>Array.isArray(arr)?arr.filter(x=>x&&x.ready===true&&x.id!=null):[];
 const candidatesSpells=ready(s.spells),candidatesItems=ready(s.items);
 const targetOk=(e,r)=>e&&e.distance<=r;
 const slotsFree=(v)=>Number.isFinite(v)?v:0;
 const costlySpellOk=(spell)=>spell.isRare!==true||cfg.mode==="boss"||world.highThreat===true;
 const canCast=(spell)=>spell.availableToActor===true&&spell.legalTarget===true&&slotsFree(spell.chargesLeftAfterCast)>=p.limits.spellReserve&&costlySpellOk(spell);
 const canItem=(item)=>item.availableToActor===true&&item.legalTarget===true&&slotsFree(item.chargesLeftAfterUse)>=p.limits.itemReserve&&
  (item.rare!==true||cfg.mode==="boss"||world.highThreat===true);
 // Emergency movement requires observed safe route. Never override an active human order.
 if(enemy&&enemy.distance<=7&&hp<p.limits.retreatHP&&permitted(p,cap,"retreat")&&
   world.safeRetreat===true&&world.escapeBudget>0&&world.retreatCooldownReady===true)
    add("RETREAT",1000,enemy.id);
 // Heal self or a single observed friendly ally; no guessing spell availability.
 const allies=(s.allies||[]).filter(a=>a&&a.visible===true&&a.friendly===true&&Number.isFinite(a.hpPct));
 const need=[{id:self.id??key,hpPct:hp,visible:true,friendly:true,distance:0},...allies]
  .filter(x=>x.hpPct<(x.id===(self.id??key)?p.limits.healHP:p.limits.allyHP))
  .sort((a,b)=>a.hpPct-b.hpPct)[0];
 if(need){
  const critical=need.hpPct<=25;
  if(permitted(p,cap,"healSpell"))
   for(const sp of candidatesSpells.filter(x=>x.group==="heal"&&canCast(x)&&x.range>=need.distance&&x.targetsAlly===true))
    add("CAST_HEAL",critical?930:720,need.id,sp.id);
  if(need.id===(self.id??key)&&permitted(p,cap,"healingItem"))
   for(const it of candidatesItems.filter(x=>x.group==="healingItem"&&canItem(x)))
    add("USE_HEAL_ITEM",critical?940:690,need.id,it.id);
 }
 if(enemy){
  if(permitted(p,cap,"control"))
   for(const sp of candidatesSpells.filter(x=>x.group==="control"&&canCast(x)&&targetOk(enemy,x.range)&&
      (x.area!==true||x.friendlyFireSafe===true)&&x.knownIneffective!==true))
     add("CAST_CONTROL",world.highThreat?840:690,enemy.id,sp.id);
  if(permitted(p,cap,"defenseSpell")&&(hp<80||world.imminentHit===true))
   for(const sp of candidatesSpells.filter(x=>x.group==="defense"&&canCast(x)&&x.buffAlreadyActive!==true))
    add("CAST_DEFENSE",world.imminentHit?870:650,self.id??key,sp.id);
  if(permitted(p,cap,"defensiveItem")&&(hp<55||world.imminentHit===true))
   for(const it of candidatesItems.filter(x=>x.group==="defensiveItem"&&canItem(x)))
    add("USE_DEFENSE_ITEM",world.imminentHit?860:620,self.id??key,it.id);
  if(permitted(p,cap,"summon")&&world.highThreat)
   for(const sp of candidatesSpells.filter(x=>x.group==="summon"&&canCast(x)&&x.summonCapFree===true))
    add("CAST_SUMMON",760,enemy.id,sp.id);
  if(permitted(p,cap,"buff")&&world.highThreat)
   for(const sp of candidatesSpells.filter(x=>x.group==="buff"&&canCast(x)&&x.buffAlreadyActive!==true))
    add("CAST_BUFF",670,self.id??key,sp.id);
  if(permitted(p,cap,"damageSpell")&&world.highThreat!==false)
   for(const sp of candidatesSpells.filter(x=>x.group==="damage"&&canCast(x)&&targetOk(enemy,x.range)&&
      (x.area!==true||x.friendlyFireSafe===true)&&x.knownIneffective!==true))
    add("CAST_DAMAGE",world.highThreat?680:435,enemy.id,sp.id);
  if(permitted(p,cap,"wand")&&world.highThreat===true)
   for(const it of candidatesItems.filter(x=>x.group==="wand"&&canItem(x)&&targetOk(enemy,x.range)&&
     (x.area!==true||x.friendlyFireSafe===true)))
    add("USE_WAND",560,enemy.id,it.id);
  if(permitted(p,cap,"specialItem")&&cfg.mode==="boss")
   for(const it of candidatesItems.filter(x=>x.group==="specialItem"&&canItem(x)&&targetOk(enemy,x.range)))
    add("USE_SPECIAL_ITEM",575,enemy.id,it.id);
  if(permitted(p,cap,"sneak")&&self.hidden===true&&world.safeMeleeApproach===true&&
   enemy.distance<=4&&enemy.sneakEligible===true&&enemy.sneakAlreadyUsed!==true&&self.meleeEquipped===true)
    add("SNEAK_ATTACK",780,enemy.id);
  // Crucial: don't break established stealth without explicitly valuable sneak opportunity.
  if(self.hidden!==true){
   if(permitted(p,cap,"ranged")&&self.rangedEquipped===true&&targetOk(enemy,self.rangedRange??18))
    add("RANGED_ATTACK",320,enemy.id);
   if(permitted(p,cap,"melee")&&self.meleeEquipped===true&&enemy.distance<=4&&hp>=40)
    add("MELEE_ATTACK",310,enemy.id);
  }
 }else if(world.safeIdle===true&&!combat){
  const obj=world.target;
  const consent=obj?.id!=null&&obj.visible===true&&obj.reachable===true&&obj.playerApproved===true&&obj.questSensitive!==true;
  if(consent&&permitted(p,cap,"disarm")&&obj.kind==="trap"&&obj.discovered===true&&obj.safeAccess===true)
   add("DISARM_TRAP",400,obj.id);
  if(consent&&permitted(p,cap,"unlock")&&obj.kind==="lock"&&obj.trapsChecked===true&&obj.safeAccess===true)
   add("PICK_LOCK",360,obj.id);
  if(permitted(p,cap,"detect")&&self.detectingTraps!==true&&
      (cfg.mode==="travel"||cfg.mode==="stealth"||cfg.mode==="boss"))
   add("DETECT_TRAPS",190);
  if(permitted(p,cap,"hide")&&self.hidden!==true&&cfg.mode==="stealth"&&
      world.safeToHide===true)
   add("HIDE",180);
 }
 // Cooldowns/hysteresis supplied by external adapter. Can't infer if last order finished.
 const cooling=world.cooldowns||{};
 const viable=candidates.filter(c=>cooling[c.kind]!==true);
 viable.sort((a,b)=>b.score-a.score||a.kind.localeCompare(b.kind)||String(a.target).localeCompare(String(b.target)));
 if(viable.length===0)return hold(combat?"no_verified_safe_combat_action":"no_authorized_idle_action");
 const chosen=viable[0];
 return {kind:chosen.kind,target:chosen.target,resource:chosen.detail,score:chosen.score,candidates:viable.length,reason:"highest_verified_utility"};
}
if(typeof module!=="undefined")module.exports={TASKS,PRESETS,CAP,config,actor,toggle,preset,mode,stance,permitted,select};
