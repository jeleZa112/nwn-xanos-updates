# coding: utf-8
"""BG_EET_RU V113: OFFLINE-ONLY proof gate for attributing a weapon to one combat log row.

This module never imports game, modifies a save, hooks EEex, rewrites UI/TLK,
or creates an updater. Intent: prevent false weapon-to-miss attribution.

No current engine source is known to supply the required per-roll common ID.
Any such ID below is SYNTHETIC ONLY, for proving the matching algorithm is safe.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

def _safe_token(row: dict[str, Any]) -> str | None:
    """Only an engine-origin, nonempty string correlation key is eligible.

    Never fall back to timestamps, actor names, attack order, or inventory.
    """
    if row.get("key_provenance") != "ENGINE_PER_ROLL_AT_LOG_CREATION":
        return None
    key = row.get("roll_instance_id")
    if not isinstance(key, str) or not key or len(key) > 128:
        return None
    return key


def decide(log_row: dict[str, Any], damage_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Return exact matched weapon ONLY when shared immutable per-roll evidence exists.

    Log row must refer to the engine-created roll ID and a specific row ID,
    outcome must be explicit, damage events must contain exact same engine roll ID.
    A miss needs a separately verified per-roll observer: hit-only context cannot
    prove the miss weapon. Weapon identification in user's inventory is unknown.
    """
    base = {"verified": False, "label_weapon": False, "label_launcher": False,
            "reason": "NO_ENGINE_ROW_JOIN_KEY", "weapon_resref": None, "launcher_resref": None}
    if not isinstance(log_row, dict) or not isinstance(damage_events, list):
        return {**base, "reason": "INVALID_INPUT"}
    key = _safe_token(log_row)
    if (key is None or log_row.get("journal_row_id_provenance") != "ENGINE_LOG_APPEND_IMMUTABLE"
            or not isinstance(log_row.get("journal_row_id"), int)
            or isinstance(log_row.get("journal_row_id"), bool)
            or log_row["journal_row_id"] < 0):
        return base
    if log_row.get("outcome") not in {"HIT", "MISS"}:
        return {**base, "reason": "UNKNOWN_ROLL_OUTCOME"}
    if len(damage_events) > 100:
        return {**base, "reason": "TOO_MANY_EVENTS_HOLD"}
    matches = [e for e in damage_events if isinstance(e, dict) and _safe_token(e) == key]
    if len(matches) != 1:
        return {**base, "reason": "AMBIGUOUS_OR_ABSENT_DAMAGE_EVENT"}
    event = matches[0]
    # Only a verified per-roll observer *including miss path* can qualify for MISS.
    if log_row["outcome"] == "MISS" and event.get("source_hook") != "VERIFIED_EACH_ROLL_INCLUDING_MISS":
        return {**base, "reason": "MISS_NOT_OBSERVED_BY_DAMAGE_HOOK"}
    if log_row["outcome"] == "HIT" and event.get("source_hook") not in {"VERIFIED_EACH_ROLL_INCLUDING_MISS", "BASE_DAMAGE_ON_HIT"}:
        return {**base, "reason": "UNKNOWN_HIT_HOOK"}
    if event.get("outcome") != log_row["outcome"]:
        return {**base, "reason": "ROLL_OUTCOME_CONFLICT"}
    for field in ("attacker_id", "target_id"):
        if event.get(field) is None or log_row.get(field) is None or event[field] != log_row[field]:
            return {**base, "reason": "ACTOR_OR_TARGET_MISMATCH"}
    weapon = event.get("weapon_resref")
    launcher = event.get("launcher_resref")
    if not isinstance(weapon, str) or not weapon or len(weapon) > 8:
        return {**base, "reason": "NO_EXACT_WEAPON_RESREF"}
    if launcher is not None and (not isinstance(launcher, str) or not launcher or len(launcher) > 8):
        return {**base, "reason": "INVALID_LAUNCHER_RESREF"}
    return {"verified": True, "label_weapon": True, "label_launcher": bool(launcher),
            "reason": "SYNTHETIC_ENGINE_KEY_CONSISTENT" if event.get("synthetic") else "COMMON_ENGINE_ROLL_ID_VERIFIED",
            "weapon_resref": weapon, "launcher_resref": launcher}


