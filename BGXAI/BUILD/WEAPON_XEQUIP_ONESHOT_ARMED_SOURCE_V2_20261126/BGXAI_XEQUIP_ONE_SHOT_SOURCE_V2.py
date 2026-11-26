#!/usr/bin/env python3
"""Generate SOURCE-ONLY one-shot script for controlled EET backpack→empty weapon slot pilot.

This is NOT an installer, does NOT invoke WeiDU, does NOT arm any game Global.
The generated BAF can act ONLY when a separate GLOBAL token is explicitly set to 1.
Deployment requires a separate approved guarded WeiDU candidate, real inventory
evidence, disposable save, noncombat setup, and exact typed user authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys

SCHEMA="BGXAI_XEQUIP_ONE_SHOT_SOURCE_V2"
ARM="BGXW2ARM"
ATTEMPT="BGXW2TRY"
ALLOWED={"schema","actorId","partyIndex","sourceSlot","targetSlot",
         "resref","weaponSlotCapacity","sourceSnapshotSha256","snapshotSession"}
class Hold(ValueError): pass
def integ(v,lo,hi):
    return type(v) is int and lo<=v<=hi
def check(data):
    if type(data) is not dict or set(data)!=ALLOWED or data.get("schema")!=SCHEMA:
        raise Hold("HOLD_SCHEMA_OR_FIELDS")
    if not integ(data["actorId"],1,2147483647) or not integ(data["partyIndex"],1,5):
        raise Hold("HOLD_ACTOR_OR_NPC_PARTY_INDEX")
    src,dst,cap=data["sourceSlot"],data["targetSlot"],data["weaponSlotCapacity"]
    if not integ(src,18,33):raise Hold("HOLD_TRUE_BACKPACK_18_TO_33")
    if not integ(cap,2,4) or not integ(dst,35,34+cap):
        raise Hold("HOLD_INVALID_OR_NOT_USABLE_WEAPON_QUICKSLOT")
    rr=data["resref"]
    if type(rr) is not str or not re.fullmatch(r"[A-Z0-9_]{1,8}",rr):
        raise Hold("HOLD_RESREF_NOT_EXACT_UPPERCASE")
    if type(data["sourceSnapshotSha256"]) is not str or not re.fullmatch(
        r"[0-9a-f]{64}",data["sourceSnapshotSha256"]):
        raise Hold("HOLD_MISSING_VERIFIABLE_SNAPSHOT_DIGEST")
    session=data["snapshotSession"]
    if type(session) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}",session):
        raise Hold("HOLD_MISSING_SNAPSHOT_SESSION")
    # This only checks representation, NOT the snapshot's actual origin,
    # source occupancy, uniqueness, empty destination, timing, or approval.
    return data
def render(data):
    d=check(data)
    src=f"SLOT_MISC{d['sourceSlot']-15}"
    dst=f"SLOT_WEAPON{d['targetSlot']-35}"
    script=f"""// BGXAI V2: ARMABLE SOURCE ONLY. NOT INSTALLED / NEVER AUTO-ARM.
 // Synthetic source data or a valid hash alone are NOT game evidence.
 // Requires separate GLOBAL {ARM}=1; never sets it to 1.
IF
  Global("{ARM}","GLOBAL",1)
  Global("{ATTEMPT}","LOCALS",0)
  InParty(Myself)
  InPartySlot(Myself,{d['partyIndex']})
  ActionListEmpty()
  CombatCounter(0)
  !GlobalTimerNotExpired("MO_SpellCast","LOCALS")
  ModalState(NONE)
  !StateCheck(Myself,STATE_PANIC)
  !StateCheck(Myself,STATE_HELPLESS)
  CheckItemSlot(Myself,"{d['resref']}",{src})
  !HasItemSlot(Myself,{dst})
THEN
  RESPONSE #100
    SetGlobal("{ARM}","GLOBAL",2)
    SetGlobal("{ATTEMPT}","LOCALS",1)
    XEquipItem("{d['resref']}",Myself,{dst},EQUIP)
END
"""
    if script.count("IF\n")!=1 or script.count("THEN\n")!=1 or script.count("END\n")!=1:
        raise Hold("HOLD_BAD_STRUCTURE")
    if (script.count('SetGlobal("'+ARM+'","GLOBAL",2)')!=1 or
        script.count('Global("'+ARM+'","GLOBAL",1)')!=1 or
        script.count('SetGlobal("'+ATTEMPT+'","LOCALS",1)')!=1 or
        script.count("XEquipItem(")!=1 or
        "  False()\n" in script):
        raise Hold("HOLD_ONE_SHOT_ARM_CONTRACT")
    for forbidden in ("ClearActions(","Stop(","FillSlot(","CreateItem(",
                      "MoveToObject(","Attack(","SelectWeaponAbility(",
                      "SetGlobal(\""+ARM+"\",\"GLOBAL\",1)"):
        if forbidden in script:raise Hold("HOLD_UNSAFE_ACTION_IN_SOURCE")
    return script
def audit(data):
    text=render(data)
    return {"schema":"BGXAI_XEQUIP_ONE_SHOT_BUILD_AUDIT_V2",
      "status":"ARMABLE_BAF_SOURCE_NOT_INSTALLED_NOT_AUTHORIZED",
      "sourceBafSha256":hashlib.sha256(text.encode("ascii")).hexdigest(),
      "sourceBafBytes":len(text.encode("ascii")),
      "sourceSlot":data["sourceSlot"],"targetSlot":data["targetSlot"],
      "itemResref":data["resref"],"actorId":data["actorId"],
      "snapshotClaimSha256":data["sourceSnapshotSha256"],
      "inputSnapshotProvenanceAuthenticated":False,
      "gameItemInstanceVerified":False,"gameInventoryUniqueVerified":False,
      "gameTargetSlotEmptyVerified":False,
      "sameActionBoundaryVerified":False,
      "manualEpsOriginVerified":False,
      "eetNativeCandidateCompileVerified":False,
      "gameScriptMergeVerified":False,
      "externalBackupVerified":False,
      "userInstallAuthorizationReceived":False,
      "inGamePilotArmed":False,"engineItemMoveVerified":False,
      "itemChargeConservationVerified":False,
      "installed":False,"ordersSent":0,
      "dispatchAuthorized":False,"gameModified":False,
      "oneShotGlobalName":ARM,"attemptLocalName":ATTEMPT}
def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--manifest",required=True)
    o=a.parse_args()
    try:
        with open(o.manifest,"r",encoding="utf-8") as f:
            d=json.load(f)
        print(json.dumps({"audit":audit(d),"baf":render(d)},ensure_ascii=False,indent=2))
        return 0
    except (OSError,TypeError,ValueError,Hold) as e:
        print(json.dumps({"status":"HOLD_ONE_SHOT_SOURCE","reason":str(e),
                          "installed":False,"ordersSent":0,"dispatchAuthorized":False}))
        return 3
if __name__=="__main__":raise SystemExit(main())
