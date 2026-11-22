-- BGXAI R10 synthetic test suite. No native EEex or EET LIVE claim.
local M=dofile('BGXAI_WEAPON_R10_INTERVAL_RANKER.lua')
local R9=dofile('dependencies/BGXAI_WEAPON_R9_CONTEXT_LEDGER.lua')
local function cp(t)
 if type(t)~='table' then return t end
 local o={} for k,v in pairs(t) do o[k]=cp(v) end return o
end
local function eq(a,b)
 if type(a)~=type(b) then return false end
 if type(a)~='table' then return a==b end
 for k,v in pairs(a) do if not eq(v,b[k]) then return false end end
 for k,v in pairs(b) do if not eq(v,a[k]) then return false end end
 return true
end
local tests=0
local function test(name,fn)
 local ok,err=pcall(fn);if not ok then error(name..': '..tostring(err)) end
 tests=tests+1;print('PASS '..tests..' '..name)
end
local function safety(out)
 assert(out.installed==false and out.executable==false and out.dispatchAuthorized==false)
 assert(out.weaponSwitchAuthorized==false and out.ordersSent==0)
 assert(out.actionQueueCleared==false and out.currentActionPreserved==true)
 assert(out.nativeEvidenceAuthenticated==false and out.liveAlternateAPRVerified==false)
 assert(out.manualOrderProven==false and out.epsQueueProven==false)
end
local f={sessionId='S',snapshotId='F1',actor=111,partyIndex=1,sequence=1,
 equipmentFingerprint='eq',activeStatsFingerprint='as',buffFingerprint='bf',
 effectFingerprint='eff',proficiencyFingerprint='pro',targetFingerprint='target',
 selectedSlot=35,selectedRef='SW1H04'}
local r={schema='BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1',
 status='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD',
 actor=111,partyIndex=1,sequence=1,weaponSwitchAuthorized=false,dispatchAuthorized=false,
 alternateSlotAPRVerified=false,targetStatsObserved=false,epsQueueProven=false,manualOrderProven=false,
 selectedAPRDecoded=1.5,currentSelected={sequence=1,selectedSlot=35,
 selectedRef='SW1H04',selectedAPRDecoded=1.5,currentActionOnlyAtRecordedEvent=true,
 contextExhaustivelyVerified=false},quickslots={}}
for i=1,4 do
 r.quickslots[i]={slot=34+i,itemResRef=({'SW1H04','BOW05','STAF01'})[i],
 selectedNow=i==1,effectiveAPRForUnselected=nil,activeBuffsFullyObserved=false,
 perSlotEffectiveTHAC0Verified=false}
end
local ledger=R9.step({sessionId='S',snapshotId='F1',actor=111,partyIndex=1,sequence=1,
 equipmentFingerprint='eq',activeStatsFingerprint='as',buffFingerprint='bf',
 effectFingerprint='eff',proficiencyFingerprint='pro',selectedSlot=35,
 selectedRef='SW1H04'},r,nil)
assert(ledger.status=='PASSIVE_LEDGER_ONLY')
local function bounds(lo,hi) return {lo=lo,hi=hi} end
local model={source='STATIC_FORECAST_UNAUTHENTICATED',nativeProof=false,
 weaponSwitchAuthorized=false,frame=cp(f),slots={}}
for i=1,4 do
 local item=({'SW1H04','BOW05','STAF01'})[i]
 if item==nil then model.slots[i]={slot=i+34,occupied=false}
 else
  model.slots[i]={slot=i+34,occupied=true,itemRef=item,
   modelSource='ITM_2DA_CONTEXTUAL_FORECAST_NOT_NATIVE',
   effectiveAPRNativeVerified=false,effectiveTHAC0NativeVerified=false,
   forecastNotEngineObservation=true,
   apr=bounds(i==1 and 1.5 or .5,i==1 and 1.5 or 4),
   thac0=bounds(10,20),targetAC=bounds(-5,5),
   damage=bounds(1,10),damageThrough=bounds(0,1),contact=bounds(0,1)}
 end
end
model.slots[1].selectedAPRAnchor=1.5
local function checkreason(why,ff,ll,mm)
 local out=M.assess(ff or f,ll or ledger,mm or model);safety(out)
 assert(out.status=='HOLD' and out.reason==why,('expected %s got %s %s'):format(why,out.reason,out.status))
 return out
