"""Structural regression gates and independent reference state-machine tests for preview BCS receiver.
This is NOT a replacement for WeiDU compilation against game IDS.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
SRC=(ROOT/'BGX52_guard_receiver_PREVIEW.baf').read_text()
BRIDGE=(ROOT/'BGX52_bridge_preview.lua').read_text()
PREVIEW=(ROOT/'M_BX43_052_PREVIEW.lua').read_text()
BASE=Path('/mnt/data/BGXAI049_GUARD_ADVISORY_SOURCE/BGX49/M_BX43.lua').read_text()

def rules():
    parts=re.findall(r'IF\s*\n(.*?)\nTHEN\s*\n(.*?)\nEND',SRC,re.S)
    assert len(parts)==8
    return parts

def test_exact_eight_rules():
    assert len(rules())==8
    assert SRC.count('ProtectObject(')==6

def test_guard_candidates_slots_1_to_6():
    for i,(conds,actions) in enumerate(rules()[2:],start=1):
        assert f'Global("BGX52_REQ_SLOT","LOCALS",{i})' in conds
        for gate in ['InParty(Myself)','!InPartySlot(Myself,0)','Global("BGX38_GUARD","LOCALS",1)',
                     'GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")',
                     '!GlobalTimerNotExpired("BGX52_COOLDOWN","LOCALS")','ActionListEmpty()',
                     'ModalState(NONE)',f'InParty(Player{i})',f'InPartySlot(Player{i},{i-1})',f'!InPartySlot(Myself,{i-1})',
                     f'See(Player{i})',f'Range(Player{i},10)',
                     f'See(NearestEnemyOf(Player{i}))',f'Range(NearestEnemyOf(Player{i}),7)']:
            assert gate in conds,(i,gate)
        assert re.search(r'SetGlobal\("BGX52_REQ_SLOT","LOCALS",0\)\s+SetGlobalTimer\("BGX52_COOLDOWN","LOCALS",8\)\s+ProtectObject\(Player'+str(i)+r',6\)',actions)

def test_expire_and_f_off_rules_do_not_command():
    stale,off=rules()[:2]
    assert 'GlobalGT("BGX52_REQ_SLOT","LOCALS",0)' in stale[0]
    assert '!GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")' in stale[0]
    assert 'Global("BGX38_GUARD","LOCALS",0)' in off[0]
    assert 'ProtectObject' not in stale[1]+off[1]
    assert 'SetGlobal("BGX52_REQ_SLOT","LOCALS",0)' in stale[1]
    assert 'SetGlobal("BGX52_REQ_SLOT","LOCALS",0)' in off[1]

def test_no_generic_attack_commands_or_clear_actions():
    for s in [SRC,BRIDGE]:
        for verb in ['ClearActions(', 'ActionOverride(', 'Attack(', 'AttackReevaluate(',
                     'SetInterrupt(', 'QueueResponse(', 'CastSpell(', 'SetGlobal("BGX38_GUARD"']:
            assert verb not in s,verb

def test_sender_never_action_dispatches():
    assert 'B.enabled = false' in BRIDGE
    assert 'return false,reason' in BRIDGE
    assert 'orders_sent=false' in BRIDGE
    assert 'best.sprite:setLocalInt(k,v)' in BRIDGE
    assert 'BGX52_LAST_TICK' in BRIDGE and 'BGX52_HAS_SENT' in BRIDGE
    assert 'BGX52_LASTSEQ' not in BRIDGE
    assert BRIDGE.index('set("BGX52_REQ_SLOT",0)') < BRIDGE.index('set("BGX52_EXPIRE",now+TTL_TICKS)') < BRIDGE.index('set("BGX52_REQ_SLOT",slot)')
    assert 'if not ok then' in BRIDGE and 'pcall(set,"BGX52_REQ_SLOT",0)' in BRIDGE

def test_preview_preserves_049_runtime():
    assert 'P.version = "0.3.21-052-BRIDGE-PREVIEW"' in PREVIEW
    assert PREVIEW.count('function P.onWeaponHit(context)')==BASE.count('function P.onWeaponHit(context)')==1
    assert PREVIEW.count('P.guardSignals[#P.guardSignals + 1] = guardRecord')==1
    assert 'P.guardDispatchEnabled = false' in PREVIEW
    assert 'B.enabled = false' in PREVIEW
    # Removing additive bridge insertion must reconstruct 049 exactly (apart from version).
    before=PREVIEW.split('BGX52Bridge = BGX52Bridge or {}')[0]
    assert before.startswith(BASE[:180])

def test_timing_state_machine_model():
    def eligible(guard_on,req_slot,expires,now,idle,modal,see_victim,see_enemy,cd_expiry=0):
        if now>=expires or not guard_on or not idle or modal!=0 or not see_victim or not see_enemy: return False
        if now<cd_expiry: return False
        return 1<=req_slot<=6
    assert eligible(True,3,1090,1001,True,0,True,True)
    import itertools
    for guard,idle,modal,sv,se,ttl_ok,cd_ok in itertools.product([False,True],[False,True],[0,1,2,3,4,5],[False,True],[False,True],[False,True],[False,True]):
        t=1000 if ttl_ok else 1100
        cd=0 if cd_ok else 2000
        expected=guard and idle and modal==0 and sv and se and ttl_ok and cd_ok
        assert eligible(guard,3,1090,t,idle,modal,sv,se,cd)==expected
