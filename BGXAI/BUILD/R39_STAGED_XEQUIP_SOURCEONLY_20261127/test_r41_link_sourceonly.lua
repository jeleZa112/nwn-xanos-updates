local file='M_BGXW3_R41_LINK_SOURCE_ONLY.lua'
local checks=0
local function check(label, f)
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
 local localVariables={BGXW3ARM=0,BGXW3TAG=0,BGXW3TRY=0,BGXW3QST=0,BGXW3QTM=0,BGXW3MAX=0}
 local listeners={destroyed={},loaded={},pressed={}}
 local keys={F12=1,['Left Ctrl']=2,['Right Ctrl']=3,['Left Alt']=4,['Right Alt']=5,['Left Shift']=6,['Right Shift']=7}
 local down={[2]=true,[4]=true,[6]=true}
 local ss={actorId=1234,portraitIndex=1,scriptName='*GCLERIC',classRaw=3,kitRaw=16384,
   strength=12,sourceResref='STAF01',sourceSlot=20,targetSlot=35,sourceUnique=true,
   targetEmpty=true,offhandEmpty=true,currentActionIdle=true,queueEmpty=true,
   combatCounter=0,visibleEnemy=false,modalNone=true,epsSpellCastCooldownExpired=true,
   noInterruptionFlags=true,itemCurrentShaVerified=true,itemEngineUsable=true,
   activeEffectsChecked=true,partyPortraitSame=true,selectedActorSame=true}
 local p={preGameStartupVerified=true,runtimeItemUsabilityVerified=true,
  runtimeEffectsVerified=true,scriptOwnerVerified=true,manualEpsSafetyVerified=true,
  addDestroyed=function(fn)table.insert(listeners.destroyed,fn)end,
  addLoaded=function(fn)table.insert(listeners.loaded,fn)end,
  addPressed=function(fn)table.insert(listeners.pressed,fn)end,
  getLocal=function(_,key)return localVariables[key]end,
  setLocal=function(_,key,val)localVariables[key]=val end,
  getPortraitSprite=function(index)if index==1 then return sprite end end,
  keyFromName=function(name)return keys[name]end,
  isDown=function(k)return down[k]==true end,
  capture=function(_)return ss end,
 }
 return p,listeners,localVariables,sprite,ss
end
check('import is inert and not armed',function()
 local M=load();assert(not M.registered and M.ordersSent==0)
 assert(M.getStatus().status=='SOURCE_ONLY_UNREGISTERED')
 assert(rawget(_G,'BGXW3_EEexSessionGate')==nil)
end)
check('no typed approval',function()
 local M=load();local p,ls=fixture()
 assert(M.prepare(p,'+') .status=='HOLD_TYPED_INSTALL_APPROVAL_REQUIRED')
 assert(#ls.loaded==0 and #ls.destroyed==0 and #ls.pressed==0)
end)
check('no pregame or missing proof',function()
 local M=load();local p,ls=fixture();p.runtimeEffectsVerified=nil
 assert(M.prepare(p,TOKEN).status=='HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING')
 assert(#ls.loaded==0 and #ls.destroyed==0 and #ls.pressed==0)
end)
check('existing function collision preserved',function()
 local M=load();local p,ls=fixture()
 local fn=function()return true end
 rawset(_G,'BGXW3_EEexSessionGate',fn)
 assert(M.prepare(p,TOKEN).status=='HOLD_GLOBAL_GATE_COLLISION')
 assert(rawget(_G,'BGXW3_EEexSessionGate')==fn and #ls.loaded==0)
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('two lifecycle hooks before one keyboard and bind last',function()
 local M=load();local p,ls=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
 assert(#ls.loaded==1 and #ls.destroyed==1 and #ls.pressed==1)
 assert(type(rawget(_G,'BGXW3_EEexSessionGate'))=='function')
 assert(BGXW3_EEexSessionGate()==false and M.getStatus().ordersSent==0)
 assert(M.prepare(p,TOKEN).status=='HOLD_ALREADY_STARTED')
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('stale LOCALS arm fails without gesture and R40 clears on load',function()
 local M=load();local p,ls,lv,spr=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
 lv.BGXW3ARM=1;lv.BGXW3TAG=2110908191
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==false)
 for _,fn in ipairs(ls.loaded) do fn(spr) end
 assert(lv.BGXW3ARM==0 and lv.BGXW3TAG==0)
 assert(BGXW3_EEexSessionGate()==false)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('gesture mock alone never enqueues game orders',function()
 local M=load();local p,ls,lv,spr=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
 assert(ls.pressed[1](1,false)==true)
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==true) -- mock fixture eligibility only
 assert(M.getStatus().ordersSent==0)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('destroyed session epoch invalidates formerly valid gesture',function()
 local M=load();local p,ls,lv,spr=fixture()
 assert(M.prepare(p,TOKEN).status=='R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
 assert(ls.pressed[1](1,false)==true)
 _G.EEex_LuaTrigger_Object=spr
 assert(BGXW3_EEexSessionGate()==true)
 for _,fn in ipairs(ls.destroyed) do fn() end
 assert(BGXW3_EEexSessionGate()==false)
 _G.EEex_LuaTrigger_Object=nil
 rawset(_G,'BGXW3_EEexSessionGate',nil)
end)
check('missing capture blocks bridge',function()
 local M=load();local p,ls=fixture();p.capture=nil
 assert(M.prepare(p,TOKEN).status=='HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING')
 assert(#ls.loaded==0)
end)
print('R41 LINK INTEGRATION '..checks..'/'..checks..' PASS (SOURCE ONLY)')
