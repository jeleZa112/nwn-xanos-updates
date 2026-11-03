-- BGXAI 0.7.3 SHADOW / capability and perception observer for EET + EEex.
-- Side effects: ONLY bounded diagnostic print() and one read-only action listener.
-- No gameplay actions, global/local writes, external files, internet or UI modification.
-- This file is a STAGED CANDIDATE, not part of BGXAI_UPDATE.cmd.
local g = _G
local MAX_OBS = 250
local PER_ACTOR_ACTION_INTERVAL = 20
local MAX_ERRORS = 5
local observed, errors = 0, 0
local roster, aliases, lastSignature, counters = {}, {}, {}, {}
local nextAlias = 0

local function protected(fn)
  local ok, value = pcall(fn)
  if not ok or value == nil then return nil end
  return value
end
local function txt(value)
  if value == nil then return '?' end
  if type(value) == 'boolean' then return value and '1' or '0' end
  if type(value) == 'number' and value == value and value > -1000000000 and value < 1000000000 then
    return tostring(value)
  end
  return '?'
end
local function actorAlias(id)
  if aliases[id] == nil then
    nextAlias = nextAlias + 1
    aliases[id] = 'A'..tostring(nextAlias)
  end
  return aliases[id]
end
local function partySnapshot()
  local list, seen = {}, {}
  for slot = 0, 5 do
    local sprite = protected(function() return EEex_Sprite_GetInPortrait(slot) end)
    if sprite ~= nil then
      local id = tonumber(protected(function() return sprite.m_id end))
      if id == nil or id < 0 or id % 1 ~= 0 or seen[id] then return nil end
      seen[id] = true
      list[id] = {slot = slot + 1, sprite = sprite}
    end
  end
  return list
end
local function classDetails(sprite)
  local bs = protected(function() return sprite.m_baseStats end)
  if bs == nil then return '?','?','?','?','?','?' end
  local c = protected(function() return bs.m_class end)
  local k = protected(function() return bs.m_kit end)
  local l1 = protected(function() return bs.m_level1 end)
  local l2 = protected(function() return bs.m_level2 end)
  local l3 = protected(function() return bs.m_level3 end)
  local hp = protected(function() return bs.m_hitPoints end)
  return txt(c),txt(k),txt(l1),txt(l2),txt(l3),txt(hp)
end
local function getLocal(sprite, key)
  local value = protected(function() return sprite:getLocalInt(key) end)
  return type(value) == 'number' and txt(value) or '?'
end
local function visibleHostiles(sprite)
  -- Documented LOS-limited lookup. It is NOT a guarantee that the area is safe.
  local value = protected(function()
    return sprite:countAllOfTypeStringInRange('[EVILCUTOFF]',448,true,false)
  end)
  if type(value) ~= 'number' or value < 0 then return '?' end
  return txt(value)
end
local function selectedID()
  if type(EEex_Sprite_GetSelectedID) ~= 'function' then return nil end
  return protected(EEex_Sprite_GetSelectedID)
end
local function snapshotActor(sprite, slot)
  local c,k,l1,l2,l3,hp = classDetails(sprite)
  local hostiles = visibleHostiles(sprite)
  local localNames = {
    'BDAI_DISABLE_ATTACK','BDAI_DISABLE_ITEMS',
    'BDAI_DISABLE_OFFENSIVE','BDAI_DISABLE_DEFENSIVE',
    'BDAI_DISABLE_SPECIAL','BDAI_SKILL_MODE','BDAI_ATTACK_MODE',
    'BDAI_NO_ARCANE'
  }
  local values = {}
  for i,name in ipairs(localNames) do values[i] = getLocal(sprite,name) end
  local id = tonumber(protected(function() return sprite.m_id end))
  local lead = tonumber(selectedID())
  local selected = lead ~= nil and id == lead and 'leader' or 'no_or_unknown'
  return string.format('slot=%d class=%s kit=%s level=%s/%s/%s hp=%s enemyLOS=%s selected=%s BDAI=%s manual=? trap=? path=? identity=SESSION_ONLY',
    slot,c,k,l1,l2,l3,hp,hostiles,selected,table.concat(values,','))
end
local function onAction(sprite, action)
  local ok, err = pcall(function()
    if observed >= MAX_OBS then return end
    local current = partySnapshot()
    if current == nil then return end -- never infer departure from transient invalid read
    local id = tonumber(protected(function() return sprite.m_id end))
    if id == nil or current[id] == nil then return end
    if type(action) ~= 'table' and type(action) ~= 'userdata' and type(action) ~= 'cdata' then return end
    counters[id] = (counters[id] or 0) + 1
    -- A noisy source: sample one of every twenty action starts, plus first and roster changes.
    if counters[id] > 1 and counters[id] % PER_ACTOR_ACTION_INTERVAL ~= 0 then return end
    local slot = current[id].slot
    local alias = actorAlias(id)
    local signature = snapshotActor(sprite,slot)
    if signature ~= lastSignature[id] then
      lastSignature[id] = signature
      observed = observed + 1
      print('[BGX73] OBS actor='..alias..' '..signature)
    end
    -- Never report actor names, raw game IDs, scripts, inventories or paths.
  end)
  if not ok and errors < MAX_ERRORS then
    errors = errors + 1
    print('[BGX73] READ_ERROR '..tostring(err):gsub('[\r\n]',' '):sub(1,80))
  end
end

if g.BGXAI073_OBSERVER_REGISTERED then
  print('[BGX73] ALREADY_REGISTERED')
elseif type(EEex_Sprite_GetInPortrait) ~= 'function' or
       type(EEex_Action_AddSpriteStartedActionListener) ~= 'function' then
  print('[BGX73] DISABLED required EEex APIs unavailable')
else
  local ok, err = pcall(EEex_Action_AddSpriteStartedActionListener,onAction)
  if ok then
    g.BGXAI073_OBSERVER_REGISTERED = true
    print('[BGX73] REGISTERED READ_ONLY selected/class/kit/levels/BDAI/enemyLOS; trap/route/manual=UNKNOWN')
  else
    print('[BGX73] DISABLED listener rejected '..tostring(err):sub(1,80))
  end
end