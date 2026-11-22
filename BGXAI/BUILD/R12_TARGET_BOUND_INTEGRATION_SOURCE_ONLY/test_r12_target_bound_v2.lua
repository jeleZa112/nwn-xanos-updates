-- Integration test R9 ledger -> R10 real forecast -> R11 target-bound -> R12 V1 -> R12 V2
-- All native calls mocked, pure source only; never represents EET LIVE.
local R9=dofile('dependencies/BGXAI_WEAPON_R9_CONTEXT_LEDGER.lua')
local R10=dofile('dependencies/BGXAI_WEAPON_R10_INTERVAL_RANKER.lua')
local R11=dofile('dependencies/BGXAI_R11_TARGET_BOUND_HIT_CANDIDATE_V2.lua')
local resolver=dofile('dependencies/BGXAI_R11_ACTION_TARGET_CANDIDATE_RO.lua')
local probe=dofile('dependencies/BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE.lua')
local R12=dofile('dependencies/BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK.lua')
local NEW=dofile('BGXAI_WEAPON_R12_TARGET_BOUND_CROSSCHECK_V2.lua')
local function cp(t)if type(t)~='table' then return t end local x={} for k,v in pairs(t) do x[k]=cp(v) end return x end
local function b(lo,hi) return {lo=lo,hi=hi} end
local frame={sessionId='S',snapshotId='F1',actor=111,targetActor=222,partyIndex=1,sequence=1,
 equipmentFingerprint='eq',activeStatsFingerprint='as',buffFingerprint='bf',
 effectFingerprint='eff',proficiencyFingerprint='prof',targetFingerprint='target',
 selectedSlot=35,selectedAbility=0,selectedRef='SW1H04'}
local r6={schema='BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1',
 status='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD',
 actor=111,partyIndex=1,sequence=1,weaponSwitchAuthorized=false,dispatchAuthorized=false,
 alternateSlotAPRVerified=false,targetStatsObserved=false,epsQueueProven=false,manualOrderProven=false,
 selectedAPRDecoded=1.5,currentSelected={sequence=1,selectedSlot=35,
 selectedRef='SW1H04',selectedAPRDecoded=1.5,currentActionOnlyAtRecordedEvent=true,
 contextExhaustivelyVerified=false},quickslots={}}
for i=1,4 do r6.quickslots[i]={slot=i+34,itemResRef=({'SW1H04','BOW05','STAF01'})[i],
 selectedNow=i==1,effectiveAPRForUnselected=nil,activeBuffsFullyObserved=false,
 perSlotEffectiveTHAC0Verified=false} end
local ledger=R9.step({sessionId='S',snapshotId='F1',actor=111,partyIndex=1,sequence=1,
 equipmentFingerprint='eq',activeStatsFingerprint='as',buffFingerprint='bf',
 effectFingerprint='eff',proficiencyFingerprint='prof',selectedSlot=35,
 selectedRef='SW1H04'},r6,nil)
assert(ledger.status=='PASSIVE_LEDGER_ONLY')
local model={source='STATIC_FORECAST_UNAUTHENTICATED',nativeProof=false,
 weaponSwitchAuthorized=false,frame=cp(frame),slots={}}
for i=1,4 do
 local item=({'SW1H04','BOW05','STAF01'})[i]
 if item==nil then model.slots[i]={slot=i+34,occupied=false}
 else model.slots[i]={slot=i+34,occupied=true,itemRef=item,
  modelSource='ITM_2DA_CONTEXTUAL_FORECAST_NOT_NATIVE',
  effectiveAPRNativeVerified=false,effectiveTHAC0NativeVerified=false,
  forecastNotEngineObservation=true,apr=b(i==1 and 1.5 or .5,i==1 and 1.5 or 4),
  thac0=b(10,20),targetAC=b(-5,5),damage=b(1,10),
  damageThrough=b(0,1),contact=b(0,1)} end
end
model.slots[1].selectedAPRAnchor=1.5
local item={resref='SW1H04'}
local src={m_id=111,m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
 m_items={get=function(_,slot) if slot==35 then return item end end}}}
local target={m_id=222,isSprite=function()return true end}
local action={m_actionID=3,m_acteeID={m_Instance=222}}
local eeex={GameObject_Get=function(id)if id==222 then return target end end,
 GetWeaponHitChance=function()return 50 end,
 IsImmuneToWeapon=function()return false end}
