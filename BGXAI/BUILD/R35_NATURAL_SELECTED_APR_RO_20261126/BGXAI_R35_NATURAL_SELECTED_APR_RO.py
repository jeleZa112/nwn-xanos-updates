#!/usr/bin/env python3
"""BGXAI R35: historical natural-selected APR witness; pure offline analysis.

Joins two separately received REAL user reports (R28 native/R27 observed and
R34 current ITM/historical R33 profile). Does NOT estimate alternative-slot APR,
infer a current equipped item, bind ammo to launcher, or send game commands.
No private actor ID, file paths, log text, EEex listener, game writes or installs.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

SCHEMA="BGXAI_R35_R27_R34_NATURAL_SELECTED_APR_WITNESS_RO_V1"
R27_SHA="6124a7d4d1fd3e168bc7fa099397964fb2e0bc4d5d0fa840c79c005647bf223b"
R33_LOG_SHA="d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538"
R28_SCHEMA="BGXAI_R28_NATIVE_FROM_R27_RO_V1"
R34_SCHEMA="BGXAI_R34_R33_NATIVE_ITM_PROF_JOIN_RO_V1"
# EE engine m_nNumberOfAttacks raw encoding; inherited from R33 verified decoder.
APR_KEY={0:0,1:1,2:2,3:3,4:4,5:5,6:0.5,7:1.5,8:2.5,9:3.5,10:4.5}
RESREF={"AROW01","BOW05","STAF01","SW1H04"}
class Hold(ValueError):
    pass

def require(ok,why):
    if not ok: raise Hold(why)

def int_exact(x,low,high):
    return type(x) is int and low<=x<=high

def side_effect_free(status,**extra):
    result={"schema":SCHEMA,"status":status,"readOnly":True,
            "gameModified":False,"ordersSent":0,"localsWritten":0,
            "dispatchAuthorized":False,"weaponSwitchAuthorized":False,
            "otherSlotEffectiveAPRVerified":False,"perSlotTHAC0Verified":False,
            "sameBuffContextVerified":False,"manualAndEPSOriginVerified":False,
            "ammoLauncherEngineBindingVerified":False,
            "targetEffectivenessVerified":False,"activeClassAndKitVerified":False,
            "gameplayPriorityExecutable":False}
    result.update(extra)
    return result

def witness(r28,r34):
    """Strict source-bound output, never current actor/weapon authorization."""
    try:
        require(type(r28) is dict and r28.get("schema")==R28_SCHEMA and
                r28.get("status")=="R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW",
                "R28_SCHEMA_OR_STATUS")
        require(type(r34) is dict and r34.get("schema")==R34_SCHEMA and
                r34.get("status")=="HISTORICAL_R33_PROFILE_CURRENT_ITM_JOINED_RO_NO_SWITCH",
                "R34_SCHEMA_OR_STATUS")
        for src in (r28,r34):
            require(src.get("gameModified") is False and
                    src.get("dispatchAuthorized") is False and
                    src.get("weaponSwitchAuthorized") is False,
                    "SOURCE_MAY_HAVE_MODIFIED_GAME")
            if "ordersSent" in src:
                require(src["ordersSent"]==0,"ORDERS_SENT_NOT_ZERO")
        require(r34.get("readOnly") is True and r34.get("liveGamePinVerified") is True
                and r34.get("historicalProfileOnly") is True
                and r34.get("sessionTemporalAlignmentVerified") is False
                and r34.get("sameBytesAsUserUploadedLogVerified") is False
                and r34.get("nativeResourceCount")==5
                and r34.get("r33EventCount")==8
                and r34.get("historicalReferenceLogSha256")==R33_LOG_SHA,
                "R34_HISTORICAL_AND_NATIVE_PROVENANCE_NOT_MATCHED")
        live=r28.get("liveR27Evidence")
        require(type(live) is dict and live.get("sourceSha256")==R27_SHA
                and r28.get("captureSha256")==R27_SHA
                and live.get("r27SessionMarkers")==1
                and live.get("r27ConfirmedCallbacks")==24
                and live.get("actorCount")==1,"R27_ARCHIVED_CAPTURE_UNVERIFIED")
        native=r28.get("nativeAudit")
        require(type(native) is dict and native.get("schema")=="BGXAI_WEAPON_NATIVE_ITM_R3_READONLY"
                and native.get("status")=="ITM_NATIVE_ALL_ITEMS_RAW_READ"
                and native.get("sourceKind")=="CURRENT_GAME", "R28_NATIVE_UNVERIFIED")
        old=native.get("items")
        new=r34.get("resourceItems")
        require(type(old) is dict and RESREF.issubset(old.keys())
                and type(new) is list and len(new)==5
                and len({row.get("resref") for row in new if type(row) is dict})==5,
                "ITM_RESOURCE_SET_INCOMPLETE")
        mapped={row["resref"]:row for row in new}
        require(set(mapped)==RESREF|{"SHLD03A"},"R34_EXPECTED_RESOURCES_DIFFER")
        for ref in RESREF:
            item=old[ref]
            row=mapped[ref]
            require(type(item) is dict and type(row) is dict and
                    type(item.get("item")) is dict and
                    type(item.get("provenance")) is dict
                    and item["provenance"].get("sha256")==row.get("resourceSha256")
                    and item["item"].get("proficiencyIdRaw")==row.get("proficiencyStatIdRaw")
                    and item["provenance"].get("origin")==row.get("sourceOrigin"),
                    "R28_R34_NATIVE_ITEM_CHANGED_OR_UNVERIFIED_"+ref)
        require(mapped["BOW05"]["proficiencyStatIdRaw"]==105
                and mapped["SW1H04"]["proficiencyStatIdRaw"]==90
                and mapped["STAF01"]["proficiencyStatIdRaw"]==102
                and mapped["BOW05"]["proficiencyLowThreeBitsObserved"]==0
                and mapped["SW1H04"]["proficiencyLowThreeBitsObserved"]==2
                and mapped["STAF01"]["proficiencyLowThreeBitsObserved"]==0,
                "HISTORICAL_PROF_MAPPING_DRIFT")
        samples=live.get("samplesSelectedOnly")
        require(type(samples) is list and len(samples)==24,
                "NATURAL_SELECTED_SAMPLES_COUNT")
        actor=None
        keys={12:[],35:[]}
        for number,event in enumerate(samples,1):
            require(type(event) is dict and event.get("sequence")==number
                    and int_exact(event.get("actorRaw"),1,2147483647)
                    and int_exact(event.get("actionRaw"),0,65535)
                    and event.get("selectedAbilityRaw")==0
                    and event.get("selectedSlotRaw") in (12,35)
                    and type(event.get("selectedAprKeyRaw")) is int
                    and event["selectedAprKeyRaw"] in APR_KEY,
                    "R27_SELECTED_EVENT_SHAPE_OR_ORDER")
            if actor is None: actor=event["actorRaw"]
            require(event["actorRaw"]==actor,"R27_ACTOR_CHANGED")
            keys[event["selectedSlotRaw"]].append(event["selectedAprKeyRaw"])
        require(len(keys[12])>0 and len(keys[35])>0,
                "BOTH_NATURALLY_SELECTED_SLOTS_NOT_OBSERVED")
        group=[]
        for slot,ref in ((12,"AROW01"),(35,"SW1H04")):
            counts={}
            for k in keys[slot]:counts[k]=counts.get(k,0)+1
            group.append({"selectedSlotRaw":slot,"rawItemResRefFromHistoricLoadout":ref,
                          "eventCount":len(keys[slot]),
                          "observedSelectedApr":[
                            {"engineAprKeyRaw":k,"aprIfStandardDecoder":APR_KEY[k],
                             "observations":counts[k]} for k in sorted(counts)],
                          "isCurrentLiveSlotAPR":False,"canApplyToOtherSlot":False,
                          "activeEffectsAndTargetMatched":False})
        return side_effect_free(
            "R35_HISTORIC_TWO_NATURALLY_SELECTED_APR_WITNESSES_NO_SWITCH",
            r27ArchivedCaptureSha256=R27_SHA,
            r33HistoricalReferenceSha256=R33_LOG_SHA,
            currentItemResourcesRead=5,currentNativeITMShaMatchCount=4,
            actualR27SelectedEvents=24,
            observationsBySelectedSlot=group,
            selectedSlot12IsAmmoNotLauncher=True,
            bowLauncherBoundToAmmoVerified=False,
            historicalLongSwordPips=2,historicalShortBowPips=0,
            note="APR readings belong to naturally selected slots in a PRIOR combat session. They are not simultaneous alternative-slot effective APR; slot 12 is ammunition, not authenticated launcher BOW05. No THAC0 in R28 selected summary.",
            requiredNextEvidence=[
                "AUDITED_PASSIVE_SAME_CONTEXT_SELECTED_STATS",
                "LAUNCHER_AMMO_SLOT_BINDING",
                "ACTIVE_BUFFS_EFFECTS_CLASS_KIT",
                "FINAL_OTHER_SLOT_APR_THAC0",
                "MANUAL_EPS_ACTION_OWNERSHIP_AND_SAFE_BOUNDARY"])
    except (Hold,KeyError,TypeError,ValueError) as exc:
        reason=str(exc) if isinstance(exc,Hold) else "SOURCE_STRUCTURE_INVALID"
        return side_effect_free("R35_HOLD",reason=reason[:128])

def main():
    p=argparse.ArgumentParser(description="Offline historic R27/R34 join; no writes")
    p.add_argument("--r28",type=Path,required=True)
    p.add_argument("--r34",type=Path,required=True)
    args=p.parse_args()
    try:
        r28=json.loads(args.r28.read_text(encoding="utf-8-sig"))
        r34=json.loads(args.r34.read_text(encoding="utf-8-sig"))
        out=witness(r28,r34)
    except (OSError,ValueError,UnicodeError) as exc:
        out=side_effect_free("R35_HOLD",reason="INPUT_FILE_UNREADABLE")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["status"].startswith("R35_HISTORIC_") else 2

if __name__=="__main__":
    sys.exit(main())
