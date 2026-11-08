#!/usr/bin/env python3
"""BGXAI 042: offline, READ-ONLY compiled BGEE BCS inspector.

Recognizes the first action of EACH RESPONSE. The original 042 v1 scanner
only matched actions after an 'AC\\n' delimiter, missing '<weight>AC\\n'.
This script does not modify the input game file and cannot install anything.
The optional in-memory preview is NOT a validated game patch.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

EXPECTED_SHA256 = '86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
EXPECTED_BYTES = 2229760
EXPECTED_BLOCKS = 1057
EXPECTED_ATTACK_BRANCHES = [1032, 1045]
EXPECTED_GUARD_BRANCHES = list(range(1047,1058))
BCS_BLOCK = re.compile(r'(?s)CR\nCO\n(.*?)\nRS\n(.*?)\nRS\nCR(?=\n(?:CR|SC))')
BCS_ACTION = re.compile(r'(?:RE\n-?\d+AC\n|AC\n)(-?\d+)OB\n')
BCS_TRIGGER = re.compile(r'(?:^|\n)TR\n(-?\d+) ([^\n]+)')
ACTION_NAMES = {0:'NoAction',3:'Attack',30:'SetGlobal',31:'Spell',36:'Continue',
                86:'SetInterrupt',87:'ProtectObject',105:'AttackOneRound',
                134:'AttackReevaluate',115:'SetGlobalTimer',160:'ApplySpellRES'}
ID_ACTION_LIST_EMPTY=16427
GUARD_FLAG='BGX38_GUARD'
ATTACK_TOGGLE='BDAI_DISABLE_ATTACK'
ATTACK_MODE='BDAI_ATTACK_MODE'

# Purely hypothetical condition: Global("BGX38_GUARD", "LOCALS", 0).
# Constructed from the user's *own compiled* guard flag representation.
# Inserting it into two Attack blocks is an offline design preview ONLY.
GUARD_OFF_TRIGGER = ('TR\n16399 0 0 0 0 "LOCALSBGX38_GUARD" "" OB\n'
                    '0 0 0 0 0 0 0 0 0 0 0 0 ""OB\nTR\n')


def parse(data: bytes):
    if not 100 < len(data) < 8_000_000 or not data.startswith(b'SC\n') or not data.endswith(b'\nSC\n'):
        raise ValueError('Expected standalone compiled textual BCS with SC boundaries')
    src = data.decode('latin1')
    blocks=[]
    for i, m in enumerate(BCS_BLOCK.finditer(src), 1):
        cond, action_body = m.group(1), m.group(2)
        actions = [int(v) for v in BCS_ACTION.findall(action_body)]
        trigs = [(int(n), t) for n,t in BCS_TRIGGER.findall(cond)]
        if not actions:
            raise ValueError(f'BCS block {i}: response has no recognized actions')
        blocks.append({'number':i,'start':m.start(),'end':m.end(),
            'condition':cond,'body':action_body,
            'action_ids':actions,
            'action_names':[ACTION_NAMES.get(a, f'Action{a}') for a in actions],
            'triggers':trigs,
            'action_list_empty':any(n==ID_ACTION_LIST_EMPTY and t.startswith('0 0') for n,t in trigs),
            'guard_enabled':GUARD_FLAG in cond,
            'attack_mode_setting':ATTACK_MODE in cond,
            'disable_attack_setting':ATTACK_TOGGLE in cond})
    if not blocks or src.count('CR\nCO\n')!=len(blocks):
        raise ValueError('Incomplete or unexpectedly nested BCS blocks')
    return blocks


def inspect(data:bytes):
    blocks=parse(data)
    all_counts=collections.Counter(a for b in blocks for a in b['action_ids'])
    att=[b for b in blocks if 3 in b['action_ids']]
    prot=[b for b in blocks if 87 in b['action_ids']]
    mode=[b for b in blocks if b['attack_mode_setting']]
    guard=[b for b in blocks if b['guard_enabled']]
    result={
        'sha256':hashlib.sha256(data).hexdigest(),
        'bytes':len(data),'blocks':len(blocks),'total_actions':sum(all_counts.values()),
        'attack_block_numbers':[b['number'] for b in att],
        'attack_conditions':[{ 'number':b['number'],'action_ids':b['action_ids'],
            'action_list_empty':b['action_list_empty'],
            'has_disable_attack_toggle':b['disable_attack_setting'],
            'has_attack_mode_setting':b['attack_mode_setting'],
            'has_guard_gate':b['guard_enabled']} for b in att],
        'protect_block_numbers':[b['number'] for b in prot],
        'protect_conditions':[{ 'number':b['number'],'action_list_empty':b['action_list_empty'],
            'guard_enabled':b['guard_enabled']} for b in prot],
        'attack_mode_setting_blocks':len(mode),
        'attack_mode_actions':dict(collections.Counter(a for b in mode for a in b['action_ids'])),
        'guard_flag_blocks':len(guard),
        'guard_action_blocks':[b['number'] for b in guard],
        'global_actions':dict(sorted((str(k),v) for k,v in all_counts.items())),
        'protect_branches_after_attack':bool(att and prot and max(b['number'] for b in att)<min(b['number'] for b in prot)),
        'read_only':True,
        'interpretation':'Compiled rule inventory, not proof of runtime choices; no installation.'}
    return result


def strict_lock(result):
    comparisons=[('sha256',EXPECTED_SHA256),('bytes',EXPECTED_BYTES),('blocks',EXPECTED_BLOCKS),
                 ('attack_block_numbers',EXPECTED_ATTACK_BRANCHES),
                 ('protect_block_numbers',EXPECTED_GUARD_BRANCHES)]
    for k,expected in comparisons:
        if result[k]!=expected:
            raise ValueError(f'Wrong target BCS: {k}={result[k]!r} != {expected!r}; abort preview')
    if not all(b['action_list_empty'] and b['has_disable_attack_toggle'] and not b['has_guard_gate'] for b in result['attack_conditions']):
        raise ValueError('Unexpected normal attack conditions; abort preview')
    if not all(b['action_list_empty'] and b['guard_enabled'] for b in result['protect_conditions']):
        raise ValueError('Unexpected protect conditions; abort preview')


def in_memory_preview(data:bytes):
    """ONLY DEMONSTRATES syntactic branch modification; no output file; no game write."""
    result=inspect(data)
    strict_lock(result)
    blocks=parse(data)
    original=data.decode('latin1')
    changes={}
    for b in blocks:
        if b['number'] in EXPECTED_ATTACK_BRANCHES:
            src=original[b['start']:b['end']]
            prefix='CR\nCO\n'
            if not src.startswith(prefix) or GUARD_FLAG in src:
                raise ValueError('Branch already gated or format changed')
            # Add an AND condition BEFORE original triggers; do not change action targets.
            changes[b['number']]=prefix+GUARD_OFF_TRIGGER+src[len(prefix):]
    for i in EXPECTED_ATTACK_BRANCHES:
        if i not in changes:raise ValueError('Missing expected attack branch')
    # Work from right to left to preserve original index spans.
    staged=original
    for b in reversed(blocks):
        if b['number'] in changes:
            staged=staged[:b['start']]+changes[b['number']]+staged[b['end']:]
    hypothetical=staged.encode('latin1')
    new=inspect(hypothetical)
    for orig,patched in zip(blocks,parse(hypothetical)):
        if orig['number'] in EXPECTED_ATTACK_BRANCHES:
            if not patched['guard_enabled'] or patched['action_ids']!=orig['action_ids']:
                raise ValueError('Failed in-memory gate review')
        else:
            if (orig['condition'],orig['body'])!=(patched['condition'],patched['body']):
                raise ValueError('Non-target branch changed in preview')
    if new['blocks']!=EXPECTED_BLOCKS or new['global_actions']!=result['global_actions']:
        raise ValueError('BCS action topology changed in preview')
    return {'preview_only':True,'input_sha256':result['sha256'],
            'simulated_sha256':new['sha256'],
            'simulated_changed_blocks':EXPECTED_ATTACK_BRANCHES,
            'changed_action_ids':False,'changed_non_target_blocks':False,
            'preview_bytes':len(hypothetical),
            'not_verified':'Runtime, WeiDU compilation, manual commands, existing in-flight Attack, and bard behavior.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('bcs',type=Path,help='Read-only path to current override/BDDEFAI.BCS')
    ap.add_argument('--preview',action='store_true',help='Generate in-memory structural preview; NEVER writes a patched BCS')
    ap.add_argument('--json',action='store_true',help='Print machine-readable report')
    args=ap.parse_args()
    data=args.bcs.read_bytes()
    result=inspect(data)
    if args.preview:result['simulation']=in_memory_preview(data)
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2));return
    print('BGXAI 042 — detailed offline READ-ONLY audit')
    print('sha256',result['sha256'],'bytes',result['bytes'],'blocks',result['blocks'])
    print('Attack actions: blocks',result['attack_block_numbers'])
    print('ProtectObject actions: blocks',result['protect_block_numbers'])
    print('BDAI_ATTACK_MODE (setting) branches',result['attack_mode_setting_blocks'])
    print('Actions in these setting branches',result['attack_mode_actions'])
    print('Guard setting blocks',result['guard_flag_blocks'])
    print('Protection blocks are all later than the normal-attack branches:',result['protect_branches_after_attack'])
    print('Guards ActionListEmpty:',[b['action_list_empty'] for b in result['protect_conditions']])
    print('Attack ActionListEmpty:',[b['action_list_empty'] for b in result['attack_conditions']])
    if args.preview:print('NOT AN INSTALL — IN-MEMORY PREVIEW',result['simulation'])
    print('No game files changed. Detailed results are NOT proof of gameplay.')

if __name__=='__main__':main()
