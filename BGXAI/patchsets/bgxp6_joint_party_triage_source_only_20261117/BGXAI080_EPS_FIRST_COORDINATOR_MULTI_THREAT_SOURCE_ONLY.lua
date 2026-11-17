-- BGXAI080: combine existing 072 guard + 078 heal decisions WITHOUT engine orders.
-- A positive verdict requires independently verified live EPS state. Any non-idle
-- action is treated as busy, regardless of its ACTION.IDS number or name.
-- This preserves existing EPS buff/heal/attack/song/trap/manual behavior without
-- hand-maintained buff spell lists. SOURCE ONLY. Not installed in EET.
local M={version='0.3.47-080-EPS-FIRST-COORDINATION-SOURCE-ONLY',installed=false}
local function integer(x)
 return type(x)=='number' and x==math.floor(x) and x>0 and x<2147483647
end
local function no(reason,details)
 return {status='HOLD_NO_ENGINE_DISPATCH',reason=reason,
  heal_id=nil,guard_id=nil,orders_sent=0,locals_written=0,
  eps_actions_interrupted=0,engine_dispatch=false,details=details or {}}
end
local function clone(t)
 local c={}; for k,v in pairs(t) do c[k]=v end;return c
end
local function free(actor)
 if type(actor)~='table' or actor.verified~=true then return false,'ACTION_STATE_UNKNOWN' end
 -- The classification is generic: any observed action, including an unfamiliar
 -- spell/buff/ability ACTION.IDS, forbids a BGXAI request.
 if actor.queue_empty~=true or actor.current_action~='IDLE' or actor.idle~=true then
  return false,'ACTION_IN_PROGRESS_OR_QUEUE_BUSY'
 end
 if actor.origin_verified~=true or actor.manual_command~=false then
  return false,'MANUAL_ORIGIN_UNPROVEN'
 end
 return true,nil
