local root=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(root..'BGXAI081_ACTION_CONTEXT_READONLY_V3.lua')
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
 eq(r.orders_sent,0)
 eq(r.locals_written,0)
 eq(r.hooks_registered,0)
end
local sourceMap={[65536]='MOCore.bcs',[65537]='BALDUR.BCS',[65538]='UI'}
EEex_ReadLString=function(ptr,limit)
 local s=sourceMap[ptr]
 if s==nil then error('unknown pointer') end
 if #s>limit then return s:sub(1,limit) end
 return s
end
local function fixture()
 local action={m_actionID=23,m_source={m_pchData=65536}}
 local sprite={m_curAction=action,m_queuedActions={m_nCount=0},
  m_bInActionExecution=0,m_bNoInterrupt=0,m_curScriptNum=4,
  m_actionCount=2,m_interrupt=0,
  m_lOrderedBy={m_Instance=0},m_lOrderedBySent={m_Instance=0}}
 return sprite,action
end

-- A stable action source is observable as raw evidence, never classified.
local s,a=fixture()
local r=M.observe(s,a)
eq(r.status,'CURRENT_ACTION_CONTEXT_OBSERVED')
eq(r.current_action_id,23)
eq(r.queue_count_observed,true)
eq(r.queue_count_raw,0)
eq(r.queue_nonempty_observed,false)
eq(r.action_context_snapshot_stable,true)
eq(r.engine_action_execution_raw,0)
eq(r.engine_no_interrupt_raw,0)
eq(r.current_script_number_raw,4)
eq(r.action_count_raw,2)
eq(r.interrupt_raw,0)
eq(r.ordered_by_instance_raw,0)
eq(r.ordered_by_sent_instance_raw,0)
eq(r.action_source_stable,true)
eq(r.action_source_raw,'MOCore.bcs')
eq(r.action_source_read_status,'SOURCE_RAW_OBSERVED')
eq(r.action_source_semantics,'UNCLASSIFIED_CAI_ACTION_M_SOURCE')
invariant(r)

-- Non-empty queue is recorded but never converted to EPS/manual origin.
s,a=fixture();s.m_queuedActions.m_nCount=7
r=M.observe(s,a)
eq(r.queue_count_raw,7);eq(r.queue_nonempty_observed,true);invariant(r)

-- m_source may also be surfaced as a direct Lua string by a binding.
s,a=fixture();a.m_source='BALDUR.BCS'
r=M.observe(s,a)
eq(r.action_source_raw,'BALDUR.BCS');eq(r.action_source_stable,true);invariant(r)

-- Missing EEex reader / missing source is a bounded unknown, not an exception.
s,a=fixture();local saved=EEex_ReadLString;EEex_ReadLString=nil
r=M.observe(s,a)
eq(r.action_source_raw,nil);eq(r.action_source_stable,false)
eq(r.action_source_read_status,'EEEX_READLSTRING_UNAVAILABLE');invariant(r)
EEex_ReadLString=saved
s,a=fixture();a.m_source=nil
r=M.observe(s,a)
eq(r.action_source_raw,nil);eq(r.action_source_read_status,'ACTION_SOURCE_FIELD_UNAVAILABLE');invariant(r)

-- Null, noncanonical and invalid pointers are not dereferenced.
for _,ptr in ipairs({0,1,65535,140737488355328,-1,1.5,'65536',false}) do
 s,a=fixture();a.m_source={m_pchData=ptr}
 r=M.observe(s,a)
 eq(r.action_source_raw,nil);eq(r.action_source_stable,false)
 eq(r.action_source_read_status,'ACTION_SOURCE_POINTER_UNAVAILABLE');invariant(r)
end

-- Failed reader, empty, truncated and non-printable values fail closed.
s,a=fixture();EEex_ReadLString=function()error('reader failure')end
r=M.observe(s,a);eq(r.action_source_raw,nil);eq(r.action_source_read_status,'ACTION_SOURCE_READ_FAILED');invariant(r)
EEex_ReadLString=function()return '' end
r=M.observe(s,a);eq(r.action_source_read_status,'ACTION_SOURCE_EMPTY');invariant(r)
EEex_ReadLString=function()return string.rep('A',49) end
r=M.observe(s,a);eq(r.action_source_read_status,'ACTION_SOURCE_TRUNCATED');invariant(r)
EEex_ReadLString=function()return 'BAD\nSOURCE' end
r=M.observe(s,a);eq(r.action_source_read_status,'ACTION_SOURCE_NONPRINTABLE');invariant(r)
EEex_ReadLString=saved

-- Source changed across two reads: do not serialize either value as stable.
s,a=fixture();local n=0
EEex_ReadLString=function()n=n+1;return n==1 and 'MOCore.bcs' or 'BALDUR.BCS' end
r=M.observe(s,a)
eq(r.action_source_stable,false);eq(r.action_source_raw,nil)
eq(r.action_source_read_status,'ACTION_SOURCE_CHANGED_DURING_READ');invariant(r)
EEex_ReadLString=saved

-- Engine context changing during capture cannot be marked stable.
s,a=fixture();local flips=0;s.m_bNoInterrupt=nil
setmetatable(s,{__index=function(t,k)
 if k=='m_bNoInterrupt' then flips=flips+1;return flips%2 end
end})
r=M.observe(s,a)
eq(r.action_context_snapshot_stable,false)
eq(r.engine_no_interrupt_raw,nil);invariant(r)

-- Action ID mismatch / mutation invalidates queue and source snapshot.
s,a=fixture();a.m_actionID=24
r=M.observe(s,a)
eq(r.status,'ACTION_UNKNOWN');eq(r.current_action_id,nil)
eq(r.queue_count_observed,false);eq(r.action_source_raw,nil);invariant(r)
s,a=fixture();local calls=0
s.m_curAction=setmetatable({}, {__index=function(_,k)
 if k=='m_actionID' then calls=calls+1;return calls==1 and 23 or 24 end
end})
r=M.observe(s,a)
eq(r.status,'ACTION_UNKNOWN');eq(r.reason,'ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT');invariant(r)

-- Queue count instability stays unknown; zero is never inferred.
s,a=fixture();local q=0
s.m_queuedActions=setmetatable({}, {__index=function(_,k)
 if k=='m_nCount' then q=q+1;return q end
end})
r=M.observe(s,a)
eq(r.queue_count_observed,false);eq(r.queue_count_raw,nil)
eq(r.queue_nonempty_observed,nil);invariant(r)

-- Out-of-range context fields are unknown, not silently normalized.
s,a=fixture();s.m_bInActionExecution=2
r=M.observe(s,a)
eq(r.action_context_snapshot_stable,false);eq(r.engine_action_execution_raw,nil);invariant(r)

-- Arbitrary metadata can never authorize a command.
local forged={status='CURRENT_ACTION_CONTEXT_OBSERVED',current_action_id=0,
 action_source_raw='PLAYER',action_origin_verified=true,manual_command_verified=true,
 queue_empty=true,safe_to_dispatch=true}
local p=M.arbitrate({orders_sent=0},forged)
eq(p.status,'HOLD');eq(p.allow_engine_action,false)
eq(p.verified_origin,false);eq(p.verified_queue_empty,false)

print('BGXAI081 action-context V3: '..checks..' assertions PASS')
