# coding: utf-8
"""V114: non-invasive source-evidence evaluator. Does not load EEex or edit EET.

References: Bubb13/EEex PR #136 (open, unmerged on 2026-11-23),
PR patch files EEex_Sprite_Patch.lua and InfinityLoader.db. Source facts are
pinned as a transparent metadata fixture, not represented as runtime behavior.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import argparse, json
from pathlib import Path

@dataclass(frozen=True)
class HookSite:
    label: str
    stage: str
    provides: tuple[str,...]
    id_for_attack_roll: bool = False
    id_for_journal_row: bool = False
    source: str = ""

SOURCE = {
  "name": "Bubb13/EEex PR #136: New Engine Feature EEex_AttackOnce",
  "url": "https://github.com/Bubb13/EEex/pull/136",
  "pr_number": 136,
  "pr_state_as_checked_2026_11_23": "open_unmerged",
  "pr_head_sha": "67766626c50abcac302f98a777bff5d9587cb765",
  "compatibility": "x64 proposed upstream PR, not installed current EEex",
  "notes": "PR changes Attack() semantics by adding AttackOnce and can change roll/damage/ammo; never deploy it as passive logger.",
}
SITES = (
    HookSite("Hook-CGameSprite::Swing()-AttackOnceHitCall-1", "BEFORE_HIT_CALL",
             ("attacker_candidate_rbx", "target_candidate_r15", "resolved_weapon_stack_r8", "weapon_ability_r9"),
             source="PR136: EEex_Sprite_Patch.lua checkAttackOnceShouldEndAction()"),
    HookSite("Hook-CGameSprite::Swing()-AttackOnceHitCall-2", "BEFORE_HIT_CALL",
             ("attacker_candidate_rbx", "target_candidate_r15", "resolved_weapon_stack_r8", "weapon_ability_r9"),
             source="PR136: EEex_Sprite_Patch.lua checkAttackOnceShouldEndAction()"),
    HookSite("Hook-CGameSprite::Hit()-AttackOnceBaseAttackRoll", "RAW_D20",
             ("attacker_candidate_rbx", "target_candidate_r14", "raw_d20_di"),
             source="PR136: EEex_Sprite_Patch.lua HookBeforeRestoreWithLabels"),
    HookSite("Hook-CGameSprite::Hit()-FormatRollCall", "FORMAT_ROLL_CALL",
             ("native_last_roll_byte",),
             source="pinned EEex_Sprite_Patch.lua + InfinityLoader.db"),
)

# Important: two labels target the SAME PATTERN but different relative offsets!
# This is not permission to assume the bytes are a unique per-attack key.
LOADER_SIGNATURES = {
  "Hit()-AttackOnceBaseAttackRoll": {"pattern": "488D4DD08D7801", "operations_add": 7, "source": "PR136 InfinityLoader.db"},
  "Hit()-FormatRollCall": {"pattern": "488D4DD08D7801", "operations_add": 18, "source": "pinned mainline InfinityLoader.db"},
}

REQUIRED = (
  "x64_source_roll_site", "per_roll_event_invoked_for_hit_and_miss",
  "same_roll_weapon_launcher_snapshot", "roll_event_has_stable_attacker_target",
  "journal_append_callback_with_immutable_row_id", "common_engine_generated_roll_instance_id",
  "journal_does_not_mutate_for_capture", "no_attack_behavior_change",
  "exact_installed_build_sha_preflight", "explicit_user_consent_for_native_install",
)


def audit(caps: dict[str,bool]) -> dict:
    """Only actual verified runtime-capability claims may authorize a test install.

    Source-level signatures alone are categorically insufficient for runtime.
    """
    if not isinstance(caps,dict) or set(caps)-set(REQUIRED):
        return {"status":"INVALID_CAPABILITY_INPUT_HOLD", "proceed_to_install":False}
    typed={k: caps.get(k) is True for k in REQUIRED}
    all_true=all(typed.values())
    return {
      "status": "V114_GUARDED_EXPERIMENT_RESEARCH_READY_NOT_INSTALLED" if all_true else
                "V114_X64_ROLL_CALLSITE_FOUND_JOURNAL_JOIN_HOLD",
      "proceed_to_install": False, # source-only tool has no install functionality, ever
      "source_review_gates": typed,
      "missing_gates": [k for k,v in typed.items() if not v],
      "risk_flags": [
          "UPSTREAM_PR_UNMERGED", "ATTACKONCE_PR_CHANGES_ATTACK_SEMANTICS",
          "RAW_D20_SITE_HAS_NO_VERIFIED_CITEM_RESREF",
          "BEFORE_HIT_CALL_SITE_NOT_PROVEN_ONE_CALLBACK_PER_ROLL",
          "NO_ENGINE_JOURNAL_APPEND_HOOK_VERIFIED",
          "FORMAT_ROLL_CALL_IS_NOT_JOURNAL_APPEND",
          "SHARED_SIGNATURE_DIFFERENT_OFFSETS_NOT_EVENT_IDENTITY",
          "NO_GAME_BUILD_SHA_MATCH_FOR_PR136",
      ],
    }


def selftest():
    src={"x64_source_roll_site":True}
    baseline=audit(src)
    assert baseline["status"]=="V114_X64_ROLL_CALLSITE_FOUND_JOURNAL_JOIN_HOLD"
    assert len(baseline["missing_gates"])==len(REQUIRED)-1
    cases={
      "only_roll_site":src,
      "all_source_hints_but_no_row_append": {**src,"per_roll_event_invoked_for_hit_and_miss":True,
            "same_roll_weapon_launcher_snapshot":True,"roll_event_has_stable_attacker_target":True},
      "row_append_but_no_engine_roll_id": {k:True for k in REQUIRED if k!="common_engine_generated_roll_instance_id"},
      "unknown_build": {k:True for k in REQUIRED if k!="exact_installed_build_sha_preflight"},
      "no_permission": {k:True for k in REQUIRED if k!="explicit_user_consent_for_native_install"},
      "unsafe_attack_mutation": {k:True for k in REQUIRED if k!="no_attack_behavior_change"},
      "no_miss_coverage": {k:True for k in REQUIRED if k!="per_roll_event_invoked_for_hit_and_miss"},
      "all_ten_claimed_only_synthetic": {k:True for k in REQUIRED},
    }
    for name, caps in cases.items():
        r=audit(caps)
        assert not r["proceed_to_install"],name
        assert r["status"]==("V114_GUARDED_EXPERIMENT_RESEARCH_READY_NOT_INSTALLED"
                               if name=="all_ten_claimed_only_synthetic" else
                               "V114_X64_ROLL_CALLSITE_FOUND_JOURNAL_JOIN_HOLD"),name
    assert audit({"x64_source_roll_site":"true"})["missing_gates"]==list(REQUIRED)
    assert audit({"unexpected_field":True})["status"]=="INVALID_CAPABILITY_INPUT_HOLD"
    assert len([x for x in SITES if x.stage=="BEFORE_HIT_CALL"])==2
    assert len([x for x in SITES if x.stage=="RAW_D20"])==1
    assert not any(site.id_for_attack_roll or site.id_for_journal_row for site in SITES)
    assert LOADER_SIGNATURES["Hit()-AttackOnceBaseAttackRoll"]["pattern"]==LOADER_SIGNATURES["Hit()-FormatRollCall"]["pattern"]
    assert LOADER_SIGNATURES["Hit()-FormatRollCall"]["operations_add"]-LOADER_SIGNATURES["Hit()-AttackOnceBaseAttackRoll"]["operations_add"]==11
    return {"status":"V114_SOURCE_CONTRACT_SELFTEST_PASS", "scenario_count":len(cases)+6,
            "all_install_paths_disabled":True}


def report():
    return {
      "schema":"BG_EET_RU_V114_X64_ATTACK_ROLL_SOURCE_RESEARCH_V1",
      "phase":"SOURCE_ONLY_NO_GAME_CHANGE", "source":SOURCE,
      "hook_candidates":[asdict(x) for x in SITES],
      "loader_signatures":LOADER_SIGNATURES,
      "requirements_before_guarded_install":list(REQUIRED),
      "gating":audit({"x64_source_roll_site":True}),
      "selftest":selftest(),
      "compatibility_status":"PR_SOURCE_PROPOSAL_NOT_CONFIRMED_AGAINST_USER_EEEX_DLL",
      "journal_row_hook":"NOT_IDENTIFIED_IN_DOCUMENTED_EEEX_LUA_APIS",
      "recommended_next_research":"Identify source-level combat journal append callback and prove engine-owned immutable attack-roll token shared with Hit(); do NOT install/modify a native hook based on PR136.",
      "last_verified_live_baseline":"V112 Windows JOIN_HOLD; V108 weapon+launcher and V111 item names preserved",
      "game_files_written":0,
      "updater_modified":False,
      "new_hook_installed":False,
      "BGXAI_changed":False,
      "BG_Voice_RU_changed":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    r=report()
    if args.report:
        args.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(r["selftest"]["status"], "scenarios", r["selftest"]["scenario_count"])
    print(r["gating"]["status"], "missing", len(r["gating"]["missing_gates"]))

if __name__=="__main__":main()