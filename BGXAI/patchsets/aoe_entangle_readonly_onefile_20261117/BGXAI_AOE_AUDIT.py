#!/usr/bin/env python3
"""BGXAI 117 -- READ-ONLY audit of the current installed BGXP5 AOE blocks.

No modification to EET, saves, BCS, Lua or WeiDU.log. WeiDU is copied to a
temporary directory and used to decompile a copy of BDDEFAI.BCS. A diagnostics
ZIP is written OUTSIDE the game into the user's Documents folder.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

GAME = Path(r"C:\Games\BG_EET_FOXX_NEW")
BCS_PIN = "cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a"
LUA_PIN = "74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c"
COUNT = 1170
AOE = (
    "ENTANGLE", "WEB", "STINKING_CLOUD", "GREASE", "CLOUDKILL", "FIREBALL",
    "ICE_STORM", "DEATH_FOG", "FIRE_STORM", "SILENCE_15", "HOLY_SMITE",
    "CONFUSION", "HORROR", "CHAOS", "INSECT_PLAGUE",
)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read(root: Path, relative: str, minimum: int = 1) -> bytes:
    if not relative or ".." in relative or "\\" in relative:
        raise ValueError("UNSAFE_FILE_PATH")
    path = root / relative
    if not path.is_file() or path.is_symlink() or path.stat().st_size < minimum:
        raise ValueError("FILE_MISSING_OR_UNSAFE:" + relative)
    for parent in list(path.parents):
        if parent.is_symlink():
            raise ValueError("REPARSE_PARENT:" + relative)
        if parent == root:
            break
    return path.read_bytes()

def checked(game: Path) -> tuple[bytes, bytes, bytes, str]:
    bcs = read(game, "override/BDDEFAI.BCS", 1000)
    lua = read(game, "override/M_BX43.lua", 100)
    if digest(bcs) != BCS_PIN or digest(lua) != LUA_PIN:
        raise ValueError("BGXP5_LIVE_SHA_MISMATCH")
    log = read(game, "WeiDU.log").decode("utf-8-sig", errors="replace")
    last = [x.strip() for x in log.splitlines() if x.strip().startswith("~")]
    if not last or not re.match(r"^~BGXP5[/\\]SETUP-BGXP5[.]TP2~\s+#0\s+#0(?:\s|$)", last[-1], re.I):
        raise ValueError("BGXP5_NOT_LAST_WEIDU")
    exe = read(game, "setup-enhanced-powergaming-scripts.exe", 100000)
    if not exe.startswith(b"MZ"):
        raise ValueError("INVALID_WEIDU_EXE")
    read(game, "lang/ru_RU/dialog.tlk", 100)
    return bcs, exe, lua, last[-1]

def find_blocks(text: str) -> list[str]:
    return re.findall(r"(?im)^IF\s*$[\s\S]*?^END\s*$", text)

def classify(text: str) -> dict:
    blocks = find_blocks(text)
    hits = []
    for i, block in enumerate(blocks):
        terms = [token for token in AOE if re.search(
            r"(?<![A-Z0-9])" + re.escape(token) + r"(?![A-Z0-9])", block, flags=re.I)]
        if terms:
            hits.append({"index_zero_based":i, "terms":terms, "block":block})
    return {"baf_block_count":len(blocks), "entangle_block_count":sum(
        "ENTANGLE" in b["terms"] for b in hits), "aoe_blocks":hits}

def decompile(game: Path, bcs: bytes, executable: bytes) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="BGXAI_AOE_TMP_") as td:
        root = Path(td)
        (root / "out").mkdir()
        (root / "BDDEFAI.BCS").write_bytes(bcs)
        compiler = root / "weidu.exe"
        compiler.write_bytes(executable)
        if digest(compiler.read_bytes()) != digest(executable):
            raise ValueError("COMPILER_COPY_MISMATCH")
        cmd=[str(compiler),"--no-auto-tp2","--no-exit-pause","--noautoupdate",
             "--game",str(game),"--tlkin",str(game / "lang" / "ru_RU" / "dialog.tlk"),
             "--script-style","BG2","--out",str(root / "out"),str(root / "BDDEFAI.BCS")]
        p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
             text=True,encoding="utf-8",errors="replace",timeout=180,check=False)
        log=(p.stdout or "")+"\n"+(p.stderr or "")
        if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
            raise ValueError("WEIDU_DECOMPILE_STOP:"+log[-1700:])
        matches=[x for x in (root/"out").rglob("*") if x.is_file() and
                 x.stem.casefold()=="bddefai" and x.suffix.casefold()==".baf"]
        if len(matches)!=1:
            raise ValueError("NO_UNIQUE_DECOMPILED_BAF:"+log[-1000:])
        return matches[0].read_text("utf-8",errors="replace"),log[-1500:]

def audit(game: Path, output: Path) -> dict:
    game = game.resolve(strict=True)
    if game != GAME.resolve(strict=True):
        raise ValueError("UNEXPECTED_GAME_ROOT")
    bcs,exe,lua,weidu=checked(game)
    baf,log=decompile(game,bcs,exe)
    found=classify(baf)
    if found["baf_block_count"] != COUNT:
        raise ValueError("COMPILED_BCS_BLOCK_COUNT_DRIFT:"+str(found["baf_block_count"]))
    if output.resolve()==game or game in output.resolve().parents:
        raise ValueError("OUTPUT_MUST_BE_OUTSIDE_GAME")
    output.mkdir(parents=True,exist_ok=True)
    zip_path=output/("BGXAI_AOE_SEND_TO_CHATGPT_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".zip")
    summary={"status":"BGXAI_AOE_READONLY_PASS","bcs_sha256":digest(bcs),
             "lua_sha256":digest(lua),"last_weidu":weidu,
             "total_blocks":COUNT,"aoe_keyword_hits":len(found["aoe_blocks"]),
             "entangle_keyword_hits":found["entangle_block_count"],
             "game_modified":False,
             "note":"Full BAF included. Numeric SPL references need further inspection."}
    with zipfile.ZipFile(zip_path,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("BDDEFAI_DECOMPILED_READONLY.BAF",baf)
        z.writestr("AOE_BLOCKS.json",json.dumps(found,ensure_ascii=False,indent=2))
        z.writestr("REPORT.json",json.dumps(summary,ensure_ascii=False,indent=2))
        z.writestr("WEIDU_OUTPUT_TAIL.txt",log)
    summary["zip"]=str(zip_path)
    summary["zip_sha256"]=digest(zip_path.read_bytes())
    return summary

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--game",type=Path,default=GAME)
    p.add_argument("--out",type=Path,default=Path.home()/"Documents"/"BGXAI_LIVE_REPORTS")
    a=p.parse_args()
    try:
        print(json.dumps(audit(a.game.resolve(strict=True),a.out),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,subprocess.TimeoutExpired) as err:
        print("BGXAI_AOE_STOP:",err)
        print("No game or save files were modified.")
        return 2
if __name__=="__main__":
    sys.exit(main())
