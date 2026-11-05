-- BGXAI 0.2.3 — read-only EEex party action / status observer.
-- STAGED ONLY. Does NOT issue ANY in-game action, modify variables or write files.
-- Output is printed to the existing InfinityLoader/EEex log when the host mirrors print().
-- No enemy knowledge from offscreen actors. No inference of manual commands or tank aggro.
local g = _G
local MAX_EVENTS, NOISY_EVERY, MAX_ERRORS = 4500, 12, 5
local nEvents, errors = 0, 0
local lastRoster, counts = nil, {}
local priority = {[3]=true,[105]=true,[134]=true,[355]=true,[296]=true}

local function safe(fn)
  local ok, result = pcall(fn)
  if ok then return result end
  return nil
end
local function num(value, low, high)
  local x = tonumber(value)
  if not x or x ~= x or x == math.huge or x == -math.huge or x%1 ~= 0 then return '?' end
  if x < low or x > high then return '?' end
  return tostring(x)
end
local function objectId(sprite)
  return tonumber(safe(function() return sprite.m_id end))
end
local function party()
  local members, ids, unique = {}, {}, {}
  for index=0,5 do
    local sprite=safe(function() return EEex_Sprite_GetInPortrait(index) end)
    if sprite then
      local id=objectId(sprite)
      if not id or id < 0 or id%1 ~= 0 or unique[id] then return nil end
      unique[id]=true
      members[index+1]=sprite
      ids[id]=index+1
    end
  end
  return members, ids
end
local function localFlag(sprite, name)
  return num(safe(function() return sprite:getLocalInt(name) end), -2147483648, 2147483647)
end
local function targetClass(action, actorId, ids)
  local t=tonumber(safe(function() return action.m_acteeID.m_Instance end))
  if t==nil or t<0 then return 'UNKNOWN' end
  if t==actorId then return 'SELF' end
  if ids[t] then return 'PARTY'..ids[t] end
  -- No enemy assertion: target can be familiar, neutral or object and not in LOS.
  return 'NONPARTY_UNVERIFIED'
end
local function coord(read)
  return num(safe(read), -30000, 30000)
end
local function partySignature(members)
  local parts={}
  for i=1,6 do
    parts[i]=members[i] and tostring(objectId(members[i])) or '-'
  end
  return table.concat(parts,':') -- internal only, NEVER printed.
end
local function currentLOS(sprite)
  return num(safe(function()
    return sprite:countAllOfTypeStringInRange('[EVILCUTOFF]',448,true,false)
  end),0,4096)
end
local function started(sprite,action)
  local ok,err=pcall(function()
    if nEvents>=MAX_EVENTS then return end
    local members,ids=party()
    if not ids then return end
    local id=objectId(sprite)
    local slot=ids[id]
    if not slot or type(action)=='nil' then return end
    local signature=partySignature(members)
    if signature~=lastRoster then
      lastRoster=signature
      counts={}
      -- Does not prove a save reload if party identity stays the same.
      print('[BGX23] ROSTER changed=1 sessionEpoch=UNKNOWN')
    end
    counts[slot]=(counts[slot] or 0)+1
    local code=tonumber(safe(function() return action.m_actionID end))
    if not code or code%1~=0 then return end
    local emit=priority[code] or counts[slot]==1 or counts[slot]%NOISY_EVERY==0
    if not emit then return end
    local st=safe(function() return sprite.m_baseStats end)
    local hp=num(st and safe(function() return st.m_hitPoints end),-100000,100000)
    local class=num(st and safe(function() return st.m_class end),0,100000)
    local skill=localFlag(sprite,'BDAI_SKILL_MODE')
    local attackMode=localFlag(sprite,'BDAI_ATTACK_MODE')
    local selected=safe(function() return EEex_Sprite_GetSelectedID() end)
    local sel=(tonumber(selected)==id) and 'SELECTED' or 'UNKNOWN'
    local posx=coord(function() return sprite.m_pos.x end)
    local posy=coord(function() return sprite.m_pos.y end)
    local destx=coord(function() return action.m_dest.x end)
    local desty=coord(function() return action.m_dest.y end)
    -- Event numbers are only within this observer session; no time or origin is asserted.
    nEvents=nEvents+1
    print(string.format('[BGX23] OBS seq=%d actor=A%d slot=%d action=%s hp=%s class=%s pos=%s,%s dest=%s,%s target=%s enemyLOS=%s selected=%s skill=%s atkMode=%s manual=UNKNOWN enemyTarget=UNKNOWN weapon=UNKNOWN maxHP=UNKNOWN path=UNKNOWN sessionEpoch=UNKNOWN',
      nEvents,slot,slot,num(code,0,9999),hp,class,posx,posy,destx,desty,
      targetClass(action,id,ids),currentLOS(sprite),sel,skill,attackMode))
  end)
  if not ok and errors<MAX_ERRORS then
    errors=errors+1
    print('[BGX23] READ_ERROR cause=unverified_fields') -- Do not leak paths from exceptions.
  end
end
if g.BGX23_REGISTERED then
  print('[BGX23] ALREADY_REGISTERED')
elseif type(EEex_Sprite_GetInPortrait)~='function' or
       type(EEex_Action_AddSpriteStartedActionListener)~='function' then
  print('[BGX23] DISABLED missing_EEex_APIs')
else
  local ok=pcall(EEex_Action_AddSpriteStartedActionListener,started)
  if ok then
    g.BGX23_REGISTERED=true
    print('[BGX23] REGISTERED shadow_only max=4500 no_game_actions=1 radar=OPTIONAL')
  else
    print('[BGX23] DISABLED listener_rejected')
  end
end
