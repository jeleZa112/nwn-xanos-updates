-- BGXAI 044-DIAG v0.3.16. Purely observational EEex 1.1.7 diagnostics.
-- Does not alter combat actions, queues, AI scripts, saves, TLK or UI.MENU.
-- Ctrl+Alt+F11 prints the counters; key event is never consumed.
BGX44Diag = BGX44Diag or {}
local D = BGX44Diag
D.version = '0.3.16-044-DIAG'
D.actionRegistered = D.actionRegistered or false
D.keyRegistered = D.keyRegistered or false
D.started = D.started or 0
D.attacks = D.attacks or 0
D.attacks134 = D.attacks134 or 0
D.partyAttacks = D.partyAttacks or 0
D.missingTarget = D.missingTarget or 0
D.lastAction = D.lastAction or 'none'
D.lastTarget = D.lastTarget or 'none'
D.errors = D.errors or 0
D.lastError = D.lastError or '-'
D.hotkeys = D.hotkeys or 0
local F11, LC, RC, LA, RA = 0x40000044, 0x400000E0, 0x400000E4, 0x400000E2, 0x400000E6
local ATTACK = { [3]=true, [105]=true, [134]=true }
local function num(f)
    local ok, val = pcall(f)
    if ok and val ~= nil then return tonumber(val) end
    return nil
end
local function isParty(id)
    if not id or type(EEex_Sprite_GetInPortraitID) ~= 'function' then return false end
    for n=0,5 do
        local slotID = num(function() return EEex_Sprite_GetInPortraitID(n) end)
        if slotID == id then return true end
    end
    return false
end
function D.onStarted(sprite, action)
    D.started = D.started + 1
    local aid = num(function() return action.m_actionID end)
    D.lastAction = aid or '?'
    if not ATTACK[aid] then return end
    D.attacks = D.attacks + 1
    if aid == 134 then D.attacks134 = D.attacks134 + 1 end
    local actor = num(function() return sprite.m_id end)
    local target = num(function() return action.m_acteeID.m_Instance end)
    D.lastTarget = target or '?'
    if not target then D.missingTarget = D.missingTarget + 1; return end
    if actor and not isParty(actor) and isParty(target) then D.partyAttacks = D.partyAttacks + 1 end
end
local function down(code)
    if type(EEex_Key_IsDown) ~= 'function' then return false end
    local ok, val = pcall(EEex_Key_IsDown, code)
    return ok and val == true
end
local function display(s)
    if type(Infinity_DisplayString) ~= 'function' then
        D.errors = D.errors + 1
        D.lastError = 'Infinity_DisplayString unavailable'
        return
    end
    local ok = pcall(Infinity_DisplayString, s)
    if not ok then D.errors = D.errors + 1; D.lastError = 'Display failed' end
end
function D.onPressed(key, repeatPress)
    if key ~= F11 or repeatPress then return false end
    if not (down(LC) or down(RC)) or not (down(LA) or down(RA)) then return false end
    D.hotkeys = D.hotkeys + 1
    local P = BGX43Probe
    local loaded = type(P) == 'table'
    local registered = loaded and P.installed == true or false
    local events = loaded and type(P.events) == 'table' and #P.events or 0
    local errors = loaded and P.errors or 0
    local notice = loaded and P.firstNoticeShown == true or false
    local last = loaded and (P.lastError or '-') or 'MODULE_MISSING'
    display('BGX44 043 loaded='..tostring(loaded)..' listener='..tostring(registered)..' events='..tostring(events)..' errors='..tostring(errors)..' notice='..tostring(notice)..' last='..tostring(last))
    display('BGX44 044 hooks='..tostring(D.actionRegistered)..'/'..tostring(D.keyRegistered)..' actions='..tostring(D.started)..' attacks='..tostring(D.attacks)..' id134='..tostring(D.attacks134)..' party='..tostring(D.partyAttacks)..' noTarget='..tostring(D.missingTarget)..' lastID='..tostring(D.lastAction)..' errors='..tostring(D.errors))
    return false
end
if not D.actionRegistered then
    if type(EEex_Action_AddSpriteStartedActionListener) == 'function' then
        local ok = pcall(EEex_Action_AddSpriteStartedActionListener, D.onStarted)
        if ok then D.actionRegistered = true else D.lastError = 'ACTION_HOOK_FAILED'; D.errors = D.errors + 1 end
    else D.lastError = 'ACTION_API_MISSING'; D.errors = D.errors + 1 end
end
if not D.keyRegistered then
    if type(EEex_Key_AddPressedListener) == 'function' then
        local ok = pcall(EEex_Key_AddPressedListener, D.onPressed, false)
        if ok then D.keyRegistered = true else D.lastError = 'KEY_HOOK_FAILED'; D.errors = D.errors + 1 end
    else D.lastError = 'KEY_API_MISSING'; D.errors = D.errors + 1 end
end
