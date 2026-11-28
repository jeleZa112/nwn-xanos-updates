"""R42 HOLD reason extension regression: pinned old observer, no game, no writes."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "r42_hold_reason_ro", HERE / "BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py")
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


class R42HoldReasonSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = D.verified_original()
        cls.r38 = cls.base.verified(cls.base.R38, cls.base.R38_BYTES, cls.base.R38_BLOB)
        cls.r39 = cls.base.verified(cls.base.R39, cls.base.R39_BYTES, cls.base.R39_BLOB)
        cls.previous = cls.base.compose(cls.r38, cls.r39)
        cls.candidate = D.compose()

    def test_exact_published_original_r42_candidate_unchanged(self):
        self.assertEqual(len(self.previous), 93776)
        self.assertEqual(hashlib.sha256(self.previous).hexdigest(),
                         "d14bf5f62f7d37663cf77f3305f57fb9631293940ed8ae2d4cb7b488248434b0")

    def test_original_r39_bridge_embedded_once_identical(self):
        self.assertEqual(self.previous.count(self.r39), 1)
        self.assertEqual(self.candidate.count(self.r39), 1)

    def test_delta_is_exactly_two_inserts_no_other_mutations(self):
        rest = self.candidate.replace(D.DIAG_LUA.encode("ascii"), b"", 1)
        rest = rest.replace(D.JSON_DELTA, b"", 1)
        self.assertEqual(rest, self.previous)

    def test_exact_one_listener_and_row(self):
        self.assertEqual(self.candidate.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener"), 1)
        self.assertEqual(self.candidate.count(b"EEex_Action_AddSpriteStartedActionListener("), 0)
        self.assertEqual(self.candidate.count(b"[BGXBCS]"), 1)
        self.assertEqual(self.candidate.count(b"R27.r42Once=true"), 1)
        self.assertEqual(self.candidate.count(b"probeInstalledScriptAssignments()"),
                         self.previous.count(b"probeInstalledScriptAssignments()"))

    def test_existing_four_streams_identical(self):
        for tag in (b"[BGXR27]", b"[BGXR37]", b"[BGXINV3]", b"[BGXID]"):
            self.assertEqual(self.previous.count(tag), self.candidate.count(tag))

    def test_source_has_single_script_scope_and_no_game_ops(self):
        added = D.DIAG_LUA.encode("ascii") + D.JSON_DELTA
        for prohibited in (b"XEquipItem(", b"SetGlobal(", b"ActionOverride(",
                           b"ClearActions(", b"SelectWeaponAbility(",
                           b"EEex_Action_AddSpriteStartedActionListener("):
            self.assertNotIn(prohibited, added)
        self.assertNotIn(b"BGXW3ARM", added)
        self.assertNotIn(b"BDDEFAI", added)

    def test_extra_json_fields_are_allowlisted_only(self):
        delta = D.DIAG_LUA + D.JSON_DELTA.decode("ascii")
        self.assertIn("allowedStatuses[row.status]", delta)
        self.assertIn("allowedDetails[row.reason]", delta)
        self.assertIn("r39ProbeStatus", delta)
        self.assertIn("r39PhysicalReason", delta)
        self.assertIn("r39ClassSlotState", delta)
        self.assertNotIn('..row.status..', delta)
        self.assertNotIn('..row.reason..', delta)

    def test_all_known_real_r39_failures_have_code(self):
        bridge = self.r39.decode("utf-8")
        codes = (
            "HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE",
            "HOLD_SCRIPT_ASSIGNMENT_ACTOR_ID",
            "HOLD_SCRIPT_ASSIGNMENT_CLASS_OR_KIT",
            "HOLD_SCRIPT_PILOT_PHYSICAL_CONTEXT",
            "HOLD_SCRIPT_CURSOR_INVALID",
            "HOLD_SCRIPT_RESREF_UNREADABLE",
            "HOLD_SCRIPT_ACTOR_CHANGED",
            "HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED",
            "HOLD_SCRIPT_RESREF_CHANGED",
            "HOLD_SCRIPT_CURSOR_CHANGED",
            "R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY",
        )
        self.assertEqual(set(codes), set(D.PROBE_STATUSES))
        for status in codes:
            self.assertIn(status, bridge)

    def test_original_listener_security_fields_still_protected(self):
        for field in (b'"actualBcsExecutionVerified":false',
                      b'"manualEpsActionOriginVerified":false',
                      b'"armAuthorized":false',
                      b'"dispatchAuthorized":false',
                      b'"ordersSent":0',
                      b'"localsWritten":0'):
            self.assertIn(field, self.candidate)

    def test_immutable_original_refuses_drift(self):
        bad = bytearray(self.previous)
        bad[120] ^= 1
        with self.assertRaisesRegex(ValueError, "HOLD_ORIGINAL_CANDIDATE_SHA"):
            D.patch(bytes(bad))

    def test_source_only_never_opens_writable_game_file(self):
        src = (HERE / "BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py").read_text()
        for unsafe in ("subprocess.Popen(", "os.system(", "write_bytes(",
                       "setup-BGXR42.exe", "InfinityLoader.exe"):
            self.assertNotIn(unsafe, src)

    def test_deterministic_candidate(self):
        self.assertEqual(self.candidate, D.compose())
        self.assertGreater(len(self.candidate), len(self.previous))

    def test_status_not_deployment(self):
        self.assertEqual(D.STATUS, "R42_HOLD_REASON_COMPOSED_NO_INSTALL")
        self.assertTrue(D.SCHEMA.endswith("SOURCE_ONLY_V1"))


if __name__ == "__main__":
    unittest.main()
