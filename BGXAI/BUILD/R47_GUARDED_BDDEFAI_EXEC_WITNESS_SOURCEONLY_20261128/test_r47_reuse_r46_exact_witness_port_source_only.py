"""R47 only substitutes R44-proven global EEex script-port, old BAF inert."""
from __future__ import annotations
import hashlib,importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('r47_fixed_port',HERE/'BGXAI_R47_CORRECT_R46_EEEX_SCRIPT_PORT_SOURCE_ONLY.py')
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)

class TestR47(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=M.original()
  cls.parts=M.source_only()
  cls.lua=cls.parts["LUA"]
  cls.baf=cls.parts["BAF"]
  cls.old=cls.original["R46_WITNESS_LUA"]

 def test_old_proven_source_git_blob(self):
  self.assertEqual(M.blob(M.R46_SOURCE.read_bytes()),M.R46_SOURCE_BLOB)
  self.assertEqual(M.sha(self.old),M.R46_ORIGINAL_LUA_SHA)

 def test_old_user_native_223B_BAF_identical(self):
  self.assertEqual(self.baf,self.original["R46_WITNESS_BAF"])
  self.assertEqual(M.sha(self.baf),M.R46_BAF_SHA)
  self.assertEqual(len(self.baf),223)

 def test_only_one_proven_EEex_API_replacement(self):
  wrong=b"local getScript=field(actor,'getScriptLevelResRef')"
  right=b"local getScript=rawget(_G,'EEex_AIBase_GetScriptLevelResRef')"
  self.assertIn(wrong,self.old)
  self.assertNotIn(wrong,self.lua)
  self.assertEqual(self.lua.count(right),1)
  self.assertEqual(self.old.replace(wrong,right,1),self.lua)

 def test_all_other_R46_behavior_unchanged(self):
  self.assertEqual(self.lua.count(b"print('[BGXBEX]"),1)
  self.assertIn(b"local seen=false",self.lua)
  self.assertIn(b"return false\n",self.lua)
  self.assertIn(b"pcall(witness)",self.lua)
  self.assertIn(b"field(portrait,'m_id')~=actorID",self.lua)
  self.assertIn(b"field(stats,'m_nKit')~=16384",self.lua)

 def test_no_game_orders_and_no_new_listener(self):
  for b in (b"XEquipItem(",b"SetGlobal(",b"ActionOverride(",
            b"SelectWeaponAbility(",b"ClearActions(",
            b"EEex_Action_AddSpriteStartedActionListener("):
   self.assertNotIn(b,self.lua)
   self.assertNotIn(b,self.baf)
  self.assertIn(b'EEex_LuaTrigger("pcall(BGXAI_R46_BDDEFAI_Witness); return false")',self.baf)

 def test_no_writes_or_native_execution_when_imported(self):
  s=(HERE/'BGXAI_R47_CORRECT_R46_EEEX_SCRIPT_PORT_SOURCE_ONLY.py').read_text()
  for bad in ("subprocess.", "os.system(", "write_bytes(", "write_text(", "InfinityLoader.exe"):
   self.assertNotIn(bad,s)

 def test_exact_reproducibility(self):
  self.assertEqual(M.source_only(),self.parts)
  self.assertNotEqual(M.sha(self.lua),M.sha(self.old))

 def test_namespace_unchanged(self):
  self.assertIn(b"local NAME='BGXAI_R46_BDDEFAI_Witness'",self.lua)
  self.assertIn(b"if rawget(_G,NAME)==nil then",self.lua)

 def test_item_interaction_never_in_this_stage(self):
  self.assertNotIn(b"BGXW3ARM",self.lua)
  self.assertNotIn(b"STAF01",self.lua)
  self.assertNotIn(b"BGXW3ARM",self.baf)

 def test_output_is_source_only_no_install(self):
  self.assertTrue(M.SCHEMA.endswith("SOURCE_ONLY_V1"))
  self.assertEqual(len(self.parts),2)

if __name__=="__main__":
 unittest.main()
