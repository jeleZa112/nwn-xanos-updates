# -*- coding: utf-8 -*-
import ctypes, ctypes.util, unittest
from pathlib import Path

src=Path(__file__).with_name('BG_EET_RU_V160_HIT_ONLY_APPEND.lua').read_bytes()

class LuaRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        name=ctypes.util.find_library('lua5.4')
        if not name:raise unittest.SkipTest('Lua 5.4 runtime not installed')
        cls.lua=ctypes.CDLL(name)
        cls.lua.luaL_newstate.restype=ctypes.c_void_p
        cls.lua.luaL_openlibs.argtypes=[ctypes.c_void_p]
        cls.lua.luaL_loadbufferx.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]
        cls.lua.luaL_loadbufferx.restype=ctypes.c_int
        cls.lua.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
        cls.lua.lua_pcallk.restype=ctypes.c_int
        cls.lua.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
        cls.lua.lua_tolstring.restype=ctypes.c_char_p
        cls.lua.lua_close.argtypes=[ctypes.c_void_p]
    def run_lua(self, code):
        L=self.lua.luaL_newstate();self.lua.luaL_openlibs(L)
        try:
            stat=self.lua.luaL_loadbufferx(L,code,len(code),b'bg_eet_ru_v160.lua',None)
            if stat:self.fail(self.lua.lua_tolstring(L,-1,None).decode(errors='replace'))
            stat=self.lua.lua_pcallk(L,0,0,0,0,None)
            if stat:self.fail(self.lua.lua_tolstring(L,-1,None).decode(errors='replace'))
        finally:self.lua.lua_close(L)

    def test_existing_callback_preserved_single_per_hit_message(self):
        mock=r'''
messages={}
oldcount=0
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
  oldcount=oldcount+1
  return 'ORIGINAL_RESULT'
end
-- Strictly test CItem binding model: mock userdata behavior without native pointers.
local original_type=type
function type(x)
  if original_type(x)=='table' and x.__as_userdata then return 'userdata' end
  return original_type(x)
end
local function obj(ref)
  return {__as_userdata=true,cResRef={get=function()return ref end}}
end
function Infinity_DisplayString(s) table.insert(messages,s) end
'''.encode('utf-8')
        tail=r'''
local hit=BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
assert(hit({weapon=obj('AROW01'),launcher=obj('BOW05')})=='ORIGINAL_RESULT')
assert(#messages==1 and messages[1]=='Оружие при попадании: Стрела (Короткий лук)')
assert(hit({weapon=obj('SW1H04')})=='ORIGINAL_RESULT')
assert(#messages==2 and messages[2]=='Оружие при попадании: Длинный меч')
assert(hit({weapon=obj('ABCD12')})=='ORIGINAL_RESULT')
assert(#messages==3 and messages[3]=='Оружие при попадании: код ABCD12')
assert(hit({weapon=obj('../bad')})=='ORIGINAL_RESULT')
assert(#messages==3)
assert(oldcount==4)
BG_EET_RU_V160_HIT.cap=3
assert(hit({weapon=obj('SW1H04')})=='ORIGINAL_RESULT')
assert(#messages==3 and BG_EET_RU_V160_HIT.reason=='SESSION_CAP')
'''.encode('utf-8')
        self.run_lua(mock+src+tail)

    def test_unavailable_display_api_silently_disables(self):
        mock=r'''
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(c) return 'OLD' end
'''.encode('utf-8')
        tail=r'''
assert(BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage({})=='OLD')
assert(BG_EET_RU_V160_HIT.reason=='DISPLAY_API_UNAVAILABLE')
assert(not BG_EET_RU_V160_HIT.enabled)
'''.encode('utf-8')
        self.run_lua(mock+src+tail)

    def test_display_failure_disables_and_recovers_busy(self):
        mock=r'''
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(c) return 7 end
local original_type=type
function type(x)
  if original_type(x)=='table' and x.__as_userdata then return 'userdata' end
  return original_type(x)
end
function Infinity_DisplayString(s)error('mock failure')end
'''.encode('utf-8')
        tail=r'''
local item={__as_userdata=true,cResRef={get=function()return 'SW1H04' end}}
assert(BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage({weapon=item})==7)
assert(BG_EET_RU_V160_HIT.reason=='DISPLAY_CALL_FAILED' and not BG_EET_RU_V160_HIT.busy)
assert(BG_EET_RU_V160_HIT.failed==1)
'''.encode('utf-8')
        self.run_lua(mock+src+tail)

if __name__=='__main__':unittest.main(verbosity=2)
