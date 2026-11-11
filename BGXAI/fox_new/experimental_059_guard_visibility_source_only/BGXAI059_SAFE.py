#!/usr/bin/env python3
"""BGXAI 059 verified source fetch + opt-in guarded WeiDU Lua-only upgrade.

Default operation is read-only status. A fully pinned, immutable GitHub raw URL
is used only for fetch/preflight/install. No fallback to branch heads.
No game write without explicit `install --yes` and a verified external backup.
Never patches BDDEFAI.BCS; BGX56 remains installed.
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
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
REPO = "jeleZa112/nwn-xanos-updates"
COMMIT = "534b7aecc5ea6a3870583beac6678a2ad3677b6f"
SOURCE_PATH = "BGXAI/fox_new/experimental_059_guard_visibility_source_only/M_BX43.lua"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{SOURCE_PATH}"
SOURCE_BLOB = "0ce2b256f2b0d5ab9246b61e15c8b11d194cdea9"
BCS_SHA = "054c1c8e99b4d8ef8fb541287844d46cb81faa4c320f59c3f39f82f8bf0ab87c"
BASE_LUA_SHA = "35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab"
BCS = "override/BDDEFAI.BCS"
LUA = "override/M_BX43.lua"
STAGE = "BGX59"
STAGE_LUA = f"{STAGE}/M_BX43.lua"
STAGE_TP2 = f"{STAGE}/setup-BGX59.tp2"
EXE = "setup-BGX59.exe"
WEIDU_EXE = "setup-enhanced-powergaming-scripts.exe"
LAST_56 = re.compile(r"^~(?:[^~]*[/\\])?BGX56[/\\]SETUP-BGX56\.TP2~(?=\s|$)", re.I)
LAST_59 = re.compile(r"^~(?:[^~]*[/\\])?BGX59[/\\]SETUP-BGX59\.TP2~(?=\s|$)", re.I)
TP2_TEXT = "BACKUP ~BGX59/backup~\nAUTHOR ~BGXAI local safeguarded test~\nBEGIN ~BGXAI 059 eligible guard (Lua-only)~\nCOPY ~BGX59/M_BX43.lua~ ~override/M_BX43.lua~\n"
BACKUP_FILES = ("WeiDU.log", "chitin.key", "weidu.conf", "lang/ru_RU/dialog.tlk", "lang/ru_RU/dialogf.tlk", BCS, LUA)
MAX_SOURCE_BYTES = 100_000

class Stop(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (FileNotFoundError, AttributeError):
        return False


def secure_file(root: Path, rel: str, min_bytes: int = 1) -> Path:
    if rel.startswith("/") or rel.startswith("\\") or ":" in rel or "\\" in rel or ".." in Path(rel).parts:
        raise Stop("UNSAFE_RELATIVE_PATH: " + rel)
    p = root / rel
    for parent in (p, *p.parents):
        if is_reparse(parent):
            raise Stop("REPARSE_BLOCKED: " + str(parent))
        if parent == root:
            break
    if not p.is_file() or p.stat().st_size < min_bytes:
        raise Stop("MISSING_OR_EMPTY: " + rel)
    return p


def validate_source(data: bytes) -> dict:
    if not data or len(data) > MAX_SOURCE_BYTES:
        raise Stop("SOURCE_BYTES_OUTSIDE_LIMIT")
    if git_blob(data) != SOURCE_BLOB:
        raise Stop("SOURCE_BLOB_MISMATCH")
    try:
        s = data.decode("utf-8")
    except UnicodeError as e:
        raise Stop("SOURCE_UTF8_INVALID") from e
    required = [
        'P.version = "0.3.25-059-GUARD-VISIBILITY-SOURCE"',
        "BGX59Eligibility.choose(victim, options)",
        'EEex_UDEqual(guardArea,victimArea)',
        'guardian, "[ANYONE]", E.maxVisualDistancePixels',
        "function P.onWeaponHit(context)",
        "return false -- CRITICAL",
    ]
    if any(x not in s for x in required):
        raise Stop("SOURCE_SEMANTIC_PIN_MISMATCH")
    if s.count("function P.onWeaponHit(context)") != 1 or s.count("function B.prepare(advisory)") != 1:
        raise Stop("SOURCE_BRIDGE_STRUCTURE_MISMATCH")
    for line in s.splitlines():
        active = line.split("--", 1)[0]
        for forbidden in ("ClearActions(", "ActionOverride(", "QueueResponse(", "io.open(", "os.execute(", "ReallyForceSpell("):
            if forbidden in active:
                raise Stop("SOURCE_FORBIDDEN_COMMAND: " + forbidden)
    return {"git_blob": git_blob(data), "sha256": sha(data), "bytes": len(data)}


def fetch_source(opener=urllib.request.urlopen) -> bytes:
    # Read no more than MAX_SOURCE_BYTES+1; never trust HTTP Content-Length alone.
    req = urllib.request.Request(RAW_URL, headers={"User-Agent": "BGXAI059-verified-sources/1"})
    with opener(req, timeout=20) as r:
        data = r.read(MAX_SOURCE_BYTES + 1)
    validate_source(data)
    return data


def source_from_disk(path: Path) -> bytes:
    if is_reparse(path) or not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES:
        raise Stop("SOURCE_FILE_UNSAFE_OR_MISSING")
    data = path.read_bytes()
    validate_source(data)
    return data


def last_weidu(root: Path) -> str:
    p = secure_file(root, "WeiDU.log")
    entries = [x.strip() for x in p.read_text(encoding="utf-8-sig", errors="replace").splitlines() if x.lstrip().startswith("~")]
    if not entries:
        raise Stop("NO_WEIDU_ENTRIES")
    return entries[-1]


def game_check(root: Path, desired: str, new_source: bytes | None = None) -> dict:
    root = root.absolute()
    if not root.is_dir() or is_reparse(root):
        raise Stop("GAME_ROOT_MISSING_OR_REPARSE")
    secure_file(root, "chitin.key", 1000)
    executable = secure_file(root, WEIDU_EXE, 100000)
    with executable.open("rb") as f:
        if f.read(2) != b"MZ":
            raise Stop("WEIDU_IS_NOT_WINDOWS_EXECUTABLE")
    secure_file(root, "InfinityLoader.exe", 10000)
    got_last = last_weidu(root)
    match = LAST_56 if desired == "056" else LAST_59
    if not match.search(got_last):
        raise Stop("UNEXPECTED_LAST_MOD: " + got_last[:160])
    got_bcs = sha(secure_file(root, BCS).read_bytes())
    if got_bcs != BCS_SHA:
        raise Stop("BCS_HASH_DRIFT")
    got_lua = sha(secure_file(root, LUA).read_bytes())
    wanted = BASE_LUA_SHA if desired == "056" else sha(new_source or b"")
    if got_lua != wanted:
        raise Stop("LUA_HASH_DRIFT")
    for rel in BACKUP_FILES:
        secure_file(root, rel)
    if desired == "056":
        for rel in (STAGE, EXE):
            if (root / rel).exists() or is_reparse(root / rel):
                raise Stop("STAGING_ALREADY_PRESENT: " + rel)
    return {"last_mod": got_last, "bcs_sha256": got_bcs, "lua_sha256": got_lua}


def process_guard() -> None:
    if os.name != "nt":
        raise Stop("WINDOWS_REQUIRED_FOR_INSTALL_OR_ROLLBACK")
    ps = ('$ErrorActionPreference="Stop";Get-CimInstance Win32_Process | '
          'Where-Object {$_.Name -match "^(Baldur|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"} | '
          'ForEach-Object {"{0} PID={1}" -f $_.Name,$_.ProcessId}')
    p = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
    if p.returncode != 0 or p.stdout.strip():
        raise Stop("GAME_OR_WEIDU_RUNNING_OR_PROCESS_CHECK_FAILED: " + p.stdout[:350])


def backup_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents" / "BGXAI59_SAFE_BACKUPS"


def make_backup(root: Path, state: dict, tag: str, dest_root: Path | None = None) -> Path:
    dest = dest_root or backup_dir()
    if is_reparse(dest) or is_reparse(dest.parent):
        raise Stop("BACKUP_DESTINATION_REPARSE")
    dest.mkdir(parents=True, exist_ok=True)
    folder = dest / (tag + "_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(exist_ok=False)
    proofs = {}
    for rel in BACKUP_FILES:
        src = secure_file(root, rel)
        target = folder / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        digest = sha(src.read_bytes())
        if sha(target.read_bytes()) != digest:
            raise Stop("BACKUP_SHA_MISMATCH: " + rel)
        proofs[rel] = digest
    (folder / "BACKUP_PROOF.json").write_text(json.dumps({"state": state, "hashes": proofs}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return folder


def wei_run(root: Path, uninstall: bool = False, runner=subprocess.run) -> dict:
    cmd = [str(root / EXE), "--noautoupdate", "--no-exit-pause", "--game", str(root),
           "--use-lang", "ru_ru", "--force-uninstall" if uninstall else "--force-install", "0"]
    out = runner(cmd, cwd=str(root), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=180, check=False)
    return {"returncode": out.returncode, "stdout": out.stdout[-6000:], "stderr": out.stderr[-3000:]}


def install(root: Path, source: bytes, *, guard=process_guard, backup=make_backup, runner=subprocess.run) -> dict:
    # Safe even if called programmatically: never install without supplied verified data.
    verified = validate_source(source)
    guard()
    old = game_check(root, "056")
    saved = backup(root, old, "PRE_INSTALL")
    # External verified backup must exist before ANY writes to the game folder.
    if not (saved / "BACKUP_PROOF.json").is_file():
        raise Stop("BACKUP_PROOF_NOT_PRESENT")
    # Post-backup TOCTOU guard; only then stage one Lua source and TP2.
    guard()
    game_check(root, "056")
    (root / STAGE).mkdir(exist_ok=False)
    (root / STAGE_LUA).write_bytes(source)
    (root / STAGE_TP2).write_text(TP2_TEXT, encoding="utf8", newline="\n")
    shutil.copy2(root / WEIDU_EXE, root / EXE)
    if sha((root / STAGE_LUA).read_bytes()) != verified["sha256"]:
        raise Stop("STAGING_LUA_SHA_MISMATCH; EXTERNAL_BACKUP_EXISTS: " + str(saved))
    result = wei_run(root, runner=runner)
    (saved / "install_weidu.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if result["returncode"] != 0:
        raise Stop("WEIDU_INSTALL_FAILED; DO_NOT_RETRY_BLINDLY; BACKUP=" + str(saved))
    after = game_check(root, "059", source)
    return {"status": "INSTALLED_GUARDED_059", "backup": str(saved), "source": verified, "weidu": result, "after": after}


def rollback(root: Path, source: bytes, *, guard=process_guard, backup=make_backup, runner=subprocess.run) -> dict:
    verified = validate_source(source)
    guard()
    pre = game_check(root, "059", source)
    secure_file(root, STAGE_LUA)
    if sha((root / STAGE_LUA).read_bytes()) != verified["sha256"]:
        raise Stop("INSTALLED_STAGING_SOURCE_DRIFT")
    secure_file(root, STAGE_TP2)
    if secure_file(root, STAGE_TP2).read_text(encoding="utf8") != TP2_TEXT:
        raise Stop("TP2_CHANGED")
    secure_file(root, EXE, 100000)
    saved = backup(root, pre, "PRE_ROLLBACK")
    guard()
    game_check(root, "059", source)
    result = wei_run(root, uninstall=True, runner=runner)
    (saved / "rollback_weidu.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if result["returncode"] != 0:
        raise Stop("WEIDU_ROLLBACK_FAILED; RECOVERY_REVIEW_REQUIRED; BACKUP=" + str(saved))
    # WeiDU normally leaves the source package as files in game folder;
    # never delete them automatically, because backups might be needed.
    after_last = last_weidu(root)
    if not LAST_56.search(after_last):
        raise Stop("ROLLBACK_WEIDU_ORDER_UNEXPECTED: " + after_last)
    if sha(secure_file(root, BCS).read_bytes()) != BCS_SHA or sha(secure_file(root, LUA).read_bytes()) != BASE_LUA_SHA:
        raise Stop("ROLLBACK_FILES_NOT_RESTORED; BACKUP=" + str(saved))
    return {"status": "ROLLED_BACK_TO_056", "backup": str(saved), "weidu": result}


def cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("status", "fetch-only", "preflight", "install", "rollback"), nargs="?", default="status")
    ap.add_argument("--source", type=Path, help="Previously verified 059 Lua file (never auto-trust)")
    ap.add_argument("--yes", action="store_true", help="Explicit opt-in for game-modifying install/rollback")
    ap.add_argument("--confirm", default="", help="Required confirmation token for install/rollback")
    args = ap.parse_args()
    try:
        root = ROOT
        if args.mode == "status":
            last = last_weidu(root)
            bcs = sha(secure_file(root, BCS).read_bytes())
            lua = sha(secure_file(root, LUA).read_bytes())
            # Blob pin detects the 059 Lua already installed without any network access.
            found_bytes = secure_file(root, LUA).read_bytes()
            print("BGXAI059 STATUS READ-ONLY", json.dumps({"last": last, "bcs_expected": bcs == BCS_SHA,
                    "lua_is_056": lua == BASE_LUA_SHA,
                    "lua_is_pinned_059": git_blob(found_bytes) == SOURCE_BLOB}, ensure_ascii=False))
            return 0
        if args.mode in ("install", "rollback") and (not args.yes or args.confirm != "BGXAI_059_EXPERIMENTAL"):
            raise Stop("EXPLICIT_--yes_AND_--confirm_BGXAI_059_EXPERIMENTAL_REQUIRED; NO GAME FILES CHANGED")
        source = source_from_disk(args.source) if args.source else fetch_source()
        proof = validate_source(source)
        if args.mode == "fetch-only":
            # Only write to user working folder, never the EET game folder.
            target = Path.cwd() / "BGXAI059_M_BX43_VERIFIED.lua"
            if target.exists() or is_reparse(target):
                raise Stop("FETCH_DESTINATION_EXISTS: " + str(target))
            target.write_bytes(source)
            print("SOURCE FETCHED TO WORK DIRECTORY; NO GAME CHANGE", target, proof)
            return 0
        if args.mode == "preflight":
            print("PRECHECK READ-ONLY:", json.dumps({"source": proof, "game": game_check(root, "056")}, ensure_ascii=False))
            return 0
        result = install(root, source) if args.mode == "install" else rollback(root, source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Stop, OSError, UnicodeError, ValueError, TimeoutError) as e:
        print("BGXAI059 STOP:", str(e))
        return 2

if __name__ == "__main__":
    sys.exit(cli())
