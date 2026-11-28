-- PRIOR_WORK_REUSE: BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3.py
-- PRIOR_WORK_EXISTING: V3 already owns BGXW3ARM/TAG/TRY, once-only XEquipItem and action/slot safety guards.
-- PRIOR_WORK_DELTA_ONLY: optional explicit physical hotkey gesture, epoch/two-snapshot/readback preflight candidate.
-- PRIOR_WORK_STATUS: CODE/MOCK only; no installed adapter, native R39 compile, approved hotkey, or LIVE equip.
-- PRIOR_WORK_NO_REIMPLEMENT: reuse V3/R37/R38/R40 and weapon priority; never claim this is autonomous weapon selection.
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
local state={epoch=nil,attemptedEpoch=nil,attemptedActorId=nil}
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
 return ret('REGISTERED_GESTURE_ONLY_NO_ARM')
end

function M.getStatus()return ret(COUNT.last)end
return M
