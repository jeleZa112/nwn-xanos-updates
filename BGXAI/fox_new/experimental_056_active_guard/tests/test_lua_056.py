"""BGXAI 056 Lua runtime behavior tests with real Lua interpreter through lupa.
Only mock EEex world; no native game code executed.
"""
from pathlib import Path
import pytest
lupa=pytest.importorskip('lupa',reason='GitHub CI explicitly installs lupa')
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'BGX56/M_BX43.lua').read_text(encoding='utf8')

MOCK='''
portraits = {[0]=101,[1]=102,[2]=103,[3]=104,[4]=105,[5]=106}
sprites={}
function sprite(id,x,y,guard)
 local s={m_id=id,m_pos={x=x,y=y},m_nModalState=0,
  vars={BGX38_GUARD=guard or 0,BGX52_LAST_TICK=0,BGX52_HAS_SENT=0}}
 function s:getLocalInt(name)return self.vars[name] or 0 end
 function s:setLocalInt(name,value)self.vars[name]=value end
 return s
end
sprites[101]=sprite(101,5,5,0) -- Player1 victim
sprites[102]=sprite(102,6,6,1) -- F-ON idle player2
sprites[103]=sprite(103,40,40,1)
sprites[104]=sprite(104,10,10,0)
sprites[105]=sprite(105,20,20,0)
sprites[106]=sprite(106,20,30,0)
sprites[900]=sprite(900,4,4,0) -- nonparty attacker
EEex_Sprite_GetInPortraitID=function(slot)return portraits[slot] end
EEex_GameObject_Get=function(id)return sprites[id] end
EEex_EngineGlobal_CBaldurChitin={m_pObjectGame={m_worldTime={m_gameTime=100}}}
EEex_Action_AddSpriteStartedActionListener=function(fn) action_listener=fn end
EEex_Sprite_AddBlockWeaponHitListener=function(fn) hit_listener=fn end
function weapon_hit(attacker,victim)
 return hit_listener({attackingSprite=sprites[attacker],targetSprite=sprites[victim]})
end
'''

def runtime():
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(SOURCE)
    return lua

def test_confirmed_hit_requests_BCS_without_combat_command():
    lua=runtime()
    assert lua.eval('weapon_hit(900,101)') is False
    assert lua.eval('sprites[102].vars.BGX52_REQ_SLOT')==1
    assert lua.eval('sprites[102].vars.BGX52_EXPIRE')==190
    snap=lua.eval('BGX43Probe.snapshot()')
    assert snap['guard_signal_count']==1
    assert snap['bridge_prepared_count']==1
    assert snap['bridge_last']['chosen_guardian']==102
    assert snap['guard_dispatch_enabled'] is False
    assert snap['bcs_bridge_enabled'] is True
    assert snap['weapon_hit_errors']==0

def test_guard_F_off_rejects_without_local_write():
    lua=runtime();lua.execute('sprites[102].vars.BGX38_GUARD=0; sprites[103].vars.BGX38_GUARD=0')
    assert lua.eval('weapon_hit(900,101)') is False
    assert lua.eval('sprites[102].vars.BGX52_REQ_SLOT') is None
    snap=lua.eval('BGX43Probe.snapshot()')
    assert snap['bridge_prepared_count']==0
    assert snap['bridge_last']['reason']=='no_guardian_with_f_mode'

def test_bardsong_modal_prevents_selection():
    lua=runtime();lua.execute('sprites[102].m_nModalState=1')
    lua.eval('weapon_hit(900,101)')
    assert lua.eval('sprites[102].vars.BGX52_REQ_SLOT') is None
    assert lua.eval('BGX43Probe.snapshot().bridge_last.chosen_guardian')==103

def test_party_hit_rejected():
    lua=runtime();lua.eval('weapon_hit(102,101)')
    assert lua.eval('BGX43Probe.snapshot().bridge_prepared_count')==0
    assert lua.eval('BGX43Probe.snapshot().guard_signal_count')==0

def test_duplicate_same_tick_does_not_rearm():
    lua=runtime()
    lua.eval('weapon_hit(900,101)')
    lua.eval('weapon_hit(900,101)')
    assert lua.eval('BGX43Probe.snapshot().guard_signal_count')==2
    assert lua.eval('BGX43Probe.snapshot().bridge_prepared_count')==1
    assert lua.eval('BGX43Probe.snapshot().bridge_last.reason')=='duplicate_same_tick_or_clock_rewound'

def test_post_tick_can_rearm_after_cooldown_like_signal():
    lua=runtime()
    lua.eval('weapon_hit(900,101)')
    lua.execute('EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=101')
    lua.eval('weapon_hit(900,101)')
    assert lua.eval('BGX43Probe.snapshot().bridge_prepared_count')==2

def test_manual_disable_bridge_retains_passive_049_observer():
    lua=runtime();lua.execute('BGX52Bridge.enabled=false')
    assert lua.eval('weapon_hit(900,101)') is False
    assert lua.eval('BGX43Probe.snapshot().guard_signal_count')==1
    assert lua.eval('BGX43Probe.snapshot().bridge_prepared_count')==0
    assert lua.eval('sprites[102].vars.BGX52_REQ_SLOT') is None

def test_attacker_falsified_party_actor_does_not_write():
    lua=runtime();lua.execute('sprites[900].m_id=103')
    assert lua.eval('weapon_hit(900,101)') is False
    assert lua.eval('BGX43Probe.snapshot().guard_signal_count')==0

def test_locals_writer_failure_does_not_interrupt_hit():
    lua=runtime()
    lua.execute('function sprites[102]:setLocalInt(name,value) error("synthetic blocked write") end')
    assert lua.eval('weapon_hit(900,101)') is False
    assert lua.eval('BGX43Probe.snapshot().bridge_prepared_count')==0
    assert lua.eval('BGX43Probe.snapshot().bridge_last.reason')=='write_failure'
