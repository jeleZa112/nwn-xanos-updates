#!/usr/bin/env python3
"""BGXAI R48 SOURCE ONLY: first real, bounded STAF01 backpack -> weapon pilot.

NOT another diagnostic. Reuse ALREADY-WRITTEN, REAL USER NATIVE-COMPILED R39
single XEquipItem action and its in-engine idle / no combat / safe actor
conditions. Replace ONLY the unpublished R39 ARM and EEex-session handshake
with a new one-shot actor LOCALS flag, because this is an explicitly user
typed, one-item, disposable-save deployment. R47 remains installed beneath
the future #159 extension. This composer NEVER touches the user's EET.

The first live game trial, after separately approved guarded install, is the
one missing proof; no R47 [BGXBEX] proof is prerequisite.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/"R39_STAGED_XEQUIP_SOURCEONLY_20261127/BGXAI_R39_JAGAN_STAF01_EEEX_SESSION_SOURCE_ONLY.baf"
OLD_BLOB="3d2816b2ba459b1d212f79bce74d925033691303"
OLD_BYTES=2407
OLD_SHA="6d39e72684548c7b1b900e80f1bdb4271044e9889364db958f52b0532d1b73f0"
SCHEMA="BGXAI_R48_SINGLE_REAL_STAF01_ACTION_SOURCE_ONLY_V1"
ONCE="BGX48TRY"
class Hold(ValueError):
    pass
def sha(x:bytes)->str:
    return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def verified_prior()->bytes:
    if OLD.is_symlink() or not OLD.is_file():
        raise Hold("HOLD_ORIGINAL_NATIVE_R39_BAF_MISSING")
    original=OLD.read_bytes()
    if len(original)!=OLD_BYTES or sha(original)!=OLD_SHA or blob(original)!=OLD_BLOB:
        raise Hold("HOLD_ORIGINAL_REAL_NATIVE_R39_BAF_DRIFT")
    if original.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')!=1:
        raise Hold("HOLD_ORIGINAL_R39_REAL_EQUIP_ACTION_NOT_UNIQUE")
    return original

REMOVED_CONDITIONS=(
 b'  Global("BGXW3ARM","LOCALS",1)\n',
 b'  Global("BGXW3TAG","LOCALS",2110908191)\n',
 b'  Global("BGXW3TRY","LOCALS",0)\n',
 b'  Global("BGXW3QST","LOCALS",1)\n',
 b'  EEex_LuaTrigger("return BGXW3_EEexSessionGate()")\n',
 b'  GlobalTimerExpired("BGXW3QTM","LOCALS")\n',
 b'  GlobalTimerNotExpired("BGXW3MAX","LOCALS")\n',
)
REMOVED_ACTIONS=(
 b'    SetGlobal("BGXW3ARM","LOCALS",2)\n',
 b'    SetGlobal("BGXW3TRY","LOCALS",1)\n',
 b'    SetGlobal("BGXW3TAG","LOCALS",0)\n',
 b'    SetGlobal("BGXW3QST","LOCALS",2)\n',
)
PRESERVED_TRIGGERS=(
 b'InParty(Myself)',b'InPartySlot(Myself,1)',b'Name("*GCLERIC",Myself)',
 b'Class(Myself,CLERIC)',b'CheckStatGT(Myself,4,STR)',
 b'!HasItemSlot(Myself,SLOT_SHIELD)',b'ActionListEmpty()',
 b'CombatCounter(0)',b'!See([EVILCUTOFF])',
 b'!GlobalTimerNotExpired("MO_SpellCast","LOCALS")',
 b'ModalState(NONE)',b'!StateCheck(Myself,STATE_PANIC)',
 b'!StateCheck(Myself,STATE_HELPLESS)',
 b'CheckItemSlot(Myself,"STAF01",SLOT_MISC5)',
 b'!HasItemSlot(Myself,SLOT_WEAPON0)',
)

def compose()->bytes:
    orig=verified_prior()
    blocks=re.findall(rb"(?ms)^IF\n.*?^END(?:\r?\n|$)",orig)
    if len(blocks)!=3:
        raise Hold("HOLD_R39_ORIGINAL_BAF_EXPECTED_THREE_BLOCKS")
    middle=blocks[1]
    if middle.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')!=1:
        raise Hold("HOLD_R39_EQUIP_BLOCK_NOT_EXACTLY_MIDDLE")
    for needle in (*REMOVED_CONDITIONS,*REMOVED_ACTIONS):
        if middle.count(needle)!=1:
            raise Hold("HOLD_R48_SESSION_ARM_ANCHOR_NOT_EXACT")
        middle=middle.replace(needle,b"",1)
    if middle.count(b"IF\n")!=1 or middle.count(b"THEN\n")!=1 or middle.count(b"END\n")!=1:
        raise Hold("HOLD_R48_BAF_SHAPE")
    middle=middle.replace(b"IF\n",
       b'IF\n  Global("BGX48TRY","LOCALS",0)\n',1)
    middle=middle.replace(b"  RESPONSE #100\n",
       b'  RESPONSE #100\n    SetGlobal("BGX48TRY","LOCALS",1)\n',1)
    for condition in PRESERVED_TRIGGERS:
        if middle.count(condition)!=1:
            raise Hold("HOLD_R48_NATIVE_R39_SAFETY_TRIGGER_REMOVED")
    if (middle.count(b'Global("BGX48TRY","LOCALS",0)')!=1 or
        middle.count(b'SetGlobal("BGX48TRY","LOCALS",1)')!=1 or
        middle.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')!=1):
        raise Hold("HOLD_R48_ONCE_ACTION_CONTRACT")
    for token in (b"BGXW3",b"EEex_LuaTrigger(",b"GlobalTimerExpired(",
                  b"GlobalTimerNotExpired(\"BGXW3"):
        if token in middle:
            raise Hold("HOLD_R48_UNVERIFIED_OLD_ARM_LEFT")
    if middle.count(b"SetGlobal(")!=1 or middle.count(b"XEquipItem(")!=1:
        raise Hold("HOLD_R48_ACTION_NOT_BOUND_TO_ONE_ATTEMPT")
    if b"SelectWeaponAbility(" in middle or b"Attack(" in middle:
        raise Hold("HOLD_R48_MAY_INTERRUPT_ATTACK")
    # Pure single block; install only by independent last-only WeiDU guard.
    return (b"// BGXAI R48 ONE gameplay action only, user-typed install needed.\n"
            b"// Restricted to Jagan *GCLERIC with the EXACT original R39\n"
            b"// off-combat, empty-action-list, STAF01 MISC5->WEAPON0 preconditions.\n"
            b"// BGX48TRY prevents repeats in this save; no second action listener.\n"
            +middle)

def main():
    raw=compose()
    print(json.dumps({"schema":SCHEMA,"status":"R48_REAL_EQUIP_BAF_SOURCE_ONLY_NO_DEPLOY",
      "sourceR39UserNativeCompiledPreviously":True,
      "newOneItemBafBytes":len(raw),"newOneItemBafSHA256":sha(raw),
      "actualMoveCandidate":"STAF01 BACKPACK SLOT20 TO SLOT35 (WEAPON0)",
      "oneShotLocalFlag":ONCE,"oneAttemptPerSave":True,
      "idleActionListRequired":True,"noCombatRequired":True,
      "oldR47PassiveBSCPreservedForFutureLast159":True,
      "autoInstall":False,"gameModified":False,"installed":False,
      "XEquipItemActuallyExecuted":False,"ordersSent":0},indent=2))
if __name__=="__main__":
    main()
