"""R49 bounded source repair: preserve original R48 guards, no deployment."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
FILE=HERE/"BGXAI_R49_REUSE_R48_BACKPACK16_SOURCE_ONLY.py"
spec=importlib.util.spec_from_file_location("r49_backpack16_source_only",FILE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PreserveR48(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=m.compose()
  cls.original_file=m.OLD

 def test_01_old_git_blob_exact_and_new_code_not_installed(self):
  self.assertEqual(m.blob(m.OLD.read_bytes()),m.OLD_BLOB)
  self.assertEqual(m.SCHEMA,"BGXAI_R49_REUSE_R48_ANY_BACKPACK16_ONE_SHOT_SOURCE_ONLY_V1")
  source=FILE.read_text(encoding="ascii")
  for danger in ("weidu.exe", "setup-BGXR49.exe", "EXTEND_TOP",
                 "native.install(", "native.rollback("):
   self.assertNotIn(danger,source)

 def test_02_all_sixteen_original_backpack_positions(self):
  self.assertEqual(self.raw.count(b'CheckItemSlot('),16)
  self.assertEqual(self.raw.count(b'OR(16)'),1)
  for n in range(3,19):
   self.assertEqual(self.raw.count(
    b'CheckItemSlot(Myself,"STAF01",SLOT_MISC%d)'%n),1)
  self.assertIn(b'SLOT_MISC7',self.raw)
  self.assertNotIn(b'CheckItemSlot(Myself,"STAF01",SLOT_MISC19)',self.raw)

 def test_03_one_unchanged_action_and_unchanged_oneshot_flag(self):
  self.assertEqual(self.raw.count(m.EQUIP),1)
  self.assertEqual(self.raw.count(m.ONCE),1)
  self.assertEqual(self.raw.count(m.ONCE_ACTION),1)
  self.assertEqual(self.raw.count(b'SetGlobal('),1)
  self.assertEqual(self.raw.count(b'XEquipItem('),1)
  self.assertLess(self.raw.index(m.ONCE_ACTION),self.raw.index(m.EQUIP))

 def test_04_every_r48_guard_preserved(self):
  for trigger in m.GUARDS:
   self.assertEqual(self.raw.count(trigger),1,trigger)
  self.assertNotIn(b'EEex_LuaTrigger(',self.raw)
  self.assertNotIn(b'ClearActions(',self.raw)
  self.assertNotIn(b'SelectWeaponAbility(',self.raw)
  self.assertNotIn(b'ActionOverride(',self.raw)

 def test_05_exact_one_span_change_vs_old_original(self):
  o_spec=importlib.util.spec_from_file_location("original_r48_verify",m.OLD)
  old=importlib.util.module_from_spec(o_spec);o_spec.loader.exec_module(old)
  source=old.compose()
  self.assertEqual(source.count(m.OLD_TRIGGER),1)
  self.assertEqual(self.raw.replace(m.CONDITION,m.OLD_TRIGGER),source)
  self.assertEqual(self.raw,source.replace(m.OLD_TRIGGER,m.CONDITION,1))
  self.assertEqual(hashlib.sha256(self.raw).hexdigest(),
                   hashlib.sha256(m.compose()).hexdigest())

 def test_06_no_additional_actor_or_weapon_commands(self):
  blocks=re.findall(rb'(?ms)^IF\n.*?^END(?:\r?\n|$)',self.raw)
  self.assertEqual(len(blocks),1)
  self.assertEqual(blocks[0].count(b'RESPONSE #100'),1)
  self.assertEqual(blocks[0].count(b'XEquipItem('),1)
  self.assertNotIn(b'Continue()',blocks[0])
  self.assertNotIn(b'ForceSpell(',blocks[0])

 def test_07_unrecognized_prior_source_fails_closed(self):
  with tempfile.TemporaryDirectory() as temp:
   broken=Path(temp)/"R48_COMPOSER.py"
   broken.write_bytes(m.OLD.read_bytes()+b"\n# MALICIOUS SOURCE DRIFT\n")
   with patch.object(m,"OLD",broken):
    with self.assertRaisesRegex(m.Hold,"ORIGINAL_R48_COMPOSER_BLOB_DRIFT"):
     m.compose()

 def test_08_no_mutation_of_prior_source(self):
  before=hashlib.sha256(m.OLD.read_bytes()).hexdigest()
  m.compose()
  self.assertEqual(before,hashlib.sha256(m.OLD.read_bytes()).hexdigest())

if __name__=="__main__":
 unittest.main(verbosity=2)
