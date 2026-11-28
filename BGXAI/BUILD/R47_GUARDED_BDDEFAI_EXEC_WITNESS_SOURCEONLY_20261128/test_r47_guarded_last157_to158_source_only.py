"""R47 source-only exact guarded WeiDU 157→158 + rollback on fake EET."""
from __future__ import annotations
import hashlib,importlib.util,json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R44_DIR=REPO/"BGXAI/BUILD/R44_R43_ACTOR_NUMERIC_ID_LAST157_20261128"
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=mod("r47_guarded_source",HERE/"BGXAI_R47_WITNESS_LAST157_TO158_GUARDED_SOURCE_ONLY.py")
C=mod("r47_corrected_compose",HERE/"BGXAI_R47_CORRECT_R46_EEEX_SCRIPT_PORT_SOURCE_ONLY.py")
OLD=mod("r47_reuse_r44_fake_eet",R44_DIR/"test_r44_guarded_last156_source_only.py")
SHA=lambda s:hashlib.sha256(s).hexdigest()
LAST_ROW="~BGXR47/setup-BGXR47.tp2~ #0 #0"

class R47FakeEET(unittest.TestCase):
 def setUp(self):
  self.base=OLD.R44FakeEET()
  self.base.setUp()
  self.addCleanup(self.base.doCleanups)
  self.game=self.base.game
  self.old=self.base.old
  self.r38=self.base.r38
  self.home=self.base.home
  self.base.do_install()
  self.assertEqual(len(self.old.history(self.game)[0]),157)
  self.parts=C.source_only()
  self.r44=OLD.G
  self.r43=OLD.R43
  self.r42=OLD.R42
  self.preimage=b"known"
  self.patchbc=patch.object(G,"BASELINE_BCS_SHA",SHA(self.preimage))
  self.patchbc.start()
  self.addCleanup(self.patchbc.stop)

 def put(self,rel,data):
  target=self.old.safe(self.game,rel)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(data)

 def native_install(self,*args,**kw):
  self.put(G.SOURCE_BCS,b"SC\nBGXAI_R46_BDDEFAI_Witness\nCOMPILED_PASSIVE")
  self.put(G.SOURCE_LUA,self.parts["LUA"])
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows+[LAST_ROW])+"\n").encode())

 def native_rollback(self,*args,**kw):
  self.put(G.SOURCE_BCS,self.preimage)
  self.old.safe(self.game,G.SOURCE_LUA).unlink()
  rows,_=self.old.history(self.game)
  self.put("WeiDU.log",("\n".join(rows[:-1])+"\n").encode())

 def install(self):
  with patch.object(G,"native_weidu",side_effect=self.native_install):
   return G.install(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game,G.INSTALL_TOKEN)

 def test_01_exact_prior_r44_and_R47_original_source_sha_pins(self):
  self.assertEqual(G.blob(G.R44_PATH.read_bytes()),G.R44_BLOB)
  self.assertEqual(G.blob(G.COMPOSE_PATH.read_bytes()),G.COMPOSE_BLOB)
  self.assertEqual(SHA(self.parts["BAF"]),G.EXPECTED_BAF_SHA)
  self.assertEqual(SHA(self.parts["LUA"]),G.EXPECTED_LUA_SHA)

 def test_02_inert_BAF_extends_BDDEFAI_without_replacing_or_equip(self):
  self.assertIn("EXTEND_TOP ~BDDEFAI.BCS~",G.TP2_TEXT)
  self.assertEqual(G.TP2_TEXT.count("EXTEND_TOP"),1)
  self.assertNotIn("XEquipItem",G.TP2_TEXT)
  self.assertNotIn("SetGlobal",G.TP2_TEXT)
  self.assertIn(b"pcall(BGXAI_R46_BDDEFAI_Witness); return false",self.parts["BAF"])
  self.assertEqual(self.parts["BAF"].count(b"EEex_LuaTrigger("),1)

 def test_03_preflight_guarded_last157_preserves_game_files(self):
  before=SHA(self.old.safe(self.game,"WeiDU.log").read_bytes())
  r=G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)
  self.assertEqual(r["status"],"R47_PREFLIGHT_R44_LAST157_PASS_NO_INSTALL")
  self.assertFalse(r["installed"]);self.assertFalse(r["gameModified"])
  self.assertEqual(before,SHA(self.old.safe(self.game,"WeiDU.log").read_bytes()))
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_04_no_install_without_new_exact_token(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_EXACT_TYPED_INSTALL_REQUIRED"):
   G.install(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game,"")
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())

 def test_05_unrelated_BCS_baseline_change_refuses(self):
  self.put(G.SOURCE_BCS,b"tamper")
  with self.assertRaisesRegex(ValueError,"HOLD_R47_ORIGINAL_BCS_BYTES_NOT_EXACT"):
   G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_06_wrong_R44_WeiDU_last_refuses(self):
  self.put("WeiDU.log",b"WRONG")
  with self.assertRaises(ValueError):
   G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_07_original_R44_active_lua_changed_refuses(self):
  self.put(G.R44_ACTIVE_LUA,b"bad")
  with self.assertRaises(ValueError):
   G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_08_wrong_R44_proof_refuses(self):
  self.put(self.r44.PROOF,b"{}")
  with self.assertRaises(ValueError):
   G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_09_existing_R47_witness_owner_collision_refuses(self):
  self.put(G.SOURCE_LUA,b"other mod already uses this file")
  with self.assertRaisesRegex(ValueError,"HOLD_R47_STAGING_ALREADY_PRESENT"):
   G.before_change(self.r44,self.r43,self.r42,self.r38,self.old,C,self.game)

 def test_10_guarded_install_only_158_same_R44_untouched(self):
  prior_r44=SHA(self.old.safe(self.game,G.R44_ACTIVE_LUA).read_bytes())
  out=self.install()
  self.assertEqual(out["status"],"R47_INERT_BDDEFAI_WITNESS_INSTALLED_AWAITING_LIVE")
  self.assertTrue(out["installed"]);self.assertTrue(out["gameModified"])
  self.assertEqual(len(self.old.history(self.game)[0]),158)
  self.assertEqual(SHA(self.old.safe(self.game,G.R44_ACTIVE_LUA).read_bytes()),prior_r44)
  self.assertEqual(SHA(self.old.safe(self.game,G.SOURCE_LUA).read_bytes()),G.EXPECTED_LUA_SHA)
  self.assertEqual(out["ordersSent"],0);self.assertFalse(out["armAuthorized"])

 def test_11_external_backup_contains_exact_legacy_BCS_and_proofs(self):
  out=self.install()
  backup=Path(out["externalBackup"])
  self.assertEqual(backup.parent,self.home/"Documents"/"BGXAI_BACKUPS")
  self.assertEqual((backup/G.SOURCE_BCS).read_bytes(),self.preimage)
  self.assertIn(self.r44.PROOF,out["baselineSnapshot"])
  self.assertIn(self.r43.PROOF,out["baselineSnapshot"])
  self.assertIn(self.r42.PROOF,out["baselineSnapshot"])
  self.old.verify_snapshot(backup,out["baselineSnapshot"])

 def test_12_mock_status_before_after_install(self):
  a=G.status(self.r44,self.r43,self.r42,self.r38,self.old,self.game)
  self.assertEqual(a["status"],"R47_NOT_INSTALLED_R44_PRESENT_LAST")
  self.install()
  b=G.status(self.r44,self.r43,self.r42,self.r38,self.old,self.game)
  self.assertEqual(b["status"],"R47_PRESENT_LAST_PASSIVE_WITNESS")
  self.assertFalse(b["actualBcsExecutionVerified"])

 def test_13_rollback_requires_new_typed_token(self):
  self.install()
  with self.assertRaisesRegex(ValueError,"HOLD_R47_EXACT_TYPED_ROLLBACK_REQUIRED"):
   G.rollback(self.r44,self.r43,self.r42,self.r38,self.old,self.game,"")

 def test_14_mock_rollback_restores_byte_exact_BCS_and_last157(self):
  self.install()
  with patch.object(G,"native_weidu",side_effect=self.native_rollback):
   out=G.rollback(self.r44,self.r43,self.r42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)
  self.assertEqual(out["status"],"R47_ROLLBACK_RESTORED_R44_LAST")
  self.assertEqual(len(self.old.history(self.game)[0]),157)
  self.assertEqual(self.old.safe(self.game,G.SOURCE_BCS).read_bytes(),self.preimage)
  self.assertFalse(self.old.safe(self.game,G.SOURCE_LUA).exists())
  self.assertEqual(SHA(self.old.safe(self.game,G.R44_ACTIVE_LUA).read_bytes()),self.r44.EXPECTED_SHA)

 def test_15_rollback_refuses_modified_BCS(self):
  self.install()
  self.put(G.SOURCE_BCS,b"other mod modified file")
  with self.assertRaisesRegex(ValueError,"HOLD_R47_INSTALLED_WITNESS_RESOURCE_DRIFT"):
   G.rollback(self.r44,self.r43,self.r42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

 def test_16_rollback_refuses_modified_unrelated_R44_file(self):
  self.install()
  self.put(G.R44_ACTIVE_LUA,b"drift")
  with self.assertRaises(ValueError):
   G.rollback(self.r44,self.r43,self.r42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

 def test_17_rollback_refuses_bad_backup_manifest(self):
  out=self.install()
  backup=Path(out["externalBackup"])
  (backup/"SHA256.json").write_text("{}")
  with self.assertRaisesRegex(ValueError,"HOLD_R47_EXTERNAL_BACKUP_MANIFEST_MISMATCH"):
   G.rollback(self.r44,self.r43,self.r42,self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

 def test_18_import_only_never_changes_game(self):
  self.assertFalse(self.old.safe(self.game,G.DIR).exists())
  raw=Path(G.__file__).read_text()
  self.assertNotIn("XEquipItem(",raw)
  self.assertNotIn("BGXAI_UPDATE2.cmd",raw)
  self.assertIn("HOLD_R47_SAME_ONEFILE_REVIEW_REQUIRED",raw)

if __name__=="__main__":
 unittest.main()
