import importlib.util,unittest
from pathlib import Path
P=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONESHOT_ARMED_SOURCE_V2_20261126/BGXAI_ONESHOT_BCS_MERGE_RO_V1.py")
spec=importlib.util.spec_from_file_location("merger",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=b"SC\nCR\nCO\nOLD1\nCR\nCO\nOLD2\nCR\nSC\n"
pilot=b"SC\nCR\nCO\nBGXW2ARM\nCR\nSC\n"
def merge(o=old,p=pilot,oh=None,ph=None):
 return m.compose(o,p,oh or m.sha(o),ph or m.sha(p))
class Tests(unittest.TestCase):
 def test_one_block_prepended(self):
  got=merge()
  self.assertEqual(len(m.split(got)),3)
  self.assertEqual(m.split(got)[1:],m.split(old))
 def test_exact_unchanged_suffix(self):
  result=merge();self.assertTrue(result.endswith(old[3:]))
 def test_all_byte_preserved(self):
  got=merge()
  self.assertEqual(m.split(got)[1:],m.split(old))
 def test_result_differs(self):
  self.assertNotEqual(m.sha(merge()),m.sha(old))
 def test_one_source_block_only(self):
  self.assertEqual(len(m.split(pilot)),1)
 def test_empty_fail(self):
  with self.assertRaises(m.Hold):merge(b"",pilot)
 def test_baf_not_bcs(self):
  with self.assertRaises(m.Hold):merge(b"IF\n THEN\nEND",pilot)
 def test_corrupt_pilot(self):
  with self.assertRaises(m.Hold):merge(old,pilot[:-1])
 def test_sha_mismatch(self):
  with self.assertRaises(m.Hold):merge(old,pilot,ph="0"*64)
 def test_old_hash_mismatch(self):
  with self.assertRaises(m.Hold):merge(old,pilot,oh="0"*64)
 def test_requires_hex(self):
  with self.assertRaises(m.Hold):merge(old,pilot,oh="INVALID")
 def test_multi_block_pilot(self):
  multi=b"SC\nCR\nCO\nP1\nCR\nCO\nP2\nCR\nSC\n"
  with self.assertRaises(m.Hold):merge(old,multi)
 def test_duplicate_in_old(self):
  original=pilot
  with self.assertRaises(m.Hold):merge(original,pilot)
 def test_not_cross_insert(self):
  old2=b"SC\nCR\nCO\nTOP\nCR\nCO\nBOTTOM\nCR\nSC\n"
  r=merge(old2)
  self.assertEqual(m.split(r)[1:],m.split(old2))
 def test_result_no_native_claim(self):
  x=m.audit(old,pilot,m.sha(old),m.sha(pilot))
  self.assertTrue(x["oldBlocksByteIdentical"])
  self.assertFalse(x["gameBaselineAuthenticated"])
  self.assertFalse(x["pilotCompiledAgainstUserEet"])
  self.assertFalse(x["sourceClaimSufficientForDeployment"])
  self.assertFalse(x["installed"])
  self.assertEqual(x["ordersSent"],0)
 def test_type_checks(self):
  with self.assertRaises(m.Hold):merge("nonbytes",pilot)
if __name__=="__main__":unittest.main(verbosity=2)
