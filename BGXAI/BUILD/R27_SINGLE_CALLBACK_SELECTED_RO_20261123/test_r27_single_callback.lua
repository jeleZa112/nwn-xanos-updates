-- R27 real original R2 and R4 cores via deterministic composition, no EEex/game.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(folder..'BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO.lua')
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
print('R27 '..n..' source-only one-callback tests PASS')
