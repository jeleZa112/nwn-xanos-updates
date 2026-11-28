"""V2 181/182: exact existing R48 typed real action and rollback, mock only."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
source=HERE/"BGXAI_MODULE181_182_R48_ONE_SHOT_GUARDED.py"
spec=importlib.util.spec_from_file_location("bgxai_v2_181_182",source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class R48V2(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.game=Path(self.tmp.name)
    self.calls=[]
    outer=self
    class Original:
     SCHEMA="BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1"
     def load_checked(self):return ("r47","r44","r43","r42","r38","old","composer")
     def install(self,*args):
        outer.calls.append(("install",args))
        return {"schema":self.SCHEMA,"status":"R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME",
                "installed":True,"userApprovedRealItemMove":True,
                "actualXEquipPerformed":False,"sourceItem":"STAF01",
                "sourceBackpackSlot":20,"targetWeaponSlot":35}
     def rollback(self,*args):
        outer.calls.append(("rollback",args))
        return {"schema":self.SCHEMA,"status":"R48_ROLLBACK_RESTORED_R47_LAST158",
                "installed":False}
    self.native=Original()

 def test_install_only_with_exact_hub_confirmation(self):
    with self.assertRaisesRegex(m.Hold,"EXACT_GUARDED_TOKEN_REQUIRED"):
      m.run(self.game,"arbitrary",require_windows=False,loader=lambda:self.native)
    self.assertEqual(self.calls,[])
    res=m.run(self.game,m.INSTALL,require_windows=False,loader=lambda:self.native)
    self.assertEqual(res["status"],"R48_GUARDED_ONE_SHOT_INSTALLED_AWAITING_GAME")
    self.assertEqual(len(self.calls),1)
    self.assertEqual(self.calls[0][0],"install")
    self.assertEqual(self.calls[0][1][-1],m.INSTALL)
    self.assertFalse(res["actualXEquipPerformed"])
    self.assertFalse((self.game/"BGXR48").exists())

 def test_rollback_requires_independent_token(self):
    res=m.run(self.game,m.ROLLBACK,require_windows=False,loader=lambda:self.native)
    self.assertEqual(res["status"],"R48_GUARDED_LAST159_ROLLBACK_COMPLETE")
    self.assertEqual(self.calls[0][0],"rollback")
    self.assertEqual(self.calls[0][1][-1],m.ROLLBACK)
    self.assertFalse(res["installed"])
    self.assertFalse((self.game/"BGXR48").exists())

 def test_hub_missing_flag_does_not_load_or_write(self):
    with patch.object(m,"run",side_effect=RuntimeError("should not execute")):
      rc=m.main(["--game",str(self.game),"--approved-token",m.INSTALL])
    self.assertEqual(rc,3)
    self.assertFalse((self.game/"BGXR48").exists())

 def test_hub_wrong_token_no_execution(self):
    with patch.object(m,"run",side_effect=RuntimeError("should not execute")):
      rc=m.main(["--game",str(self.game),"--onefile-hub-guarded",
                 "--approved-token","INSTALL_SOMETHING_UNSAFE"])
    self.assertEqual(rc,3)

 def test_wrong_native_install_status_never_claims_success(self):
    self.native.install=lambda *args:{"schema":self.native.SCHEMA,
       "status":"R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME",
       "installed":True,"actualXEquipPerformed":True,
       "userApprovedRealItemMove":True,
       "sourceItem":"STAF01","sourceBackpackSlot":20,"targetWeaponSlot":35}
    with self.assertRaisesRegex(m.Hold,"NATIVE_INSTALL_PROOF_INVALID"):
      m.run(self.game,m.INSTALL,require_windows=False,loader=lambda:self.native)

 def test_missing_guard_fails_closed_before_native_execution(self):
    with patch.object(m,"GUARD",self.game/"NONEXISTENT.py"):
      with self.assertRaisesRegex(m.Hold,"ORIGINAL_GUARD_SOURCE_ABSENT"):
       m.load_original()

 def test_existing_guard_blob_and_token_stable(self):
    native=m.load_original()
    self.assertEqual(native.INSTALL_TOKEN,m.INSTALL)
    self.assertEqual(native.ROLLBACK_TOKEN,m.ROLLBACK)
    self.assertEqual(native.SCHEMA,"BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1")

 def test_real_windows_root_gate_not_bypassed_on_linux(self):
    if __import__("os").name!="nt":
      with self.assertRaisesRegex(m.Hold,"EXACT_WINDOWS_EET_REQUIRED"):
        m.run(self.game,m.INSTALL,loader=lambda:self.native)

 def test_no_executable_engine_code_or_new_updater(self):
    s=source.read_text("ascii")
    for tok in ("XEquipItem(", "ClearActions(", "SelectWeaponAbility(",
                "BGXAI_UPDATE2.cmd", "InfinityLoader.exe"):
       self.assertNotIn(tok,s)
    self.assertIn("native.install(",s)
    self.assertIn("native.rollback(",s)

if __name__=="__main__":
    unittest.main()
