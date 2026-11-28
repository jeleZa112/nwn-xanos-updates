"""R48 one-shot real STAF01 action source and fake-EET guarded lifecycle tests."""
from __future__ import annotations
import hashlib,importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R47_DIR=REPO/"BGXAI/BUILD/R47_GUARDED_BDDEFAI_EXEC_WITNESS_SOURCEONLY_20261128"
def mod(name,p):
    x=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(x);x.loader.exec_module(m);return m
C=mod("r48_one_staf01_composer",HERE/"BGXAI_R48_REUSE_R39_ONE_SHOT_BAF_SOURCE_ONLY.py")
G=mod("r48_last159_guard",HERE/"BGXAI_R48_LAST158_TO159_ONE_ITEM_GUARDED.py")
OLD=mod("r48_unchanged_r47_fake_eet",R47_DIR/"test_r47_guarded_last157_to158_source_only.py")
SHA=lambda b:hashlib.sha256(b).hexdigest()
LAST_ROW="~BGXR48/setup-BGXR48.tp2~ #0 #0"

class R48OneShotFakeGame(unittest.TestCase):
 def setUp(self):
  self.base=OLD.R47FakeEET()
  self.base.setUp()
  self.addCleanup(self.base.doCleanups)
  self.base.install()
  self.old=self.base.old
  self.game=self.base.game
  self.home=self.base.home
  self.r47=OLD.G
  self.r44=self.base.r44
  self.r43=self.base.r43
  self.r42=self.base.r42
  self.r38=self.base.r38
  self.r48_baf=C.compose()
  self.r47bcs=self.old.safe(self.game,G.SOURCE_BCS).read_bytes()
  self.assertEqual(len(self.old.history(self.game)[0]),158)

 def put(self,rel,raw):
  target=self.old.safe(self.game,rel)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(raw)

 def fake_weidu_install(self,*args,**kw):
  self.put(G.SOURCE_BCS,self.r47bcs+b"\nR48_STAF01_ONE_XEQUIP_MOCK")
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows+[LAST_ROW])+"\n").encode())

 def fake_weidu_rollback(self,*args,**kw):
  self.put(G.SOURCE_BCS,self.r47bcs)
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())

 def run_install(self):
  with patch.object(G,"native_weidu",side_effect=self.fake_weidu_install):
   return G.install(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,C,
                    self.game,G.INSTALL_TOKEN)

 def test_01_existing_user_native_R39_source_exact_pins(self):
  self.assertEqual(C.blob(C.OLD.read_bytes()),C.OLD_BLOB)
  self.assertEqual(C.sha(C.OLD.read_bytes()),C.OLD_SHA)
  self.assertEqual(C.OLD.read_bytes().count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'),1)

 def test_02_new_source_one_actual_equip_and_one_flag(self):
  self.assertEqual(self.r48_baf.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'),1)
  self.assertEqual(self.r48_baf.count(b'SetGlobal("BGX48TRY","LOCALS",1)'),1)
  self.assertEqual(self.r48_baf.count(b'Global("BGX48TRY","LOCALS",0)'),1)
  self.assertEqual(self.r48_baf.count(b"RESPONSE #100"),1)

 def test_03_no_unverified_R39_global_arm_dependency(self):
  self.assertNotIn(b"BGXW3",self.r48_baf)
  self.assertNotIn(b"EEex_LuaTrigger(",self.r48_baf)
  self.assertNotIn(b"EEex_Action_AddSpriteStartedActionListener(",self.r48_baf)

 def test_04_reuses_all_original_idle_and_exact_STAF01_guards(self):
  for token in C.PRESERVED_TRIGGERS:
   self.assertEqual(self.r48_baf.count(token),1,token)
  self.assertIn(b"ActionListEmpty()",self.r48_baf)
  self.assertIn(b"CombatCounter(0)",self.r48_baf)
  self.assertIn(b'CheckItemSlot(Myself,"STAF01",SLOT_MISC5)',self.r48_baf)

 def test_05_install_is_separate_explicit_user_consent(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R48_EXACT_TYPED_REAL_EQUIP_INSTALL_REQUIRED"):
   G.install(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,C,self.game,"")
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_06_preflight_auto_inside_installer_no_user_extra_report(self):
  status=G.before_change(self.r47,self.r44,self.r43,self.r42,self.r38,
                         self.old,C,self.game)
  self.assertEqual(status["status"],"R48_LAST158_SOURCE_EXACT_ONE_ITEM_READY_NOT_INSTALLED")
  self.assertEqual(status["sourceBcsSHA256"],SHA(self.r47bcs))
  self.assertFalse(status["gameModified"])
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_07_original_R47_BCS_modified_after_user_session_HOLD(self):
  self.put(G.SOURCE_BCS,b"tamper")
  with self.assertRaises(ValueError):
   G.before_change(self.r47,self.r44,self.r43,self.r42,self.r38,
                   self.old,C,self.game)

 def test_08_wrong_final_158_refuses(self):
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())
  with self.assertRaises(ValueError):
   G.before_change(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_09_existing_R48_install_namespace_COLLISION_HOLD(self):
  self.put(G.DIR+"/unrelated",b"existing")
  with self.assertRaisesRegex(ValueError,"HOLD_R48_STAGING_OR_OWNER_ALREADY_PRESENT"):
   G.before_change(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_10_mock_install_last159_changes_only_BCS_and_WeiDU(self):
  r=self.run_install()
  self.assertEqual(r["status"],"R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME")
  self.assertTrue(r["installed"]);self.assertTrue(r["gameModified"])
  self.assertEqual(r["ordersSentAtInstall"],0)
  self.assertFalse(r["actualXEquipPerformed"])
  self.assertEqual(len(self.old.history(self.game)[0]),159)
  self.assertEqual(SHA(self.old.safe(self.game,self.r47.SOURCE_LUA).read_bytes()),self.r47.EXPECTED_LUA_SHA)

 def test_11_external_R47_preimage_backup_real_SHA(self):
  r=self.run_install()
  backup=Path(r["externalBackup"])
  self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
  self.assertEqual((backup/G.SOURCE_BCS).read_bytes(),self.r47bcs)
  self.old.verify_snapshot(backup,r["baselineSnapshot"])

 def test_12_mock_status_before_after(self):
  self.assertEqual(G.status(self.r47,self.r44,self.r43,self.r42,self.r38,
                            self.old,self.game)["status"],
                   "R48_NOT_INSTALLED_R47_LAST158")
  self.run_install()
  self.assertEqual(G.status(self.r47,self.r44,self.r43,self.r42,self.r38,
                            self.old,self.game)["status"],
                   "R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT")

 def test_13_wrong_rollback_token_has_no_side_effects(self):
  self.run_install()
  with self.assertRaisesRegex(ValueError,"HOLD_R48_EXACT_TYPED_ROLLBACK_REQUIRED"):
   G.rollback(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,self.game,"")

 def test_14_mock_rollback_restores_byte_exact_R47_BCS_LAST158(self):
  self.run_install()
  with patch.object(G,"native_weidu",side_effect=self.fake_weidu_rollback):
   r=G.rollback(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,
                self.game,G.ROLLBACK_TOKEN)
  self.assertEqual(r["status"],"R48_ROLLBACK_RESTORED_R47_LAST158")
  self.assertEqual(len(self.old.history(self.game)[0]),158)
  self.assertEqual(self.old.safe(self.game,G.SOURCE_BCS).read_bytes(),self.r47bcs)

 def test_15_rollback_refuses_modified_BCS(self):
  self.run_install()
  self.put(G.SOURCE_BCS,b"modified externally")
  with self.assertRaisesRegex(ValueError,"HOLD_R48_LIVE_BCS_CHANGED_AFTER_INSTALL"):
   G.rollback(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,
              self.game,G.ROLLBACK_TOKEN)

 def test_16_rollback_refuses_corrupt_external_backup(self):
  r=self.run_install()
  (Path(r["externalBackup"])/"SHA256.json").write_text("{}")
  with self.assertRaisesRegex(ValueError,"HOLD_R48_EXTERNAL_BACKUP_MANIFEST_DRIFT"):
   G.rollback(self.r47,self.r44,self.r43,self.r42,self.r38,self.old,
              self.game,G.ROLLBACK_TOKEN)

 def test_17_old_game_and_onefile_updater_not_altered_by_source_generation(self):
  self.assertNotIn("BGXAI_UPDATE2.cmd",G.__doc__)
  self.assertEqual(C.compose(),self.r48_baf)
  self.assertNotIn(b"SetGlobalTimer(",self.r48_baf)
  self.assertNotIn(b"AttackOneRound(",self.r48_baf)

 def test_18_real_game_action_not_falsely_reported_by_mock_install(self):
  r=self.run_install()
  self.assertFalse(r["actualXEquipPerformed"])
  self.assertEqual(r["sourceItem"],"STAF01")
  self.assertEqual(r["sourceBackpackSlot"],20)
  self.assertEqual(r["targetWeaponSlot"],35)

if __name__=="__main__":
 unittest.main()
