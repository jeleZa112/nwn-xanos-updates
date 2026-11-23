#!/usr/bin/env python3
"""BGXRANGED7 installer simulated lifecycle: temporary mock game ONLY."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

import BGXRANGED_V7_GUARDED_INSTALL as I
import BGXRANGED_V6_DPLAYER_NATIVE_READONLY as N
import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V5

def bcs(tags):
    return b"SC\n"+b"".join(b"CR\nCO\n"+str(t).encode()+b"\nCR\n" for t in tags)+b"SC\n"

class GuardedV7(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)
        self.root=self.home/"game"
        (self.root/"override").mkdir(parents=True)
        self.old=bcs(("OLD_ATTACK1","OLD_ATTACK2"))
        self.candidate=bcs(("SAFE_ATTACK1","SAFE_ATTACK2"))
        self.live_v6=False
        for name in I.REQUIRED:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b"MOCK:"+name.encode())
        (self.root/I.TARGET).write_bytes(self.old)
        (self.root/N.BDDEFAI).write_bytes(b"GOOD_BDDEFAI")
        (self.root/N.WTASIGHT).write_bytes(b"GOOD_WTASIGHT")
        (self.root/"setup-enhanced-powergaming-scripts.exe").write_bytes(b"MZMOCK_WEIDU")
        self.patches=[
          patch.object(I,"GAME",self.root),
          patch.object(N,"EXPECTED_DPLAYER_SHA",N.sha(self.old)),
          patch.object(N,"EXPECTED_BDDEFAI_SHA",N.sha(b"GOOD_BDDEFAI")),
          patch.object(N,"EXPECTED_WTASIGHT_SHA",N.sha(b"GOOD_WTASIGHT")),
          patch.object(I,"EXPECTED_NEW_SHA",N.sha(self.candidate)),
          patch.object(I,"OTHER",{}),
          patch.object(I.E,"common",return_value=None),
          patch.object(I.E,"guard",return_value=None),
          patch.object(I,"r27_status",return_value={"status":"R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST"}),
          patch.object(I.E,"last",side_effect=lambda _:
              r"~BGXRANGED7\SETUP-BGXRANGED7.TP2~ #0 #0" if self.live_v6
              else r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0"),
          patch.object(I,"running",return_value=None),
          patch.object(I,"compile_candidate",side_effect=self.fake_compile),
          patch.dict(I.os.environ,{"USERPROFILE":str(self.home)}),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.before_hashes={
          x:N.sha((self.root/x).read_bytes()) for x in I.REQUIRED
        }

    def fake_compile(self,root):
        self.assertEqual(root,self.root)
        return self.candidate,{
         "last_weidu":I.weidu_last(root),
         "wei_log_sha256":I.sha(root/"WeiDU.log"),
         "candidate_dplayer_sha256":N.sha(self.candidate),
         "changed_blocks":[1,2]}

    def fake_weidu(self,root,uninstall=False):
        self.assertEqual(root,self.root)
        self.live_v6=not uninstall
        (self.root/I.TARGET).write_bytes(self.old if uninstall else self.candidate)
        (self.root/"WeiDU.log").write_bytes(b"WEIDU_LAST_CHANGED")

    def test_onefile_menu_cancel_has_no_side_effect(self):
        with patch.object(I.sys,"argv",["v6.py","--game",str(self.root)]),\
             patch("builtins.input",return_value="0"),\
             patch.object(I,"install",side_effect=AssertionError("installed")):
            self.assertEqual(I.main(),0)
        self.assertFalse((self.root/I.PACKAGE).exists())

    def test_user_must_type_exact_authorization_for_install(self):
        with patch.object(I.sys,"argv",["v6.py","--game",str(self.root)]),\
             patch("builtins.input",side_effect=["2","yes"]),\
             patch.object(I,"install",side_effect=AssertionError("installed")):
            self.assertEqual(I.main(),1)
        self.assertFalse((self.root/I.PACKAGE).exists())

    def test_preflight_remains_readonly(self):
        report=I.preflight(self.root)
        self.assertEqual(report["status"],"BGXRANGED7_NATIVE_GUARDED_PREFLIGHT_PASS")
        self.assertEqual(report["changed_blocks"],[1,2])
        self.assertFalse(report["game_modified"])
        self.assertFalse((self.root/I.PACKAGE).exists())
        self.assertEqual(self.before_hashes,
            {x:N.sha((self.root/x).read_bytes()) for x in I.REQUIRED})

    def test_install_verify_and_last_only_rollback(self):
        with patch.object(I,"use_weidu",side_effect=self.fake_weidu):
            installed=I.install(self.root)
            self.assertEqual(installed["status"],"BGXRANGED7_INSTALLED_VERIFIED")
            self.assertTrue(installed["game_modified"])
            self.assertEqual(installed["changed_blocks"],[1,2])
            self.assertEqual(installed["backup"],str(self.backup_path(installed)))
            self.assertEqual((self.root/I.TARGET).read_bytes(),self.candidate)
            self.assertEqual((self.root/N.BDDEFAI).read_bytes(),b"GOOD_BDDEFAI")
            self.assertEqual((self.root/N.WTASIGHT).read_bytes(),b"GOOD_WTASIGHT")
            for f in I.REQUIRED:
                if f not in (I.TARGET,"WeiDU.log"):
                    self.assertEqual(N.sha((self.root/f).read_bytes()),self.before_hashes[f])
            self.assertEqual(I.status(self.root)["status"],"BGXRANGED7_INSTALLED_VERIFIED")
            rollback=I.rollback(self.root)
            self.assertEqual(rollback["status"],
                             "BGXRANGED7_ROLLBACK_VERIFIED_R27_RESTORED")
            self.assertTrue(rollback["game_modified"])
            self.assertEqual((self.root/I.TARGET).read_bytes(),self.old)

    @staticmethod
    def backup_path(installed):
        return Path(installed["backup"])

    def test_install_source_mismatch_must_stop_before_staging(self):
        (self.root/I.TARGET).write_bytes(b"DRIFT")
        with patch.object(I,"use_weidu",side_effect=AssertionError("weidu")):
            with self.assertRaisesRegex(ValueError,"DPLAYER_BASELINE_SHA_DRIFT"):
                I.install(self.root)
        self.assertFalse((self.root/I.PACKAGE).exists())

    def test_modified_BDDEFAI_or_WTASIGHT_fails_closed(self):
        for name in (N.BDDEFAI,N.WTASIGHT):
            current=(self.root/name).read_bytes()
            (self.root/name).write_bytes(b"TAMPER")
            with self.assertRaises(ValueError):I.before(self.root)
            (self.root/name).write_bytes(current)

    def test_tampered_external_backup_stops_rollback(self):
        with patch.object(I,"use_weidu",side_effect=self.fake_weidu):
            installed=I.install(self.root)
            backup=Path(installed["backup"])
            (backup/I.TARGET).write_bytes(b"CORRUPTED")
            with self.assertRaisesRegex(ValueError,"BACKUP_CORRUPTED"):
                I.status(self.root)
            with self.assertRaisesRegex(ValueError,"BACKUP_CORRUPTED"):
                I.rollback(self.root)
            self.assertEqual((self.root/I.TARGET).read_bytes(),self.candidate)

    def test_rollback_without_v6_last_is_forbidden(self):
        with self.assertRaisesRegex(ValueError,"V7_NOT_LAST_WEIDU"):
            I.rollback(self.root)

    def test_staged_WeiDU_edits_only_DPLAYER(self):
        self.assertEqual(I.TP2_CONTENT.count("COPY "),1)
        self.assertIn("~override/DPLAYER.BCS~",I.TP2_CONTENT)
        self.assertNotIn("BDDEFAI.BCS",I.TP2_CONTENT)
        self.assertNotIn("WTASIGHT.BCS",I.TP2_CONTENT)
        self.assertEqual(I.INSTALL_TOKEN,"INSTALL_BGXRANGED7_DPLAYER_GUARD_PILOT")
        self.assertEqual(I.ROLLBACK_TOKEN,"ROLLBACK_BGXRANGED7_DPLAYER_GUARD_PILOT")

    def test_no_queue_wipe_inventory_move_or_force_attack(self):
        import inspect
        src=inspect.getsource(I)
        for bad in ("ClearActions(","ClearAllActions(","FillSlot(","ForceAttack(",
                    "DropInventory(","XEquipItem("):
            self.assertNotIn(bad,src)

if __name__=="__main__":
    unittest.main(verbosity=2)
