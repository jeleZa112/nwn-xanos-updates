local file='M_BGXW3_R41_LINK_SOURCE_ONLY.lua'
local checks=0
local function check(label,f)
 local ok,e=pcall(f)
 if not ok then error(label..': '..tostring(e)) end
 checks=checks+1
end
local TOKEN='BGXAI_R41_GUARDED_TYPED_INSTALL_APPROVED'
local function load()
 assert(rawget(_G,'BGXW3_EEexSessionGate')==nil)
 return assert(loadfile(file))()
end
local function fixture()
 local sprite={m_id=1234}
 local lv={BGXW3ARM=0,BGXW3TAG=0,BGXW3TRY=0,BGXW3QST=0,BGXW3QTM=0,BGXW3MAX=0}
 local listeners={destroyed={},loaded={},pressed={}}
 local keys={F12=1,['Left Ctrl']=2,['Right Ctrl']=3,['Left Alt']=4,['Right Alt']=5,['Left Shift']=6,['Right Shift']=7}
 local down={[2]=true,[4]=true,[6]=true}
 local snapshot={actorId=1234,portraitIndex=1,scriptName='*GCLERIC',classRaw=3,kitRaw=16384,
   strength=12,sourceResref='STAF01',sourceSlot=20,targetSlot=35,sourceUnique=true,
   targetEmpty=true,offhandEmpty=true,currentActionIdle=true,queueEmpty=true,
   combatCounter=0,visibleEnemy=false,modalNone=true,epsSpellCastCooldownExpired=true,
   noInterruptionFlags=true,itemCurrentShaVerified=true,itemEngineUsable=true,
   activeEffectsChecked=true,partyPortraitSame=true,selectedActorSame=true}
 local selected=sprite
 local p={preGameStartupVerified=true,runtimeItemUsabilityVerified=true,
  runtimeEffectsVerified=true,scriptOwnerVerified=true,manualEpsSafetyVerified=true,
  addDestroyed=function(fn)table.insert(listeners.destroyed,fn)end,
  addLoaded=function(fn)table.insert(listeners.loaded,fn)end,
  addPressed=function(fn)table.insert(listeners.pressed,fn)end,
  getLocal=function(_,key)return lv[key]end,
  setLocal=function(_,key,val)lv[key]=val end,
  getPortraitSprite=function(index)if index==1 then return selected end end,
  keyFromName=function(name)return keys[name]end,
  isDown=function(k)return down[k]==true end,
  capture=function(_)return snapshot end}
 local function loaded(s)
  for _,fn in ipairs(listeners.loaded) do fn(s or sprite) end
 end
 local function destroyed()
  for _,fn in ipairs(listeners.destroyed) do fn() end
 end
 local function replacePortrait(s) selected=s end
 return p,listeners,lv,sprite,snapshot,loaded,destroyed,replacePortrait
end
check('import is inert and not armed',function()
 local M=load();assert(not M.registered and M.ordersSent==0)
 assert(M.getStatus().status=='SOURCE_ONLY_UNREGISTERED')
 assert(rawget(_G,'BGXW3_EEexSessionGate')==nil)
end)
check('no typed approval',function()
 local M=load();local p,ls=fixture()
 assert(M.prepare(p,'+').status=='HOLD_TYPED_INSTALL_APPROVAL_REQUIRED')
 assert(#ls.loaded==0 and #ls.destroyed==0 and #ls.pressed==0)
end)
check('missing live runtime proof holds',function()
 local M=load();local p,ls=fixture();p.runtimeEffectsVerified=nil
 assert(M.prepare(p,TOKEN).status=='HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING')
 assert(#ls.loaded==0 and #ls.destroyed==0 and #ls.pressed==0)
end)
check('global collision remains untouched',function()
 local M=load();local p,ls=fixture();local fn=function()return true end
 rawset(_G,'BGXW3_EEexSessionGate',fn)
 assert(M.prepare(p,TOKEN).status=='HOLD_GLOBAL_GATE_COLLISION')
 assert(rawget(_G,'BGXW3_EEexSessionGate')==fn and #ls.loaded==0)
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('first only R40 hooks no gesture / no global until Jagan loaded',function()
 local M=load();local p,ls,lv,spr,snap,loaded=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 assert(#ls.loaded==1 and #ls.destroyed==1 and #ls.pressed==0)
 assert(rawget(_G,'BGXW3_EEexSessionGate')==nil)
 loaded(spr)
 assert(#ls.pressed==1 and type(BGXW3_EEexSessionGate)=='function')
 assert(BGXW3_EEexSessionGate()==false and M.getStatus().ordersSent==0)
 assert(M.prepare(p,TOKEN).status=='HOLD_ALREADY_PREPARED')
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('non-Jagan loaded sprite does not bind any R39 gate',function()
 local M=load();local p,ls,lv,spr,snap,loaded=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 loaded({m_id=888})
 assert(#ls.pressed==0 and rawget(_G,'BGXW3_EEexSessionGate')==nil)
 loaded(spr)
 assert(#ls.pressed==1)
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('stale LOCALS arm fails without gesture; R40 clears before bind',function()
 local M=load();local p,ls,lv,spr,snap,loaded=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 lv.BGXW3ARM=1;lv.BGXW3TAG=2110908191
 loaded(spr)
 assert(lv.BGXW3ARM==0 and lv.BGXW3TAG==0)
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==false)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('one mocked gesture authorizes only Lua predicate, not an engine order',function()
 local M=load();local p,ls,lv,spr,snap,loaded=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 loaded(spr)
 assert(ls.pressed[1](1,false)==true)
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==true) -- mocked eligibility! not LIVE proof
 assert(M.getStatus().ordersSent==0)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('destroyed epoch invalidates token before next save loads',function()
 local M=load();local p,ls,lv,spr,snap,loaded,destroyed=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 loaded(spr)
 assert(ls.pressed[1](1,false)==true)
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==true)
 destroyed()
 assert(BGXW3_EEexSessionGate()==false)
 loaded(spr)
 assert(BGXW3_EEexSessionGate()==false)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('no capture API denies initial registration',function()
 local M=load();local p,ls=fixture();p.capture=nil
 assert(M.prepare(p,TOKEN).status=='HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING')
 assert(#ls.loaded==0)
end)
check('R40 reset write fails, no R39 binding',function()
 local M=load();local p,ls,lv,spr,snap,loaded=fixture()
 p.setLocal=function()error('disk failure')end
 assert(M.prepare(p,TOKEN).status=='R41_R40_HOOKS_WAITING_FOR_VERIFIED_JAGAN_LOAD')
 lv.BGXW3ARM=1
 loaded(spr)
 assert(#ls.pressed==0 and rawget(_G,'BGXW3_EEexSessionGate')==nil)
end)
print('R41 LINK INTEGRATION '..checks..'/'..checks..' PASS (SOURCE ONLY, NO DEPLOY)')
