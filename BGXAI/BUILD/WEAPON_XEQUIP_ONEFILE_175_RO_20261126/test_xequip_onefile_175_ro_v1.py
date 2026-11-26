import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126")
spec=importlib.util.spec_from_file_location("m175",BASE/"BGXAI_XEQUIP_ONEFILE_175_RO_V1.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def offline_fetch(commit,path):
    return Path(path).read_bytes()

class TestOnefile175(unittest.TestCase):
    def test_fixed_commit_validation(self):
        self.assertEqual(m.validate_pin("a"*40),"a"*40)
        for x in ("","123", "a"*39, "a"*41,"A"*40,"a"*38+"//",None):
            with self.assertRaises(m.Hold):
                m.validate_pin(x)
    def test_allowlist_pins_verified(self):
        self.assertEqual(len(m.SOURCES),4)
        for p in m.SOURCES:
            m.verify_file(p,Path(p).read_bytes())
    def test_drift_does_not_stage(self):
        for p in m.SOURCES:
            with self.assertRaises(m.Hold):
                m.verify_file(p,Path(p).read_bytes()+b"X")
    def test_source_only_end_to_end_without_eet(self):
        r=m.prepare(Path("/nonexistent/FakeBG"),"a"*40,False,fetcher=offline_fetch)
        self.assertEqual(r["status"],"INERT_SOURCE_PIN_VERIFIED_NO_NATIVE")
        self.assertEqual(len(r["sourcePins"]),4)
        self.assertEqual(r["innerReport"]["ordersSent"],0)
        self.assertFalse(r["gameplayMoveAuthorized"])
        self.assertFalse(r["gameplayFeatureInstalled"])
    def test_native_never_claims_game_success_on_fake_path(self):
        r=m.prepare(Path("/nonexistent/FakeBG"),"a"*40,True,fetcher=offline_fetch)
        self.assertIn(r["status"],("HOLD_INERT_SOURCE_OR_NATIVE_COMPILE","HOLD_WRAPPER_PROCESS"))
        self.assertNotEqual(r["status"],"NATIVE_INERT_WEIDU_COMPILE_PASS_TEMP_ONLY")
    def test_never_fakes_success_after_false_approval(self):
        fake={"installed":False,"ordersSent":0,"dispatchAuthorized":False,
              "inventoryMoveAuthorized":False,
              "status":"NATIVE_WEIDU_COMPILED_TEMP_ONLY",
              "nativeSymbolsAcceptedByCompiler":True,
              "watchedFilesChanged":False,"temporaryOutputRemoved":True}
        self.assertTrue(m.check_report(fake,True))
        for key,value in (("installed",True),("ordersSent",1),
                          ("dispatchAuthorized",True),("inventoryMoveAuthorized",True),
                          ("watchedFilesChanged",True),
                          ("nativeSymbolsAcceptedByCompiler",False),
                          ("temporaryOutputRemoved",False)):
            altered=dict(fake);altered[key]=value
            self.assertFalse(m.check_report(altered,True),key)
    def test_reject_unapproved_path(self):
        with self.assertRaises(m.Hold):
            m.fetch_pinned("a"*40,"BGXAI/override/DPLAYER.BCS")
    def test_source_pins_enforced_after_fetch(self):
        with self.assertRaises(m.Hold):
            with tempfile.TemporaryDirectory() as td:
                m.stage_sources(Path(td),"a"*40,lambda c,p:b"FAKE")
    def test_external_cache_not_in_game(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"game").mkdir();(root/"game"/"cache").mkdir()
            with self.assertRaises(m.Hold):
                m.ensure_external(root/"game"/"cache",root/"game")
    def test_report_saved_one_copy(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"report.json"
            out=m.write_report({"status":"PASS","ordersSent":0},p)
            self.assertEqual(out,str(p))
            self.assertEqual(json.loads(p.read_text())["ordersSent"],0)
            with self.assertRaises(m.Hold):m.write_report({},p)
    def test_inert_generated_baf_only(self):
        r=m.prepare(Path("/nonexistent/Mock"),"a"*40,False,fetcher=offline_fetch)
        self.assertFalse(r["innerReport"]["inventoryMoveAuthorized"])
        self.assertEqual(r["innerReport"]["status"],"INERT_SOURCE_READY_NO_NATIVE_COMPILE")

if __name__=="__main__":
    unittest.main(verbosity=2)
