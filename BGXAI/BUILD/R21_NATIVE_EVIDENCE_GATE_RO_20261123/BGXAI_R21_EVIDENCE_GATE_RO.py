"""BGXAI R21 pure offline evidence gate. Never reads/writes the game or sends actions.

This validates a sanitized R20 static audit plus optional scalar-only selected-attack
snapshots. It cannot authenticate native pointer lifetime, compute alternate APR,
or authorize weapon switching. No EEex, Lua, filesystem or subprocess imports.
"""
from __future__ import annotations
from collections.abc import Mapping

SCHEMA = "BGXAI_R21_NATIVE_EVIDENCE_GATE_RO_V1"
TAG = "v1.1.7"
SOURCE_BLOBS = {
    "resource": "5ecd3c2f9e9bcc6cbd317653fc057a06d956916b",
    "sprite": "b2d8d930c47785737bd30dad08e9f35a9d859578",
    "action": "e7543274ed066b5abe3c58262105212f208d1595",
}
REQUIRED_FALSE = (
    "apiPresentAtRuntimeVerified", "nativeAbilityPointerSafe",
    "nativeLauncherReturnSafe", "nativeResourceLifetimeVerified",
    "safeToCallGetAbility", "safeToCallGetLauncher",
    "safeToRegisterListener", "alternateSlotAPRVerified",
    "fullActiveEffectsFingerprintVerified", "weaponSwitchAuthorized",
    "dispatchAuthorized", "installAuthorized", "gameModified",
)
APR_KEYS = {**{i: float(i) for i in range(6)},
            6: 0.5, 7: 1.5, 8: 2.5, 9: 3.5, 10: 4.5}
BLOCKERS = (
    "ITEM_ABILITY_STRIDE_SOURCE_MISMATCH",
    "NO_NATIVE_RESOURCE_LIFETIME_PROOF",
    "NO_AUTHENTICATED_LAUNCHER_AMMO_PAIR",
    "NO_ALTERNATE_SLOT_APR",
    "NO_COMPLETE_ACTIVE_EFFECT_FINGERPRINT",
    "NO_MANUAL_EPS_ACTION_QUEUE_BOUNDARY",
)


def _strict_int(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _resref(value: object) -> bool:
    return (isinstance(value, str) and 1 <= len(value) <= 8 and
            all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in value))


def _static_report_proof(report: object) -> tuple[bool, str]:
    if not isinstance(report, Mapping):
        return False, "REPORT_NOT_MAPPING"
    if (report.get("schema") != "BGXAI_R19_INSTALLED_EEEX_STATIC_AUDIT_RO_V1"
            or report.get("status") != "UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY"
            or report.get("sourceTag") != TAG
            or report.get("sourceRepository") != "Bubb13/EEex"):
        return False, "REPORT_SOURCE_IDENTITY_NOT_MATCHED"
    for key in ("readOnly", "installedGameFilesInspected", "allRequiredLuaScriptsPresent",
                "allStaticMethodCallsitesPresent", "allInstalledFilesCanonicalLFUpstream"):
        if report.get(key) is not True:
            return False, "MISSING_STATIC_PROOF_" + key
    for key in REQUIRED_FALSE:
        if report.get(key) is not False:
            return False, "UNSAFE_OR_UNPROVEN_CAPABILITY_" + key
    scripts = report.get("scripts")
    if not isinstance(scripts, Mapping):
        return False, "SCRIPTS_NOT_MAPPING"
    for name, sha in SOURCE_BLOBS.items():
        data = scripts.get(name)
        if not isinstance(data, Mapping):
            return False, "MISSING_SOURCE_" + name
        if (data.get("present") is not True or
            data.get("allCallsitesPresent") is not True or
            data.get("canonicalLFUpstreamMatch") is not True or
            data.get("gitBlobSha1LF") != sha or
            data.get("upstreamTagGitBlobSha1") != sha):
            return False, "SOURCE_MISMATCH_" + name
    return True, "UPSTREAM_LF_EQUIVALENT_STATIC_ONLY"


