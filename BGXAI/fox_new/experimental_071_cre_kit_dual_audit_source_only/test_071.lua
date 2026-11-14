-- Native Lua mock tests: never executed in real EET.
local M=dofile('BGXAI071_KIT_HINTS_READONLY.lua')
local A=dofile('BGXAI070_EEEX_FACTS_READONLY.lua')
local R=dofile('BGXAI069_ROLE_OBSERVER.lua')
local n=0
local function eq(a,b,label)
 if a~=b then error((label or '?')..': want '..tostring(b)..' got '..tostring(a),2) end
 n=n+1
end
local function sprite(cls, kit)
 return {m_typeAI={m_Class=cls},m_baseStats={m_hitPoints=100},
 m_derivedStats={m_nMaxHitPoints=100,m_nKit=kit},
 getLocalInt=function(_,key) if key=='BGX38_GUARD' then return 1 end end,
 setLocalInt=function() error('NO WRITES') end,
 Attack=function() error('NO ORDERS') end}
end
local samples={
 {2,0x40010000,'BERSERKER'},{2,0x40030000,'KENSAI'},
 {6,0x40040000,'CAVALIER'},{12,0x40070000,'ARCHER'},
 {4,0x400A0000,'ASSASSIN'},{5,0x400D0000,'BLADE'},
 {5,0x400F0000,'SKALD'},{11,0x40100000,'TOTEMIC_DRUID'},
 {11,0x40110000,'SHAPESHIFTER'},{11,0x40120000,'AVENGER'},
 {3,0x40150000,'LATHANDER'},{6,0x40200000,'BLACKGUARD'},
 {4,0x40210000,'SHADOWDANCER'},
 {2,0x40220000,'DWARVEN_DEFENDER'},
 {19,0x40230000,'DRAGON_DISCIPLE'},{20,0x40240000,'DARK_MOON'},
}
for _,s in ipairs(samples) do
 local raw=A.snapshot(sprite(s[1],s[2]))
 local x=M.hint(raw)
 eq(raw.kit_raw,s[2],'exact CRE raw')
 eq(x.kit_name_hint,s[3],'standard kit hint')
 eq(x.kit_verified,false,'never verified raw')
 eq(x.form_verified,false,'no form proof')
 eq(x.orders_sent,0,'no engine commands')
 local facts=M.hint_for_069(raw)
 eq(facts.kit.verified,false,'not a verified 069 kit')
 eq(facts.form.verified,false,'not verified shape')
 local advice=R.inspect(sprite(s[1],s[2]),facts)
 eq(advice.possible_interceptor,false,'no new F-guard authorization')
 eq(advice.orders_sent,0,'no guard order')
end
for _,id in ipairs({0,1,8,11,21,255}) do
 local h=M.hint(A.snapshot(sprite(id,0x40110000)))
 eq(h.kit_verified,false,'unknown class does not verify')
 eq(h.form_verified,false,'unknown class does not prove shape')
 if id~=11 then eq(h.kit_name_hint,'UNKNOWN','shapeshifter needs druid') end
end
for _,x in ipairs({0x4011,0x99990000,0x40000000,0,0x80000000,0x10000000}) do
 local h=M.hint(A.snapshot(sprite(11,x)))
 eq(h.kit_verified,false,'no raw verification on edge cases')
 eq(h.orders_sent,0,'no orders on edge cases')
end
eq(M.hint(A.snapshot(sprite(11,0x4011))).reason,'KIT_IDS_TOKEN_NOT_CRE_RAW','IDS vs CRE distinguish')
eq(M.hint(nil).reason,'SNAPSHOT_UNAVAILABLE','no sprite')
eq(M.hint({kit_raw='0x40110000',class_id=11}).reason,'RAW_KIT_UNAVAILABLE','string never acceptable')
eq(M.hint({kit_raw=0x40110000,class_id=16}).reason,'CLASS_KIT_FAMILY_MISMATCH','hybrid cannot assert single kit')
for i=1,21 do
 local s=A.snapshot(sprite(i,0x40110000)); local h=M.hint(s)
 eq(h.status,'ADVISORY_ONLY','all class advisory')
 eq(h.kit_verified,false,'no class kit authorized')
 eq(h.form_verified,false,'no class form authorized')
end
print('BGXAI071_NATIVE_LUA_PASS '..n)
