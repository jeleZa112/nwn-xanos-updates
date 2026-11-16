#!/usr/bin/env python3
"""Offline regression tests; never modify the game."""
import hashlib
import unittest
import BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY as P


class TestBGXP3AutoAttackBuffer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = P.SOURCE.read_bytes()
        cls.patched = P.candidate(cls.original)
        cls.before = cls.original.decode("utf-8")
        cls.after = cls.patched.decode("utf-8")

    def test_baseline_byte_exact(self):
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), P.BASE_SHA256)

    def test_only_last_auto_attack_changed(self):
        marker = P.AUTO_ATTACK_MARKER
        self.assertEqual(self.before.split(marker, 1)[0], self.after.split(marker, 1)[0])
        self.assertNotEqual(self.before.split(marker, 1)[1], self.after.split(marker, 1)[1])
        self.assertEqual(self.after.count("\nIF\n"), 28)
        self.assertEqual(self.after.count("AttackOneRound("), 2)
        self.assertEqual(self.after.count("    Spell("), 26)

    def test_buffer_60_protects_50pct_case(self):
        tail = self.after.split(P.AUTO_ATTACK_MARKER, 1)[1]
        for i in range(1, 7):
            self.assertIn(f"!HPPercentLT(Player{i},60)", tail)
            self.assertNotIn(f"!HPPercentLT(Player{i},45)", tail)
        self.assertEqual(tail.count("!HPPercentLT(Player"), 6)

    def test_combat_control_spell_unchanged(self):
        # Full prefix (27 blocks) includes both BATTLE and AUTO Command.
        old = self.before.split(P.AUTO_ATTACK_MARKER, 1)[0]
        new = self.after.split(P.AUTO_ATTACK_MARKER, 1)[0]
        self.assertEqual(old, new)
        self.assertIn("HaveSpell(CLERIC_COMMAND)", old)

    def test_idle_guard_and_no_force_actions(self):
        tail = self.after.split(P.AUTO_ATTACK_MARKER, 1)[1]
        for gate in ('ActionListEmpty()', 'Global("BGX38_GUARD","LOCALS",1)',
                     'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                     'Global("BGXR_ROLE","LOCALS",4)'):
            self.assertIn(gate, tail)
        for dangerous in ("ClearActions(", "ForceSpell(", "ActionOverride(", "MoveToObject("):
            self.assertNotIn(dangerous, tail)

    def test_fail_closed_on_baseline_drift(self):
        with self.assertRaisesRegex(ValueError, "BASELINE_SHA_MISMATCH"):
            P.candidate(self.original + b" ")

    def test_deterministic_proposal(self):
        self.assertEqual(P.candidate(self.original), self.patched)
        status = P.check()
        self.assertEqual(status["status"], "SOURCE_ONLY_CANDIDATE_VERIFIED")
        self.assertFalse(status["game_modified"])
        self.assertFalse(status["installable"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
