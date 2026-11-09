import importlib.util,pathlib,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('mod048',ROOT/'BGXAI48_INSTALL.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class InstallerSafety(unittest.TestCase):
 def test_manifest(self):self.assertEqual(m.verify_sources(ROOT)['version'],m.VERSION)
 def test_old_sha_pin(self):self.assertEqual(len(m.OLD),64)
 def test_last_log(self):
  self.assertTrue(m.RE['47'].search('~BGX47\\SETUP-BGX47.TP2~ #0 #0 // passive'))
  self.assertTrue(m.RE['48'].search('~BGX48\\SETUP-BGX48.TP2~ #0 #0 // passive'))
  self.assertFalse(m.RE['47'].search('~BGX48\\SETUP-BGX48.TP2~ #0 #0'))
 def test_allowlist(self):self.assertEqual(m.DEST,'override/M_BX43.lua')
 def test_source_only(self):
  self.assertEqual(len(m.FILES),6)
  self.assertIn('BGX48/setup-BGX48.tp2',m.FILES)
 def test_safety_processes(self):self.assertTrue(callable(m.guard_processes))
 def test_no_traversal(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,'Unsafe'):m.safe(pathlib.Path(d),'../escape')
if __name__=='__main__':unittest.main()
