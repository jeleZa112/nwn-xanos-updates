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


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, default=ROOT)
    p.add_argument("--commit", required=True)
    p.add_argument("--native-readonly", action="store_true", required=True)
    args = p.parse_args(argv)
    try:
        result = run(args.game, args.commit)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        result = {"schema": SCHEMA, "status": "R42_HOLD_ONEFILE_RO",
                  "reason": str(error) if isinstance(error, Hold) else "HOLD_RUNTIME_OR_IO",
                  "gameModified": False, "installed": False,
                  "ordersSent": 0, "dispatchAuthorized": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "R42_EXISTING_ONEFILE_SOURCE_READY_NO_INSTALL" else 3


if __name__ == "__main__":
    sys.exit(main())
