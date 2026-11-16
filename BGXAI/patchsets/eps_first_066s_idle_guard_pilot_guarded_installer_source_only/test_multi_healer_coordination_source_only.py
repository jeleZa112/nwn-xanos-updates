"""Native Lua 5.4 synthetic EEex regression: team healer coordination, SOURCE ONLY."""
import unittest
import difflib
from pathlib import Path
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
OLD=R/'M_BX43_066S_IDLE_GUARD_HEAL_TRIAGE_SOURCE_ONLY.lua'
NEW=R/'M_BX43_066S_MULTI_HEAL_COORDINATION_SOURCE_ONLY.lua'
# v1 1/14 (7%), v2 2/14 (14%), g1 and g2 are both priest healers.
TWO='g1.m_typeAI.m_Class=3;g2.m_typeAI.m_Class=3;v1.m_baseStats.m_hitPoints=1;v2.m_baseStats.m_hitPoints=2;'
ONE='g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3;v1.m_baseStats.m_hitPoints=1;v2.m_baseStats.m_hitPoints=2;'

def run(assertions, setup=TWO, source=NEW):
    run_case(PREAMBLE+'\n'+setup, assertions, source)

class MultiHealerCoordination(unittest.TestCase):
    def test_red_previous_candidate_only_sends_one_request(self):
        run('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0)''',source=OLD)
        with self.assertRaises(AssertionError):
            run('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==2)''',source=OLD)
    def test_green_two_patients_two_healers_exclusive_requests(self):
        run('''assert(hit(v2)==false)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2 and g2.locals.BGX66_S_HEAL_SLOT==3)
            assert(BGX66Caster.healPrepared==2 and BGX66Caster.last.heal_count==2)
            assert(BGX66Caster.last.heals[1].patient_id==102)
            assert(BGX66Caster.last.heals[2].patient_id==103)
            assert(BGX66Caster.last.heals[1].healer_id~=BGX66Caster.last.heals[2].healer_id)
            assert(#actions==0)''')
    def test_single_healer_only_one_request_for_worst_patient(self):
        run('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(BGX66Caster.last.heal_count==1 and #actions==0)''',ONE)
    def test_two_healers_one_patient_no_duplicate(self):
        run('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(g1.locals.BGX66_S_HEAL_SLOT==3)
            assert((g2.locals.BGX66_S_HEAL_SLOT or 0)==0 and #actions==0)''', TWO+'v1.m_baseStats.m_hitPoints=12;')
    def test_second_confirmed_hit_same_tick_no_duplicate(self):
        run('''assert(hit(v2)==false);local count=BGX66Caster.healPrepared
            assert(hit(v1)==false);assert(BGX66Caster.healPrepared==count)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2 and g2.locals.BGX66_S_HEAL_SLOT==3)
            assert(#actions==0)''')
    def test_pending_bcs_request_blocks_duplicate_after_45_ticks(self):
        run('''assert(hit(v2)==false);local old=BGX66Caster.healPrepared
            EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=146
            assert(hit(v1)==false);assert(BGX66Caster.healPrepared==old)
            assert(#actions==0)''')
    def test_after_confirmed_bcs_clear_and_lease_elapsed_reissue_allowed(self):
        run('''assert(hit(v2)==false)
            g1.locals.BGX66_S_HEAL_SLOT=0
            g2.locals.BGX66_S_HEAL_SLOT=0
            EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=146
            assert(hit(v2)==false);assert(BGX66Caster.healPrepared==4)
            assert(#actions==0)''')
    def test_reloaded_lua_still_honors_live_bcs_pending(self):
        run('''assert(hit(v2)==false)
            BGX66Caster.victims={};BGX66Caster.reservations={}
            EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=146
            assert(hit(v2)==false);assert(BGX66Caster.healPrepared==2)
            assert(#actions==0)''')
    def test_live_pending_patient_one_routes_second_healer_to_patient_two(self):
        run('''g1.locals.BGX66_S_HEAL_SLOT=2
            g1.locals.BGX66_S_HEAL_EXPIRE=300
            assert(hit(v2)==false)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2)
            assert(g2.locals.BGX66_S_HEAL_SLOT==3)
            assert(BGX66Caster.healPrepared==1 and #actions==0)''')
    def test_expired_bcs_pending_does_not_reserve_patient(self):
        run('''g1.locals.BGX66_S_HEAL_SLOT=2
            g1.locals.BGX66_S_HEAL_EXPIRE=50
            assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(BGX66Caster.healPrepared==1 and #actions==0)''')
    def test_fail_closed_if_pending_request_expiry_unreadable(self):
        run('''local old=g1.getLocalInt
            g1.getLocalInt=function(self,k)
               if k=='BGX66_S_HEAL_EXPIRE' then error('read error') end
               return old(self,k)
            end
            g1.locals.BGX66_S_HEAL_SLOT=2
            assert(hit(v2)==false)
            assert(BGX66Caster.healPrepared==0 and #actions==0)''')
    def test_skip_healer_with_pending_guard_action(self):
        run('''g1.locals.BGX52_REQ_SLOT=3
            assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(g1.locals.BGX66_S_HEAL_SLOT==nil)
            assert(#actions==0)''')
    def test_skip_healer_with_pending_ward_action(self):
        run('''g1.locals.BGX66_S_WARD=1
            assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(#actions==0)''')
    def test_f_off_second_healer_has_only_one_cure(self):
        run('''g2.locals.BGX38_GUARD=0
            assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2 and #actions==0)''')
    def test_other_area_second_healer_has_only_one_cure(self):
        run('''g2.m_pArea=b
            assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(g1.locals.BGX66_S_HEAL_SLOT==2 and #actions==0)''')
    def test_idle_hint_preferred_for_high_priority_patient(self):
        run('''g1.m_curAction.m_actionID=3;g2.m_curAction.m_actionID=0
            assert(hit(v2)==false)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2 and g1.locals.BGX66_S_HEAL_SLOT==3)
            assert(#actions==0)''')
    def test_moderate_only_one_heal_even_with_two_healers(self):
        run('''v1.m_baseStats.m_hitPoints=8;v2.m_baseStats.m_hitPoints=5
            assert(hit(v2)==false);assert(BGX66Caster.healPrepared==1)
            assert(BGX66Caster.last.heal_count==1 and #actions==0)''')
    def test_guard_still_protects_hit_victim(self):
        run('''g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3
            assert(hit(v2)==false)
            assert(g1.locals.BGX52_REQ_SLOT==3)
            assert(g2.locals.BGX66_S_HEAL_SLOT==2)
            assert(#actions==0)''')
    def test_clock_rewind_resets_runtime_leases_but_honors_bcs_pending(self):
        run('''assert(hit(v2)==false)
            EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=50
            assert(hit(v2)==false)
            assert(BGX66Caster.healPrepared==2 and #actions==0)''')
    def test_lease_count_never_more_than_two_requests_per_hit(self):
        run('''pc.m_baseStats.m_hitPoints=1;pc.m_baseStats.m_nMaxHitPoints=14
            assert(hit(v2)==false)
            assert(BGX66Caster.healPrepared==2 and #actions==0)''')
    def test_seeded_60_scenarios_unique_healers_unique_patients_no_orders(self):
        run('''math.randomseed(20261116)
            for n=1,60 do
                g1.locals.BGX66_S_HEAL_SLOT=0;g2.locals.BGX66_S_HEAL_SLOT=0
                g1.locals.BGX66_S_HEAL_SENT=0;g2.locals.BGX66_S_HEAL_SENT=0
                g1.locals.BGX66_S_WARD=0;g2.locals.BGX66_S_WARD=0
                g1.locals.BGX52_REQ_SLOT=0;g2.locals.BGX52_REQ_SLOT=0
                BGX66Caster.victims={};BGX66Caster.reservations={}
                v1.m_baseStats.m_hitPoints=math.random(1,14)
                v2.m_baseStats.m_hitPoints=math.random(1,14)
                g1.locals.BGX38_GUARD=math.random(0,1)
                g2.locals.BGX38_GUARD=math.random(0,1)
                g1.m_curAction.m_actionID=math.random(0,1)*3
                g2.m_curAction.m_actionID=math.random(0,1)*3
                EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=100+n
                local before=BGX66Caster.healPrepared
                assert(hit(v2)==false)
                local c=BGX66Caster.healPrepared-before
                assert(c>=0 and c<=2)
                local a=g1.locals.BGX66_S_HEAL_SLOT or 0
                local b=g2.locals.BGX66_S_HEAL_SLOT or 0
                assert(a==0 or a==2 or a==3)
                assert(b==0 or b==2 or b==3)
                assert(a==0 or b==0 or a~=b)
                assert((a~=0 and 1 or 0)+(b~=0 and 1 or 0)==c)
                assert((a==0 or g1.locals.BGX38_GUARD==1))
                assert((b==0 or g2.locals.BGX38_GUARD==1))
                assert(#actions==0)
            end''')

    def test_source_no_additional_engine_calls_or_hooks(self):
        old=OLD.read_text();new=NEW.read_text()
        for needle in ('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit',
                       'EEex_Action_AddSpriteStartedActionListener, P.onStarted',
                       'function S.onHit(hit)', "set('BGX52_REQ_SLOT',slot)"):
            self.assertEqual(old.count(needle),new.count(needle))
        for x in ('ClearActions(', 'Spell(', 'Attack(', 'ProtectObject('):
            self.assertEqual(old.count(x),new.count(x))
        self.assertNotIn('os.execute(',new)
        self.assertLessEqual(len([x for x in difflib.SequenceMatcher(a=old.splitlines(),b=new.splitlines()).get_opcodes() if x[0]!='equal']),18)

if __name__=='__main__':
    unittest.main(verbosity=2)
