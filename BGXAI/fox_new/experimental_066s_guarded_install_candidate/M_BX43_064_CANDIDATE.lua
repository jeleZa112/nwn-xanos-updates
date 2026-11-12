-- BGXAI 056: EEex confirmed weapon-hit listener with F-gated BCS requests.
-- Loaded as M_BX43.lua only after separately confirmed guarded 056 install.
-- Writes BGX52_* LOCALS to one selected F-enabled guardian; never sends
-- Attack/ProtectObject, clears a queued player action or accesses the filesystem.
-- BCS verifies the live idle/modal/F/TTL conditions before ProtectObject.

BGX43Probe = BGX43Probe or {}
local P = BGX43Probe
P.schema = 1
P.version = "0.3.29-064-061-SAME-AREA-GUARD-SOURCE"
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
-- Additional passive verification at an actual weapon-hit calculation.
-- The engine supplies explicit attacker / victim objects here; unlike an
-- AttackReevaluate object selector, these are not unresolved CAIObjectTypes.
P.weaponHitCalls = 0
P.weaponHitErrors = 0
P.weaponHitRegistered = false
P.weaponHitRejections = {}
P.lastWeaponHit = nil
-- BGXAI 049: bounded, passive guard-coordination ADVISORIES. No engine actions.
P.guardSignals = {}
P.maxGuardSignals = 64
P.guardSignalCount = 0
P.guardSignalErrors = 0
P.lastGuardSignal = nil
P.guardDispatchEnabled = false -- Lua NEVER issues combat orders; BCS handles approved requests.

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

