"""Read-only, mock-install and mock-rollback tests; NEVER invoke native WeiDU."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock
import shutil

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r31_guarded", ROOT / "R31_GUARDED_SOURCE_ONLY.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
SOURCE = ROOT / "M_BGXR27_R31_SOURCE_ONLY.lua"
R29_LINE = "~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // BGXR29 fighter quickslot bow-to-sword rule"
R31_LINE = "~BGXR31/SETUP-BGXR31.TP2~ #0 #0 // BGXR31 passive R27V3 observer only"
R27_LINE = "~BGXR27/SETUP-BGXR27.TP2~ #0 #0 // R27"


def digest(x):
    return hashlib.sha256(x).hexdigest()


def fixture(root):
    rows = [f"~MOCK{i:03}/SETUP-MOCK{i:03}.TP2~ #0 #0 // synthetic" for i in range(148)]
    rows.extend((R27_LINE, R29_LINE))
    paths = {
        "WeiDU.log": ("\n".join(rows) + "\n").encode(),
        g.OVERRIDE: b"existing_r27_fixture",
        "chitin.key": b"synthetic_game_key",
        "override/BDDEFAI.BCS": b"r29_pilot_should_remain",
        "override/DPLAYER.BCS": b"v6_should_remain",
        "EEex/copy/EEex_scripts/EEex_Action.lua": b"EEex_Action_fixture",
        "EEex/copy/EEex_scripts/EEex_Sprite.lua": b"EEex_Sprite_fixture",
        "enhanced-powergaming-scripts/lib/core_base.tph": b"EPS_core_fixture",
        "setup-enhanced-powergaming-scripts.exe": b"MZsynthetic_weidu",
    }
    for rel, data in paths.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return paths


class R31GuardedTests(TestCase):
    def test_source_frozen_and_exact(self):
        data = g.candidate_data(SOURCE)
        self.assertEqual(len(data), 47550)
        self.assertEqual(digest(data), g.SOURCE_SHA)
        self.assertNotIn(b"SelectWeaponAbility(", data)

    def test_tokens_block_unapproved_mutations(self):
        with self.assertRaisesRegex(g.Hold, "EXACT_TYPED_INSTALL_CONSENT_REQUIRED"):
            g.install(Path("/no/game"), SOURCE, "")
        with self.assertRaisesRegex(g.Hold, "EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED"):
            g.rollback(Path("/no/game"), "")
        self.assertNotIn("subprocess.run(", g.backup.__code__.co_names)

    def test_history_150_preflight_and_negative_cases(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            paths = fixture(root)
            pins = {x: digest(paths[x]) for x in g.PINNED}
            with mock.patch.object(g, "WEIDU_BASELINE_SHA", digest(paths["WeiDU.log"])), \
                 mock.patch.object(g, "WEIDU_EXE_SHA", digest(paths["setup-enhanced-powergaming-scripts.exe"])), \
                 mock.patch.object(g, "PINNED", pins):
                before = {key: (root / key).read_bytes() for key in paths}
                baseline = g.baseline(root, SOURCE, live=False)
                self.assertEqual(baseline["weiduComponentCount"], 150)
                self.assertEqual(baseline["r27ComponentPosition"], 149)
                self.assertEqual(baseline["weiduLastComponent"], R29_LINE)
                self.assertFalse(baseline["installationPerformed"])
                self.assertFalse(baseline["dispatchAuthorized"])
                self.assertFalse(baseline["queueBindingLiveVerified"])
                self.assertEqual(before, {key: (root / key).read_bytes() for key in paths})
                (root / "WeiDU.log").write_bytes(paths["WeiDU.log"].replace(R29_LINE.encode(), b"~MOCK/SETUP-MOCK.TP2~ #0 #0"))
                with self.assertRaisesRegex(g.Hold, "WEIDU_BASELINE_SHA_DRIFT"):
                    g.baseline(root, SOURCE, live=False)

    def test_protected_paths_reject_symlink_and_traversal(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(g.Hold, "BAD_PATH_COMPONENT"):
                g.safe(root, "../override/foo")
            with self.assertRaisesRegex(g.Hold, "BAD_RELATIVE_PATH"):
                g.safe(root, "C:/anything")

    def test_mocked_install_and_last_only_rollback_preserve_unrelated_files(self):
        with TemporaryDirectory() as td:
            base = Path(td)
            root = base / "game"
            root.mkdir()
            paths = fixture(root)
            pins = {x: digest(paths[x]) for x in g.PINNED}
            home = base / "home"
            home.mkdir()
            native_calls = []
            def fake_native(game, uninstall=False):
                native_calls.append("uninstall" if uninstall else "install")
                if uninstall:
                    proof = json.loads((game / g.PROOF).read_text())
                    back = Path(proof["externalBackup"])
                    shutil.copy2(back / g.OVERRIDE, game / g.OVERRIDE)
                    shutil.copy2(back / "WeiDU.log", game / "WeiDU.log")
                else:
                    shutil.copy2(game / g.STAGED, game / g.OVERRIDE)
                    with (game / "WeiDU.log").open("a", encoding="utf-8") as f:
                        f.write(R31_LINE + "\n")
            with mock.patch.object(g, "WEIDU_BASELINE_SHA", digest(paths["WeiDU.log"])), \
                 mock.patch.object(g, "WEIDU_EXE_SHA", digest(paths["setup-enhanced-powergaming-scripts.exe"])), \
                 mock.patch.object(g, "PINNED", pins), \
                 mock.patch.object(g, "OLD_R27_SHA", digest(paths[g.OVERRIDE])), \
                 mock.patch.object(g, "verify_processes", lambda: None), \
                 mock.patch.object(g, "protected_root", lambda game, live: None), \
                 mock.patch.object(g, "invoke_weidu", fake_native), \
                 mock.patch.dict(os.environ, {"USERPROFILE": str(home)}):
                result = g.install(root, SOURCE, g.INSTALL_TOKEN)
                self.assertEqual(result["status"], "R31_PASSIVE_INSTALLED_AWAITING_RUNTIME")
                self.assertEqual(digest((root / g.OVERRIDE).read_bytes()), g.SOURCE_SHA)
                self.assertEqual((root / "override/BDDEFAI.BCS").read_bytes(), paths["override/BDDEFAI.BCS"])
                self.assertEqual((root / "override/DPLAYER.BCS").read_bytes(), paths["override/DPLAYER.BCS"])
                self.assertEqual(native_calls, ["install"])
                # Never allow a rollback when a later WeiDU component is last.
                with (root / "WeiDU.log").open("a", encoding="utf-8") as handle:
                    handle.write("~MOCKLATER/SETUP-MOCKLATER.TP2~ #0 #0 // later component\\n")
                with self.assertRaisesRegex(g.Hold, "R31_NOT_LAST_NO_ROLLBACK"):
                    g.rollback(root, g.ROLLBACK_TOKEN)
                lines = (root / "WeiDU.log").read_text(encoding="utf-8").splitlines()
                (root / "WeiDU.log").write_text("\\n".join(lines[:-1]) + "\\n", encoding="utf-8")
                state = g.rollback(root, g.ROLLBACK_TOKEN)
                self.assertEqual(state["status"], "R31_ROLLBACK_R29_RESTORED")
                self.assertEqual((root / g.OVERRIDE).read_bytes(), paths[g.OVERRIDE])
                self.assertEqual((root / "override/BDDEFAI.BCS").read_bytes(), paths["override/BDDEFAI.BCS"])
                self.assertEqual(native_calls, ["install", "uninstall"])


if __name__ == "__main__":
    main()