end
test('baseline overlapping intervals never dispatch',function()
 local o=M.assess(f,ledger,model);safety(o)
 assert(o.status=='INTERVAL_FORECAST_ONLY' and o.modelDominantSlot==nil)
 assert(o.reason=='RANGES_OVERLAP_NO_STABLE_PREFERENCE')
 assert(#o.rows==3 and o.rows[1].slot==35)
end)
test('natural 1 always misses, 20 always hits',function()
 assert(M.hitProbability(-100,100)==.95)
 assert(M.hitProbability(100,-100)==.05)
 assert(M.hitProbability(15,0)==.30)
 assert(M.hitProbability(2,0)==.95)
 assert(M.hitProbability(20,0)==.05)
end)
test('lower THAC0 never reduces hit probability',function()
 for t=-20,40 do assert(M.hitProbability(t-1,-5)>=M.hitProbability(t,-5)) end
end)
test('higher target AC never reduces hit probability',function()
 for ac=-20,20 do assert(M.hitProbability(10,ac+1)>=M.hitProbability(10,ac)) end
end)
test('missed target resistance conservatively yields zero lower bound',function()
 local o=M.assess(f,ledger,model);assert(o.rows[1].minPhysicalDamagePerRound==0)
end)
test('unit resistance and contact produce nonzero lower estimate',function()
 local m=cp(model)
 for i=1,3 do m.slots[i].contact=bounds(1,1);m.slots[i].damageThrough=bounds(1,1) end
 local o=M.assess(f,ledger,m);safety(o);assert(o.rows[1].minPhysicalDamagePerRound>0)
end)
test('dominance is MODEL-only, not permission',function()
 local m=cp(model)
 for i=1,3 do m.slots[i].contact=bounds(1,1);m.slots[i].damageThrough=bounds(1,1);m.slots[i].thac0=bounds(10,10);m.slots[i].targetAC=bounds(0,0) end
 m.slots[1].damage=bounds(1,1)
 m.slots[2].apr=bounds(4,4);m.slots[2].damage=bounds(100,100)
 m.slots[3].damage=bounds(1,1)
 local o=M.assess(f,ledger,m);safety(o);assert(o.modelDominantSlot==36)
 assert(o.mayRecommendWeaponSwitch==false and o.rankedNative==false)
end)
test('empty slots do not block modeling',function()
 local m=cp(model);local o=M.assess(f,ledger,m);assert(#o.rows==3)
end)
test('partial target reach never claims guaranteed damage',function()
 local m=cp(model);m.slots[2].contact=bounds(0,.5)
 local o=M.assess(f,ledger,m);assert(o.rows[2].minPhysicalDamagePerRound==0)
end)
test('different actor blocks',function()
 local x=cp(f);x.actor=112;checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('different session blocks',function()
 local x=cp(f);x.sessionId='S2';checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('different target fingerprint blocks model',function()
 local x=cp(f);x.targetFingerprint='DIFFERENT';checkreason('MODEL_FRAME_OR_PROVENANCE_INVALID',x)
end)
test('different buff fingerprint blocks model',function()
 local x=cp(f);x.buffFingerprint='HASTE';checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('different equipment fingerprint blocks model',function()
 local x=cp(f);x.equipmentFingerprint='EQUIP2';checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('different proficiency fingerprint blocks model',function()
 local x=cp(f);x.proficiencyFingerprint='PROF2';checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('selected weapon ref mismatch blocks',function()
 local x=cp(f);x.selectedRef='BOW05';checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('selected slot different blocks',function()
 local x=cp(f);x.selectedSlot=36;checkreason('R9_LEDGER_INVALID_OR_STALE',x)
end)
test('NaN APR blocked',function()
 local m=cp(model);m.slots[2].apr.lo=0/0;checkreason('NUMERIC_BOUNDS_INVALID',nil,nil,m)
end)
test('infinite damage blocked',function()
 local m=cp(model);m.slots[1].damage.hi=math.huge;checkreason('NUMERIC_BOUNDS_INVALID',nil,nil,m)
end)
test('reversed APR bounds blocked',function()
 local m=cp(model);m.slots[2].apr=bounds(3,2);checkreason('NUMERIC_BOUNDS_INVALID',nil,nil,m)
end)
test('fractional THAC0 blocked',function()
 local m=cp(model);m.slots[2].thac0=bounds(1.5,9.5);checkreason('THAC0_AC_NOT_INTEGER',nil,nil,m)
end)
test('fake native source blocked',function()
 local m=cp(model);m.source='NATIVE_AUTHENTICATED';checkreason('MODEL_FRAME_OR_PROVENANCE_INVALID',nil,nil,m)
end)
test('fake engine APR verified blocked',function()
 local m=cp(model);m.slots[2].effectiveAPRNativeVerified=true;checkreason('FORECAST_PROVENANCE_INCOMPLETE',nil,nil,m)
end)
test('historical APR smuggled into alternate slot blocked',function()
 local m=cp(model);m.slots[2].selectedAPRAnchor=2;checkreason('HISTORICAL_AS_CURRENT_APR_FORBIDDEN',nil,nil,m)
end)
test('selected APR excludes observed value blocked',function()
 local m=cp(model);m.slots[1].apr=bounds(2,4);checkreason('SELECTED_APR_ANCHOR_CONTRADICTION',nil,nil,m)
end)
test('selected anchor false blocked',function()
 local m=cp(model);m.slots[1].selectedAPRAnchor=2;checkreason('SELECTED_APR_ANCHOR_CONTRADICTION',nil,nil,m)
end)
test('negative physical damage blocked',function()
 local m=cp(model);m.slots[2].damage=bounds(-1,4);checkreason('NUMERIC_BOUNDS_INVALID',nil,nil,m)
end)
test('bad resistance factor blocked',function()
 local m=cp(model);m.slots[2].damageThrough=bounds(0,1.1);checkreason('NUMERIC_BOUNDS_INVALID',nil,nil,m)
end)
test('empty slot injection blocked',function()
 local m=cp(model);m.slots[4].itemRef='AX1H01';checkreason('EMPTY_SLOT_HAS_MODEL',nil,nil,m)
end)
test('item mismatch blocked',function()
 local m=cp(model);m.slots[2].itemRef='SLNG01';checkreason('LOADOUT_DIFFERS_FROM_R9',nil,nil,m)
end)
test('R9 fake native authority blocked',function()
 local l=cp(ledger);l.nativeEvidenceAuthenticated=true;checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('R9 alternate current APR forgery blocked',function()
 local l=cp(ledger);l.rows[2].currentAlternateAPR=3;checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('R9 changed actor in next blocks',function()
 local l=cp(ledger);l.next.actor=555;checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('model has no native proof even with all point intervals',function()
 local m=cp(model)
 for i=1,3 do
  m.slots[i].contact=bounds(1,1);m.slots[i].damageThrough=bounds(1,1)
  m.slots[i].thac0=bounds(10,10);m.slots[i].targetAC=bounds(0,0)
  m.slots[i].damage=bounds(10,10);m.slots[i].apr=bounds(i==1 and 1.5 or 2,i==1 and 1.5 or 2)
 end
 local o=M.assess(f,ledger,m);safety(o)
 assert(o.nativeEvidenceAuthenticated==false and o.rankedNative==false)
end)
test('source cannot cause data mutation',function()
 local a,b,c=cp(f),cp(ledger),cp(model)
 local o=M.assess(f,ledger,model);safety(o)
 assert(eq(a,f) and eq(b,ledger) and eq(c,model))
end)
test('bad R9 next state has no context blocks',function()
 local l=cp(ledger);l.next.context=nil;checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('R9 forged current context rejected',function()
 local l=cp(ledger);l.next.context='S|111|1|OTHER|as|bf|eff|pro'
 checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('nonstring equipment fingerprint blocked',function()
 local x=cp(f);x.equipmentFingerprint=8
 checkreason('FRAME_INVALID',x)
end)
test('nonstring target fingerprint blocked',function()
 local x=cp(f);x.targetFingerprint={}
 checkreason('FRAME_INVALID',x)
end)
test('r9 status must be exact',function()
 local l=cp(ledger);l.status='ENGINE_NATIVE_VERIFIED'
 checkreason('R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
print(('TOTAL %d/%d PASS'):format(tests,tests))
