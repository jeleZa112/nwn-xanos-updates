#!/usr/bin/env python3
"""R34: join REAL R33 selected-action samples to CURRENT installed ITM prof IDs.

This is NOT a weapon selector. It refuses to guess alternate effective APR,
target protection, spell/buff effects, action ownership, or a safe switch time.
Reuses the existing SHA-pinned R3 KEY/BIFF/ITM parser, never reimplements it.
No game writes, no EEex hooks, no new updater, no WeiDU or BCS changes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

SCHEMA = "BGXAI_R34_R33_NATIVE_ITM_PROF_JOIN_RO_V1"
ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
R3_REL = Path("BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py")
R3_SHA = "ed87a7a6618826c6d3901d2579a39bf280fcaeb09cd18b7b6ee159b9ebfcc74a"
R33_SHA = "1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069"
R33_SCHEMA = "BGXAI_R33_R31_PASSIVE_PROF_GUARDED_V1"
MAX_LOG = 6_000_000
MAX_EVENTS = 512
EXPECTED_R33_LOG_NAME = "BGXAI_R33_CONSOLE_20261125T161358491052Z.log"
EXPECTED_R33_LOG_SHA = "d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538"
MAX_CANDIDATE_LOGS = 128
REF = re.compile(r"^[A-Z0-9_#-]{1,8}$")
WPROF = {90:"LONG_SWORD",92:"AXE",102:"QUARTERSTAFF",
         104:"LONG_BOW",105:"SHORT_BOW"}
EXPECTED_WEAPONS = (35,36,37,38)
EXPECTED_AMMO = (11,12,13,14)

class Hold(ValueError):
    pass

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def must(ok: bool, reason: str) -> None:
    if not ok:
        raise Hold(reason)

def int_exact(x, lo, hi):
    return type(x) is int and lo <= x <= hi

def clean_slots(items, nums):
    must(type(items) is list and len(items)==len(nums), "SLOT_ARRAY_SHAPE")
    result={}
    for i,n in enumerate(nums):
        x=items[i]
        must(type(x) is dict and x.get("slot")==n, "SLOT_INDEX_DRIFT")
        ref=x.get("resrefRaw")
        must(ref is None or (type(ref) is str and REF.fullmatch(ref) is not None),
             "SLOT_RESREF_INVALID")
        result[n]=ref
    return result

def read_session(raw: bytes) -> dict:
    must(0<len(raw)<=MAX_LOG,"LOG_SIZE_UNSUPPORTED")
    try:
        lines=raw.decode("utf-8-sig").splitlines()
    except UnicodeError as ex:
        raise Hold("LOG_ENCODING_UNSUPPORTED") from ex
    must(len(lines)<=30000,"LOG_TOO_MANY_LINES")
    sessions=[]
    rows=[]
    prefix="INFO: LUA: [BGXR27] "
    for line in lines:
        if not line.startswith(prefix):
            continue
        try:
            obj=json.loads(line[len(prefix):])
        except (ValueError,UnicodeError) as ex:
            raise Hold("R33_EVENT_INVALID_JSON") from ex
        must(type(obj) is dict,"R33_EVENT_NOT_OBJECT")
        if obj.get("type")=="SESSION":
            sessions.append(obj)
        elif obj.get("type")=="R27_SINGLE_CALLBACK":
            rows.append(obj)
            must(len(rows)<=MAX_EVENTS,"R33_TOO_MANY_EVENTS")
    must(len(sessions)==1,"R33_SESSION_COUNT_NOT_ONE")
    ses=sessions[0]
    must(ses.get("observerCandidate")=="R33_R27V3_PASSIVE_PROF_RO"
         and ses.get("readOnly") is True
         and ses.get("ordersSent")==0
         and ses.get("weaponSwitchAuthorized") is False
         and ses.get("dispatchAuthorized") is False, "R33_SESSION_FLAGS_INVALID")
    must(len(rows)>0,"R33_NO_SELECTED_EVENTS")
    actor, party,loadout=None,None,None
    apr_keys=set()
    total_stats=0
    action_raw=[]
    profile=None
    for seq,x in enumerate(rows,1):
        must(x.get("schema")=="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1"
             and x.get("status")=="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE"
             and x.get("seq")==seq
             and x.get("readOnly") is True
             and x.get("ordersSent")==0
             and x.get("localsWritten")==0
             and x.get("dispatchAuthorized") is False
             and x.get("weaponSwitchAuthorized") is False
             and x.get("sameLuaListenerInvocation") is True, "R33_EVENT_CONTRACT_DRIFT")
        must(all(x.get(k) is True for k in (
            "rawInventoryDoubleReadConsistent",
            "selectedDerivedStatsDoubleReadConsistent",
            "queueSnapshotStable",
            "actionContextSnapshotStable")), "R33_SNAPSHOT_UNSTABLE")
        must(int_exact(x.get("actor"),1,2147483647)
             and int_exact(x.get("partyIndex"),0,5), "ACTOR_OR_PARTY_INVALID")
        if actor is None:
            actor,party=x["actor"],x["partyIndex"]
        must(x["actor"]==actor and x["partyIndex"]==party,
             "CROSS_ACTOR_OR_PARTY_EVENTS")
        stats=x.get("proficiencyStat89to134Raw")
        must(type(stats) is list and len(stats)==46
             and all(int_exact(s,0,65535) for s in stats),
             "R33_WPROF_46_FIELDS_INVALID")
        levels=x.get("levelsAndKitRaw")
        # Kit is commonly a multi-byte bitmask; verify levels separately.
        must(type(levels) is dict
             and all(int_exact(levels.get(k),0,255) for k in ("level1","level2","level3"))
             and int_exact(levels.get("kitRaw"),0,4294967295),"R33_LEVELS_OR_KIT_INVALID")
        weapon=clean_slots(x.get("quickWeaponsRaw"),EXPECTED_WEAPONS)
        ammo=clean_slots(x.get("quiversRaw"),EXPECTED_AMMO)
        off=clean_slots(x.get("offhandRaw"),(9,))
        fp=(tuple(weapon.items()),tuple(ammo.items()),tuple(off.items()))
        if loadout is None:
            loadout=fp
            profile=(tuple(stats),levels)
        must(fp==loadout,"R33_EQUIPMENT_CHANGED_DURING_CAPTURE")
        must((tuple(stats),levels)==profile,"R33_PROFICIENCY_CHANGED_DURING_CAPTURE")
        must(int_exact(x.get("selectedAprKeyRaw"),0,255),"R33_SELECTED_APR_KEY_INVALID")
        apr_keys.add(x["selectedAprKeyRaw"])
        must(int_exact(x.get("actionRaw"),0,65535),"R33_ACTION_INVALID")
        action_raw.append(x["actionRaw"])
        # Source pointer is not authenticated: never infer the action is EPS/manual.
        total_stats+=len(stats)
    return {"sourceLogSha256":sha(raw),"sampleCount":len(rows),
            "levelsAndKitRaw":profile[1],"stats":profile[0],
            "loadout":{"weapons":dict(loadout[0]),"ammo":dict(loadout[1]),
                       "offhand":dict(loadout[2])},
            "selectedAprKeysRaw":sorted(apr_keys),
            "actionRawValues":sorted(set(action_raw)),
            "rawStatReads":total_stats}

def load_r3(path: Path):
    must(path.is_file() and not path.is_symlink(),"R3_SOURCE_FILE_UNAVAILABLE")
    raw=path.read_bytes()
    must(len(raw)==18641 and sha(raw)==R3_SHA,"R3_SOURCE_SHA256_MISMATCH")
    spec=importlib.util.spec_from_file_location("bgxai_r3_pinned",path)
    must(spec is not None and spec.loader is not None,"R3_MODULE_SPEC_INVALID")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate_game(root: Path) -> None:
    must(os.name=="nt" and os.path.normcase(os.path.abspath(root))==
         os.path.normcase(os.path.abspath(ROOT)), "EXACT_WINDOWS_GAME_ROOT_ONLY")
    must(root.is_dir() and not root.is_symlink(),"GAME_ROOT_UNSAFE")
    live=root/"override"/"M_BGXR27.lua"
    must(live.is_file() and not live.is_symlink() and sha(live.read_bytes())==R33_SHA,
         "R33_LIVE_LUA_PIN_MISMATCH")
    proof=root/"BGXR33"/"PROOF.json"
    must(proof.is_file() and not proof.is_symlink() and proof.stat().st_size<100000,
         "R33_INSTALLED_PROOF_UNAVAILABLE")
    data=json.loads(proof.read_text(encoding="utf-8"))
    must(data.get("schema")==R33_SCHEMA
         and data.get("status")=="R33_PASSIVE_INSTALLED_AWAITING_RUNTIME"
         and data.get("installationPerformed") is True
         and data.get("sourceSha256")==R33_SHA,"R33_INSTALL_PROOF_INCONSISTENT")

def join(log: bytes, source, parse_itm, *, game_identity_verified: bool=False) -> dict:
    """No root or files written; source injected for deterministic/mock tests."""
    event=read_session(log)
    result={"schema":SCHEMA,"status":"HOLD","readOnly":True,
            "gameModified":False,"ordersSent":0,"dispatchAuthorized":False,
            "weaponSwitchAuthorized":False,"adviceOnly":True,
            "safeDispatchTimeVerified":False,"manualAndEPSOriginVerified":False,
            "alternateEffectiveAPRVerified":False,"targetProtectionsVerified":False,
            "allBuffsAndEffectsVerified":False,"actorClassRowVerified":False,
            "dualMultiClassVerified":False,"ammoLauncherEngineBindingVerified":False,
            "sourceLogSha256":event["sourceLogSha256"],
            "r33EventCount":event["sampleCount"],
            "sameActorSameLoadoutSnapshots":True,
            "r33SelectedAprKeysRaw":event["selectedAprKeysRaw"],
            "observedActionIdsRaw":event["actionRawValues"],
            "levelsAndKitRaw":event["levelsAndKitRaw"],
            "liveGamePinVerified":game_identity_verified,
            "sameSessionItemResourcesVerified":False,
            "resourceItems":[],
            "actionOwnershipStatus":"ACTION_SOURCE_POINTER_UNAVAILABLE"}
    names={}
    for kind,slotmap in event["loadout"].items():
        for slot,ref in slotmap.items():
            if ref:
                names.setdefault(ref,[]).append((kind,slot))
    must(len(names)<=9,"TOO_MANY_DISTINCT_ITM_ITEMS")
    rows=[]
    for ref in sorted(names):
        raw, provenance=source.get(ref,".ITM")
        itm=parse_itm(raw)
        must(type(itm) is dict and itm.get("schema")=="BGXAI_ITM_RAW_V1"
             and itm.get("rawOnly") is True,"R3_ITM_PARSE_CONTRACT_FAILED")
        must(provenance.get("sha256")==sha(raw) and
             provenance.get("origin") in ("CURRENT_GAME_OVERRIDE","CURRENT_GAME_BIFF"),
             "R3_NOT_CURRENT_GAME_RESOURCE")
        pid=itm.get("proficiencyIdRaw")
        must(int_exact(pid,0,255),"ITM_PROFICIENCY_ID_INVALID")
        rank=event["stats"][pid-89] & 7 if 89<=pid<=134 else None
        slots=[{"kind":kind,"slot":slot} for kind,slot in names[ref]]
        # ID outside WPROF 89..134 is NOT "zero pips"; it is unknown.
        rows.append({"resref":ref,"sourceOrigin":provenance["origin"],
            "resourceSha256":sha(raw),"slots":slots,
            "itemTypeRaw":itm.get("itemTypeRaw"),
            "proficiencyStatIdRaw":pid,
            "proficiencyLabelKnown":WPROF.get(pid),
            "proficiencyLowThreeBitsObserved":rank,
            "rawStatForProficiency":event["stats"][pid-89] if rank is not None else None,
            "noProficiencyInLiveActor":rank==0 if rank is not None else None,
            "twoHandedFlagRaw":itm.get("twoHandedFlagRaw"),
            "minStrengthRaw":itm.get("minStrengthRaw"),
            "abilityHeadersRaw":[{"attackTypeRaw":a.get("attackTypeRaw"),
                "launcherRequiredRaw":a.get("launcherRequiredRaw"),
                "rangeRaw":a.get("rangeRaw"),
                "baseDamageMeanBeforeEffects":a.get("baseDamageMeanBeforeEffects"),
                "abilityEffectOpcodesRaw":[e.get("opcodeRaw") for e in a.get("effects",[])]}
                for a in itm.get("abilities",[])],
            "equippedEffectOpcodesRaw":[e.get("opcodeRaw") for e in itm.get("equippedEffects",[])],
            "characterCanEquipVerified":False,
            "targetEffectiveDamageVerified":False,
            "effectiveAPRForThisSlotVerified":False,
            "weaponSwitchAuthorized":False})
    result["resourceItems"]=rows
    result["nativeResourceCount"]=len(rows)
    result["status"]=("CURRENT_NATIVE_ITM_PROF_GROUPS_JOINED_RO_NO_SWITCH" if game_identity_verified else "R34_SOURCE_ONLY_SYNTHETIC_JOIN_NO_SWITCH")
    result["proficiencyMismatches"]=[{"resref":r["resref"],
        "slots":r["slots"],"proficiencyStatIdRaw":r["proficiencyStatIdRaw"]}
        for r in rows if any(s["kind"]=="weapons" for s in r["slots"])
        and r["noProficiencyInLiveActor"] is True]
    return result

def _reference_fingerprint(event: dict) -> bool:
    """Known non-private fingerprint from uploaded eight-event R33 source.

    A matching fingerprint is SOURCE CANDIDATE only. It does NOT authenticate
    the bytes of the uploaded file, game actor identity at a later time,
    action origin, item effects, or alternate APR.
    """
    stats=event["stats"]
    slots=event["loadout"]
    return (event["sampleCount"]==8
            and event["actionRawValues"]==[3,23]
            and event["levelsAndKitRaw"]=={
                "level1":1,"level2":1,"level3":1,"kitRaw":16384}
            and stats[90-89]==2 and stats[92-89]==1
            and stats[104-89]==1 and stats[105-89]==0
            and slots["weapons"]=={
                35:"SW1H04",36:"BOW05",37:None,38:"STAF01"}
            and slots["ammo"]=={
                11:None,12:"AROW01",13:None,14:None}
            and slots["offhand"]=={9:"SHLD03A"})

def choose_r33_log(reports: Path) -> tuple[bytes,dict]:
    """Read only from the known reports folder; no more game capture.

    Strongly prefer the exact uploaded log SHA. If it was copied,
    re-encoded or renamed, accept only ONE fully parsed R33 session
    with the independently recorded eight-event fingerprint and mark
    exact-byte provenance as NOT verified. Fail closed on ambiguity.
    """
    must(reports.is_dir() and not reports.is_symlink()
         and not (hasattr(reports,"is_junction") and reports.is_junction()),
         "R34_REPORT_FOLDER_MISSING_OR_REPARSE")
    found=list(reports.glob("BGXAI_R33_CONSOLE_*.log"))
    must(len(found)<=MAX_CANDIDATE_LOGS,"R34_TOO_MANY_R33_LOG_CANDIDATES")
    exact=reports / EXPECTED_R33_LOG_NAME
    paths=sorted(found,key=lambda p:(p.name!=EXPECTED_R33_LOG_NAME,p.name))
    matches=[]
    for path in paths:
        if path.is_symlink() or (hasattr(path,"is_junction") and path.is_junction()) or not path.is_file():
            continue
        if not 0<path.stat().st_size<=MAX_LOG:
            continue
        raw=path.read_bytes()
        if not 0<len(raw)<=MAX_LOG:
            continue
        try:
            event=read_session(raw)
        except Hold:
            continue
        if not _reference_fingerprint(event):
            continue
        match_sha=sha(raw)==EXPECTED_R33_LOG_SHA
        rec={"sourceLogFilename":path.name,
             "sourceLogSha256":sha(raw),
             "referenceUploadedLogSha256":EXPECTED_R33_LOG_SHA,
             "sameBytesAsUserUploadedLogVerified":match_sha,
             "sameEightEventFingerprintCandidate":True,
             "logSourceStatus":("EXACT_UPLOADED_BYTES_VERIFIED" if match_sha
                                else "STRUCTURAL_R33_FINGERPRINT_ONLY_DIFFERENT_SHA"),
             "fileFoundUnderReports":True}
        if match_sha:
            return raw,rec
        matches.append((raw,rec))
    if len(matches)==1:
        return matches[0]
    if not found:
        raise Hold("R34_R33_LOG_MISSING_IN_REPORTS_NO_RECAPTURE")
    if matches:
        raise Hold("R34_R33_LOG_AMBIGUOUS_STRUCTURAL_MATCHES_NO_RECAPTURE")
    if exact.is_file() and not exact.is_symlink() and not (hasattr(exact,"is_junction") and exact.is_junction()):
        raise Hold("R34_R33_NAMED_LOG_DIFFERS_AND_FAILS_FINGERPRINT")
    raise Hold("R34_R33_LOGS_EXIST_BUT_REFERENCE_SESSION_NOT_FOUND")

def main() -> int:
    cli=argparse.ArgumentParser()
    cli.add_argument("--game",type=Path,default=ROOT)
    cli.add_argument("--reports-dir",type=Path,required=True)
    cli.add_argument("--r3-source",type=Path,required=True)
    args=cli.parse_args()
    try:
        validate_game(args.game)
        raw, provenance=choose_r33_log(args.reports_dir)
        r3=load_r3(args.r3_source)
        out=join(raw,r3.NativeSource(args.game),
                 r3.parse_itm,game_identity_verified=True)
        out.update(provenance)
        print(json.dumps(out,ensure_ascii=False,indent=2))
        return 0
    except (Hold,OSError,ValueError) as err:
        print(json.dumps({"schema":SCHEMA,"status":"R34_HOLD",
            "reason":str(err)[:180],"readOnly":True,"gameModified":False,
            "ordersSent":0,"dispatchAuthorized":False,
            "weaponSwitchAuthorized":False},ensure_ascii=False,indent=2))
        return 2

if __name__=="__main__":
    sys.exit(main())
