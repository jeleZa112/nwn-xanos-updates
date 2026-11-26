local M=dofile("BGXAI/BUILD/WEAPON_INVENTORY_CONSERVATION_V1_20261126/BGXAI_TRANSFER_CONSERVATION_RO_V1.lua")
local n=0
local function t(name,fn)
 local ok,err=pcall(fn);assert(ok,name..": "..tostring(err));n=n+1;print("PASS "..name)
end
local function item(s,r,count)
 return {slot=s,status="PRESENT_RAW",resref=r,flagsRaw=1,
  useCount1Raw=count or 2,useCount2Raw=3,useCount3Raw=4}
end
local function snapshot()
 local x={status="TOPLEVEL_SLOTS_RAW_NOT_INSTANCE_PROOF",actorId=123,slots={}}
 for s=0,38 do x.slots[s]={slot=s,status="EMPTY"} end
 x.slots[18]=item(18,"HAMM01")
 x.slots[35]=item(35,"BOW05")
 x.slots[12]=item(12,"AROW01",22)
 return x
end
local function clone(x)
 local y={status=x.status,actorId=x.actorId,slots={}}
 for s,v in pairs(x.slots) do
  y.slots[s]={};for k,z in pairs(v) do y.slots[s][k]=z end
 end
 return y
end
local function data()
 local b=snapshot();local a=clone(b)
 a.slots[36]=a.slots[18];a.slots[36].slot=36
 -- Must mutate ONLY new snapshot to avoid corrupting before.
 a.slots[18]={slot=18,status="EMPTY"}
 return b,a,{actorId=123,sourceSlot=18,targetSlot=36,resref="HAMM01"}
end
local function check(x)
 assert(x.ordersSent==0 and x.executable==false and x.dispatchAuthorized==false
 and x.inventoryMoveAuthorized==false and x.weaponSwitchAuthorized==false
 and x.rollbackAuthorized==false and x.gameModified==false
 and x.engineTransferSemanticsVerified==false and x.liveEvidenceVerified==false)
end
t("exact_item_move_conserves_all_slots",function()
 local b,a,e=data();local x=M.verify(b,a,e)
 assert(x.status=="OBSERVED_EXACT_TOPLEVEL_CONSERVATION_ADVICE_ONLY"
 and x.topLevelConservationMatches and x.itemFlagsAndChargesUnchanged)
 check(x)
end)
t("nil_fails_closed",function()
 local x=M.verify();assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("source_not_emptied",function()
 local b,a,e=data();a.slots[18]=item(18,"HAMM01")
 local x=M.verify(b,a,e);assert(x.status=="HOLD_SOURCE_NOT_EMPTIED");check(x)
end)
t("missing_destination",function()
 local b,a,e=data();a.slots[36]={slot=36,status="EMPTY"}
 local x=M.verify(b,a,e)
 assert(x.status=="HOLD_DESTINATION_ITEM_CHANGED_OR_MISSING");check(x)
end)
t("changed_charges",function()
 local b,a,e=data();a.slots[36].useCount1Raw=1
 local x=M.verify(b,a,e);assert(x.status=="HOLD_DESTINATION_ITEM_CHANGED_OR_MISSING");check(x)
end)
t("changed_flags",function()
 local b,a,e=data();a.slots[36].flagsRaw=9
 local x=M.verify(b,a,e);assert(x.status=="HOLD_DESTINATION_ITEM_CHANGED_OR_MISSING");check(x)
end)
t("unrelated_ammo_consumed",function()
 local b,a,e=data();a.slots[12].useCount1Raw=20
 local x=M.verify(b,a,e);assert(x.status=="HOLD_UNRELATED_ITEM_CHANGED" and x.unexpectedSlot==12);check(x)
end)
t("unrelated_shield_changed",function()
 local b,a,e=data();a.slots[9]=item(9,"SHLD03A")
 local x=M.verify(b,a,e);assert(x.status=="HOLD_UNRELATED_ITEM_CHANGED" and x.unexpectedSlot==9);check(x)
end)
t("cross_actor",function()
 local b,a,e=data();a.actorId=124
 local x=M.verify(b,a,e);assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("duplicate_same_resref",function()
 local b,a,e=data();b.slots[19]=item(19,"HAMM01");a.slots[19]=item(19,"HAMM01")
 local x=M.verify(b,a,e);assert(x.status=="HOLD_DUPLICATE_OR_UNPROVEN_INSTANCE");check(x)
end)
t("occupied_target",function()
 local b,a,e=data();b.slots[36]=item(36,"STAF01")
 local x=M.verify(b,a,e);assert(x.status=="HOLD_PRECONDITION_NOT_MET");check(x)
end)
t("bad_source_slot",function()
 local b,a,e=data();e.sourceSlot=15
 local x=M.verify(b,a,e);assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("bad_target_slot",function()
 local b,a,e=data();e.targetSlot=34
 local x=M.verify(b,a,e);assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("incomplete_equipment_map",function()
 local b,a,e=data();a.slots[17]=nil
 local x=M.verify(b,a,e);assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("unknown_item_fields",function()
 local b,a,e=data();a.slots[36].flagsRaw=nil
 local x=M.verify(b,a,e);assert(x.status=="HOLD_INCOMPLETE_OR_CROSS_ACTOR");check(x)
end)
t("unexpected_new_item",function()
 local b,a,e=data();a.slots[20]=item(20,"SW1H04")
 local x=M.verify(b,a,e);assert(x.status=="HOLD_UNRELATED_ITEM_CHANGED");check(x)
end)
print("BGXAI item conservation "..n.." pure model tests PASS")
