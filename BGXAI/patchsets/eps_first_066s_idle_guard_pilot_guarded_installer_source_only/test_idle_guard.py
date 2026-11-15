"""Red-green Lua5.4 mocked-EEex test of narrowly scoped F-guard idle preference.

No game installed or accessed. A blank current-action is an ADVISORY,
not a proven empty EPS action queue. Only unchanged BCS is authorized to act.
"""
from pathlib import Path
import unittest
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
OLD=R/'M_BX43_066S_VERIFIED_ORIGINAL.lua'
NEW=R/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua'


def run(assertions,extra='',file=NEW):
    run_case(PREAMBLE+'\n'+extra,assertions,file)

class IdleGuard(unittest.TestCase):
    def test_red_old_closest_busy_defender(self):
        # The actual installed 066S selects closer attacking guardian g1.
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)
            assert(g2.locals.BGX52_REQ_SLOT==0 and BGX66Team.prepared==1)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0',OLD)
    def test_green_new_idle_further_defender(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX52_REQ_SLOT==3)
            assert(g1.locals.BGX52_REQ_SLOT==0 and BGX66Team.prepared==1)
            assert(#actions==0 and registrations.hit==1 and registrations.action==1)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0')
    def test_old_fails_new_acceptance(self):
        with self.assertRaises(AssertionError):
            run('''assert(hit(v2)==false);assert(g2.locals.BGX52_REQ_SLOT==3)''',
                'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0',OLD)
    def test_both_busy_keep_nearest_original(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)
            assert(g2.locals.BGX52_REQ_SLOT==0)''')
    def test_both_idle_keep_nearest_original(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)
            assert(g2.locals.BGX52_REQ_SLOT==0)''',
            'g1.m_curAction.m_actionID=0;g2.m_curAction.m_actionID=0')
    def test_unknown_action_keep_nearest_original(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction=nil;g2.m_curAction=nil')
    def test_idle_guard_f_off_does_not_qualify(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)
            assert(g2.locals.BGX52_REQ_SLOT==0)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.locals.BGX38_GUARD=0')
    def test_idle_guard_wrong_area_does_not_qualify(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.m_pArea=b')
    def test_idle_guard_modal_does_not_qualify(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.m_nModalState=1')
    def test_idle_guard_low_hp_does_not_qualify(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.m_baseStats.m_hitPoints=1')
    def test_idle_guard_existing_pending_request_does_not_qualify(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.locals.BGX52_REQ_SLOT=2')
    def test_only_busy_guard_original_fallback(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==3)''',
            'g1.m_curAction.m_actionID=3;g2.locals.BGX38_GUARD=0')
    def test_no_f_guard_maintains_zero_requests(self):
        run('''assert(hit(v2)==false);assert(g1.locals.BGX52_REQ_SLOT==0)
            assert(g2.locals.BGX52_REQ_SLOT==0 and #writes==0)''',
            'g1.locals.BGX38_GUARD=0;g2.locals.BGX38_GUARD=0')
    def test_other_heal_caster_untouched_when_low_hp(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX52_REQ_SLOT==3)
            assert(BGX66Caster.healPrepared==0 and #actions==0)''',
            'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=6')
    def test_script_writes_no_new_bcs_or_engine_orders(self):
        import hashlib,difflib
        a=OLD.read_text();b=NEW.read_text()
        self.assertEqual(hashlib.sha256(OLD.read_bytes()).hexdigest(),'50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f')
        self.assertEqual(a.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
        self.assertEqual(b.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
        self.assertEqual(a.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),1)
        self.assertEqual(b.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),1)
        self.assertEqual(a.count('function S.onHit(hit)'),b.count('function S.onHit(hit)'))
        self.assertEqual(a.count("set('BGX52_REQ_SLOT',slot)"),b.count("set('BGX52_REQ_SLOT',slot)"))
        self.assertEqual(a.count("set('BGX66_S_HEAL_SLOT'"),b.count("set('BGX66_S_HEAL_SLOT'"))
        self.assertEqual(len([x for x in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines()).get_opcodes() if x[0]!='equal']),2)

if __name__=='__main__':unittest.main()