local context={sessionId='S',snapshotId='F1',sequence=1,actor=111,targetActor=222,
 actionRaw=3,observeSelectedOnly=true,readOnlyProbeConsent=true,
 manualEPSBoundaryProven=false,switchAttempted=false}
local bound=R11.inspect(src,action,eeex,context,resolver,probe)
assert(bound.status=='TARGET_BOUND_SELECTED_HIT_CANDIDATE_NOT_NATIVE_PROOF')
local n=0
local function safe(x)
 assert(x.installed==false and x.executable==false and x.dispatchAuthorized==false and
 x.weaponSwitchAuthorized==false and x.rankingAuthorized==false and x.ordersSent==0 and
 x.actionQueueCleared==false and x.currentActionPreserved==true and
 x.nativeEvidenceAuthenticated==false and x.liveReadVerified==false and
 x.manualOrderProven==false and x.epsQueueProven==false and
 x.alternateSlotAPRVerified==false and x.gameFilesModified==false)
end
local function test(name,fn)
 local ok,e=pcall(fn);if not ok then error(name..': '..tostring(e)) end
 n=n+1;print('PASS R12-TB '..n..' '..name)
end
local function run(f,l,m,c,r10,r12)
 local x=NEW.compare(f or frame,l or ledger,m or model,c or bound,r10 or R10,r12 or R12)
 safe(x);return x
end
local function held(reason,f,l,m,c,mod10,mod12)
 local x=run(f,l,m,c,mod10,mod12)
 assert(x.status=='HOLD' and x.reason==reason,'expected '..reason..' got '..x.reason)
