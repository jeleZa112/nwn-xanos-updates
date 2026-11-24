local mod=dofile('BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua')
local rows=dofile('BGXAI_R6_LIVE_REDUCED_FIXTURE_20261122.lua')
assert(#rows==16)
local previous=nil
local rates={}
for i,record in ipairs(rows) do
 local r,p=mod.observe(record.r4,record.r2,record.r1,previous)
 assert(r.status=='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD',i..' '..tostring(r.reason))
 assert(r.actor==139266124 and r.partyIndex==2 and r.sequence==i)
 assert(r.executable==false and r.dispatchAuthorized==false and r.weaponSwitchAuthorized==false)
 assert(r.currentActionPreserved==true and r.actionQueueCleared==false)
 assert(r.alternateSlotAPRVerified==false)
 local raw=r.currentSelected.selectedRef
 local apr=r.selectedAPRDecoded
 rates[raw]=apr
 for _,quick in ipairs(r.quickslots) do
  assert(quick.effectiveAPRForUnselected==nil)
  assert(quick.activeBuffsFullyObserved==false and quick.perSlotEffectiveTHAC0Verified==false)
 end
 previous=p
end
assert(rates.STAF01==1 and rates.AROW01==2 and rates.SW1H04==1.5)
assert(rates.BOW05==nil) -- arrow selection does not independently prove active bow
-- Legacy R2 raw ammunition/count changes invalidate the previous history.
-- Standalone real recorded measurements still exist in `rates` above.
assert(previous.history.STAF01==nil)
assert(previous.history.AROW01==nil)
assert(previous.history.SW1H04.selectedAPRDecoded==1.5)
print('PASS R6 REAL 16/16 CORRELATION; ACTIVE LAUNCHER UNKNOWN; PER-ALTERNATE EFFECTIVE APR HOLD; NO DISPATCH')
