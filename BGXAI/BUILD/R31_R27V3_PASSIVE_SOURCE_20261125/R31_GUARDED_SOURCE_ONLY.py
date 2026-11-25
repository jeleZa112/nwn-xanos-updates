"""BGXAI R31 source-only guarded WeiDU design. NO integration into updater yet.

Default/preflight/status are read-only. Game-changing paths require Windows,
the exact frozen 25-Nov R30 baseline, game closed, external SHA backup, typed
authorization, and a new last-only WeiDU component. NEVER auto-retry/rollback.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

GAME = Path(r"C:\Games\BG_EET_FOXX_NEW")
ROOT = Path(__file__).resolve().parent
PACKAGE = "BGXR31"
TP2 = "BGXR31/setup-BGXR31.tp2"
SETUP = "BGXR31/setup-BGXR31.exe"
STAGED = "BGXR31/staged/M_BGXR27.lua"
PROOF = "BGXR31/PROOF.json"
OVERRIDE = "override/M_BGXR27.lua"
SOURCE_SIZE = 47550
SOURCE_SHA = "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38"
OLD_R27_SHA = "e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735"
WEIDU_BASELINE_SHA = "3cec176f9e6eab721f7aa931c29e7e0d7a4a0d70fab346cffbbb4ae58960e0d6"
WEIDU_EXE_SHA = "0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75"
PINNED = {
    OVERRIDE: OLD_R27_SHA,
    "EEex/copy/EEex_scripts/EEex_Action.lua":
        "7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da",
    "EEex/copy/EEex_scripts/EEex_Sprite.lua":
        "4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28",
    "enhanced-powergaming-scripts/lib/core_base.tph":
        "1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776",
}
R27 = re.compile(r"^~(?:[^~]*[/\\])?BGXR27[/\\]SETUP-BGXR27[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
R29 = re.compile(r"^~(?:[^~]*[/\\])?BGXR29[/\\]SETUP-BGXR29[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
R31 = re.compile(r"^~(?:[^~]*[/\\])?BGXR31[/\\]SETUP-BGXR31[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
INSTALL_TOKEN = "INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29"
ROLLBACK_TOKEN = "ROLLBACK_BGXAI_R31_PASSIVE_V3_ONLY"
TP2_TEXT = (
    "BACKUP ~BGXR31/backup~\n"
    "AUTHOR ~BGXAI R31 passive EEex V3 observer~\n"
    "BEGIN ~BGXR31 passive R27V3 observer only~\n"
    "COPY ~BGXR31/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n"
)
EXTRA_BASELINE = ("WeiDU.log", "chitin.key", "override/BDDEFAI.BCS",
                  "override/DPLAYER.BCS")
SCHEMA = "BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1"


class Hold(ValueError):
    pass


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe(root: Path, rel: str) -> Path:
    if not rel or rel.startswith(("/", "\\")) or ":" in rel or "\x00" in rel:
        raise Hold("BAD_RELATIVE_PATH")
    path = root
    for name in rel.replace("\\", "/").split("/"):
        if name in ("", ".", ".."):
            raise Hold("BAD_PATH_COMPONENT")
        path = path / name
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise Hold("REPARSE_POINT_DENIED:" + rel)
    return path


def protected_root(root: Path, live: bool) -> None:
    if live:
        if os.name != "nt" or os.path.normcase(os.path.abspath(root)) != os.path.normcase(os.path.abspath(GAME)):
            raise Hold("EXACT_WINDOWS_GAME_ROOT_REQUIRED")
    if not root.is_dir() or root.is_symlink() or (
        hasattr(root, "is_junction") and root.is_junction()
    ):
        raise Hold("GAME_ROOT_MISSING_OR_REPARSE_POINT")


def verify_processes() -> None:
    if os.name != "nt":
        raise Hold("WINDOWS_REQUIRED")
    cmd = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                         stdin=subprocess.DEVNULL, text=True, capture_output=True,
                         errors="replace", timeout=25, check=False)
    if cmd.returncode:
        raise Hold("TASKLIST_FAILED")
    processes = {row[0].strip().lower() for row in csv.reader(io.StringIO(cmd.stdout)) if row}
    blockers = {"baldur.exe", "bgmain.exe", "infinityloader.exe", "weidu.exe",
                "setup-enhanced-powergaming-scripts.exe", "setup-bgxr29.exe",
                "setup-bgxr31.exe"}
    if processes & blockers:
        raise Hold("CLOSE_GAME_AND_WEIDU:" + ",".join(sorted(processes & blockers)))


def weidu_components(root: Path) -> tuple[list[str], str]:
    file = safe(root, "WeiDU.log")
    if not file.is_file() or file.stat().st_size > 4_000_000:
        raise Hold("WEIDU_LOG_MISSING_OR_OVERSIZE")
    data = file.read_bytes()
    rows = []
    for line in data.decode("utf-8-sig", errors="replace").splitlines():
        value = line.strip()
        if not value or value.startswith("//") or value.startswith("#"):
            continue
        if not re.match(r"^~[^~]+~\s+#\d+\s+#\d+(?:\s|$)", value):
            raise Hold("UNKNOWN_WEIDU_RECORD")
        rows.append(value)
    if not rows:
        raise Hold("WEIDU_COMPONENTS_MISSING")
    return rows, hashlib.sha256(data).hexdigest()


def candidate_data(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != SOURCE_SIZE:
        raise Hold("R31_CANDIDATE_MISSING_OR_BAD_SIZE")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA:
        raise Hold("R31_CANDIDATE_SHA_DRIFT")
    forbidden = (b"SelectWeaponAbility(", b"ClearActions(", b"ActionOverride(",
                 b"EEex_Action_QueueScriptFileResponseOnAIBase(")
    if any(token in data for token in forbidden):
        raise Hold("R31_CANDIDATE_DISPATCH_FORBIDDEN")
    if data.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1:
        raise Hold("R31_CANDIDATE_LISTENER_COUNT_INVALID")
    return data


def baseline(root: Path, candidate: Path, live: bool = True) -> dict:
    protected_root(root, live)
    rows, log_hash = weidu_components(root)
    if log_hash != WEIDU_BASELINE_SHA:
        raise Hold("WEIDU_BASELINE_SHA_DRIFT")
    if len(rows) != 150 or not R27.match(rows[148]) or not R29.match(rows[-1]):
        raise Hold("R27_149_R29_150_HISTORY_REQUIRED")
    if any(R31.match(row) for row in rows):
        raise Hold("R31_ALREADY_IN_WEIDU")
    for rel, expected in PINNED.items():
        item = safe(root, rel)
        if not item.is_file() or sha(item) != expected:
            raise Hold("INSTALLED_SHA_DRIFT:" + rel)
    staged = candidate_data(candidate)
    for rel in (PACKAGE, TP2, SETUP, STAGED, PROOF):
        if safe(root, rel).exists():
            raise Hold("R31_STAGING_COLLISION:" + rel)
    exe = safe(root, "setup-enhanced-powergaming-scripts.exe")
    if not exe.is_file() or sha(exe) != WEIDU_EXE_SHA:
        raise Hold("NATIVE_WEIDU_BINARY_SHA_DRIFT")
    if live:
        verify_processes()
    hashes = {}
    for rel in list(PINNED) + list(EXTRA_BASELINE):
        item = safe(root, rel)
        if not item.is_file():
            if rel in ("override/BDDEFAI.BCS", "override/DPLAYER.BCS"):
                continue  # missing optional file is recorded as absent; not created
            raise Hold("BASELINE_FILE_MISSING:" + rel)
        hashes[rel] = sha(item)
    return {
        "schema": SCHEMA, "status": "R31_SOURCE_PREFLIGHT_PASS_INSTALL_STILL_UNAUTHORIZED",
        "weiduComponentCount": 150, "r27ComponentPosition": 149,
        "weiduLastComponent": rows[-1], "sourceSha256": SOURCE_SHA,
        "sourceBytes": len(staged), "baselineSnapshot": hashes,
        "ordersSent": 0, "dispatchAuthorized": False,
        "typedInstallApproved": False, "installationPerformed": False,
        "gameModified": False, "queueBindingLiveVerified": False,
        "manualEpsOriginVerified": False, "alternateEffectiveAPRVerified": False,
    }


def ensure_snapshot(root: Path, expected: dict[str, str]) -> None:
    for rel, wanted in expected.items():
        item = safe(root, rel)
        if not item.is_file() or sha(item) != wanted:
            raise Hold("BASELINE_CHANGED:" + rel)


def backup(root: Path, baseline_hashes: dict[str, str]) -> Path:
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    parent = Path(home) / "Documents" / "BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
        raise Hold("BACKUP_PARENT_REPARSE_POINT")
    parent.mkdir(parents=True, exist_ok=True)
    dest = Path(tempfile.mkdtemp(prefix="PRE_BGXR31_", dir=parent))
    for rel, digest in baseline_hashes.items():
        source = safe(root, rel)
        target = safe(dest, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(target) != digest:
            raise Hold("EXTERNAL_BACKUP_SHA_MISMATCH:" + rel)
    (dest / "SHA256.json").write_text(json.dumps(baseline_hashes, indent=2), encoding="utf-8")
    return dest


def invoke_weidu(root: Path, uninstall: bool = False) -> None:
    exe = safe(root, SETUP)
    if sha(exe) != WEIDU_EXE_SHA:
        raise Hold("R31_STAGED_WEIDU_SHA_DRIFT")
    argv = [str(exe), "--noautoupdate", "--no-exit-pause",
            "--game", str(root), "--use-lang", "ru_ru",
            "--force-uninstall" if uninstall else "--force-install", "0"]
    output = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, errors="replace", timeout=240, check=False)
    transcript = (output.stdout or "") + "\n" + (output.stderr or "")
    if output.returncode or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)", transcript):
        raise Hold("R31_WEIDU_FAILED_MANUAL_REVIEW:" + transcript[-600:])


def install(root: Path, candidate: Path, token: str) -> dict:
    if token != INSTALL_TOKEN:
        raise Hold("EXACT_TYPED_INSTALL_CONSENT_REQUIRED")
    pre = baseline(root, candidate, True)
    hashes = pre["baselineSnapshot"]
    ensure_snapshot(root, hashes)
    b = backup(root, hashes)
    verify_processes()
    ensure_snapshot(root, hashes)
    package = safe(root, PACKAGE)
    package.mkdir(parents=True, exist_ok=False)
    stage = safe(root, STAGED)
    stage.parent.mkdir(parents=True, exist_ok=False)
    stage.write_bytes(candidate_data(candidate))
    safe(root, TP2).write_text(TP2_TEXT, encoding="ascii", newline="\n")
    shutil.copy2(safe(root, "setup-enhanced-powergaming-scripts.exe"), safe(root, SETUP))
    if sha(stage) != SOURCE_SHA or sha(safe(root, SETUP)) != WEIDU_EXE_SHA:
        raise Hold("R31_STAGE_SHA_MISMATCH")
    verify_processes()
    ensure_snapshot(root, hashes)
    proof = safe(root, PROOF)
    proof.write_text(json.dumps({"schema": SCHEMA, "status": "R31_PENDING_WEIDU",
                                 "sourceSha256": SOURCE_SHA,
                                 "externalBackup": str(b), "baselineSnapshot": hashes},
                                indent=2), encoding="utf-8")
    invoke_weidu(root)
    rows, _ = weidu_components(root)
    if not R31.match(rows[-1]) or sha(safe(root, OVERRIDE)) != SOURCE_SHA:
        raise Hold("R31_POST_WEIDU_UNKNOWN_MANUAL_REVIEW")
    for rel, value in hashes.items():
        if rel not in ("WeiDU.log", OVERRIDE) and sha(safe(root, rel)) != value:
            raise Hold("R31_UNRELATED_GAME_RESOURCE_CHANGED:" + rel)
    proof_data = {"schema": SCHEMA, "status": "R31_PASSIVE_INSTALLED_AWAITING_RUNTIME",
                  "sourceSha256": SOURCE_SHA, "externalBackup": str(b),
                  "baselineSnapshot": hashes, "typedInstallApproved": True,
                  "gameModified": True, "installationPerformed": True,
                  "dispatchAuthorized": False, "weaponSwitchAuthorized": False,
                  "queueBindingLiveVerified": False, "manualEpsOriginVerified": False}
    proof.write_text(json.dumps(proof_data, indent=2), encoding="utf-8")
    return proof_data


def rollback(root: Path, token: str) -> dict:
    if token != ROLLBACK_TOKEN:
        raise Hold("EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED")
    protected_root(root, True)
    verify_processes()
    rows, _ = weidu_components(root)
    if len(rows) != 151 or not R31.match(rows[-1]) or not R29.match(rows[-2]):
        raise Hold("R31_NOT_LAST_NO_ROLLBACK")
    if sha(safe(root, OVERRIDE)) != SOURCE_SHA:
        raise Hold("R31_LIVE_RESOURCE_SHA_DRIFT")
    proof_file = safe(root, PROOF)
    if not proof_file.is_file():
        raise Hold("R31_PROOF_MISSING")
    p = json.loads(proof_file.read_text(encoding="utf-8"))
    if p.get("status") != "R31_PASSIVE_INSTALLED_AWAITING_RUNTIME" or p.get("sourceSha256") != SOURCE_SHA:
        raise Hold("R31_PROOF_UNTRUSTED")
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    expected_parent = Path(home) / "Documents" / "BGXAI_BACKUPS"
    b = Path(p.get("externalBackup", ""))
    if b.parent != expected_parent or not b.name.startswith("PRE_BGXR31_") or not b.is_dir() or b.is_symlink():
        raise Hold("BACKUP_PROVENANCE_INVALID")
    hashes = json.loads(safe(b, "SHA256.json").read_text(encoding="utf-8"))
    if hashes != p.get("baselineSnapshot") or hashes.get(OVERRIDE) != OLD_R27_SHA or hashes.get("WeiDU.log") != WEIDU_BASELINE_SHA:
        raise Hold("BACKUP_MANIFEST_MISMATCH")
    ensure_snapshot(b, hashes)
    if sha(safe(root, SETUP)) != WEIDU_EXE_SHA:
        raise Hold("R31_WEIDU_BINARY_SHA_DRIFT")
    invoke_weidu(root, uninstall=True)
    rows, _ = weidu_components(root)
    if not R29.match(rows[-1]) or sha(safe(root, OVERRIDE)) != OLD_R27_SHA:
        raise Hold("R31_ROLLBACK_NOT_VERIFIED_MANUAL_REVIEW")
    for rel, value in hashes.items():
        if rel not in ("WeiDU.log", OVERRIDE) and sha(safe(root, rel)) != value:
            raise Hold("R31_ROLLBACK_UNRELATED_RESOURCE_DRIFT:" + rel)
    return {"schema": SCHEMA, "status": "R31_ROLLBACK_R29_RESTORED",
            "gameModified": True, "weaponSwitchAuthorized": False}


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--game", type=Path, default=GAME)
    cli.add_argument("--candidate", type=Path)
    cli.add_argument("--mode", choices=["preflight", "status", "install", "rollback"],
                     default="preflight")
    a = cli.parse_args()
    try:
        if a.mode == "status":
            protected_root(a.game, True)
            rows, _ = weidu_components(a.game)
            result = {"schema": SCHEMA, "status": "R31_PRESENT_LAST" if R31.match(rows[-1])
                      else "R31_NOT_LAST_OR_NOT_INSTALLED", "weiduLastComponent": rows[-1],
                      "gameModified": False, "ordersSent": 0}
        elif a.mode == "preflight":
            if not a.candidate:
                raise Hold("CANDIDATE_REQUIRED")
            result = baseline(a.game, a.candidate, True)
        elif a.mode == "install":
            if not a.candidate:
                raise Hold("CANDIDATE_REQUIRED")
            print("R31 passive R27 V3 OBSERVER ONLY. No weapon actions.")
            token = input("Type " + INSTALL_TOKEN + " exactly (ENTER cancels): ").strip()
            result = install(a.game, a.candidate, token)
        else:
            token = input("Type " + ROLLBACK_TOKEN + " exactly (ENTER cancels): ").strip()
            result = rollback(a.game, token)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Hold, OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "R31_STOP_MANUAL_REVIEW",
                          "reason": str(exc), "noAutoRetry": True,
                          "gameModifiedUnknown": a.mode in ("install", "rollback")},
                         ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
