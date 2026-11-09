-- BGXAI 043 / EEex v1.1.7 observation-only bridge. NOT A COMBAT AI INSTALLER.
-- Loaded as M_*.lua only after a future explicit, verified installation.
-- Read-only CGameSprite/action fields; never calls QueueResponse, ClearActions,
-- ActionOverride, SetGlobal, mutating engine APIs, filesystem I/O or network.

BGX43Probe = BGX43Probe or {}
local P = BGX43Probe
P.schema = 1
P.version = "0.3.18-047-RESOLVED-TARGET"
P.events = P.events or {}
P.maxEvents = 64
P.enabled = true
P.installed = P.installed or false
P.errors = P.errors or 0
P.dropped = P.dropped or 0
P.lastError = nil
P.firstNoticeShown = P.firstNoticeShown or false
P.manualOriginKnown = false -- Listener has no player-vs-script origin metadata.
-- Bounded, read-only diagnostic counters for filtered attack actions.
P.seenActions = 0
P.attackCandidates = 0
P.rejections = {}
P.lastAttack = nil

-- Confirmed BGEE ACTION.IDS attack-family codes; do not infer target identity
-- from GroupAttack(94) without a concrete portrait id.
local attackAction = { [3] = true, [94] = true, [98] = true,
                       [105] = true, [134] = true }

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
    if not sprite or not action then return nil, "missing_args" end
    local id = safe(function() return action.m_actionID end)
    if not attackAction[id] then return nil end
    P.attackCandidates = P.attackCandidates + 1
    local actorID = safe(function() return sprite.m_id end)
    -- AttackReevaluate decodes the target into m_acteeID2 when the action starts.
    -- Keep the original field for explicit targets / predecoded actions. A -1
    -- m_Instance is *not* a target, even when combat text shows a real victim.
    local target1 = safe(function() return action.m_acteeID.m_Instance end)
    local target2 = safe(function() return action.m_acteeID2.m_Instance end)
    local resolvedId = safe(function() return sprite.m_targetId end) -- diagnostic only
    local party, ordered = partyIDs()
    local targetID, targetSource
    -- For AttackReevaluate/AttackOneRound the *decoded* target takes priority.
    local prefer2 = id == 134 or id == 105
    if prefer2 then
        if type(target2) == "number" and target2 >= 0 then
            targetID, targetSource = target2, "actee2"
        elseif type(target1) == "number" and target1 >= 0 then
            targetID, targetSource = target1, "actee1"
        end
    else
        if type(target1) == "number" and target1 >= 0 then
            targetID, targetSource = target1, "actee1"
        elseif type(target2) == "number" and target2 >= 0 then
            targetID, targetSource = target2, "actee2"
        end
    end
    P.lastAttack = {action_id = id, actor_id = actorID or false,
                    target_id = targetID or false, target1 = target1 or false,
                    target2 = target2 or false, sprite_target = resolvedId or false,
                    target_source = targetSource or "none", reason = "unresolved"}
    if type(actorID) ~= "number" then
        P.lastAttack.reason = "actor_not_numeric"
        return nil, "actor_not_numeric"
    end
    if type(targetID) ~= "number" then
        P.lastAttack.reason = "target_unresolved"
        return nil, "target_unresolved"
    end
    if party[actorID] then
        P.lastAttack.reason = "party_actor"
        return nil, "party_actor"
    end
    if not party[targetID] then
        P.lastAttack.reason = "target_not_party"
        return nil, "target_not_party"
    end
    P.lastAttack.reason = "recorded"
    local x = safe(function() return sprite.m_pos.x end)
    local y = safe(function() return sprite.m_pos.y end)
    -- Position may be unknown: never invent a valid trajectory or visibility.
    local result = {
        schema = 1,
        event = "NONPARTY_ATTACK_STARTED_ON_PARTY",
        actor_id = actorID,
        target_id = targetID,
        target_source = targetSource,
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
    P.seenActions = P.seenActions + 1
    local ok, result, reason = pcall(actionInfo, sprite, action)
    if not ok then
        P.errors = P.errors + 1
        P.lastError = "ACTION_READ_FAILURE" -- Do not leak game state or a traceback.
        return
    end
    if not result then
        if reason then P.rejections[reason] = (P.rejections[reason] or 0) + 1 end
        return
    end
    P.events[#P.events + 1] = result
    -- Optional one-time, UI-only observer proof; never enqueue an AI action.
    -- If no game UI is ready, the event is still recorded without error.
    if not P.firstNoticeShown and type(Infinity_DisplayString) == "function" then
        local displayed = pcall(Infinity_DisplayString,
            "BGXAI 043 observer: party attack seen (NO AI COMMANDS)")
        if displayed then P.firstNoticeShown = true end
    end
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
        first_notice_shown = P.firstNoticeShown,
        seen_actions = P.seenActions,
        attack_candidates = P.attackCandidates,
        -- Copy the diagnostics as well; snapshot() never exposes the mutable map.
        rejections = (function()
            local copy = {}
            for k, v in pairs(P.rejections) do copy[k] = v end
            return copy
        end)(),
        last_attack = (function()
            if not P.lastAttack then return nil end
            local copy = {}
            for k, v in pairs(P.lastAttack) do copy[k] = v end
            return copy
        end)(),
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
