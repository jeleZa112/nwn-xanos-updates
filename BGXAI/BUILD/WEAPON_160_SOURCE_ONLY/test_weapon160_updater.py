#!/usr/bin/env python3
"""Source-only invariant tests for a staged BGXAI one-file menu 160.

The Windows PowerShell AST test is in the paired workflow. This module does
NOT execute the updater, install anything, alter the game, or update PIN.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
UPDATER = ROOT / "BGXAI/BGXAI_SYNC.ps1"
CANDIDATE = ROOT / "BGXAI/BUILD/WEAPON_160_SOURCE_ONLY/BGXAI_SYNC_160_CANDIDATE.ps1"
PIN = ROOT / "BGXAI/fox_new/BOOTSTRAP_PIN.json"
SCANNER = ROOT / "BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V2.py"
MENU = "160 - Weapon EEex R11 static compat READ ONLY\n"
HANDLER_PREFIX = "'160' {"
SCANNER_HASH = "0b05e83a6a34bfc2b97be87d8b06761719b43ddaab39593a3863bf1f2317e316"
RENAMES = {
    "releaseRanged": "rg",
    "releaseAOE": "ao",
    "releaseWeaponRO": "wr",
    "release042b": "b42",
    "release041": "b41",
    "release040": "b40",
    "release060": "b60",
}

def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def restore(candidate: str) -> str:
    assert candidate.count(MENU) == 1
    candidate = candidate.replace(MENU, "", 1)
    candidate, count = re.subn(r"(?m)^'160' \{[^\n]*\}\n", "", candidate)
    assert count == 1
    for old, short in RENAMES.items():
        candidate = re.sub(r"\$" + re.escape(short) + r"\b", "$" + old, candidate)
    return candidate


class Weapon160Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_bytes = UPDATER.read_bytes()
        cls.candidate_bytes = CANDIDATE.read_bytes()
        cls.original = cls.original_bytes.decode("utf-8")
        cls.candidate = cls.candidate_bytes.decode("utf-8")
        cls.pin = json.loads(PIN.read_text("utf-8"))

    def test_old_script_matches_immutable_channel_descriptor(self):
        self.assertEqual(len(self.original_bytes), self.pin["script_size"])
        self.assertEqual(sha(self.original_bytes), self.pin["script_sha256"])

    def test_candidate_fits_existing_bootstrap_limit(self):
        self.assertLessEqual(len(self.candidate_bytes), 80_000)
        self.assertGreater(len(self.candidate_bytes), 70_000)

    def test_all_legacy_actions_exact_when_restored(self):
        self.assertEqual(restore(self.candidate).encode("utf-8"), self.original_bytes)

    def test_no_menu_collision(self):
        pattern = r"(?m)^'(\d+)' \{"
        legacy = re.findall(pattern, self.original)
        actual = re.findall(pattern, self.candidate)
        self.assertEqual(len(legacy), 159)
        self.assertEqual(len(set(legacy)), 159)
        self.assertEqual(actual, legacy + ["160"])

    def test_source_is_pinned_by_hash_and_size(self):
        payload = SCANNER.read_bytes()
        self.assertEqual(len(payload), 6044)
        self.assertEqual(sha(payload), SCANNER_HASH)
        self.assertEqual(self.candidate.count(SCANNER_HASH), 2)
        self.assertIn("if($b.Length -ne 6044", self.candidate)

    def test_new_menu_read_only_and_temp_cache_not_game_override(self):
        handler = next(line for line in self.candidate.splitlines()
                       if line.startswith(HANDLER_PREFIX))
        self.assertIn("Get-PinnedBytes $r", handler)
        self.assertIn("Join-Path $cacheDir", handler)
        self.assertIn("[IO.FileMode]::CreateNew", handler)
        self.assertIn("--game $GameRoot", handler)
        self.assertIn("finally{if(Test-Path -LiteralPath $f)", handler)
        for banned in ("WeiDU", "override\\", "ClearActions", "SelectWeaponAbility", "SetGlobal"):
            self.assertNotIn(banned, handler)
        self.assertIn("runtimeApiAuthenticated", SCANNER.read_text("utf-8"))

    def test_no_unapproved_pin_promotion(self):
        self.assertEqual(self.pin["commit"], "0811abcf0903c621b408997481ada0ee2009d9a9")
        self.assertNotIn("160", self.pin.get("description", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
