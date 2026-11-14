local P=dofile('BGXAI084_NATIVE_QUEUE_PROBE.lua')
local n=0
local function eq(a,b,msg)
 n=n+1;if a~=b then error((msg or 'assert')..': expected '..tostring(b)..' got '..tostring(a),2) end
end
local function deny(r)
 eq(r.safe_to_dispatch,false)
 eq(r.engine_dispatch,false)
 eq(r.orders_sent,0)
 eq(r.locals_written,0)
 eq(r.hooks_registered,0)
 eq(r.queue_empty_verified,false)
 eq(r.manual_command_verified,false)
 eq(r.origin_verified,false)
 eq(r.installed,false)
end
local c=0
local a={m_id=123,m_curAction={m_actionID=0}}
local ok=P.sample(a,function(t,s) c=c+1;eq(t,'ActionListEmpty()');eq(s,a);return true end)
eq(c,1);eq(ok.status,'NATIVE_TRIGGER_BOOLEAN_OBSERVED');eq(ok.queue_empty_sample,true)
eq(ok.trigger_boolean_observed,true);deny(ok)
local occupied=P.sample(a,function(t,s) return false end)
eq(occupied.queue_empty_sample,false);eq(occupied.trigger_boolean_observed,true);deny(occupied)
local broken=P.sample(a,function()error('untrusted evaluator exception')end)
eq(broken.reason,'NATIVE_EVALUATION_ERROR');eq(broken.queue_empty_sample,nil);deny(broken)
for _,v in ipairs({nil,0,1,'true',{},function()end}) do
 local r=P.sample(a,function()return v end)
 eq(r.reason,'NATIVE_EVALUATION_NON_BOOLEAN');deny(r)
end
local missing=P.sample(a,nil)
eq(missing.reason,'NATIVE_EVALUATOR_NOT_SUPPLIED');deny(missing)
local badid=0
for _,id in ipairs({-1,0,1.5,math.huge,0x100000000,'1',true}) do
 local r=P.sample({m_id=id},function()badid=badid+1;return true end)
 eq(r.reason,'INVALID_OR_UNREADABLE_ACTOR_ID');deny(r)
end
eq(badid,0)
local nilsprite=P.sample(nil,function()error('must not run')end)
eq(nilsprite.reason,'INVALID_OR_UNREADABLE_ACTOR_ID');deny(nilsprite)
local bridge=P.for_082(function()return true end)
local observed=bridge.observe(a)
eq(observed.queue_empty_sample,true)
eq(observed.queue_empty,nil)
eq(observed.queue_empty_verified,false)
eq(observed.safe_to_dispatch,false)
eq(observed.orders_sent,0)
eq(observed.locals_written,0)
eq(observed.hooks_registered,0)
local original=rawget(_G,'EEex_Trigger_EvalConditionalStringAsAIBase')
_G.EEex_Trigger_EvalConditionalStringAsAIBase=nil
local noapi=P.sample_from_eeex(a)
eq(noapi.reason,'EEEX117_NATIVE_EVALUATOR_UNAVAILABLE');deny(noapi)
_G.EEex_Trigger_EvalConditionalStringAsAIBase=function(t,s) eq(t,'ActionListEmpty()');return true end
local fromapi=P.sample_from_eeex(a)
eq(fromapi.queue_empty_sample,true);deny(fromapi)
_G.EEex_Trigger_EvalConditionalStringAsAIBase=original
print('BGXAI084_LUA_PASS '..n..' checks; no game files or commands')