def _selected_snapshot(snapshot: object) -> tuple[bool, str, dict]:
    if not isinstance(snapshot, Mapping):
        return False, "NO_SCALAR_SNAPSHOT", {}
    actor, target, slot = snapshot.get("actor"), snapshot.get("target"), snapshot.get("selectedSlot")
    apr = snapshot.get("selectedAprKeyRaw")
    if not (_strict_int(actor, 1, 2_147_483_647)
            and _strict_int(target, 1, 2_147_483_647) and actor != target):
        return False, "ACTOR_TARGET_ID_INVALID", {}
    if not _strict_int(slot, 10, 38) or slot not in (10, 11, 12, 13, 14, 35, 36, 37, 38):
        return False, "SELECTED_SLOT_INVALID", {}
    if not _strict_int(apr, 0, 10):
        return False, "SELECTED_APR_KEY_INVALID", {}
    if slot != 10 and not _resref(snapshot.get("selectedResref")):
        return False, "SELECTED_RESREF_INVALID", {}
    if snapshot.get("nativeEventAuthenticated") is not False:
        return False, "EVENT_AUTHENTICATION_NOT_ESTABLISHED", {}
    if snapshot.get("alternateSlotAPRVerified") is not False:
        return False, "ALTERNATE_APR_CLAIM_NOT_ALLOWED", {}
    if snapshot.get("manualEpsQueueVerified") is not False:
        return False, "MANUAL_EPS_CLAIM_NOT_ALLOWED", {}
    return True, "CURRENT_SELECTION_ONLY", {
        "actor": actor,
        "target": target,
        "slot": slot,
        "slotClass": ("FIST" if slot == 10 else "AMMO" if slot <= 14 else "WEAPON"),
        "selectedAprKeyRaw": apr,
        "selectedAprDecoded": APR_KEYS[apr],
    }


def evaluate(report: object, selected_snapshot: object = None) -> dict:
    """Return an immutable-in-intent verdict only; NEVER authorize game actions.

    ``selected_snapshot`` is an already-sanitized scalar dict, *not* a native
    handle. Snapshot cannot authenticate an EEex event or alternative weapon.
    """
    source_ok, source_reason = _static_report_proof(report)
    candidate_ok, candidate_reason, current = _selected_snapshot(selected_snapshot)
    status = ("HOLD_NATIVE_POINTER_AND_ACTION_QUEUE" if source_ok
              else "HOLD_STATIC_SOURCE_NOT_AUTHENTICATED")
    return {
        "schema": SCHEMA,
        "status": status,
        "sourceStaticMatched": source_ok,
        "sourceReason": source_reason,
        "currentSelectionScalarValid": candidate_ok if selected_snapshot is not None else False,
        "currentSelectionReason": candidate_reason,
        "selected": current if source_ok and candidate_ok else None,
        "itemHeaderSizeX64Documented": 114,
        "itemAbilitySizeX64Documented": 56,
        "abilityStrideMismatchForIndex1": 58,
        "upstreamItemHelperUsesWrongStride": True,
        "engineSuppliedAbilityOnHitSourceCandidate": True,
        "onHitHookCanChangeCombat": True,
        "engineSuppliedAbilityRuntimeSafe": False,
        "nativePointerLifetimeVerified": False,
        "safeToCallGetAbility": False,
        "safeToCallGetLauncher": False,
        "safeToRegisterListener": False,
        "alternateSlotAPRVerified": False,
        "launcherAmmoLinkVerified": False,
        "completeActiveEffectsVerified": False,
        "manualEpsQueueVerified": False,
        "weaponSwitchAuthorized": False,
        "dispatchAuthorized": False,
        "installAuthorized": False,
        "readOnly": True,
        "gameModified": False,
        "ordersSent": 0,
        "nextAction": "KEEP_CURRENT_WEAPON_NO_DISPATCH",
        "blockers": list(BLOCKERS),
    }
