#!/usr/bin/env python3
"""BGXP5 exact synthetic BCS topology; no EET, no install."""
from __future__ import annotations
import hashlib
import unittest
import BGXP5_BCS_PREFLIGHT_READ_ONLY as N


def block(actions:list[int],tag:bytes=b"OLD") -> bytes:
    b=(b"CR\nCO\nTR\nRS\nRE\nRS\n"
       b"BGXR_ROLE BGX38_GUARD BGX66_S_HEAL_SLOT BGXR_HEAL_CD "+tag+b"\n")
    for n in actions:
        b+=b"AC\n"+str(n).encode()+b"OB\nx\n"
    return b+b"CR\n"


def fragment(blocks:list[bytes])->bytes:
    return b"SC\n"+b"".join(blocks)+b"SC\n"


class TestBGXP5BCS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        codes=[[115,31]]*24+[[115,31],[115,105],[115,31],[115,105]]
        cls.old_blocks=[block(c) for c in codes]
        cls.new_blocks=[block(c,b"GUARDED" if i in (24,25,26,27) else b"OLD") for i,c in enumerate(codes)]
        cls.live=b"SC\n"+block([115,31],b"PREVIOUS")*1130+fragment(cls.old_blocks)[3:]
        cls.priority=fragment([block([115,31],b"HEAL") for _ in range(12)])
        cls.orig=fragment(cls.old_blocks)
        cls.new=fragment(cls.new_blocks)
        cls.pin=hashlib.sha256(cls.live).hexdigest()

    def test_1154_original_blocks_preserved_and_12_priority_blocks_prepend(self):
        candidate,info=N.assemble(self.live,self.orig,self.new,self.priority,self.pin)
        old=N.P.chunks(self.live,1158)
        new=N.P.chunks(candidate,1170)
        self.assertEqual(new[:12],N.priority_compiled_blocks(self.priority)[:-1]+
                         [N.priority_compiled_blocks(self.priority)[-1][:-3]])
        for i in range(1158):
            if i not in (1154,1155,1156,1157):
                self.assertEqual(new[i+12],old[i])
        self.assertEqual(info["new_total_blocks"],1170)
        self.assertEqual(info["old_blocks_preserved_exact"],1154)
        self.assertFalse(info["game_modified"])

    def test_last_four_hostile_checks_changed_only(self):
        out,_=N.assemble(self.live,self.orig,self.new,self.priority,self.pin)
        original=N.P.chunks(self.live,1158)
        updated=N.P.chunks(out,1170)
        for i in range(1154,1158):
            self.assertNotEqual(original[i],updated[i+12])
            self.assertIn(b"GUARDED",updated[i+12])

    def test_reject_live_hash_drift(self):
        with self.assertRaisesRegex(ValueError,"LIVE_BGXP3_BCS_SHA_MISMATCH"):
            N.assemble(self.live+b"X",self.orig,self.new,self.priority,self.pin)

    def test_reject_native_fragment_mismatch(self):
        tampered=self.orig.replace(b"OLD",b"EVIL",1)
        with self.assertRaisesRegex(ValueError,"OLD_BGXP3_NATIVE_FRAGMENT_NOT_EQUAL_LIVE"):
            N.assemble(self.live,tampered,self.new,self.priority,self.pin)

    def test_reject_previous_support_spell_modification(self):
        changed=self.new.replace(b"OLD",b"OTHER",1)
        with self.assertRaisesRegex(ValueError,"NON_COMBAT_FRAGMENT_CHANGE"):
            N.assemble(self.live,self.orig,changed,self.priority,self.pin)

    def test_reject_wrong_heal_actions(self):
        wrong=fragment([block([115,22],b"HEAL")]+[block([115,31],b"HEAL") for _ in range(11)])
        with self.assertRaisesRegex(ValueError,"HEAL_COMPILED_ACTIONS_UNEXPECTED"):
            N.assemble(self.live,self.orig,self.new,wrong,self.pin)

    def test_reject_missing_heal_guard(self):
        wrong=self.priority.replace(b"BGXR_ROLE",b"OTHER_ROLE",1)
        with self.assertRaisesRegex(ValueError,"MISSING_COMPILED_HEAL_GATE"):
            N.assemble(self.live,self.orig,self.new,wrong,self.pin)


if __name__=="__main__":
    unittest.main(verbosity=2)
