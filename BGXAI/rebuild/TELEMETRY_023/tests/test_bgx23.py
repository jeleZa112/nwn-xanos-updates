import ctypes, pathlib, re
ROOT=pathlib.Path(__file__).parents[1]
SRC=(ROOT/'src/M_BGX23.lua').read_text('utf-8')
L=ctypes.CDLL('liblua5.4.so.0')
L.luaL_newstate.restype=ctypes.c_void_p
L.luaL_openlibs.argtypes=[ctypes.c_void_p]
L.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];L.luaL_loadstring.restype=ctypes.c_int
L.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];L.lua_pcallk.restype=ctypes.c_int
L.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];L.lua_tolstring.restype=ctypes.c_char_p
L.lua_close.argtypes=[ctypes.c_void_p]
def run(lua):
 s=L.luaL_newstate();L.luaL_openlibs(s)
 try:
  code=lua.encode('utf-8');err=L.luaL_loadstring(s,code)
  if not err:err=L.lua_pcallk(s,0,-1,0,0,None)
  if err:
   c=L.lua_tolstring(s,-1,None)
   raise AssertionError(c.decode(errors='replace') if c else str(err))
 finally:L.lua_close(s)
MOCK='''
LOG={}; print=function(s) LOG[#LOG+1]=tostring(s) end
function sprite(i,h,c)
 local s={m_id=i,m_pos={x=301,y=400},m_baseStats={m_hitPoints=h,m_class=c}}
 function s:getLocalInt(n) if n=='BDAI_SKILL_MODE' then return 3 end if n=='BDAI_ATTACK_MODE' then return 2 end return 0 end
 function s:countAllOfTypeStringInRange(s,r,los,unused)
   assert(s=='[EVILCUTOFF]' and r==448 and los==true);return 1
 end
 return s
end
p=sprite(139331661,10,4);q=sprite(1500001,9,7);outsider=sprite(1600001,14,2)
local ps={[0]=p,[1]=q}; EEex_Sprite_GetInPortrait=function(i)return ps[i]end
EEex_Action_AddSpriteStartedActionListener=function(f) CALLBACK=f end
EEex_Sprite_GetSelectedID=function() return p.m_id end
function a(id,target) return {m_actionID=id,m_dest={x=0,y=0},m_acteeID={m_Instance=target or -1}} end
'''
checks=0
def ok(label,lua):
 global checks
 run(MOCK+SRC+lua);checks+=1;print('PASS',label)
ok('Registration and party HP/position/flags', '''
assert(LOG[1]:find('REGISTERED'));CALLBACK(p,a(105,136316959));local t=LOG[#LOG]
assert(t:find('actor=A1 slot=1 action=105 hp=10 class=4'))
assert(t:find('pos=301,400'));assert(t:find('enemyLOS=1'))
assert(t:find('skill=3 atkMode=2'));assert(t:find('manual=UNKNOWN'))
assert(not t:find('139331661') and not t:find('136316959'))
''')
ok('Flee and bard song always recorded', '''
CALLBACK(p,a(105,136316959));CALLBACK(p,a(355,136316959));CALLBACK(q,a(296,-1))
assert(table.concat(LOG):find('action=355'));assert(table.concat(LOG):find('action=296'))
assert(table.concat(LOG):find('actor=A2 slot=2'))
''')
ok('Party and self target detection', '''
CALLBACK(p,a(105,p.m_id));assert(LOG[#LOG]:find('target=SELF'))
CALLBACK(p,a(105,q.m_id));assert(LOG[#LOG]:find('target=PARTY2'))
CALLBACK(p,a(105,3131238));assert(LOG[#LOG]:find('target=NONPARTY_UNVERIFIED'))
''')
ok('Only party actors observed', '''
local n=#LOG;CALLBACK(outsider,a(105,p.m_id));assert(#LOG==n)
''')
ok('Noisy actions throttled but critical actions not', '''
for i=1,24 do CALLBACK(p,a(269,-1)) end
local entries=0
for _,s in ipairs(LOG) do if s:find('OBS') then entries=entries+1 end end
assert(entries==3,entries) -- first, 12th, 24th
''')
ok('Missing data is UNKNOWN', '''
p.m_baseStats=nil;p.m_pos=nil;p.getLocalInt=nil;p.countAllOfTypeStringInRange=nil
CALLBACK(p,{m_actionID=355});local s=LOG[#LOG]
assert(s:find('hp=%?'));assert(s:find('enemyLOS=%?'))
assert(s:find('pos=%?,%?'));assert(s:find('target=UNKNOWN'))
''')
ok('Duplicate registration is rejected', '''
local l=#LOG; local old=CALLBACK
'''+SRC+'''assert(CALLBACK==old and #LOG==l+1 and LOG[#LOG]:find('ALREADY_REGISTERED'))
''')
ok('Rate limits avoid unlimited logs', '''
for i=1,4700 do CALLBACK(p,a(105,10000)) end
local n=#LOG;CALLBACK(p,a(105,10000));assert(#LOG==n)
''')
ok('Invalid portrait/mismatched actor rejected', '''
p.m_id=-5;CALLBACK(p,a(105,3));assert(LOG[#LOG]:find('REGISTERED'))
''')
run(MOCK+"EEex_Action_AddSpriteStartedActionListener=nil\n"+SRC+"assert(LOG[#LOG]:find('DISABLED'))")
checks+=1;print('PASS Missing required API is disabled')
assert not any(s in SRC for s in ('RunAwayFromNoLeaveArea(', 'AttackOneRound(', 'AttackReevaluate(', 'BattleSong(', 'SetGlobal(', 'setLocalInt(', 'MoveToPoint(', 'EEex_Action_Execute'))
checks+=1;print('PASS read-only no game-action / script-variable writes')
print('TOTAL',checks,'Lua runtime mock groups PASS')
