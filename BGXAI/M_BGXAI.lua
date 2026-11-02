-- BGXAI SAFE ACTION PROBE v3. Diagnostic only; no game interface calls.
-- Logger uses InfinityLoader native LogFile print redirection.
print("[BGXAI] ACTION PROBE v3 module loaded")
local total = 0
local errors = 0
local function onStarted(sprite, action)
    local ok, message = pcall(function()
        total = total + 1
        if total > 150 then return end
        local actionId = tonumber(action.m_actionID) or -1
        local name = tostring(sprite.m_sName.m_pchData:get() or "?")
        name = name:gsub("[\r\n]"," "):sub(1,80)
        local id = tonumber(sprite.m_id) or -1
        print(string.format("[BGXAI] START_ACTION number=%d sprite_id=%d name=%s action_id=%d",total,id,name,actionId))
    end)
    if not ok and errors < 5 then
        errors = errors + 1
        print("[BGXAI] ACTION_HOOK_ERROR " .. tostring(message):sub(1,120))
    end
end
if type(EEex_Action_AddSpriteStartedActionListener) == "function" then
    EEex_Action_AddSpriteStartedActionListener(onStarted)
    print("[BGXAI] ACTION HOOK REGISTERED")
else
    print("[BGXAI] ACTION HOOK UNAVAILABLE")
end
