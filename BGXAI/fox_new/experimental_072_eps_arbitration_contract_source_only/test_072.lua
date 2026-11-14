-- Lua-native EPS-first contract tests. Synthetic inputs only; never EET.
local A=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')
local n=0
local function eq(g,w,label)
 if g~=w then error((label or '?')..': '..tostring(g)..' != '..tostring(w),2) end
 n=n+1
end
local function copy(x)
 local y={} for k,v in pairs(x) do y[k]=v end return y
end
local r={status='ADVISORY_ONLY',possible_interceptor=true,orders_sent=0,guard_toggle=1}
local t={verified=true,source='EEEX_EXPLICIT_ATTACK_ACTION',hostile=true,
 victim_is_party=true,attacker_is_party=false,same_area=true,
 attack_in_progress=true,attacker_id=150,victim_id=201}
local e={verified=true,manual_command=false,heal_pending=false,
 ally_in_critical_danger=false,casting=false,singing=false,
 detecting_traps=false,queue_empty=true,idle=true}
local p={verified=true,target_source='EXACT_RESOLVED_ATTACKER_ID',target_id=150}
local c={opt_in=true,smart_guard=true}
local function review(rr,tt,ee,pp,cc)
 return A.review(rr or r,tt or t,ee or e,pp or p,cc or c)
end
local x=review();eq(x.state,'CANDIDATE_REVIEW_ONLY','only safe synthetic scenario');
eq(x.allow_engine_action,false,'never dispatch');eq(x.engine_orders_sent,0,'no orders');
eq(x.confirmed_target_id,150,'specific attacker id not nearest enemy')
for _,k in ipairs({'opt_in','smart_guard'}) do
 local v=copy(c);v[k]=false
 eq(review(nil,nil,nil,nil,v).reason,'OPT_IN_OFF',k..' off')
end
eq(A.review(r,t,e,p,nil).reason,'OPT_IN_OFF','default opt in is off')
for _,k in ipairs({'possible_interceptor','status','orders_sent','guard_toggle'}) do
 local v=copy(r)
 if k=='possible_interceptor' then v[k]=false elseif k=='status' then v[k]='UNKNOWN'
 elseif k=='orders_sent' then v[k]=1 else v[k]=0 end
 eq(review(v).reason,'ROLE_UNVERIFIED_OR_F_OFF','role fail '..k)
end
for _,k in ipairs({'verified','source','hostile','victim_is_party','attacker_is_party',
 'same_area','attack_in_progress','attacker_id','victim_id'}) do
 local v=copy(t)
 if k=='verified' or k=='hostile' or k=='victim_is_party' or k=='same_area' or k=='attack_in_progress' then v[k]=false
 elseif k=='source' then v[k]='HIT_FROM_OTHER_SOURCE'
 elseif k=='attacker_is_party' then v[k]=true
 else v[k]=nil end
 eq(review(nil,v).reason,'REAL_ATTACKER_NOT_PROVED','threat fail '..k)
end
local same=copy(t);same.attacker_id=same.victim_id
eq(review(nil,same).reason,'REAL_ATTACKER_NOT_PROVED','self attack rejected')
local friendly=copy(t);friendly.attacker_is_party=true
eq(review(nil,friendly).reason,'REAL_ATTACKER_NOT_PROVED','friendly fire rejected')
for _,k in ipairs({'manual_command','heal_pending','ally_in_critical_danger',
 'casting','singing','detecting_traps','queue_empty','idle'}) do
 local v=copy(e)
 if k=='queue_empty' or k=='idle' then v[k]=false else v[k]=true end
 local out=review(nil,nil,v)
 eq(out.state,'HOLD','EPS blocks '..k)
 eq(out.engine_orders_sent,0,'no engine action '..k)
end
local unknown=copy(e);unknown.verified=false
eq(review(nil,nil,unknown).reason,'EPS_STATE_UNKNOWN','unknown EPS refuses')
for _,k in ipairs({'manual_command','heal_pending','ally_in_critical_danger',
 'casting','singing','detecting_traps','queue_empty','idle'}) do
 local v=copy(e);v[k]=nil
 local out=review(nil,nil,v)
 eq(out.state,'HOLD','unknown per EPS field hold '..k)
 eq(out.allow_engine_action,false,'no dispatch unknown '..k)
end
for _,k in ipairs({'verified','target_source','target_id'}) do
 local v=copy(p)
 if k=='verified' then v[k]=false elseif k=='target_source' then v[k]='NEAREST_ENEMY'
 else v[k]=151 end
 eq(review(nil,nil,nil,v).reason,'BCS_TARGET_NOT_EXACT_ATTACKER','bad BCS target '..k)
end
local original=review();eq(r.possible_interceptor,true,'input not mutated');
eq(e.queue_empty,true,'EPS not mutated');eq(p.target_id,150,'target not mutated');
eq(original.script_changes,0,'no BCS writes');eq(original.engine_orders_sent,0,'no game commands')
for _,k in ipairs({'','danger',7,nil}) do
 local v=copy(p);v.target_id=k
 eq(review(nil,nil,nil,v).allow_engine_action,false,'invalid target never dispatch')
end
print('BGXAI072_EPS_FIRST_LUA_PASS '..n)
