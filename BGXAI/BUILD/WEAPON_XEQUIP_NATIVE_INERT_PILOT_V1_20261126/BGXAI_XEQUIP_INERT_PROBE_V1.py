#!/usr/bin/env python3
"""Generate a strictly inert BG(2)EE XEquipItem WeiDU compile-only BAF.

NO game write, NO installation, NO activation, NO runtime dispatch.
The 'False()' trigger is MANDATORY and unconditional.
"""
from __future__ import annotations
import argparse
import json
import re
import sys

SOURCE_SLOTS = tuple(range(18, 34))
WEAPON_SLOTS = tuple(range(35, 39))
MAX_RESREF = 8
SCHEMA = "BGXAI_XEQUIP_INERT_NATIVE_PROBE_MANIFEST_V1"
STATUS = "NATIVE_COMPILE_PROBE_SOURCE_ONLY_NOT_SAFE_TO_INSTALL"

class Hold(ValueError):
    pass

def strictly_int(value, lo, hi):
    return type(value) is int and lo <= value <= hi

def validate(manifest):
    if type(manifest) is not dict or manifest.get("schema") != SCHEMA:
        raise Hold("HOLD_SCHEMA")
    if set(manifest) != {"schema", "actorId", "partyIndex", "sourceSlot",
                         "targetSlot", "resref", "weaponSlotCapacity"}:
        raise Hold("HOLD_MANIFEST_KEYS")
    if not strictly_int(manifest["actorId"], 1, 2147483647):
        raise Hold("HOLD_ACTOR")
    if not strictly_int(manifest["partyIndex"], 1, 5):
        raise Hold("HOLD_NON_PROTAGONIST_PARTY_SLOT")
    if not strictly_int(manifest["sourceSlot"], 18, 33):
        raise Hold("HOLD_BACKPACK_SLOT_NOT_18_TO_33")
    if not strictly_int(manifest["weaponSlotCapacity"], 2, 4):
        raise Hold("HOLD_WEAPON_CAPACITY")
    if not strictly_int(manifest["targetSlot"], 35, 38) or (
        manifest["targetSlot"] >= 35 + manifest["weaponSlotCapacity"]
    ):
        raise Hold("HOLD_TARGET_NOT_PERMITTED")
    res = manifest["resref"]
    if not isinstance(res, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,8}", res):
        raise Hold("HOLD_INVALID_ITEM_RESREF")
    if res != res.upper():
        raise Hold("HOLD_RESREF_MUST_BE_UPPERCASE")
    return dict(manifest)

def render(manifest):
    m = validate(manifest)
    source = "SLOT_MISC" + str(m["sourceSlot"] - 15)
    target = "SLOT_WEAPON" + str(m["targetSlot"] - 35)
    # Important: even a valid ID and all script guards MUST NEVER execute.
    # Source is only proof that native WeiDU recognizes command and symbols.
    script = f'''// BGXAI XEquipItem INERT source-only WeiDU compile probe.
 // NOT FOR IN-GAME INSTALL. Engine target identity and item instance UNPROVEN.
 // False() is intentionally unconditional and mandatory. NEVER remove here.
IF
  False()
  InParty(Myself)
  InPartySlot(Myself,{m["partyIndex"]})
  Global("BGXWI1GO","LOCALS",1)
  ActionListEmpty()
  CombatCounter(0)
  !GlobalTimerNotExpired("MO_SpellCast","LOCALS")
  ModalState(NONE)
  !StateCheck(Myself,STATE_PANIC)
  !StateCheck(Myself,STATE_HELPLESS)
  CheckItemSlot(Myself,"{m["resref"]}",{source})
  !HasItemSlot(Myself,{target})
THEN
  RESPONSE #100
    SetGlobal("BGXWI1GO","LOCALS",2)
    XEquipItem("{m["resref"]}",Myself,{target},EQUIP)
END
'''
    if script.count("\\n  False()\\n") != 1:
        raise Hold("HOLD_FALSE_GUARD_MISSING")
    if script.count("XEquipItem(") != 1 or script.count("SetGlobal(") != 1:
        raise Hold("HOLD_PROBE_DRIFT")
    return script

def report(manifest):
    baf = render(manifest)
    return {
        "schema": "BGXAI_XEQUIP_INERT_NATIVE_PROBE_RESULT_V1",
        "status": STATUS,
        "baf_source_only": baf,
        "ordersSent": 0,
        "installed": False,
        "dispatchAuthorized": False,
        "weaponSwitchAuthorized": False,
        "inventoryMoveAuthorized": False,
        "realItemIdentityVerified": False,
        "realGameSourceSlotVerified": False,
        "manualEpsOriginVerified": False,
        "safeActionBoundaryVerified": False,
        "nativeWeiDUCompileVerified": False,
        "postTransferConservationVerified": False,
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="JSON file; no game paths")
    args=ap.parse_args(argv)
    try:
        with open(args.manifest, "r", encoding="utf-8") as fh:
            manifest=json.load(fh)
        print(json.dumps(report(manifest), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as err:
        print(json.dumps({"status": "HOLD_INERT_PROBE", "reason": str(err),
                          "installed": False, "ordersSent": 0,
                          "dispatchAuthorized": False}), file=sys.stdout)
        return 3

if __name__=="__main__":
    raise SystemExit(main())
