-- BGXAI FILTERED ACTION PROBE v4
-- Captures only Khalid, Jaheira and wolf action starts. No interface calls / AI changes.
print("[BGXAI] FILTERED ACTION PROBE v4 module loaded")
local total, errors, limit = 0, 0, 2000
local accepted = {
    ["Халид"]=true, ["Джахейра"]=true, ["Волк"]=true,
    ["Khalid"]=true, ["Jaheira"]=true, ["Wolf"]=true
}
local function onStarted(sprite,action)
    local ok, msg = pcall(function()
        local name = tostring(sprite.m_sName.m_pchData:get() or "?")
        if not accepted[name] then return end
        total=total+1
        if total > limit then
            if total == limit+1 then print("[BGXAI] FILTERED LIMIT REACHED " .. tostring(limit)) end
            return
        end
        local id = tonumber(sprite.m_id) or -1
        local actionId = tonumber(action.m_actionID) or -1
        print(string.format("[BGXAI] ACTION_%04d name=%s sprite_id=%d action_id=%d",
            total,name,id,actionId))
    end)
    if not ok and errors < 5 then
        errors=errors+1
        print("[BGXAI] ACTION_HOOK_ERROR " .. tostring(msg):sub(1,120))
    end
end
if type(EEex_Action_AddSpriteStartedActionListener) == "function" then
    EEex_Action_AddSpriteStartedActionListener(onStarted)
    print("[BGXAI] FILTERED ACTION HOOK REGISTERED")
else
    print("[BGXAI] ACTION HOOK UNAVAILABLE")
end
