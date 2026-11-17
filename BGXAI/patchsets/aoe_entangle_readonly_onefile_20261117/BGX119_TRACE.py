#!/usr/bin/env python3
"""BGXAI 119 -- read-only provenance: Jaheira's five script layers in THIS EET.
Extracts override files or BIFF assets to TEMP with copied WeiDU, decompiles
them and writes a diagnostics ZIP in Documents. Does not modify the game.
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

import BGXAI_AOE_AUDIT as A

SCRIPTS = ("JAHEIRA_", "BDDEFAI", "PRIEST1", "WTASIGHT", "DPLAYER")
SLOTS = (("override",0x248), ("class",0x250), ("race",0x258),
         ("general",0x260), ("default",0x268))
SPELL = re.compile(r"(?im)^\s*(?:Spell|SpellNoDec|SpellRES|SpellNoDecRES|SpellPoint|"
    r"ForceSpell|ReallyForceSpell|ReallyForceSpellRES|ForceSpellPoint|"
    r"ActionOverride|ApplySpellRES)\s*\([^\n]*(?:CLERIC_ENTANGLE|SPPR105|"
    r"\b2005\b)[^\n]*$")
RESPONSE = re.compile(r"(?im)^\s*(?:Spell(?:NoDec)?(?:Point|RES)?|"
    r"ForceSpell(?:Point)?|ReallyForceSpell(?:RES)?)\s*\(")

def run(cmd: list[str], cwd: Path) -> tuple[int,str]:
    p=subprocess.run(cmd,cwd=cwd,stdin=subprocess.DEVNULL,
                     capture_output=True,text=True,encoding="utf-8",
                     errors="replace",timeout=150,check=False)
    return p.returncode, ((p.stdout or "")+"\n"+(p.stderr or ""))[-3500:]

def exe_args(compiler: Path,game: Path) -> list[str]:
    return [str(compiler),"--no-auto-tp2","--no-exit-pause","--noautoupdate",
            "--game",str(game),"--tlkin",str(game/"lang"/"ru_RU"/"dialog.tlk"),
            "--script-style","BG2"]

def find_file(folder: Path, name: str) -> Path|None:
    if not folder.is_dir(): return None
    candidates=[p for p in folder.iterdir()
                if p.is_file() and not p.is_symlink() and p.name.upper()==name.upper()]
    if len(candidates)>1: raise ValueError("DUPLICATE_RESOURCE:"+name)
    return candidates[0] if candidates else None

def gam_snapshot(game: Path) -> dict:
    gam=Path.home()/"Documents"/"Baldur's Gate - Enhanced Edition Trilogy"/"save"/"000000901-BGXAI_TEST_6_NO_PRIEST1"/"BALDUR.gam"
    if not gam.is_file() or gam.is_symlink():return {"status":"SAVE_SLOT_NOT_FOUND"}
    raw=gam.read_bytes()
    if len(raw)<10000 or raw[:8]!=b"GAMEV2.0":return {"status":"UNEXPECTED_GAM"}
    off,n=struct.unpack_from("<II",raw,0x20)
    if n!=6 or off+n*352>len(raw):return {"status":"PARTY_DATA_DRIFT","count":n}
    members=[]
    for i in range(n):
        pos=off+i*352
        cre,length=struct.unpack_from("<II",raw,pos+4)
        if cre+length>len(raw) or length<0x2d4 or raw[cre:cre+8]!=b"CRE V1.0":
            return {"status":"INVALID_CRE","slot":i+1}
        member={"slot":i+1,"name":raw[pos+0xc0:pos+0xe0].split(b"\0")[0].decode("ascii","replace")}
        member["scripts"]={k:raw[cre+o:cre+o+8].split(b"\0")[0].decode("ascii","replace")
                           for k,o in SLOTS}
        members.append(member)
    return {"status":"GAM_READ_ONLY","sha256":A.digest(raw),"members":members}

def read_script(game: Path, exe: Path, td: Path, stem: str) -> tuple[bytes|None,str,str]:
    ov=find_file(game/"override",stem+".BCS")
    if ov:
        raw=ov.read_bytes()
        if not (raw.startswith(b"SC\n") and raw.endswith(b"SC\n")):
            raise ValueError("INVALID_OVERRIDE_BCS:"+stem)
        return raw,"override",str(ov)
    target=td/(stem+"_BIF")
    target.mkdir()
    cmd=exe_args(exe,game)+["--out",str(target),"--biff-get",stem+".BCS"]
    code,log=run(cmd,td)
    if code:return None,"biff_extract_failed",log
    found=find_file(target,stem+".BCS")
    if not found:return None,"not_found_in_chitin",log
    raw=found.read_bytes()
    if not (raw.startswith(b"SC\n") and raw.endswith(b"SC\n")):
        return None,"invalid_biff_BCS",log
    return raw,"chitin_biff",log

def decompile(exe: Path,game: Path,td: Path,stem: str,raw: bytes)->tuple[str,str]:
    inp=td/(stem+".BCS")
    inp.write_bytes(raw)
    out=td/(stem+"_BAF")
    out.mkdir()
    code,log=run(exe_args(exe,game)+["--out",str(out),str(inp)],td)
    if code:return "","WEIDU_DECOMPILE_FAILED "+log
    found=find_file(out,stem+".BAF")
    if found is None:return "","BAF_NOT_CREATED "+log
    return found.read_text("utf-8",errors="replace"),log

def extract(game: Path,out: Path)->dict:
    game=game.resolve(strict=True)
    if game!=A.GAME.resolve(strict=True):raise ValueError("GAME_ROOT_MISMATCH")
    bcs,exeb,lua,last=A.checked(game)
    out=out.resolve()
    if out==game or game in out.parents:raise ValueError("REPORT_INSIDE_GAME_BLOCKED")
    report={"status":"BGX119_READONLY_PASS","game_modified":False,
            "bcs_sha256":A.digest(bcs),"lua_sha256":A.digest(lua),
            "last_weidu":last,"save":gam_snapshot(game),"scripts":[]}
    outputs={}
    with tempfile.TemporaryDirectory(prefix="BGX119_SCRIPT_TRACE_") as tmp:
        td=Path(tmp);exe=td/"weidu.exe";exe.write_bytes(exeb)
        if A.digest(exe.read_bytes())!=A.digest(exeb):raise ValueError("WEIDU_COPY_MISMATCH")
        for stem in SCRIPTS:
            try:
                raw,origin,origin_log=read_script(game,exe,td,stem)
                row={"resource":stem,"origin":origin}
                if raw is not None:
                    if len(raw)>5_000_000:raise ValueError("OVERSIZED_SCRIPT")
                    row.update({"sha256":A.digest(raw),"size":len(raw)})
                    outputs[stem+".BCS"]=raw
                    baf,log=decompile(exe,game,td,stem,raw)
                    if baf:
                        row["baf_blocks"]=len(A.find_blocks(baf))
                        row["entangle_action_lines"]=SPELL.findall(baf)
                        row["entangle_text_mentioned"]=bool(re.search("ENTANGLE|SPPR105",baf,re.I))
                        row["spell_action_count"]=len(RESPONSE.findall(baf))
                        row["decompile_status"]="OK"
                        outputs[stem+".BAF"]=baf
                    else:row["decompile_status"]=log
                else:row["diagnostic"]=origin_log[-850:]
            except (OSError,ValueError,subprocess.TimeoutExpired) as e:
                row={"resource":stem,"status":"ERROR_CONTINUED","error":str(e)}
            report["scripts"].append(row)
    out.mkdir(parents=True,exist_ok=True)
    fn=out/("BGXAI_SEND_SCRIPT_TRACE_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".zip")
    report["found_scripts"]=sum("sha256" in s for s in report["scripts"])
    if report["found_scripts"]<1:report["status"]="BGX119_PARTIAL_NO_SCRIPTS"
    with zipfile.ZipFile(fn,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("REPORT.json",json.dumps(report,ensure_ascii=False,indent=2))
        for k,v in outputs.items():z.writestr(k,v)
    report["zip_path"]=str(fn)
    report["zip_sha256"]=A.digest(fn.read_bytes())
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--game-root",type=Path,default=A.GAME)
    p.add_argument("--out",type=Path,default=Path.home()/"Documents"/"BGXAI_LIVE_REPORTS")
    args=p.parse_args()
    try:
        result=extract(args.game_root,args.out)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result["status"]=="BGX119_READONLY_PASS" else 2
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        print("BGX119_STOP:",str(e),"Game unchanged.")
        return 2

if __name__=="__main__":
    sys.exit(main())
