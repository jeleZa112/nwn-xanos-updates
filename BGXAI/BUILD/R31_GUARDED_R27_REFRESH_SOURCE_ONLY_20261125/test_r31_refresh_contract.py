"""SOURCE-ONLY acceptance contract for the planned BGXR31 R27 refresh.

These tests do not install, mutate a game, or claim the native queue binding works.
"""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CANDIDATE = REPO / "BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua"
LEGACY_SHA = "e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735"
CANDIDATE_SHA = "7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b"
R29_LINE = "~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // BGXR29 fighter quickslot bow-to-sword rule"

class RefreshContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CANDIDATE.read_bytes()
        cls.text = cls.source.decode("utf-8")

    def test_candidate_exact_sha(self):
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), CANDIDATE_SHA)

    def test_same_single_callback_and_existing_observer_identity(self):
        self.assertIn("BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1", self.text)
        self.assertIn("R27.makeListener", self.text)
        self.assertIn("R2_CORE.observe_sprite", self.text)
        self.assertIn("R4_CORE.observe", self.text)
        self.assertEqual(self.text.count("EEex_Action_AddSpriteStartedActionListener("), 1)

    def test_queue_observation_fails_closed(self):
        for marker in ("m_queuedActions", "m_nCount", "queueSnapshotStable",
                       "queue_empty=nil", "eps_queue_empty_verified=false",
                       "action_origin='UNKNOWN'", "manual_command_verified=false"):
            self.assertIn(marker, self.text)

    def test_no_dispatch_or_mutating_game_actions(self):
        for marker in ("ordersSent=0", "localsWritten=0",
                       "dispatchAuthorized=false", "weaponSwitchAuthorized=false",
                       "actionQueueCleared=false"):
            self.assertIn(marker, self.text)
        for forbidden in ("SelectWeaponAbility(", "ClearActions(", "ActionOverride(",
                          "EEex_Action_QueueResponseStringOnAIBase(",
                          "EEex_Action_QueueScriptFileResponseOnAIBase("):
            self.assertNotIn(forbidden, self.text)

    def test_candidate_is_not_the_installed_legacy_module(self):
        self.assertNotEqual(CANDIDATE_SHA, LEGACY_SHA)

    def test_weidu_upgrade_must_append_after_r29_without_reordering(self):
        # Contract test: the deployment plan names the exact observed R29 tail
        # and requires BGXR31 to append, not to make R27 last.
        doc = (ROOT / "README_RU.md").read_text(encoding="utf-8")
        self.assertIn(R29_LINE, doc)
        self.assertIn("BGXR31", doc)
        self.assertIn("must not uninstall, reinstall, or reorder BGXR27 or BGXR29", doc)
        self.assertIn("R29 remains immediately before it", doc)

    def test_origin_and_empty_queue_never_authorize_dispatch(self):
        self.assertIn("queue_empty", self.text)
        self.assertIn("eps_queue_empty_verified=false", self.text)
        self.assertIn("manual_command_verified=false", self.text)
        self.assertIn("safe_to_dispatch=false", self.text)
        self.assertIn("dispatchAuthorized=false", self.text)

if __name__ == "__main__":
    unittest.main()
