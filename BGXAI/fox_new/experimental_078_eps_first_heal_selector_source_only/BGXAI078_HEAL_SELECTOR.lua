-- BGXAI 078: EPS-first advisory selector for an already confirmed injured ally.
-- SOURCE ONLY: no EEex APIs, no hook, timers, game variable writes or engine orders.
-- Unknown and unverified facts MUST NOT be silently treated as available.
local M = {version='0.3.45-078-HEAL-SELECTOR-SOURCE-ONLY', installed=false}
local function integer(v)
  return type(v)=='number' and v==math.floor(v) and v>0 and v<2147483647
end
local function num(v)
  return type(v)=='number' and v==v and v>-1e9 and v<1e9
end
local function deny(why, counters, trace)
  return {status='NO_REQUEST',reason=why,selected_id=nil,selected_slot=nil,
    orders_sent=0,locals_written=0,engine_dispatch=false,
    rejected=counters or {},trace=trace or {}}
end
local function safe_copy(t)
  local out={}
  if type(t)=='table' then for k,v in pairs(t) do out[k]=v end end
  return out
end
local function rejected(counters,trace,candidate,why)
  counters[why]=(counters[why] or 0)+1
  if #trace<12 then trace[#trace+1]={id=candidate and candidate.id or nil,reason=why} end
end
local function ready(c, victim_id, ids, seen)
  if type(c)~='table' or not integer(c.id) or seen[c.id] then return 'INVALID_OR_DUPLICATE_CANDIDATE' end
  seen[c.id]=true
  if type(c.slot)~='number' or c.slot~=math.floor(c.slot) or c.slot<1 or c.slot>6 then return 'INVALID_PARTY_SLOT' end
  if c.in_party~=true or c.guard_f_on~=true then return 'NOT_AVAILABLE_FOR_F_GUARD_SUPPORT' end
  if c.id==ids.attacker_id then return 'ATTACKER_NOT_HEALER' end
  -- The candidate can be the patient if they actually have a confirmed heal.
  if c.alive~=true or c.same_area~=true or c.can_act~=true then return 'ACTOR_NOT_AVAILABLE' end
  if type(c.role)~='table' or c.role.verified~=true or c.role.heal_capable~=true then
    return 'NO_VERIFIED_HEAL_CAPABILITY'
  end
  -- A restored dual, class/kit and Shaman are all admitted by verified ability,
  -- NEVER by an allowlist inferred from raw CLASS.IDS alone.
  if type(c.spell)~='table' or c.spell.verified~=true
    or c.spell.bcs_spell_id~='CLERIC_CURE_LIGHT_WOUNDS'
    or c.spell.usable_now~=true then return 'NO_VERIFIED_USABLE_BCS_SPELL' end
  if type(c.target)~='table' or c.target.verified~=true
    or c.target.victim_id~=victim_id or c.target.visible~=true
    or c.target.in_bcs_range_10~=true then return 'TARGET_NOT_REACHABLE_BY_BCS' end
  if type(c.eps)~='table' or c.eps.verified~=true then return 'EPS_STATE_UNVERIFIED' end
  if c.eps.manual_command~=false or c.eps.casting~=false
    or c.eps.singing~=false or c.eps.detecting_traps~=false
    or c.eps.heal_pending~=false then return 'EPS_PRIORITY_ACTION_ACTIVE' end
  if c.eps.queue_empty~=true or c.eps.idle~=true then return 'EPS_QUEUE_BUSY_OR_UNKNOWN' end
  if c.request_pending~=false then return 'REQUEST_ALREADY_PENDING_OR_UNKNOWN' end
  -- Only a separately verified squared-distance ordering metric is used here.
  -- Never convert EEex raw pixels to BCS Range(): they are different units.
  if c.distance_verified~=true or not num(c.distance_sq)
    or c.distance_sq<0 then return 'DISTANCE_UNKNOWN' end
  return nil
end
-- event: verified hit + verified current patient HP; candidates: factual read-only snapshots.
-- Output contains a *proposal*, never a pending request, spell command or game write.
function M.select(event, candidates, config)
  if type(config)~='table' or config.opt_in~=true then return deny('OPT_IN_OFF') end
  if type(event)~='table' or event.verified~=true or
    event.type~='CONFIRMED_HOSTILE_WEAPON_HIT' or event.party_victim~=true
    or event.attacker_is_party~=false or not integer(event.attacker_id)
    or not integer(event.victim_id) or event.victim_id==event.attacker_id then
    return deny('UNCONFIRMED_HOSTILE_HIT')
  end
  if event.hp_verified~=true or not num(event.hp_percent) or
     event.hp_percent<=0 or event.hp_percent>=45 then
    return deny('NO_VERIFIED_HEAL_EMERGENCY')
  end
  if event.existing_eps_heal_handling~=false then
    return deny('EXISTING_EPS_HEAL_UNCONFIRMED_OR_ACTIVE')
  end
  if type(candidates)~='table' then return deny('INVALID_CANDIDATE_LIST') end
  local counts,trace,seen={}, {}, {}
  local best=nil
  for i,c in ipairs(candidates) do
    -- Hard upper bound is a safety measure against stale/malformed source lists.
    if i>6 then return deny('CANDIDATES_EXCEED_PARTY_SIZE',counts,trace) end
    local why=ready(c,event.victim_id,event,seen)
    if why then rejected(counts,trace,c,why)
    else
      if not best or c.distance_sq<best.distance_sq
        or (c.distance_sq==best.distance_sq and c.slot<best.slot) then
        best={id=c.id,slot=c.slot,distance_sq=c.distance_sq}
      end
    end
  end
  if not best then return deny('NO_VERIFIED_USABLE_HEALER',counts,trace) end
  return {status='ADVISORY_HEAL_CANDIDATE_ONLY',reason='NO_GAME_DISPATCH_IMPLEMENTED',
    selected_id=best.id,selected_slot=best.slot,
    verified_spell='CLERIC_CURE_LIGHT_WOUNDS',
    orders_sent=0,locals_written=0,engine_dispatch=false,
    rejected=safe_copy(counts),trace=trace}
end
return M
