local coord=dofile('BGXAI080_EPS_FIRST_COORDINATOR.lua')
local heal=dofile('BGXAI078_HEAL_SELECTOR.lua')
local guard=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')
local deps={heal=heal,guard=guard}
local cfg={opt_in=true,auto_heal=true,smart_guard=true}
local count=0
local function eq(a,b,msg)
 if a~=b then error((msg or 'assert')..': expected '..tostring(b)..' got '..tostring(a),2) end
 count=count+1
end
local function event()
 return {verified=true,victim_id=500,attacker_id=700,
  heal_event={type='CONFIRMED_HOSTILE_WEAPON_HIT',verified=true,party_victim=true,
    attacker_is_party=false,attacker_id=700,victim_id=500,hp_verified=true,
    hp_percent=35,existing_eps_heal_handling=false},
  threat={verified=true,source='EEEX_EXPLICIT_ATTACK_ACTION',hostile=true,
    victim_is_party=true,attacker_is_party=false,same_area=true,
    attack_in_progress=true,attacker_id=700,victim_id=500},
  proposed_target={verified=true,target_source='EXACT_RESOLVED_ATTACKER_ID',target_id=700}}
end
local function member(id,slot,kind,d)
 local base={id=id,slot=slot,in_party=true,guard_f_on=true,alive=true,
  same_area=true,can_act=true,request_pending=false,distance_verified=true,
  distance_sq=d,
  role={verified=true,heal_capable=(kind=='heal')},
  guard_role={status='ADVISORY_ONLY',possible_interceptor=(kind=='guard'),
    orders_sent=0,guard_toggle=1},
  spell={verified=true,bcs_spell_id='CLERIC_CURE_LIGHT_WOUNDS',usable_now=(kind=='heal')},
  target={verified=true,victim_id=500,visible=true,in_bcs_range_10=true},
  eps={verified=true,manual_command=false,casting=false,singing=false,
   detecting_traps=false,heal_pending=false,ally_in_critical_danger=false,
   queue_empty=true,idle=true},
  action_state={verified=true,origin_verified=true,manual_command=false,
   current_action='IDLE',queue_empty=true,idle=true}}
 return base
end
local function run(m,e,c,d) return coord.review(e or event(),m,c or cfg,d or deps) end
local healer=member(100,2,'heal',5)
local fighter=member(200,3,'guard',2)
local result=run({healer,fighter})
eq(result.status,'ADVISORY_COORDINATION_ONLY')
eq(result.heal_id,100)
eq(result.guard_id,200)
eq(result.guard_target_id,700)
eq(result.orders_sent,0)
eq(result.locals_written,0)
eq(result.eps_actions_interrupted,0)
eq(result.engine_dispatch,false)
-- Any unfamiliar active action ID must be preserved, without an ID allowlist.
for _,act in ipairs({7,123,808080,'UNKNOWN_BUFF_OR_ITEM','SPELL','MANUAL_PATH'}) do
 local h=member(100,2,'heal',5); h.action_state.current_action=act
 local f=member(200,3,'guard',2);f.action_state.current_action=act
 local r=run({h,f})
 eq(r.status,'HOLD_NO_ENGINE_DISPATCH','all non-idle actions denied')
 eq(r.details.actor_holds[100],'ACTION_IN_PROGRESS_OR_QUEUE_BUSY','unknown heal action protected')
 eq(r.details.actor_holds[200],'ACTION_IN_PROGRESS_OR_QUEUE_BUSY','unknown guard action protected')
end
for _,property in ipairs({'verified','origin_verified','queue_empty','idle','manual_command','current_action'}) do
 local h=member(100,2,'heal',5)
 if property=='current_action' then h.action_state.current_action=nil
 elseif property=='manual_command' then h.action_state.manual_command=true
 else h.action_state[property]=nil end
 local r=run({h,fighter})
 eq(r.heal_id,nil,'unknown action gate blocks healer '..property)
 eq(r.guard_id,200,'unaffected guardian may remain eligible')
end
-- Even if action observer claims idle, the EPS queue must be separately empty.
for _,key in ipairs({'queue_empty','idle','verified'}) do
 local h=member(100,2,'heal',5);h.eps[key]=nil
 local r=run({h,fighter});eq(r.heal_id,nil,'EPS '..key)
end
for _,key in ipairs({'casting','singing','detecting_traps','heal_pending','manual_command'}) do
 local h=member(100,2,'heal',5);h.eps[key]=true
 eq(run({h,fighter}).heal_id,nil,'EPS current priority '..key)
 local f=member(200,3,'guard',2);f.eps[key]=true
 eq(run({healer,f}).guard_id,nil,'Guard preserves '..key)
