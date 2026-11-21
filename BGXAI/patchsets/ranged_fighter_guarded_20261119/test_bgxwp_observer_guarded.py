import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import BGXWP_OBSERVER_GUARDED as mod


class SourceContract(unittest.TestCase):
 def test_source_sha(self):self.assertEqual(mod.digest(mod.SOURCE),mod.SOURCE_SHA)
 def test_source_filter(self):mod.check_source()
 def test_source_rejects_wrong_checksum(self):
  with mock.patch.object(mod,'SOURCE_SHA','0'*64),self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
   mod.check_source()
 def test_source_has_no_combat_action_commands(self):
  text=mod.SOURCE.read_text()
  self.assertNotIn('SelectWeaponAbility(',text)
  self.assertNotIn('ClearActions(',text)
  self.assertNotIn('SetGlobal(',text)
 def test_unique_new_filename_only(self):
  self.assertEqual(mod.MODULE,'override/M_BGXWP.lua')
  self.assertNotIn('DPLAYER',mod.TP2_TEXT)
  self.assertNotIn('M_BX43',mod.TP2_TEXT)
  self.assertNotIn('M_BXFR',mod.TP2_TEXT)
  self.assertIn('COPY ~BGXWP/staged/M_BGXWP.lua~ ~override/M_BGXWP.lua~',mod.TP2_TEXT)
 def test_token_required_in_main(self):
  with mock.patch.object(sys,'argv',['prog','install']),mock.patch('builtins.input',return_value='NO'),mock.patch.object(mod,'write_report'),mock.patch.object(mod,'install') as f:
   self.assertEqual(mod.main(),2);f.assert_not_called()
 def test_rollback_token_required(self):
  with mock.patch.object(sys,'argv',['prog','rollback']),mock.patch('builtins.input',return_value='NO'),mock.patch.object(mod,'write_report'),mock.patch.object(mod,'rollback') as f:
   self.assertEqual(mod.main(),2);f.assert_not_called()
 def test_default_menu_exit_no_game_action(self):
  with mock.patch.object(sys,'argv',['prog']),mock.patch('builtins.input',return_value='0'),mock.patch.object(mod,'install') as f:
   self.assertEqual(mod.main(),0);f.assert_not_called()


