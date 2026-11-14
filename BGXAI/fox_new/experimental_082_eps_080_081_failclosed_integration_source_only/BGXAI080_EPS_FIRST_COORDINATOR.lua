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
return M
