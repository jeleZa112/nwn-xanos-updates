-- BGXAI FILTERED ACTION PROBE v5
-- Read-only: character location, destination, target and action code.
-- Uses loader-native print mirroring; no UI calls or changes to AI action queues.
print("[BGXAI] FILTERED ACTION PROBE v5 module loaded")
local total, errors, limit = 0, 0, 5000
local accepted = {
    ["Халид"]=true, ["Джахейра"]=true, ["Волк"]=true,
    ["Khalid"]=true, ["Jaheira"]=true, ["Wolf"]=true
}
local function field(read)
    local ok, value = pcall(read)
    if not ok or value == nil then return "NA" end
    return tostring(value):gsub("[%c]","?"):sub(1,64)
end
local function onStarted(sprite,action)
    local ok,err=pcall(function()
        local name=field(function() return sprite.m_sName.m_pchData:get() end)
        if not accepted[name] then return end
        total=total+1
        if total > limit then
            if total == limit+1 then print("[BGXAI] FILTERED LIMIT REACHED "..limit) end
            return
        end
        local id=field(function() return sprite.m_id end)
        local actionId=field(function() return action.m_actionID end)
        local px=field(function() return sprite.m_pos.x end)
        local py=field(function() return sprite.m_pos.y end)
        local dx=field(function() return action.m_dest.x end)
        local dy=field(function() return action.m_dest.y end)
        local target=field(function() return action.m_acteeID.m_Instance end)
        print(string.format("[BGXAI] ACTION_%04d name=%s id=%s action=%s pos=(%s,%s) dest=(%s,%s) target=%s",
            total,name,id,actionId,px,py,dx,dy,target))
    end)
    if not ok and errors < 5 then
        errors=errors+1
        print("[BGXAI] HOOK_ERROR "..tostring(err):sub(1,160))
    end
end
if type(EEex_Action_AddSpriteStartedActionListener) == "function" then
    EEex_Action_AddSpriteStartedActionListener(onStarted)
    print("[BGXAI] FILTERED ACTION HOOK REGISTERED v5")
else
    print("[BGXAI] ACTION HOOK UNAVAILABLE")
end
