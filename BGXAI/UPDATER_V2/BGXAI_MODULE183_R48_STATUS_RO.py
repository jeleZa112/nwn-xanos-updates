#!/usr/bin/env python3
"""BGXAI V2 option 183: recover R48 install state after closed console.

READ ONLY. Reuses pinned original option 181/182 bridge, which authenticates
the original R48 guard. R48.status uses WeiDU last-only proofs and BCS SHA.
This module NEVER installs, rolls back, opens game, or sends any action.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
BRIDGE=ROOT/"BGXAI/UPDATER_V2/BGXAI_MODULE181_182_R48_ONE_SHOT_GUARDED.py"
SCHEMA="BGXAI_V2_R48_POST_CLOSED_CONSOLE_STATUS_READONLY_V1"
ALLOWED={
 "R48_NOT_INSTALLED_R47_LAST158":"R48_NOT_INSTALLED_VERIFIED",
 "R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT":"R48_INSTALLED_AWAITING_GAMEPLAY_VERIFIED",
}

class Hold(ValueError):
    pass

def load_previous_bridge():
    if not BRIDGE.is_file() or BRIDGE.is_symlink():
        raise Hold("HOLD_R48_V2_ORIGINAL_BRIDGE_ABSENT")
    spec=importlib.util.spec_from_file_location("bgxai_v2_original_r48_bridge",BRIDGE)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R48_V2_ORIGINAL_BRIDGE_IMPORT")
    bridge=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    if (bridge.SCHEMA!=
        "BGXAI_V2_MENU181_182_REUSE_EXISTING_R48_ONE_SHOT_GUARDED_V1"):
        raise Hold("HOLD_R48_V2_ORIGINAL_BRIDGE_CONTRACT")
    # The existing upstream bridge validates original native R48 git blob,
    # exact tokens and original R48 schema; not a second implementation.
    return bridge

def inspect(game:Path, *, require_windows:bool=True, bridge_loader=load_previous_bridge):
    if require_windows and (
        os.name!="nt" or os.path.normcase(os.path.abspath(game))!=
        os.path.normcase(os.path.abspath(GAME))):
        raise Hold("HOLD_R48_V2_EXACT_WINDOWS_GAME_ONLY")
    if game.is_symlink() or not game.is_dir():
        raise Hold("HOLD_R48_V2_GAME_DIRECTORY")
    bridge=bridge_loader()
    native=bridge.load_original()
    parents=native.load_checked()
    # Original upstream R48.status is already read-only and strictly
    # checks R47/R48 WeiDU ordering, PROOF and BCS SHA256.
    data=native.status(*parents[:-1],game)
    if (not isinstance(data,dict) or data.get("schema")!=native.SCHEMA or
        data.get("status") not in ALLOWED or
        data.get("installed") is not (
            data["status"]=="R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT") or
        data.get("gameModified") is not False):
        raise Hold("HOLD_R48_V2_NATIVE_STATUS_CONTRACT")
    return {
      "schema":SCHEMA,
      "status":ALLOWED[data["status"]],
      "nativeStatus":data["status"],
      "installed":data["installed"],
      "gameModified":False,
      "ordersSent":0,
      "actualXEquipPerformed":False,
      "noInstallOrRollbackAttempted":True,
      "sourceOnly":False,
      "statusOnly":True,
      "next":("ONE_EXPLICIT_GAMEPLAY_TEST_ON_DISPOSABLE_SAVE"
              if data["installed"] else
              "NO_AUTOMATIC_REINSTALL_OR_ROLLBACK"),
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--onefile-hub-source-only",action="store_true")
    args=p.parse_args(argv)
    try:
        if not args.onefile_hub_source_only:
            raise Hold("HOLD_R48_V2_ORIGINAL_ONEFILE_REQUIRED")
        report=inspect(args.game)
        exit_code=0
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as err:
        # Failed read-only verification says UNKNOWN, NOT installed/absent.
        reason=str(err).split(":",1)[0]
        if not re.fullmatch(r"HOLD_[A-Z0-9_]{5,105}",reason):
            reason="HOLD_R48_V2_STATE_UNKNOWN"
        report={"schema":SCHEMA,"status":"R48_STATE_UNVERIFIED_DO_NOT_REINSTALL",
            "reason":reason,"installed":None,"gameModified":False,
            "ordersSent":0,"noAutoRetry":True,
            "manualReviewRequired":True}
        exit_code=3
    print(json.dumps(report,ensure_ascii=True,indent=2))
    return exit_code

if __name__=="__main__":
    raise SystemExit(main())
