-- BGXAI 084: EEex v1.1.7 ActionListEmpty() native-trigger probe (SOURCE ONLY).
-- No hook registration, engine orders, LOCALS writes, or game file writes.
-- Evaluating a trigger is NOT a proof of command origin or future queue state.
local M = {version='084-NATIVE-QUEUE-PROBE-SOURCE-ONLY',installed=false}
local TRIGGER='ActionListEmpty()'
local function get(o,k)
  if o == nil then return nil end
  local ok,v=pcall(function() return o[k] end)
  if ok then return v end
  return nil
end
local function valid_actor(id)
  return type(id)=='number' and id==math.floor(id) and id>=1 and id<=0xFFFFFFFF
end
local function hold(reason,id)
  return {status='HOLD_NO_ENGINE_DISPATCH',reason=reason,actor_id=id,
    trigger=TRIGGER,trigger_boolean_observed=false,queue_empty_sample=nil,
    queue_empty_verified=false,origin='UNKNOWN',origin_verified=false,
    manual_command_verified=false,eps_command_verified=false,
    current_action_idle_verified=false,engine_dispatch=false,
    safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0,
    installed=false}
end
-- Adapter must be provided explicitly. Does not discover or register engine APIs.
-- Returned Boolean is an observation AT EVALUATION TIME, not an authorization.
function M.sample(sprite,evaluate)
  local id=get(sprite,'m_id')
  if not valid_actor(id) then return hold('INVALID_OR_UNREADABLE_ACTOR_ID',nil) end
  if type(evaluate)~='function' then return hold('NATIVE_EVALUATOR_NOT_SUPPLIED',id) end
  local ok,answer=pcall(evaluate,TRIGGER,sprite)
  if not ok then return hold('NATIVE_EVALUATION_ERROR',id) end
  if type(answer)~='boolean' then return hold('NATIVE_EVALUATION_NON_BOOLEAN',id) end
  local res=hold('LIVE_PROVENANCE_AND_QUEUE_STABILITY_UNVERIFIED',id)
  res.status='NATIVE_TRIGGER_BOOLEAN_OBSERVED'
  res.trigger_boolean_observed=true
  res.queue_empty_sample=answer
  -- This is intentionally NOT assigned to queue_empty_verified / idle_verified.
  return res
end
-- Optional, explicit call site for an eventual separately approved observer.
-- In EEex v1.1.7 EEex_Trigger_EvalConditionalStringAsAIBase delegates to
-- ParseConditionalString(...), then m_curCondition:Hold(aiBase.m_pendingTriggers,aiBase).
-- No live side-effect/concurrency tests have been performed on the user's EET.
function M.sample_from_eeex(sprite)
  local f=rawget(_G,'EEex_Trigger_EvalConditionalStringAsAIBase')
  if type(f)~='function' then
    local id=get(sprite,'m_id')
    return hold('EEEX117_NATIVE_EVALUATOR_UNAVAILABLE',valid_actor(id) and id or nil)
  end
  return M.sample(sprite,function(trigger,actor) return f(trigger,actor) end)
end
-- Bridge to BGXAI 082 remains fail closed even on queue_empty_sample=true.
-- Do NOT turn a transient trigger result into 080 verified=true.
function M.for_082(evaluate)
  return {observe=function(sprite)
    local s=M.sample(sprite,evaluate)
    return {status=s.status,reason=s.reason,
      current_action_id=nil,queue_empty=nil,
      queue_empty_sample=s.queue_empty_sample,
      queue_empty_verified=false,action_origin='UNKNOWN',
      action_origin_verified=false,manual_command_verified=false,
      safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0}
  end}
end
return M
