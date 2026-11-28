"""R48 closed-console recovery: mock exact status logic, NEVER install/undo."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parent/"BGXAI_MODULE183_R48_STATUS_RO.py"
sp=importlib.util.spec_from_file_location("bgxai_r48_183_ro",SOURCE)
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)

class RecoveryOnly(unittest.TestCase):
 def setUp(self):
    tmp=tempfile.TemporaryDirectory()
    self.addCleanup(tmp.cleanup)
    self.game=Path(tmp.name)
    self.calls=[]
    outer=self
    class OriginalR48:
     SCHEMA="BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1"
     def load_checked(self):
      return ("r47","r44","r43","r42","r38","old","composer")
     def status(self,*args):
      outer.calls.append(("status",args))
      return {"schema":self.SCHEMA,
        "status":"R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT",
        "installed":True,"gameModified":False,"actualXEquipPerformed":False}
     def install(self,*args):
      raise AssertionError("READ-ONLY STATUS MUST NEVER INSTALL")
     def rollback(self,*args):
      raise AssertionError("READ-ONLY STATUS MUST NEVER ROLLBACK")
    self.native=OriginalR48()
    class Bridge:
     def load_original(inner):return outer.native
    self.bridge=Bridge()
 def check(self):
    return mod.inspect(self.game,require_windows=False,
      bridge_loader=lambda:self.bridge)

 def test_01_successful_real_r48_status_does_not_send_action(self):
    out=self.check()
    self.assertEqual(out["status"],"R48_INSTALLED_AWAITING_GAMEPLAY_VERIFIED")
    self.assertEqual(out["nativeStatus"],
                     "R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT")
    self.assertTrue(out["installed"])
    self.assertTrue(out["noInstallOrRollbackAttempted"])
    self.assertFalse(out["gameModified"])
    self.assertEqual(out["ordersSent"],0)
    self.assertFalse(out["actualXEquipPerformed"])
    self.assertEqual(len(self.calls),1)
    self.assertEqual(self.calls[0][0],"status")
    self.assertEqual(self.calls[0][1][-1],self.game)

 def test_02_verified_not_installed_is_not_unverified(self):
    def absent(*a):
     return {"schema":self.native.SCHEMA,
      "status":"R48_NOT_INSTALLED_R47_LAST158",
      "installed":False,"gameModified":False}
    self.native.status=absent
    out=self.check()
    self.assertEqual(out["status"],"R48_NOT_INSTALLED_VERIFIED")
    self.assertFalse(out["installed"])
    self.assertEqual(out["next"],"NO_AUTOMATIC_REINSTALL_OR_ROLLBACK")

 def test_03_pending_weidu_state_never_claims_install(self):
    def uncertain(*a):raise mod.Hold("HOLD_R48_INSTALL_PROOF_INVALID")
    self.native.status=uncertain
    with self.assertRaisesRegex(mod.Hold,"HOLD_R48_INSTALL_PROOF_INVALID"):
     self.check()

 def test_04_forged_installed_native_report_rejected(self):
    self.native.status=lambda *a:{
     "schema":self.native.SCHEMA,
     "status":"R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT",
     "installed":True,"gameModified":True}
    with self.assertRaisesRegex(mod.Hold,"NATIVE_STATUS_CONTRACT"):
     self.check()
    self.native.status=lambda *a:{
     "schema":self.native.SCHEMA,
     "status":"R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT",
     "installed":False,"gameModified":False}
    with self.assertRaisesRegex(mod.Hold,"NATIVE_STATUS_CONTRACT"):
     self.check()

 def test_05_no_direct_run_without_original_onefile(self):
    with patch.object(mod,"inspect",side_effect=AssertionError("should not inspect")):
     self.assertEqual(mod.main(["--game",str(self.game)]),3)

 def test_06_concrete_bridge_imports_original_r48_not_second_guard(self):
    b=mod.load_previous_bridge()
    self.assertEqual(b.INSTALL,
       "INSTALL_BGXAI_R48_ONE_STAF01_FROM_BACKPACK_TO_WEAPON_AFTER_R47")
    original=b.load_original()
    self.assertEqual(original.SCHEMA,
                     "BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1")
    self.assertTrue(callable(original.status))

 def test_07_no_new_game_mutation_or_second_cmd(self):
    s=SOURCE.read_text(encoding="ascii")
    for bad in ("native.install(", "native.rollback(", "XEquipItem(",
                "EXTEND_TOP", "WeiDU --", "BGXAI_UPDATE2.cmd",
                "ClearActions(", "SelectWeaponAbility("):
     self.assertNotIn(bad,s)
    self.assertIn("native.status(",s)

if __name__=="__main__":
 unittest.main()
