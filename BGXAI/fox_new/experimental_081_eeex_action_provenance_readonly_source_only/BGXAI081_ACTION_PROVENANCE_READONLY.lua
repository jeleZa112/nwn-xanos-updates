-- BGXAI 081: fail-closed observation of action ID; NEVER proof of manual/EPS origin.
-- SOURCE ONLY. No hook, engine command, timers, local writes, file system or globals.
local M = {version='0.3.49-081-ACTION-PROVENANCE-SOURCE-ONLY',installed=false}
local function integer(x)
  return type(x)=='number' and x==math.floor(x) and x>=0 and x<=65535
end
local function get_action(sprite)
  if sprite==nil then return nil,'NO_SPRITE' end
  local ok,action=pcall(function() return sprite.m_curAction end)
  if not ok or action==nil then return nil,'CURRENT_ACTION_UNAVAILABLE' end
  local ok2,id=pcall(function() return action.m_actionID end)
  if not ok2 or not integer(id) then return nil,'ACTION_ID_UNAVAILABLE' end
  return id,nil
end
function M.observe(sprite)
  local id,issue=get_action(sprite)
  return {
    status=id==nil and 'ACTION_UNKNOWN' or 'CURRENT_ACTION_ID_OBSERVED',
    reason=issue or 'ORIGIN_AND_QUEUE_NOT_PROVEN',
    current_action_id=id,
    -- Neither id==0 nor action-started listener proves script queue is empty.
    queue_empty=nil,
    eps_queue_empty_verified=false,
    action_origin='UNKNOWN',
    action_origin_verified=false,
    manual_command=nil,
    manual_command_verified=false,
    casting=nil,
    healing=nil,
    buffing=nil,
    singing=nil,
    detecting_traps=nil,
    safe_to_dispatch=false,
    orders_sent=0,
    locals_written=0,
    hooks_registered=0,
  }
end
function M.arbitrate(advisory, snapshot)
  -- A new active adapter is NOT present in 081. Even a fabricated externally
  -- optimistic snapshot cannot grant dispatch permission through this module.
  local reason='ACTION_ORIGIN_AND_EPS_QUEUE_UNVERIFIED'
  if type(snapshot)~='table' or snapshot.status~='CURRENT_ACTION_ID_OBSERVED' then
    reason='CURRENT_ACTION_NOT_OBSERVED'
  elseif type(advisory)~='table' or advisory.orders_sent~=0 then
    reason='ADVISORY_NOT_TRUSTED'
  elseif snapshot.current_action_id~=0 then
    reason='ACTION_PRESENT_OR_QUEUE_UNVERIFIED'
  end
  return {status='HOLD',reason=reason,allow_engine_action=false,
    orders_sent=0,locals_written=0,verified_queue_empty=false,
    verified_origin=false}
end
return M
