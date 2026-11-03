import ctypes, pathlib, re
SRC=pathlib.Path(__file__).with_name('M_BGX73.lua').read_text()
lua=ctypes.CDLL('liblua5.4.so.0')
lua.luaL_newstate.restype=ctypes.c_void_p
lua.luaL_openlibs.argtypes=[ctypes.c_void_p]
lua.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lua.luaL_loadstring.restype=ctypes.c_int
lua.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lua.lua_pcallk.restype=ctypes.c_int
lua.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
lua.lua_tolstring.restype=ctypes.c_char_p
lua.lua_close.argtypes=[ctypes.c_void_p]
def run(code):
 l=lua.luaL_newstate();lua.luaL_openlibs(l)
 err=lua.luaL_loadstring(l,code.encode())
 if not err:err=lua.lua_pcallk(l,0,-1,0,0,None)
 if err:
  msg=lua.lua_tolstring(l,-1,None)
  raise RuntimeError(msg.decode() if msg else f'Lua error {err}')
 lua.lua_close(l)
BASE='''
BGX73_TEST_LOG={}; local native_print=print
print=function(s) BGX73_TEST_LOG[#BGX73_TEST_LOG+1]=tostring(s) end
function makeSprite(id, hp, cls)
 local s={m_id=id,m_baseStats={m_class=cls,m_kit=2000,m_level1=3,m_level2=2,m_level3=0,m_hitPoints=hp}}
 function s:getLocalInt(name) if name=='BDAI_SKILL_MODE' then return 1 else return 0 end end
 function s:countAllOfTypeStringInRange(t,r,los,extra) if t~='[EVILCUTOFF]' or r~=448 or los~=true then error('bad args') end return 2 end
 return s
end
p1=makeSprite(501,25,7);p2=makeSprite(502,12,4);outsider=makeSprite(998,12,4)
local slots={[0]=p1,[1]=p2}
EEex_Sprite_GetInPortrait=function(i)return slots[i] end
EEex_Sprite_GetSelectedID=function() return 501 end
EEex_Action_AddSpriteStartedActionListener=function(fn) BGX73_HOOK=fn end
'''
run(BASE+SRC+'''\nassert(#BGX73_TEST_LOG==1,'registered');assert(BGX73_TEST_LOG[1]:find('REGISTERED'))
BGX73_HOOK(p1,{m_actionID=3});assert(#BGX73_TEST_LOG==2,'first observation')
assert(BGX73_TEST_LOG[2]:find('enemyLOS=2'))
assert(BGX73_TEST_LOG[2]:find('class=7'))
assert(BGX73_TEST_LOG[2]:find('BDAI='))
assert(BGX73_TEST_LOG[2]:find('selected=leader'))
BGX73_HOOK(outsider,{m_actionID=3});assert(#BGX73_TEST_LOG==2,'outsider ignored')
for i=2,19 do BGX73_HOOK(p1,{m_actionID=3}) end
assert(#BGX73_TEST_LOG==2,'throttled')
p1.m_baseStats.m_hitPoints=22;BGX73_HOOK(p1,{m_actionID=3});assert(#BGX73_TEST_LOG==3,'changes logged')
BGX73_HOOK(p2,{m_actionID=3});assert(BGX73_TEST_LOG[4]:find('slot=2'))
assert(not table.concat(BGX73_TEST_LOG):find('actor=501'),'no IDs')
assert(not table.concat(BGX73_TEST_LOG):find('actor=502'),'no IDs 2')
print('SUCCESS')
''')
print('PASS: registration, class, HP, BDAI, LOS count, selection, outsider filtered, throttling, change, 2nd member, no raw IDs')
run(BASE+'''EEex_Sprite_GetInPortrait=nil;'''+SRC+'''assert(BGX73_HOOK==nil);assert(BGX73_TEST_LOG[1]:find('DISABLED'))''')
print('PASS: missing EEex API fails closed')
run(BASE+'''p1.countAllOfTypeStringInRange=function()error('no method')end'''+SRC+'''BGX73_HOOK(p1,{m_actionID=3});assert(BGX73_TEST_LOG[2]:find('enemyLOS=%?'))''')
print('PASS: failure of line-of-sight probe remains UNKNOWN')
run(BASE+'''p1.m_baseStats=nil'''+SRC+'''BGX73_HOOK(p1,{m_actionID=3});assert(BGX73_TEST_LOG[2]:find('class=%?'))''')
print('PASS: missing stats remain UNKNOWN')
run(BASE+'''EEex_Action_AddSpriteStartedActionListener=function(fn) error('no hook') end'''+SRC+'''assert(BGX73_TEST_LOG[1]:find('DISABLED'))''')
print('PASS: hook registration exception fails closed')
run(BASE+SRC+SRC+'''assert(#BGX73_TEST_LOG==2);assert(BGX73_TEST_LOG[2]:find('ALREADY_REGISTERED'))''')
print('PASS: duplicate registration prevented')
print('PASS 17 observer groups')