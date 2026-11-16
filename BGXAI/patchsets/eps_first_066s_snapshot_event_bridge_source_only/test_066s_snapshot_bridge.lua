local adapter=dofile('BGXAI066S_080_CONFIRMED_HIT_BRIDGE_SOURCE_ONLY.lua')
local n=0
local function eq(a,b,msg) n=n+1;if a~=b then error((msg or 'assert')..' '..tostring(a)..' != '..tostring(b),2) end end
local function hit(seq,att,vic)
 return {schema=1,event='NONPARTY_WEAPON_HIT_ON_PARTY',actor_id=att,target_id=vic,
 target_source='weapon_hit_context',hostility='CONFIRMED_BY_WEAPON_HIT_CONTEXT',
 action_origin='UNKNOWN',party_ids={501,502,201,202},sequence=seq}
end
local function signal(seq,att,vic)
 return {schema=1,event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT',
 source_event_sequence=seq,attacker_id=att,protected_id=vic,
 confirmation='ENGINE_WEAPON_HIT_CONTEXT',candidate_party_ids={201,202},
 candidate_order='PORTRAIT_ONLY_NOT_PRIORITY',guard_switch_state='UNKNOWN',
 line_of_sight='UNKNOWN',ability_to_intercept='UNKNOWN',
 action_command_sent=false,dispatch_status='ADVISORY_ONLY_BCS_BRIDGE_SEPARATE'}
end
local function snapshot()
 return {schema=1,installed=true,enabled=true,weapon_hit_registered=true,
 origin_verifiable=false,queue_verifiable=false,guard_dispatch_enabled=false,
 events={hit(3,701,501),hit(5,702,502)},
 guard_signals={signal(3,701,501),signal(5,702,502)}}
end
local function safe(r)
 eq(r.orders_sent,0);eq(r.locals_written,0);eq(r.hooks_registered or 0,0)
 eq(r.engine_dispatch,false);eq(r.safe_to_dispatch,false)
 eq(r.queue_empty_verified or false,false);eq(r.origin_verified or false,false)
end
local s=snapshot();local a=adapter.observe(s)
eq(a.status,'CONFIRMED_HIT_HISTORY_ONLY');eq(a.observed_count,2)
eq(a.observed_hits[1].attacker_id,702);eq(a.observed_hits[2].attacker_id,701)
eq(a.observed_hits[1].active_now_verified,false);safe(a)
eq(s.guard_signals[1].attacker_id,701) -- no input mutation
local r=adapter.readiness(s);eq(r.status,'HOLD_NO_ENGINE_DISPATCH');safe(r)
-- Never mistake a started-action event (whose source has no confirmed hit) for a hit.
s=snapshot();s.events[2]={event='NONPARTY_ATTACK_STARTED_ON_PARTY',sequence=5};a=adapter.observe(s)
eq(a.observed_count,1);eq(a.skipped_orphan_signals,1);safe(a)
-- Older ring buffer entries are *history*, not evidence of attack in progress.
s=snapshot();s.guard_signals[1]={source_event_sequence=123,attacker_id=701};a=adapter.observe(s)
eq(a.observed_count,1);eq(a.skipped_orphan_signals,1);safe(a)
-- Same attacker switched target: use latest confirmed hit only.
s=snapshot();s.events[2]=hit(5,701,502);s.guard_signals[2]=signal(5,701,502)
a=adapter.observe(s);eq(a.observed_count,1);eq(a.observed_hits[1].victim_id,502);safe(a)
-- Reject a corrupted or forged exact match; never fall back to nearest enemy.
for _,change in ipairs({
 function(x) x.events[1].actor_id=999 end,
 function(x) x.events[1].sequence=5 end,
 function(x) x.events[1].hostility='UNKNOWN' end,
 function(x) x.events[1].party_ids={501,201,701} end,
 function(x) x.events[1].party_ids={501,501} end,
 function(x) x.events[1].target_source='GUESS' end,
 function(x) x.guard_signals[1].confirmation='UNKNOWN' end,
 function(x) x.guard_signals[1].candidate_party_ids={702} end,
 function(x) x.guard_signals[1].candidate_party_ids={201,201} end,
 function(x) x.guard_signals[1].action_command_sent=true end,
 function(x) x.guard_signals[1].line_of_sight='VERIFIED' end,
 function(x) table.insert(x.guard_signals,x.guard_signals[1]) end,
}) do
 s=snapshot();change(s);a=adapter.observe(s)
 eq(a.status,'HOLD_NO_ENGINE_DISPATCH');safe(a)
end
-- Missing APIs or optimistic flags are not allowed to strengthen the contract.
for _,key in ipairs({'installed','enabled','weapon_hit_registered','origin_verifiable','queue_verifiable','guard_dispatch_enabled'}) do
 s=snapshot();s[key]=nil;a=adapter.observe(s)
 eq(a.status,'HOLD_NO_ENGINE_DISPATCH');safe(a)
end
for _,shape in ipairs({
 function(x)x.events=nil end,
 function(x)x.guard_signals=nil end,
 function(x)x.events[3]=x.events[1] end,
 function(x)x.guard_signals[3]=x.guard_signals[1] end,
 function(x)x.events={[1]=x.events[1],[3]=x.events[2]} end,
 function(x)x.events[1]='invalid' end,
 function(x)x.guard_signals[2]='invalid' end,
}) do
 s=snapshot();shape(s);a=adapter.observe(s)
 eq(a.status,'HOLD_NO_ENGINE_DISPATCH');safe(a)
end
-- No hit in the engine buffer -> no evidence; no candidate means no cast.
s=snapshot();s.events={};s.guard_signals={};a=adapter.observe(s)
eq(a.reason,'NO_CORRELATED_CONFIRMED_HITS');safe(a)
-- No invented verified multi-threat event allowed into existing 080 gate.
s=snapshot();a=adapter.observe(s)
local coordinator=dofile('BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua')
local q=coordinator.reviewMultipleThreats(a.observed_hits,{}, {opt_in=true,smart_guard=true},
 {guard=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')})
eq(q.status,'HOLD_NO_ENGINE_DISPATCH');eq(q.orders_sent,0);eq(q.locals_written,0)
-- Existing 082 remains fail closed even if the caller tries to elevate a hit.
local bridge082=dofile('BGXAI082_QUEUE_GUARD_BRIDGE.lua')
local bad=bridge082.review({}, {}, {},{}, {}, {}, {})
eq(bad.status,'HOLD_NO_ENGINE_DISPATCH');eq(bad.engine_dispatch,false)
print('BGXAI_066S_HIT_BRIDGE_ASSERTIONS_PASS '..n)
