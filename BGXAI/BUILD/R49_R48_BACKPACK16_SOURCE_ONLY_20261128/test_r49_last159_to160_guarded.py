"""R49 guarded install after real original R48: exhaustive fake-EET only.

Reuses all existing R48/R47/R44 fake-game native fixtures. No user's EET.
"""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ORIG=REPO/"BGXAI/BUILD/R48_ONE_REAL_STAF01_EQUIP_AFTER_R47_20261128"
def import_path(label,path):
 spec=importlib.util.spec_from_file_location(label,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod
G=import_path("r49_guarded_last160",HERE/"BGXAI_R49_LAST159_TO160_GUARDED.py")
C=import_path("r49_backpack16_composer",HERE/"BGXAI_R49_REUSE_R48_BACKPACK16_SOURCE_ONLY.py")
OLD=import_path("r49_reuse_r48_test_fixture",ORIG/"test_r48_first_real_one_shot_item_source_only.py")
SHA=lambda b:hashlib.sha256(b).hexdigest()
LAST_ROW="~BGXR49/setup-BGXR49.tp2~ #0 #0"

class R49FakeEET(unittest.TestCase):
 def setUp(self):
  self.base=OLD.R48OneShotFakeGame()
  self.base.setUp()
  self.addCleanup(self.base.doCleanups)
  self.base.run_install()  # verified old R48 last 159, mock only
  self.game=self.base.game
  self.old=self.base.old
  self.r48=OLD.G
  self.r47=self.base.r47
  self.r44=self.base.r44
  self.r43=self.base.r43
  self.r42=self.base.r42
  self.r38=self.base.r38
  self.home=self.base.home
  self.r48bcs=self.old.safe(self.game,G.SOURCE_BCS).read_bytes()
  self.assertEqual(len(self.old.history(self.game)[0]),159)

 def put(self,rel,payload):
  p=self.old.safe(self.game,rel)
  p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(payload)

 def native_install(self,*args,**kwargs):
  self.put(G.SOURCE_BCS,self.r48bcs+b"\nBGXAI_R49_ONE_SHOT_BACKPACK16_MOCK")
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows+[LAST_ROW])+"\n").encode())

 def native_rollback(self,*args,**kwargs):
  self.put(G.SOURCE_BCS,self.r48bcs)
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())

 def args(self):
  return (self.r48,self.r47,self.r44,self.r43,self.r42,self.r38,self.old)

 def install(self):
  with patch.object(G,"native_weidu",side_effect=self.native_install):
   return G.install(*self.args(),C,self.game,G.INSTALL_TOKEN)

 def test_01_immutable_actual_old_R48_ancestry_and_composer(self):
  self.assertEqual(G.blob(G.R48_PATH.read_bytes()),G.R48_BLOB)
  self.assertEqual(G.blob(G.COMPOSE_PATH.read_bytes()),G.COMPOSE_BLOB)
  self.assertEqual(len(G.load_checked()),8)
  self.assertEqual(G.SCHEMA,"BGXAI_R49_BACKPACK16_ONE_STAF01_LAST160_GUARDED_V1")

 def test_02_r49_only_original_one_action_same_BGX48TRY(self):
  b=C.compose()
  self.assertEqual(b.count(b'Global("BGX48TRY","LOCALS",0)'),1)
  self.assertEqual(b.count(b'SetGlobal("BGX48TRY","LOCALS",1)'),1)
  self.assertEqual(b.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'),1)
  self.assertIn(b'OR(16)',b)
  self.assertEqual(b.count(b'CheckItemSlot('),16)
  self.assertEqual(G.TP2_TEXT.count("EXTEND_TOP"),1)
  self.assertIn("EXTEND_TOP ~BDDEFAI.BCS~",G.TP2_TEXT)

 def test_03_preflight_last159_source_ro_no_write(self):
  before=SHA(self.old.safe(self.game,G.SOURCE_BCS).read_bytes())
  out=G.preflight(*self.args(),C,self.game)
  self.assertEqual(out["status"],"R49_SOURCE_PREFLIGHT_R48_LAST159_PASS_NO_INSTALL")
  self.assertTrue(out["originalR48Last159Verified"])
  self.assertFalse(out["nativeCompilationOnUserEETVerified"])
  self.assertFalse(out["gameModified"])
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())
  self.assertEqual(before,SHA(self.old.safe(self.game,G.SOURCE_BCS).read_bytes()))

 def test_04_wrong_install_token_rejects_without_stage(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R49_EXACT_TYPED_INSTALL_REQUIRED"):
   G.install(*self.args(),C,self.game,"NO")
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_05_wrong_last_component_guard(self):
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())
  with self.assertRaises(ValueError):
   G.preflight(*self.args(),C,self.game)

 def test_06_tampered_old_R48_BCS_guard(self):
  self.put(G.SOURCE_BCS,b"malicious BCS tamper")
  with self.assertRaises(ValueError):
   G.preflight(*self.args(),C,self.game)

 def test_07_name_collision_blocks_before_backup_or_write(self):
  self.put(G.DIR+"/foreign",b"not ours")
  with self.assertRaisesRegex(ValueError,"HOLD_R49_NAMESPACE_ALREADY_PRESENT"):
   G.preflight(*self.args(),C,self.game)

 def test_08_mock_install_changes_BCS_last160_only(self):
  out=self.install()
  self.assertEqual(out["status"],"R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME")
  self.assertTrue(out["installed"])
  self.assertTrue(out["originalR48Last159Preserved"])
  self.assertEqual(out["sourceBackpackSlots"],list(range(18,34)))
  self.assertEqual(out["sourceBackpackSlot22Included"],True)
  self.assertEqual(out["ordersSentAtInstall"],0)
  self.assertFalse(out["actualXEquipPerformed"])
  self.assertEqual(len(self.old.history(self.game)[0]),160)
  self.assertEqual(SHA(self.old.safe(self.game,self.r48.PROOF).read_bytes()),out["originalR48ProofSHA256"])

 def test_09_backup_preserves_actual_r48_BCS_and_original_proof(self):
  out=self.install()
  backup=Path(out["externalBackup"])
  self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
  self.assertTrue(backup.name.startswith("PRE_BGXR49_"))
  self.old.verify_snapshot(backup,out["baselineSnapshot"])
  self.assertEqual((backup/G.SOURCE_BCS).read_bytes(),self.r48bcs)
  self.assertEqual((backup/self.r48.PROOF).read_bytes(),self.old.safe(self.game,self.r48.PROOF).read_bytes())

 def test_10_readonly_status_before_after(self):
  before=G.status(*self.args(),self.game)
  self.assertEqual(before["status"],"R49_NOT_INSTALLED_R48_LAST159")
  self.assertFalse(before["installed"])
  self.install()
  after=G.status(*self.args(),self.game)
  self.assertEqual(after["status"],"R49_BACKPACK16_LAST160_INSTALLED_AWAITING_GAME")
  self.assertFalse(after["actualXEquipPerformed"])

 def test_11_rollback_different_exact_token(self):
  self.install()
  with self.assertRaisesRegex(ValueError,"HOLD_R49_EXACT_TYPED_ROLLBACK_REQUIRED"):
   G.rollback(*self.args(),self.game,G.INSTALL_TOKEN)

 def test_12_mock_rollback_restores_last159_R48_byte_exact(self):
  self.install()
  with patch.object(G,"native_weidu",side_effect=self.native_rollback):
   result=G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)
  self.assertEqual(result["status"],"R49_ROLLBACK_RESTORED_ORIGINAL_R48_LAST159")
  self.assertEqual(self.old.safe(self.game,G.SOURCE_BCS).read_bytes(),self.r48bcs)
  self.assertEqual(len(self.old.history(self.game)[0]),159)
  self.assertTrue(G.status(*self.args(),self.game)["status"].startswith("R49_NOT_INSTALLED_"))

 def test_13_rollback_refuses_resource_drift(self):
  self.install()
  self.put(G.SOURCE_BCS,b"conflicting external modification")
  with self.assertRaisesRegex(ValueError,"HOLD_R49_LIVE_BCS_DRIFT"):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_14_rollback_refuses_corrupt_backup(self):
  out=self.install()
  (Path(out["externalBackup"])/"SHA256.json").write_text("{}")
  with self.assertRaisesRegex(ValueError,"HOLD_R49_BACKUP_SNAPSHOT_DRIFT"):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_15_rollback_refuses_R48_proof_drift(self):
  self.install()
  self.put(self.r48.PROOF,b"corrupt")
  with self.assertRaisesRegex(ValueError,"HOLD_R49_R48_PROOF_DRIFT"):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_16_one_updater_only_no_automatic_retry_or_rollback(self):
  source=Path(G.__file__).read_text(encoding="ascii")
  self.assertNotIn("BGXAI_UPDATE2.cmd",source)
  self.assertNotIn("ClearActions(",source)
  self.assertNotIn("SelectWeaponAbility(",source)
  self.assertNotIn("ForceAttack(",source)
  self.assertIn("never auto-retry",source)
  self.assertTrue(G.INSTALL_TOKEN!=G.ROLLBACK_TOKEN)

if __name__=="__main__":
 unittest.main()
