-- BGXAI 082: strict read-only bridge from observed action ID to 080.
-- A sampled current action ID NEVER proves provenance, EPS queue, or idle.
-- Pure, local, no engine hooks, no orders, no LOCALS. Game unchanged.
local M={version='0.3.50-082-EPS-QUEUE-GUARD-READONLY',installed=false}
local function fail(reason)
  return {status='HOLD_NO_ENGINE_DISPATCH',reason=reason,
    heal_id=nil,guard_id=nil,orders_sent=0,locals_written=0,
    eps_actions_interrupted=0,engine_dispatch=false}
end
local function shallow(input)
  local out={};if type(input)=='table' then for k,v in pairs(input) do out[k]=v end end
  return out
end
function M.observed_members(members,sprites,observer)
  if type(members)~='table' or type(sprites)~='table' or
     type(observer)~='table' or type(observer.observe)~='function' then
    return nil,'OBSERVATION_SOURCE_MISSING'
  end
  local seen,n={},0
  local result={}
  for i,actor in ipairs(members) do
    n=n+1
    if n>6 or type(actor)~='table' or type(actor.id)~='number'
       or seen[actor.id] then return nil,'MALFORMED_PARTY' end
    seen[actor.id]=true
    local observed=observer.observe(sprites[actor.id])
    if type(observed)~='table' or observed.orders_sent~=0
       or observed.locals_written~=0 or observed.hooks_registered~=0 then
      return nil,'OBSERVATION_NOT_PASSIVE'
    end
    local copy=shallow(actor)
    -- This new snapshot replaces any earlier optimistic test fixture. No user
    -- provided `verified=true` flag can override missing engine evidence.
    copy.action_state={verified=false,origin_verified=false,
      current_action=observed.current_action_id or 'UNKNOWN',
      queue_empty=nil,idle=false,manual_command=nil}
    result[i]=copy
  end
  if n==0 then return nil,'EMPTY_PARTY' end
  for k in pairs(members) do
    if type(k)~='number' or k~=math.floor(k) or k<1 or k>n then
      return nil,'MALFORMED_PARTY'
    end
  end
  return result,nil
end
function M.review(event,members,sprites,observer,coordinator,dependencies,config)
  local actors,why=M.observed_members(members,sprites,observer)
  if not actors then return fail(why) end
  if type(coordinator)~='table' or type(coordinator.review)~='function' then
    return fail('COORDINATOR_MISSING') end
  local ok,answer=pcall(coordinator.review,event,actors,config,dependencies)
  if not ok or type(answer)~='table' or answer.orders_sent~=0
     or answer.locals_written~=0 or answer.engine_dispatch~=false then
    return fail('COORDINATOR_INVARIANT_FAILED')
  end
  if answer.status~='HOLD_NO_ENGINE_DISPATCH' then
    return fail('UNPROVEN_EPS_QUEUE_CANNOT_GRANT_PERMISSION') end
  return fail('MANUAL_ORIGIN_AND_EPS_QUEUE_NOT_YET_VERIFIED')
end
return M
