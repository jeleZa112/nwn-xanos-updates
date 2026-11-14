import unittest
from pathlib import Path
from audit_bcs_074 import (PIN_041_BLOCKS, PIN_041_SHA, UnsafeOrUnexpectedBCS,
                           audit_041, parse_lossless, source_066s_layout, positions)
SNAPSHOT=Path('/mnt/data/bg074_inputs/BDDEFAI_EPS18_4_BGXAI041_LIVE_20261108.BCS')
class TestBCSAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=SNAPSHOT.read_bytes()
        cls.chunks=parse_lossless(cls.data)
        cls.out=audit_041(cls.data)
    def test_real_file_is_lossless(self):
        self.assertEqual(b'SC\n'+b''.join(self.chunks)+b'SC\n',self.data)
    def test_actual_fixture_sha(self):self.assertEqual(self.out['sha256'],PIN_041_SHA)
    def test_all_1057_blocks(self):self.assertEqual(len(self.chunks),PIN_041_BLOCKS)
    def test_f_key_guard_first_seven(self):self.assertEqual(self.out['f_guard_marker_blocks'][:7],list(range(1,8)))
    def test_original_eps_attack_mode_exists(self):self.assertGreater(self.out['eps_attack_mode_blocks_count'],0)
    def test_original_eps_healing_exists(self):self.assertIn(27,self.out['eps_heal_cast_blocks'])
    def test_bx39_tail_at_1048_1057(self):self.assertEqual(self.out['bgx39_team_cooldown_blocks'],list(range(1048,1058)))
    def test_source_not_mistaken_for_066s(self):self.assertEqual(self.out['later_bxs_present'],{'BGX52':False,'BGX66':False,'BGX67':False})
    def test_insertion_count(self):self.assertEqual(source_066s_layout()['candidate_066s_total_blocks'],1088)
    def test_exact_splice_point(self):self.assertEqual(source_066s_layout()['066s_inserts_before_existing_one_based_block'],1052)
    def test_truncation_rejected(self):
        with self.assertRaises(UnsafeOrUnexpectedBCS):parse_lossless(self.data[:-5])
    def test_extra_nonblock_rejected(self):
        with self.assertRaises(UnsafeOrUnexpectedBCS):parse_lossless(self.data.replace(b'SC\n',b'SC\ntrash',1))
    def test_crlf_rejected(self):
        with self.assertRaises(UnsafeOrUnexpectedBCS):parse_lossless(self.data.replace(b'\n',b'\r\n',1))
    def test_changed_snapshot_rejected(self):
        x=self.data.replace(b'BGX38_GUARD',b'BGX38_GUARX',1)
        with self.assertRaisesRegex(UnsafeOrUnexpectedBCS,'PINNED'):audit_041(x)
    def test_position_range(self):self.assertEqual(positions(self.chunks,b'BGX39_TEAM_CD')[0],1048)
if __name__=='__main__':unittest.main()
