local M=dofile('BGXAI081_ACTION_PROVENANCE_READONLY.lua')
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
print('BGXAI081 Lua: '..checks..' assertions PASS')