def decide_batch(rows: list[dict[str, Any]], damage_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reject duplicate row IDs or roll IDs across the *entire* candidate batch.

    A successful individual join is NOT proof of one-to-one attribution if the
    same roll ID or log-message ID appears in multiple source rows.
    """
    if not isinstance(rows, list) or len(rows) > 100:
        return [{"verified": False, "label_weapon": False, "reason": "BAD_BATCH"}]
    keys = [_safe_token(row) for row in rows]
    rowids = [row.get("journal_row_id") if isinstance(row, dict) else None for row in rows]
    from collections import Counter
    keyfreq = Counter(x for x in keys if x is not None)
    rowfreq = Counter(x for x in rowids if isinstance(x, int))
    result = []
    for row, key, rid in zip(rows, keys, rowids):
        if key is not None and keyfreq[key] > 1:
            result.append({"verified": False, "label_weapon": False, "reason": "DUPLICATE_ROLL_IN_LOG_BATCH"})
        elif isinstance(rid, int) and rowfreq[rid] > 1:
            result.append({"verified": False, "label_weapon": False, "reason": "DUPLICATE_ROW_ID_IN_LOG_BATCH"})
        else:
            result.append(decide(row, damage_events))
    return result


def selftest() -> dict[str, Any]:
    event = {"synthetic": True, "key_provenance": "ENGINE_PER_ROLL_AT_LOG_CREATION",
             "roll_instance_id": "tick-independent-test-roll-0001", "source_hook": "BASE_DAMAGE_ON_HIT",
             "attacker_id": 5, "target_id": 8, "outcome": "HIT",
             "weapon_resref": "AROW01", "launcher_resref": "BOW05"}
    row = {"key_provenance": "ENGINE_PER_ROLL_AT_LOG_CREATION",
           "roll_instance_id": event["roll_instance_id"], "journal_row_id": 13,
           "journal_row_id_provenance": "ENGINE_LOG_APPEND_IMMUTABLE",
           "attacker_id": 5, "target_id": 8, "outcome": "HIT"}
    cases: dict[str, dict[str, Any]] = {
        "synthetic_valid_hit": decide(row, [event]),
        "miss_from_damage_hook_rejected": decide({**row, "outcome": "MISS"}, [{**event, "outcome": "MISS"}]),
        "same_actor_different_roll_rejected": decide(row, [{**event, "roll_instance_id": "other"}]),
        "duplicate_roll_events_rejected": decide(row, [event, event]),
        "actor_only_never_sufficient": decide({"attacker_id": 5, "target_id": 8, "outcome": "HIT", "journal_row_id": 13}, [event]),
        "timestamp_order_never_sufficient": decide({**row, "key_provenance": "TIMESTAMP_SORT"}, [event]),
        "dual_wield_wrong_weapon_rejected": decide({**row, "roll_instance_id": "left-hand"}, [event]),
        "projectile_in_flight_switch_rejected": decide({**row, "roll_instance_id": "later-roll"}, [event]),
        "wrong_target_rejected": decide({**row, "target_id": 99}, [event]),
        "no_row_id_rejected": decide({k: v for k, v in row.items() if k != "journal_row_id"}, [event]),
        "ui_row_index_is_not_stable_id": decide({**row, "journal_row_id_provenance": "UI_VISIBLE_ROW_INDEX"}, [event]),
        "outcome_conflict_rejected": decide(row, [{**event, "outcome": "MISS"}]),
        "partial_weapon_rejected": decide(row, [{**event, "weapon_resref": None}]),
        "miss_with_hypothetical_per_roll_source": decide(
            {**row, "outcome": "MISS"}, [{**event, "source_hook": "VERIFIED_EACH_ROLL_INCLUDING_MISS", "outcome": "MISS"}]),
    }
    assert cases["synthetic_valid_hit"]["verified"]
    duplicate_roll_in_log = decide_batch([row, {**row, "journal_row_id": 14}], [event])
    assert all(x["reason"] == "DUPLICATE_ROLL_IN_LOG_BATCH" for x in duplicate_roll_in_log)
    duplicate_row_id = decide_batch([row, {**row, "roll_instance_id": "another"}], [event])
    assert all(x["reason"] == "DUPLICATE_ROW_ID_IN_LOG_BATCH" for x in duplicate_row_id)
    cases["duplicate_roll_in_log_batch_rejected"] = {"verified": False, "reason": duplicate_roll_in_log[0]["reason"]}
    cases["duplicate_row_id_in_log_batch_rejected"] = {"verified": False, "reason": duplicate_row_id[0]["reason"]}
    assert cases["miss_with_hypothetical_per_roll_source"]["verified"]
    assert all(not obj["verified"] for name, obj in cases.items() if name not in (
        "synthetic_valid_hit", "miss_with_hypothetical_per_roll_source")), cases
    return {"status": "V113_OFFLINE_SYNTHETIC_TESTS_PASS", "case_count": len(cases),
            "case_results": {name: {"verified": v["verified"], "reason": v["reason"]}
                             for name, v in cases.items()},
            "any_gameplay_verified": False, "game_files_written": 0}


def audit_previous_zip(path: Path) -> dict[str, Any]:
    import zipfile
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert len(names) == len(set(names))
        v112 = json.loads(z.read("56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json"))
        v111 = json.loads(z.read("55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json"))
        v108 = json.loads(z.read("54_V108_NATIVE_ITEM_RESREF_PILOT.json"))
    samples = v108.get("console_evidence", {}).get("samples", [])
    evidence = {
        "input_basename": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_crc_pass": True,
        "reported_v112_status": v112.get("status"),
        "v108_damage_events": len(samples),
        "contains_full_per_roll_engine_token": any("roll_instance_id=" in s for s in samples),
        "contains_engine_journal_row_id": any("journal_row_id=" in s for s in samples),
        "v111_all_three_item_names": v111.get("resolved_identified_names") == 3,
        "name_provenance": "ITM_TLK_RESOURCE_NOT_RUNTIME_DISPLAY_NAME",
        "miss_weapon_verified": False,
        "combat_log_row_weapon_verified": False,
        "safe_decision": "NO_WEAPON_ROW_LABELS_PERMITTED_WITH_AVAILABLE_EVENTS",
        "game_files_written": 0,
    }
    assert evidence["v111_all_three_item_names"]
    assert not evidence["contains_full_per_roll_engine_token"]
    assert not evidence["contains_engine_journal_row_id"]
    return evidence


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--prior-zip", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    record = {"schema": "BG_EET_RU_V113_OFFLINE_JOIN_SAFETY_GATE_V1", "tests": selftest(),
              "report_class": "SOURCE_AND_SYNTHETIC_ONLY_NOT_WINDOWS_LIVE"}
    if args.prior_zip:
        record["last_windows_evidence"] = audit_previous_zip(args.prior_zip)
    if args.report:
        args.report.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print("V113",record["tests"]["status"], "cases", record["tests"]["case_count"])
    if args.prior_zip:
        print("V113_OLD_CAPTURE", record["last_windows_evidence"]["safe_decision"])

if __name__ == "__main__":
    main()