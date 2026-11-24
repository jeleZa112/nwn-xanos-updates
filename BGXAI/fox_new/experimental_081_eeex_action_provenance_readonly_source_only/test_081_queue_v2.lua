local root=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(root..'BGXAI081_ACTION_PROVENANCE_QUEUE_V2.lua')
local checks=0
local function eq(a,b,msg)
 checks=checks+1
 if a~=b then error((msg or 'assertion')..': '..tostring(a)..' ~= '..tostring(b),2) end
end
local function invariant(r)
 eq(r.safe_to_dispatch,false)
 eq(r.eps_queue_empty_verified,false)
 eq(r.action_origin,'UNKNOWN')
 eq(r.action_origin_verified,false)
 eq(r.manual_command_verified,false)
 eq(r.queue_empty,nil)
 eq(r.manual_command,nil)
 eq(r.orders_sent,0)
 eq(r.locals_written,0)
 eq(r.hooks_registered,0)
end
for _,value in ipairs({0,3,23,94,98,105,134,65535}) do
 local r=M.observe({m_curAction={m_actionID=value}})
 eq(r.current_action_id,value)
 eq(r.status,'CURRENT_ACTION_ID_OBSERVED')
 invariant(r)
 local p=M.arbitrate({orders_sent=0},r)
 eq(p.status,'HOLD')
 eq(p.allow_engine_action,false)
 eq(p.orders_sent,0)
 eq(p.locals_written,0)
 eq(p.verified_queue_empty,false)
 eq(p.verified_origin,false)
end
for _,value in ipairs({-1,1.5,65536,'0',false,math.huge,math.huge/-1}) do
 local r=M.observe({m_curAction={m_actionID=value}})
 eq(r.status,'ACTION_UNKNOWN')
 eq(r.current_action_id,nil)
 invariant(r)
end
for _,spr in ipairs({{}, {m_curAction={}}, {m_curAction=false}}) do
 local r=M.observe(spr)
 eq(r.status,'ACTION_UNKNOWN')
 invariant(r)
end
local r=M.observe(nil);eq(r.status,'ACTION_UNKNOWN');invariant(r)
local weird=setmetatable({}, {__index=function()error('field fault')end})
r=M.observe(weird);eq(r.status,'ACTION_UNKNOWN');invariant(r)
local fake={status='CURRENT_ACTION_ID_OBSERVED',current_action_id=0,queue_empty=true,
  manual_command=false,action_origin_verified=true,verified=true}
local a=M.arbitrate({orders_sent=0},fake)
eq(a.status,'HOLD');eq(a.allow_engine_action,false);eq(a.verified_queue_empty,false)
a=M.arbitrate({orders_sent=1},fake)
eq(a.status,'HOLD');eq(a.reason,'ADVISORY_NOT_TRUSTED')
eq(M.installed,false)
local q0=M.observe({m_curAction={m_actionID=0},m_queuedActions={m_nCount=0}})
eq(q0.queue_count_raw,0)
eq(q0.queue_count_observed,true)
eq(q0.queue_nonempty_observed,false)
eq(q0.queue_count_read_status,'RAW_QUEUE_COUNT_STABLE')
invariant(q0)
local q5=M.observe({m_curAction={m_actionID=23},m_queuedActions={m_nCount=5}})
eq(q5.queue_count_raw,5)
eq(q5.queue_nonempty_observed,true)
eq(q5.queue_count_observed,true)
invariant(q5)
local qmiss=M.observe({m_curAction={m_actionID=0}})
eq(qmiss.queue_count_raw,nil)
eq(qmiss.queue_count_observed,false)
eq(qmiss.queue_count_read_status,'QUEUE_COUNT_NOT_READABLE')
invariant(qmiss)
for _,bad in ipairs({-1,0.5,513,65535,false,'0',math.huge}) do
 local x=M.observe({m_curAction={m_actionID=0},m_queuedActions={m_nCount=bad}})
 eq(x.queue_count_raw,nil);eq(x.queue_count_observed,false)
 invariant(x)
end
local n=0
local moving={m_curAction={m_actionID=0},m_queuedActions=setmetatable({},{__index=function(_,k)
 if k=='m_nCount' then n=n+1;return n end
end})}
local changed=M.observe(moving)
eq(changed.queue_count_raw,nil)
eq(changed.queue_count_read_status,'QUEUE_COUNT_CHANGED_DURING_READ')
invariant(changed)
local e=0
local actionChanging=setmetatable({}, {__index=function(_,k)
 if k=='m_curAction' then e=e+1;return {m_actionID=e} end
 if k=='m_queuedActions' then return {m_nCount=0} end
end})
local movingAction=M.observe(actionChanging)
eq(movingAction.status,'ACTION_UNKNOWN')
eq(movingAction.reason,'ACTION_CHANGED_DURING_QUEUE_SNAPSHOT')
eq(movingAction.queue_count_raw,nil)
invariant(movingAction)
local p=M.arbitrate({orders_sent=0},q0)
eq(p.allow_engine_action,false)
eq(p.verified_queue_empty,false)
eq(p.verified_origin,false)
print('BGXAI081 Lua: '..checks..' assertions PASS')
