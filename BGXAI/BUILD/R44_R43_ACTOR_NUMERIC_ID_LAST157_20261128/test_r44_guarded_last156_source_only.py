"""R44 LAST157 fake-EET lifecycle regression; ZERO access to live user's game."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
LEGACY_DIR=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128"
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
G=module("r44_guard_157",HERE/"BGXAI_R44_GUARDED_LAST156_SOURCE_ONLY.py")
C=module("r44_composer_157",HERE/"BGXAI_R44_COMPOSE_FROM_R43_SOURCE_ONLY.py")
R43=module("r44_real_r43_guard",LEGACY_DIR/"BGXAI_R42_DIAG_UPGRADE_GUARDED_SOURCE_ONLY.py")
OLD=module("r44_fake_legacy_r43",LEGACY_DIR/"test_r42_diag_upgrade_guarded_source_only.py")
R42=OLD.R42
R38_ROW=OLD.ROWS
R43_ROW=OLD.R43_ROW
R44_ROW="~BGXR44/setup-BGXR44.tp2~ #0 #0"
NEW=C.compose()
SHA=lambda b:hashlib.sha256(b).hexdigest()

class R44FakeEET(unittest.TestCase):
    def setUp(self):
        self.legacy=OLD.R43Test()
        self.legacy.setUp()
        self.addCleanup(self.legacy.doCleanups)
        self.game=self.legacy.game
        self.old=self.legacy.old
        self.r38=self.legacy.r38
        self.home=self.legacy.home
        self.legacy._do_install()
        self.assertEqual(len(self.old.history(self.game)[0]),156)
        self.assertEqual(SHA(self.old.safe(self.game,G.OVERRIDE).read_bytes()),R43.EXPECTED_SHA)

    def put(self,rel,raw):
        target=self.old.safe(self.game,rel)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)

    def fake_install_weidu(self,*args,**kwargs):
        self.put(G.OVERRIDE,NEW)
        self.put("WeiDU.log",("\n".join(R38_ROW+[R43_ROW,R44_ROW])+"\n").encode())

    def fake_rollback_weidu(self,*args,**kwargs):
        self.put(G.OVERRIDE,OLD.NEW)
        self.put("WeiDU.log",("\n".join(R38_ROW+[R43_ROW])+"\n").encode())

    def do_install(self):
        with patch.object(G,"native_weidu",side_effect=self.fake_install_weidu):
            return G.install(R43,R42,self.r38,self.old,C,self.game,G.INSTALL_TOKEN)

    def test_01_imported_reusable_guard_and_composer_exact_blob(self):
        self.assertEqual(G.blob(G.R43_PATH.read_bytes()),G.R43_BLOB)
        self.assertEqual(G.blob(G.R44_COMPOSE_PATH.read_bytes()),G.COMPOSE_BLOB)

    def test_02_r44_single_pinned_candidate(self):
        self.assertEqual(len(NEW),96410)
        self.assertEqual(SHA(NEW),G.EXPECTED_SHA)
        self.assertEqual(NEW.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener"),1)

    def test_03_status_original_r43_last(self):
        r=G.status(R43,R42,self.r38,self.old,self.game)
        self.assertEqual(r["status"],"R44_NOT_INSTALLED_R43_PRESENT_LAST")
        self.assertFalse(r["installed"])

    def test_04_preflight_exact_original_r43_with_no_mutation(self):
        old_hash=SHA(self.old.safe(self.game,"WeiDU.log").read_bytes())
        res=G.before_change(R43,R42,self.r38,self.old,C,self.game)
        self.assertEqual(res["status"],"R44_PREFLIGHT_LAST156_PASS_NO_INSTALL")
        self.assertFalse(res["gameModified"])
        self.assertEqual(SHA(self.old.safe(self.game,"WeiDU.log").read_bytes()),old_hash)
        self.assertFalse(self.old.safe(self.game,G.DIR).exists())

    def test_05_wrong_last156_refuses_r44_install(self):
        self.put("WeiDU.log",("\n".join(R38_ROW)+"\n").encode())
        with self.assertRaisesRegex(ValueError,"HOLD_R43_NOT_WEIDU_LAST_156"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_06_bad_original_lua_refuses(self):
        self.put(G.OVERRIDE,b"bad")
        with self.assertRaisesRegex(ValueError,"HOLD_R43_LIVE_LUA_SHA_DRIFT"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_07_different_chitin_refuses(self):
        self.put("chitin.key",b"bad")
        with self.assertRaisesRegex(ValueError,"HOLD_UNRELATED_SOURCE_CHANGED"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_08_wrong_ancestor_r42_proof_refuses(self):
        self.put(R42.PROOF,b"tamper")
        with self.assertRaisesRegex(ValueError,"HOLD_UNRELATED_SOURCE_CHANGED"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_09_wrong_r43_proof_refuses(self):
        self.put(R43.PROOF,b'{"installed":false}')
        with self.assertRaisesRegex(ValueError,"HOLD_R43_PROOF_INVALID"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_10_no_typed_token_no_mutation(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R44_EXACT_TYPED_INSTALL_REQUIRED"):
            G.install(R43,R42,self.r38,self.old,C,self.game,"")
        self.assertFalse(self.old.safe(self.game,G.DIR).exists())

    def test_11_native_weidu_binary_pin(self):
        self.put("setup-enhanced-powergaming-scripts.exe",b"wrong")
        with self.assertRaisesRegex(ValueError,"HOLD_R44_NATIVE_WEIDU_DRIFT"):
            G.before_change(R43,R42,self.r38,self.old,C,self.game)

    def test_12_mock_install_r44_last157_exact_sha(self):
        out=self.do_install()
        self.assertEqual(out["status"],"R44_READONLY_NUMERIC_ACTOR_INSTALLED_AWAITING_LIVE")
        self.assertTrue(out["installed"])
        self.assertEqual(len(self.old.history(self.game)[0]),157)
        self.assertEqual(SHA(self.old.safe(self.game,G.OVERRIDE).read_bytes()),G.EXPECTED_SHA)
        self.assertEqual(G.status(R43,R42,self.r38,self.old,self.game)["status"],
                         "R44_PRESENT_LAST_READONLY")
        self.assertEqual(out["ordersSent"],0)

    def test_13_external_backup_restores_original_r43_sha(self):
        out=self.do_install()
        backup=Path(out["externalBackup"])
        self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
        self.assertEqual(SHA((backup/G.OVERRIDE).read_bytes()),R43.EXPECTED_SHA)
        self.old.verify_snapshot(backup,out["baselineSnapshot"])
        self.assertIn(R43.PROOF,out["baselineSnapshot"])
        self.assertIn(R42.PROOF,out["baselineSnapshot"])

    def test_14_rollback_requires_exact_typed(self):
        self.do_install()
        with self.assertRaisesRegex(ValueError,"HOLD_R44_EXACT_TYPED_ROLLBACK_REQUIRED"):
            G.rollback(R43,R42,self.r38,self.old,self.game,"")

    def test_15_mock_rollback_restores_r43_last156(self):
        self.do_install()
        with patch.object(G,"native_weidu",side_effect=self.fake_rollback_weidu):
            out=G.rollback(R43,R42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)
        self.assertEqual(out["status"],"R44_ROLLBACK_RESTORED_R43_LAST")
        self.assertEqual(len(self.old.history(self.game)[0]),156)
        self.assertEqual(SHA(self.old.safe(self.game,G.OVERRIDE).read_bytes()),R43.EXPECTED_SHA)

    def test_16_rollback_refuses_modified_unrelated_source(self):
        self.do_install()
        self.put("override/BDDEFAI.BCS",b"tamper")
        with self.assertRaisesRegex(ValueError,"HOLD_R44_UNRELATED_FILE_DRIFT"):
            G.rollback(R43,R42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_17_rollback_refuses_corrupt_external_manifest(self):
        out=self.do_install()
        backup=Path(out["externalBackup"])
        (backup/"SHA256.json").write_text("{}")
        with self.assertRaisesRegex(ValueError,"HOLD_R44_BACKUP_MANIFEST_MISMATCH"):
            G.rollback(R43,R42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_18_unconnected_capture_refused_without_game_start(self):
        with patch.object(G,"load_checked",return_value=(R43,R42,self.r38,self.old,C)), \
             patch("sys.argv",["r44","--game",str(self.game),"--mode","capture"]):
            self.assertEqual(G.main(),3)

    def test_19_source_only_not_second_cmd(self):
        src=Path(G.__file__).read_text()
        self.assertIn("HOLD_NOT_CONNECTED_TO_EXISTING_ONEFILE",src)
        self.assertIn("INSTALL_BGXAI_R44_READONLY_NUMERIC_ACTOR_AFTER_R43_LAST",src)
        self.assertNotIn("os.system(",src)
        self.assertNotIn("BGXAI_UPDATE2.cmd",src)
        self.assertNotIn("XEquipItem(",src)

if __name__=="__main__":
    unittest.main()
