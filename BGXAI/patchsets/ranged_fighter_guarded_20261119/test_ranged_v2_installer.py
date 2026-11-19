#!/usr/bin/env python3
"""Fail-closed, non-game regression tests for guarded BGXRANGED V2 WeiDU upgrade."""
import ast
from pathlib import Path
import unittest
from unittest import mock
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import BGXRANGED_V2_GUARDED_INSTALL as U

class V2InstallerTests(unittest.TestCase):
    def test_python_syntax(self):
        ast.parse((ROOT/"BGXRANGED_V2_GUARDED_INSTALL.py").read_text(encoding="utf-8"))
    def test_unchanged_v1_sha(self):
        self.assertEqual(U.V1_SHA,"49b553908e7b66ab85714e91dd27800cad2ec4a9c51d8860d24aeb67b3c461b3")
    def test_native_v2_exact_candidate(self):
        self.assertEqual(U.V2_SHA,"1991f04d0a6acc556f53e03a7aa4a9fcaab252668b689f3d6726be118ca7c1e2")
        self.assertEqual(U.V2_SOURCE_SHA,"dc08fa3a1e5d34463ecb984d1e2fdf2c2c8bc938bd36411f189ffc4f1d0a3eb0")
    def test_dedicated_weidu_component(self):
        self.assertEqual(U.DIR,"BGXRANGED2")
        self.assertNotEqual(U.EXE,U.V1.EXE)
        self.assertNotEqual(U.TP2,U.V1.TP2)
        self.assertIn("COPY ~BGXRANGED2/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~",U.TP2_DATA)
    def test_no_unapproved_game_writes_in_status_or_preflight(self):
        src=(ROOT/"BGXRANGED_V2_GUARDED_INSTALL.py").read_text()
        self.assertIn("if args.mode==\"status\":report=status(root)",src)
        self.assertIn('elif args.mode=="preflight":report=V.run(root)',src)
        self.assertIn("INSTALL_NOT_AUTHORIZED",src)
        self.assertIn("ROLLBACK_NOT_AUTHORIZED",src)
    def test_status_v1_allows_staging_after_rollback(self):
        with mock.patch.object(U,"require_root"), mock.patch.object(U,"check_protected"), \
             mock.patch.object(U,"sha",return_value=U.V1_SHA), \
             mock.patch.object(U.P,"parts",return_value=[object()]*1171), \
             mock.patch.object(U,"last",return_value="~BGXRANGED/SETUP-BGXRANGED.TP2~ #0 #0"), \
             mock.patch.object(U.pathlib.Path,"is_file",return_value=True), \
             mock.patch.object(U.json,"loads",return_value={"bcs_sha256":U.V1_SHA,"original_sha256":U.BASE_SHA}), \
             mock.patch.object(U.pathlib.Path,"read_bytes",return_value=b"old"), \
             mock.patch.object(U.pathlib.Path,"read_text",return_value="{}"):
            # The staging check must be opt-in only, not bypassed during install.
            with mock.patch.object(U.pathlib.Path,"exists",return_value=True):
                self.assertEqual(U.v1_state(U.ROOT,allow_v2_staging=True),b"old")
                with self.assertRaisesRegex(ValueError,"V2_STAGING_COLLISION"):
                    U.v1_state(U.ROOT,allow_v2_staging=False)
    def test_weidu_error_does_not_retry(self):
        bad=mock.Mock(returncode=1,stdout="",stderr="FATAL ERROR: blocked")
        with mock.patch.object(U.subprocess,"run",return_value=bad) as call:
            with self.assertRaisesRegex(ValueError,"WEIDU_STOP_MANUAL_RECOVERY_REQUIRED"):
                U.call_weidu(U.ROOT)
            self.assertEqual(call.call_count,1)
    def test_rollback_refuses_when_not_last(self):
        with mock.patch.object(U.V1,"processes"),mock.patch.object(U,"status",return_value={"status":"BGXRANGED_V2_INSTALLED_VERIFIED"}),mock.patch.object(U,"last",return_value="~SOMETHING_ELSE/SETUP.TP2~ #0 #0"):
            with self.assertRaisesRegex(ValueError,"V2_NOT_LAST"):
                U.rollback(U.ROOT)
    def test_backup_before_game_stage(self):
        s=(ROOT/"BGXRANGED_V2_GUARDED_INSTALL.py").read_text()
        self.assertLess(s.index("backup=snapshot(root)"),s.index("(folder/\"staged\").mkdir"))
        self.assertLess(s.index("(root/STAGED).write_bytes(data)"),s.index("call_weidu(root)"))
        self.assertLess(s.index("result=status(root)"),s.index("return dict(result,game_modified=True",s.index("def install(")))
    def test_old_bcs_protected_in_rollback(self):
        s=(ROOT/"BGXRANGED_V2_GUARDED_INSTALL.py").read_text()
        self.assertIn("if checks.get(BCS)!=V1_SHA",s)
        self.assertIn('return dict(result,status="BGXRANGED_V2_ROLLBACK_VERIFIED_V1_RESTORED"',s)
    def test_refuse_no_live_v1(self):
        with mock.patch.object(U.V1,"processes"),mock.patch.object(U,"v1_state",side_effect=ValueError("V1_BCS_NOT_EXACT")),mock.patch.object(U,"snapshot") as backup:
            with self.assertRaisesRegex(ValueError,"V1_BCS_NOT_EXACT"):
                U.install(U.ROOT)
            backup.assert_not_called()

if __name__=="__main__":unittest.main()
