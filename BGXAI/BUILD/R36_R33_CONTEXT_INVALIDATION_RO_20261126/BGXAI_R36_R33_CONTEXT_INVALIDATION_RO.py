#!/usr/bin/env python3
"""BGXAI R36: validate existing R33 same-callback records, invalidate ONLY advice.

This is an offline consumer of the already-captured R33 console, NOT an
EEex listener, an APR calculator or a game patch. It does not read or write
the installed game, actor action queue, or system state. It NEVER approves a
weapon switch. In particular the R33 sample lacks full effect fingerprints
and verified manual/EPS action origin. A zero queue count is NOT authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA="BGXAI_R36_R33_OBSERVED_CONTEXT_INVALIDATION_RO_V1"
R33_SCHEMA="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1"
R33_SHA="d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538"
R33_EVENT_STATUS="CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE"
R4_STATUS="RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS"
MAX_FILE_BYTES=6_000_000
MAX_EVENTS=64
EVENT_TAG="[BGXR27]"
FIELDS=("m_nNumberOfAttacks","m_nTHAC0","m_nSTR","m_nSTRExtra",
        "m_bImprovedHaste","m_nHitBonus")
LEVELS=("level1","level2","level3","kitRaw")
RESREF=re.compile(r"^[A-Z0-9_#-]{1,8}$")


class Hold(Exception):
    pass


def require(predicate,reason):
    if not predicate:
        raise Hold(reason)


def exact_int(x,lo,hi):
    return type(x) is int and lo<=x<=hi


def safe(status,**details):
    result={
        "schema":SCHEMA,"status":status,
        "readOnly":True,"sourceOnly":True,"gameModified":False,
        "ordersSent":0,"localsWritten":0,"actionQueueCleared":False,
        "currentActionPreserved":True,"dispatchAuthorized":False,
        "weaponSwitchAuthorized":False,"executable":False,
        "alternateEffectiveAPRVerified":False,
        "fullActiveEffectsVerified":False,"sameBuffContextVerified":False,
        "manualEpsOriginVerified":False,"safeActionBoundaryVerified":False,
        "launcherAmmoBindingVerified":False,
        "classRowVerified":False,
        "zeroQueueDoesNotProveFreeAction":True,
    }
    result.update(details)
    return result


def _slots(event,key,indices):
    group=event.get(key)
    require(type(group) is list and len(group)==len(indices),
            "INCOMPLETE_"+key.upper())
    normalized=[]
    for item,slot in zip(group,indices):
        require(type(item) is dict and item.get("slot")==slot,
                "SLOT_LAYOUT_DRIFT_"+key.upper())
        ref=item.get("resrefRaw")
        if ref is None:
            require(all(item.get("useCount"+str(k)+"Raw") is None for k in (1,2,3)),
                    "EMPTY_SLOT_WITH_COUNTS")
            normalized.append((slot,None,None,None,None))
        else:
            require(type(ref) is str and RESREF.fullmatch(ref) is not None,
                    "INVALID_RESREF")
            counts=[item.get("useCount"+str(k)+"Raw") for k in (1,2,3)]
            require(all(exact_int(v,0,65535) for v in counts),
                    "OCCUPIED_SLOT_WITHOUT_RAW_COUNTS")
            normalized.append((slot,ref,*counts))
    return tuple(normalized)


def _event(event,index,actor):
    require(type(event) is dict and
            event.get("schema")==R33_SCHEMA and
            event.get("type")=="R27_SINGLE_CALLBACK" and
            event.get("status")==R33_EVENT_STATUS,
            "R33_EVENT_SCHEMA_STATUS")
    require(event.get("seq")==index and exact_int(event.get("actor"),1,2147483647)
            and exact_int(event.get("partyIndex"),0,5)
            and exact_int(event.get("actionRaw"),0,65535)
            and exact_int(event.get("selectedWeaponRaw"),0,65535)
            and exact_int(event.get("selectedAbilityRaw"),0,65535)
            and exact_int(event.get("selectedAprKeyRaw"),0,10),
            "R33_SEQUENCE_OR_SCALARS")
    if actor is not None:
        require(event["actor"]==actor,"ACTOR_CHANGED")
    for key in ("readOnly","sameLuaListenerInvocation",
                "rawInventoryDoubleReadConsistent",
                "selectedDerivedStatsDoubleReadConsistent"):
        require(event.get(key) is True,"R33_EVIDENCE_MISSING_"+key)
    for key in ("dispatchAuthorized","weaponSwitchAuthorized",
                "alternativeAPRVerified","launcherAmmoPairVerified",
                "completeActiveEffectsVerified","manualEpsQueueVerified",
                "actionOriginVerified"):
        require(event.get(key) is False,"R33_UNSAFE_PROMOTION_"+key)
    require(event.get("ordersSent")==0 and event.get("localsWritten")==0
            and event.get("r4Status")==R4_STATUS,
            "R33_R4_OR_MUTATION_MISMATCH")
    stats=event.get("selectedStatsRaw")
    require(type(stats) is dict,"R33_SELECTED_STATS_MISSING")
    ranges={"m_nNumberOfAttacks":(0,10),"m_nTHAC0":(-100,100),
            "m_nSTR":(0,25),"m_nSTRExtra":(0,100),
            "m_bImprovedHaste":(0,1),"m_nHitBonus":(-100,100)}
    require(all(exact_int(stats.get(k),*ranges[k]) for k in FIELDS),
            "R33_STATS_UNREADABLE")
    require(stats["m_nNumberOfAttacks"]==event["selectedAprKeyRaw"],
            "R33_APR_SOURCE_DISAGREES")
    levels=event.get("levelsAndKitRaw")
    require(type(levels) is dict and
            all(exact_int(levels.get(k),0,4294967295 if k=="kitRaw" else 50)
                for k in LEVELS),"R33_LEVELS_KIT_UNREADABLE")
    proficiency=event.get("proficiencyStat89to134Raw")
    require(type(proficiency) is list and len(proficiency)==46 and
            all(exact_int(v,-2147483648,2147483647) for v in proficiency),
            "R33_WPROF_INCOMPLETE")
    require(event.get("queueSnapshotStable") is True and
            exact_int(event.get("queuedActionsRaw"),0,512),
            "R33_QUEUE_RAW_UNSTABLE")
    # The origin pointer was not readable in the real R33 log.
    # A classified action-source string must not silently become authorization.
    require(event.get("actionSourceSemantics")=="UNCLASSIFIED_CAI_ACTION_M_SOURCE",
            "R33_ACTION_SOURCE_SEMANTICS_CHANGED")
    return {
        "actor":event["actor"],"party":event["partyIndex"],
        "selected":event["selectedWeaponRaw"],
        "ability":event["selectedAbilityRaw"],"action":event["actionRaw"],
        "stats":tuple(stats[k] for k in FIELDS),
        "levels":tuple(levels[k] for k in LEVELS),
        "pipsRaw":tuple(proficiency),
        "gear":(
            _slots(event,"quickWeaponsRaw",(35,36,37,38)),
            _slots(event,"quiversRaw",(11,12,13,14)),
            _slots(event,"offhandRaw",(9,)),
        ),
        "queue":event["queuedActionsRaw"],
        "actionSourceStable":event.get("actionSourceStable") is True,
        "actionSourceRaw":event.get("actionSourceRaw"),
        "actionSourceStatus":event.get("actionSourceReadStatus"),
        "sourceUnknown":event.get("actionSourceStable") is not True,
        "actionContextStable":event.get("actionContextSnapshotStable") is True,
    }


def analyze_events(events):
    try:
        require(type(events) is list and 2<=len(events)<=MAX_EVENTS,
                "R33_EVENTS_COUNT_OUT_OF_RANGE")
        parsed=[]
        actor=None
        for i,event in enumerate(events,1):
            p=_event(event,i,actor)
            if actor is None:
                actor=p["actor"]
            parsed.append(p)
        changes=[]
        counts={"RAW_CONTEXT_EQUAL_BUT_NOT_EFFECT_PROOF":0,
                "AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE":0,
                "STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE":0,
                "NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE":0,
                "ACTION_CONTEXT_CHANGED_KEEP_ACTION":0}
        for prev,cur in zip(parsed,parsed[1:]):
            pair=len(changes)+2
            changed=[]
            for a,b in zip(prev["gear"],cur["gear"]):
                for old,new in zip(a,b):
                    if old!=new:
                        changed.append({"slot":old[0],
                            "beforeResrefRaw":old[1],"afterResrefRaw":new[1],
                            "beforeUseCount1Raw":old[2],
                            "afterUseCount1Raw":new[2]})
            if prev["selected"]!=cur["selected"] or prev["ability"]!=cur["ability"]:
                status="NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE"
            elif changed:
                status="AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE"
            elif (prev["stats"]!=cur["stats"] or
                  prev["levels"]!=cur["levels"] or
                  prev["pipsRaw"]!=cur["pipsRaw"]):
                status="STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE"
            elif (prev["action"]!=cur["action"] or prev["queue"]!=cur["queue"]
                  or prev["actionSourceRaw"]!=cur["actionSourceRaw"]
                  or prev["actionSourceStatus"]!=cur["actionSourceStatus"]
                  or prev["actionContextStable"]!=cur["actionContextStable"]):
                status="ACTION_CONTEXT_CHANGED_KEEP_ACTION"
            else:
                status="RAW_CONTEXT_EQUAL_BUT_NOT_EFFECT_PROOF"
            counts[status]+=1
            changes.append({
                "fromSequence":pair-1,"toSequence":pair,
                "status":status,
                "invalidateCachedRankingOnly":status!="RAW_CONTEXT_EQUAL_BUT_NOT_EFFECT_PROOF",
                "observedEquipmentDeltas":changed,
                "selectedAprRawBefore":prev["stats"][0],
                "selectedAprRawAfter":cur["stats"][0],
                "selectedTHAC0RawBefore":prev["stats"][1],
                "selectedTHAC0RawAfter":cur["stats"][1],
                "manualEpsOriginStillUnknown":True,
                "neverInterruptCurrentAction":True,
            })
        return safe("R36_HISTORICAL_RAW_CONTEXT_CONSISTENCY_PASS_NO_SWITCH",
                    recordedEvents=len(parsed),actorCount=1,
                    consecutiveComparisons=len(changes),
                    classifications=counts,comparisons=changes,
                    allSameActor=True,
                    activeEffectFingerprintAvailable=False,
                    r33ActionSourceProven=False)
    except (Hold,KeyError,TypeError,ValueError,OverflowError) as exc:
        return safe("R36_HOLD",reason=str(exc) if isinstance(exc,Hold)
                    else "R33_INPUT_STRUCTURE_UNEXPECTED")


def parse_real_r33_log(raw):
    """Strict exact SHA authenticates the *whole* known historical log."""
    require(type(raw) is bytes and len(raw)<=MAX_FILE_BYTES,"LOG_SIZE_UNSAFE")
    require(hashlib.sha256(raw).hexdigest()==R33_SHA,
            "R33_HISTORICAL_LOG_SHA_MISMATCH")
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeError:
        raise Hold("R33_LOG_NOT_UTF8")
    prefix='[BGXR27] '
    events=[]
    sessions=0
    for line in text.splitlines():
        if prefix not in line:
            continue
        candidate=line.split(prefix,1)[1]
        try:
            obj=json.loads(candidate)
        except (ValueError,TypeError):
            raise Hold("R33_JSON_INVALID")
        if type(obj) is not dict or obj.get("schema")!=R33_SCHEMA:
            continue
        if obj.get("type")=="SESSION":
            sessions+=1
        elif obj.get("type")=="R27_SINGLE_CALLBACK":
            events.append(obj)
    require(sessions==1,"R33_SESSION_COUNT_NOT_ONE")
    return events


def main():
    ap=argparse.ArgumentParser(description="Offline R33 raw-context invalidation audit, no game modifications")
    ap.add_argument("--known-r33-log",type=Path,required=True)
    args=ap.parse_args()
    try:
        data=args.known_r33_log.read_bytes()
        result=analyze_events(parse_real_r33_log(data))
    except (Hold,OSError) as exc:
        result=safe("R36_HOLD",reason=str(exc) if isinstance(exc,Hold)
                    else "INPUT_READ_FAILED")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["status"].startswith("R36_HISTORICAL_") else 2


if __name__=="__main__":
    sys.exit(main())
