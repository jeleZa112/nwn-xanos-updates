"""R42 source-only adversarial checks. No game, installer, action or listener calls."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
MODFILE = HERE / "BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py"
spec = importlib.util.spec_from_file_location("r42_existing_one_callback", MODFILE)
R42 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R42)


class R42Reuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = R42.verified(R42.R38, R42.R38_BYTES, R42.R38_BLOB)
        cls.bridge = R42.verified(R42.R39, R42.R39_BYTES, R42.R39_BLOB)
        cls.composed = R42.compose(cls.old, cls.bridge)

    def test_existing_r38_exact_immutable_sha(self):
        self.assertEqual(len(self.old), 78927)
        self.assertEqual(hashlib.sha256(self.old).hexdigest(), R42.R38_SHA)

    def test_existing_r39_embedded_identically_once(self):
        self.assertIn(self.bridge, self.composed)
        self.assertEqual(self.composed.count(self.bridge), 1)
        self.assertEqual(R42.gitblob(self.bridge), R42.R39_BLOB)

    def test_one_existing_action_listener_only(self):
        self.assertEqual(self.composed.count(R42.LISTENER_CALL.encode()), 1)
        self.assertEqual(self.composed.count(b"EEex_Action_AddSpriteStartedActionListener("), 0)

    def test_one_extra_readonly_log_tag_only(self):
        self.assertEqual(self.composed.count(b"[BGXBCS]"), 1)
        self.assertIn(b"probeInstalledScriptAssignments()", self.composed)

    def test_existing_four_streams_preserved(self):
        for tag in (b"[BGXR27]", b"[BGXR37]", b"[BGXINV3]", b"[BGXID]"):
            self.assertEqual(self.composed.count(tag), self.old.count(tag))

    def test_single_candidate_pilot_jagan_only(self):
        for gate in (
            b"p==1",
            b"RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM",
            b"R27.r42Once=true",
            b"R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY",
            b"pilotPhysicalSnapshotDoubleMatched",
            b"row.portraitActorId==id",
            b"row.scriptLevelResrefs[4]",
        ):
            self.assertIn(gate, self.composed)

    def test_explicit_not_authorized_in_one_shot_json(self):
        for flag in (
            b'"actualBcsExecutionVerified":false',
            b'"manualEpsActionOriginVerified":false',
            b'"armAuthorized":false',
            b'"dispatchAuthorized":false',
            b'"ordersSent":0',
            b'"localsWritten":0',
        ):
            self.assertIn(flag, self.composed)

    def test_no_active_game_outputs(self):
        outcome = R42.source_report()
        self.assertEqual(outcome["status"], R42.READONLY_STATUS)
        self.assertFalse(outcome["nativeGameInstalled"])
        self.assertFalse(outcome["gameModified"])
        self.assertFalse(outcome["installAuthorized"])
        self.assertFalse(outcome["classScriptResrefAtLiveJaganVerified"])
        self.assertTrue(outcome["onlyExistingActionStartedListener"])

    def test_reject_modified_r38_sha(self):
        fake = bytearray(self.old)
        fake[12] ^= 1
        with self.assertRaisesRegex(ValueError, "HOLD_R38_SHA"):
            R42.compose(bytes(fake), self.bridge)

    def test_reject_modified_r39_sha(self):
        fake = bytearray(self.bridge)
        fake[12] ^= 1
        with self.assertRaisesRegex(ValueError, "HOLD_R39_SHA"):
            R42.compose(self.old, bytes(fake))

    def test_reject_truncated_r38(self):
        with self.assertRaisesRegex(ValueError, "HOLD_R38_INPUT"):
            R42.compose(self.old[:-1], self.bridge)

    def test_reject_truncated_r39(self):
        with self.assertRaisesRegex(ValueError, "HOLD_R39_INPUT"):
            R42.compose(self.old, self.bridge[:-1])

    def test_anchor_duplication_fails(self):
        with self.assertRaisesRegex(ValueError, "HOLD_NONUNIQUE_ANCHOR"):
            R42.exact_replace("A A", "A", "B")

    def test_source_has_no_temp_game_write_or_loader(self):
        s = MODFILE.read_text(encoding="utf-8")
        self.assertNotIn("os.system(", s)
        self.assertNotIn("subprocess.Popen(", s)
        self.assertNotIn("urllib.request", s)
        self.assertNotIn("write_bytes(", s)

    def test_only_new_emitter_is_bounded(self):
        self.assertEqual(self.composed.count(b"r42Once~=true"), 1)
        self.assertEqual(self.composed.count(b"R27.r42Once=true"), 1)

    def test_no_action_issued_by_new_delta(self):
        delta = R42.CALL_DELTA + R42.EMIT_DELTA
        for prohibited in ("XEquipItem(", "SetGlobal(", "ClearActions(",
                           "FillSlot(", "ActionOverride(", "Attack(",
                           "SelectWeaponAbility(", "EEex_Action_AddSpriteStartedActionListener("):
            self.assertNotIn(prohibited, delta)

    def test_readonly_handler_does_not_infer_current_name_from_historical_bddefai(self):
        delta = R42.CALL_DELTA + R42.EMIT_DELTA
        self.assertNotIn("BDDEFAI", delta)
        self.assertNotIn("PRIEST1", delta)
        self.assertIn("row.scriptLevelResrefs[4]", delta)

    def test_candidate_sha_repeatable(self):
        one = hashlib.sha256(self.composed).hexdigest()
        two = hashlib.sha256(R42.compose(self.old, self.bridge)).hexdigest()
        self.assertEqual(one, two)

    def test_existing_exact_physical_callback_unmodified(self):
        self.assertIn(b"-- BEGIN BGXAI_IDV1_CAPTURE", self.old)
        self.assertIn(b"-- END BGXAI_IDV1_CAPTURE", self.composed)
        self.assertIn(b"R27.captureInventoryV3", self.composed)


if __name__ == "__main__":
    unittest.main()
