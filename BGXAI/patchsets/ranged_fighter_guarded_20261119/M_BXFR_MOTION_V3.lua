-- BGXFTRACE v3: passive all-started-action trace for party slot 3 (Khalid).
-- Also observes any other party actor's started action aimed at another member.
-- Never changes BCS, queues, sprites, local/global variables or game state.
if type(BGXFRTrace) == "table" and BGXFRTrace.initialized then return end
local M={initialized=false,version=3,recorded=0,errors=0,writer="UNAVAILABLE",handle=nil}
BGXFRTrace=M
local LIMIT=3600
local FILE="BGXAI_FRIENDLY_ACTION_TRACE.log"
local function safe(fn) local ok,v=pcall(fn);if ok then return v end;return nil end
local function field(v,k) return safe(function() return v[k] end) end
local function id(x)
 if type(x)=="number" and x==math.floor(x) and x>=0 and x<=2147483647 then return x end
 return nil
end
local function number(x) if type(x)=="number" and x==math.floor(x) then return x end;return -1 end
local function emit(line)
 if M.handle then
  local ok=pcall(function() M.handle:write(line,"\n"); M.handle:flush() end)
  if ok then return end
  M.errors=M.errors+1
  safe(function() M.handle:close() end)
  M.handle=nil
  M.writer="CONSOLE_AFTER_FILE_ERROR"
 end
 if type(Infinity_Log)=="function" then
  local ok=pcall(Infinity_Log,line)
  if not ok then M.errors=M.errors+1 end
 end
 if type(print)=="function" then
  local ok=pcall(print,line)
  if not ok then M.errors=M.errors+1 end
 end
end
local function party()
 local result={}
 if type(EEex_Sprite_GetInPortraitID)~="function" then return result end
 for index=0,5 do
  local eid=id(safe(function() return EEex_Sprite_GetInPortraitID(index) end))
  if eid then result[eid]=index+1 end
 end
 return result
end
function M.on_started(sprite,action)
 local ok=pcall(function()
  if M.recorded>=LIMIT then return end
  local act=id(field(action,"m_actionID"))
  local actor=id(field(sprite,"m_id"))
  if not actor or not act then return end
  local ids=party()
  local slot=ids[actor]
  if not slot then return end
  local a1=id(field(field(action,"m_acteeID"),"m_Instance"))
  local a2=id(field(field(action,"m_acteeID2"),"m_Instance"))
  -- Selection is only a hint. Both raw actee fields are ALWAYS preserved.
  local dst=((act==105 or act==134) and (a2 or a1)) or (a1 or a2)
  local dstslot=(dst and ids[dst]) or -1
  local party_target=(dstslot>0 and dst~=actor)
  -- Observe all Khalid actions, including MoveToObject and ProtectObject.
  -- Other actors matter only when aimed at a fellow party member.
  if slot~=3 and not party_target then return end
  local script=number(field(sprite,"m_curScriptNum"))
  M.recorded=M.recorded+1
  local status=party_target and "PARTY_TARGET_OBSERVED" or "TARGET_NOT_CONFIRMED_PARTY"
  emit(string.format(
   "[BGXFTRACE] ACTION seq=%d actor=%d slot=%d action=%d a1=%d a2=%d target=%d target_slot=%d script=%d status=%s origin=UNKNOWN",
   M.recorded,actor,slot,act,a1 or -1,a2 or -1,dst or -1,dstslot,script,status))
 end)
 if not ok then M.errors=M.errors+1 end
end
local function initialize()
 if type(EEex_Action_AddSpriteStartedActionListener)~="function"
    or type(EEex_Sprite_GetInPortraitID)~="function" then
  M.writer="EEEX_HOOK_UNAVAILABLE"
  emit("[BGXFTRACE] STOP reason=EEEX_HOOK_UNAVAILABLE")
  return false
 end
 if type(io)=="table" and type(io.open)=="function" then
  M.handle=safe(function() return io.open(FILE,"w") end)
 end
 M.writer=M.handle and "FILE" or "CONSOLE"
 if not M.handle and type(Infinity_Log)~="function" and type(print)~="function" then
  M.writer="NO_SINK"
  return false
 end
 emit("[BGXFTRACE] SESSION version=3 origin=UNKNOWN coverage=KHALID_ALL_STARTED_ACTIONS_AND_PARTY_TARGET_ACTIONS")
 local ok=safe(function() EEex_Action_AddSpriteStartedActionListener(M.on_started);return true end)
 if not ok then
  emit("[BGXFTRACE] STOP reason=EEEX_LISTENER_REGISTRATION_FAILED")
  M.writer="EEEX_LISTENER_REGISTRATION_FAILED"
  return false
 end
 M.initialized=true
 emit("[BGXFTRACE] READY hook=REGISTERED writer="..M.writer.." origin=UNKNOWN")
 return true
end
M.active=initialize()
