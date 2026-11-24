"""V123 source-only cross-platform control-flow fallback tests.

Only synthetic bytes. No game binaries, hooks, or private report data.
"""
from __future__ import annotations
import base64
import hashlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
BUNDLE_PATH = HERE / "trusted_sources.zip.b64"
BUNDLE_SHA = "9d9a92e182a2389dc4ac4ca1f5c218c04b6452c80e4167d47a95d578da791090"
BOT_SHA = "94dec300ea191101e74da139e5844e1f04c97a5b42eaf299f2a68e42a6f881bc"
RET_OFFSET = 0x39E9B9 - 0x39DA50


class NoObjdumpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bundle = base64.b64decode(b"".join(BUNDLE_PATH.read_bytes().split()), validate=True)
        assert hashlib.sha256(bundle).hexdigest() == BUNDLE_SHA
        bot = (HERE / "BG_EET_RU_AUTOFIX_BOT.py").read_bytes()
        assert hashlib.sha256(bot).hexdigest() == BOT_SHA
        with ZipFile(io.BytesIO(bundle)) as archive:
            assert archive.testzip() is None
            assert len(archive.namelist()) == 14
            src = archive.read("hit_control_flow_audit.py")
            runner = archive.read("one_pass_offline_validation.py")
            assert b"PASS_SHA_PINNED_OFFLINE_DISASSEMBLY" in runner
            assert b"'evidence_mode':v.get('evidence_mode','LOCAL_OBJDUMP')" in runner
        lib = types.ModuleType("proof_hit_event_abi")
        lib.FUNC_NAME = "synthetic.bin"
        cls.module = types.ModuleType("hit_control_flow_audit")
        with patch.dict(sys.modules, {"proof_hit_event_abi": lib}):
            exec(compile(src, "hit_control_flow_audit.py", "exec"), cls.module.__dict__)

    def setUp(self):
        self.body = bytearray(b"\x90" * 3980)
        self.body[RET_OFFSET] = 0xC3

    def audit_synthetic(self):
        data = bytes(self.body)
        mod = self.module

        class SyntheticZip:
            def __init__(self, path):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                return False
            def read(self, name):
                assert name == "synthetic.bin"
                return data

        with patch.object(mod, "ZipFile", SyntheticZip), patch.object(mod.shutil, "which", return_value=None):
            return mod.audit(Path("synthetic.zip"))

    def test_pinned_no_objdump_exposes_replay_mode(self):
        self.module.PINNED = hashlib.sha256(self.body).hexdigest()
        result = self.audit_synthetic()
        self.assertEqual(result["status"], "PASS_SHA_PINNED_OFFLINE_DISASSEMBLY")
        self.assertEqual(result["direct_branches"], 95)
        self.assertFalse(result["direct_jumps_verified_here"])
        self.assertIn("NOT_LOCAL_DISASSEMBLY", result["evidence_mode"])
        self.assertEqual(result["game_files_written"], 0)

    def test_changed_input_does_not_replay_previous_evidence(self):
        self.module.PINNED = hashlib.sha256(self.body).hexdigest()
        self.body[7] ^= 1
        self.assertEqual(self.audit_synthetic()["status"], "BYTE_SHA_MISMATCH_HOLD")

    def test_expected_hash_with_invalid_layout_still_holds(self):
        self.body[RET_OFFSET] = 0x90
        self.module.PINNED = hashlib.sha256(self.body).hexdigest()
        self.assertEqual(self.audit_synthetic()["status"], "PINNED_FIXTURE_LAYOUT_HOLD")

    def test_truncated_bytes_hold_even_if_digest_matches(self):
        del self.body[-1:]
        self.module.PINNED = hashlib.sha256(self.body).hexdigest()
        self.assertEqual(self.audit_synthetic()["status"], "PINNED_FIXTURE_LAYOUT_HOLD")


if __name__ == "__main__":
    unittest.main()
