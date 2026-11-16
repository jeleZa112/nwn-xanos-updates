"""Real Lua5.4 interpreter with mock EEex. Does not execute spells or change game files."""
from pathlib import Path
import unittest
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
OLD=R/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua'
NEW=R/'M_BX43_066S_IDLE_GUARD_IDLE_HEAL_SOURCE_ONLY.lua'

def run(asserts,setup='',file=NEW):
    run_case(PREAMBLE+'\n'+setup, asserts, file)

# Both g1/g2 are healers (3), but g1 is nearest victim v2.
# A healer who is attacking is likely to fail the old BCS ActionListEmpty gate.
BASE='g1.m_typeAI.m_Class=3;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;'

class IdleHealer(unittest.TestCase):
    def test_red_old_nearest_busy_healer(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3);assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0',OLD)
    def test_new_prefers_idle_further_healer(self):
        run("assert(hit(v2)==false);assert((g1.locals.BGX66_S_HEAL_SLOT or 0)==0);assert(g2.locals.BGX66_S_HEAL_SLOT==3);assert(BGX66Caster.healPrepared==1 and #actions==0)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0')
    def test_old_fails_new_acceptance(self):
        with self.assertRaises(AssertionError):
            run("assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0',OLD)
    def test_two_idle_choose_closer(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction.m_actionID=0;g2.m_curAction.m_actionID=0')
    def test_two_busy_choose_closer(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE)
    def test_action_unknown_choose_closer(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction=nil;g2.m_curAction=nil')
    def test_f_off_idle_healer_not_selected(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.locals.BGX38_GUARD=0')
    def test_other_area_idle_healer_not_selected(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.m_pArea=b')
    def test_modal_idle_healer_not_selected(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and (g2.locals.BGX66_S_HEAL_SLOT or 0)==0)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.m_nModalState=1')
    def test_existing_pending_request_excludes_idle_healer(self):
        run("assert(hit(v2)==false);assert(g1.locals.BGX66_S_HEAL_SLOT==3 and g2.locals.BGX66_S_HEAL_SLOT==2)",BASE+'g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0;g2.locals.BGX66_S_HEAL_SLOT=2')
    def test_no_cast_if_not_hurt(self):
        run("assert(hit(v2)==false);assert(BGX66Caster.healPrepared==0 and #actions==0 and #writes==0)",'g1.m_typeAI.m_Class=3;g2.m_typeAI.m_Class=3;g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0')
    def test_lethal_hp_only_still_fail_closed_for_absent_guard_mode(self):
        run("assert(hit(v2)==false);assert(BGX66Caster.healPrepared==0 and #actions==0)",BASE+'g1.locals.BGX38_GUARD=0;g2.locals.BGX38_GUARD=0')
    def test_guard_select_remains_idle_hint(self):
        # The prior frontline-selection feature must remain independent.
        run("assert(hit(v2)==false);assert(g2.locals.BGX52_REQ_SLOT==3 and #actions==0)",'g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=6;g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0')
    def test_one_healer_both_roles_not_queue_engine_action(self):
        run("assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1 and #actions==0 and BGX66Team.prepared==1)",'g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;g2.m_curAction.m_actionID=0')
    def test_safety_same_hook_counts(self):
        old=OLD.read_text();new=NEW.read_text()
        for needle in ('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit','EEex_Action_AddSpriteStartedActionListener, P.onStarted','function S.onHit(hit)',"set('BGX52_REQ_SLOT',slot)"):
            self.assertEqual(old.count(needle),new.count(needle),needle)
        import difflib
        self.assertEqual(1,len([x for x in difflib.SequenceMatcher(a=old.splitlines(),b=new.splitlines()).get_opcodes() if x[0]!='equal']))

if __name__=='__main__':unittest.main(verbosity=2)