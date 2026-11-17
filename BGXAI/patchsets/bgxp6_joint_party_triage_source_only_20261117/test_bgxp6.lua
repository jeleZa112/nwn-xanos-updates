local joint=dofile("BGXP6_JOINT_TRIAGE.lua")
local coord=dofile("BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua")
local guard=dofile("BGXAI072_EPS_FIRST_ARBITER.lua")
local n=0
local function eq(a,b,msg)
 if a~=b then error((msg or "mismatch").." expected "..tostring(b).." got "..tostring(a),2) end
 n=n+1
end
local function safe(r)
 eq(r.engine_dispatch,false)
 eq(r.orders_sent,0)
 eq(r.locals_written,0)
 eq(r.eps_actions_interrupted,0)
end
local function member(id,slot,role,hp)
 local g=role=="GUARD"
 local h=role=="AUTO" or role=="HEALER"
 return {
  id=id,slot=slot,alive=true,can_act=true,in_party=true,
  hp={verified=true,percent=hp},
  heal={verified=true,role=h and role or "OTHER",
   guard_on=h,prepared=h,cooldown_ready=true,targets={}},
  action_state={verified=true,origin_verified=true,manual_command=false,
    queue_empty=true,idle=true,current_action="IDLE"},
  eps={verified=true,manual_command=false,casting=false,singing=false,
    detecting_traps=false,heal_pending=false,ally_in_critical_danger=false,
    queue_empty=true,idle=true},
  guard_role={status="ADVISORY_ONLY",possible_interceptor=g,
    guard_toggle=g and 1 or 0,orders_sent=0},
  guard_distances={}
 }
end
local TICK=7522
local function healSight(healer,target,dist,opts)
 opts=opts or {}
 healer.heal.targets[target.id]={
  verified=opts.verified~=false,snapshot_tick=opts.tick or TICK,
  same_area=opts.area~=false,visible=opts.visible~=false,
  range_verified=true,range_18=(dist<=18),distance_sq=dist*dist}
end
local function guardSight(guardian,patient,dist)
 guardian.guard_distances[patient.id]={
  verified=true,snapshot_tick=TICK,guardian_id=guardian.id,
  victim_id=patient.id,same_area=true,distance_sq=dist*dist}
end
local function attacked(attacker,patient,rear)
 return {
  verified=true,snapshot_tick=TICK,victim_id=patient.id,attacker_id=attacker,
  freshness_verified=true,active_now=true,
  victim_state={verified=true,victim_id=patient.id,hp_percent=patient.hp.percent,
   rear_support_verified=true,rear_support=rear},
  threat={verified=true,source="EEEX_EXPLICIT_ATTACK_ACTION",hostile=true,
   victim_is_party=true,attacker_is_party=false,same_area=true,
   attack_in_progress=true,attacker_id=attacker,victim_id=patient.id},
  proposed_target={verified=true,target_source="EXACT_RESOLVED_ATTACKER_ID",target_id=attacker}
 }
end
local function setup()
 local p1=member(101,1,"OTHER",40)
 local p2=member(102,2,"OTHER",55)
 local h1=member(301,3,"AUTO",100)
 local h2=member(302,4,"HEALER",100)
 local g1=member(401,5,"GUARD",100)
 local g2=member(402,6,"GUARD",100)
 healSight(h1,p1,2);healSight(h1,p2,5)
 healSight(h2,p1,1)
 guardSight(g1,p1,2);guardSight(g1,p2,12)
 guardSight(g2,p1,12);guardSight(g2,p2,2)
 return {p1,p2,h1,h2,g1,g2},{attacked(701,p1,true),attacked(702,p2,false)}
end
local cfg={opt_in=true,auto_heal=true,smart_guard=true,joint_coordination=true}
local deps={coordinator=coord,guard=guard}
local function run(m,e)
 return joint.plan({verified=true,tick=TICK},e or {},m,cfg,deps)
