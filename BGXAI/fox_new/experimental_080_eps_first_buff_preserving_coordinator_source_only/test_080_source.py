import unittest,sys,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit_eps_buff_080 import parse,audit,Blocked,MARKERS
FIX=Path('/mnt/data/bg074_inputs/BDDEFAI_EPS18_4_BGXAI041_LIVE_20261108.BCS')
class TestEPSAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=FIX.read_bytes();cls.a=audit(cls.raw)
 def test_source_sha(self):self.assertEqual(hashlib.sha256(self.raw).hexdigest(),'86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5')
 def test_count(self):self.assertEqual(len(parse(self.raw)),1057)
 def test_marker_buff(self):self.assertEqual(self.a['markers']['EPS_BUFF']['count'],190)
 def test_marker_long_buff(self):self.assertEqual(self.a['markers']['EPS_LONG_BUFF']['count'],90)
 def test_marker_solo_buff(self):self.assertEqual(self.a['markers']['EPS_SOLO_BUFFING']['count'],2)
 def test_marker_heal(self):self.assertEqual(self.a['markers']['EPS_HEAL_CAST']['count'],11)
 def test_marker_attack(self):self.assertEqual(self.a['markers']['EPS_ATTACK_MODE']['count'],60)
 def test_guard_not_eps(self):self.assertEqual(self.a['markers']['BGXAI_F_GUARD']['count'],18)
 def test_min_max(self):self.assertEqual(self.a['markers']['EPS_BUFF']['first'],42);self.assertEqual(self.a['markers']['EPS_BUFF']['last'],232)
 def test_runtime_not_claimed(self):self.assertIs(self.a['runtime_proof'],False)
 def test_066s_buff_not_claimed(self):self.assertIs(self.a['live_066s_buff_marker_counts_verified'],False)
 def test_tampered_rejected(self):
  with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'):audit(self.raw+b'\n')
 def test_missing_rejected(self):
  with self.assertRaisesRegex(Blocked,'SHA_MISMATCH'):audit(b'')
 def test_non_mutating(self):
  x=self.raw[:];audit(self.raw);self.assertEqual(x,self.raw)
 def test_marker_dictionary(self):self.assertEqual(set(MARKERS),{'EPS_BUFF','EPS_LONG_BUFF','EPS_SOLO_BUFFING','EPS_HEAL_CAST','EPS_ATTACK_MODE','BGXAI_F_GUARD'})
 def test_no_game_write_calls(self):
  for n in ['BGXAI080_EPS_FIRST_COORDINATOR.lua','audit_eps_buff_080.py']:
   t=(HERE/n).read_text()
   for forbidden in ['setLocalInt(', 'ClearActions(', 'AttackReevaluate(', 'EEex_Action_AddSpriteStartedActionListener(']:
    self.assertNotIn(forbidden,t)
if __name__=='__main__':unittest.main()
