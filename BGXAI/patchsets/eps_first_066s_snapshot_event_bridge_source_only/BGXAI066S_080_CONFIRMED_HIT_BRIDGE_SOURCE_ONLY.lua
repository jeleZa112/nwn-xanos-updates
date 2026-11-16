-- BGXAI: read-only adapter for the ACTUAL INSTALLED 066S BGX43Probe.snapshot() schema.
-- Connects 049/066S confirmed weapon-hit + corresponding F-guard advisory
-- to a bounded multi-threat OBSERVATION. Not a dispatch adapter.
-- In particular, an old weapon hit DOES NOT prove attacker active now,
-- origin of the latest command, or EPS/manual action queue status.
-- No hooks, globals, BCS LOCALS, engine calls, filesystem, or mutation.
local M={version='066S-080-CONFIRMED-HIT-ADAPTER-SOURCE-ONLY',installed=false}
local function ident(x)
 return type(x)=='number' and x==math.floor(x) and x>=1 and x<2147483647
end
local function bounded_array(t,limit)
 if type(t)~='table' then return nil end
 local n=0
 for k in pairs(t) do
  if type(k)~='number' or k~=math.floor(k) or k<1 or k>limit then return nil end
  n=n+1
 end
 for i=1,n do if t[i]==nil then return nil end end
 return n
end
local function stop(reason,counts)
 return {status='HOLD_NO_ENGINE_DISPATCH',reason=reason,
  observed_hits={},observed_count=0,skipped_orphan_signals=counts or 0,
  origin_verified=false,queue_empty_verified=false,
  active_now_verified=false,freshness_verified=false,
  orders_sent=0,locals_written=0,hooks_registered=0,
  engine_dispatch=false,safe_to_dispatch=false,installed=false}
end
local function validate_party_ids(ids,victim,attacker)
 local n=bounded_array(ids,6)
 if not n or n<1 then return false end
 local seen,hasVictim={},false
 for i=1,n do
  local id=ids[i]
  if not ident(id) or seen[id] or id==attacker then return false end
  seen[id]=true
  if id==victim then hasVictim=true end
 end
 return hasVictim,seen
end
local function hit_record(e)
 if type(e)~='table' or e.schema~=1 or
   e.event~='NONPARTY_WEAPON_HIT_ON_PARTY' or
   e.target_source~='weapon_hit_context' or
   e.hostility~='CONFIRMED_BY_WEAPON_HIT_CONTEXT' or
   e.action_origin~='UNKNOWN' or
   not ident(e.actor_id) or not ident(e.target_id) or
   e.actor_id==e.target_id or not ident(e.sequence) then return nil end
 local ok,party=validate_party_ids(e.party_ids,e.target_id,e.actor_id)
 if not ok then return nil end
 return {attacker_id=e.actor_id,victim_id=e.target_id,sequence=e.sequence,party=party}
end
local function guard_signal(s,hit)
 if type(s)~='table' or s.schema~=1 or
   s.event~='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT' or
   s.source_event_sequence~=hit.sequence or
   s.attacker_id~=hit.attacker_id or s.protected_id~=hit.victim_id or
   s.confirmation~='ENGINE_WEAPON_HIT_CONTEXT' or
   s.candidate_order~='PORTRAIT_ONLY_NOT_PRIORITY' or
   s.guard_switch_state~='UNKNOWN' or s.line_of_sight~='UNKNOWN' or
   s.ability_to_intercept~='UNKNOWN' or
   s.action_command_sent~=false or
   s.dispatch_status~='ADVISORY_ONLY_BCS_BRIDGE_SEPARATE' then return false end
 local n=bounded_array(s.candidate_party_ids,6)
 if not n then return false end
 local seen={}
 for i=1,n do
  local id=s.candidate_party_ids[i]
  if not ident(id) or seen[id] or not hit.party[id] or
     id==hit.attacker_id or id==hit.victim_id then return false end
  seen[id]=true
 end
 return true
end

