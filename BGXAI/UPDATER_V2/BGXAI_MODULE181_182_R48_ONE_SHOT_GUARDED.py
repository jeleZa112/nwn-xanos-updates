#!/usr/bin/env python3
"""BGXAI original onefile V2: expose EXISTING R48 real single-item WeiDU guard.

181 = separately typed, one-shot real STAF01 install (never silent).
182 = independently typed last-only R48 rollback (never automatic).
The existing R48 guard/composer performs all native checks; no second
installer, no new CMD, no new evaluator, no gameplay action in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
GUARD=ROOT/"BGXAI/BUILD/R48_ONE_REAL_STAF01_EQUIP_AFTER_R47_20261128/BGXAI_R48_LAST158_TO159_ONE_ITEM_GUARDED.py"
GUARD_GIT_BLOB="1051bfd0f4fc767590468924dc8147e6e86ec768"
GUARD_LENGTH=15135
INSTALL="INSTALL_BGXAI_R48_ONE_STAF01_FROM_BACKPACK_TO_WEAPON_AFTER_R47"
ROLLBACK="ROLLBACK_BGXAI_R48_RESTORE_R47_ONLY"
SCHEMA="BGXAI_V2_MENU181_182_REUSE_EXISTING_R48_ONE_SHOT_GUARDED_V1"

class Hold(ValueError):
    pass

def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def load_original():
    if GUARD.is_symlink() or not GUARD.is_file() or GUARD.stat().st_size!=GUARD_LENGTH:
        raise Hold("HOLD_R48_ORIGINAL_GUARD_SOURCE_ABSENT")
    raw=GUARD.read_bytes()
    if gitblob(raw)!=GUARD_GIT_BLOB:
        raise Hold("HOLD_R48_ORIGINAL_GUARD_BLOB_MISMATCH")
    spec=importlib.util.spec_from_file_location("bgxai_v2_original_r48_native_guard",GUARD)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R48_ORIGINAL_GUARD_IMPORT")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if (mod.INSTALL_TOKEN!=INSTALL or mod.ROLLBACK_TOKEN!=ROLLBACK or
        mod.SCHEMA!="BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1"):
        raise Hold("HOLD_R48_ORIGINAL_CONSENT_CONTRACT_CHANGED")
    return mod

def run(game:Path,token:str,*,require_windows:bool=True,loader=load_original):
    if token not in (INSTALL,ROLLBACK):
        raise Hold("HOLD_R48_V2_EXACT_GUARDED_TOKEN_REQUIRED")
    if require_windows and (os.name!="nt" or
        os.path.normcase(os.path.abspath(game))!=
        os.path.normcase(os.path.abspath(GAME))):
        raise Hold("HOLD_R48_V2_EXACT_WINDOWS_EET_REQUIRED")
    if game.is_symlink() or not game.is_dir():
        raise Hold("HOLD_R48_V2_GAME_DIRECTORY")
    native=loader()
    parents=native.load_checked()
    if token==INSTALL:
        # The ORIGINAL R48 guard checks current WeiDU #158, protected SHA,
        # process shutdown, game archive, backups, exact native compiler,
        # and ONE real STAF01 action before any game writes.
        data=native.install(*parents,game,token)
        if not isinstance(data,dict) or (
            data.get("schema")!=native.SCHEMA or
            data.get("status")!="R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME" or
            data.get("installed") is not True or
            data.get("userApprovedRealItemMove") is not True or
            data.get("actualXEquipPerformed") is not False or
            data.get("sourceItem")!="STAF01" or
            data.get("sourceBackpackSlot")!=20 or
            data.get("targetWeaponSlot")!=35):
            raise Hold("HOLD_R48_V2_NATIVE_INSTALL_PROOF_INVALID_MANUAL_REVIEW")
        return {"schema":SCHEMA,"status":"R48_GUARDED_ONE_SHOT_INSTALLED_AWAITING_GAME",
            "nativeStatus":data["status"],"gameModified":True,
            "manualReviewIfInterrupted":True,"installed":True,
            "oneShotAttemptMayRunOnlyInGame":True,
            "actualXEquipPerformed":False,"ordersSentAtInstall":0}
    # Only the exact original R48's protected last159 rollback may run.
    data=native.rollback(*parents[:-1],game,token)
    if not isinstance(data,dict) or (
        data.get("schema")!=native.SCHEMA or
        data.get("status")!="R48_ROLLBACK_RESTORED_R47_LAST158" or
        data.get("installed") is not False):
        raise Hold("HOLD_R48_V2_NATIVE_ROLLBACK_PROOF_INVALID_MANUAL_REVIEW")
    return {"schema":SCHEMA,"status":"R48_GUARDED_LAST159_ROLLBACK_COMPLETE",
        "nativeStatus":data["status"],"gameModified":True,
        "installed":False,"actualXEquipPerformed":False,
        "note":"WeiDU rollback does not restore save-game LOCALS or inventory"}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--onefile-hub-guarded",action="store_true")
    p.add_argument("--approved-token",default="")
    args=p.parse_args(argv)
    if not args.onefile_hub_guarded or args.approved_token not in (INSTALL,ROLLBACK):
        print(json.dumps({"schema":SCHEMA,"status":"HOLD_R48_V2_EXPLICIT_ONEFILE_CONSENT_REQUIRED",
            "gameModified":False,"noAutoRetry":True}))
        return 3
    try:
        report=run(args.game,args.approved_token)
        rc=0
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        # In a native WeiDU failure the game may have changed; never
        # silently roll back or retry. Do not leak filepaths / save names.
        reason=str(exc).split(":",1)[0]
        if not re.fullmatch(r"[A-Z0-9_]{6,100}",reason) or not (
            reason.startswith("HOLD_")):
            reason="HOLD_R48_V2_NATIVE_MANUAL_REVIEW_REQUIRED"
        report={"schema":SCHEMA,"status":"R48_STOP_MANUAL_REVIEW",
          "reason":reason,"gameModifiedUnknown":True,
          "actualXEquipPerformed":False,"noAutoRetry":True}
        rc=3
    print(json.dumps(report,ensure_ascii=True,indent=2))
    return rc

if __name__=="__main__":
    raise SystemExit(main())
