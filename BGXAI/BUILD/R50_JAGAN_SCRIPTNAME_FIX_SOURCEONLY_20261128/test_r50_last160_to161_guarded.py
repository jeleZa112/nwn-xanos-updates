"""R50 #160->#161 guarded fake-EET-only tests; original R49 installed mock."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ORIG=REPO/"BGXAI/BUILD/R49_R48_BACKPACK16_SOURCE_ONLY_20261128"
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out)
 return out
G=mod("r50_last161_guard",HERE/"BGXAI_R50_LAST160_TO161_GUARDED.py")
C=mod("r50_source_composer",HERE/"BGXAI_R50_REUSE_R49_IDENTITY_DWARF_SOURCE_ONLY.py")
OLD=mod("r50_reuse_original_R49_fake_EET",ORIG/"test_r49_last159_to160_guarded.py")
SHA=lambda raw: hashlib.sha256(raw).hexdigest()
LAST_ROW="~BGXR50/setup-BGXR50.tp2~ #0 #0"

class R50FakeEET(unittest.TestCase):
 def setUp(self):
  self.base=OLD.R49FakeEET()
  self.base.setUp()
  self.addCleanup(self.base.doCleanups)
  self.base.install()
  self.game=self.base.game
  self.old=self.base.old
  self.r49=OLD.G
  self.r48=self.base.r48
  self.r47=self.base.r47
  self.r44=self.base.r44
  self.r43=self.base.r43
  self.r42=self.base.r42
  self.r38=self.base.r38
  self.home=self.base.home
  self.r49bcs=self.old.safe(self.game,G.SOURCE_BCS).read_bytes()
  self.assertEqual(len(self.old.history(self.game)[0]),160)

 def args(self):
  return (self.r49,self.r48,self.r47,self.r44,
          self.r43,self.r42,self.r38,self.old)

 def put(self,rel,b):
  file=self.old.safe(self.game,rel)
  file.parent.mkdir(parents=True,exist_ok=True)
  file.write_bytes(b)

 def mock_native_install(self,*args,**kwargs):
  self.put(G.SOURCE_BCS,self.r49bcs+b"\nR50_R49_JAGAN_DWARF_REPLACE_NAME_MOCK")
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows+[LAST_ROW])+"\n").encode())

 def mock_native_rollback(self,*args,**kwargs):
  self.put(G.SOURCE_BCS,self.r49bcs)
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())

 def install(self):
  with patch.object(G,"native_weidu",side_effect=self.mock_native_install):
   return G.install(*self.args(),C,self.game,G.INSTALL_TOKEN)

 def test_01_original_chain_exact_frozen_hashes(self):
  self.assertEqual(G.gitblob(G.R49_PATH.read_bytes()),G.R49_GIT_BLOB)
  self.assertEqual(G.gitblob(G.COMPOSE_PATH.read_bytes()),G.COMPOSE_GIT_BLOB)
  self.assertEqual(len(G.load_checked()),9)

 def test_02_old_confirmed_false_Name_replaced_by_race_guard(self):
  baf=C.compose()
  self.assertNotIn(b'Name("*GCLERIC",Myself)',baf)
  self.assertIn(b'Race(Myself,DWARF)',baf)
  self.assertEqual(baf.count(b'InPartySlot(Myself,1)'),1)
  self.assertEqual(baf.count(b'Class(Myself,CLERIC)'),1)

 def test_03_backpack16_and_once_no_new_attack_order(self):
  baf=C.compose()
  self.assertEqual(baf.count(b'CheckItemSlot('),16)
  self.assertEqual(baf.count(b'XEquipItem('),1)
  self.assertEqual(baf.count(b'SetGlobal('),1)
  self.assertEqual(baf.count(b'Global("BGX48TRY","LOCALS",0)'),1)
  self.assertIn(b'ActionListEmpty()',baf)
  self.assertIn(b'CombatCounter(0)',baf)

 def test_04_preflight_last160_readonly_hash_unchanged(self):
  before=SHA(self.old.safe(self.game,G.SOURCE_BCS).read_bytes())
  out=G.preflight(*self.args(),C,self.game)
  self.assertEqual(out["status"],"R50_R49_LAST160_SOURCE_PREFLIGHT_PASS_NO_INSTALL")
  self.assertTrue(out["r49Last160Verified"])
  self.assertFalse(out["nativeCompiledOnUserGame"])
  self.assertFalse(out["gameModified"])
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())
  self.assertEqual(SHA(self.old.safe(self.game,G.SOURCE_BCS).read_bytes()),before)

 def test_05_install_wrong_token_has_no_action(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R50_EXACT_TYPED_INSTALL_TOKEN_REQUIRED"):
   G.install(*self.args(),C,self.game,"WRONG")
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_06_wrong_original_last160_stop(self):
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())
  with self.assertRaises(ValueError):
   G.preflight(*self.args(),C,self.game)

 def test_07_old_R49_BCS_tampering_stop(self):
  self.put(G.SOURCE_BCS,b"tampered")
  with self.assertRaises(ValueError):
   G.preflight(*self.args(),C,self.game)

 def test_08_old_R49_PROOF_tampering_stop(self):
  self.put(self.r49.PROOF,b"tampered")
  with self.assertRaises(ValueError):
   G.preflight(*self.args(),C,self.game)

 def test_09_namespace_collision_stop(self):
  self.put(G.DIR+"/unrelated",b"external")
  with self.assertRaisesRegex(ValueError,"HOLD_R50_NAMESPACE_ALREADY_PRESENT"):
   G.preflight(*self.args(),C,self.game)

 def test_10_mock_native_installs_exact_last161_source_only_not_game(self):
  out=self.install()
  self.assertEqual(out["status"],"R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME")
  self.assertTrue(out["installed"])
  self.assertTrue(out["r49Last160Preserved"])
  self.assertTrue(out["userApproved"])
  self.assertEqual(out["onceFlag"],"BGX48TRY")
  self.assertFalse(out["actualXEquipPerformed"])
  self.assertEqual(len(self.old.history(self.game)[0]),161)
  self.assertEqual(out["ordersSentAtInstall"],0)

 def test_11_external_backup_original_R49_preimage_proof_SHA(self):
  out=self.install()
  backup=Path(out["externalBackup"])
  self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
  self.assertTrue(backup.name.startswith("PRE_BGXR50_"))
  self.old.verify_snapshot(backup,out["baselineSnapshot"])
  self.assertEqual((backup/G.SOURCE_BCS).read_bytes(),self.r49bcs)
  self.assertEqual((backup/self.r49.PROOF).read_bytes(),
                   self.old.safe(self.game,self.r49.PROOF).read_bytes())

 def test_12_readonly_status_before_after_install(self):
  before=G.status(*self.args(),self.game)
  self.assertEqual(before["status"],"R50_NOT_INSTALLED_R49_LAST160")
  self.install()
  after=G.status(*self.args(),self.game)
  self.assertEqual(after["status"],"R50_LAST161_INSTALLED_AWAITING_GAME")
  self.assertTrue(after["installed"])
  self.assertFalse(after["actualXEquipPerformed"])

 def test_13_wrong_rollback_token_fails_closed(self):
  self.install()
  with self.assertRaisesRegex(ValueError,"HOLD_R50_EXACT_TYPED_ROLLBACK_TOKEN_REQUIRED"):
   G.rollback(*self.args(),self.game,G.INSTALL_TOKEN)

 def test_14_rollback_restores_old_R49_last160_BYTE_exact(self):
  self.install()
  with patch.object(G,"native_weidu",side_effect=self.mock_native_rollback):
   out=G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)
  self.assertEqual(out["status"],"R50_ROLLBACK_RESTORED_ORIGINAL_R49_LAST160")
  self.assertFalse(out["installed"])
  self.assertEqual(self.old.safe(self.game,G.SOURCE_BCS).read_bytes(),self.r49bcs)
  self.assertEqual(len(self.old.history(self.game)[0]),160)
  self.assertEqual(G.status(*self.args(),self.game)["status"],
                   "R50_NOT_INSTALLED_R49_LAST160")

 def test_15_rollback_refuses_live_BCS_drift(self):
  self.install()
  self.put(G.SOURCE_BCS,b"unrelated changes")
  with self.assertRaisesRegex(ValueError,"HOLD_R50_INSTALLED_BCS_SHA_DRIFT"):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_16_rollback_refuses_corrupt_external_backup(self):
  out=self.install()
  (Path(out["externalBackup"])/"SHA256.json").write_text("{}")
  with self.assertRaisesRegex(ValueError,"HOLD_R50_BACKUP_MANIFEST_DRIFT"):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_17_rollback_refuses_old_R49_proof_drift(self):
  self.install()
  self.put(self.r49.PROOF,b"invalid")
  with self.assertRaises(ValueError):
   G.rollback(*self.args(),self.game,G.ROLLBACK_TOKEN)

 def test_18_no_second_updater_or_action_listener(self):
  s=Path(G.__file__).read_text("ascii")
  for forbidden in ("BGXAI_UPDATE2.cmd","ActionOverride(",
                    "ClearActions(","ForceAttack(","SelectWeaponAbility("):
   self.assertNotIn(forbidden,s)
  self.assertNotEqual(G.INSTALL_TOKEN,G.ROLLBACK_TOKEN)

if __name__=="__main__":
 unittest.main()
