"""BGXAI R38: source-only adversarial tests. Never call the game or run WeiDU."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
FOLDER=ROOT/"BGXAI/BUILD/R38_R37_IDENTITY_UPGRADE_PREFLIGHT_SOURCEONLY_20261127"
SRC=FOLDER/"BGXAI_R38_R37_PREUPGRADE_OFFLINE_GATE.py"
FIXTURE=FOLDER/"R37_USER_STATUS_SANITIZED_20261127.json"
spec=importlib.util.spec_from_file_location("bgxai_r38gate",SRC)
gate=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)

def status():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

class GateTests(unittest.TestCase):
    def test_01_snapshot_grounded_r37_source(self):
        actual=gate.status_evidence(status())
        self.assertTrue(actual["historicalR37StatusMatched"])
        self.assertFalse(actual["currentGameRechecked"])

    def test_02_four_inserts_exact_prior_bytes(self):
        s=gate.source_evidence()
        self.assertTrue(s["sourceByteIdenticalExceptFourMarkers"])
        self.assertTrue(s["identityReadOnlyCodeEmbedded"])
        self.assertEqual(s["newEngineActionCalls"],0)

    def test_03_candidate_one_listener(self):
        s=gate.source_evidence()
        self.assertTrue(s["oneStartedActionListener"])
        self.assertTrue(s["previousMessagesPreserved"])

    def test_04_offline_gate_never_authorizes(self):
        s=gate.run(status())
        self.assertEqual(s["status"],"R38_OFFLINE_SOURCE_GATE_PASS_NO_GAME_ACCESS")
        for key in ("installed","updaterIntegrated","weiduInstallerBuilt",
                    "runtimeIdentityVerified","safeActionBoundaryVerified",
                    "manualEpsOriginVerified","classKitItmUsabilityVerified",
                    "gameFilesModified","dispatchAuthorized","armAuthorized",
                    "liveUpgradePermitted"):
            self.assertIs(s[key],False,key)
        self.assertEqual(s["ordersSent"],0)

    def test_05_reject_old_r33_as_last(self):
        s=status();s["status"]="R33_PRESENT_LAST_BEFORE_R37"
        with self.assertRaises(gate.Hold):gate.status_evidence(s)

    def test_06_reject_wrong_component_count(self):
        for value in (152,154,True,153.0,None):
            s=status();s["weiduComponents"]=value
            with self.subTest(value=value),self.assertRaises(gate.Hold):
                gate.status_evidence(s)

    def test_07_reject_changed_weidu_last(self):
        for value in ("~BGXR38\\SETUP-BGXR38.TP2~ #0 #0",status()["weiduLastComponent"]+" ",""):
            s=status();s["weiduLastComponent"]=value
            with self.subTest(value=value),self.assertRaises(gate.Hold):
                gate.status_evidence(s)

    def test_08_reject_weidu_log_snapshot_sha_drift(self):
        s=status();s["weiDULogSha256"]="0"*64
        with self.assertRaises(gate.Hold):gate.status_evidence(s)

    def test_09_reject_live_module_sha_drift(self):
        s=status();s["liveModuleSha256"]="0"*64
        with self.assertRaises(gate.Hold):gate.status_evidence(s)

    def test_10_reject_source_flags_drift(self):
        for field in ("r33SourceExact","r37SourceExact","gameModified",
                      "dispatchAuthorized","weaponSwitchAuthorized"):
            s=status();s[field]=not s[field]
            with self.subTest(field=field),self.assertRaises(gate.Hold):
                gate.status_evidence(s)

    def test_11_reject_1_order(self):
        for value in (1,True,"0",None,-1):
            s=status();s["ordersSent"]=value
            with self.subTest(value=value),self.assertRaises(gate.Hold):
                gate.status_evidence(s)

    def test_12_reject_missing_status_field(self):
        for field in ("status","weiDULogSha256","liveModuleSha256","r37SourceExact"):
            s=status();del s[field]
            with self.subTest(field=field),self.assertRaises(gate.Hold):
                gate.status_evidence(s)

    def test_13_source_pin_rejects_modified_file(self):
        # Source-only in-memory mutation; no file changes.
        raw=gate.verified_file(gate.R38)
        with patch.object(gate.R38,"read_bytes",return_value=raw+b"x"):
            with self.assertRaises(gate.Hold):
                gate.verified_file(gate.R38)

    def test_14_extra_listener_guard(self):
        original=[gate.verified_file(p) for p in (gate.BASE,gate.R38,gate.IDENTITY)]
        malicious=original[1]+b"\nEEex_Action_AddSpriteStartedActionListener(foo)\n"
        def load(p):
            return {gate.BASE:original[0],gate.R38:malicious,gate.IDENTITY:original[2]}[p]
        with patch.object(gate,"verified_file",side_effect=load):
            with self.assertRaises(gate.Hold):gate.source_evidence()

    def test_15_absent_id_core_guard(self):
        original=[gate.verified_file(p) for p in (gate.BASE,gate.R38,gate.IDENTITY)]
        malicious=original[1].replace(original[2],b"-- FAKED ID CORE --")
        def load(p):
            return {gate.BASE:original[0],gate.R38:malicious,gate.IDENTITY:original[2]}[p]
        with patch.object(gate,"verified_file",side_effect=load):
            with self.assertRaises(gate.Hold):gate.source_evidence()

    def test_16_cli_fixture_safe_pass(self):
        p=subprocess.run([sys.executable,str(SRC),"--r37-status",str(FIXTURE)],
            capture_output=True,text=True,check=False,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr+"\n"+p.stdout[:400])
        s=json.loads(p.stdout)
        self.assertEqual(s["status"],"R38_OFFLINE_SOURCE_GATE_PASS_NO_GAME_ACCESS")
        self.assertFalse(s["liveUpgradePermitted"])

    def test_17_cli_invalid_json_safe_hold(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"status.json";p.write_text("invalid json",encoding="utf-8")
            proc=subprocess.run([sys.executable,str(SRC),"--r37-status",str(p)],
                capture_output=True,text=True,check=False,timeout=20)
            self.assertEqual(proc.returncode,3)
            result=json.loads(proc.stdout)
            self.assertEqual(result["status"],"R38_OFFLINE_HOLD")
            self.assertFalse(result["dispatchAuthorized"])

    def test_18_cli_missing_snapshot_safe_hold(self):
        proc=subprocess.run([sys.executable,str(SRC),
            "--r37-status",str(FOLDER/"NO_SUCH_STATUS.json")],
            capture_output=True,text=True,check=False,timeout=20)
        self.assertEqual(proc.returncode,3)
        self.assertEqual(json.loads(proc.stdout)["ordersSent"],0)

    def test_19_source_only_not_installer(self):
        data=SRC.read_text(encoding="utf-8")
        self.assertNotIn("import subprocess",data)
        self.assertNotIn("COPY ~",data)
        self.assertNotIn("XEquipItem(",data)
        self.assertNotIn("SetGlobal(",data)
        self.assertNotIn("subprocess.run(",data)

if __name__=="__main__":
    unittest.main(verbosity=2)
