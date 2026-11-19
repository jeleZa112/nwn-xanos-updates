#!/usr/bin/env python3
"""BGXAI: inspect saved party CRE script slots and actual script resources, READ ONLY.

GAME V2.0 and CRE V1.0 layouts are from IESDP. The most recently saved
GAM is a historical snapshot, not proof of the LIVE runtime state.
Do not mistake source-script risk for action origin: no runtime tracing here.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

CRE_SLOTS = {"override":0x248, "class":0x250, "race":0x258,
             "general":0x260, "default":0x268}
GAM_NPC_SIZE=0x160
GAM_MAX=32_000_000
BCS_MAX=30_000_000
SCRIPT_MAX=32
NAME_PATTERN=re.compile(r"^[A-Za-z0-9_]{1,8}$")
ATTACK=re.compile(r"(?i)\b(?:Attack|AttackReevaluate|AttackOneRound|AttackNoSound|ForceAttack|ProtectObject|ChangeEnemyAlly)\s*\(")
EVENT=re.compile(r"(?i)\b(?:AttackedBy|HitBy|LastAttackerOf|LastHitter|LastSeenBy|NearestEnemyOf|Allegiance|InParty|Help|Hurt)\s*\(")
def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_resref(raw):
    return raw.split(b"\0",1)[0].strip().decode("ascii","replace").upper()

def gam_party(data):
    if len(data)<0x160 or data[:8]!=b"GAMEV2.0":
        raise ValueError("UNSUPPORTED_GAM_VERSION")
    off,count=struct.unpack_from("<II",data,0x20)
    if count>6 or off<0xA4 or off+count*GAM_NPC_SIZE>len(data):
        raise ValueError("GAM_PARTY_BOUNDS")
    gui_flags=struct.unpack_from("<I",data,0x60)[0]
    party=[]
    for i in range(count):
        p=off+i*GAM_NPC_SIZE
        pos=struct.unpack_from("<H",data,p+2)[0]
        cre_off,cre_size=struct.unpack_from("<II",data,p+4)
        if cre_size<0x2D4 or cre_size>8_000_000 or cre_off+cre_size>len(data):
            party.append({"position":pos,"status":"INVALID_CRE_BOUNDS"});continue
        cre=data[cre_off:cre_off+cre_size]
        if cre[:8]!=b"CRE V1.0":
            party.append({"position":pos,"status":"UNSUPPORTED_CRE_VERSION",
                          "cre_signature":cre[:8].decode("ascii","replace")});continue
        name=data[p+0xC0:p+0xE0].split(b"\0",1)[0].decode("cp1251","replace")
        scripts={key:read_resref(cre[o:o+8]) for key,o in CRE_SLOTS.items()}
        party.append({"position":pos,"name_from_saved_record":name,
                      "cre_sha256":sha(cre),"current_hp_in_saved_cre":
                      struct.unpack_from("<h",cre,0x24)[0],
                      "ea_in_saved_cre":cre[0x270],"scripts":scripts,
                      "status":"SAVED_CRE_SCRIPT_SLOTS_READ"})
    return {"status":"SAVED_GAM_PARTY_READ","gui_party_ai_flag_at_save":bool(gui_flags&1),
            "party":party,"gam_sha256":sha(data)}

def save_roots(root):
    home=Path(os.environ.get("USERPROFILE", str(Path.home())))
    docs=home/"Documents"
    names=("Baldur's Gate II - Enhanced Edition","Baldur's Gate - Enhanced Edition",
           "Baldur's Gate Enhanced Edition Trilogy","Baldur's Gate - Enhanced Edition Trilogy")
    folders=[root/"save",root/"mpsave"]
    for name in names:
        for dir_name in ("save","mpsave"):
            folders.append(docs/name/dir_name)
    return folders

def latest_saved_party(root):
    found=[];blocked=[]
    for folder in save_roots(root):
        if folder.is_symlink() or not folder.is_dir():continue
        for saved in folder.glob("*/BALDUR.GAM"):
            if saved.is_symlink():continue
            try:
                stat=saved.stat()
                if stat.st_size<=GAM_MAX:found.append((stat.st_mtime,saved))
                else:blocked.append("OVERSIZED:"+str(saved))
            except OSError:continue
    if not found:
        return {"status":"NO_SUPPORTED_SAVE_DISCOVERED",
                "note":"Cannot infer live CRE script slots without a saved GAM",
                "blocked":blocked}
    selected=max(found,key=lambda x:x[0])[1]
    try:
        contents=selected.read_bytes()
        parsed=gam_party(contents)
        return dict(parsed,save_file=str(selected),save_mtime=selected.stat().st_mtime,
                    snapshots_discovered=len(found),blocked=blocked,
                    runtime_state_verified=False)
    except (OSError,ValueError,struct.error) as e:
        return {"status":"LATEST_SAVE_PARSE_STOP","save_file":str(selected),
                "reason":str(e),"runtime_state_verified":False}

def script_names(saved):
    names={"BDDEFAI","PRIEST1"}
    for item in saved.get("party",[]):
        for resref in item.get("scripts",{}).values():
            if resref and NAME_PATTERN.fullmatch(resref): names.add(resref)
    return sorted(names)[:SCRIPT_MAX]

def inspect_script(root, name, binary, temp, parse_baf):
    override=root/"override"/(name+".BCS")
    if override.is_symlink():
        return {"script":name,"status":"OVERRIDE_SYMLINK_BLOCKED"}
    if override.is_file():
        try:
            raw=override.read_bytes()
        except OSError as e:
            return {"script":name,"status":"OVERRIDE_READ_FAILED","reason":str(e)}
        if len(raw)>BCS_MAX:return {"script":name,"status":"OVERSIZED_OVERRIDE"}
        input_file=temp/(name+".BCS")
        input_file.write_bytes(raw)
        source="GAME_OVERRIDE_COPY"
        byte_sha=sha(raw)
    else:
        # WeiDU resolves resources from the game's CHITIN.KEY when possible.
        input_file=Path(name+".BCS")
        source="GAME_RESOURCE_NAME"
        byte_sha=None
    output=temp/(name+".BAF")
    try:
        p=subprocess.run([str(binary),"--game",str(root),"--out",str(output),str(input_file)],
            cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,
            text=True,errors="replace",timeout=45)
        if p.returncode or not output.is_file():
            return {"script":name,"source":source,"status":"NATIVE_DECOMPILE_UNAVAILABLE",
                    "detail":((p.stdout or "")+"\n"+(p.stderr or ""))[-350:]}
        baf=output.read_text("utf-8-sig",errors="replace")
        blocks=parse_baf(baf)
        flagged=[]
        for ix,block in enumerate(blocks,1):
            actions=[a for a in block["actions"] if ATTACK.search(a)]
            if not actions:continue
            cond=block["conditions"]
            flagged.append({"block":ix,"actions":actions[:10],
                            "conditions":cond[:35],
                            "has_party_filter":any("!InParty(" in x for x in cond),
                            "has_friendly_allegiance_filter":any("!Allegiance(" in x for x in cond),
                            "reacts_to_last_attacker":bool(EVENT.search("\n".join(cond+actions)))})
        return {"script":name,"source":source,"source_sha256":byte_sha,
                "status":"DECOMPILED","total_blocks":len(blocks),
                "attack_or_protect_blocks":len(flagged),"matches":flagged}
    except (OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        return {"script":name,"source":source,"status":"NATIVE_DECOMPILE_STOP",
                "detail":str(e)[:350]}

def audit(root, weidu, temp, parse_baf, saved=None):
    saved=saved or latest_saved_party(root)
    names=script_names(saved)
    binary=temp/"weidu.exe"
    if not binary.is_file():
        shutil.copy2(weidu,binary)
    scripts=[inspect_script(root,name,binary,temp,parse_baf) for name in names]
    lua=root/"override"/"M_BX43.lua"
    lua_info={"status":"MISSING"}
    if not lua.is_symlink() and lua.is_file():
        source=lua.read_bytes()
        lua_info={"status":"READ_ONLY_STATIC_SOURCE","sha256":sha(source),
                  "has_started_action_listener":b"EEex_Action_AddSpriteStartedActionListener" in source,
                  "has_weapon_hit_listener":b"EEex_Sprite_AddBlockWeaponHitListener" in source,
                  "manual_vs_eps_origin_verified":False,
                  "runtime_action_target_verified":False}
    return {"status":"BGXAI_SCRIPT_SLOTS_READONLY_REPORT",
            "saved_party":saved,"scripts":scripts,"lua_action_contract":lua_info,
            "runtime_action_origin":"UNKNOWN",
            "conclusion":"Static script assignment/decompilation cannot prove which action executed",
            "game_modified":False}
