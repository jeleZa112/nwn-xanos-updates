#!/usr/bin/env python3
"""BGXAI R42: inert source-only composition of *installed* R38 + tested R39.

No new listener, no game access, no actions, LOCALS, installer or updater here.
Production installation, if authorized later, must be R38-last guarded WeiDU
with exact game-state proofs, typed approval, external backups and rollback.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
R38 = "BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua"
R39 = "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua"
R38_BYTES = 78927
R38_SHA = "958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c"
R38_BLOB = "ada1ff628873e83a0b21296e5b5017bbc47510cd"
R39_BYTES = 13088
R39_BLOB = "52bd8751581aa9f9d9ac09559f11a856e81ba1da"
SCHEMA = "BGXAI_R42_R38_R39_SINGLE_LISTENER_CLASS_BCS_SOURCE_ONLY_V1"
READONLY_STATUS = "R42_COMPOSED_CLASS_BCS_SINGLE_LISTENER_NO_INSTALL"
EMIT_ANCHOR = "   if idline then ports.emitString('[BGXID] '..idline) end"
CALL_ANCHOR = "  local emitted=pcall(deps.emit,result)"
BRIDGE_ANCHOR = "-- BGXAI R31: passive bootstrap for EXACT R27 ACTION_CONTEXT_V3 source."
LISTENER_CALL = "EEex_Action_AddSpriteStartedActionListener,pilot.listener"

# This line is emitted at most once in the existing R38 callback. It is
# deliberately additional metadata, not one of R38's four existing streams.
EMIT_DELTA = """   if type(sample.r42Row)=='string' then
    ports.emitString('[BGXBCS] '..sample.r42Row)
   end
"""

# The existing R39 bridge is called ONLY if the original R38 ID_CORE already
# corroborated the exact Jagan physical pilot candidate. It rechecks actor,
# unique STAF01 slot20, empty slot35, and 2x seven assigned script names.
# It never calls R39.probe() (which has engine trigger evaluations).
CALL_DELTA = """  -- R42: observe CLASS BCS once, INSIDE the already-registered R38 callback.
  -- No second listener, gameplay action, LOCALS, native trigger eval or ARM.
  if p==1 and
     result.identityV1Status=='RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM' and
     R27.r42Once~=true then
   R27.r42Once=true
   local ok,row=pcall(function()
    if type(R27.r42Bridge)~='table' then return nil end
    return R27.r42Bridge.probeInstalledScriptAssignments()
   end)
   local name=nil
   if ok and type(row)=='table' and
      row.status=='R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY' and
      row.pilotPhysicalSnapshotDoubleMatched==true and
      row.portraitActorId==id and
      row.canArm==false and row.ordersSent==0 and
      type(row.scriptLevelResrefs)=='table' then
    name=row.scriptLevelResrefs[4]
   end
   local match=type(name)=='string' and #name>=1 and #name<=8 and
               name~='NONE' and not name:find('[^%w_#*]')
   local status=match and 'CLASS_BCS_RESREF_OBSERVED_NO_ARM' or
                      'HOLD_CLASS_BCS_NOT_READABLE'
   local value=match and ('"'..name..'"') or 'null'
   result.r42Row='{"schema":"BGXAI_R42_CLASS_BCS_SINGLE_CALLBACK_RO_V1",'..
     '"type":"CLASS_BCS_ONCE","seq":'..tostring(result.collectorOrdinal)..
     ',"partyIndex":1,"classScriptResref":'..value..
     ',"scrlev":4,"status":"'..status..'",'..
     '"sameR38Listener":true,"gameModified":false,'..
     '"actualBcsExecutionVerified":false,"manualEpsActionOriginVerified":false,'..
     '"armAuthorized":false,"dispatchAuthorized":false,'..
     '"ordersSent":0,"localsWritten":0}'
  end
