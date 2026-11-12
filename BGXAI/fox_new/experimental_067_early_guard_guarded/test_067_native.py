"""Real Lua 5.4 VM with simulated EEex; never writes to live game."""
import unittest
from pathlib import Path
from hashlib import sha256
import re
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
from build_067 import build,OUT
ROOT=Path(__file__).parent

def run(assertions,settings='',action=None):
    if action is None:action='{m_actionID=3,m_acteeID={m_Instance=103}}'
    run_case(PREAMBLE+'\n'+settings+'\nlocal incoming='+action+'\n', assertions,OUT)

class EarlyGuard(unittest.TestCase):
    def test_01_reproducible_only_additive(self):
        self.assertEqual(OUT.read_bytes(),build())
        self.assertEqual(OUT.read_text().count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),1)
        self.assertEqual(OUT.read_text().count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
    def test_02_cleric_intercepts_at_attack_start_before_hit(self):
        run('''assert(registrations.hit==1 and registrations.action==1)
registrations.a(e,incoming)
assert(BGX67Early.prepared==1 and BGX67Early.last.victim_slot==3)
assert(g2.locals.BGX67_EARLY_SLOT==3)
assert(BGX66Caster.healPrepared==0 and BGX43Probe.weaponHitCalls==0)
assert(#actions==0 and #writes>0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=8;')
    def test_03_frontline_over_cleric(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==1 and g1.locals.BGX67_EARLY_SLOT==3)
assert(g2.locals.BGX67_EARLY_SLOT==nil or g2.locals.BGX67_EARLY_SLOT==0)''','g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3;')
    def test_04_critical_victim_cleric_reserved_for_heal(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)
assert(BGX67Early.rejected.no_eligible_melee_guardian==1)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;')
    def test_05_mage_bard_not_forced_to_melee(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=5;')
    def test_06_f_off(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.locals.BGX38_GUARD=0;')
    def test_07_unresolved_target_no_action(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;','{m_actionID=3,m_acteeID={m_Instance=-1}}')
    def test_08_group_attack_no_action(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;','{m_actionID=94,m_acteeID={m_Instance=103}}')
    def test_09_nonattack_no_action(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;','{m_actionID=31,m_acteeID={m_Instance=103}}')
    def test_10_nonparty_target(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;','{m_actionID=3,m_acteeID={m_Instance=999}}')
    def test_11_enemy_other_area(self):
        run('''e.m_pArea=b;registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;')
    def test_12_guardian_busy(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.m_nModalState=1;')
    def test_13_guardian_low_health(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.m_baseStats.m_hitPoints=2;')
    def test_14_heal_request_pending(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==0 and #writes==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.locals.BGX66_S_HEAL_SLOT=3;')
    def test_15_duplicate_same_victim_no_spam(self):
        run('''registrations.a(e,incoming);local n=#writes
registrations.a(e,incoming)
assert(BGX67Early.prepared==1 and #writes==n and BGX67Early.rejected.victim_lease==1)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;')
    def test_16_clock_rewind_fails_open_only_for_next_valid_attack(self):
        run('''registrations.a(e,incoming);assert(BGX67Early.prepared==1)
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=10
assert(BGX67Early.onAttack({event='fake'})==false)
assert(#actions==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;')
    def test_17_hit_listener_still_heals(self):
        run('''registrations.a(e,incoming)
assert(BGX67Early.prepared==1)
v2.m_baseStats.m_hitPoints=2
hit(v2)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)
assert(#actions==0)''','g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;')
    def test_18_no_extra_unconfirmed_event(self):
        run('''local ok,why=BGX67Early.onAttack({event='GUESS',hostility='NOT_CONCRETE'})
assert(ok==false and why=='not_explicit_resolved_attack' and #writes==0)''')
    def test_19_range_gate_in_BAF(self):
        s=(ROOT/'BGX67_EARLY_GUARD.baf').read_text()
        self.assertEqual(s.count('\nIF\n'),8)
        self.assertEqual(s.count('AttackReevaluate(NearestEnemyOf('),6)
        self.assertEqual(s.count('ActionListEmpty()'),6)
        self.assertEqual(s.count('ModalState(NONE)'),6)
        self.assertEqual(s.count('InMyArea(Player'),6)
        self.assertEqual(s.count('See(NearestEnemyOf(Player'),6)
        self.assertNotIn('ClearActions(',s)
    def test_20_no_direct_engine_orders(self):
        s=(ROOT/'BGX67_PREHIT_GUARD.lua').read_text()
        for n in ('Attack(', 'Spell(', 'ProtectObject(', 'ClearActions('):
            self.assertIsNone(re.search(r'(?<![.\w])'+re.escape(n),s))
if __name__=='__main__':unittest.main()
