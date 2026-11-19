"""Static safety checks for the BGXAI fighter ranged pilot (not runtime proof)."""
from pathlib import Path
import hashlib
import unittest

BAF = Path(__file__).with_name("BGX_RANGED_FIGHTER.baf")
PIN = "af7ef6e4287a346fd9ad66ac8458e39eb5d2a0e45bb7f52cabc7b5d266ee1546"

class RangedSourceTests(unittest.TestCase):
    def test_exact_source(self):
        self.assertEqual(hashlib.sha256(BAF.read_bytes()).hexdigest(), PIN)
    def test_guardrails(self):
        source = BAF.read_text(encoding="utf-8")
        for required in (
            "Class(Myself,FIGHTER)", 'Global("BGX38_GUARD","LOCALS",1)',
            'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
            "ActionListEmpty()", "HPPercentGT(Myself,75)",
            "IsWeaponRanged(Myself)", "InWeaponRange(NearestEnemyOf(Myself))",
            "!Range(NearestEnemyOf(Myself),4)",
            "!InParty(NearestEnemyOf(Myself))",
            "AttackOneRound(NearestEnemyOf(Myself))",
        ):
            self.assertIn(required, source)
        self.assertEqual(source.count("\nIF\n"), 1)
        for forbidden in ("MoveToObject(", "Spell(", "ForceSpell(", "EquipItem(", "Attack(NearestEnemyOf", "Continue()"):
            self.assertNotIn(forbidden, source)

if __name__ == "__main__":
    unittest.main()
