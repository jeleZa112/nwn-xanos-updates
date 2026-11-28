"""R48 one-CMD menu 179→23 typed real item pilot, 24 rollback, 25 status; mocks ONLY."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CHILD=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py"
sp=importlib.util.spec_from_file_location('r48_original_onefile179',CHILD)
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
PIN="b"*40
class OriginalOnefileR48(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.game=Path(self.tmp.name)/"game"
  self.game.mkdir()
  (self.game/"chitin.key").write_bytes(b"STATIC_GAME")
  self.fetched=[]
  self.called=[]
 def fetch(self,commit,path):
  self.assertEqual(commit,PIN)
  self.fetched.append(path)
  return (REPO/path).read_bytes()
 def mock(self,mode="r48_install",status=None,token=None,sourceSha=None,rc=0,mod=None):
  native=mode.split("_",1)[1]
  assert native in ("install","rollback","status")
  expected={"install":"R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME",
            "rollback":"R48_ROLLBACK_RESTORED_R47_LAST158",
            "status":"R48_NOT_INSTALLED_R47_LAST158"}
  inner={"schema":"BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1",
         "status":status or expected[native],
         "installed":native=="install",
         "gameModified":native in ("install","rollback"),
         "candidateBafSHA256":sourceSha or M.R48_ACTION_BAF_SHA,
         "userApprovedRealItemMove":native=="install",
         "sourceItem":"STAF01","sourceBackpackSlot":20,"targetWeaponSlot":35,
         "onceFlag":"BGX48TRY","ordersSentAtInstall":0,
         "actualXEquipPerformed":False}
  if mod:inner.update(mod)
  testcase=self
  class R:
   stdout="other preamble\n"+json.dumps(inner)
   returncode=rc
  def runner(command,**kw):
   testcase.called.append((command,kw))
   testcase.assertTrue(str(command[1]).endswith("BGXAI_R48_LAST158_TO159_ONE_ITEM_GUARDED.py"))
   testcase.assertIn("--onefile-review-gate",command)
   testcase.assertFalse(Path(kw["cwd"]).is_relative_to(testcase.game))
   testcase.assertNotIn("--force-install",command)
   testcase.assertNotIn("InfinityLoader.exe",str(command))
   return R()
  return M.run_r48_real_equip(self.game,PIN,mode,
      fetcher=self.fetch,runner=runner,require_windows=False,approved_token=token)

 def test_01_preserve_earlier_179_modes(self):
  checks={"1":"source","2":"status","3":"preflight","4":"install","5":"rollback",
   "6":"capture","7":"diag_status","8":"diag_preflight","9":"diag_install",
   "10":"diag_rollback","11":"diag_capture","12":"numeric_status",
   "13":"numeric_preflight","14":"numeric_install","15":"numeric_rollback",
   "16":"numeric_capture","17":"r46_native_ro","18":"r47_preflight",
   "19":"r47_install","20":"r47_status","21":"r47_rollback","22":"r47_capture"}
  for k,v in checks.items():self.assertEqual(M.MODES[k],v)
  self.assertEqual(M.MODES["23"],"r48_install")
  self.assertEqual(M.MODES["24"],"r48_rollback")
  self.assertEqual(M.MODES["25"],"r48_status")

 def test_02_real_item_install_requires_exact_user_token_before_download(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R48_EXACT_TYPED_USER_CONSENT_REQUIRED"):
   self.mock("r48_install")
  self.assertFalse(self.fetched)
  self.assertFalse(self.called)

 def test_03_integration_stages_existing_sources_only(self):
  r=self.mock(token=M.R48_INSTALL_CONFIRM)
  self.assertEqual(r["status"],"R48_INSTALL_EXACT_GUARDED_PASS")
  self.assertEqual(len(self.fetched),17)
  self.assertEqual(len(set(self.fetched)),17)
  self.assertIn(M.R48_GUARD,self.fetched)
  self.assertIn(M.R48_COMPOSE,self.fetched)
  self.assertIn(M.R46_PREVIOUS_BAF,self.fetched)
  self.assertIn(M.R47_GUARD,self.fetched)
  self.assertEqual((self.game/"chitin.key").read_bytes(),b"STATIC_GAME")

 def test_04_installer_arms_one_real_equip_but_does_not_claim_executed(self):
  r=self.mock(token=M.R48_INSTALL_CONFIRM)
  self.assertTrue(r["installed"]);self.assertTrue(r["gameModified"])
  self.assertTrue(r["automaticOneShotInGameAttemptArmedByInstall"])
  self.assertFalse(r["actualXEquipPerformed"])
  self.assertEqual(r["ordersSentAtInstall"],0)
  self.assertEqual(r["onceFlag"],"BGX48TRY")

 def test_05_rollbacks_require_distinct_typed_consent(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R48_EXACT_TYPED_USER_CONSENT_REQUIRED"):
   self.mock(mode="r48_rollback",token=M.R48_INSTALL_CONFIRM)
  self.assertFalse(self.fetched)

 def test_06_rollback_reports_only_BCS_restore(self):
  r=self.mock(mode="r48_rollback",token=M.R48_ROLLBACK_CONFIRM)
  self.assertTrue(r["gameModified"])
  self.assertFalse(r["installed"])
  self.assertFalse(r["actualXEquipPerformed"])

 def test_07_status_readonly_and_does_not_arm(self):
  r=self.mock(mode="r48_status")
  self.assertFalse(r["installed"]);self.assertFalse(r["gameModified"])
  self.assertFalse(r["automaticOneShotInGameAttemptArmedByInstall"])

 def test_08_reject_wrong_action_sha(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R48_GAMEPLAY_ACTION_SOURCE_CONTRACT"):
   self.mock(token=M.R48_INSTALL_CONFIRM,sourceSha="0"*64)

 def test_09_reject_false_report_saying_inventory_moved_by_mock(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R48_GAMEPLAY_ACTION_SOURCE_CONTRACT"):
   self.mock(token=M.R48_INSTALL_CONFIRM,mod={"actualXEquipPerformed":True})

 def test_10_reject_native_nonzero_or_STOP_no_retry(self):
  r=self.mock(token=M.R48_INSTALL_CONFIRM,status="R48_STOP_MANUAL_REVIEW",
              mod={"reason":"HOLD_NATIVE_WEIDU_MANUAL_REVIEW"},rc=3)
  self.assertEqual(r["status"],"R48_NATIVE_HOLD_DETAILS")
  self.assertTrue(r["noAutoRetry"])
  self.assertTrue(r["gameModifiedUnknown"])

 def test_11_corrupt_SHA_source_cannot_execute_installer(self):
  def corrupt(commit,path):
   data=(REPO/path).read_bytes()
   return data+b"bad" if path==M.R48_GUARD else data
  with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_SHA_DRIFT"):
   M.run_r48_real_equip(self.game,PIN,"r48_install",
     fetcher=corrupt,runner=lambda *a,**kw:None,require_windows=False,
     approved_token=M.R48_INSTALL_CONFIRM)

 def test_12_no_second_CMD_or_implicit_game_start(self):
  s=CHILD.read_text(encoding="utf-8")
  self.assertNotIn("BGXAI_UPDATE2.cmd",s)
  self.assertNotIn("XEquipItem(",s)
  self.assertIn("run_r48_real_equip",s)

if __name__=="__main__":
 unittest.main()