function M.observe(snapshot)
 if type(snapshot)~='table' or snapshot.schema~=1 or
    snapshot.installed~=true or snapshot.enabled~=true or
    snapshot.weapon_hit_registered~=true or
    snapshot.origin_verifiable~=false or snapshot.queue_verifiable~=false or
    snapshot.guard_dispatch_enabled~=false then
  return stop('UNVERIFIED_066S_SNAPSHOT_CONTRACT')
 end
 local numEvents=bounded_array(snapshot.events,64)
 local numSignals=bounded_array(snapshot.guard_signals,64)
 if numEvents==nil or numSignals==nil then return stop('MALFORMED_SNAPSHOT_ARRAY') end
 local hitsBySequence={}
 for i=1,numEvents do
  local e=snapshot.events[i]
  if type(e)~='table' then return stop('MALFORMED_EVENT') end
  if e.event=='NONPARTY_WEAPON_HIT_ON_PARTY' then
   local h=hit_record(e)
   if not h or hitsBySequence[h.sequence] then return stop('CORRUPT_OR_DUPLICATE_HIT') end
   hitsBySequence[h.sequence]=h
  end
 end
 local joined,orphans={},0
 for i=1,numSignals do
  local signal=snapshot.guard_signals[i]
  if type(signal)~='table' then return stop('MALFORMED_GUARD_SIGNAL') end
  local seq=signal.source_event_sequence
  if not ident(seq) then return stop('INVALID_GUARD_SEQUENCE') end
  local hit=hitsBySequence[seq]
  if not hit then
   -- The two 066S ring buffers may roll over independently. A signal without
   -- the corresponding hit is NOT proof of an active threat.
   orphans=orphans+1
  else
   if joined[seq] or not guard_signal(signal,hit) then
    return stop('CORRUPT_OR_DUPLICATE_GUARD_SIGNAL',orphans)
   end
   joined[seq]=hit
  end
 end
 -- Only the latest corroborated *hit* per attacker is reported.
 local sorted={}
 for _,h in pairs(joined) do sorted[#sorted+1]=h end
 table.sort(sorted,function(a,b) return a.sequence>b.sequence end)
 local seenAttacker,observed={},{}
 for _,h in ipairs(sorted) do
  if not seenAttacker[h.attacker_id] and #observed<6 then
   seenAttacker[h.attacker_id]=true
   observed[#observed+1]={attacker_id=h.attacker_id,victim_id=h.victim_id,
    source_event_sequence=h.sequence,
    evidence='EEEX_CONFIRMED_WEAPON_HIT_AND_MATCHED_GUARD_ADVISORY',
    -- Deliberately do not claim a timestamp / ongoing attack / current role.
    event_time_verified=false,active_now_verified=false,
    queue_empty_verified=false,origin_verified=false,
    dispatch_authorized=false}
  end
 end
 if #observed==0 then return stop('NO_CORRELATED_CONFIRMED_HITS',orphans) end
 return {status='CONFIRMED_HIT_HISTORY_ONLY',reason='ACTIVE_ATTACK_AND_EPS_ORIGIN_UNPROVEN',
  observed_hits=observed,observed_count=#observed,
  skipped_orphan_signals=orphans,
  origin_verified=false,queue_empty_verified=false,
  active_now_verified=false,freshness_verified=false,
  orders_sent=0,locals_written=0,hooks_registered=0,
  engine_dispatch=false,safe_to_dispatch=false,installed=false}
end

-- A canonical 080 multi-threat input cannot be assembled from an old hit log:
-- it additionally requires a contemporaneous active-attack proof plus a
-- separately verified EPS queue/manual-origin snapshot. Do not forge them.
function M.readiness(snapshot)
 local o=M.observe(snapshot)
 return {status='HOLD_NO_ENGINE_DISPATCH',reason=o.reason,
  observed_hits=o.observed_hits,observed_count=o.observed_count,
  missing={'ACTIVE_ATTACK_NOW','EVENT_TIMESTAMP','EPS_QUEUE_STABILITY','MANUAL_COMMAND_ORIGIN'},
  orders_sent=0,locals_written=0,engine_dispatch=false,safe_to_dispatch=false}
end
return M
