#!/usr/bin/env python3
"""Offline test suite for version-matched EEex 1.1.7 probe.

The runtime tests use system Lua 5.4 as a syntax/behavior simulator,
NOT actual EEex/LuaJIT nor in-game testing.
"""
from __future__ import annotations
import ctypes
from pathlib import Path
import unittest
from eeex_bridge_043 import summarize, validate_report, simulate_policy_offline

ROOT=Path(__file__).resolve().parent
LUA_SOURCE=(ROOT/'M_BGX43Probe.lua').read_text(encoding='utf-8')


def mock_event(seq=1,src=12,dst=34,action=3):
    return {'schema':1,'event':'NONPARTY_ATTACK_STARTED_ON_PARTY','actor_id':src,
        'target_id':dst,'action_id':action,'actor_x':10,'actor_y':5,
        'action_origin':'UNKNOWN','visibility':'UNKNOWN',
        'hostility':'CONFIRMED_BY_EXPLICIT_ATTACK_ACTION','party_ids':[34,67],
        'sequence':seq}


def mock_report(events):
    return {'schema':1,'version':'0.3.13-043-PROBE','origin_verifiable':False,
        'queue_verifiable':False,'events':events}


class BridgeTests(unittest.TestCase):
    def test_empty(self):self.assertEqual(summarize(mock_report([]))['events_considered'],0)
    def test_single_attack(self):self.assertEqual(summarize(mock_report([mock_event()]))['events_considered'],1)
    def test_one_round(self):self.assertEqual(summarize(mock_report([mock_event(action=105)]))['events_considered'],1)
    def test_no_dispatch(self):
        x=summarize(mock_report([mock_event()]));self.assertFalse(x['execution_allowed']);self.assertEqual(x['action_commands'],[])
    def test_manual_unknown(self):self.assertFalse(summarize(mock_report([mock_event()]))['queue_origin_known'])
    def test_visibility_unknown(self):self.assertFalse(summarize(mock_report([mock_event()]))['engine_visibility_known'])
    def test_bad_schema(self):
        with self.assertRaises(ValueError):summarize({'schema':2,'events':[]})
    def test_too_many(self):
        with self.assertRaises(ValueError):summarize(mock_report([mock_event(i+1) for i in range(65)]))
    def test_no_future_claim(self):
        with self.assertRaises(ValueError):summarize({'schema':1,'origin_verifiable':True,'queue_verifiable':False,'events':[]})
    def test_false_target(self):
        e=mock_event();e['party_ids']=[67];self.assertEqual(summarize(mock_report([e]))['events_considered'],0)
    def test_party_actor(self):
        e=mock_event();e['party_ids']=[12,34];self.assertEqual(summarize(mock_report([e]))['events_considered'],0)
    def test_wrong_opcode(self):
        e=mock_event();e['action_id']=31;self.assertEqual(summarize(mock_report([e]))['events_considered'],0)
    def test_spoofed_evidence(self):
        e=mock_event();e['hostility']='APPROACHING';self.assertEqual(summarize(mock_report([e]))['events_considered'],0)
    def test_nonmonotonic(self):
        x=summarize(mock_report([mock_event(2),mock_event(1)]));self.assertEqual(x['events_considered'],1)
    def test_untagged_origin(self):
        e=mock_event();e['action_origin']='MANUAL';self.assertEqual(summarize(mock_report([e]))['events_considered'],0)
    def test_position_missing(self):
        e=mock_event();e['actor_x']=False;e['actor_y']=None
        x=summarize(mock_report([e]))['attack_alerts'][0];self.assertIsNone(x['actor_x']);self.assertIsNone(x['actor_y'])
    def test_infinite_position_block(self):
        e=mock_event();e['actor_x']=float('inf');self.assertIsNone(summarize(mock_report([e]))['attack_alerts'][0]['actor_x'])
    def test_no_mutating_lua_calls(self):
        code='\n'.join(l.split('--',1)[0] for l in LUA_SOURCE.splitlines())
        for token in ('ClearActions(', 'QueueResponseString(', 'SetGlobal(', 'ActionOverride(',
                      'EEex_Action_Execute', 'EEex_GameState_Set', 'io.open(', 'os.execute(',
                      'EEex_AIBase_Set', 'sprite:enqueue', 'EEex_Action_Queue'):
            self.assertNotIn(token, code)
    def test_version(self):self.assertIn('0.3.13-043-PROBE',LUA_SOURCE)


class PolicyPipelineTests(unittest.TestCase):
    def fixture(self):
        return {'provenance':'OFFLINE_FIXTURE','tick':20,'party_ai_on':True,
          'allies':[{'uid':'34','x':0,'y':0,'hp':1,'max_hp':6}],
          'defenders':[
            {'uid':'D1','x':3,'y':0,'hp':14,'max_hp':14,'role':'frontline','busy':'idle'},
            {'uid':'D2','x':0,'y':2,'hp':14,'max_hp':14,'role':'frontline','busy':'idle'}]}
    def test_two_guard_pipeline(self):
        r=simulate_policy_offline(mock_report([mock_event(src=12,dst=34)]),self.fixture())
        self.assertEqual(r['mode'],'OFFLINE_FIXTURE_ONLY')
        self.assertIsNotNone(r['policy_plan']['interceptor_uid'])
        self.assertIsNotNone(r['policy_plan']['cover_uid'])
        self.assertNotEqual(r['policy_plan']['interceptor_uid'],r['policy_plan']['cover_uid'])
        self.assertFalse(r['execution_allowed']);self.assertEqual(r['action_commands'],[])
    def test_manual_guard_excluded(self):
        f=self.fixture();f['defenders'][0]['busy']='manual';f['defenders'][1]['busy']='casting'
        r=simulate_policy_offline(mock_report([mock_event()]),f)
        self.assertIsNone(r['policy_plan']['interceptor_uid'])
        self.assertFalse(r['execution_allowed'])
    def test_provenance_protection(self):
        f=self.fixture();f['provenance']='EEEX_LIVE_UNVERIFIED'
        with self.assertRaises(ValueError):simulate_policy_offline(mock_report([mock_event()]),f)
    def test_target_protection(self):
        f=self.fixture();f['allies'][0]['uid']='999'
        with self.assertRaises(ValueError):simulate_policy_offline(mock_report([mock_event()]),f)
    def test_zero_events(self):
        r=simulate_policy_offline(mock_report([]),self.fixture())
        self.assertIsNone(r['policy_plan'])
    def test_disabled_party_ai(self):
        f=self.fixture();f['party_ai_on']=False
        r=simulate_policy_offline(mock_report([mock_event()]),f)
        self.assertIsNone(r['policy_plan']['interceptor_uid'])


class LuaRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try: cls.lib=ctypes.CDLL('liblua5.4.so.0')
        except OSError: raise unittest.SkipTest('system liblua5.4 unavailable')
        L=cls.lib
        L.luaL_newstate.restype=ctypes.c_void_p
        L.luaL_openlibs.argtypes=[ctypes.c_void_p]
        L.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        L.luaL_loadstring.restype=ctypes.c_int
        L.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
        L.lua_pcallk.restype=ctypes.c_int
        L.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
        L.lua_tolstring.restype=ctypes.c_char_p
        L.lua_close.argtypes=[ctypes.c_void_p]
    def eval_lua(self,scenario:str,preamble:str=''):
        L=self.lib.luaL_newstate()
        try:
            self.lib.luaL_openlibs(L)
            chunk=preamble+'\n'+LUA_SOURCE+'\n'+scenario
            out=self.lib.luaL_loadstring(L,chunk.encode('utf-8'))
            if out!=0:raise AssertionError('LUA SYNTAX: '+str(self.lib.lua_tolstring(L,-1,None)))
            ret=self.lib.lua_pcallk(L,0,-1,0,0,None)
            if ret!=0:raise AssertionError('LUA RUNTIME: '+str(self.lib.lua_tolstring(L,-1,None)))
        finally:self.lib.lua_close(L)
    BASE="""
      ids={[0]=34,[1]=67}
      listenerCount=0
      EEex_Sprite_GetInPortraitID=function(i) return ids[i] or -1 end
      EEex_Action_AddSpriteStartedActionListener=function(fn) listener=fn;listenerCount=listenerCount+1 end
    """
    def test_lua_syntax(self):self.eval_lua('assert(BGX43Probe.installed == false)')
    def test_hooks(self):self.eval_lua('assert(BGX43Probe.installed and listenerCount==1)',self.BASE)
    def test_install_idempotent(self):self.eval_lua('assert(BGX43Probe.init() and listenerCount==1)',self.BASE)
    def test_enemy_attack(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=34}})
      local x=BGX43Probe.snapshot()
      assert(#x.events==1 and x.events[1].actor_id==12 and x.events[1].target_id==34)
      assert(x.events[1].actor_x==3 and x.events[1].action_origin=='UNKNOWN')
    ''',self.BASE)
    def test_action_105(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=105,m_acteeID={m_Instance=34}})
      assert(#BGX43Probe.snapshot().events==1)
    ''',self.BASE)
    def test_filter_party_attack(self):self.eval_lua('''
      listener({m_id=34,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=12}})
      assert(#BGX43Probe.snapshot().events==0)
    ''',self.BASE)
    def test_filter_neutral_action(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=31,m_acteeID={m_Instance=34}})
      assert(#BGX43Probe.snapshot().events==0)
    ''',self.BASE)
    def test_filter_nonparty_target(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=99}})
      assert(#BGX43Probe.snapshot().events==0)
    ''',self.BASE)
    def test_missing_field_safe(self):self.eval_lua('''
      listener({m_id=12,m_pos={}},{m_actionID=3,m_acteeID={m_Instance=34}})
      assert(#BGX43Probe.snapshot().events==1 and BGX43Probe.snapshot().events[1].actor_x==false)
    ''',self.BASE)
    def test_disabled(self):self.eval_lua('''
      BGX43Probe.enabled=false
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=34}})
      assert(#BGX43Probe.snapshot().events==0)
    ''',self.BASE)
    def test_ring_bound(self):self.eval_lua('''
      for i=1,65 do listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=34}}) end
      local x=BGX43Probe.snapshot();assert(#x.events==64 and x.dropped==1)
      assert(x.events[1].sequence==2 and x.events[64].sequence==65)
    ''',self.BASE)
    def test_copy_snapshot(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=34}})
      local x=BGX43Probe.snapshot();x.events[1].actor_id=777;x.events[1].party_ids[1]=777
      local y=BGX43Probe.snapshot();assert(y.events[1].actor_id==12 and y.events[1].party_ids[1]==34)
    ''',self.BASE)
    def test_reset_is_private(self):self.eval_lua('''
      listener({m_id=12,m_pos={x=3,y=5}},{m_actionID=3,m_acteeID={m_Instance=34}})
      BGX43Probe.clearMemory()
      assert(#BGX43Probe.snapshot().events==0 and BGX43Probe.installed)
    ''',self.BASE)

if __name__=='__main__':unittest.main(verbosity=2)
