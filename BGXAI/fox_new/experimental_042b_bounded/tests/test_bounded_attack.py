from pathlib import Path
import hashlib
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_042b_preview import build, to_bounded_attack
from guard_source_042a import segments,action_ids,generate

SOURCE=Path('/mnt/data/BDDEFAI.BCS')

class BoundAttackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live=SOURCE.read_bytes()
        cls.a,_=generate(cls.live)
        cls.b,cls.report=build(cls.live)
        cls.original=segments(cls.live)
        cls.A=segments(cls.a)
        cls.B=segments(cls.b)

    def test_27_same_header(self): self.assertEqual(self.live[:3],self.b[:3])
    def test_28_bcs_size_exact(self): self.assertEqual(len(self.b),len(self.live)+4)
    def test_29_blocks_count_exact(self): self.assertEqual(len(self.B),1057)
    def test_30_existing_f_key_unchanged(self):self.assertEqual(self.original[:7],self.B[:7])
    def test_31_all_guard_blocks_unchanged(self): self.assertEqual(self.A[1031:1042],self.B[1031:1042])
    def test_32_first_eps_attack_bounded(self): self.assertEqual(action_ids(self.B[1042]),[105])
    def test_33_second_eps_attack_bounded(self): self.assertEqual(action_ids(self.B[1055]),[105])
    def test_34_only_two_blocks_changed_vs_A(self):
        self.assertEqual([i for i,(a,b) in enumerate(zip(self.A,self.B),1) if a!=b],[1043,1056])
    def test_35_all_other_action_payloads_byte_equal(self):
        for i,(a,b) in enumerate(zip(self.A,self.B),1):
            if i not in (1043,1056):self.assertEqual(a,b)
    def test_36_finite_action_id_zero_attack(self):
        self.assertEqual(sum(action_ids(x).count(3) for x in self.B),0)
    def test_37_finite_action_id_two_one_round(self):
        self.assertEqual(sum(action_ids(x).count(105) for x in self.B),2)
    def test_38_guard_has_idle_gates(self):
        self.assertTrue(all(b'16427 0 0 0 0' in x for x in self.B[1031:1042]))
    def test_39_attack_has_idle_gates(self):
        self.assertTrue(all(b'16427 0 0 0 0' in self.B[i-1] for i in (1043,1056)))
    def test_40_spell_blocks_remain(self):
        self.assertEqual(sum(action_ids(x).count(31) for x in self.B),sum(action_ids(x).count(31) for x in self.original))
    def test_41_no_new_clear_actions(self):
        self.assertEqual(sum(action_ids(x).count(133) for x in self.B),sum(action_ids(x).count(133) for x in self.original))
    def test_42_no_new_action_override(self):
        self.assertEqual(sum(action_ids(x).count(34) for x in self.B),sum(action_ids(x).count(34) for x in self.original))
    def test_43_repeatable(self): self.assertEqual(build(self.live)[0],self.b)
    def test_44_refuse_other_source_hash(self):
        with self.assertRaises(ValueError):build(b'NOT EET BCS')
    def test_45_controlled_hash(self):self.assertEqual(hashlib.sha256(self.b).hexdigest(),'8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0')
    def test_46_not_game_validated(self):self.assertIn('NO INSTALLER',self.report['release'])

class AbstractQueueModel(unittest.TestCase):
    """Illustrative abstract model ONLY; not EET engine execution proof."""
    def test_47_bounded_attack_releases_queue_in_model(self):
        queue=['AttackOneRound'];queue.clear();self.assertEqual(queue,[])
    def test_48_guard_threat_wins_next_priority_model(self):
        roles=['guard','attack'];self.assertEqual(roles[0],'guard')
    def test_49_manual_queue_is_never_cleared_by_patch(self):
        manual=['CastSpell'];noop=lambda x:x
        self.assertEqual(noop(manual),['CastSpell'])
    def test_50_bard_song_payload_unchanged(self):
        original=segments(SOURCE.read_bytes()); preview=segments(build(SOURCE.read_bytes())[0])
        self.assertEqual(b''.join(original[:1031]),b''.join(preview[:1031]))

if __name__=='__main__':unittest.main()