end
-- Never replace an emergency EPS cure, whether confirmed pending or unknown.
local e=event();e.heal_event.existing_eps_heal_handling=true
local r=run({healer,fighter},e);eq(r.heal_id,nil)
e=event();e.heal_event.existing_eps_heal_handling=nil
r=run({healer,fighter},e);eq(r.heal_id,nil)
-- At truly critical HP, life-saving healing takes priority over a new guard.
e=event();e.heal_event.hp_percent=20
r=run({healer,fighter},e);eq(r.heal_id,100);eq(r.guard_id,nil)
-- Without actually castable spell, 079 memory observer does not authorize heal.
local h=member(100,2,'heal',5);h.spell.usable_now=nil
r=run({h,fighter});eq(r.heal_id,nil);eq(r.guard_id,200)
-- Without exact attacker, neither defense nor healing should be guessed.
e=event();e.threat.attacker_id=701
r=run({healer,fighter},e);eq(r.reason,'CROSS_MODULE_IDENTITY_MISMATCH')
e=event();e.proposed_target.target_id=701
r=run({healer,fighter},e);eq(r.guard_id,nil);eq(r.heal_id,100)
-- Unknown safety facts fail closed.
for _,item in ipairs({nil,{},true,'x',0}) do
 local r=run({healer,fighter},item or {verified=false})
 eq(r.reason,'HIT_CONTEXT_UNVERIFIED')
end
for _,field in ipairs({'opt_in','auto_heal','smart_guard'}) do
 local c={opt_in=true,auto_heal=true,smart_guard=true};c[field]=false
 eq(run({healer,fighter},nil,c).reason,'OPT_IN_OFF')
end
eq(run({healer,healer,fighter}).reason,'PARTY_DUPLICATE_OR_INVALID')
local h=member(101,2,'heal',8)
eq(run({healer,h}).reason,'PARTY_DUPLICATE_OR_INVALID')
eq(run({}).reason,'NO_PARTY_CANDIDATES')
eq(run({healer,fighter},event(),cfg,{}).reason,'VERIFIED_SELECTORS_NOT_SUPPLIED')
-- No side effects on snapshots, even across multiple reviews.
local original={healer.action_state.current_action,healer.eps.casting,healer.spell.usable_now}
run({healer,fighter});eq(healer.action_state.current_action,original[1]);eq(healer.eps.casting,original[2]);eq(healer.spell.usable_now,original[3])
-- Guard and cure never use same actor in a single advisory.
local both=member(111,2,'heal',1);both.guard_role.possible_interceptor=true
r=run({both,fighter});eq(r.heal_id,111);eq(r.guard_id,200)
-- If only actor is both guard and healer, guard stays deferred.
r=run({both});eq(r.heal_id,111);eq(r.guard_id,nil)
-- Broken/malicious injected providers cannot authorize an engine order or crash.
local broken={heal={select=function()error('simulated provider crash')end},guard=guard}
eq(run({healer,fighter},event(),cfg,broken).reason,'HEAL_MODULE_FAILED')
local wrong={heal={select=function()return {status='ADVISORY_HEAL_CANDIDATE_ONLY',selected_id=100,
 orders_sent=1,locals_written=0,engine_dispatch=false} end},guard=guard}
eq(run({healer,fighter},event(),cfg,wrong).reason,'HEAL_MODULE_FAILED')
local unknownid={heal={select=function()return {status='ADVISORY_HEAL_CANDIDATE_ONLY',selected_id=999,
 orders_sent=0,locals_written=0,engine_dispatch=false} end},guard=guard}
eq(run({healer,fighter},event(),cfg,unknownid).reason,'HEAL_ID_UNVERIFIED')
local guarded={heal=heal,guard={review=function()error('simulated guard crash')end}}
eq(run({healer,fighter},event(),cfg,guarded).heal_id,100)
eq(run({healer,fighter},event(),cfg,guarded).guard_id,nil)
local malicious_guard={heal=heal,guard={review=function()return {state='CANDIDATE_REVIEW_ONLY',
 confirmed_target_id=700,allow_engine_action=false,engine_orders_sent=1,script_changes=0} end}}
eq(run({healer,fighter},event(),cfg,malicious_guard).guard_id,nil)
local hole={[1]=healer,[3]=fighter}
eq(run(hole).reason,'PARTY_DUPLICATE_OR_INVALID')
local weird={[1]=healer,x=fighter}
eq(run(weird).reason,'PARTY_DUPLICATE_OR_INVALID')
print('BGXAI080_EPS_FIRST_COORDINATOR_TESTS_PASS '..count)
