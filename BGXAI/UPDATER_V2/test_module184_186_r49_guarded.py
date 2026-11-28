"""Original onefile V2 guarded R49 native bridge: fake-game only."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SRC=HERE/"BGXAI_MODULE184_186_R49_ORIGINAL_GUARDED.py"
sp=importlib.util.spec_from_file_location("original_v2_r49",SRC)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)

class FakeNative:
 SCHEMA="BGXAI_R49_BACKPACK16_ONE_STAF01_LAST160_GUARDED_V1"
 INSTALL_TOKEN=m.INSTALL
 ROLLBACK_TOKEN=m.ROLLBACK
 ONCE_FLAG="BGX48TRY"
 SOURCE_BCS="override/BDDEFAI.BCS"
 def __init__(self):
  self.operations=[]
  self.installed=False
 def load_checked(self):
  self.operations.append(("load",))
  return ("r48","r47","r44","r43","r42","r38","old","composer")
 def status(self,*args):
  self.operations.append(("status",args))
  return {"schema":self.SCHEMA,
   "status":("R49_BACKPACK16_LAST160_INSTALLED_AWAITING_GAME" if self.installed
             else "R49_NOT_INSTALLED_R48_LAST159"),
   "installed":self.installed,"gameModified":False,
   "ordersSent":0,"actualXEquipPerformed":False}
 def preflight(self,*args):
  self.operations.append(("preflight",args))
  return {"schema":self.SCHEMA,
   "status":"R49_SOURCE_PREFLIGHT_R48_LAST159_PASS_NO_INSTALL",
   "originalR48Last159Verified":True,"oldR48OneShotFlagReused":True,
   "onlyOneNewXEquipSourceAction":True,
   "nativeCompilationOnUserEETVerified":False,
   "gameModified":False,"ordersSent":0,"installed":False,
   "candidateBafSHA256":"0"*64}
 def install(self,*args):
  self.operations.append(("install",args))
  self.installed=True
  return {"schema":self.SCHEMA,
   "status":"R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME",
   "installed":True,"originalR48Last159Preserved":True,
   "sourceBackpackSlot22Included":True,"sourceBackpackSlots":list(range(18,34)),
   "onceFlag":"BGX48TRY","ordersSentAtInstall":0,
   "actualXEquipPerformed":False}
 def rollback(self,*args):
  self.operations.append(("rollback",args))
  self.installed=False
  return {"schema":self.SCHEMA,
   "status":"R49_ROLLBACK_RESTORED_ORIGINAL_R48_LAST159",
   "installed":False}

class V2OnefileR49(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.game=Path(self.tmp.name)
  self.native=FakeNative()
 def call(self,token=""):
  return m.run(self.game,token=token,require_windows=False,
          loader=lambda:self.native)
 def test_01_readonly_preflight_uninstalled(self):
  x=self.call()
  self.assertEqual(x["status"],"R49_LAST159_TO160_PREFLIGHT_PASS_READONLY")
  self.assertFalse(x["installed"])
  self.assertFalse(x["gameModified"])
  self.assertEqual(x["ordersSent"],0)
  self.assertEqual([x[0] for x in self.native.operations],
                   ["load","status","preflight"])
  self.assertFalse((self.game/"BGXR49").exists())
 def test_02_readonly_status_after_install_only_status_no_preflight(self):
  self.native.installed=True
  x=self.call()
  self.assertEqual(x["status"],"R49_LAST160_INSTALLED_VERIFIED_READONLY")
  self.assertTrue(x["installed"])
  self.assertFalse(x["actualXEquipPerformed"])
  self.assertEqual([x[0] for x in self.native.operations],["load","status"])
 def test_03_typed_install_preserves_original_native(self):
  x=self.call(m.INSTALL)
  self.assertEqual(x["status"],"R49_LAST160_INSTALLED_AWAITING_GAMEPLAY")
  self.assertTrue(x["installed"])
  self.assertFalse(x["actualXEquipPerformed"])
  self.assertEqual(self.native.operations[-1][0],"install")
  self.assertEqual(self.native.operations[-1][1][-1],m.INSTALL)
 def test_04_separate_exact_rollback(self):
  x=self.call(m.ROLLBACK)
  self.assertEqual(x["status"],"R49_ROLLBACK_RESTORED_R48_LAST159")
  self.assertFalse(x["installed"])
  self.assertEqual(self.native.operations[-1][0],"rollback")
  self.assertEqual(self.native.operations[-1][1][-1],m.ROLLBACK)
 def test_05_unknown_token_fails_before_native_code(self):
  with self.assertRaisesRegex(m.Hold,"HOLD_R49_ONEFILE_EXACT_TOKEN"):
   self.call("ATTACK")
  self.assertEqual(self.native.operations,[])
 def test_06_direct_no_hub_flags_cannot_run(self):
  with patch.object(m,"run",side_effect=AssertionError("must not run")):
   self.assertEqual(m.main(["--game",str(self.game)]),3)
 def test_07_wrong_confirmation_cannot_enter_game(self):
  with patch.object(m,"run",side_effect=AssertionError("must not run")):
   self.assertEqual(m.main(["--game",str(self.game),
      "--onefile-hub-guarded","--approved-token","INSTALL_FAKE"]),3)
 def test_08_double_flags_rejected(self):
  with patch.object(m,"run",side_effect=AssertionError("must not run")):
   self.assertEqual(m.main(["--game",str(self.game),
      "--onefile-hub-guarded","--onefile-hub-source-only",
      "--approved-token",m.INSTALL]),3)
 def test_09_unchanged_native_guard_git_blob_and_frozen_tokens(self):
  g=m.load_native()
  self.assertEqual(g.INSTALL_TOKEN,m.INSTALL)
  self.assertEqual(g.ROLLBACK_TOKEN,m.ROLLBACK)
  self.assertTrue(callable(g.exact_last_160))
  self.assertTrue(callable(g.preflight))
  self.assertEqual(g.SCHEMA,self.native.SCHEMA)
 def test_10_immutability_and_no_second_installer(self):
  raw=SRC.read_text(encoding="ascii")
  for t in ("XEquipItem(", "ClearActions(", "Attack(", "BGXAI_UPDATE2.cmd",
            "native_weidu(", "setup-BGXR49.exe"):
   self.assertNotIn(t,raw)
  self.assertIn("native.install(",raw)
  self.assertIn("native.rollback(",raw)
  self.assertIn("native.preflight(",raw)
 def test_11_fail_closed_forged_compat_readonly(self):
  self.native.preflight=lambda *a:{
    "schema":self.native.SCHEMA,
    "status":"R49_SOURCE_PREFLIGHT_R48_LAST159_PASS_NO_INSTALL",
    "installed":False,"gameModified":False,"ordersSent":0,
    "originalR48Last159Verified":True,
    "oldR48OneShotFlagReused":True,
    "onlyOneNewXEquipSourceAction":True,
    "nativeCompilationOnUserEETVerified":True}
  with self.assertRaisesRegex(m.Hold,"NATIVE_PREFLIGHT_CONTRACT"):
   self.call()
 def test_12_fail_closed_forged_installer_status(self):
  self.native.install=lambda *a:{
    "schema":self.native.SCHEMA,
    "status":"R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME",
    "installed":True,"originalR48Last159Preserved":True,
    "sourceBackpackSlots":[22],"sourceBackpackSlot22Included":True,
    "onceFlag":"BGX48TRY","ordersSentAtInstall":0,
    "actualXEquipPerformed":False}
  with self.assertRaisesRegex(m.Hold,"NATIVE_INSTALL_PROOF"):
   self.call(m.INSTALL)
 def test_13_real_windows_root_gate_blocks_linux(self):
  import os
  if os.name!="nt":
   with self.assertRaisesRegex(m.Hold,"EXACT_WINDOWS_GAME"):
    m.run(self.game,loader=lambda:self.native)
if __name__=="__main__":
 unittest.main()
