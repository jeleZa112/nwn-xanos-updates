#!/usr/bin/env python3
"""R37 guarded-last WeiDU mock lifecycle: isolated temporary game ONLY."""
from __future__ import annotations
from pathlib import Path
from unittest import mock
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
MOD=HERE/"R37_GUARDED_SOURCE_ONLY.py"
CAND=HERE/"M_BGXR27_R37_SOURCE_ONLY.lua"
SPEC=importlib.util.spec_from_file_location("r37_guard",MOD)
G=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)

def hash_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def history(n=152):
    records=[f"~OTHER/SETUP-OTHER.TP2~ #0 #0 // {i}" for i in range(n-4)]
    records += [f"~BGXR{x}/SETUP-BGXR{x}.TP2~ #0 #0 // install" for x in ("27","29","31","33")]
    return ("\n".join(records)+"\n").encode("utf-8")

class R37Guarded(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"game"
        self.root.mkdir()
        self.home=Path(self.tmp.name)/"home"
        self.home.mkdir()
        self.r33_bytes=b"R33_MOCK_NOT_REAL_INSTALLED_MODULE"
        self.native=b"FAKE_WEIDU_BINARY_NOT_EXECUTABLE"
        self.resources={name:(b"fixture-"+name.encode()) for name in G.BASELINE_SHA}
        self.patches=[
            mock.patch.object(G,"R33_SHA",hash_bytes(self.r33_bytes)),
            mock.patch.object(G,"NATIVE_SHA",hash_bytes(self.native)),
            mock.patch.object(G,"BASELINE_SHA",
                {k:hash_bytes(v) for k,v in self.resources.items()}),
            mock.patch.object(G,"protected_root",
                side_effect=lambda root,live=True: None),
            mock.patch.object(G,"verify_processes",return_value=None),
            mock.patch.dict(os.environ,{"USERPROFILE":str(self.home)})
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        for name,blob in self.resources.items():
            self.write(name,blob)
        self.write("WeiDU.log",history())
        self.write(G.OVERRIDE,self.r33_bytes)
        self.write("setup-enhanced-powergaming-scripts.exe",self.native)
        self.write("BGXR33/setup-BGXR33.exe",self.native)
        self.write(G.R31_PROOF,b"R31 PREVIOUS PROOF")
        self.write(G.R33_PROOF,json.dumps({
            "schema":G.R33_SCHEMA,
            "status":"R33_PASSIVE_INSTALLED_AWAITING_RUNTIME",
            "sourceSha256":G.R33_SHA,
            "typedInstallApproved":True,"installationPerformed":True,
            "dispatchAuthorized":False,"weaponSwitchAuthorized":False,
            "baselineSnapshot":{G.OVERRIDE:
                "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38",
                **G.BASELINE_SHA}
        }).encode())
    def write(self,name,contents):
        p=G.safe(self.root,name);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(contents)
        return p
    def fake_native(self,root,uninstall=False):
        assert root==self.root
        if uninstall:
            self.write("WeiDU.log",history())
            self.write(G.OVERRIDE,self.r33_bytes)
        else:
            self.write("WeiDU.log",history()+b"~BGXR37/SETUP-BGXR37.TP2~ #0 #0 // install\n")
            self.write(G.OVERRIDE,CAND.read_bytes())
    def test_source_exact_real_sha_and_one_listener(self):
        original=G.candidate_bytes(CAND)
        self.assertEqual(len(original),60835)
        self.assertEqual(hash_bytes(original),
            "5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6")
    def test_readonly_preflight_152_r33_last_no_write(self):
        before=self.write("WeiDU.log",history()).read_bytes()
        out=G.preflight(self.root,CAND,live=False)
        self.assertEqual(out["status"],"R37_PREFLIGHT_PASS_NO_INSTALL")
        self.assertEqual(out["weiduComponents"],152)
        self.assertEqual(self.write("WeiDU.log",history()).read_bytes(),before)
        self.assertFalse((self.root/G.R37_DIR).exists())
    def test_status_reports_r33_before_install(self):
        self.assertEqual(G.status(self.root)["status"],"R33_PRESENT_LAST_BEFORE_R37")
    def test_wrong_install_token_does_not_stage(self):
        with self.assertRaisesRegex(G.Hold,"EXACT_TYPED_INSTALL"):
            G.install(self.root,CAND,"")
        self.assertFalse((self.root/G.R37_DIR).exists())
    def test_wrong_candidate_size_denied(self):
        bad=self.write("not_candidate.lua",b"incorrect")
        with self.assertRaisesRegex(G.Hold,"R37_CANDIDATE_SIZE"):
            G.preflight(self.root,bad,live=False)
    def test_wrong_candidate_same_size_denied(self):
        data=bytearray(CAND.read_bytes());data[-22]^=3
        bad=self.write("wrong_candidate.lua",data)
        with self.assertRaisesRegex(G.Hold,"R37_CANDIDATE_SHA"):
            G.preflight(self.root,bad,live=False)
    def test_153_existing_last_denied_before_any_install(self):
        self.write("WeiDU.log",history()+b"~BGXR37/SETUP-BGXR37.TP2~ #0 #0\n")
        with self.assertRaisesRegex(G.Hold,"R33_MUST_BE_EXACT"):
            G.preflight(self.root,CAND,live=False)
    def test_staging_collision_denied(self):
        (self.root/G.R37_DIR).mkdir()
        with self.assertRaisesRegex(G.Hold,"R37_STAGING_COLLISION"):
            G.preflight(self.root,CAND,live=False)
    def test_r33_proof_wrong_source_denied(self):
        p=self.root/G.R33_PROOF
        proof=json.loads(p.read_text())
        proof["sourceSha256"]="untrusted"
        p.write_text(json.dumps(proof))
        with self.assertRaisesRegex(G.Hold,"R33_INSTALLED_PROOF"):
            G.preflight(self.root,CAND,live=False)
    def test_r33_live_override_changed_denied(self):
        self.write(G.OVERRIDE,b"DRIFTED_R33")
        with self.assertRaisesRegex(G.Hold,"R33_LIVE_MODULE_SHA"):
            G.preflight(self.root,CAND,live=False)
    def test_native_weidu_sha_drift_denied(self):
        self.write("BGXR33/setup-BGXR33.exe",b"bad")
        with self.assertRaisesRegex(G.Hold,"NATIVE_WEIDU_BINARY"):
            G.preflight(self.root,CAND,live=False)
    def test_baseline_bcs_changed_denied(self):
        self.write("override/DPLAYER.BCS",b"unexpected BCS change")
        with self.assertRaisesRegex(G.Hold,"PREEXISTING_RESOURCE_SHA"):
            G.preflight(self.root,CAND,live=False)
    def test_mocked_typed_install_and_rollback(self):
        original=G.snapshot(self.root)
        with mock.patch.object(G,"native_weidu",side_effect=self.fake_native):
            value=G.install(self.root,CAND,G.INSTALL_TOKEN)
            self.assertEqual(value["status"],"R37_PASSIVE_INSTALLED_AWAITING_RUNTIME")
            self.assertTrue(value["typedInstallApproved"])
            self.assertEqual(G.status(self.root)["status"],"R37_PRESENT_LAST_PASSIVE")
            self.assertEqual(G.installed_proof(self.root)["sourceSha256"],G.SOURCE_SHA)
            self.assertEqual((self.root/G.OVERRIDE).read_bytes(),CAND.read_bytes())
            self.assertEqual(G.safe(self.root,G.TP2).read_text(encoding="ascii"),G.TP2_TEXT)
            back=Path(value["externalBackup"])
            self.assertTrue(back.is_dir())
            G.verify_snapshot(back,original)
            with self.assertRaisesRegex(G.Hold,"EXACT_TYPED_ROLLBACK"):
                G.rollback(self.root,"")
            rolled=G.rollback(self.root,G.ROLLBACK_TOKEN)
            self.assertEqual(rolled["status"],"R37_ROLLBACK_RESTORED_R33")
            self.assertEqual(G.status(self.root)["status"],"R33_PRESENT_LAST_BEFORE_R37")
            self.assertEqual((self.root/G.OVERRIDE).read_bytes(),self.r33_bytes)
    def test_not_last_rollback_stopped_before_weidu(self):
        with mock.patch.object(G,"native_weidu",side_effect=self.fake_native) as f:
            G.install(self.root,CAND,G.INSTALL_TOKEN)
            self.write("WeiDU.log",history()+b"~BGXR37/SETUP-BGXR37.TP2~ #0 #0\n~OTHER/SETUP-OTHER.TP2~ #0 #0\n")
            before=f.call_count
            with self.assertRaisesRegex(G.Hold,"R37_NOT_WEIDU_LAST"):
                G.rollback(self.root,G.ROLLBACK_TOKEN)
            self.assertEqual(f.call_count,before)
    def test_backup_tamper_prevents_rollback(self):
        with mock.patch.object(G,"native_weidu",side_effect=self.fake_native) as f:
            result=G.install(self.root,CAND,G.INSTALL_TOKEN)
            back=Path(result["externalBackup"])
            (back/G.OVERRIDE).write_bytes(b"attacker payload")
            before=f.call_count
            with self.assertRaisesRegex(G.Hold,"WATCHED_RESOURCE_SHA"):
                G.rollback(self.root,G.ROLLBACK_TOKEN)
            self.assertEqual(f.call_count,before)
    def test_live_unrelated_change_prevents_rollback(self):
        with mock.patch.object(G,"native_weidu",side_effect=self.fake_native) as f:
            G.install(self.root,CAND,G.INSTALL_TOKEN)
            self.write("override/DPLAYER.BCS",b"unexpected later install")
            before=f.call_count
            with self.assertRaisesRegex(G.Hold,"R37_ROLLBACK_UNRELATED_RESOURCE"):
                G.rollback(self.root,G.ROLLBACK_TOKEN)
            self.assertEqual(f.call_count,before)
    def test_no_auto_recovery_or_second_updater(self):
        src=MOD.read_text(encoding="utf-8")
        self.assertIn("EXACT_TYPED_INSTALL_CONSENT_REQUIRED",src)
        self.assertIn("EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED",src)
        self.assertIn("R37_STOP_MANUAL_REVIEW",src)
        self.assertNotIn("BGXAI_UPDATE_2.cmd",src)
        self.assertNotIn("os.system(",src)
        self.assertNotIn("shutil.rmtree(",src)
        import ast
        calls=[node.func.id for node in ast.walk(ast.parse(src))
               if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
        self.assertNotIn("ClearActions",calls)
        self.assertNotIn("SelectWeaponAbility",calls)

if __name__=="__main__":
    unittest.main(verbosity=2)
