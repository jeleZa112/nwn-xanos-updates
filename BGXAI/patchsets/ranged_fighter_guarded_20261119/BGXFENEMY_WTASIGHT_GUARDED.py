#!/usr/bin/env python3
"""BGXFENEMY: explicit-consent, native, reversible WTASIGHT party-friendly Enemy() guard.

Only the single verified WTASIGHT BCS response block changes. All other
WTASIGHT blocks, other combat resources, EPS, voices, and saves are preserved.
Game integration / live combat is NOT certified by offline or native preflight.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import BGXF_WTASIGHT_ENEMY_GUARD_SOURCE_ONLY as C
import BGXFTRACE_V3_GUARDED as TRACE

ROOT = C.ROOT
COMPONENT = "BGXFENEMY"
TARGET = "override/WTASIGHT.BCS"
STAGED = COMPONENT + "/staged/WTASIGHT.BCS"
PROOF = COMPONENT + "/PROOF.json"
TP2 = COMPONENT + "/setup-BGXFENEMY.tp2"
EXE = "setup-BGXFENEMY.exe"
LAST = re.compile(r"^~(?:[^~]*[/\\])?BGXFENEMY[/\\]SETUP-BGXFENEMY[.]TP2~\\s+#0\\s+#0(?:\\s|$)", re.I)
INSTALL_TOKEN = "INSTALL_BGXFENEMY_WTASIGHT_GUARD"
ROLLBACK_TOKEN = "ROLLBACK_BGXFENEMY_WTASIGHT_GUARD"
TP2_TEXT = (
    "BACKUP ~BGXFENEMY/backup~\\n"
    "AUTHOR ~BGXAI safe party Enemy guard~\\n"
    "BEGIN ~BGXFENEMY guard friendly-fire Enemy() in WTASIGHT for party only~\\n"
    "COPY ~BGXFENEMY/staged/WTASIGHT.BCS~ ~override/WTASIGHT.BCS~\\n"
)
BASE = dict(TRACE.BASE)
OTHER = {name: value for name, value in BASE.items() if name != TARGET}
OTHER["override/M_BXFR.lua"] = TRACE.SOURCE_SHA
SNAP = [*BASE, "override/M_BXFR.lua", "WeiDU.log", "chitin.key"]
OPTIONAL = ("lang/ru_RU/dialog.tlk", "lang/ru_RU/dialogf.tlk")


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard(path: pathlib.Path) -> None:
    TRACE.guard(path)


def last(root: pathlib.Path) -> str:
    return TRACE.last(root)


def common(root: pathlib.Path) -> None:
    if root != ROOT:
        raise ValueError("WRONG_GAME_ROOT")
    TRACE.V3.V2.require_root(root)
    for rel in [*SNAP, *OPTIONAL, STAGED, PROOF, TP2, EXE]:
        guard(root / rel)


def unchanged(root: pathlib.Path) -> None:
    for name, expected in OTHER.items():
        f = root / name
        guard(f)
        if not f.is_file() or digest(f) != expected:
            raise ValueError("OTHER_RESOURCE_SHA_DRIFT:" + name)


def baseline(root: pathlib.Path) -> None:
    common(root)
    observed = TRACE.status(root)
    if observed.get("status") != "BGXF3_INSTALLED_VERIFIED" or not TRACE.LAST.match(last(root)):
        raise ValueError("BGXF3_NOT_LAST_OR_DRIFT")
    if (root / COMPONENT).exists() or (root / EXE).exists():
        raise ValueError("STAGING_COLLISION")
    if digest(root / TARGET) != C.BASE_SHA:
        raise ValueError("WTASIGHT_BASELINE_SHA_DRIFT")
    unchanged(root)


def candidate(root: pathlib.Path) -> tuple[bytes, int]:
    baseline(root)
    built, changed = C.build_candidate(root)
    if changed not in range(1, C.BCS_COUNT + 1):
        raise ValueError("CHANGED_BLOCK_OUT_OF_RANGE")
    if C.digest(built) == C.BASE_SHA:
        raise ValueError("CANDIDATE_UNCHANGED")
    return built, changed


def preflight(root: pathlib.Path) -> dict:
    compiled, block = candidate(root)
    return {
        "status": "BGXFENEMY_NATIVE_PREFLIGHT_PASS",
        "changed_block": block,
        "old_wtasight_sha256": C.BASE_SHA,
        "candidate_sha256": C.digest(compiled),
        "preserved_blocks": C.BCS_COUNT - 1,
        "all_other_resources_pinned": True,
        "game_modified": False,
        "installed": False,
        "live_tested": False,
    }


def backup(root: pathlib.Path) -> pathlib.Path:
    base = pathlib.Path(os.environ.get("USERPROFILE", str(pathlib.Path.home()))) / "Documents" / "BGXFENEMY_SAFE_BACKUPS"
    guard(base)
    folder = base / ("PRE_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    guard(folder)
    folder.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in [*SNAP, *OPTIONAL]:
        src = root / name
        guard(src)
        if name in OPTIONAL and not src.exists():
            continue
        if src.is_symlink() or not src.is_file():
            raise ValueError("BACKUP_MISSING:" + name)
        dst = folder / name
        guard(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        hashes[name] = digest(src)
        if digest(dst) != hashes[name]:
            raise ValueError("BACKUP_SHA_MISMATCH:" + name)
    if hashes[TARGET] != C.BASE_SHA:
        raise ValueError("BACKUP_WRONG_WTASIGHT")
    (folder / "SHA256.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    return folder


def checked_backup(folder: pathlib.Path) -> dict:
    guard(folder)
    mf = folder / "SHA256.json"
    guard(mf)
    if not mf.is_file():
        raise ValueError("BACKUP_MANIFEST_MISSING")
    recorded = json.loads(mf.read_text("utf-8"))
    if recorded.get(TARGET) != C.BASE_SHA:
        raise ValueError("BACKUP_WRONG_BASE")
    if not all(name in recorded for name in SNAP):
        raise ValueError("BACKUP_REQUIRED_FILES_MISSING")
    if any(name not in (*SNAP, *OPTIONAL) for name in recorded):
        raise ValueError("BACKUP_PATH_UNEXPECTED")
    for name, expected in recorded.items():
        f = folder / name
        guard(f)
        if not f.is_file() or digest(f) != expected:
            raise ValueError("BACKUP_CORRUPTED:" + name)
    return recorded


def run_weidu(root: pathlib.Path, remove: bool = False) -> None:
    executable = root / EXE
    guard(executable)
    if not executable.is_file():
        raise ValueError("WEIDU_SETUP_MISSING")
    command = [
        str(executable), "--noautoupdate", "--no-exit-pause", "--game", str(root),
        "--use-lang", "ru_ru", "--force-uninstall" if remove else "--force-install", "0",
    ]
    p = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, errors="replace", timeout=240)
    stdout = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode or re.search(r"(?im)^\\s*(?:ERROR:|FATAL ERROR:)", stdout):
        raise ValueError("WEIDU_STOP_MANUAL_REVIEW:" + stdout[-700:])


def status(root: pathlib.Path) -> dict:
    common(root)
    if TRACE.LAST.match(last(root)):
        baseline(root)
        return {"status": "BGXFENEMY_NOT_INSTALLED_BGXF3_VERIFIED", "game_modified": False}
    if not LAST.match(last(root)):
        raise ValueError("BGXFENEMY_NOT_LAST_WEIDU")
    pf = root / PROOF
    guard(pf)
    if not pf.is_file():
        raise ValueError("PROOF_MISSING")
    record = json.loads(pf.read_text("utf-8"))
    if record.get("old_sha") != C.BASE_SHA:
        raise ValueError("PROOF_BASE_DRIFT")
    expected = record.get("new_sha")
    if not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected):
        raise ValueError("PROOF_NEW_SHA_INVALID")
    if record.get("block") not in range(1, C.BCS_COUNT + 1):
        raise ValueError("PROOF_BLOCK_INVALID")
    changed = record["block"]
    for name in [TARGET, STAGED]:
        f = root / name
        guard(f)
        if not f.is_file() or digest(f) != expected:
            raise ValueError("INSTALLED_SHA_DRIFT:" + name)
    unchanged(root)
    snap = pathlib.Path(record["backup"])
    checks = checked_backup(snap)
    original = (snap / TARGET).read_bytes()
    installed = (root / TARGET).read_bytes()
    old_parts = C.parts(original)
    now_parts = C.parts(installed)
    if len(old_parts) != C.BCS_COUNT or len(now_parts) != C.BCS_COUNT:
        raise ValueError("BCS_COUNT_DRIFT")
    if any(old_parts[i] != now_parts[i] for i in range(C.BCS_COUNT) if i != changed-1):
        raise ValueError("UNRELATED_BCS_BLOCK_MODIFIED")
    if old_parts[changed-1] == now_parts[changed-1]:
        raise ValueError("TARGET_BCS_BLOCK_UNCHANGED")
    for name in OPTIONAL:
        if name in checks and digest(root / name) != checks[name]:
            raise ValueError("DIALOG_TLK_CHANGED:" + name)
    return {
        "status": "BGXFENEMY_INSTALLED_VERIFIED",
        "old_sha256": C.BASE_SHA,
        "new_sha256": expected,
        "changed_block": changed,
        "preserved_blocks": C.BCS_COUNT - 1,
        "combat_scripts_other_than_WTASIGHT_unchanged": True,
        "live_tested": False,
        "game_modified": False,
    }


def install(root: pathlib.Path) -> dict:
    TRACE.V3.V2.V1.processes()
    compiled, block = candidate(root)
    old_log_sha = digest(root / "WeiDU.log")
    snap = backup(root)
    TRACE.V3.V2.V1.processes()
    baseline(root)
    if digest(root / "WeiDU.log") != old_log_sha:
        raise ValueError("WEIDU_CHANGED_AFTER_BACKUP")
    staging = root / COMPONENT / "staged"
    guard(staging)
    staging.mkdir(parents=True, exist_ok=False)
    (root / STAGED).write_bytes(compiled)
    (root / TP2).write_text(TP2_TEXT, encoding="utf-8", newline="\n")
    (root / PROOF).write_text(json.dumps({
        "old_sha": C.BASE_SHA, "new_sha": C.digest(compiled), "block": block,
        "backup": str(snap)}, indent=2), encoding="utf-8")
    shutil.copy2(root / "setup-enhanced-powergaming-scripts.exe", root / EXE)
    TRACE.V3.V2.V1.processes()
    if digest(root / "WeiDU.log") != old_log_sha or not TRACE.LAST.match(last(root)):
        raise ValueError("WEIDU_INTERLEAVED")
    if digest(root / TARGET) != C.BASE_SHA or digest(root / STAGED) != C.digest(compiled):
        raise ValueError("BCS_SHA_CHANGED_BEFORE_INSTALL")
    unchanged(root)
    run_weidu(root)
    verified = status(root)
    if verified.get("status") != "BGXFENEMY_INSTALLED_VERIFIED":
        raise ValueError("POST_INSTALL_NOT_VERIFIED")
    return dict(verified, game_modified=True, backup=str(snap))


def rollback(root: pathlib.Path) -> dict:
    TRACE.V3.V2.V1.processes()
    if not LAST.match(last(root)) or status(root)["status"] != "BGXFENEMY_INSTALLED_VERIFIED":
        raise ValueError("BGXFENEMY_NOT_LAST_OR_DRIFT")
    proof = json.loads((root / PROOF).read_text("utf-8"))
    snap = pathlib.Path(proof["backup"])
    checked_backup(snap)
    TRACE.V3.V2.V1.processes()
    run_weidu(root, remove=True)
    if not TRACE.LAST.match(last(root)):
        raise ValueError("BGXF3_NOT_RESTORED_AS_LAST")
    if digest(root / TARGET) != C.BASE_SHA:
        raise ValueError("WTASIGHT_ORIGINAL_NOT_RESTORED")
    unchanged(root)
    return {"status": "BGXFENEMY_ROLLBACK_VERIFIED_BGXF3_RESTORED", "game_modified": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "status", "install", "rollback"))
    parser.add_argument("--game", default=str(ROOT))
    a = parser.parse_args()
    root = pathlib.Path(a.game)
    try:
        if a.mode == "preflight":
            report = preflight(root)
        elif a.mode == "status":
            report = status(root)
        elif a.mode == "install":
            if input("Type " + INSTALL_TOKEN + " exactly: ").strip() != INSTALL_TOKEN:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            report = install(root)
        else:
            if input("Type " + ROLLBACK_TOKEN + " exactly: ").strip() != ROLLBACK_TOKEN:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            report = rollback(root)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print("BGXFENEMY_STOP:" + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
