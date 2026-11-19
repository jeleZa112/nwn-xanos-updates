#!/usr/bin/env python3
"""Source-only regression tests. These do not establish gameplay correctness."""
from pathlib import Path
import re, unittest
BAF=Path(__file__).with_name("BGXRANGED_V2_MELEE_HANDOFF.baf")
class FighterHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=BAF.read_text(encoding="utf-8")
        cls.blocks=re.findall(r"(?m)^IF\n(.*?)^THEN\n(.*?)^END\s*$",cls.text,re.S|re.M)
    def test_three_blocks(self):self.assertEqual(len(self.blocks),3)
    def test_melee_first(self):
        t,a=self.blocks[0]
        self.assertIn("IsWeaponRanged(Myself)",t)
        self.assertIn("Range(NearestEnemyOf(Myself),4)",t)
        self.assertIn("EquipMostDamagingMelee()",a)
    def test_return_to_ranged_hysteresis_and_ammo(self):
        t,a=self.blocks[1]
        for x in ("!IsWeaponRanged(Myself)","CanEquipRanged()","!Range(NearestEnemyOf(Myself),10)"):
            self.assertIn(x,t)
        self.assertIn("EquipRanged()",a)
    def test_shoot_no_closer_than_four(self):
        t,a=self.blocks[2]
        self.assertIn("!Range(NearestEnemyOf(Myself),4)",t)
        self.assertIn("InWeaponRange(NearestEnemyOf(Myself))",t)
        self.assertIn("AttackOneRound(NearestEnemyOf(Myself))",a)
    def test_no_forced_movement_or_casting(self):
        for _,a in self.blocks:
            self.assertNotRegex(a,r"(?i)\b(?:MoveToObject|MoveToPoint|RunAwayFrom|Spell|ForceSpell|ReallyForceSpell)\s*\(")
    def test_common_safety_gate(self):
        for t,_ in self.blocks:
            for x in ("Class(Myself,FIGHTER)",'Global("BGX38_GUARD","LOCALS",1)',
                      'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',"ActionListEmpty()",
                      "ModalState(NONE)","HPPercentGT(Myself,75)",
                      "!StateCheck(Myself,STATE_HELPLESS)"):
                self.assertIn(x,t)
    def test_no_global_switch(self):
        for _,a in self.blocks:self.assertNotIn("SetGlobal(",a)
    def test_no_auto_multi_or_dual(self):
        self.assertNotIn("FIGHTER_MAGE",self.text)
        self.assertNotIn("FIGHTER_THIEF",self.text)
    def test_source_is_not_installed(self):
        self.assertIn("NOT INSTALLED",self.text)
if __name__=="__main__":unittest.main()
