"""BGXP3 installer safety unit tests. Synthetic files only, no EET process."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import BGXP3_INSTALL as I
import BGXP3_BCS_PREFLIGHT_SOURCE_ONLY as P
import BGXP2_BCS_PATCH as B


def write(root, name, data):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def fake_bcs():
    unit = b"CR\nCO\nTR\nRS\nRE\nRS\nCR\n"
    return b"SC\n" + unit * 1158 + b"SC\n"


class TestGuardedInstaller(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "BG_EET_FOXX_NEW"
        self.root.mkdir()
        self.raw = fake_bcs()
        self.live_sha = hashlib.sha256(self.raw).hexdigest()
        write(self.root, I.BCS_PATH, self.raw)
        write(self.root, I.LUA_PATH, b"LUA-original")
        write(self.root, "WeiDU.log", b"~BGXP2\\SETUP-BGXP2.TP2~ #0 #0 // mock\n")
        write(self.root, "BGXP2/STAGED_PROOF.json",
              json.dumps({"new_bcs_sha256": self.live_sha,
                          "lua_sha256": hashlib.sha256(b"LUA-original").hexdigest()}).encode())
        write(self.root, "BGXP2/staged/BDDEFAI.BCS", self.raw)
        self.old_bcs, self.old_lua = P.LIVE_BCS_SHA, P.LIVE_LUA_SHA
        P.LIVE_BCS_SHA = self.live_sha
        P.LIVE_LUA_SHA = hashlib.sha256(b"LUA-original").hexdigest()
        self.addCleanup(lambda: setattr(P, "LIVE_BCS_SHA", self.old_bcs))
        self.addCleanup(lambda: setattr(P, "LIVE_LUA_SHA", self.old_lua))

    def test_baseline_exact_and_readonly(self):
        before = self.raw
        result = I.baseline(self.root)
        self.assertEqual(result["state"], "BGXP2_INSTALLED_VERIFIED")
        self.assertEqual((self.root / I.BCS_PATH).read_bytes(), before)

    def test_refuses_last_mod_change(self):
        write(self.root, "WeiDU.log", b"~other\\SETUP-OTHER.TP2~ #0 #0\n")
        with self.assertRaisesRegex(I.Stop, "BGXP2_NOT_LAST"):
            I.baseline(self.root)

    def test_refuses_changed_lua(self):
        write(self.root, I.LUA_PATH, b"CHANGED")
        with self.assertRaisesRegex(I.Stop, "INSTALLED_BGXP2_LUA_CHANGED"):
            I.baseline(self.root)

    def test_refuses_changed_bcs(self):
        write(self.root, I.BCS_PATH, self.raw + b"X")
        with self.assertRaisesRegex(I.Stop, "INSTALLED_BGXP2_BCS_CHANGED"):
            I.baseline(self.root)

    def test_refuses_stage_collision(self):
        (self.root / "BGXP3").mkdir()
        with self.assertRaisesRegex(I.Stop, "BGXP3_STAGE_ALREADY_EXISTS"):
            I.baseline(self.root)

    def test_no_install_without_exact_consent(self):
        self.assertEqual(I.main(["install", "--game-root", str(self.root)]), 2)
        self.assertEqual(I.main(["install", "--confirm", I.INSTALL_TOKEN,
                                "--game-root", str(self.root)]), 2)
        self.assertEqual(I.main(["rollback", "--game-root", str(self.root)]), 2)

    def test_refuse_wrong_root_even_with_consent(self):
        self.assertEqual(I.main(["install", "--yes", "--confirm", I.INSTALL_TOKEN,
                                 "--game-root", str(self.root)]), 2)

    def test_installed_requires_exact_prior_1157(self):
        # Simulate last-installed mod but a BCS whose first 1157 blocks are different.
        raw = b"SC\n" + b"CR\nCO\nTR\nRS\nRE\nRS\nCR\n" * 1157 + b"CR\nCO\nTR\nRS\nRE\nRS\nX\nCR\nSC\n"
        write(self.root, "WeiDU.log", b"~BGXP3\\SETUP-BGXP3.TP2~ #0 #0 // mock\n")
        write(self.root, I.TP2, I.TP2_TEXT.encode("utf-8"))
        write(self.root, I.PROOF, json.dumps({"old_bcs_sha256": self.live_sha,
                                            "new_bcs_sha256": hashlib.sha256(raw).hexdigest(),
                                            "lua_sha256": P.LIVE_LUA_SHA}).encode())
        write(self.root, I.STAGE, raw)
        write(self.root, I.BCS_PATH, raw)
        with self.assertRaisesRegex(I.Stop, "BGXP3_UNEXPECTED_BCS_DELTA"):
            I.installed(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
