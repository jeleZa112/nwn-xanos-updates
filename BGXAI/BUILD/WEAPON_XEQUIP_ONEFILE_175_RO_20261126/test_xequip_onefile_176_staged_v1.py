"""Source-only regression: old menu175 must survive new V3 mode176."""
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest

BASE=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126")
def load(name, file):
    s=importlib.util.spec_from_file_location(name,str(BASE/file))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load("old175","BGXAI_XEQUIP_ONEFILE_175_RO_V1.py")
v3=load("stage176","BGXAI_XEQUIP_ONEFILE_175_RO_DUALMODE_STAGE_176.py")
COMMIT="a"*40
def fetch(commit,path):
    assert commit == COMMIT
    return Path(path).read_bytes()

class Tests(unittest.TestCase):
    def test_existing_four_pins_identical(self):
        self.assertEqual(len(old.SOURCES),4)
        self.assertEqual(old.SOURCES,v3.SOURCES)
    def test_old_175_code_identical(self):
        for name in ("prepare","check_report","ensure_external","write_report",
                     "validate_pin","digest"):
            self.assertEqual(inspect.getsource(getattr(old,name)),
                             inspect.getsource(getattr(v3,name)),name)
    def test_old_175_behavior_unmodified(self):
        with tempfile.TemporaryDirectory() as d:
            pass
        out=v3.prepare(Path("/nonexistent/FakeBG"),COMMIT,False,fetcher=fetch)
        self.assertEqual(out["status"],"INERT_SOURCE_PIN_VERIFIED_NO_NATIVE")
        self.assertFalse(out["gameplayFeatureInstalled"])
        self.assertFalse(out["gameplayMoveAuthorized"])
        self.assertEqual(len(out["sourcePins"]),4)
    def test_exact_v3_pins_unchanged(self):
        self.assertEqual(len(v3.V3_SOURCES),3)
        for path,(n,sha) in v3.V3_SOURCES.items():
            raw=Path(path).read_bytes()
            self.assertEqual(len(raw),n,path)
            self.assertEqual(v3.digest(raw),sha,path)
            v3.verify_file(path,raw)
    def test_v3_source_only_no_game(self):
        out=v3.prepare_v3(Path("/nonexistent/FakeBG"),COMMIT,False,fetcher=fetch)
        self.assertEqual(out["status"],"V3_EXACT_SOURCE_PIN_PASS_NOT_NATIVE")
        self.assertFalse(out["innerReport"]["nativeWeiDUCompileVerified"])
        self.assertEqual(len(out["sourcePins"]),3)
        self.assertFalse(out["gameplayFeatureInstalled"])
        self.assertFalse(out["gameplayLiveVerified"])
        self.assertFalse(out["gameplayMoveAuthorized"])
        self.assertFalse(out["safeActionBoundaryVerified"])
        self.assertEqual(out["ordersSent"],0)
    def test_native_missing_user_game_is_hold(self):
        out=v3.prepare_v3(Path("/nonexistent/FakeBG"),COMMIT,True,fetcher=fetch)
        self.assertEqual(out["status"],"HOLD_V3_NATIVE_OR_SOURCE_PREFLIGHT")
        self.assertNotEqual(out["innerReport"]["status"],"V3_NATIVE_BAF_COMPILED_TEMP_ONLY")
    def test_byte_tamper_holds(self):
        for path in v3.V3_SOURCES:
            with self.subTest(path=path):
                data=Path(path).read_bytes()
                with self.assertRaises(v3.Hold):
                    v3.verify_file(path,data+b"\n")
    def test_no_arbitrary_fetch(self):
        with self.assertRaises(v3.Hold):
            v3.fetch_pinned(COMMIT,"BGXAI/override/DPLAYER.BCS")
    def test_no_extra_sources_in_old_menu(self):
        out=v3.prepare(Path("/nonexistent/FakeBG"),COMMIT,False,fetcher=fetch)
        self.assertEqual(set(out["sourcePins"]),set(old.SOURCES))
    def test_accept_only_strict_native_report(self):
        fake=dict(status="V3_NATIVE_BAF_COMPILED_TEMP_ONLY",
            bafSha256=v3.V3_BAF_SHA256,bafBytes=762,
            installed=False,ordersSent=0,dispatchAuthorized=False,
            safeActionBoundaryVerified=False,runtimeActorIdentityVerified=False,
            nativeWeiDUCompileVerified=True,watchedFilesChanged=False,
            temporaryOutputRemoved=True,compiledBcsSha256="a"*64)
        self.assertTrue(v3.check_report_v3(fake,True))
        for key,bad in (
            ("installed",True),("ordersSent",1),("dispatchAuthorized",True),
            ("safeActionBoundaryVerified",True),("runtimeActorIdentityVerified",True),
            ("nativeWeiDUCompileVerified",False),("watchedFilesChanged",True),
            ("temporaryOutputRemoved",False),("compiledBcsSha256",""),
            ("bafSha256","b"*64),("bafBytes",1)):
            with self.subTest(key=key):
                altered=dict(fake);altered[key]=bad
                self.assertFalse(v3.check_report_v3(altered,True),key)
    def test_v3_source_result_not_native(self):
        fake=dict(status="EXACT_V3_BAF_PIN_VERIFIED_NO_NATIVE_COMPILE",
            bafSha256=v3.V3_BAF_SHA256,bafBytes=762,installed=False,
            ordersSent=0,dispatchAuthorized=False,safeActionBoundaryVerified=False,
            runtimeActorIdentityVerified=False,nativeWeiDUCompileVerified=False)
        self.assertTrue(v3.check_report_v3(fake,False))
        self.assertFalse(v3.check_report_v3(fake,True))
    def test_synthetic_native_runner_fail_closed(self):
        class Proc:
            returncode=0
            stdout=json.dumps(dict(status="V3_NATIVE_BAF_COMPILED_TEMP_ONLY",
                    bafSha256=v3.V3_BAF_SHA256,bafBytes=762,
                    installed=False,ordersSent=0,dispatchAuthorized=False,
                    safeActionBoundaryVerified=False,runtimeActorIdentityVerified=False,
                    nativeWeiDUCompileVerified=True,watchedFilesChanged=False,
                    temporaryOutputRemoved=True,compiledBcsSha256="a"*64))
        def runner(args,**kwargs):
            self.assertIn("--native-readonly",args)
            self.assertIn("--backend",args)
            self.assertIn("--evidence",args)
            self.assertIn("--game",args)
            self.assertFalse(kwargs.get("check"))
            return Proc()
        out=v3.prepare_v3(Path("/nonexistent/FakeBG"),COMMIT,True,fetcher=fetch,runner=runner)
        self.assertEqual(out["status"],"V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL")
        self.assertFalse(out["gameplayFeatureInstalled"])
        self.assertFalse(out["gameplayMoveAuthorized"])
        self.assertEqual(out["ordersSent"],0)
        self.assertFalse(out["safeActionBoundaryVerified"])
    def test_invalid_commit_and_bad_runner_json(self):
        with self.assertRaises(v3.Hold):
            v3.prepare_v3(Path("/nonexistent/FakeBG"),"fake",False,fetcher=fetch)
        class Proc:
            returncode=0
            stdout="invalid json"
        x=v3.prepare_v3(Path("/nonexistent/FakeBG"),COMMIT,False,
                        fetcher=fetch,runner=lambda *a,**k:Proc())
        self.assertEqual(x["status"],"HOLD_V3_NATIVE_OR_SOURCE_PREFLIGHT")

if __name__=="__main__":
    unittest.main(verbosity=2)
