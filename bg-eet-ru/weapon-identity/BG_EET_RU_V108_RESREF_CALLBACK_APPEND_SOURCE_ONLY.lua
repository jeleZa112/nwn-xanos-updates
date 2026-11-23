-- BG_EET_RU V108 RESTRICTED CItem RESREF pilot, SOURCE ONLY, NOT INSTALLED.
-- Append only to exact pinned V106 BG_EET_RU_WeaponObserver.lua.
-- No new listener registration, no game effect / action / UI / TLK mutation.
-- A future guarded installer MUST hash EEex.dll, EEex_Sprite.lua,
-- EEex_Sprite_Patch.lua, EEex_Main.lua and exact V106 module, take external
-- backup, require typed user approval, and provide atomic last-only rollback.
-- NOTE: pcall does NOT prevent native memory corruption / process crash.

BG_EET_RU_V108 = {
    enabled = false, -- MUST remain off until a separately authorized install
    native_read_authorized = false,
    max_samples = 8,
    seen = 0,
    emitted = 0,
    weapon_refs_verified = 0,
    launcher_refs_verified = 0,
    ammo_verified = false,
    misses_verified = false,
    journal_mapping_verified = false,
}

local function v108_ref(obj)
    if type(obj) ~= 'userdata' then return 'NOT_CITEM_USERDATA' end
    -- This dereferences native CItem. It is ONLY permitted while the callback
    -- is executing with the exact approved ABI + source hashes.
    local ok, ref = pcall(function() return obj.cResRef:get() end)
    if not ok then return 'LUA_READ_ERROR' end
    if type(ref) ~= 'string' or #ref == 0 or #ref > 8 then return 'INVALID_RESREF' end
    if ref:find('[^A-Za-z0-9_]') then return 'INVALID_RESREF' end
    return string.upper(ref)
end

local v108_previous_callback = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
    -- Preserve the proven, installed V106 observer and its bounded event logs.
    v108_previous_callback(context)
    local st = BG_EET_RU_V108
    if not st.enabled or not st.native_read_authorized then return nil end
    if type(context) ~= 'table' then return nil end
    st.seen = st.seen + 1
    if st.emitted >= st.max_samples then return nil end
    local weapon = v108_ref(context.weapon)
    local launcher = v108_ref(context.launcher)
    if weapon ~= 'INVALID_RESREF' and weapon ~= 'NOT_CITEM_USERDATA' and weapon ~= 'LUA_READ_ERROR' then
        st.weapon_refs_verified = st.weapon_refs_verified + 1
    end
    if launcher ~= 'INVALID_RESREF' and launcher ~= 'NOT_CITEM_USERDATA' and launcher ~= 'LUA_READ_ERROR' then
        st.launcher_refs_verified = st.launcher_refs_verified + 1
    end
    st.emitted = st.emitted + 1
    if type(Infinity_Log) == 'function' then
        local line = '[BG_EET_RU_V108] EVENT\t' .. tostring(st.emitted) ..
                     '\tweapon_resref=' .. weapon .. '\tlauncher_resref=' .. launcher ..
                     '\tammo=UNVERIFIED\thit_miss=UNVERIFIED\tjournal_row=UNVERIFIED'
        pcall(Infinity_Log,line)
    end
    return nil
end

function BG_EET_RU_V108_Status()
    local s=BG_EET_RU_V108
    return {enabled=s.enabled, native_read_authorized=s.native_read_authorized,
        max_samples=s.max_samples, seen=s.seen, emitted=s.emitted,
        weapon_refs_verified=s.weapon_refs_verified,
        launcher_refs_verified=s.launcher_refs_verified,
        ammo_verified=false, misses_verified=false, journal_mapping_verified=false}
end
