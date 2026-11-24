-- R27 real original R2 and R4 cores via deterministic composition, no EEex/game.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(folder..'BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua')
local n=0
local function check(yes,what)
 n=n+1
 assert(yes,'test '..n..' FAILED: '..what)
end
EEex_ReadLString=function(ptr,limit)
 if ptr==65536 then return 'MOCore.bcs' end
 error('unknown CString pointer')
end
local function fixture()
 local stats=setmetatable({m_nNumberOfAttacks=7},{__index=function() return 1 end})
 local action={m_actionID=3,m_source={m_pchData=65536}}
 local sprite={m_id=1001,m_bAllowEffectListCall=1,m_curAction=action,
  m_queuedActions={m_nCount=0},m_bInActionExecution=0,m_bNoInterrupt=0,
  m_curScriptNum=4,m_actionCount=2,m_interrupt=0,
  m_lOrderedBy={m_Instance=0},m_lOrderedBySent={m_Instance=0},
  m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
   m_items={get=function() return nil end}}}
 return sprite,action,stats
end
local s,a,st=fixture()
local function active()return st end
local x=M.observe(s,a,2,active)
check(M.registered==false and M.sourceOnly==true,'no registration')
check(x.status=='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE','same callback pass')
check(x.actor==1001 and x.selectedWeaponRaw==35,'selected scalars')
check(x.selectedAprKeyRaw==7,'selected APR raw 7')
check(x.sameLuaListenerInvocation==true,'one Lua callback')
check(x.engineSessionVerified==false and x.nativeEventTokenAuthenticated==false,'session event unverified')
check(x.alternativeAPRVerified==false and x.launcherAmmoPairVerified==false,'no alt pair proof')
check(x.completeActiveEffectsVerified==false and x.epsManualQueueVerified==false,'effects queue unverified')
check(x.ordersSent==0 and x.localsWritten==0 and x.dispatchAuthorized==false,'no commands')
check(x.actionQueueCleared==false and x.currentActionPreserved==true,'no queue change')
check(x.queueSnapshotStable==true and x.queuedActionsRaw==0,'raw engine queue zero only')
check(x.actionContextSnapshotStable==true and x.engineActionExecutionRaw==0 and
 x.engineNoInterruptRaw==0,'stable engine action flags')
check(x.currentScriptNumberRaw==4 and x.actionCountRaw==2 and x.interruptRaw==0,
 'raw current script/action context')
check(x.actionSourceStable==true and x.actionSourceRaw=='MOCore.bcs',
 'bounded CAIAction m_source candidate observed')
check(x.actionOriginVerified==false and x.manualEpsQueueVerified==false,
 'raw source never classifies manual or EPS origin')
local z=M.observe(nil,a,2,active)
check(z.status=='HOLD_SINGLE_CALLBACK_NO_DISPATCH','missing sprite hold')
z=M.observe(s,nil,2,active)
check(z.status=='HOLD_SINGLE_CALLBACK_NO_DISPATCH','missing action hold')
z=M.observe(s,a,6,active)
check(z.status=='HOLD_SINGLE_CALLBACK_NO_DISPATCH','invalid portrait hold')
s,a,st=fixture()
z=M.observe(s,a,2,function()s.m_equipment.m_selectedWeapon=38; return st end)
check(z.reason=='SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE','changed selected weapon reject')
s,a,st=fixture()
z=M.observe(s,a,2,function()a.m_actionID=23; return st end)
check(z.reason=='SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE','changed action reject')
s,a,st=fixture()
z=M.observe(s,a,2,function() return {} end)
check(z.reason=='R4_DERIVED_STATS_NOT_STABLE','no APR reject')
s,a,st=fixture()
z=M.observe(s,a,2,function() error('fake stats API failure') end)
check(z.reason=='R4_DERIVED_STATS_NOT_STABLE','stats API fail safe')
s,a,st=fixture()
s.m_equipment.m_selectedWeapon=nil
z=M.observe(s,a,2,active)
check(z.reason=='START_EVENT_KEYS_UNREADABLE','missing weapon hold')
s,a,st=fixture()
local emitterCount=0
local listener,err=M.makeListener({portraitIndex=function(id)return 2 end,
  getActiveStats=function()return st end,emit=function(r) emitterCount=emitterCount+1;assert(r.ordersSent==0) end})
check(type(listener)=='function' and err==nil,'injectable listener preparation only')
listener(s,a)
check(emitterCount==1 and M.recorded==1,'bounded passive listener')
check(M.registered==false and M.gameModified==false,'still not registered')
listener(s,a)
check(M.recorded==2 and emitterCount==2,'monotonic per module observations')
M.limit=2
listener(s,a)
check(M.recorded==2 and emitterCount==2,'max samples enforced')
local bad=M.makeListener({getActiveStats=active,emit=function()end})
check(bad==nil,'missing portrait deps denied')
local h=M.hold('TEST')
check(h.dispatchAuthorized==false and h.ordersSent==0,'all holds forbid dispatch')
local good=M.observe(s,a,2,active)
local json=M.toConsoleJson(good)
check(type(json)=='string' and json:find('"selectedAprKeyRaw":7',1,true)~=nil,'JSON selected APR')
check(json:find('"alternativeAPRVerified":false',1,true)~=nil,'JSON never grants alternate APR')
check(json:find('"r4Status":"RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS"',1,true)~=nil,
 'R4 status serialized, selected-only provenance')
