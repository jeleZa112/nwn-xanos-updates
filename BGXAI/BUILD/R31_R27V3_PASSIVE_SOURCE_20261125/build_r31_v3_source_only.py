"""Deterministically COMPOSE R27 V3 observer; no writes, no installer, no deploy.

The resulting bytes are a SOURCE-ONLY candidate for a future, separately
authorized WeiDU component replacing (not duplicating) the original R27 Lua.
CI/tests may write the returned bytes to a disposable temp directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R27_V3 = HERE.parent / "R27_R2_IDENTITY_REFRESH_20261124" / "BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua"
BOOT = HERE / "R31_PASSIVE_BOOTSTRAP.lua"
EXPECTED_V3_SIZE = 44805
EXPECTED_V3_SHA256 = "61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929"
OLD_INSTALLED_R27_SHA256 = "e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735"
FORBIDDEN_CORE = (
    b"SelectWeaponAbility(", b"ClearActions(", b"ActionOverride(",
    b"EEex_Action_AddSpriteStartedActionListener(", b"P.initialized=start()",
)
FORBIDDEN_BUNDLE = (
    b"SelectWeaponAbility(", b"ClearActions(", b"ActionOverride(",
    b"EEex_Action_QueueScriptFileResponseOnAIBase(",
)


class SourceHold(ValueError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def assemble(source: bytes, boot: bytes) -> bytes:
    if len(source) != EXPECTED_V3_SIZE or sha256(source) != EXPECTED_V3_SHA256:
        raise SourceHold("R27_V3_EXACT_SHA_OR_SIZE_DRIFT")
    if any(token in source for token in FORBIDDEN_CORE):
        raise SourceHold("R27_V3_CONTAINS_HOOK_OR_DISPATCH")
    if not source.rstrip().endswith(b"return R27"):
        raise SourceHold("R27_V3_TERMINAL_EXPORT_MISSING")
    for marker in (
        b"queueSnapshotStable=qStable",
        b"actionContextSnapshotStable=ctxStable",
        b"actionOriginVerified=false",
        b"manualEpsQueueVerified=false",
        b"function R27.prepareConsolePilot(",
        b"function R27.makeListener(",
    ):
        if marker not in source:
            raise SourceHold("R27_V3_CONTRACT_MISSING:" + repr(marker))
    if not boot.startswith(b"-- BGXAI R31: passive bootstrap"):
        raise SourceHold("R31_BOOTSTRAP_IDENTITY_MISSING")
    for marker in (
        b"BGXAI_R27_ObserverPilot",
        b"EEex_Action_AddSpriteStartedActionListener,pilot.listener",
        b"R31_R27V3_PASSIVE",
        b"readOnly=true",
        b"dispatchAuthorized=false",
        b"weaponSwitchAuthorized=false",
    ):
        if marker not in boot:
            raise SourceHold("R31_BOOTSTRAP_CONTRACT_MISSING:" + repr(marker))
    result = (
        b"-- R31 SOURCE ONLY: derived from exact V3, not installed.\n"
        b"local R27 = (function()\n"
        + source
        + b"\nend)()\n"
        + boot
    )
    if any(token in result for token in FORBIDDEN_BUNDLE):
        raise SourceHold("BUNDLE_HAS_ENGINE_DISPATCH")
    if result.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1:
        raise SourceHold("BUNDLE_LISTENER_COUNT_NOT_ONE")
    if len(result) > 128000:
        raise SourceHold("BUNDLE_OVERSIZE")
    return result


def compose() -> bytes:
    return assemble(R27_V3.read_bytes(), BOOT.read_bytes())


if __name__ == "__main__":
    result = compose()
    print(json.dumps({
        "schema": "BGXAI_R31_V3_COMPOSITION_SOURCE_ONLY_V1",
        "status": "SOURCE_COMPOSITION_PASS_NO_INSTALL",
        "sourceSha256": EXPECTED_V3_SHA256,
        "candidateSha256": sha256(result),
        "candidateBytes": len(result),
        "gameModified": False,
        "installationPerformed": False,
        "dispatchAuthorized": False,
        "ordersSent": 0,
    }, indent=2))
