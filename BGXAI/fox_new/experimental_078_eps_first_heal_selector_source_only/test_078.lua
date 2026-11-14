local M = dofile('BGXAI078_HEAL_SELECTOR.lua')
local count=0
local function eq(a,b,msg)
  if a~=b then error((msg or 'check')..': expected '..tostring(b)..' got '..tostring(a),2) end
  count=count+1
end
local function event()
  return {type='CONFIRMED_HOSTILE_WEAPON_HIT',verified=true,party_victim=true,
   attacker_is_party=false,attacker_id=222,victim_id=333,hp_verified=true,
   hp_percent=20,existing_eps_heal_handling=false}
end
local function healer(id,slot,dist)
  return {id=id,slot=slot,in_party=true,guard_f_on=true,alive=true,
   same_area=true,can_act=true,role={verified=true,heal_capable=true},
   spell={verified=true,bcs_spell_id='CLERIC_CURE_LIGHT_WOUNDS',usable_now=true},
   target={verified=true,victim_id=333,visible=true,in_bcs_range_10=true},
   eps={verified=true,manual_command=false,casting=false,singing=false,
     detecting_traps=false,heal_pending=false,queue_empty=true,idle=true},
   request_pending=false,distance_verified=true,distance_sq=dist}
end
local function select(c,e,cfg)
  return M.select(e or event(),c,cfg or {opt_in=true})
end
local a,b,c=healer(10,2,1),healer(20,3,4),healer(30,4,9)
eq(select({a,b,c}).selected_id,10,'nearest viable')
eq(select({a,b,c}).status,'ADVISORY_HEAL_CANDIDATE_ONLY')
eq(select({a,b,c}).orders_sent,0,'no orders')
eq(select({a,b,c}).locals_written,0,'no locals')
eq(select({a,b,c}).engine_dispatch,false,'no dispatch')
local reasons={
 {key='guard_f_on',value=false,reason='NOT_AVAILABLE_FOR_F_GUARD_SUPPORT'},
 {key='same_area',value=false,reason='ACTOR_NOT_AVAILABLE'},
 {key='alive',value=false,reason='ACTOR_NOT_AVAILABLE'},
 {key='can_act',value=false,reason='ACTOR_NOT_AVAILABLE'},
 {key='request_pending',value=true,reason='REQUEST_ALREADY_PENDING_OR_UNKNOWN'},
 {key='distance_verified',value=false,reason='DISTANCE_UNKNOWN'},
 {key='distance_sq',value=-1,reason='DISTANCE_UNKNOWN'},
}
for _,case in ipairs(reasons) do
  local h=healer(10,2,1);h[case.key]=case.value
  local r=select({h,b});eq(r.selected_id,20,'fallback '..case.key)
  eq(r.rejected[case.reason],1,'reason '..case.key)
end
local nested={
 {'spell','usable_now',false,'NO_VERIFIED_USABLE_BCS_SPELL'},
 {'spell','verified',false,'NO_VERIFIED_USABLE_BCS_SPELL'},
 {'spell','bcs_spell_id','SPPR102','NO_VERIFIED_USABLE_BCS_SPELL'},
 {'target','in_bcs_range_10',false,'TARGET_NOT_REACHABLE_BY_BCS'},
 {'target','visible',false,'TARGET_NOT_REACHABLE_BY_BCS'},
 {'target','verified',false,'TARGET_NOT_REACHABLE_BY_BCS'},
 {'target','victim_id',555,'TARGET_NOT_REACHABLE_BY_BCS'},
 {'role','heal_capable',false,'NO_VERIFIED_HEAL_CAPABILITY'},
 {'role','verified',false,'NO_VERIFIED_HEAL_CAPABILITY'},
 {'eps','verified',false,'EPS_STATE_UNVERIFIED'},
 {'eps','manual_command',true,'EPS_PRIORITY_ACTION_ACTIVE'},
 {'eps','casting',true,'EPS_PRIORITY_ACTION_ACTIVE'},
 {'eps','singing',true,'EPS_PRIORITY_ACTION_ACTIVE'},
 {'eps','detecting_traps',true,'EPS_PRIORITY_ACTION_ACTIVE'},
 {'eps','heal_pending',true,'EPS_PRIORITY_ACTION_ACTIVE'},
 {'eps','queue_empty',false,'EPS_QUEUE_BUSY_OR_UNKNOWN'},
 {'eps','idle',false,'EPS_QUEUE_BUSY_OR_UNKNOWN'},
}
for _,case in ipairs(nested) do
  local h=healer(10,2,1);h[case[1]][case[2]]=case[3]
  local r=select({h,b});eq(r.selected_id,20,'nested fallback '..case[1]..'.'..case[2]);
  eq(r.rejected[case[4]],1,'nested reason '..case[4])
