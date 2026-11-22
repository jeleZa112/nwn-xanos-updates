local M=dofile('BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE.lua')
local n=0
local function test(name,fn)
 local ok,err=pcall(fn)
 if not ok then error(name..': '..tostring(err)) end
 n=n+1;print('PASS R11 '..n..' '..name)
end
local function mock(slot,ability,hit,immune)
 local item={resref='SW1H04'}
 local items={get=function(_,index) if index==slot then return item end end}
 local source={m_equipment={m_selectedWeapon=slot,m_selectedWeaponAbility=ability,m_items=items}}
 local target={}
 local calls={hit=0,immune=0}
 local api={GetWeaponHitChance=function(s,t,w,a,off)
   assert(s==source and t==target and w==item and a==ability and off==false)
   calls.hit=calls.hit+1;return hit,'reason'
 end,IsImmuneToWeapon=function(s,t,k,w,a)
   assert(s==source and t==target and k==slot and w==item and a==ability)
   calls.immune=calls.immune+1;return immune
 end}
 local context={sessionId='Session_1',snapshotId='Frame_1',actor=11,
   targetActor=22,sequence=1,usesAlreadySelectedWeapon=true,
   readOnlyProbeConsent=true,manualEPSBoundaryProven=false,switchAttempted=false}
 return source,target,api,context,calls
end
local function safe(o)
 assert(o.executable==false and o.dispatchAuthorized==false and
  o.weaponSwitchAuthorized==false and o.ordersSent==0 and
  o.actionQueueCleared==false and o.currentActionPreserved==true and
  o.manualOrderProven==false and o.epsQueueProven==false and
  o.nativeEvidenceAuthenticated==false and o.liveReadVerified==false and
  o.alternateSlotAPRVerified==false and o.alternateSlotHitChanceVerified==false)
end
local s,t,a,c,calls=mock(35,0,70,false)
test('selected normal returns candidate only',function()
 local o=M.inspect(s,t,a,c);safe(o)
 assert(o.status=='SELECTED_HIT_CHANCE_CANDIDATE_ONLY' and o.hitChancePercent==70)
 assert(calls.hit==1 and calls.immune==1 and o.selectedSlot==35)
end)
test('candidate is never native proof',function()
 local o=M.inspect(s,t,a,c);safe(o)
 assert(o.engineMethodProvenInstalled==false and o.targetActorBindingProven==false)
end)
test('selected ammo does not prove bow',function()
 local x,y,z,k=mock(12,0,65,false)
 local o=M.inspect(x,y,z,k);safe(o)
 assert(o.launcherIdentityProven==false and o.selectedSlot==12)
end)
test('selected sword slot supports 38',function()
 local x,y,z,k=mock(38,1,95,false)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.selectedSlot==38)
end)
test('immune kept separate from hit chance',function()
 local x,y,z,k=mock(35,0,95,true)
 local o=M.inspect(x,y,z,k);safe(o)
 assert(o.hitChancePercent==95 and o.isImmuneToSelectedWeapon==true)
end)
test('missing source blocks',function()
 local o=M.inspect(nil,t,a,c);safe(o);assert(o.status=='HOLD')
end)
test('same source and target blocks',function()
 local o=M.inspect(s,s,a,c);safe(o);assert(o.status=='HOLD')
end)
test('unapproved read blocks before engine call',function()
 local x,y,z,k,counts=mock(35,0,70,false);k.readOnlyProbeConsent=false
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD' and counts.hit==0)
end)
test('manual boundary asserted true is rejected',function()
 local x,y,z,k=mock(35,0,70,false);k.manualEPSBoundaryProven=true
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('switchAttempted true blocks',function()
 local x,y,z,k=mock(35,0,70,false);k.switchAttempted=true
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('bad actor tuple blocks',function()
 local x,y,z,k=mock(35,0,70,false);k.targetActor=11
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid id blocks',function()
 local x,y,z,k=mock(35,0,70,false);k.sessionId='with spaces'
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('nil api blocks',function()
 local x,y,_,k=mock(35,0,70,false)
 local o=M.inspect(x,y,nil,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid function blocks',function()
 local x,y,z,k=mock(35,0,70,false);z.GetWeaponHitChance='bad'
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('unsupported equipment slot blocks',function()
 local x,y,z,k=mock(9,0,70,false)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('missing item blocks',function()
 local x,y,z,k=mock(35,0,70,false);x.m_equipment.m_items.get=function() return nil end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('hit API throws and hold',function()
 local x,y,z,k=mock(35,0,70,false);z.GetWeaponHitChance=function() error('bad') end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('immunity API throws and hold',function()
 local x,y,z,k=mock(35,0,70,false);z.IsImmuneToWeapon=function() error('bad') end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid hit 101 hold',function()
 local x,y,z,k=mock(35,0,101,false)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid hit negative hold',function()
 local x,y,z,k=mock(35,0,-1,false)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid hit fractional hold',function()
 local x,y,z,k=mock(35,0,14.5,false)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('invalid immunity integer hold',function()
 local x,y,z,k=mock(35,0,50,1)
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('selected changes during call blocks',function()
 local x,y,z,k=mock(35,0,50,false)
 z.GetWeaponHitChance=function() x.m_equipment.m_selectedWeapon=38;return 50 end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('selected ability changes during call blocks',function()
 local x,y,z,k=mock(35,0,50,false)
 z.GetWeaponHitChance=function() x.m_equipment.m_selectedWeaponAbility=3;return 50 end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('selected item object changes during call blocks',function()
 local x,y,z,k=mock(35,0,50,false)
 z.GetWeaponHitChance=function() x.m_equipment.m_items.get=function() return {} end;return 50 end
 local o=M.inspect(x,y,z,k);safe(o);assert(o.status=='HOLD')
end)
test('unchanged scene input on success',function()
 local x,y,z,k=mock(35,0,50,false)
 local slot=x.m_equipment.m_selectedWeapon
 local o=M.inspect(x,y,z,k);safe(o)
 assert(x.m_equipment.m_selectedWeapon==slot)
end)
test('no game API globally connected',function()
 assert(M.installed==false and _G.EEex==nil)
end)
print(('R11 total %d/%d PASS'):format(n,n))
