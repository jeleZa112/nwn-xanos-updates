#!/usr/bin/env python3
"""Known-error regression gate. Pure read-only validator, never invokes TTS/install.

Usage:
  python known_error_guard.py --self-test
  python known_error_guard.py --policy KNOWN_ERROR_GATES_V1.json --check-zip archive.zip
  python known_error_guard.py --policy KNOWN_ERROR_GATES_V1.json --check-plan plan.json

Exit 0 = checked operations safe for these *limited* known conditions; exit 2 = HOLD.
This program is NOT a second user-facing updater, installer, or audio-quality assessor.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import unittest
import zipfile

KNOWN_SCHEMA = "GLOBAL_KNOWN_ERROR_GATES_V1"


def validate_universal_registry(policy: dict) -> None:
    """Schema-only cross-project audit; NEVER authorizes a task or certifies live behavior.

    This permits manual/non-updater projects to share the same registry without
    pretending that the voice-only check_plan() can approve their operations.
    """
    procedure = policy.get("procedure")
    if not isinstance(procedure, dict) or procedure.get("applies_even_without_updater") is not True:
        raise ValueError("universal process missing or incorrectly requires updater")
    entries = policy.get("project_error_register")
    if not isinstance(entries, list) or not entries:
        raise ValueError("universal project error register missing")
    allowed_types = set(procedure.get("entry_types", []))
    allowed_statuses = set(procedure.get("entry_statuses", []))
    if not allowed_types or not allowed_statuses:
        raise ValueError("registry type/status vocabulary missing")
    already = set()
    for legacy in policy.get("known_errors", []):
        if not isinstance(legacy, dict) or not isinstance(legacy.get("error_id"), str):
            raise ValueError("malformed legacy error ID")
        if legacy["error_id"] in already:
            raise ValueError("duplicate legacy error ID: " + legacy["error_id"])
        already.add(legacy["error_id"])
    required = ("error_id", "project", "type", "status", "discovered_at", "trigger",
                "observed_failure", "cause", "do_not_repeat", "safe_action",
                "closure_condition", "evidence", "enforcement")
    for pos, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"invalid universal error record at {pos}")
        if any(not entry.get(k) for k in required):
            raise ValueError("incomplete universal error record at " + str(pos))
        identifier = entry["error_id"]
        if not isinstance(identifier, str) or not identifier.replace("_", "").isalnum():
            raise ValueError("invalid stable error ID")
        if identifier in already:
            raise ValueError("duplicate error ID: " + identifier)
        already.add(identifier)
        if entry["type"] not in allowed_types or entry["status"] not in allowed_statuses:
            raise ValueError("unknown error class/status for " + identifier)
        if not isinstance(entry["evidence"], list) or not entry["evidence"] or any(
            not isinstance(source, str) or not (source.startswith("/") or source.startswith("https://"))
            for source in entry["evidence"]
        ):
            raise ValueError("bad evidence link for " + identifier)
    # A registry used by chat/document work must include at least one source-backed
    # project without an updater, not only voice-specific technical checks.
    no_updater = {"MARKETPLACE_NSK", "IP_GONCHAROV_DOCUMENTS"}
    if not no_updater.intersection(x["project"] for x in entries):
        raise ValueError("no evidence-backed non-updater coverage")


def load_policy(path: Path) -> dict:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema") != KNOWN_SCHEMA:
        raise ValueError("unsupported known-error registry schema")
    rules = policy["approval_rules"]
    approved = rules["BGVOICE_IWINTRO"]["approved_sound_ids"]
    if len(approved) != 7 or len(set(approved)) != 7:
        raise ValueError("approved audio decisions missing/duplicated")
    if not rules["BGVOICE_MINSC57"].get("preserve_authentic_shout"):
        raise ValueError("MINSC57 authentic shout protection missing")
    validate_universal_registry(policy)
    return policy


def lint_ps1(name: str, data: bytes) -> list[str]:
    """Only detect confirmed Windows PowerShell 5.1 UTF-8 BOM failure mode."""
    if not name.lower().endswith(".ps1"):
        return []
    if data.startswith(b"\xef\xbb\xbf"):
        try:
            data.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            return ["BGVOICE_PS51_UNICODE_INVALID_UTF8:" + name]
        return []
    if data.isascii():
        return []
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ["BGVOICE_PS51_UNICODE_INVALID_UTF8:" + name]
    return ["BGVOICE_PS51_UNICODE_NO_BOM:" + name]


def check_zip(path: Path) -> list[str]:
    problems = []
    with zipfile.ZipFile(path, "r") as z:
        if z.testzip() is not None:
            return ["ARCHIVE_CRC_ERROR"]
        for info in z.infolist():
            if info.is_dir():
                continue
            if info.filename.lower().endswith(".ps1"):
                problems.extend(lint_ps1(info.filename, z.read(info)))
    return problems


def check_plan(plan: dict, policy: dict) -> list[str]:
    """Structured preflight checks of a proposed action; no filesystem writes."""
    bad = []
    action = plan.get("action")
    recognized_actions = {
        "regenerate", "resynthesize", "overwrite", "replace_master", "synthesize_in_place",
        "release", "game_install", "approve_all", "promote", "reuse_as_approved",
        "rerun_stress_models", "reuse_existing_approved", "generate_new_unapproved_candidate",
        "review_candidate", "build_preview", "safe_remix_draft"
    }
    if action not in recognized_actions:
        return ["UNKNOWN_ACTION_FAIL_CLOSED"]
    project = plan.get("project")
    sound_id = plan.get("sound_id")
    rules = policy["approval_rules"]
    if not isinstance(action, str) or not isinstance(project, str):
        return ["UNKNOWN_ACTION_OR_PROJECT_HOLD"]
    destructive = {"regenerate", "resynthesize", "overwrite", "replace_master", "synthesize_in_place"}
    if project == "BGVOICE_IWINTRO":
        approved = set(rules[project]["approved_sound_ids"])
        if sound_id in approved and action in destructive:
            bad.append("BGVOICE_APPROVED_AUDIO_REGEN:" + sound_id)
        if action in {"release", "game_install", "approve_all"}:
            if not plan.get("explicit_human_audio_approval") or not plan.get("explicit_game_install_authorization"):
                bad.append("BGVOICE_TECH_PASS_NOT_AUDIO_PASS")
            # This project has a known 7/19 approval state. No blanket authorization for others.
            if plan.get("release_scope") == "all_19" and set(plan.get("human_approved_sound_ids", [])) != {
                f"IWINTRO_G{i:02}" for i in range(1, 20)
            }:
                bad.append("BGVOICE_12_UNAPPROVED_CUES")
        if action == "rerun_stress_models" and plan.get("model_result_sha256") == next(
            (e["known_result_sha256"] for e in policy["known_errors"] if e["error_id"] == "BGVOICE_R34_STRESS_RECOMPUTE"), None
        ) and not plan.get("source_sha_changed"):
            bad.append("BGVOICE_R34_STRESS_RECOMPUTE")
    if project in {"BGVOICE_MINSC57", "BGVOICE_MINSC48"}:
        rejected = set(rules[project]["rejected_variants"])
        if plan.get("variant") in rejected and action in {"promote", "release", "game_install", "reuse_as_approved"}:
            bad.append("BGVOICE_HUMAN_REJECTED_PROMOTION:" + str(plan.get("variant")))
        if action in {"release", "game_install"} and not (
            plan.get("explicit_human_audio_approval") and plan.get("explicit_game_install_authorization")
        ):
            bad.append("BGVOICE_TECH_PASS_NOT_AUDIO_PASS")
    if action in {"game_install", "replace_master", "release", "approve_all", "promote"}:
        bad.append("EXTERNAL_HUMAN_RELEASE_OR_INSTALL_NOT_VERIFIED_BY_THIS_GUARD")
    if project not in {"BGVOICE_IWINTRO", "BGVOICE_MINSC57", "BGVOICE_MINSC48"}:
        bad.append("UNKNOWN_PROJECT_NOT_VERIFIED")
    return bad


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(Path(__file__).with_name("KNOWN_ERROR_GATES_V1.json"))

    def test_universal_registry_structured(self):
        self.assertGreaterEqual(len(self.policy["project_error_register"]), 6)
        self.assertIsNone(validate_universal_registry(self.policy))

    def test_universal_registry_non_updater_projects(self):
        categories = {e["project"] for e in self.policy["project_error_register"]}
        self.assertIn("MARKETPLACE_NSK", categories)
        self.assertIn("IP_GONCHAROV_DOCUMENTS", categories)

    def test_duplicate_universal_ids_blocked(self):
        import copy
        bad = copy.deepcopy(self.policy)
        bad["project_error_register"][1]["error_id"] = bad["project_error_register"][0]["error_id"]
        with self.assertRaisesRegex(ValueError, "duplicate error ID"):
            validate_universal_registry(bad)

    def test_universal_registry_missing_evidence_blocked(self):
        import copy
        bad = copy.deepcopy(self.policy)
        bad["project_error_register"][0]["evidence"] = []
        with self.assertRaisesRegex(ValueError, "incomplete universal error record"):
            validate_universal_registry(bad)

    def test_registry_does_not_authorize_uncovered_artifacts(self):
        # The existing narrow BGVOICE checker must not silently PASS another project.
        self.assertIn("UNKNOWN_PROJECT_NOT_VERIFIED", check_plan({"project": "MARKETPLACE_NSK", "action": "release"}, self.policy))

    def test_bad_ps51_encoding(self):
        self.assertIn("BGVOICE_PS51_UNICODE_NO_BOM:x.ps1", lint_ps1("x.ps1", "Ошибка 'кавычки'".encode("utf-8")))

    def test_good_ps51_with_bom(self):
        self.assertEqual([], lint_ps1("x.ps1", b"\xef\xbb\xbf" + "Ошибка 'кавычки'".encode("utf-8")))

    def test_ascii_ps51_no_bom_allowed(self):
        self.assertEqual([], lint_ps1("x.ps1", b"Write-Host PASS"))

    def test_invalid_unicode_block(self):
        self.assertTrue(lint_ps1("x.ps1", b"\xff"))

    def test_approved_audio_regen_blocked(self):
        for sound in self.policy["approval_rules"]["BGVOICE_IWINTRO"]["approved_sound_ids"]:
            self.assertTrue(check_plan({"project": "BGVOICE_IWINTRO", "action": "regenerate", "sound_id": sound}, self.policy))

    def test_approved_reuse_not_regen(self):
        self.assertEqual([], check_plan({"project": "BGVOICE_IWINTRO", "action": "reuse_existing_approved", "sound_id": "IWINTRO_G16"}, self.policy))

    def test_minsc57_rejected_C_release_blocked(self):
        self.assertTrue(check_plan({"project": "BGVOICE_MINSC57", "action": "release", "variant": "C"}, self.policy))

    def test_minsc48_previous_V5_blocked(self):
        self.assertTrue(check_plan({"project": "BGVOICE_MINSC48", "action": "reuse_as_approved", "variant": "V5"}, self.policy))

    def test_new_candidate_allowed_not_automatically_approved(self):
        self.assertEqual([], check_plan({"project": "BGVOICE_MINSC48", "action": "generate_new_unapproved_candidate", "variant": "Qwen-new"}, self.policy))

    def test_technically_good_does_not_authorize_install(self):
        self.assertIn("BGVOICE_TECH_PASS_NOT_AUDIO_PASS", check_plan({"project": "BGVOICE_IWINTRO", "action": "game_install", "sound_id": "IWINTRO_G16", "technical_pass": True}, self.policy))

    def test_full19_requires_human_approval_19(self):
        result = check_plan({"project": "BGVOICE_IWINTRO", "action": "release", "release_scope": "all_19", "explicit_human_audio_approval": True, "explicit_game_install_authorization": True, "human_approved_sound_ids": self.policy["approval_rules"]["BGVOICE_IWINTRO"]["approved_sound_ids"]}, self.policy)
        self.assertIn("BGVOICE_12_UNAPPROVED_CUES", result)

    def test_no_repeat_saved_stress(self):
        result = check_plan({"project": "BGVOICE_IWINTRO", "action": "rerun_stress_models", "model_result_sha256": "d361d10e3851202e8c231d54f851e044052a9ee0fc79569ce4023c3ac652da47", "source_sha_changed": False}, self.policy)
        self.assertIn("BGVOICE_R34_STRESS_RECOMPUTE", result)

    def test_changed_sources_allow_focused_stress_check(self):
        result = check_plan({"project": "BGVOICE_IWINTRO", "action": "rerun_stress_models", "model_result_sha256": "d361d10e3851202e8c231d54f851e044052a9ee0fc79569ce4023c3ac652da47", "source_sha_changed": True}, self.policy)
        self.assertFalse(result)

    def test_unknown_action_fail_closed(self):
        self.assertEqual(["UNKNOWN_ACTION_FAIL_CLOSED"], check_plan({"project":"BGVOICE_IWINTRO", "action":"do_anything"}, self.policy))

    def test_install_even_with_fake_flags_still_hold(self):
        plan = {"project": "BGVOICE_IWINTRO", "action": "game_install", "sound_id": "IWINTRO_G16", "explicit_human_audio_approval": True, "explicit_game_install_authorization": True}
        self.assertIn("EXTERNAL_HUMAN_RELEASE_OR_INSTALL_NOT_VERIFIED_BY_THIS_GUARD", check_plan(plan, self.policy))

    def test_release_even_with_fake_flags_still_hold(self):
        plan = {"project": "BGVOICE_IWINTRO", "action": "release", "release_scope": "single", "sound_id": "IWINTRO_G16", "explicit_human_audio_approval": True, "explicit_game_install_authorization": True}
        self.assertIn("EXTERNAL_HUMAN_RELEASE_OR_INSTALL_NOT_VERIFIED_BY_THIS_GUARD", check_plan(plan, self.policy))

    def test_unknown_project_fail_closed(self):
        self.assertIn("UNKNOWN_PROJECT_NOT_VERIFIED", check_plan({"project": "BGXAI", "action": "game_install"}, self.policy))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=Path(__file__).with_name("KNOWN_ERROR_GATES_V1.json"))
    parser.add_argument("--check-zip", type=Path)
    parser.add_argument("--check-plan", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            return 0 if result.wasSuccessful() else 2
        policy = load_policy(args.policy)
        if (args.check_zip is None) == (args.check_plan is None):
            parser.error("pass exactly one of --check-zip or --check-plan (or --self-test)")
        problems = check_zip(args.check_zip) if args.check_zip is not None else check_plan(json.loads(args.check_plan.read_text(encoding="utf-8")), policy)
        print(json.dumps({"status": "HOLD_KNOWN_ERROR" if problems else "PASS_KNOWN_ERROR_CHECKS_ONLY", "problems": problems, "audio_quality_verified": False, "game_modified": False}, ensure_ascii=False))
        return 2 if problems else 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as e:
        print(json.dumps({"status": "HOLD_GUARD_INPUT", "error": str(e)[:240]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())