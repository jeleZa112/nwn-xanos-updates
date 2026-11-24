-- R27 real original R2 and R4 cores via deterministic composition, no EEex/game.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(folder..'BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua')
local n=0
local function check(yes,what)
 n=n+1
 assert(yes,'test '..n..' FAILED: '..what)
end
local function fixture()
 local stats=setmetatable({m_nNumberOfAttacks=7},{__index=function() return 1 end})
 local sprite={m_id=1001,m_equipment={m_selectedWeapon=35,
  m_selectedWeaponAbility=0,m_items={get=function() return nil end}}}
 local action={m_actionID=3}
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
check(z.reason=='CURRENT_SELECTED_APR_UNAVAILABLE','no APR reject')
s,a,st=fixture()
z=M.observe(s,a,2,function() error('fake stats API failure') end)
check(z.reason=='CURRENT_SELECTED_APR_UNAVAILABLE','stats API fail safe')
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
check(json:find('"dispatchAuthorized":false',1,true)~=nil,'JSON never authorizes dispatch')
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
print('R27 '..n..' source-only one-callback tests PASS')
