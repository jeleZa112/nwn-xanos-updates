"""R33 guarded upgrade mock safety matrix; no installed game access or real WeiDU."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r33guard", HERE / "R33_GUARDED_SOURCE_ONLY.py")
g = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = g
SPEC.loader.exec_module(g)
CANDIDATE = HERE / "M_BGXR27_R33_SOURCE_ONLY.lua"
R31_SRC = HERE.parent / "R31_R27V3_PASSIVE_SOURCE_20261125" / "M_BGXR27_R31_SOURCE_ONLY.lua"

R27_LINE = "~BGXR27/SETUP-BGXR27.TP2~ #0 #0 // R27"
R29_LINE = "~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // R29"
R31_LINE = "~BGXR31/SETUP-BGXR31.TP2~ #0 #0 // R31"
R33_LINE = "~BGXR33/SETUP-BGXR33.TP2~ #0 #0 // R33"


def digest(v):
    return hashlib.sha256(v).hexdigest()


def fixture(root: Path):
    rows = [f"~MOCK{i:03}/SETUP-MOCK{i:03}.TP2~ #0 #0 // mocked" for i in range(148)]
    rows.extend((R27_LINE, R29_LINE, R31_LINE))
    files = {
        "WeiDU.log": ("\n".join(rows) + "\n").encode(),
        g.OVERRIDE: R31_SRC.read_bytes(),
        g.R31_PROOF: b"pending-proof",
        "BGXR31/setup-BGXR31.exe": b"MZ_mock_native",
        "setup-enhanced-powergaming-scripts.exe": b"MZ_mock_native",
        "chitin.key": b"mock_key",
        "EEex/copy/EEex_scripts/EEex_Action.lua": b"mock_eeex_action",
        "EEex/copy/EEex_scripts/EEex_Sprite.lua": b"mock_eeex_sprite",
        "enhanced-powergaming-scripts/lib/core_base.tph": b"mock_EPS",
        "override/BDDEFAI.BCS": b"R29_BCS",
        "override/DPLAYER.BCS": b"V6_BCS",
    }
    for name, data in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    base = {key: digest(files[key]) for key in g.BASELINE_SHA}
    p = {
        "schema": "BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1",
        "status": "R31_PASSIVE_INSTALLED_AWAITING_RUNTIME",
        "sourceSha256": g.R31_SHA,
        "installationPerformed": True,
        "typedInstallApproved": True,
        "dispatchAuthorized": False,
        "baselineSnapshot": {
            "WeiDU.log": g.WEIDU_PRE_R31_SHA,
            g.OVERRIDE: "e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735",
            **base,
        },
    }
    (root / g.R31_PROOF).write_text(json.dumps(p))
    return files, base


class GuardTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.temp = Path(td.name)
        self.root = self.temp / "game"
        self.root.mkdir()
        self.home = self.temp / "user"
        self.home.mkdir()
        self.original, self.pins = fixture(self.root)
        p1 = mock.patch.object(g, "BASELINE_SHA", self.pins)
        p2 = mock.patch.object(g, "NATIVE_SHA", digest(self.original["setup-enhanced-powergaming-scripts.exe"]))
        p3 = mock.patch.object(g, "protected_root", lambda root, live=True: None)
        p4 = mock.patch.object(g, "verify_processes", lambda: None)
        p5 = mock.patch.dict(os.environ, {"USERPROFILE": str(self.home)})
        for p in (p1,p2,p3,p4,p5):
            p.start()
            self.addCleanup(p.stop)

    def test_real_candidate_exact_hash_and_no_orders(self):
        self.assertEqual(len(CANDIDATE.read_bytes()), 49438)
        self.assertEqual(g.candidate_bytes(CANDIDATE), CANDIDATE.read_bytes())
        self.assertEqual(digest(CANDIDATE.read_bytes()), g.R33_SHA)
        self.assertEqual(digest(R31_SRC.read_bytes()), g.R31_SHA)

    def test_real_r31_151_preflight_is_read_only(self):
        before = {key: (self.root / key).read_bytes() for key in self.original}
        pre = g.preflight(self.root, CANDIDATE, False)
        self.assertEqual(pre["status"], "R33_PREFLIGHT_PASS_INSTALL_UNAUTHORIZED")
        self.assertEqual(pre["weiduComponents"], 151)
        self.assertEqual(pre["baselineSnapshot"][g.OVERRIDE],g.R31_SHA)
        self.assertEqual(before, {key: (self.root / key).read_bytes() for key in self.original})
        self.assertFalse(pre["dispatchAuthorized"])

    def test_deny_install_without_exact_typed_consent(self):
        with self.assertRaisesRegex(g.Hold, "EXACT_TYPED_INSTALL_CONSENT_REQUIRED"):
            g.install(self.root, CANDIDATE, "")
        self.assertFalse((self.root/g.R33_DIR).exists())
        with self.assertRaisesRegex(g.Hold, "EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED"):
            g.rollback(self.root, "WRONG")

    def test_preflight_requires_r31_exact_last_and_proof(self):
        with (self.root / "WeiDU.log").open("a") as f:
            f.write("~MOCKNEW/SETUP-MOCKNEW.TP2~ #0 #0 // later\n")
        with self.assertRaisesRegex(g.Hold,"R31_MUST_BE_WEIDU_LAST_151"):
            g.preflight(self.root,CANDIDATE,False)
        (self.root/"WeiDU.log").write_bytes(self.original["WeiDU.log"])
        p = self.root / g.R31_PROOF
        q = json.loads(p.read_text())
        q["typedInstallApproved"] = False
        p.write_text(json.dumps(q))
        with self.assertRaisesRegex(g.Hold,"R31_INSTALLED_PROOF_INCONSISTENT"):
            g.preflight(self.root,CANDIDATE,False)

    def test_preflight_detects_unrelated_game_drift(self):
        x=self.root/"override/DPLAYER.BCS"
        x.write_bytes(b"wrong")
        with self.assertRaisesRegex(g.Hold,"INSTALLED_RESOURCE_SHA_DRIFT"):
            g.preflight(self.root,CANDIDATE,False)

    def test_preflight_detects_bad_exe_or_existing_stage(self):
        (self.root/g.R33_DIR).mkdir()
        with self.assertRaisesRegex(g.Hold,"R33_STAGING_COLLISION"):
            g.preflight(self.root,CANDIDATE,False)
        (self.root/g.R33_DIR).rmdir()
        (self.root/"BGXR31/setup-BGXR31.exe").write_bytes(b"incorrect")
        with self.assertRaisesRegex(g.Hold,"R31_NATIVE_BINARY_PIN_MISMATCH"):
            g.preflight(self.root,CANDIDATE,False)

    def test_candidate_tampering_holds(self):
        p = self.temp/"t.lua"
        p.write_bytes(CANDIDATE.read_bytes()[:-1]+b"X")
        with self.assertRaisesRegex(g.Hold,"R33_CANDIDATE_SHA_DRIFT"):
            g.preflight(self.root,p,False)

    def install_mock(self):
        native=[]
        def fake_native(root,uninstall=False):
            native.append("uninstall" if uninstall else "install")
            if uninstall:
                proof=json.loads((root/g.R33_PROOF).read_text())
                previous=Path(proof["externalBackup"])
                shutil.copy2(previous/g.OVERRIDE,root/g.OVERRIDE)
                shutil.copy2(previous/"WeiDU.log",root/"WeiDU.log")
            else:
                shutil.copy2(root/g.STAGED,root/g.OVERRIDE)
                with (root/"WeiDU.log").open("a") as stream:
                    stream.write(R33_LINE+"\n")
        patch=mock.patch.object(g,"native_weidu",fake_native)
        patch.start()
        self.addCleanup(patch.stop)
        return native

    def test_fake_install_and_last_only_rollback_no_unrelated_changes(self):
        calls=self.install_mock()
        result=g.install(self.root,CANDIDATE,g.INSTALL_TOKEN)
        self.assertEqual(result["status"],"R33_PASSIVE_INSTALLED_AWAITING_RUNTIME")
        self.assertEqual(calls,["install"])
        self.assertEqual(g.sha(self.root/g.OVERRIDE),g.R33_SHA)
        self.assertEqual(g.history(self.root)[0][-1],R33_LINE)
        self.assertEqual(g.status(self.root)["status"],"R33_PRESENT_LAST")
        self.assertEqual(result["baselineSnapshot"][g.OVERRIDE],g.R31_SHA)
        for key in self.pins:
            self.assertEqual((self.root/key).read_bytes(),self.original[key])
        with (self.root/"WeiDU.log").open("a") as stream:
            stream.write("~LATER/SETUP-LATER.TP2~ #0 #0 // later\n")
        with self.assertRaisesRegex(g.Hold,"R33_NOT_WEIDU_LAST"):
            g.rollback(self.root,g.ROLLBACK_TOKEN)
        lines=(self.root/"WeiDU.log").read_text().splitlines()
        (self.root/"WeiDU.log").write_text("\n".join(lines[:-1])+"\n",newline="\n")
        returned=g.rollback(self.root,g.ROLLBACK_TOKEN)
        self.assertEqual(returned["status"],"R33_ROLLBACK_R31_RESTORED")
        self.assertEqual(calls,["install","uninstall"])
        self.assertEqual(g.sha(self.root/g.OVERRIDE),g.R31_SHA)
        self.assertEqual(g.history(self.root)[0][-1],R31_LINE)

    def test_mock_capture_one_raw_prof_sample_and_no_live_approvals(self):
        self.install_mock()
        g.install(self.root,CANDIDATE,g.INSTALL_TOKEN)
        (self.root/"InfinityLoader.exe").write_bytes(b"MZ"+b"\0"*2048)
        class Child:
            def wait(self): return 0
        def popen(args,**kwargs):
            kwargs["stdout"].write(
                b'[BGXR27] {"type":"SESSION","observerCandidate":"R33_R27V3_PASSIVE_PROF_RO"}\n'
                b'[BGXR27] {"type":"R27_SINGLE_CALLBACK","queueSnapshotStable":true,'
                b'"actionRaw":3,"queuedActionsRaw":0,"proficiencyStat89to134Raw":[1,2,3]}\n'
            )
            return Child()
        with mock.patch.object(g.subprocess,"Popen",popen):
            result=g.capture(self.root)
        self.assertEqual(result["status"],"R33_RUNTIME_RAW_PROF_LOG_READY_FOR_REVIEW")
        self.assertEqual(result["rawProficiencySamples"],1)
        self.assertEqual(result["sessionMarkers"],1)
        self.assertFalse(result["classRowVerified"])
        self.assertFalse(result["alternateEffectiveAPRVerified"])

    def test_backup_tamper_or_unrelated_change_denies_rollback(self):
        self.install_mock()
        result=g.install(self.root,CANDIDATE,g.INSTALL_TOKEN)
        (Path(result["externalBackup"])/g.OVERRIDE).write_bytes(b"tampered")
        with self.assertRaisesRegex(g.Hold,"WATCHED_BASELINE_CHANGED"):
            g.rollback(self.root,g.ROLLBACK_TOKEN)
        self.assertEqual(g.sha(self.root/g.OVERRIDE),g.R33_SHA)

    def test_no_background_or_auto_rollback(self):
        source=(HERE/"R33_GUARDED_SOURCE_ONLY.py").read_text()
        self.assertNotIn("threading",source)
        self.assertNotIn("ClearActions(root",source)
        self.assertNotIn("SelectWeaponAbility(root",source)
        self.assertNotIn("while True",source)


if __name__=="__main__":
    unittest.main()
