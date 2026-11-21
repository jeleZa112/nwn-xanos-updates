#!/usr/bin/env python3
"""Mock source-only WeiDU lifecycle; no game or real user files involved."""
from __future__ import annotations
import hashlib
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import BGXRANGED_V5_GUARDED_INSTALL as I
import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V

def fake_bcs(parts):
    return b"SC\n"+b"".join(b"CR\nCO\n"+str(x).encode()+b"\nCR\n" for x in parts)+b"SC\n"

class GuardedV5(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home=pathlib.Path(self.temp.name)
        self.root=self.home/"game"
        (self.root/"override").mkdir(parents=True)
        self.old=fake_bcs(["A4","B10","C4"]+[f"P{i:04}" for i in range(3,1162)])
        self.new=fake_bcs(["A6","B10","C6"]+[f"P{i:04}" for i in range(3,1162)])
        assert len(V.bcs_parts(self.old))==1162
        assert len(V.bcs_parts(self.new))==1162
        self.sha=lambda x:hashlib.sha256(x).hexdigest()
        self.active=False
        for rel in I.REQUIRED:
            p=self.root/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b"SAFEMOCK:"+rel.encode())
        (self.root/I.TARGET).write_bytes(self.old)
        (self.root/I.V5.WTASIGHT).write_bytes(b"MOCK_WTASIGHT")
        (self.root/"setup-enhanced-powergaming-scripts.exe").write_bytes(b"MZMOCK_EXE")
        self.original_hashes={rel:self.sha((self.root/rel).read_bytes())
                               for rel in I.REQUIRED}
        self.mocks=[
            patch.object(I,"ROOT",self.root),
            patch.object(V,"GAME",self.root),
            patch.object(V,"EXACT_BCS_SHA",self.sha(self.old)),
            patch.object(V,"EXACT_WTASIGHT_SHA",self.sha(b"MOCK_WTASIGHT")),
            patch.object(I,"EXACT_NEW_SHA",self.sha(self.new)),
            patch.object(I,"IMMUTABLE",{}),
            patch.object(I.E,"common",return_value=None),
            patch.object(I.E,"guard",return_value=None),
            patch.object(I.E,"last",side_effect=lambda _:
                r"~BGXRANGED5\SETUP-BGXRANGED5.TP2~ #0 #0" if self.active
                else r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0"),
            patch.object(I.E,"status",return_value={"status":"BGXFENEMY_INSTALLED_VERIFIED"}),
            patch.object(I,"processes",return_value=None),
            patch.object(I,"build",side_effect=self._build),
            patch.dict(I.os.environ,{"USERPROFILE":str(self.home)})
        ]
        for p in self.mocks:
            p.start()
            self.addCleanup(p.stop)

    def _build(self,root):
        self.assertEqual(root,self.root)
        return self.new,{"wei_log_sha256":I.digest(root/"WeiDU.log"),
                        "candidate_bcs_sha256":self.sha(self.new)}

    def _weidu(self,_root,remove=False):
        self.assertEqual(_root,self.root)
        self.active=not remove
        (self.root/I.TARGET).write_bytes(self.old if remove else self.new)
        (self.root/"WeiDU.log").write_bytes(b"MOCK_WEIDU_UPDATED")

    def test_preflight_is_readonly(self):
        before={rel:self.sha((self.root/rel).read_bytes()) for rel in I.REQUIRED}
        p=I.preflight(self.root)
        self.assertEqual(p["status"],"BGXRANGED5_NATIVE_PREFLIGHT_PASS")
        self.assertEqual(p["changed_blocks"],[1,3])
        self.assertEqual(p["preserved_blocks"],1160)
        self.assertFalse(p["game_modified"])
        self.assertEqual(before,{rel:self.sha((self.root/rel).read_bytes()) for rel in I.REQUIRED})

    def test_native_installer_and_last_only_rollback(self):
        with patch.object(I,"run_weidu",side_effect=self._weidu):
            installed=I.install(self.root)
            self.assertEqual(installed["status"],"BGXRANGED5_INSTALLED_VERIFIED")
            self.assertTrue(installed["game_modified"])
            self.assertEqual(installed["changed_blocks"],[1,3])
            self.assertEqual(installed["preserved_blocks"],1160)
            self.assertEqual(self.sha((self.root/I.TARGET).read_bytes()),self.sha(self.new))
            self.assertEqual(self.sha((self.root/I.V5.WTASIGHT).read_bytes()),
                             self.sha(b"MOCK_WTASIGHT"))
            for item in I.REQUIRED:
                if item not in (I.TARGET,"WeiDU.log"):
                    self.assertEqual(self.sha((self.root/item).read_bytes()),
                                     self.original_hashes[item],item)
            proof=I.status(self.root)
            self.assertEqual(proof["status"],"BGXRANGED5_INSTALLED_VERIFIED")
            outcome=I.rollback(self.root)
            self.assertEqual(outcome["status"],"BGXRANGED5_ROLLBACK_VERIFIED_BGXFENEMY_RESTORED")
            self.assertEqual((self.root/I.TARGET).read_bytes(),self.old)

    def test_rollback_stops_when_not_last(self):
        with self.assertRaisesRegex(ValueError,"V5_NOT_LAST_WEIDU"):
            I.rollback(self.root)

    def test_install_blocks_on_old_sha_drift_without_mutation(self):
        (self.root/I.TARGET).write_bytes(b"BAD_BASE")
        with patch.object(I,"run_weidu",side_effect=self._weidu):
            with self.assertRaisesRegex(ValueError,"V5_PREVIOUS_BCS_SHA_MISMATCH"):
                I.install(self.root)
        self.assertEqual((self.root/I.TARGET).read_bytes(),b"BAD_BASE")
        self.assertFalse((self.root/I.PACKAGE).exists())

    def test_backup_hash_and_forged_proof_rejected(self):
        with patch.object(I,"run_weidu",side_effect=self._weidu):
            installed=I.install(self.root)
            backup=pathlib.Path(installed["backup"])
            self.assertTrue(backup.is_dir())
            (backup/I.TARGET).write_bytes(b"TAMPERED")
            with self.assertRaisesRegex(ValueError,"BACKUP_INVALID"):
                I.status(self.root)
            with self.assertRaisesRegex(ValueError,"BACKUP_INVALID"):
                I.rollback(self.root)

    def test_missing_required_file_fails_safe(self):
        (self.root/"chitin.key").unlink()
        with self.assertRaisesRegex((FileNotFoundError, ValueError),
                                    "chitin.key|BACKUP_SOURCE_MISSING"):
            I.snapshot(self.root)

    def test_expected_consent_strings_and_wei_du_copy_only(self):
        self.assertEqual(I.TOKEN_INSTALL,"INSTALL_BGXRANGED5_ANTICIPATORY_PILOT")
        self.assertEqual(I.TOKEN_ROLLBACK,"ROLLBACK_BGXRANGED5_ANTICIPATORY_PILOT")
        self.assertIn("COPY ~BGXRANGED5/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~",
                      I.TP2_CONTENT)
        self.assertEqual(I.TP2_CONTENT.count("COPY "),1)
        self.assertTrue(I.LAST.match(r"~BGXRANGED5\SETUP-BGXRANGED5.TP2~ #0 #0"))
        self.assertFalse(I.LAST.match(r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0"))

    def test_no_queue_clearing_or_inventory_loss_in_installer(self):
        text=pathlib.Path(I.__file__).read_text("utf-8")
        for forbidden in ("ClearActions(","ClearAllActions(","FillSlot(",
                          "ForceAttack(","DropInventory(","XEquipItem("):
            self.assertNotIn(forbidden,text)

if __name__=="__main__":
    unittest.main(verbosity=2)
