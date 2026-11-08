import hashlib
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_042_preview import generate,segments,inspect_source,sha,PIN_SHA,ACTION,action_ids,ATTACK_IDS,GUARD_IDS

SOURCE=Path(__file__).resolve().parents[2] / 'BDDEFAI.BCS'
if not SOURCE.is_file():
    SOURCE=Path('/mnt/data/BDDEFAI.BCS')

class LiveScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=SOURCE.read_bytes()
        cls.after,cls.report=generate(cls.before)
        cls.a=segments(cls.before)
        cls.b=segments(cls.after)

    def test_01_pin_exact(self): self.assertEqual(sha(self.before),PIN_SHA)
    def test_02_size_same(self): self.assertEqual(len(self.before),len(self.after))
    def test_03_full_bcs_parse(self):self.assertEqual(len(self.a),len(self.b))
    def test_04_expected_blocks(self):self.assertEqual(len(self.b),1057)
    def test_05_old_guard(self):self.assertEqual([action_ids(self.a[i-1]) for i in GUARD_IDS],[[115,87]]*11)
    def test_06_new_guard(self):self.assertEqual([action_ids(self.b[i-1]) for i in range(1032,1043)],[[115,87]]*11)
    def test_07_old_attack(self):self.assertEqual([action_ids(self.a[i-1]) for i in ATTACK_IDS],[[3],[3]])
    def test_08_new_attack(self):self.assertEqual([action_ids(self.b[i-1]) for i in (1043,1056)],[[3],[3]])
    def test_09_original_prefix_untouched(self):self.assertEqual(self.a[:1031],self.b[:1031])
    def test_10_original_mode_controls_untouched(self):self.assertEqual(self.a[:7],self.b[:7])
    def test_11_every_byte_block_preserved(self):
        self.assertEqual(sorted(self.a),sorted(self.b))
    def test_12_spell_action_counts(self):
        def ct(blocks):return sum(action_ids(b).count(31) for b in blocks)
        self.assertEqual(ct(self.a),ct(self.b))
    def test_13_queues_preserved(self):
        self.assertTrue(all(b'16427 0 0 0 0' in self.b[i-1] for i in range(1032,1043)))
    def test_14_attack_gate_preserved(self):
        self.assertTrue(all(b'LOCALSBDAI_DISABLE_ATTACK' in self.b[i-1] for i in (1043,1056)))
    def test_15_no_new_control_actions(self):
        self.assertEqual(sum(action_ids(b).count(103) for b in self.b),sum(action_ids(b).count(103) for b in self.a))
    def test_16_result_reproducible(self):
        self.assertEqual(self.after, generate(self.before)[0])
    def test_17_hash_gate_rejects_mutation(self):
        mutated=bytearray(self.before);mutated[1234] ^= 1
        with self.assertRaisesRegex(ValueError,'HASH GATE'):generate(bytes(mutated))
    def test_18_hash_gate_rejects_other_length(self):
        with self.assertRaisesRegex(ValueError,'HASH GATE'):generate(self.before[:-10])
    def test_19_unchanged_later_blocks(self):
        # All nonmoved later blocks occur in their original relative order.
        omitted=set(GUARD_IDS)
        self.assertEqual([b for i,b in enumerate(self.a,1) if i not in omitted],
                         [b for i,b in enumerate(self.b,1) if i not in range(1032,1043)])
    def test_20_report_disclaims_runtime(self):
        self.assertIn('NOT INSTALLED',self.report['scope'])
        self.assertIn('not interrupted',self.report['known_gap'])

class AbstractPriorityTests(unittest.TestCase):
    """Only a model of logical branches, *not* the Infinity Engine scheduler."""
    @staticmethod
    def first_action(guard,threat,queue_empty,attack_possible,moved):
        priorities=('guard','attack') if moved else ('attack','guard')
        for role in priorities:
            if role=='guard' and guard and threat and queue_empty:return 'ProtectObject'
            if role=='attack' and attack_possible and queue_empty:return 'Attack'
        return 'none'
    def test_21_guard_off_preserves_attack(self):
        self.assertEqual(self.first_action(False,True,True,True,True),'Attack')
    def test_22_guard_with_threat_prioritized(self):
        self.assertEqual(self.first_action(True,True,True,True,True),'ProtectObject')
    def test_23_original_would_attack(self):
        self.assertEqual(self.first_action(True,True,True,True,False),'Attack')
    def test_24_without_threat_allows_attack(self):
        self.assertEqual(self.first_action(True,False,True,True,True),'Attack')
    def test_25_busy_queue_does_not_interrupt(self):
        self.assertEqual(self.first_action(True,True,False,True,True),'none')
    def test_26_no_enemy_no_guard(self):
        self.assertEqual(self.first_action(True,False,True,False,True),'none')

if __name__=='__main__':unittest.main()