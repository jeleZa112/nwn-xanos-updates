local bridge=dofile("BGXAI/BUILD/WEAPON_INVENTORY_PREP_V2_R37_BRIDGE_20261126/BGXAI_R37_BACKPACK_BRIDGE_RO_V2.lua")
local passed=0
local function check(condition,label)
 assert(condition,label)
 passed=passed+1
end
local sample={schema="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",
 status="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE",
 sameLuaListenerInvocation=true,rawInventoryDoubleReadConsistent=true,
 selectedDerivedStatsDoubleReadConsistent=true,readOnly=true,ordersSent=0,
 dispatchAuthorized=false,weaponSwitchAuthorized=false,actor=123,partyIndex=2}
local function observe(_)
 local items={}
 for i=15,34 do items[i]={slot=i,status="EMPTY"} end
 items[18]={slot=18,status="PRESENT_RAW",resref="HAMM01",
  flagsRaw=0,useCount1Raw=1,useCount2Raw=0,useCount3Raw=0}
 return {status="RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN",
   actorId=123,slots=items}
end
local inv={observe=observe}
local function verify(r,label)
 check(r.readOnly==true and r.sourceOnly==true and
  r.ordersSent==0 and r.localsWritten==0 and
  r.dispatchAuthorized==false and r.weaponSwitchAuthorized==false and
  r.inventoryMoveAuthorized==false and r.safeActionBoundaryVerified==false,label)
end
local r=bridge.capture({},sample,inv)
check(r.status=="R37_BACKPACK_DOUBLE_CAPTURE_STABLE_ADVICE_ONLY","stable result")
check(r.snapshot.slots[18].resref=="HAMM01","sample resref")
check(r.itemInstanceIdentityVerified==false and
 r.fullEquipmentUniquenessVerified==false and
 r.cachedAdvisoryCanBeExecuted==false,"cannot authorize")
verify(r,"zero orders")
local bad={}
for k,v in pairs(sample) do bad[k]=v end
bad.ordersSent=1
r=bridge.capture({},bad,inv)
check(r.status=="HOLD_R37_CONTRACT_NOT_MET","reject dispatch prior")
verify(r,"reject cannot dispatch")
bad.ordersSent=0
bad.actor=124
r=bridge.capture({},bad,inv)
check(r.status=="HOLD_BACKPACK_CAPTURE_INVALID","actor mismatch")
verify(r,"actor mismatch cannot dispatch")
local count=0
r=bridge.capture({},sample,{observe=function(sprite)
 count=count+1
 local s=observe(sprite)
 if count==2 then s.slots[18].useCount1Raw=2 end
 return s
end})
check(r.status=="HOLD_BACKPACK_CHANGED_DURING_CAPTURE" and r.unstableSlot==18,
 "raw drift")
verify(r,"drift cannot dispatch")
r=bridge.capture({},sample,{observe=function() error("engine fail") end})
check(r.status=="HOLD_BACKPACK_READ_ERROR","read errors")
verify(r,"read failure cannot dispatch")
r=bridge.capture({},sample,{observe=function(sprite)
 local s=observe(sprite)
 s.slots[20]={slot=20,status="PRESENT_RAW",resref="HAMM01",
  flagsRaw=0,useCount1Raw=1,useCount2Raw=0,useCount3Raw=0}
 return s
end})
check(r.duplicateBackpackResrefObserved==true and
 r.fullEquipmentUniquenessVerified==false,"duplicate flagged")
verify(r,"duplicate cannot dispatch")
r=bridge.capture({},sample,{observe=function(sprite)
 local s=observe(sprite)
 s.slots[18]={slot=18,status="PRESENT_UNVERIFIED"}
 return s
end})
check(r.status=="HOLD_UNVERIFIED_ITEM_STATE","unverified item")
verify(r,"unverified cannot dispatch")
print("BGXAI R37 backpack bridge source-only: "..passed.." checks PASS")
