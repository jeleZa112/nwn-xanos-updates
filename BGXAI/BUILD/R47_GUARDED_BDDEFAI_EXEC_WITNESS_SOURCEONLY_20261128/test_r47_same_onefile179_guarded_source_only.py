"""R47 original BGXAI_UPDATE.cmd menu179->18..22; all offline source tests."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CHILD=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py"
sp=importlib.util.spec_from_file_location("r47_onefile_child",CHILD)
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
COMMIT="a"*40

class R47Onefile179(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.game=Path(self.temp.name)/"eet"
  self.game.mkdir()
  (self.game/"chitin.key").write_bytes(b"UNCHANGED_GAME_FIXTURE")
  self.fetched=[]
  self.called=[]
 def fetch(self,commit,path):
  self.assertEqual(commit,COMMIT)
  self.fetched.append(path)
  return (REPO/path).read_bytes()
 def mock(self,mode="r47_preflight",state=None,token=None,code=0):
  native=mode.split("_",1)[1]
  expected={
   "preflight":"R47_PREFLIGHT_R44_LAST157_PASS_NO_INSTALL",
   "install":"R47_INERT_BDDEFAI_WITNESS_INSTALLED_AWAITING_LIVE",
   "status":"R47_NOT_INSTALLED_R44_PRESENT_LAST",
   "rollback":"R47_ROLLBACK_RESTORED_R44_LAST",
   "capture":"R47_LIVE_BDDEFAI_WITNESS_TRIGGER_EVALUATED_NO_ARM"}
  inner={"schema":"BGXAI_R47_INERT_BDDEFAI_EXEC_WITNESS_LAST158_V1",
         "status":expected[native],
         "installed":native in ("install","capture"),
         "gameModified":native in ("install","rollback"),
         "ordersSent":0,"armAuthorized":False,"dispatchAuthorized":False,
         "actualBcsExecutionVerified":False,
         "manualEpsActionOriginVerified":False,
         "originalBcsSha256":"24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331",
         "expectedLuaSha256":R.R47_LUA_SHA,"expectedBafSha256":R.R47_BAF_SHA,
         "sourceBafSha256":R.R47_BAF_SHA,"sourceLuaSha256":R.R47_LUA_SHA,
         "observedWitnessRows":1,"actualBcsWitnessBlockEvaluated":True,
         "actualBcsActionExecutionVerified":False}
  if state:inner.update(state)
  parent=self
  class Response:
   returncode=code
   stdout="progress\n"+json.dumps(inner)
  def runner(command,**kw):
   parent.called.append((command,kw))
   self.assertTrue(str(command[1]).endswith("BGXAI_R47_WITNESS_LAST157_TO158_GUARDED_SOURCE_ONLY.py"))
   self.assertTrue(Path(kw["cwd"]).is_dir())
   self.assertFalse(Path(kw["cwd"]).is_relative_to(self.game))
   self.assertIn("--onefile-review-gate",command)
   self.assertNotIn("--force-install",command)
   return Response()
  return R.run_r47_guarded(self.game,COMMIT,mode,fetcher=self.fetch,
        runner=runner,require_windows=False,approved_token=token)

 def test_01_preserves_entire_menu_1_to17(self):
  expected={"1":"source","2":"status","3":"preflight","4":"install",
   "5":"rollback","6":"capture","7":"diag_status","8":"diag_preflight",
   "9":"diag_install","10":"diag_rollback","11":"diag_capture",
   "12":"numeric_status","13":"numeric_preflight","14":"numeric_install",
   "15":"numeric_rollback","16":"numeric_capture","17":"r46_native_ro"}
  for k,v in expected.items():self.assertEqual(R.MODES[k],v)
  self.assertEqual(R.MODES["18"],"r47_preflight")
  self.assertEqual(R.MODES["19"],"r47_install")
  self.assertEqual(R.MODES["20"],"r47_status")
  self.assertEqual(R.MODES["21"],"r47_rollback")
  self.assertEqual(R.MODES["22"],"r47_capture")

 def test_02_native_preflight_only_readonly(self):
  out=self.mock()
  self.assertEqual(out["status"],"R47_PREFLIGHT_EXACT_GUARDED_PASS")
  self.assertFalse(out["gameModified"])
  self.assertFalse(out["installed"])
  self.assertFalse(out["armAuthorized"])
  self.assertEqual(out["ordersSent"],0)

 def test_03_15_exact_sha_pinned_source_dependencies(self):
  self.mock()
  self.assertEqual(len(self.fetched),15)
  self.assertEqual(len(set(self.fetched)),15)
  self.assertIn(R.R47_GUARD,self.fetched)
  self.assertIn(R.R47_COMPOSE,self.fetched)
  self.assertIn(R.R46_PREVIOUS_BAF,self.fetched)
  self.assertIn(R.R44_GUARD,self.fetched)
  self.assertEqual((self.game/"chitin.key").read_bytes(),b"UNCHANGED_GAME_FIXTURE")

 def test_04_install_requires_typed_user_approval_before_fetch(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_EXACT_TYPED_APPROVAL_REQUIRED"):
   self.mock("r47_install")
  self.assertEqual(self.fetched,[])
  self.assertEqual(self.called,[])

 def test_05_typed_install_claims_modified_but_no_orders(self):
  out=self.mock("r47_install",token=R.R47_INSTALL_CONFIRM)
  self.assertEqual(out["status"],"R47_INSTALL_EXACT_GUARDED_PASS")
  self.assertTrue(out["gameModified"]);self.assertTrue(out["installed"])
  self.assertEqual(out["ordersSent"],0)
  self.assertFalse(out["armAuthorized"])

 def test_06_rollback_requires_distinct_explicit_approval(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_EXACT_TYPED_APPROVAL_REQUIRED"):
   self.mock("r47_rollback",token=R.R47_INSTALL_CONFIRM)
  self.assertEqual(self.fetched,[])

 def test_07_typed_rollback_is_its_own_action(self):
  out=self.mock("r47_rollback",token=R.R47_ROLLBACK_CONFIRM)
  self.assertEqual(out["status"],"R47_ROLLBACK_EXACT_GUARDED_PASS")
  self.assertTrue(out["gameModified"]);self.assertFalse(out["installed"])

 def test_08_readonly_status_without_installed_witness(self):
  out=self.mock("r47_status")
  self.assertEqual(out["innerStatus"],"R47_NOT_INSTALLED_R44_PRESENT_LAST")
  self.assertFalse(out["gameModified"]);self.assertFalse(out["installed"])

 def test_09_one_live_capture_only_when_installed(self):
  out=self.mock("r47_capture")
  self.assertEqual(out["status"],"R47_CAPTURE_EXACT_GUARDED_PASS")
  self.assertTrue(out["actualBcsWitnessBlockEvaluated"])
  self.assertFalse(out["actualBcsExecutionVerified"])
  self.assertFalse(out["manualEpsActionOriginVerified"])

 def test_10_capture_missing_witness_holds_no_retry(self):
  out=self.mock("r47_capture",state={
    "status":"R47_CAPTURE_HOLD_WITNESS_NOT_OBSERVED",
    "observedWitnessRows":0,"actualBcsWitnessBlockEvaluated":False,
    "noAutoRetry":True},code=3)
  self.assertTrue(out["noAutoRetry"])
  self.assertEqual(out["status"],"R47_CAPTURE_HOLD_REASON_OBSERVED")

 def test_11_capture_fake_success_without_witness_rejected(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_CAPTURE_FALSE_PROOF"):
   self.mock("r47_capture",state={"actualBcsWitnessBlockEvaluated":False})

 def test_12_game_modified_false_on_installer_claim_rejected(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_NATIVE_GAME_MODIFIED_FLAG"):
   self.mock("r47_install",state={"gameModified":False},token=R.R47_INSTALL_CONFIRM)

 def test_13_native_baf_or_Lua_pin_mismatch_rejected(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_NATIVE_PREIMAGE_OR_BAF_PIN"):
   self.mock(state={"expectedBafSha256":"0"*64})

 def test_14_corrupt_fetched_source_stops_before_native(self):
  def fetcher(commit,path):
   data=(REPO/path).read_bytes()
   return data+b"bad" if path==R.R47_GUARD else data
  with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_SHA_DRIFT"):
   R.run_r47_guarded(self.game,COMMIT,"r47_preflight",
    fetcher=fetcher,runner=lambda *a,**k:None,require_windows=False)

 def test_15_no_second_CMD_or_direct_gameplay_actions(self):
  s=CHILD.read_text(encoding="utf-8")
  self.assertNotIn("BGXAI_UPDATE2.cmd",s)
  self.assertNotIn("XEquipItem(",s)
  self.assertIn("run_r47_guarded(",s)

 def test_16_unknown_status_fail_closed(self):
  out=self.mock(state={"status":"SUCCESS_BUT_NOT_REAL"})
  self.assertEqual(out["status"],"R47_NATIVE_HOLD_DETAILS")
  self.assertTrue(out["noAutoRetry"])

if __name__=="__main__":
 unittest.main()
