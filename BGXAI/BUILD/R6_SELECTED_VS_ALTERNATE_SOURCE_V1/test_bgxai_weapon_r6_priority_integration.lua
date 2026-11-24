-- Repo-relative regression: never rely on another chat's /mnt/data paths.
local here=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local root=here..'../../../'
local priority=root..'BGXAI/patchsets/ranged_fighter_guarded_20261119/'
local r6=dofile(here..'BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua')
local r5=dofile(root..'BGXAI/BUILD/R4_R3_PRIORITY_SOURCE_V1/BGXAI_WEAPON_R4_PRIORITY_GATE_V1.lua')
local modules={
 current=dofile(priority..'BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua'),
 apr=dofile(priority..'BGXAI_WEAPON_APR_PROVENANCE_V5.lua'),
 effects=dofile(priority..'BGXAI_WEAPON_EFFECTS_V4.lua'),
 priority=dofile(priority..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua'),
 noninterrupt=dofile(priority..'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua')
}
local rows=dofile(here..'BGXAI_R6_LIVE_REDUCED_FIXTURE_20261122.lua')
local matrix={schema='BGXAI_WEAPON_R4_R3_LIVE_EVIDENCE_V1',
 status='SELECTED_HISTORICAL_APR_AND_ITEM_IDENTITY_OBSERVED_PRIORITY_HOLD',
 executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
 rankingGate={status='HOLD_COMPLETE_EFFECTIVE_SCENE_REQUIRED',cannotInferFromHistoricalSelectedAPRs=true},
 actors={{actorId=139266124,partyIndex=2,events=16}}}
local count=0
local function test(name,fn)count=count+1;fn();print('PASS '..count..' '..name)end
local function safe(x)
 assert(x.executable==false and x.dispatchAuthorized==false and x.weaponSwitchAuthorized==false)
 assert(x.currentActionPreserved==true and x.actionQueueCleared==false)
end
local staff,_=r6.observe(rows[1].r4,rows[1].r2,rows[1].r1)
local sword,_=r6.observe(rows[16].r4,rows[16].r2,rows[16].r1)
test('R6 current selection alone never a COMPLETE_EFFECTIVE_SCENE',function()
 local out=r5.preview(staff,nil,matrix,modules)
 safe(out);assert(out.reason=='CURRENT_EFFECTIVE_SCENE_NOT_PROVIDED')
end)
test('R6 sword selection alone never ranks alternate slots',function()
 local out=r5.step(sword,nil,matrix,modules)
 safe(out);assert(out.reason=='CURRENT_EFFECTIVE_SCENE_NOT_PROVIDED')
end)
test('Cannot conflate raw ammo with bow after R6 output',function()
 assert(sword.currentSelected.selectedRef=='SW1H04')
 local rawbow=r6.observe(rows[11].r4,rows[11].r2,rows[11].r1)
 assert(rawbow.currentSelected.selectedRef=='AROW01')
 assert(rawbow.currentSelected.launcherCandidate==nil)
end)
test('R6 forged frame alone cannot satisfy V3/V4/V5 completeness',function()
 local scene={frame={actorId='139266124',snapshotId='S',tick=1},actor={}}
 local out=r5.preview(scene,nil,matrix,modules)
 safe(out);assert(out.reason:find('CURRENT_STATS:SCENE_INCOMPLETE',1,true))
end)
test('R6 makes no game calls',function()
 assert(r6.installed==false)
end)
test('R5 makes no game calls',function()
 assert(r5.installed==false)
end)
test('R6 and R5 never grant dispatch by themselves',function()
 for _,o in ipairs({staff,sword}) do
  assert(o.dispatchAuthorized==false and o.weaponSwitchAuthorized==false)
  assert(o.targetStatsObserved==false and o.alternateSlotAPRVerified==false)
 end
end)
print('PASS R6 -> R5 existing source gate '..count..'/'..count)
