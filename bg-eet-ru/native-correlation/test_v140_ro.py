"""V140 read-only actual-module regression and synthetic PE tests; never patches game."""
from __future__ import annotations
import hashlib
import tempfile
import unittest
from pathlib import Path
import v140_ro as M
from test_v139_combat_dispatch_producer_ro import synthetic_pe

class V140ReadOnlyTests(unittest.TestCase):
    def test_provenance_and_abi_are_hold(self):
        self.assertFalse(M.extract_pdata_function(synthetic_pe(),rva=0x1120,expected_sha=M.digest(synthetic_pe()))['verified_direct_combatlog_producer'])
        self.assertTrue(callable(M._v136_run_game))
        self.assertTrue(callable(M.selftest_windows))

    def test_wrapped_status_preserves_v136_and_fail_closes_wrong_exe(self):
        old=M._v136_run_game
        M._v136_run_game=lambda game,legacy:{'status':'V136_TEST_HOLD','firstcall_owner_verified':False}
        try:
            with tempfile.TemporaryDirectory() as d:
                f=Path(d)/'Baldur.exe'; f.write_bytes(synthetic_pe())
                before=hashlib.sha256(f.read_bytes()).hexdigest()
                out=M.run_game(Path(d),object())
                self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),before)
                self.assertEqual(out['status'],'V140_CALLEE_SOURCE_HOLD')
                self.assertEqual(out['reason'],'EXACT_GAME_EXE_SHA_MISMATCH')
                self.assertEqual(out['v136_live_observation']['status'],'V136_TEST_HOLD')
                self.assertEqual(out['game_files_written'],0)
                self.assertFalse(out['native_hooks_installed'])
                self.assertFalse(out['safe_to_install'])
                self.assertFalse(out['visible_row_join_verified'])
        finally:
            M._v136_run_game=old

    def test_wrapper_synthetic_extraction_without_game_writes(self):
        old_live=M._v136_run_game
        old_extract=M.extract_pdata_function
        M._v136_run_game=lambda game,legacy:{'status':'V136_LIVE_TEST_OWNER_HOLD'}
        M.extract_pdata_function=lambda data:old_extract(data,rva=0x1120,expected_sha=M.digest(data))
        try:
            with tempfile.TemporaryDirectory() as d:
                exe=Path(d)/'Baldur.exe'; exe.write_bytes(synthetic_pe())
                before=exe.read_bytes()
                out=M.run_game(Path(d),None)
                self.assertEqual(exe.read_bytes(),before)
                self.assertEqual(out['status'],'V140_PINNED_FUNCTION_EXTRACTED_SEMANTIC_PROVENANCE_HOLD')
                self.assertEqual(out['callee']['function_begin_rva'],'0x1100')
                self.assertEqual(out['callee']['function_bytes'],0x300)
                self.assertEqual(out['v136_live_observation']['status'],'V136_LIVE_TEST_OWNER_HOLD')
                self.assertFalse(out['calleeto_combatlog_verified'])
                self.assertFalse(out['per_attempt_hit_miss_verified'])
        finally:
            M.extract_pdata_function=old_extract
            M._v136_run_game=old_live

    def test_nonexistent_exe_is_not_created(self):
        old=M._v136_run_game
        M._v136_run_game=lambda game,legacy:{'status':'V136_TEST_HOLD'}
        try:
            with tempfile.TemporaryDirectory() as d:
                out=M.run_game(Path(d),None)
                self.assertEqual(out['status'],'V140_CALLEE_SOURCE_HOLD')
                self.assertFalse((Path(d)/'Baldur.exe').exists())
        finally:M._v136_run_game=old

    def test_no_native_install_primitives(self):
        src=Path(M.__file__).read_text('utf8')
        for forbidden in ('WriteProcessMemory(', 'VirtualProtect(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore(', 'os.replace('):
            self.assertNotIn(forbidden,src)
        self.assertIn("'game_files_written':0",src)
        self.assertIn("'safe_to_install':False",src)
        self.assertIn("'native_hooks_installed':False",src)

if __name__=='__main__': unittest.main(verbosity=2)
