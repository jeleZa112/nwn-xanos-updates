import unittest
from pathlib import Path
from verify_066s_live_075 import (Blocked,inspect,blocks,action_ids,EXPECTED_061,
                                  EXPECTED_066S,INSERT_AT,INSERT_COUNT,sha)
HISTORICAL=Path('/mnt/data/bg074_inputs/BDDEFAI_EPS18_4_BGXAI041_LIVE_20261108.BCS')

def make_block(actions,marker=None,footer=False):
    s=b'CR\nCO\nTR\n16399 1 0 0 0 "'+(marker or b'TEST')+b'" "LOCALS" OB\nTR\nCO\nRS\nRE\n100AC\n'
    for i,a in enumerate(actions):
        if i>0:s+=b'AC\n'
        s+=str(a).encode()+b'OB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\n'
    return s+b'AC\nRE\nRS\nCR\n'+(b'SC\n' if footer else b'')

def fixture():
    old=[]
    for i in range(1077):
        a=EXPECTED_061[i-1031] if 1031<=i<1051 else [30,36]
        m=b'LOCALSBGX52_REQ_SLOT BGX61_LAST_BRANCH' if 1031<=i<1051 else b'BDAI_ATTACK_MODE MO_HealCast BGX38_GUARD'
        old.append(make_block(a,m,footer=i==1076))
    inserted=[]
    for i,a in enumerate(EXPECTED_066S):
        m=b'LOCALSBGX66_S_TEST' if i<4 else b'BGX66_S_HEAL_SLOT' if i<10 else b'BGX66_S_WARD'
        inserted.append(make_block(a,m))
    return b'SC\n'+b''.join(old[:INSERT_AT]+inserted+old[INSERT_AT:])

class Test075(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.mock=fixture()
    def test_064_reconstruction_synthetic(self):
        d=inspect(self.mock,verify_pins=False)
        self.assertEqual(d['blocks_inserted_by_066s'],11)
        self.assertEqual(d['block_count_recovered_064'],1077)
    def test_pinned_sha_mandatory(self):
        with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'):inspect(self.mock)
    def test_041_not_066s(self):
        if not HISTORICAL.exists():self.skipTest('Private historical BCS deliberately not included in source-only archive')
        with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'):inspect(HISTORICAL.read_bytes())
    def test_041_cannot_fake_066s_with_pin_disabled(self):
        if not HISTORICAL.exists():self.skipTest('Private historical BCS deliberately not included in source-only archive')
        with self.assertRaisesRegex(Blocked,'BLOCK_COUNT'):inspect(HISTORICAL.read_bytes(),verify_pins=False)
    def test_wrong_count(self):
        with self.assertRaises(Blocked):blocks(self.mock[:-10],1088)
    def test_insert_bad_action(self):
        x=self.mock.replace(b'AC\n31OB\n',b'AC\n44OB\n',1)
        with self.assertRaisesRegex(Blocked,'066S_ACTION_LAYOUT'):inspect(x,verify_pins=False)
    def test_061_bad_action(self):
        x=self.mock.replace(b'AC\n134OB\n',b'AC\n133OB\n',1)
        with self.assertRaisesRegex(Blocked,'061_RECEIVER'):inspect(x,verify_pins=False)
    def test_bad_heal_marker(self):
        x=self.mock.replace(b'BGX66_S_HEAL_SLOT',b'NO_HEAL_MARKER_',1)
        with self.assertRaisesRegex(Blocked,'HEAL_MARKER'):inspect(x,verify_pins=False)
    def test_bad_ward_marker(self):
        x=self.mock.replace(b'BGX66_S_WARD',b'NO_WARD_MARKR',1)
        with self.assertRaisesRegex(Blocked,'WARD_MARKER'):inspect(x,verify_pins=False)
    def test_bad_cleanup_marker(self):
        x=self.mock.replace(b'LOCALSBGX66_S_TEST',b'LOCALSDISABLED_',1)
        with self.assertRaisesRegex(Blocked,'CLEANUP_MARKER'):inspect(x,verify_pins=False)
    def test_reparse_exact_1088(self):self.assertEqual(len(blocks(self.mock,1088)),1088)
    def test_expected_actions_count(self):self.assertEqual(len(EXPECTED_061),20)
    def test_expect_11_receiver_blocks(self):self.assertEqual(len(EXPECTED_066S),11)
    def test_no_mutation(self):
        x=self.mock
        inspect(x,verify_pins=False)
        self.assertEqual(x,self.mock)
    def test_no_eps_source_marker(self):
        x=self.mock.replace(b'BDAI_ATTACK_MODE MO_HealCast BGX38_GUARD',b'ABSENT',1077)
        with self.assertRaisesRegex(Blocked,'EPS_OR_F_GUARD'):inspect(x,verify_pins=False)
if __name__=='__main__':unittest.main()
