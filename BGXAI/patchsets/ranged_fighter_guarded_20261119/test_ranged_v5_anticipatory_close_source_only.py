#!/usr/bin/env python3
"""SOURCE ONLY: verifies minimal anticipatory 6/10 threshold delta vs V4.
Neither compilation in the user's EET nor runtime responsiveness is claimed.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=ROOT/"BGXRANGED_V4_NO_FRIEND_ATTACK.baf"
NEW=ROOT/"BGXRANGED_V5_ANTICIPATORY_CLOSE_SOURCE_ONLY.baf"

def blocks(path):
    data=path.read_text(encoding="ascii")
    matches=re.findall(r"(?ms)^IF\s*\n(.*?)^THEN\s*\n\s*RESPONSE #100\s*\n(.*?)^END\s*$",data)
    return [([v.strip() for v in cond.splitlines() if v.strip()],
             [v.strip() for v in acts.splitlines() if v.strip()])
            for cond,acts in matches]

class AnticipatoryHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=blocks(OLD)
        cls.after=blocks(NEW)
        cls.text=NEW.read_text(encoding="ascii")

    def test_exactly_three_blocks(self):
        self.assertEqual(len(self.before),3)
        self.assertEqual(len(self.after),3)

    def test_only_two_trigger_thresholds_changed(self):
        original=[(c[:],a[:]) for c,a in self.before]
        original[0][0][original[0][0].index("Range(NearestEnemyOf(Myself),4)")]="Range(NearestEnemyOf(Myself),6)"
        original[2][0][original[2][0].index("!Range(NearestEnemyOf(Myself),4)")]="!Range(NearestEnemyOf(Myself),6)"
        self.assertEqual(original,self.after)

    def test_early_melee_before_contact(self):
        self.assertIn("Range(NearestEnemyOf(Myself),6)",self.after[0][0])
        self.assertIn("EquipMostDamagingMelee()",self.after[0][1])
        self.assertNotIn("HPPercentGT(Myself,75)",self.after[0][0])

    def test_do_not_restart_ranged_attack_inside_buffer(self):
        self.assertIn("!Range(NearestEnemyOf(Myself),6)",self.after[2][0])
        self.assertIn("AttackOneRound(NearestEnemyOf(Myself))",self.after[2][1])
        self.assertIn("HPPercentGT(Myself,75)",self.after[2][0])

    def test_return_to_bow_still_far_hysteresis(self):
        self.assertIn("!Range(NearestEnemyOf(Myself),10)",self.after[1][0])
        self.assertIn("CanEquipRanged()",self.after[1][0])
        self.assertEqual(self.after[1][1],["EquipRanged()"])

    def test_party_only_nonfriendly_and_eps_protection_all_blocks(self):
        for conditions,_ in self.after:
            self.assertIn("InParty(Myself)",conditions)
            self.assertIn('Global("BGX38_GUARD","LOCALS",1)',conditions)
            self.assertIn('Global("BGX66_S_HEAL_SLOT","LOCALS",0)',conditions)
            self.assertIn("!InParty(NearestEnemyOf(Myself))",conditions)
            self.assertIn("!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)",conditions)
            self.assertIn("ActionListEmpty()",conditions)
            self.assertIn("ModalState(NONE)",conditions)

    def test_no_forced_action_or_inventory_mutation(self):
        actions="\n".join(a for _,acts in self.after for a in acts)
        for dangerous in ["ClearActions(","ClearAllActions(","ForceAttack(","XEquipItem(",
                          "FillSlot(","DropInventory(","MoveTo","ActionOverride(","Spell("]:
            self.assertNotIn(dangerous,actions)

    def test_no_naive_runtime_claims(self):
        self.assertIn("SOURCE ONLY",self.text)
        self.assertIn("does NOT interrupt",self.text)
        self.assertNotIn("BGXFENEMY_INSTALLED_VERIFIED",self.text)

if __name__=="__main__":
    unittest.main(verbosity=2)
