import hashlib,tempfile,unittest
from pathlib import Path
from PREFLIGHT_059_READONLY import Blocked,check_game,check_source,git_blob

class PreflightTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  (self.root/'override').mkdir()
  (self.root/'chitin.key').write_bytes(b'dummy-no-game')
  (self.root/'WeiDU.log').write_text('~BGX56\\setup-BGX56.tp2~ #0 #0 // 056\n')
  (self.root/'override/BDDEFAI.BCS').write_bytes(b'BCS_TEST')
  (self.root/'override/M_BX43.lua').write_bytes(b'LUA_TEST')
 def tearDown(self):self.tmp.cleanup()
 def pins(self):return [hashlib.sha256((self.root/x).read_bytes()).hexdigest() for x in ('override/BDDEFAI.BCS','override/M_BX43.lua')]
 def test_good_baseline_unchanged(self):
  files={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  a,b=self.pins(); self.assertTrue(check_game(self.root,a,b)['installed_056_last'])
  self.assertEqual(files,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_refuse_later_mod(self):
  (self.root/'WeiDU.log').write_text('~BGX56\\setup-BGX56.tp2~ #0 #0\n~ANOTHER\\setup.tp2~ #0 #0\n')
  with self.assertRaises(Blocked):check_game(self.root,*self.pins())
 def test_refuse_bcs_drift(self):
  a,b=self.pins();(self.root/'override/BDDEFAI.BCS').write_bytes(b'MODIFIED')
  with self.assertRaises(Blocked):check_game(self.root,a,b)
 def test_refuse_lua_drift(self):
  a,b=self.pins();(self.root/'override/M_BX43.lua').write_bytes(b'MODIFIED')
  with self.assertRaises(Blocked):check_game(self.root,a,b)
 def test_refuse_symlinked_file(self):
  f=self.root/'override/BDDEFAI.BCS';f.unlink(); f.symlink_to(self.root/'chitin.key')
  with self.assertRaises(Blocked):check_game(self.root,*self.pins())
 def test_refuse_wrong_source(self):
  source=self.root/'M_BX43.lua';source.write_text('this is not 059')
  with self.assertRaises(Blocked):check_source(source)

if __name__=='__main__':unittest.main(verbosity=2)