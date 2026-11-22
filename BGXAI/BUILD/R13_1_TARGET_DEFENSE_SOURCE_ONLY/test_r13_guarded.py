from __future__ import annotations
import hashlib
import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

P = Path(__file__).with_name('BGXAI_R13_GUARDED.py')
spec = importlib.util.spec_from_file_location('bgx13guard',P)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)/'EET'
        self.root.mkdir()
        (self.root/'chitin.key').write_bytes(b'EET_TEST_KEY')
        (self.root/'WeiDU.log').write_text('~OLD/SETUP-OLD.TP2~ #0 #0 // prior\n',encoding='utf-8')
        tool=self.root/m.WEIDU_EXE
        tool.write_bytes(b'MZ'+b'\0'*100_000)
        self.fake={}
        for k in m.BASELINE:
            p=self.root/k;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('-- test fixture '+k,encoding='utf-8')
            self.fake[k]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.patches=[patch.object(m,'BASELINE',self.fake),
                      patch.object(m,'check_root',lambda root:None),
                      patch.object(m,'check_processes',lambda:None),
                      patch.object(m,'report_dir',lambda: Path(self.tmp.name)/'REPORTS')]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_01_source_digest_exact(self):
        m.check_source()
        self.assertEqual(m.digest(m.SCRIPT),m.SCRIPT_SHA)
    def test_02_preflight_clean_source_only(self):
        before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        r=m.preflight(self.root)
        after={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual(r['status'],'BGXTD13_PREFLIGHT_PASS_NO_INSTALL')
        self.assertEqual(r['baselineVerified'],len(self.fake))
        self.assertFalse(r['gameplayResourcesModified'])
        self.assertFalse(r['optionalAttackInfoRequired'])
        self.assertFalse(r['installAuthorized'])
        self.assertFalse(r['weaponSwitchAuthorized'])
    def test_03_optional_attack_info_absent_pass(self):
        self.assertFalse((self.root/'EEex_scripts/B3AttackInfo.lua').exists())
        self.assertEqual(m.preflight(self.root)['status'],'BGXTD13_PREFLIGHT_PASS_NO_INSTALL')
    def test_04_missing_legacy_r4_blocks(self):
        (self.root/'override/M_BGXW4.lua').unlink()
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_05_drift_legacy_r1_blocks(self):
        (self.root/'override/M_BGXWP.lua').write_text('CHANGED')
        with self.assertRaisesRegex(ValueError,'INSTALLED_BASELINE_CHANGED'):m.preflight(self.root)
    def test_06_drift_eeex_action_blocks(self):
        (self.root/'EEex_scripts/EEex_Action.lua').write_text('CHANGED')
        with self.assertRaisesRegex(ValueError,'INSTALLED_BASELINE_CHANGED'):m.preflight(self.root)
    def test_07_already_installed_path_blocks(self):
        (self.root/'BGXTDEF13').mkdir()
        with self.assertRaisesRegex(ValueError,'BGXTD13_PATH_ALREADY_EXISTS'):m.preflight(self.root)
    def test_08_module_filename_collision_blocks(self):
        (self.root/m.MODULE).write_text('EXISTING')
        with self.assertRaisesRegex(ValueError,'BGXTD13_PATH_ALREADY_EXISTS'):m.preflight(self.root)
    def test_09_WeiDU_missing_blocks(self):
        (self.root/m.WEIDU_EXE).unlink()
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_10_WeiDU_header_too_short_blocks(self):
        (self.root/m.WEIDU_EXE).write_bytes(b'MZ')
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_11_WeiDU_not_PE_blocks(self):
        (self.root/m.WEIDU_EXE).write_bytes(b'NO'+b'\0'*100_000)
        with self.assertRaisesRegex(ValueError,'WEIDU_PE_HEADER_INVALID'):m.preflight(self.root)
    def test_12_Weidu_log_missing_blocks(self):
        (self.root/'WeiDU.log').unlink()
        with self.assertRaises(ValueError):m.preflight(self.root)
    def test_13_status_not_installed(self):
        r=m.status(self.root)
        self.assertEqual(r['status'],'BGXTD13_NOT_INSTALLED')
        self.assertFalse(r['gameplayResourcesModifiedByStatus'])
    def test_14_status_unknown_override_hold(self):
        (self.root/m.MODULE).write_text('-- UNKNOWN')
        with self.assertRaisesRegex(ValueError,'INSTALLED_R13_MODULE_UNKNOWN_HOLD'):m.status(self.root)
    def test_15_install_denied_without_exact_token(self):
        before=set(self.root.rglob('*'))
        with self.assertRaisesRegex(ValueError,'INSTALL_EXPLICIT_TOKEN_MISSING'):
            m.install(self.root,'INSTALL')
        self.assertEqual(set(self.root.rglob('*')),before)
    def test_16_rollback_denied_without_exact_token(self):
        with self.assertRaisesRegex(ValueError,'ROLLBACK_EXPLICIT_TOKEN_MISSING'):
            m.rollback(self.root,'ROLLBACK')
    def test_17_install_guards_run_before_backup(self):
        with patch.object(m,'preflight',side_effect=ValueError('DRIFT')) as pre,patch.object(m,'external_backup') as backup:
            with self.assertRaisesRegex(ValueError,'DRIFT'):m.install(self.root,m.INSTALL_TOKEN)
            pre.assert_called_once();backup.assert_not_called()
    def test_18_rollback_guards_run_before_uninstall(self):
        with patch.object(m,'weidu') as w:
            with self.assertRaisesRegex(ValueError,'NOT_LAST_WEIDU_ROLLBACK_FORBIDDEN'):
                m.rollback(self.root,m.ROLLBACK_TOKEN)
            w.assert_not_called()
    def test_19_reserved_field_baseline_sha(self):
        self.assertEqual(len(m.BASELINE),5)
        self.assertTrue(all(len(s)==64 for s in m.BASELINE.values()))
    def test_20_source_forbidden_command_stop(self):
        f=self.root/'SOURCE.lua';f.write_text('SelectWeaponAbility(x)')
        with patch.object(m,'SCRIPT',f),patch.object(m,'SCRIPT_SHA',hashlib.sha256(f.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError,'OBSERVER_FORBIDDEN_COMMAND_OR_SIZE'):m.check_source()
    def test_21_invalid_source_sha_stop(self):
        with patch.object(m,'SCRIPT_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'SOURCE_SHA256_MISMATCH'):m.check_source()
    def test_22_nested_baseline_symlink_stop(self):
        p=self.root/'EEex_scripts/EEex_Action.lua';p.unlink()
        try:p.symlink_to(self.root/'chitin.key')
        except OSError:self.skipTest('symlinks unsupported')
        with self.assertRaisesRegex(ValueError,'BASELINE_REPARSE_POINT'):m.preflight(self.root)
    def test_23_existing_external_report_not_required_for_preflight(self):
        self.assertFalse((Path(self.tmp.name)/'REPORTS').exists())
        m.preflight(self.root)
        self.assertFalse((Path(self.tmp.name)/'REPORTS').exists())
    def test_24_no_automatic_rollback_after_failed_install(self):
        source=P.read_text()
        self.assertNotIn('except: rollback(',source)
        self.assertIn('NOT_LAST_WEIDU_ROLLBACK_FORBIDDEN',source)
    def test_25_different_module_name(self):
        self.assertNotEqual(m.MODULE,'override/M_BGXW4.lua')
        self.assertNotEqual(m.MODULE,'override/M_BGXWP.lua')
        self.assertNotEqual(m.MODULE,'override/M_BGXW2.lua')
    def test_26_required_exact_approval_tokens(self):
        self.assertEqual(m.INSTALL_TOKEN,'INSTALL_BGXAI_R13_PASSIVE_TARGET')
        self.assertEqual(m.ROLLBACK_TOKEN,'ROLLBACK_BGXAI_R13_PASSIVE_TARGET')

if __name__=='__main__':unittest.main(verbosity=2)
