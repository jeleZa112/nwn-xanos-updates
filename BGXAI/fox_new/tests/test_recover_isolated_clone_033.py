"""BGXAI 033 recovery tests: fictional data and mocked WeiDU ONLY."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parent/'src'))  # installed Windows BGXAI_DEV/tests -> ../src
sys.path.insert(0,str(HERE.parent/'BGXAI_032')) # offline developer fixture
import test_weidu_isolated_032 as fx
import weidu_isolated_test_032 as old
import recover_isolated_clone_033 as mod

class TestRecovery(unittest.TestCase):
    def save_stage(self):return fx.TestIsolated.save_stage(self)
    def setUp(self):
        fx.TestIsolated.setUp(self)
        self.clone=self.root.with_name(self.root.name+old.CLONE_SUFFIX)
        self.clone.mkdir()
        # The old run copied only three files before it was interrupted.
        for name in ('chitin.key','WeiDU.log','override/BDDEFAI.BCS'):
            dst=self.clone/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(self.root/name,dst)
    def state(self):return mod.inspect(self.root,enforce_root=False,preflight=self.preflight)
    def resume(self,*,runner=None,probe=lambda:False):
        return mod.resume(self.root,enforce_root=False,preflight=self.preflight,
                          process_probe=probe,runner=runner or self.fake_weidu)
    def fake_weidu(self,cmd,**kw):return fx.TestIsolated.fake_weidu(self,cmd,**kw)
    def test_01_initial_inspect_partial(self):
        s=self.state();self.assertIn('INCOMPLETE_CLONE',s['status']);self.assertGreater(s['missing_files'],0)
    def test_02_inspect_does_not_write(self):
        before=set(self.root.rglob('*'))|set(self.clone.rglob('*'))
        self.state()
        self.assertEqual(before,set(self.root.rglob('*'))|set(self.clone.rglob('*')))
    def test_03_resume_partial_and_rollback(self):
        r=self.resume()
        self.assertEqual(r['status'],'PASS_ISOLATED_INSTALL_AND_ROLLBACK')
        self.assertGreater(r['copied_missing_files'],0)
    def test_04_original_BDDEFAI_not_modified(self):
        before=old.digest(self.root/'override/BDDEFAI.BCS');self.resume()
        self.assertEqual(old.digest(self.root/'override/BDDEFAI.BCS'),before)
    def test_05_original_TLK_unchanged(self):
        before=old.capture_critical(self.root);self.resume()
        self.assertEqual(old.capture_critical(self.root),before)
    def test_06_no_new_BGX31_in_live_game(self):
        self.resume();self.assertFalse((self.root/'override/BGX31.BCS').exists())
        self.assertFalse((self.root/'setup-BGX31.exe').exists())
    def test_07_report_metadata_in_live_LOCAL_only(self):
        self.resume()
        self.assertTrue((self.local/mod.REPORT_NAME).exists())
        self.assertFalse((self.clone/mod.REPORT_NAME).exists())
    def test_08_never_process_active_copy(self):
        called=[]
        def active():called.append(1);return True
        with self.assertRaisesRegex(ValueError,'STILL ACTIVE'):self.resume(probe=active)
        self.assertTrue(called)
        self.assertFalse((self.clone/'setup-BGX31.exe').exists())
    def test_09_extra_file_refused(self):
        (self.clone/'something_extra.dat').write_bytes(b'do not remove')
        with self.assertRaisesRegex(ValueError,'Clone has changes'):self.resume()
        self.assertTrue((self.clone/'something_extra.dat').exists())
    def test_10_preexisting_WeiDU_artifacts_refused(self):
        (self.clone/'setup-BGX31.exe').write_bytes(b'old')
        with self.assertRaises(ValueError):self.resume()
    def test_11_wrong_size_refused(self):
        (self.clone/'chitin.key').write_bytes(b'WRONG SIZE')
        self.assertEqual(self.state()['status'],'REVIEW_CLONE_HAS_CHANGES')
        with self.assertRaises(ValueError):self.resume()
    def test_12_same_length_corruption_refused(self):
        (self.clone/'chitin.key').write_bytes(b'garbage') # 7 bytes as 'fixture'
        self.assertEqual(self.state()['status'],'INCOMPLETE_CLONE_CAN_RESUME_AFTER_PROCESS_CHECK')
        with self.assertRaisesRegex(ValueError,'differs'):self.resume()
    def test_13_032_previous_report_refused(self):
        payload={'schema':32,'status':'PASS_ISOLATED_INSTALL_AND_ROLLBACK',
                 'clone_root':str(self.clone)}
        (self.local/old.OUT_NAME).write_text(json.dumps(payload))
        self.assertEqual(self.state()['status'],'REVIEW_PREVIOUS_WEIDU_TEST')
        with self.assertRaises(ValueError):self.resume()
    def test_14_clone_missing_refused(self):
        shutil.rmtree(self.clone)
        with self.assertRaises(ValueError):self.state()
    def test_15_clone_symlink_refused(self):
        shutil.rmtree(self.clone)
        try:self.clone.symlink_to(self.root,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('no symlinks')
        with self.assertRaises(ValueError):self.state()
    def test_16_original_game_change_blocked(self):
        self.preflight=lambda *_args,**_kwargs:{'status':'BLOCKED_REVIEW'}
        with self.assertRaises(ValueError):self.resume()
    def test_17_clone_hardlink_refused(self):
        path=self.clone/'chitin.key';path.unlink()
        try:os.link(self.root/'chitin.key',path)
        except OSError:self.skipTest('hardlinks unavailable')
        with self.assertRaisesRegex(ValueError,'HARDLINKED'):self.resume()
    def test_18_no_hardlinks_after_repair(self):
        self.resume()
        self.assertNotEqual((self.root/'lang/ru_ru/dialog.tlk').stat().st_ino,
                            (self.clone/'lang/ru_ru/dialog.tlk').stat().st_ino)
    def test_19_completed_clean_clone_reused(self):
        files,_=old.collect(self.root)
        for rel,size in files:
            target=self.clone/rel
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(self.root/rel,target)
        self.assertEqual(self.state()['status'],'COMPLETE_CLONE_CAN_VERIFY_BEFORE_TEST')
        r=self.resume();self.assertEqual(r['copied_missing_files'],0)
        self.assertEqual(r['status'],'PASS_ISOLATED_INSTALL_AND_ROLLBACK')
    def test_20_rollback_failure_reported(self):
        def fail(cmd,**kw):
            if '--force-install' in cmd:return self.fake_weidu(cmd,**kw)
            return SimpleNamespace(returncode=1,stdout='undone failed',stderr='')
        r=self.resume(runner=fail)
        self.assertEqual(r['status'],'REVIEW_ISOLATED_WEIDU')
        self.assertTrue((self.local/mod.REPORT_NAME).exists())
    def test_21_install_failure_does_not_try_uninstall(self):
        ran=[]
        def fail(cmd,**kw):
            ran.append(cmd)
            return SimpleNamespace(returncode=1,stdout='broken',stderr='')
        r=self.resume(runner=fail)
        self.assertEqual(r['status'],'REVIEW_ISOLATED_WEIDU');self.assertEqual(len(ran),1)
    def test_22_stage_corruption_blocked(self):
        (self.stage/'BGX31/disabled_observer.baf').write_text('unsafe')
        with self.assertRaises(ValueError):self.resume()
    def test_23_custom_outside_root_blocked(self):
        with self.assertRaises(ValueError):mod.resume(self.root,process_probe=lambda:False,
                                                preflight=self.preflight,runner=self.fake_weidu)
    def test_24_unexpected_weidu_log_after_install_not_pass(self):
        def fake(cmd,**kw):
            r=self.fake_weidu(cmd,**kw)
            if '--force-install' in cmd:
                (Path(kw['cwd'])/'WeiDU.log').write_text('// no mod installed')
            return r
        x=self.resume(runner=fake)
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
    def test_25_wmi_query_fail_closed(self):
        prior=mod.os.name
        try:
            mod.os.name='nt'
            def probe(*_args,**_kw):return SimpleNamespace(returncode=1,stdout='',stderr='WMI failed')
            with self.assertRaisesRegex(ValueError,'Windows process check unavailable'):
                mod.running_original_032(check=probe)
        finally:mod.os.name=prior
    def test_26_wmi_query_detects_running(self):
        prior=mod.os.name
        try:
            mod.os.name='nt'
            def probe(*_args,**_kw):return SimpleNamespace(returncode=0,stdout='1234\n',stderr='')
            self.assertTrue(mod.running_original_032(check=probe))
        finally:mod.os.name=prior
    def test_27_wmi_query_success_no_running(self):
        prior=mod.os.name
        try:
            mod.os.name='nt'
            def probe(*_args,**_kw):return SimpleNamespace(returncode=0,stdout='',stderr='')
            self.assertFalse(mod.running_original_032(check=probe))
        finally:mod.os.name=prior

    def test_28_low_disk_space_blocks_before_copy(self):
        original=mod.shutil.disk_usage
        mod.shutil.disk_usage=lambda _path:SimpleNamespace(free=0)
        try:
            with self.assertRaisesRegex(ValueError,'Insufficient disk space'):self.resume()
            self.assertFalse((self.clone/'setup-BGX31.exe').exists())
        finally:mod.shutil.disk_usage=original
    def test_29_rollback_log_component_must_disappear(self):
        def bad_uninstall_log(cmd, **kw):
            r=self.fake_weidu(cmd,**kw)
            if '--force-uninstall' in cmd:
                clone=Path(kw['cwd'])
                (clone/'WeiDU.log').write_text('// EPS\n~setup-BGX31.tp2~ #0 #0 // orphaned')
            return r
        r=self.resume(runner=bad_uninstall_log)
        self.assertEqual(r['status'],'REVIEW_ISOLATED_WEIDU')
        self.assertFalse(r['clone_weidu_component_removed'])

if __name__=='__main__':unittest.main(verbosity=2)