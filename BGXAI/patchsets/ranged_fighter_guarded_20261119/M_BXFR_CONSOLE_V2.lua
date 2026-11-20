-- BGXFTRACE v2: passive EEex observer with console fallback for INTERNAL Lua.
-- No AI decisions, queuing, attack cancellation, globals, or game-state mutation.
if type(BGXFRTrace) == "table" and BGXFRTrace.initialized then return end
local M={initialized=false,version=2,recorded=0,errors=0,writer="UNAVAILABLE",handle=nil}
BGXFRTrace=M
local LIMIT=1200
local FILE="BGXAI_FRIENDLY_ACTION_TRACE.log"
local ATTACK={[3]=true,[94]=true,[98]=true,[105]=true,[134]=true}
local function safe(fn) local ok,v=pcall(fn); if ok then return v end; return nil end
local function field(v,k) return safe(function() return v[k] end) end
local function object_id(x)
 if type(x)=="number" and x==math.floor(x) and x>=0 and x<=2147483647 then return x end
 return nil
end
local function numeric(x) if type(x)=="number" and x==math.floor(x) then return x end; return -1 end
local function emit(line)
 if M.handle then
  local ok=pcall(function() M.handle:write(line,"\\n"); M.handle:flush() end)
  if ok then return end
  M.errors=M.errors+1
  safe(function() M.handle:close() end)
  M.handle=nil
  M.writer="CONSOLE_AFTER_FILE_ERROR"
 end
 -- Emit to BOTH console APIs. Only one need reach captured stdout.
 -- Duplicate records are deduplicated by the read-only report parser.
 if type(Infinity_Log)=="function" then
  local ok=pcall(Infinity_Log,line)
  if not ok then M.errors=M.errors+1 end
 end
 if type(print)=="function" then
  local ok=pcall(print,line)
  if not ok then M.errors=M.errors+1 end
 end
end
local function portrait_ids()
 local map={}
 if type(EEex_Sprite_GetInPortraitID)~="function" then return map end
 for i=0,5 do
  local id=object_id(safe(function() return EEex_Sprite_GetInPortraitID(i) end))
  if id then map[id]=i+1 end
 end
 return map
end
function M.on_started(sprite,action)
 local ok=pcall(function()
  if M.recorded>=LIMIT then return end
  local act=object_id(field(action,"m_actionID"))
  if not ATTACK[act] then return end
  local actor=object_id(field(sprite,"m_id"))
  if not actor then return end
  local ids=portrait_ids()
  local slot=ids[actor]
  if not slot then return end
  local a1=object_id(field(field(action,"m_acteeID"),"m_Instance"))
  local a2=object_id(field(field(action,"m_acteeID2"),"m_Instance"))
  local dest=((act==105 or act==134) and (a2 or a1)) or (a1 or a2)
  local destslot=(dest and ids[dest]) or -1
  local script=numeric(field(sprite,"m_curScriptNum"))
  M.recorded=M.recorded+1
  local tag=(destslot>0 and dest~=actor) and "PARTY_TARGET_OBSERVED" or "TARGET_NOT_CONFIRMED_PARTY"
  emit(string.format("[BGXFTRACE] ACTION seq=%d actor=%d slot=%d action=%d a1=%d a2=%d target=%d target_slot=%d script=%d status=%s origin=UNKNOWN",
   M.recorded,actor,slot,act,a1 or -1,a2 or -1,dest or -1,destslot,script,tag))
 end)
 if not ok then M.errors=M.errors+1 end
end
local function init()
 if type(EEex_Action_AddSpriteStartedActionListener)~="function" or type(EEex_Sprite_GetInPortraitID)~="function" then
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
 emit("[BGXFTRACE] SESSION version=2 origin=UNKNOWN coverage=STARTED_PARTY_ATTACK_ACTIONS_ONLY")
 local ok=safe(function() EEex_Action_AddSpriteStartedActionListener(M.on_started); return true end)
 if not ok then
  emit("[BGXFTRACE] STOP reason=EEEX_LISTENER_REGISTRATION_FAILED")
  M.writer="EEEX_LISTENER_REGISTRATION_FAILED"
  return false
 end
 M.initialized=true
 emit("[BGXFTRACE] READY hook=REGISTERED writer="..M.writer.." origin=UNKNOWN")
 return true
end
M.active=init()
