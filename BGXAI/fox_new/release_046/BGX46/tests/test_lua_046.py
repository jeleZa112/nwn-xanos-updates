"""Offline EEex simulation, Lua 5.4 syntax and safe listener behavior."""
from pathlib import Path
import ctypes
import hashlib
import unittest

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'BGX46/M_BX43.lua'
PREV='f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f'

class LuaVM:
    def __init__(self):
        lib=ctypes.CDLL('liblua5.4.so.0')
        self.lib=lib
        lib.luaL_newstate.restype=ctypes.c_void_p
        lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
        lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        lib.luaL_loadstring.restype=ctypes.c_int
        lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
        lib.lua_pcallk.restype=ctypes.c_int
        lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
        lib.lua_tolstring.restype=ctypes.c_char_p
        lib.lua_settop.argtypes=[ctypes.c_void_p,ctypes.c_int]
        lib.lua_close.argtypes=[ctypes.c_void_p]
        self.L=lib.luaL_newstate();lib.luaL_openlibs(self.L)
    def run(self,s):
        code=s.encode()
        a=self.lib.luaL_loadstring(self.L,code)
        if a:raise AssertionError('Lua compile: '+str(self.lib.lua_tolstring(self.L,-1,None)))
        b=self.lib.lua_pcallk(self.L,0,0,0,0,None)
        if b:raise AssertionError('Lua runtime: '+str(self.lib.lua_tolstring(self.L,-1,None)))
    def close(self):self.lib.lua_close(self.L)

class LuaObserver(unittest.TestCase):
    def setUp(self):
        self.vm=LuaVM();self.addCleanup(self.vm.close)
        self.vm.run('''
            local ids = {[0]=141363308,[1]=141428845,[2]=141494382,[3]=141559919,[4]=-1,[5]=-1}
            function EEex_Sprite_GetInPortraitID(i) return ids[i] end
            function EEex_Action_AddSpriteStartedActionListener(f) _TEST_LISTENER=f end
            function Infinity_DisplayString(msg) _TEST_NOTICE=msg end
        ''')
        self.vm.run(SRC.read_text())
    def test_attack_reevaluate_shank(self):
        self.vm.run('''
          _TEST_LISTENER({m_id=777,m_pos={x=11,y=12}},
                         {m_actionID=134,m_acteeID={m_Instance=141363308}})
          assert(#BGX43Probe.events==1)
          assert(BGX43Probe.events[1].action_id==134)
          assert(BGX43Probe.events[1].target_id==141363308)
          local s=BGX43Probe.snapshot()
          assert(s.installed and s.action_listener and s.party_api)
          assert(s.attack_candidates==1 and s.seen_actions==1)
          assert(s.last_attack.reason=='recorded')
          s.events[1].action_id=1000
          assert(BGX43Probe.events[1].action_id==134)
        ''')
    def test_all_attack_family(self):
        self.vm.run('''
          for _,id in ipairs({3,94,98,105,134}) do
            _TEST_LISTENER({m_id=777,m_pos={}}, {m_actionID=id,m_acteeID={m_Instance=141363308}})
          end
          assert(#BGX43Probe.events==5)
          assert(BGX43Probe.attackCandidates==5)
        ''')
    def test_rejected_nonparty_and_invalid_targets(self):
        self.vm.run('''
          _TEST_LISTENER({m_id=141363308},{m_actionID=3,m_acteeID={m_Instance=777}})
          _TEST_LISTENER({m_id=777},{m_actionID=134,m_acteeID={m_Instance=888}})
          _TEST_LISTENER({m_id=777},{m_actionID=134,m_acteeID={}})
          _TEST_LISTENER({m_id=777},{m_actionID=8,m_acteeID={m_Instance=141363308}})
          assert(#BGX43Probe.events==0)
          assert(BGX43Probe.rejections.party_actor==1)
          assert(BGX43Probe.rejections.target_not_party==1)
          assert(BGX43Probe.rejections.target_not_numeric==1)
          assert(BGX43Probe.attackCandidates==3 and BGX43Probe.seenActions==4)
        ''')
    def test_ring_limit_and_safe_snapshot(self):
        self.vm.run('''
          for _=1,70 do _TEST_LISTENER({m_id=777},{m_actionID=134,m_acteeID={m_Instance=141363308}}) end
          assert(#BGX43Probe.events==64 and BGX43Probe.dropped==6)
          local x=BGX43Probe.snapshot()
          x.rejections.fake=999
          x.last_attack.reason='tampered'
          assert(BGX43Probe.rejections.fake==nil)
          assert(BGX43Probe.lastAttack.reason=='recorded')
        ''')
    def test_read_only_allowlist(self):
        data=SRC.read_text()
        for forbidden in ['ClearActions(', 'QueueResponse(', 'ActionOverride(', 'SetGlobal(',
                          'EEex_Action_Queue', 'io.open(', 'os.execute(', 'Infinity_DoFile(']:
            self.assertNotIn(forbidden, '\n'.join(l.split('--',1)[0] for l in data.splitlines()))
        self.assertLessEqual(len(SRC.stem),8)

if __name__=='__main__':unittest.main()
