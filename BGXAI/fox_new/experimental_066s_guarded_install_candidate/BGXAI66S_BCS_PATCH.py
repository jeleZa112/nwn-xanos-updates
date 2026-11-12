#!/usr/bin/env python3
"""066S: verified 064 BCS -> 066S BCS; pure splice + isolated real-game IDS compiler.

Never changes game files. Uses exact SHA-pinned 064 BCS, preserves every old
compiled CR/CO trigger and action block byte-for-byte and in the same order.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import hashlib, re, shutil, subprocess, tempfile

PIN_064_BCS='db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b'
PIN_064_BLOCKS=1077
PIN_FRAGMENT_BAF='c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae'
PIN_FRAGMENT_BLOCKS=11
# The installed 064 retains the 061 receiver: 20 BCS blocks, NOT the earlier
# 056 eight-block receiver. Real EET 061 preflight on user PC proved:
# old 060 BCS 1071 - 14 receiver blocks + 20 BGX61 blocks = 1077.
# 064 modifies Lua ONLY and leaves this SHA-pinned 1077-block BCS untouched.
# Insert new 066S support rules after the 20 BGX61 receiver blocks, before
# original 042B/EPS rule bodies. Every pre-existing block remains byte-identical.
OLD_RECEIVER_START=1031
OLD_RECEIVER_BLOCKS=20
SPLICE_AT=OLD_RECEIVER_START+OLD_RECEIVER_BLOCKS
# Exact real 061 receiver: 2 cleanup, 6 immediate attacks, 6 approaches,
# 6 fallback guards. Never silently downgrade to the obsolete 056 layout.
EXISTING_061_ACTIONS=([[30,36],[30,36]]+
   [[30,115,30,30,134]]*6+
   [[115,115,30,30,22]]*6+
   [[30,115,30,30,87]]*6)
START=re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACTIONS=re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def actions(b:bytes):return [int(x) for x in ACTIONS.findall(b)]

def segment(raw:bytes,count:int)->list[bytes]:
    if not raw.startswith(b'SC\n'):raise ValueError('BCS_HEADER_NOT_SC')
    starts=[m.start(1) for m in START.finditer(raw)]
    if len(starts)!=count or starts[0]!=3:
        raise ValueError(f'BCS_BLOCK_COUNT_{len(starts)}_EXPECTED_{count}')
    chunks=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if any(not b.startswith(b'CR\nCO\n') or b.count(b'\nRS\n')<2 for b in chunks):
        raise ValueError('BCS_BLOCK_BOUNDARY_INVALID')
    if any(not b.endswith(b'CR\n') for b in chunks[:-1]):
        raise ValueError('BCS_NONFINAL_CR_INVALID')
    if not chunks[-1].endswith(b'CR\nSC\n') or raw.count(b'\nSC\n')!=1:
        raise ValueError('BCS_FOOTER_INVALID')
    if b'SC\n'+b''.join(chunks)!=raw:raise ValueError('BCS_NONLOSSLESS_SEGMENT')
    return chunks

def prove_original(raw:bytes)->list[bytes]:
    if sha(raw)!=PIN_064_BCS:raise ValueError('064_BCS_SHA_MISMATCH')
    blocks=segment(raw,PIN_064_BLOCKS)
    guard=blocks[OLD_RECEIVER_START:SPLICE_AT]
    if len(guard)!=OLD_RECEIVER_BLOCKS or [actions(b) for b in guard]!=EXISTING_061_ACTIONS:
        raise ValueError('064_061_RECEIVER_ACTION_LAYOUT_DRIFT')
    if any(b'BGX52_REQ_SLOT' not in b for b in guard):
        raise ValueError('064_061_RECEIVER_REQUEST_MARKER_MISSING')
    if any(b'BGX61_LAST_BRANCH' not in b for b in guard[2:]):
        raise ValueError('064_061_RECEIVER_BRANCH_MARKER_MISSING')
    return blocks

def prove_fragment(raw:bytes)->list[bytes]:
    blocks=segment(raw,PIN_FRAGMENT_BLOCKS)
    acts=[a for b in blocks for a in actions(b)]
    expected=[30,36]*4+[30,115,31]*7
    if acts!=expected:raise ValueError('066S_RECEIVER_ACTION_LAYOUT_DRIFT:'+repr(acts))
    for i,b in enumerate(blocks):
        if i<4 and b'LOCALSBGX66_S_' not in b:raise ValueError('066S_CLEANUP_MARKER')
    return blocks

def splice(original:bytes,compiled:bytes):
    before=prove_original(original)
    inserted=list(prove_fragment(compiled))
    if not inserted[-1].endswith(b'CR\nSC\n'):
        raise ValueError('066S_INSERT_MISSING_FINAL_FOOTER')
    inserted[-1]=inserted[-1][:-3]   # remove ONLY the fragment's SC\n
    new=before[:SPLICE_AT]+inserted+before[SPLICE_AT:]
    final=b'SC\n'+b''.join(new)
    blocks=segment(final,PIN_064_BLOCKS+PIN_FRAGMENT_BLOCKS)
    if blocks[:SPLICE_AT]!=before[:SPLICE_AT] or blocks[SPLICE_AT+PIN_FRAGMENT_BLOCKS:]!=before[SPLICE_AT:]:
        raise AssertionError('OLD_BCS_BLOCK_DRIFT')
    if blocks[SPLICE_AT:SPLICE_AT+PIN_FRAGMENT_BLOCKS]!=inserted:
        raise AssertionError('066S_INSERTED_BCS_DRIFT')
    if Counter(blocks)!=Counter(before+inserted):raise AssertionError('BLOCKS_NOT_PRESERVED')
    if sha(final)==sha(original):raise AssertionError('NO_BCS_CHANGE')
    return final,{'status':'BCS_PATCH_VERIFIED','source_sha256':sha(original),
      'compiled_receiver_sha256':sha(compiled),'final_sha256':sha(final),
      'old_blocks':len(before),'new_blocks':len(inserted),'total_blocks':len(blocks),
      'existing_bcs_blocks_byte_exact':True,'insertion_before_old_block':SPLICE_AT+1}


def verify_installed(candidate:bytes)->dict:
    """Prove removal of 066S restores the EXACT pinned 064 BCS bytes."""
    blocks=segment(candidate,PIN_064_BLOCKS+PIN_FRAGMENT_BLOCKS)
    part=list(blocks[SPLICE_AT:SPLICE_AT+PIN_FRAGMENT_BLOCKS])
    if not part or not part[-1].endswith(b'CR\n'):
        raise ValueError('066S_FRAGMENT_BOUNDS_INVALID')
    part[-1]+=b'SC\n'
    prove_fragment(b'SC\n'+b''.join(part))
    original=b'SC\n'+b''.join(blocks[:SPLICE_AT]+blocks[SPLICE_AT+PIN_FRAGMENT_BLOCKS:])
    prove_original(original)
    return {'old_bcs_restored_sha256':sha(original),
        'installed_bcs_sha256':sha(candidate),'legacy_blocks_preserved':PIN_064_BLOCKS,
        '066s_inserted_blocks_verified':PIN_FRAGMENT_BLOCKS}

def compile_real_game(game:Path,baf:Path,weidu:Path,tlk:Path,*,runner=subprocess.run):
    """Offline compile using live EET IDS; NEVER executes a TP2 or writes to game."""
    game=game.resolve(strict=True)
    baf=baf.resolve(strict=True)
    if sha(baf.read_bytes())!=PIN_FRAGMENT_BAF:raise ValueError('066S_BAF_SHA_MISMATCH')
    if weidu.resolve(strict=True).parent!=game:raise ValueError('WEIDU_NOT_GAME_ROOT')
    if game not in tlk.resolve(strict=True).parents:raise ValueError('TLK_NOT_FROM_GAME')
    with tempfile.TemporaryDirectory(prefix='BGXAI66S_READONLY_COMPILE_') as t:
        root=Path(t)
        tool=root/'weidu.exe'
        shutil.copy2(weidu,tool)
        if sha(tool.read_bytes())!=sha(weidu.read_bytes()):raise ValueError('WEIDU_TEMP_COPY_HASH')
        src=root/'BX66SCHK.baf';src.write_bytes(baf.read_bytes())
        out=root/'out';out.mkdir()
        # Only output paths are under the isolated temp folder; 
        # game is READ only while obtaining the installed IDS.
        args=[str(tool),'--no-auto-tp2','--no-exit-pause','--noautoupdate',
             '--game',str(game),'--tlkin',str(tlk),'--script-style','BG2',
             '--out',str(out),str(src)]
        proc=runner(args,cwd=str(root),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
           stderr=subprocess.PIPE,timeout=40,check=False,text=True,encoding='utf-8',errors='replace')
        msg=(proc.stdout or '')+'\n'+(proc.stderr or '')
        if proc.returncode or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',msg):
            raise ValueError('REAL_IDS_COMPILE_FAILED:'+msg[-1800:])
        candidates=list(out.rglob('BX66SCHK.bcs'))
        if len(candidates)!=1:raise ValueError('REAL_IDS_COMPILE_OUTPUT_MISSING')
        data=candidates[0].read_bytes()
        prove_fragment(data)
        return data
