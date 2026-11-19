#!/usr/bin/env python3
"""Read-only V3 guards: weapon selection must not be blocked by low HP.
Engine native WeiDU compilation + actual gameplay still required.
"""
import re, unittest
from pathlib import Path
BAF=Path(__file__).with_name("BGXRANGED_V3_MELEE_HANDOFF.baf")
class V3WeaponSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=BAF.read_text(encoding="ascii")
        cls.blocks=re.findall(r"(?m)^IF\n(.*?)^THEN\n(.*?)^END\s*$",s,re.S|re.M)
    def test_three_blocks(self):self.assertEqual(len(self.blocks),3)
    def test_low_hp_melee_switch(self):
        triggers,actions=self.blocks[0]
        self.assertIn("Range(NearestEnemyOf(Myself),4)",triggers)
        self.assertIn("HasWeaponEquiped(Myself)",triggers)
        self.assertIn("EquipMostDamagingMelee()",actions)
        self.assertNotIn("HPPercentGT(",triggers)
        self.assertNotIn("Attack(",actions)
    def test_low_hp_ranged_switch(self):
        triggers,actions=self.blocks[1]
        self.assertIn("CanEquipRanged()",triggers)
        self.assertIn("!Range(NearestEnemyOf(Myself),10)",triggers)
        self.assertIn("EquipRanged()",actions)
        self.assertNotIn("HPPercentGT(",triggers)
    def test_offensive_fire_remains_hp_gated(self):
        triggers,actions=self.blocks[2]
        self.assertIn("HPPercentGT(Myself,75)",triggers)
        self.assertIn("AttackOneRound(NearestEnemyOf(Myself))",actions)
    def test_injury_does_not_override_eps(self):
        for t,a in self.blocks:
            self.assertIn('Global("BGX66_S_HEAL_SLOT","LOCALS",0)',t)
            self.assertIn("ActionListEmpty()",t)
            self.assertIn("ModalState(NONE)",t)
            self.assertNotIn("MoveTo",a)
    def test_no_destructive_inventory_autoequip(self):
        alltext=BAF.read_text(encoding="ascii")
        self.assertNotIn("FillSlot(",alltext)
        self.assertNotIn("XEquipItem(",alltext)
        self.assertNotIn("DropInventory(",alltext)
if __name__=="__main__":unittest.main()
