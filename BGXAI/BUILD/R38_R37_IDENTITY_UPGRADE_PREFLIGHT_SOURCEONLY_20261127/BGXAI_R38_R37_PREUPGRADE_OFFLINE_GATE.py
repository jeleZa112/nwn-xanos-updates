#!/usr/bin/env python3
"""BGXAI R38: offline/source-only preupgrade gate for installed R37 + optional identity advisory.

This does NOT install R38, compile it natively, access the live game or authorize XEquipItem.
The passed-in R37 status is a user-provided historical snapshot, not an authenticated current state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "BGXAI/BUILD/R37_INVENTORY16_SINGLE_CALLBACK_SOURCEONLY_20261126/M_BGXR27_R37_INV3_SOURCE_ONLY.lua"
R38 = ROOT / "BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua"
IDENTITY = ROOT / "BGXAI/BUILD/WEAPON_XEQUIP_IDENTITY_RO_V1_20261127/BGXAI_XEQUIP_IDENTITY_RO_V1.lua"
MAX_BYTES = 100_000
PINS = {
    BASE: (69725, "ae5011dfdf132cb3cc29643acdb3c66da33f5412"),
    R38: (78927, "ada1ff628873e83a0b21296e5b5017bbc47510cd"),
    IDENTITY: (6884, "895451dd64caa818cb3117c580442d70ef226016"),
}
EXPECTED_R37_SHA256 = "5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6"
EXPECTED_WEIDU_LOG_SHA256 = "3f838e42236898b63cacb3256e9fff4bcea1b9f2273baba4baff27e8883f4538"
EXPECTED_LAST = r"~BGXR37\SETUP-BGXR37.TP2~ #0 #0 // BGXR37 passive reuse existing R33 callback"
SCHEMA = "BGXAI_R38_R37_IDENTITY_OFFLINE_PREFLIGHT_V1"
MARKERS = ("CORE", "JSON", "CAPTURE", "EMIT")

class Hold(ValueError):
    pass

def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()

def verified_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise Hold("HOLD_SOURCE_PATH_OR_FILE_INVALID")
    raw = path.read_bytes()
    size, pinned = PINS[path]
    if len(raw) != size or blob_sha1(raw) != pinned:
        raise Hold("HOLD_SOURCE_PIN_DRIFT:" + path.name)
    return raw

def source_evidence() -> dict:
    base, cand, identity = (verified_file(x) for x in (BASE, R38, IDENTITY))
    # Strip exactly four additions; all pre-existing R37 + INV3 bytes must remain identical.
    original = cand
    for name in MARKERS:
        pattern = re.compile(
            rb"-- BEGIN BGXAI_IDV1_" + name.encode("ascii") +
            rb"\n.*?-- END BGXAI_IDV1_" + name.encode("ascii") + rb"\n",
            re.S,
        )
        if len(pattern.findall(original)) != 1:
            raise Hold("HOLD_IDENTITY_INSERT_MARKER_COUNT:" + name)
        if name == "CORE" and identity not in pattern.search(original).group(0):
            raise Hold("HOLD_EMBEDDED_IDENTITY_MISMATCH")
        original = pattern.sub(b"", original)
    if original != base:
        raise Hold("HOLD_R37_INV3_BASE_DRIFT")
    if cand.count(b"EEex_Action_AddSpriteStartedActionListener") != base.count(
        b"EEex_Action_AddSpriteStartedActionListener"
    ):
        raise Hold("HOLD_EXTRA_LISTENER_TOKEN")
    if cand.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1:
        raise Hold("HOLD_LISTENER_NOT_EXACTLY_ONCE")
    for marker in (b"[BGXR27]", b"[BGXR37]", b"[BGXINV3]"):
        if cand.count(marker) != base.count(marker):
            raise Hold("HOLD_ORIGINAL_LOG_MARKER_DRIFT")
    if cand.count(b"[BGXID]") != 1:
        raise Hold("HOLD_IDENTITY_LOG_MARKER_DRIFT")
    # Reject actual game mutations; don't falsely reject descriptions in comments.
    uncommented = b"\n".join(
        line.split(b"--", 1)[0] for line in cand.splitlines()
    )
    for forbidden in (
        rb"\bXEquipItem\s*\(", rb"\bClearActions\s*\(",
        rb"\bFillSlot\s*\(", rb"\bSetGlobal\s*\(",
        rb"\bActionOverride\s*\(", rb"\bSelectWeaponAbility\s*\(",
    ):
        if re.search(forbidden, uncommented):
            raise Hold("HOLD_ENGINE_WRITE_TOKEN")
    required = (
        b"\"armAuthorized\":false", b"\"safeActionBoundaryVerified\":false",
        b"\"dispatchAuthorized\":false",
        b"result.identityV1Status=",
        b"ports.emitString('[BGXID] '..idline)",
    )
    if any(v not in cand for v in required):
        raise Hold("HOLD_ADVISORY_ONLY_GUARDS_MISSING")
    return {
        "sourceByteIdenticalExceptFourMarkers": True,
        "previousMessagesPreserved": True,
        "oneStartedActionListener": True,
        "identityReadOnlyCodeEmbedded": True,
        "candidateBytes": len(cand),
        "candidateGitBlobSha1": blob_sha1(cand),
        "newEngineActionCalls": 0,
    }

def status_evidence(report: dict) -> dict:
    if type(report) is not dict:
        raise Hold("HOLD_R37_STATUS_NOT_OBJECT")
    if report.get("schema") != "BGXAI_R37_R33_R36_SINGLE_LISTENER_GUARDED_V1":
        raise Hold("HOLD_R37_STATUS_SCHEMA_DRIFT")
    if report.get("status") != "R37_PRESENT_LAST_PASSIVE":
        raise Hold("HOLD_R37_NOT_LAST_PASSIVE")
    if type(report.get("weiduComponents")) is not int or report["weiduComponents"] != 153:
        raise Hold("HOLD_WEIDU_COMPONENT_COUNT_DRIFT")
    if report.get("weiduLastComponent") != EXPECTED_LAST:
        raise Hold("HOLD_WEIDU_LAST_COMPONENT_DRIFT")
    if report.get("weiDULogSha256") != EXPECTED_WEIDU_LOG_SHA256:
        raise Hold("HOLD_WEIDU_SNAPSHOT_SHA_DRIFT")
    if report.get("liveModuleSha256") != EXPECTED_R37_SHA256:
        raise Hold("HOLD_LIVE_R37_MODULE_SHA_DRIFT")
    for key, want in (
        ("r33SourceExact", False), ("r37SourceExact", True),
        ("gameModified", False), ("dispatchAuthorized", False),
        ("weaponSwitchAuthorized", False),
    ):
        if report.get(key) is not want:
            raise Hold("HOLD_R37_FLAG_DRIFT:" + key)
    if type(report.get("ordersSent")) is not int or report["ordersSent"] != 0:
        raise Hold("HOLD_R37_ORDERS_NOT_ZERO")
    return {
        "historicalR37StatusMatched": True,
        "historicalWeiDULogSha256": EXPECTED_WEIDU_LOG_SHA256,
        "historicalR37Sha256": EXPECTED_R37_SHA256,
        "historicalComponents": 153,
        "currentGameRechecked": False,
    }

def run(report: dict) -> dict:
    a = status_evidence(report)
    b = source_evidence()
    return {
        "schema": SCHEMA,
        "status": "R38_OFFLINE_SOURCE_GATE_PASS_NO_GAME_ACCESS",
        "sourceEvidence": b,
        "snapshotEvidence": a,
        "installedR37SnapshotSource": "USER_PROVIDED_STATUS_NOT_LIVE_RECHECK",
        "updaterIntegrated": False,
        "weiduInstallerBuilt": False,
        "runtimeIdentityVerified": False,
        "classKitItmUsabilityVerified": False,
        "safeActionBoundaryVerified": False,
        "manualEpsOriginVerified": False,
        "nativeV3CompileAlreadyProvenSeparately": True,
        "readOnly": True,
        "gameFilesModified": False,
        "installed": False,
        "ordersSent": 0,
        "dispatchAuthorized": False,
        "armAuthorized": False,
        "liveUpgradePermitted": False,
    }

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--r37-status", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        # Never touch user's game path; exact status is only a static fixture/snapshot.
        p = args.r37_status
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 16_384:
            raise Hold("HOLD_SNAPSHOT_FILE_INVALID")
        report = json.loads(p.read_bytes().decode("utf-8-sig"))
        out = run(report)
    except (Hold, ValueError, UnicodeError, OSError, KeyError) as exc:
        out = {
            "schema": SCHEMA, "status": "R38_OFFLINE_HOLD",
            "reason": str(exc), "installed": False,
            "gameFilesModified": False, "ordersSent": 0,
            "dispatchAuthorized": False, "armAuthorized": False,
        }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["status"] == "R38_OFFLINE_SOURCE_GATE_PASS_NO_GAME_ACCESS" else 3

if __name__ == "__main__":
    sys.exit(main())