end
function M.review(event,members,config,dependencies)
 if type(config)~='table' or config.opt_in~=true or
    config.auto_heal~=true or config.smart_guard~=true then
  return no('OPT_IN_OFF')
 end
 if type(dependencies)~='table' or type(dependencies.heal)~='table'
   or type(dependencies.heal.select)~='function'
   or type(dependencies.guard)~='table'
   or type(dependencies.guard.review)~='function' then
  return no('VERIFIED_SELECTORS_NOT_SUPPLIED')
 end
 if type(event)~='table' or event.verified~=true or not integer(event.victim_id)
   or not integer(event.attacker_id) or event.victim_id==event.attacker_id
   or type(event.heal_event)~='table' or type(event.threat)~='table' then
  return no('HIT_CONTEXT_UNVERIFIED')
 end
 if event.heal_event.victim_id~=event.victim_id or
    event.heal_event.attacker_id~=event.attacker_id or
    event.threat.victim_id~=event.victim_id or
    event.threat.attacker_id~=event.attacker_id then
  return no('CROSS_MODULE_IDENTITY_MISMATCH')
 end
 if type(members)~='table' then return no('PARTY_UNAVAILABLE') end
 local keys,highest=0,0
 for k in pairs(members) do
  if type(k)~='number' or k~=math.floor(k) or k<1 or k>6 then
   return no('PARTY_DUPLICATE_OR_INVALID')
  end
  keys=keys+1
  if k>highest then highest=k end
 end
 if keys~=highest then return no('PARTY_DUPLICATE_OR_INVALID') end
 local byId,bySlot,healCandidates,rej,guardCandidates={},{},{},{},{}
 local n=0
 for _,m in ipairs(members) do
  n=n+1
  if n>6 or type(m)~='table' or not integer(m.id) or byId[m.id] or
    type(m.slot)~='number' or m.slot~=math.floor(m.slot) or
    m.slot<1 or m.slot>6 or bySlot[m.slot] then
   return no('PARTY_DUPLICATE_OR_INVALID')
  end
  byId[m.id]=true;bySlot[m.slot]=true
  local available,why=free(m.action_state)
  if not available then
    rej[m.id]=why
  elseif type(m.eps)~='table' or m.eps.verified~=true or
      m.eps.queue_empty~=true or m.eps.idle~=true then
    rej[m.id]='EPS_STATE_UNKNOWN_OR_BUSY'
  else
    -- Never mutate the caller's factual snapshots. A gate is not proof that
    -- the unknown EPS manual/cast/song/heal/trap flags are false.
    local h=clone(m)
    h.eps=clone(m.eps)
    healCandidates[#healCandidates+1]=h
    guardCandidates[#guardCandidates+1]=m
  end
 end
 if n==0 then return no('NO_PARTY_CANDIDATES') end
 if keys~=n then return no('PARTY_DUPLICATE_OR_INVALID') end
 local okHeal,healResult=pcall(dependencies.heal.select,event.heal_event,healCandidates,{opt_in=true})
 if not okHeal or type(healResult)~='table' or
    healResult.orders_sent~=0 or healResult.locals_written~=0 or
    healResult.engine_dispatch~=false then return no('HEAL_MODULE_FAILED') end
 local healId=healResult.status=='ADVISORY_HEAL_CANDIDATE_ONLY' and healResult.selected_id or nil
 if healId~=nil and (not integer(healId) or not byId[healId]) then
   return no('HEAL_ID_UNVERIFIED')
 end
 local guardId,guardReview=nil,nil
 local guardHoldReasons={}
 for _,m in ipairs(guardCandidates) do
  if m.id~=event.victim_id and m.id~=event.attacker_id and m.id~=healId then
   -- If the victim is in a verified life-threatening condition, protect
   -- EPS emergency recovery over a new move/attack regardless of class.
   if event.heal_event.hp_verified~=true or
      type(event.heal_event.hp_percent)~='number' or
      event.heal_event.hp_percent<25 then
    guardHoldReasons[m.id]='CRITICAL_LIFE_SAVING_PRIORITY'
   else
    local okGuard,gr=pcall(dependencies.guard.review,m.guard_role,event.threat,m.eps,
       event.proposed_target,{opt_in=true,smart_guard=true})
    if not okGuard then gr={reason='GUARD_MODULE_FAILED'} end
    if type(gr)=='table' and gr.state=='CANDIDATE_REVIEW_ONLY' and
       gr.confirmed_target_id==event.attacker_id and gr.allow_engine_action==false
       and gr.engine_orders_sent==0 and gr.script_changes==0 then
       guardId=m.id;guardReview=gr;break
    end
    guardHoldReasons[m.id]=type(gr)=='table' and gr.reason or 'UNVERIFIED_GUARD_RESULT'
   end
  end
 end
 if not healId and not guardId then
  return no('NO_ELIGIBLE_ACTOR',{actor_holds=rej,guard_holds=guardHoldReasons,
     heal_status=healResult.status,heal_reason=healResult.reason})
 end
 return {status='ADVISORY_COORDINATION_ONLY',reason='NO_GAME_DISPATCH_IMPLEMENTED',
   heal_id=healId,guard_id=guardId,guard_target_id=guardId and event.attacker_id or nil,
   selected_roles_verified=true,orders_sent=0,locals_written=0,
   eps_actions_interrupted=0,engine_dispatch=false,
   details={actor_holds=rej,guard_holds=guardHoldReasons,
     heal_status=healResult.status,heal_reason=healResult.reason,
     guard_status=guardReview and guardReview.state or nil}}
end
-- BGXAI EPS-FIRST MULTI-THREAT extension (SOURCE ONLY; NOT INSTALLED).
-- Old M.review remains byte-exact. This is a read-only multi-attacker advisory:
-- it neither issues engine orders nor writes BCS LOCALS. It reuses 072 guard
-- arbitration and 080's origin/queue safety gate. 062 already handled one hit;
-- this adds verified multi-threat assignment with global coverage optimization.
local function holdMulti(why,details)
 return {status='HOLD_NO_ENGINE_DISPATCH',reason=why,assignments={},
  orders_sent=0,locals_written=0,engine_dispatch=false,
  eps_actions_interrupted=0,details=details or {}}
end
local function validPercent(x)
 return type(x)=='number' and x==x and x>=0 and x<=100
end
local function distNumber(x)
 return type(x)=='number' and x==x and x>=0 and x<1000000000
end
local function integerZero(x)
 return type(x)=='number' and x==math.floor(x) and x>=0 and x<2147483647
end
function M.reviewMultipleThreats(events,members,config,dependencies)
 if type(config)~='table' or config.opt_in~=true or config.smart_guard~=true then
  return holdMulti('OPT_IN_OFF')
 end
 if type(dependencies)~='table' or type(dependencies.guard)~='table'
    or type(dependencies.guard.review)~='function' then
  return holdMulti('GUARD_ARBITER_MISSING')
 end
 if type(events)~='table' or #events<1 or #events>6 or
    type(members)~='table' or #members<1 or #members>6 then
  return holdMulti('INVALID_TEAM_OR_THREAT_COUNT')
 end
 local function dense(t)
  local n=0
  for k in pairs(t) do
   if type(k)~='number' or k~=math.floor(k) or k<1 or k>#t then return false end
   n=n+1
  end
  return n==#t
 end
 if not dense(events) or not dense(members) then return holdMulti('SPARSE_OR_MALFORMED_ARRAY') end
 local byId,bySlot={},{}
 for _,m in ipairs(members) do
  if type(m)~='table' or not integer(m.id) or
     not integer(m.slot) or m.slot>6 or byId[m.id] or bySlot[m.slot] then
   return holdMulti('DUPLICATE_OR_INVALID_PARTY')
  end
  byId[m.id]=m;bySlot[m.slot]=true
 end
 local usedAttackers,patientEvidence={},{}
 local sorted={}
 for _,e in ipairs(events) do
  if type(e)~='table' or e.verified~=true or
     not integer(e.victim_id) or not integer(e.attacker_id) or
     e.attacker_id==e.victim_id or not byId[e.victim_id] or
     byId[e.attacker_id] or usedAttackers[e.attacker_id] or
     e.freshness_verified~=true or e.active_now~=true or
     not integerZero(e.snapshot_tick) or
     type(e.victim_state)~='table' or e.victim_state.verified~=true or
     e.victim_state.victim_id~=e.victim_id or
     e.victim_state.rear_support_verified~=true or
     type(e.victim_state.rear_support)~='boolean' or
     not validPercent(e.victim_state.hp_percent) or
     e.victim_state.hp_percent<=0 or
     type(e.threat)~='table' or e.threat.verified~=true or
     e.threat.source~='EEEX_EXPLICIT_ATTACK_ACTION' or
     e.threat.hostile~=true or e.threat.victim_is_party~=true or
     e.threat.attacker_is_party~=false or e.threat.same_area~=true or
     e.threat.attack_in_progress~=true or
     e.threat.attacker_id~=e.attacker_id or e.threat.victim_id~=e.victim_id or
     type(e.proposed_target)~='table' or e.proposed_target.verified~=true or
     e.proposed_target.target_source~='EXACT_RESOLVED_ATTACKER_ID' or
     e.proposed_target.target_id~=e.attacker_id then
   return holdMulti('UNVERIFIED_OR_AMBIGUOUS_THREAT')
  end
  local prev=patientEvidence[e.victim_id]
  if prev and (prev.hp_percent~=e.victim_state.hp_percent or
     prev.rear_support~=e.victim_state.rear_support or
     prev.snapshot_tick~=e.snapshot_tick) then
   return holdMulti('CONFLICTING_VICTIM_EVIDENCE')
  end
  patientEvidence[e.victim_id]={hp_percent=e.victim_state.hp_percent,
   rear_support=e.victim_state.rear_support,snapshot_tick=e.snapshot_tick}
  usedAttackers[e.attacker_id]=true
  sorted[#sorted+1]=e
 end
 -- Priority: save spells/healing via EPS for <=25%, then protect verified rear
 -- support first, then the lower-HP victim, then stable party slot / attacker ID.
 table.sort(sorted,function(a,b)
  if a.victim_state.rear_support~=b.victim_state.rear_support then
   return a.victim_state.rear_support
  end
  if a.victim_state.hp_percent~=b.victim_state.hp_percent then
   return a.victim_state.hp_percent<b.victim_state.hp_percent
  end
  local pa,pb=byId[a.victim_id].slot,byId[b.victim_id].slot
  if pa~=pb then return pa<pb end
  return a.attacker_id<b.attacker_id
 end)
 local candidates={}
 for i,e in ipairs(sorted) do
  local options={}
  -- Keep old 080 critical-life-saving priority; never override EPS recovery.
  if e.victim_state.hp_percent>=25 then
   for _,m in ipairs(members) do
    if m.id~=e.victim_id and m.id~=e.attacker_id and
       m.in_party==true and m.alive==true and m.can_act==true then
     local freeNow=free(m.action_state)
     if freeNow and type(m.eps)=='table' and m.eps.verified==true and
        m.eps.queue_empty==true and m.eps.idle==true then
      local d=type(m.guard_distances)=='table' and m.guard_distances[e.victim_id] or nil
      if type(d)=='table' and d.verified==true and
         d.guardian_id==m.id and d.victim_id==e.victim_id and
         d.snapshot_tick==e.snapshot_tick and d.same_area==true and
         distNumber(d.distance_sq) then
       -- Source and target identity still require the *existing* 072 contract.
       local ok,review=pcall(dependencies.guard.review,clone(m.guard_role),
         clone(e.threat),clone(m.eps),clone(e.proposed_target),
         {opt_in=true,smart_guard=true})
       if ok and type(review)=='table' and
          review.state=='CANDIDATE_REVIEW_ONLY' and
          review.confirmed_target_id==e.attacker_id and
          review.allow_engine_action==false and
          review.engine_orders_sent==0 and review.script_changes==0 then
        options[#options+1]={m=m,distance=d.distance_sq}
       end
      end
     end
    end
   end
  end
  table.sort(options,function(a,b)
   if a.distance~=b.distance then return a.distance<b.distance end
   return a.m.slot<b.m.slot
  end)
  candidates[i]=options
 end
 local best,chosen,usedGuardians={}, {}, {}
 local function better(a,b)
  if not b then return true end
  -- Lexicographic coverage: prioritize confirmed vulnerable rear threats;
  -- but a different first guardian may cover more total threats.
  for i=1,#sorted do
   local ca,cb=a[i]~=nil,b[i]~=nil
   if ca~=cb then return ca end
  end
  local da,db=0,0
  for i=1,#sorted do
   if a[i] then da=da+a[i].distance end
   if b[i] then db=db+b[i].distance end
  end
  if da~=db then return da<db end
  for i=1,#sorted do
   local sa=a[i] and a[i].m.slot or 99
   local sb=b[i] and b[i].m.slot or 99
   if sa~=sb then return sa<sb end
  end
  return false
 end
 local function search(i)
  if i>#sorted then
   if better(chosen,best) then
    best={};for j=1,#sorted do best[j]=chosen[j] end
   end
   return
  end
  -- nil branch means no available guardian, while other threats can be covered.
  chosen[i]=nil;search(i+1)
  for _,opt in ipairs(candidates[i]) do
   if not usedGuardians[opt.m.id] then
    usedGuardians[opt.m.id]=true;chosen[i]=opt
    search(i+1)
    usedGuardians[opt.m.id]=nil;chosen[i]=nil
   end
  end
 end
 search(1)
 local assignments={}
 for i,e in ipairs(sorted) do
  local o=best and best[i]
  if o then
   assignments[#assignments+1]={guardian_id=o.m.id,guardian_slot=o.m.slot,
    victim_id=e.victim_id,attacker_id=e.attacker_id,
    distance_sq=o.distance,rear_support=e.victim_state.rear_support,
    verified_source='EXACT_RESOLVED_ATTACKER_ID',
    status='ADVISORY_NO_ENGINE_ORDER'}
  end
 end
 if #assignments==0 then return holdMulti('NO_VERIFIED_FREE_INTERCEPTOR') end
 return {status='ADVISORY_MULTI_THREAT_ONLY',reason='NO_ENGINE_DISPATCH_IMPLEMENTED',
  assignments=assignments,orders_sent=0,locals_written=0,engine_dispatch=false,
  eps_actions_interrupted=0,threats_seen=#sorted,threats_covered=#assignments}
end
return M
