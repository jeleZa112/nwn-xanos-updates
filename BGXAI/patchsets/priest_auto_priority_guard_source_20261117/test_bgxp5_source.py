#!/usr/bin/env python3
"""BGXP5 source-only regression: protect party, give idle AUTO heal first priority."""
import hashlib
import unittest
import BGXP5_PRIORITY_AND_ALLY_GUARD_SOURCE_ONLY as S


class TestBGXP5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=S.canonical(S.COMBAT_SOURCE.read_bytes())
        cls.pr=S.canonical(S.PR_SOURCE.read_bytes())
        cls.old_blocks=S.sections(cls.old,28)
        cls.friendly=S.guarded_combat_baf(cls.old)
        cls.new_blocks=S.sections(cls.friendly,28)
        cls.healing=S.priority_auto_cure_baf()
        cls.heal_blocks=S.sections(cls.healing,12)

    def test_input_hashes(self):
        self.assertEqual(S.sha(self.old),S.COMBAT_SHA)
        self.assertEqual(S.sha(self.pr),S.PR_SHA)

    def test_current_bgxp3_reproduced_exact(self):
        self.assertEqual(S.sha(S.expected_bgxp3_baf(self.old)),S.BGXP3_BUF_SHA)

    def test_combat_only_four_blocks_changed(self):
        changed=[i for i,(a,b) in enumerate(zip(self.old_blocks,self.new_blocks)) if a!=b]
        self.assertEqual(changed,list(S.COMBAT_INDICES))

    def test_explicit_no_party_target_in_all_combat_blocks(self):
        for i in S.COMBAT_INDICES:
            block=self.new_blocks[i]
            self.assertEqual(block.count("!InParty(NearestEnemyOf(Myself))"),1)
            self.assertIn("ActionListEmpty()",block)
            self.assertIn("Global(\"BGXR_ROLE\",\"LOCALS\",",block)
            self.assertIn("See(NearestEnemyOf(Myself))",block)

    def test_auto_attack_no_when_ally_below_sixty(self):
        last=self.new_blocks[-1]
        for player in range(1,7):
            self.assertIn(f"!HPPercentLT(Player{player},60)",last)

    def test_priority_two_tiers_each_six_slots(self):
        self.assertEqual(len(self.heal_blocks),12)
        for j,threshold in enumerate((35,70)):
            for slot in range(1,7):
                b=self.heal_blocks[j*6+slot-1]
                self.assertIn(f"HPPercentLT(Player{slot},{threshold})",b)
                self.assertIn(f"Range(Player{slot},18)",b)
                self.assertIn(f"Spell(Player{slot},CLERIC_CURE_LIGHT_WOUNDS)",b)
                self.assertIn(f"InPartySlot(Player{slot},{slot-1})",b)

    def test_manual_and_timers_safety(self):
        for b in self.heal_blocks:
            for gate in ("ActionListEmpty()","ModalState(NONE)","HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)",
                         'Global("BGXR_ROLE","LOCALS",4)','Global("BGX38_GUARD","LOCALS",1)',
                         'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                         '!GlobalTimerNotExpired("BGXR_HEAL_CD","LOCALS")',
                         'HPGT(Player'):
                self.assertIn(gate,b)
        for disallowed in ("ClearActions(","ActionOverride(","ForceSpell(","ReallyForceSpell("):
            self.assertNotIn(disallowed,self.healing.decode())

    def test_idle_priority_over_eps_not_in_pr_baf(self):
        self.assertTrue(self.healing.startswith(b"// BGXP5 source only"))
        self.assertEqual(len(S.sections(self.pr,42)),42)
        self.assertEqual(self.old_blocks[0],self.new_blocks[0])

    def test_fail_closed_on_input_drift(self):
        with self.assertRaisesRegex(ValueError,"SHA_DRIFT"):
            S.guarded_combat_baf(self.old+b"x")
        with self.assertRaisesRegex(ValueError,"SHA_DRIFT"):
            S.expected_bgxp3_baf(self.old+b"x")

    def test_report_source_only(self):
        r=S.report()
        self.assertEqual(r["status"],"BGXP5_SOURCE_ONLY_NO_INSTALL")
        self.assertFalse(r["game_modified"])
        self.assertFalse(r["installable"])
        self.assertEqual(r["current_bgxp3_baf_sha256"],S.BGXP3_BUF_SHA)


if __name__=="__main__":
    unittest.main(verbosity=2)
