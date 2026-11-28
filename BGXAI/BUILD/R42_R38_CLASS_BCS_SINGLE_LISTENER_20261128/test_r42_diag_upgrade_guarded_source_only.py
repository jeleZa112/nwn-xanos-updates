"""Source-only R43 successor checks. Fake game only: NO LIVE GAME / NO WeiDU."""
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
def module(name, path):
    s=importlib.util.spec_from_file_location(name,path)
    x=importlib.util.module_from_spec(s)
    s.loader.exec_module(x)
    return x
G=module("r43_guard_test",HERE/"BGXAI_R42_DIAG_UPGRADE_GUARDED_SOURCE_ONLY.py")
R42=module("r43_r42_old_test",HERE/"BGXAI_R42_GUARDED_FROM_R38.py")
D=module("r43_diag_old_test",HERE/"BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py")
B=module("r43_builder_old_test",HERE/"BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py")
old_fixtures=module("r43_r42_fixture",HERE/"test_r42_guarded_r38_last.py")
OLD_R42=B.compose(B.verified(B.R38,B.R38_BYTES,B.R38_BLOB),
                  B.verified(B.R39,B.R39_BYTES,B.R39_BLOB))
NEW=D.compose()
def sha(b):return hashlib.sha256(b).hexdigest()
ROWS=old_fixtures.R38_ROWS+[old_fixtures.R42_ROW]
R43_ROW="~BGXR43/setup-BGXR43.tp2~ #0 #0"

