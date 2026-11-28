"""R43 diagnostic extension on EXISTING 179 child. Offline fake game ONLY."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
s=importlib.util.spec_from_file_location('r43_upgraded_onefile',HERE/'BGXAI_R42_ONEFILE_SOURCE_RO.py')
R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
COMMIT="f"*40

class OnefileDiag(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)/"game"
        self.game.mkdir()
        (self.game/"chitin.key").write_bytes(b"fixture")
        self.fetches=[];self.calls=[]

    def fetch(self,commit,path):
        self.assertEqual(commit,COMMIT)
        self.fetches.append(path)
        return (REPO/path).read_bytes()

    def run(self,mode,status,*,returncode=0,token=None,details=None):
        data={"status":status,"ordersSent":0,
              "dispatchAuthorized":False,"armAuthorized":False}
        data.update(details or {})
        outer=self
        class Resp:
            stdout="R43 native\n"+json.dumps(data)
        Resp.returncode=returncode
        def mock_runner(cmd,**kw):
            outer.calls.append((cmd,kw))
            self.assertTrue(str(cmd[1]).endswith("BGXAI_R42_DIAG_UPGRADE_GUARDED_SOURCE_ONLY.py"))
            self.assertTrue(Path(kw["cwd"]).is_dir())
            self.assertIn("--onefile-review-gate",cmd)
            self.assertIn("--mode",cmd)
            self.assertEqual(cmd[cmd.index("--mode")+1],mode[5:])
            return Resp()
        return R.run_diag_guarded(self.game,COMMIT,mode,fetcher=self.fetch,
                                  runner=mock_runner,require_windows=False,
                                  approved_token=token)

    def test_existing_modes_1_to_6_preserved(self):
        self.assertEqual([R.MODES[str(i)] for i in range(1,7)],
                         ["source","status","preflight","install","rollback","capture"])

    def test_new_modes_7_to_11_are_explicit(self):
        self.assertEqual([R.MODES[str(i)] for i in range(7,12)],
                         ["diag_status","diag_preflight","diag_install","diag_rollback","diag_capture"])

    def test_status_uses_sha_pinned_files_only_in_temp(self):
        out=self.run("diag_status","R43_NOT_INSTALLED_R42_PRESENT_LAST")
        self.assertEqual(out["status"],"R43_STATUS_EXACT_GUARDED_PASS")
        self.assertFalse(out["installed"])
        self.assertEqual(set(self.fetches),set([R.R37_GUARD,R.R38_GUARD,R.R42_GUARD,
                                                R.BUILDER,R.BRIDGE,R.LIVE_SOURCE,
                                                R.R43_DIAG,R.R43_GUARD]))
        self.assertFalse((self.game/"BGXR43").exists())

    def test_native_preflight_pass_has_no_mutation(self):
        out=self.run("diag_preflight","R43_PREFLIGHT_LAST155_PASS_NO_INSTALL")
        self.assertEqual(out["status"],"R43_PREFLIGHT_EXACT_GUARDED_PASS")
        self.assertFalse(out["gameModified"])
        self.assertEqual(out["ordersSent"],0)

    def test_install_requires_exact_token_before_network(self):
        with self.assertRaisesRegex(ValueError,"HOLD_EXACT_TYPED_R43_APPROVAL_REQUIRED"):
            self.run("diag_install","R43_READONLY_REASON_INSTALLED_AWAITING_LIVE")
        self.assertEqual(self.fetches,[])

    def test_typed_install_propagates_only_token_into_native(self):
        out=self.run("diag_install","R43_READONLY_REASON_INSTALLED_AWAITING_LIVE",
                     token=R.R43_INSTALL_CONFIRM)
        self.assertEqual(out["status"],"R43_INSTALL_EXACT_GUARDED_PASS")
        self.assertEqual(self.calls[0][1]["input"],R.R43_INSTALL_CONFIRM+"\n")
        self.assertTrue(out["gameModified"])

    def test_typed_rollback_must_be_exact(self):
        with self.assertRaisesRegex(ValueError,"HOLD_EXACT_TYPED_R43_APPROVAL_REQUIRED"):
            self.run("diag_rollback","R43_ROLLBACK_RESTORED_R42_LAST",token="WRONG")

    def test_typed_rollback_exact_native_response(self):
        out=self.run("diag_rollback","R43_ROLLBACK_RESTORED_R42_LAST",
                     token=R.R43_ROLLBACK_CONFIRM)
        self.assertEqual(out["status"],"R43_ROLLBACK_EXACT_GUARDED_PASS")
        self.assertEqual(self.calls[0][1]["input"],R.R43_ROLLBACK_CONFIRM+"\n")

    def test_capture_holds_but_safely_surfaces_specific_reason(self):
        out=self.run("diag_capture","R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
                     returncode=3,details={
                         "r39ProbeStatus":"HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE",
                         "r39ClassSlotState":"NOT_READ",
                         "classScriptResrefAtLiveJaganVerified":False})
        self.assertEqual(out["status"],"R43_CAPTURE_HOLD_REASON_OBSERVED")
        self.assertEqual(out["r39ProbeStatus"],"HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE")
        self.assertFalse(out["classScriptResrefAtLiveJaganVerified"])
        self.assertTrue(out["noAutoRetry"])

    def test_capture_rejects_nonmatching_native_exit(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R43_NATIVE_EXIT_CODE"):
            self.run("diag_capture","R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM",returncode=3)

    def test_capture_does_not_upgrade_unknown_reason_to_authority(self):
        out=self.run("diag_capture","R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
                     returncode=3,details={
                         "r39ProbeStatus":"EVIL","r39ClassSlotState":"EVIL",
                         "classScriptResref":"BDDEFAI",
                         "classScriptResrefAtLiveJaganVerified":False})
        self.assertEqual(out["status"],"R43_CAPTURE_HOLD_REASON_OBSERVED")
        self.assertNotIn("r39ProbeStatus",out)
        self.assertNotIn("r39ClassSlotState",out)
        self.assertIsNone(out["classScriptResref"])

    def test_source_pins_enforced_on_extra_files(self):
        original=(REPO/R.R43_GUARD).read_bytes()
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_SHA_DRIFT"):
            R.verified(R.R43_GUARD,original+b"1")

    def test_unknown_mode_is_hold(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R43_UNSUPPORTED_MODE"):
            self.run("diag_fake","R43_NOT_INSTALLED_R42_PRESENT_LAST")

    def test_original_only_one_updater_static(self):
        raw=(HERE/"BGXAI_R42_ONEFILE_SOURCE_RO.py").read_text()
        self.assertNotIn("XEquipItem(",raw)
        self.assertNotIn("SetGlobal(",raw)
        self.assertNotIn("BGXAI_UPDATE2.cmd",raw)
        self.assertIn("run_guarded(",raw)
        self.assertIn("run_diag_guarded(",raw)

    def test_native_bad_status_is_explicit_hold_not_success(self):
        out=self.run("diag_status","R43_STOP_MANUAL_REVIEW",returncode=3,
                     details={"reason":"HOLD_PROOF_INVALID"})
        self.assertEqual(out["status"],"R43_NATIVE_HOLD_DETAILS")
        self.assertEqual(out["nativeReason"],"HOLD_PROOF_INVALID")
        self.assertTrue(out["noAutoRetry"])

if __name__=="__main__":
    unittest.main()
