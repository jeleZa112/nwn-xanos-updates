"""Native Lua 5.4 EET/EEex MOCK tests, no game installation/engine actions."""
from pathlib import Path
import difflib
import unittest
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
OLD=R/'M_BX43_066S_IDLE_GUARD_IDLE_HEAL_SOURCE_ONLY.lua'
NEW=R/'M_BX43_066S_IDLE_GUARD_HEAL_TRIAGE_SOURCE_ONLY.lua'

def run(assertions, setup='', source=NEW):
    run_case(PREAMBLE+'\n'+setup, assertions, source)

# A 40%-healthy hit recipient v2 (5/14) and an incapacitated v1 (1/14).
CASE='g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3;v1.m_baseStats.m_hitPoints=1;v2.m_baseStats.m_hitPoints=5;'

class EmergencyTriage(unittest.TestCase):
    def test_red_original_heals_recent_hit_not_most_critical(self):
        run('assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)',CASE,OLD)
        with self.assertRaises(AssertionError):
            run('assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==2)',CASE,OLD)
    def test_green_heals_critically_wounded_other_ally(self):
        run('''assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(BGX66Caster.last.triage_redirected==true)
            assert(BGX66Caster.last.victim_id==103 and BGX66Caster.last.heal_target_id==102)
            assert(BGX66Caster.last.heal_target_slot==2)
            assert(BGX66Caster.last.heal_target_percent<20)
            assert(g1.locals.BGX52_REQ_SLOT==3 and #actions==0)''', CASE)
    def test_hit_healthy_ally_can_trigger_critical_rescue(self):
        run('''assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(BGX66Caster.last.triage_redirected==true and #actions==0)''',CASE+'v2.m_baseStats.m_hitPoints=13;')
    def test_no_critical_and_healthy_hit_does_nothing(self):
        run('''assert(hit(v2)==false)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0)
            assert(BGX66Caster.rejected.not_emergency==1 and #writes==0)''',
            'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;')
    def test_less_critical_ally_never_steals_heal(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)
            assert(BGX66Caster.last.triage_redirected==false)''',CASE+'v1.m_baseStats.m_hitPoints=4;')
    def test_worst_of_two_critical_injuries_is_first(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE+'v2.m_baseStats.m_hitPoints=1;v1.m_baseStats.m_hitPoints=2;')
    def test_tie_prefers_recently_hit_target(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE+'v2.m_baseStats.m_hitPoints=1;')
    def test_critical_ally_different_area_falls_back_to_hit_target(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE+'v1.m_pArea=b;')
    def test_critical_ally_unknown_hp_falls_back_to_hit_target(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE+'v1.m_baseStats=nil;')
    def test_critical_ally_invalid_position_falls_back(self):
        run('''assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE+'v1.m_pos=nil;')
    def test_critical_target_with_active_lease_ignored(self):
        run('''BGX66Caster.victims[102]=200
            assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==3)''',CASE)
    def test_original_hit_target_with_lease_can_rescue_other(self):
        run('''BGX66Caster.victims[103]=200
            assert(hit(v2)==false);assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(BGX66Caster.victims[102]>100 and #actions==0)''',CASE)
    def test_lease_prevents_double_cast_for_redirected_target(self):
        run('''assert(hit(v2)==false)
            local before=BGX66Caster.healPrepared
            local writesBefore=#writes
            assert(hit(v2)==false)
            assert(BGX66Caster.healPrepared==before and #writes==writesBefore)
            assert(BGX66Caster.victims[102]>100 and #actions==0)''',CASE)
    def test_nonparty_attacker_rejected(self):
        run('''assert(hit(v2,g1)==false);assert(#writes==0 and #actions==0)''',CASE)
    def test_f_off_healer_cannot_rescue(self):
        run('''assert(hit(v2)==false)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0 and #actions==0)''',CASE+'g2.locals.BGX38_GUARD=0;')
    def test_modal_healer_cannot_rescue(self):
        run('''assert(hit(v2)==false)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0 and #actions==0)''',CASE+'g2.m_nModalState=1;')
    def test_pending_heal_request_not_clobbered(self):
        run('''assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==4 and #actions==0)''',CASE+'g2.locals.BGX66_S_HEAL_SLOT=4;')
    def test_caster_ward_still_targets_attacked_mage(self):
        run('''assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(v2.locals.BGX66_S_WARD==1)
            assert(BGX66Caster.last.victim_id==103 and BGX66Caster.last.heal_target_id==102)
            assert(BGX66Caster.victims[102]>100 and BGX66Caster.victims[103]>100)
            assert(#actions==0)''',CASE+'v2.m_typeAI.m_Class=1;v2.locals.BGX38_GUARD=1;v2.m_baseStats.m_hitPoints=2;v1.m_baseStats.m_hitPoints=1;')
    def test_conservatively_rejects_missing_hit_victim_health(self):
        run('''assert(hit(v2)==false)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0)
            assert(BGX66Caster.rejected.victim_health_unknown==1 and #actions==0)''',CASE+'v2.m_baseStats=nil;')
    def test_no_double_lease_and_time_rewind_reset(self):
        run('''assert(hit(v2)==false)
            EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=50
            g2.locals.BGX66_S_HEAL_SLOT=0
            g2.locals.BGX66_S_HEAL_SENT=0
            assert(hit(v2)==false)
            assert(BGX66Caster.healPrepared==2 and #actions==0)''',CASE)
    def test_code_is_limited_to_victim_triage_no_new_hooks(self):
        old=OLD.read_text();new=NEW.read_text()
        for x in ('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit',
                  'EEex_Action_AddSpriteStartedActionListener, P.onStarted',
                  'function S.onHit(hit)',"set('BGX52_REQ_SLOT',slot)"):
            self.assertEqual(old.count(x),new.count(x))
        for x in ('ClearActions(', 'Spell(', 'Attack(', 'ProtectObject('):
            self.assertEqual(old.count(x),new.count(x))
        self.assertLessEqual(len([op for op in difflib.SequenceMatcher(a=old.splitlines(),b=new.splitlines()).get_opcodes() if op[0]!='equal']),9)

if __name__=='__main__': unittest.main(verbosity=2)
