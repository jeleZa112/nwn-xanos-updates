import importlib.util,pathlib,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('mod049',ROOT/'BGXAI49_INSTALL.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class InstallerSafety(unittest.TestCase):
 def test_manifest(self):self.assertEqual(m.verify_sources(ROOT)['version'],m.VERSION)
 def test_expected_old_sha(self):self.assertEqual(m.OLD,'7b7b613c736df4d7d8a360e9879486bfe26ca52b7f29242c64ab6b2a27c694ea')
 def test_last_log(self):
  self.assertTrue(m.RE['48'].search('~BGX48\\SETUP-BGX48.TP2~ #0 #0 // passive'))
  self.assertTrue(m.RE['49'].search('~BGX49\\SETUP-BGX49.TP2~ #0 #0 // passive'))
  self.assertFalse(m.RE['48'].search('~BGX49\\SETUP-BGX49.TP2~ #0 #0'))
 def test_dest(self):self.assertEqual(m.DEST,'override/M_BX43.lua')
 def test_backup_folder(self):self.assertIn('BGXAI49_SAFE_BACKUPS',str(m.backup_root()))
 def test_allowlist(self):self.assertEqual(len(m.FILES),6)
 def test_safety_processes(self):self.assertTrue(callable(m.guard_processes))
 def test_no_traversal(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,'Unsafe'):m.safe(pathlib.Path(d),'../escape')
if __name__=='__main__':unittest.main()
