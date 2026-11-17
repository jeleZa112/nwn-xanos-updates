#!/usr/bin/env python3
"""BGXAI122 EET read-only modded projectile and opcode177 EFF audit.

Uses exact BGX120+BGXP5 installed guards; reads only SOURCE files from current
EET, using a copied WeiDU for BIF extraction. Exports raw PRO/IDS/EFF/SPL
outside the game. Never installs a BCS or changes AI/script/saves.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import zipfile

import BGX120_ENTANGLE_GUARD as G
import BGX121_READONLY as R
import BGX119_TRACE as T

# From the actual uploaded BGX121 user archive, NOT vanilla assumptions.
EXACT_SPELLS={
    "SPPR105":"1835ff5051cd21c576c2b19233a7392d31d4fcda4fa89620c083d078d2cc2b84",
    "SPWI215":"5fcf361c566db8d2070a882f54defc58c565b8fa2fd51846712cc111b487feed",
    "SPWI213":"c1da0ff730457196d4263de67c3de0988bebf772d59126b0df2466766e0de91d",
    "SPWI502":"17f627732b0ede9f22574f5e5654881009147e5811b889ffcc0c6f0072eb0ce4",
}
EXPECTED_PROJECTL_INDEX={"SPPR105":242,"SPWI215":63,"SPWI213":94,"SPWI502":186}
RE_RESOURCE=re.compile(r"[A-Za-z0-9_#]{1,8}\Z")

def parse_projectl(raw:bytes)->dict[int,str]:
    if len(raw)>2_000_000:raise ValueError("PROJECTL_OVERSIZED")
    text=raw.decode("utf-8-sig",errors="replace")
    if "IDS V1.0" not in text.upper():
        raise ValueError("PROJECTL_IDS_BAD_HEADER")
    entries={}
    for line in text.splitlines():
        line=line.split("//",1)[0].split(";",1)[0].strip()
        if not line or line.upper().startswith("IDS "):continue
        parts=line.split()
        if len(parts)<2:continue
        numeric,name=parts[:2]
        try:
            value=int(numeric,16) if numeric.lower().startswith("0x") else int(numeric,10)
        except ValueError:
            continue
        if value<0 or value>65535 or not RE_RESOURCE.fullmatch(name):
            raise ValueError("PROJECTL_IDS_BAD_ENTRY:"+line[:85])
        if value in entries and entries[value].upper()!=name.upper():
            # Ambiguous mapping could redirect the safety zone to another PRO.
            raise ValueError("PROJECTL_IDS_AMBIGUOUS:"+str(value))
        entries[value]=name.upper()
    if len(entries)<20:
        raise ValueError("PROJECTL_IDS_SUSPICIOUSLY_SHORT:"+str(len(entries)))
    return entries

def parse_pro(raw:bytes)->dict:
    if len(raw) not in (256,512,768) or raw[:8]!=b"PRO V1.0":
        raise ValueError("PRO_BAD_HEADER_OR_LENGTH")
    typ=struct.unpack_from("<H",raw,0x08)[0]
    if typ not in (0,1,2,3):
        raise ValueError("UNKNOWN_PRO_TYPE:"+str(typ))
    if typ==3 and len(raw)!=768:
        raise ValueError("PRO_AREA_NOT_768")
    result={"pro_type":typ,"bytes":len(raw),
            "is_area":typ==3,"radius_validated_for_cast":False,
            "geometry_safe_to_use_at_runtime":False,
            "shape_status":"NOT_YET_CLASSIFIED"}
    if typ==3:
        result.update({
          "area_flags":struct.unpack_from("<H",raw,0x200)[0],
          "trigger_radius_px":struct.unpack_from("<H",raw,0x204)[0],
          "explosion_radius_px":abs(struct.unpack_from("<h",raw,0x206)[0]),
          "explosion_frequency":struct.unpack_from("<H",raw,0x210)[0],
          "secondary_projectile_index":struct.unpack_from("<H",raw,0x214)[0],
          "repetitions":raw[0x216],
          "explosion_projectile_index":struct.unpack_from("<H",raw,0x21a)[0],
          "cone_angle":struct.unpack_from("<H",raw,0x224)[0],
          "ray_rotation":struct.unpack_from("<H",raw,0x226)[0],
          "note":"0x206 is size, not a proof of exact hazard geometry; flags/nesting require audit."
        })
    return result

def parse_eff(raw:bytes)->dict:
    if len(raw)<0xd8 or raw[:8]!=b"EFF V2.0":
        raise ValueError("UNEXPECTED_EFF_V2")
    r2=raw[0x30:0x38].split(b"\0",1)[0].decode("ascii","replace")
    return {
      "opcode":struct.unpack_from("<I",raw,0x10)[0],
      "target_type":struct.unpack_from("<I",raw,0x14)[0],
      "parameter1":struct.unpack_from("<I",raw,0x1c)[0],
      "parameter2":struct.unpack_from("<I",raw,0x20)[0],
      "resource":r2,
      "resist_dispel_flags":struct.unpack_from("<I",raw,0x5c)[0],
      "projectile_index":struct.unpack_from("<I",raw,0xa0)[0],
      "note":"Duration and other EFF fields may be overwritten by calling SPL opcode 177",
    }

def read_ids(game:Path,exe:Path,tmp:Path)->tuple[bytes|None,str]:
    # Modded EET usually has PROJECTL.IDS in override; root is another
    # possible loose resource location. Do not rely on web vanilla names.
    for root,location in ((game/"override","override"),(game,"root")):
        obj=T.find_file(root,"PROJECTL.IDS")
        if obj:
            if obj.is_symlink() or obj.stat().st_size>2_000_000:raise ValueError("IDS_UNSAFE")
            return obj.read_bytes(),location
    return R.resource(game,exe,tmp,"PROJECTL","IDS")

def audit(game:Path,out:Path)->dict:
    game=G.exact_game(game)
    live=G.installed(game)
    if out.resolve()==game or game in out.resolve().parents:
        raise ValueError("REPORT_PATH_INSIDE_GAME")
    compiler=G.require(game,"setup-enhanced-powergaming-scripts.exe",100000).read_bytes()
    if not compiler.startswith(b"MZ"):raise ValueError("COMPILER_NOT_PE")
    data={"status":"BGX122_READONLY_PASS","game_modified":False,
          "bgxp5_sha256":live["bcs_sha256"],
          "lua_sha256":live["lua_sha256"],
          "bgx120_priest1_sha256":live["priest1_sha256"],
          "scope":"EET PROJECTL.IDS / PRO / direct spell EFF opcode177; no automatic actions",
          "spells":[],"effs":[],"limitations":[
              "PRO explosion size alone cannot prove circular footprint",
              "No detected immunity is trusted until EEex runtime confirms all harmful effects",
              "No active AoE casting or ranged pathing modification"] }
    files={}
    with tempfile.TemporaryDirectory(prefix="BGX122_EET_PRO_READONLY_") as t:
        temp=Path(t);exe=temp/"weidu.exe";exe.write_bytes(compiler)
        if G.sha(exe.read_bytes())!=G.sha(compiler):
            raise ValueError("TEMP_WEIDU_COPY_CHANGED")
        ids_raw,ids_origin=read_ids(game,exe,temp)
        if ids_raw is None:raise ValueError("PROJECTL_IDS_NOT_FOUND:"+ids_origin)
        ids=parse_projectl(ids_raw)
        data["projectl_ids"]={"origin":ids_origin,"sha256":G.sha(ids_raw),
                              "bytes":len(ids_raw),"entries":len(ids)}
        files["PROJECTL.IDS"]=ids_raw
        children=set()
        for spell,expected_sha in EXACT_SPELLS.items():
            row={"spell":spell}
            try:
                raw,loc=R.resource(game,exe,temp,spell,"SPL")
                if raw is None:raise ValueError("SPELL_MISSING:"+loc)
                if G.sha(raw)!=expected_sha:raise ValueError("SPL_SHA_CHANGED:"+spell)
                files[spell+".SPL"]=raw
                spl=R.parse_spl(raw)
                if len(spl["abilities"])!=1:
                    raise ValueError("SPELL_MULTIPLE_ABILITIES_REQUIRES_REVIEW")
                ext=spl["abilities"][0]
                proj=ext["projectl_ids_index"]
                if proj!=EXPECTED_PROJECTL_INDEX[spell]:
                    raise ValueError("SPELL_PROJECTILE_CHANGED:"+str(proj))
                name=ids.get(proj)
                if not name:
                    raise ValueError("MISSING_OR_HARDCODED_PROJECTILE:"+str(proj))
                row.update({"source":loc,"spl_sha256":expected_sha,"projectl_index":proj,
                            "projectl_symbol":name})
                pro,origin=R.resource(game,exe,temp,name,"PRO")
                if pro is None:raise ValueError("PROJECTILE_PRO_NOT_FOUND:"+name+":"+origin)
                files[name+".PRO"]=pro
                row.update({"pro_origin":origin,"pro_sha256":G.sha(pro),
                            "pro":parse_pro(pro)})
                for ef in ext["effects"]:
                    if ef.get("opcode")==177 and ef.get("resref"):
                        children.add(ef["resref"].upper())
                row["status"]="PROJECTILE_EXTRACTED"
            except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
                row["status"]="ERROR_CONTINUED"
                row["error"]=str(exc)
            data["spells"].append(row)
        for name in sorted(children):
            row={"resource":name,"from_opcode":177,"file_type":"EFF"}
            try:
                if not RE_RESOURCE.fullmatch(name):
                    raise ValueError("INVALID_EFF_RESREF")
                b,where=R.resource(game,exe,temp,name,"EFF")
                if b is None:raise ValueError("EFF_NOT_FOUND:"+where)
                files[name+".EFF"]=b
                row.update({"origin":where,"sha256":G.sha(b),"bytes":len(b),"details":parse_eff(b),
                            "status":"EXTRACTED"})
            except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
                row["status"]="ERROR_CONTINUED"
                row["error"]=str(exc)
            data["effs"].append(row)
    data["projectiles_extracted"]=sum(x.get("status")=="PROJECTILE_EXTRACTED" for x in data["spells"])
    data["effects_extracted"]=sum(x.get("status")=="EXTRACTED" for x in data["effs"])
    if data["projectiles_extracted"]!=len(EXACT_SPELLS):
        data["status"]="BGX122_PARTIAL_PROJECTILE_DATA"
    if data["effects_extracted"]!=len(data["effs"]):
        data["status"]="BGX122_PARTIAL_EFFECT_DATA"
    out.mkdir(parents=True,exist_ok=True)
    filename="BGXAI_SEND_PRO122_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".zip"
    dest=out/filename
    with zipfile.ZipFile(dest,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("AOE122_REPORT.json",json.dumps(data,ensure_ascii=False,indent=2))
        for name,raw in sorted(files.items()):z.writestr(name,raw)
    data["archive_path"]=str(dest)
    data["archive_sha256"]=G.sha(dest.read_bytes())
    return data

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--game-root",type=Path,default=G.GAME)
    parser.add_argument("--out",type=Path,default=Path.home()/"Documents"/"BGXAI_LIVE_REPORTS")
    args=parser.parse_args()
    try:
        res=audit(args.game_root,args.out)
        print(json.dumps(res,ensure_ascii=False,indent=2))
        return 0 if res["status"]=="BGX122_READONLY_PASS" else 2
    except (OSError,ValueError,G.Stop,subprocess.TimeoutExpired) as exc:
        print("BGX122_STOP:",str(exc))
        print("Live game and BGXP5+BGX120 were not modified.")
        return 2

if __name__=="__main__":
    sys.exit(main())
