'use strict';
// Run: node test_role_advisor_024.js (offline, never communicates with game)
const {recommend}=require('../src/role_advisor_024');
const assert=require('node:assert/strict');
const actor={id:'cleric',alive:true,isCasting:false,commandOrigin:'AI',manualLocked:false,hp:45,maxHp:100,songStatus:'INACTIVE',isBard:false};
const ab=(kind,id,target='cleric')=>({kind,id,available:true,canUse:true,resourceConfirmed:true,cooldownReady:true,inRange:true,legal:true,verifiedTargets:[target],healAmount:20,healAmountVerified:true,effectStatus:'INACTIVE'});
const make=(extra={})=>({actor,abilities:[ab('HEAL','cure'),ab('BUFF','armor'),ab('POTION','potion')],allies:[],toggles:{healing:true,buffs:true,items:true},visibleHostiles:0,inCombat:false,...extra});
const checks=[
  ['heal eligible',make(), 'HEAL_ADVICE'],
  ['manual order',make({actor:{...actor,commandOrigin:'PLAYER'}}),'NATIVE_FALLBACK'],
  ['manual unknown',make({actor:{...actor,manualLocked:null}}),'NATIVE_FALLBACK'],
  ['casting',make({actor:{...actor,isCasting:true}}),'NATIVE_FALLBACK'],
  ['song active',make({actor:{...actor,songStatus:'ACTIVE'}}),'NATIVE_FALLBACK'],
  ['song unknown',make({actor:{...actor,songStatus:'UNKNOWN'}}),'NATIVE_FALLBACK'],
  ['pending heal',make({pendingHeals:{cleric:{verified:true,expiresTick:99}},tick:1}),'BUFF_ADVICE'],
  ['unknown pending heal',make({pendingHeals:{cleric:{verified:false}}}),'BUFF_ADVICE'],
  ['heal disabled',make({toggles:{healing:false,buffs:true,items:false}}),'BUFF_ADVICE'],
  ['buff in combat blocked',make({toggles:{healing:false,buffs:true,items:false},inCombat:true}),'NATIVE_FALLBACK'],
  ['unknown enemies blocked',make({toggles:{healing:false,buffs:true},visibleHostiles:null}),'NATIVE_FALLBACK'],
  ['critical potion',make({actor:{...actor,hp:20},inCombat:true}),'EMERGENCY_POTION_ADVICE'],
  ['potion missing',make({actor:{...actor,hp:20},inCombat:true,abilities:[]}), 'NATIVE_FALLBACK'],
  ['0-level bard song',make({actor:{...actor,id:'bard',isBard:true,hp:50,maxHp:50},toggles:{song:true},abilities:[ab('SONG','bardSong','bard')]}),'SONG_ADVICE'],
  ['trap without risk proof',make({toggles:{traps:true},abilities:[ab('DISARM_TRAP','tool','tr1')],areaScanned:true,actorCanDisarm:true,trap:{detected:true,trapId:'tr1',successProbability:.95,safeApproach:true}}),'NATIVE_FALLBACK'],
  ['verified trap',make({toggles:{traps:true},abilities:[ab('DISARM_TRAP','tool','tr1')],areaScanned:true,actorCanDisarm:true,trap:{detected:true,trapId:'tr1',successProbability:.95,safeApproach:true,hostilesNearby:false}}),'TRAP_ADVICE'],
  ['low trap chance',make({toggles:{traps:true},abilities:[ab('DISARM_TRAP','tool','tr1')],areaScanned:true,actorCanDisarm:true,trap:{detected:true,trapId:'tr1',successProbability:.4,safeApproach:true,hostilesNearby:false}}),'NATIVE_FALLBACK'],
  ['stealth safe',make({toggles:{stealth:true},abilities:[ab('STEALTH','shadow')],areaScanned:true,noNearbyThreats:true}),'STEALTH_ADVICE'],
  ['stealth not scanned',make({toggles:{stealth:true},abilities:[ab('STEALTH','shadow')],noNearbyThreats:true}),'NATIVE_FALLBACK']
];
for(const [name,scene,kind] of checks){const got=recommend(scene);assert.equal(got.kind,kind,name);assert.equal(got.executable,false,name);}
console.log('BGXAI 024 offline checks:',checks.length,'PASS, 0 FAIL (no game execution)');
