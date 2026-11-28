"""R44 same original menu179 source: fake network/native only, NO real game."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CHILD=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py"
sp=importlib.util.spec_from_file_location('r44_179_stage',CHILD)
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
COMMIT="f"*40

class R44Existing179(unittest.TestCase):
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

    def invoke(self,mode,status,*,rc=0,token=None,details=None):
        data={"status":status,"ordersSent":0,
              "dispatchAuthorized":False,"armAuthorized":False}
        data.update(details or {})
        outer=self
        class Resp:
            stdout="R44 standard console\n"+json.dumps(data)
        Resp.returncode=rc
        def fake_runner(cmd,**kw):
            outer.calls.append((cmd,kw))
            self.assertTrue(str(cmd[1]).endswith("BGXAI_R44_GUARDED_LAST156_SOURCE_ONLY.py"))
            self.assertIn("--onefile-review-gate",cmd)
            self.assertEqual(cmd[cmd.index("--mode")+1],mode[8:])
            self.assertTrue(Path(kw["cwd"]).is_dir())
            return Resp()
        return R.run_numeric_guarded(self.game,COMMIT,mode,fetcher=self.fetch,
                                     runner=fake_runner,require_windows=False,
                                     approved_token=token)

    def test_01_preserve_old_179_all_1_to_11(self):
        self.assertEqual([R.MODES[str(i)] for i in range(1,12)],
            ["source","status","preflight","install","rollback","capture",
             "diag_status","diag_preflight","diag_install","diag_rollback","diag_capture"])

    def test_02_new_12_to_16_separate(self):
        self.assertEqual([R.MODES[str(i)] for i in range(12,17)],
                         ["numeric_status","numeric_preflight","numeric_install",
                          "numeric_rollback","numeric_capture"])

    def test_03_status_R43_current_not_installed_R44(self):
        out=self.invoke("numeric_status","R44_NOT_INSTALLED_R43_PRESENT_LAST")
        self.assertEqual(out["status"],"R44_STATUS_EXACT_GUARDED_PASS")
        self.assertFalse(out["installed"])
        self.assertFalse((self.game/"BGXR44").exists())

    def test_04_sources_exact_sha_and_temp(self):
        self.invoke("numeric_status","R44_NOT_INSTALLED_R43_PRESENT_LAST")
        self.assertEqual(set(self.fetches),set([
            R.R37_GUARD,R.R38_GUARD,R.R42_GUARD,R.BUILDER,R.BRIDGE,R.LIVE_SOURCE,
            R.R43_DIAG,R.R43_GUARD,R.R39_NUMERIC_PATCH,R.R44_COMPOSE,R.R44_GUARD]))
        self.assertFalse((self.game/"BGXR44").exists())

    def test_05_preflight_no_mutation(self):
        out=self.invoke("numeric_preflight","R44_PREFLIGHT_LAST156_PASS_NO_INSTALL")
        self.assertEqual(out["status"],"R44_PREFLIGHT_EXACT_GUARDED_PASS")
        self.assertFalse(out["gameModified"])
        self.assertEqual(out["ordersSent"],0)

    def test_06_install_exact_typed_before_fetch(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_TYPED_CONSENT_REQUIRED"):
            self.invoke("numeric_install","R44_READONLY_NUMERIC_ACTOR_INSTALLED_AWAITING_LIVE")
        self.assertFalse(self.fetches)

    def test_07_install_confirmed_pass_and_only_token_to_native(self):
        out=self.invoke("numeric_install","R44_READONLY_NUMERIC_ACTOR_INSTALLED_AWAITING_LIVE",
                        token=R.R44_INSTALL_CONFIRM)
        self.assertEqual(out["status"],"R44_INSTALL_EXACT_GUARDED_PASS")
        self.assertTrue(out["gameModified"])
        self.assertEqual(self.calls[0][1]["input"],R.R44_INSTALL_CONFIRM+"\n")

    def test_08_rollback_requires_distinct_token(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_TYPED_CONSENT_REQUIRED"):
            self.invoke("numeric_rollback","R44_ROLLBACK_RESTORED_R43_LAST",
                        token=R.R43_ROLLBACK_CONFIRM)

    def test_09_rollback_typed_pass(self):
        out=self.invoke("numeric_rollback","R44_ROLLBACK_RESTORED_R43_LAST",
                        token=R.R44_ROLLBACK_CONFIRM)
        self.assertEqual(out["status"],"R44_ROLLBACK_EXACT_GUARDED_PASS")
        self.assertEqual(self.calls[0][1]["input"],R.R44_ROLLBACK_CONFIRM+"\n")

    def test_10_capture_readonly_hold_exposes_r39_reason(self):
        out=self.invoke("numeric_capture","R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
            rc=3,details={"r39ProbeStatus":"HOLD_SCRIPT_CURSOR_CHANGED",
                          "r39ClassSlotState":"NOT_READ",
                          "r39PhysicalReason":"NONE",
                          "classScriptResrefAtLiveJaganVerified":False})
        self.assertEqual(out["status"],"R44_CAPTURE_HOLD_REASON_OBSERVED")
        self.assertEqual(out["r39ProbeStatus"],"HOLD_SCRIPT_CURSOR_CHANGED")
        self.assertIsNone(out["classScriptResref"])
        self.assertTrue(out["noAutoRetry"])

    def test_11_false_native_pass_cannot_claim_live_class(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_LIVE_CLASS_NAME_PROOF_INVALID"):
            self.invoke("numeric_capture","R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM")

    def test_12_success_is_assignment_only_not_BCS_execution(self):
        out=self.invoke("numeric_capture","R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM",
            details={"classScriptResrefAtLiveJaganVerified":True,
                     "classScriptResref":"BDDEFAI","partyIndex":1,"scrlev":4,
                     "actualBcsExecutionVerified":False,
                     "manualEpsActionOriginVerified":False,
                     "r39ProbeStatus":"R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY",
                     "r39ClassSlotState":"VALID_NAME_CANDIDATE"})
        self.assertEqual(out["status"],"R44_CAPTURE_EXACT_GUARDED_PASS")
        self.assertEqual(out["classScriptResref"],"BDDEFAI")
        self.assertFalse(out["actualBcsExecutionVerified"])
        self.assertFalse(out["manualEpsActionOriginVerified"])

    def test_13_hold_claiming_live_proof_denied(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_HOLD_DISGUISED_AS_PROOF"):
            self.invoke("numeric_capture","R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
                        rc=3,details={"classScriptResrefAtLiveJaganVerified":True})

    def test_14_bad_native_report_fail_closed_with_reason(self):
        out=self.invoke("numeric_status","R44_STOP_MANUAL_REVIEW",rc=3,
                        details={"reason":"HOLD_PROOF_INVALID"})
        self.assertEqual(out["status"],"R44_NATIVE_HOLD_DETAILS")
        self.assertEqual(out["nativeReason"],"HOLD_PROOF_INVALID")
        self.assertTrue(out["noAutoRetry"])

    def test_15_no_unknown_modes(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_UNSUPPORTED_MODE"):
            self.invoke("numeric_invalid","R44_NOT_INSTALLED_R43_PRESENT_LAST")

    def test_16_r44_does_not_invent_new_cmd(self):
        raw=CHILD.read_text(encoding="utf-8")
        self.assertIn("run_numeric_guarded(",raw)
        self.assertNotIn("BGXAI_UPDATE2.cmd",raw)
        self.assertNotIn("XEquipItem(",raw)
        self.assertNotIn("SetGlobal(",raw)

    def test_17_native_bad_exit_on_positive_is_hold(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_NATIVE_EXIT_CODE"):
            self.invoke("numeric_status","R44_NOT_INSTALLED_R43_PRESENT_LAST",rc=3)

    def test_18_result_does_not_echo_actor_ids_or_inventory(self):
        out=self.invoke("numeric_capture","R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
            rc=3,details={"r39ProbeStatus":"HOLD_SCRIPT_ACTOR_CHANGED","actorId":987654321,
                          "inventoryPrivate":"private","r39ClassSlotState":"NOT_READ"})
        self.assertNotIn("actorId",out)
        self.assertNotIn("inventoryPrivate",out)

if __name__=="__main__":
    unittest.main()
