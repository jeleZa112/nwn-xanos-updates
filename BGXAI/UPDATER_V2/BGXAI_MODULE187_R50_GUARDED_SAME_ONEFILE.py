#!/usr/bin/env python3
"""Original BGXAI_UPDATE.cmd V2 module187: guarded one-menu R50 management.

V2 hub only accepts <=32768 bytes total JSON index and repeats full SHA assets
for each entry. Keep all old 180..186 entries untouched, add ONE isolated
guarded module187 with distinct extra exact native install and rollback
confirmations inside it. Hub's own exact approval opens an inert management
menu ONLY; no game writes happen on opening. Status RO is default.

Reuses immutable previously mocked/CI-tested R50 native last160->161 guard
and all R49/R48/etc sources. One original CMD and existing PowerShell hub.
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
GUARD=REPO/"BGXAI/BUILD/R50_JAGAN_SCRIPTNAME_FIX_SOURCEONLY_20261128/BGXAI_R50_LAST160_TO161_GUARDED.py"
GUARD_BLOB="282d157f3b19759d7071aeb8634afcca900c5bc1"
GUARD_BYTES=17133
SCHEMA="BGXAI_V2_MODULE187_R50_GUARDED_SAME_ONEFILE_V1"
OPEN="INSTALL_BGXAI_R50_OPEN_GUARDED_MENU_NO_GAME_WRITES"
INSTALL="INSTALL_BGXAI_R50_DWARF_CLERIC_IDENTITY_AFTER_R49_LAST160"
ROLLBACK="ROLLBACK_BGXAI_R50_RESTORE_R49_LAST160_ONLY"

class Hold(ValueError):
    pass

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def load_native():
    if (GUARD.is_symlink() or not GUARD.is_file() or
        GUARD.stat().st_size!=GUARD_BYTES or blob(GUARD.read_bytes())!=GUARD_BLOB):
        raise Hold("HOLD_R50_ONEFILE_EXACT_NATIVE_GUARD_PIN")
    spec=importlib.util.spec_from_file_location("bgxai_r50_last161_native_guarded",GUARD)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R50_ONEFILE_GUARD_IMPORT")
    native=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    if (native.SCHEMA!="BGXAI_R50_JAGAN_DWARF_CLERIC_LAST161_GUARDED_V1"
        or native.INSTALL_TOKEN!=INSTALL or native.ROLLBACK_TOKEN!=ROLLBACK
        or native.ONCE_FLAG!="BGX48TRY"
        or native.SOURCE_BCS!="override/BDDEFAI.BCS"):
        raise Hold("HOLD_R50_ONEFILE_NATIVE_CONTRACT_CHANGED")
    return native

def run(game:Path,kind:str,token:str="",*,require_windows:bool=True,
        loader=load_native):
    if kind not in ("status","preflight","install","rollback"):
        raise Hold("HOLD_R50_ONEFILE_UNKNOWN_ACTION")
    if kind=="install" and token!=INSTALL:
        raise Hold("HOLD_R50_ONEFILE_EXACT_INSTALL_CONSENT")
    if kind=="rollback" and token!=ROLLBACK:
        raise Hold("HOLD_R50_ONEFILE_EXACT_ROLLBACK_CONSENT")
    if kind in ("status","preflight") and token:
        raise Hold("HOLD_R50_ONEFILE_READONLY_TOKEN_NOT_ALLOWED")
    if require_windows and (os.name!="nt" or
        os.path.normcase(os.path.abspath(game))!=
        os.path.normcase(os.path.abspath(GAME))):
        raise Hold("HOLD_R50_ONEFILE_EXACT_WINDOWS_GAME")
    if game.is_symlink() or not game.is_dir():
        raise Hold("HOLD_R50_ONEFILE_MISSING_GAME_ROOT")
    native=loader()
    parts=native.load_checked()
    if kind=="status":
        result=native.status(*parts[:8],game)
        if (type(result) is not dict or result.get("schema")!=native.SCHEMA
            or result.get("gameModified") is not False
            or result.get("ordersSent")!=0
            or result.get("status") not in (
              "R50_NOT_INSTALLED_R49_LAST160",
              "R50_LAST161_INSTALLED_AWAITING_GAME")):
            raise Hold("HOLD_R50_ONEFILE_NATIVE_STATUS_INVALID")
        installed=(result["status"]=="R50_LAST161_INSTALLED_AWAITING_GAME")
        if result.get("installed") is not installed:
            raise Hold("HOLD_R50_ONEFILE_STATUS_INSTALLED_CONTRADICTION")
        return {
          "schema":SCHEMA,
          "status":("R50_LAST161_INSTALLED_VERIFIED_READONLY"
                    if installed else "R50_ABSENT_R49_LAST160_VERIFIED_READONLY"),
          "installed":installed,"gameModified":False,"ordersSent":0,
          "actualXEquipPerformed":False,"noAutoRetry":True
        }
    if kind=="preflight":
        result=native.preflight(*parts,game)
        if (type(result) is not dict or result.get("schema")!=native.SCHEMA
            or result.get("status")!="R50_R49_LAST160_SOURCE_PREFLIGHT_PASS_NO_INSTALL"
            or result.get("r49Last160Verified") is not True
            or result.get("falseNameGuardRemoved") is not True
            or result.get("party1DwarfClericGuardPreserved") is not True
            or result.get("oldOneShotBGX48TRYPreserved") is not True
            or result.get("nativeCompiledOnUserGame") is not False
            or result.get("installed") is not False
            or result.get("gameModified") is not False
            or result.get("ordersSent")!=0):
            raise Hold("HOLD_R50_ONEFILE_NATIVE_PREFLIGHT_INVALID")
        return {"schema":SCHEMA,
            "status":"R50_R49_LAST160_PREFLIGHT_PASS_READONLY",
            "installed":False,"gameModified":False,"ordersSent":0,
            "candidateBAFSHA256":result["candidateBAFSHA256"],
            "nativeCompiledOnUserGame":False,"noAutoRetry":True}
    if kind=="install":
        result=native.install(*parts,game,token)
        if (type(result) is not dict or result.get("schema")!=native.SCHEMA or
            result.get("status")!="R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME" or
            result.get("installed") is not True or
            result.get("r49Last160Preserved") is not True or
            result.get("userApproved") is not True or
            result.get("sourceItem")!="STAF01" or
            result.get("sourceBackpackSlots")!=list(range(18,34)) or
            result.get("onceFlag")!="BGX48TRY" or
            result.get("targetWeaponSlot")!=35 or
            result.get("ordersSentAtInstall")!=0 or
            result.get("actualXEquipPerformed") is not False):
            raise Hold("HOLD_R50_ONEFILE_NATIVE_INSTALL_MANUAL_REVIEW")
        return {"schema":SCHEMA,
            "status":"R50_LAST161_INSTALLED_AWAITING_GAMEPLAY",
            "installed":True,"gameModified":True,
            "originalR49Last160Preserved":True,
            "ordersSentAtInstall":0,"actualXEquipPerformed":False,
            "oneShotBGX48TRYStillInEffect":True,"noAutoRetry":True}
    result=native.rollback(*parts[:8],game,token)
    if (type(result) is not dict or result.get("schema")!=native.SCHEMA or
        result.get("status")!="R50_ROLLBACK_RESTORED_ORIGINAL_R49_LAST160" or
        result.get("installed") is not False):
        raise Hold("HOLD_R50_ONEFILE_NATIVE_ROLLBACK_MANUAL_REVIEW")
    return {"schema":SCHEMA,
        "status":"R50_ROLLBACK_TO_R49_LAST160_VERIFIED",
        "installed":False,"gameModified":True,"ordersSentAtInstall":0,
        "savedActorOneShotFlagReset":False,"noAutoRetry":True}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--onefile-hub-guarded",action="store_true")
    p.add_argument("--approved-token",default="")
    args=p.parse_args(argv)
    if not args.onefile_hub_guarded or args.approved_token!=OPEN:
        print(json.dumps({"schema":SCHEMA,
            "status":"R50_STOP_EXPLICIT_ORIGINAL_ONEFILE_MENU_APPROVAL_REQUIRED",
            "gameModified":False,"ordersSent":0,"noAutoRetry":True}))
        return 3
    print("R50 (same original CMD) 0=exit [default]; 1=status RO; "
          "2=preflight RO; 3=install typed #161; 4=rollback typed only #161")
    answer=input("R50 choice [0]: ").strip()
    choices={"0":None,"1":"status","2":"preflight",
             "3":"install","4":"rollback"}
    if answer not in choices or answer=="0" or not answer:
        print(json.dumps({"schema":SCHEMA,"status":"R50_USER_CANCELLED_NO_WRITES",
               "gameModified":False,"ordersSent":0}))
        return 0
    kind=choices[answer]
    token=""
    if kind in ("install","rollback"):
        expected=INSTALL if kind=="install" else ROLLBACK
        token=input("Type "+expected+" exactly (ENTER cancels): ").strip()
        if token!=expected:
            print(json.dumps({"schema":SCHEMA,
                "status":"R50_STOP_NO_NATIVE_WRITES_USER_DECLINED_EXACT_TOKEN",
                "gameModified":False,"ordersSent":0,"noAutoRetry":True}))
            return 3
    try:
        result=run(args.game,kind,token)
        rc=0
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as ex:
        reason=str(ex).split(":",1)[0]
        if not re.fullmatch(r"HOLD_[A-Z0-9_]{5,120}",reason):
            reason="HOLD_R50_ONEFILE_MANUAL_REVIEW_REQUIRED"
        result={"schema":SCHEMA,"status":"R50_STOP_MANUAL_REVIEW",
           "reason":reason,"installed":None,
           "gameModifiedUnknown":kind in ("install","rollback"),
           "ordersSent":0,"noAutoRetry":True,
           "actualXEquipPerformed":False}
        rc=3
    print(json.dumps(result,ensure_ascii=True,indent=2))
    return rc

if __name__=="__main__":
    raise SystemExit(main())
