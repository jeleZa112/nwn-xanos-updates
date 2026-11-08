#!/usr/bin/env python3
"""BGXAI 042B source-only off-game bytecode preview, NEVER an installer.

For the single EXACT live EPS 18.4 file: 11 original Guard blocks before
2 normal EPS attacks, and replace only those two Attack action ids with
AttackOneRound. No queue clearing. No manual action/ability alteration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from guard_source_042a import generate as candidate_a,segments,action_ids,PIN_SHA,sha,GUARD_IDS,ATTACK_IDS

SOURCE_SIZE=2_229_760
ORIGINAL_ATTACK_NEW_IDS=(1043,1056)


def to_bounded_attack(block:bytes)->bytes:
    if action_ids(block)!=[3]:
        raise ValueError('Expected exactly one Attack action')
    if block.count(b'100AC\n3OB\n')!=1:
        raise ValueError('Attack opcode not in expected compiled representation')
    updated=block.replace(b'100AC\n3OB\n',b'100AC\n105OB\n')
    if action_ids(updated)!=[105]:
        raise ValueError('Failed to substitute AttackOneRound')
    if len(updated)-len(block)!=2:
        raise ValueError('Unexpected compiled action size change')
    return updated


def build(raw:bytes):
    a,meta=candidate_a(raw)
    items=segments(a)
    before=[x for x in items]
    for n in ORIGINAL_ATTACK_NEW_IDS:
        items[n-1]=to_bounded_attack(items[n-1])
    out=b'SC\n'+b''.join(items)
    if len(out)!=SOURCE_SIZE+4 or len(segments(out))!=1057:
        raise AssertionError('Wrong total bytes/block count')
    diffs=[i for i,(x,y) in enumerate(zip(before,items),1) if x!=y]
    if diffs!=list(ORIGINAL_ATTACK_NEW_IDS):
        raise AssertionError('Other block content changed')
    if any(action_ids(items[i-1])!=[115,87] for i in range(1032,1043)):
        raise AssertionError('Guard commands changed')
    if any(action_ids(items[i-1])!=[105] for i in ORIGINAL_ATTACK_NEW_IDS):
        raise AssertionError('Missing one-round action')
    report={
        **meta,'unchanged_block_bytes':False,
        'every_other_block_unchanged':True,
        'changed_only_two_action_identifiers':True,
        'variant':'042B bounded attack + guard priority SOURCE ONLY',
        'preview_sha256':sha(out),'preview_bytes':len(out),
        'changed_block_actions': list(ORIGINAL_ATTACK_NEW_IDS),
        'changed_ids':'Attack(3) -> AttackOneRound(105), exactly 2',
        'queue_policy':'Guard takes priority over next EPS attack when idle; normal EPS attacks end after one round then can be reconsidered',
        'limitation':'Manual attacks are not interrupted; previously queued Attack action after loading might continue; spell/bard runtime unverified.',
        'release':'NO INSTALLER, NO GAME MODIFICATION, NO WeiDU COMPILE PROOF'
    }
    return out,report


def main():
    p=argparse.ArgumentParser(description='BGXAI 042B source-only, strict SHA256 offline BCS preview')
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--preview',type=Path)
    p.add_argument('--json-report',type=Path)
    a=p.parse_args()
    raw=a.source.read_bytes()
    out,report=build(raw)
    if a.preview:
        if a.preview.resolve()==a.source.resolve() or 'override' in [x.lower() for x in a.preview.parts]:
            raise ValueError('Refusing source overwrite or game override')
        a.preview.write_bytes(out)
    if a.json_report:
        a.json_report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()