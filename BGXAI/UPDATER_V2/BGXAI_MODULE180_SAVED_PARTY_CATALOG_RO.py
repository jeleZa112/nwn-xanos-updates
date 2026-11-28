#!/usr/bin/env python3
"""BGXAI V2 module 180: one saved-party GAM + original R3 ITM -> passive Lua.

No game script, WeiDU, save, or installed resource is ever modified.
The catalog is NOT live current actor inventory or alternate effective APR.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
R3_PATH=ROOT/"BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py"
GAM_PATH=ROOT/"BGXAI/BUILD/WEAPON_SAVE_GAM_INVENTORY_RO_V1_20261126/BGXAI_GAM_INVENTORY_RO_V1.py"
SCHEMA="BGXAI_V2_MENU180_SAVED_PARTY_TO_R3_INERT_LUA_V1"

class Hold(ValueError):pass

def load(path:Path,name:str):
    if not path.is_file() or path.is_symlink():raise Hold("HOLD_REQUIRED_OLD_MODULE_MISSING")
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise Hold("HOLD_MODULE_IMPORT")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def choose_gam(game:Path,documents:Path)->Path:
    roots=(
        documents/"Baldur's Gate - Enhanced Edition Trilogy"/"save",
        documents/"Baldur's Gate II - Enhanced Edition"/"save",
        documents/"Baldur's Gate - Enhanced Edition"/"save",
        game/"save",
    )
    found=[]
    for rank,root in enumerate(roots):
        if root.is_symlink() or not root.is_dir():continue
        children=list(root.iterdir())
        if len(children)>512:raise Hold("HOLD_TOO_MANY_SAVE_FOLDERS")
        for parent in children:
            if not parent.is_dir() or parent.is_symlink():continue
            path=parent/"BALDUR.GAM"
            if path.is_symlink() or not path.is_file():continue
            st=path.stat()
            if 0<st.st_size<=50_000_000:
                found.append((st.st_mtime_ns,-rank,str(path).casefold(),path))
    if not found:raise Hold("HOLD_NO_EXISTING_BALDUR_GAM")
    found.sort(reverse=True)
    if len(found)>1 and found[0][0]==found[1][0]:
        raise Hold("HOLD_TWO_NEWEST_GAM_SAME_TIMESTAMP")
    return found[0][3]

def saved_names(gam:dict)->set[str]:
    if not isinstance(gam,dict) or gam.get("schema")!=(
        "BGXAI_GAM_V20_PARTY_INVENTORY_SOURCE_RO_V1") or (
        gam.get("status")!="SAVED_PARTY_GAM_READONLY_PARSED_NOT_LIVE_GAME") or (
        gam.get("userGameRuntimeItemPresentVerified") is not False) or (
        gam.get("saveMatchesCurrentlyLoadedSessionVerified") is not False) or (
        gam.get("partyActorEngineIdVerified") is not False) or (
        not isinstance(gam.get("partyMembers"),list)) or (
        not 1<=len(gam["partyMembers"])<=6):
        raise Hold("HOLD_SAVED_GAM_NOT_PROVEN_AS_SAVED_SOURCE")
    names=set();seen_party=set()
    for actor in gam["partyMembers"]:
        if type(actor) is not dict or type(actor.get("partyIndex")) is not int or (
            actor["partyIndex"] in seen_party) or (
            not 0<=actor["partyIndex"]<=5) or (
            actor.get("actorIdNotAvailableInSave") is not True) or (
            not isinstance(actor.get("topLevelSlots"),list)) or (
            len(actor["topLevelSlots"])!=39):
            raise Hold("HOLD_GAM_PARTY_39_SLOTS_UNTRUSTED")
        seen_party.add(actor["partyIndex"])
        for slot,raw in enumerate(actor["topLevelSlots"]):
            if not isinstance(raw,dict) or raw.get("slot")!=slot:
                raise Hold("HOLD_GAM_SLOT_INDEX_UNTRUSTED")
            if slot==10:
                if raw.get("status")!="UNOBSERVED_IMPLICIT_FIST_SLOT":
                    raise Hold("HOLD_GAM_IMPLICIT_FIST_NOT_OBSERVED")
            elif raw.get("status")=="PRESENT_RAW":
                rr=raw.get("resref")
                if not isinstance(rr,str) or not (1<=len(rr)<=8) or (
                    not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_#-" for c in rr)):
                    raise Hold("HOLD_GAM_ITEM_RESREF_INVALID")
                names.add(rr)
            elif raw.get("status")!="EMPTY":
                raise Hold("HOLD_GAM_SLOT_STATUS_NOT_SUPPORTED")
    if not names or len(names)>234:raise Hold("HOLD_GAM_ITEM_COUNT_INVALID")
    return names

def build_source(gam:dict, audit:dict, keyhash:str, r3)->str:
    names=saved_names(gam)
    if not isinstance(keyhash,str) or len(keyhash)!=64 or (
        any(c not in "0123456789abcdef" for c in keyhash)):
        raise Hold("HOLD_GAME_RESOURCE_KEY_DIGEST")
    if not isinstance(audit,dict) or audit.get("schema")!=(
        "BGXAI_WEAPON_NATIVE_ITM_R3_READONLY") or (
        audit.get("sourceKind")!="CURRENT_GAME") or (
        audit.get("status")!="ITM_NATIVE_ALL_ITEMS_RAW_READ") or (
        audit.get("dispatchAuthorized") is not False) or (
        audit.get("weaponSwitchAuthorized") is not False) or (
        audit.get("missingItemsOrLinkedSpells")) or (
        set(audit.get("items",{}))!=names) or (
        sorted(audit.get("requestedItems",[]))!=sorted(names)):
        raise Hold("HOLD_R3_CURRENT_GAME_RESOURCE_COVERAGE")
    compact=r3._r3_compact_items(audit,names)
    people=[]
    for actor in gam["partyMembers"]:
        inv={}
        for raw in actor["topLevelSlots"]:
            k=raw["slot"]
            inv[k]={"slot":k,"status":raw["status"]}
            if raw["status"]=="PRESENT_RAW":
                inv[k]["resref"]=raw["resref"]
                for field in ("useCount1Raw","useCount2Raw","useCount3Raw","flagsRaw"):
                    value=raw.get(field)
                    high=0xffffffff if field=="flagsRaw" else 0xffff
                    if type(value) is not int or not 0<=value<=high:
                        raise Hold("HOLD_GAM_ITEM_INSTANCE_FLAGS_UNTRUSTED")
                    inv[k][field]=value
        people.append({
            "partyIndex":actor["partyIndex"],
            "inventoryRawMapFromSavedGAM":inv,
            "actorIdNotAvailableInSave":True,
            "sourceSaveNotCurrentGameProcess":True,
            "liveItemInstancesVerified":False,
        })
    catalog={
        "schema":"BGXAI_R3_GAM_SAVED_PARTY_STATIC_LUA_V1",
        "status":"SAVED_PARTY_CATALOG_NON_EXECUTABLE",
        "sourceKind":"SAVED_GAM_WITH_CURRENT_GAME_RESOURCE_BYTES",
        "partyMembers":people,
        "items":compact,
        "gamSha256":gam["gamSha256"],
        "chitinSha256":keyhash,
        "rawUniqueItemResources":len(names),
        "liveInventorySnapshotAuthenticated":False,
        "alternateSlotEffectiveAprVerified":False,
        "alternateSlotEffectiveThac0Verified":False,
        "targetImmunitiesAndProtectionsVerified":False,
        "manualEpsRoundBoundaryVerified":False,
        "reuseOnlyAfterLiveR37SameActorCrosscheck":True,
        "dispatchAuthorized":False,
        "inventoryMoveAuthorized":False,
        "executable":False,
        "gameModified":False,
        "ordersSent":0
    }
    return r3._r3_lua_source(catalog,
       "Saved GAM not live R37. Do not use for runtime dispatch without revalidation.")

def run(game:Path,documents:Path,reports:Path,*,game_required:bool=True,
        source_path:Path|None=None)->dict:
    info={"schema":SCHEMA,"status":"HOLD_SAVED_PARTY_CATALOG_PREPARATION",
          "gameModified":False,"ordersSent":0,"dispatchAuthorized":False,
          "inventoryMoveAuthorized":False,"sourceOnly":True,
          "gameplayAIInstalled":False,"noAutoRetry":True}
    try:
        if game_required and (os.name!="nt" or
            os.path.normcase(os.path.abspath(game))!=
            os.path.normcase(os.path.abspath(GAME))):
            raise Hold("HOLD_REAL_WINDOWS_GAME_PATH_REQUIRED")
        if game.is_symlink() or not game.is_dir():raise Hold("HOLD_GAME_NOT_FOLDER")
        key=game/"chitin.key"
        if key.is_symlink() or not key.is_file():raise Hold("HOLD_GAME_CHITIN_MISSING")
        if reports.resolve()==game.resolve() or (
            game.resolve() in reports.resolve().parents):
            raise Hold("HOLD_REPORT_DIRECTORY_INSIDE_GAME")
        if reports.is_symlink():raise Hold("HOLD_REPORTS_DIRECTORY_REPARSE")
        # Create output directory ONLY outside the EET tree.
        reports.mkdir(parents=True,exist_ok=True)
        game_module=load(GAM_PATH,"bgxai_existing_saved_gam_parser_v1")
        r3=load(R3_PATH,"bgxai_existing_r3_itm_parser_v3")
        selected=source_path if source_path is not None else choose_gam(game,documents)
        if selected.is_symlink() or not selected.is_file() or (
            not 0<selected.stat().st_size<=50_000_000):
            raise Hold("HOLD_SELECTED_GAM_NOT_SAFE")
        saved=selected.read_bytes()
        gam=game_module.parse(saved)
        if gam["gamSha256"]!=hashlib.sha256(saved).hexdigest():
            raise Hold("HOLD_GAM_PARSER_SOURCE_DIGEST_MISMATCH")
        key_before=hashlib.sha256(key.read_bytes()).hexdigest()
        names=saved_names(gam)
        audited=r3.audit(r3.NativeSource(game),sorted(names),
                         {"sourceKind":"SAVED_GAM_DOES_NOT_PROVE_LIVE"})
        text=build_source(gam,audited,key_before,r3)
        if selected.read_bytes()!=saved or key_before!=hashlib.sha256(
                key.read_bytes()).hexdigest():
            raise Hold("HOLD_GAME_OR_SAVED_SOURCE_CHANGED_DURING_AUDIT")
        content=text.encode("ascii")
        digest=hashlib.sha256(content).hexdigest()
        stem="BGXAI_GAM_R3_"+gam["gamSha256"][:12]+"_"+digest[:12]
        output=reports/(stem+".lua")
        report=reports/(stem+".json")
        done={**info,"status":"SOURCE_CATALOG_READY_OUTSIDE_GAME",
              "noAutoRetry":False,
              "sourceGAMHash":gam["gamSha256"],
              "chitinKeyHash":key_before,"catalogHash":digest,
              "partyCount":len(gam["partyMembers"]),
              "uniqueItemResources":len(names),
              "catalogPath":str(output),"reportPath":str(report),
              "liveInventoryVerified":False,
              "actorNativeStatsVerified":False,
              "r39EquipAuthorized":False}
        record=(json.dumps(done,ensure_ascii=True,indent=2,sort_keys=True)+"\n").encode("ascii")
        # Never silently overwrite an earlier staged catalog with new bytes.
        for path,blob in ((output,content),(report,record)):
            if path.is_symlink():raise Hold("HOLD_REPORT_OUTPUT_REPARSE")
            if path.exists():
                if not path.is_file() or path.read_bytes()!=blob:
                    raise Hold("HOLD_REPORT_OUTPUT_CONFLICT")
            else:
                with path.open("xb") as f:
                    f.write(blob);f.flush();os.fsync(f.fileno())
        return done
    except (Hold,OSError,ValueError,TypeError,KeyError,AttributeError) as e:
        info["reason"]=str(e) if isinstance(e,Hold) else "HOLD_R3_GAM_STAGE_IO_OR_SOURCE"
        return info

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--onefile-hub-source-only",action="store_true",required=True)
    args=p.parse_args(argv)
    if not args.onefile_hub_source_only:
        print(json.dumps({"schema":SCHEMA,"status":"HOLD_ONLY_EXISTING_ONEFILE_READONLY"}))
        return 3
    documents=Path.home()/"Documents"
    reports=documents/"BGXAI_LIVE_REPORTS"
    result=run(args.game,documents,reports)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["status"]=="SOURCE_CATALOG_READY_OUTSIDE_GAME" else 3

if __name__=="__main__":
    raise SystemExit(main())
