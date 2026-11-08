#!/usr/bin/env python3
"""Offline exact-BSC invariants. Requires original verified 042B in local/private working area."""
from __future__ import annotations
import unittest,hashlib
from pathlib import Path
from preview_guard_ranges_043 import preview,blocks,change_guard,TR_RANGE,sha

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'BGXAI_042B_REVIEW'/'BDDEFAI_042B_VERIFY_ONLY.BCS'

class TestRangePreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=SOURCE.read_bytes();cls.result,cls.meta=preview(cls.original)
    def test_pinned_input(self): self.assertEqual(sha(self.original),'8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0')
    def test_report_matches_real_parameters(self):
        self.assertEqual(self.meta['player1_enemy_distance'], {'from':8,'to':9})
        self.assertEqual(self.meta['player2_6_enemy_distance'], {'from':7,'to':9})
    def test_length(self): self.assertEqual(len(self.original),len(self.result))
    def test_blocks(self): self.assertEqual(len(blocks(self.result)),1057)
    def test_exact_indices(self): self.assertEqual(self.meta['changed_blocks'],list(range(1032,1043)))
    def test_first_1031_identical(self):self.assertEqual(blocks(self.original)[:1031],blocks(self.result)[:1031])
    def test_last_15_identical(self):self.assertEqual(blocks(self.original)[1042:],blocks(self.result)[1042:])
    def test_song_and_spells_identical(self):
        o,r=blocks(self.original),blocks(self.result)
        for i in (1,2,7,987,988,1031,1043,1056,1057):self.assertEqual(o[i-1],r[i-1])
    def test_hero_guard_still_ProtectObject(self):self.assertIn(b'AC\n87OB\n',blocks(self.result)[1031])
    def test_guard_11_still_ProtectObject(self):self.assertTrue(all(b'AC\n87OB\n' in b for b in blocks(self.result)[1031:1042]))
    def test_range_two(self):
        for i,b in enumerate(blocks(self.result)[1031:1042]):
            r=list(TR_RANGE.finditer(b));self.assertEqual(len(r),2)
            self.assertEqual([int(x.group(2)) for x in r],[10,9])
    def test_only_guard_range_latin_numeric_bytes(self):
        o,r=blocks(self.original),blocks(self.result)
        for a,b in zip(o[1031:1042],r[1031:1042]):
            differing=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            self.assertEqual(len(differing),1)
            self.assertIn(b[differing[0]]-a[differing[0]],(1,2))
    def test_mismatch_rejected(self):
        data=bytearray(self.original);data[300]^=1
        with self.assertRaisesRegex(ValueError,'SHA256'):preview(bytes(data))
    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(ValueError,'SHA256'):preview(self.original+b'x')
    def test_wrong_slot_rejected(self):
        with self.assertRaisesRegex(ValueError,'target selector'):change_guard(blocks(self.original)[1032],hero=False,slot=21)
    def test_same_target_mismatched_range_rejected(self):
        with self.assertRaisesRegex(ValueError,'distance trigger'):change_guard(blocks(self.result)[1031],hero=True,slot=21)
    def test_not_game_verified(self):self.assertFalse(self.meta['gameplay_runtime_verified'])

if __name__=='__main__':unittest.main()
