"""R46 source-only BCS witness: never WeiDU, installed files, or actor actions."""
from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('r46_witness',HERE/'BGXAI_R46_INERT_BDDEFAI_WITNESS_SOURCE_ONLY.py')
P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)

class R46InertWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=P.compose()
        cls.baf=cls.src["R46_WITNESS_BAF"]
        cls.lua=cls.src["R46_WITNESS_LUA"]
        cls.tp2=cls.src["R46_WEIDU_BLUEPRINT_SOURCE_ONLY"]

    def test_exact_preexisting_compiled_R39_BAF_untouched(self):
        old=P.verified_prior()
        self.assertEqual(P.git_blob(old),P.R39_BAF_BLOB)
        self.assertEqual(old.count(b'XEquipItem("STAF01"'),1)
        self.assertNotIn(b'XEquipItem(',self.baf)

    def test_new_fragment_only_one_trigger_and_no_BAF_arm(self):
        self.assertEqual(self.baf.count(b"EEex_LuaTrigger("),1)
        self.assertEqual(self.baf.count(b"IF\n"),1)
        self.assertEqual(self.baf.count(b"Continue()"),1)
        self.assertNotIn(b"BGXW3ARM",self.baf)
        self.assertNotIn(b"Global(",self.baf)

    def test_LuaTrigger_always_false_even_on_global_collision(self):
        self.assertIn(b'EEex_LuaTrigger("pcall(BGXAI_R46_BDDEFAI_Witness); return false")',self.baf)
        self.assertNotIn(b'EEex_LuaTrigger("return BGXAI_R46_BDDEFAI_Witness()',self.baf)
        self.assertRegex(self.lua,rb"local function bridge\(\).*?return false\s+end".replace(b'.*?',b'[\s\S]*?'))

    def test_reuses_installed_EEex_conditional_pattern_only(self):
        self.assertIn(b"InParty(Myself)",self.baf)
        self.assertIn(b"InPartySlot(Myself,1)",self.baf)
        self.assertIn(b"EEex_LuaTrigger(",self.baf)
        self.assertNotIn(b"SetGlobal(",self.baf)

    def test_native_script_target_exact_reversible_weiDU_extension(self):
        self.assertEqual(self.tp2.count(b"EXTEND_TOP ~BDDEFAI.BCS~"),1)
        self.assertEqual(self.tp2.count(b"BACKUP ~BGXR46/backup~"),1)
        self.assertIn(b"COPY ~BGXR46/staged/M_BGXR46_WITNESS.lua~",self.tp2)
        self.assertNotIn(b"R39_JAGAN",self.tp2)
        self.assertNotIn(b"BGXW3ARM",self.tp2)

    def test_source_has_no_game_actions_and_no_observer_callbacks(self):
        for marker in (b"XEquipItem(",b"SetGlobal(",b"ActionOverride(",
                       b"ClearActions(",b"SelectWeaponAbility(",
                       b"EEex_Action_AddSpriteStartedActionListener(",
                       b"EEex_GameState_AddDestroyedListener("):
            for name,raw in self.src.items():
                self.assertNotIn(marker,raw,(name,marker))

    def test_actor_numeric_identity_and_class_assignment_guards(self):
        for marker in (b"field(actor,'m_id')",
                       b"field(portrait,'m_id')~=actorID",
                       b"portraitID~=actorID",
                       b"field(field(actor,'m_typeAI'),'m_Class')",
                       b"field(stats,'m_nKit')",
                       b"getScriptLevelResRef",
                       b"assigned:upper()~='BDDEFAI'"):
            self.assertIn(marker,self.lua)

    def test_only_one_bounded_redacted_log(self):
        self.assertEqual(self.lua.count(b"print('[BGXBEX]"),1)
        self.assertIn(b"if seen then return end",self.lua)
        self.assertIn(b"seen=true",self.lua)
        self.assertIn(b"witnessBlockEvaluated=true",self.lua)
        self.assertNotIn(b"actorID..",self.lua)
        self.assertIn(b"actionOriginVerified=false",self.lua)

    def test_deterministic_source_only(self):
        self.assertEqual(self.src,P.compose())
        self.assertGreater(len(self.lua),1000)
        self.assertLess(len(self.lua),7000)
        self.assertLess(len(self.baf),1000)

    def test_no_native_program_or_fs_game_mutation(self):
        raw=(HERE/'BGXAI_R46_INERT_BDDEFAI_WITNESS_SOURCE_ONLY.py').read_text()
        for bad in ("subprocess.", "os.system(", "write_bytes(",
                    "write_text(", "InfinityLoader.exe", "BGXAI_UPDATE.cmd"):
            self.assertNotIn(bad,raw)

    def test_already_existing_version_only_so_new_material_is_delta(self):
        orig=P.verified_prior()
        self.assertGreater(len(orig),len(self.baf))
        self.assertIn(b'XEquipItem("STAF01"',orig)
        self.assertNotIn(b'XEquipItem("STAF01"',self.baf)
        self.assertNotIn(b'XEquipItem("STAF01"',self.lua)

    def test_no_duplicate_source_creation(self):
        self.assertEqual(len(self.src),3)
        self.assertSetEqual(set(self.src),{
            "R46_WITNESS_BAF","R46_WITNESS_LUA","R46_WEIDU_BLUEPRINT_SOURCE_ONLY"})

if __name__=="__main__":
    unittest.main()
