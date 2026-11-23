-- BGXAI R27 BOOTSTRAP CANDIDATE (source-only, no live deployment).
-- This code is only appended to M_BGXR27.lua *for a separately authorized,
-- SHA-guarded WeiDU installer in the existing one-file updater*.
-- Loading the staged file WOULD register a passive EEex listener.
-- NEVER install or load this file in a user's game without typed consent.
local P={name='M_BGXR27',version='BGXAI_R27_SINGLE_CALLBACK_PILOT_V1',
 registered=false,sourceOnlyCandidate=true,ordersSent=0,errors=0,
 writer='UNAVAILABLE'}
if type(BGXAI_R27_ObserverPilot)=='table' and
 BGXAI_R27_ObserverPilot.registered==true then return end
BGXAI_R27_ObserverPilot=P
local function safe(fn)
 local ok,v=pcall(fn)
 if ok then return v end
 return nil
end
local function writer(line)
 if type(Infinity_Log)=='function' then
  local ok=pcall(Infinity_Log,line)
  if ok then P.writer='INFINITY_LOG';return end
 end
 if type(print)=='function' then
  local ok=pcall(print,line)
  if ok then P.writer='PRINT_FALLBACK';return end
 end
 P.errors=P.errors+1
end
local function portraitIndex(actorId)
 for i=0,5 do
  if safe(function() return EEex_Sprite_GetInPortraitID(i) end)==actorId then
   return i end
 end
 return nil
end
local function start()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
   type(EEex_Sprite_GetInPortraitID)~='function' or
   type(EEex_Sprite_GetActiveStats)~='function' then
  P.writer='REQUIRED_EEEX_API_MISSING';return false end
 local pilot=R27.prepareConsolePilot({portraitIndex=portraitIndex,
  getActiveStats=EEex_Sprite_GetActiveStats,emitString=writer})
 if type(pilot)~='table' or type(pilot.listener)~='function' then
  P.writer='R27_SOURCE_CONTRACT_INCOMPLETE';return false end
 local ok=pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener)
 if not ok then P.writer='LISTENER_REGISTRATION_FAILED';return false end
 P.registered=true
 writer('[BGXR27] {"schema":"BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",'..
   '"type":"SESSION","readOnly":true,"nativeEventTokenAuthenticated":false,'..
   '"engineSessionVerified":false,"ordersSent":0,'..
   '"weaponSwitchAuthorized":false,"dispatchAuthorized":false}')
 return true
end
P.initialized=start()
