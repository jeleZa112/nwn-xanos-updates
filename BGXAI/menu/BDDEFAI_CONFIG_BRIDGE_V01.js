// BGXAI — BDDEFAI real EET Advanced AI flag import adapter v0.1
// Read-only / SHADOW. Extracts known BDAI globals from a validated EEex snapshot.
// Does not write game variables or execute commands.
"use strict";
const MODE_MAP={1:"detect",2:"hide",3:"song",4:"turnUndead"};
const MAPPED_TASKS=["melee","ranged","detect","hide","song","turnUndead","control","damageSpell","defenseSpell","healSpell","buff","summon","healingItem","defensiveItem","wand","specialItem"];
function hasOwn(obj,key){return Object.prototype.hasOwnProperty.call(obj,key);}
function flag(vars,name){
 if(!vars||typeof vars!=="object")return null;
 for(const k of [name,"LOCALS"+name]) if(hasOwn(vars,k)){
  const v=vars[k];return Number.isInteger(v)?v:null;
 }
 return null;
}
function disabled(vars,name){
 const v=flag(vars,name);return v===null?null:v!==0;
}
function importBDAI(vars, capabilities={}, userChoices={}){
 const attack=disabled(vars,"BDAI_DISABLE_ATTACK");
 const attackMode=flag(vars,"BDAI_ATTACK_MODE");
 const skill=flag(vars,"BDAI_SKILL_MODE");
 const items=disabled(vars,"BDAI_DISABLE_ITEMS");
 const defensive=disabled(vars,"BDAI_DISABLE_DEFENSIVE");
 const offensive=disabled(vars,"BDAI_DISABLE_OFFENSIVE");
 const special=disabled(vars,"BDAI_DISABLE_SPECIAL");
 const noArcane=flag(vars,"BDAI_NO_ARCANE");
 const requested=Object.create(null);
 function apply(keys,value){
  if(value===null)return;
  for(const k of keys)requested[k]=value;
 }
 apply(["melee","ranged"],attack===null?null:!attack);
 if(attack===false&&attackMode===1)requested.ranged=false;
 if(attack===false&&attackMode===2){requested.melee=true;requested.ranged=true;}
 apply(["healingItem","defensiveItem","wand"],items===null?null:!items);
 // 'specialItem' is never automatically enabled: could consume a rare quest item.
 requested.specialItem=false;
 apply(["defenseSpell","healSpell","buff"],defensive===null?null:!defensive);
 apply(["control","damageSpell"],offensive===null?null:!offensive);
 // Magic / song / skills are separate checks, not forced by broad SCS/Beamdog switch.
 if(skill in MODE_MAP)requested[MODE_MAP[skill]]=true;
 // DO NOT interpret exclusive existing modal choice as a permanent ban on the others.
 // Additional per-task explicit player settings override all imported suggestions.
 for(const [task,val] of Object.entries(userChoices)){
  if(MAPPED_TASKS.includes(task)&&typeof val==="boolean")requested[task]=val;
 }
 const available=Object.create(null),enabled=Object.create(null);
 for(const task of MAPPED_TASKS){
  available[task]=capabilities[task]===true;
  enabled[task]=available[task]&&requested[task]===true;
 }
 return {
  source:"user_BDDEFAI_BCS_variables",selectedLegacyMode:MODE_MAP[skill]||null,
  attackPreference:attackMode===1?"melee":attackMode===2?"ranged_when_safe":"auto",
  specialPermitted:special===null?null:!special,
  noArcaneContext:noArcane===1,
  enabled,requested,available,
  warnings:["Exclusive legacy skill mode imported as one starting permission, not a lifelong role",
            "Actual active class/kit/multi/dual and prepared spells must be rechecked by EEex",
            "No automatic quest-item use, pickpocket or unlocked-object targeting"]
 };
}
function selectModal(snapshot,permission){
 const p=permission||{},w=snapshot||{};
 if(w.manualOrder||w.actionBusy||w.cutscene||w.actorDisabled)return "HOLD";
 if(w.hidden===true)return "HOLD"; // never reveal a hidden actor
 // A modal action already running should be preserved unless user explicitly cancels it.
 if(w.activeModal&&["detect","hide","song","turnUndead"].includes(w.activeModal)){
  if(p[w.activeModal]===true&&!w.cancelModal)return "KEEP_"+w.activeModal.toUpperCase();
 }
 if(w.combat===true){
  if(p.turnUndead===true&&w.undeadVisible===true&&w.canTurnNow===true&&w.turnExpectedUseful===true)return "TURN_UNDEAD";
  if(p.song===true&&w.canSingNow===true&&w.songExpectedUseful===true)return "SING";
  return "HOLD";
 }
 if(w.safeIdle===true){
  if(p.detect===true&&w.trapRisk===true&&w.canDetectNow===true)return "DETECT_TRAPS";
  if(p.hide===true&&w.stealthMode===true&&w.canHideNow===true)return "HIDE";
  if(p.song===true&&w.precombatSongRequested===true&&w.canSingNow===true)return "SING";
 }
 return "HOLD";
}
if(typeof module!=="undefined")module.exports={MODE_MAP,MAPPED_TASKS,flag,disabled,importBDAI,selectModal};
