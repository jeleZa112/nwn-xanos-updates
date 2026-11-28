#!/usr/bin/env python3
"""BGXAI R49 source-only repair for proven R48 exact backpack slot mismatch.

User's GAM shows Jagan's unique STAF01 in runtime slot22, while old R48
only tests SLOT_MISC5=20. Keep all other existing R48 trigger/one-shot
safeguards; replace the ONE exact slot test with sixteen bounded checks.
NO GAME writes, WeiDU installation, new update CMD, arming, or orders.
Published SOURCE CANDIDATE only; native compile and separate user approval
would be required for any future gameplay deployment.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/"R48_ONE_REAL_STAF01_EQUIP_AFTER_R47_20261128/BGXAI_R48_REUSE_R39_ONE_SHOT_BAF_SOURCE_ONLY.py"
OLD_BLOB="87049cafc4108c607fffd5b907a7557149bcdfd8"
SCHEMA="BGXAI_R49_REUSE_R48_ANY_BACKPACK16_ONE_SHOT_SOURCE_ONLY_V1"
OLD_TRIGGER=b'  CheckItemSlot(Myself,"STAF01",SLOT_MISC5)\n'
CONDITION=b'  OR(16)\n'+b''.join(
    b'    CheckItemSlot(Myself,"STAF01",SLOT_MISC%d)\n'%n
    for n in range(3,19)
)
ONCE=b'Global("BGX48TRY","LOCALS",0)'
ONCE_ACTION=b'SetGlobal("BGX48TRY","LOCALS",1)'
EQUIP=b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'
GUARDS=(
    b'InParty(Myself)',b'InPartySlot(Myself,1)',
    b'Name("*GCLERIC",Myself)',b'Class(Myself,CLERIC)',
    b'CheckStatGT(Myself,4,STR)',b'!HasItemSlot(Myself,SLOT_SHIELD)',
    b'ActionListEmpty()',b'CombatCounter(0)',b'!See([EVILCUTOFF])',
    b'!GlobalTimerNotExpired("MO_SpellCast","LOCALS")',
    b'ModalState(NONE)',b'!StateCheck(Myself,STATE_PANIC)',
    b'!StateCheck(Myself,STATE_HELPLESS)',
    b'!HasItemSlot(Myself,SLOT_WEAPON0)',ONCE,ONCE_ACTION,EQUIP,
)
class Hold(ValueError):
    pass

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def compose()->bytes:
    if OLD.is_symlink() or not OLD.is_file() or blob(OLD.read_bytes())!=OLD_BLOB:
        raise Hold("HOLD_R49_ORIGINAL_R48_COMPOSER_BLOB_DRIFT")
    spec=importlib.util.spec_from_file_location("bgxai_old_r48_unmodified",OLD)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R49_ORIGINAL_R48_IMPORT")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.SCHEMA!="BGXAI_R48_SINGLE_REAL_STAF01_ACTION_SOURCE_ONLY_V1":
        raise Hold("HOLD_R49_ORIGINAL_R48_CONTRACT")
    original=mod.compose()  # original in turn validates earlier R39 SHA and blob
    if original.count(OLD_TRIGGER)!=1 or original.count(EQUIP)!=1:
        raise Hold("HOLD_R49_EXACT_ORIGINAL_MIDDLE_TRIGGER")
    if b'OR(16)' in original or original.count(b'IF\n')!=1:
        raise Hold("HOLD_R49_ORIGINAL_BAF_SHAPE")
    candidate=original.replace(OLD_TRIGGER,CONDITION,1)
    # The exact byte diff is ONLY the original rigid item slot trigger.
    if candidate.replace(CONDITION,OLD_TRIGGER,1)!=original:
        raise Hold("HOLD_R49_NOT_AN_EXACT_ONE_TRIGGER_REPLACEMENT")
    if candidate.count(b'OR(16)')!=1 or candidate.count(b'CheckItemSlot(')!=16:
        raise Hold("HOLD_R49_BACKPACK16_CHECKS_NOT_EXACT")
    for n in range(3,19):
        if candidate.count(
          b'CheckItemSlot(Myself,"STAF01",SLOT_MISC%d)'%n)!=1:
            raise Hold("HOLD_R49_BACKPACK_SLOT_MISSING_OR_DUPLICATED")
    for guard in GUARDS:
        if candidate.count(guard)!=1:
            raise Hold("HOLD_R49_ORIGINAL_ACTOR_OR_IDLE_GUARD_LOST")
    for forbidden in (b'ClearActions(',b'Attack(',b'SelectWeaponAbility(',
                      b'EEex_LuaTrigger(',b'BGXW3ARM',b'ActionOverride('):
        if forbidden in candidate:
            raise Hold("HOLD_R49_FORBIDDEN_OLD_OR_UNSAFE_ACTION")
    if candidate.count(b'SetGlobal(')!=1 or candidate.count(b'XEquipItem(')!=1:
        raise Hold("HOLD_R49_NOT_EXACT_ONE_ONESHOT_ACTION")
    return candidate

def main()->None:
    baf=compose()
    print(json.dumps({
       "schema":SCHEMA,
       "status":"R49_BACKPACK16_BAF_CANDIDATE_SOURCE_ONLY_NO_INSTALL",
       "baseR48GitBlob":OLD_BLOB,
       "change":"R48 exact SLOT_MISC5 -> OR16 SLOT_MISC3..SLOT_MISC18",
       "oldR48NameGuardPreserved":True,
       "oldR48ClassAndIdleGuardsPreserved":True,
       "oneShotLocalBGX48TRYPreserved":True,
       "oneRealXEquipActionInSource":True,
       "nativeCompilerPassed":False,
       "r49Installed":False,
       "gameModified":False,
       "ordersSent":0,
       "newBafBytes":len(baf),
       "newBafSHA256":hashlib.sha256(baf).hexdigest(),
       "needsExactLiveSourceAndSafeInstallPreflight":True,
       "userTypedConsentBeforeGameplay":True
    },indent=2))
if __name__=="__main__":
    main()
