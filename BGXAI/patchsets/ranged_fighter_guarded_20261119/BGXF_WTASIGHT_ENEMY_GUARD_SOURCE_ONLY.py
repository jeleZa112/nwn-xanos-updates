#!/usr/bin/env python3
"""BGXAI source-only/native read-only preflight for party-friendly Enemy() in WTASIGHT.

This code NEVER installs a BCS or alters game files. It is intended to be
integrated with the existing SHA-pinned BGXAI_UPDATE.cmd after offline review.
No proof of combat success is implied by a passing source/native check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(r"C:\Games\BG_EET_FOXX_NEW")
BASE_SHA = "7d69e5408ad84912afec848cba221614a625caee7f8469db067108c70041bde1"
BASE_BCS = pathlib.Path("override/WTASIGHT.BCS")
BCS_COUNT = 6
BLOCK_RE = re.compile(r"(?ms)^IF[ \t]*\n.*?^END[ \t]*$")
CONDITION = "!InParty(Myself)"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parts(binary: bytes) -> list[bytes]:
    """Split BCS in same lossless way as the project's audited preflight."""
    if not binary.startswith(b"SC\nCR\nCO\n") or not binary.endswith(b"CR\nSC\n"):
        raise ValueError("BCS_ENVELOPE")
    starts = [m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)", binary)]
    if not starts or starts[0] != 3:
        raise ValueError("BCS_START")
    result = [binary[a:b] for a, b in zip(starts, starts[1:] + [len(binary)])]
    if b"SC\n" + b"".join(result) != binary:
        raise ValueError("BCS_SPLIT_NOT_LOSSLESS")
    return result


def transform_baf(source: str) -> tuple[str, int]:
    blocks = list(BLOCK_RE.finditer(source))
    if len(blocks) != BCS_COUNT:
        raise ValueError("WTASIGHT_BAF_BLOCK_COUNT_DRIFT")
    targets: list[tuple[int, re.Match, str]] = []
    for index, match in enumerate(blocks, 1):
        block = match.group()
        halves = re.split(r"(?m)^THEN[ \t]*$", block)
        if len(halves) != 2:
            raise ValueError(f"BAD_THEN_BLOCK_{index}")
        condition_part, response_part = halves
        # Only exactly the in-game reaction to friendly fire may be touched.
        if not re.search(r"(?m)^\s*Enemy\(\)\s*$", response_part):
            continue
        if not re.search(r"(?m)^\s*AttackedBy\(\[GOODCUTOFF\],DEFAULT\)\s*$", condition_part):
            raise ValueError(f"OTHER_ENEMY_BLOCK_{index}")
        if re.search(r"(?m)^\s*" + re.escape(CONDITION) + r"\s*$", condition_part):
            raise ValueError("ALREADY_GUARDED_NO_CHANGE_REQUIRED")
        # Restrict to the only action in the block, no extras / story actions.
        actions = re.findall(r"(?m)^\s*([A-Za-z]\w*\s*\([^\n]*\))\s*$", response_part)
        if actions != ["Enemy()"]:
            raise ValueError(f"ENEMY_BLOCK_HAS_OTHER_ACTIONS_{index}:{actions!r}")
        targets.append((index, match, block))
    if len(targets) != 1:
        raise ValueError("EXPECTED_EXACTLY_ONE_FRIENDLY_ENEMY_BLOCK")
    index, match, old = targets[0]
    new, count = re.subn(r"(?m)^THEN[ \t]*$", "  " + CONDITION + "\nTHEN", old, count=1)
    if count != 1 or new == old:
        raise ValueError("BAF_PATCH_NOT_APPLIED")
    result = source[:match.start()] + new + source[match.end():]
    changed = list(BLOCK_RE.finditer(result))
    if len(changed) != BCS_COUNT:
        raise ValueError("NEW_BAF_BLOCK_COUNT_DRIFT")
    if any(changed[i].group() != blocks[i].group() for i in range(BCS_COUNT) if i != index - 1):
        raise ValueError("OTHER_BAF_BLOCK_MODIFIED")
    if result.count(CONDITION) != source.count(CONDITION) + 1:
        raise ValueError("UNEXPECTED_GUARD_COUNT")
    return result, index


