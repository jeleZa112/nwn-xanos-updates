#!/usr/bin/env python3
"""Source-only V4 regression: automatic attacks and weapon-target selection never admit party members."""
from pathlib import Path
import re,unittest
P=Path(__file__).with_name("BGXRANGED_V4_NO_FRIEND_ATTACK.baf")
class NoFriendlyAttack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=P.read_text(encoding="ascii")
        cls.blocks=re.findall(r"(?ms)^IF\n(.*?)^THEN\n(.*?)^END\s*$",s)
    def test_three_blocks(self):self.assertEqual(len(self.blocks),3)
    def test_every_target_has_both_friendly_guards(self):
        for trigger,actions in self.blocks:
            self.assertIn("!InParty(NearestEnemyOf(Myself))",trigger)
            self.assertIn("!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)",trigger)
            self.assertIn("See(NearestEnemyOf(Myself))",trigger)
    def test_attacks_are_not_triggered_when_wounded(self):
        t,a=self.blocks[2]
        self.assertIn("HPPercentGT(Myself,75)",t)
        self.assertIn("AttackOneRound(NearestEnemyOf(Myself))",a)
    def test_weapon_selection_not_hp_blocked(self):
        for t,a in self.blocks[:2]:
            self.assertNotIn("HPPercentGT",t)
            self.assertIn('Global("BGX66_S_HEAL_SLOT","LOCALS",0)',t)
            self.assertIn("ActionListEmpty()",t)
        self.assertIn("EquipMostDamagingMelee()",self.blocks[0][1])
        self.assertIn("EquipRanged()",self.blocks[1][1])
    def test_no_engagement_or_forced_actions_in_weapon_selection(self):
        for t,a in self.blocks[:2]:
            self.assertNotIn("Attack(",a)
            self.assertNotIn("AttackOneRound(",a)
            self.assertNotIn("MoveTo",a)
    def test_no_persistent_protection_or_destructive_inventory(self):
        s=P.read_text(encoding="ascii")
        for bad in ("ProtectObject(", "FillSlot(", "XEquipItem(", "ClearActions(", "MoveToPoint(", "SetGlobal("):
            self.assertNotIn(bad,s)
if __name__=="__main__":unittest.main()
