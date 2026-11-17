#!/usr/bin/env python3
"""BGXAI 121 READ ONLY. Extract REAL modded AoE SPL metadata from this EET.

Needs installed BGX120 and unchanged healing BGXP5; no in-game modifications.
Output a ZIP outside the game for exact projectile+effect analysis. Radius is
NOT guessed from SPL alone: real PRO or EET projectile table is still needed.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zipfile

import BGX119_TRACE as T
import BGX120_ENTANGLE_GUARD as G
import BGX121_POLICY as P

SPELLS = (
    ("SPPR105","Entangle"),
    ("SPWI215","Web"),
    ("SPWI213","Stinking Cloud"),
    ("SPWI502","Cloudkill"),
)
EXT_SIZE=0x28
EFFECT_SIZE=0x30

def resource(game:Path,exe:Path,tmp:Path,stem:str,ext:str)->tuple[bytes|None,str]:
    ov=T.find_file(game/"override",stem+"."+ext)
    if ov:
        raw=ov.read_bytes()
        if len(raw)>2_000_000:raise ValueError("OVERSIZED_RESOURCE")
        return raw,"override"
    out=tmp/(stem+"_EXTRACT_"+ext)
    out.mkdir()
    code,log=T.run(T.exe_args(exe,game)+["--out",str(out),"--biff-get",stem+"."+ext],tmp)
    if code:return None,"BIFF_NOT_FOUND_OR_FAILED: "+log[-300:]
    found=T.find_file(out,stem+"."+ext)
    if not found:return None,"BIFF_NOT_FOUND: "+log[-300:]
    raw=found.read_bytes()
    if len(raw)>2_000_000:raise ValueError("OVERSIZED_RESOURCE")
    return raw,"chitin_biff"

def parse_spl(b:bytes)->dict:
    if len(b)<0x72 or b[:8]!=b"SPL V1  ":
        raise ValueError("INVALID_SPL_V1")
    ext_start=struct.unpack_from("<I",b,0x64)[0]
    n=struct.unpack_from("<H",b,0x68)[0]
    table=struct.unpack_from("<I",b,0x6a)[0]
    if not 1<=n<=64 or ext_start<0x72 or ext_start+n*EXT_SIZE>len(b):
        raise ValueError("UNEXPECTED_SPL_ABILITIES")
    if table<0x72 or table>=len(b):
        raise ValueError("INVALID_EFFECT_TABLE")
    result={"spell_level":struct.unpack_from("<I",b,0x34)[0],
            "spell_type":struct.unpack_from("<H",b,0x1c)[0],
            "spell_flags":struct.unpack_from("<I",b,0x18)[0],
            "ability_count":n,"abilities":[]}
    for i in range(n):
        p=ext_start+i*EXT_SIZE
        num=struct.unpack_from("<H",b,p+0x1e)[0]
        first=struct.unpack_from("<H",b,p+0x20)[0]
        proj=struct.unpack_from("<H",b,p+0x26)[0]
        if num>128 or table+(first+num)*EFFECT_SIZE>len(b):
            raise ValueError("EFFECT_BLOCK_OOB")
        effects=[]
        for j in range(num):
            a=table+(first+j)*EFFECT_SIZE
            opcode=struct.unpack_from("<H",b,a)[0]
            effects.append({"opcode":opcode,"target_type":b[a+2],
                            "timing":b[a+12],"dispel_resistance":b[a+13],
                            "duration":struct.unpack_from("<I",b,a+14)[0],
                            "resref":b[a+0x14:a+0x1c].split(b"\0")[0].decode("ascii","replace")})
        result["abilities"].append({"level_required":struct.unpack_from("<H",b,p+0x10)[0],
            "range":struct.unpack_from("<H",b,p+0xe)[0],
            "casting_time":struct.unpack_from("<H",b,p+0x12)[0],
            "projectile_encoded":proj,"projectl_ids_index":proj-1 if proj else None,
            "projectile_radius_px":"UNKNOWN_NEEDS_EXACT_PRO",
            "effects":effects})
    return result

def policy_proofs()->dict:
    in_area=P.Ally("ally1",130,100,"BG2700")
    immune=P.Ally("spirit",130,100,"BG2700",frozenset({"ENTANGLE"}))
    far=P.Ally("far",900,200,"BG2700")
    h=P.Hazard("SPPR105",100,100,"BG2700",160,frozenset({"ENTANGLE"}))
    assert P.safe_aoe(h,[far],True)==(True,[])
    assert P.safe_aoe(h,[in_area],True)==(False,["ally1"])
    assert P.safe_aoe(h,[immune],True)==(True,[])
    assert not P.safe_aoe(h,[far],False)[0]
    assert P.choose_combat_action(in_area,(500,500),(100,100),[h],True,False)=="RANGED_WEAPON_FROM_SAFE_POSITION"
    assert P.choose_combat_action(in_area,(500,500),(100,100),[h],True,False,urgent_healing=True)=="DEFER_TO_BGXP5_HEAL"
    return {"status":"BGX121_POLICY_SELFTEST_PASS","examples":6,
            "manual_or_enemy_spells_modified":False,"game_modified":False}

def audit(game:Path,out:Path)->dict:
    game=G.exact_game(game)
    live=G.installed(game)  # requires installed BGX120, protects BGXP5
    if game==out.resolve() or game in out.resolve().parents:raise ValueError("OUTPUT_INSIDE_GAME")
    prog=G.require(game,"setup-enhanced-powergaming-scripts.exe",100000).read_bytes()
    if prog[:2]!=b"MZ":raise ValueError("WEIDU_NOT_PE")
    result={"status":"BGX121_READONLY_PASS","game_modified":False,
        "current_bgxp5_bcs_sha256":live["bcs_sha256"],
        "current_bgxp5_lua_sha256":live["lua_sha256"],
        "current_bgx120_priest1_sha256":live["priest1_sha256"],
        "geometry_policy":policy_proofs(),
        "limitations":["SPL ability projectile ID is not explosion radius",
                       "Exact PRO resource and projectile metadata pending",
                       "All summoned friendlies and immunities must be checked live by EEex",
                       "No automatic cast/movement changes made"],"spells":[]}
    collected={}
    with tempfile.TemporaryDirectory(prefix="BGX121_EET_AOE_READONLY_") as tmp:
        td=Path(tmp)
        exe=td/"weidu.exe"
        exe.write_bytes(prog)
        if G.sha(exe.read_bytes())!=G.sha(prog):raise ValueError("WEIDU_TEMP_DRIFT")
        for stem,label in SPELLS:
            row={"resref":stem,"label":label}
            try:
                b,where=resource(game,exe,td,stem,"SPL")
                row["origin"]=where
                if b is not None:
                    row["sha256"]=G.sha(b)
                    row["bytes"]=len(b)
                    row.update(parse_spl(b))
                    collected[stem+".SPL"]=b
                else:row["status"]="NOT_AVAILABLE"
            except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
                row["status"]="ERROR_CONTINUED"
                row["error"]=str(exc)
            result["spells"].append(row)
    result["valid_spell_resources"]=sum("sha256" in x for x in result["spells"])
    if result["valid_spell_resources"]<1:
        result["status"]="BGX121_PARTIAL_NO_SPL"
    out.mkdir(parents=True,exist_ok=True)
    name="BGXAI_SEND_AOE121_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".zip"
    archive=out/name
    with zipfile.ZipFile(archive,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("AOE121_REPORT.json",json.dumps(result,ensure_ascii=False,indent=2))
        for resref,raw in collected.items():z.writestr(resref,raw)
    result["zip_path"]=str(archive)
    result["zip_sha256"]=G.sha(archive.read_bytes())
    return result

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--game-root",type=Path,default=G.GAME)
    p.add_argument("--out",type=Path,default=Path.home()/"Documents"/"BGXAI_LIVE_REPORTS")
    o=p.parse_args()
    try:
        answer=audit(o.game_root,o.out)
        print(json.dumps(answer,ensure_ascii=False,indent=2))
        return 0 if answer["status"]=="BGX121_READONLY_PASS" else 2
    except (OSError,ValueError,G.Stop,subprocess.TimeoutExpired) as exc:
        print("BGX121_STOP:",str(exc))
        print("BGX121 no writes to game or saves.")
        return 2
if __name__=="__main__":
    sys.exit(main())
