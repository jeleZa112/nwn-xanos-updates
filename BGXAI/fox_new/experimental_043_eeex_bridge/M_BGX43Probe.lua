-- BGXAI 043 / EEex v1.1.7 observation-only bridge. NOT A COMBAT AI INSTALLER.
-- Loaded as M_*.lua only after a future explicit, verified installation.
-- Read-only CGameSprite/action fields; never calls QueueResponse, ClearActions,
-- ActionOverride, SetGlobal, mutating engine APIs, filesystem I/O or network.

BGX43Probe = BGX43Probe or {}
local P = BGX43Probe
P.schema = 1
P.version = "0.3.13-043-PROBE"
P.events = P.events or {}
P.maxEvents = 64
P.enabled = true
P.installed = P.installed or false
P.errors = P.errors or 0
P.dropped = P.dropped or 0
P.lastError = nil
P.manualOriginKnown = false -- Listener has no player-vs-script origin metadata.

local attackAction = { [3] = true, [105] = true }

local function safe(f, ...)
    local ok, value = pcall(f, ...)
    if ok then return value end
    return nil
end

local function partyIDs()
    local set, ordered = {}, {}
    if type(EEex_Sprite_GetInPortraitID) ~= "function" then return set, ordered end
    for i = 0, 5 do
        local id = safe(EEex_Sprite_GetInPortraitID, i)
        if type(id) == "number" and id >= 0 then
            set[id] = true
            ordered[#ordered + 1] = id
        end
    end
    return set, ordered
end

local function actionInfo(sprite, action)
    if not sprite or not action then return nil end
    local id = safe(function() return action.m_actionID end)
    if not attackAction[id] then return nil end
    local actorID = safe(function() return sprite.m_id end)
    local targetID = safe(function() return action.m_acteeID.m_Instance end)
    if type(actorID) ~= "number" or type(targetID) ~= "number" then return nil end
    local party, ordered = partyIDs()
    if party[actorID] or not party[targetID] then return nil end
    local x = safe(function() return sprite.m_pos.x end)
    local y = safe(function() return sprite.m_pos.y end)
    -- Position may be unknown: never invent a valid trajectory or visibility.
    local result = {
        schema = 1,
        event = "NONPARTY_ATTACK_STARTED_ON_PARTY",
        actor_id = actorID,
        target_id = targetID,
        action_id = id,
        actor_x = type(x) == "number" and x or false,
        actor_y = type(y) == "number" and y or false,
        action_origin = "UNKNOWN",
        visibility = "UNKNOWN",
        hostility = "CONFIRMED_BY_EXPLICIT_ATTACK_ACTION",
        party_ids = ordered,
        sequence = P.nextSequence or 1,
    }
    P.nextSequence = (P.nextSequence or 1) + 1
    return result
end

function P.onStarted(sprite, action)
    if not P.enabled then return end
    local ok, result = pcall(actionInfo, sprite, action)
    if not ok then
        P.errors = P.errors + 1
        P.lastError = "ACTION_READ_FAILURE" -- Do not leak game state or a traceback.
        return
    end
    if not result then return end
    P.events[#P.events + 1] = result
    if #P.events > P.maxEvents then
        table.remove(P.events, 1)
        P.dropped = P.dropped + 1
    end
end

function P.snapshot()
    -- Returns a COPY. The original bounded buffer remains private.
    local out = {}
    for i, event in ipairs(P.events) do
        local copy = {}
        for key, value in pairs(event) do
            if type(value) == "table" then
                local t = {}
                for _, v in ipairs(value) do t[#t + 1] = v end
                copy[key] = t
            else
                copy[key] = value
            end
        end
        out[i] = copy
    end
    return {
        schema = P.schema,
        version = P.version,
        installed = P.installed,
        enabled = P.enabled,
        origin_verifiable = false,
        queue_verifiable = false,
        action_listener = type(EEex_Action_AddSpriteStartedActionListener) == "function",
        party_api = type(EEex_Sprite_GetInPortraitID) == "function",
        error_count = P.errors,
        dropped = P.dropped,
        events = out,
    }
end

function P.clearMemory()
    P.events = {}
    P.dropped = 0
    -- No engine state changed, only this module's private Lua ring buffer.
end

function P.init()
    if P.installed then return true end
    if type(EEex_Action_AddSpriteStartedActionListener) ~= "function"
        or type(EEex_Sprite_GetInPortraitID) ~= "function" then
        P.lastError = "REQUIRED_EEEX_1_1_7_API_MISSING"
        return false
    end
    local ok = pcall(EEex_Action_AddSpriteStartedActionListener, P.onStarted)
    if not ok then
        P.lastError = "LISTENER_REGISTRATION_FAILED"
        return false
    end
    P.installed = true
    return true
end

P.init()