end
test('full R9 R10 R11 R12 integrated selected-only',function()
 local o=run();assert(o.status=='R10_R11_TARGET_BOUND_R12_CONSISTENT_SOURCE_ONLY')
 assert(o.candidateHitChancePercent==50 and o.targetFingerprintUnauthenticated==true)
 assert(o.selectedItemRefUnverifiedAtRead and o.historicalOrEstimatedAlternateAPRNotCurrentProof)
end)
test('legacy R12 rejects bound wrapper directly',function()
 local r10=R10.assess(frame,ledger,model)
 local old=R12.compare(frame,r10,bound)
 assert(old.status=='HOLD' and old.reason=='R11_NOT_MATCHED_OR_UNTRUSTED')
end)
test('different actor blocks',function()
 local f=cp(frame);f.actor=112
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f)
end)
test('different target actor blocks before evidence',function()
 local f=cp(frame);f.targetActor=333
 held('FRAME_TARGET_OR_ABILITY_UNBOUND',f)
end)
test('model differing target actor blocks',function()
 local m=cp(model);m.frame.targetActor=333
 held('FRAME_TARGET_OR_ABILITY_UNBOUND',nil,nil,m)
end)
test('model differing selected ability blocks',function()
 local m=cp(model);m.frame.selectedAbility=1
 held('FRAME_TARGET_OR_ABILITY_UNBOUND',nil,nil,m)
end)
test('wrong selected ability blocks bound evidence',function()
 local f=cp(frame);f.selectedAbility=1;local m=cp(model);m.frame.selectedAbility=1
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f,nil,m)
end)
test('changed session blocked',function()
 local f=cp(frame);f.sessionId='S2'
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f)
end)
test('changed snapshot blocked',function()
 local f=cp(frame);f.snapshotId='F2'
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f)
end)
test('changed sequence blocked',function()
 local f=cp(frame);f.sequence=2
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f)
end)
test('changed selected slot blocked',function()
 local f=cp(frame);f.selectedSlot=36
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',f)
end)
test('unknown session blocks frame',function()
 local f=cp(frame);f.sessionId='\nINJECTION'
 held('FRAME_TARGET_OR_ABILITY_UNBOUND',f)
end)
test('forged authority in R11 targetbound blocks',function()
 local c=cp(bound);c.weaponSwitchAuthorized=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged rank authority in R11 targetbound blocks',function()
 local c=cp(bound);c.rankingAuthorized=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged live proof blocks',function()
 local c=cp(bound);c.nativeEvidenceAuthenticated=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged enemy proof blocks',function()
 local c=cp(bound);c.hostileTargetProven=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged manual order proof blocks',function()
 local c=cp(bound);c.manualOrderProven=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged EPS proof blocks',function()
 local c=cp(bound);c.epsQueueProven=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('forged alternate slot APR proof blocks',function()
 local c=cp(bound);c.alternateSlotAPRVerified=true
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('nonattack raw action blocked',function()
 local c=cp(bound);c.rawActionId=160
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('fractional hit chance blocked',function()
 local c=cp(bound);c.hitChancePercentCandidate=50.5
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('invalid immunity blocks',function()
 local c=cp(bound);c.isImmuneCandidate='false'
 held('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED',nil,nil,nil,c)
end)
test('stale buff fingerprint blocked via R9',function()
 local f=cp(frame);f.buffFingerprint='HASTE';local m=cp(model);m.frame=cp(f)
 held('R10_CALCULATION_HELD:R9_LEDGER_INVALID_OR_STALE',f,nil,m)
end)
test('stale equipment blocked via R9',function()
 local f=cp(frame);f.equipmentFingerprint='OTHER';local m=cp(model);m.frame=cp(f)
 held('R10_CALCULATION_HELD:R9_LEDGER_INVALID_OR_STALE',f,nil,m)
end)
test('stale target fingerprint blocked by R10',function()
 local f=cp(frame);f.targetFingerprint='NEW'
 held('R10_CALCULATION_HELD:MODEL_FRAME_OR_PROVENANCE_INVALID',f)
end)
test('R10 invalid poison projection blocked',function()
 local m=cp(model);m.slots[2].effectiveAPRNativeVerified=true
 held('R10_CALCULATION_HELD:FORECAST_PROVENANCE_INCOMPLETE',nil,nil,m)
end)
test('R10 missing evidence blocked',function()
 local l=cp(ledger);l.nativeEvidenceAuthenticated=true
 held('R10_CALCULATION_HELD:R9_LEDGER_INVALID_OR_STALE',nil,l)
end)
test('R12 chance discrepancy blocks',function()
 local m=cp(model);m.slots[1].thac0=b(15,15);m.slots[1].targetAC=b(0,0)
 held('R12_COMPARISON_HELD:FORECAST_ENGINE_CANDIDATE_DISAGREEMENT',nil,nil,m)
end)
test('immune candidate remains only comparison',function()
 local c=cp(bound);c.isImmuneCandidate=true;local x=run(nil,nil,nil,c)
 assert(x.status=='R10_R11_TARGET_BOUND_R12_CONSISTENT_SOURCE_ONLY' and x.candidateImmunity==true)
end)
test('missing R10 pure module blocked',function()
 held('PURE_MODULE_DEPENDENCY_MISSING',nil,nil,nil,nil,{},nil)
end)
test('missing R12 pure module blocked',function()
 held('PURE_MODULE_DEPENDENCY_MISSING',nil,nil,nil,nil,nil,{})
end)
test('R10 fake executor output blocked',function()
 local evil={assess=function()return {schema='BGXAI_WEAPON_R10_INTERVAL_RANKER_V1',
  installed=false,executable=false,dispatchAuthorized=true}end}
 held('R10_CALCULATION_UNAVAILABLE_OR_UNTRUSTED',nil,nil,nil,nil,evil)
end)
test('R12 fake executor output blocked',function()
 local evil={compare=function()return {schema='BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK_V1',
  installed=false,executable=true,dispatchAuthorized=true}end}
 held('R12_COMPARISON_UNAVAILABLE_OR_UNTRUSTED',nil,nil,nil,nil,nil,evil)
end)
test('R12 faked consistent values blocked',function()
 local old=R12.compare
 local evil={compare=function(ff,forecast,candidate)
  local x=old(ff,forecast,candidate)
  x.candidateSelectedHitPercent=80
  return x
 end}
 held('R12_COMPARISON_RESULT_MISMATCH',nil,nil,nil,nil,nil,evil)
end)
test('no runtime globals or hooks written',function()
 assert(NEW.installed==false and type(NEW.compare)=='function')
 assert(_G.EEex_Action_AddSpriteStartedActionListener==nil)
end)
print(('R12-TB total %d/%d PASS'):format(n,n))
