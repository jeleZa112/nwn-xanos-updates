-- BGXAI 083. Pure source-only, opt-in future hook adapter. NOT INSTALLED.
-- The event of a started action is not evidence of an empty queued action list,
-- nor evidence that the actor's action is manually ordered or EPS generated.
-- No engine dispatch, no LOCALS, no timer, no game files, no global changes.
local M = {version='083-EEEX117-PASSIVE-TRACE-SOURCE-ONLY', installed=false}
local function valid_id(x)
  return type(x)=='number' and x >= 0 and x <= 65535 and x == math.floor(x)
end
local function safe_get(o,k)
  if o == nil then return nil end
  local ok,v=pcall(function() return o[k] end)
  if ok then return v end
  return nil
end
local function nonnegative(x)
  if type(x)=='number' and x==math.floor(x) and x>=0 and x<=65535 then return x end
  return nil
end
local function fresh_event(seq,actor_id,action_id,script_num,origin)
  return {
    seq=seq, actor_id=actor_id, action_id=action_id,
    script_num=script_num, script_metadata_observed=(script_num~=nil),
    action_id_observed=(action_id~=nil),
    action_origin='UNKNOWN', origin_verified=false,
    manual_order_verified=false, eps_order_verified=false,
    eps_queue_empty=nil, eps_queue_empty_verified=false,
    current_action_idle_verified=false,  -- even action_id==0 is insufficient
    safe_to_dispatch=false, orders_sent=0, locals_written=0,
    source=origin or 'UNATTRIBUTED',
  }
end
function M.new(max_events)
  if type(max_events)~='number' or max_events~=math.floor(max_events)
     or max_events<1 or max_events>256 then return nil,'INVALID_LIMIT' end
  local state = {capacity=max_events, history={}, seq=0, dropped=0}
  function state:observe(actor_id,sprite,action,source)
    if not valid_id(actor_id) then return nil,'INVALID_ACTOR_ID' end
    local current=action or safe_get(sprite,'m_curAction')
    local action_id=nonnegative(safe_get(current,'m_actionID'))
    -- m_curScriptNum is an OBSERVATION ONLY (not a provenance certificate).
    local script_num=nonnegative(safe_get(sprite,'m_curScriptNum'))
    self.seq=self.seq+1
    local e=fresh_event(self.seq,actor_id,action_id,script_num,source)
    if #self.history>=self.capacity then
      table.remove(self.history,1); self.dropped=self.dropped+1
    end
    table.insert(self.history,e)
    return e,nil
  end
  function state:copy()
    local out={}
    for i,e in ipairs(self.history) do
      local clone={}
      for k,v in pairs(e) do clone[k]=v end
      out[i]=clone
    end
    return {events=out,capacity=self.capacity,dropped=self.dropped,
      observations=self.seq,queue_verifiable=false,origin_verifiable=false,
      can_activate_080=false,installed=false,engine_dispatch=false}
  end
  function state:can_issue_order()
    return false,'MANUAL_ORIGIN_AND_EPS_QUEUE_UNVERIFIED'
  end
  -- Compatibility facade for the already source-only 082 bridge. A missing actor
  -- ID or unreadable sprite is still an unknown observation, never permission.
  function state:for_082()
    return {observe=function(sprite)
      local actor_id=safe_get(sprite,'m_id')
      local e,err=self:observe(valid_id(actor_id) and actor_id or 0,sprite,nil,'SOURCE_083_OBSERVATION')
      return {status=e and (e.action_id_observed and 'CURRENT_ACTION_ID_OBSERVED' or 'ACTION_UNKNOWN') or 'ACTION_UNKNOWN',
        reason=err or 'ORIGIN_AND_QUEUE_NOT_PROVEN',
        current_action_id=e and e.action_id or nil, queue_empty=nil,
        action_origin='UNKNOWN', action_origin_verified=false,
        manual_command_verified=false, safe_to_dispatch=false,
        orders_sent=0, locals_written=0, hooks_registered=0}
    end}
  end
  return state,nil
end
return M