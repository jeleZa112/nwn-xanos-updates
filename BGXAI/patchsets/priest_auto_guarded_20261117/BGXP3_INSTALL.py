#!/usr/bin/env python3
"""BGXP3 guarded WeiDU replacement of ONLY the last BGXP2 AUTO attack block.

No install without exact Windows root, explicit typed approval, real EET native
compile, original BGXP2 hashes, checked external backup, and last WeiDU entry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import BGXP3_BCS_PREFLIGHT_SOURCE_ONLY as PREF
import BGXP2_BCS_PATCH as BCS
from BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY import candidate, SOURCE

ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
BASE = Path(__file__).resolve().parent
BCS_PATH = "override/BDDEFAI.BCS"
LUA_PATH = "override/M_BX43.lua"
WEIDU_PATH = "setup-enhanced-powergaming-scripts.exe"
STAGE = "BGXP3/staged/BDDEFAI.BCS"
PROOF = "BGXP3/STAGED_PROOF.json"
TP2 = "BGXP3/setup-BGXP3.tp2"
EXE = "setup-BGXP3.exe"
BACKUP = ("WeiDU.log", "chitin.key", "weidu.conf",
          "lang/ru_RU/dialog.tlk", "lang/ru_RU/dialogf.tlk",
          LUA_PATH, BCS_PATH)
TP2_TEXT = ("BACKUP ~BGXP3/backup~\n"
            "AUTHOR ~BGXAI guarded AUTO attack safety buffer~\n"
            "BEGIN ~BGXAI BGXP3 preserve 1157 blocks and replace only AUTO attack~\n"
            "COPY ~BGXP3/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n")
INSTALL_TOKEN = "INSTALL_BGXP3_AUTO_HEAL_GUARD"
ROLLBACK_TOKEN = "ROLLBACK_BGXP3_AUTO_HEAL_GUARD"
BGXP2_LAST = re.compile(r"^~(?:[^~]*[/\\])?BGXP2[/\\]SETUP-BGXP2[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
BGXP3_LAST = re.compile(r"^~(?:[^~]*[/\\])?BGXP3[/\\]SETUP-BGXP3[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)


class Stop(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_link(path: Path):
    if path.is_symlink():
        raise Stop("SYMLINK_BLOCKED:" + str(path))
    try:
        if path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Stop("REPARSE_BLOCKED:" + str(path))
    except (AttributeError, FileNotFoundError):
        pass


def guarded_file(root: Path, name: str, size: int = 1) -> Path:
    if not name or "\\" in name or ":" in name or name.startswith("/") or ".." in name.split("/"):
        raise Stop("INVALID_RELATIVE_PATH:" + name)
    path = root / name
    for ancestor in (path, *path.parents):
        no_link(ancestor)
        if ancestor == root:
            break
    if not path.is_file() or path.stat().st_size < size:
        raise Stop("MISSING_OR_SMALL_FILE:" + name)
    return path


def sources() -> dict:
    manifest_path = BASE / "SHA256_FILES.json"
    no_link(manifest_path)
    manifest = json.loads(manifest_path.read_text("utf-8"))
    allowed = manifest.get("sha256", {})
    if manifest.get("schema") != 1 or not allowed or set(manifest.get("files", [])) != set(allowed):
        raise Stop("SOURCE_MANIFEST_STRUCTURE_INVALID")
    for name, expected in allowed.items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise Stop("SOURCE_MANIFEST_ENTRY_INVALID:" + name)
        src = BASE / name
        no_link(src)
        if not src.is_file() or digest(src.read_bytes()) != expected:
            raise Stop("SOURCE_SHA256_INVALID:" + name)
    if SOURCE.parent.resolve() != BASE.resolve():
        raise Stop("SOURCE_BAF_NOT_BUNDLED")
    candidate(SOURCE.read_bytes())
    return manifest


def last_weidu(root: Path) -> str:
    content = guarded_file(root, "WeiDU.log").read_text("utf-8-sig", errors="replace")
    lines = [line.strip() for line in content.splitlines() if line.strip().startswith("~")]
    if not lines:
        raise Stop("WEIDU_LOG_EMPTY")
    return lines[-1]


def baseline(root: Path, allow_stage: bool = False) -> dict:
    root = root.resolve(strict=True)
    no_link(root)
    entry = last_weidu(root)
    if not BGXP2_LAST.match(entry):
        raise Stop("BGXP2_NOT_LAST_WEIDU:" + entry)
    original = guarded_file(root, BCS_PATH).read_bytes()
    if digest(original) != PREF.LIVE_BCS_SHA:
        raise Stop("INSTALLED_BGXP2_BCS_CHANGED")
    if digest(guarded_file(root, LUA_PATH).read_bytes()) != PREF.LIVE_LUA_SHA:
        raise Stop("INSTALLED_BGXP2_LUA_CHANGED")
    BCS.chunks(original, 1158)
    prior_proof = json.loads(guarded_file(root, "BGXP2/STAGED_PROOF.json").read_text("utf-8"))
    if prior_proof.get("new_bcs_sha256") != PREF.LIVE_BCS_SHA or prior_proof.get("lua_sha256") != PREF.LIVE_LUA_SHA:
        raise Stop("BGXP2_PROOF_MISMATCH")
    if not allow_stage and ((root / "BGXP3").exists() or (root / EXE).exists()):
        raise Stop("BGXP3_STAGE_ALREADY_EXISTS")
    return {"state": "BGXP2_INSTALLED_VERIFIED", "last_weidu": entry,
            "bcs_sha256": PREF.LIVE_BCS_SHA, "lua_sha256": PREF.LIVE_LUA_SHA}


def installed(root: Path) -> dict:
    root = root.resolve(strict=True)
    if not BGXP3_LAST.match(last_weidu(root)):
        raise Stop("BGXP3_NOT_LAST_WEIDU")
    if guarded_file(root, TP2).read_text("utf-8") != TP2_TEXT:
        raise Stop("BGXP3_TP2_DRIFT")
    proof = json.loads(guarded_file(root, PROOF).read_text("utf-8"))
    if proof.get("old_bcs_sha256") != PREF.LIVE_BCS_SHA or proof.get("lua_sha256") != PREF.LIVE_LUA_SHA:
        raise Stop("BGXP3_PROOF_MISMATCH")
    raw = guarded_file(root, BCS_PATH).read_bytes()
    if digest(raw) != proof.get("new_bcs_sha256") or digest(guarded_file(root, STAGE).read_bytes()) != digest(raw):
        raise Stop("BGXP3_BCS_OR_STAGE_CHANGED")
    if digest(guarded_file(root, LUA_PATH).read_bytes()) != PREF.LIVE_LUA_SHA:
        raise Stop("BGXP3_LUA_CHANGED")
    blocks = BCS.chunks(raw, 1158)
    previous = BCS.chunks(guarded_file(root, "BGXP2/staged/BDDEFAI.BCS").read_bytes(), 1158)
    if digest(b"SC\n" + b"".join(previous)) != PREF.LIVE_BCS_SHA:
        raise Stop("BGXP2_STAGED_BASELINE_CHANGED")
    if blocks[:1157] != previous[:1157] or blocks[1157] == previous[1157]:
        raise Stop("BGXP3_UNEXPECTED_BCS_DELTA")
    return {"state": "BGXP3_INSTALLED_VERIFIED", "total_blocks": len(blocks),
            "old_bcs_sha256": PREF.LIVE_BCS_SHA, "bcs_sha256": digest(raw),
            "lua_sha256": PREF.LIVE_LUA_SHA}


def process_guard():
    if os.name != "nt":
        raise Stop("WINDOWS_ONLY")
    command = ('$ErrorActionPreference="Stop"; $p=Get-CimInstance Win32_Process | '
               'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
               'if($p){$p|Select-Object Name,ProcessId|Out-String;exit 3}')
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                            capture_output=True, text=True, stdin=subprocess.DEVNULL,
                            timeout=30, check=False)
    if result.returncode or result.stdout.strip():
        raise Stop("GAME_OR_WEIDU_RUNNING_OR_CHECK_FAILED:" + result.stdout[-500:])


def snapshot(root: Path, state: dict, prefix: str) -> Path:
    parent = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents" / "BGXAI_PRIEST3_SAFE_BACKUPS"
    no_link(parent)
    no_link(parent.parent)
    if root.resolve(strict=True) == parent.resolve() or root.resolve(strict=True) in parent.resolve().parents:
        raise Stop("BACKUP_MUST_BE_OUTSIDE_GAME")
    parent.mkdir(parents=True, exist_ok=True)
    folder = parent / (prefix + "_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(exist_ok=False)
    hashes = {}
    for name in BACKUP:
        source = guarded_file(root, name)
        destination = folder / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[name] = digest(source.read_bytes())
        if hashes[name] != digest(destination.read_bytes()):
            raise Stop("BACKUP_HASH_MISMATCH:" + name)
    (folder / "PROOF.json").write_text(json.dumps({"state": state, "sha256": hashes}, indent=2) + "\n", encoding="utf-8")
    return folder


def verify_other_files(root: Path, backup: Path):
    expected = json.loads((backup / "PROOF.json").read_text("utf-8"))["sha256"]
    for name in BACKUP:
        if name not in (BCS_PATH, "WeiDU.log") and digest(guarded_file(root, name).read_bytes()) != expected[name]:
            raise Stop("NON_TARGET_FILE_CHANGED:" + name)


def run_weidu(root: Path, uninstall: bool = False) -> str:
    exe = guarded_file(root, EXE, 100000)
    args = [str(exe), "--noautoupdate", "--no-exit-pause", "--game", str(root), "--use-lang", "ru_ru",
            "--force-uninstall" if uninstall else "--force-install", "0"]
    output = subprocess.run(args, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=200, check=False)
    lines = (output.stdout or "") + "\n" + (output.stderr or "")
    if output.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)", lines):
        raise Stop("WEIDU_FAILED_NO_AUTORETRY:" + lines[-1800:])
    return lines[-1900:]


def preflight(root: Path) -> dict:
    sources()
    prior = baseline(root)
    for name in BACKUP:
        guarded_file(root, name)
    exe = guarded_file(root, WEIDU_PATH, 100000)
    if exe.read_bytes()[:2] != b"MZ":
        raise Stop("WEIDU_EXE_MZ_INVALID")
    result = PREF.preflight(root)
    if result["old_sha256"] != PREF.LIVE_BCS_SHA or result["preserved_blocks_exact"] != 1157:
        raise Stop("NATIVE_BCS_PREFLIGHT_RESULT_INVALID")
    result.update({"status": "BGXP3_EET_READ_ONLY_PASS", "baseline": prior,
                   "authorized_to_install": False})
    return result


def install(root: Path) -> dict:
    process_guard()
    root = root.resolve(strict=True)
    ready = preflight(root)
    prior_log_hash = digest(guarded_file(root, "WeiDU.log").read_bytes())
    saved = snapshot(root, ready["baseline"], "PRE_INSTALL")
    process_guard()
    baseline(root)
    if digest(guarded_file(root, "WeiDU.log").read_bytes()) != prior_log_hash:
        raise Stop("WEIDU_LOG_CHANGED_DURING_PREFLIGHT")
    new = PREF.preflight(root)
    if new.get("proposed_sha256") != ready.get("proposed_sha256"):
        raise Stop("NONDETERMINISTIC_NATIVE_BCS")
    # Only NOW create staging, after the exact baseline, external backup and compile.
    directory = root / "BGXP3"
    directory.mkdir(exist_ok=False)
    (directory / "staged").mkdir(exist_ok=False)
    # Assemble again with the exact native compiler, keeping the compiled BCS in memory.
    old_fragment = BCS.compile_fragment(root, guarded_file(root, WEIDU_PATH),
                                       guarded_file(root, "lang/ru_RU/dialog.tlk"), SOURCE)
    import tempfile
    with tempfile.TemporaryDirectory(prefix="BGXP3_INSTALL_NATIVE_") as temp:
        patch = Path(temp) / "BGXP3.baf"
        patch.write_bytes(candidate(SOURCE.read_bytes()))
        new_fragment = BCS.compile_fragment(root, guarded_file(root, WEIDU_PATH),
                                           guarded_file(root, "lang/ru_RU/dialog.tlk"), patch)
    merged, details = PREF.assemble(guarded_file(root, BCS_PATH).read_bytes(), old_fragment, new_fragment)
    if details["proposed_sha256"] != ready["proposed_sha256"]:
        raise Stop("FINAL_BCS_SHA_MISMATCH")
    (root / STAGE).write_bytes(merged)
    (root / PROOF).write_text(json.dumps({"old_bcs_sha256": PREF.LIVE_BCS_SHA,
                                          "new_bcs_sha256": digest(merged),
                                          "lua_sha256": PREF.LIVE_LUA_SHA}, indent=2) + "\n", encoding="utf-8")
    (root / TP2).write_text(TP2_TEXT, encoding="utf-8", newline="\n")
    shutil.copy2(guarded_file(root, WEIDU_PATH), root / EXE)
    process_guard()
    baseline(root, allow_stage=True)
    if digest(guarded_file(root, "WeiDU.log").read_bytes()) != prior_log_hash:
        raise Stop("WEIDU_LOG_CHANGED_BEFORE_INSTALL")
    log = run_weidu(root)
    (saved / "weidu_install_log_tail.txt").write_text(log, encoding="utf-8")
    after = installed(root)
    verify_other_files(root, saved)
    return {"status": "BGXP3_INSTALLED_VERIFIED", "backup": str(saved), "after": after}


def rollback(root: Path) -> dict:
    process_guard()
    root = root.resolve(strict=True)
    current = installed(root)
    backup = snapshot(root, current, "PRE_ROLLBACK")
    process_guard()
    installed(root)
    result = run_weidu(root, uninstall=True)
    (backup / "weidu_rollback_log_tail.txt").write_text(result, encoding="utf-8")
    after = baseline(root, allow_stage=True)
    verify_other_files(root, backup)
    return {"status": "BGXP3_RETURNED_TO_BGXP2_VERIFIED", "backup": str(backup), "after": after}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["status", "preflight", "install", "rollback"], nargs="?", default="status")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--game-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        sources()
        if args.mode == "status":
            root = args.game_root
            check = installed(root) if BGXP3_LAST.match(last_weidu(root)) else baseline(root, allow_stage=True)
            outcome = {"status": "READ_ONLY_STATUS", "game": check}
        elif args.mode == "preflight":
            outcome = preflight(args.game_root)
        else:
            token = INSTALL_TOKEN if args.mode == "install" else ROLLBACK_TOKEN
            if not args.yes or args.confirm != token:
                raise Stop("EXPLICIT_TYPED_APPROVAL_REQUIRED:" + token)
            if os.name != "nt" or args.game_root != ROOT:
                raise Stop("LIVE_INSTALL_REQUIRES_EXACT_WINDOWS_ROOT")
            outcome = install(ROOT) if args.mode == "install" else rollback(ROOT)
        print(json.dumps(outcome, ensure_ascii=False, indent=2))
        return 0
    except (Stop, ValueError, OSError, UnicodeError, subprocess.TimeoutExpired, KeyError) as exc:
        print("BGXP3_STOP:", str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
