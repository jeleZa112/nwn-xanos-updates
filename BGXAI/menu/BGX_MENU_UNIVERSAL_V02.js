// BGXAI universal menu configuration and capability-driven roles v0.2
// SHADOW ONLY: no EEex hooks, filesystem access, or game commands.
"use strict";
const ROLES=["auto","tank","ranged","scout","controller","healer","striker","hybrid"];
const MODES=["travel","combat","boss","stealth","rest"];
const STANCES=["cautious","balanced","aggressive","manual"];
const FEATURES=["martial","melee","ranged","thief","detectTraps","disarmTraps","pickLocks","stealth","arcane","divine","heal","summon","buff","song","sneakAttack"];
const ACTIONS={
 attackRanged:"ranged",attackMelee:"melee",detectTraps:"detectTraps",
 disarmTraps:"disarmTraps",pickLocks:"pickLocks",hide:"stealth",sneakAttack:"sneakAttack",
 arcaneOffense:"arcane",arcaneDefense:"arcane",divineOffense:"divine",
 heal:"heal",summon:"summon",buff:"buff",sing:"song",retreat:null
};
const DEFAULT_TASKS={
 auto:["attackRanged","attackMelee","detectTraps","arcaneOffense","arcaneDefense","heal","buff","retreat"],
 tank:["attackMelee","attackRanged","buff","retreat"],
 ranged:["attackRanged","detectTraps","retreat"],
 scout:["detectTraps","hide","sneakAttack","attackMelee","attackRanged","retreat"],
 controller:["arcaneOffense","arcaneDefense","divineOffense","summon","buff","attackRanged","retreat"],
 healer:["heal","buff","arcaneDefense","attackRanged","retreat"],
 striker:["attackMelee","attackRanged","sneakAttack","buff","retreat"],
 hybrid:Object.keys(ACTIONS).filter(a=>!["disarmTraps","pickLocks"].includes(a))
};
const groupPreset={groupMode:"travel",stance:"balanced",active:true};
function valid(value,items,label){if(!items.includes(value))throw Error("Invalid "+label);return value}
function actorKey(key){if(typeof key!=="string"||!key||key.length>128||!/^[-_.A-Za-z0-9:]+$/.test(key))throw Error("Invalid actor identity");return key}
function newState(campaignKey){
 actorKey(campaignKey);return {schemaVersion:2,campaignKey,group:{...groupPreset},profiles:Object.create(null)};
}
function newProfile(key){
 actorKey(key);return {key,role:"auto",stance:"balanced",tasks:{},buildSignature:null,limits:{retreatHP:35,healHP:65,allyHealHP:45,reserveSpells:1},enabled:true};
}
function ensureProfile(state,key){
 actorKey(key);
 if(!Object.prototype.hasOwnProperty.call(state.profiles,key))state.profiles[key]=newProfile(key);
 return state.profiles[key];
}
function setRole(p,role){p.role=valid(role,ROLES,"role");return p}
function setStance(p,stance){p.stance=valid(stance,STANCES,"stance");return p}
function setGroupMode(state,mode){state.group.groupMode=valid(mode,MODES,"mode");return state}
function setTask(p,task,permission){if(!Object.prototype.hasOwnProperty.call(ACTIONS,task)||typeof permission!=="boolean")throw Error("Invalid task");p.tasks[task]=permission;return p}
function setLimit(p,name,value){
 if(!Object.prototype.hasOwnProperty.call(p.limits,name)||!Number.isFinite(value)||value<0||value>100)throw Error("Invalid limit");
 p.limits[name]=value;return p;
}
// The EEex adapter must report currently verified available abilities, not just nominal classes.
// Thus an inactive dual-class school, forbidden kit spell, or drained spell slot cannot be used.
function verifiedFeatures(observation){
 const actual=Object.create(null);
 for(const k of FEATURES)actual[k]=observation?.features?.[k]===true;
 if(observation?.unavailable)for(const k of FEATURES)actual[k]=false;
 if(!actual.thief)for(const k of ["detectTraps","disarmTraps","pickLocks","stealth","sneakAttack"])actual[k]=false;
 if(!actual.melee)actual.sneakAttack=false;
 return actual;
}
function roleSuggestions(features){
 const r=[];
 if(features.thief&&features.martial){r.push("scout","ranged","striker")}
 if(features.arcane&&(features.martial||features.divine||features.thief)){r.push("hybrid","controller")}
 else if(features.arcane){r.push("controller")}
 if(features.heal||features.divine){r.push("healer")}
 if(features.martial&&features.melee){r.push("tank","striker")}
 if(features.ranged){r.push("ranged")}
 if(features.stealth){r.push("scout")}
 r.push("hybrid");return [...new Set(r)];
}
function optionsFor(p,observation){
 const feature=verifiedFeatures(observation);
 const role=p.role==="auto"?roleSuggestions(feature)[0]:p.role;
 const defaults=new Set(DEFAULT_TASKS[role]);
 const opts=Object.create(null);
 for(const [task,need] of Object.entries(ACTIONS)){
  const requested=p.tasks[task]===undefined?defaults.has(task):p.tasks[task];
  const possible=need===null||feature[need]===true;
  opts[task]={requested,possible,enabled:requested&&possible,reason:possible?null:"Unavailable with current class/kit/skills"};
 }
 return {role,features:feature,options:opts,availableRoles:roleSuggestions(feature)};
}
function evaluate(state,key,observation,world={}){
 const p=ensureProfile(state,key),sel=optionsFor(p,observation);
 const stance=p.stance==="balanced"?state.group.stance:p.stance;
 const paused=!!(world.paused||world.cutscene||world.manualOrder||world.queuedAction||!state.group.active||!p.enabled||observation?.unavailable||stance==="manual");
 const combat=!!world.visibleHostile,mode=state.group.groupMode;
 const safeIdle=!!world.safeIdle&&!combat;
 const a=Object.fromEntries(Object.entries(sel.options).map(([name,v])=>[name,!paused&&v.enabled]));
 if(mode==="travel"||mode==="stealth"||mode==="rest"){
  a.arcaneOffense=false;a.divineOffense=false;
 }
 if(mode==="stealth"){a.attackMelee=false;a.attackRanged=false}
 if(mode==="rest"){a.attackMelee=false;a.attackRanged=false;a.sneakAttack=false}
 if(stance==="cautious"){a.sneakAttack=false}
 a.detectTraps=a.detectTraps&&safeIdle&&(mode==="travel"||mode==="stealth"||mode==="boss");
 a.hide=a.hide&&safeIdle;
 a.sneakAttack=a.sneakAttack&&combat&&world.safeMeleeApproach===true;
 // Exact known and player-approved target, never blanket auto-pick or auto-disarm:
 const target=world.target;
 const permitted=!!target&&target.visible===true&&target.reachable===true&&target.playerApproved===true&&target.questSensitive!==true&&target.id!==undefined&&target.id!==null;
 a.pickLocks=a.pickLocks&&safeIdle&&permitted&&target.kind==="lock"&&target.trapsChecked===true;
 a.disarmTraps=a.disarmTraps&&safeIdle&&permitted&&target.kind==="trap"&&target.discovered===true;
 const knownSpells=Array.isArray(observation?.preparedSpells)?observation.preparedSpells:[];
 // Ability flag is not proof of a memorized spell or usable slot.
 for(const k of ["arcaneOffense","arcaneDefense","divineOffense","heal","summon","buff"]){
  a[k]=a[k]&&knownSpells.length>0;
 }
 return {actor:key,role:sel.role,availableRoles:sel.availableRoles,stance,mode,paused,allowed:a,availability:sel.options,features:sel.features};
}
function refreshBuild(p,signature){
 if(typeof signature!=="string"||!signature)throw Error("Invalid build signature");
 const changed=p.buildSignature!==null&&p.buildSignature!==signature;p.buildSignature=signature;return changed;
}
function exportProfiles(state){return JSON.stringify(state)}
function importProfiles(s){
 const x=JSON.parse(s);
 if(x?.schemaVersion!==2||!x.campaignKey||!x.profiles||typeof x.profiles!=="object"||Array.isArray(x.profiles))throw Error("Invalid state");
 const st=newState(x.campaignKey);setGroupMode(st,x.group?.groupMode);
 st.group.active=x.group?.active===true;st.group.stance=valid(x.group?.stance,STANCES,"stance");
 for(const [key,p] of Object.entries(x.profiles)){
  const np=ensureProfile(st,key);setRole(np,p.role);setStance(np,p.stance);
  for(const [k,v] of Object.entries(p.tasks||{}))setTask(np,k,v);
  for(const [k,v] of Object.entries(p.limits||{}))setLimit(np,k,v);
  np.enabled=p.enabled===true;
  if(p.buildSignature)refreshBuild(np,p.buildSignature);
 }
 return st;
}
if(typeof module!=="undefined")module.exports={ROLES,MODES,STANCES,FEATURES,ACTIONS,newState,ensureProfile,setRole,setStance,setGroupMode,setTask,setLimit,verifiedFeatures,roleSuggestions,optionsFor,evaluate,refreshBuild,exportProfiles,importProfiles};