"""

def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def verified(path: str, length: int, expected_blob: str) -> bytes:
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("HOLD_PATH")
    file = ROOT / rel
    if file.is_symlink() or not file.is_file():
        raise ValueError("HOLD_SOURCE_MISSING_OR_SYMLINK")
    if file.stat().st_size != length:
        raise ValueError("HOLD_SOURCE_LENGTH")
    data = file.read_bytes()
    if len(data) != length or gitblob(data) != expected_blob:
        raise ValueError("HOLD_PREDECESSOR_GIT_BLOB_DRIFT")
    if path == R38 and hashlib.sha256(data).hexdigest() != R38_SHA:
        raise ValueError("HOLD_ACTIVE_R38_SOURCE_SHA")
    return data

def exact_replace(text: str, anchor: str, inserted: str) -> str:
    if text.count(anchor) != 1:
        raise ValueError("HOLD_NONUNIQUE_ANCHOR")
    return text.replace(anchor, inserted + anchor, 1)

def compose(r38_bytes: bytes, r39_bytes: bytes) -> bytes:
    if not isinstance(r38_bytes, bytes) or len(r38_bytes) != R38_BYTES:
        raise ValueError("HOLD_R38_INPUT")
    if not isinstance(r39_bytes, bytes) or len(r39_bytes) != R39_BYTES:
        raise ValueError("HOLD_R39_INPUT")
    if hashlib.sha256(r38_bytes).hexdigest() != R38_SHA or gitblob(r38_bytes) != R38_BLOB:
        raise ValueError("HOLD_R38_SHA")
    if gitblob(r39_bytes) != R39_BLOB:
        raise ValueError("HOLD_R39_SHA")
    orig = r38_bytes.decode("utf-8", "strict")
    bridge = r39_bytes.decode("utf-8", "strict")
    if orig.count(LISTENER_CALL) != 1:
        raise ValueError("HOLD_ORIGINAL_LISTENER_NOT_ONCE")
    if bridge.count("function M.probeInstalledScriptAssignments()") != 1:
        raise ValueError("HOLD_UNSUPPORTED_R39_BRIDGE")
    if "function M.probeScriptAssignments(ports)" not in bridge:
        raise ValueError("HOLD_R39_READONLY_BCS_PROBE")
    out = exact_replace(orig, EMIT_ANCHOR, EMIT_DELTA)
    out = exact_replace(out, CALL_ANCHOR, CALL_DELTA)
    unchanged_bridge = " local BGXAI_R42_Bridge=(function()\n" + bridge + "\n end)()\n R27.r42Bridge=BGXAI_R42_Bridge\n"
    out = exact_replace(out, BRIDGE_ANCHOR, unchanged_bridge)
    if out.count(LISTENER_CALL) != 1 or out.count("[BGXBCS]") != 1:
        raise ValueError("HOLD_DUPLICATE_LISTENER_OR_EMIT")
    if out.count("R27.r42Once=true") != 1:
        raise ValueError("HOLD_UNBOUNDED_PROBE")
    if out.count("R27.r42Bridge.probeInstalledScriptAssignments()") != 1:
        raise ValueError("HOLD_WRONG_READONLY_ENTRYPOINT")
    if out.count("BGXAI_R42_Bridge=(function()\n" + bridge + "\n end)()") != 1:
        raise ValueError("HOLD_R39_NOT_EMBEDDED_EXACTLY")
    for marker in ('[BGXR27]', '[BGXR37]', '[BGXINV3]', '[BGXID]'):
        if out.count(marker) != orig.count(marker):
            raise ValueError("HOLD_R38_STREAM_MUTATED")
    # New code is parsed as static text only. Never invoke the constructed Lua.
    clean = re.sub(r"--[^\n]*", "", EMIT_DELTA + "\n" + CALL_DELTA)
    for prohibited in ("XEquipItem(", "SetGlobal(", "ClearActions(",
                       "ActionOverride(", "SelectWeaponAbility(", "EEex_Action_AddSpriteStartedActionListener("):
        if prohibited in clean:
            raise ValueError("HOLD_R42_ADDED_GAME_ACTION")
    return out.encode("utf-8")

def source_report() -> dict:
    src = verified(R38, R38_BYTES, R38_BLOB)
    bridge = verified(R39, R39_BYTES, R39_BLOB)
    result = compose(src, bridge)
    return {
        "schema": SCHEMA, "status": READONLY_STATUS,
        "r38ExistingSourceSha256": R38_SHA,
        "r39ExistingGitBlob": R39_BLOB,
        "composedCandidateBytes": len(result),
        "composedCandidateSha256": hashlib.sha256(result).hexdigest(),
        "onlyExistingActionStartedListener": result.count(LISTENER_CALL.encode()) == 1,
        "additionalActionStartedListeners": 0,
        "classBCSProbeOneShot": True,
        "classScriptResrefAtLiveJaganVerified": False,
        "manualEpsActionOriginVerified": False,
        "actualBcsExecutionVerified": False,
        "nativeGameInstalled": False,
        "gameModified": False,
        "ordersSent": 0,
        "localsWritten": 0,
        "installAuthorized": False,
        "armAuthorized": False,
        "dispatchAuthorized": False,
        "next": "GUARDED_R38_LAST_WEIDU_PREFLIGHT_NOT_BUILT_OR_AUTHORIZED",
    }

if __name__ == "__main__":
    try:
        report = source_report()
    except (OSError, ValueError, UnicodeError) as error:
        report = {"schema": SCHEMA, "status": "HOLD_R42_SOURCE_PROVENANCE",
                  "reason": str(error), "gameModified": False,
                  "installAuthorized": False, "ordersSent": 0}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["status"] == READONLY_STATUS else 3)
