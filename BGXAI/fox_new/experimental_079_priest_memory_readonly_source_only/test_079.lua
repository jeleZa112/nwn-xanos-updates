local M=dofile('BGXAI079_PRIEST_MEMORY_READONLY.lua')
local n=0
local function eq(a,b,label)
 if a~=b then error((label or '')..' expected '..tostring(b)..' got '..tostring(a),2) end
 n=n+1
end
local function sprite(levels)
 return {m_memorizedSpellsPriest={getReference=function(_,i)return levels[i+1]end}}
end
local function api()
 return {iterate_list=function(list,fn) for _,e in ipairs(list) do fn(e) end end,
   resref_of=function(e)return e.ref end,
   bit0_unset=function(flags)return flags==0 end}
end
local levels={{ {ref='SPPR101',m_flags=1},{ref='SPPR101',m_flags=0} },{},{},{},{},{},{}}
local a=M.scan(sprite(levels),'SPPR101',api())
eq(a.status,'READ_ONLY_MEMORIZATION_OBSERVED')
eq(a.known_in_memory,true);eq(a.matched_memorizations,2);eq(a.unused_memorizations,1)
eq(a.visited,2);eq(a.castable_now_verified,false);eq(a.usable_now,nil)
eq(a.orders_sent,0);eq(a.locals_written,0)
local b=M.scan(sprite(levels),'SPPR102',api())
eq(b.known_in_memory,false);eq(b.unused_memorizations,0)
local c=M.scan(sprite({{ {ref='SPPR101',m_flags=0} },{},{},{},{},{},{}}),'SPPR101',api())
eq(c.known_in_memory,true);eq(c.unused_memorizations,0)
local d=M.scan(nil,'SPPR101',api());eq(d.status,'UNVERIFIED')
local e=M.scan(sprite(levels),'',api());eq(e.reason,'WANTED_RESREF_NOT_VERIFIED')
local f=M.scan(sprite(levels),'SPPR101',{});eq(f.reason,'EEEX_READER_UNAVAILABLE')
local g=M.scan(sprite({{},{},{},{},{},{}}),'SPPR101',api());eq(g.reason,'SPELL_LEVEL_POINTER_MISSING')
local h=M.scan(sprite({{{ref='SPPR101',m_flags='BAD'}},{},{},{},{},{},{}}),'SPPR101',api());eq(h.reason,'PRIEST_LIST_READ_INCOMPLETE')
local reader=api();reader.iterate_list=function()error('failed')end
local j=M.scan(sprite(levels),'SPPR101',reader);eq(j.reason,'PRIEST_LIST_READ_INCOMPLETE')
local malformed=M.scan({},'SPPR101',api());eq(malformed.reason,'PRIEST_MEMORIZED_LIST_UNKNOWN')
local upper=M.scan(sprite({{{ref='sppr101',m_flags=1}},{},{},{},{},{},{}}),'SPPR101',api())
eq(upper.unused_memorizations,1)
local big={}
for i=1,513 do big[#big+1]={ref='SPPR101',m_flags=1}end
local k=M.scan(sprite({big,{},{},{},{},{},{}}),'SPPR101',api());eq(k.reason,'PRIEST_LIST_READ_INCOMPLETE')
local missing=sprite(levels);missing.m_memorizedSpellsPriest={};
eq(M.scan(missing,'SPPR101',api()).reason,'PRIEST_LIST_METHOD_UNAVAILABLE')
local copy=M.scan(sprite(levels),'SPPR101',api());eq(copy.matched_memorizations,2)
-- Integration invariant: memorized unused does not authorize 078 actual healing.
local selector=dofile('BGXAI078_HEAL_SELECTOR.lua')
local fact=M.scan(sprite(levels),'SPPR101',api())
local proposed={id=10,slot=2,in_party=true,guard_f_on=true,alive=true,same_area=true,can_act=true,
 role={verified=true,heal_capable=true},
 spell={verified=fact.castable_now_verified,bcs_spell_id='CLERIC_CURE_LIGHT_WOUNDS',usable_now=fact.usable_now},
 target={verified=true,victim_id=333,visible=true,in_bcs_range_10=true},
 eps={verified=true,manual_command=false,casting=false,singing=false,detecting_traps=false,heal_pending=false,queue_empty=true,idle=true},
 request_pending=false,distance_verified=true,distance_sq=1}
local hit={type='CONFIRMED_HOSTILE_WEAPON_HIT',verified=true,party_victim=true,attacker_is_party=false,
 attacker_id=222,victim_id=333,hp_verified=true,hp_percent=20,existing_eps_heal_handling=false}
local response=selector.select(hit,{proposed},{opt_in=true})
eq(response.status,'NO_REQUEST','no live authorization from memory only')
eq(response.rejected.NO_VERIFIED_USABLE_BCS_SPELL,1,'unknown castability cannot authorize')
eq(response.orders_sent,0,'no commands ever')
print('BGXAI079_PRIEST_MEMORY_MOCK_PASS '..n)
