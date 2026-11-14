import unittest
from pathlib import Path
from verify_066s_live_075 import Blocked, BLOCKS_066S, EXPECTED_061, EXPECTED_066S
from audit_priority_076 import analyze, spans

HIST=Path('/mnt/data/bg074_inputs/BDDEFAI_EPS18_4_BGXAI041_LIVE_20261108.BCS')

def block(actions,marker,footer=False):
    head=b'CR\nCO\nTR\n16399 1 0 0 0 "'+marker+b'" "LOCALS" OB\nTR\nCO\nRS\nRE\n100AC\n'
    act=b''.join((b'AC\n' if k else b'')+str(a).encode()+b'OB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\n' for k,a in enumerate(actions))
    return head+act+b'AC\nRE\nRS\nCR\n'+(b'SC\n' if footer else b'')

def sample():
    old=[]
    for i in range(1077):
        if 1031<=i<1051:
            acts=EXPECTED_061[i-1031];m=b'LOCALSBGX52_REQ_SLOT BGX61_LAST_BRANCH'
        else:
            acts=[30,36]
            m=(b'BDAI_ATTACK_MODE MO_HealCast BGX38_GUARD' if i<5
               else b'BGX38_GUARD BGX39_TEAM_CD')
        old.append(block(acts,m,footer=i==1076))
    new=[]
    for i,acts in enumerate(EXPECTED_066S):
        m=b'LOCALSBGX66_S_CHECK' if i<4 else b'BGX66_S_HEAL_SLOT' if i<10 else b'BGX66_S_WARD'
        new.append(block(acts,m))
    return b'SC\n'+b''.join(old[:1051]+new+old[1051:])

class Test076(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.raw=sample();cls.o=analyze(cls.raw,live_pins=False)
    def test_count(self): self.assertEqual(self.o['total_blocks'],1088)
    def test_synthetic_status(self): self.assertEqual(self.o['status'],'SYNTHETIC_066S_POSITION_MAP')
    def test_strict_pin(self):
        with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'): analyze(self.raw)
    def test_061_indices(self): self.assertEqual(self.o['fixed_receivers']['BGXAI_061_receiver_blocks_inclusive'],[1032,1051])
    def test_cleanup_indices(self): self.assertEqual(self.o['fixed_receivers']['BGXAI_066S_cleanup_blocks_inclusive'],[1052,1055])
    def test_heal_indices(self): self.assertEqual(self.o['fixed_receivers']['BGXAI_066S_healing_blocks_inclusive'],[1056,1061])
    def test_ward_index(self): self.assertEqual(self.o['fixed_receivers']['BGXAI_066S_mage_ward_block'],1062)
    def test_source_earlier_eps_heal(self): self.assertTrue(self.o['source_order_only']['EPS_heal_marker_appears_before_066S_heal_receiver'])
    def test_source_earlier_eps_attack(self): self.assertTrue(self.o['source_order_only']['EPS_attack_marker_appears_before_061_guard_receiver'])
    def test_061_before_066s(self): self.assertTrue(self.o['source_order_only']['061_guard_receiver_precedes_066S_heal_receiver'])
    def test_067_absent(self): self.assertEqual(self.o['marker_blocks']['BGXAI_067_EARLY']['count'],0)
    def test_spans(self):self.assertEqual(spans([1,2,4,5,9]),[[1,2],[4,5],[9,9]])
    def test_no_spans(self):self.assertEqual(spans([]),[])
    def test_current_041_rejected(self):
        if not HIST.exists():self.skipTest('Private fixture not present')
        with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'): analyze(HIST.read_bytes())
    def test_original_not_modified(self):
        saved=self.raw[:]; analyze(self.raw,live_pins=False);self.assertEqual(self.raw,saved)
    def test_missing_061_rejected(self):
        tampered=self.raw.replace(b'BGX52_REQ_SLOT',b'XXX52_REQ_SLOT',1)
        with self.assertRaises(Blocked):analyze(tampered,live_pins=False)
    def test_missing_heal_rejected(self):
        tampered=self.raw.replace(b'BGX66_S_HEAL_SLOT',b'XXX66_S_HEAL_SLOT',1)
        with self.assertRaises(Blocked):analyze(tampered,live_pins=False)
    def test_missing_ward_rejected(self):
        tampered=self.raw.replace(b'BGX66_S_WARD',b'XXX66_S_WARD',1)
        with self.assertRaises(Blocked):analyze(tampered,live_pins=False)
    def test_empty_blob_rejected(self):
        with self.assertRaises(Blocked):analyze(b'',live_pins=False)
if __name__=='__main__':unittest.main()
