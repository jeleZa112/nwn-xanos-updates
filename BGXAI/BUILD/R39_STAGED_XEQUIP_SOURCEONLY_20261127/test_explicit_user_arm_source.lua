-- SOURCE-ONLY behavioral checks through fake EEex ports. Never modifies EET.
local file='M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua'
local M=assert(loadfile(file))()
local tests,passed=0,0
local function check(label,fn)
 tests=tests+1
 local ok,err=pcall(fn)
 if not ok then error(label..': '..tostring(err)) end
 passed=passed+1
end
local function eq(a,b)assert(a==b,tostring(a)..' ~= '..tostring(b))end
local function make(opts)
 opts=opts or {}
 local sprite={m_id=1234}
 local locals={BGXW3ARM=opts.oldArm or 0,BGXW3TAG=0,BGXW3TRY=0,
 BGXW3QST=0,BGXW3QTM=0,BGXW3MAX=0}
 local regs={}
 local keys={F12=1,['Left Ctrl']=2,['Right Ctrl']=3,
 ['Left Alt']=4,['Right Alt']=5,['Left Shift']=6,['Right Shift']=7}
 local pressed={[2]=true,[4]=true,[6]=true}
 local epoch=opts.epoch or 1
 local tries=0
 local s={actorId=1234,portraitIndex=1,scriptName='*GCLERIC',
 classRaw=3,kitRaw=16384,strength=12,sourceResref='STAF01',sourceSlot=20,
 targetSlot=35,sourceUnique=true,targetEmpty=true,offhandEmpty=true,
 currentActionIdle=true,queueEmpty=true,combatCounter=0,visibleEnemy=false,
 modalNone=true,epsSpellCastCooldownExpired=true,noInterruptionFlags=true,
 itemCurrentShaVerified=true,itemEngineUsable=true,activeEffectsChecked=true,
 partyPortraitSame=true,selectedActorSame=true}
 local ports={
 addPressed=function(f,repeats)
   eq(repeats,false);regs[#regs+1]=f
   if opts.registrationReturnsFalse then return false end
   if opts.registrationEpochFlip then epoch=epoch+1 end
 end,
 keyFromName=function(k)return keys[k]end,
 isDown=function(k)return pressed[k]end,
 getEpoch=function()return epoch end,
 proveLifecycle=function()return opts.guardReady~=false end,
 getPortraitSprite=function(i)eq(i,1);return sprite end,
 getLocal=function(_s,k)return locals[k]end,
 setLocal=function(_s,k,v)
   if opts.writeFailure==k then error('WRITE_FAILURE') end
   if opts.writeIgnored==k then return end
   locals[k]=v
 end,
 capture=function(_s)
   tries=tries+1
   if opts.flipEpochAtCapture==tries then epoch=epoch+1 end
   local x={}
   for k,v in pairs(s)do x[k]=v end
   if opts.badField then x[opts.badField]=opts.badValue end
   if opts.changedOn and tries==opts.changedOn then x.actorId=1235 end
   return x
 end,
 onResult=function(x)opts.result=x end,
 }
 return {ports=ports,locals=locals,keys=keys,pressed=pressed,regs=regs,
         sprite=sprite,s=s,opts=opts,fire=function(self,k,r)
          eq(#regs,1);return regs[1](k or keys.F12,r or false)
         end, setEpoch=function(n)epoch=n end}
end
local token='INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD'
check('source only',function()eq(M.sourceOnly,true);eq(M.registered,false)end)
check('no keyboard registration without typed approval',function()
 local p=make();eq(M.prepare(p.ports,'x').status,'HOLD_EXACT_TYPED_INSTALL_APPROVAL_REQUIRED');eq(#p.regs,0)
end)
check('no lifecycle guard -> no keyboard listener',function()
 local p=make({guardReady=false})
 eq(M.prepare(p.ports,token).status,'HOLD_SESSION_RESET_ORDER_UNPROVEN');eq(#p.regs,0)
end)
check('no bare ports',function()
 eq(M.prepare({},token).status,'HOLD_REQUIRED_PORTS_MISSING')
end)
check('explicit keyboard register once',function()
 local p=make();eq(M.prepare(p.ports,token).status,'REGISTERED_GESTURE_ONLY_NO_ARM')
 _G.P=p
 eq(#p.regs,1);eq(p.locals.BGXW3ARM,0)
end)
check('reject duplicate callbacks',function()
 eq(M.prepare(P.ports,token).status,'HOLD_DUPLICATE_HOTKEY_REGISTRATION')
end)
check('ignore F11',function()
 eq(P:fire(20),false);eq(P.locals.BGXW3ARM,0)
end)
check('ignore auto repeat',function()
 eq(P:fire(P.keys.F12,true),false);eq(P.locals.BGXW3ARM,0)
end)
check('ignore Ctrl+Alt without Shift',function()
 P.pressed[P.keys['Left Shift']]=false
 eq(P:fire(),false);eq(P.locals.BGXW3ARM,0)
 P.pressed[P.keys['Left Shift']]=true
end)
check('ignore Alt+Shift without Ctrl',function()
 P.pressed[P.keys['Left Ctrl']]=false
 eq(P:fire(),false);eq(P.locals.BGXW3ARM,0)
 P.pressed[P.keys['Left Ctrl']]=true
end)
check('ignore Ctrl+Shift without Alt',function()
 P.pressed[P.keys['Left Alt']]=false
 eq(P:fire(),false);eq(P.locals.BGXW3ARM,0)
 P.pressed[P.keys['Left Alt']]=true
end)
check('accept exactly one user chord',function()
 eq(P:fire(),true);eq(P.locals.BGXW3ARM,1)
 eq(P.locals.BGXW3TAG,2110908191)
 eq(P.locals.BGXW3TRY,0);eq(P.locals.BGXW3QST,0)
 eq(P.opts.result.status,'EXPLICIT_GESTURE_ARMED_ONCE_BAF_WILL_RECHECK')
end)
check('do not rearm on second key press',function()
 eq(P:fire(),true);eq(P.opts.result.status,'HOLD_ONE_ATTEMPT_PER_SESSION')
 eq(P.locals.BGXW3ARM,1) -- no write to another attempt
end)
check('no gameplay engine action from module',function()
 eq(M.ordersSent,0);eq(M.dispatchAuthorized,false)
end)
local function newCore()
 return assert(loadfile(file))()
end
local function onceWith(options)
 local q=newCore()
 local p=make(options or {})
 eq(q.prepare(p.ports,token).status,'REGISTERED_GESTURE_ONLY_NO_ARM')
 eq(p:fire(),true)
 return p
end
check('target occupied => no arm',function()
 local p=onceWith({badField='targetEmpty',badValue=false})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('not unique item => no arm',function()
 local p=onceWith({badField='sourceUnique',badValue=false})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('weapon engine usability unknown => no arm',function()
 local p=onceWith({badField='itemEngineUsable',badValue=nil})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('kit mismatch => no arm',function()
 local p=onceWith({badField='kitRaw',badValue=0})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('class mismatch => no arm',function()
 local p=onceWith({badField='classRaw',badValue=1})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('queue has EPS/manual action => no arm',function()
 local p=onceWith({badField='queueEmpty',badValue=false})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('other actor selected => no arm',function()
 local p=onceWith({badField='selectedActorSame',badValue=false})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('enemy visible => no arm',function()
 local p=onceWith({badField='visibleEnemy',badValue=true})
 eq(p.opts.result.status,'HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE')
 eq(p.locals.BGXW3ARM,0)
end)
check('actor changes between first and second snapshot => no arm',function()
 local p=onceWith({changedOn=2})
 eq(p.opts.result.status,'HOLD_DOUBLE_SNAPSHOT_UNSTABLE')
 eq(p.locals.BGXW3ARM,0)
end)
check('actor changes immediately before ARM => no arm',function()
 local p=onceWith({changedOn=3})
 eq(p.opts.result.status,'HOLD_ACTOR_OR_SESSION_CHANGED_BEFORE_ARM')
 eq(p.locals.BGXW3ARM,0)
end)
check('actor changes after ARM => arm immediately cleared',function()
 local p=onceWith({changedOn=4})
 eq(p.opts.result.status,'HOLD_CHANGED_AFTER_ARM_DISARMED')
 eq(p.locals.BGXW3ARM,0)
end)
check('lifecycle epoch changes before ARM => no arm',function()
 local p=onceWith({flipEpochAtCapture=3})
 eq(p.opts.result.status,'HOLD_ACTOR_OR_SESSION_CHANGED_BEFORE_ARM')
 eq(p.locals.BGXW3ARM,0)
end)
check('lifecycle epoch changes after ARM => arm immediately cleared',function()
 local p=onceWith({flipEpochAtCapture=4})
 eq(p.opts.result.status,'HOLD_CHANGED_AFTER_ARM_DISARMED')
 eq(p.locals.BGXW3ARM,0)
end)
check('stale saved ARM detected and cleared, no rearm',function()
 local p=onceWith({oldArm=1})
 eq(p.opts.result.status,'HOLD_STALE_ARM_FOUND_DISARMED_NO_REARM')
 eq(p.locals.BGXW3ARM,0)
end)
check('failure while writing tag leaves ARM zero',function()
 local p=onceWith({writeFailure='BGXW3TAG'})
 eq(p.opts.result.status,'HOLD_PREARM_FIELDS_NOT_VERIFIED')
 eq(p.locals.BGXW3ARM,0)
end)
check('silent failed tag write readback leaves ARM zero',function()
 local p=onceWith({writeIgnored='BGXW3TAG'})
 eq(p.opts.result.status,'HOLD_PREARM_FIELDS_NOT_VERIFIED')
 eq(p.locals.BGXW3ARM,0)
end)
check('final ARM write failure does not authorize',function()
 local p=onceWith({writeFailure='BGXW3ARM'})
 eq(p.opts.result.status,'HOLD_FINAL_ARM_READBACK_FAILED')
 eq(p.locals.BGXW3ARM,0)
end)
check('registration silently rejected does not enable',function()
 local core=newCore();local p=make({registrationReturnsFalse=true})
 eq(core.prepare(p.ports,token).status,'HOLD_HOTKEY_REGISTRATION_FAILED')
 eq(core.registered,false)
 eq(p:fire(),false)
 eq(p.locals.BGXW3ARM,0)
end)
check('registration session changed -> callback inert',function()
 local core=newCore();local p=make({registrationEpochFlip=true})
 eq(core.prepare(p.ports,token).status,'HOLD_LIFECYCLE_CHANGED_DURING_HOTKEY_REGISTER')
 eq(core.registered,false)
 eq(p:fire(),false)
 eq(p.locals.BGXW3ARM,0)
end)
print('BGXAI R39 EXPLICIT USER GESTURE mock PASS '..passed..'/'..tests)
