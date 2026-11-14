local bridge=dofile('BGXAI082_QUEUE_GUARD_BRIDGE.lua')
local observed=dofile('BGXAI081_ACTION_PROVENANCE_READONLY.lua')
local coord=dofile('BGXAI080_EPS_FIRST_COORDINATOR.lua')
local heal=dofile('BGXAI078_HEAL_SELECTOR.lua')
local guard=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')
local c=0
local function eq(a,b)
  c=c+1
  if a~=b then error('BGX082 '..tostring(a)..' not equal '..tostring(b),2) end
end
local config={opt_in=true,auto_heal=true,smart_guard=true}
local event={verified=true,victim_id=500,attacker_id=700,
  heal_event={type='CONFIRMED_HOSTILE_WEAPON_HIT',verified=true,party_victim=true,
    attacker_is_party=false,attacker_id=700,victim_id=500,hp_verified=true,
    hp_percent=35,existing_eps_heal_handling=false},
  threat={verified=true,source='EEEX_EXPLICIT_ATTACK_ACTION',hostile=true,
    victim_is_party=true,attacker_is_party=false,same_area=true,
    attack_in_progress=true,attacker_id=700,victim_id=500},
  proposed_target={verified=true,target_source='EXACT_RESOLVED_ATTACKER_ID',target_id=700}}
local function actor(id,slot,kind)
  return {id=id,slot=slot,in_party=true,guard_f_on=true,alive=true,
    same_area=true,can_act=true,request_pending=false,distance_verified=true,distance_sq=slot,
    role={verified=true,heal_capable=(kind=='heal')},
    guard_role={status='ADVISORY_ONLY',possible_interceptor=(kind=='guard'),orders_sent=0,guard_toggle=1},
    spell={verified=true,bcs_spell_id='CLERIC_CURE_LIGHT_WOUNDS',usable_now=(kind=='heal')},
    target={verified=true,victim_id=500,visible=true,in_bcs_range_10=true},
    eps={verified=true,manual_command=false,casting=false,singing=false,
      detecting_traps=false,heal_pending=false,ally_in_critical_danger=false,
      queue_empty=true,idle=true},
    action_state={verified=true,origin_verified=true,manual_command=false,
      current_action='IDLE',queue_empty=true,idle=true}}
end
local function sprites(a,b) return {[100]={m_curAction={m_actionID=a}},[200]={m_curAction={m_actionID=b}}} end
local deps={heal=heal,guard=guard}
local h,f=actor(100,2,'heal'),actor(200,3,'guard')
local original=coord.review(event,{h,f},config,deps)
eq(original.status,'ADVISORY_COORDINATION_ONLY')
eq(original.heal_id,100);eq(original.guard_id,200)
for _,a in ipairs({0,3,23,94,105,134,65535}) do
 for _,b in ipairs({0,3,23,94,105,134,65535}) do
  local party={h,f}
  local view,err=bridge.observed_members(party,sprites(a,b),observed)
  eq(err,nil)
  eq(view[1].action_state.verified,false)
  eq(view[2].action_state.origin_verified,false)
  eq(view[1].action_state.queue_empty,nil)
  eq(view[2].action_state.manual_command,nil)
  eq(view[1].action_state.idle,false)
  eq(h.action_state.verified,true) -- original not changed
  eq(f.action_state.queue_empty,true)
  local r=bridge.review(event,party,sprites(a,b),observed,coord,deps,config)
  eq(r.status,'HOLD_NO_ENGINE_DISPATCH')
  eq(r.heal_id,nil);eq(r.guard_id,nil)
  eq(r.engine_dispatch,false);eq(r.orders_sent,0);eq(r.locals_written,0)
  eq(r.eps_actions_interrupted,0)
 end
end
-- Unknown / missing sprites, so current ID is not known either.
for _,sp in ipairs({{}, {[100]={}}, {[200]={}}}) do
 local r=bridge.review(event,{h,f},sp,observed,coord,deps,config)
 eq(r.status,'HOLD_NO_ENGINE_DISPATCH');eq(r.engine_dispatch,false)
end
local function invalid(party,src)
 local x=bridge.review(event,party,src or sprites(0,0),observed,coord,deps,config)
 eq(x.status,'HOLD_NO_ENGINE_DISPATCH');eq(x.engine_dispatch,false);eq(x.orders_sent,0)
end
invalid({});invalid({h,h});invalid({h,f,[8]=h});invalid({h,f},{});invalid({h,f},sprites(0,0))
local evil={observe=function()return {orders_sent=1,locals_written=0,hooks_registered=0}end}
invalid({h,f},sprites(0,0));local r=bridge.review(event,{h,f},sprites(0,0),evil,coord,deps,config)
eq(r.reason,'OBSERVATION_NOT_PASSIVE')
local badcoord={review=function()return {status='ADVISORY_COORDINATION_ONLY',orders_sent=1,locals_written=0,engine_dispatch=true}end}
r=bridge.review(event,{h,f},sprites(0,0),observed,badcoord,deps,config)
eq(r.reason,'COORDINATOR_INVARIANT_FAILED')
eq(bridge.installed,false)
print('BGXAI082 Lua: '..c..' assertions PASS')
