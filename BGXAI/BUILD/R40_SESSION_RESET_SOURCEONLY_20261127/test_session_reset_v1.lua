-- R40 adversarial Lua mocks; no EEex or game needed.
local M=dofile('M_BGXW3_SESSION_RESET_V1.lua')
local TOTAL=0
local function check(label,fn)
 local ok,e=pcall(fn)
 if not ok then error(label..': '..tostring(e)) end
 TOTAL=TOTAL+1
end
local keys={'BGXW3ARM','BGXW3TAG','BGXW3TRY','BGXW3QST','BGXW3QTM','BGXW3MAX'}
local function actor(values)
 local a={nonPilot=456}
 for _,k in ipairs(keys) do a[k]=0 end
 for k,v in pairs(values or {}) do a[k]=v end
 return a
end
local function ports()
 local p={loadedCallbacks={},destroyedCallbacks={},getCount=0,setCount=0,
         preGameStartupVerified=true}
 p.getLocal=function(a,k) p.getCount=p.getCount+1;return a[k] end
 p.setLocal=function(a,k,v) p.setCount=p.setCount+1;a[k]=v end
 p.addLoaded=function(cb) table.insert(p.loadedCallbacks,cb) end
 p.addDestroyed=function(cb) table.insert(p.destroyedCallbacks,cb) end
 return p
end
local APPROVAL='ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD'
check('not auto registered',function()assert(not M.registered and M.ordersSent==0)end)
check('reject absent approval',function()
 assert(M.register(ports(),nil).status=='HOLD_NO_EXACT_INSTALL_APPROVAL')
end)
check('reject invented approval',function()
 assert(M.register(ports(),true).status=='HOLD_NO_EXACT_INSTALL_APPROVAL')
end)
check('reject missing pregame proof',function()
 local p=ports();p.preGameStartupVerified=nil
 assert(M.register(p,APPROVAL).status=='HOLD_PRE_GAME_REGISTRATION_UNPROVEN')
end)
check('reject missing API',function()
 assert(M.register({preGameStartupVerified=true},APPROVAL).status=='HOLD_REQUIRED_EEEX_APIS_MISSING')
end)
check('reject missing sprite',function()
 local p=ports();assert(M.resetIfPending(nil,p).status=='HOLD_NO_LOCAL_PORTS')
end)
check('clean sprite no writes',function()
 local p=ports();local a=actor()
 assert(M.resetIfPending(a,p).status=='NO_PENDING_ARM_ON_SPRITE_LOAD')
 assert(p.setCount==0 and a.nonPilot==456)
end)
check('pending arm resets all six',function()
 local p=ports();local a=actor({BGXW3ARM=1,BGXW3TAG=2110908191,
 BGXW3TRY=0,BGXW3QST=1,BGXW3QTM=90,BGXW3MAX=120})
 local r=M.resetIfPending(a,p)
 assert(r.status=='PENDING_ARM_CLEARED_ON_SPRITE_LOAD' and p.setCount==6)
 for _,k in ipairs(keys) do assert(a[k]==0) end
 assert(a.nonPilot==456)
end)
check('fails if ARM reset throws',function()
 local p=ports();local a=actor({BGXW3ARM=1,BGXW3TAG=2110908191})
 p.setLocal=function(_,k,_) if k=='BGXW3ARM' then error('readonly') end end
 assert(M.resetIfPending(a,p).status=='HOLD_ARM_CLEAR_FAILED_NOT_SAFE')
 assert(a.BGXW3ARM==1)
end)
check('fails if ARM readback remains set',function()
 local p=ports();local a=actor({BGXW3ARM=1,BGXW3TAG=3})
 p.setLocal=function(_,_,_) end
 assert(M.resetIfPending(a,p).status=='HOLD_ARM_CLEAR_FAILED_NOT_SAFE')
end)
check('partial failure leaves ARM zero',function()
 local p=ports();local a=actor({BGXW3ARM=1,BGXW3TAG=2110908191})
 p.setLocal=function(a,k,v)
   if k=='BGXW3TAG' then error('blocked') else a[k]=v end end
 assert(M.resetIfPending(a,p).status=='HOLD_PARTIAL_CLEAR_ARM_CONFIRMED_ZERO')
 assert(a.BGXW3ARM==0 and a.BGXW3TAG~=0)
end)
check('invalid getter does not write',function()
 local p=ports();local a=actor({BGXW3ARM=1})
 p.getLocal=function(a,k) if k=='BGXW3QTM' then return nil end return a[k] end
 assert(M.resetIfPending(a,p).status=='HOLD_LOCAL_READ_UNAVAILABLE')
 assert(p.setCount==0)
end)
check('NaN/boolean getter rejects',function()
 for _,v in ipairs({true,false,0/0}) do
  local p=ports();local a=actor({BGXW3ARM=v})
  assert(M.resetIfPending(a,p).status=='HOLD_LOCAL_READ_UNAVAILABLE')
  assert(p.setCount==0)
 end
end)
check('failed destroyed registration no loaded',function()
 local p=ports();p.addDestroyed=function()error('unavailable')end
 assert(M.register(p,APPROVAL).status=='HOLD_DESTROYED_HOOK_FAILED')
 assert(not M.registered)
end)
check('partial failure listener remains inert',function()
 local p=ports();p.addLoaded=function()error('failure')end
 assert(M.register(p,APPROVAL).status=='HOLD_LOADED_HOOK_FAILED_PARTIAL_INERT')
 assert(not M.registered)
 local before=M.getStatus().destroyedEvents
 p.destroyedCallbacks[1]()
 assert(M.getStatus().destroyedEvents==before)
end)
local registered=ports()
check('registration exact approval once',function()
 local s=M.register(registered,APPROVAL)
 assert(s.status=='RESET_ONLY_LIFECYCLE_HOOKS_REGISTERED_NO_ARM')
 assert(M.registered and #registered.loadedCallbacks==1 and #registered.destroyedCallbacks==1)
end)
check('duplicate registration rejected',function()
 assert(M.register(registered,APPROVAL).status=='HOLD_ALREADY_REGISTERED')
 assert(#registered.loadedCallbacks==1)
end)
check('loaded callback clears stale arm',function()
 local a=actor({BGXW3ARM=1,BGXW3TAG=2110908191})
 registered.loadedCallbacks[1](a)
 assert(a.BGXW3ARM==0 and a.BGXW3TAG==0)
 assert(M.getStatus().status=='PENDING_ARM_CLEARED_ON_SPRITE_LOAD')
end)
check('clean load does not modify actor',function()
 local a=actor({nonPilot=33})
 local prev=registered.setCount
 registered.loadedCallbacks[1](a)
 assert(registered.setCount==prev and a.nonPilot==33)
end)
check('destroy event invalidates LUA session epoch',function()
 local old=M.getStatus().sessionEpoch
 registered.destroyedCallbacks[1]()
 assert(M.getStatus().sessionEpoch==old+1)
 assert(M.getStatus().status=='SESSION_DESTROYED_NO_ACTOR_BINDING')
end)
check('loaded after destroyed still clears',function()
 local a=actor({BGXW3ARM=1,BGXW3TAG=2110908191})
 registered.loadedCallbacks[1](a)
 assert(a.BGXW3ARM==0 and a.BGXW3TAG==0)
end)
check('no dispatch or arm',function()
 local r=M.getStatus()
 assert(r.dispatchAuthorized==false and r.armAuthorized==false and r.ordersSent==0)
 assert(M.autoArm==false)
end)
print('R40_SESSION_RESET_SOURCE_ONLY: '..TOTAL..'/'..TOTAL..' PASS')
