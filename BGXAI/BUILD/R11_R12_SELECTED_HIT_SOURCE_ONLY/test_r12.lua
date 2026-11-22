local M=dofile('BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK.lua')
local R11=dofile('BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE.lua')
local total=0
local function test(name,fn)
 local ok,e=pcall(fn);if not ok then error(name..': '..tostring(e)) end
 total=total+1;print('PASS R12 '..total..' '..name)
end
local function copy(x)
 if type(x)~='table' then return x end
 local t={} for k,v in pairs(x) do t[k]=copy(v) end return t
end
local f={sessionId='S',snapshotId='F',targetFingerprint='T',actor=11,targetActor=22,
 sequence=1,selectedSlot=35}
local r10={schema='BGXAI_WEAPON_R10_INTERVAL_RANKER_V1',
 status='INTERVAL_FORECAST_ONLY',installed=false,executable=false,
 nativeEvidenceAuthenticated=false,weaponSwitchAuthorized=false,
 dispatchAuthorized=false,mayRecommendWeaponSwitch=false,rankedNative=false,
 currentActionPreserved=true,actionQueueCleared=false,manualOrderProven=false,
 epsQueueProven=false,selectedSlot=35,targetFingerprint='T',rows={{
 slot=35,itemRef='SW1H04',selected=true,hitChanceMin=.10,hitChanceMax=.90,
 evidence='CONSERVATIVE_STATIC_FORECAST_NOT_MEASURED_ALTERNATE_APR'}}}
local src={m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,m_items={
 get=function() return {dummy=1} end}}}
-- Keep exact item identity stable across access.
local item={dummy=1};src.m_equipment.m_items.get=function() return item end
local tgt={}
local api={GetWeaponHitChance=function() return 50 end,
 IsImmuneToWeapon=function() return false end}
local ctx={sessionId='S',snapshotId='F',actor=11,targetActor=22,sequence=1,
 usesAlreadySelectedWeapon=true,readOnlyProbeConsent=true,
 manualEPSBoundaryProven=false,switchAttempted=false}
local r11=R11.inspect(src,tgt,api,ctx)
assert(r11.status=='SELECTED_HIT_CHANCE_CANDIDATE_ONLY')
local function safe(o)
 assert(o.installed==false and o.executable==false and o.dispatchAuthorized==false)
 assert(o.weaponSwitchAuthorized==false and o.ordersSent==0 and
  o.currentActionPreserved==true and o.actionQueueCleared==false)
 assert(o.nativeEvidenceAuthenticated==false and o.rankingAuthorized==false and
  o.liveReadVerified==false and o.manualOrderProven==false and o.epsQueueProven==false)
end
local function hold(why,ff,a,b)
 local o=M.compare(ff or f,a or r10,b or r11);safe(o)
 assert(o.status=='HOLD' and o.reason==why,'expected '..why..' got '..tostring(o.reason))
end
test('selected 50% within 10..90 remains nonexecutable',function()
 local x=M.compare(f,r10,r11);safe(x)
 assert(x.status=='SELECTED_ONLY_CONSISTENCY_UNAUTHENTICATED' and
  x.candidateSelectedHitPercent==50 and x.alternativeWeaponEvidenceAdded==false)
end)
test('disagreement with bounds is HOLD',function()
 local a=copy(r10);a.rows[1].hitChanceMax=.40
 hold('FORECAST_ENGINE_CANDIDATE_DISAGREEMENT',nil,a)
end)
test('low bound disagreement is HOLD',function()
 local a=copy(r10);a.rows[1].hitChanceMin=.60
 hold('FORECAST_ENGINE_CANDIDATE_DISAGREEMENT',nil,a)
end)
test('immune true still not recommendation',function()
 local b=copy(r11);b.isImmuneToSelectedWeapon=true
 local x=M.compare(f,r10,b);safe(x)
 assert(x.selectedImmunityCandidate==true and x.rankingAuthorized==false)
end)
test('session replay mismatch blocks',function()
 local ff=copy(f);ff.sessionId='S2'
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',ff)
end)
test('different snapshot blocks',function()
 local ff=copy(f);ff.snapshotId='NEW'
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',ff)
end)
test('different actor blocks',function()
 local ff=copy(f);ff.actor=33
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',ff)
end)
test('different target actor blocks',function()
 local ff=copy(f);ff.targetActor=33
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',ff)
end)
test('different event sequence blocks',function()
 local ff=copy(f);ff.sequence=2
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',ff)
end)
test('different target fingerprint blocks',function()
 local ff=copy(f);ff.targetFingerprint='T2'
 hold('R10_UNTRUSTED_OR_NOT_MATCHED',ff)
end)
test('different selected slot blocks',function()
 local ff=copy(f);ff.selectedSlot=36
 hold('R10_UNTRUSTED_OR_NOT_MATCHED',ff)
end)
test('forged EEex native proof blocked',function()
 local b=copy(r11);b.nativeEvidenceAuthenticated=true
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',nil,nil,b)
end)
test('R10 claim engine native blocked',function()
 local a=copy(r10);a.nativeEvidenceAuthenticated=true
 hold('R10_UNTRUSTED_OR_NOT_MATCHED',nil,a)
end)
test('forged alternate APR blocked',function()
 local b=copy(r11);b.alternateSlotAPRVerified=true
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',nil,nil,b)
end)
test('forged EPS origin blocked',function()
 local b=copy(r11);b.epsQueueProven=true
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',nil,nil,b)
end)
test('multiple selected rows blocked',function()
 local a=copy(r10);a.rows[2]=copy(a.rows[1]);a.rows[2].slot=36
 hold('R10_MULTIPLE_SELECTED_ROWS',nil,a)
end)
test('bogus hit range blocked',function()
 local a=copy(r10);a.rows[1].hitChanceMin=-.1
 hold('R10_ROWS_INVALID',nil,a)
end)
test('NaN hit range blocked',function()
 local a=copy(r10);a.rows[1].hitChanceMax=0/0
 hold('R10_ROWS_INVALID',nil,a)
end)
test('untrusted R11 status blocked',function()
 local b=copy(r11);b.status='NATIVE_VERIFIED'
 hold('R11_NOT_MATCHED_OR_UNTRUSTED',nil,nil,b)
end)
test('bogus selected item status blocked',function()
 local a=copy(r10);a.rows[1].evidence='ENGINE_NATIVE'
 hold('R10_ROWS_INVALID',nil,a)
end)
test('invalid frame blocks',function()
 local ff=copy(f);ff.actor={}
 hold('FRAME_INVALID',ff)
end)
test('caller cannot mutate both inputs',function()
 local aa=copy(r10);local bb=copy(r11)
 local o=M.compare(f,r10,r11);safe(o)
 assert(r10.rows[1].hitChanceMin==aa.rows[1].hitChanceMin)
 assert(r11.hitChancePercent==bb.hitChancePercent)
end)
print(('R12 total %d/%d PASS'):format(total,total))
