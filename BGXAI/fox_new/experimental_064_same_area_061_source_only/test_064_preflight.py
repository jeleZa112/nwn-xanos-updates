"""Offline tests of source-only preflight, never modifying installed user game."""
import tempfile,unittest
from pathlib import Path
import BGXAI64_PATCH as p
import BGXAI64_PREFLIGHT_READONLY as f
from test_064_patch import fixture

class TestPreflight(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    self.root=Path(self.tmp.name)
    self.lua,self.candidate=fixture()
    self.bcs=b'SC\ncompiled dummy BCS fixture\nSC\n'
    self.kw=dict(bcs_pin=p.digest(self.bcs),lua_pin=p.digest(self.lua),candidate_pin=p.digest(self.candidate))
    self.write('WeiDU.log',b'~EPS/SETUP-ENHANCED-POWERGAMING-SCRIPTS.TP2~ #0 #0\n~BGX61\\SETUP-BGX61.TP2~ #0 #0\n')
    self.write('chitin.key',b'fake key for read-only test')
    self.write('override/BDDEFAI.BCS',self.bcs)
    self.write('BGX61/staged/BDDEFAI.BCS',self.bcs)
    self.write('override/M_BX43.lua',self.lua)
    self.write('BGX61/staged/M_BX43.lua',self.lua)
 def write(self,name,raw):
    dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 def test_success_without_game_writes_and_no_install_authorization(self):
    before={rel:(self.root/rel).read_bytes() for rel in f.WATCH}
    result=f.check(self.root,**self.kw)
    self.assertEqual(result['status'],'064_SOURCE_ONLY_PREFLIGHT_PASS')
    self.assertEqual(result['eeex_runtime_area_api'],'NOT_CHECKED')
    self.assertFalse(result['installed_game_changed'])
    self.assertFalse(result['authorized_to_install'])
    self.assertEqual(before,{rel:(self.root/rel).read_bytes() for rel in f.WATCH})
 def test_last_mod_rejected(self):
    with (self.root/'WeiDU.log').open('ab') as ff: ff.write(b'~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
    with self.assertRaisesRegex(f.Stop,'LAST_WEIDU_NOT_061'):f.check(self.root,**self.kw)
 def test_wrong_bcs_rejected(self):
    self.write('override/BDDEFAI.BCS',b'invalid')
    with self.assertRaisesRegex(f.Stop,'INSTALLED_BCS_MISMATCH'):f.check(self.root,**self.kw)
 def test_wrong_lua_rejected(self):
    self.write('override/M_BX43.lua',b'invalid')
    with self.assertRaisesRegex(f.Stop,'INSTALLED_LUA_MISMATCH'):f.check(self.root,**self.kw)
 def test_stage_bcs_mismatch_rejected(self):
    self.write('BGX61/staged/BDDEFAI.BCS',b'invalid')
    with self.assertRaisesRegex(f.Stop,'061_BCS_STAGE_MISMATCH'):f.check(self.root,**self.kw)
 def test_stage_lua_mismatch_rejected(self):
    self.write('BGX61/staged/M_BX43.lua',b'invalid')
    with self.assertRaisesRegex(f.Stop,'061_LUA_STAGE_MISMATCH'):f.check(self.root,**self.kw)
 def test_unknown_candidate_pin_rejected(self):
    kw=self.kw|{'candidate_pin':'0'*64}
    with self.assertRaisesRegex(ValueError,'CANDIDATE_064_SHA256_MISMATCH'):f.check(self.root,**kw)
 def test_missing_file_rejected(self):
    (self.root/'BGX61/staged/M_BX43.lua').unlink()
    with self.assertRaisesRegex(f.Stop,'MISSING_FILE'):f.check(self.root,**self.kw)
 def test_link_file_rejected(self):
    pth=self.root/'override/BDDEFAI.BCS';pth.unlink()
    pth.symlink_to(self.root/'BGX61/staged/BDDEFAI.BCS')
    with self.assertRaisesRegex(f.Stop,'SYMLINK_BLOCKED'):f.check(self.root,**self.kw)
 def test_wrong_log_path_style_rejected(self):
    self.write('WeiDU.log',b'~BGX60\\SETUP-BGX60.TP2~ #0 #0\n')
    with self.assertRaisesRegex(f.Stop,'LAST_WEIDU_NOT_061'):f.check(self.root,**self.kw)
 def test_original_pin_defaults_fail_for_mock(self):
    with self.assertRaisesRegex(f.Stop,'INSTALLED_BCS_MISMATCH'):f.check(self.root)
 def test_read_only_status_no_new_files(self):
    before=sorted(str(q.relative_to(self.root)) for q in self.root.rglob('*') if q.is_file())
    f.check(self.root,**self.kw)
    after=sorted(str(q.relative_to(self.root)) for q in self.root.rglob('*') if q.is_file())
    self.assertEqual(before,after)

if __name__=='__main__':unittest.main()
