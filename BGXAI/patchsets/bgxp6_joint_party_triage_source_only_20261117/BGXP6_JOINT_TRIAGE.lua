-- BGXP6: joint AUTO/HEALER reservation + 080 verified multi-threat protection.
-- PURE ADVISORY ONLY; no engine, no LOCALS, no BCS, no game installation.
-- Baseline BGXP5 healing thresholds 35%, 70%, visibility+18 range, F and idle.
local M = {version='0.3.42-BGXP6-HEAL-GUARD-JOINT-ADVISORY',installed=false}

local function validId(x)
 return type(x)=='number' and x==math.floor(x) and x>0 and x<2147483647
end
local function validTick(x)
 return type(x)=='number' and x==math.floor(x) and x>=0 and x<2147483647
end
local function pct(x)
 return type(x)=='number' and x==x and x>=0 and x<=100
end
local function num(x)
 return type(x)=='number' and x==x and x>=0 and x<1000000000
end
local function dense(t,maximum)
 if type(t)~='table' then return false end
 local n=#t
 if n<1 or n>maximum then return false end
 local count=0
 for k in pairs(t) do
  if type(k)~='number' or k~=math.floor(k) or k<1 or k>n then return false end
  count=count+1
 end
 return count==n
end
local function copy(source)
 local t={}
 for k,v in pairs(source) do t[k]=v end
 return t
end
local function hold(reason,extras)
 return {status='HOLD_NO_ENGINE_DISPATCH',reason=reason,heal_assignments={},
   guard_assignments={},reserved_healers={},heal_coverage=0,
   guard_coverage=0,engine_dispatch=false,orders_sent=0,locals_written=0,
   eps_actions_interrupted=0,details=extras or {}}
end
local function free(actor)
 local a,e=actor.action_state,actor.eps
 return type(a)=='table' and a.verified==true and a.origin_verified==true
    and a.queue_empty==true and a.idle==true and a.current_action=='IDLE'
    and a.manual_command==false
    and type(e)=='table' and e.verified==true and e.queue_empty==true
    and e.idle==true and e.manual_command==false and e.casting==false
    and e.singing==false and e.detecting_traps==false
    and e.heal_pending==false and e.ally_in_critical_danger==false
end
local function healerRole(h)
 return h.role=='AUTO' or h.role=='HEALER'
end
local function validHealth(m)
 return type(m.hp)=='table' and m.hp.verified==true
     and pct(m.hp.percent) and (m.hp.percent>0)==(m.alive==true)
end
local function matchScore(matching,patients)
 local count,dist=0,0
 for _,p in ipairs(patients) do
  local selected=matching[p.id]
  if selected then count=count+1;dist=dist+selected.distance_sq end
 end
 return count,dist
end
local function isBetter(a,b,patients)
 if not b then return true end
 -- Emergency patients are first, then less damaged, then portrait slot.
 for _,p in ipairs(patients) do
  local ae=a[p.id]~=nil
  local be=b[p.id]~=nil
  if ae~=be then return ae end
 end
 local ca,da=matchScore(a,patients)
 local cb,db=matchScore(b,patients)
 if ca~=cb then return ca>cb end
 if da~=db then return da<db end
 for _,p in ipairs(patients) do
  local aa=a[p.id] and a[p.id].slot or 99
  local bb=b[p.id] and b[p.id].slot or 99
  if aa~=bb then return aa<bb end
 end
 return false
end

