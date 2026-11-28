"""V2 original hub R50 one guarded menu below 32K; no second CMD, mock only."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SRC=HERE/"BGXAI_MODULE187_R50_GUARDED_SAME_ONEFILE.py"
sp=importlib.util.spec_from_file_location("bgxai_original_187_r50",SRC)
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)

class FakeR50Native:
 SCHEMA="BGXAI_R50_JAGAN_DWARF_CLERIC_LAST161_GUARDED_V1"
 INSTALL_TOKEN=M.INSTALL
 ROLLBACK_TOKEN=M.ROLLBACK
 ONCE_FLAG="BGX48TRY"
 SOURCE_BCS="override/BDDEFAI.BCS"
 def __init__(self):self.operations=[];self.installed=False
 def load_checked(self):
  self.operations.append("source")
  return ("r49","r48","r47","r44","r43","r42","r38","old","composer")
 def status(self,*args):
  self.operations.append("status")
  return {"schema":self.SCHEMA,
    "status":"R50_LAST161_INSTALLED_AWAITING_GAME" if self.installed else
             "R50_NOT_INSTALLED_R49_LAST160",
    "installed":self.installed,"gameModified":False,"ordersSent":0,
    "actualXEquipPerformed":False}
 def preflight(self,*args):
  self.operations.append("preflight")
  return {"schema":self.SCHEMA,
   "status":"R50_R49_LAST160_SOURCE_PREFLIGHT_PASS_NO_INSTALL",
   "r49Last160Verified":True,"falseNameGuardRemoved":True,
   "party1DwarfClericGuardPreserved":True,
   "oldOneShotBGX48TRYPreserved":True,
   "nativeCompiledOnUserGame":False,"installed":False,
   "gameModified":False,"ordersSent":0,
   "candidateBAFSHA256":"a"*64}
 def install(self,*args):
  self.operations.append("install")
  self.installed=True
  return {"schema":self.SCHEMA,
    "status":"R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME",
    "installed":True,"r49Last160Preserved":True,
    "userApproved":True,"sourceItem":"STAF01",
    "sourceBackpackSlots":list(range(18,34)),
    "onceFlag":"BGX48TRY","targetWeaponSlot":35,
    "ordersSentAtInstall":0,"actualXEquipPerformed":False}
 def rollback(self,*args):
  self.operations.append("rollback")
  self.installed=False
  return {"schema":self.SCHEMA,
    "status":"R50_ROLLBACK_RESTORED_ORIGINAL_R49_LAST160",
    "installed":False,"gameModified":True}

class V2OriginalR50(unittest.TestCase):
 def setUp(self):
  td=tempfile.TemporaryDirectory()
  self.addCleanup(td.cleanup)
  self.game=Path(td.name)
  self.native=FakeR50Native()
 def call(self,kind,token=""):
  return M.run(self.game,kind,token,require_windows=False,
               loader=lambda:self.native)

 def test_01_default_status_ro_last160(self):
  r=self.call("status")
  self.assertEqual(r["status"],"R50_ABSENT_R49_LAST160_VERIFIED_READONLY")
  self.assertFalse(r["installed"])
  self.assertEqual(self.native.operations,["source","status"])
  self.assertFalse((self.game/"BGXR50").exists())

 def test_02_status_ro_last161_real_native(self):
  self.native.installed=True
  r=self.call("status")
  self.assertEqual(r["status"],"R50_LAST161_INSTALLED_VERIFIED_READONLY")
  self.assertTrue(r["installed"])
  self.assertFalse(r["gameModified"])
  self.assertFalse(r["actualXEquipPerformed"])
  self.assertEqual(self.native.operations,["source","status"])

 def test_03_preflight_ro_never_install(self):
  r=self.call("preflight")
  self.assertEqual(r["status"],"R50_R49_LAST160_PREFLIGHT_PASS_READONLY")
  self.assertFalse(r["gameModified"])
  self.assertEqual(self.native.operations,["source","preflight"])

 def test_04_guarded_install_exact_separate_token(self):
  r=self.call("install",M.INSTALL)
  self.assertEqual(r["status"],"R50_LAST161_INSTALLED_AWAITING_GAMEPLAY")
  self.assertTrue(r["originalR49Last160Preserved"])
  self.assertEqual(self.native.operations,["source","install"])
  self.assertFalse(r["actualXEquipPerformed"])

 def test_05_rollback_has_DIFFERENT_exact_token(self):
  r=self.call("rollback",M.ROLLBACK)
  self.assertEqual(r["status"],"R50_ROLLBACK_TO_R49_LAST160_VERIFIED")
  self.assertFalse(r["installed"])
  self.assertEqual(self.native.operations,["source","rollback"])

 def test_06_wrong_install_token_fail_before_source(self):
  with self.assertRaisesRegex(M.Hold,"EXACT_INSTALL_CONSENT"):
   self.call("install",M.OPEN)
  self.assertEqual(self.native.operations,[])

 def test_07_rollback_token_cannot_install(self):
  with self.assertRaisesRegex(M.Hold,"EXACT_INSTALL_CONSENT"):
   self.call("install",M.ROLLBACK)
  self.assertEqual(self.native.operations,[])

 def test_08_install_token_cannot_rollback(self):
  with self.assertRaisesRegex(M.Hold,"EXACT_ROLLBACK_CONSENT"):
   self.call("rollback",M.INSTALL)
  self.assertEqual(self.native.operations,[])

 def test_09_source_only_rejects_approval_token(self):
  with self.assertRaisesRegex(M.Hold,"READONLY_TOKEN_NOT_ALLOWED"):
   self.call("status",M.INSTALL)

 def test_10_original_hub_outer_token_REQUIRED_before_input(self):
  with patch("builtins.input",side_effect=AssertionError("must not prompt")):
   self.assertEqual(M.main(["--game",str(self.game)]),3)
   self.assertEqual(M.main(["--game",str(self.game),
                            "--onefile-hub-guarded",
                            "--approved-token",M.INSTALL]),3)

 def test_11_outer_approval_does_NOT_call_native_if_cancelled(self):
  with patch("builtins.input",return_value=""):
   self.assertEqual(M.main(["--game",str(self.game),
      "--onefile-hub-guarded","--approved-token",M.OPEN]),0)
  self.assertEqual(self.native.operations,[])

 def test_12_guarded_inside_choice_requires_EXACT_new_token(self):
  with (patch("builtins.input",side_effect=["3",""]),
        patch.object(M,"run",side_effect=AssertionError("must not execute"))):
   self.assertEqual(M.main(["--game",str(self.game),
       "--onefile-hub-guarded","--approved-token",M.OPEN]),3)

 def test_13_real_guard_PIN_and_same_original R50 frozen contracts(self):
  n=M.load_native()
  self.assertEqual(n.INSTALL_TOKEN,M.INSTALL)
  self.assertEqual(n.ROLLBACK_TOKEN,M.ROLLBACK)
  self.assertTrue(callable(n.exact_last_161))
  self.assertTrue(callable(n.preflight))

 def test_14_new_updater_not_created_and_no_game_engine_commands(self):
  raw=SRC.read_text("ascii")
  for forbidden in ("BGXAI_UPDATE2.cmd","ClearActions(","ForceAttack(",
                    "XEquipItem(","native_weidu(", "SELECT_WEAPON_ABILITY"):
   self.assertNotIn(forbidden,raw)
  self.assertIn("native.install(",raw)
  self.assertIn("native.rollback(",raw)

 def test_15_readonly_fake_contract_forgery_stops(self):
  self.native.status=lambda *a:{"schema":self.native.SCHEMA,
       "status":"R50_LAST161_INSTALLED_AWAITING_GAME",
       "gameModified":False,"ordersSent":0,"installed":False}
  with self.assertRaisesRegex(M.Hold,"STATUS_INSTALLED_CONTRADICTION"):
   self.call("status")

 def test_16_forged_native_install_does_not_count_as_proof(self):
  self.native.install=lambda *a:{"schema":self.native.SCHEMA,
      "status":"R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME",
      "installed":True,"r49Last160Preserved":True,
      "userApproved":True,"sourceItem":"STAF01",
      "sourceBackpackSlots":[22],
      "onceFlag":"BGX48TRY","targetWeaponSlot":35,
      "ordersSentAtInstall":0,"actualXEquipPerformed":False}
  with self.assertRaisesRegex(M.Hold,"NATIVE_INSTALL_MANUAL_REVIEW"):
   self.call("install",M.INSTALL)

if __name__=="__main__":
 unittest.main()