end
local m,e=setup()
local r=run(m,e)
eq(r.status,"ADVISORY_JOINT_ONLY");eq(r.heal_coverage,2);eq(r.guard_coverage,2);safe(r)
-- Scarce second healer reaches only first patient. Avoid greedy healer1->first.
eq(r.heal_assignments[1].healer_id,302);eq(r.heal_assignments[1].patient_id,101)
eq(r.heal_assignments[2].healer_id,301);eq(r.heal_assignments[2].patient_id,102)
eq(r.guard_assignments[1].guardian_id,401);eq(r.guard_assignments[2].guardian_id,402)
eq(#r.reserved_healers,2)
-- Joint decisions must never rewrite source snapshots.
eq(m[3].action_state.verified,true);eq(m[3].eps.verified,true)
eq(e[1].threat.attacker_id,701)
-- No threat: preserve useful healing plan, never invent guard event.
m,e=setup();r=run(m,{})
eq(r.heal_coverage,2);eq(r.guard_coverage,0);eq(r.status,"ADVISORY_JOINT_ONLY");safe(r)
-- One healer and 2 patients: prioritize more severely injured first.
m,e=setup();m[4].heal.prepared=false
r=run(m,{})
eq(r.heal_coverage,1);eq(r.heal_assignments[1].patient_id,101)
-- At less than 35 percent, emergency tier is first regardless of portrait slot.
m,e=setup();m[1].hp.percent=50;m[2].hp.percent=20;m[4].heal.prepared=false
r=run(m,{})
eq(r.heal_assignments[1].patient_id,102);eq(r.heal_assignments[1].priority,"EMERGENCY")
-- The health thresholds mirror the stable, installed BGXP5 behavior.
m,e=setup();m[1].hp.percent=70;m[2].hp.percent=69
r=run(m,{})
eq(r.heal_coverage,1);eq(r.heal_assignments[1].patient_id,102)
-- Patient must be another living party member and have verified same-area sight/range.
for _,mode in ipairs({"invisible","outside_18","other_area","stale","unknown"}) do
 m,e=setup()
 for _,h in ipairs({m[3],m[4]}) do
  local obs=h.heal.targets[101]
  if obs then
   if mode=="invisible" then obs.visible=false
   elseif mode=="outside_18" then obs.range_18=false
   elseif mode=="other_area" then obs.same_area=false
   elseif mode=="stale" then obs.snapshot_tick=TICK-1
   else obs.verified=nil end
  end
 end
 r=run(m,{})
 eq(r.heal_coverage,1)
 eq(r.heal_assignments[1].patient_id,102)
 safe(r)
end
-- With unknown prepared state, potential cleric is held out of guard duty.
m,e=setup();m[3].heal.prepared=nil;m[3].guard_role.possible_interceptor=true
r=run(m,e)
eq(r.heal_coverage,1);eq(r.guard_coverage,2)
eq(r.reserved_healers[1].actor_id,301)
-- When a healer is in a manual command, do not assign it to attack or cast.
m,e=setup();m[3].action_state.manual_command=true;m[3].action_state.current_action="ATTACK"
m[3].action_state.queue_empty=false;m[3].action_state.idle=false
r=run(m,e)
eq(r.heal_coverage,1);eq(r.guard_coverage,2);safe(r)
-- F OFF means no special heal or guard in this BGXAI module.
m,e=setup();m[3].heal.guard_on=false;m[4].heal.guard_on=false
r=run(m,{})
eq(r.heal_coverage,0);eq(r.guard_coverage,0);safe(r)
-- Disable all opt-in without changing old coordinator or its two assignments.
m,e=setup()
for _,flag in ipairs({"opt_in","smart_guard","auto_heal","joint_coordination"}) do
 local c={}
 for k,v in pairs(cfg) do c[k]=v end
 c[flag]=false
 local x=joint.plan({verified=true,tick=TICK},e,m,c,deps)
 eq(x.reason,"OPT_IN_OFF");safe(x)
end
-- Unknown/malformed party, conflicting health and duplicate IDs fail closed.
m,e=setup();m[2].id=m[1].id;eq(run(m,e).reason,"ACTOR_OR_HEAL_EVIDENCE_INVALID")
m,e=setup();m[1].hp.verified=nil;eq(run(m,e).reason,"ACTOR_OR_HEAL_EVIDENCE_INVALID")
m,e=setup();m[1].hp.percent=-1;eq(run(m,e).reason,"ACTOR_OR_HEAL_EVIDENCE_INVALID")
m,e=setup();m[1].hp.percent=0;eq(run(m,e).reason,"ACTOR_OR_HEAL_EVIDENCE_INVALID")
m,e=setup();m[2].heal.verified=nil;eq(run(m,e).reason,"ACTOR_OR_HEAL_EVIDENCE_INVALID")
m,e=setup();e[2].snapshot_tick=TICK+1;eq(run(m,e).reason,"CROSS_MODULE_SNAPSHOT_MISMATCH")
m,e=setup();eq(joint.plan({verified=false,tick=TICK},e,m,cfg,deps).reason,"SNAPSHOT_UNVERIFIED")
-- Malicious coordinator cannot grant a guard order to reserved healer.
m,e=setup()
local fake={coordinator={reviewMultipleThreats=function()
 return {status="ADVISORY_MULTI_THREAT_ONLY",engine_dispatch=false,
   orders_sent=0,locals_written=0,eps_actions_interrupted=0,
   assignments={{guardian_id=301,guardian_slot=3,victim_id=101,attacker_id=701}}}
 end},guard=guard}
local x=joint.plan({verified=true,tick=TICK},e,m,cfg,fake)
eq(x.reason,"HEAL_GUARD_COLLISION_REJECTED");safe(x)
-- Forged party attacker, duplicate guardians or fake engine writes fail closed.
m,e=setup()
local fake2={coordinator={reviewMultipleThreats=function()
 return {status="ADVISORY_MULTI_THREAT_ONLY",engine_dispatch=false,
   orders_sent=0,locals_written=0,eps_actions_interrupted=0,
   assignments={{guardian_id=401,guardian_slot=5,victim_id=101,attacker_id=999}}}
 end},guard=guard}
x=joint.plan({verified=true,tick=TICK},e,m,cfg,fake2)
eq(x.reason,"UNTRUSTED_GUARD_ASSIGNMENT");safe(x)
fake2.coordinator.reviewMultipleThreats=function()
 return {status="ADVISORY_MULTI_THREAT_ONLY",engine_dispatch=true,
    orders_sent=1,locals_written=0,eps_actions_interrupted=0,assignments={}}
end
x=joint.plan({verified=true,tick=TICK},e,m,cfg,fake2)
eq(x.reason,"UNVERIFIED_GUARD_COORDINATOR_RESULT");safe(x)
-- Adversarial provider mutation cannot change the original party/evidence.
m,e=setup()
local evil={coordinator={reviewMultipleThreats=function(events,party)
 events[1].threat.attacker_id=999
 party[1].hp.percent=99
 party[3].guard_role.guard_toggle=0
 return {status="HOLD_NO_ENGINE_DISPATCH",reason="SAFE_HOLD",
  engine_dispatch=false,orders_sent=0,locals_written=0,eps_actions_interrupted=0}
end},guard=guard}
x=joint.plan({verified=true,tick=TICK},e,m,cfg,evil)
eq(m[1].hp.percent,40);eq(m[3].guard_role.guard_toggle,0)
eq(e[1].threat.attacker_id,701);safe(x)
-- Absent real action provenance: guaranteed no guard and no auto-heal.
m,e=setup()
for _,actor in ipairs(m) do
 actor.action_state.origin_verified=false
 actor.action_state.queue_empty=nil
end
r=run(m,e)
eq(r.heal_coverage,0);eq(r.guard_coverage,0);safe(r)
print("BGXP6_NATIVE_LUA_TESTS_PASS "..n)