function M.plan(snapshot,events,members,config,dependencies)
 if type(config)~='table' or config.opt_in~=true
    or config.auto_heal~=true or config.smart_guard~=true
    or config.joint_coordination~=true then return hold('OPT_IN_OFF') end
 if type(snapshot)~='table' or snapshot.verified~=true
    or not validTick(snapshot.tick) then return hold('SNAPSHOT_UNVERIFIED') end
 if not dense(members,6) then return hold('PARTY_MALFORMED') end
 if type(events)~='table' then return hold('THREATS_MALFORMED') end
 local eventCount=0
 for k in pairs(events) do
  if type(k)~='number' or k~=math.floor(k) or k<1 or k>#events then
   return hold('THREATS_MALFORMED')
  end
  eventCount=eventCount+1
 end
 if eventCount~=#events or #events>6 then return hold('THREATS_MALFORMED') end
 if type(dependencies)~='table' or type(dependencies.coordinator)~='table'
    or type(dependencies.coordinator.reviewMultipleThreats)~='function'
    or type(dependencies.guard)~='table' or
    type(dependencies.guard.review)~='function' then
  return hold('VERIFIED_COORDINATOR_NOT_SUPPLIED')
 end
 local byId,bySlot={},{}
 local injured={}
 for _,m in ipairs(members) do
  if type(m)~='table' or not validId(m.id) or not validId(m.slot)
     or m.slot>6 or byId[m.id] or bySlot[m.slot]
     or (m.in_party~=true and m.in_party~=false)
     or (m.alive~=true and m.alive~=false)
     or (m.can_act~=true and m.can_act~=false)
     or not validHealth(m)
     or type(m.heal)~='table' or m.heal.verified~=true
     or (m.heal.role~='AUTO' and m.heal.role~='HEALER'
         and m.heal.role~='OTHER')
     or (m.heal.guard_on~=true and m.heal.guard_on~=false) then
    return hold('ACTOR_OR_HEAL_EVIDENCE_INVALID')
  end
  byId[m.id]=m;bySlot[m.slot]=true
  if m.in_party and m.alive and m.hp.percent<70 then injured[#injured+1]=m end
 end
 table.sort(injured,function(a,b)
  local ae,be=a.hp.percent<35,b.hp.percent<35
  if ae~=be then return ae end
  if a.hp.percent~=b.hp.percent then return a.hp.percent<b.hp.percent end
  return a.slot<b.slot
 end)
 local reserved,options={},{}
 for _,m in ipairs(members) do
  if healerRole(m.heal) and m.heal.guard_on==true and m.in_party==true
     and m.alive==true and m.can_act==true and #injured>0 then
   -- Even if ability/queue state is unknown, keep potential healers out
   -- of guard duty until availability is proven. No guessed permission.
   if m.heal.prepared~=false then
    reserved[m.id]='POTENTIAL_BGXP5_HEALER'
   end
   if m.heal.prepared==true and m.heal.cooldown_ready==true and free(m) then
    for _,target in ipairs(injured) do
     if target.id~=m.id then
      local obs=type(m.heal.targets)=='table' and m.heal.targets[target.id] or nil
      if type(obs)=='table' and obs.verified==true
          and obs.snapshot_tick==snapshot.tick and obs.same_area==true
          and obs.visible==true and num(obs.distance_sq)
          and type(obs.range_verified)=='boolean'
          and obs.range_verified==true and obs.range_18==true then
       options[target.id]=options[target.id] or {}
       options[target.id][#options[target.id]+1]={
        id=m.id,slot=m.slot,distance_sq=obs.distance_sq}
      end
     end
    end
   end
  end
 end
 for _,opts in pairs(options) do
  table.sort(opts,function(a,b)
   if a.distance_sq~=b.distance_sq then return a.distance_sq<b.distance_sq end
   return a.slot<b.slot
  end)
 end
 local chosen,best,used={},{},{}
 best=nil
 local function assign(i)
  if i>#injured then
   if isBetter(chosen,best,injured) then
    best={}
    for k,v in pairs(chosen) do best[k]=v end
   end
   return
  end
  local patient=injured[i]
  chosen[patient.id]=nil;assign(i+1)
  for _,candidate in ipairs(options[patient.id] or {}) do
   if not used[candidate.id] then
    used[candidate.id]=true
    chosen[patient.id]=candidate
    assign(i+1)
    chosen[patient.id]=nil
    used[candidate.id]=nil
   end
  end
 end
 assign(1)
 local heals={}
 for _,m in ipairs(injured) do
  local selected=best and best[m.id]
  if selected then
   heals[#heals+1]={
    healer_id=selected.id,healer_slot=selected.slot,
    patient_id=m.id,patient_slot=m.slot,
    patient_hp_percent=m.hp.percent,distance_sq=selected.distance_sq,
    priority=m.hp.percent<35 and 'EMERGENCY' or 'EARLY'}
  end
 end
 -- Provide all party identities to the old coordinator (it validates victims),
 -- but lock any healer candidate from a simultaneous guard assignment.
 local forGuard={}
 for i,m in ipairs(members) do
  local c=copy(m)
  if reserved[m.id] then
   c.action_state={verified=false,origin_verified=false,queue_empty=nil,
      idle=false,current_action='HEAL_RESERVED',manual_command=nil}
   c.eps={verified=false,queue_empty=nil,idle=false,manual_command=nil}
  end
  forGuard[i]=c
 end
 local guards={}
 local guardReason='NO_VERIFIED_ACTIVE_THREATS'
 if #events>0 then
  for _,e in ipairs(events) do
   if type(e)~='table' or e.snapshot_tick~=snapshot.tick then
    return hold('CROSS_MODULE_SNAPSHOT_MISMATCH')
   end
  end
  local ok,r=pcall(dependencies.coordinator.reviewMultipleThreats,events,
        forGuard,{opt_in=true,smart_guard=true},{guard=dependencies.guard})
  if not ok or type(r)~='table' or r.engine_dispatch~=false
     or r.orders_sent~=0 or r.locals_written~=0 or
     r.eps_actions_interrupted~=0 then
   return hold('UNVERIFIED_GUARD_COORDINATOR_RESULT')
  end
  guardReason=r.reason
  if r.status=='ADVISORY_MULTI_THREAT_ONLY' then
   for _,g in ipairs(r.assignments or {}) do
    if reserved[g.guardian_id] or not byId[g.guardian_id] then
     return hold('HEAL_GUARD_COLLISION_REJECTED')
    end
    guards[#guards+1]={
      guardian_id=g.guardian_id,guardian_slot=g.guardian_slot,
      victim_id=g.victim_id,attacker_id=g.attacker_id}
   end
  elseif r.status~='HOLD_NO_ENGINE_DISPATCH' then
   return hold('UNVERIFIED_GUARD_COORDINATOR_STATUS')
  end
 end
 local reservedList={}
 for _,m in ipairs(members) do
  if reserved[m.id] then
   reservedList[#reservedList+1]={actor_id=m.id,reason=reserved[m.id]}
  end
 end
 local active=#heals>0 or #guards>0
 return {status=active and 'ADVISORY_JOINT_ONLY' or 'HOLD_NO_ENGINE_DISPATCH',
   reason=active and 'NO_ENGINE_DISPATCH_IMPLEMENTED' or guardReason,
   heal_assignments=heals,guard_assignments=guards,
   reserved_healers=reservedList,heal_coverage=#heals,guard_coverage=#guards,
   engine_dispatch=false,orders_sent=0,locals_written=0,
   eps_actions_interrupted=0,details={snapshot_tick=snapshot.tick,
     injured_count=#injured,still_requires_proven_EEex_action_origin=true}}
end

return M
