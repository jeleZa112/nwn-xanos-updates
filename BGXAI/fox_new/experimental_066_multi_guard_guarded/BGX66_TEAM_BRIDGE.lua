-- BGXAI 066: replacement selector for the EXISTING EEex confirmed-weapon-hit bridge.
-- No new listener. No Attack/Spell/ClearActions; only existing BGX52 BCS LOCALS.
-- Only verified frontline base classes 2/6/12 may receive ProtectObject requests.
-- All other classes (including dual/multi and unknown respec) are passive support.
BGX66Team = BGX66Team or {}
local T = BGX66Team
T.version = '0.3.32-066-MULTI-FRONTLINE-GUARDED'
T.enabled = true
T.attempts, T.prepared, T.errors = 0, 0, 0
T.rejected = {}
T.reservations = {} -- ephemeral, keyed by guardian id
T.victims = {}      -- ephemeral, keyed by victim id
T.last = nil
local RESERVE_TICKS, EXPIRE_TICKS, MAX_TIME = 45, 300, 2147483346
local FRONTLINE = {[2]=true,[6]=true,[12]=true} -- fighter/paladin/ranger CLASS.IDS
local SUPPORT = {[1]='arcane',[3]='healer',[5]='bard',[7]='arcane',[8]='healer',
                 [10]='arcane',[11]='healer',[13]='arcane',[14]='arcane_healer',
                 [16]='healer',[17]='arcane_healer',[18]='healer',[19]='arcane'}
local function safe(f,...) local ok,v=pcall(f,...);if ok then return v end; return nil end
local function integer(x)
  return type(x)=='number' and x==math.floor(x) and x>=0 and x<=2147483647
end
local function finite(x) return type(x)=='number' and x==x and x>-100000000 and x<100000000 end
local function stop(reason)
  T.rejected[reason]=(T.rejected[reason] or 0)+1
  T.last={status='NO_WRITE',reason=reason,orders_sent=0}
  if BGX52Bridge then BGX52Bridge.rejected[reason]=(BGX52Bridge.rejected[reason] or 0)+1;BGX52Bridge.last=T.last end
  return false,reason
end
local function roleOf(sprite)
  local cls=safe(function()return sprite.m_typeAI.m_Class end)
  if FRONTLINE[cls] then return 'frontline',cls end
  return SUPPORT[cls] or 'unknown',cls
end
local function urgency(sprite)
  local hp=safe(function()return sprite.m_baseStats.m_hitPoints end)
  local mh=safe(function()return sprite.m_derivedStats.m_nMaxHitPoints end)
  if not finite(hp) or not finite(mh) or hp<=0 or mh<=0 then return nil end
  if hp<=3 or hp/mh<=0.2 then return 1 end
  local role=roleOf(sprite)
  if role=='arcane' or role=='healer' or role=='bard' or role=='arcane_healer' then return 2 end
  if hp/mh<=0.5 then return 3 end
  if role=='frontline' then return 5 end
  return 4
end
local function validGuardian(sprite)
  local hp=safe(function()return sprite.m_baseStats.m_hitPoints end)
  local mh=safe(function()return sprite.m_derivedStats.m_nMaxHitPoints end)
  return finite(hp) and finite(mh) and hp>3 and mh>0 and hp/mh>0.50
end
local function resetIfClockRewound(now)
  if T.lastTick and now<T.lastTick then T.reservations={};T.victims={} end
  T.lastTick=now
end
local function purge(now)
  for k,v in pairs(T.reservations) do if not integer(v.untilTick) or v.untilTick<=now then T.reservations[k]=nil end end
  for k,v in pairs(T.victims) do if not integer(v) or v<=now then T.victims[k]=nil end end
