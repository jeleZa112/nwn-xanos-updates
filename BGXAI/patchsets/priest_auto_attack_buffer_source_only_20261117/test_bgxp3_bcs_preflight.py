#!/usr/bin/env python3
"""Synthetic BCS topology tests; all tests run without EET."""
from __future__ import annotations
import hashlib
import unittest

import BGXP3_BCS_PREFLIGHT_SOURCE_ONLY as Q
import BGXP2_BCS_PATCH as P


def bcs_block(actions: list[int], mark: bytes = b"45") -> bytes:
    data = b"CR\nCO\nTR\nRS\nRE\nRS\nBGXR_ROLE BGX38_GUARD BGX66_S_HEAL_SLOT " + mark + b"\n"
    for n in actions:
        data += b"AC\n" + str(n).encode() + b"OB\nX\n"
    return data + b"CR\n"


class TestBGXP3ReadOnlyTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seq = [[115, 31]] * 24 + [[115, 31], [115, 105], [115, 31], [115, 105]]
        cls.old = b"SC\n" + b"".join(bcs_block(a) for a in seq) + b"SC\n"
        cls.new = b"SC\n" + b"".join(
            bcs_block(a, b"60" if i == 27 else b"45") for i, a in enumerate(seq)
        ) + b"SC\n"
        cls.live = b"SC\n" + bcs_block([115, 31]) * Q.PRIOR_BGXPR_BLOCKS + cls.old[3:]
        cls.live_sha = hashlib.sha256(cls.live).hexdigest()

    def test_exact_1157_compiled_blocks_preserved(self):
        out, report = Q.assemble(self.live, self.old, self.new, self.live_sha)
        before = P.chunks(self.live, 1158)
        after = P.chunks(out, 1158)
        self.assertEqual(before[:1157], after[:1157])
        self.assertNotEqual(before[-1], after[-1])
        self.assertEqual(report["preserved_blocks_exact"], 1157)
        self.assertEqual(report["total_blocks"], 1158)
        self.assertFalse(report["game_modified"])

    def test_wrong_live_hash_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "LIVE_BGXP2_BCS_SHA_DRIFT"):
            Q.assemble(self.live + b"X", self.old, self.new, self.live_sha)

    def test_prior_block_changed_rejected(self):
        invalid = self.new.replace(b" 45\n", b" 60\n", 1)
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_PRIOR_27"):
            Q.assemble(self.live, self.old, invalid, self.live_sha)

    def test_native_old_fragment_must_match_live(self):
        wrong = self.old.replace(b" 45\n", b" 46\n", 1)
        with self.assertRaisesRegex(ValueError, "INSTALLED_BGXP2_FRAGMENT_DIFFERS"):
            Q.assemble(self.live, wrong, self.new, self.live_sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
