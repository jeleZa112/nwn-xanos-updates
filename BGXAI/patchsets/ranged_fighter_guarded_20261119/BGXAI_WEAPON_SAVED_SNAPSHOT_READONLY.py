#!/usr/bin/env python3
"""Weapon / ammo slot survey of last saved GAMEV2.0 / CRE V1.0. READ ONLY.

Slot pointers and count are CRE values at 0x2B8/0x2BC/0x2C0 per IESDP.
This intentionally does NOT assert a weapon's type, legality, enchantment,
damage, current APR, THAC0, enemy defenses, command origin or live item state.
It never issues inventory actions and never writes the game or save.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
import BGXAI_SAVE_SCRIPT_AUDIT_READONLY as S

SLOT_TOTAL=40
SLOT_BYTES=80
ITEM_BYTES=20
MAX_ITEMS=2048
WEAPONS=range(9,13)
QUIVERS=range(13,17)
BACKPACK=range(21,37)

def ref(raw:bytes)->str:
    head=raw.split(b"\x00",1)[0].strip()
    if not head or any(x>127 or not (65<=x<=90 or 97<=x<=122 or 48<=x<=57 or x==95) for x in head):
        raise ValueError("INVALID_ITEM_RESREF")
    return head.decode("ascii").upper()

def extract_cre(cre:bytes)->dict:
    if len(cre)<0x2D4 or cre[:8]!=b"CRE V1.0":
        raise ValueError("UNSUPPORTED_CRE")
    slot_off,item_off,count=struct.unpack_from("<III",cre,0x2B8)
    if count>MAX_ITEMS or slot_off<0x2D4 or item_off<0x2D4 or slot_off+SLOT_BYTES>len(cre) or item_off+count*ITEM_BYTES>len(cre):
        raise ValueError("CRE_ITEM_POINTER_BOUNDS")
    if (slot_off<item_off+count*ITEM_BYTES and item_off<slot_off+SLOT_BYTES):
        raise ValueError("CRE_ITEM_SLOT_OVERLAP")
    slot_refs=struct.unpack_from("<40H",cre,slot_off)
    refs=[]
    for i in range(count):
        off=item_off+i*ITEM_BYTES
        refs.append({"resref":ref(cre[off:off+8]),
                     "charges":list(struct.unpack_from("<3H",cre,off+10)),
                     "identified_in_save":bool(struct.unpack_from("<I",cre,off+16)[0]&1)})
    def contents(slot:int)->dict|None:
        index=slot_refs[slot]
        if index==65535:return None
        if index>=count:raise ValueError("CRE_INVALID_ITEM_SLOT_INDEX")
        item=refs[index]
        return {"slot":slot,"item_index":index,"resref":item["resref"],
                "charges":item["charges"],"identified_in_save":item["identified_in_save"]}
    quick=[contents(i) for i in WEAPONS]
    ammo=[contents(i) for i in QUIVERS]
    bag=[v for i in BACKPACK if (v:=contents(i)) is not None]
    selected=slot_refs[38]
    if selected==1000:
        selected_result={"state":"FIST_SELECTED","quickslot_index":None,"resref":None}
    elif selected in range(4):
        slot=selected+9
        selected_result={"state":"SELECTED_QUICKSLOT" if quick[selected] else "EMPTY_SELECTED_QUICKSLOT",
                         "quickslot_index":selected,"resref":quick[selected]["resref"] if quick[selected] else None}
    else:
        selected_result={"state":"SELECTED_SLOT_UNKNOWN","raw_selection":selected,
                         "quickslot_index":None,"resref":None}
    return {"status":"SAVED_CRE_ITEM_SLOTS_READ_ONLY","quickslots":quick,"quiver_slots":ammo,
            "backpack_items":bag,"magic_weapon_slot":contents(37),
            "selected_weapon":selected_result,
            "selected_ability_raw":slot_refs[39],
            "items_table_count":count,"weapon_type_verified":False,
            "inventory_move_performed":False,"live_equipment_verified":False,
            "enchantment_verified":False,"attack_stats_verified":False}

def inspect_gam(data:bytes)->dict:
    saved=S.gam_party(data)
    off,count=struct.unpack_from("<II",data,0x20)
    results=[]
    for i in range(count):
        pos=off+i*S.GAM_NPC_SIZE
        idx=struct.unpack_from("<H",data,pos+2)[0]
        co,cs=struct.unpack_from("<II",data,pos+4)
        base=saved["party"][i]
        if base.get("status")!="SAVED_CRE_SCRIPT_SLOTS_READ":
            results.append({"position":idx,"status":"UNSUPPORTED_OR_INVALID_CRE"})
            continue
        try:
            slot_data=extract_cre(data[co:co+cs])
            results.append({"position":idx,
                            "name_from_saved_record":base["name_from_saved_record"],
                            "cre_sha256":base["cre_sha256"], **slot_data})
        except (struct.error, ValueError) as exc:
            results.append({"position":idx,"status":"CRE_WEAPON_SLOTS_READ_STOP",
                            "reason":str(exc)})
    return {"status":"SAVED_WEAPON_SLOTS_SURVEY","saved_gam_sha256":hashlib.sha256(data).hexdigest(),
            "party":results,"runtime_verified":False,"game_modified":False,
            "item_types_and_combat_performance_verified":False}

def inspect_latest(root:Path)->dict:
    saved=S.latest_saved_party(root)
    if saved.get("status")!="SAVED_GAM_PARTY_READ":
        return {"status":"NO_VALID_SAVED_GAM_WEAPON_SURVEY",
                "underlying_status":saved.get("status"),"game_modified":False}
    path=Path(saved["save_file"])
    if path.is_symlink() or not path.is_file():
        return {"status":"SAVED_GAM_LINK_OR_MISSING_BLOCKED","game_modified":False}
    try:
        if path.stat().st_size>S.GAM_MAX:
            raise ValueError("GAM_TOO_LARGE")
        raw=path.read_bytes()
        if S.sha(raw)!=saved.get("gam_sha256"):
            raise ValueError("GAM_CHANGED_DURING_SNAPSHOT")
        result=inspect_gam(raw)
        return {**result,"save_file":str(path),"snapshots_discovered":saved.get("snapshots_discovered"),
                "game_modified":False}
    except (OSError, ValueError, struct.error) as exc:
        return {"status":"SAVED_WEAPON_SURVEY_STOP","reason":str(exc)[:150],
                "game_modified":False}
