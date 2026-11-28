"""R46 menu179→17 integration mocks, no network/real game/WeiDU install."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CHILD=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py"
sp=importlib.util.spec_from_file_location('r46_child_179',CHILD)
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
COMMIT="f"*40

class OnefileR46NativeRO(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)/"game"
        self.game.mkdir()
        (self.game/"chitin.key").write_bytes(b"STATIC_GAME_NO_MOD")
        self.fetches=[];self.invocations=[];self.checks=[]

    def status(self,game,commit,mode,**kw):
        self.assertEqual(mode,"numeric_status")
        self.assertEqual(game,self.game)
        self.checks.append(mode)
        return {"schema":R.SCHEMA,"status":"R44_STATUS_EXACT_GUARDED_PASS",
            "innerStatus":"R44_PRESENT_LAST_READONLY",
            "installed":True,"ordersSent":0,"armAuthorized":False,
            "dispatchAuthorized":False}

    def fetch(self,commit,path):
        self.assertEqual(commit,COMMIT)
        self.fetches.append(path)
        return (REPO/path).read_bytes()

    def invoke(self,*,inner_status="R46_NATIVE_BAF_TEMP_PASS_NO_INSTALL",
               changed=False,rc=0,sha=None,return_status=None):
        data={"status":inner_status,"r46BafSourceSha256":sha or R.R46_BAF_SHA,
              "r46BafBytes":223,
              "compiledBcsSha256":"a"*64,
              "watchedFilesChanged":changed,"temporaryOutputRemoved":True,
              "installed":False,"gameModified":False,"ordersSent":0,
              "armAuthorized":False,"dispatchAuthorized":False,
              "nativeStatus":return_status or "NATIVE_WEIDU_COMPILED_TEMP_ONLY"}
        outer=self
        class Resp:
            stdout="dummy\n"+json.dumps(data)
            returncode=rc
        def runner(cmd,**kw):
            outer.invocations.append((cmd,kw))
            self.assertTrue(str(cmd[1]).endswith("BGXAI_R46_NATIVE_COMPILE_RO_REUSE_R39.py"))
            self.assertIn("--native-ro",cmd)
            self.assertTrue(Path(kw["cwd"]).is_dir())
            self.assertFalse(Path(kw["cwd"]).is_relative_to(self.game))
            self.assertNotIn("--force-install",cmd)
            return Resp()
        return R.run_r46_native_readonly(self.game,COMMIT,
            fetcher=self.fetch,runner=runner,require_windows=False,
            status_checker=self.status)

    def test_01_preserve_earlier_179_modes_1_to_16(self):
        self.assertEqual(R.MODES["1"],"source")
        self.assertEqual(R.MODES["6"],"capture")
        self.assertEqual(R.MODES["7"],"diag_status")
        self.assertEqual(R.MODES["11"],"diag_capture")
        self.assertEqual(R.MODES["12"],"numeric_status")
        self.assertEqual(R.MODES["16"],"numeric_capture")
        self.assertEqual(R.MODES["17"],"r46_native_ro")

    def test_02_r44_exact_last157_checked_before_any_new_fetch(self):
        def blocked(*args,**kw):
            return {"status":"R44_NATIVE_HOLD_DETAILS","innerStatus":"STOP"}
        with self.assertRaisesRegex(ValueError,"HOLD_R46_EXACT_R44_LAST157_PROOF_REQUIRED"):
            R.run_r46_native_readonly(self.game,COMMIT,
                fetcher=self.fetch,runner=lambda *a,**k:None,
                require_windows=False,status_checker=blocked)
        self.assertFalse(self.fetches)

    def test_03_six_exact_existing_sources_reused_once(self):
        out=self.invoke()
        self.assertEqual(set(self.fetches),{
            R.R46_COMPOSE,R.R46_NATIVE,R.R46_PREVIOUS_BAF,
            R.R46_R39_NATIVE,R.R46_V3_NATIVE,R.R46_BACKEND})
        self.assertEqual(out["status"],"R46_NATIVE_TEMP_COMPILE_EXACT_PASS_NOT_INSTALLED")
        self.assertEqual(self.checks,["numeric_status"])

    def test_04_readonly_success_not_an_equip(self):
        out=self.invoke()
        self.assertFalse(out["installed"])
        self.assertFalse(out["gameModified"])
        self.assertFalse(out["armAuthorized"])
        self.assertFalse(out["actualBcsExecutionVerified"])
        self.assertFalse(out["R39XEquipInstalled"])
        self.assertEqual(out["ordersSent"],0)
        self.assertEqual((self.game/"chitin.key").read_bytes(),b"STATIC_GAME_NO_MOD")
        self.assertFalse((self.game/"BGXR46").exists())

    def test_05_native_compilation_failure_hold_no_retry(self):
        out=self.invoke(inner_status="HOLD_R46_NATIVE_BAF",rc=3,
                        return_status="WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS")
        self.assertEqual(out["status"],"R46_NATIVE_TEMP_COMPILE_HOLD")
        self.assertEqual(out["nativeStatus"],"WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS")
        self.assertTrue(out["noAutoRetry"])

    def test_06_compiler_touched_watched_file_hold(self):
        out=self.invoke(changed=True)
        self.assertEqual(out["status"],"R46_NATIVE_TEMP_COMPILE_HOLD")

    def test_07_compiler_source_sha_drift_hold(self):
        out=self.invoke(sha="0"*64)
        self.assertEqual(out["status"],"R46_NATIVE_TEMP_COMPILE_HOLD")

    def test_08_compiler_exit_nonzero_on_claimed_pass_hold(self):
        out=self.invoke(rc=3)
        self.assertEqual(out["status"],"R46_NATIVE_TEMP_COMPILE_HOLD")

    def test_09_corrupt_fetched_source_fails_closed(self):
        def corrupt(commit,path):
            payload=(REPO/path).read_bytes()
            return payload+b"oops" if path==R.R46_NATIVE else payload
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_SHA_DRIFT"):
            R.run_r46_native_readonly(self.game,COMMIT,
                fetcher=corrupt,runner=lambda *args,**kw:None,
                require_windows=False,status_checker=self.status)

    def test_10_no_new_updater_and_no_gameplay_actions(self):
        raw=CHILD.read_text(encoding="utf-8")
        self.assertNotIn("BGXAI_UPDATE2.cmd",raw)
        self.assertNotIn("XEquipItem(",raw)
        self.assertIn("run_r46_native_readonly",raw)

if __name__=="__main__":
    unittest.main()
