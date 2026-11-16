#!/usr/bin/env python3
"""BGXP5 native BCS preflight: read-only real EET WeiDU and strict 1158-block proof.

Never write to EET or install. Compiler writes in system temp only.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGXP5_PRIORITY_AND_ALLY_GUARD_SOURCE_ONLY as SRC
import BGXP2_BCS_PATCH as P

GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
BCS_PIN="c63173381aa93de799b02ab203337c2444c0b50a7268a95130a768e5d0ca28e3"
LUA_PIN="74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c"
OLD_COUNT=1158
NEW_COUNT=1170
ADDITIONS=12
OLD_COMBAT_START=1130
COMBAT_CHANGED=(24,25,26,27)
PRESERVED=OLD_COUNT-len(COMBAT_CHANGED)


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def priority_compiled_blocks(data:bytes)->list[bytes]:
    blocks=P.chunks(data,ADDITIONS)
    actions=[[int(x) for x in P.ACT.findall(b)] for b in blocks]
    if actions!=[[115,31]]*ADDITIONS:
        raise ValueError("HEAL_COMPILED_ACTIONS_UNEXPECTED:"+repr(actions))
    for i,b in enumerate(blocks):
        for tag in (b"BGXR_ROLE",b"BGX38_GUARD",b"BGXR_HEAL_CD"):
            if tag not in b:
                raise ValueError(f"MISSING_COMPILED_HEAL_GATE:{i}:{tag!r}")
    return blocks


def assemble(live:bytes,bgxp3_native:bytes,guarded_combat_native:bytes,
             priority_native:bytes,expected_live:str=BCS_PIN)->tuple[bytes,dict]:
    if sha(live)!=expected_live:
        raise ValueError("LIVE_BGXP3_BCS_SHA_MISMATCH")
    before=P.chunks(live,OLD_COUNT)
    old=P.verify_fragment(bgxp3_native)
    new=P.verify_fragment(guarded_combat_native)
    extra=priority_compiled_blocks(priority_native)
    if before[OLD_COMBAT_START:]!=old:
        raise ValueError("OLD_BGXP3_NATIVE_FRAGMENT_NOT_EQUAL_LIVE")
    changed=tuple(i for i,(a,b) in enumerate(zip(old,new)) if a!=b)
    if changed!=COMBAT_CHANGED:
        raise ValueError("NON_COMBAT_FRAGMENT_CHANGE:"+repr(changed))
    if not extra[-1].endswith(b"CR\nSC\n"):
        raise ValueError("INVALID_HEAL_FRAGMENT_TRAILER")
    clean_extra=extra[:-1]+[extra[-1][:-3]]
    final_blocks=clean_extra+before[:OLD_COMBAT_START]+new
    if len(final_blocks)!=NEW_COUNT:
        raise ValueError("EXPECTED_1170_BLOCKS")
    merged=b"SC\n"+b"".join(final_blocks)
    after=P.chunks(merged,NEW_COUNT)
    if after[ADDITIONS:ADDITIONS+OLD_COMBAT_START]!=before[:OLD_COMBAT_START]:
        raise ValueError("PRIOR_EPS_BGXPR_MODIFIED")
    if after[ADDITIONS+OLD_COMBAT_START:ADDITIONS+OLD_COMBAT_START+24]!=old[:24]:
        raise ValueError("PRIOR_SUPPORT_OR_OTHER_ACTION_MODIFIED")
    if after[-4:]!=new[-4:]:
        raise ValueError("NEW_COMBAT_GUARDS_NOT_PRESERVED")
    return merged,{
        "status":"BGXP5_NATIVE_CANDIDATE_COMPILED",
        "old_sha256":sha(live),
        "candidate_bcs_sha256":sha(merged),
        "old_blocks_preserved_exact":PRESERVED,
        "new_early_heal_blocks":ADDITIONS,
        "new_total_blocks":NEW_COUNT,
        "changed_existing_combat_blocks":list(COMBAT_CHANGED),
        "Lua_modified":False,"game_modified":False,"installable":False
    }


def compile_native(game:Path,weidu:Path,tlk:Path,baf:bytes,filename:str)->bytes:
    if not re.fullmatch(r"[A-Za-z0-9_]+",filename):
        raise ValueError("UNSAFE_BAF_NAME")
    if weidu.resolve(strict=True).parent!=game.resolve(strict=True):
        raise ValueError("WEIDU_OUTSIDE_GAME")
    if game.resolve(strict=True) not in tlk.resolve(strict=True).parents:
        raise ValueError("TLK_OUTSIDE_GAME")
    with tempfile.TemporaryDirectory(prefix="BGXP5_EET_IDS_READ_ONLY_") as folder:
        root=Path(folder)
        compiler=root/"weidu.exe"
        shutil.copy2(weidu,compiler)
        if sha(compiler.read_bytes())!=sha(weidu.read_bytes()):
            raise ValueError("WEIDU_TEMP_COPY_HASH_MISMATCH")
        (root/"out").mkdir()
        bafpath=root/(filename+".baf")
        bafpath.write_bytes(baf)
        cmd=[str(compiler),"--no-auto-tp2","--no-exit-pause","--noautoupdate",
             "--game",str(game),"--tlkin",str(tlk),"--script-style","BG2",
             "--out",str(root/"out"),str(bafpath)]
        proc=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
                            text=True,encoding="utf-8",errors="replace",timeout=90,check=False)
        log=(proc.stdout or "")+"\n"+(proc.stderr or "")
        if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
            raise ValueError("NATIVE_WEIDU_COMPILER_STOP:"+log[-1500:])
        matches=[p for p in (root/"out").rglob("*") if p.is_file() and
                 p.suffix.lower()==".bcs" and p.stem.upper()==filename.upper()]
        if len(matches)!=1:
            raise ValueError("WEIDU_COMPILED_BCS_MISSING_OR_DUPLICATE")
        return matches[0].read_bytes()


def preflight(game:Path=GAME)->dict:
    game=game.resolve(strict=True)
    if game!=GAME.resolve(strict=True):
        raise ValueError("UNEXPECTED_GAME_ROOT")
    raw=(game/"override"/"BDDEFAI.BCS").read_bytes()
    lua=(game/"override"/"M_BX43.lua").read_bytes()
    if sha(raw)!=BCS_PIN or sha(lua)!=LUA_PIN:
        raise ValueError("BGXP3_INSTALLED_BCS_LUA_SHA_REQUIRED")
    lines=[x.strip().upper() for x in (game/"WeiDU.log").read_text("utf-8-sig",errors="replace").splitlines() if x.strip().startswith("~")]
    if not lines or not re.match(r"^~BGXP3[/\\]SETUP-BGXP3[.]TP2~\s+#0\s+#0(?:\s|$)",lines[-1]):
        raise ValueError("BGXP3_MUST_BE_LAST_WEIDU")
    proof=json.loads((game/"BGXP3"/"STAGED_PROOF.json").read_text("utf-8"))
    if proof.get("new_bcs_sha256")!=BCS_PIN or proof.get("lua_sha256")!=LUA_PIN:
        raise ValueError("BGXP3_STAGED_PROOF_INVALID")
    weidu=game/"setup-enhanced-powergaming-scripts.exe"
    tlk=game/"lang"/"ru_RU"/"dialog.tlk"
    if weidu.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_EXE_MZ_INVALID")
    src=SRC.COMBAT_SOURCE.read_bytes()
    if sha(SRC.canonical(SRC.PR_SOURCE.read_bytes()))!=SRC.PR_SHA:
        raise ValueError("BGXPR_SOURCE_SHA_MISMATCH")
    original=compile_native(game,weidu,tlk,SRC.expected_bgxp3_baf(src),"BXP5OLD")
    guarded=compile_native(game,weidu,tlk,SRC.guarded_combat_baf(src),"BXP5NEW")
    heal=compile_native(game,weidu,tlk,SRC.priority_auto_cure_baf(),"BXP5HEAL")
    merged,proof=assemble(raw,original,guarded,heal)
    proof["candidate_heal_baf_sha256"]=sha(SRC.priority_auto_cure_baf())
    proof["candidate_guarded_combat_baf_sha256"]=sha(SRC.guarded_combat_baf(src))
    return proof


if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--preflight-read-only",action="store_true")
    opts=ap.parse_args()
    if not opts.preflight_read_only:
        print(json.dumps({"status":"BGXP5_SOURCE_ONLY","game_modified":False,
                          "installable":False},indent=2))
    else:
        try:
            print(json.dumps(preflight(),ensure_ascii=False,indent=2))
        except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as e:
            print("BGXP5_PREFLIGHT_STOP:",str(e))
            sys.exit(2)
