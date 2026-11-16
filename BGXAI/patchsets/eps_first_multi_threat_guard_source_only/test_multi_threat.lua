local coord=dofile('BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua')
local guard=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')
local count=0
local function eq(a,b,msg) if a~=b then error((msg or 'assert')..' expected '..tostring(b)..' got '..tostring(a),2) end;count=count+1 end
local cfg={opt_in=true,smart_guard=true}
local deps={guard=guard}
local function member(id,slot,kind)
 return {id=id,slot=slot,in_party=true,alive=true,can_act=true,
  action_state={verified=true,origin_verified=true,manual_command=false,current_action='IDLE',queue_empty=true,idle=true},
  eps={verified=true,queue_empty=true,idle=true,manual_command=false,heal_pending=false,ally_in_critical_danger=false,casting=false,singing=false,detecting_traps=false},
  guard_role={status='ADVISORY_ONLY',possible_interceptor=(kind=='guard'),orders_sent=0,guard_toggle=1},
  guard_distances={}}
end
local function victim(id,slot)
 local m=member(id,slot,'rear');m.guard_role.possible_interceptor=false;return m
end
local function event(attacker,victimId,hp,rear,tick)
 tick=tick or 4321
 return {verified=true,victim_id=victimId,attacker_id=attacker,snapshot_tick=tick,freshness_verified=true,active_now=true,
   victim_state={verified=true,victim_id=victimId,hp_percent=hp,rear_support_verified=true,rear_support=rear},
   threat={verified=true,source='EEEX_EXPLICIT_ATTACK_ACTION',hostile=true,victim_is_party=true,attacker_is_party=false,
    same_area=true,attack_in_progress=true,attacker_id=attacker,victim_id=victimId},
   proposed_target={verified=true,target_source='EXACT_RESOLVED_ATTACKER_ID',target_id=attacker}}
end
local function distance(g,v,d,tick)
 g.guard_distances[v]={verified=true,guardian_id=g.id,victim_id=v,snapshot_tick=tick or 4321,
  same_area=true,distance_sq=d}
end
local function setup()
 local mage=victim(501,1);local archer=victim(502,2);local tank1=member(201,3,'guard');local tank2=member(202,4,'guard')
 local e1=event(701,501,40,true);local e2=event(702,502,50,false)
 distance(tank1,501,4);distance(tank1,502,100)
 distance(tank2,501,100);distance(tank2,502,4)
 return {e1,e2},{mage,archer,tank1,tank2},tank1,tank2
end
local function run(events,members,configuration,providers)
 return coord.reviewMultipleThreats(events,members,configuration or cfg,providers or deps)
end
local function safety(r)
 eq(r.orders_sent,0);eq(r.locals_written,0);eq(r.eps_actions_interrupted,0);eq(r.engine_dispatch,false)
