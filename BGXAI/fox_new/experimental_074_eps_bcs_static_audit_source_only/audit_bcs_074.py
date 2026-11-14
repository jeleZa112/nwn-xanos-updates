#!/usr/bin/env python3
"""BGXAI 074. Strict, read-only parser/auditor for Infinity Engine textual BCS.

No dependency on, write operation to, or installation into a game. Blocks are
reported by 1-based index. No raw BCS content is exported to the result JSON.
The 041 fixture is a HISTORICAL SNAPSHOT, NOT the currently installed 066S.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

BLOCK = re.compile(rb'CR\nCO\n.*?\nRS\nCR\n', re.DOTALL)
PIN_041_SHA = '86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
PIN_041_BLOCKS = 1057
PIN_064_BLOCKS = 1077  # exact pinned 066S builder, distinct from 041
PIN_066S_INSERT_BLOCKS = 11
PIN_066S_SPLICE_ZERO_BASED = 1051
PIN_066S_TOTAL_BLOCKS = PIN_064_BLOCKS + PIN_066S_INSERT_BLOCKS

class UnsafeOrUnexpectedBCS(ValueError):
    pass


def parse_lossless(data: bytes) -> list[bytes]:
    if not isinstance(data, bytes) or not data.startswith(b'SC\n') or not data.endswith(b'CR\nSC\n'):
        raise UnsafeOrUnexpectedBCS('BCS_SC_HEADER_OR_FOOTER_INVALID')
    if b'\r' in data or b'\x00' in data:
        raise UnsafeOrUnexpectedBCS('BCS_EXPECTED_ASCII_LF_ONLY')
    matches = list(BLOCK.finditer(data))
    if not matches:
        raise UnsafeOrUnexpectedBCS('BCS_NO_COMPLETE_BLOCKS')
    chunks = [m.group(0) for m in matches]
    if b'SC\n' + b''.join(chunks) + b'SC\n' != data:
        raise UnsafeOrUnexpectedBCS('BCS_SEGMENTATION_NOT_LOSSLESS')
    if any(b.count(b'\nRS\n') != 2 for b in chunks):
        raise UnsafeOrUnexpectedBCS('BCS_RESPONSE_SEPARATOR_INVALID')
    return chunks


def positions(chunks: list[bytes], needle: bytes) -> list[int]:
    return [i for i, chunk in enumerate(chunks, 1) if needle in chunk]


def audit_041(data: bytes, *, strict_fixture: bool = True) -> dict:
    chunks = parse_lossless(data)
    digest = hashlib.sha256(data).hexdigest()
    if strict_fixture and (digest != PIN_041_SHA or len(chunks) != PIN_041_BLOCKS):
        raise UnsafeOrUnexpectedBCS('NOT_PINNED_USER_041_SNAPSHOT')
    guard = positions(chunks, b'LOCALSBGX38_GUARD')
    f_key = positions(chunks, b'BGX38_KEY_CD')
    eps_core = positions(chunks, b'LOCALSBDAI_ATTACK_MODE')
    healing = positions(chunks, b'MO_HealCast')
    team = positions(chunks, b'BGX39_TEAM_CD')
    bgx52 = positions(chunks, b'BGX52_REQ_SLOT')
    bgx66 = positions(chunks, b'BGX66_S_HEAL_SLOT')
    bgx67 = positions(chunks, b'BGX67_EARLY_SLOT')
    if strict_fixture:
        if guard[:7] != list(range(1, 8)):
            raise UnsafeOrUnexpectedBCS('041_INITIAL_F_GUARD_BLOCKS_MISSING')
        if team != list(range(1048, 1058)):
            raise UnsafeOrUnexpectedBCS('041_TAIL_TEAM_GUARD_LAYOUT_DRIFT')
        if not healing or not eps_core:
            raise UnsafeOrUnexpectedBCS('041_EPS_MISSING')
        if bgx52 or bgx66 or bgx67:
            raise UnsafeOrUnexpectedBCS('041_UNEXPECTED_LATER_VERSION_MARKERS')
    return {
       'audit_version':'074',
       'source':'HISTORICAL_041_FILE_2026-11-08_NOT_LIVE_066S',
       'sha256':digest,'size_bytes':len(data),'lossless_blocks':len(chunks),
       'bcs_reassembled_byte_exact':True,
       'f_guard_marker_blocks':guard,
       'f_key_cooldown_blocks':f_key,
       'eps_attack_mode_blocks_count':len(eps_core),
       'eps_attack_mode_first_last':[eps_core[0],eps_core[-1]] if eps_core else [],
       'eps_heal_cast_blocks':healing,
       'bgx39_team_cooldown_blocks':team,
       'later_bxs_present':{'BGX52':bool(bgx52),'BGX66':bool(bgx66),'BGX67':bool(bgx67)},
       'important_limit':'A 041 file cannot establish current 066S action dispatch or live EPS behavior.'
    }


def source_066s_layout() -> dict:
    """Facts transcribed from pinned source BGXAI66S_BCS_PATCH.py, NOT a live verification."""
    return {
       'evidence':'SOURCE_ONLY_FROM_GITHUB_066S_BCS_PATCH_PY',
       'baseline_064_blocks':PIN_064_BLOCKS,
       'existing_061_receiver_zero_based_slice':[1031,1051],
       '066s_insertion_zero_based_index':PIN_066S_SPLICE_ZERO_BASED,
       '066s_inserts_before_existing_one_based_block':PIN_066S_SPLICE_ZERO_BASED+1,
       '066s_inserted_cleanup_and_heal_ward_blocks':PIN_066S_INSERT_BLOCKS,
       'candidate_066s_total_blocks':PIN_066S_TOTAL_BLOCKS,
       'source_preservation_claim':'old blocks byte exact in relative order, checked by source builder, not independently reconstructed from this 041 file',
       'engineering_risk':'EPS scripts have early blocks: inserted BGXAI rules are not globally above all EPS rules; scheduling / ActionListEmpty can delay interception or heal.'
    }


def main() -> None:
    ap=argparse.ArgumentParser(description='Read-only EPS+F guard 041 BCS audit; do not install')
    ap.add_argument('snapshot',type=Path,help='historical 041 BCS file to read; NEVER live 066S required')
    ap.add_argument('--out',type=Path,help='write only to an explicitly selected external report directory')
    args=ap.parse_args()
    result={'snapshot_041':audit_041(args.snapshot.read_bytes()),'066s_patch_source':source_066s_layout()}
    output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        if args.out.resolve() == args.snapshot.resolve():
            raise SystemExit('REPORT_MUST_NOT_REPLACE_SOURCE_BCS')
        if args.out.suffix.lower()!='.json':
            raise SystemExit('REPORT_MUST_BE_JSON')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(output,encoding='utf-8')
    print(output,end='')

if __name__ == '__main__': main()
