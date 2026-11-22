-- BG_EET_RU WEAPON EVENT OBSERVER V1: SOURCE ONLY, NOT INSTALLED.
-- Purpose: discover *available* context fields at base-weapon-damage events.
-- This is not an attack-log annotator, not a miss observer, and not a damage modifier.
-- Do not load this file or call Start without separate explicit installation approval.
-- No game/log/save writes, no disk writes, and no action/AI modification.

BG_EET_RU_WEAPON_EVENT_OBSERVER_V1 = {
    enabled = false,
    registered = false,
    max_events = 64,
    events = {},
    total_seen = 0,
    total_recorded = 0,
}

local function bounded_field_record(context)
    local fields = {}
    local observed = 0
    if type(context) ~= 'table' then return fields end
    for key, value in pairs(context) do
        if type(key) == 'string' and #key <= 80 then
            observed = observed + 1
            if observed > 80 then break end
            local kind = type(value)
            local entry = { value_type = kind }
            if kind == 'number' and value == value and math.abs(value) < 1000000000 then
                entry.primitive = value
            elseif kind == 'boolean' then
                entry.primitive = value
            elseif kind == 'string' then
                entry.primitive = value:sub(1, 120)
            end
            -- Never dereference or stringify userdata (may be CItem/CGameSprite).
            fields[key] = entry
        end
    end
    return fields
end

function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
    local st = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1
    if not st.enabled then return end
    st.total_seen = st.total_seen + 1
    local record = {
        kind = 'base_weapon_damage',
        ordinal = st.total_seen,
        fields = bounded_field_record(context),
        -- Actual weapon, ammo, target, and attack-to-log correlation are UNKNOWN.
        weapon_id_verified = false,
        ammo_id_verified = false,
        attack_log_row_correlated = false,
    }
    st.events[#st.events + 1] = record
    if #st.events > st.max_events then table.remove(st.events, 1) end
    st.total_recorded = st.total_recorded + 1
    -- No context mutations. No combat state modifications. No return value.
end

function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_Start()
    local st = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1
    if st.registered then st.enabled = true; return true, 'ALREADY_REGISTERED' end
    if type(EEex_Sprite_AddAlterBaseWeaponDamageListener) ~= 'function' then
        return false, 'EEEX_DAMAGE_LISTENER_UNAVAILABLE'
    end
    EEex_Sprite_AddAlterBaseWeaponDamageListener(
        BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
    )
    st.registered = true
    st.enabled = true
    return true, 'LISTENER_REGISTERED'
end

function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_Stop()
    -- EEex listener-registration API has no verified removal API in this build.
    -- Disable recording rather than pretending to detach the registered callback.
    BG_EET_RU_WEAPON_EVENT_OBSERVER_V1.enabled = false
end

function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_Status()
    local st = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1
    return {
        enabled = st.enabled,
        registered = st.registered,
        total_seen = st.total_seen,
        total_recorded = st.total_recorded,
        buffered_events = #st.events,
        observed_hit_or_damage_only = true,
        misses_proven = false,
        launcher_ammo_pair_proven = false,
        log_row_attribution_proven = false,
    }
end
