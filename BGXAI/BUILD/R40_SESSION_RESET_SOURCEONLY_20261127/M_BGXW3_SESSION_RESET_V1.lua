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
