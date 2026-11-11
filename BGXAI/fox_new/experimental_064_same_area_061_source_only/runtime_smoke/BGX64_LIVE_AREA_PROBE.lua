-- BGXAI 064 / source-only read-only EEex area comparison smoke test.
-- Invoke probe() from an already available Lua console; NEVER place in override.
-- Does not register listeners, write locals, issue commands or modify files.
local M = {}
local function safely(fn, ...)
    local ok, val = pcall(fn, ...)
    if ok then return val end
    return nil
end
local function object_area(i)
    local id = safely(EEex_Sprite_GetInPortraitID, i)
    if type(id) ~= 'number' or id < 0 or id ~= math.floor(id) then return nil end
    local obj = safely(EEex_GameObject_Get, id)
    if not obj then return nil end
    if safely(function() return obj.m_id end) ~= id then return nil end
    return safely(function() return obj.m_pArea end), id
end
function M.probe()
    local report = {
        schema = 1, kind = 'BGX64_READ_ONLY_LIVE_API_PROBE',
        status = 'API_UNAVAILABLE', api = false,
        valid_sprites = 0, self_true = 0, self_failed = 0,
        pair_true = 0, pair_false = 0, pair_failed = 0,
        install_authorized = false,
    }
    if type(EEex_UDEqual) ~= 'function'
        or type(EEex_Sprite_GetInPortraitID) ~= 'function'
        or type(EEex_GameObject_Get) ~= 'function' then return report end
    report.api = true
    local areas, seen = {}, {}
    for i=0,5 do
        local area, id = object_area(i)
        if area and not seen[id] then
            seen[id] = true
            report.valid_sprites = report.valid_sprites + 1
            local result = safely(EEex_UDEqual, area, area)
            if result == true then
                report.self_true = report.self_true + 1
                areas[#areas+1] = area
            else
                report.self_failed = report.self_failed + 1
            end
        end
    end
    if report.valid_sprites == 0 then report.status = 'NO_VALID_GAME_SPRITES'; return report end
    if report.self_failed > 0 then report.status = 'SELF_EQUALITY_FAILED'; return report end
    for i=1,#areas do for j=i+1,#areas do
        local result = safely(EEex_UDEqual, areas[i], areas[j])
        if result == true then report.pair_true=report.pair_true+1
        elseif result == false then report.pair_false=report.pair_false+1
        else report.pair_failed=report.pair_failed+1 end
    end end
    if report.pair_failed > 0 then report.status = 'PAIR_COMPARISON_FAILED'
    elseif report.pair_true > 0 then report.status = 'SAME_AREA_API_CONFIRMED'
    else report.status = 'SELF_ONLY_NO_IN_AREA_PAIR' end
    return report
end
function M.message(r)
    return 'BGX64 area='..r.status..' api='..tostring(r.api)
        ..' sprites='..r.valid_sprites..' self='..r.self_true..'/'..r.valid_sprites
        ..' pairs='..r.pair_true..'/'..r.pair_false..'/'..r.pair_failed
end
return M
