"""Regression: self-update --selftest MUST NOT depend on user's V120 cache."""
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import subprocess
import sys
import unittest

UPDATER=Path(__file__).resolve().parents[1]/"onefile"/"BG_EET_RU_UPDATE.cmd"

class CacheIsolation(unittest.TestCase):
    def test_prior_user_pinned_cache_does_not_change_selftest(self):
        with TemporaryDirectory(prefix="BG_EET_RU_V128_EXISTING_CACHE_") as tmp:
            home=Path(tmp)
            cache=home/"Documents"/"BG_EET_RU"/".BG_EET_RU_AUTOFIX_CACHE"
            cache.mkdir(parents=True)
            existing=cache/"V120_EVIDENCE_PINNED.zip"
            existing.write_bytes(b"EXISTING_UNTRUSTED_CACHE_TEST_SENTINEL")
            env=os.environ.copy()
            env["HOME"]=str(home)
            env["USERPROFILE"]=str(home)
            p=subprocess.run([sys.executable,"-x",str(UPDATER),"--selftest"],
                             env=env,capture_output=True,text=True,
                             errors="replace",timeout=75)
            self.assertEqual(p.returncode,0,p.stdout[-1500:]+p.stderr[-1500:])
            self.assertIn("SELFTEST: PASS",p.stdout)
            self.assertEqual(existing.read_bytes(),b"EXISTING_UNTRUSTED_CACHE_TEST_SENTINEL")

    def test_isolated_temporary_workdir_is_restored_even_on_snapshot_error(self):
        code=UPDATER.read_text(encoding="utf8").split("\n",1)[1]
        ns={"__name__":"v128_ci_fixture","__file__":str(UPDATER)}
        exec(compile(code,str(UPDATER),"exec"),ns)
        with TemporaryDirectory(prefix="BG_EET_RU_V128_PREV_") as d:
            orig=Path(d)/"current_user_cache"
            orig.mkdir()
            ns["WORKDIR"]=orig
            prior=ns["v121_snapshot"]
            try:
                def error(*args):
                    self.assertNotEqual(ns["WORKDIR"],orig)
                    raise RuntimeError("SYNTHETIC_SNAPSHOT_ABORT")
                ns["v121_snapshot"]=error
                with self.assertRaisesRegex(RuntimeError,"SYNTHETIC_SNAPSHOT_ABORT"):
                    ns["v121_selftest"]()
                self.assertEqual(ns["WORKDIR"],orig)
            finally:
                ns["v121_snapshot"]=prior
            self.assertTrue(ns["v121_selftest"]())
            self.assertEqual(ns["WORKDIR"],orig)
            self.assertEqual(list(orig.iterdir()),[])

if __name__=="__main__":
    unittest.main()
