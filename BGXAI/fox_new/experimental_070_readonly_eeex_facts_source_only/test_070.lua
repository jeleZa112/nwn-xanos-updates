-- Native Lua simulation, NOT an actual EEex/EET runtime test.
local R=dofile('BGXAI069_ROLE_OBSERVER.lua')
local M=dofile('BGXAI070_EEEX_FACTS_READONLY.lua')
local n=0
local function eq(a,b,label)
  if a~=b then error((label or 'eq')..': expected '..tostring(b)..', got '..tostring(a),2) end
  n=n+1
end
local function sprite(cls, kit, hp, maxhp, f, level1, level2, level3, poly, modal)
  local reads=0
  local obj={m_typeAI={m_Class=cls},m_baseStats={m_hitPoints=hp},
    m_derivedStats={m_nKit=kit,m_nMaxHitPoints=maxhp,
      m_nLevel1=level1,m_nLevel2=level2,m_nLevel3=level3,
      m_bPolymorphed=poly},m_nModalState=modal}
  function obj:getLocalInt(key)
    eq(key,'BGX38_GUARD','read only F key');reads=reads+1;return f
  end
  function obj:setLocalInt() error('unsafe write detected') end
  function obj:Attack() error('unsafe attack detected') end
  return obj,function() return reads end
end
local sp,reads=sprite(11,0x4011,80,100,1,17,0,0,1,0)
local snap=M.snapshot(sp)
eq(snap.status,'RAW_READ_ONLY_NO_VERIFICATION','snap status')
eq(snap.class_id,11,'class')
eq(snap.hp_percent,80,'hp')
eq(snap.guard_toggle,1,'guard')
eq(snap.kit_raw,0x4011,'kit raw')
eq(snap.kit_verified,false,'kit unverified')
eq(snap.kit_name,'UNKNOWN','kit name unknown')
eq(snap.polymorph_raw,1,'polymorph raw')
eq(snap.form_verified,false,'form not claimed')
eq(snap.form_name,'UNKNOWN','form unknown')
eq(snap.dual_state,'UNKNOWN','dual unknown')
eq(snap.dual_verified,false,'dual unverified')
eq(snap.levels[1],17,'level1')
eq(snap.levels[2],0,'level2')
eq(snap.levels[3],0,'level3')
eq(snap.modal_raw,0,'modal raw')
eq(snap.action_queue_verified,false,'no action inference')
eq(snap.engine_orders_sent,0,'no engine orders')
eq(snap.hook_registered,false,'no hooks')
eq(reads(),1,'one F read')
local facts=M.facts_for_069(snap)
for _,k in ipairs({'kit','form','healing','actions','combat'}) do
  eq(facts[k].verified,false,'unverified '..k)
end
eq(facts.dual,nil,'unconfirmed dual must not pretend dual-class')
local both=M.inspect(sp,R)
eq(both.orders_sent,0,'integrated no orders')
eq(both.role_advice.orders_sent,0,'role no orders')
eq(both.role_advice.possible_interceptor,false,'Shapeshifter without verified form cannot auto-guard')
eq(both.role_advice.possible_healer,false,'no verified spell')
eq(both.snapshot.class_id,11,'integration raw class')
local fighter=sprite(2,0,70,100,1,10,0,0,0,0)
local fa=M.inspect(fighter,R)
eq(fa.role_advice.possible_interceptor,false,'fighter still NO action verification')
eq(fa.role_advice.reason,'ACTIONS_UNVERIFIED','unknown action queue')
local restored=sprite(1,0,90,100,1,13,14,0,0,0)
local ra=M.inspect(restored,R)
eq(ra.role_advice.possible_interceptor,false,'unproven restored dual')
eq(ra.snapshot.dual_verified,false,'raw levels not dual proof')
for cls=1,21 do
  local c=sprite(cls,0,95,100,1,1,0,0,0,0)
  local p=M.inspect(c,R)
  eq(p.snapshot.class_id,cls,'id '..cls)
  eq(p.role_advice.possible_interceptor,false,'no class alone dispatch '..cls)
  eq(p.orders_sent,0,'no engine order '..cls)
end
for _,id in ipairs({0,-1,22,100,256,'2',nil}) do
  local c=sprite(id,0,95,100,1,1,0,0,0,0)
  local p=M.inspect(c,R)
  eq(p.snapshot.class_id,nil,'invalid class')
  eq(p.role_advice.possible_interceptor,false,'invalid cannot dispatch')
end
for _,k in ipairs({-1,4294967296,'0',true,1.5}) do
  local p=M.snapshot(sprite(2,k,90,100,1,1,0,0,0,0))
  eq(p.kit_raw,nil,'invalid raw kit')
  eq(p.kit_verified,false,'kit never inferred')
end
for _,hp in ipairs({-1,101,0/0,math.huge}) do
  local p=M.snapshot(sprite(2,0,hp,100,1,1,0,0,0,0))
  eq(p.hp_percent,nil,'invalid HP')
end
for _,v in ipairs({-1,65536,1.5,'4',false}) do
  local p=M.snapshot(sprite(2,0,90,100,1,v,v,v,0,0))
  eq(p.levels_available[1],false,'invalid level1')
  eq(p.levels_available[2],false,'invalid level2')
  eq(p.levels_available[3],false,'invalid level3')
end
local missing=M.inspect({},R)
eq(missing.snapshot.class_id,nil,'missing class')
eq(missing.role_advice.possible_interceptor,false,'missing fields fail closed')
local no_obj=M.inspect(nil,R)
eq(no_obj.snapshot.guard_toggle,nil,'nil sprite safe')
eq(no_obj.role_advice.possible_interceptor,false,'nil fail closed')
local bad=setmetatable({},{__index=function() error('field read unavailable') end})
local inaccessible=M.inspect(bad,R)
eq(inaccessible.snapshot.class_id,nil,'crashing field read safe')
eq(inaccessible.role_advice.possible_interceptor,false,'crashing read fail closed')
local bad_guard=sprite(2,0,90,100,2,1,0,0,0,0)
eq(M.snapshot(bad_guard).guard_toggle,nil,'unexpected F state unknown')
local p=M.snapshot(sprite(2,0,90,100,1,1,0,0,3,0))
eq(p.polymorph_raw,nil,'unknown polymorph flag')
local plain=M.inspect(sprite(2,0,90,100,1,1,0,0,0,0),nil)
eq(plain.role_advice,nil,'optional 069 safe')
-- Test caller-provided, improperly verified facts don't enter the model via raw fields.
local sh2=sprite(11,0x4011,90,100,1,17,0,0,1,0)
local a=M.inspect(sh2,R)
eq(a.role_advice.kit_name,'UNKNOWN','raw kit never becomes verified name')
eq(a.role_advice.shape_melee_confirmed,false,'polymorph not transformed into werewolf')
print('BGXAI070_READONLY_LUA_TESTS_PASS '..n)
