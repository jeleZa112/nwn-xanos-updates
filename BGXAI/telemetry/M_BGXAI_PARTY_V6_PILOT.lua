-- BGXAI v6 PARTY ACTION PROBE (read-only PILOT, NOT auto-installed)
-- Portrait-based party membership; current game M_BGXAI.lua is unchanged.
-- Uses EEex_Sprite_GetInPortrait(0..5). Never edits game state or queues.
local total, errors, limit = 0, 0, 12000
local sampleEnemy = { ["Волк"] = true, ["Wolf"] = true }
local function get(read)
  local ok,v = pcall(read)
  if not ok or v == nil then return "NA" end
  return tostring(v):gsub("[%c]", "?"):sub(1,64)
end
local function partySlot(sprite)
  if type(EEex_Sprite_GetInPortrait) ~= "function" then return nil end
  local id = get(function() return sprite.m_id end)
  if id == "NA" then return nil end
  for slot=0,5 do
    local ok, member = pcall(EEex_Sprite_GetInPortrait, slot)
    if ok and member ~= nil then
      local mid = get(function() return member.m_id end)
      if mid ~= "NA" and mid == id then return slot + 1 end
    end
  end
  return nil
end
local function onStarted(sprite, action)
  local ok, err = pcall(function()
    local name = get(function() return sprite.m_sName.m_pchData:get() end)
    local slot = partySlot(sprite)
    if not slot and not sampleEnemy[name] then return end
    total = total + 1
    if total > limit then
      if total == limit + 1 then print("[BGXAI] PARTY_V6 LIMIT REACHED") end
      return
    end
    local id = get(function() return sprite.m_id end)
    local code = get(function() return action.m_actionID end)
    local x = get(function() return sprite.m_pos.x end)
    local y = get(function() return sprite.m_pos.y end)
    local dx = get(function() return action.m_dest.x end)
    local dy = get(function() return action.m_dest.y end)
    local target = get(function() return action.m_acteeID.m_Instance end)
    print(string.format("[BGXAI] ACTION_%05d name=%s id=%s action=%s pos=(%s,%s) dest=(%s,%s) target=%s slot=%s", total,name,id,code,x,y,dx,dy,target,tostring(slot or 0)))
  end)
  if not ok and errors < 5 then
    errors = errors + 1
    print("[BGXAI] PARTY_V6 HOOK_ERROR "..tostring(err):sub(1,160))
  end
end
if type(EEex_Sprite_GetInPortrait) ~= "function" then
  print("[BGXAI] PARTY_V6 DISABLED: portrait EEex API missing (no fallback or changes)")
elseif type(EEex_Action_AddSpriteStartedActionListener) ~= "function" then
  print("[BGXAI] PARTY_V6 DISABLED: action listener missing")
else
  EEex_Action_AddSpriteStartedActionListener(onStarted)
  print("[BGXAI] PARTY_V6 READ_ONLY HOOK REGISTERED")
end
