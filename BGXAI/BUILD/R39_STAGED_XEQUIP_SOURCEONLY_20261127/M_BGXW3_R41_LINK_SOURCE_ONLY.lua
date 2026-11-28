-- BGXAI R41 source-only, not installed. Do NOT copy into EET without typed guard.
-- Two original immutable modules embedded, not reimplemented.
local Reset=(function()
-- BGXAI R40: SOURCE ONLY. Never import into a live game without typed approval.
-- Lifecycle guard for the pre-existing R39 Jagan staged-XEquip BAF.
-- Registers NO action-start listener; optional lifecycle hooks are separate.
-- Does not ARM, equip, send game orders, alter BCS, or claim readiness.
local M={schema='BGXAI_R40_SESSION_RESET_SOURCE_ONLY_V1',sourceOnly=true,
         registered=false,autoArm=false,dispatchAuthorized=false,ordersSent=0}
local KEYS={'BGXW3ARM','BGXW3TAG','BGXW3TRY','BGXW3QST','BGXW3QTM','BGXW3MAX'}
local APPROVAL='ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD'
local state={epoch=1,loaded=0,resets=0,destroyed=0,last='NOT_REGISTERED'}

local function validInt(v)
 return type(v)=='number' and v==v and v%1==0 and v>=-2147483648 and v<=2147483647
end
local function status(s)
 return {schema=M.schema,status=s,sessionEpoch=state.epoch,
         spriteLoadEvents=state.loaded,spriteResetEvents=state.resets,
         destroyedEvents=state.destroyed,sourceOnly=true,
         armAuthorized=false,dispatchAuthorized=false,ordersSent=0}
end
local function safeRead(get,sprite,key)
 local ok,x=pcall(get,sprite,key)
 if not ok or not validInt(x) then return nil end
 return x
end
local function safeClear(get,set,sprite,key)
 local ok=pcall(set,sprite,key,0)
 if not ok then return false end
 return safeRead(get,sprite,key)==0
end

-- Fail closed: verify read APIs before writes; clear ARM FIRST and read it back.
-- Remaining fields may fail to clear, but no XEquip block can run if ARM is 0.
function M.resetIfPending(sprite,ports)
 if sprite==nil or type(ports)~='table' or
    type(ports.getLocal)~='function' or type(ports.setLocal)~='function' then
  return status('HOLD_NO_LOCAL_PORTS') end
 local before={}
 local pending=false
 for _,key in ipairs(KEYS) do
  local v=safeRead(ports.getLocal,sprite,key)
  if v==nil then return status('HOLD_LOCAL_READ_UNAVAILABLE') end
  before[key]=v
  if v~=0 then pending=true end
 end
 if not pending then return status('NO_PENDING_ARM_ON_SPRITE_LOAD') end
 if not safeClear(ports.getLocal,ports.setLocal,sprite,KEYS[1]) then
  return status('HOLD_ARM_CLEAR_FAILED_NOT_SAFE')
 end
 for i=2,#KEYS do
  if not safeClear(ports.getLocal,ports.setLocal,sprite,KEYS[i]) then
   return status('HOLD_PARTIAL_CLEAR_ARM_CONFIRMED_ZERO')
  end
 end
 state.resets=state.resets+1
 return status('PENDING_ARM_CLEARED_ON_SPRITE_LOAD')
end

function M.onGameDestroyed()
 -- Sprite pointers are invalid after destroying a game. Clear only Lua state.
 state.epoch=state.epoch+1
 state.destroyed=state.destroyed+1
 state.last='SESSION_DESTROYED_NO_ACTOR_BINDING'
 return status(state.last)
end
function M.onSpriteLoaded(sprite,ports)
 state.loaded=state.loaded+1
 local r=M.resetIfPending(sprite,ports)
 state.last=r.status
 return r
end

function M.register(ports,exactInstallerApproval)
 if exactInstallerApproval~=APPROVAL then return status('HOLD_NO_EXACT_INSTALL_APPROVAL') end
 if M.registered then return status('HOLD_ALREADY_REGISTERED') end
 if type(ports)~='table' or ports.preGameStartupVerified~=true then
  return status('HOLD_PRE_GAME_REGISTRATION_UNPROVEN') end
 if type(ports)~='table' or
   type(ports.addDestroyed)~='function' or
   type(ports.addLoaded)~='function' or
   type(ports.getLocal)~='function' or
   type(ports.setLocal)~='function' then
  return status('HOLD_REQUIRED_EEEX_APIS_MISSING') end
 local enabled=false
 local okD=pcall(ports.addDestroyed,function()
  if enabled then M.onGameDestroyed() end
 end)
 if not okD then return status('HOLD_DESTROYED_HOOK_FAILED') end
 local okL=pcall(ports.addLoaded,function(sprite)
  if enabled then M.onSpriteLoaded(sprite,ports) end
 end)
 if not okL then
  -- First callback may remain registered, but it is inert (enabled=false).
  return status('HOLD_LOADED_HOOK_FAILED_PARTIAL_INERT')
 end
 enabled=true
 M.registered=true
 state.last='RESET_ONLY_LIFECYCLE_HOOKS_REGISTERED_NO_ARM'
 return status(state.last)
end

-- The one and only user-facing updater may call this *after* separate typed
-- approval. Upstream API names verified in EEex master (not user's build).
-- This function is not called by merely importing the module.
function M.registerWithInstalledEEex(exactInstallerApproval, preGameStartupVerified)
 return M.register({
   preGameStartupVerified=preGameStartupVerified,
   addDestroyed=rawget(_G,'EEex_GameState_AddDestroyedListener'),
   addLoaded=rawget(_G,'EEex_Sprite_AddLoadedListener'),
   getLocal=rawget(_G,'EEex_Sprite_GetLocalInt'),
   setLocal=rawget(_G,'EEex_Sprite_SetLocalInt'),
 },exactInstallerApproval)
end

function M.getStatus()
 return status(state.last)
end
return M

end)()
local Armer=(function()
-- BGXAI R39 controlled first actual-inventory-transfer pilot, SOURCE ONLY.
-- NOT INSTALLED. No auto-arm, no action injection, no second action-start observer.
-- If later installed after typed approval, an explicit (non-repeat) Ctrl+Alt+Shift+F12
-- user key gesture permits ONE pending attempt for saved character *GCLERIC.
-- The pre-existing R39 BAF alone would perform XEquipItem if still safe.
-- Critical: depends on R40 load-time reset proven BEFORE AI ticks, and complete
-- live item/kit/effect/queue eligibility proved by caller's adapter. No such
-- integration proof exists yet on user's EET. This is not deploy authorization.
local M={schema='BGXAI_R39_USER_GESTURE_ARM_SOURCE_ONLY_V1',sourceOnly=true,
         registered=false,autoArm=false,installed=false,
         actionListenerRegistered=false,ordersSent=0,dispatchAuthorized=false}
local APPROVAL='INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD'
local WITNESS=2110908191
local KEYS={'BGXW3ARM','BGXW3TAG','BGXW3TRY','BGXW3QST','BGXW3QTM','BGXW3MAX'}
local COUNT={gestures=0,armed=0,holds=0,last='NOT_REGISTERED'}
local state={epoch=nil,attemptedEpoch=nil,attemptedActorId=nil,
             volatileEpoch=nil,volatileActorId=nil,volatileSprite=nil,activePorts=nil}
local function validInt(v,lo,hi)
 return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
local function ret(status)
 COUNT.last=status
 if status:match('^HOLD_') then COUNT.holds=COUNT.holds+1 end
 return {schema=M.schema,status=status,registered=M.registered,sourceOnly=true,
   installAuthorized=false,dispatchAuthorized=false,ordersSent=0,
   explicitUserGestureRequired=true,
   gesturesObserved=COUNT.gestures,oneShotArmsWrittenInMockOrFuture=COUNT.armed}
end
local function read(ports,sprite,key)
 local ok,v=pcall(ports.getLocal,sprite,key)
 if not ok or not validInt(v,-2147483648,2147483647) then return nil end
 return v
end
local function setAndVerify(ports,sprite,key,value)
 if not pcall(ports.setLocal,sprite,key,value) then return false end
 return read(ports,sprite,key)==value
end
local function canCapture(x)
 if type(x)~='table' then return false end
 return validInt(x.actorId,1,2147483647) and x.portraitIndex==1 and
    x.scriptName=='*GCLERIC' and x.classRaw==3 and x.kitRaw==16384 and
    validInt(x.strength,5,255) and x.sourceResref=='STAF01' and
    x.sourceSlot==20 and x.targetSlot==35 and x.sourceUnique==true and
    x.targetEmpty==true and x.offhandEmpty==true and
    x.currentActionIdle==true and x.queueEmpty==true and
    x.combatCounter==0 and x.visibleEnemy==false and
    x.modalNone==true and x.epsSpellCastCooldownExpired==true and
    x.noInterruptionFlags==true and x.itemCurrentShaVerified==true and
    x.itemEngineUsable==true and x.activeEffectsChecked==true and
    x.partyPortraitSame==true and x.selectedActorSame==true
end
local SNAP_KEYS={'actorId','portraitIndex','scriptName','classRaw','kitRaw',
 'strength','sourceResref','sourceSlot','targetSlot','sourceUnique',
 'targetEmpty','offhandEmpty','currentActionIdle','queueEmpty','combatCounter',
 'visibleEnemy','modalNone','epsSpellCastCooldownExpired','noInterruptionFlags',
 'itemCurrentShaVerified','itemEngineUsable','activeEffectsChecked',
 'partyPortraitSame','selectedActorSame'}
local function snapshot(ports,sprite)
 local ok,x=pcall(ports.capture,sprite)
 if not ok or not canCapture(x) then return nil end
 return x
end
local function same(a,b)
 if not a or not b then return false end
 for _,k in ipairs(SNAP_KEYS) do if a[k]~=b[k] then return false end end
 return true
end
local function armingAllowed(ports)
 -- No invented session proof: delegate to a separately verified R40 startup
 -- and installed-EEex proof adapter; return HOLD if either answer is unknown.
 local ok,a=pcall(ports.proveLifecycle)
 if not ok or a~=true then return nil end
 local ok2,e=pcall(ports.getEpoch)
 if not ok2 or not validInt(e,1,2147483647) then return nil end
 return e
end
local function disarm(ports,sprite)
 return setAndVerify(ports,sprite,KEYS[1],0)
end

local function requestOnce(ports)
 local epoch=armingAllowed(ports)
 if not epoch then return ret('HOLD_SESSION_RESET_ORDER_UNPROVEN') end
 if state.epoch~=epoch then
  state.epoch=epoch
  state.attemptedEpoch=nil
  state.attemptedActorId=nil
  state.volatileEpoch=nil
  state.volatileActorId=nil
  state.volatileSprite=nil
 end
 local ok,sprite=pcall(ports.getPortraitSprite,1)
 if not ok or sprite==nil then return ret('HOLD_PARTY_ACTOR_UNAVAILABLE') end
 local first=snapshot(ports,sprite)
 if not first then return ret('HOLD_LIVE_IDENTITY_ITEM_OR_ACTION_UNSAFE') end
 local second=snapshot(ports,sprite)
 if not same(first,second) then return ret('HOLD_DOUBLE_SNAPSHOT_UNSTABLE') end
 if state.attemptedEpoch==epoch then return ret('HOLD_ONE_ATTEMPT_PER_SESSION') end
 -- If an old ARM exists, clear it first; never override another arm attempt.
 local arm=read(ports,sprite,KEYS[1])
 if arm==nil then return ret('HOLD_OLD_ARM_READ_FAILED') end
 if arm~=0 then
  if not disarm(ports,sprite) then return ret('HOLD_OLD_ARM_DISARM_FAILED') end
  return ret('HOLD_STALE_ARM_FOUND_DISARMED_NO_REARM')
 end
 -- Two-phase write: ARM stays zero until all dependent fields read back.
 -- An exception or failed readback cannot produce a positive authorization.
 local initial={{KEYS[2],WITNESS},{KEYS[3],0},{KEYS[4],0},
                {KEYS[5],0},{KEYS[6],0}}
 for _,pair in ipairs(initial) do
  if not setAndVerify(ports,sprite,pair[1],pair[2]) then
   disarm(ports,sprite)
   return ret('HOLD_PREARM_FIELDS_NOT_VERIFIED')
  end
 end
 local third=snapshot(ports,sprite)
 local epochAgain=armingAllowed(ports)
 if not same(second,third) or epochAgain~=epoch or
    read(ports,sprite,KEYS[1])~=0 then
  disarm(ports,sprite)
  return ret('HOLD_ACTOR_OR_SESSION_CHANGED_BEFORE_ARM')
 end
 -- Do not attempt to arm again in this live session even if the transfer fails.
 state.attemptedEpoch=epoch
 state.attemptedActorId=first.actorId -- in-memory only, never emitted
 if not setAndVerify(ports,sprite,KEYS[1],1) then
  disarm(ports,sprite)
  return ret('HOLD_FINAL_ARM_READBACK_FAILED')
 end
 local fourth=snapshot(ports,sprite)
 if not same(third,fourth) or armingAllowed(ports)~=epoch then
  disarm(ports,sprite)
  return ret('HOLD_CHANGED_AFTER_ARM_DISARMED')
 end
 -- A volatile permission is NEVER saved in actor LOCALS. The exact
 -- EEex_LuaTrigger guard must see BOTH saved BAF flags and this live token.
 -- Assign only after the final verified arming snapshot has succeeded.
 state.volatileEpoch=epoch
 state.volatileActorId=first.actorId
 state.volatileSprite=sprite
 COUNT.armed=COUNT.armed+1
 return ret('EXPLICIT_GESTURE_ARMED_ONCE_BAF_WILL_RECHECK')
end

-- Only this registered keyboard callback can invoke the private requestOnce.
-- Repeated OS keydown events are ignored. It consumes only the FULL chord.
function M.prepare(ports,exactInstallerApproval)
 if exactInstallerApproval~=APPROVAL then return ret('HOLD_EXACT_TYPED_INSTALL_APPROVAL_REQUIRED') end
 if M.registered then return ret('HOLD_DUPLICATE_HOTKEY_REGISTRATION') end
 if type(ports)~='table' or type(ports.addPressed)~='function' or
    type(ports.keyFromName)~='function' or type(ports.isDown)~='function' or
    type(ports.getPortraitSprite)~='function' or
    type(ports.capture)~='function' or type(ports.getLocal)~='function' or
    type(ports.setLocal)~='function' or
    type(ports.proveLifecycle)~='function' or
    type(ports.getEpoch)~='function' then
  return ret('HOLD_REQUIRED_PORTS_MISSING') end
 local registerEpoch=armingAllowed(ports)
 if not registerEpoch then return ret('HOLD_SESSION_RESET_ORDER_UNPROVEN') end
 local function getName(n)
  local ok,k=pcall(ports.keyFromName,n)
  if not ok or not validInt(k,1,2147483647) then return nil end
  return k
 end
 local f12=getName('F12')
 local ctrl={getName('Left Ctrl'),getName('Right Ctrl')}
 local alt={getName('Left Alt'),getName('Right Alt')}
 local shift={getName('Left Shift'),getName('Right Shift')}
 if not f12 or not ctrl[1] or not ctrl[2] or not alt[1] or
    not alt[2] or not shift[1] or not shift[2] then
  return ret('HOLD_KEYCODES_UNAVAILABLE') end
 local enabled=false
 local function down(k)
  local ok,x=pcall(ports.isDown,k)
  return ok and x==true
 end
 local function callback(key,repeatFlag)
  if not enabled or key~=f12 or repeatFlag==true then return false end
  if not (down(ctrl[1]) or down(ctrl[2])) or
     not (down(alt[1]) or down(alt[2])) or
     not (down(shift[1]) or down(shift[2])) then return false end
  COUNT.gestures=COUNT.gestures+1
  local ok,x=pcall(requestOnce,ports)
  if not ok then ret('HOLD_EXCEPTION_NO_PERMISSION_GRANTED')
  elseif type(ports.onResult)=='function' then pcall(ports.onResult,x) end
  return true -- consume this one explicitly guarded key event
 end
 local ok,registrationStatus=pcall(ports.addPressed,callback,false)
 if not ok or registrationStatus==false then return ret('HOLD_HOTKEY_REGISTRATION_FAILED') end
 -- A lifecycle change during listener registration leaves an inert callback.
 if armingAllowed(ports)~=registerEpoch then
  return ret('HOLD_LIFECYCLE_CHANGED_DURING_HOTKEY_REGISTER')
 end
 enabled=true
 M.registered=true
 state.activePorts=ports
 return ret('REGISTERED_GESTURE_ONLY_NO_ARM')
end

-- Invoked ONLY by an EEex_LuaTrigger in the future guarded R39 BAF.
-- It returns false for every unapproved / stale / missing-proof state.
-- It does NOT modify LOCALS, authorize installation, or cause a game action.
-- EEex_LuaTrigger_Object must be forwarded as the aiBase argument by the
-- future typed-approved bootstrap; the source itself exports no global hook.
function M.sessionGate(aiBase)
 local ports=state.activePorts
 if not M.registered or type(ports)~='table' or aiBase==nil then return false end
 if state.volatileEpoch==nil or state.volatileActorId==nil or
    state.volatileSprite~=aiBase then return false end
 local epoch=armingAllowed(ports)
 if epoch==nil or epoch~=state.volatileEpoch or
    state.attemptedEpoch~=epoch or
    state.attemptedActorId~=state.volatileActorId then
   -- Destroyed game / new session: immediately invalidate the volatile token.
   state.volatileEpoch=nil
   state.volatileActorId=nil
   state.volatileSprite=nil
   return false
 end
 local ok,portraitSprite=pcall(ports.getPortraitSprite,1)
 if not ok or portraitSprite~=aiBase then return false end
 -- Fail closed even if an old save contains BGXW3ARM=1.
 if read(ports,aiBase,KEYS[1])~=1 or
    read(ports,aiBase,KEYS[2])~=WITNESS or
    read(ports,aiBase,KEYS[3])~=0 then return false end
 local stage=read(ports,aiBase,KEYS[4])
 if stage~=0 and stage~=1 then return false end
 local live=snapshot(ports,aiBase)
 if not live or live.actorId~=state.volatileActorId then return false end
 local postEpoch=armingAllowed(ports)
 local ok2,postPortrait=pcall(ports.getPortraitSprite,1)
 if postEpoch~=epoch or not ok2 or postPortrait~=aiBase or
    read(ports,aiBase,KEYS[1])~=1 then return false end
 return true
end

-- This function could be called by the future guarded installer via
-- The future guarded bootstrap may bind M.makeLuaTrigger() only AFTER approval.
-- No global function is installed by merely importing this source.
function M.makeLuaTrigger()
 return function()
  local actor=rawget(_G,'EEex_LuaTrigger_Object')
  local ok,allowed=pcall(M.sessionGate,actor)
  return ok and allowed==true
 end
end

function M.getStatus()return ret(COUNT.last)end
return M

end)()

local M={schema='BGXAI_R41_SOURCE_ONLY_LINK_R39_R40_V1',sourceOnly=true,
         registered=false,installed=false,ordersSent=0,dispatchAuthorized=false,
         last='SOURCE_ONLY_UNREGISTERED'}
local R40_APPROVAL='ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD'
local R39_APPROVAL='INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD'
local started=false
local function ret(s)
 M.last=s
 return {schema=M.schema,status=s,sourceOnly=true,installed=false,
  armAuthorized=false,dispatchAuthorized=false,ordersSent=0,
  r40Registered=Reset.registered,
  r39Registered=Armer.registered,globalGateBound=started}
end
-- Pre-game install proof is an external, separately authenticated fact.
-- A boolean inserted by this file would not be evidence.
function M.prepare(ports,installerApproval)
 if installerApproval~='BGXAI_R41_GUARDED_TYPED_INSTALL_APPROVED' then
  return ret('HOLD_TYPED_INSTALL_APPROVAL_REQUIRED') end
 if started then return ret('HOLD_ALREADY_STARTED') end
 if rawget(_G,'BGXW3_EEexSessionGate')~=nil then
  return ret('HOLD_GLOBAL_GATE_COLLISION') end
 if type(ports)~='table' or ports.preGameStartupVerified~=true or
    ports.runtimeItemUsabilityVerified~=true or
    ports.runtimeEffectsVerified~=true or
    ports.scriptOwnerVerified~=true or
    ports.manualEpsSafetyVerified~=true or
    type(ports.capture)~='function' or
    type(ports.getPortraitSprite)~='function' or
    type(ports.getLocal)~='function' or
    type(ports.setLocal)~='function' or
    type(ports.addDestroyed)~='function' or
    type(ports.addLoaded)~='function' or
    type(ports.addPressed)~='function' or
    type(ports.keyFromName)~='function' or
    type(ports.isDown)~='function' then
  return ret('HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING') end
 -- R40 lifecycle callbacks must be installed BEFORE a key can ARM an actor.
 local rr=Reset.register({preGameStartupVerified=ports.preGameStartupVerified,
  addDestroyed=ports.addDestroyed,addLoaded=ports.addLoaded,
  getLocal=ports.getLocal,setLocal=ports.setLocal},R40_APPROVAL)
 if rr.status~='RESET_ONLY_LIFECYCLE_HOOKS_REGISTERED_NO_ARM' then
  return ret('HOLD_R40_REGISTER_FAILED') end
 local lastEpoch=Reset.getStatus().sessionEpoch
 local function getEpoch()
  local state=Reset.getStatus()
  if state.status=='NOT_REGISTERED' or type(state.sessionEpoch)~='number' then
   return nil end
  return state.sessionEpoch
 end
 local function proveLifecycle()
  local state=Reset.getStatus()
  return type(state.sessionEpoch)=='number' and state.sessionEpoch>=lastEpoch and
   ports.preGameStartupVerified==true and
   Reset.registered==true
 end
 local ar=Armer.prepare({addPressed=ports.addPressed,
  keyFromName=ports.keyFromName,isDown=ports.isDown,
  getPortraitSprite=ports.getPortraitSprite,
  capture=ports.capture,getLocal=ports.getLocal,setLocal=ports.setLocal,
  proveLifecycle=proveLifecycle,getEpoch=getEpoch,onResult=ports.onResult},R39_APPROVAL)
 if ar.status~='REGISTERED_GESTURE_ONLY_NO_ARM' then
  return ret('HOLD_R39_REGISTER_FAILED_R40_ONLY') end
 local gated=Armer.makeLuaTrigger()
 if type(gated)~='function' then return ret('HOLD_TRIGGER_INVALID_R40_ONLY') end
 local function guarded()
  if not started then return false end
  local ok,allowed=pcall(gated)
  return ok and allowed==true
 end
 -- Final single global write; all prerequisite registrations already succeeded.
 -- No self-ARM, no script start, no engine command in this module.
 if rawget(_G,'BGXW3_EEexSessionGate')~=nil then
  return ret('HOLD_GLOBAL_GATE_CHANGED_R40_ONLY') end
 rawset(_G,'BGXW3_EEexSessionGate',guarded)
 started=true
 M.registered=true
 return ret('R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
end
function M.getStatus()return ret(M.last)end
function M.getEmbeddedStatus()
 return {r39=Armer.getStatus(),r40=Reset.getStatus(),globalGateBound=started}
end
-- No registration and no global function published at import time.
return M
