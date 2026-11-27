-- BG_EET_RU V160: hit-only player-visible weapon label (experimental).
-- Append ONLY to SHA-verified existing V108 observer. No additional listeners.
-- EEex callback occurs after weapon-hit base damage effect is constructed;
-- NOT a miss hook, NOT proof damage was applied, NOT a journal-row join.
-- No changes to damage, APR, AI, item/effect/context, or engine hooks.
BG_EET_RU_V160_HIT = {enabled=true, shown=0, failed=0, cap=2000, busy=false, reason='READY'}
local BG_EET_RU_V160_previous = BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
local BG_EET_RU_V160_names = {
    SW1H04='Длинный меч',
    AROW01='Стрела',
    BOW05='Короткий лук',
}
local function BG_EET_RU_V160_ref(item)
    if type(item) ~= 'userdata' then return nil end
    local ok, ref = pcall(function() return item.cResRef:get() end)
    if not ok or type(ref)~='string' or #ref<1 or #ref>8 then return nil end
    if ref:find('[^A-Za-z0-9_]') then return nil end
    return string.upper(ref)
end
local function BG_EET_RU_V160_name(ref)
    if not ref then return nil end
    return BG_EET_RU_V160_names[ref] or ('код '..ref)
end
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
    local previous_result = BG_EET_RU_V160_previous(context)
    local s = BG_EET_RU_V160_HIT
    if not s.enabled or s.busy or type(context)~='table' then return previous_result end
    if s.shown >= s.cap then s.enabled=false; s.reason='SESSION_CAP'; return previous_result end
    if type(Infinity_DisplayString)~='function' then
        s.enabled=false; s.reason='DISPLAY_API_UNAVAILABLE'; return previous_result
    end
    local weapon = BG_EET_RU_V160_ref(context.weapon)
    if not weapon then return previous_result end
    local launcher = BG_EET_RU_V160_ref(context.launcher)
    local label = 'Оружие при попадании: '..BG_EET_RU_V160_name(weapon)
    if launcher then label = label..' ('..BG_EET_RU_V160_name(launcher)..')' end
    s.busy=true
    local ok = pcall(Infinity_DisplayString, label)
    s.busy=false
    if not ok then
        s.failed=s.failed+1; s.enabled=false; s.reason='DISPLAY_CALL_FAILED'
    else
        s.shown=s.shown+1
    end
    return previous_result
end