end
local function dispatch(advisory)
  T.attempts=T.attempts+1
  if BGX52Bridge then BGX52Bridge.attempts=BGX52Bridge.attempts+1 end
  if not T.enabled or not BGX52Bridge or BGX52Bridge.enabled~=true then return stop('disabled') end
  if type(advisory)~='table' or advisory.event~='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT'
    or advisory.confirmation~='ENGINE_WEAPON_HIT_CONTEXT' then return stop('unconfirmed_hit') end
  local victimID,attackerID,seq=advisory.protected_id,advisory.attacker_id,advisory.source_event_sequence
  if not integer(victimID) or not integer(attackerID) or not integer(seq) or seq==0
    or victimID==attackerID then return stop('identity_invalid') end
  if type(EEex_GameObject_Get)~='function' or type(EEex_Sprite_GetInPortraitID)~='function'
    or type(EEex_UDEqual)~='function' then return stop('eeex_unavailable') end
  local slot, victim, present=nil,nil,{}
  for i=0,5 do
    local id=safe(EEex_Sprite_GetInPortraitID,i)
    if integer(id) then
      present[id]=true
      if id==victimID then slot=i+1;victim=safe(EEex_GameObject_Get,id) end
    end
  end
  if present[attackerID] then return stop('party_attacker') end
  if not slot or not victim or safe(function()return victim.m_id end)~=victimID then return stop('victim_not_in_party') end
  local now=safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end)
  if not integer(now) or now>MAX_TIME then return stop('clock_unavailable') end
  resetIfClockRewound(now);purge(now)
  if T.victims[victimID] then return stop('victim_reserved') end
  local vx=safe(function()return victim.m_pos.x end)
  local vy=safe(function()return victim.m_pos.y end)
  local area=safe(function()return victim.m_pArea end)
  if not finite(vx) or not finite(vy) or area==nil then return stop('victim_position_missing') end
  local options,support={},{}
  for i=1,5 do
    local id=safe(EEex_Sprite_GetInPortraitID,i)
    if integer(id) and id~=victimID and id~=attackerID then
      local obj=safe(EEex_GameObject_Get,id)
      if obj and safe(function()return obj.m_id end)==id then
        local g=safe(function()return obj:getLocalInt('BGX38_GUARD')end)
        local modal=safe(function()return obj.m_nModalState end)
        local x=safe(function()return obj.m_pos.x end)
        local y=safe(function()return obj.m_pos.y end)
        local other=safe(function()return obj.m_pArea end)
        local same=other~=nil and safe(function()return EEex_UDEqual(area,other)end)==true
        if g==1 and modal==0 and finite(x) and finite(y) and same then
          local role=roleOf(obj)
          if role=='frontline' and validGuardian(obj) and not T.reservations[id] then
            local req=safe(function()return obj:getLocalInt('BGX52_REQ_SLOT')end)
            local previous=safe(function()return obj:getLocalInt('BGX52_LAST_TICK')end)
            local sent=safe(function()return obj:getLocalInt('BGX52_HAS_SENT')end)
            if req==0 and integer(previous) and (sent==0 or sent==1)
              and (sent==0 or now>previous) then
              local dx,dy=x-vx,y-vy
              options[#options+1]={id=id,slot=i+1,sprite=obj,distance=dx*dx+dy*dy}
            end
          elseif role~='frontline' then
            support[#support+1]={id=id,slot=i+1,role=role}
          end
        end
      end
    end
  end
  table.sort(support,function(a,b)return a.slot<b.slot end)
  if #options==0 then
    T.last={status='NO_FRONTLINE',victim_id=victimID,urgency=urgency(victim),
      support_candidates=support,orders_sent=0}
    if BGX52Bridge then BGX52Bridge.last=T.last end
    return false,'no_eligible_frontline'
  end
  table.sort(options,function(a,b)if a.distance~=b.distance then return a.distance<b.distance end; return a.slot<b.slot end)
  local best=options[1]
  -- Identical verified WeiDU/BCS receiver protocol to working 064.
  -- All keys must be written before final nonzero REQ_SLOT; failure clears it.
  local function set(k,v)best.sprite:setLocalInt(k,v) end
  local success=pcall(function()
    set('BGX52_REQ_SLOT',0)
    set('BGX52_EXPIRE',now+EXPIRE_TICKS)
    set('BGX52_LAST_TICK',now)
    set('BGX52_HAS_SENT',1)
    set('BGX52_REQ_SLOT',slot)
  end)
  if not success then
    pcall(set,'BGX52_REQ_SLOT',0)
    return stop('write_failed')
  end
  T.reservations[best.id]={victimID=victimID,untilTick=now+RESERVE_TICKS}
  T.victims[victimID]=now+RESERVE_TICKS
  T.prepared=T.prepared+1
  if BGX52Bridge then BGX52Bridge.prepared=BGX52Bridge.prepared+1 end
  T.last={status='PREPARED_BCS_ONLY',victim_id=victimID,
    guardian_id=best.id,guardian_slot=best.slot,victim_slot=slot,
    urgency=urgency(victim),support_candidates=support,
    expires_at=now+EXPIRE_TICKS,orders_sent=0}
  if BGX52Bridge then BGX52Bridge.last=T.last end
  return true,'prepared'
end
function T.prepare(advisory)
  local ok,result,reason=pcall(dispatch,advisory)
  if not ok then T.errors=T.errors+1;return stop('internal_error') end
  return result,reason
end
-- Existing onWeaponHit calls BGX52Bridge.prepare dynamically. Replace only selector.
BGX52Bridge.prepare=T.prepare
