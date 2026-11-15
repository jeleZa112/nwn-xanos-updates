"""Real Lua 5.4 unit tests of actual 066S source with mocked EEex (game unchanged)."""
from pathlib import Path
from hashlib import sha256
import re
import sys
import unittest
HERE=Path(__file__).resolve().parent
BASE=HERE/'M_BX43_066_BASELINE_READONLY.lua'
OUT=HERE/'M_BX43_066S_CASTER_CANDIDATE.lua'
POLICY=HERE/'BGX66_CASTER_SUPPORT.lua'
BAF=HERE/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'
from lua65_harness import run_case
from native_066_fixture import PREAMBLE


def check(assertions,extra=''):
    run_case(PREAMBLE+extra,assertions,OUT)

class CasterSupport066S(unittest.TestCase):
    def test_exact_066_base_and_listener_count(self):
        self.assertEqual(sha256(BASE.read_bytes()).hexdigest(),'c66ebb5190be8103819106a48d3100055b5791adf7c2d1df5f3e54596823540b')
        policy=POLICY.read_text(); base=BASE.read_text();candidate=OUT.read_text()
        self.assertEqual(candidate,base.replace('\nP.init()\n','\n'+policy+'\nP.init()\n',1))
        self.assertEqual(candidate.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
        self.assertEqual(candidate.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),1)
        self.assertEqual(candidate.count('function P.onWeaponHit(context)'),1)
    def test_current_party_mage_and_cleric_critical(self):
        check('''assert(hit(v1)==false)
assert(BGX66Team.prepared==0)
assert(BGX66Caster.healPrepared==1 and BGX66Caster.wardPrepared==1)
assert(g2.locals.BGX66_S_HEAL_SLOT==2 and v1.locals.BGX66_S_WARD==1)
assert(#actions==0 and BGX43Probe.weaponHitErrors==0 and registrations.hit==1)
assert(BGX66Caster.last.spells_cast==0 and BGX66Caster.last.status=='REQUESTS_PREPARED_BCS_ONLY')''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v1.locals.BGX38_GUARD=1;v1.m_baseStats.m_hitPoints=3;')
    def test_cleric_heals_bard_below_45(self):
        check('''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==1 and BGX66Caster.wardPrepared==0)
assert(g2.locals.BGX66_S_HEAL_SLOT==3 and #actions==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=5;')
    def test_above_threshold_does_not_cast(self):
        check('''assert(hit(v1)==false)
assert(BGX66Caster.healPrepared==0 and BGX66Caster.wardPrepared==0)
assert(#writes==0 and #actions==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v1.locals.BGX38_GUARD=1;')
    def test_f_off_no_support(self):
        check('''assert(hit(v1)==false);assert(BGX66Caster.healPrepared==0 and BGX66Caster.wardPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g1.locals.BGX38_GUARD=0;g2.locals.BGX38_GUARD=0;v1.locals.BGX38_GUARD=0;v1.m_baseStats.m_hitPoints=2;')
    def test_other_area_fails_closed(self):
        check('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.m_pArea=b;v2.m_baseStats.m_hitPoints=2;')
    def test_modal_busy_guard_fails_closed(self):
        check('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;g2.m_nModalState=1;v2.m_baseStats.m_hitPoints=2;')
    def test_no_health_data_no_spell(self):
        check('''assert(hit(v2)==false);assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats=nil;')
    def test_party_attacker_rejected(self):
        check('''assert(hit(v2,g2)==false);assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;')
    def test_no_duplicate_request_same_victim(self):
        check('''assert(hit(v2)==false);local n=#writes;assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==1 and #writes==n and BGX66Caster.rejected.victim_lease==1)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;')
    def test_lease_and_local_pending_prevents_reuse(self):
        check('''assert(hit(v2)==false)
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=200
assert(hit(v1)==false)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;v1.m_baseStats.m_hitPoints=2;')
    def test_frontline_still_responds_plus_cleric_support(self):
        check('''assert(hit(v2)==false);assert(BGX66Team.prepared==1)
assert(g1.locals.BGX52_REQ_SLOT==3 and BGX66Caster.healPrepared==1)
assert(g2.locals.BGX66_S_HEAL_SLOT==3 and #actions==0)''',
        'g1.m_typeAI.m_Class=2;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;')
    def test_low_hp_mage_only_self_ward(self):
        check('''assert(hit(v1)==false)
assert(BGX66Caster.healPrepared==0 and BGX66Caster.wardPrepared==1)
assert(v1.locals.BGX66_S_WARD==1 and #actions==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=1;v1.locals.BGX38_GUARD=1;v1.m_baseStats.m_hitPoints=2;')
    def test_ward_does_not_shield_other_mage(self):
        check('''assert(hit(v1)==false);assert(BGX66Caster.wardPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=1;v1.locals.BGX38_GUARD=0;v1.m_baseStats.m_hitPoints=2;')
    def test_missing_eeex_fails_closed(self):
        check('''EEex_UDEqual=nil;assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;')
    def test_unconfirmed_no_writes(self):
        check('''local ok,why=BGX66Caster.onHit({event='guess',confirmation='none',protected_id=103,attacker_id=999})
assert(ok==false and why=='unconfirmed_hit' and #writes==0)''')
    def test_staged_receiver_has_six_heal_slots_and_self_shield(self):
        text=BAF.read_text()
        self.assertEqual(text.count('IF\n'),11)
        self.assertEqual(text.count('HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)'),6)
        self.assertEqual(text.count('Spell(Player'),6)
        self.assertEqual(text.count('HaveSpell(WIZARD_SHIELD)'),1)
        self.assertEqual(text.count('Spell(Myself,WIZARD_SHIELD)'),1)
        self.assertEqual(text.count('ActionListEmpty()'),7)
        self.assertEqual(text.count('ModalState(NONE)'),7)
        self.assertEqual(text.count('HPPercentLT('),7)
        self.assertIn('!GlobalTimerNotExpired("BGX66_S_HEAL_COOLDOWN","LOCALS")',text)
        self.assertNotIn('ClearActions(',text)
        self.assertNotIn('SpellRES(',text)
    def test_source_only_no_new_hooks_or_immediate_spells(self):
        text=POLICY.read_text()
        for needle in ('EEex_Sprite_AddBlockWeaponHitListener(', 'EEex_Action_AddSpriteStartedActionListener(', 'Spell(', 'Attack(', 'ClearActions('):
            self.assertNotIn(needle,text)

if __name__=='__main__':unittest.main()
