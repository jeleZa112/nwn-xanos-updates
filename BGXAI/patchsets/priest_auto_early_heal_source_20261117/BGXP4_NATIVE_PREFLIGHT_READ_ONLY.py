#!/usr/bin/env python3
"""BGXP4: strict read-only native BCS proof over BGXP3, not an installer."""
from __future__ import annotations
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import BGXPR_BCS_PATCH as PR
import BGXP2_BCS_PATCH as CP
import BGXP4_AUTO_EARLY_HEAL_SOURCE_ONLY as CAND

GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
LIVE_PIN="c63173381aa93de799b02ab203337c2444c0b50a7268a95130a768e5d0ca28e3"
LUA_PIN="74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c"
BCS_COUNT=1158
FIRST_BGXPR_BLOCK=1088
EXPECTED_INDICES=tuple(FIRST_BGXPR_BLOCK+i for i in CAND.AUTO_CURE_BLOCKS)


def sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def normalize_middle_fragment(fragment: bytes) -> list[bytes]:
    blocks=PR.verify_fragment(fragment)
    if not blocks[-1].endswith(b"CR\nSC\n"):
        raise ValueError("COMPILED_BGXPR_LAST_TRAILER_CHANGED")
    return blocks[:-1] + [blocks[-1][:-3]]


def assemble(live: bytes, old_compiled: bytes, new_compiled: bytes,
             expected_live: str = LIVE_PIN) -> tuple[bytes, dict]:
    if sha(live)!=expected_live:
        raise ValueError("BGXP3_INSTALLED_BCS_SHA_MISMATCH")
    previous=CP.chunks(live,BCS_COUNT)
    original=normalize_middle_fragment(old_compiled)
    changed=normalize_middle_fragment(new_compiled)
    if previous[FIRST_BGXPR_BLOCK:FIRST_BGXPR_BLOCK+42]!=original:
        raise ValueError("COMPILED_OLD_BGXPR_NOT_EQUAL_INSTALLED")
    differences=tuple(i for i,(old,new) in enumerate(zip(original,changed)) if old!=new)
    if differences!=CAND.AUTO_CURE_BLOCKS:
        raise ValueError("UNEXPECTED_BGXPR_CURE_BLOCK_DELTA:"+repr(differences))
    output_blocks=previous.copy()
    for index in CAND.AUTO_CURE_BLOCKS:
        output_blocks[FIRST_BGXPR_BLOCK+index]=changed[index]
    output=b"SC\n"+b"".join(output_blocks)
    after=CP.chunks(output,BCS_COUNT)
    if after!=output_blocks:
        raise ValueError("BCS_LOSSLESS_REASSEMBLY_FAILED")
    changed_globals=tuple(i for i,(a,b) in enumerate(zip(previous,after)) if a!=b)
    if changed_globals!=EXPECTED_INDICES:
        raise ValueError("NON_HEAL_BCS_BLOCK_CHANGED:"+repr(changed_globals))
    if after[-1]!=previous[-1]:
        raise ValueError("BGXP3_ATTACK_BLOCK_CHANGED")
    return output, {"status":"BGXP4_NATIVE_BCS_EARLY_HEAL_CANDIDATE",
                    "installed_sha256":sha(live),"candidate_bcs_sha256":sha(output),
                    "total_blocks":BCS_COUNT,
                    "changed_block_indices_zero_based":list(EXPECTED_INDICES),
                    "preserved_blocks_exact":BCS_COUNT-len(EXPECTED_INDICES),
                    "current_BGXP3_attack_block_preserved":True,
                    "game_modified":False,"installable":False}


def preflight(game: Path = GAME) -> dict:
    game=game.resolve(strict=True)
    if game!=GAME.resolve(strict=True):
        raise ValueError("UNEXPECTED_GAME_ROOT")
    bcs=(game/"override"/"BDDEFAI.BCS").read_bytes()
    lua=(game/"override"/"M_BX43.lua").read_bytes()
    if sha(bcs)!=LIVE_PIN or sha(lua)!=LUA_PIN:
        raise ValueError("INSTALLED_BGXP3_SHA_REQUIRED")
    data=(game/"WeiDU.log").read_text("utf-8-sig",errors="replace")
    last=[s.strip().upper() for s in data.splitlines() if s.strip().startswith("~")]
    if not last or not re.match(r"^~BGXP3[/\\]SETUP-BGXP3[.]TP2~\s+#0\s+#0(?:\s|$)",last[-1]):
        raise ValueError("BGXP3_MUST_BE_LAST_WEIDU")
    proof=json.loads((game/"BGXP3"/"STAGED_PROOF.json").read_text("utf-8"))
    if proof.get("new_bcs_sha256")!=LIVE_PIN or proof.get("lua_sha256")!=LUA_PIN:
        raise ValueError("BGXP3_PROOF_CHANGED")
    source=CAND.ORIGINAL_BAF.read_bytes()
    proposed=CAND.patch(source)
    weidu=game/"setup-enhanced-powergaming-scripts.exe"
    tlk=game/"lang"/"ru_RU"/"dialog.tlk"
    if weidu.read_bytes()[:2]!=b"MZ":
        raise ValueError("INVALID_WEIDU_EXE")
    old_compiled=PR.compile_fragment(game,weidu,tlk,CAND.ORIGINAL_BAF)
    with tempfile.TemporaryDirectory(prefix="BGXP4_SOURCE_ONLY_") as td:
        baf=Path(td)/"BGXP4.baf"
        baf.write_bytes(proposed)
        new_compiled=PR.compile_fragment(game,weidu,tlk,baf)
    _,info=assemble(bcs,old_compiled,new_compiled)
    info["candidate_baf_sha256"]=sha(proposed)
    return info


if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--preflight-read-only",action="store_true")
    args=ap.parse_args()
    if not args.preflight_read_only:
        print(json.dumps({"status":"BGXP4_SOURCE_ONLY","game_modified":False,
                          "installable":False},indent=2))
    else:
        try:
            print(json.dumps(preflight(),indent=2,ensure_ascii=False))
        except (OSError,ValueError,KeyError) as err:
            print("BGXP4_STOP:",err)
            sys.exit(2)
