-- Run luahbtex --luaonly test_bgxai_weapon_r4_priority_gate_v1.lua
local gate=dofile('BGXAI_WEAPON_R4_PRIORITY_GATE_V1.lua')
local root='/mnt/data/bgxai_weapon_r4/'
local deps={current=dofile(root..'BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua'),
 apr=dofile(root..'BGXAI_WEAPON_APR_PROVENANCE_V5.lua'),
 effects=dofile(root..'BGXAI_WEAPON_EFFECTS_V4.lua'),
 priority=dofile(root..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua'),
 noninterrupt=dofile(root..'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua')}
local COUNT=0
local function check(desc,fn)
 COUNT=COUNT+1;fn();print('PASS '..COUNT..' '..desc)
end
local evidence={schema='BGXAI_WEAPON_R4_R3_LIVE_EVIDENCE_V1',
 status='SELECTED_HISTORICAL_APR_AND_ITEM_IDENTITY_OBSERVED_PRIORITY_HOLD',
 executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
 rankingGate={status='HOLD_COMPLETE_EFFECTIVE_SCENE_REQUIRED',
  cannotInferFromHistoricalSelectedAPRs=true},
 actors={{actorId=139266124,partyIndex=2,events=16}}}
local function scene() return {frame={actorId='139266124'},actor={}}
end
local function assert_safe(r)
 assert(type(r)=='table');assert(r.executable==false)
 assert(r.dispatchAuthorized==false)
 assert(r.weaponSwitchAuthorized==false)
 assert(r.currentActionPreserved==true)
 assert(r.ordersSent==0);assert(r.actionQueueCleared==false)
end
check('actual R4 history cannot supply absent effective scene',function()
 local r=gate.preview(nil,nil,evidence,deps)
 assert_safe(r);assert(r.reason=='CURRENT_EFFECTIVE_SCENE_NOT_PROVIDED')
end)
check('current stats bridge is authoritative over sampled APR',function()
 local r=gate.preview(scene(),nil,evidence,deps)
 assert_safe(r);assert(r.reason:match('CURRENT_STATS:SCENE_INCOMPLETE'))
end)
check('noninterrupt step preserves current action and no orders',function()
 local r=gate.step(scene(),nil,evidence,deps)
 assert_safe(r);assert(r.status=='HOLD_EVIDENCE_BEFORE_PRIORITY')
end)
check('actor mismatch fail closed',function()
 local a=scene();a.frame.actorId='139724883'
 local r=gate.preview(a,nil,evidence,deps)
 assert_safe(r);assert(r.reason=='HISTORICAL_R4_R3_ACTOR_OR_SOURCE_MISMATCH')
end)
check('force dispatch true in report cannot elevate history',function()
 local fake=dofile('BGXAI_WEAPON_R4_PRIORITY_GATE_V1.lua')
 local bad={};for k,v in pairs(evidence) do bad[k]=v end
 bad.dispatchAuthorized=true
 local r=fake.preview(scene(),nil,bad,deps)
 assert_safe(r);assert(r.reason=='HISTORICAL_R4_R3_ACTOR_OR_SOURCE_MISMATCH')
end)
check('fake COMPLETE_EFFECTIVE scene status in history refused',function()
 local bad={};for k,v in pairs(evidence) do bad[k]=v end
 bad.status='COMPLETE_EFFECTIVE_SCENE'
 local r=gate.step(scene(),nil,bad,deps)
 assert_safe(r)
end)
check('missing V3 module prevents advisory',function()
 local other={};for k,v in pairs(deps) do other[k]=v end
 other.priority=nil
 local r=gate.preview(scene(),nil,evidence,other)
 assert_safe(r);assert(r.reason=='AUDITED_SOURCE_ONLY_MODULES_MISSING')
end)
check('fake old per-slot APR not enough for current gate',function()
 local s=scene();s.frame.snapshotId='S';s.frame.tick=1
 s.weapons={{id='SW1H04',apr=1.5,finalTHAC0=20,avgDamageOnHit=4.5},
            {id='BOW05',apr=2,finalTHAC0=20,avgDamageOnHit=3.5}}
 local r=gate.step(s,nil,evidence,deps)
 assert_safe(r)
end)
check('no module issues gameplay actions or has install flag',function()
 assert(gate.installed==false)
 assert(gate.version=='BGXAI_WEAPON_R4_PRIORITY_GATE_V1')
end)
print('PASS R4 PRIORITY SOURCE GATE '..COUNT..'/'..COUNT)