-- The advisory itself lists portraits; it does NOT assign a bodyguard.
-- BGX52Bridge.prepare() separately checks the F switch for each guardian.
local function makeGuardSignal(event, portraitIDs)
    if not event or event.event ~= "NONPARTY_WEAPON_HIT_ON_PARTY" then return nil end
    if type(event.actor_id) ~= "number" or type(event.target_id) ~= "number" then return nil end
    local seen, candidateIDs = {}, {}
    for _, partyID in ipairs(portraitIDs or {}) do
        if type(partyID) == "number" and partyID >= 0
           and partyID ~= event.target_id and partyID ~= event.actor_id
           and not seen[partyID] then
            seen[partyID] = true
            candidateIDs[#candidateIDs + 1] = partyID
        end
    end
    return {
        schema = 1,
        event = "PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT",
        source_event_sequence = event.sequence,
        attacker_id = event.actor_id,
        protected_id = event.target_id,
        candidate_party_ids = candidateIDs,
        candidate_order = "PORTRAIT_ONLY_NOT_PRIORITY",
        guard_switch_state = "UNKNOWN",
        line_of_sight = "UNKNOWN",
        ability_to_intercept = "UNKNOWN",
        confirmation = "ENGINE_WEAPON_HIT_CONTEXT",
        action_command_sent = false,
        dispatch_status = "ADVISORY_ONLY_BCS_BRIDGE_SEPARATE",
    }
end

-- Copies of guard signals must not leak mutable internal queue tables.
local function copyGuardSignals()
    local out = {}
    for i, signal in ipairs(P.guardSignals) do
        local rec = {}
        for k, v in pairs(signal) do
            if type(v) == "table" then
                local arr = {}
                for _, id in ipairs(v) do arr[#arr + 1] = id end
                rec[k] = arr
            else
                rec[k] = v
            end
        end
        out[i] = rec
    end
    return out
end

-- BGXAI 052 guarded threat-to-BCS bridge - SOURCE PROTOTYPE, NOT INSTALLED.
-- Only the matching BCS rule may execute ProtectObject. Never queues any engine action.
BGX52Bridge = BGX52Bridge or {}
local B = BGX52Bridge
B.enabled = true -- Enabled ONLY in installed BGXAI 056, and ONLY on guardian(s) with F=ON.
B.attempts = 0
B.prepared = 0
B.rejected = {}
B.last = nil
local TTL_TICKS = 300 -- 20 seconds at standard IE game clock; must match BCS time clock.
local MAX_GAME_TIME = 2147483346 -- signed-int room for TTL
local function safe(fn,...)
    local ok,val = pcall(fn,...)
    if ok then return val end
    return nil
end
local function reject(reason)
    B.rejected[reason]=(B.rejected[reason] or 0)+1
    B.last={result="NO_WRITE",reason=reason}
    return false,reason
end
local function validInt(x)
    return type(x)=="number" and x==math.floor(x) and x>=0 and x<=2147483647
end
function B.prepare(advisory)
    B.attempts=B.attempts+1
    if not B.enabled then return reject("disabled") end
    if type(advisory)~="table" or advisory.event~="PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT"
       or advisory.confirmation~="ENGINE_WEAPON_HIT_CONTEXT" then
       return reject("unconfirmed_hit")
    end
    local victimID,attackerID=advisory.protected_id,advisory.attacker_id
    local sequence=advisory.source_event_sequence
    if not validInt(victimID) or not validInt(attackerID) or victimID==attackerID
       or not validInt(sequence) or sequence==0 then return reject("invalid_identity") end
    if type(EEex_Sprite_GetInPortraitID)~="function" or type(EEex_GameObject_Get)~="function" then
       return reject("api_unavailable")
    end
    local slot, victim
    for i=0,5 do
       local id=safe(EEex_Sprite_GetInPortraitID,i)
       if id==attackerID then return reject("party_actor") end
       if id==victimID then slot=i+1;victim=safe(EEex_GameObject_Get,id) end
    end
    if not slot or not victim or safe(function()return victim.m_id end)~=victimID then return reject("victim_not_in_party") end
    local now=safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end)
    if not validInt(now) or now>MAX_GAME_TIME then return reject("clock_invalid") end
    local vx=safe(function()return victim.m_pos.x end)
    local vy=safe(function()return victim.m_pos.y end)
    if type(vx)~="number" or type(vy)~="number" then return reject("unknown_position") end
    -- 064: never select a defender in a different loaded ARE.
    local victimArea=safe(function()return victim.m_pArea end)
    if not victimArea or type(EEex_UDEqual)~="function" then return reject("area_comparison_unavailable") end
    local options={}
    for i=1,5 do -- Player1 is never a 042B team guardian.
       local id=safe(EEex_Sprite_GetInPortraitID,i)
       if validInt(id) and id~=victimID and id~=attackerID then
          local obj=safe(EEex_GameObject_Get,id)
          if obj and safe(function()return obj.m_id end)==id then
             local guard=safe(function()return obj:getLocalInt("BGX38_GUARD")end)
             local modal=safe(function()return obj.m_nModalState end)
             local xx=safe(function()return obj.m_pos.x end)
             local yy=safe(function()return obj.m_pos.y end)
             local guardArea=safe(function()return obj.m_pArea end)
             local sameArea=guardArea and safe(function()return EEex_UDEqual(guardArea,victimArea)end)==true
             if guard==1 and modal==0 and sameArea and type(xx)=="number" and type(yy)=="number" then
                local dx,dy=xx-vx,yy-vy
                options[#options+1]={sprite=obj,id=id,slot=i+1,dist=dx*dx+dy*dy}
             end
          end
       end
    end
    if #options==0 then return reject("no_guardian_with_f_mode_in_same_area") end
    table.sort(options,function(a,b)
       if a.dist==b.dist then return a.slot<b.slot end
       return a.dist<b.dist
    end)
    local best=options[1]
    -- 049 event sequence resets on reload; never persist it as dedup across saves.
    -- Persist monotonic GAME CLOCK + initialized flag instead.
    local previous=safe(function()return best.sprite:getLocalInt("BGX52_LAST_TICK")end)
    local initialized=safe(function()return best.sprite:getLocalInt("BGX52_HAS_SENT")end)
    if not validInt(previous) or (initialized~=0 and initialized~=1) then
       return reject("dedup_unreadable")
    end
    if initialized==1 and now<=previous then return reject("duplicate_same_tick_or_clock_rewound") end
    -- Write request LAST: script can never see a half-formed new request.
    -- A failure clears the request; never call Attack/ClearActions/ProtectObject from Lua.
    local function set(k,v)best.sprite:setLocalInt(k,v) end
    local ok=pcall(function()
       set("BGX52_REQ_SLOT",0)
       set("BGX52_EXPIRE",now+TTL_TICKS)
       set("BGX52_LAST_TICK",now)
       set("BGX52_HAS_SENT",1)
       set("BGX52_REQ_SLOT",slot)
    end)
    if not ok then
       pcall(set,"BGX52_REQ_SLOT",0)
       return reject("write_failure")
    end
    B.prepared=B.prepared+1
    B.last={result="PREPARED_BCS_ONLY",source_event_sequence=sequence,
            chosen_guardian=best.id,victim_id=victimID,victim_slot=slot,
            expires_at_tick=now+TTL_TICKS,orders_sent=false}
    return true,"prepared"
end

-- Called from EEex's block-weapon-hit dispatcher. This listener NEVER blocks
-- damage. Return false unconditionally, including on unexpected Lua errors.
function P.onWeaponHit(context)
    local ok = pcall(function()
        if not P.enabled then return end
        P.weaponHitCalls = P.weaponHitCalls + 1
        local attacker = context and context.attackingSprite
        local victim = context and context.targetSprite
        local actorID = attacker and safe(function() return attacker.m_id end)
        local targetID = victim and safe(function() return victim.m_id end)
        local reason = "unknown"
        local party, ordered = partyIDs()
        if type(actorID) ~= "number" or type(targetID) ~= "number" then
            reason = "missing_sprite_id"
        elseif party[actorID] then
            reason = "party_actor"
        elseif not party[targetID] then
            reason = "not_party_victim"
        else
            reason = "recorded"
        end
        P.lastWeaponHit = {actor_id = actorID or false,
                           target_id = targetID or false, reason = reason}
        if reason ~= "recorded" then
            P.weaponHitRejections[reason] = (P.weaponHitRejections[reason] or 0) + 1
            return
        end
        local id = attacker and safe(function() return attacker.m_curAction.m_actionID end)
        local x = safe(function() return attacker.m_pos.x end)
        local y = safe(function() return attacker.m_pos.y end)
        local confirmedEvent = {
            schema = 1,
            event = "NONPARTY_WEAPON_HIT_ON_PARTY",
            actor_id = actorID, target_id = targetID,
            target_source = "weapon_hit_context",
            action_id = type(id) == "number" and id or false,
            actor_x = type(x) == "number" and x or false,
            actor_y = type(y) == "number" and y or false,
            action_origin = "UNKNOWN", visibility = "UNKNOWN",
            hostility = "CONFIRMED_BY_WEAPON_HIT_CONTEXT",
            party_ids = ordered,
            sequence = P.nextSequence or 1,
        }
        P.events[#P.events + 1] = confirmedEvent
        P.nextSequence = (P.nextSequence or 1) + 1
        -- Failure in the advisory must NEVER break a registered weapon-hit event.
        local guardOK, guardRecord = pcall(makeGuardSignal, confirmedEvent, ordered)
        if guardOK and guardRecord then
            P.guardSignals[#P.guardSignals + 1] = guardRecord
            P.guardSignalCount = P.guardSignalCount + 1
            P.lastGuardSignal = guardRecord
            -- 056 opt-in bridge writes an F-gated BCS request; queues no Lua actions.
            if BGX52Bridge then
                local ok052 = pcall(BGX52Bridge.prepare, guardRecord)
                if not ok052 then P.guardSignalErrors=P.guardSignalErrors+1 end
            end
            if #P.guardSignals > P.maxGuardSignals then
                table.remove(P.guardSignals, 1)
            end
        elseif not guardOK then
            P.guardSignalErrors = P.guardSignalErrors + 1
        end
        if #P.events > P.maxEvents then
            table.remove(P.events, 1)
            P.dropped = P.dropped + 1
        end
    end)
    if not ok then P.weaponHitErrors = P.weaponHitErrors + 1 end
    return false -- CRITICAL: never suppress attack damage or on-hit effects.
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
        weapon_hit_listener = type(EEex_Sprite_AddBlockWeaponHitListener) == "function",
        weapon_hit_registered = P.weaponHitRegistered,
        weapon_hit_calls = P.weaponHitCalls,
        weapon_hit_errors = P.weaponHitErrors,
        guard_mode = "F_GATED_BCS_REQUESTS_056",
        bcs_bridge_enabled = B.enabled,
        bridge_prepared_count = B.prepared,
        bridge_attempts = B.attempts,
        bridge_last = (function()
            if not B.last then return nil end
            local t={} for k,v in pairs(B.last) do t[k]=v end return t
        end)(),
        bridge_rejections = (function() local t={} for k,v in pairs(B.rejected) do t[k]=v end return t end)(),
        guard_dispatch_enabled = P.guardDispatchEnabled,
        guard_signal_count = P.guardSignalCount,
        guard_signal_errors = P.guardSignalErrors,
        guard_signals = copyGuardSignals(),
        last_weapon_hit = (function()
            if not P.lastWeaponHit then return nil end
            local out = {}
            for k,v in pairs(P.lastWeaponHit) do out[k]=v end
            return out
        end)(),
        weapon_hit_rejections = (function()
            local out = {}
            for k,v in pairs(P.weaponHitRejections) do out[k]=v end
            return out
        end)(),
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
    P.guardSignals = {}
    P.lastGuardSignal = nil
    B.last = nil -- report buffer only; never clear saved LOCALS on party sprites.
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
    -- Missing hook leaves the earlier action observer operational, but reports
    -- the lack of on-hit verification clearly. No fabricated hit events.
    if type(EEex_Sprite_AddBlockWeaponHitListener) == "function" then
        local hitOK = pcall(EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit)
        P.weaponHitRegistered = hitOK
        if not hitOK then P.lastError = "WEAPON_HIT_LISTENER_REGISTRATION_FAILED" end
    else
        P.lastError = "WEAPON_HIT_LISTENER_UNAVAILABLE"
    end
    return true
end

P.init()