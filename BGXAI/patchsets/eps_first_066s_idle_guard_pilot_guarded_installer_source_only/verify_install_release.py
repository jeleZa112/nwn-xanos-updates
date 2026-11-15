"""Static, no-game-write verification of the guarded install source release."""
from __future__ import annotations
import difflib
import hashlib
import json
from pathlib import Path
from BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY import (
    check_source, digest, BCS_SHA, ORIGINAL_SHA, CANDIDATE_SHA, TP2_TEXT,
    LUA, TP2, STAGE
)
HERE=Path(__file__).resolve().parent

def verify():
    manifest=json.loads((HERE/'manifest_install_sha256.json').read_text('utf-8'))
    for name,expected in manifest['files'].items():
        f=HERE/name
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('FILE_SHA_MISMATCH '+name)
    check_source()
    a=(HERE/'M_BX43_066S_VERIFIED_ORIGINAL.lua').read_text('utf-8')
    b=(HERE/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua').read_text('utf-8')
    changes=[o for o in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines()).get_opcodes() if o[0]!='equal']
    if len(changes)!=2:
        raise RuntimeError('MORE_THAN_TWO_SOURCE_REGIONS')
    computed=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='066S_live_exact',tofile='066S_idle_guard_candidate'))
    if computed != (HERE/'066S_idle_guard_minimal.diff').read_text('utf-8'):
        raise RuntimeError('SOURCE_DIFF_DOES_NOT_MATCH')
    if 'COPY ~BGXIDLE/staged/M_BX43.lua~ ~override/M_BX43.lua~' not in TP2_TEXT:
        raise RuntimeError('WEIDU_TP2_LUA_ONLY_EXPECTED')
    lines=[l for l in TP2_TEXT.splitlines() if l.startswith('COPY')]
    if len(lines)!=1 or lines[0] != 'COPY ~BGXIDLE/staged/M_BX43.lua~ ~override/M_BX43.lua~':
        raise RuntimeError('WEIDU_TP2_OTHER_TARGETS')
    print('SAFE_SOURCE_RELEASE VERIFIED',len(manifest['files']),'SHA256, exact two-hunk Lua diff, WeiDU Lua-only TP2; NO_GAME_WRITE')

if __name__=='__main__':verify()
