#!/usr/bin/env python3
"""BGXP3 read-only native BCS compiler/provenance check; NO game writes.

Use immutable installed BGXP2 state and two separately compiled BAFs to prove
the proposed 28th block differs while all first 1157 compiled BCS blocks match.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BGXP2_DIR = HERE if (HERE / "BGXP2_BCS_PATCH.py").is_file() else HERE.parent / "priest_combat_eps_first_20261116"
sys.path.insert(0, str(BGXP2_DIR))
import BGXP2_BCS_PATCH as BCS
from BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY import SOURCE, candidate

GAME = Path(r"C:\Games\BG_EET_FOXX_NEW")
LIVE_BCS_SHA = "583e0a5e78c6ae66ffc3c03b8811ade0168377660a6afc79b0859718d84a82eb"
LIVE_LUA_SHA = "74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c"
BASE_BLOCK_COUNT = 1158
ORIGINAL_FRAGMENT_BLOCKS = 28
UNCHANGED_BLOCKS = 1157
PRIOR_BGXPR_BLOCKS = 1130


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assemble(live: bytes, compiled_old: bytes, compiled_new: bytes,
             expected_live_sha: str | None = None) -> tuple[bytes, dict]:
    """Strict byte-preserving splice; never executes game actions or writes files."""
    if digest(live) != (expected_live_sha or LIVE_BCS_SHA):
        raise ValueError("LIVE_BGXP2_BCS_SHA_DRIFT")
    prior = BCS.chunks(live, BASE_BLOCK_COUNT)
    old = BCS.verify_fragment(compiled_old)
    new = BCS.verify_fragment(compiled_new)
    if prior[PRIOR_BGXPR_BLOCKS:] != old:
        raise ValueError("INSTALLED_BGXP2_FRAGMENT_DIFFERS_FROM_NATIVE_COMPILER")
    if old[:-1] != new[:-1]:
        raise ValueError("UNEXPECTED_PRIOR_27_BCS_BLOCK_MODIFICATION")
    if old[-1] == new[-1]:
        raise ValueError("NO_NEW_LAST_BLOCK_CHANGE")
    out = b"SC\n" + b"".join(prior[:-1] + [new[-1]])
    after = BCS.chunks(out, BASE_BLOCK_COUNT)
    if prior[:-1] != after[:-1] or after[-1] != new[-1]:
        raise ValueError("LOSSLESS_BCS_RECONSTRUCTION_FAILED")
    return out, {
        "status": "BGXP3_CANDIDATE_NATIVE_COMPILED",
        "old_sha256": digest(live),
        "proposed_sha256": digest(out),
        "preserved_blocks_exact": UNCHANGED_BLOCKS,
        "replaced_last_block_only": True,
        "total_blocks": len(after),
        "installer_available": False,
        "game_modified": False,
    }


def preflight(game: Path = GAME) -> dict:
    """Read-only EET and native WeiDU IDS preflight. Writes only OS temporary files."""
    if game.resolve(strict=True) != GAME.resolve(strict=True):
        raise ValueError("UNEXPECTED_GAME_ROOT")
    bcs = (game / "override" / "BDDEFAI.BCS").read_bytes()
    lua = (game / "override" / "M_BX43.lua").read_bytes()
    if digest(bcs) != LIVE_BCS_SHA or digest(lua) != LIVE_LUA_SHA:
        raise ValueError("INSTALLED_BGXP2_SHA_REQUIRED")
    last = [line.strip().upper() for line in (game / "WeiDU.log").read_text(
        encoding="utf-8-sig", errors="replace").splitlines() if line.strip().startswith("~")]
    if not last or "BGXP2" not in last[-1] or "SETUP-BGXP2.TP2" not in last[-1]:
        raise ValueError("BGXP2_NOT_LAST_WEIDU")
    proof = json.loads((game / "BGXP2" / "STAGED_PROOF.json").read_text(encoding="utf-8"))
    if proof.get("new_bcs_sha256") != LIVE_BCS_SHA or proof.get("lua_sha256") != LIVE_LUA_SHA:
        raise ValueError("BGXP2_PROOF_INVALID")
    orig_baf = SOURCE.read_bytes()
    proposed_baf = candidate(orig_baf)
    exe = game / "setup-enhanced-powergaming-scripts.exe"
    tlk = game / "lang" / "ru_RU" / "dialog.tlk"
    if exe.read_bytes()[:2] != b"MZ":
        raise ValueError("WEIDU_EXE_INVALID")
    compiled_old = BCS.compile_fragment(game, exe, tlk, SOURCE)
    with tempfile.TemporaryDirectory(prefix="BGXP3_CANDIDATE_READ_ONLY_") as td:
        tmp = Path(td) / "BGXP3.baf"
        tmp.write_bytes(proposed_baf)
        compiled_new = BCS.compile_fragment(game, exe, tlk, tmp)
    out, result = assemble(bcs, compiled_old, compiled_new)
    result["candidate_baf_sha256"] = digest(proposed_baf)
    result["compiled_fragment_sha256"] = digest(compiled_new)
    result["game_modified"] = False
    # Never create a staged game file; generated BCS remains memory-only.
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preflight-read-only", action="store_true")
    args = ap.parse_args()
    if not args.preflight_read_only:
        print(json.dumps({"status": "SOURCE_ONLY_NO_GAME_ACCESS",
                          "game_modified": False, "installer_available": False}))
    else:
        try:
            print(json.dumps(preflight(), indent=2, ensure_ascii=False))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print("BGXP3_PREFLIGHT_STOP:", exc)
            sys.exit(2)
