#!/usr/bin/env python3
"""BGXAI R42 diagnostic extension, SOURCE ONLY. Never installs/runs game.

Reuses the original exact R42 one-shot Jagan listener and the existing R39
assignment probe. The missing delta is a strictly bounded R39 HOLD reason.
Produces an alternative Lua CANDIDATE in memory; does not modify R42, R39,
bootstrap, WeiDU or the user's live installed 155th component.

Do not deploy without a later separate last-only guarded upgrade and explicit
typed authorization. Offline syntax checks are not game runtime proof.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py"
ORIGINAL_BLOB = "8fbf928a7f346433eaac01c47208b153eeb81b64"
ORIGINAL_CANDIDATE_SHA256 = "d14bf5f62f7d37663cf77f3305f57fb9631293940ed8ae2d4cb7b488248434b0"
SCHEMA = "BGXAI_R42_HOLD_REASON_SOURCE_ONLY_V1"
STATUS = "R42_HOLD_REASON_COMPOSED_NO_INSTALL"
NAME_ANCHOR = b"   local name=nil\n"
JSON_ANCHOR = b'     \'"sameR38Listener":true,"gameModified":false,\'..\n'

# R39 returns these stable status codes already; do NOT create new probing.
# Only allowlist members can enter the JSON string. Never print raw row.status.
PROBE_STATUSES = (
    "R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY",
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
)
PHYSICAL_DETAILS = (
    "HOLD_PORTRAIT_ACTOR_ID",
    "HOLD_SELECTION_NOT_EXACTLY_THIS_ACTOR",
    "HOLD_ACTOR_NOT_CLERIC",
    "HOLD_ACTIVE_STATS_UNAVAILABLE",
    "HOLD_KIT_OR_STRENGTH_NOT_MATCHED",
    "HOLD_EQUIPMENT_UNAVAILABLE",
    "HOLD_SLOT_UNREADABLE",
    "HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED",
)

# Exactly one small addendum IN the existing R42 callback, not a second hook.
# All variables are local. It never evaluates native triggers or issues orders.
DIAG_LUA = """   local r39ProbeStatus='R39_BRIDGE_RESULT_MISSING'
   local r39PhysicalReason='NONE'
   if not ok then
    r39ProbeStatus='R39_PROBE_EXCEPTION'
   elseif type(row)=='table' then
    local allowedStatuses={
""" + "".join("     ['" + s + "']=true,\n" for s in PROBE_STATUSES) + """    }
    if type(row.status)=='string' and allowedStatuses[row.status] then
     r39ProbeStatus=row.status
    else
     r39ProbeStatus='R39_UNCLASSIFIED_STATUS'
    end
    local allowedDetails={
""" + "".join("     ['" + s + "']=true,\n" for s in PHYSICAL_DETAILS) + """    }
    if type(row.reason)=='string' and allowedDetails[row.reason] then
     r39PhysicalReason=row.reason
    end
   end
   local r39ClassSlotState='NOT_READ'
   if r39ProbeStatus=='R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY' then
    if type(row.scriptLevelResrefs)~='table' then
     r39ClassSlotState='LEVEL_TABLE_MISSING'
    else
     local className=row.scriptLevelResrefs[4]
     if type(className)~='string' then
      r39ClassSlotState='MISSING_CLASS_ENTRY'
     elseif className=='' then
      r39ClassSlotState='EMPTY'
     elseif #className>8 or className=='NONE' or
            className:find('[^%w_#*]') then
      r39ClassSlotState='INVALID_RESREF'
     else
      r39ClassSlotState='VALID_NAME_CANDIDATE'
     end
    end
   end
"""

JSON_DELTA = (b'     \'"r39ProbeStatus":"\'..r39ProbeStatus..\'",\'..\n'
              b'     \'"r39PhysicalReason":"\'..r39PhysicalReason..\'",\'..\n'
              b'     \'"r39ClassSlotState":"\'..r39ClassSlotState..\'",\'..\n')

def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def verified_original():
    raw = ORIGINAL.read_bytes()
    if gitblob(raw) != ORIGINAL_BLOB:
        raise ValueError("HOLD_R42_ORIGINAL_SOURCE_DRIFT")
    spec = importlib.util.spec_from_file_location("bgxai_original_exact_r42", ORIGINAL)
    if spec is None or spec.loader is None:
        raise ValueError("HOLD_R42_SOURCE_IMPORT")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def patch(original_candidate: bytes) -> bytes:
    if hashlib.sha256(original_candidate).hexdigest() != ORIGINAL_CANDIDATE_SHA256:
        raise ValueError("HOLD_ORIGINAL_CANDIDATE_SHA")
    if original_candidate.count(NAME_ANCHOR) != 1 or original_candidate.count(JSON_ANCHOR) != 1:
        raise ValueError("HOLD_R42_DIAG_ANCHOR_UNIQUE")
    if original_candidate.count(b"[BGXBCS]") != 1:
        raise ValueError("HOLD_R42_EXISTING_ONE_SHOT_DRIFT")
    delta = DIAG_LUA.encode("ascii") + JSON_DELTA
    for bad in (b"XEquipItem(", b"SetGlobal(", b"ActionOverride(", b"ClearActions(",
                b"SelectWeaponAbility(", b"EEex_Action_AddSpriteStartedActionListener(",
                b"EEex_Trigger_EvalConditionalStringAsAIBase("):
        if bad in delta:
            raise ValueError("HOLD_R42_DIAG_UNSAFE_ACTION")
    result = original_candidate.replace(NAME_ANCHOR, NAME_ANCHOR + DIAG_LUA.encode("ascii"), 1)
    result = result.replace(JSON_ANCHOR, JSON_DELTA + JSON_ANCHOR, 1)
    if (result.count(b"[BGXBCS]") != 1 or
        result.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1 or
        result.count(b"EEex_Action_AddSpriteStartedActionListener(") != 0 or
        result.count(b"R27.r42Once=true") != 1 or
        result.count(b"probeInstalledScriptAssignments()") != 1):
        raise ValueError("HOLD_R42_DIAG_LISTENER_OR_ONE_SHOT_CHANGED")
    for tag in (b"[BGXR27]", b"[BGXR37]", b"[BGXINV3]", b"[BGXID]"):
        if result.count(tag) != original_candidate.count(tag):
            raise ValueError("HOLD_R42_DIAG_PREDECESSOR_TAG_DRIFT")
    return result

def compose() -> bytes:
    original = verified_original()
    r38 = original.verified(original.R38, original.R38_BYTES, original.R38_BLOB)
    r39 = original.verified(original.R39, original.R39_BYTES, original.R39_BLOB)
    return patch(original.compose(r38, r39))

def main():
    raw = compose()
    print(json.dumps({
        "schema": SCHEMA, "status": STATUS,
        "baseR42CandidateSHA256": ORIGINAL_CANDIDATE_SHA256,
        "diagnosticCandidateSHA256": hashlib.sha256(raw).hexdigest(),
        "diagnosticCandidateBytes": len(raw),
        "onlyExistingActionStartedListener": True,
        "r39ProbeStatusesAllowlisted": len(PROBE_STATUSES),
        "gameModified": False, "installed": False,
        "classScriptResrefAtLiveJaganVerified": False,
        "ordersSent": 0, "dispatchAuthorized": False, "armAuthorized": False,
        "next": "REQUIRES_SEPARATE_REVIEWED_LAST_ONLY_UPGRADE_AND_TYPED_APPROVAL"
    }, indent=2))

if __name__ == "__main__":
    main()