end
-- Invalid/unknown values must fail closed; no confidence leaks.
for _,field in ipairs({'spell','role','target','eps'}) do
  local h=healer(10,2,1);h[field]=nil
  eq(select({h,b}).selected_id,20,'nil '..field)
end
for _,field in ipairs({'manual_command','casting','singing','detecting_traps','heal_pending','queue_empty','idle'}) do
  local h=healer(10,2,1);h.eps[field]=nil
  eq(select({h,b}).selected_id,20,'unknown EPS '..field)
end
local shaman=healer(42,2,1)
shaman.class_id=21
shaman.role.family='SHAMAN'
eq(select({shaman,b}).selected_id,42,'shaman permitted by verified spell not class whitelist')
local dual=healer(43,2,1);dual.class_id=1;dual.role.family='FIGHTER_TO_MAGE_RESTORED'
eq(select({dual,b}).selected_id,43,'restored dual with verified healing ability')
local shapeshifter=healer(44,2,1);shapeshifter.class_id=11;shapeshifter.role.heal_capable=false
eq(select({shapeshifter,b}).selected_id,20,'shapeshifter cannot auto-heal without verified spell capability')
local h=healer(10,2,1)
eq(select({h},event(),{opt_in=false}).reason,'OPT_IN_OFF')
eq(select({h},{verified=false}).reason,'UNCONFIRMED_HOSTILE_HIT')
local e=event();e.hp_percent=45;eq(select({h},e).reason,'NO_VERIFIED_HEAL_EMERGENCY')
e=event();e.hp_percent=0;eq(select({h},e).reason,'NO_VERIFIED_HEAL_EMERGENCY')
e=event();e.existing_eps_heal_handling=true;eq(select({h},e).reason,'EXISTING_EPS_HEAL_UNCONFIRMED_OR_ACTIVE')
e=event();e.existing_eps_heal_handling=nil;eq(select({h},e).reason,'EXISTING_EPS_HEAL_UNCONFIRMED_OR_ACTIVE')
e=event();e.attacker_is_party=true;eq(select({h},e).reason,'UNCONFIRMED_HOSTILE_HIT')
e=event();e.attacker_id=e.victim_id;eq(select({h},e).reason,'UNCONFIRMED_HOSTILE_HIT')
eq(select({}).reason,'NO_VERIFIED_USABLE_HEALER')
eq(select({h,h}).reason,'NO_GAME_DISPATCH_IMPLEMENTED') -- first remains viable; duplicate rejected
local t=select({h,h});eq(t.rejected.INVALID_OR_DUPLICATE_CANDIDATE,1)
local dup=healer(10,2,1)
eq(select({dup,healer(10,3,2),b}).selected_id,10)
eq(select({dup,healer(10,3,2),b}).rejected.INVALID_OR_DUPLICATE_CANDIDATE,1)
local e2=event();e2.hp_percent=44.99
local tie1=healer(10,3,100);local tie2=healer(11,2,100)
eq(select({tie1,tie2},e2).selected_id,11,'equal distance lower portrait slot')
local overflow={healer(1,1,1),healer(2,2,2),healer(3,3,3),healer(4,4,4),healer(5,5,5),healer(6,6,6),healer(7,6,7)}
eq(select(overflow).reason,'CANDIDATES_EXCEED_PARTY_SIZE')
for _,arg in ipairs({1,'x',true}) do eq(select(arg).reason,'INVALID_CANDIDATE_LIST') end
local before={h.distance_sq,h.eps.idle,h.spell.usable_now}
select({h,b});eq(h.distance_sq,before[1]);eq(h.eps.idle,before[2]);eq(h.spell.usable_now,before[3]);
print('BGXAI078_HEAL_SELECTOR_TESTS_PASS '..count)
