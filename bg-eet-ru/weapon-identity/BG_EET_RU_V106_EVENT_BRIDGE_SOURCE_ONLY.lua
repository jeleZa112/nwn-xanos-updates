-- BG_EET_RU V106 — SOURCE ONLY; not installed or auto-loaded.
-- Real V105 runtime observation: registered callback; event fields attacker/target/weapon/
-- ability/effect=userdata; attackRoll=number; isCritical/isLeftHand=boolean; io.open absent.
-- Read objects only while callback is active. No changes to damage/effect, no hook patches.
-- Logs through Infinity_Log only; no io/open/file writes. No automatic registration.

BG_EET_RU_V106 = {
    enabled = false,
    registered = false,
    seen = 0,
    logged = 0,
    max_events = 64,
    recent = {},
    -- RESREF reading is a separate gate. Keep disabled until live API/ABI validation.
    enable_weapon_resref = false,
}

local function safe_scalar(value)
    local kind = type(value)
    if kind == "boolean" then return value and "true" or "false" end
    if kind == "number" then
        if value ~= value or math.abs(value) > 99999999 then return "INVALID" end
        return tostring(value)
    end
    return "UNKNOWN"
end

local function safe_resref(weapon)
    if not BG_EET_RU_V106.enable_weapon_resref then return "NOT_ENABLED" end
    if type(weapon) ~= "userdata" then return "NOT_USERDATA" end
    -- CItem / CResHelper layout identified in EEex x64 docs. This is a
    -- native-bound userdata dereference, therefore not enabled until tested
    -- on the specific game build. pcall handles Lua errors but not native crashes.
    local ok, name = pcall(function() return weapon.baseclass_0.cResRef:get() end)
    if not ok or type(name) ~= "string" or #name < 1 or #name > 8 then
        return "UNVERIFIED"
    end
    if not name:match("^[%w_]+$") then return "UNVERIFIED" end
    return string.upper(name)
end

function BG_EET_RU_V106_OnDamage(context)
    local st = BG_EET_RU_V106
    if not st.enabled then return end
    st.seen = st.seen + 1
    if st.logged >= st.max_events then return end
    if type(context) ~= "table" then return end
    local line = "BG_EET_RU_V106 EVENT " .. st.seen ..
        " roll=" .. safe_scalar(context.attackRoll) ..
        " critical=" .. safe_scalar(context.isCritical) ..
        " left=" .. safe_scalar(context.isLeftHand) ..
        " weapon_type=" .. type(context.weapon) ..
        " weapon_resref=" .. safe_resref(context.weapon) ..
        " ability_type=" .. type(context.ability) ..
        " attacker_type=" .. type(context.attacker) ..
        " target_type=" .. type(context.target)
    st.logged = st.logged + 1
    st.recent[#st.recent+1] = line
    if #st.recent > st.max_events then table.remove(st.recent,1) end
    if type(Infinity_Log) == "function" then pcall(Infinity_Log,line) end
    -- Intentionally no return and no mutation of context.
end

function BG_EET_RU_V106_Start()
    local st = BG_EET_RU_V106
    if st.registered then st.enabled=true;return true,"ALREADY_REGISTERED" end
    if type(EEex_Sprite_AddAlterBaseWeaponDamageListener)~="function" then
        return false,"EEEX_LISTENER_MISSING"
    end
    EEex_Sprite_AddAlterBaseWeaponDamageListener(BG_EET_RU_V106_OnDamage)
    st.registered=true
    st.enabled=true
    return true,"REGISTERED"
end

function BG_EET_RU_V106_Stop()
    -- No confirmed listener removal API. Only disable recording.
    BG_EET_RU_V106.enabled=false
end

function BG_EET_RU_V106_Status()
    local st=BG_EET_RU_V106
    return {registered=st.registered,enabled=st.enabled,seen=st.seen,
        logged=st.logged,buffered=#st.recent,weapon_resref_enabled=st.enable_weapon_resref,
        misses_verified=false,ammo_verified=false,combat_log_correlation_verified=false}
end
