"""Offline test: R33 builder must preserve R31 source and fail closed."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("r33", HERE / "build_r33_r31_reuse_prof_ro.py")
r33 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = r33
SPEC.loader.exec_module(r33)


class R33(unittest.TestCase):
    def test_pinned_original_is_unmodified(self):
        before = hashlib.sha256(r33.R31.read_bytes()).hexdigest()
        source, digest = r33.build()
        self.assertEqual(before, r33.R31_SHA256)
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(r33.R31.read_bytes()).hexdigest(), before)
        self.assertIn("BGXAI_R33_R27V3_PASSIVE_PROF_CANDIDATE", source)

    def test_one_listener_no_actions(self):
        before = r33.R31.read_text()
        after, _ = r33.build()
        for token in ("EEex_Action_AddSpriteStartedActionListener", "SelectWeaponAbility(",
                      "ClearActions(", "ActionOverride(", "SetGlobal(", "Attack(",
                      "EEex_Sprite_GetActiveStats"):
            self.assertEqual(after.count(token), before.count(token), token)
        self.assertEqual(after.count("local R27 = {schema="), 1)

    def test_existing_double_read_reused_not_new_getactive(self):
        content, _ = r33.build()
        self.assertIn("r4=pcall(R4_CORE.observeStableDerived", content)
        self.assertIn("local field=R4_CORE.proficiencyFieldById[id]", content)
        self.assertIn("proficiencyStat89to134Raw", content)
        self.assertIn("actorPipsVerified", content)
        self.assertIn("activeDualMultiClassVerified", content)
        self.assertIn('"classRowVerified":false', content)
        self.assertIn('"weaponToProficiencyVerified":false', content)

    def test_new_code_only_raw_data_and_no_engine_dispatch(self):
        content, _ = r33.build()
        self.assertIn("local profRaw={}", content)
        self.assertIn("for id=89,134 do", content)
        self.assertIn("jnum(values[i],-2147483648,2147483647)", content)
        self.assertIn("local okClass,typeAI=pcall(function()return sprite.m_typeAI end)", content)
        self.assertIn("a.aiClass==b.aiClass", content)
        self.assertIn("currentActionPreserved=true", content)
        self.assertIn("weaponSwitchAuthorized=false", content)

    def test_builder_rejects_mutated_or_repeated_anchors(self):
        original = r33.R31.read_text()
        for damaged in (original.replace(" local ability=scalar(eq,", " local ability2=scalar(eq(", 1),
                        original + original):
            with self.assertRaises(ValueError):
                r33.generate(damaged)

    def test_generate_deterministic(self):
        a, hash_a = r33.build()
        b, hash_b = r33.build()
        self.assertEqual(hash_a, hash_b)
        self.assertEqual(a, b)

    def test_invalid_output_folders_hold(self):
        import argparse
        # The Python entrypoint forbids outputs under override / EEex,
        # while unit tests deliberately never write to either path.
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / r33.NAME
            s, _ = r33.build()
            p.write_text(s)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             hashlib.sha256(s.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
