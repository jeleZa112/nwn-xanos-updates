#!/usr/bin/env python3
"""BGXAI menu 175: pinned source-only / native read-only XEquipItem preflight.

Invoked ONLY by the existing BGXAI_UPDATE.cmd -> SHA-pinned BGXAI_SYNC.ps1.
Never install an action; the sole BAF under test contains mandatory False().
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

SCHEMA = "BGXAI_XEQUIP_ONEFILE_175_READONLY_V1"
REPO = "jeleZa112/nwn-xanos-updates"
PREFIX = "BGXAI/BUILD/WEAPON_XEQUIP_NATIVE_INERT_PILOT_V1_20261126/"
BACKEND = "BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py"
WRAPPER = PREFIX + "BGXAI_XEQUIP_NATIVE_PREFLIGHT_RO_V1.py"
GENERATOR = PREFIX + "BGXAI_XEQUIP_INERT_PROBE_V1.py"
MANIFEST = PREFIX + "EXAMPLE_ONLY_NOT_USER_EET.json"
SOURCES = {
    WRAPPER: (7345, "44830e915ce1ca5d9e2e8ed430857388cfbe217568491803972db61ecf262741"),
    GENERATOR: (4442, "77fc4681a78460f3ba5ac83c6056a2259b86880680fbc9b03692e0cd798a5137"),
    MANIFEST: (188, "2aef6c3b98ce147e3da388038583a217b6c3fa8155f6984765819758564cc8c7"),
    BACKEND: (9551, "27285b3d067eab2c67b075dc8654b9a0f74da0d7920b2e96339ced3e14bcd10a"),
}
# Separate V3 source allowlist; menu175's existing four pinned sources stay intact.
V3_PREFIX = "BGXAI/BUILD/WEAPON_XEQUIP_V3_NATIVE_RO_20261127/"
V3_WRAPPER = V3_PREFIX + "BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py"
V3_EVIDENCE = V3_PREFIX + "BGXAI_REAL_JAGAN_BUILD_AUDIT_AND_BAF_V3.json"
V3_SOURCES = {
    V3_WRAPPER: (10743, "b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e"),
    V3_EVIDENCE: (1942, "83a6865028336b9a2ebec5645ae34670832f1b07f372620f9c3961968a378b28"),
    BACKEND: SOURCES[BACKEND],
}
V3_BAF_SHA256 = "996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1"

# R38 passive observer sub-menu. Three independently pinned sources; no second CMD.
R38_PREFIX = "BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/"
R38_PY = R38_PREFIX + "BGXAI_R38_GUARDED_FROM_R37.py"
R38_LUA = "BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua"
R38_R37_HELPER = "BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py"
R38_SOURCES = {
    R38_PY: (21303, "f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c"),
    R38_LUA: (78927, "958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c"),
    R38_R37_HELPER: (26252, "b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d"),
}
R38_MODES = ("preflight", "status", "install", "rollback", "capture")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")

class Hold(ValueError):
    pass

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def validate_pin(commit: str) -> str:
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise Hold("HOLD_IMMUTABLE_COMMIT_INVALID")
    return commit

def fetch_pinned(commit: str, path: str) -> bytes:
    validate_pin(commit)
    if path not in SOURCES and path not in V3_SOURCES and path not in R38_SOURCES:
        raise Hold("HOLD_SOURCE_NOT_ALLOWLISTED")
    err = []
    for base in (
        "https://raw.githubusercontent.com/" + REPO + "/" + commit + "/",
        "https://cdn.jsdelivr.net/gh/" + REPO + "@" + commit + "/",
    ):
        try:
            req = urllib.request.Request(base + path,
                headers={"User-Agent": "BGXAI-Onefile175-NoAPI"})
            with urllib.request.urlopen(req, timeout=25) as h:
                raw = h.read((SOURCES.get(path) or V3_SOURCES.get(path) or R38_SOURCES[path])[0] + 1)
            verify_file(path, raw)
            return raw
        except (OSError, ValueError, Exception) as exc:
            err.append(type(exc).__name__)
    raise Hold("HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:" + ",".join(err))

def verify_file(path: str, raw: bytes) -> None:
    expected = SOURCES.get(path) or V3_SOURCES.get(path) or R38_SOURCES.get(path)
    if expected is None or not isinstance(raw, bytes):
        raise Hold("HOLD_SOURCE_NOT_ALLOWLISTED")
    if len(raw) != expected[0] or digest(raw) != expected[1]:
        raise Hold("HOLD_PINNED_SOURCE_SHA256_OR_SIZE_DRIFT:" + path.rsplit("/", 1)[-1])

def ensure_external(work: Path, game: Path) -> None:
    root = game.resolve(strict=False)
    target = work.resolve(strict=True)
    if target == root or root in target.parents or target in root.parents:
        raise Hold("HOLD_TEMP_IN_GAME_OR_PARENT")

def stage_sources(root: Path, commit: str, fetcher=fetch_pinned, sources=None) -> dict:
    validate_pin(commit)
    out = {}
    for path in (SOURCES if sources is None else sources):
        raw = fetcher(commit, path)
        verify_file(path, raw)
        p = root.joinpath(*path.split("/"))
        if root not in p.parents or p.is_symlink():
            raise Hold("HOLD_SOURCE_STAGING_PATH")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        if digest(p.read_bytes()) != (SOURCES.get(path) or V3_SOURCES.get(path) or R38_SOURCES[path])[1]:
            raise Hold("HOLD_LOCAL_SOURCE_SHA256_CHANGED")
        out[path] = {"sha256": (SOURCES.get(path) or V3_SOURCES.get(path) or R38_SOURCES[path])[1], "bytes": len(raw)}
    return out

def check_report(inner: dict, native: bool) -> bool:
    if not isinstance(inner, dict):
        return False
    if inner.get("installed") is not False or inner.get("ordersSent") != 0:
        return False
    if inner.get("dispatchAuthorized") is not False or inner.get("inventoryMoveAuthorized") is not False:
        return False
    if native:
        return (inner.get("status") == "NATIVE_WEIDU_COMPILED_TEMP_ONLY"
            and inner.get("nativeSymbolsAcceptedByCompiler") is True
            and inner.get("watchedFilesChanged") is False
            and inner.get("temporaryOutputRemoved") is True)
    return (inner.get("status") == "INERT_SOURCE_READY_NO_NATIVE_COMPILE"
        and inner.get("nativeSymbolsAcceptedByCompiler") is False
        and inner.get("nativeWeiDUCompileVerified") is False)

def prepare(game: Path, commit: str, native: bool,
            fetcher=fetch_pinned, runner=subprocess.run) -> dict:
    validate_pin(commit)
    # Runtime script is always staged OUTSIDE the game; no BCS, TLK or override write.
    with tempfile.TemporaryDirectory(prefix="BGXAI_XEQUIP175_RO_") as directory:
        folder = Path(directory).resolve(strict=True)
        ensure_external(folder, game)
        sources = stage_sources(folder, commit, fetcher)
        script = folder.joinpath(*WRAPPER.split("/"))
        sample = folder.joinpath(*MANIFEST.split("/"))
        args = [sys.executable, str(script), "--manifest", str(sample),
                "--game", str(game)]
        if native:
            args.append("--native-readonly")
        proc = runner(args, cwd=str(folder), stdin=subprocess.DEVNULL,
             capture_output=True, text=True, encoding="utf-8",
             errors="replace", timeout=120, check=False)
        if proc.returncode not in (0, 3):
            return {"schema": SCHEMA, "status": "HOLD_WRAPPER_PROCESS",
                "exitCode": proc.returncode, "sourcePins": sources}
        try:
            inner = json.loads(proc.stdout)
        except (ValueError, TypeError):
            return {"schema": SCHEMA, "status": "HOLD_WRAPPER_JSON",
                "sourcePins": sources}
        ok = proc.returncode == 0 and check_report(inner, native)
        return {
            "schema": SCHEMA,
            "status": ("NATIVE_INERT_WEIDU_COMPILE_PASS_TEMP_ONLY"
                       if ok and native else
                       "INERT_SOURCE_PIN_VERIFIED_NO_NATIVE" if ok else
                       "HOLD_INERT_SOURCE_OR_NATIVE_COMPILE"),
            "sourcePins": sources,
            "nativePreflightRequested": bool(native),
            "innerReport": inner,
            "gameplayFeatureInstalled": False,
            "gameplayLiveVerified": False,
            "itemInstanceIdentityVerified": False,
            "safeActionBoundaryVerified": False,
            "manualEpsOriginVerified": False,
            "gameplayMoveAuthorized": False,
            "ordersSent": 0,
            "newGameFilesWrittenByThisRunner": 0,
        }

def check_report_v3(inner: dict, native: bool) -> bool:
    if not isinstance(inner, dict) or inner.get("installed") is not False or (
        type(inner.get("ordersSent")) is not int or inner["ordersSent"] != 0
    ) or inner.get("dispatchAuthorized") is not False:
        return False
    if inner.get("bafSha256") != V3_BAF_SHA256 or inner.get("bafBytes") != 762:
        return False
    if inner.get("safeActionBoundaryVerified") is not False or (
        inner.get("runtimeActorIdentityVerified") is not False
    ):
        return False
    if native:
        return (inner.get("status") == "V3_NATIVE_BAF_COMPILED_TEMP_ONLY"
                and inner.get("nativeWeiDUCompileVerified") is True
                and inner.get("watchedFilesChanged") is False
                and inner.get("temporaryOutputRemoved") is True
                and isinstance(inner.get("compiledBcsSha256"), str)
                and re.fullmatch(r"[a-f0-9]{64}", inner["compiledBcsSha256"]) is not None)
    return (inner.get("status") == "EXACT_V3_BAF_PIN_VERIFIED_NO_NATIVE_COMPILE"
            and inner.get("nativeWeiDUCompileVerified") is False)

def prepare_v3(game: Path, commit: str, native: bool,
               fetcher=fetch_pinned, runner=subprocess.run) -> dict:
    validate_pin(commit)
    with tempfile.TemporaryDirectory(prefix="BGXAI_XEQUIP176_V3_RO_") as directory:
        folder = Path(directory).resolve(strict=True)
        ensure_external(folder, game)
        sources = stage_sources(folder, commit, fetcher, V3_SOURCES)
        script = folder.joinpath(*V3_WRAPPER.split("/"))
        evidence = folder.joinpath(*V3_EVIDENCE.split("/"))
        backend = folder.joinpath(*BACKEND.split("/"))
        args = [sys.executable, str(script), "--game", str(game),
                "--evidence", str(evidence), "--backend", str(backend)]
        if native: args.append("--native-readonly")
        proc = runner(args, cwd=str(folder), stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120, check=False)
        try:
            inner = json.loads(proc.stdout)
        except (ValueError,TypeError):
            inner = {"status":"HOLD_INVALID_V3_WRAPPER_JSON"}
        ok = proc.returncode == 0 and check_report_v3(inner, native)
        return {
            "schema": "BGXAI_XEQUIP_ONEFILE_176_V3_READONLY_V1",
            "status": ("V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL" if ok and native
                else "V3_EXACT_SOURCE_PIN_PASS_NOT_NATIVE" if ok else
                "HOLD_V3_NATIVE_OR_SOURCE_PREFLIGHT"),
            "sourcePins": sources,
            "innerReport": inner,
            "nativePreflightRequested": bool(native),
            "gameplayFeatureInstalled": False,
            "gameplayLiveVerified": False,
            "safeActionBoundaryVerified": False,
            "runtimeActorIdentityVerified": False,
            "gameplayMoveAuthorized": False,
            "ordersSent": 0,
            "newGameFilesWrittenByThisRunner": 0,
        }


def ask_r38_mode(v3: bool, forced: str | None = None) -> str | None:
    if forced is not None:
        if not v3 or forced not in R38_MODES:
            raise Hold("HOLD_R38_REQUIRES_MENU176")
        return forced
    if not v3 or sys.stdin is None or not sys.stdin.isatty():
        return None  # Existing automated/menu176 V3 read-only behavior is unchanged.
    print("BGXAI 176: 1=V3 native RO [default]; 2=R38 preflight; "
          "3=status; 4=install (typed); 5=rollback (typed); 6=capture; 0=exit",flush=True)
    choice=input("R38 choice [1]: ").strip()
    if choice in ("", "1"): return None
    if choice == "0": return "cancel"
    mode = {"2":"preflight","3":"status","4":"install",
            "5":"rollback","6":"capture"}.get(choice)
    if mode is None: raise Hold("HOLD_R38_UNKNOWN_SUBMENU_CHOICE")
    return mode


def run_r38(game: Path, commit: str, mode: str, fetcher=fetch_pinned,
            runner=subprocess.run) -> int:
    validate_pin(commit)
    if mode not in R38_MODES:
        raise Hold("HOLD_R38_MODE_NOT_ALLOWED")
    with tempfile.TemporaryDirectory(prefix="BGXAI_R38_ONEFILE_") as folder_name:
        folder=Path(folder_name).resolve(strict=True)
        ensure_external(folder,game)
        pins=stage_sources(folder,commit,fetcher,R38_SOURCES)
        script=folder.joinpath(*R38_PY.split("/"))
        candidate=folder.joinpath(*R38_LUA.split("/"))
        previous=folder.joinpath(*R38_R37_HELPER.split("/"))
        print("BGXAI R38: sources SHA-pinned, mode="+mode
              +"; no automatic game install; existing updater only.",flush=True)
        args=[sys.executable,str(script),"--game",str(game),
              "--mode",mode,"--candidate",str(candidate),
              "--r37-tool",str(previous)]
        # Child prompts for exact typed install/rollback token. Keep a real
        # console; never pipe, invent or auto-answer approval.
        result=runner(args,cwd=str(folder),stdin=None,
                      stdout=None,stderr=None,check=False)
        return int(result.returncode)

def write_report(report: dict, target: Path) -> str:
    # A SINGLE external report file is the user's only upload when asked.
    target = target.expanduser()
    if target.is_symlink():
        raise Hold("HOLD_REPORT_PATH_SYMLINK")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise Hold("HOLD_REPORT_ALREADY_EXISTS")
    with target.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return str(target)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=Path(r"C:\Games\BG_EET_FOXX_NEW"))
    parser.add_argument("--commit", required=True)
    parser.add_argument("--native-readonly", action="store_true")
    parser.add_argument("--v3", action="store_true", help="Use exact V3 BAF read-only preflight for menu176")
    parser.add_argument("--r38-mode", choices=R38_MODES, help="Test-only explicit R38 mode through menu176")
    parser.add_argument("--report", type=Path)
    a = parser.parse_args(argv)
    try:
        mode = ask_r38_mode(a.v3,a.r38_mode)
        if mode == "cancel":
            print("BGXAI R38 cancelled. No changes.")
            return 0
        if mode in R38_MODES:
            return run_r38(a.game,a.commit,mode)
    except (Hold,OSError,ValueError,subprocess.TimeoutExpired,EOFError) as exc:
        report = {"schema":"BGXAI_R38_ONEFILE_LOADER_HOLD_V1",
                  "status":"R38_SOURCE_STAGE_HOLD","reason":str(exc),
                  "gameplayFeatureInstalled":False,"ordersSent":0,
                  "newGameFilesWrittenByThisRunner":0}
        if os.name=="nt":
            target=Path.home()/"Documents"/"BGXAI_LIVE_REPORTS"/(
                "BGXAI_R38_SOURCE_HOLD_"+dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")+".json")
            try: report["reportFile"]=write_report(report,target)
            except (OSError,Hold) as err: report["reportFileError"]=str(err)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 3
    try:
        report = (prepare_v3(a.game, a.commit, a.native_readonly) if a.v3
                  else prepare(a.game, a.commit, a.native_readonly))
    except (Hold, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        report = {"schema": "BGXAI_XEQUIP_ONEFILE_176_V3_READONLY_V1" if a.v3 else SCHEMA,
            "status": "HOLD_XEQUIP176_V3" if a.v3 else "HOLD_XEQUIP175",
            "reason": str(exc), "gameplayFeatureInstalled": False,
            "ordersSent": 0, "newGameFilesWrittenByThisRunner": 0}
    path = a.report
    if path is None and os.name == "nt":
        name = ("BGXAI_XEQUIP176_V3_RO_" if a.v3 else "BGXAI_XEQUIP175_RO_") + dt.datetime.now().strftime("%Y%m%dT%H%M%S%f") + ".json"
        path = Path.home() / "Documents" / "BGXAI_LIVE_REPORTS" / name
    if path is not None:
        try:
            report["reportFile"] = write_report(report, path)
        except (OSError, Hold) as exc:
            report["reportFileError"] = str(exc)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in (
        "NATIVE_INERT_WEIDU_COMPILE_PASS_TEMP_ONLY",
        "INERT_SOURCE_PIN_VERIFIED_NO_NATIVE",
        "V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL",
        "V3_EXACT_SOURCE_PIN_PASS_NOT_NATIVE") else 3

if __name__ == "__main__":
    raise SystemExit(main())
