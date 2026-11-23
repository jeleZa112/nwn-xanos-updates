-- BG_EET_RU V107 guarded CItem callback probe — SOURCE ONLY / NOT INSTALLED.
-- No automatic registration, no mutation of attack context or combat state.
-- Exact callback shape independently demonstrated in cdtweaks:
-- EEex_Sprite_AddAlterBaseWeaponDamageListener(function(context)
--    local resref = context.weapon.cResRef:get()
-- end)
-- Upstream example does not prove safe native ABI on this user's EEex build.
-- WARNING: Lua pcall does NOT prevent a native crash or invalid userdata dereference.
-- An exact Windows-version gate and separate typed approval are prerequisites.

BG_EET_RU_V107_GUARD = {
    enabled = false,
    native_abi_verified = false,
    explicit_native_read_consent = false,
    source_only = true,
    max_events = 16,
    seen = 0,
    recorded = 0,
    events = {},
}

local function scalar(value)
    if type(value) == 'boolean' then return tostring(value) end
    if type(value) ~= 'number' then return 'UNKNOWN' end
    if value ~= value or value > 100000000 or value < -100000000 then
        return 'INVALID_NUMBER'
    end
    return tostring(value)
end

local function resref_string(ref)
    if type(ref) ~= 'string' or #ref < 1 or #ref > 8 then return nil end
    if not ref:match('^[%w_]+$') then return nil end
    -- Restrict to ASCII to avoid locale-dependent pattern exceptions.
    if ref:find('[^A-Za-z0-9_]') then return nil end
    return ref:upper()
end

local function read_citem_ref(item, state)
    if not state.native_abi_verified or not state.explicit_native_read_consent then
        return 'HOLD_NATIVE_READ_NOT_AUTHORIZED'
    end
    if type(item) ~= 'userdata' then return 'NO_CITEM_USERDATA' end
    -- Only inside the original callback. Never retain item/userdata after return.
    -- pcall catches Lua exceptions only, NOT a native segmentation fault.
    local ok, value = pcall(function() return item.cResRef:get() end)
    if not ok then return 'NATIVE_READ_LUA_ERROR' end
    return resref_string(value) or 'NATIVE_READ_UNVERIFIED_VALUE'
end

-- Called by an already-registered V105/V106 listener ONLY after a future
-- explicitly approved same-CMD deployment; no auto-hook or auto-execution.
function BG_EET_RU_V107_GuardedObserve(context)
    local st = BG_EET_RU_V107_GUARD
    if not st.enabled or type(context) ~= 'table' then return nil end
    st.seen = st.seen + 1
    if st.recorded >= st.max_events then return nil end
    local rec = {
        ordinal = st.seen,
        attack_roll = scalar(context.attackRoll),
        critical = scalar(context.isCritical),
        weapon_type = type(context.weapon),
        launcher_type = type(context.launcher),
        weapon_resref = read_citem_ref(context.weapon, st),
        launcher_resref = read_citem_ref(context.launcher, st),
        ammo_resref = 'NOT_VERIFIED',
        is_hit = 'NOT_VERIFIED',
        is_miss = 'NOT_VERIFIED',
        journal_row = 'NOT_VERIFIED',
    }
    st.recorded = st.recorded + 1
    st.events[#st.events + 1] = rec
    -- No raw CItem userdata, pointers, attacker or target retained.
    return nil
end

function BG_EET_RU_V107_GuardStatus()
    local s = BG_EET_RU_V107_GUARD
    return {
        source_only = s.source_only,
        enabled = s.enabled,
        native_abi_verified = s.native_abi_verified,
        native_read_authorized = s.explicit_native_read_consent,
        seen = s.seen,
        recorded = s.recorded,
        event_count = #s.events,
        ammo_verified = false,
        miss_coverage_verified = false,
        journal_mapping_verified = false,
    }
end
