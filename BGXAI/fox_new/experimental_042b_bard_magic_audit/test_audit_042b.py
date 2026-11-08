"""Read-only regression tests against user's exact archived pre-042B EET BCS.
Runs only with environment BGXAI_BCS_BASELINE and BGXAI_RELEASE_DIR.
Never writes to game or backups; release builder computes bytes in memory.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from collections import Counter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit_042b_song_spells import audit, SOURCE_SHA, PATCHED_SHA

class BardSpellRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=os.environ.get('BGXAI_BCS_BASELINE')
        released=os.environ.get('BGXAI_RELEASE_DIR')
        if not source or not released:
            raise unittest.SkipTest('Set BGXAI_BCS_BASELINE and BGXAI_RELEASE_DIR for protected offline audit')
        cls.src=Path(source)
        cls.rel=Path(released)
        sys.path.insert(0,str(cls.rel))
        from build_042b_preview import build
        from guard_source_042a import segments, action_ids
        cls.raw=cls.src.read_bytes()
        cls.output,_=build(cls.raw)
        cls.before=segments(cls.raw)
        cls.after=segments(cls.output)
        cls.ids=staticmethod(action_ids)
        cls.report=audit(cls.src,cls.rel)

    def test_01_pinned_source_sha(self):self.assertEqual(hashlib.sha256(self.raw).hexdigest(),SOURCE_SHA)
    def test_02_pinned_patch_sha(self):self.assertEqual(hashlib.sha256(self.output).hexdigest(),PATCHED_SHA)
    def test_03_all_checks_pass(self):self.assertTrue(self.report['all_checks_passed'])
    def test_04_31_audit_conditions(self):self.assertEqual(self.report['checks_count'],31)
    def test_05_block_count(self):self.assertEqual(len(self.before),len(self.after));self.assertEqual(len(self.after),1057)
    def test_06_icon_toggle_exact(self):self.assertEqual(self.before[:7],self.after[:7])
    def test_07_original_songs(self):self.assertEqual([i for i,b in enumerate(self.before,1) if 296 in self.ids(b)],[987,988])
    def test_08_song_bytes_preserved(self):self.assertEqual([self.before[i-1] for i in (987,988)],[self.after[i-1] for i in (987,988)])
    def test_09_song_mode_conditions(self):self.assertTrue(all(b'LOCALSBDAI_SKILL_MODE' in self.after[i-1] for i in (987,988)))
    def test_10_spells_31(self):self.assertEqual(sum(31 in self.ids(x) for x in self.after),275)
    def test_11_spells_34(self):self.assertEqual(sum(34 in self.ids(x) for x in self.after),51)
    def test_12_spells_63(self):self.assertEqual(sum(63 in self.ids(x) for x in self.after),5)
    def test_13_spells_160(self):self.assertEqual(sum(160 in self.ids(x) for x in self.after),42)
    def test_14_song_prior_to_guard(self):self.assertLess(988,1032)
    def test_15_guard_prior_to_autoattack(self):self.assertLess(1042,1043)
    def test_16_guard_action_preserved(self):self.assertTrue(all(self.ids(self.after[i-1])==[115,87] for i in range(1032,1043)))
    def test_17_attack_bounded(self):self.assertEqual([self.ids(self.after[i-1]) for i in (1043,1056)],[[105],[105]])
    def test_18_all_pre_1032_identical(self):self.assertEqual(self.before[:1031],self.after[:1031])
    def test_19_attack_opcode_deltas_only(self):
        a=Counter(n for x in self.before for n in self.ids(x))
        b=Counter(n for x in self.after for n in self.ids(x))
        self.assertEqual(a[3],2);self.assertEqual(b[3],0);self.assertEqual(a[105],0);self.assertEqual(b[105],2)
        self.assertTrue(all(a[k]==b[k] for k in set(a)|set(b) if k not in (3,105)))
    def test_20_no_output_to_game(self):
        self.assertEqual(self.report['status'],'PASS - COMPILED BCS NON-INTERFERENCE ONLY; GAMEPLAY UNVERIFIED')
    def test_21_tamper_baseline_refused(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as d:
            t=Path(d)/'tampered.BCS'
            t.write_bytes(self.raw[:-1]+bytes([self.raw[-1]^1]))
            with self.assertRaises(ValueError):audit(t,self.rel)
    def test_22_spell_aggregate_counts_unchanged(self):
        for k in (31,34,63,160):
            self.assertEqual(sum(k in self.ids(x) for x in self.before),sum(k in self.ids(x) for x in self.after))
    def test_23_spell_block_bytes_unchanged(self):
        for i,orig in enumerate(self.before,1):
            if any(k in self.ids(orig) for k in (31,34,63,160)):
                self.assertEqual(orig,self.after[i-1])
    def test_24_all_pre_guard_trigger_conditions_identical(self):
        self.assertTrue(all(self.before[i-1]==self.after[i-1] for i in range(1,1032)))

if __name__=='__main__':unittest.main(verbosity=2)