class Preflight(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  (self.root/'override').mkdir();(self.root/'override'/'M___EEex.lua').write_bytes(b'EEEX')
  (self.root/'WeiDU.log').write_text('~BGXRANGED6/SETUP-BGXRANGED6.TP2~ #0 #0 // live v6\n')
  self.patches=[mock.patch.object(mod,'check_path'),mock.patch.object(mod,'check_processes'),mock.patch.object(mod,'baseline',return_value={'x':'SHA'}),mock.patch.object(mod,'validate_weidu',return_value=self.root/'tmp-weidu')]
  for p in self.patches:p.start();self.addCleanup(p.stop)
 def test_readonly_no_game_file_changes(self):
  old={p.relative_to(self.root):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
  a=mod.preflight(self.root)
  self.assertEqual(a['status'],'PREFLIGHT_OBSERVER_READY_SOURCE_ONLY')
  self.assertFalse(a['game_modified']);self.assertFalse(a['runtime_EEex_validated'])
  new={p.relative_to(self.root):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
  self.assertEqual(old,new)
 def test_existing_new_module_is_blocked(self):
  (self.root/'override'/'M_BGXWP.lua').write_text('collision')
  with self.assertRaisesRegex(ValueError,'BGXWP_PATH_ALREADY_EXISTS'):mod.preflight(self.root)
 def test_existing_install_directory_is_blocked(self):
  (self.root/'BGXWP').mkdir()
  with self.assertRaisesRegex(ValueError,'BGXWP_PATH_ALREADY_EXISTS'):mod.preflight(self.root)
 def test_missing_eeex_is_blocked(self):
  (self.root/'override'/'M___EEex.lua').unlink()
  with self.assertRaisesRegex(ValueError,'EEEX_BOOTSTRAP_MISSING'):mod.preflight(self.root)
 def test_no_sources_modified_when_running_game(self):
  with mock.patch.object(mod,'check_processes',side_effect=ValueError('GAME_OR_WEIDU_PROCESS_RUNNING')):
   with self.assertRaisesRegex(ValueError,'RUNNING'):mod.preflight(self.root)
 def test_last_weidu_parse(self):
  self.assertIn('BGXRANGED6',mod.weidu_last(self.root))
  self.assertTrue(mod.LAST.match('~BGXWP/SETUP-BGXWP.TP2~ #0 #0 // observed'))
 def test_status_not_installed(self):
  with mock.patch.dict('os.environ',{'USERPROFILE':str(self.root)}):
   res=mod.status(self.root)
   self.assertEqual(res['status'],'NOT_INSTALLED')
 def test_status_exact_installed(self):
  (self.root/'override'/'M_BGXWP.lua').write_bytes(mod.SOURCE.read_bytes())
  with mock.patch.dict('os.environ',{'USERPROFILE':str(self.root)}):
   res=mod.status(self.root)
   self.assertEqual(res['status'],'INSTALLED_READONLY_OBSERVER_SOURCE_EXACT')
 def test_status_unrecognized_collision_fails(self):
  (self.root/'override'/'M_BGXWP.lua').write_text('not ours')
  with mock.patch.dict('os.environ',{'USERPROFILE':str(self.root)}):
   with self.assertRaisesRegex(ValueError,'UNKNOWN_OBSERVER_SOURCE'):mod.status(self.root)
 def test_last_only_rollback_fails_before_any_write(self):
  with self.assertRaisesRegex(ValueError,'NOT_LAST_WEIDU'):mod.rollback(self.root)
 def test_report_outside_root(self):
  with mock.patch.dict('os.environ',{'USERPROFILE':str(self.root)}):
   report=mod.report_dir();backup=mod.backup_dir()
   self.assertEqual(report,self.root/'Documents'/'BGXAI_LIVE_REPORTS')
   self.assertEqual(backup,self.root/'Documents'/'BGXAI_BACKUPS')
   self.assertFalse(report.exists());self.assertFalse(backup.exists())
 def test_external_backup_copies_and_verifies(self):
  (self.root/'chitin.key').write_text('key')
  for name in mod.BASELINE:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
  with mock.patch.dict('os.environ',{'USERPROFILE':str(self.root)}):
   backup=mod.external_backup(self.root)
   self.assertTrue((backup/'chitin.key').is_file())
   for name in mod.BASELINE:self.assertEqual(mod.digest(backup/name),mod.digest(self.root/name))

if __name__=='__main__':unittest.main(verbosity=2)

class GuardedInstallLifecycle(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)/'BG_EET_FOXX_NEW';self.root.mkdir()
  (self.root/'override').mkdir()
  (self.root/'override'/'M___EEex.lua').write_text('--eeex boot\n')
  (self.root/'chitin.key').write_bytes(b'FAKEKEY')
  (self.root/mod.WEIDU_EXE).write_bytes(b'MZ'+b'FAKE_WEIDU')
  (self.root/'WeiDU.log').write_text('~BGXRANGED6/SETUP-BGXRANGED6.TP2~ #0 #0 // pilot\n')
  self.sha={}
  for name in mod.BASELINE:
   file=self.root/name;file.parent.mkdir(parents=True,exist_ok=True)
   file.write_text('ORIGINAL '+name)
   self.sha[name]=mod.digest(file)
  p=mock.patch.object(mod,'BASELINE',self.sha);p.start();self.addCleanup(p.stop)
  for p in [mock.patch.object(mod,'check_path'),mock.patch.object(mod,'check_processes')]:
   p.start();self.addCleanup(p.stop)
  home=Path(self.temp.name)/'Home'
  p=mock.patch.dict('os.environ',{'USERPROFILE':str(home)});p.start();self.addCleanup(p.stop)
  self.home=home
 def weidu_simulator(self,root,uninstall=False):
  module=root/mod.MODULE
  if uninstall:
   module.unlink()
   (root/'WeiDU.log').write_text('~BGXRANGED6/SETUP-BGXRANGED6.TP2~ #0 #0 // pilot\n')
  else:
   module.write_bytes((root/mod.STAGED).read_bytes())
   with (root/'WeiDU.log').open('a') as f:f.write('~BGXWP/SETUP-BGXWP.TP2~ #0 #0 // instrument\n')
 def test_install_and_last_only_rollback_simulated(self):
  old={(self.root/name):mod.digest(self.root/name) for name in mod.BASELINE}
  with mock.patch.object(mod,'native_weidu',side_effect=self.weidu_simulator):
   result=mod.install(self.root)
   self.assertEqual(result['status'],'BGXWP_OBSERVER_INSTALLED_NOT_YET_RUNTIME_TESTED')
   self.assertEqual(mod.digest(self.root/mod.MODULE),mod.SOURCE_SHA)
   self.assertTrue((self.root/mod.PROOF).is_file())
   self.assertTrue((self.home/'Documents'/'BGXAI_LIVE_REPORTS').is_dir())
   self.assertTrue(Path(result['external_backup']).is_dir())
   self.assertEqual(mod.status(self.root)['status'],'INSTALLED_READONLY_OBSERVER_SOURCE_EXACT')
   self.assertEqual(mod.rollback(self.root)['status'],'BGXWP_LAST_ONLY_WEIDU_ROLLBACK_VERIFIED')
  self.assertFalse((self.root/mod.MODULE).exists())
  for name in mod.BASELINE:self.assertEqual(mod.digest(self.root/name),old[self.root/name])
 def test_not_last_blocks_rollback(self):
  with mock.patch.object(mod,'native_weidu',side_effect=self.weidu_simulator):mod.install(self.root)
  with (self.root/'WeiDU.log').open('a') as f:f.write('~SOMEOTHER/SETUP-SOMEOTHER.TP2~ #0 #0 // mod\n')
  with mock.patch.object(mod,'native_weidu') as fake:
   with self.assertRaisesRegex(ValueError,'NOT_LAST_WEIDU'):mod.rollback(self.root)
   fake.assert_not_called()
