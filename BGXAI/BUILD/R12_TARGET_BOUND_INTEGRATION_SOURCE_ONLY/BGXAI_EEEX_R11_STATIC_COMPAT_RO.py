#!/usr/bin/env python3
"""BGXAI R11/R12 source-only EEex installed-script compatibility scan.

Reads only. No file writing, no subprocesses, no game hook, no WeiDU.
Static Lua callsites never prove that a function is available in the live EEex VM.
The normal BGXAI_UPDATE.cmd is deliberately unchanged; integration later requires consent.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

GAME = Path(r"C:\Games\BG_EET_FOXX_NEW")
CHECKS = {
    "bootstrap": ("override/M___EEex.lua", ()),
    "attack_info": ("EEex_scripts/B3AttackInfo.lua", (
        r"EEex\.GetWeaponHitChance\s*\(",
        r"EEex\.IsImmuneToWeapon\s*\(",
        r"sourceSpriteEquipment\.m_selectedWeapon",
        r"sourceSpriteEquipment\.m_selectedWeaponAbility",
    )),
    "action": ("EEex_scripts/EEex_Action.lua", (
        r"function\s+EEex_Action_AddSpriteStartedActionListener\s*\(",
        r"function\s+EEex_Action_LuaHook_OnAfterSpriteStartedAction\s*\(",
        r"sprite\.m_curAction",
    )),
    "r1": ("override/M_BGXWP.lua", ()),
    "r2": ("override/M_BGXW2.lua", ()),
    "r4": ("override/M_BGXW4.lua", ()),
}


def _file(root: Path, relative: str) -> tuple[dict[str, Any], str | None]:
    path = root / relative
    result = {"relative": relative, "exists": False, "sha256": None, "bytes": None}
    # Fail closed on symlinks for each part to avoid following reparse-like aliases.
    rel_parts = Path(relative).parts
    p = root
    for part in rel_parts:
        p = p / part
        if p.is_symlink():
            return {**result, "error": "SYMLINK_PATH_STOP"}, None
    if not path.is_file():
        return {**result, "error": "FILE_NOT_FOUND"}, None
    if path.stat().st_size > 2_000_000:
        return {**result, "error": "SCRIPT_TOO_LARGE"}, None
    data = path.read_bytes()
    result.update(exists=True, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    # Source is the user's installed code, not trusted instructions.
    return result, data.decode("utf-8-sig", errors="replace")


def _lua_active_lines(src: str) -> str:
    # Source-only heuristic, not a Lua parser. Never treat a comment-only token
    # as evidence of a live callsite. Literal strings remain untrusted.
    src = re.sub(r"--\[(=*)\[.*?\]\1\]", "", src, flags=re.S)
    return "\n".join(line.split("--", 1)[0] for line in src.splitlines())


def scan(root: Path) -> dict[str, Any]:
    report = {
        "schema": "BGXAI_EEEX_R11_STATIC_COMPAT_RO_V1",
        "status": "HOLD",
        "root": str(root),
        "gameModified": False,
        "readOnly": True,
        "runtimeApiAuthenticated": False,
        "liveHookSafetyProven": False,
        "actionSourceProven": False,
        "manualEPSBoundaryProven": False,
        "alternateSlotEffectiveAPRVerified": False,
        "weaponSwitchAuthorized": False,
        "installAuthorized": False,
        "scripts": {},
    }
    if not root.exists() or not root.is_dir() or root.is_symlink():
        report["status"] = "HOLD_GAME_ROOT_UNAVAILABLE"
        return report
    if not (root / "chitin.key").is_file() or (root / "chitin.key").is_symlink():
        report["status"] = "HOLD_GAME_ROOT_UNVERIFIED"
        return report
    all_ok = True
    for key, (rel, patterns) in CHECKS.items():
        info, src = _file(root, rel)
        if src is None:
            all_ok = False
        else:
            missing = [p for p in patterns if not re.search(p, _lua_active_lines(src))]
            info["expectedStaticCallsitesPresent"] = not missing
            if missing:
                info["missingStaticCallsiteCount"] = len(missing)
                all_ok = False
        report["scripts"][key] = info
    report["status"] = ("STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN" if all_ok else
                        "HOLD_STATIC_COMPAT_INCOMPLETE")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default=str(GAME))
    args = parser.parse_args()
    root = Path(args.game)
    # This executable entrypoint is deliberately pinned to the known game root.
    # Tests use scan(temp_path) directly and cannot authorize installing it.
    allowed = os.path.normcase(os.path.abspath(str(GAME)))
    actual = os.path.normcase(os.path.abspath(str(root)))
    if os.name != "nt" or actual != allowed:
        print(json.dumps({"status": "HOLD_THIS_WINDOWS_GAME_ONLY",
                          "gameModified": False, "weaponSwitchAuthorized": False}))
        return 2
    report = scan(root)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN" else 3


if __name__ == "__main__":
    raise SystemExit(main())
