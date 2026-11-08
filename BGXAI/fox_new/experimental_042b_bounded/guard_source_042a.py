#!/usr/bin/env python3
"""BGXAI 042 experimental SOURCE ONLY: offline, no game writes or installation.

With strict SHA256 and structural invariants, reorders 11 existing guard
blocks ahead of two EPS normal Attack blocks; leaves each compiled CR block
byte-for-byte unchanged. This does NOT interrupt ongoing Attack actions.
Generated preview must NOT be copied to EET or installed directly.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

PIN_SHA = "86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5"
PIN_SIZE = 2_229_760
PIN_BLOCKS = 1057
ATTACK_IDS = (1032, 1045)
GUARD_IDS = tuple(range(1047,1058))
INSERT_BEFORE = 1032
START_RE = re.compile(rb'(?:^|\n)(CR\nCO\n)')
BLOCK_PATTERN = re.compile(rb'(?s)CR\nCO\n(.*?)\nRS\n(.*?)\nRS\nCR(?=\n(?:CR|SC))')
ACTION = re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def segments(raw):
    if not raw.startswith(b'SC\n'):
        raise ValueError('BCS must start with SC\\n')
    # Every block starts exactly at the CR after a newline.
    pos = [m.start(1) for m in START_RE.finditer(raw)]
    if len(pos) != PIN_BLOCKS or pos[0] != 3:
        raise ValueError('BCS block boundary inventory changed')
    blocks = [raw[a:b] for a,b in zip(pos, pos[1:]+[len(raw)])]
    if not all(x.startswith(b'CR\nCO\n') for x in blocks):
        raise ValueError('Unexpected BCS block boundary')
    if raw[:3] + b''.join(blocks) != raw:
        raise AssertionError('Lossless parse failed')
    return blocks


def action_ids(block):
    # The original 042 scanner counts exact action slots in compiled BCS.
    m = BLOCK_PATTERN.match(block+b'CR\n')
    if not m:
        # For simpler exact representation, split at the first RS delimiter
        a = block.find(b'\nRS\n')
        if a < 0: raise ValueError('Missing RS')
        body = block[a+4:]
    else:
        body=m.group(2)
    return [int(v) for v in ACTION.findall(body)]


def inspect_source(raw):
    if len(raw)!=PIN_SIZE or sha(raw)!=PIN_SHA:
        raise ValueError('HASH GATE: wrong installed EPS script; no preview generated')
    blocks=segments(raw)
    for i in ATTACK_IDS:
        b=blocks[i-1]
        if action_ids(b) != [3] or b'LOCALSBDAI_DISABLE_ATTACK' not in b or b'16427 ' not in b:
            raise ValueError(f'Unexpected EPS Attack block {i}')
    for i in GUARD_IDS:
        b=blocks[i-1]
        if action_ids(b) != [115,87] or b'LOCALSBGX38_GUARD' not in b or b'16427 ' not in b:
            raise ValueError(f'Unexpected BGX guard block {i}')
    if b'LOCALSBGX38_GUARD' not in blocks[0]:
        raise ValueError('F/041 mode control shifted')
    if len(BLOCK_PATTERN.findall(raw)) != PIN_BLOCKS:
        raise ValueError('Compiled CR structure is not complete')
    return blocks


def generate(raw):
    blocks=inspect_source(raw)
    guarded=[blocks[i-1] for i in GUARD_IDS]
    remain=[b for i,b in enumerate(blocks,1) if i not in GUARD_IDS]
    # Move the eleven blocks in their exact original order before original 1032.
    new=remain[:INSERT_BEFORE-1]+guarded+remain[INSERT_BEFORE-1:]
    assert len(new)==len(blocks)
    candidate=b'SC\n'+b''.join(new)
    if len(candidate)!=len(raw):raise AssertionError('Byte-count regression')
    if Counter(blocks)!=Counter(segments(candidate)):
        raise AssertionError('Any modified condition/action is forbidden')
    if candidate[:3]!=raw[:3]:raise AssertionError('Header regression')
    if new[:INSERT_BEFORE-1]!=blocks[:INSERT_BEFORE-1]:
        raise AssertionError('Earlier EPS blocks changed')
    guard_positions=[new.index(blocks[i-1])+1 for i in GUARD_IDS]
    attack_positions=[new.index(blocks[i-1])+1 for i in ATTACK_IDS]
    assert guard_positions==list(range(1032,1043))
    assert attack_positions==[1043, 1056]
    assert all(b'16427 ' in new[i-1] for i in guard_positions)
    return candidate,{
      'source_sha256':sha(raw),'source_bytes':len(raw),
      'preview_sha256':sha(candidate),'preview_bytes':len(candidate),
      'block_count':len(blocks),'moved_guard_old':list(GUARD_IDS),
      'moved_guard_new':guard_positions,'eps_attack_old':list(ATTACK_IDS),
      'eps_attack_new':attack_positions,
      'unchanged_block_bytes':True,
      'scope':'OFFLINE ONLY; NOT INSTALLED OR GAME/WEIDU-VERIFIED',
      'known_gap':'Existing continuous Attack and manual actions are not interrupted; priority only when ActionListEmpty().',
      'no_game_write':True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--preview',type=Path,help='A file OUTSIDE game root. Leave unset for hash+offline audit only.')
    p.add_argument('--json-report',type=Path)
    args=p.parse_args()
    raw=args.source.read_bytes()
    preview,report=generate(raw)
    if args.preview:
        if args.preview.resolve()==args.source.resolve() or 'override' in [x.lower() for x in args.preview.parts]:
            raise ValueError('Refusing overwrite or game override path')
        args.preview.write_bytes(preview)
    if args.json_report:args.json_report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()