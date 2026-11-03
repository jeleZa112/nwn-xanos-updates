"use strict";
const assert=require("node:assert/strict");
const {merge}=require("./BGXRADAR_FUSION_V01.js");
const radar={schema:1,source:"BG2RadarOverlay",session:"s1",area:"AR1000",timeMs:4800,
 entities:[{id:"r1",side:"enemy",hp:25,effects:[{effect:"PFMW",ms:11000}],resist:{fire:75}},
 {id:"r2",side:"enemy",hp:50}]};
const eeex={source:"EEex",session:"s1",area:"AR1000",timeMs:4900,
 confirmedMatches:[{radarId:"r1",actorId:"e1",sameCreatureVerified:true,inGameVisible:true,sameArea:true,alive:true},
 {radarId:"r2",actorId:"e2",sameCreatureVerified:true,inGameVisible:false,sameArea:true,alive:true}]};
let n=0;
const t=(name,actual,expected)=>{assert.deepEqual(actual,expected,name);n++};
const actual=()=>merge(radar,eeex,5000);
t("ready",actual().ready,true);
t("only confirmed",actual().visible.length,1);
t("hidden excluded",actual().untrusted,1);
t("hp",actual().visible[0].hp,25);
t("buff",actual().visible[0].effects[0].ms,11000);
t("resistance",actual().visible[0].resist.fire,75);
t("disarm denied",actual().canDisarm,false);
t("retreat denied",actual().canRetreat,false);
t("area mismatch",merge({...radar,area:"AR9999"},eeex,5000).ready,false);
t("session mismatch",merge({...radar,session:"s2"},eeex,5000).ready,false);
t("radar stale",merge({...radar,timeMs:4000},eeex,5000).ready,false);
t("EEex stale",merge(radar,{...eeex,timeMs:4000},5000).ready,false);
t("timestamp skew",merge({...radar,timeMs:4400},eeex,5000).ready,false);
t("false match",merge(radar,{...eeex,confirmedMatches:eeex.confirmedMatches.map(x=>({...x,sameCreatureVerified:false}))},5000).visible.length,0);
t("wrong source",merge({...radar,source:"Unknown"},eeex,5000).ready,false);
t("no confirmation",merge(radar,{...eeex,confirmedMatches:[]},5000).visible.length,0);
t("no snapshot",merge(radar,null,5000).ready,false);
t("invalid HP",merge({...radar,entities:[{...radar.entities[0],hp:-1}]},eeex,5000).visible[0].hp,null);
t("invalid resistance",Object.keys(merge({...radar,entities:[{...radar.entities[0],resist:{fire:1000}}]},eeex,5000).visible[0].resist).length,0);
t("explicit EEex visibility proof",actual().visible[0].visibilityVerifiedByEEex,true);
console.log("PASS "+n+" BG Radar source-fusion cases");
