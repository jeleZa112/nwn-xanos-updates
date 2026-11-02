-- BGXAI SAFE BOOT PROBE v1. Does not register action hooks or inspect engine pointers.
-- This module is intentionally passive.
local ok, err = pcall(function()
    if type(io) ~= "table" or type(io.open) ~= "function" then return end
    local file = io.open("BGXAI_BOOT_PROBE.log", "a")
    if not file then return end
    file:write("BGXAI Lua module loaded: safe probe v1\n")
    file:close()
end)
-- No engine callbacks; no action hooks; no changes to combat AI.
