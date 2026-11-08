#!/usr/bin/env python3
"""BGXAI 043A conservative, OFFLINE ONLY guarded-range BCS preview.

Target: exact installed 042B BCS, never an in-game file. Change only the
Range(NearestEnemyOf(PlayerX),N) TR integer in 11 guard blocks.
This does *not* implement dual-guard role arbitration from intercept_policy.py.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PIN_042B = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
PIN_BLOCKS = 1057
PIN_BYTES = 2229764
GUARDS = tuple(range(1032, 1043))
# Conservative increase in enemy-detection distance; preserve 10-unit ally tether.
HERO_OLD, HERO_NEW = 8, 9
TEAM_OLD, TEAM_NEW = 7, 9
TR_RANGE = re.compile(rb'(TR\nTR\n16408 )(-?\d+)( 0 0 0 "" "" OB\n)([^\n]+)(\nTR\n|\nCO\n)')
BLOCK = re.compile(rb'(?m)^CR\nCO\n')


def sha(raw:bytes) -> str: return hashlib.sha256(raw).hexdigest()


def blocks(raw:bytes) -> list[bytes]:
    if not raw.startswith(b'SC\n'):raise ValueError('invalid BCS header')
    starts = [m.start() for m in BLOCK.finditer(raw)]
    if len(starts)!=PIN_BLOCKS or starts[0]!=3:raise ValueError('invalid number of BCS blocks')
    result=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if b'SC\n'+b''.join(result)!=raw:raise AssertionError('lossless split failed')
    return result


def change_guard(block:bytes, *, hero:bool, slot:int) -> bytes:
    if b'LOCALSBGX38_GUARD' not in block or b'16427 0 0 0 0' not in block:
        raise ValueError('guard mode/idle trigger absent')
    ranges=list(TR_RANGE.finditer(block))
    if len(ranges)!=2:raise ValueError('guard must have exactly two Range triggers')
    parsed=[]
    for m in ranges:
        obj=[int(n) for n in m.group(4).split(b'"',1)[0].split()]
        if len(obj)!=12 or obj[7]!=slot:raise ValueError('unexpected guard target selector')
        parsed.append((int(m.group(2)),obj[8]))
    old=HERO_OLD if hero else TEAM_OLD
    new=HERO_NEW if hero else TEAM_NEW
    if parsed != [(10,0),(old,12)]:
        raise ValueError('unexpected ally/enemy distance trigger pattern')
    m=ranges[1]
    result=block[:m.start(2)]+str(new).encode('ascii')+block[m.end(2):]
    check=list(TR_RANGE.finditer(result))
    if [(int(x.group(2)),int(x.group(4).split(b'"',1)[0].split()[8])) for x in check] != [(10,0),(new,12)]:
        raise AssertionError('wrong range replacement')
    if len(result)!=len(block):raise AssertionError('unexpected BCS block length')
    if block.count(b'AC\n87OB\n')!=1 or result.count(b'AC\n87OB\n')!=1:
        raise AssertionError('ProtectObject action changed/missing')
    return result


def preview(raw:bytes) -> tuple[bytes,dict]:
    if len(raw)!=PIN_BYTES or sha(raw)!=PIN_042B:
        raise ValueError('042B BCS SHA256/size mismatch: refusing preview')
    orig=blocks(raw);out=list(orig)
    for num in GUARDS:
        slot = 21 if num==1032 else (23,24,25,26,22)[(num-1033)%5]
        out[num-1]=change_guard(orig[num-1],hero=num==1032,slot=slot)
    compiled=b'SC\n'+b''.join(out)
    if len(compiled)!=len(raw):raise AssertionError('BCS length changed')
    if len(blocks(compiled))!=PIN_BLOCKS:raise AssertionError('BCS block count changed')
    changed=[i for i,(a,b) in enumerate(zip(orig,out),1) if a!=b]
    if changed!=list(GUARDS):raise AssertionError('Only 11 guard conditions may change')
    if out[:1031]!=orig[:1031] or out[1042:]!=orig[1042:]:
        raise AssertionError('EPS/spell/bard/attack or F blocks changed')
    if any(b'AC\n105OB\n' in out[i] for i in range(1031,1042)):
        raise AssertionError('Attack opcode accidentally migrated into guard')
    report={
        'status':'SOURCE_ONLY_OFFLINE_PREVIEW_NEVER_INSTALLED',
        'source_042b_sha256':sha(raw),'candidate_043a_sha256':sha(compiled),
        'bytes':len(compiled),'blocks':len(out),'changed_blocks':changed,
        'changed_only_range_parameters':True,
        'player1_enemy_distance':{'from':HERO_OLD,'to':HERO_NEW},
        'player2_6_enemy_distance':{'from':TEAM_OLD,'to':TEAM_NEW},
        'protected_ally_distance_unchanged':10,
        'compiled_guard_action_unchanged':True,
        'eps_magic_bard_f_ui_unmodified':True,
        'does_not_allocate_two_guard_roles':True,
        'gameplay_runtime_verified':False,
        'caveat':'Earlier range may cause earlier approach or extra chasing; real in-game behaviour UNVERIFIED.',
    }
    return compiled,report


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--out',type=Path,help='PRIVATE offline preview output, never use game override')
    a.add_argument('--report',type=Path)
    args=a.parse_args()
    raw=args.source.read_bytes()
    generated,info=preview(raw)
    if args.out:
        dest=args.out.resolve()
        if dest==args.source.resolve() or any(part.lower() in ('override','bg_eet_foxx_new') for part in dest.parts):
            raise ValueError('will not write game or original BCS')
        dest.write_bytes(generated)
    if args.report:args.report.write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
