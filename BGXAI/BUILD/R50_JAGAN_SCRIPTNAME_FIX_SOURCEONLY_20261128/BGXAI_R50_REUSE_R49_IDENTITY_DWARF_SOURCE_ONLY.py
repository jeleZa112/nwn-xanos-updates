#!/usr/bin/env python3
"""BGXAI R50 source-only: repair a CONFIRMED false Name() gate on generated PC.

Actual user GAMEV2.0 embedded CRE V1.0, party index1 Jagan:
  GAM 8-char character RESREF = "*GCLERIC" (NOT script name),
  CRE 0x280 Script name/death variable = "None",
  CRE race 0x272=4 (DWARF), class 0x273=3 (CLERIC).
IESDP: Name(S:Name*,O:Object*) checks SCRIPT NAME (CRE death variable).
The old Name("*GCLERIC",Myself) therefore cannot identify this player-created
Jagan. Replace exactly that one incorrect check with Race(Myself,DWARF).
EXISTING R49 already checks InPartySlot(Myself,1) + Class(Myself,CLERIC)
+ all original no-combat/no-action/no-shield guards, STAF01 in any of the 16
backpack slots and same BGX48TRY one-attempt flag. No new listener or action.

This module does not install/rollback anything, touch files or save games.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/"R49_R48_BACKPACK16_SOURCE_ONLY_20261128/BGXAI_R49_REUSE_R48_BACKPACK16_SOURCE_ONLY.py"
OLD_BLOB="7c6ba99e56f98fd72a1f15b18a91a0bb32e69387"
SCHEMA="BGXAI_R50_REUSE_R49_JAGAN_CRE_IDENTITY_ONE_TRIGGER_SOURCE_ONLY_V1"
BAD=b'  Name("*GCLERIC",Myself)\n'
GOOD=b'  Race(Myself,DWARF)\n'
IDENTITY=(b'InParty(Myself)',b'InPartySlot(Myself,1)',
          b'Class(Myself,CLERIC)',b'Race(Myself,DWARF)',
          b'CheckStatGT(Myself,4,STR)')
SAFETY=(
 b'!HasItemSlot(Myself,SLOT_SHIELD)',
 b'ActionListEmpty()',b'CombatCounter(0)',b'!See([EVILCUTOFF])',
 b'!GlobalTimerNotExpired("MO_SpellCast","LOCALS")',b'ModalState(NONE)',
 b'!StateCheck(Myself,STATE_PANIC)',b'!StateCheck(Myself,STATE_HELPLESS)',
 b'!HasItemSlot(Myself,SLOT_WEAPON0)',
 b'Global("BGX48TRY","LOCALS",0)',
 b'SetGlobal("BGX48TRY","LOCALS",1)',
 b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)',
)
class Hold(ValueError):
    pass

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def source():
    if OLD.is_symlink() or not OLD.is_file() or blob(OLD.read_bytes())!=OLD_BLOB:
        raise Hold("HOLD_R50_PRIOR_R49_SOURCE_GIT_BLOB_CHANGED")
    spec=importlib.util.spec_from_file_location("bgxai_original_r49_composer",OLD)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R50_OLD_R49_COMPOSER_IMPORT")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.SCHEMA!="BGXAI_R49_REUSE_R48_ANY_BACKPACK16_ONE_SHOT_SOURCE_ONLY_V1":
        raise Hold("HOLD_R50_OLD_R49_SOURCE_CONTRACT")
    original=mod.compose()
    if original.count(BAD)!=1 or original.count(GOOD)!=0:
        raise Hold("HOLD_R50_EXACT_NAME_CHECK_NOT_UNIQUE")
    return original

def compose()->bytes:
    original=source()
    out=original.replace(BAD,GOOD,1)
    if out.replace(GOOD,BAD,1)!=original:
        raise Hold("HOLD_R50_ONE_TRIGGER_PATCH_REVERSIBILITY")
    if (out.count(b'IF\n')!=1 or out.count(b'THEN\n')!=1 or
        out.count(b'RESPONSE #100')!=1 or out.count(b'END\n')!=1 or
        out.count(b'OR(16)')!=1 or out.count(b'CheckItemSlot(')!=16 or
        out.count(b'XEquipItem(')!=1 or out.count(b'SetGlobal(')!=1 or
        out.count(b'Global("BGX48TRY","LOCALS",0)')!=1):
        raise Hold("HOLD_R50_OLD_R49_SAFETY_OR_SHAPE_CHANGED")
    for token in (*IDENTITY,*SAFETY):
        if out.count(token)!=1:
            raise Hold("HOLD_R50_ORIGINAL_IDENTITY_OR_SAFETY_LOST")
    if b'Name("*GCLERIC",Myself)' in out:
        raise Hold("HOLD_R50_FALSE_NAME_GATE_REMAINED")
    for i in range(3,19):
        if out.count(b'CheckItemSlot(Myself,"STAF01",SLOT_MISC%d)'%i)!=1:
            raise Hold("HOLD_R50_MISSING_BOUNDED_BACKPACK_SLOT")
    for bad in (b'Attack(',b'AttackOneRound(',b'SelectWeaponAbility(',
                b'ClearActions(',b'ForceSpell(',b'EEex_LuaTrigger(',
                b'ActionOverride('):
        if bad in out:raise Hold("HOLD_R50_UNSAFE_ACTION_ADDED")
    if out.index(b'SetGlobal("BGX48TRY","LOCALS",1)') > out.index(
       b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'):
        raise Hold("HOLD_R50_ONESHOT_ORDER")
    return out

def main():
    baf=compose()
    print(json.dumps({
      "schema":SCHEMA,
      "status":"R50_EXACT_FALSE_NAME_GATE_REPAIRED_SOURCE_ONLY",
      "userUploadedSaveCREScriptName":"None",
      "userUploadedSaveGAMCharacterResref":"*GCLERIC",
      "userUploadedSaveRaceId":4,
      "targetGuard":"InPartySlot(Myself,1) and Class(Myself,CLERIC) and Race(Myself,DWARF)",
      "previousR49Backpack16Preserved":True,
      "oldOneShotBGX48TRYPreserved":True,
      "oneXEquipItemActionPreserved":True,
      "sourceBAFSHA256":hashlib.sha256(baf).hexdigest(),
      "sourceBAFBytes":len(baf),
      "nativeWeiDUCompiledOnUserEET":False,
      "installed":False,"gameModified":False,"ordersSent":0
    },indent=2))
if __name__=="__main__":
    main()
