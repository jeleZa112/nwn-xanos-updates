-- Native Lua model/EEex-mock tests. No actual game is used.
local R=dofile('BGXAI069_ROLE_OBSERVER.lua')
local passed=0
local function eq(got,want,description)
 if got~=want then error((description or 'mismatch')..' expected='..tostring(want)..' actual='..tostring(got),2) end
 passed=passed+1
end
local function sprite(cls,hp,maxhp,f)
 return {m_typeAI={m_Class=cls},m_baseStats={m_hitPoints=hp},
  m_derivedStats={m_nMaxHitPoints=maxhp},
  getLocalInt=function(self,key) if key=='BGX38_GUARD' then return f end end}
end
local function ready()
 return {actions={verified=true,manual=false,casting=false,singing=false,traps=false,heal_pending=false,idle=true},
   combat={verified=true,same_area=true,can_act=true,melee=true,survivability=true}}
end
local function run(cls,ctx,hp,f)
 return R.inspect(sprite(cls,hp or 90,100,f==nil and 1 or f),ctx or ready())
end
for i=1,21 do eq(R.class_name(i)=='UNKNOWN',false,'valid class '..i) end
eq(R.class_name(8),'FIGHTER_CLERIC','08 fighter cleric')
eq(R.class_name(11),'DRUID','11 druid')
eq(R.class_name(21),'SHAMAN','21 shaman')
for _,id in ipairs({0,22,99,-1}) do
 eq(R.class_name(id),'UNKNOWN','unknown class')
 eq(run(id).possible_interceptor,false,'unknown cannot guard')
end
for _,id in ipairs({2,6,7,8,9,10,12,16,17,18}) do
 eq(run(id).possible_interceptor,true,'martial candidate '..id)
 eq(run(id).orders_sent,0,'never order '..id)
end
for _,id in ipairs({1,3,4,5,11,13,14,15,19,20,21}) do
 eq(run(id).possible_interceptor,false,'support not forced '..id)
end
local d=ready()
d.dual={verified=true,old_class_id=2,old_active=true}
eq(run(1,d).possible_interceptor,true,'fighter to mage restored')
eq(run(1,{dual={old_class_id=2,old_active=true},actions=ready().actions,combat=ready().combat}).possible_interceptor,false,'dual unverified does not count')
d.dual={verified=true,old_class_id=2,old_active=false}
eq(run(1,d).possible_interceptor,false,'fighter to mage locked')
eq(run(2,d).possible_interceptor,false,'mage to fighter requires current active proof')
d.dual.current_martial_verified=true
eq(run(2,d).possible_interceptor,true,'mage to fighter current active verified')
local sh=ready()
sh.kit={verified=true,name='SHAPESHIFTER'}
eq(run(11,sh).possible_interceptor,false,'shapeshifter no shape does not guard')
sh.form={verified=true,name='WEREWOLF',melee_verified=true}
eq(run(11,sh).possible_interceptor,true,'shapeshifter verified werewolf')
sh.form.name='GREATER_WEREWOLF'
eq(run(11,sh).possible_interceptor,true,'greater werewolf')
sh.form.name='WOLF'
eq(run(11,sh).possible_interceptor,false,'other form must not assume')
sh.form.name='WEREWOLF';sh.kit.verified=false
eq(run(11,sh).possible_interceptor,false,'unverified kit must not assume')
local h=ready()
h.healing={verified=true,usable_now=true}
eq(run(21,h).possible_healer,true,'shaman healer ability verified')
eq(run(3,h).possible_healer,true,'cleric healer ability verified')
eq(run(8,h).possible_healer,true,'fighter cleric healer ability verified')
eq(run(1,h).possible_healer,false,'mage not healer by class')
h.healing.verified=false
eq(run(21,h).possible_healer,false,'unverified spell not assumed')
local b=ready()
b.actions.singing=true
eq(run(2,b).possible_interceptor,false,'song protected')
b.actions.singing=false;b.actions.manual=true
eq(run(2,b).possible_interceptor,false,'manual protected')
b.actions.manual=false;b.actions.heal_pending=true
eq(run(8,b).possible_interceptor,false,'heal before guard')
b=ready();b.actions.verified=false
eq(run(2,b).possible_interceptor,false,'unknown actions fail closed')
b=ready();b.combat.verified=false
eq(run(2,b).possible_interceptor,false,'unknown combat fail closed')
b=ready();b.combat.melee=false
eq(run(2,b).possible_interceptor,false,'unverified melee fail closed')
b=ready();b.combat.survivability=false
eq(run(2,b).possible_interceptor,false,'unverified survivability fail closed')
eq(run(2,ready(),60).possible_interceptor,false,'low hp fail closed')
eq(run(2,ready(),90,0).possible_interceptor,false,'f off')
eq(R.inspect(sprite(2,0,100,1),ready()).possible_interceptor,false,'dead')
eq(R.inspect(sprite(2,150,100,1),ready()).possible_interceptor,false,'invalid hp')
eq(R.inspect({},ready()).possible_interceptor,false,'missing EEex facts')
eq(R.inspect(nil,ready()).possible_interceptor,false,'nil sprite')
eq(run(2,ready()).status,'ADVISORY_ONLY','advisory')
eq(run(2,ready()).hook_registered,false,'no hooks')
print('BGXAI069_PASSIVE_LUA_TESTS_PASS '..passed)