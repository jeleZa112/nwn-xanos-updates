#!/usr/bin/env python3
"""BGXAI R42: one-CMD SOURCE ONLY, no game writes, no second observer.

Called only from SHA-pinned BGXAI_SYNC.ps1 as main menu 179.
Reuses existing live installed R38 Lua after byte-for-byte proof, and exact
immutable R39 Lua + R42 source composer from the same signed commit.
This is NOT a game installation or a real-time BCS observation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
REPO = "jeleZa112/nwn-xanos-updates"
PREFIX = "BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/"
BUILDER = PREFIX + "BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py"
BRIDGE = "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua"
LIVE_SOURCE = "BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua"
LIVE_R38_LEN = 78927
LIVE_R38_SHA = "958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c"
BUILDER_BYTES = 8409
BUILDER_SHA = "11e6967cbfe22ba1b819d4744bc20275b392bf30e98d2a2a8a6323e79c4891b9"
BRIDGE_BYTES = 13088
BRIDGE_SHA = "80891a29a38d9bddac948ddf95146761d73e9112c44242a4fa0e673a2a476f95"
SOURCES = {BUILDER: (BUILDER_BYTES, BUILDER_SHA),
           BRIDGE: (BRIDGE_BYTES, BRIDGE_SHA)}
SCHEMA = "BGXAI_R42_ONEFILE179_CLASS_BCS_SOURCEONLY_V1"
R38_GUARD = "BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py"
R37_GUARD = "BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py"
R42_GUARD = PREFIX + "BGXAI_R42_GUARDED_FROM_R38.py"
CANDIDATE_SIZE = 93776
CANDIDATE_SHA = "d14bf5f62f7d37663cf77f3305f57fb9631293940ed8ae2d4cb7b488248434b0"
SOURCES.update({
    R38_GUARD: (21303, "f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c"),
    R37_GUARD: (26252, "b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d"),
    R42_GUARD: (20471, "347722909c8c41364530adc1c51cd1607fb4181d6c2628d1d52b80596c170215"),
})
MODES = {"1": "source", "2": "status", "3": "preflight",
         "4": "install", "5": "rollback", "6": "capture"}
# R43 is an opt-in guarded successor; preserve R42 menu 1..6 byte-for-byte.
# Additional choices are inert until individually selected.
MODES.update({"7":"diag_status", "8":"diag_preflight", "9":"diag_install",
              "10":"diag_rollback", "11":"diag_capture"})
R43_GUARD = PREFIX + "BGXAI_R42_DIAG_UPGRADE_GUARDED_SOURCE_ONLY.py"
R43_DIAG = PREFIX + "BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py"
R43_INSTALL_CONFIRM = "INSTALL_BGXAI_R43_READONLY_REASON_AFTER_R42_LAST"
R43_ROLLBACK_CONFIRM = "ROLLBACK_BGXAI_R43_RESTORE_R42_ONLY"
R43_CANDIDATE_SHA = "8abdc5b1d2088d8c8e2f53b6e4502de5dd0b05225fc6fcca52ebe165253e7ce6"
SOURCES.update({
    R43_GUARD:(19969,"8c1d0275e861909d1caa004a3e434e2791d5f8181c1ff966bd578f610cb4bb31"),
    R43_DIAG:(6950,"718e0f11a405439398a4102406f0b27acd08f8f75f29e53bb054e19a5c138da2"),
    LIVE_SOURCE:(LIVE_R38_LEN,LIVE_R38_SHA),
})
INSTALL_CONFIRM = "INSTALL_BGXAI_R42_READONLY_CLASS_BCS_AFTER_R38"
ROLLBACK_CONFIRM = "ROLLBACK_BGXAI_R42_RESTORE_R38_ONLY"



class Hold(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified(path: str, payload: bytes) -> bytes:
    if path not in SOURCES or type(payload) is not bytes:
        raise Hold("HOLD_NOT_PINNED_R42_SOURCE")
    length, expected = SOURCES[path]
    if len(payload) != length or sha(payload) != expected:
        raise Hold("HOLD_SOURCE_SHA_DRIFT:" + path.rsplit("/", 1)[-1])
    return payload


def pin(commit: str) -> str:
    if not isinstance(commit, str) or re.fullmatch(r"[a-f0-9]{40}", commit) is None:
        raise Hold("HOLD_IMMUTABLE_COMMIT_MISSING")
    return commit


def fetch(commit: str, path: str, opener=urllib.request.urlopen) -> bytes:
    pin(commit)
    if path not in SOURCES:
        raise Hold("HOLD_FETCH_PATH_NOT_ALLOWLISTED")
    failures = []
    for base in (
        "https://raw.githubusercontent.com/" + REPO + "/" + commit + "/",
        "https://cdn.jsdelivr.net/gh/" + REPO + "@" + commit + "/",
        "https://fastly.jsdelivr.net/gh/" + REPO + "@" + commit + "/",
    ):
        try:
            request = urllib.request.Request(base + path,
                headers={"User-Agent": "BGXAI-R42-Onefile-SHA-NoAPI"})
            with opener(request, timeout=16) as reply:
                raw = reply.read(SOURCES[path][0] + 1)
            return verified(path, raw)
        except (OSError, ValueError, TypeError) as error:
            failures.append(type(error).__name__)
    raise Hold("HOLD_PINNED_R42_DOWNLOAD:" + ",".join(failures))


def protected_root(game: Path, require_windows: bool = True) -> Path:
    game = Path(game)
    if require_windows:
        if os.name != "nt":
            raise Hold("HOLD_WINDOWS_REQUIRED")
        if os.path.normcase(os.path.abspath(game)) != os.path.normcase(os.path.abspath(ROOT)):
            raise Hold("HOLD_NOT_EXACT_GAME_ROOT")
    if not game.is_dir() or game.is_symlink():
        raise Hold("HOLD_GAME_FOLDER")
    chitin = game / "chitin.key"
    if not chitin.is_file() or chitin.is_symlink():
        raise Hold("HOLD_CHITIN_KEY")
    return game


def exact_installed_r38(game: Path) -> bytes:
    file = game / "override" / "M_BGXR27.lua"
    if not file.is_file() or file.is_symlink():
        raise Hold("HOLD_INSTALLED_R38_NOT_PRESENT")
    if file.stat().st_size != LIVE_R38_LEN:
        raise Hold("HOLD_R38_INSTALLED_LENGTH_CHANGED")
    before = file.read_bytes()
    if len(before) != LIVE_R38_LEN or sha(before) != LIVE_R38_SHA:
        raise Hold("HOLD_R38_INSTALLED_SHA_CHANGED")
    # Read twice to reject concurrent edits to the live override.
    if file.stat().st_size != LIVE_R38_LEN or sha(file.read_bytes()) != LIVE_R38_SHA:
        raise Hold("HOLD_R38_FILE_CHANGED_DURING_READ")
    return before


def run(game: Path, commit: str, *, fetcher=fetch,
        runner=subprocess.run, require_windows: bool = True) -> dict:
    game = protected_root(game, require_windows)
    commit = pin(commit)
    live = exact_installed_r38(game)
    with tempfile.TemporaryDirectory(prefix="BGXAI_R42_RO_") as folder:
        workspace = Path(folder).resolve(strict=True)
        real_game = game.resolve(strict=True)
        if workspace == real_game or workspace in real_game.parents or real_game in workspace.parents:
            raise Hold("HOLD_TEMP_OVERLAPS_GAME")
        for path, data in (
            (LIVE_SOURCE, live),
            (BUILDER, verified(BUILDER, fetcher(commit, BUILDER))),
            (BRIDGE, verified(BRIDGE, fetcher(commit, BRIDGE))),
        ):
            target = workspace.joinpath(*path.split("/"))
            if workspace not in target.parents or target.is_symlink():
                raise Hold("HOLD_STAGE_OUTSIDE_TEMP")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if sha(target.read_bytes()) != sha(data):
                raise Hold("HOLD_R42_STAGE_BYTES_CHANGED")
        tool = workspace.joinpath(*BUILDER.split("/"))
        completed = runner(
            [sys.executable, str(tool)], cwd=str(workspace),
            stdin=subprocess.DEVNULL, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=50, check=False,
        )
        if completed.returncode:
            raise Hold("HOLD_R42_COMPOSER_REJECTED")
        try:
            inner = json.loads(completed.stdout)
        except (TypeError, ValueError):
            raise Hold("HOLD_R42_COMPOSER_OUTPUT_INVALID")
        if (type(inner) is not dict or
            inner.get("status") != "R42_COMPOSED_CLASS_BCS_SINGLE_LISTENER_NO_INSTALL" or
            inner.get("onlyExistingActionStartedListener") is not True or
            inner.get("additionalActionStartedListeners") != 0 or
            inner.get("gameModified") is not False or
            inner.get("nativeGameInstalled") is not False or
            inner.get("ordersSent") != 0 or
            inner.get("installAuthorized") is not False or
            inner.get("classScriptResrefAtLiveJaganVerified") is not False):
            raise Hold("HOLD_R42_INNER_REPORT_NOT_READONLY")
        return {
            "schema": SCHEMA,
            "status": "R42_EXISTING_ONEFILE_SOURCE_READY_NO_INSTALL",
            "sourceCommit": commit,
            "liveR38ExistingSHA256Matched": True,
            "r42SourceSHA256": BUILDER_SHA,
            "r39BridgeSHA256": BRIDGE_SHA,
            "candidateLuaSHA256": inner.get("composedCandidateSha256"),
            "candidateLuaBytes": inner.get("composedCandidateBytes"),
            "originalOneListenerPreserved": True,
            "newActionListeners": 0,
            "classScriptResrefAtLiveJaganVerified": False,
            "gameModified": False,
            "installed": False,
            "ordersSent": 0,
            "localsWritten": 0,
            "armAuthorized": False,
            "dispatchAuthorized": False,
            "nextStep": "GUARDED_R38_LAST_WEIDU_TYPED_CLASS_OBSERVER_INSTALL_NOT_YET_AVAILABLE",
        }



def run_guarded(game: Path, commit: str, mode: str, *, fetcher=fetch,
                runner=subprocess.run, require_windows: bool=True,
                approved_token: str | None=None) -> dict:
    """Preflight/install/rollback uses exact pinned legacy helpers and one existing CMD."""
    if mode not in ("status", "preflight", "install", "rollback", "capture"):
        raise Hold("HOLD_R42_GUARDED_MODE")
    game=protected_root(game,require_windows)
    commit=pin(commit)
    install_mode=mode in ("install", "rollback")
    required=INSTALL_CONFIRM if mode=="install" else ROLLBACK_CONFIRM
    if install_mode and approved_token!=required:
        raise Hold("HOLD_EXACT_TYPED_R42_APPROVAL_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="BGXAI_R42_GUARDED_") as folder:
        workspace=Path(folder).resolve(strict=True)
        real_game=game.resolve(strict=True)
        if workspace==real_game or workspace in real_game.parents or real_game in workspace.parents:
            raise Hold("HOLD_R42_STAGE_INSIDE_GAME")
        # No game file is opened for writing. The only copy of R38 is original,
        # exact SHA, used for composing a temporary candidate.
        for path in (R38_GUARD, R37_GUARD, R42_GUARD, BUILDER, BRIDGE):
            data=verified(path,fetcher(commit,path))
            target=workspace.joinpath(*path.split("/"))
            if workspace not in target.parents or target.is_symlink():
                raise Hold("HOLD_R42_STAGE_PATH")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            if sha(target.read_bytes())!=SOURCES[path][1]:
                raise Hold("HOLD_R42_STAGED_SHA")
        candidate=None
        if mode in ("preflight", "install"):
            live=exact_installed_r38(game)
            source=workspace.joinpath(*LIVE_SOURCE.split("/"))
            source.parent.mkdir(parents=True,exist_ok=True)
            source.write_bytes(live)
            if sha(source.read_bytes())!=LIVE_R38_SHA:
                raise Hold("HOLD_R42_STAGED_R38_SHA")
            import importlib.util
            loader=workspace.joinpath(*BUILDER.split("/"))
            spec=importlib.util.spec_from_file_location('bgxai_verified_r42_builder',loader)
            if spec is None or spec.loader is None:
                raise Hold("HOLD_R42_BUILDER_IMPORT")
            builder=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(builder)
            raw=builder.compose(source.read_bytes(),workspace.joinpath(*BRIDGE.split("/")).read_bytes())
            if len(raw)!=CANDIDATE_SIZE or sha(raw)!=CANDIDATE_SHA:
                raise Hold("HOLD_R42_COMPOSED_BYTES_DRIFT")
            candidate=workspace/"R42_CANDIDATE_M_BGXR27.lua"
            candidate.write_bytes(raw)
            if sha(candidate.read_bytes())!=CANDIDATE_SHA:
                raise Hold("HOLD_R42_TEMP_CANDIDATE_SHA")
        command=[sys.executable,str(workspace.joinpath(*R42_GUARD.split("/"))),
                 "--game",str(game),
                 "--r38-tool",str(workspace.joinpath(*R38_GUARD.split("/"))),
                 "--r37-tool",str(workspace.joinpath(*R37_GUARD.split("/"))),
                 "--mode",mode]
        if candidate is not None:
            command+=["--candidate",str(candidate)]
        # Token is typed by user on the current console before this call.
        # The independently SHA-checked native guarded installer validates
        # the same exact token again: no implicit or script-provided approval.
        result=runner(command,cwd=str(workspace),input=(approved_token+"\n") if install_mode else "",
                      stdin=None,capture_output=True,text=True,encoding="utf-8",
                      errors="replace",timeout=330,check=False)
        try:
            inner=json.loads(result.stdout[result.stdout.find("{"):])
        except (ValueError,TypeError):
            raise Hold("HOLD_R42_NATIVE_REPORT_INVALID")
        expected={
            "status": ("R42_NOT_INSTALLED_R38_LAST","R42_PRESENT_LAST_READONLY"),
            "preflight": ("R42_PREFLIGHT_PASS_NO_INSTALL",),
            "install": ("R42_READONLY_INSTALLED_AWAITING_LIVE_CLASS",),
            "rollback": ("R42_ROLLBACK_RESTORED_R38_LAST",),
            "capture": ("R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM",),
        }
        accepted=expected["status"] if mode=="status" else expected[mode]
        observed=inner.get("classScriptResrefAtLiveJaganVerified") is True
        resref=inner.get("classScriptResref")
        if (result.returncode!=0 or type(inner) is not dict or
            inner.get("status") not in accepted or
            inner.get("ordersSent")!=0 or
            inner.get("dispatchAuthorized") is not False or
            inner.get("armAuthorized") is not False or
            (observed and mode!="capture") or
            (mode=="capture" and (not observed or
              type(resref) is not str or
              re.fullmatch(r'[A-Z0-9_#*]{1,8}',resref) is None or
              inner.get("scrlev")!=4 or inner.get("partyIndex")!=1 or
              inner.get("actualBcsExecutionVerified") is not False or
              inner.get("manualEpsActionOriginVerified") is not False))):
            raise Hold("HOLD_R42_NATIVE_GUARD_OR_STATE")
        return {
            "schema":SCHEMA,"status":"R42_"+mode.upper()+"_EXACT_GUARDED_PASS",
            "innerStatus":inner["status"],"sourceCommit":commit,
            "r42ExpectedCandidateSHA256":CANDIDATE_SHA,
            "gameModified":mode in ("install","rollback"),
            "installed":mode in ("install","capture") or (mode=="status" and inner.get("installed") is True),
            "classScriptResrefAtLiveJaganVerified":observed,
            "classScriptResref":resref if observed else None,
            "actualBcsExecutionVerified":False,
            "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False,
            "manualEpsActionOriginVerified":False,
        }


def run_diag_guarded(game: Path, commit: str, mode: str, *, fetcher=fetch,
                     runner=subprocess.run, require_windows: bool=True,
                     approved_token: str | None=None) -> dict:
    """R43-only, same onefile 179. No extra listener or separate CMD."""
    if mode not in ("diag_status","diag_preflight","diag_install","diag_rollback","diag_capture"):
        raise Hold("HOLD_R43_UNSUPPORTED_MODE")
    game=protected_root(game,require_windows)
    commit=pin(commit)
    native_mode=mode[5:]
    install_mode=native_mode in ("install","rollback")
    required=R43_INSTALL_CONFIRM if native_mode=="install" else R43_ROLLBACK_CONFIRM
    if install_mode and approved_token!=required:
        raise Hold("HOLD_EXACT_TYPED_R43_APPROVAL_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="BGXAI_R43_GUARDED_") as folder:
        workspace=Path(folder).resolve(strict=True)
        real_game=game.resolve(strict=True)
        if workspace==real_game or workspace in real_game.parents or real_game in workspace.parents:
            raise Hold("HOLD_R43_STAGE_INSIDE_GAME")
        for path in (R37_GUARD,R38_GUARD,R42_GUARD,BUILDER,BRIDGE,LIVE_SOURCE,R43_DIAG,R43_GUARD):
            data=verified(path,fetcher(commit,path))
            target=workspace.joinpath(*path.split("/"))
            if workspace not in target.parents or target.is_symlink():
                raise Hold("HOLD_R43_STAGING_PATH")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            if sha(target.read_bytes())!=SOURCES[path][1]:
                raise Hold("HOLD_R43_SOURCE_STAGED_SHA")
        command=[sys.executable,str(workspace.joinpath(*R43_GUARD.split("/"))),
                 "--game",str(game),"--mode",native_mode,"--onefile-review-gate"]
        result=runner(command,cwd=str(workspace),
                      input=(approved_token+"\n") if install_mode else "",
                      stdin=None,capture_output=True,text=True,encoding="utf-8",
                      errors="replace",timeout=350,check=False)
        try:
            inner=json.loads(result.stdout[result.stdout.find("{"):])
        except (ValueError,TypeError):
            raise Hold("HOLD_R43_NATIVE_REPORT_INVALID")
        if type(inner) is not dict:
            raise Hold("HOLD_R43_NATIVE_NOT_A_DICT")
        status=inner.get("status")
        if inner.get("ordersSent")!=0 or inner.get("dispatchAuthorized") is not False or inner.get("armAuthorized") is not False:
            raise Hold("HOLD_R43_NATIVE_SAFETY_MARKERS")
        expected={
            "status":("R43_NOT_INSTALLED_R42_PRESENT_LAST","R43_PRESENT_LAST_READONLY_REASON"),
            "preflight":("R43_PREFLIGHT_LAST155_PASS_NO_INSTALL",),
            "install":("R43_READONLY_REASON_INSTALLED_AWAITING_LIVE",),
            "rollback":("R43_ROLLBACK_RESTORED_R42_LAST",),
            "capture":("R42_LIVE_CLASS_BCS_ASSIGNMENT_OBSERVED_NO_ARM",
                       "R42_CAPTURE_HOLD_CLASS_BCS_UNREADABLE",
                       "R42_CAPTURE_HOLD_MANUAL_REVIEW",
                       "R43_CAPTURE_HOLD_DIAG_ROW_COUNT_OR_FORMAT",
                       "R43_CAPTURE_HOLD_DIAG_INVALID_JSON",
                       "R43_CAPTURE_HOLD_DIAG_FIELDS"),
        }
        accepted=expected[native_mode]
        if status not in accepted:
            reason=inner.get("reason")
            if not (type(reason) is str and len(reason)<=128 and
                    re.fullmatch(r"[A-Z0-9_:.+-]+",reason)):
                reason="HOLD_R43_UNCLASSIFIED_NATIVE_STOP"
            return {"schema":SCHEMA,"status":"R43_NATIVE_HOLD_DETAILS",
                    "innerStatus":status if type(status) is str and status in (
                        "R43_STOP_MANUAL_REVIEW","R43_HOLD_UNEXPECTED_WEIDU_OR_LUA") else "UNCLASSIFIED",
                    "nativeReason":reason,"noAutoRetry":True,
                    "gameModifiedUnknown":native_mode in ("install","rollback"),
                    "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False}
        hold=("_HOLD_" in status)
        if result.returncode not in ((0,3) if (native_mode=="capture" and hold) else (0,)):
            raise Hold("HOLD_R43_NATIVE_EXIT_CODE")
        if native_mode=="capture":
            if hold and inner.get("classScriptResrefAtLiveJaganVerified") is True:
                raise Hold("HOLD_R43_NATIVE_HOLD_DISGUISED_AS_PROOF")
            if not hold and (
                inner.get("classScriptResrefAtLiveJaganVerified") is not True or
                type(inner.get("classScriptResref")) is not str or
                re.fullmatch(r"[A-Z0-9_#*]{1,8}",inner["classScriptResref"]) is None or
                inner.get("scrlev")!=4 or inner.get("partyIndex")!=1 or
                inner.get("actualBcsExecutionVerified") is not False or
                inner.get("manualEpsActionOriginVerified") is not False or
                inner.get("r39ProbeStatus")!="R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY" or
                inner.get("r39ClassSlotState")!="VALID_NAME_CANDIDATE"):
                raise Hold("HOLD_R43_CLASS_ASSIGNMENT_PROOF_INVALID")
        outcome={"schema":SCHEMA,
                 "status":"R43_"+native_mode.upper()+("_HOLD_REASON_OBSERVED" if hold else "_EXACT_GUARDED_PASS"),
                 "innerStatus":status, "sourceCommit":commit,
                 "expectedDiagnosticSHA256":R43_CANDIDATE_SHA,
                 "gameModified":native_mode in ("install","rollback"),
                 "installed":native_mode in ("install","capture") or
                             (native_mode=="status" and inner.get("installed") is True),
                 "classScriptResrefAtLiveJaganVerified":inner.get("classScriptResrefAtLiveJaganVerified") is True,
                 "classScriptResref":inner.get("classScriptResref") if native_mode=="capture" else None,
                 "actualBcsExecutionVerified":False,
                 "manualEpsActionOriginVerified":False,
                 "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False,
                 "noAutoRetry":hold}
        if native_mode=="capture":
            # Never silently turn a failed CLASS resref probe into success.
            if hold:
                outcome["classScriptResrefAtLiveJaganVerified"]=False
                outcome["classScriptResref"]=None
            for key,allowed in (
                ("r39ProbeStatus",("R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY",
                    "HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE","HOLD_SCRIPT_ASSIGNMENT_ACTOR_ID",
                    "HOLD_SCRIPT_ASSIGNMENT_CLASS_OR_KIT","HOLD_SCRIPT_PILOT_PHYSICAL_CONTEXT",
                    "HOLD_SCRIPT_CURSOR_INVALID","HOLD_SCRIPT_RESREF_UNREADABLE",
                    "HOLD_SCRIPT_ACTOR_CHANGED","HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED",
                    "HOLD_SCRIPT_RESREF_CHANGED","HOLD_SCRIPT_CURSOR_CHANGED",
                    "R39_BRIDGE_RESULT_MISSING","R39_PROBE_EXCEPTION","R39_UNCLASSIFIED_STATUS")),
                ("r39ClassSlotState",("NOT_READ","LEVEL_TABLE_MISSING","MISSING_CLASS_ENTRY",
                    "EMPTY","INVALID_RESREF","VALID_NAME_CANDIDATE"))):
                val=inner.get(key)
                if val in allowed:
                    outcome[key]=val
            if type(inner.get("rawConsoleFile")) is str:
                outcome["rawConsoleFile"]=inner["rawConsoleFile"]
            if type(inner.get("rawConsoleBytes")) is int:
                outcome["rawConsoleBytes"]=inner["rawConsoleBytes"]
        return outcome


def choose_mode() -> str:
    print("R42 (single BGXAI_UPDATE.cmd): 1=source RO [default]; 2=status; "
          "3=preflight RO; 4=install (typed); 5=rollback (typed); 6=capture game RO; 0=exit",flush=True)
    print("R43 after R42: 7=status; 8=preflight RO; 9=install typed; "
          "10=rollback typed; 11=capture game RO",flush=True)
    s=input("R42 choice [1]: ").strip()
    if not s:s="1"
    if s=="0":return "exit"
    if s not in MODES:raise Hold("HOLD_INVALID_R42_SUBMENU")
    return MODES[s]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, default=ROOT)
    p.add_argument("--commit", required=True)
    p.add_argument("--native-readonly", action="store_true", required=True)
    p.add_argument("--mode", choices=("source","status","preflight","install","rollback","capture"))
    args = p.parse_args(argv)
    try:
        mode=args.mode if args.mode is not None else choose_mode()
        if mode=="exit":
            result={"schema":SCHEMA,"status":"R42_CANCELLED_NO_CHANGE",
                    "installed":False,"gameModified":False,"ordersSent":0,
                    "dispatchAuthorized":False,"armAuthorized":False}
        elif mode=="source":
            result=run(args.game,args.commit)
        elif mode.startswith("diag_"):
            token=None
            if mode in ("diag_install","diag_rollback"):
                correct=R43_INSTALL_CONFIRM if mode=="diag_install" else R43_ROLLBACK_CONFIRM
                print("R43 "+mode+": guarded WeiDU; close game. No auto retry.",flush=True)
                token=input("Type "+correct+" exactly (ENTER cancels): ").strip()
                if token!=correct:raise Hold("HOLD_EXACT_TYPED_R43_APPROVAL_REQUIRED")
            result=run_diag_guarded(args.game,args.commit,mode,approved_token=token)
        else:
            token=None
            if mode in ("install","rollback"):
                correct=INSTALL_CONFIRM if mode=="install" else ROLLBACK_CONFIRM
                print("R42 "+mode+": this changes installed WeiDU; close game. "
                      "No auto retry/restore after failure.",flush=True)
                token=input("Type "+correct+" exactly (ENTER cancels): ").strip()
                if token!=correct:raise Hold("HOLD_EXACT_TYPED_R42_APPROVAL_REQUIRED")
            result=run_guarded(args.game,args.commit,mode,approved_token=token)
        rc=3 if result.get("noAutoRetry") is True or "_HOLD_" in result.get("status","") else 0
    except (OSError, ValueError, subprocess.TimeoutExpired, EOFError) as error:
        result = {"schema": SCHEMA, "status": "R42_HOLD_ONEFILE_GUARDED",
                  "reason": str(error) if isinstance(error, Hold) else "HOLD_RUNTIME_OR_IO",
                  "noAutoRetry":True,
                  "gameModifiedUnknown":args.mode in ("install","rollback"),
                  "ordersSent": 0, "dispatchAuthorized": False,"armAuthorized":False}
        rc=3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())