def execute_weidu(exe: pathlib.Path, game: pathlib.Path, work: pathlib.Path, src: pathlib.Path,
                  dest: pathlib.Path, label: str) -> None:
    if dest.exists():
        raise ValueError("TEMP_DEST_COLLISION:" + label)
    proc = subprocess.run(
        [str(exe), "--game", str(game), "--out", str(dest), str(src)],
        cwd=work, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, errors="replace", timeout=180,
    )
    transcript = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)", transcript) or not dest.is_file():
        raise ValueError("WEIDU_" + label + "_FAILED:" + transcript[-400:])


def build_candidate(game: pathlib.Path) -> tuple[bytes, int]:
    if game != ROOT or not (game / "chitin.key").is_file():
        raise ValueError("GAME_ROOT_NOT_VERIFIED")
    candidate = game / BASE_BCS
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError("WTASIGHT_SOURCE_INVALID")
    live_bytes = candidate.read_bytes()
    if digest(live_bytes) != BASE_SHA:
        raise ValueError("WTASIGHT_LIVE_SHA_DRIFT")
    old = parts(live_bytes)
    if len(old) != BCS_COUNT:
        raise ValueError("WTASIGHT_LIVE_BLOCK_COUNT_DRIFT")
    weidu = game / "setup-enhanced-powergaming-scripts.exe"
    if weidu.is_symlink() or not weidu.is_file() or weidu.read_bytes()[:2] != b"MZ":
        raise ValueError("NATIVE_WEIDU_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="BGXAI_WTASIGHT_SOURCEONLY_") as tmp:
        folder = pathlib.Path(tmp)
        binary = folder / "weidu.exe"
        shutil.copy2(weidu, binary)
        source = folder / "WTASIGHT.BCS"
        shutil.copy2(candidate, source)
        if digest(source.read_bytes()) != BASE_SHA:
            raise ValueError("TEMP_SOURCE_SHA_MISMATCH")
        extracted = folder / "WTASIGHT.BAF"
        execute_weidu(binary, game, folder, source, extracted, "DECOMPILE")
        patched_text, index = transform_baf(extracted.read_text("utf-8-sig", errors="replace"))
        compiled_dir = folder / "build"
        compiled_dir.mkdir()
        baf = compiled_dir / "WTASIGHT.BAF"
        baf.write_text(patched_text, encoding="utf-8")
        new = compiled_dir / "WTASIGHT.BCS"
        execute_weidu(binary, game, compiled_dir, baf, new, "COMPILE")
        fresh = parts(new.read_bytes())
        if len(fresh) != BCS_COUNT:
            raise ValueError("COMPILED_BCS_BLOCK_COUNT_DRIFT")
        # Preserve all other blocks *byte-for-byte*, even if WeiDU recompiles differently.
        merged_parts = old.copy()
        merged_parts[index - 1] = fresh[index - 1]
        merged = b"SC\n" + b"".join(merged_parts)
        check = parts(merged)
        if len(check) != BCS_COUNT or any(check[i] != old[i] for i in range(BCS_COUNT) if i != index - 1):
            raise ValueError("NON_TARGET_BLOCK_DRIFT")
        if check[index - 1] == old[index - 1]:
            raise ValueError("NO_BYTE_CHANGE")
        return merged, index


def preflight(game: pathlib.Path) -> dict:
    merged, index = build_candidate(game)
    return {
        "status": "BGXF_WTASIGHT_SOURCE_ONLY_PREFLIGHT_PASS",
        "game_modified": False,
        "live_wtasight_sha256": BASE_SHA,
        "patched_bcs_sha256": digest(merged),
        "changed_block": index,
        "preserved_other_blocks": BCS_COUNT - 1,
        "safety": "Only guard Enemy() after friendly attack for characters currently in party",
        "combat_tested": False,
        "installed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BGXAI WTASIGHT read-only source-only native preflight")
    parser.add_argument("--game", default=str(ROOT))
    args = parser.parse_args()
    try:
        print(json.dumps(preflight(pathlib.Path(args.game)), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print("BGXF_WTASIGHT_SOURCE_ONLY_STOP:" + str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())