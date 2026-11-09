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
INSERT_INDEX = 1031 # Python zero-index (before 1-based block 1032)
SOURCE_BAF = 'BGX56_RECEIVER.baf'
TEMP_BAF = 'BX56CHCK.baf'
BCS_IN_GAME = 'override/BDDEFAI.BCS'
BLOCK_START = re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACTIONS = re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
MAX_SECONDS = 25

def sha(raw:bytes): return hashlib.sha256(raw).hexdigest()

def segment(raw:bytes,expected:int):
    if not raw.startswith(b'SC\n'): raise ValueError('BCS_NOT_SC_HEADER')
    starts=[m.start(1) for m in BLOCK_START.finditer(raw)]
    if len(starts)!=expected or starts[0]!=3:raise ValueError(f'BLOCK_COUNT_EXPECTED_{expected}_GOT_{len(starts)}')
    blocks=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    # A compiled BCS has a ONE-TIME SC\n footer. The final CR block includes
    # this footer in a lossless segment. When inserting, remove the extra footer
    # from the inserted BCS but preserve the original script footer unchanged.
    if not all(b.startswith(b'CR\nCO\n') and b.count(b'\nRS\n')>=2 for b in blocks):
        raise ValueError('BCS_UNEXPECTED_CR_OR_RS_BOUNDARY')
    if not all(b.endswith(b'CR\n') for b in blocks[:-1]):
        raise ValueError('BCS_INTERNAL_BLOCK_NO_CR_LF')
    if not blocks[-1].endswith(b'CR\nSC\n'):
        raise ValueError('BCS_MISSING_FINAL_SC_FOOTER')
    if b'SC\n'+b''.join(blocks)!=raw:raise AssertionError('BCS_LOSSLESS_ROUNDTRIP')
    return blocks

def actions(block:bytes):return [int(v) for v in ACTIONS.findall(block)]

def verify_old(raw:bytes):
    if len(raw)!=PIN_BCS_BYTES or sha(raw)!=PIN_BCS:raise ValueError('LIVE_042B_HASH_MISMATCH')
    blocks=segment(raw,PIN_BLOCKS)
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
    if strict:before=verify_old(old)
    else:before=segment(old,PIN_BLOCKS)
    new=verify_insert(insert)
    # Insert only the CR blocks, not the standalone SC trailer from the
    # separately compiled BCS; the original live BCS retains its own footer.
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
    return candidate,{'old_sha':sha(old),'new_receiver_sha':sha(insert),
                      'patched_sha':sha(candidate),'old_blocks':len(before),
                      'inserted_blocks':len(new),'total_blocks':len(merged),
                      'insert_before_original_block':INSERT_INDEX+1,
                      'compiled_fragment_internal_SC_removed':True,
                      'existing_bcs_blocks_byte_identical':True,
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
