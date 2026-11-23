-- BG_EET_RU V107 — SOURCE ONLY. Not installed, not loaded, no active hooks.
-- The 2026-11-23 real V106 capture confirmed two events:
-- EVENT 1: weapon userdata, no launcher; EVENT 2: weapon AND launcher userdata.
-- Runtime userdata are not retained by V105/V106. Identify item RESREF only in
-- an active callback, never from a stale object or a saved primitive record.
--
-- EEex Docs CItem: baseclass_0 = CResHelper<CResItem,1005>, whose cResRef is
-- a CResRef; EEex scripts use flattened baseclass item.pRes. Thus cResRef may
-- be accessible through the CItem SWIG binding as item.cResRef:get().
-- Runtime field access is NOT yet proved on user's EEex build. pcall does not
-- guarantee safety against native-memory faults. Remain disabled by default.
--
-- No damage modification, event registration, game action, AI/UI or file I/O.
-- Native reads require a separately approved guarded runtime implementation.

BG_EET_RU_V107 = {
    enabled = false,
    capture_native_item_refs = false,
    seen = 0,
    saved = 0,
    max_events = 32,
    buffer = {},
    source_only = true,
}

local function primitive(value)
    local t = type(value)
    if t == "boolean" then return value and "true" or "false" end
    if t == "number" then
        if value ~= value or value > 99999999 or value < -99999999 then
            return "INVALID_NUMBER"
        end
        return tostring(value)
    end
    return "UNKNOWN"
end

local function sanitized_ref(ref)
    if type(ref) ~= "string" then return nil end
    if #ref < 1 or #ref > 8 then return nil end
    if not ref:match("^[%a%d_]+$") then return nil end
    return string.upper(ref)
end

local function resref_now(item)
    if not BG_EET_RU_V107.capture_native_item_refs then
        return "NATIVE_ITEM_READ_NOT_AUTHORIZED"
    end
    if type(item) ~= "userdata" then return "NO_CITEM_USERDATA" end
    -- The CItem binding/ABI must be validated before enabling this branch.
    local ok, value = pcall(function()
        return item.cResRef:get()
    end)
    local result = ok and sanitized_ref(value) or nil
    return result or "NATIVE_ITEM_RESREF_UNVERIFIED"
end

function BG_EET_RU_V107_Inspect(context)
    local state = BG_EET_RU_V107
    if not state.enabled or type(context) ~= "table" then return end
    state.seen = state.seen + 1
    if state.saved >= state.max_events then return end
    local record = {
        ordinal=state.seen,
        weapon_type=type(context.weapon),
        launcher_type=type(context.launcher),
        ability_type=type(context.ability),
        attacker_type=type(context.attacker),
        target_type=type(context.target),
        attack_roll=primitive(context.attackRoll),
        critical=primitive(context.isCritical),
        weapon_resref=resref_now(context.weapon),
        launcher_resref=resref_now(context.launcher),
        -- A launcher's item RESREF is not the arrow/bolt/bullet's RESREF.
        ammo_resref="NOT_VERIFIED",
        attack_to_journal_row="NOT_VERIFIED",
        miss_coverage="NOT_VERIFIED",
    }
    state.saved=state.saved+1
    state.buffer[#state.buffer+1]=record
    if #state.buffer>state.max_events then table.remove(state.buffer,1) end
    return nil
end

function BG_EET_RU_V107_Status()
    local s=BG_EET_RU_V107
    return {
        enabled=s.enabled, capture_native_item_refs=s.capture_native_item_refs,
        seen=s.seen, saved=s.saved, buffered=#s.buffer,
        miss_coverage_verified=false, ammo_identification_verified=false,
        journal_row_mapping_verified=false,
    }
end
