from pathlib import Path
import os, sys, tempfile, shutil, unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import BGXAI42_INSTALL as w
import test_installer_042b as base
PKG=Path(__file__).resolve().parents[2]

class RecoveryTests(unittest.TestCase):
    # Reuse fixture helpers without duplicating the original 20 test cases.
    setUp=base.InstallerTests.setUp
    tearDown=base.InstallerTests.tearDown
    call_install=base.InstallerTests.call_install
    fake_weidu=base.InstallerTests.fake_weidu
    def test_21_after_install_backup_findable(self):
        r=self.call_install()
        self.assertEqual(r['status'],'INSTALLED_EXPERIMENTAL')
        with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
            self.assertTrue(w.locate_verified_install_backup(self.root).is_dir())
    def test_22_refuse_missing_backup(self):
        r=self.call_install();shutil.rmtree(r['backup'])
        with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
            with self.assertRaisesRegex(RuntimeError,'backup'):
                w.uninstall(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)
        self.assertEqual(w.sha(self.root/w.BCS),w.OUTPUT_HASH)
    def test_23_refuse_damaged_backup(self):
        r=self.call_install();(Path(r['backup'])/w.BCS).write_bytes(b'TAMPER')
        with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
            with self.assertRaisesRegex(RuntimeError,'backup'):
                w.uninstall(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)
        self.assertEqual(w.sha(self.root/w.BCS),w.OUTPUT_HASH)
    def test_24_preuninstall_backup(self):
        self.call_install()
        with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
            r=w.uninstall(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)
        self.assertEqual(r['status'],'UNINSTALLED_AND_RESTORED')
        self.assertEqual(w.sha(Path(r['rollback_backup'])/w.BCS),w.OUTPUT_HASH)
        self.assertTrue((Path(r['rollback_backup'])/'uninstall_report.json').is_file())
    def test_25_no_explicit_yes_command_cannot_start_weidu(self):
        self.assertNotIn('ClearActions(',PKG.joinpath('BGXAI42_INSTALL.py').read_text())
    def test_26_source_disallowed_when_external_backup_is_symlink(self):
        self.call_install()
        root=Path(self.user)/'Documents'/'BGXAI42_SAFE_BACKUPS'
        # Destroy existing backing folder and replace it with a redirect
        shutil.rmtree(root)
        root.symlink_to(self.user, target_is_directory=True)
        with patch.dict(os.environ,{'USERPROFILE':str(self.user)}):
            with self.assertRaisesRegex(RuntimeError,'unsafe|backup'):
                w.uninstall(self.root,PKG,check_process=lambda:None,runner=self.fake_weidu,require_exact_path=False)

if __name__=='__main__':unittest.main()