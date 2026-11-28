#!/usr/bin/env python3
"""One original BGXAI_UPDATE.cmd V2: R49 status/preflight 184, typed install
185, typed last-only rollback 186. Reuses immutable existing R49 native guard.

Guarded install cannot run without a separate EXACT consent in the existing
V2 PowerShell hub, which prompts BEFORE staging, verifies pinned asset SHA,
then supplies --onefile-hub-guarded and --approved-token. Never auto-retry.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

REPO=Path(__file__).resolve().parents[2]
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
NATIVE=REPO/"BGXAI/BUILD/R49_R48_BACKPACK16_SOURCE_ONLY_20261128/BGXAI_R49_LAST159_TO160_GUARDED.py"
NATIVE_GIT_BLOB="3c147e1f5c1b7de811f7bbf590e22d2b702cbffa"
NATIVE_SIZE=16559
SCHEMA="BGXAI_V2_R49_MENUS184_185_186_ORIGINAL_GUARDED_V1"
INSTALL="INSTALL_BGXAI_R49_BACKPACK16_ONE_STAF01_AFTER_R48_LAST159"
ROLLBACK="ROLLBACK_BGXAI_R49_RESTORE_R48_LAST159_ONLY"

class Hold(ValueError):
    pass

def gitblob(payload:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(payload)).encode("ascii")+b"\0"+payload).hexdigest()

def load_native():
    if (NATIVE.is_symlink() or not NATIVE.is_file() or
        NATIVE.stat().st_size!=NATIVE_SIZE or
        gitblob(NATIVE.read_bytes())!=NATIVE_GIT_BLOB):
        raise Hold("HOLD_R49_ONEFILE_NATIVE_SOURCE_PIN")
    spec=importlib.util.spec_from_file_location("bgxai_existing_r49_last160_guard",NATIVE)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R49_ONEFILE_NATIVE_IMPORT")
    native=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    if (native.SCHEMA!="BGXAI_R49_BACKPACK16_ONE_STAF01_LAST160_GUARDED_V1" or
        native.INSTALL_TOKEN!=INSTALL or native.ROLLBACK_TOKEN!=ROLLBACK or
        native.ONCE_FLAG!="BGX48TRY" or native.SOURCE_BCS!="override/BDDEFAI.BCS"):
        raise Hold("HOLD_R49_ONEFILE_NATIVE_CONTRACT")
    return native

def run(game:Path,*,token:str="",require_windows:bool=True,loader=load_native):
    if token not in ("",INSTALL,ROLLBACK):
        raise Hold("HOLD_R49_ONEFILE_EXACT_TOKEN")
    if (require_windows and (os.name!="nt" or
        os.path.normcase(os.path.abspath(game))!=
        os.path.normcase(os.path.abspath(GAME)))):
        raise Hold("HOLD_R49_ONEFILE_EXACT_WINDOWS_GAME")
    if game.is_symlink() or not game.is_dir():
        raise Hold("HOLD_R49_ONEFILE_GAME_DIRECTORY")
    native=loader()
    parts=native.load_checked()
    if token=="":
        current=native.status(*parts[:7],game)
        if (type(current) is not dict or current.get("schema")!=native.SCHEMA or
            current.get("gameModified") is not False or
            current.get("ordersSent")!=0):
            raise Hold("HOLD_R49_ONEFILE_NATIVE_STATUS_CONTRACT")
        if current.get("status")=="R49_BACKPACK16_LAST160_INSTALLED_AWAITING_GAME":
            if current.get("installed") is not True or (
                current.get("actualXEquipPerformed") is not False):
                raise Hold("HOLD_R49_ONEFILE_INSTALLED_PROOF")
            return {"schema":SCHEMA,"status":"R49_LAST160_INSTALLED_VERIFIED_READONLY",
                "nativeStatus":current["status"],"installed":True,
                "gameModified":False,"ordersSent":0,"actualXEquipPerformed":False,
                "noAutoRetry":True,"noInstallOrRollbackAttempted":True}
        if current.get("status")!="R49_NOT_INSTALLED_R48_LAST159" or (
            current.get("installed") is not False):
            raise Hold("HOLD_R49_ONEFILE_UNEXPECTED_LAST_STATE")
        pre=native.preflight(*parts,game)
        if (type(pre) is not dict or pre.get("schema")!=native.SCHEMA or
            pre.get("status")!="R49_SOURCE_PREFLIGHT_R48_LAST159_PASS_NO_INSTALL" or
            pre.get("originalR48Last159Verified") is not True or
            pre.get("oldR48OneShotFlagReused") is not True or
            pre.get("onlyOneNewXEquipSourceAction") is not True or
            pre.get("nativeCompilationOnUserEETVerified") is not False or
            pre.get("gameModified") is not False or
            pre.get("installed") is not False or pre.get("ordersSent")!=0):
            raise Hold("HOLD_R49_ONEFILE_NATIVE_PREFLIGHT_CONTRACT")
        return {"schema":SCHEMA,"status":"R49_LAST159_TO160_PREFLIGHT_PASS_READONLY",
            "nativeStatus":pre["status"],"installed":False,
            "originalR48Last159Verified":True,"gameModified":False,
            "ordersSent":0,"nativeCompiledOnUserEET":False,
            "candidateBafSHA256":pre["candidateBafSHA256"],
            "noAutoRetry":True,"noInstallOrRollbackAttempted":True}
    if token==INSTALL:
        result=native.install(*parts,game,token)
        if (type(result) is not dict or result.get("schema")!=native.SCHEMA or
            result.get("status")!="R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME" or
            result.get("installed") is not True or
            result.get("originalR48Last159Preserved") is not True or
            result.get("sourceBackpackSlot22Included") is not True or
            result.get("sourceBackpackSlots")!=list(range(18,34)) or
            result.get("onceFlag")!="BGX48TRY" or
            result.get("ordersSentAtInstall")!=0 or
            result.get("actualXEquipPerformed") is not False):
            raise Hold("HOLD_R49_ONEFILE_NATIVE_INSTALL_PROOF_MANUAL_REVIEW")
        return {"schema":SCHEMA,"status":"R49_LAST160_INSTALLED_AWAITING_GAMEPLAY",
            "nativeStatus":result["status"],"installed":True,
            "gameModified":True,"ordersSentAtInstall":0,
            "actualXEquipPerformed":False,
            "originalR48Last159Preserved":True,
            "oneShotBGX48TRYStillInEffect":True,
            "manualReviewIfInterrupted":True,
            "noAutoRetry":True}
    result=native.rollback(*parts[:7],game,token)
    if (type(result) is not dict or result.get("schema")!=native.SCHEMA or
        result.get("status")!="R49_ROLLBACK_RESTORED_ORIGINAL_R48_LAST159" or
        result.get("installed") is not False):
        raise Hold("HOLD_R49_ONEFILE_NATIVE_ROLLBACK_PROOF_MANUAL_REVIEW")
    return {"schema":SCHEMA,"status":"R49_ROLLBACK_RESTORED_R48_LAST159",
        "nativeStatus":result["status"],"installed":False,
        "gameModified":True,"ordersSentAtInstall":0,
        "noAutoRetry":True,
        "note":"No rollback of saved actor BGX48TRY or inventory"}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game",type=Path,required=True)
    parser.add_argument("--onefile-hub-source-only",action="store_true")
    parser.add_argument("--onefile-hub-guarded",action="store_true")
    parser.add_argument("--approved-token",default="")
    args=parser.parse_args(argv)
    readonly=args.onefile_hub_source_only and not args.onefile_hub_guarded and (
        args.approved_token=="")
    guarded=args.onefile_hub_guarded and not args.onefile_hub_source_only and (
        args.approved_token in (INSTALL,ROLLBACK))
    if not (readonly or guarded):
        print(json.dumps({"schema":SCHEMA,
             "status":"R49_STOP_EXPLICIT_ORIGINAL_ONEFILE_REQUIRED",
             "gameModified":False,"ordersSent":0,"noAutoRetry":True}))
        return 3
    try:
        report=run(args.game,token="" if readonly else args.approved_token)
        rc=0
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        reason=str(exc).split(":",1)[0]
        if not re.fullmatch(r"HOLD_[A-Z0-9_]{5,100}",reason):
            reason="HOLD_R49_ONEFILE_NATIVE_MANUAL_REVIEW"
        report={"schema":SCHEMA,"status":"R49_STOP_MANUAL_REVIEW",
            "reason":reason,
            "gameModifiedUnknown":not readonly,
            "noAutoRetry":True,"ordersSent":0,
            "installed":None,"actualXEquipPerformed":False}
        rc=3
    print(json.dumps(report,indent=2,ensure_ascii=True))
    return rc

if __name__=="__main__":
    raise SystemExit(main())
