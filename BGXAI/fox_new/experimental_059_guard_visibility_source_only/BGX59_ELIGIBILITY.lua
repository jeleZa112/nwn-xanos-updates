-- BGXAI 059 / SAFE OFFLINE ELIGIBILITY POLICY (SOURCE ONLY)
-- Pure selection helper. Does not install in EET, mutate LOCALS or issue engine actions.
-- 059 intended for integration into 056's BGX52Bridge.prepare before choosing guardian.
BGX59Eligibility = BGX59Eligibility or {}
local E = BGX59Eligibility
E.version = "0.3.24-059-GUARD-ELIGIBILITY-SOURCE"
-- EEex Sprite docs: sprite visual range is ~448 pixels. This is a deliberately
-- smaller *pre-filter*, NOT a replacement for BCS Range(PlayerN,10).
E.maxVisualDistancePixels = 128

local function probe(fn)
    local ok, result = pcall(fn)
    if ok then return result end
    return nil
end

function E.check(guardian, victim)
    if not guardian or not victim then return false, "missing_sprite" end
    if type(EEex_UDEqual) ~= "function" then
        return false, "area_comparison_unavailable"
    end
    local ga = probe(function() return guardian.m_pArea end)
    local va = probe(function() return victim.m_pArea end)
    if not ga or not va then return false, "area_unknown" end
    local same = probe(function() return EEex_UDEqual(ga, va) end)
    if same ~= true then return false, "different_or_unreadable_area" end
    if type(EEex_Sprite_ForAllOfTypeStringInRange) ~= "function" then
        return false, "sight_api_unavailable"
    end
    local victimID = probe(function() return victim.m_id end)
    if type(victimID) ~= "number" or victimID < 0 then
        return false, "victim_id_unavailable"
    end
    local seen = false
    local ran = pcall(function()
        EEex_Sprite_ForAllOfTypeStringInRange(
            guardian, "[ANYONE]", E.maxVisualDistancePixels,
            function(sprite)
                if probe(function() return sprite.m_id end) == victimID then seen = true end
            end, true, false)
    end)
    if not ran then return false, "sight_query_failed" end
    if not seen then return false, "not_visible_nearby" end
    return true, "eligible_preflight"
end

function E.choose(victim, options)
    if type(options) ~= "table" then return nil, "options_invalid" end
    local count = 0
    local rejectCounts = {}
    local eligible = {}
    for _, item in ipairs(options) do
        count = count + 1
        local ok, reason = E.check(item.sprite, victim)
        if ok then
            eligible[#eligible + 1] = item
        else
            rejectCounts[reason] = (rejectCounts[reason] or 0) + 1
        end
    end
    if #eligible == 0 then
        if count == 0 then return nil, "no_f_mode_guardian" end
        if rejectCounts.different_or_unreadable_area == count then
            return nil, "no_guardian_same_area"
        end
        return nil, "no_guardian_visible_nearby"
    end
    table.sort(eligible, function(a,b)
        if a.dist == b.dist then return a.slot < b.slot end
        return a.dist < b.dist
    end)
    return eligible[1], "selected"
end
