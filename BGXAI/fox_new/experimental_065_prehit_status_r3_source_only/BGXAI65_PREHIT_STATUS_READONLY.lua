-- BGXAI 065-R3 SOURCE ONLY. Read existing live 064 observer state; never install hooks.
-- Run in EET Lua console only when an ordinary combat event has already occurred.
local function say(t) pcall(function() C:DisplayText(t) end) end
local p=BGX43Probe
if type(p)~='table' then
  say('BGX65PRE NO_OBSERVER')
else
  say('BGX65PRE init='..tostring(p.installed)..' seen='..tostring(p.seenActions)..
    ' candidates='..tostring(p.attackCandidates)..' hits='..tostring(p.weaponHitCalls)..
    ' registered='..tostring(p.weaponHitRegistered))
  local a=p.lastAttack
  if type(a)=='table' then
    say('BGX65PRE action='..tostring(a.action_id)..' reason='..tostring(a.reason)..
      ' source='..tostring(a.target_source)..' actor='..tostring(a.actor_id)..
      ' victim='..tostring(a.target_id)..' a1='..tostring(a.target1)..
      ' a2='..tostring(a.target2)..' sprite='..tostring(a.sprite_target))
  else
    say('BGX65PRE lastAction=NONE')
  end
  local h=p.lastWeaponHit
  if type(h)=='table' then
    say('BGX65PRE lastHit='..tostring(h.reason)..' actor='..tostring(h.actor_id)..
      ' victim='..tostring(h.target_id))
  else
    say('BGX65PRE lastHit=NONE')
  end
end
