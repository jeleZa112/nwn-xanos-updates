#!/usr/bin/env python3
"""BGXAI 056: strict hash-pinned source-only BCS compiler and exact insertion.

The 8 BAF blocks are compiled with the game's real IDS via a temporary WeiDU 251
executable. Insert at block 1032, after the existing F toggle and immediately
before 042B guard rules. Original 1057 blocks remain byte-identical and in order.
No game writes occur here. Installation is separately explicit via WeiDU.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import hashlib, re, shutil, subprocess, tempfile

PIN_BCS = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
PIN_BCS_BYTES = 2229764
PIN_BLOCKS = 1057
LEGACY_FOOTER_BLOCK = 1042  # 042B moved the original FINAL block to here WITH SC footer.
# The exact 042B BCS is SHA-pinned. Its internal SC marker is an old 042B
# construction defect, not an alternate WeiDU syntax to accept generally.
INSERT_INDEX = 1031 # Python zero-index (before 1-based block 1032)
SOURCE_BAF = 'BGX56_RECEIVER.baf'
TEMP_BAF = 'BX56CHCK.baf'
BCS_IN_GAME = 'override/BDDEFAI.BCS'
BLOCK_START = re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACTIONS = re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
MAX_SECONDS = 25

def sha(raw:bytes): return hashlib.sha256(raw).hexdigest()

def segment(raw:bytes,expected:int,*,legacy_042b=False):
    if not raw.startswith(b'SC\n'): raise ValueError('BCS_NOT_SC_HEADER')
    starts=[m.start(1) for m in BLOCK_START.finditer(raw)]
    if len(starts)!=expected or starts[0]!=3:
        raise ValueError(f'BLOCK_COUNT_EXPECTED_{expected}_GOT_{len(starts)}')
    blocks=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if not all(b.startswith(b'CR\nCO\n') and b.count(b'\nRS\n')>=2 for b in blocks):
        raise ValueError('BCS_UNEXPECTED_CR_OR_RS_BOUNDARY')
    if legacy_042b:
        # The original 042A / 042B block mover relocated block #1057 to
        # position 1042, bringing its terminal SC\n along. Other original
        # blocks, including the now-last block, were preserved byte-for-byte.
        # This exceptional layout is allowed ONLY for the exact SHA-pinned
        # existing 042B script, never for newly compiled / patched output.
        if not blocks[LEGACY_FOOTER_BLOCK-1].endswith(b'CR\nSC\n'):
            raise ValueError('042B_EXPECTED_MOVED_SC_AFTER_1042_MISSING')
        if not all(b.endswith(b'CR\n') for i,b in enumerate(blocks[:-1],1)
                   if i!=LEGACY_FOOTER_BLOCK):
            raise ValueError('042B_OTHER_INTERNAL_BLOCK_INVALID')
        if not blocks[-1].endswith(b'CR\n') or blocks[-1].endswith(b'CR\nSC\n'):
            raise ValueError('042B_UNEXPECTED_LAST_BLOCK_TRAILER')
        if raw.count(b'\nSC\n')!=1:
            raise ValueError('042B_DUPLICATE_OR_MISSING_SC_TRAILER')
    else:
        if not all(b.endswith(b'CR\n') for b in blocks[:-1]):
            raise ValueError('BCS_INTERNAL_BLOCK_NO_CR_LF')
        if not blocks[-1].endswith(b'CR\nSC\n'):
            raise ValueError('BCS_MISSING_FINAL_SC_FOOTER')
        if raw.count(b'\nSC\n')!=1:
            raise ValueError('BCS_DUPLICATE_SC_FOOTER')
    if b'SC\n'+b''.join(blocks)!=raw:raise AssertionError('BCS_LOSSLESS_ROUNDTRIP')
    return blocks


def canonicalize_legacy_042b(blocks:list[bytes])->list[bytes]:
    # Re-home ONLY the displaced 3-byte terminal SC\n marker; every
    # original IF/THEN block, its triggers, actions and order are unchanged.
    if len(blocks)!=PIN_BLOCKS:raise ValueError('042B_BLOCK_COUNT_MISMATCH')
    out=list(blocks)
    moved=out[LEGACY_FOOTER_BLOCK-1]
    if not moved.endswith(b'CR\nSC\n') or not out[-1].endswith(b'CR\n'):
        raise ValueError('042B_FOOTER_RELOCATION_PRECONDITION_FAILED')
    out[LEGACY_FOOTER_BLOCK-1]=moved[:-3]
    out[-1]=out[-1]+b'SC\n'
    assert out[LEGACY_FOOTER_BLOCK-1]==moved[:-3]
    assert out[-1]==blocks[-1]+b'SC\n'
    if any(out[i]!=blocks[i] for i in range(PIN_BLOCKS)
           if i not in (LEGACY_FOOTER_BLOCK-1,PIN_BLOCKS-1)):
        raise AssertionError('042B_UNRELATED_BLOCK_CHANGED')
    return out

def actions(block:bytes):return [int(v) for v in ACTIONS.findall(block)]

def verify_old(raw:bytes):
    if len(raw)!=PIN_BCS_BYTES or sha(raw)!=PIN_BCS:raise ValueError('LIVE_042B_HASH_MISMATCH')
    blocks=segment(raw,PIN_BLOCKS,legacy_042b=True)
    for i in range(1031,1042):
        if b'LOCALSBGX38_GUARD' not in blocks[i] or actions(blocks[i])!=[115,87]:
            raise ValueError(f'EXISTING_GUARD_BLOCK_{i+1}_CHANGED')
    if [actions(blocks[i]) for i in (1042,1055)]!=[[105],[105]]:
        # 042B uses EPS AttackOneRound() as action ID 105 in this verified BCS.
        raise ValueError('EXISTING_EPS_ONE_ROUND_ATTACK_CHANGED')
    if b'LOCALSBGX38_GUARD' not in blocks[0]:raise ValueError('ORIGINAL_F_TOGGLE_MISSING')
    return blocks

def verify_insert(raw:bytes):
    blocks=segment(raw,8)
    want=[30,36,30,36]+[30,115,87]*6
    got=[a for b in blocks for a in actions(b)]
    if got!=want:raise ValueError('NEW_RECEIVER_ACTION_IDS_UNEXPECTED_'+str(got))
    return blocks

def combine(old:bytes,insert:bytes,*,strict:bool=True):
    if strict:legacy=verify_old(old)
    else:legacy=segment(old,PIN_BLOCKS,legacy_042b=True)
    before=canonicalize_legacy_042b(legacy)
    new=verify_insert(insert)
    # Insert only CR blocks, never the standalone SC footer from the
    # separately compiled BCS. The existing 042B mislocated SC is first
    # relocated to the genuine last block, preserving 1057 rule bodies.
    new = list(new)
    if not new[-1].endswith(b'CR\nSC\n'):
        raise ValueError('INSERTED_BCS_FINAL_SC_MISSING')
    new[-1]=new[-1][:-3] # remove ONLY terminal SC\n
    candidate=b'SC\n'+b''.join(before[:INSERT_INDEX]+new+before[INSERT_INDEX:])
    merged=segment(candidate,PIN_BLOCKS+8)
    if merged[:INSERT_INDEX]!=before[:INSERT_INDEX]:raise AssertionError('EARLIER_F_OR_EPS_BLOCK_CHANGED')
    if merged[INSERT_INDEX:INSERT_INDEX+8]!=new:raise AssertionError('RECEIVER_INSERTION_NOT_EXACT')
    if merged[INSERT_INDEX+8:]!=before[INSERT_INDEX:]:raise AssertionError('EXISTING_EPS_BLOCK_CHANGED')
    if Counter(merged)!=Counter(before+new):raise AssertionError('BLOCK_MULTISETS_DIFFER')
    if len(candidate)!=len(old)+len(insert)-6:raise AssertionError('SIZE_MISMATCH')
    if candidate.count(b'\nSC\n')!=1 or not candidate.endswith(b'CR\nSC\n'):
        raise AssertionError('PATCHED_TRAILER_INTEGRITY_FAILURE')
    if merged[LEGACY_FOOTER_BLOCK-1+len(new)]!=legacy[LEGACY_FOOTER_BLOCK-1][:-3]:
        raise AssertionError('LEGACY_BLOCK_1042_NOT_NORMALIZED')
    return candidate,{'old_sha':sha(old),'new_receiver_sha':sha(insert),
                      'patched_sha':sha(candidate),'old_blocks':len(before),
                      'inserted_blocks':len(new),'total_blocks':len(merged),
                      'insert_before_original_block':INSERT_INDEX+1,
                      'compiled_fragment_internal_SC_removed':True,
                      'existing_rule_bodies_byte_identical':True,
                      '042b_displaced_SC_footer_relocated':True,
                      'legacy_footer_original_block':LEGACY_FOOTER_BLOCK,
                      'legacy_sha256':sha(old),
                      'original_F_toggle_precedes_receiver':True,
                      'original_guard_follows_receiver':True}

def compile_only(game:Path,baf:Path,weidu_source:Path,tlk:Path,*,runner=subprocess.run):
    """Invoke a temporary weidu.exe with no TP2 or stdin, 25 s max; no game writes."""
    game=game.resolve(strict=True);baf=baf.resolve(strict=True)
    weidu_source=weidu_source.resolve(strict=True);tlk=tlk.resolve(strict=True)
    if sha(baf.read_bytes())!=BAF_PIN:raise ValueError('BAF_HASH_MISMATCH')
    if weidu_source.parent!=game or not weidu_source.is_file():raise ValueError('WEIDU_PATH_UNEXPECTED')
    if not tlk.is_file() or game not in tlk.parents:raise ValueError('TLK_PATH_UNEXPECTED')
    with tempfile.TemporaryDirectory(prefix='BGXAI56_BCS_') as temp:
        tmp=Path(temp);exe=tmp/('weidu.exe' if weidu_source.suffix.lower()=='.exe' else 'weidu')
        shutil.copy2(weidu_source,exe)
        if sha(exe.read_bytes())!=sha(weidu_source.read_bytes()):raise RuntimeError('WEIDU_TEMP_COPY_HASH_MISMATCH')
        src=tmp/TEMP_BAF;src.write_bytes(baf.read_bytes())
        out=tmp/'out';out.mkdir()
        cmd=[str(exe),'--no-auto-tp2','--no-exit-pause','--noautoupdate',
             '--game',str(game),'--tlkin',str(tlk),'--script-style','BG2',
             '--out',str(out),str(src)]
        try:proc=runner(cmd,cwd=str(game),stdin=subprocess.DEVNULL,capture_output=True,
                        text=True,timeout=MAX_SECONDS,check=False,encoding='utf-8',errors='replace')
        except subprocess.TimeoutExpired as exc:raise RuntimeError('WEIDU_COMPILE_TIMEOUT_25S') from exc
        output=(proc.stdout or '')+'\n'+(proc.stderr or '')
        if proc.returncode!=0 or re.search(r'(?im)^\s*(FATAL ERROR:|ERROR:)',output):
            raise RuntimeError('WEIDU_COMPILE_FAILED: '+output[-600:])
        candidates=list(out.rglob('BX56CHCK.bcs'))
        if len(candidates)!=1:raise RuntimeError('WEIDU_COMPILE_NO_EXACT_OUTPUT')
        result=candidates[0].read_bytes();verify_insert(result)
        return result

BAF_PIN='b8309fdfd903fb6a0c50cd14fb687b862ac06fb8bbd79a26c9324fd0908b5d88'
