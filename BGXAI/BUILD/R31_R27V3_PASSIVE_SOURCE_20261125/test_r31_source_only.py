"""R31 passive observer source-only composition tests. Does not touch game files."""
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bgxai_r31", ROOT / "build_r31_v3_source_only.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class R31Offline(unittest.TestCase):
    def test_exact_v3_source_and_canonical_original(self):
        source = builder.R27_V3.read_bytes()
        self.assertEqual(len(source), builder.EXPECTED_V3_SIZE)
        self.assertEqual(builder.sha256(source), builder.EXPECTED_V3_SHA256)
        original = ROOT.parent / "R27_SINGLE_CALLBACK_SELECTED_RO_20261123" / "M_BGXR27.lua"
        self.assertEqual(builder.sha256(original.read_bytes()), builder.OLD_INSTALLED_R27_SHA256)
        self.assertNotEqual(builder.sha256(source), builder.OLD_INSTALLED_R27_SHA256)

    def test_bundle_is_deterministic_and_passive(self):
        a = builder.compose()
        self.assertEqual(a, builder.compose())
        self.assertTrue(a.startswith(b"-- R31 SOURCE ONLY:"))
        self.assertIn(b"local R27 = (function()\n", a)
        self.assertIn(b"\nreturn R27\n\nend)()\n", a)
        self.assertEqual(a.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener"), 1)
        self.assertEqual(a.count(b"BGXAI_R27_ObserverPilot=P"), 1)
        for forbidden in builder.FORBIDDEN_BUNDLE:
            self.assertNotIn(forbidden, a)
        self.assertNotIn(b"BGXW3_REQ", a)
        self.assertNotIn(b"INSTALL_BGXAI_", a)
        self.assertLess(len(a), 128000)

    def test_altered_source_and_removed_contract_are_denied(self):
        source = builder.R27_V3.read_bytes()
        boot = builder.BOOT.read_bytes()
        with self.assertRaisesRegex(builder.SourceHold, "R27_V3_EXACT_SHA_OR_SIZE_DRIFT"):
            builder.assemble(source + b"\n", boot)
        with self.assertRaisesRegex(builder.SourceHold, "R27_V3_EXACT_SHA_OR_SIZE_DRIFT"):
            builder.assemble(source.replace(b"queueSnapshotStable", b"QUEUE__SnapshotStable", 1), boot)
        with self.assertRaisesRegex(builder.SourceHold, "R31_BOOTSTRAP_CONTRACT_MISSING"):
            builder.assemble(source, boot.replace(b"R31_R27V3_PASSIVE", b"R31_DISABLED_______"))

    def test_bootstrap_is_only_passive_eeex_observer(self):
        boot = builder.BOOT.read_bytes()
        for command in (
            b"SelectWeaponAbility(", b"Attack(", b"Spell(", b"ClearActions(",
            b"SetGlobal(", b"CreateCreature(", b"ActionOverride(",
            b"EEex_Action_QueueScriptFileResponseOnAIBase(", b"os.execute(",
            b"io.open(", b"dofile(", b"loadfile(", b"debug.",
        ):
            self.assertNotIn(command, boot, command)
        self.assertNotIn(b"\nP.registered=true\n", boot[:boot.index(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener")])
        self.assertIn(b"if type(BGXAI_R27_ObserverPilot)=='table' and", boot)
        self.assertIn(b"if not pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener) then", boot)

    def test_offline_mock_three_lua_runtimes(self):
        names = ("lua5.3", "lua5.4", "luajit")
        available = [(name, shutil.which(name)) for name in names]
        if os.getenv("BGXAI_R31_REQUIRE_LUA") == "1":
            self.assertTrue(all(binpath for _, binpath in available), "all three Lua interpreters required")
        if not any(binpath for _, binpath in available):
            self.skipTest("Lua interpreters unavailable; static tests run independently")
        with tempfile.TemporaryDirectory(prefix="bgxai_r31_source_only_") as td:
            output = Path(td) / "R31V3_SOURCE_ONLY.lua"
            output.write_bytes(builder.compose())
            for name, binpath in available:
                if not binpath:
                    continue
                with self.subTest(runtime=name):
                    run = subprocess.run(
                        [binpath, str(ROOT / "test_r31_runtime.lua"), str(output)],
                        capture_output=True, text=True, timeout=25,
                    )
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertIn("0 orders", run.stdout)

    def test_builder_does_not_write_to_game_or_install(self):
        source = (ROOT / "build_r31_v3_source_only.py").read_text(encoding="utf-8")
        for command in ("write_bytes(", "write_text(", "subprocess.", "os.system(", "shutil.copy", "unlink(", "mkdir("):
            self.assertNotIn(command, source)
        self.assertIn("SOURCE_COMPOSITION_PASS_NO_INSTALL", source)


if __name__ == "__main__":
    unittest.main()
