-- Offline mock tests only; the source-only bridge cannot send orders.
local M=dofile("BGXAI/BUILD/WEAPON_INVENTORY_CORRECTED_V3_20261126/BGXAI_BACKPACK16_R37_RO_V3.lua")
local n=0
local function test(name,fn)
 local ok,e=pcall(fn);assert(ok,name..": "..tostring(e));n=n+1;print("PASS "..name)
end
local function check(r)
 assert(r.ordersSent==0 and r.dispatchAuthorized==false and
  r.weaponSwitchAuthorized==false and r.inventoryMoveAuthorized==false and
  r.cachedAdvisoryCanBeExecuted==false and r.gameModified==false)
end
local function item(id,count)
 return {cResRef={get=function()return id end},m_flags=1,
  m_useCount1=count or 0,m_useCount2=0,m_useCount3=0}
end
local function sprite()
 local t={ [18]=item("HAMM01",1),[15]=item("QUICK01"),
  [17]=item("QUICK03"),[34]=item("MAGIC01")}
 return {m_id=123,m_equipment={m_items={get=function(_,s)return t[s] end}}},t
end
local r37={schema="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",
 status="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE",
 readOnly=true,ordersSent=0,dispatchAuthorized=false,
 weaponSwitchAuthorized=false,sameLuaListenerInvocation=true,
 queueSnapshotStable=true,actionContextSnapshotStable=true,
 actor=123,partyIndex=2,actionRaw=105,selectedWeaponRaw=35,
 selectedAbilityRaw=0,queuedActionsRaw=0,currentScriptNumberRaw=3}
local function ctx()
 return {actorId=123,actionRaw=105,selectedWeaponRaw=35,
 selectedAbilityRaw=0,queuedActionsRaw=0,currentScriptNumberRaw=3}
end
test("observe_only_16_real_backpack",function()
 local s=sprite();local x=M.observe(s)
 assert(x.status=="BACKPACK16_RAW_NOT_INSTANCE_PROOF" and x.presentCount==1)
 assert(x.emptyCount==15 and x.slots[18].resref=="HAMM01")
 assert(x.slots[15]==nil and x.slots[17]==nil and x.slots[34]==nil)
 check(x)
end)
test("two_snapshots_and_postcontext",function()
 local s=sprite(); local k=0
 local out=M.capture(s,r37,function()k=k+1;return ctx()end)
 assert(k==2 and out.status=="BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY")
 check(out)
end)
test("reject_context_after_action_changes",function()
 local s=sprite();local k=0
 local out=M.capture(s,r37,function()
 k=k+1;local x=ctx();if k==2 then x.actionRaw=92 end;return x end)
 assert(out.status=="HOLD_CONTEXT_AFTER");check(out)
end)
test("reject_context_after_queue_changes",function()
 local s=sprite();local k=0
 local out=M.capture(s,r37,function()
 k=k+1;local x=ctx();if k==2 then x.queuedActionsRaw=1 end;return x end)
 assert(out.status=="HOLD_CONTEXT_AFTER");check(out)
end)
test("reject_context_after_weapon_changes",function()
 local s=sprite();local k=0
 local out=M.capture(s,r37,function()
 k=k+1;local x=ctx();if k==2 then x.selectedWeaponRaw=36 end;return x end)
 assert(out.status=="HOLD_CONTEXT_AFTER");check(out)
end)
test("reject_invalid_r37",function()
 local s=sprite();local c={}
 for k,v in pairs(r37) do c[k]=v end
 c.dispatchAuthorized=true
 local out=M.capture(s,c,ctx)
 assert(out.status=="HOLD_R37_CONTRACT");check(out)
end)
test("reject_unreadable_backpack",function()
 local s,t=sprite();t[18]={cResRef={get=function()return "HAMM01" end}}
 local out=M.observe(s)
 assert(out.status=="HOLD_BACKPACK16_UNREADABLE");check(out)
end)
test("drift_during_double_read",function()
 local s,t=sprite(); local rawget=s.m_equipment.m_items.get;local k=0
 s.m_equipment.m_items.get=function(self,slot)
  if slot==18 then k=k+1;if k==2 then t[18]=item("HAMM01",2) end end
  return rawget(self,slot)
 end
 local out=M.capture(s,r37,ctx)
 assert(out.status=="HOLD_BACKPACK_CHANGED");check(out)
end)
test("duplicate_same_resref_advisory_only",function()
 local s,t=sprite();t[19]=item("HAMM01",1)
 local out=M.capture(s,r37,ctx)
 assert(out.duplicateBackpackResrefObserved==true and
  out.fullEquipmentUniquenessVerified==false);check(out)
end)
test("exclude_quick_and_magic_unreadable",function()
 local s,t=sprite();t[15]={};t[34]={}
 local out=M.capture(s,r37,ctx)
 assert(out.status=="BACKPACK16_AND_R37_RAW_CONTEXT_STABLE_ADVICE_ONLY");check(out)
end)
test("reject_broken_context_reader",function()
 local s=sprite()
 local out=M.capture(s,r37,function() error("context failed")end)
 assert(out.status=="HOLD_CONTEXT_BEFORE");check(out)
end)
print("BGXAI corrected backpack V3 "..n.." mock tests PASS")
