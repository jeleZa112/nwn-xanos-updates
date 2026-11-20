-- BGXFRTRACE v1.0: passive EEex party action observer.
-- This file does not issue actions, write locals, alter priorities, or cancel damage.
-- The source of an action is UNKNOWN even if m_curScriptNum is present.
if type(BGXFRTrace) == "table" and BGXFRTrace.initialized then return end
local M = { initialized = false, version = 1, observations = 0,
            recorded = 0, dropped = 0, write_errors = 0, writer = "UNAVAILABLE" }
BGXFRTrace = M

local ATTACK = { [3]=true, [94]=true, [98]=true, [105]=true, [134]=true }
local LIMIT = 1200
local FILE = "BGXAI_FRIENDLY_ACTION_TRACE.log"
local function safe(fn)
    local ok, res = pcall(fn)
    if ok then return res end
    return nil
end
local function object_id(x)
    if type(x)=="number" and x==math.floor(x) and x>=0 and x<=2147483647 then return x end
    return nil
end
local function field(x,k)
    return safe(function() return x[k] end)
end
local function write_line(line)
    if not M.handle then return end
    local ok = pcall(function() M.handle:write(line,"\n"); M.handle:flush() end)
    if not ok then
        M.write_errors=M.write_errors+1
        safe(function() M.handle:close() end)
        M.handle=nil
        M.writer="WRITE_ERROR"
    end
end
local function portrait_ids()
    local by_id={}
    if type(EEex_Sprite_GetInPortraitID)~="function" then return by_id end
    for i=0,5 do
        local id=object_id(safe(function() return EEex_Sprite_GetInPortraitID(i) end))
        if id then by_id[id]=i+1 end
    end
    return by_id
end
local function numeric(x)
    if type(x)=="number" and x==math.floor(x) then return x end
    return -1
end
function M.on_started(sprite, action)
    -- Never throw an error into the EEex dispatcher.
    local ok=pcall(function()
        if M.recorded>=LIMIT then M.dropped=M.dropped+1; return end
        local act=object_id(field(action,"m_actionID"))
        if not ATTACK[act] then return end
        M.observations=M.observations+1
        local actor=object_id(field(sprite,"m_id"))
        if not actor then return end
        local party=portrait_ids()
        local actor_slot=party[actor]
        if not actor_slot then return end
        local a1=object_id(field(field(action,"m_acteeID"),"m_Instance"))
        local a2=object_id(field(field(action,"m_acteeID2"),"m_Instance"))
        -- AttackReevaluate / AttackOneRound may populate m_acteeID2.
        -- Selection is a heuristic; record both raw fields for independent review.
        local prefer_second=act==105 or act==134
        local target=(prefer_second and (a2 or a1)) or (a1 or a2)
        local target_slot=(target and party[target]) or -1
        local script=numeric(field(sprite,"m_curScriptNum"))
        M.recorded=M.recorded+1
        local status=(target_slot>0 and target~=actor) and "PARTY_TARGET_OBSERVED" or "TARGET_NOT_CONFIRMED_PARTY"
        write_line(string.format(
            "[BGXFTRACE] ACTION seq=%d actor=%d slot=%d action=%d a1=%d a2=%d target=%d target_slot=%d script=%d status=%s origin=UNKNOWN",
            M.recorded,actor,actor_slot,act,a1 or -1,a2 or -1,target or -1,
            target_slot,script,status))
    end)
    if not ok then M.write_errors=M.write_errors+1 end
end

local function init()
    if type(EEex_Action_AddSpriteStartedActionListener)~="function"
        or type(EEex_Sprite_GetInPortraitID)~="function" then
        M.writer="EEEX_HOOK_UNAVAILABLE"
        return false
    end
    if type(io)~="table" or type(io.open)~="function" then
        M.writer="IO_UNAVAILABLE"
        return false
    end
    -- Truncate ONLY the dedicated diagnostic file, once per game process.
    -- Do not touch EEex.log, BGXAI_COMBAT.log, saves, BCS or other mods' Lua.
    local f=safe(function() return io.open(FILE,"w") end)
    if not f then M.writer="TRACE_FILE_OPEN_FAILED"; return false end
    M.handle=f
    M.writer="FILE"
    write_line("[BGXFTRACE] SESSION version=1 origin=UNKNOWN coverage=STARTED_PARTY_ATTACK_ACTIONS_ONLY")
    local ok=safe(function() EEex_Action_AddSpriteStartedActionListener(M.on_started); return true end)
    if not ok then
        write_line("[BGXFTRACE] STOP reason=EEEX_LISTENER_REGISTRATION_FAILED")
        safe(function() M.handle:close() end)
        M.handle=nil
        M.writer="EEEX_LISTENER_REGISTRATION_FAILED"
        return false
    end
    M.initialized=true
    write_line("[BGXFTRACE] READY hook=REGISTERED writer=FILE origin=UNKNOWN")
    return true
end
M.active=init()
