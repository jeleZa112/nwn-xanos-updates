from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('BGXAI_R13_SHORTNAME_GUARDED.py')
sp=importlib.util.spec_from_file_location('shortfix',P)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
ROOT=Path(__file__).parent
ORIG=Path('/mnt/data/BGXAI_R13_1_SOURCE_ONLY/M_BGXTDEF13.lua')
if not ORIG.exists():ORIG=ROOT/'dependencies/M_BGXTDEF13.lua'

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'EET'
        self.root.mkdir()
        (self.root/'chitin.key').write_bytes(b'EET_TEST')
        (self.root/'WeiDU.log').write_text('~BGXTDEF13\\SETUP-BGXTDEF13.TP2~ #0 #0 // original R13\n',encoding='utf-8')
        exe=self.root/m.WEIDU_EXE
        exe.write_bytes(b'MZ'+b'\0'*100000)
        self.baseline={}
        for rel in m.BASELINE:
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('-- fixture '+rel,encoding='utf-8')
            self.baseline[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
        old=self.root/m.PREVIOUS;old.parent.mkdir(exist_ok=True,parents=True)
        old.write_bytes(ORIG.read_bytes())
        assert m.sha(old)==m.PREVIOUS_SHA
        proof=self.root/m.OLD_PROOF;proof.parent.mkdir(exist_ok=True,parents=True)
        proof.write_text(json.dumps({'sourceSha256':m.PREVIOUS_SHA,'status':'BGXTD13_INSTALLED_AWAITING_LIVE_TEST'}))
        self.ext=Path(self.temp.name)/'BACKUPS'
        patches=[patch.object(m,'game',lambda r:None),patch.object(m,'processes',lambda:None),
                 patch.object(m,'BASELINE',self.baseline),patch.object(m,'outside_dir',lambda:self.ext)]
        for p in patches:p.start();self.addCleanup(p.stop)
    def test_01_resref_8_or_fewer(self):self.assertEqual(len(Path(m.MODULE).stem),8)
    def test_02_prefix_m(self):self.assertTrue(Path(m.MODULE).name.startswith('M_'))
    def test_03_source_sha_exact(self):m.sources();self.assertEqual(m.sha(m.SOURCE),m.SOURCE_SHA)
    def test_04_original_still_exact(self):self.assertEqual(m.sha(self.root/m.PREVIOUS),m.PREVIOUS_SHA)
    def test_05_original_not_modified_by_preflight(self):
        old=m.sha(self.root/m.PREVIOUS);self.assertFalse((self.root/'BGXTD14').exists())
        out=m.preflight(self.root)
        self.assertEqual(out['status'],'BGXTD14_SHORTNAME_PREFLIGHT_PASS_NO_INSTALL')
        self.assertEqual(m.sha(self.root/m.PREVIOUS),old)
        self.assertFalse((self.root/'BGXTD14').exists())
    def test_06_legacy_original_is_last(self):self.assertTrue(m.OLD_LAST.match(m.weidu_last(self.root)))
    def test_07_new_component_distinct(self):self.assertNotEqual(m.PREVIOUS,m.MODULE)
    def test_08_filename_collision_blocks(self):
        (self.root/m.MODULE).write_text('tampered')
        with self.assertRaisesRegex(ValueError,'PATH_ALREADY_EXISTS'):m.preflight(self.root)
    def test_09_existing_component_folder_blocks(self):
        (self.root/m.DIR).mkdir()
        with self.assertRaisesRegex(ValueError,'PATH_ALREADY_EXISTS'):m.preflight(self.root)
    def test_10_wrong_old_last_blocks(self):
        (self.root/'WeiDU.log').write_text('~BGXW4\\SETUP-BGXW4.TP2~ #0 #0\n')
        with self.assertRaisesRegex(ValueError,'R13_NOT_LAST_WEIDU'):m.preflight(self.root)
    def test_11_different_last_blocks(self):
        with (self.root/'WeiDU.log').open('a') as f:f.write('~OTHER\\SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(ValueError,'R13_NOT_LAST_WEIDU'):m.preflight(self.root)
    def test_12_original_not_present_blocks(self):
        (self.root/m.PREVIOUS).unlink()
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_13_original_modified_blocks(self):
        (self.root/m.PREVIOUS).write_text('-- changed')
        with self.assertRaisesRegex(ValueError,'INSTALLED_R13_SOURCE_DRIFT'):m.preflight(self.root)
    def test_14_old_proof_mismatch_blocks(self):
        (self.root/m.OLD_PROOF).write_text(json.dumps({'sourceSha256':'0'*64,'status':'READY'}))
        with self.assertRaisesRegex(ValueError,'R13_PREVIOUS_PROOF_UNVERIFIED'):m.preflight(self.root)
    def test_15_eeex_baseline_changed_blocks(self):
        (self.root/'EEex_scripts/EEex_Action.lua').write_text('DRIFT')
        with self.assertRaisesRegex(ValueError,'BASELINE_SHA_MISMATCH'):m.preflight(self.root)
    def test_16_absent_weidu_binary_blocks(self):
        (self.root/m.WEIDU_EXE).unlink()
        with self.assertRaisesRegex(ValueError,'NATIVE_WEIDU_UNAVAILABLE'):m.preflight(self.root)
    def test_17_bad_weidu_pe_blocks(self):
        (self.root/m.WEIDU_EXE).write_bytes(b'NOT PE'+b'\0'*100000)
        with self.assertRaisesRegex(ValueError,'WEIDU_NOT_PE_EXE'):m.preflight(self.root)
    def test_18_default_status_not_installed(self):
        r=m.status(self.root);self.assertEqual(r['status'],'BGXTD14_NOT_INSTALLED')
    def test_19_install_denied_without_exact_token(self):
        with patch.object(m,'backup') as b:
            with self.assertRaisesRegex(ValueError,'INSTALL_TOKEN_NOT_CONFIRMED'):
                m.install(self.root,'INSTALL')
            b.assert_not_called()
    def test_20_rollback_denied_without_exact_token(self):
        with self.assertRaisesRegex(ValueError,'ROLLBACK_TOKEN_NOT_CONFIRMED'):
            m.rollback(self.root,'ROLLBACK')
    def test_21_backup_outside_game_verified(self):
        b=m.backup(self.root)
        self.assertNotIn(str(self.root),str(b))
        for rel in ('WeiDU.log','chitin.key',m.PREVIOUS,m.OLD_PROOF,*m.BASELINE.keys()):
            self.assertEqual(m.sha(b/rel),m.sha(self.root/rel))
    def test_22_unchanged_module_not_overwritten(self):
        old=m.sha(self.root/m.PREVIOUS)
        with self.assertRaisesRegex(ValueError,'INSTALL_TOKEN_NOT_CONFIRMED'):
            m.install(self.root,'no')
        self.assertEqual(m.sha(self.root/m.PREVIOUS),old)
    def test_23_source_has_no_commands(self):
        s=m.SOURCE.read_bytes();self.assertFalse(any(word in s for word in m.BLOCKED_COMMANDS))
        self.assertEqual(s.count(b'EEex_Action_AddSpriteStartedActionListener(R.on_started)'),1)
    def test_24_module_missile_field(self):self.assertIn(b'm_nResistMissile',m.SOURCE.read_bytes())
    def test_25_runtime_singleton_guard(self):
        self.assertIn(b'BGXTargetDefenseR13.registered==true',m.SOURCE.read_bytes())
    def test_26_target_tp2_only_one_copy(self):
        self.assertEqual(m.TP2_TEXT.count('COPY '),1)
        self.assertIn('~override/M_BGXD13.lua~',m.TP2_TEXT)
        self.assertNotIn('~override/M_BGXTDEF13.lua~',m.TP2_TEXT)
    def test_27_no_symlink_old(self):
        old=self.root/m.PREVIOUS;old.unlink()
        try:old.symlink_to(self.root/'chitin.key')
        except OSError:self.skipTest('Windows symlink unavailable')
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_28_rollback_denied_when_other_last(self):
        with patch.object(m,'run_weidu') as w:
            with self.assertRaisesRegex(ValueError,'SHORTNAME_FIX_NOT_LAST_WEIDU'):
                m.rollback(self.root,m.ROLLBACK_TOKEN)
            w.assert_not_called()
    def fake_weidu(self,root,uninstall=False):
        if uninstall:
            (root/m.MODULE).unlink()
            (root/'WeiDU.log').write_text('~BGXTDEF13\\SETUP-BGXTDEF13.TP2~ #0 #0\n')
        else:
            dst=root/m.MODULE;dst.write_bytes((root/m.STAGED).read_bytes())
            with (root/'WeiDU.log').open('a') as f:f.write('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0 // 8-char Lua resource\n')
    def test_29_mock_install_backup_and_preserves_old(self):
        old=m.sha(self.root/m.PREVIOUS)
        with patch.object(m,'run_weidu',self.fake_weidu):
            r=m.install(self.root,m.INSTALL_TOKEN)
        self.assertEqual(r['status'],'BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST')
        self.assertTrue((self.root/m.MODULE).exists())
        self.assertEqual(m.sha(self.root/m.MODULE),m.SOURCE_SHA)
        self.assertEqual(m.sha(self.root/m.PREVIOUS),old)
        self.assertTrue(Path(r['externalBackup']).is_dir())
        self.assertTrue(m.NEW_LAST.match(m.weidu_last(self.root)))
    def test_30_mock_rollback_restore_original_order(self):
        with patch.object(m,'run_weidu',self.fake_weidu):
            r=m.install(self.root,m.INSTALL_TOKEN)
            v=m.rollback(self.root,m.ROLLBACK_TOKEN)
        self.assertEqual(v['status'],'BGXTD14_ROLLBACK_LAST_ONLY_VERIFIED')
        self.assertFalse((self.root/m.MODULE).exists())
        self.assertEqual(m.sha(self.root/m.PREVIOUS),m.PREVIOUS_SHA)
    def test_31_status_installed_exact(self):
        with patch.object(m,'run_weidu',self.fake_weidu):m.install(self.root,m.INSTALL_TOKEN)
        self.assertEqual(m.status(self.root)['status'],'BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST')
    def test_32_status_drift_blocks(self):
        with patch.object(m,'run_weidu',self.fake_weidu):m.install(self.root,m.INSTALL_TOKEN)
        (self.root/m.MODULE).write_text('DRIFT')
        with self.assertRaises(ValueError):m.status(self.root)
    def test_33_weidu_unchanged_before_token(self):
        before=(self.root/'WeiDU.log').read_bytes()
        with self.assertRaises(ValueError):m.install(self.root,'NO')
        self.assertEqual((self.root/'WeiDU.log').read_bytes(),before)
    def test_34_unrecognized_proof_blocks_rollback(self):
        with patch.object(m,'run_weidu',self.fake_weidu):m.install(self.root,m.INSTALL_TOKEN)
        (self.root/m.PROOF).write_text('{}')
        with patch.object(m,'run_weidu') as w:
            with self.assertRaisesRegex(ValueError,'SHORTNAME_BACKUP_UNTRUSTED'):
                m.rollback(self.root,m.ROLLBACK_TOKEN)
            w.assert_not_called()
    def test_35_backup_missing_old_blocks_rollback(self):
        with patch.object(m,'run_weidu',self.fake_weidu):r=m.install(self.root,m.INSTALL_TOKEN)
        (Path(r['externalBackup'])/m.PREVIOUS).unlink()
        with patch.object(m,'run_weidu') as w:
            with self.assertRaises(ValueError):m.rollback(self.root,m.ROLLBACK_TOKEN)
            w.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
