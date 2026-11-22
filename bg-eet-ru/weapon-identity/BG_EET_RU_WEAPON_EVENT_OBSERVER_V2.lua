-- BG_EET_RU WEAPON EVENT OBSERVER V2: SOURCE ONLY, NOT INSTALLED.
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


-- V2 source extension: bounded external evidence, only after authorized installation.
-- The configured report paths are generated from the single updater and are outside the game.
local BG_EET_RU_V105_EXPORT_FILE = __V105_EVENTS_PATH__
local BG_EET_RU_V105_STATUS_FILE = __V105_STATUS_PATH__
local function BG_EET_RU_V105_SaveLine(path, line)
    if type(io) ~= "table" or type(io.open) ~= "function" then return false end
    return pcall(function()
        local f = io.open(path, "ab")
        if not f then error("EXTERNAL_FILE_NOT_WRITABLE") end
        f:write(line, "\n")
        f:close()
    end)
end
local function BG_EET_RU_V105_Sanitize(v)
    local s = tostring(v)
    s = s:gsub("[\t\r\n\\]", "_")
    return s:sub(1, 92)
end
local BG_EET_RU_V105_OriginalDamage = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
    BG_EET_RU_V105_OriginalDamage(context)
    local state = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1
    if not state.enabled or state.total_recorded > state.max_events then return end
    local event = state.events[#state.events]
    if not event then return end
    local line = "EVENT\t" .. tostring(event.ordinal)
    local names = {}
    for name in pairs(event.fields) do
        names[#names+1] = name
    end
    table.sort(names)
    for _, key in ipairs(names) do
        local field = event.fields[key]
        local value = ""
        if field.primitive ~= nil then value = BG_EET_RU_V105_Sanitize(field.primitive) end
        line = line .. "\t" .. BG_EET_RU_V105_Sanitize(key) .. ":" ..
                      BG_EET_RU_V105_Sanitize(field.value_type) .. ":" .. value
        if #line > 3000 then break end
    end
    BG_EET_RU_V105_SaveLine(BG_EET_RU_V105_EXPORT_FILE, line)
end

local BG_EET_RU_V105_OriginalStart = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_Start
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_Start()
    local ok, reason = BG_EET_RU_V105_OriginalStart()
    BG_EET_RU_V105_SaveLine(BG_EET_RU_V105_STATUS_FILE,
        "START\t" .. tostring(ok) .. "\t" .. BG_EET_RU_V105_Sanitize(reason))
    return ok, reason
end
BG_EET_RU_V105_SaveLine(BG_EET_RU_V105_STATUS_FILE, "SOURCE_LOADED")