end
local es,ms=setup();local r=run(es,ms)
eq(r.status,'ADVISORY_MULTI_THREAT_ONLY');eq(r.threats_seen,2);eq(r.threats_covered,2)
eq(#r.assignments,2);eq(r.assignments[1].guardian_id,201);eq(r.assignments[1].attacker_id,701)
eq(r.assignments[2].guardian_id,202);eq(r.assignments[2].attacker_id,702);safety(r)
-- Reverse input order: rear mage still receives first place; no data mutation.
es,ms=setup();r=run({es[2],es[1]},ms);eq(r.assignments[1].victim_id,501);eq(r.assignments[1].guardian_id,201)
-- Global matching: greedy nearest would steal tank 201 from an uncovered second victim.
es,ms=setup();local a,b=ms[3],ms[4]
distance(a,501,1);distance(a,502,9);distance(b,501,4);b.guard_distances[502]=nil
r=run(es,ms);eq(r.threats_covered,2);eq(r.assignments[1].guardian_id,202);eq(r.assignments[2].guardian_id,201);safety(r)
-- Missing rear-class proof or stale/mismatched exact targets always blocks everything.
local fields={'verified','freshness_verified','active_now'}
for _,f in ipairs(fields) do
 es,ms=setup();es[2][f]=nil;r=run(es,ms);eq(r.reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT');eq(#r.assignments,0);safety(r)
end
es,ms=setup();es[1].victim_state.rear_support_verified=nil;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[1].victim_state.hp_percent=0/0;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[1].proposed_target.target_id=7011;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[1].threat.source='NEAREST_ENEMY_GUESS';eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[2].attacker_id=701;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[1].attacker_id=201;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();es[1].threat.same_area=nil;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();ms[3].guard_distances[501].snapshot_tick=4320;eq(run(es,ms).assignments[1].guardian_id,202)
-- 25% safety: do not hijack EPS urgent healing for a critically injured mage.
es,ms=setup();es[1].victim_state.hp_percent=12;r=run(es,ms);eq(r.threats_covered,1);eq(r.assignments[1].victim_id,502)
-- 25 exactly may admit as in 080 legacy <25 hold.
es,ms=setup();es[1].victim_state.hp_percent=25;r=run(es,ms);eq(r.threats_covered,2)
-- Unknown/active EPS/manual/cast/song/trap/heal always excludes the candidate guardian.
for _,k in ipairs({'manual_command','casting','singing','detecting_traps','heal_pending','ally_in_critical_danger'}) do
 es,ms=setup();ms[3].eps[k]=true;r=run(es,ms);eq(r.threats_covered,1);eq(r.assignments[1].guardian_id,202);safety(r)
end
-- Active guardian must be alive, in party, and able to act: no trusted data => HOLD.
for _,key in ipairs({'in_party','alive','can_act'}) do
 es,ms=setup();ms[3][key]=nil;r=run(es,ms);eq(r.threats_covered,1);eq(r.assignments[1].guardian_id,202)
end
-- If no trusted EPS/manual-origin proof for either guard, do not recommend action.
for _,key in ipairs({'verified','origin_verified','queue_empty','idle','current_action','manual_command'}) do
 es,ms=setup()
 for _,m in ipairs({ms[3],ms[4]}) do m.action_state[key]=nil end
 eq(run(es,ms).reason,'NO_VERIFIED_FREE_INTERCEPTOR')
end
for _,key in ipairs({'verified','queue_empty','idle','manual_command','casting','singing','detecting_traps','heal_pending'}) do
 es,ms=setup()
 for _,m in ipairs({ms[3],ms[4]}) do m.eps[key]=nil end
 eq(run(es,ms).reason,'NO_VERIFIED_FREE_INTERCEPTOR')
end
-- F OFF, not-frontline, unknown distance, and actor-not-in-area are no-op.
for _,mode in ipairs({'F_OFF','NON_FIGHTER','MISSING_DISTANCE','OTHER_AREA'}) do
 es,ms=setup()
 for _,m in ipairs({ms[3],ms[4]}) do
  if mode=='F_OFF' then m.guard_role.guard_toggle=0
  elseif mode=='NON_FIGHTER' then m.guard_role.possible_interceptor=false
  elseif mode=='MISSING_DISTANCE' then m.guard_distances={}
  else for _,v in pairs(m.guard_distances) do v.same_area=false end end
 end
 eq(run(es,ms).reason,'NO_VERIFIED_FREE_INTERCEPTOR')
end
-- Avoid false positive for an unconscious/dead patient and inconsistent multi-hit snapshots.
es,ms=setup();es[1].victim_state.hp_percent=0;eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
es,ms=setup();local sameVictim=event(703,501,41,true)
 eq(run({es[1],sameVictim},ms).reason,'CONFLICTING_VICTIM_EVIDENCE')
es,ms=setup();sameVictim=event(703,501,40,false)
 eq(run({es[1],sameVictim},ms).reason,'CONFLICTING_VICTIM_EVIDENCE')
es,ms=setup();sameVictim=event(703,501,40,true,4320)
 eq(run({es[1],sameVictim},ms).reason,'CONFLICTING_VICTIM_EVIDENCE')
-- Two attackers targeting same mage can select two different guards when evidence agrees.
es,ms=setup();sameVictim=event(703,501,40,true)
 r=run({es[1],sameVictim},ms);eq(r.threats_covered,2)
 eq(r.assignments[1].attacker_id,701);eq(r.assignments[2].attacker_id,703)
-- Safety: malicious provider may not change input snapshots; output is never a dispatch.
es,ms=setup();local before=ms[3].eps.manual_command
 local evil={guard={review=function(role,threat,eps,target,config)
  eps.manual_command=true;threat.attacker_id=999;role.guard_toggle=0;target.target_id=999
  return {state='CANDIDATE_REVIEW_ONLY',confirmed_target_id=999,allow_engine_action=false,
   engine_orders_sent=0,script_changes=0}
 end}}
 r=run(es,ms,cfg,evil);eq(r.reason,'NO_VERIFIED_FREE_INTERCEPTOR');eq(ms[3].eps.manual_command,before)
 eq(es[1].threat.attacker_id,701);eq(es[1].proposed_target.target_id,701);safety(r)
-- Even a fake 'pass' that sends a game order must be rejected.
es,ms=setup();local wrong={guard={review=function()return {state='CANDIDATE_REVIEW_ONLY',
 confirmed_target_id=701,allow_engine_action=false,engine_orders_sent=1,script_changes=0} end}}
 eq(run(es,ms,cfg,wrong).reason,'NO_VERIFIED_FREE_INTERCEPTOR')
-- Unknown attacker guess and missing freshness are NEVER upgraded to an exact target.
for _,mode in ipairs({'missing_target','not_active','guess','different_tick','same_party_attacker'}) do
 es,ms=setup()
 if mode=='missing_target' then es[1].proposed_target=nil
 elseif mode=='not_active' then es[1].threat.attack_in_progress=false
 elseif mode=='guess' then es[1].proposed_target.target_source='NEAREST_ENEMY_GUESS'
 elseif mode=='different_tick' then es[1].snapshot_tick=nil
 else es[1].attacker_id=ms[3].id end
 eq(run(es,ms).reason,'UNVERIFIED_OR_AMBIGUOUS_THREAT')
end
-- Even an optimistic synthetic all-idle six-member party yields advisory only.
-- Maximize coverage before distance when some defenders have unique reachable patients.
es,ms=setup();local aux,z=member(203,5,'guard'),member(204,6,'guard')
 distance(aux,501,25);distance(aux,502,25);distance(z,501,35);distance(z,502,35)
 ms[#ms+1]=aux;ms[#ms+1]=z
 r=run(es,ms);eq(r.threats_covered,2);safety(r)
-- Disable the feature without affecting old 080 review() in any way.
es,ms=setup();eq(run(es,ms,{opt_in=false,smart_guard=true}).reason,'OPT_IN_OFF')
-- Sparse malformed arrays and duplicate portrait IDs are rejected.
es,ms=setup();eq(run({[1]=es[1],[3]=es[2]},ms).reason,'SPARSE_OR_MALFORMED_ARRAY')
es,ms=setup();ms[4].id=ms[3].id;eq(run(es,ms).reason,'DUPLICATE_OR_INVALID_PARTY')
-- Source-only EEex 083 observes an action but cannot prove empty queue/manual provenance.
local passive=dofile('BGXAI083_PASSIVE_TRACE.lua')
local obs=assert(passive.new(5))
local observed=assert(obs:observe(201,{m_curAction={m_actionID=0},m_curScriptNum=0},nil,'TEST'))
eq(observed.origin_verified,false);eq(observed.eps_queue_empty,nil)
es,ms=setup()
for _,m in ipairs({ms[3],ms[4]}) do
 m.action_state.verified=true;m.action_state.origin_verified=observed.origin_verified
 m.action_state.queue_empty=observed.eps_queue_empty
end
eq(run(es,ms).reason,'NO_VERIFIED_FREE_INTERCEPTOR')
-- Old single-threat review() is still present, same old opt-in gates.
eq(coord.review(nil,nil,nil,nil).reason,'OPT_IN_OFF')
print('BGXAI_MULTI_THREAT_TESTS_PASS '..count)