check(json:find('"dispatchAuthorized":false',1,true)~=nil,'JSON never authorizes dispatch')
check(json:find('"actionSourceRaw":"MOCore.bcs"',1,true)~=nil,'JSON bounded action source')
check(json:find('"actionSourceSemantics":"UNCLASSIFIED_CAI_ACTION_M_SOURCE"',1,true)~=nil,
 'JSON keeps source semantics unclassified')
check(json:find('"actionContextSnapshotStable":true',1,true)~=nil,'JSON stable engine context')
check(M.toConsoleJson({status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE'})==nil,'unknown sample denied')
local emitted={}
M.recorded=0;M.limit=64
local p=M.prepareConsolePilot({portraitIndex=function()return 2 end,
  getActiveStats=active,emitString=function(v)emitted[#emitted+1]=v end})
check(type(p)=='table' and p.registered==false,'prepared but unregistered')
p.listener(s,a)
check(#emitted==1 and emitted[1]:find('[BGXR27]',1,true)==1,'one source-only line')
check(M.registered==false and M.ordersSent==0,'no auto registration after callback')
check(M.prepareConsolePilot({})==nil,'ports required')
-- New action source / engine context negative tests remain one-callback and read-only.
s,a,st=fixture();local reads=0
EEex_ReadLString=function(ptr,limit) reads=reads+1;return reads<=2 and 'MOCore.bcs' or 'BALDUR.BCS' end
local sourceDrift=M.observe(s,a,2,function()return st end)
check(sourceDrift.actionSourceStable==false and sourceDrift.actionSourceRaw==nil,
 'source drift across same callback fails closed')
check(sourceDrift.actionSourceReadStatus=='ACTION_SOURCE_CHANGED_DURING_CAPTURE',
 'source drift is named in the report')
EEex_ReadLString=function(ptr,limit) return 'MOCore.bcs' end
s,a,st=fixture();local noInterrupt=0
local contextDrift=M.observe(s,a,2,function() noInterrupt=noInterrupt+1;if noInterrupt==1 then s.m_bNoInterrupt=1 end;return st end)
check(contextDrift.actionContextSnapshotStable==false,
 'engine no-interrupt flag drift invalidates context snapshot')
s,a,st=fixture();s.m_bInActionExecution=1;s.m_bNoInterrupt=1
local activeContext=M.observe(s,a,2,function()return st end)
check(activeContext.engineActionExecutionRaw==1 and activeContext.engineNoInterruptRaw==1,
 'active execution and no-interrupt raw flags observed')
local savedReader=EEex_ReadLString;EEex_ReadLString=nil
s,a,st=fixture();local noReader=M.observe(s,a,2,function()return st end)
check(noReader.actionSourceStable==false and noReader.actionSourceRaw==nil and
 noReader.actionSourceReadStatus=='EEEX_READLSTRING_UNAVAILABLE',
 'missing bounded reader fails closed without dispatch')
EEex_ReadLString=savedReader
-- Additional R2-refresh invariants not covered by the historical R27 suite.
local function inventory_fixture(index, original)
 local sprite,action,stats=fixture()
 local entries={[index]={m_useCount1=17,m_flags=0,
   cResRef={get=function()return original end}}}
 local fail=false
 sprite.m_equipment.m_items={get=function(_,slot)
   if fail and slot==index then error('native read unavailable') end
   return entries[slot]
 end}
 return sprite,action,stats,entries,function(v)fail=v end
end
local function must_hold(r,reason)
 check(r.status=='HOLD_SINGLE_CALLBACK_NO_DISPATCH' and r.reason==reason,reason)
 check(r.ordersSent==0 and r.dispatchAuthorized==false and
  r.currentActionPreserved==true and r.actionQueueCleared==false,'hold no interruption')
end
s,a,st=inventory_fixture(36,'BOW05')
local item=s.m_equipment.m_items:get(36)
local snapshot=M.observe(s,a,2,function()
  item.cResRef.get=function()return 'BOW06' end
  return st
end)
must_hold(snapshot,'EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE')
s,a,st=inventory_fixture(12,'AROW01')
item=s.m_equipment.m_items:get(12)
snapshot=M.observe(s,a,2,function()
  item.cResRef.get=function()return 'AROW02' end
  return st
end)
must_hold(snapshot,'EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE')
s,a,st=inventory_fixture(9,'SHLD01')
item=s.m_equipment.m_items:get(9)
snapshot=M.observe(s,a,2,function()
  item.cResRef.get=function()return 'SHLD02' end
  return st
end)
must_hold(snapshot,'EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE')
s,a,st=inventory_fixture(12,'AROW01')
item=s.m_equipment.m_items:get(12)
snapshot=M.observe(s,a,2,function()
  item.m_useCount1=16
  return st
end)
must_hold(snapshot,'EQUIPMENT_OR_AMMO_CHANGED_DURING_CAPTURE')
s,a,st,_,setfail=inventory_fixture(11,'AROW01')
snapshot=M.observe(s,a,2,function()setfail(true);return st end)
must_hold(snapshot,'R2_RECHECK_INCOMPLETE')
s,a,st=inventory_fixture(9,'SHLD01')
local valid=M.observe(s,a,2,function()return st end)
check(valid.status=='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE','stable raw evidence accepted')
check(valid.rawInventoryDoubleReadConsistent==true,'two-read evidence annotation')
check(valid.alternativeAPRVerified==false and valid.launcherAmmoPairVerified==false,
 'still no alternate APR or launcher proof')
local encoded=M.toConsoleJson(valid)
check(encoded:find('"offhandRaw":[{"slot":9',1,true)~=nil,'offhand serialized')
check(encoded:find('"rawInventoryDoubleReadConsistent":true',1,true)~=nil,'consistency serialized')
check(encoded:find('"alternativeAPRVerified":false',1,true)~=nil,'no false engine APR claim')
-- EEex 1.1.7 active stats branch: 0 -> m_tempStats work-in-progress.
s,a,st=fixture();s.m_bAllowEffectListCall=0
must_hold(M.observe(s,a,2,function()error('must not read temp stats')end),'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();s.m_bAllowEffectListCall=nil
must_hold(M.observe(s,a,2,function()return st end),'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();local calls=0
snapshot=M.observe(s,a,2,function()
 calls=calls+1;if calls==1 then s.m_bAllowEffectListCall=0 end
 return st end)
must_hold(snapshot,'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();calls=0
snapshot=M.observe(s,a,2,function()
 calls=calls+1;if calls==2 then st.m_nNumberOfAttacks=2 end
 return st end)
must_hold(snapshot,'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();calls=0
snapshot=M.observe(s,a,2,function()
 calls=calls+1;if calls==2 then st.m_nSTR=19 end
 return st end)
must_hold(snapshot,'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();calls=0
snapshot=M.observe(s,a,2,function()
 calls=calls+1;if calls==2 then s.m_bAllowEffectListCall=0 end
 return st end)
must_hold(snapshot,'R4_DERIVED_STATS_NOT_STABLE')
s,a,st=fixture();local stable=M.observe(s,a,2,function()return st end)
check(stable.status=='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE','stable native path candidate')
check(stable.selectedDerivedStatsDoubleReadConsistent==true,'two selected derived stats reads')
local js=M.toConsoleJson(stable)
check(type(js)=='string' and js:find('"selectedDerivedStatsDoubleReadConsistent":true',1,true)~=nil,
 'stable derived status serialized without granting APR permission')
-- x64 raw CGameAIBase queued action count is only negative evidence.
s,a,st=fixture();s.m_curAction=a;s.m_queuedActions={m_nCount=3}
local qSample=M.observe(s,a,2,function()return st end)
check(qSample.status=='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
 'queue read does not interrupt selected APR observation')
check(qSample.queueSnapshotStable==true and qSample.queuedActionsRaw==3,
 'stable engine queue count 3 recognized')
check(qSample.actionOriginVerified==false and qSample.manualEpsQueueVerified==false,
 'queue count cannot authenticate manual EPS action origin')
local qJson=M.toConsoleJson(qSample)
check(qJson:find('"queuedActionsRaw":3',1,true)~=nil,
 'bounded JSON carries engine observed queue count')
check(qJson:find('"queueNonemptyObserved":true',1,true)~=nil,
 'nonempty engine queue can be exposed for negative scheduling')
check(qJson:find('"manualEpsQueueVerified":false',1,true)~=nil,
 'zero switch authorization even if count known')
s,a,st=fixture();s.m_curAction=a;s.m_queuedActions={m_nCount=0}
local qZero=M.observe(s,a,2,function()return st end)
check(qZero.queuedActionsRaw==0 and qZero.queueSnapshotStable==true,
 'zero means raw queue count zero only')
check(M.toConsoleJson(qZero):find('"queueNonemptyObserved":false',1,true)~=nil,
 'zero queue count JSON not an EPS-free proof')
s,a,st=fixture();s.m_curAction=a;s.m_queuedActions={m_nCount=3}
local changed=M.observe(s,a,2,function()
 s.m_queuedActions.m_nCount=4;return st end)
check(changed.status=='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
 'queue transition does not invalidate selected-only APR observation')
check(changed.queueSnapshotStable==false and changed.queuedActionsRaw==nil,
 'queue changed between two observer reads fails closed')
check(M.toConsoleJson(changed):find('"queuedActionsRaw":null',1,true)~=nil,
 'no stale queue count exposed')
s,a,st=fixture();s.m_curAction=a;s.m_queuedActions={m_nCount=900}
local badQ=M.observe(s,a,2,function()return st end)
check(badQ.queueSnapshotStable==false and badQ.queuedActionsRaw==nil,
 'invalid queue count never gives a false raw queue observation')
print('R27 '..n..' source-only one-callback tests PASS')
