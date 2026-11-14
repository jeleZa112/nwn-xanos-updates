-- Integration with real saved 082 source. Does not call EEex or edit the game.
local t83=dofile('BGXAI083_PASSIVE_TRACE.lua')
local dir=assert(os.getenv('BGXAI082_SOURCE_DIR'), 'Set BGXAI082_SOURCE_DIR to existing verified 082 source folder')
local b82=dofile(dir..'/BGXAI082_QUEUE_GUARD_BRIDGE.lua')
local o81=dofile(dir..'/BGXAI081_ACTION_PROVENANCE_READONLY.lua')
local coord=dofile(dir..'/BGXAI080_EPS_FIRST_COORDINATOR.lua')
local h78=dofile(dir..'/BGXAI078_HEAL_SELECTOR.lua')
local g72=dofile(dir..'/BGXAI072_EPS_FIRST_ARBITER.lua')
local trace=t83.new(8)
local tests=0
local function check(ok,reason)
 tests=tests+1;assert(ok,reason or 'failed')
end
local event={verified=true,victim_id=500,attacker_id=700,heal_event={},threat={}}
local members={{id=100,slot=2,action_state={verified=true,origin_verified=true,queue_empty=true,idle=true},eps={verified=true,queue_empty=true,idle=true}},
 {id=200,slot=3,action_state={verified=true,origin_verified=true,queue_empty=true,idle=true},eps={verified=true,queue_empty=true,idle=true}}}
local deps={heal=h78,guard=g72}
for _,a in ipairs({0,3,31,105,134,65535}) do
 for _,b in ipairs({0,3,31,105,134,65535}) do
  local sprites={[100]={m_id=100,m_curAction={m_actionID=a}},[200]={m_id=200,m_curAction={m_actionID=b}}}
  local rec=b82.review(event,members,sprites,trace:for_082(),coord,deps,{opt_in=true})
  check(rec.status=='HOLD_NO_ENGINE_DISPATCH')
  check(rec.engine_dispatch==false)
  check(rec.orders_sent==0 and rec.locals_written==0)
  check(rec.heal_id==nil and rec.guard_id==nil)
 end
end
local snap=trace:copy()
check(snap.observations==72 and snap.dropped==64)
check(snap.queue_verifiable==false and snap.origin_verifiable==false)
check(members[1].action_state.verified==true)
check(members[2].action_state.queue_empty==true)
check(o81.installed==false and b82.installed==false)
print('BGXAI 083+082: '..tests..' Lua assertions PASS; EPS FIRST HOLD enforced')