-- BGXAI combat telemetry pilot. Requires EEex to load M_*.lua from override.
-- Nonintrusive: observes started sprite actions and never changes AI orders.
BGXAI_COMBAT = BGXAI_COMBAT or { count = 0, errors = 0, disabled = false }
local T = BGXAI_COMBAT
local function saferead(f)
    local ok,v = pcall(f)
    if ok and v ~= nil then return tostring(v) end
    return "?"
end
local function append(msg)
    if T.disabled then return end
    local ok,err = pcall(function()
        local root = (type(Infinity_GetGameDirectory) == "function" and Infinity_GetGameDirectory()) or "."
        local separator = "\\"
        if root:sub(-1) == "\\" or root:sub(-1) == "/" then separator = "" end
        local fullpath = root .. separator .. "BGXAI_COMBAT.log"
        local f,e = io.open(fullpath, "a")
        if not f then error(e or "io.open failed") end
        f:write(os.date("!%Y-%m-%dT%H:%M:%SZ"), " ", msg, "\n")
        f:close()
    end)
    if not ok then
        T.errors = T.errors + 1
        -- Do not repeatedly retry file errors on every engine action.
        if T.errors >= 3 then T.disabled = true end
    end
end
append("SESSION START; BGXAI telemetry=0.6.15-pilot.2; action-start events only; UTC")
if type(Infinity_DisplayString) == "function" then pcall(Infinity_DisplayString, "[BGXAI] Lua telemetry loaded; search for BGXAI_COMBAT.log") end
local function onAction(sprite,action)
    local ok,err = pcall(function()
        T.count = T.count + 1
        if T.count > 60000 then
            if T.count == 60001 then append("LIMIT reached (60000 action events); restart game for new session") end
            return
        end
        local id = saferead(function() return sprite.m_id end)
        local x = saferead(function() return sprite.m_pos.x end)
        local y = saferead(function() return sprite.m_pos.y end)
        local a = saferead(function() return action.m_actionID end)
        local target = saferead(function() return action.m_acteeID.m_Instance end)
        local destX = saferead(function() return action.m_dest.x end)
        local destY = saferead(function() return action.m_dest.y end)
        local hp = saferead(function() return sprite.m_baseStats.m_hitPoints end)
        local spell = saferead(function() return action.m_string1.m_pchData:get() end)
        -- No unescaped control chars or excessively long strings from game data.
        spell = spell:gsub("[%c]", "?"):sub(1,48)
        append(string.format("SPRITE id=%s pos=(%s,%s) hp=%s ACTION=%s target=%s dest=(%s,%s) arg=%s",
            id,x,y,hp,a,target,destX,destY,spell))
    end)
    if not ok then append("HOOK_ERROR "..tostring(err):sub(1,200)) end
end
if type(EEex_Action_AddSpriteStartedActionListener) == "function" then
    EEex_Action_AddSpriteStartedActionListener(onAction)
    append("HOOK ACTIVE EEex_Action_AddSpriteStartedActionListener")
else
    append("HOOK UNAVAILABLE: EEex action listener missing")
end