class R43Test(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home=Path(self.temp.name)
        self.game=home/"game";self.game.mkdir()
        self.home=home/"home";self.home.mkdir()
        self.old=old_fixtures.FakeOld(self.game)
        self.r38=old_fixtures.FakeR38()
        self._file("chitin.key",b"fixture")
        self._file("override/BDDEFAI.BCS",b"known")
        self._file("BGXR37/PROOF.json",b'{"installed":true}')
        self._file("BGXR38/PROOF.json",b'{"installed":true,"source":"R38"}')
        self._file("override/M_BGXR27.lua",OLD_R42)
        self._file("WeiDU.log",("\n".join(ROWS)+"\n").encode())
        self._file("setup-enhanced-powergaming-scripts.exe",b"fake-native")
        baseline={
            "chitin.key":sha(b"fixture"),
            "override/BDDEFAI.BCS":sha(b"known"),
            "BGXR37/PROOF.json":self.old.sha(self.old.safe(self.game,"BGXR37/PROOF.json")),
            "BGXR38/PROOF.json":self.old.sha(self.old.safe(self.game,"BGXR38/PROOF.json")),
            "WeiDU.log":sha(b"old-before-R42"),
            "override/M_BGXR27.lua":R42.R38_SHA,
        }
        proof={
            "schema":R42.SCHEMA, "status":"R42_READONLY_INSTALLED_AWAITING_LIVE_CLASS",
            "sourceSha256":R42.CANDIDATE_SHA,"typedInstallApproved":True,
            "installationPerformed":True,"dispatchAuthorized":False,
            "armAuthorized":False,"ordersSent":0,"baselineSnapshot":baseline,
        }
        self._file("BGXR42/PROOF.json",json.dumps(proof).encode())
        patches=[
            patch.object(R42,"WEIDU_SHA",sha(b"fake-native")),
            patch.object(R42,"check_processes",return_value=None),
            patch.dict(os.environ,{"USERPROFILE":str(self.home)}),
        ]
        for c in patches:c.start();self.addCleanup(c.stop)

    def _file(self,path,contents):
        p=self.game/path;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(contents)

    def _install_mock_weidu(self,*args,**kwargs):
        self._file("override/M_BGXR27.lua",NEW)
        self._file("WeiDU.log",("\n".join(ROWS+[R43_ROW])+"\n").encode())

    def _uninstall_mock_weidu(self,*args,**kwargs):
        self._file("override/M_BGXR27.lua",OLD_R42)
        self._file("WeiDU.log",("\n".join(ROWS)+"\n").encode())

    def _do_install(self):
        with patch.object(G,"native_weidu",side_effect=self._install_mock_weidu):
            return G.install(R42,D,self.r38,self.old,self.game,G.INSTALL_TOKEN)

    def test_01_reused_exact_modules_source_git_blobs(self):
        self.assertEqual(G.blob(G.R42_SOURCE.read_bytes()),G.R42_BLOB)
        self.assertEqual(G.blob(G.DIAG_SOURCE.read_bytes()),G.DIAG_BLOB)

    def test_02_candidate_sha_bytes_and_no_new_listener(self):
        self.assertEqual(len(NEW),95965)
        self.assertEqual(sha(NEW),G.EXPECTED_SHA)
        self.assertEqual(NEW.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener"),1)
        self.assertEqual(NEW.count(b"[BGXBCS]"),1)

    def test_03_preflight_positive_fake_game_preserves_bytes(self):
        before=self.old.sha(self.old.safe(self.game,"WeiDU.log"))
        result=G.before_change(R42,D,self.r38,self.old,self.game)
        self.assertEqual(result["status"],"R43_PREFLIGHT_LAST155_PASS_NO_INSTALL")
        self.assertFalse(result["gameModified"])
        self.assertEqual(self.old.sha(self.old.safe(self.game,"WeiDU.log")),before)
        self.assertEqual(self.old.sha(self.old.safe(self.game,G.OVERRIDE)),R42.CANDIDATE_SHA)

    def test_04_reject_wrong_last_component(self):
        self._file("WeiDU.log",("\n".join(ROWS[:-1])+"\n").encode())
        with self.assertRaisesRegex(ValueError,"HOLD_R42_NOT_WEIDU_LAST_155"):
            G.before_change(R42,D,self.r38,self.old,self.game)

    def test_05_reject_original_lua_drift(self):
        self._file("override/M_BGXR27.lua",b"tamper")
        with self.assertRaisesRegex(ValueError,"HOLD_R42_ACTIVE_LUA_SHA_DRIFT"):
            G.before_change(R42,D,self.r38,self.old,self.game)

    def test_06_reject_unrelated_file_change(self):
        self._file("chitin.key",b"changed")
        with self.assertRaisesRegex(ValueError,"HOLD_UNRELATED_SOURCE_CHANGED"):
            G.before_change(R42,D,self.r38,self.old,self.game)

    def test_07_typed_install_required_even_with_fake_eet(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R43_EXACT_TYPED_INSTALL_REQUIRED"):
            G.install(R42,D,self.r38,self.old,self.game,"")
        self.assertFalse(self.old.safe(self.game,G.DIR).exists())

    def test_08_native_weidu_binary_pin_required(self):
        self._file("setup-enhanced-powergaming-scripts.exe",b"tampered")
        with self.assertRaisesRegex(ValueError,"HOLD_R43_NATIVE_WEIDU_DRIFT"):
            G.before_change(R42,D,self.r38,self.old,self.game)

    def test_09_installs_only_156_last_with_mocked_weidu(self):
        out=self._do_install()
        self.assertEqual(out["status"],"R43_READONLY_REASON_INSTALLED_AWAITING_LIVE")
        self.assertEqual(len(self.old.history(self.game)[0]),156)
        self.assertEqual(self.old.sha(self.old.safe(self.game,G.OVERRIDE)),G.EXPECTED_SHA)
        self.assertEqual(G.status(R42,self.r38,self.old,self.game)["status"],
                         "R43_PRESENT_LAST_READONLY_REASON")
        self.assertEqual(out["ordersSent"],0)

    def test_10_backup_external_and_matches_baseline(self):
        out=self._do_install()
        backup=Path(out["externalBackup"])
        self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
        self.assertEqual(self.old.sha(backup/G.OVERRIDE),R42.CANDIDATE_SHA)
        self.old.verify_snapshot(backup,out["baselineSnapshot"])

    def test_11_rollback_requires_typed_token(self):
        self._do_install()
        with self.assertRaisesRegex(ValueError,"HOLD_R43_EXACT_TYPED_ROLLBACK_REQUIRED"):
            G.rollback(R42,self.r38,self.old,self.game,"")

    def test_12_mock_rollback_restores_exact_R42_155_last(self):
        self._do_install()
        with patch.object(G,"native_weidu",side_effect=self._uninstall_mock_weidu):
            out=G.rollback(R42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)
        self.assertEqual(out["status"],"R43_ROLLBACK_RESTORED_R42_LAST")
        self.assertEqual(self.old.sha(self.old.safe(self.game,G.OVERRIDE)),R42.CANDIDATE_SHA)
        self.assertEqual(len(self.old.history(self.game)[0]),155)

    def test_13_abort_rollback_on_modified_unrelated_file(self):
        self._do_install()
        self._file("override/BDDEFAI.BCS",b"drift")
        with self.assertRaisesRegex(ValueError,"HOLD_R43_UNRELATED_FILE_DRIFT"):
            G.rollback(R42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_14_status_original_installed_not_successor(self):
        out=G.status(R42,self.r38,self.old,self.game)
        self.assertEqual(out["status"],"R43_NOT_INSTALLED_R42_PRESENT_LAST")
        self.assertFalse(out["installed"])

    def test_15_source_not_a_second_updater(self):
        source=G.__file__ and Path(G.__file__).read_text()
        self.assertIn("HOLD_NOT_CONNECTED_TO_EXISTING_ONEFILE",source)
        self.assertNotIn("os.system(",source)
        self.assertNotIn("BGXW3ARM",source.split("class Hold")[1])
        self.assertIn("--onefile-review-gate",source)

    def test_16_reject_unapproved_cli_capture_before_any_game_start(self):
        with patch.object(G,"load_checked",return_value=(R42,D,self.r38,self.old)), \
             patch("sys.argv",["r43","--game",str(self.game),"--mode","capture"]):
            self.assertEqual(G.main(),3)

    def test_17_extra_reason_fields_preserved_but_hold(self):
        row={"schema":R42.BCS_SCHEMA,"type":"CLASS_BCS_ONCE","seq":1,
             "partyIndex":1,"classScriptResref":None,"scrlev":4,
             "status":"HOLD_CLASS_BCS_NOT_READABLE","sameR38Listener":True,
             "gameModified":False,"actualBcsExecutionVerified":False,
             "manualEpsActionOriginVerified":False,"armAuthorized":False,
             "dispatchAuthorized":False,"ordersSent":0,"localsWritten":0,
             "r39ProbeStatus":"HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE",
             "r39PhysicalReason":"NONE","r39ClassSlotState":"NOT_READ"}
        f=Path(self.temp.name)/"test.log"
        f.write_text("INFO: LUA: [BGXBCS] "+json.dumps(row)+"\n")
        out=G.parse_diag_console(R42,f,0)
        self.assertEqual(out["r39ProbeStatus"],"HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE")
        self.assertEqual(out["status"],"R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE")
        self.assertFalse(out["classScriptResrefAtLiveJaganVerified"])

    def test_18_reject_unallowlisted_row_reason(self):
        row={"r39ProbeStatus":"INJECT","r39PhysicalReason":"NONE",
             "r39ClassSlotState":"NOT_READ","ordersSent":0,
             "armAuthorized":False,"dispatchAuthorized":False}
        f=Path(self.temp.name)/"test.log"
        f.write_text("INFO: LUA: [BGXBCS] "+json.dumps(row)+"\n")
        self.assertEqual(G.parse_diag_console(R42,f,0)["status"],
                         "R43_CAPTURE_HOLD_DIAG_FIELDS")


if __name__=="__main__":
    unittest.main()
