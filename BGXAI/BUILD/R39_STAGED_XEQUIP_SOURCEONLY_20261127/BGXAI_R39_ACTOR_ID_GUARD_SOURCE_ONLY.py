#!/usr/bin/env python3
"""BGXAI R39 actor-wrapper stability micro-delta, SOURCE ONLY.

First real user R43 179->11 read-only capture returned
HOLD_SCRIPT_ACTOR_CHANGED. Existing R39 code compares two Lua sprite
wrapper objects, whereas EEex_Sprite_GetInPortrait() obtains and casts a
CGameSprite usertype on EACH call. Object equality is not a trustworthy
substitute for numerical m_id. We do not know which half of the original
OR test failed in the user's game.

This program creates an *alternative* R39 Lua source, never edits the
original SHA-pinned bridge or an installed game. Nothing is deployed,
registered, armed or dispatched by calling this module.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua"
ORIGINAL_GIT_BLOB = "52bd8751581aa9f9d9ac09559f11a856e81ba1da"
SCHEMA = "BGXAI_R39_STABLE_NUMERIC_ACTOR_ID_SOURCE_ONLY_V1"
STATUS = "SOURCE_COMPOSED_NOT_INSTALLED"
PATCHES = (
    (
        b" local function once()\n",
        b" local function once(readSprite)\n",
    ),
    (
        b"   local value=safe(ports.getScriptLevelResRef,sprite,level)\n",
        b"   local value=safe(ports.getScriptLevelResRef,readSprite,level)\n",
    ),
    (
        b" local first=once()\n",
        b" local first=once(sprite)\n",
    ),
    (
        b" if sameActor~=sprite or sameId~=portraitId then\n"
        b"  return report('HOLD_SCRIPT_ACTOR_CHANGED') end\n",
        b" -- EEex returns a typed Lua wrapper per portrait lookup. An object\n"
        b" -- wrapper's Lua equality is NOT a stable actor-identity contract.\n"
        b" -- Retain the original numeric actor ID from exactPhysical(), which\n"
        b" -- also validated portrait and lone selection before the first read.\n"
        b" local secondActorId=prop(sameActor,'m_id')\n"
        b" if not int(secondActorId,1,2147483647) or\n"
        b"    secondActorId~=initialPhysical.actorId or\n"
        b"    secondActorId~=portraitId or sameId~=portraitId then\n"
        b"  return report('HOLD_SCRIPT_ACTOR_CHANGED') end\n",
    ),
    (
        b" local second=once()\n",
        b" local second=once(sameActor)\n",
    ),
)

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def verified_original() -> bytes:
    raw = ORIGINAL.read_bytes()
    if ORIGINAL.is_symlink() or git_blob(raw) != ORIGINAL_GIT_BLOB:
        raise ValueError("HOLD_ORIGINAL_R39_SOURCE_GIT_BLOB_DRIFT")
    return raw

def compose() -> bytes:
    source = verified_original()
    original = source
    for old, new in PATCHES:
        if source.count(old) != 1 or source.count(new) != 0:
            raise ValueError("HOLD_R39_PATCH_ANCHOR_DRIFT")
        source = source.replace(old, new, 1)
    if source == original:
        raise ValueError("HOLD_R39_PATCH_NOT_APPLIED")
    for marker in (
        b"HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE",
        b"HOLD_SCRIPT_PILOT_PHYSICAL_CONTEXT",
        b"HOLD_SCRIPT_ACTOR_CHANGED",
        b"HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED",
        b"HOLD_SCRIPT_RESREF_CHANGED",
        b"HOLD_SCRIPT_CURSOR_CHANGED",
        b"function M.probeInstalledScriptAssignments()",
        b"local finalPhysical,finalReason=exactPhysical(sameActor",
    ):
        if marker not in source:
            raise ValueError("HOLD_R39_SECURITY_MARKER_MISSING")
    for marker in (
        b"XEquipItem(", b"SetGlobal(", b"ActionOverride(",
        b"EEex_Action_AddSpriteStartedActionListener(",
        b"EEex_Trigger_EvalConditionalStringAsAIBase(",
    ):
        if source.count(marker) != original.count(marker):
            raise ValueError("HOLD_R39_ACTION_BOUNDARY_CHANGED")
    if source.count(b"function M.probeScriptAssignments(ports)") != 1:
        raise ValueError("HOLD_R39_PROBE_DUPLICATED")
    return source

def main() -> None:
    raw = compose()
    print(json.dumps({
        "schema": SCHEMA,
        "status": STATUS,
        "previousR39GitBlob": ORIGINAL_GIT_BLOB,
        "candidateBytes": len(raw),
        "candidateSha256": hashlib.sha256(raw).hexdigest(),
        "oneExactExistingR39ProbePreserved": True,
        "newEEexListeners": 0,
        "installed": False,
        "gameModified": False,
        "ordersSent": 0,
        "armAuthorized": False,
        "dispatchAuthorized": False,
        "classScriptResrefAtLiveJaganVerified": False,
        "runtimeCauseConfirmed": False,
        "requiresSeparateLastOnlyGuardedUpgrade": True,
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
