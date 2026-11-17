#!/usr/bin/env python3
"""BGXAI 118: safe A/B test save COPY without Jaheira's independent PRIEST1 script.

Never change original saves, current playthrough, override, BCS, Lua or WeiDU.
Separate explicit confirmation required for creating the NEW save slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import uuid

import BGXAI_AOE_AUDIT as A

SOURCE_SLOT = "000000900-BGXAI_TEST_6"
TARGET_SLOT = "000000901-BGXAI_TEST_6_NO_PRIEST1"
TOKEN = "CREATE_BGXAI_TEST6_NO_PRIEST1"
ENTRY_SIZE = 352
SLOT_NAMES = ("Tarana", "Tarana", "Jade", "Jagan Battleforge", "Khalid", "Jaheira")


def u32(raw: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(raw):
        raise ValueError("GAM_OFFSET_OUTSIDE_DATA")
    return struct.unpack_from("<I", raw, off)[0]


def name(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("ascii", errors="strict")


def alter_gam(original: bytes) -> tuple[bytes, dict]:
    if not (10000 < len(original) < 10_000_000) or original[:8] != b"GAMEV2.0":
        raise ValueError("UNEXPECTED_GAME_V2_SAVE_HEADER")
    count = u32(original, 0x24)
    off = u32(original, 0x20)
    if count != 6 or off < 0x80 or off + ENTRY_SIZE * count > len(original):
        raise ValueError("EXPECTED_EXACT_SIX_PARTY_TEST_SLOTS")
    found = []
    pos = None
    for idx, expected in enumerate(SLOT_NAMES):
        start = off + idx * ENTRY_SIZE
        actual = name(original[start + 0xC0 : start + 0xE0])
        if actual != expected:
            raise ValueError(f"WRONG_TEST_PARTY_SLOT_{idx+1}:{actual}")
        cre = u32(original, start + 4)
        length = u32(original, start + 8)
        if length < 0x2D4 or cre < 0x80 or cre + length > len(original):
            raise ValueError("CORRUPTED_EMBEDDED_CRE")
        if original[cre : cre + 8] != b"CRE V1.0":
            raise ValueError("NOT_CRE_V1")
        class_script = name(original[cre + 0x250 : cre + 0x258])
        if class_script.upper() != "BDDEFAI":
            raise ValueError("BGXP5_CLASS_SCRIPT_REQUIRED")
        if idx == 5:
            if name(original[cre + 0x248 : cre + 0x250]).upper() != "JAHEIRA_":
                raise ValueError("JAHEIRA_OVERRIDE_SCRIPT_CHANGED")
            if original[cre + 0x258 : cre + 0x260] != b"PRIEST1\0":
                raise ValueError("JAHEIRA_RACE_SCRIPT_NOT_PRIEST1")
            pos = cre + 0x258
        found.append({"slot": idx + 1, "name": actual, "class_script": class_script})
    if pos is None:
        raise ValueError("JAHEIRA_NOT_FOUND")
    modified = bytearray(original)
    modified[pos : pos + 8] = b"None\0\0\0\0"
    # Prove all save bytes except this one resref are absolutely unchanged.
    if modified[:pos] != original[:pos] or modified[pos + 8:] != original[pos + 8:]:
        raise ValueError("TEST_SAVE_EXCESS_MUTATION")
    return bytes(modified), {
        "original_gam_sha256": A.digest(original),
        "new_gam_sha256": A.digest(modified),
        "modified_offset": pos,
        "modified_bytes": 8,
        "party": found,
        "jaheira_script_change": {"slot": "race", "old": "PRIEST1", "new": "None"},
        "original_preserved": True,
        "game_bcs_lua_preserved": True,
    }


def files(source: Path) -> list[Path]:
    if not source.is_dir() or source.is_symlink() or source.parent.is_symlink():
        raise ValueError("TEST_SOURCE_DIRECTORY_MISSING_OR_LINKED")
    found = sorted(source.iterdir())
    if not (2 <= len(found) <= 16):
        raise ValueError("TEST_SOURCE_FILE_LIST_UNEXPECTED")
    for f in found:
        if not f.is_file() or f.is_symlink() or not (
            f.name.lower() in ("baldur.gam", "baldur.sav", "baldur.bmp") or
            re.fullmatch(r"PORTRT\d{1,2}\.BMP", f.name, re.I)
        ):
            raise ValueError("TEST_SOURCE_UNEXPECTED_FILE:"+f.name)
        if f.stat().st_size > 100_000_000:
            raise ValueError("TEST_SAVE_FILE_TOO_LARGE")
    if not any(f.name.lower() == "baldur.sav" for f in found):
        raise ValueError("MISSING_ORIGINAL_BALDUR_SAV")
    if sum(f.name.lower() == "baldur.gam" for f in found) != 1:
        raise ValueError("MISSING_OR_DUPLICATE_BALDUR_GAM")
    return found


def guard_no_running_game():
    if os.name != "nt":
        raise ValueError("WINDOWS_ONLY")
    p = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=30)
    if p.returncode:
        raise ValueError("CANNOT_VERIFY_GAME_PROCESSES")
    import csv, io
    for row in csv.reader(io.StringIO(p.stdout)):
        if not row:
            continue
        if re.search(r"^(?:Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|weidu|setup-.*)\.exe$",row[0],re.I):
            raise ValueError("CLOSE_BALDUR_INFINITYLOADER_WEIDU_FIRST:"+row[0])


def new_copy(game: Path, save_root: Path, confirm: str, yes: bool) -> dict:
    if not yes or confirm != TOKEN:
        raise ValueError("EXPLICIT_TEST_SAVE_COPY_APPROVAL_REQUIRED")
    if game.resolve(strict=True) != A.GAME.resolve(strict=True):
        raise ValueError("WRONG_GAME_ROOT")
    if os.name != "nt":
        raise ValueError("WINDOWS_ONLY")
    A.checked(game)  # exact installed BGXP5 BCS + Lua + last WeiDU
    guard_no_running_game()
    if save_root.is_symlink() or not save_root.is_dir():
        raise ValueError("EET_SAVE_DIRECTORY_MISSING")
    src = save_root / SOURCE_SLOT
    dst = save_root / TARGET_SLOT
    if dst.exists() or dst.is_symlink():
        raise ValueError("TARGET_TEST_SAVE_ALREADY_EXISTS_NO_OVERWRITE")
    originals = files(src)
    raw_gam = next(f.read_bytes() for f in originals if f.name.lower() == "baldur.gam")
    new_gam, report = alter_gam(raw_gam)
    hashes = {f.name: A.digest(f.read_bytes()) for f in originals}
    temporary = save_root / (TARGET_SLOT + "_STAGING_" + uuid.uuid4().hex[:12])
    if temporary.exists():
        raise ValueError("STAGING_COLLISION")
    created = False
    try:
        temporary.mkdir()
        created = True
        for item in originals:
            shutil.copy2(item, temporary / item.name)
            if A.digest((temporary/item.name).read_bytes()) != hashes[item.name]:
                raise ValueError("COPIED_SAVE_SHA_MISMATCH:"+item.name)
        dest_gam = next(f for f in temporary.iterdir() if f.name.lower()=="baldur.gam")
        dest_gam.write_bytes(new_gam)
        if dest_gam.read_bytes() != new_gam:
            raise ValueError("CHANGED_SAVE_MISMATCH")
        if A.digest(next(f.read_bytes() for f in originals if f.name.lower()=="baldur.gam")) != A.digest(raw_gam):
            raise ValueError("ORIGINAL_SAVE_CHANGED_ABORT")
        guard_no_running_game()
        if dst.exists():
            raise ValueError("TARGET_SAVE_APPEARED_NO_OVERWRITE")
        os.rename(temporary, dst)
        created = False
    finally:
        if created and temporary.exists():
            shutil.rmtree(temporary)
    if next(f for f in dst.iterdir() if f.name.lower()=="baldur.gam").read_bytes() != new_gam:
        raise ValueError("FINAL_TEST_SAVE_COPY_CORRUPTED")
    report.update({
        "status": "BGXAI_TEST6_NO_PRIEST1_COPY_VERIFIED",
        "source_slot": SOURCE_SLOT,
        "new_slot": TARGET_SLOT,
        "new_save_path": str(dst),
        "source_files_sha256": hashes,
        "new_save_file_count": len(originals),
        "game_modified": False,
        "only_new_test_save_created": True,
        "warning": "A/B test only. This does not repair other scripts or prove PRIEST1 was the sole source of Entangle.",
    })
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--game-root", type=Path, default=A.GAME)
    p.add_argument("--save-root", type=Path, default=Path.home()/"Documents"/
                   "Baldur's Gate - Enhanced Edition Trilogy"/"save")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--confirm", default="")
    a = p.parse_args()
    try:
        result = new_copy(a.game_root, a.save_root, a.confirm, a.yes)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError,ValueError,subprocess.TimeoutExpired) as error:
        print("BGXAI_TEST6_SAFE_STOP:",str(error))
        print("Installed BGXP5 and existing saves unchanged.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
