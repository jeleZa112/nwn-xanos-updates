#!/usr/bin/env python3
"""BGXAI guarded R42(last155)->R43(last156) diagnostic upgrade, SOURCE ONLY.

This is NOT connected to the single BGXAI_UPDATE.cmd. It cannot authorize or
perform an action merely because a chat contains "+". Never use this module as
a separate updater. Only source/CI development is permitted until an explicit
typed upgrade is wired into the already existing onefile with its own immutable
pins, and independently reviewed/tested on Windows.

Reuses the original SHA-pinned R42 155-last verifier, R38/R37 provenance,
exact external backup semantics and the existing ONE R38 action-start listener.
No XEquip, no LOCALS, no manual/EPS origin claims, no silent game changes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
R42_SOURCE = HERE / "BGXAI_R42_GUARDED_FROM_R38.py"
DIAG_SOURCE = HERE / "BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py"
R38_SOURCE = REPO / "BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py"
R37_SOURCE = REPO / "BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py"
R42_BLOB = "6d54acbffc09ce51a95bed67f5dacd852c2729bd"
DIAG_BLOB = "2436a29f72f296fdba3ca00b075992f80fea6973"
SCHEMA = "BGXAI_R42_DIAG_R43_GUARDED_SOURCE_ONLY_V1"
EXPECTED_SIZE = 95965
EXPECTED_SHA = "8abdc5b1d2088d8c8e2f53b6e4502de5dd0b05225fc6fcca52ebe165253e7ce6"
DIR = "BGXR43"
OVERRIDE = "override/M_BGXR27.lua"
STAGED = DIR + "/staged/M_BGXR27.lua"
TP2 = DIR + "/setup-BGXR43.tp2"
EXE = DIR + "/setup-BGXR43.exe"
PROOF = DIR + "/PROOF.json"
INSTALL_TOKEN = "INSTALL_BGXAI_R43_READONLY_REASON_AFTER_R42_LAST"
ROLLBACK_TOKEN = "ROLLBACK_BGXAI_R43_RESTORE_R42_ONLY"
LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXR43[/\\]SETUP-BGXR43[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
TP2_TEXT = (
    "BACKUP ~BGXR43/backup~\n"
    "AUTHOR ~BGXAI R43 read-only reason for R42 CLASS probe~\n"
    "BEGIN ~BGXR43 exact R42 one-shot reason-only extension~\n"
    "COPY ~BGXR43/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n"
)
DIAG_STATUSES = {
    "R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY", "HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE",
    "HOLD_SCRIPT_ASSIGNMENT_ACTOR_ID", "HOLD_SCRIPT_ASSIGNMENT_CLASS_OR_KIT",
    "HOLD_SCRIPT_PILOT_PHYSICAL_CONTEXT", "HOLD_SCRIPT_CURSOR_INVALID",
    "HOLD_SCRIPT_RESREF_UNREADABLE", "HOLD_SCRIPT_ACTOR_CHANGED",
    "HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED", "HOLD_SCRIPT_RESREF_CHANGED",
    "HOLD_SCRIPT_CURSOR_CHANGED", "R39_BRIDGE_RESULT_MISSING", "R39_PROBE_EXCEPTION",
    "R39_UNCLASSIFIED_STATUS",
}
CLASS_STATES = {
    "NOT_READ", "LEVEL_TABLE_MISSING", "MISSING_CLASS_ENTRY", "EMPTY",
    "INVALID_RESREF", "VALID_NAME_CANDIDATE",
}
PHYSICAL_STATES = {
    "NONE", "HOLD_PORTRAIT_ACTOR_ID", "HOLD_SELECTION_NOT_EXACTLY_THIS_ACTOR",
    "HOLD_ACTOR_NOT_CLERIC", "HOLD_ACTIVE_STATS_UNAVAILABLE",
    "HOLD_KIT_OR_STRENGTH_NOT_MATCHED", "HOLD_EQUIPMENT_UNAVAILABLE",
    "HOLD_SLOT_UNREADABLE", "HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED",
}

class Hold(ValueError):
    pass

def sha(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return hashlib.sha256(path_or_bytes).hexdigest()
    return sha(Path(path_or_bytes).read_bytes())

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def verified_import(path: Path, expected_blob: str, modname: str):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes()) != expected_blob:
        raise Hold("HOLD_PINNED_SOURCE_BLOB:" + modname)
    spec = importlib.util.spec_from_file_location(modname, path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_PINNED_SOURCE_IMPORT:" + modname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_checked():
    original = verified_import(R42_SOURCE, R42_BLOB, "bgxai_verified_r42")
    diag = verified_import(DIAG_SOURCE, DIAG_BLOB, "bgxai_verified_r42_diag")
    r38, old = original.load(R38_SOURCE, R37_SOURCE)
    if original.CANDIDATE_SHA != "d14bf5f62f7d37663cf77f3305f57fb9631293940ed8ae2d4cb7b488248434b0":
        raise Hold("HOLD_R42_BASELINE_SHA")
    if EXPECTED_SHA != sha(diag.compose()):
        raise Hold("HOLD_DIAG_COMPOSED_SHA")
    return original, diag, r38, old

def candidate_bytes(diag):
    data = diag.compose()
    if len(data) != EXPECTED_SIZE or sha(data) != EXPECTED_SHA:
        raise Hold("HOLD_DIAG_CANDIDATE_SHA_OR_SIZE")
    if data.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener") != 1:
        raise Hold("HOLD_DIAG_LISTENER_DRIFT")
    if data.count(b"[BGXBCS]") != 1:
        raise Hold("HOLD_DIAG_BCS_TAG_DRIFT")
    for marker in (b'"ordersSent":0', b'"localsWritten":0', b'"armAuthorized":false',
                   b'"dispatchAuthorized":false', b'"actualBcsExecutionVerified":false'):
        if marker not in data:
            raise Hold("HOLD_DIAG_SAFETY_MARKER_MISSING")
    return data

def exact_last_r43(r42, r38, old, game):
    old.protected_root(game, True)
    rows, loghash = old.history(game)
    if (len(rows) != 156 or not old.last_r37_history(rows[:153]) or
        r38.LAST.match(rows[153]) is None or
        r42.LAST.match(rows[154]) is None or LAST.match(rows[155]) is None):
        raise Hold("HOLD_R43_NOT_WEIDU_LAST_156")
    if old.sha(old.safe(game, OVERRIDE)) != EXPECTED_SHA:
        raise Hold("HOLD_R43_LIVE_LUA_SHA_DRIFT")
    return rows, loghash

def exact_proof(old, game):
    proof = old.safe(game, PROOF)
    if not proof.is_file() or proof.is_symlink() or proof.stat().st_size > 1_000_000:
        raise Hold("HOLD_R43_PROOF_MISSING")
    d = json.loads(proof.read_text(encoding="utf-8"))
    if (type(d) is not dict or d.get("schema") != SCHEMA or
        d.get("status") != "R43_READONLY_REASON_INSTALLED_AWAITING_LIVE" or
        d.get("sourceSha256") != EXPECTED_SHA or
        d.get("typedInstallApproved") is not True or
        d.get("installed") is not True or
        d.get("ordersSent") != 0 or d.get("dispatchAuthorized") is not False or
        d.get("armAuthorized") is not False):
        raise Hold("HOLD_R43_PROOF_INVALID")
    return d

def watched_baseline(r42, r38, old, game):
    proof = r42.installed_proof(old, game)
    watched = proof.get("baselineSnapshot")
    if type(watched) is not dict or not watched or watched.get(OVERRIDE) != r42.R38_SHA:
        raise Hold("HOLD_R42_BASELINE_SNAPSHOT_INVALID")
    # Old snapshot predated installation of R42, so WeiDU.log and active Lua
    # MUST differ; all unrelated source files must be unchanged.
    for rel, digest in watched.items():
        if rel in ("WeiDU.log", OVERRIDE):
            continue
        if not isinstance(rel, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", rel):
            raise Hold("HOLD_R42_WATCHED_PATH")
        if old.sha(old.safe(game, rel)) != digest:
            raise Hold("HOLD_UNRELATED_SOURCE_CHANGED:" + rel)
    observed = dict(watched)
    observed["WeiDU.log"] = old.sha(old.safe(game, "WeiDU.log"))
    observed[OVERRIDE] = r42.CANDIDATE_SHA
    observed[r42.PROOF] = old.sha(old.safe(game, r42.PROOF))
    for rel in observed:
        if old.sha(old.safe(game, rel)) != observed[rel]:
            raise Hold("HOLD_R42_WATCHED_SOURCE_DRIFT:" + rel)
    return observed

def before_change(r42, diag, r38, old, game):
    old.protected_root(game, True)
    r42.check_processes(r38, old)
    r42.r42_last(r38, old, game)
    r42.installed_proof(old, game)
    for rel in (DIR, STAGED, TP2, EXE, PROOF):
        if old.safe(game, rel).exists():
            raise Hold("HOLD_R43_STAGING_ALREADY_PRESENT:" + rel)
    old.verify_snapshot(game, watched_baseline(r42, r38, old, game))
    native = old.safe(game, "setup-enhanced-powergaming-scripts.exe")
    if not native.is_file() or old.sha(native) != r42.WEIDU_SHA:
        raise Hold("HOLD_R43_NATIVE_WEIDU_DRIFT")
    candidate_bytes(diag)
    return {"schema": SCHEMA, "status": "R43_PREFLIGHT_LAST155_PASS_NO_INSTALL",
            "expectedDiagnosticSha256": EXPECTED_SHA, "expectedDiagnosticBytes": EXPECTED_SIZE,
            "gameModified": False, "installed": False, "ordersSent": 0,
            "dispatchAuthorized": False, "armAuthorized": False}

def external_backup(old, game, snapshot):
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_USERPROFILE_MISSING")
    parent = Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
        raise Hold("HOLD_BACKUP_PARENT_REPARSE")
    parent.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="PRE_BGXR43_", dir=parent))
    for rel, digest in snapshot.items():
        src = old.safe(game, rel)
        dst = old.safe(backup, rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if old.sha(dst) != digest:
            raise Hold("HOLD_BACKUP_DIGEST_MISMATCH:" + rel)
    old.safe(backup, "SHA256.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return backup

def native_weidu(old, game, r42, uninstall=False):
    exe = old.safe(game, EXE)
    if not exe.is_file() or old.sha(exe) != r42.WEIDU_SHA:
        raise Hold("HOLD_R43_WEIDU_EXE_SHA")
    res = subprocess.run(
        [str(exe), "--noautoupdate", "--no-exit-pause", "--game", str(game),
         "--use-lang", "ru_ru", "--force-uninstall" if uninstall else "--force-install", "0"],
        cwd=game, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, errors="replace", timeout=240, check=False)
    out = (res.stdout or "") + "\n" + (res.stderr or "")
    if res.returncode or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)", out):
        raise Hold("HOLD_R43_NATIVE_WEIDU_MANUAL_REVIEW:" + out[-500:])

def install(r42, diag, r38, old, game, typed_token):
    if typed_token != INSTALL_TOKEN:
        raise Hold("HOLD_R43_EXACT_TYPED_INSTALL_REQUIRED")
    before_change(r42, diag, r38, old, game)
    snapshot = watched_baseline(r42, r38, old, game)
    old.verify_snapshot(game, snapshot)
    backup = external_backup(old, game, snapshot)
    r42.check_processes(r38, old)
    old.verify_snapshot(game, snapshot)
    data = candidate_bytes(diag)
    old.safe(game, DIR).mkdir(parents=True, exist_ok=False)
    old.safe(game, STAGED).parent.mkdir(parents=True, exist_ok=False)
    old.safe(game, STAGED).write_bytes(data)
    old.safe(game, TP2).write_text(TP2_TEXT, encoding="ascii", newline="\n")
    shutil.copy2(old.safe(game, "setup-enhanced-powergaming-scripts.exe"), old.safe(game, EXE))
    if old.sha(old.safe(game, STAGED)) != EXPECTED_SHA or old.sha(old.safe(game, EXE)) != r42.WEIDU_SHA:
        raise Hold("HOLD_R43_STAGED_SHA")
    r42.check_processes(r38, old)
    old.verify_snapshot(game, snapshot)
    proof = old.safe(game, PROOF)
    proof.write_text(json.dumps({"schema":SCHEMA, "status":"R43_PENDING_WEIDU",
                                 "sourceSha256":EXPECTED_SHA, "externalBackup":str(backup),
                                 "baselineSnapshot":snapshot}, indent=2), encoding="utf-8")
    # Possible real game mutation starts here. NO automated retry or rollback.
    native_weidu(old, game, r42)
    exact_last_r43(r42, r38, old, game)
    for rel, digest in snapshot.items():
        if rel not in ("WeiDU.log", OVERRIDE) and old.sha(old.safe(game, rel)) != digest:
            raise Hold("HOLD_R43_UNRELATED_FILE_CHANGED:" + rel)
    result = {"schema":SCHEMA, "status":"R43_READONLY_REASON_INSTALLED_AWAITING_LIVE",
              "sourceSha256":EXPECTED_SHA, "externalBackup":str(backup),
              "baselineSnapshot":snapshot, "typedInstallApproved":True,
              "installed":True, "gameModified":True, "ordersSent":0, "localsWritten":0,
              "dispatchAuthorized":False, "armAuthorized":False,
              "actualBcsExecutionVerified":False, "manualEpsActionOriginVerified":False,
              "classScriptResrefAtLiveJaganVerified":False}
    proof.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def rollback(r42, r38, old, game, typed_token):
    if typed_token != ROLLBACK_TOKEN:
        raise Hold("HOLD_R43_EXACT_TYPED_ROLLBACK_REQUIRED")
    exact_last_r43(r42, r38, old, game)
    r42.check_processes(r38, old)
    proof = exact_proof(old, game)
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_USERPROFILE_MISSING")
    parent = Path(home)/"Documents"/"BGXAI_BACKUPS"
    backup = Path(proof.get("externalBackup", ""))
    if (backup.parent != parent or not backup.name.startswith("PRE_BGXR43_") or
        not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R43_BACKUP_PROVENANCE")
    saved = json.loads(old.safe(backup, "SHA256.json").read_text(encoding="utf-8"))
    if (saved != proof.get("baselineSnapshot") or saved.get(OVERRIDE) != r42.CANDIDATE_SHA or
        r42.PROOF not in saved):
        raise Hold("HOLD_R43_BACKUP_MANIFEST_MISMATCH")
    old.verify_snapshot(backup, saved)
    for rel, digest in saved.items():
        if rel not in ("WeiDU.log", OVERRIDE) and old.sha(old.safe(game, rel)) != digest:
            raise Hold("HOLD_R43_UNRELATED_FILE_DRIFT:" + rel)
    r42.check_processes(r38, old)
    native_weidu(old, game, r42, uninstall=True)
    r42.r42_last(r38, old, game)
    for rel, digest in saved.items():
        if rel not in ("WeiDU.log", OVERRIDE) and old.sha(old.safe(game, rel)) != digest:
            raise Hold("HOLD_R43_ROLLBACK_UNRELATED_DRIFT:" + rel)
    return {"schema": SCHEMA, "status": "R43_ROLLBACK_RESTORED_R42_LAST",
            "installed": False, "gameModified": True, "ordersSent":0,
            "dispatchAuthorized":False, "armAuthorized":False}

def status(r42, r38, old, game):
    old.protected_root(game, True)
    rows, _ = old.history(game)
    if (len(rows) == 156 and old.last_r37_history(rows[:153]) and
        r38.LAST.match(rows[153]) and r42.LAST.match(rows[154]) and
        LAST.match(rows[155]) and old.sha(old.safe(game, OVERRIDE)) == EXPECTED_SHA):
        exact_proof(old, game)
        stage = "R43_PRESENT_LAST_READONLY_REASON"
        installed = True
    elif (len(rows) == 155 and old.last_r37_history(rows[:153]) and
          r38.LAST.match(rows[153]) and r42.LAST.match(rows[154]) and
          old.sha(old.safe(game, OVERRIDE)) == r42.CANDIDATE_SHA):
        r42.installed_proof(old, game)
        stage = "R43_NOT_INSTALLED_R42_PRESENT_LAST"
        installed = False
    else:
        stage = "R43_HOLD_UNEXPECTED_WEIDU_OR_LUA"
        installed = False
    return {"schema":SCHEMA, "status":stage, "installed":installed,
            "gameModified":False, "ordersSent":0, "dispatchAuthorized":False, "armAuthorized":False}

def parse_diag_console(r42, log, exit_code):
    out = r42.parse_bcs_console(log, exit_code)
    lines = []
    with Path(log).open("rb") as f:
        for raw in f:
            if b"[BGXBCS] " in raw:
                lines.append(raw)
    if len(lines) != 1 or lines[0].count(b"[BGXBCS] ") != 1 or len(lines[0]) > 4096:
        return {"schema": SCHEMA, "status":"R43_CAPTURE_HOLD_DIAG_ROW_COUNT_OR_FORMAT",
                "ordersSent":0, "dispatchAuthorized":False, "armAuthorized":False}
    try:
        row = json.loads(lines[0].split(b"[BGXBCS] ", 1)[1].decode("utf-8-sig").strip())
    except (ValueError, UnicodeError):
        return {"schema": SCHEMA, "status":"R43_CAPTURE_HOLD_DIAG_INVALID_JSON",
                "ordersSent":0, "dispatchAuthorized":False, "armAuthorized":False}
    if (type(row) is not dict or row.get("r39ProbeStatus") not in DIAG_STATUSES or
        row.get("r39PhysicalReason") not in PHYSICAL_STATES or
        row.get("r39ClassSlotState") not in CLASS_STATES or
        row.get("ordersSent") != 0 or row.get("armAuthorized") is not False or
        row.get("dispatchAuthorized") is not False):
        return {"schema": SCHEMA, "status":"R43_CAPTURE_HOLD_DIAG_FIELDS",
                "ordersSent":0, "dispatchAuthorized":False, "armAuthorized":False}
    # Old R42 validates actor, row count and zero-order context. We preserve
    # its FAIL/CAPTURE-HOLD; even a known R39 code is NOT a successful BCS read.
    out["r39ProbeStatus"] = row["r39ProbeStatus"]
    out["r39PhysicalReason"] = row["r39PhysicalReason"]
    out["r39ClassSlotState"] = row["r39ClassSlotState"]
    return out

def capture(r42, r38, old, game):
    exact_last_r43(r42, r38, old, game)
    exact_proof(old, game)
    r42.check_processes(r38, old)
    loader = old.safe(game, "InfinityLoader.exe")
    if loader.is_symlink() or not loader.is_file() or not 1024 < loader.stat().st_size < 70_000_000:
        raise Hold("HOLD_R43_LOADER_SIZE")
    with loader.open("rb") as f:
        if f.read(2) != b"MZ":
            raise Hold("HOLD_R43_LOADER_SIGNATURE")
    home = os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_USERPROFILE_MISSING")
    parent = Path(home)/"Documents"/"BGXAI_LIVE_REPORTS"
    if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
        raise Hold("HOLD_R43_LOG_PARENT_REPARSE")
    parent.mkdir(parents=True, exist_ok=True)
    target = parent/("BGXAI_R43_CLASS_REASON_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".log")
    with target.open("xb") as f:
        child = subprocess.Popen([str(loader)], cwd=game, stdin=subprocess.DEVNULL,
                                 stdout=f, stderr=subprocess.STDOUT, close_fds=True)
        code = child.wait()
        f.flush()
    exact_last_r43(r42, r38, old, game)
    out = parse_diag_console(r42, target, code)
    out["rawConsoleFile"] = str(target)
    out["rawConsoleBytes"] = target.stat().st_size
    return out

def main(argv=None):
    p = __import__("argparse").ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, default=ROOT)
    p.add_argument("--mode", choices=("status","preflight","install","rollback","capture"), default="status")
    # Deliberately unavailable as a standalone installer. Existing onefile
    # integration must provide the exact externally reviewed authorization.
    p.add_argument("--onefile-review-gate", action="store_true")
    args = p.parse_args(argv)
    try:
        r42, diag, r38, old = load_checked()
        if args.mode == "status":
            out = status(r42, r38, old, args.game)
        elif args.mode == "preflight":
            out = before_change(r42, diag, r38, old, args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_NOT_CONNECTED_TO_EXISTING_ONEFILE")
        elif args.mode == "install":
            token = input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            out = install(r42, diag, r38, old, args.game, token)
        elif args.mode == "rollback":
            token = input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            out = rollback(r42, r38, old, args.game, token)
        else:
            out = capture(r42, r38, old, args.game)
        rc = 3 if out["status"].startswith(("HOLD_", "R43_HOLD", "R43_CAPTURE_HOLD")) or "HOLD" in out["status"] else 0
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired,EOFError) as e:
        out = {"schema":SCHEMA, "status":"R43_STOP_MANUAL_REVIEW",
               "reason":str(e) if isinstance(e,Hold) else "HOLD_RUNTIME_OR_IO",
               "noAutoRetry":True, "gameModifiedUnknown":args.mode in ("install","rollback"),
               "ordersSent":0, "dispatchAuthorized":False, "armAuthorized":False}
        rc = 3
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return rc

if __name__ == "__main__":
    sys.exit(main())
