"""SOURCE ONLY regression test: status must work after successful WeiDU rollback.
Does not touch the actual EET directory. Uses the existing synthetic fixture.
"""
from pathlib import Path
import importlib.util
import unittest
import test_guarded_installer as old

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'fixed_status_pilot', HERE/'BGXAI_IDLE_GUARD_INSTALL_STATUS_FIX_SOURCE_ONLY.py')
fixed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixed)
# Reuse the verified synthetic game fixture with the candidate module.
old.pilot = fixed

class StatusAfterRollback(old.TestInstaller):
    def test_status_after_rollback_reports_066s_and_stale_stage(self):
        fixed.install(self.root, guard=self.guard, backup=self.backup, runner=self.runner)
        fixed.rollback(self.root, guard=self.guard, backup=self.backup, runner=self.runner)
        data = fixed.source_status(self.root)
        self.assertEqual(data['state'], 'BASELINE_066S_VERIFIED')
        self.assertTrue(data['stale_stage_detected'])
        self.assertEqual(data['lua_sha256'], fixed.ORIGINAL_SHA)
        self.assertEqual(data['bcs_sha256'], fixed.BCS_SHA)

    def test_status_clean_baseline_and_preflight_are_separate(self):
        data = fixed.source_status(self.root)
        self.assertFalse(data['stale_stage_detected'])
        self.assertEqual(fixed.preflight(self.root)['status'], 'READ_ONLY_PREFLIGHT_PASS')
        (self.root/'BGXIDLE').mkdir()
        self.assertTrue(fixed.source_status(self.root)['stale_stage_detected'])
        with self.assertRaisesRegex(fixed.Stop, 'PILOT_STAGE_ALREADY_PRESENT'):
            fixed.preflight(self.root)

    def test_status_stale_stage_never_overrides_hash_failure(self):
        (self.root/'BGXIDLE').mkdir()
        (self.root/fixed.LUA).write_bytes(b'TAMPERED')
        with self.assertRaisesRegex(fixed.Stop, 'LIVE_HASH_MISMATCH'):
            fixed.source_status(self.root)

if __name__ == '__main__':
    unittest.main(verbosity=2)
