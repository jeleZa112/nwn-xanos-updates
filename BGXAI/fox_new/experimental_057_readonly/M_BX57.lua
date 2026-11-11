-- BGXAI 057 read-only EEex runtime diagnostic, SOURCE ONLY (not installed).
-- Intended M_ autoload resource name M_BX57 (6 characters).
-- Ctrl+Alt+F10 reports the installed 056 Lua counters and party F/REQ status.
-- No combat commands, timers, local writes, filesystem, or external access.
BGX57Diag = BGX57Diag or {}
local D = BGX57Diag
D.version = "0.3.23-057-READONLY-DIAG-SOURCE"
D.registered = D.registered or false
D.pressCount = D.pressCount or 0
D.lastError = nil
D.lastLines = {}

local F10 = 0x40000043
local LCTRL, RCTRL = 0x400000E0, 0x400000E4
local LALT, RALT = 0x400000E2, 0x400000E6

local function safe(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end
local function down(key)
    if type(EEex_Key_IsDown) ~= "function" then return false end
    return safe(function() return EEex_Key_IsDown(key) end) == true
end
local function val(x)
    if x == nil then return "-" end
    if type(x) == "boolean" then return x and "1" or "0" end
    local s = tostring(x)
    return string.sub(s, 1, 55)
end
local function emit(s)
    D.lastLines[#D.lastLines + 1] = s
    if type(Infinity_DisplayString) ~= "function" then
        D.lastError = "DISPLAY_API_UNAVAILABLE"
        return
    end
    if not safe(function() Infinity_DisplayString(s); return true end) then
        D.lastError = "DISPLAY_FAILED"
    end
end
local function reasonSummary(rejections)
    if type(rejections) ~= "table" then return "-" end
    local t = {}
    for k, v in pairs(rejections) do
        if type(k) == "string" and type(v) == "number" and v > 0 then
            t[#t+1] = {key=k, count=v}
        end
    end
    table.sort(t, function(a, b)
        if a.count == b.count then return a.key < b.key end
        return a.count > b.count
    end)
    if #t == 0 then return "none" end
    local parts = {}
    for i=1,math.min(#t, 2) do
        parts[#parts+1] = string.sub(t[i].key,1,30) .. ":" .. val(t[i].count)
    end
    return table.concat(parts, ",")
end
function D.report()
    D.lastLines = {}
    D.lastError = nil
    if type(BGX43Probe) ~= "table" or type(BGX43Probe.snapshot) ~= "function" then
        emit("BGX57: 056 BGX43Probe not loaded; NO COUNTERS")
        return false
    end
    local ok, snap = pcall(BGX43Probe.snapshot)
    if not ok or type(snap) ~= "table" then
        emit("BGX57: 056 snapshot failed; NO COUNTERS")
        return false
    end
    emit("BGX57 056="..val(snap.version).." hook="..val(snap.weapon_hit_registered)
        .." H="..val(snap.weapon_hit_calls).." HE="..val(snap.weapon_hit_errors))
    emit("BGX57 bridge="..val(snap.bcs_bridge_enabled).." PREP="..val(snap.bridge_prepared_count)
        .." ATT="..val(snap.bridge_attempts).." GE="..val(snap.guard_signal_errors))
    local last = type(snap.bridge_last)=="table" and snap.bridge_last or {}
    emit("BGX57 last="..val(last.reason or last.result or "none")
        .." victim="..val(last.victim_slot).." guardian="..val(last.chosen_guardian))
    emit("BGX57 rejects="..reasonSummary(snap.bridge_rejections))
    if type(EEex_Sprite_GetInPortraitID) ~= "function" or
        type(EEex_GameObject_Get) ~= "function" then
        emit("BGX57: portrait/object API unavailable")
        return true
    end
    local active = 0
    for i=1,5 do
        local id = safe(function() return EEex_Sprite_GetInPortraitID(i) end)
        if type(id)=="number" and id>=0 then
            local obj = safe(function() return EEex_GameObject_Get(id) end)
            if obj then
                local f = safe(function() return obj:getLocalInt("BGX38_GUARD") end)
                local q = safe(function() return obj:getLocalInt("BGX52_REQ_SLOT") end)
                local m = safe(function() return obj.m_nModalState end)
                if f==1 or (type(q)=="number" and q>0) then
                    active = active + 1
                    local expire = safe(function() return obj:getLocalInt("BGX52_EXPIRE") end)
                    local cooldown = safe(function() return obj:getLocalInt("BGX52_COOLDOWN") end)
                    emit("BGX57 P"..val(i+1).." F="..val(f).." Q="..val(q).." MOD="..val(m)
                        .." EX="..val(expire).." CD="..val(cooldown))
                end
            end
        end
    end
    if active==0 then emit("BGX57: no F=1 guardian or pending request in slots 2-6") end
    return true
end
function D.onKeyPressed(key)
    if key~=F10 or not (down(LCTRL) or down(RCTRL)) or
        not (down(LALT) or down(RALT)) then return false end
    D.pressCount = D.pressCount + 1
    local ok = pcall(D.report)
    if not ok then D.lastError = "REPORT_EXCEPTION" end
    return false -- never consumes the player's key
end
if not D.registered then
    if type(EEex_Key_AddPressedListener)=="function" then
        local ok = pcall(EEex_Key_AddPressedListener, D.onKeyPressed, false)
        if ok then D.registered = true
        else D.lastError = "KEY_HOOK_REGISTRATION_FAILED" end
    else
        D.lastError = "KEY_API_UNAVAILABLE"
    end
end