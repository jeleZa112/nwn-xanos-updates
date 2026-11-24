-- BGXAI 081 V3: passive raw action-context evidence, NEVER origin authorization.
-- SOURCE ONLY. No hooks, actions, LOCALS, timers, files or game writes.
-- m_source is recorded as an unclassified candidate, not manual/EPS proof.
local M={version='0.3.51-081-ACTION-CONTEXT-V3',installed=false}

local function integer(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
  x%1==0 and x>=lo and x<=hi
end

local function read_int(obj,key,lo,hi)
 if obj==nil then return nil end
 local ok,value=pcall(function() return obj[key] end)
 if ok and integer(value,lo,hi) then return value end
 return nil
end

local function read_nested_int(obj,parentKey,key,lo,hi)
 if obj==nil then return nil end
 local ok,parent=pcall(function() return obj[parentKey] end)
 if not ok or parent==nil then return nil end
 return read_int(parent,key,lo,hi)
end

local function current_action_id(sprite)
 if sprite==nil then return nil end
 local ok,action=pcall(function() return sprite.m_curAction end)
 if not ok or action==nil then return nil end
 return read_int(action,'m_actionID',0,65535)
end

local function queue_count(sprite)
 if sprite==nil then return nil end
 local function once()
  local q=sprite.m_queuedActions
  if q==nil then return nil end
  return q.m_nCount
 end
 local okA,a=pcall(once)
 if not okA or not integer(a,0,512) then return nil,'QUEUE_COUNT_NOT_READABLE' end
 local okB,b=pcall(once)
 if not okB or not integer(b,0,512) then return nil,'QUEUE_COUNT_NOT_READABLE' end
 if a~=b then return nil,'QUEUE_COUNT_CHANGED_DURING_READ' end
 return a,'RAW_QUEUE_COUNT_STABLE'
end

local function printable_ascii(value)
 if type(value)~='string' or #value<1 or #value>48 then return false end
 for i=1,#value do
  local b=value:byte(i)
  if b<32 or b>126 then return false end
 end
 return true
end

local function read_action_source(action)
 if action==nil then return nil,'ACTION_SOURCE_ACTION_UNAVAILABLE' end
 local ok,source=pcall(function() return action.m_source end)
 if not ok or source==nil then return nil,'ACTION_SOURCE_FIELD_UNAVAILABLE' end
 if type(source)=='string' then
  if printable_ascii(source) then return source,'SOURCE_RAW_OBSERVED' end
  return nil,'ACTION_SOURCE_STRING_INVALID'
 end
 local okPtr,ptr=pcall(function() return source.m_pchData end)
 if not okPtr or not integer(ptr,65536,140737488355327) then
  return nil,'ACTION_SOURCE_POINTER_UNAVAILABLE'
 end
 local reader=rawget(_G,'EEex_ReadLString')
 if type(reader)~='function' then return nil,'EEEX_READLSTRING_UNAVAILABLE' end
 local okRead,value=pcall(reader,ptr,49)
 if not okRead or type(value)~='string' then return nil,'ACTION_SOURCE_READ_FAILED' end
 if #value>48 then return nil,'ACTION_SOURCE_TRUNCATED' end
 if value=='' then return nil,'ACTION_SOURCE_EMPTY' end
 if not printable_ascii(value) then return nil,'ACTION_SOURCE_NONPRINTABLE' end
 return value,'SOURCE_RAW_OBSERVED'
end

local function context_once(sprite,action)
 local source,sourceStatus=read_action_source(action)
 return {
  inActionExecution=read_int(sprite,'m_bInActionExecution',0,1),
  noInterrupt=read_int(sprite,'m_bNoInterrupt',0,1),
  curScriptNum=read_int(sprite,'m_curScriptNum',-32768,32767),
  actionCount=read_int(sprite,'m_actionCount',-32768,32767),
  interrupt=read_int(sprite,'m_interrupt',-2147483648,2147483647),
  orderedByInstance=read_nested_int(sprite,'m_lOrderedBy','m_Instance',0,2147483647),
  orderedBySentInstance=read_nested_int(sprite,'m_lOrderedBySent','m_Instance',0,2147483647),
  actionSource=source,
  actionSourceStatus=sourceStatus,
 }
end

local function context_stable(a,b)
 return a.inActionExecution~=nil and b.inActionExecution==a.inActionExecution and
  a.noInterrupt~=nil and b.noInterrupt==a.noInterrupt and
  a.curScriptNum~=nil and b.curScriptNum==a.curScriptNum and
  a.actionCount~=nil and b.actionCount==a.actionCount and
  a.interrupt~=nil and b.interrupt==a.interrupt and
  a.orderedByInstance==b.orderedByInstance and
  a.orderedBySentInstance==b.orderedBySentInstance
end

function M.observe(sprite,action)
 local idBefore=current_action_id(sprite)
 local q1,q1Status=queue_count(sprite)
 local c1=context_once(sprite,action)
 local q2,q2Status=queue_count(sprite)
 local c2=context_once(sprite,action)
 local idAfter=current_action_id(sprite)
 local callbackId=read_int(action,'m_actionID',0,65535)
 local actionStable=idBefore~=nil and idBefore==idAfter and callbackId==idBefore
 if not actionStable then
  return {
   status='ACTION_UNKNOWN',reason='ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT',
   current_action_id=nil,queue_empty=nil,queue_count_raw=nil,
   queue_count_observed=false,queue_count_read_status='QUEUE_OR_ACTION_UNSTABLE',
   action_context_snapshot_stable=false,action_source_stable=false,
   action_source_raw=nil,action_source_read_status='ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT',
   action_origin='UNKNOWN',action_origin_verified=false,
   manual_command=nil,manual_command_verified=false,eps_queue_empty_verified=false,
   safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0,
  }
 end
 local queueStable=q1~=nil and q2~=nil and q1==q2
 local contextStable=context_stable(c1,c2)
 local sourceStable=c1.actionSourceStatus=='SOURCE_RAW_OBSERVED' and
  c2.actionSourceStatus=='SOURCE_RAW_OBSERVED' and c1.actionSource==c2.actionSource
 local sourceStatus=c1.actionSourceStatus
 if c1.actionSourceStatus~=c2.actionSourceStatus then
  sourceStatus='ACTION_SOURCE_STATUS_CHANGED_DURING_READ'
 elseif c1.actionSourceStatus=='SOURCE_RAW_OBSERVED' and c1.actionSource~=c2.actionSource then
  sourceStatus='ACTION_SOURCE_CHANGED_DURING_READ'
 end
 local qNonempty=nil
 if queueStable then qNonempty=(q1>0) end
 local qStatus=q1Status
 if q1Status~=q2Status then qStatus='QUEUE_COUNT_STATUS_CHANGED_DURING_READ'
 elseif q1~=q2 then qStatus='QUEUE_COUNT_CHANGED_DURING_CAPTURE' end
 return {
  status='CURRENT_ACTION_CONTEXT_OBSERVED',reason='ORIGIN_NOT_PROVEN',
  current_action_id=idBefore,
  queue_empty=nil,
  queue_count_raw=queueStable and q1 or nil,
  queue_count_observed=queueStable,
  queue_count_read_status=queueStable and 'RAW_QUEUE_COUNT_STABLE' or qStatus,
  queue_nonempty_observed=qNonempty,
  action_context_snapshot_stable=contextStable,
  engine_action_execution_raw=contextStable and c1.inActionExecution or nil,
  engine_no_interrupt_raw=contextStable and c1.noInterrupt or nil,
  current_script_number_raw=contextStable and c1.curScriptNum or nil,
  action_count_raw=contextStable and c1.actionCount or nil,
  interrupt_raw=contextStable and c1.interrupt or nil,
  ordered_by_instance_raw=contextStable and c1.orderedByInstance or nil,
  ordered_by_sent_instance_raw=contextStable and c1.orderedBySentInstance or nil,
  action_source_stable=sourceStable,
  action_source_raw=sourceStable and c1.actionSource or nil,
  action_source_read_status=sourceStatus,
  action_source_semantics='UNCLASSIFIED_CAI_ACTION_M_SOURCE',
  eps_queue_empty_verified=false,
  action_origin='UNKNOWN',action_origin_verified=false,
  manual_command=nil,manual_command_verified=false,
  casting=nil,healing=nil,buffing=nil,singing=nil,detecting_traps=nil,
  safe_to_dispatch=false,orders_sent=0,locals_written=0,hooks_registered=0,
 }
end

function M.arbitrate(advisory,snapshot)
 return {status='HOLD',reason='ACTION_ORIGIN_AND_SAFE_BOUNDARY_NOT_PROVEN',
  allow_engine_action=false,orders_sent=0,locals_written=0,
  verified_queue_empty=false,verified_origin=false}
end
return M
