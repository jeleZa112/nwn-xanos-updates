"""Confirmed user GAM CRE Script Name None vs GAM NPC character *GCLERIC.
R50 source-only exact correction, do not change game or old R48/R49.
"""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"BGXAI_R50_REUSE_R49_IDENTITY_DWARF_SOURCE_ONLY.py"
s=importlib.util.spec_from_file_location("bgxai_r50_identity_source_only",SOURCE)
R=importlib.util.module_from_spec(s);s.loader.exec_module(R)

class IdentityFix(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.old=R.source()
  cls.new=R.compose()

 def test_01_unchanged_pinned_R49_source(self):
  self.assertEqual(R.blob(R.OLD.read_bytes()),R.OLD_BLOB)
  self.assertEqual(len(self.new),len(self.old)+len(R.GOOD)-len(R.BAD))

 def test_02_exact_one_reversible_identity_trigger_patch(self):
  self.assertEqual(self.old.count(R.BAD),1)
  self.assertEqual(self.new.count(R.BAD),0)
  self.assertEqual(self.new.count(R.GOOD),1)
  self.assertEqual(self.new,R.source().replace(R.BAD,R.GOOD,1))
  self.assertEqual(self.new.replace(R.GOOD,R.BAD,1),self.old)

 def test_03_script_name_vs_gam_character_id_not_forged(self):
  self.assertIn(b'Race(Myself,DWARF)',self.new)
  self.assertNotIn(b'Name("*GCLERIC",Myself)',self.new)
  self.assertEqual(self.new.count(b'InPartySlot(Myself,1)'),1)
  self.assertEqual(self.new.count(b'Class(Myself,CLERIC)'),1)
  self.assertEqual(self.new.count(b'CheckStatGT(Myself,4,STR)'),1)
  self.assertEqual(self.new.count(b'InParty(Myself)'),1)

 def test_04_all_backpack16_slots_still_present(self):
  self.assertEqual(self.new.count(b'OR(16)'),1)
  self.assertEqual(self.new.count(b'CheckItemSlot('),16)
  for k in range(3,19):
   self.assertEqual(self.new.count(b'CheckItemSlot(Myself,"STAF01",SLOT_MISC%d)'%k),1)
  self.assertIn(b'SLOT_MISC7',self.new)

 def test_05_unchanged_action_and_one_attempt(self):
  self.assertEqual(self.new.count(b'XEquipItem('),1)
  self.assertEqual(self.new.count(b'SetGlobal('),1)
  self.assertEqual(self.new.count(b'Global("BGX48TRY","LOCALS",0)'),1)
  self.assertLess(self.new.index(b'SetGlobal("BGX48TRY","LOCALS",1)'),
                  self.new.index(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'))

 def test_06_bcs_combat_and_manual_eps_queue_guards_unchanged(self):
  for needle in R.SAFETY:
   self.assertEqual(self.new.count(needle),1,needle)
  for forbidden in (b'Attack(',b'ClearActions(',b'EEex_LuaTrigger(',
                   b'ForceSpell(',b'ActionOverride('):
   self.assertNotIn(forbidden,self.new)

 def test_07_tampered_R49_original_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   fake=Path(td)/"old.py"
   fake.write_bytes(R.OLD.read_bytes()+b"\n#tweak")
   with patch.object(R,"OLD",fake):
    with self.assertRaisesRegex(R.Hold,"HOLD_R50_PRIOR_R49_SOURCE_GIT_BLOB_CHANGED"):
     R.compose()

 def test_08_source_bytes_deterministic(self):
  self.assertEqual(hashlib.sha256(R.compose()).digest(),
                   hashlib.sha256(self.new).digest())
  self.assertEqual(hashlib.sha256(R.OLD.read_bytes()).digest(),
                   hashlib.sha256(R.OLD.read_bytes()).digest())

 def test_09_no_new_native_deployment_or_updater(self):
  s=SOURCE.read_text("ascii")
  for token in ("setup-BGXR50.exe","BGXAI_UPDATE2.cmd",
                "native.install(", "subprocess.run(", "XEquipItem\\("):
   self.assertNotIn(token,s)
  self.assertIn("oldOneShotBGX48TRYPreserved",s)

if __name__=="__main__":
 unittest.main()
