#!/usr/bin/env python3
"""SOURCE ONLY: match saved DPLAYER two-block action contract; no install/IO game."""
from pathlib import Path
import unittest
from BGXRANGED_V5_NATIVE_CANDIDATE_READONLY import parse_blocks

BASE=Path(__file__).resolve().parent
CAND=BASE/"BGXRANGED_V6_DPLAYER_CLOSE_GUARD_SOURCE_ONLY.baf"
GUARD_HEAD="OR(5)"
COMMON=(
    "!InParty(Myself)",
    "!Class(Myself,FIGHTER)",
    '!Global("BGX38_GUARD","LOCALS",1)',
    "!IsWeaponRanged(Myself)",
)
EXPECTED=[
(
 ("InWeaponRange(NearestEnemyOf(Myself))",
  "ActionListEmpty()",
  "!InParty(NearestEnemyOf(Myself))",
  "!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)"),
 ("AttackOneRound(NearestEnemyOf(Myself))",),
 "!Range(NearestEnemyOf(Myself),6)"
),
(
 ("AttackedBy([ANYONE],DEFAULT)",
  "!InParty(LastAttackerOf(Myself))",
  "!Allegiance(LastAttackerOf(Myself),GOODCUTOFF)"),
 ("AttackOneRound(LastAttackerOf(Myself))",),
 "!Range(LastAttackerOf(Myself),6)"
)]

def duplicate_attack_should_start(in_party,fighter,guarded,ranged_weapon,near):
    # The fifth trigger means "target not near": it is the logical negation
    # of Range(Target,6), not a guarantee that a currently running attack stops.
    return (not in_party or not fighter or not guarded or
            not ranged_weapon or not near)

class CloseRangeDPLAYER(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=CAND.read_text("ascii")
        cls.blocks=parse_blocks(cls.raw)

    def test_two_blocks_actions_preserved(self):
        self.assertEqual(len(self.blocks),2)
        for i,(_,expected_actions,_) in enumerate(EXPECTED):
            self.assertEqual(self.blocks[i][1],expected_actions)

    def test_only_five_veto_triggers_added_to_current_dplayer(self):
        for i,(base,_,range_guard) in enumerate(EXPECTED):
            triggers,actions=self.blocks[i]
            self.assertEqual(triggers[:len(base)],base)
            self.assertEqual(triggers[len(base):],(GUARD_HEAD,*COMMON,range_guard))
            self.assertEqual(len(triggers),len(base)+6)

    def test_duplicate_attack_guard_holds_at_close(self):
        self.assertFalse(duplicate_attack_should_start(True,True,True,True,True))

    def test_non_party_dplayer_unaffected(self):
        self.assertTrue(duplicate_attack_should_start(False,True,True,True,True))

    def test_non_fighter_party_unaffected(self):
        self.assertTrue(duplicate_attack_should_start(True,False,True,True,True))

    def test_guard_off_unaffected(self):
        self.assertTrue(duplicate_attack_should_start(True,True,False,True,True))

    def test_melee_already_selected_unaffected(self):
        self.assertTrue(duplicate_attack_should_start(True,True,True,False,True))

    def test_ranged_attack_outside_contact_unaffected(self):
        self.assertTrue(duplicate_attack_should_start(True,True,True,True,False))

    def test_do_not_change_default_reactive_last_attacker(self):
        self.assertEqual(self.blocks[1][1],("AttackOneRound(LastAttackerOf(Myself))",))
        self.assertIn("AttackedBy([ANYONE],DEFAULT)",self.blocks[1][0])

    def test_never_inject_direct_equip_or_queue_clear(self):
        actions="\n".join(action for _,actions in self.blocks for action in actions)
        for bad in ("ClearActions(","ActionOverride(","EquipRanged(",
                    "EquipMostDamagingMelee(","ForceAttack(","FillSlot(",
                    "DropInventory(","MoveToObject(","Spell("):
            self.assertNotIn(bad,actions)
        self.assertEqual(actions.count("AttackOneRound("),2)

    def test_unverified_candidate_must_not_claim_live_pass(self):
        self.assertIn("SOURCE ONLY, NOT INSTALLED",self.raw)
        self.assertIn("not cancel queued attacks",self.raw)
        self.assertIn("LIVE not yet verified",self.raw)

if __name__=="__main__":
    unittest.main(verbosity=2)
