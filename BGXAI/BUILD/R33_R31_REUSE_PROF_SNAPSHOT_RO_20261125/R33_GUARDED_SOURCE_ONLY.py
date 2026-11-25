"""BGXAI R33: guarded, SHA-pinned, LAST-ONLY R31 -> R33 passive upgrade.

This source alone DOES NOT install. Default status/preflight never change game.
Only exact typed approval authorizes install; rollback is separately typed.
All game writes through a NEW WeiDU last component; baseline R31 remains backed.
Never auto-retry or restore files manually on ambiguous WeiDU errors.
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

ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
SCHEMA = "BGXAI_R33_R31_PASSIVE_PROF_GUARDED_V1"
OVERRIDE = "override/M_BGXR27.lua"
R31_PROOF = "BGXR31/PROOF.json"
R33_PROOF = "BGXR33/PROOF.json"
STAGED = "BGXR33/staged/M_BGXR27.lua"
TP2 = "BGXR33/setup-BGXR33.tp2"
SETUP = "BGXR33/setup-BGXR33.exe"
R33_DIR = "BGXR33"
R31_SHA = "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38"
R33_SHA = "1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069"
R33_SIZE = 49438
NATIVE_SHA = "0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75"
WEIDU_PRE_R31_SHA = "3cec176f9e6eab721f7aa931c29e7e0d7a4a0d70fab346cffbbb4ae58960e0d6"
BASELINE_SHA = {
    "EEex/copy/EEex_scripts/EEex_Action.lua": "7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da",
    "EEex/copy/EEex_scripts/EEex_Sprite.lua": "4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28",
    "enhanced-powergaming-scripts/lib/core_base.tph": "1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776",
    "chitin.key": "ad67498a222043421c39bcdb2026abf6cdf0fbd160cba51135ab61d6a85d9515",
    "override/BDDEFAI.BCS": "24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331",
    "override/DPLAYER.BCS": "4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed",
}
WATCHED = ("WeiDU.log", OVERRIDE, R31_PROOF, *BASELINE_SHA)
INSTALL_TOKEN = "INSTALL_BGXAI_R33_PASSIVE_PROF_AFTER_R31"
ROLLBACK_TOKEN = "ROLLBACK_BGXAI_R33_PASSIVE_PROF_ONLY"
TP2_TEXT = (
    "BACKUP ~BGXR33/backup~\n"
    "AUTHOR ~BGXAI R33 passive R31 R4 proficiency snapshot~\n"
    "BEGIN ~BGXR33 passive R27V3 prof snapshot only~\n"
    "COPY ~BGXR33/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n"
)
R27 = re.compile(r"^~(?:[^~]*[/\\])?BGXR27[/\\]SETUP-BGXR27[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
R29 = re.compile(r"^~(?:[^~]*[/\\])?BGXR29[/\\]SETUP-BGXR29[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
R31 = re.compile(r"^~(?:[^~]*[/\\])?BGXR31[/\\]SETUP-BGXR31[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
R33 = re.compile(r"^~(?:[^~]*[/\\])?BGXR33[/\\]SETUP-BGXR33[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)


class Hold(ValueError):
    pass


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe(root: Path, rel: str) -> Path:
    if not rel or rel.startswith(("/", "\\")) or ":" in rel or "\x00" in rel:
        raise Hold("INVALID_RELATIVE_PATH")
    dst = root
    for item in rel.replace("\\", "/").split("/"):
        if item in ("", ".", ".."):
            raise Hold("INVALID_PATH_COMPONENT")
        dst = dst / item
        if dst.is_symlink() or (hasattr(dst, "is_junction") and dst.is_junction()):
            raise Hold("SYMLINK_OR_JUNCTION_DENIED:" + rel)
    return dst


def protected_root(root: Path, live: bool = True) -> None:
    if live and (os.name != "nt" or os.path.normcase(os.path.abspath(root)) !=
                 os.path.normcase(os.path.abspath(ROOT))):
        raise Hold("EXACT_WINDOWS_FOXX_ROOT_REQUIRED")
    if not root.is_dir() or root.is_symlink() or (
        hasattr(root, "is_junction") and root.is_junction()
    ):
        raise Hold("GAME_ROOT_MISSING_OR_REPARSE_POINT")


def verify_processes() -> None:
    if os.name != "nt":
        raise Hold("WINDOWS_REQUIRED_FOR_MUTATION")
    p = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, errors="replace", timeout=25, check=False)
    if p.returncode:
        raise Hold("TASKLIST_FAILED")
    names = {r[0].strip().lower() for r in csv.reader(io.StringIO(p.stdout)) if r}
    blocker = {"baldur.exe", "bgmain.exe", "infinityloader.exe", "weidu.exe",
               "setup-enhanced-powergaming-scripts.exe", "setup-bgxr29.exe",
               "setup-bgxr31.exe", "setup-bgxr33.exe"}
    if names & blocker:
        raise Hold("CLOSE_GAME_AND_WEIDU:" + ",".join(sorted(names & blocker)))


def history(root: Path) -> tuple[list[str], str]:
    log = safe(root, "WeiDU.log")
    if not log.is_file() or log.stat().st_size > 4_000_000:
        raise Hold("WEIDU_LOG_MISSING_OR_TOO_LARGE")
    b = log.read_bytes()
    rows = []
    for line in b.decode("utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith(("//", "#")):
            continue
        if not re.match(r"^~[^~]+~\s+#\d+\s+#\d+(?:\s|$)", line):
            raise Hold("UNKNOWN_WEIDU_RECORD")
        rows.append(line)
    if not rows:
        raise Hold("EMPTY_WEIDU_HISTORY")
    return rows, hashlib.sha256(b).hexdigest()


def candidate_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != R33_SIZE:
        raise Hold("R33_CANDIDATE_BAD_SIZE_OR_MISSING")
    b = path.read_bytes()
    if hashlib.sha256(b).hexdigest() != R33_SHA:
        raise Hold("R33_CANDIDATE_SHA_DRIFT")
    for command in (b"SelectWeaponAbility(", b"ClearActions(", b"ActionOverride(",
                    b"EEex_Action_QueueScriptFileResponseOnAIBase("):
        if command in b:
            raise Hold("R33_HAS_FORBIDDEN_ENGINE_COMMAND")
    if b.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1:
        raise Hold("R33_LISTENER_COUNT_DRIFT")
    if b'"actorPipsVerified":false' not in b or b'"dispatchAuthorized":false' not in b:
        # The first literal lives in the encoded R27 console-string code.
        raise Hold("R33_FAIL_CLOSED_FLAGS_MISSING")
    return b


def proof_r31(root: Path) -> dict:
    p = safe(root, R31_PROOF)
    if not p.is_file() or p.stat().st_size > 1_000_000:
        raise Hold("R31_PROOF_MISSING")
    data = json.loads(p.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or
        data.get("schema") != "BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1" or
        data.get("status") != "R31_PASSIVE_INSTALLED_AWAITING_RUNTIME" or
        data.get("sourceSha256") != R31_SHA or
        data.get("installationPerformed") is not True or
        data.get("typedInstallApproved") is not True or
        data.get("dispatchAuthorized") is not False):
        raise Hold("R31_INSTALLED_PROOF_INCONSISTENT")
    snap = data.get("baselineSnapshot")
    if not isinstance(snap, dict) or snap.get("WeiDU.log") != WEIDU_PRE_R31_SHA or snap.get(OVERRIDE) != "e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735":
        raise Hold("R31_PREINSTALL_MANIFEST_MISMATCH")
    for rel, digest in BASELINE_SHA.items():
        if snap.get(rel) != digest:
            raise Hold("R31_INHERITED_PIN_MISMATCH:" + rel)
    return data


def snapshot(root: Path) -> dict[str, str]:
    result = {}
    for rel in WATCHED:
        p = safe(root, rel)
        if not p.is_file():
            raise Hold("WATCHED_FILE_MISSING:" + rel)
        result[rel] = sha(p)
    return result


def verify_snapshot(root: Path, expected: dict[str, str]) -> None:
    for rel, digest in expected.items():
        item = safe(root, rel)
        if not item.is_file() or sha(item) != digest:
            raise Hold("WATCHED_BASELINE_CHANGED:" + rel)


def preflight(root: Path, candidate: Path, live: bool = True) -> dict:
    protected_root(root, live)
    rows, wei_hash = history(root)
    if len(rows) != 151 or not R27.match(rows[148]) or not R29.match(rows[149]) or not R31.match(rows[150]):
        raise Hold("R31_MUST_BE_WEIDU_LAST_151")
    if any(R33.match(line) for line in rows):
        raise Hold("R33_ALREADY_PRESENT")
    for rel in (R33_DIR, TP2, SETUP, STAGED, R33_PROOF):
        if safe(root, rel).exists():
            raise Hold("R33_STAGING_COLLISION:" + rel)
    if sha(safe(root, OVERRIDE)) != R31_SHA:
        raise Hold("R31_LIVE_SHA_MISMATCH")
    p = proof_r31(root)
    if sha(safe(root, "setup-enhanced-powergaming-scripts.exe")) != NATIVE_SHA:
        raise Hold("WEIDU_NATIVE_BINARY_PIN_MISMATCH")
    if sha(safe(root, "BGXR31/setup-BGXR31.exe")) != NATIVE_SHA:
        raise Hold("R31_NATIVE_BINARY_PIN_MISMATCH")
    for rel, wanted in BASELINE_SHA.items():
        if sha(safe(root, rel)) != wanted:
            raise Hold("INSTALLED_RESOURCE_SHA_DRIFT:" + rel)
    candidate_bytes(candidate)
    if live:
        verify_processes()
    snap = snapshot(root)
    return {"schema": SCHEMA, "status": "R33_PREFLIGHT_PASS_INSTALL_UNAUTHORIZED",
            "r31Last": True, "weiduComponents": 151, "weiduLogSha256": wei_hash,
            "sourceSha256": R33_SHA, "sourceSize": R33_SIZE,
            "r31ProofStatus": p["status"], "baselineSnapshot": snap,
            "gameModified": False, "installationPerformed": False,
            "typedInstallApproved": False, "ordersSent": 0,
            "dispatchAuthorized": False, "weaponSwitchAuthorized": False,
            "alternateEffectiveAPRVerified": False, "classRowVerified": False}


def external_backup(root: Path, expected: dict[str, str]) -> Path:
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    parent = Path(home) / "Documents" / "BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
        raise Hold("EXTERNAL_BACKUP_REPARSE_POINT")
    parent.mkdir(parents=True, exist_ok=True)
    dest = Path(tempfile.mkdtemp(prefix="PRE_BGXR33_", dir=parent))
    for rel, wanted in expected.items():
        origin, backup = safe(root, rel), safe(dest, rel)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, backup)
        if sha(backup) != wanted:
            raise Hold("EXTERNAL_BACKUP_HASH_MISMATCH:" + rel)
    safe(dest, "SHA256.json").write_text(json.dumps(expected, indent=2), encoding="utf-8")
    return dest


def native_weidu(root: Path, uninstall: bool = False) -> None:
    exe = safe(root, SETUP)
    if not exe.is_file() or sha(exe) != NATIVE_SHA:
        raise Hold("R33_STAGED_WEIDU_BINARY_DRIFT")
    args = [str(exe), "--noautoupdate", "--no-exit-pause",
            "--game", str(root), "--use-lang", "ru_ru",
            "--force-uninstall" if uninstall else "--force-install", "0"]
    p = subprocess.run(args, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, errors="replace", timeout=240, check=False)
    transcript = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)", transcript):
        raise Hold("R33_WEIDU_FAILED_MANUAL_REVIEW:" + transcript[-600:])


def install(root: Path, candidate: Path, token: str) -> dict:
    if token != INSTALL_TOKEN:
        raise Hold("EXACT_TYPED_INSTALL_CONSENT_REQUIRED")
    ready = preflight(root, candidate, True)
    baseline_hashes = ready["baselineSnapshot"]
    verify_snapshot(root, baseline_hashes)
    back = external_backup(root, baseline_hashes)
    verify_processes()
    verify_snapshot(root, baseline_hashes)
    # From this point: failed steps are MANUAL REVIEW, never automatic retry.
    folder = safe(root, R33_DIR)
    folder.mkdir(parents=True, exist_ok=False)
    stage = safe(root, STAGED)
    stage.parent.mkdir(parents=True, exist_ok=False)
    stage.write_bytes(candidate_bytes(candidate))
    safe(root, TP2).write_text(TP2_TEXT, encoding="ascii", newline="\n")
    shutil.copy2(safe(root, "setup-enhanced-powergaming-scripts.exe"), safe(root, SETUP))
    if sha(stage) != R33_SHA or sha(safe(root, SETUP)) != NATIVE_SHA:
        raise Hold("R33_STAGING_SHA_DRIFT")
    verify_processes()
    verify_snapshot(root, baseline_hashes)
    proof = safe(root, R33_PROOF)
    proof.write_text(json.dumps({"schema": SCHEMA, "status": "R33_PENDING_WEIDU",
        "sourceSha256": R33_SHA, "externalBackup": str(back),
        "baselineSnapshot": baseline_hashes}, indent=2), encoding="utf-8")
    native_weidu(root)
    rows, _ = history(root)
    if len(rows) != 152 or not R33.match(rows[-1]) or not R31.match(rows[-2]) or sha(safe(root, OVERRIDE)) != R33_SHA:
        raise Hold("R33_POST_WEIDU_INCONSISTENT_MANUAL_REVIEW")
    for rel, expected in baseline_hashes.items():
        if rel not in ("WeiDU.log", OVERRIDE) and sha(safe(root, rel)) != expected:
            raise Hold("R33_UNRELATED_RESOURCE_CHANGED_MANUAL_REVIEW:" + rel)
    data = {"schema": SCHEMA, "status": "R33_PASSIVE_INSTALLED_AWAITING_RUNTIME",
            "sourceSha256": R33_SHA, "externalBackup": str(back),
            "baselineSnapshot": baseline_hashes,
            "typedInstallApproved": True, "installationPerformed": True,
            "gameModified": True, "ordersSent": 0,
            "dispatchAuthorized": False, "weaponSwitchAuthorized": False,
            "classRowVerified": False, "actorPipsVerified": False,
            "alternateEffectiveAPRVerified": False,
            "manualEpsOriginVerified": False}
    proof.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def installed_proof(root: Path) -> dict:
    proof = safe(root, R33_PROOF)
    if not proof.is_file() or proof.stat().st_size > 1_000_000:
        raise Hold("R33_PROOF_MISSING")
    p = json.loads(proof.read_text(encoding="utf-8"))
    if not isinstance(p, dict) or p.get("schema") != SCHEMA or p.get("status") != "R33_PASSIVE_INSTALLED_AWAITING_RUNTIME" or p.get("sourceSha256") != R33_SHA or p.get("typedInstallApproved") is not True or p.get("installationPerformed") is not True:
        raise Hold("R33_INSTALLED_PROOF_INCONSISTENT")
    return p


def last_r33(root: Path) -> list[str]:
    protected_root(root)
    rows, _ = history(root)
    if len(rows) != 152 or not R27.match(rows[148]) or not R29.match(rows[149]) or not R31.match(rows[150]) or not R33.match(rows[-1]):
        raise Hold("R33_NOT_WEIDU_LAST_NO_MUTATION")
    if sha(safe(root, OVERRIDE)) != R33_SHA:
        raise Hold("R33_LIVE_SOURCE_SHA_DRIFT")
    return rows


def rollback(root: Path, token: str) -> dict:
    if token != ROLLBACK_TOKEN:
        raise Hold("EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED")
    last_r33(root)
    verify_processes()
    p = installed_proof(root)
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    parent = Path(home) / "Documents" / "BGXAI_BACKUPS"
    b = Path(p.get("externalBackup", ""))
    if b.parent != parent or not b.name.startswith("PRE_BGXR33_") or not b.is_dir() or b.is_symlink():
        raise Hold("BACKUP_PROVENANCE_INVALID")
    expected = json.loads(safe(b, "SHA256.json").read_text(encoding="utf-8"))
    if expected != p.get("baselineSnapshot") or expected.get(OVERRIDE) != R31_SHA:
        raise Hold("BACKUP_MANIFEST_OR_R31_PIN_MISMATCH")
    verify_snapshot(b, expected)
    for rel, sha_before in expected.items():
        if rel not in (OVERRIDE, "WeiDU.log") and sha(safe(root, rel)) != sha_before:
            raise Hold("LIVE_UNRELATED_RESOURCE_DRIFT_STOP:" + rel)
    if sha(safe(root, SETUP)) != NATIVE_SHA:
        raise Hold("R33_WEIDU_BINARY_DRIFT")
    native_weidu(root, uninstall=True)
    rows, _ = history(root)
    if len(rows) != 151 or not R31.match(rows[-1]) or sha(safe(root, OVERRIDE)) != R31_SHA:
        raise Hold("R33_ROLLBACK_NOT_VERIFIED_MANUAL_REVIEW")
    for rel, value in expected.items():
        if rel not in (OVERRIDE, "WeiDU.log") and sha(safe(root, rel)) != value:
            raise Hold("R33_ROLLBACK_UNRELATED_DRIFT:" + rel)
    return {"schema": SCHEMA, "status": "R33_ROLLBACK_R31_RESTORED",
            "gameModified": True, "ordersSent": 0,
            "dispatchAuthorized": False, "weaponSwitchAuthorized": False}


def capture(root: Path) -> dict:
    last_r33(root)
    installed_proof(root)
    verify_processes()
    loader = safe(root, "InfinityLoader.exe")
    if not loader.is_file() or not 1024 < loader.stat().st_size < 70_000_000:
        raise Hold("INFINITYLOADER_MISSING_OR_SIZE")
    with loader.open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise Hold("INFINITYLOADER_INVALID_PE")
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    reports = Path(home) / "Documents" / "BGXAI_LIVE_REPORTS"
    if reports.is_symlink() or (hasattr(reports, "is_junction") and reports.is_junction()):
        raise Hold("REPORTS_REPARSE_POINT")
    reports.mkdir(parents=True, exist_ok=True)
    name = "BGXAI_R33_CONSOLE_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".log"
    path = reports / name
    if path.exists() or path.is_symlink():
        raise Hold("REPORT_COLLISION")
    with path.open("xb") as output:
        child = subprocess.Popen([str(loader)], cwd=root, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=subprocess.STDOUT, close_fds=True)
        exit_code = child.wait()
        output.flush()
    count, sessions, stable, prof = 0, 0, 0, 0
    if path.stat().st_size <= 64_000_000:
        with path.open("rb") as stream:
            for line in stream:
                if b"[BGXR27]" not in line:
                    continue
                if b'"type":"SESSION"' in line and b'R33_R27V3_PASSIVE_PROF_RO' in line:
                    sessions += 1
                if b'"type":"R27_SINGLE_CALLBACK"' in line:
                    count += 1
                    stable += int(b'"queueSnapshotStable":true' in line)
                    prof += int(b'"proficiencyStat89to134Raw":[' in line)
    # Keep raw log for human review, never infer AI dispatch origin or effective APR.
    ready = exit_code == 0 and sessions == 1 and count > 0 and prof > 0
    return {"schema": SCHEMA, "status": "R33_RUNTIME_RAW_PROF_LOG_READY_FOR_REVIEW" if ready else "R33_RUNTIME_HOLD_REVIEW",
            "reportFile": str(path), "reportBytes": path.stat().st_size,
            "gameExitCode": exit_code, "sessionMarkers": sessions,
            "selectedActionSamples": count, "stableQueueSamples": stable,
            "rawProficiencySamples": prof, "gameModifiedByCapture": False,
            "readOnly": True, "ordersSent": 0, "dispatchAuthorized": False,
            "weaponSwitchAuthorized": False, "classRowVerified": False,
            "alternateEffectiveAPRVerified": False}


def status(root: Path) -> dict:
    protected_root(root)
    rows, digest = history(root)
    last = rows[-1]
    phase = ("R33_PRESENT_LAST" if len(rows) == 152 and R33.match(last) else
             "R31_PRESENT_LAST" if len(rows) == 151 and R31.match(last) else
             "HOLD_UNKNOWN_WEIDU_LAST")
    live_digest = sha(safe(root, OVERRIDE))
    return {"schema": SCHEMA, "status": phase, "weiduComponents": len(rows),
            "weiduLastComponent": last, "weiduLogSha256": digest,
            "liveModuleSha256": live_digest,
            "r31ModuleExact": live_digest == R31_SHA,
            "r33ModuleExact": live_digest == R33_SHA,
            "gameModified": False, "ordersSent": 0,
            "dispatchAuthorized": False}


def report(mode: str, data: dict) -> dict:
    home = os.environ.get("USERPROFILE")
    if not home:
        return {**data, "reportStatus": "USERPROFILE_MISSING"}
    path = Path(home) / "Documents" / "BGXAI_LIVE_REPORTS"
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return {**data, "reportStatus": "REPORTS_REPARSE_POINT"}
    try:
        path.mkdir(parents=True, exist_ok=True)
        name = "BGXAI_R33_" + mode.upper() + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        p = path / name
        data = {**data, "reportFile": str(p)}
        with p.open("x", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write("\n")
        return data
    except (OSError, ValueError) as error:
        return {**data, "reportStatus": "SAVE_FAILED:" + str(error)}


def main() -> int:
    cli = argparse.ArgumentParser(description="R33 passive prof: source-only until explicit typed WeiDU approval")
    cli.add_argument("--game", type=Path, default=ROOT)
    cli.add_argument("--candidate", type=Path)
    cli.add_argument("--mode", choices=["preflight", "status", "install", "rollback", "capture"], default="preflight")
    a = cli.parse_args()
    try:
        if a.mode == "status":
            data = status(a.game)
        elif a.mode == "preflight":
            if not a.candidate:
                raise Hold("R33_CANDIDATE_REQUIRED")
            data = preflight(a.game, a.candidate)
        elif a.mode == "install":
            if not a.candidate:
                raise Hold("R33_CANDIDATE_REQUIRED")
            print("R33 replaces R31 passive observer ONLY. It does not switch weapons.")
            token = input("Type " + INSTALL_TOKEN + " exactly (ENTER cancels): ").strip()
            data = install(a.game, a.candidate, token)
        elif a.mode == "rollback":
            token = input("Type " + ROLLBACK_TOKEN + " exactly (ENTER cancels): ").strip()
            data = rollback(a.game, token)
        else:
            data = capture(a.game)
        print(json.dumps(report(a.mode, data), ensure_ascii=False, indent=2))
        return 0
    except (Hold, OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as err:
        payload = {"schema": SCHEMA, "status": "R33_STOP_MANUAL_REVIEW",
                   "reason": str(err), "noAutoRetry": True,
                   "gameModifiedUnknown": a.mode in ("install", "rollback"),
                   "dispatchAuthorized": False, "weaponSwitchAuthorized": False}
        print(json.dumps(report(a.mode, payload), ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
