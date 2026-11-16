#!/usr/bin/env python3
"""BGXP4 early-heal source + synthetic BCS integrity regression, no game."""
from __future__ import annotations
import hashlib
import re
import unittest

import BGXP4_AUTO_EARLY_HEAL_SOURCE_ONLY as C
import BGXP4_NATIVE_PREFLIGHT_READ_ONLY as N
import BGXPR_BCS_PATCH as PR
import BGXP2_BCS_PATCH as CP


def block(actions: list[int], val: bytes = b"45") -> bytes:
    out=(b"CR\nCO\nTR\nRS\nRE\nRS\n"
         b"BGXR_ROLE BGX38_GUARD BGXR_HEAL_CD " + val + b"\n")
    for code in actions:
        out+=b"AC\n"+str(code).encode()+b"OB\nx\n"
    return out+b"CR\n"


def pattern(index: int) -> list[int]:
    if 24<=index<30 or (index<24 and index%2==0) or (index>=30 and index%2==0):
        return [115,31]
    return [115,22]


class TestEarlyHealSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=C.canon(C.ORIGINAL_BAF.read_bytes())
        cls.changed=C.patch(cls.original)
        cls.oldblocks=[block(pattern(i)) for i in range(42)]
        cls.newblocks=[block(pattern(i),b"70" if i in C.AUTO_CURE_BLOCKS else b"45") for i in range(42)]
        cls.old_comp=b"SC\n"+b"".join(cls.oldblocks)+b"SC\n"
        cls.new_comp=b"SC\n"+b"".join(cls.newblocks)+b"SC\n"
        cls.live=b"SC\n"+block([115,31])*1088+b"".join(cls.oldblocks)+block([115,31])*28+b"SC\n"
        cls.livehash=hashlib.sha256(cls.live).hexdigest()

    def test_source_hash_is_pinned(self):
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), C.PIN)

    def test_six_exact_auto_cure_blocks_changed(self):
        old=list(re.finditer(r"(?m)^IF\n.*?^END$",self.original.decode(),flags=re.S))
        new=list(re.finditer(r"(?m)^IF\n.*?^END$",self.changed.decode(),flags=re.S))
        self.assertEqual(len(old),42)
        self.assertEqual(len(new),42)
        changed=[i for i,(a,b) in enumerate(zip(old,new)) if a.group()!=b.group()]
        self.assertEqual(changed,list(C.AUTO_CURE_BLOCKS))
        for i in C.AUTO_CURE_BLOCKS:
            target=(i-30)//2+1
            self.assertIn(f"HPPercentLT(Player{target},70)",new[i].group())
            self.assertIn("ActionListEmpty()",new[i].group())
            self.assertIn("HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)",new[i].group())

    def test_expanded_heal_targets_four_of_six_hp(self):
        self.assertLess(4/6*100,C.NEW_THRESHOLD)
        self.assertGreater(4/6*100,C.OLD_THRESHOLD)
        self.assertLess(3/6*100,C.NEW_THRESHOLD)

    def test_no_action_queue_override(self):
        change=self.changed.decode()
        for denied in ("ClearActions(", "ActionOverride(", "ForceSpell(", "AttackOneRound("):
            self.assertNotIn(denied,change)

    def test_fail_closed_drift(self):
        with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
            C.patch(self.original+b" ")

    def test_fragment_action_and_gates(self):
        self.assertEqual(len(PR.verify_fragment(self.old_comp)),42)
        self.assertEqual(len(PR.verify_fragment(self.new_comp)),42)

    def test_synthetic_bcs_replace_only_six(self):
        compiled,info=N.assemble(self.live,self.old_comp,self.new_comp,self.livehash)
        oldblocks=CP.chunks(self.live,1158)
        newblocks=CP.chunks(compiled,1158)
        diffs=[i for i,(a,b) in enumerate(zip(oldblocks,newblocks)) if a!=b]
        self.assertEqual(diffs,list(N.EXPECTED_INDICES))
        self.assertEqual(info["preserved_blocks_exact"],1152)
        self.assertEqual(info["total_blocks"],1158)
        self.assertTrue(info["current_BGXP3_attack_block_preserved"])
        self.assertFalse(info["game_modified"])

    def test_old_native_fragment_mismatch_rejected(self):
        bad=self.old_comp.replace(b" 45\n",b" 46\n",1)
        with self.assertRaisesRegex(ValueError,"OLD_BGXPR_NOT_EQUAL"):
            N.assemble(self.live,bad,self.new_comp,self.livehash)

    def test_non_cure_new_fragment_modification_rejected(self):
        bad=self.new_comp.replace(b" 45\n",b" 55\n",1)
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_BGXPR_CURE_BLOCK_DELTA"):
            N.assemble(self.live,self.old_comp,bad,self.livehash)

    def test_live_sha_drift_rejected(self):
        with self.assertRaisesRegex(ValueError,"INSTALLED_BCS_SHA_MISMATCH"):
            N.assemble(self.live+b"x",self.old_comp,self.new_comp,self.livehash)

    def test_same_source_is_deterministic(self):
        self.assertEqual(C.patch(self.original),self.changed)
        self.assertEqual(C.report()["status"],"BGXP4_SOURCE_ONLY_EARLY_HEAL_CANDIDATE")


if __name__=="__main__":
    unittest.main(verbosity=2)
