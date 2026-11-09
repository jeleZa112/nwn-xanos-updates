from ctypes import CDLL, c_void_p, c_char_p, c_int, c_longlong
import ctypes.util
from pathlib import Path
import unittest

LUA = ctypes.util.find_library('lua5.4')
MOD = Path(__file__).resolve().parents[1] / 'M_BGX44Diag.lua'


@unittest.skipUnless(LUA,'System Lua 5.4 C runtime unavailable')
class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.lib=CDLL(LUA)
        self.lib.luaL_newstate.restype=c_void_p
        self.lib.luaL_openlibs.argtypes=[c_void_p]
        self.lib.luaL_loadstring.argtypes=[c_void_p,c_char_p];self.lib.luaL_loadstring.restype=c_int
        self.lib.lua_pcallk.argtypes=[c_void_p,c_int,c_int,c_int,c_longlong,c_void_p]
        self.lib.lua_pcallk.restype=c_int
        self.lib.lua_tolstring.argtypes=[c_void_p,c_int,c_void_p];self.lib.lua_tolstring.restype=c_char_p
        self.lib.lua_close.argtypes=[c_void_p]
        self.L=self.lib.luaL_newstate();self.lib.luaL_openlibs(self.L)
        self.eval('''
          registered = 0; message = nil; callback = nil; pressed = {}
          EEex_Key_AddPressedListener=function(f,r) callback=f; registered=registered+1 end
          EEex_Key_IsDown=function(k) return pressed[k] == true end
          Infinity_DisplayString=function(s) message=s end
          EEex_Action_AddSpriteStartedActionListener=function() end
          EEex_Sprite_GetInPortraitID=function() return -1 end
        ''')
        self.eval(MOD.read_text(encoding='utf-8'))
    def tearDown(self):self.lib.lua_close(self.L)
    def eval(self,s):
        b=s.encode('utf-8');rc=self.lib.luaL_loadstring(self.L,b)
        if rc==0:rc=self.lib.lua_pcallk(self.L,0,-1,0,0,None)
        if rc:
            raise AssertionError('Lua: '+str(self.lib.lua_tolstring(self.L,-1,None)))
    def get(self,code):
        self.eval('check_result=tostring('+code+')')
        self.lib.lua_getglobal.argtypes=[c_void_p,c_char_p];self.lib.lua_getglobal.restype=c_int
        self.lib.lua_getglobal(self.L,b'check_result')
        result=self.lib.lua_tolstring(self.L,-1,None).decode('utf-8')
        self.lib.lua_settop.argtypes=[c_void_p,c_int];self.lib.lua_settop(self.L,-2)
        return result
    def test_registered_once(self):
        self.assertEqual(self.get('registered'),'1')
        self.eval(MOD.read_text(encoding='utf-8'))
        self.assertEqual(self.get('registered'),'1')
    def test_not_triggered_by_plain_f11(self):
        self.eval('callback(0x40000044)')
        self.assertEqual(self.get('BGX44Diag.pressCount'),'0')
        self.assertEqual(self.get('message'),'nil')
    def test_ctrl_alt_f11_reports_unloaded(self):
        self.eval('pressed[0x400000E0]=true;pressed[0x400000E2]=true;callback(0x40000044)')
        self.assertIn('loaded=false',self.get('message'))
        self.assertIn('listener=false',self.get('message'))
        self.assertEqual(self.get('BGX44Diag.pressCount'),'1')
    def test_loaded_event_counts(self):
        self.eval('''BGX43Probe={installed=true,enabled=true,events={{},{}},errors=0,firstNoticeShown=false};
          pressed[0x400000E4]=true;pressed[0x400000E6]=true;callback(0x40000044)''')
        self.assertIn('loaded=true',self.get('message'))
        self.assertIn('attacks=2',self.get('message'))
        self.assertIn('listener=true',self.get('message'))
    def test_never_consumes_input(self):
        self.eval('pressed[0x400000E0]=true;pressed[0x400000E2]=true;consumed=callback(0x40000044)')
        self.assertEqual(self.get('consumed'),'false')
    def test_display_missing_does_not_crash(self):
        self.eval('Infinity_DisplayString=nil;pressed[0x400000E0]=true;pressed[0x400000E2]=true;callback(0x40000044)')
        self.assertEqual(self.get('BGX44Diag.lastError'),'DISPLAY_API_UNAVAILABLE')


if __name__=='__main__':unittest.main()
