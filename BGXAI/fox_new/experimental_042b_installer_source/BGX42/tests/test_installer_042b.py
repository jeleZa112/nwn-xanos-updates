import json,os
from pathlib import Path
import shutil,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import BGXAI42_INSTALL as w
from build_042b_preview import build

LIVE=Path('/mnt/data/BDDEFAI.BCS')
PKG=Path(__file__).resolve().parents[2]

class InstallerTests(unittest.TestCase):
  def setUp(self):
    self.t=tempfile.TemporaryDirectory()
    self.root=Path(self.t.name)/'EET';self.root.mkdir()
    self.user=Path(self.t.name)/'fakeuser';self.user.mkdir()
    (self.root/'chitin.key').write_bytes(b'CHITIN'+b'0'*1300)
    (self.root/w.EXE).write_bytes(b'MZ'+b'A'*110000)
    (self.root/'override').mkdir()
    self.raw=LIVE.read_bytes()
    (self.root/w.BCS).write_bytes(self.raw)
    for filename in ('dialog.tlk','dialogf.tlk'):
      x=self.root/'lang'/'ru_RU'/filename;x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(b'TLK V1  '+b'0'*150)
    (self.root/'WeiDU.log').write_text('~ENHANCED-POWERGAMING-SCRIPTS/SETUP-ENHANCED-POWERGAMING-SCRIPTS.TP2~ #0 #0\n~BGX41/SETUP-BGX41.TP2~ #0 #0\n')
  def tearDown(self):self.t.cleanup()
  def fake_weidu(self,argv,**kwargs):
    from types import SimpleNamespace
    if '--force-install' in argv:
      shutil.copy2(self.root/'BGX42'/'staged'/'BDDEFAI.BCS',self.root/w.BCS)
      with (self.root/'WeiDU.log').open('a') as f:f.write('~BGX42/SETUP-BGX42.TP2~ #0 #0\n')
    elif '--force-uninstall' in argv:
      (self.root/w.BCS).write_bytes(self.raw)
      lines=(self.root/'WeiDU.log').read_text().splitlines()
      (self.root/'WeiDU.log').write_text('\n'.join(l for l in lines if 'BGX42' not in l)+'\n')
    return SimpleNamespace(returncode=0,stdout='WeiDU MOCK SUCCESS',stderr='')
  def call_install(self):
    with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
      return w.install(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)
  def test_01_pkg_verified(self):self.assertTrue(w.package_verify(PKG))
  def test_02_correct_live_sha(self):self.assertEqual(w.sha(self.root/w.BCS),w.PIN_SHA)
  def test_03_last041(self):self.assertEqual(len(w.entries(self.root)),2)
  def test_04_preflight_unchanged(self):
    w.preflight(self.root,require_exact_path=False,check_process=lambda:None)
    self.assertEqual(w.sha(self.root/w.BCS),w.PIN_SHA)
  def test_05_missing_chitin_blocks(self):
    (self.root/'chitin.key').unlink()
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_06_wrong_hash_blocks(self):
    (self.root/w.BCS).write_bytes(b'NONSENSE')
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_07_wrong_mod_order_blocks(self):
    with (self.root/'WeiDU.log').open('a') as f:f.write('~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_08_staging_collision_blocks(self):
    (self.root/'BGX42').mkdir()
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_09_prevent_symlink(self):
    p=self.root/'BGX42';p.symlink_to(self.user,target_is_directory=True)
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_10_game_path_gate(self):
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=True)
  def test_11_process_check_blocks(self):
    with self.assertRaisesRegex(RuntimeError,'game running'):w.preflight(self.root,require_exact_path=False,check_process=lambda:(_ for _ in ()).throw(RuntimeError('game running')))
  def test_12_preview_matches_live(self):self.assertEqual(len(build(self.raw)[0]),len(self.raw)+4)
  def test_13_install_fake_success(self):
    r=self.call_install()
    self.assertEqual(r['status'],'INSTALLED_EXPERIMENTAL')
    self.assertEqual(w.sha(self.root/w.BCS),w.OUTPUT_HASH)
    self.assertTrue((self.root/'BGX42'/'staged'/'BDDEFAI.BCS').is_file())
  def test_14_external_backup_integrity(self):
    r=self.call_install();b=Path(r['backup'])
    self.assertEqual(w.sha(b/w.BCS),w.PIN_SHA)
    self.assertTrue((b/'WeiDU.log').is_file())
    self.assertTrue((b/'chitin.key').is_file())
  def test_15_last_weidu42_after_mock(self):
    r=self.call_install();self.assertTrue(w.MOD42_RE.search(w.entries(self.root)[-1]))
  def test_16_refuse_double_install(self):
    self.call_install()
    with self.assertRaises(RuntimeError):w.preflight(self.root,require_exact_path=False)
  def test_17_rollback_fake_success(self):
    self.call_install()
    with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
      r=w.uninstall(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)
    self.assertEqual(r['status'],'UNINSTALLED_AND_RESTORED')
    self.assertEqual(w.sha(self.root/w.BCS),w.PIN_SHA)
  def test_18_rollback_if_not_last_fails(self):
    self.call_install()
    with (self.root/'WeiDU.log').open('a') as f:f.write('~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
    with self.assertRaisesRegex(RuntimeError,'last'):w.preflight(self.root,uninstall=True,require_exact_path=False)
  def test_19_rollback_if_tampered_fails(self):
    self.call_install();(self.root/w.BCS).write_bytes(b'mutated')
    with self.assertRaisesRegex(RuntimeError,'matches|missing/unsafe'):w.preflight(self.root,uninstall=True,require_exact_path=False)
  def test_20_no_user_game_files_read_after_wrong_hash(self):
    (self.root/w.BCS).write_bytes(b'bad')
    with self.assertRaises(RuntimeError):self.call_install()
    self.assertFalse((self.root/'BGX42').exists())
    self.assertFalse((self.root/w.OWN_EXE).exists())

if __name__=='__main__':unittest.main()