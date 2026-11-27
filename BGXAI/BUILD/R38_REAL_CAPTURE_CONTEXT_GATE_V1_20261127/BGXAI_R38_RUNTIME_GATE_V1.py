#!/usr/bin/env python3
"""Source-only audit of existing R38 four-stream telemetry.

Never changes game files, writes Lua/BCS, arms any actor or dispatches orders.
A same-actor live observation is not saved-GAM identity, safe idle, or approval.
Raw actor IDs and personal log paths are deliberately absent from the result.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

PREFIXES = ("[BGXR27] ", "[BGXR37] ", "[BGXINV3] ", "[BGXID] ")
SCHEMAS = (
    "BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",
    "BGXAI_R37_R33_R36_SINGLE_LISTENER_SOURCE_V1",
    "BGXAI_BACKPACK16_R37_SINGLE_LISTENER_SOURCE_V1",
    "BGXAI_XEQUIP_IDENTITY_RO_V1",
)
TYPES = ("R27_SINGLE_CALLBACK", "ADVISORY_CONTEXT",
         "BACKPACK16_ADVISORY", "IDENTITY_ADVISORY")
MATCH = "RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM"
OTHER = "HOLD_WRONG_PORTRAIT_CONTEXT"
RESULT_SCHEMA = "BGXAI_R38_REAL_CAPTURE_CONTEXT_GATE_V1"
# BG(2)EE IESDP: action 23 = MoveToPoint, not idle. No other action
# is whitelisted as idle; even NoAction does not establish manual/EPS ownership.
KNOWN_ACTIVE = {23: "MoveToPoint"}
MAX_LOG_BYTES = 64_000_000


class Hold(ValueError):
    pass


def _int(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _read_events(lines):
    records = [{} for _ in PREFIXES]
    sessions = [0] * len(PREFIXES)
    observed = 0
    for line in lines:
        if len(line) > 500_000:
            raise Hold("HOLD_OVERSIZE_LOG_LINE")
        found = [(i, s) for i, s in enumerate(PREFIXES) if s in line]
        if not found:
            continue
        if len(found) != 1:
            raise Hold("HOLD_MULTIPLE_R38_TAGS_ONE_LINE")
        i, tag = found[0]
        try:
            record = json.loads(line.split(tag, 1)[1].strip())
        except (ValueError, UnicodeError) as exc:
            raise Hold("HOLD_INVALID_R38_JSON") from exc
        if type(record) is not dict or record.get("schema") != SCHEMAS[i]:
            raise Hold("HOLD_R38_SCHEMA_DRIFT")
        if record.get("type") == "SESSION":
            sessions[i] += 1
            continue
        if record.get("type") != TYPES[i]:
            raise Hold("HOLD_WRONG_R38_RECORD_TYPE")
        n, party = record.get("seq"), record.get("partyIndex")
        if not _int(n, 1, 64) or not _int(party, 0, 5):
            raise Hold("HOLD_INVALID_SEQ_OR_PARTY")
        if n in records[i]:
            raise Hold("HOLD_DUPLICATE_SEQ")
        if (record.get("readOnly") is not True or
            record.get("ordersSent") != 0 or
            record.get("dispatchAuthorized") is not False):
            raise Hold("HOLD_RECORD_NOT_PASSIVE")
        if i == 3 and (record.get("armAuthorized") is not False or
                       record.get("localsWritten") != 0 or
                       record.get("safeActionBoundaryVerified") is not False):
            raise Hold("HOLD_IDENTITY_RECORD_NOT_PASSIVE")
        records[i][n] = record
        observed += 1
    if sessions != [1, 1, 1, 0]:
        raise Hold("HOLD_SESSION_MARKERS_UNEXPECTED")
    seq = set(records[0])
    if not seq or any(set(stream) != seq for stream in records[1:]):
        raise Hold("HOLD_FOUR_STREAM_SEQ_MISMATCH")
    if observed > 64 * 4:
        raise Hold("HOLD_EXCESS_R38_EVENTS")
    for n in seq:
        if len({s[n]["partyIndex"] for s in records}) != 1:
            raise Hold("HOLD_PARTY_MISMATCH_PER_EVENT")
    return records, sorted(seq)


def audit_lines(lines):
    """Returns a sanitized decision: NEVER an authorization to act."""
    try:
        streams, seq = _read_events(lines)
        candidates = []
        others = []
        for n in seq:
            r27 = streams[0][n]
            rid = streams[3][n]
            party, actor = r27["partyIndex"], r27.get("actor")
            if not _int(actor, 1, 2147483647):
                raise Hold("HOLD_INVALID_R27_RUNTIME_ACTOR")
            if rid["status"] == MATCH:
                if party != 1:
                    raise Hold("HOLD_JAGAN_STATUS_FOR_WRONG_PARTY")
                candidates.append((n, actor, r27))
            elif rid["status"] == OTHER:
                if party == 1:
                    raise Hold("HOLD_EXPECTED_JAGAN_REJECTED")
                others.append((n, actor, r27))
            else:
                raise Hold("HOLD_UNKNOWN_IDENTITY_STATUS")
        if not candidates:
            raise Hold("HOLD_NO_REAL_JAGAN_MATCH")
        actor_ids = {actor for _, actor, _ in candidates}
        other_ids = {actor for _, actor, _ in others}
        if len(actor_ids) != 1 or actor_ids & other_ids:
            raise Hold("HOLD_ACTOR_CHANGED_OR_COLLIDED")
        active_movement = sum(r.get("actionRaw") in KNOWN_ACTIVE for _, _, r in candidates)
        queued = sum(_int(r.get("queuedActionsRaw"), 1, 512) for _, _, r in candidates)
        if any(not _int(r.get("queuedActionsRaw"), 0, 512) for _, _, r in candidates):
            raise Hold("HOLD_QUEUE_RAW_UNREADABLE")
        if any(r.get("actionOriginVerified") is not False or
               r.get("manualEpsQueueVerified") is not False for _, _, r in candidates):
            raise Hold("HOLD_UNEXPECTED_ORIGIN_CONTRACT")
        return {
            "schema": RESULT_SCHEMA,
            "status": "HOLD_SAFE_IDLE_AND_SESSION_AUTHENTICATION_NOT_PROVEN",
            "source": "EXISTING_R38_REAL_GAME_CONSOLE_READONLY",
            "alignedEvents": len(seq),
            "jaganMatchingEvents": len(candidates),
            "otherActorFilteredEvents": len(others),
            "sameRuntimeActorAcrossJaganEvents": True,
            "noOtherActorUsesJaganRuntimeId": True,
            "moveToPointObservedInJaganEvents": active_movement,
            "nonemptyQueueObservedInJaganEvents": queued,
            "zeroQueueIsIdleProof": False,
            "eventStartIsIdleProof": False,
            "actorIdentityWithinCaptureCorroborated": True,
            "savedGAMSessionIdentityVerified": False,
            "classKitItmUsabilityVerified": False,
            "manualEpsActionOriginVerified": False,
            "safeActionBoundaryVerified": False,
            "sourceAndTargetInventoryObservedReadOnly": True,
            "gameplayEquipVerified": False,
            "readOnly": True,
            "ordersSent": 0,
            "armAuthorized": False,
            "dispatchAuthorized": False,
            "gameModified": False,
        }
    except (Hold, KeyError, TypeError, IndexError) as exc:
        code = str(exc) if isinstance(exc, Hold) else "HOLD_INCOMPLETE_OR_MALFORMED_RECORD"
        return {"schema": RESULT_SCHEMA, "status": "HOLD_UNTRUSTED_R38_CAPTURE",
                "reason": code, "readOnly": True, "ordersSent": 0,
                "armAuthorized": False, "dispatchAuthorized": False,
                "gameModified": False}


def audit_file(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_LOG_BYTES:
        raise Hold("HOLD_MISSING_OR_OVERSIZE_LOG")
    with path.open("r", encoding="utf-8-sig", errors="strict") as inp:
        return audit_lines(inp)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--console-log", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        result = audit_file(a.console_log)
    except (OSError, UnicodeError, Hold) as exc:
        result = {"schema": RESULT_SCHEMA,
                  "status": "HOLD_UNTRUSTED_R38_CAPTURE",
                  "reason": str(exc) if isinstance(exc, Hold) else "HOLD_UNREADABLE_LOG",
                  "readOnly": True, "ordersSent": 0, "armAuthorized": False,
                  "dispatchAuthorized": False, "gameModified": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "HOLD_SAFE_IDLE_AND_SESSION_AUTHENTICATION_NOT_PROVEN" else 3


if __name__ == "__main__":
    sys.exit(main())