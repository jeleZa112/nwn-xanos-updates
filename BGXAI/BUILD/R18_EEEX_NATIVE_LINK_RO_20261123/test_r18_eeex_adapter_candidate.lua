local A=dofile('BGXAI_R18_EEEX_ADAPTER_CANDIDATE.lua')
local cases=0
local function case(n,f)
 cases=cases+1
 local ok,err=pcall(f)
 assert(ok,'FAIL '..n..': '..tostring(err))
end
local function eq(a,b)assert(a==b,tostring(a)..' vs '..tostring(b))end
local function item(ref)
 return {cResRef={get=function()return ref end},getAbility=function(self,i)
  if i==0 then return {mock_native_ability=true} end
  return nil
 end}
end
local arrow=item('AROW01')
local bow=item('BOW05')
local stats={m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=15,m_nDEX=16,
 m_nMeleeTHAC0Bonus=0,m_nMissileTHAC0Bonus=0,m_bImprovedHaste=0,m_nLuck=0}
EEex_Sprite_GetActiveStats=function()return stats end
local sprite={m_id=139266124,m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0,
 m_items={get=function(self,i)if i==12 then return arrow elseif i==36 then return bow end end}},
 getLauncher=function(self,ab)assert(ab.mock_native_ability);return bow,36 end}
local action={m_actionID=3,m_acteeID={m_Instance=135137293}}
case('event',function()
 local e=A.read_event(sprite,action)
 eq(e.actor,139266124);eq(e.target,135137293);eq(e.action,3)
end)
case('selection',function()
 local s=A.read_selection(sprite)
 eq(s.slot,12);eq(s.abilityIndex,0);eq(s.resref,'AROW01')
end)
case('ability',function()
 local a=A.read_ability(sprite,A.read_selection(sprite))
 eq(a.present,true);eq(a.handle.mock_native_ability,true)
end)
case('launcher',function()
 local s=A.read_selection(sprite)
 local a=A.read_ability(sprite,s)
 local l=A.read_launcher(sprite,s,a)
 eq(l.slot,36);eq(l.resref,'BOW05')
end)
case('stats',function()
 local x=A.read_stats(sprite)
 eq(x.m_nNumberOfAttacks,2);eq(x.m_nLuck,0)
end)
case('bad_ability',function()
 local s={slot=12,abilityIndex=5,resref='AROW01'}
 eq(A.read_ability(sprite,s),nil)
end)
case('bad_ref',function()
 local s={slot=12,abilityIndex=0,resref='SPOOF'}
 eq(A.read_ability(sprite,s),nil)
end)
case('empty_slot',function()
 sprite.m_equipment.m_selectedWeapon=13
 eq(A.read_selection(sprite).resref,nil)
 sprite.m_equipment.m_selectedWeapon=12
end)
case('fist',function()
 sprite.m_equipment.m_selectedWeapon=10
 eq(A.read_selection(sprite).slot,10)
 eq(A.read_ability(sprite,A.read_selection(sprite)),nil)
 sprite.m_equipment.m_selectedWeapon=12
end)
case('no_stats_function',function()
 local save=EEex_Sprite_GetActiveStats;EEex_Sprite_GetActiveStats=nil
 eq(A.read_stats(sprite),nil);EEex_Sprite_GetActiveStats=save
end)
case('bad_resref',function()
 local prev=arrow.cResRef.get;arrow.cResRef.get=function()return '../bad' end
 eq(A.read_selection(sprite).resref,nil)
 arrow.cResRef.get=prev
end)
case('no_launcher',function()
 sprite.getLauncher=function()return nil,-1 end
 eq(A.read_launcher(sprite,A.read_selection(sprite),A.read_ability(sprite,A.read_selection(sprite))),nil)
 sprite.getLauncher=function(self,ab)return bow,36 end
end)
print('BGXAI_R18_ADAPTER_LUA_MOCK_PASS',cases)
