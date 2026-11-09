-- BGXAI 044: passive EEex diagnosis. No BCS/actions/queues/AI changes.
-- Ctrl+Alt+F11 (while the game window is focused) displays 043P runtime state.
-- No Lua console or battle is needed. Never swallows the key event.
BGX44Diag = BGX44Diag or {}
local D = BGX44Diag
D.version = "0.3.15-044-DIAG"
D.registered = D.registered or false
D.pressCount = D.pressCount or 0
D.lastStatus = D.lastStatus or "NOT_CHECKED"
D.lastError = D.lastError or nil

local F11 = 0x40000044
local LCTRL, RCTRL = 0x400000E0, 0x400000E4
local LALT, RALT = 0x400000E2, 0x400000E6

local function down(key)
    if type(EEex_Key_IsDown) ~= "function" then return false end
    local ok, state = pcall(EEex_Key_IsDown, key)
    return ok and state == true
end

local function report()
    local p = BGX43Probe
    local loaded = type(p) == "table"
    local listener = loaded and p.installed == true or false
    local enabled = loaded and p.enabled == true or false
    local hits = loaded and type(p.events) == "table" and #p.events or 0
    local errors = loaded and tonumber(p.errors) or 0
    local notice = loaded and p.firstNoticeShown == true or false
    local listenerApi = type(EEex_Action_AddSpriteStartedActionListener) == "function"
    local portraitApi = type(EEex_Sprite_GetInPortraitID) == "function"
    local last = loaded and tostring(p.lastError or "-") or "MODULE_NOT_LOADED"
    local msg = "BGX44: 043P loaded=" .. tostring(loaded)
        .. " listener=" .. tostring(listener)
        .. " enabled=" .. tostring(enabled)
        .. " attacks=" .. tostring(hits)
        .. " errors=" .. tostring(errors)
        .. " notice=" .. tostring(notice)
        .. " API=" .. tostring(listenerApi) .. "/" .. tostring(portraitApi)
        .. " last=" .. last
    D.pressCount = D.pressCount + 1
    D.lastStatus = msg
    if type(Infinity_DisplayString) == "function" then
        local ok = pcall(Infinity_DisplayString, msg)
        D.lastError = ok and nil or "DISPLAY_FAILED"
    else
        D.lastError = "DISPLAY_API_UNAVAILABLE"
    end
end

function D.onKeyPressed(key)
    if key ~= F11 then return false end
    if not (down(LCTRL) or down(RCTRL)) then return false end
    if not (down(LALT) or down(RALT)) then return false end
    local ok = pcall(report)
    if not ok then D.lastError = "READ_ONLY_REPORT_FAILED" end
    return false
end

if not D.registered then
    if type(EEex_Key_AddPressedListener) == "function" then
        local ok = pcall(EEex_Key_AddPressedListener, D.onKeyPressed, false)
        if ok then D.registered = true
        else D.lastError = "KEY_HOOK_REGISTRATION_FAILED" end
    else
        D.lastError = "KEY_API_UNAVAILABLE"
    end
end
