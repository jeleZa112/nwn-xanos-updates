-- BGXAI R31: passive bootstrap for EXACT R27 ACTION_CONTEXT_V3 source.
-- SOURCE ONLY. Not installed. It may be wrapped around R27 only after a
-- separately approved SHA/WeiDU upgrade; never load in the game directly.
-- Depends on the preceding local R27 produced by the verified builder.
-- Does not issue engine actions, set LOCALS, mutate scripts, or clear queues.
local P={name='M_BGXR27',version='BGXAI_R31_R27V3_PASSIVE_CANDIDATE',
  registered=false,readOnly=true,ordersSent=0,errors=0,writer='UNAVAILABLE',
  dispatchAuthorized=false,weaponSwitchAuthorized=false}
-- No duplicate listeners in the same session. A fresh game process is required
-- before any future replacement; do not try to unhook the old listener.
if type(BGXAI_R27_ObserverPilot)=='table' and
   BGXAI_R27_ObserverPilot.registered==true then return end
BGXAI_R27_ObserverPilot=P
local function safe(fn)
  local ok,v=pcall(fn)
  if ok then return v end
  return nil
end
local function emit(line)
  if type(Infinity_Log)=='function' and pcall(Infinity_Log,line) then
    P.writer='INFINITY_LOG';return
  end
  if type(print)=='function' and pcall(print,line) then
    P.writer='PRINT_FALLBACK';return
  end
  P.errors=P.errors+1
end
local function portraitIndex(actorId)
  for i=0,5 do
    if safe(function() return EEex_Sprite_GetInPortraitID(i) end)==actorId then
      return i
    end
  end
  return nil
end
local function start()
  if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
     type(EEex_Sprite_GetInPortraitID)~='function' or
     type(EEex_Sprite_GetActiveStats)~='function' then
    P.writer='REQUIRED_EEEX_API_MISSING';return false
  end
  if type(R27)~='table' or type(R27.prepareConsolePilot)~='function' then
    P.writer='R27_V3_CONTRACT_INCOMPLETE';return false
  end
  local ok,pilot=pcall(R27.prepareConsolePilot,{
    portraitIndex=portraitIndex,
    getActiveStats=EEex_Sprite_GetActiveStats,emitString=emit
  })
  if not ok or type(pilot)~='table' or type(pilot.listener)~='function' then
    P.writer='R27_V3_LISTENER_MISSING';return false
  end
  if not pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener) then
    P.writer='LISTENER_REGISTRATION_FAILED';return false
  end
  P.registered=true
  emit('[BGXR27] {"schema":"BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",'..
       '"type":"SESSION","observerCandidate":"R31_R27V3_PASSIVE",'..
       '"queueBindingLiveVerified":false,"manualEpsOriginVerified":false,'..
       '"alternateEffectiveAPRVerified":false,"readOnly":true,'..
       '"ordersSent":0,"weaponSwitchAuthorized":false,'..
       '"dispatchAuthorized":false}')
  return true
end
P.initialized=start()
