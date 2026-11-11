-- BGXAI 062E / SOURCE ONLY / NEVER AUTO-LOADED.
-- Read-only probe for x64 EEex class ID and current action ID.
-- External code must call returned table's snapshot() deliberately.
-- No listener registration, no writes, no engine commands.
local function probe(f)
    local ok, value = pcall(f)
    if ok then return value end
    return nil
end

local function uint(n, maximum)
    return type(n) == 'number' and n == math.floor(n) and n >= 0 and n <= maximum
end

local function maybe_uint(n, maximum)
    if uint(n, maximum) then return n end
    return 'unknown'
end

local function snapshot()
    local result = {
        schema = 2,
        mode = 'READ_ONLY',
        origin = 'BGXAI_062E_SOURCE_ONLY',
        binding = 'X64_EEEX_SOURCE_DOCUMENTED_RUNTIME_UNVERIFIED',
        status = 'PARTIAL_OBSERVATIONS_ONLY',
        party = {},
    }
    if type(EEex_Sprite_GetInPortraitID) ~= 'function'
       or type(EEex_GameObject_Get) ~= 'function' then
        result.status = 'API_UNAVAILABLE'
        return result
    end
    local seen = {}
    for i = 0, 5 do
        local id = probe(function() return EEex_Sprite_GetInPortraitID(i) end)
        if uint(id, 2147483646) and not seen[id] then
            seen[id] = true
            local obj = probe(function() return EEex_GameObject_Get(id) end)
            if obj and probe(function() return obj.m_id end) == id then
                -- Class ID from EEex's x64 bound CGameSprite.m_typeAI.m_Class.
                -- Does not establish usable class features after respec/dual-class.
                local classID = probe(function() return obj.m_typeAI.m_Class end)
                -- Action ID is instantaneous; an idle sample is not permission to
                -- cancel human-issued orders or EPS queued casts.
                local actionID = probe(function() return obj.m_curAction.m_actionID end)
                local guard = probe(function() return obj:getLocalInt('BGX38_GUARD') end)
                local modal = probe(function() return obj.m_nModalState end)
                result.party[#result.party + 1] = {
                    slot = i + 1,
                    id = id,
                    guard_f = (guard == 0 or guard == 1) and guard or 'unknown',
                    modal = maybe_uint(modal, 65535),
                    class_id = maybe_uint(classID, 255),
                    current_action_id = maybe_uint(actionID, 65535),
                    equipped_weapon = 'unknown',
                    can_melee = 'unknown',
                    can_cast = 'unknown',
                    manual_order_absent = 'unknown',
                    action_queue_idle = 'unknown',
                    stealth_absent = 'unknown',
                    consciousness = 'unknown',
                    role = 'unknown',
                }
            end
        end
    end
    return result
end

return {snapshot = snapshot}
