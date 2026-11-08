#!/usr/bin/env python3
"""BGXAI 042B exact-byte bard/spell invariant audit. READ-ONLY, NEVER modifies EET.

Run from alongside the 042B release's build_042b_preview.py + guard_source_042a.py,
or supply --release-dir pointing to that source folder.

This checks the *compiled script structure* against a known baseline BCS,
NOT actual engine execution of BattleSong(), Spell() or EEex.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

SOURCE_SHA = '86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
PATCHED_SHA = '8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
SONG_OPCODE = 296   # IESDP: BattleSong()
SPELL_OPCODES = (31, 34, 63, 160)  # script's spell / force-spell / apply-spell families
OTHER_MONITORED = (33, 36, 86, 105, 3, 87, 115, 269)
GUARD_FROM = tuple(range(1047, 1058))
GUARD_TO = tuple(range(1032, 1043))
ATTACK_FROM = (1032, 1045)
ATTACK_TO = (1043, 1056)
SONG_POSITIONS = (987, 988)

def audit(source_file:Path, release_dir:Path)->dict:
    sys.path.insert(0, str(release_dir))
    from build_042b_preview import build
    from guard_source_042a import segments, action_ids
    raw=source_file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('REFUSE: wrong baseline BCS source hash')
    current,report=build(raw)
    if hashlib.sha256(current).hexdigest()!=PATCHED_SHA:
        raise AssertionError('REFUSE: patch does not match installed 042B SHA256')
    before,after=segments(raw),segments(current)
    if len(before)!=1057 or len(after)!=1057:
        raise AssertionError('Wrong script block count')
    checks={}
    def check(name, expression):
        checks[name]=bool(expression)
        if not checks[name]:raise AssertionError('FAILED: '+name)
    action_count=lambda blocks:Counter(a for block in blocks for a in action_ids(block))
    a,b=action_count(before),action_count(after)
    check('all_1057_blocks',len(before)==len(after)==1057)
    check('first_7_F_icon_blocks_identical', before[:7]==after[:7])
    check('all_first_1031_blocks_unchanged',before[:1031]==after[:1031])
    check('no_attack_3_in_candidate',a[3]==2 and b[3]==0)
    check('exactly_two_AttackOneRound_105',a[105]==0 and b[105]==2)
    check('11_ProtectObject_87_preserved',a[87]==b[87]==11)
    check('all_non_attack_action_multiset_preserved', all(a[n]==b[n] for n in set(a)|set(b) if n not in (3,105)))
    check('11_guard_blocks_exact_bytes',all(before[i-1]==after[j-1] for i,j in zip(GUARD_FROM,GUARD_TO)))
    check('guard_priority_is_after_song_and_before_new_attack', max(SONG_POSITIONS)<min(GUARD_TO) and max(GUARD_TO)<min(ATTACK_TO))
    check('2_unchanged_bard_BattleSong_blocks',tuple(i for i,x in enumerate(before,1) if SONG_OPCODE in action_ids(x))==SONG_POSITIONS and all(before[i-1]==after[i-1] for i in SONG_POSITIONS))
    check('bard_skill_mode_triggers_unchanged',all(b'LOCALSBDAI_SKILL_MODE' in before[i-1] and b'LOCALSBDAI_SKILL_MODE' in after[i-1] for i in SONG_POSITIONS))
    check('BDAI_skill_mode_blocks_pre_guard_unchanged',all(x==y for x,y in zip(before[:1031],after[:1031]) if b'LOCALSBDAI_SKILL_MODE' in x))
    spell_positions={}
    for opcode in SPELL_OPCODES:
        indexes=tuple(i for i,x in enumerate(before,1) if opcode in action_ids(x))
        spell_positions[str(opcode)]=dict(count=len(indexes),first=indexes[:10],last=indexes[-10:])
        check('spell_opcode_'+str(opcode)+'_count',len(indexes)>0 and a[opcode]==b[opcode])
        check('spell_opcode_'+str(opcode)+'_block_bytes',all(before[i-1]==after[i-1] for i in indexes))
        check('spell_opcode_'+str(opcode)+'_priority_unchanged',all(i<=1031 for i in indexes))
    check('BDAI_mode_gates_unmodified', all(before[i-1]==after[i-1] for i in range(1,1032) if b'BDAI_' in before[i-1]))
    check('SetInterrupt_opcode_unmodified', a[86]==b[86] and all(before[i-1]==after[i-1] for i in range(1,1032) if 86 in action_ids(before[i-1])))
    check('Continue_action_count_unmodified',a[36]==b[36])
    check('exactly_2_attack_blocks_rewritten',all(action_ids(after[i-1])==[105] for i in ATTACK_TO))
    check('attack_round_blocks_not_prior_to_guard',min(ATTACK_TO)>max(GUARD_TO))
    # Guard move is the only reorder; outside it, byte content differs only for 2 targeted Attack blocks.
    rest=[block for i,block in enumerate(before,1) if i not in GUARD_FROM]
    inverse=[block for i,block in enumerate(after,1) if i not in GUARD_TO]
    check('other_1046_blocks_in_same_order',len(rest)==len(inverse)==1046)
    diff=[i for i,(old,new) in enumerate(zip(rest,inverse),1) if old!=new]
    check('exactly_2_changed_remaining_blocks',len(diff)==2 and [action_ids(inverse[i-1]) for i in diff]==[[105],[105]])
    return {
        'status':'PASS - COMPILED BCS NON-INTERFERENCE ONLY; GAMEPLAY UNVERIFIED',
        'baseline_sha256':SOURCE_SHA, 'installed_042b_sha256':PATCHED_SHA,
        'all_checks_passed':all(checks.values()), 'checks_count':len(checks),
        'checks':checks,
        'song':{'BattleSong_action_id':SONG_OPCODE,'blocks':list(SONG_POSITIONS),'blocks_identical':True,'precede_11_guard_blocks':True},
        'spells':spell_positions,
        'changes':{'moved_guard_blocks':[list(GUARD_FROM),list(GUARD_TO)],'Attack_to_AttackOneRound':[list(ATTACK_FROM),list(ATTACK_TO)],'other_1046_blocks_order_preserved':True},
        'limitations':'Does NOT prove runtime song continuity, spell animation/cast survival, or responsiveness to threat during a song. Scripts in other assigned slots are out of scope.'
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--release-dir',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    r=audit(args.source,args.release_dir)
    rendered=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    if args.report:
        if args.report.resolve()==args.source.resolve() or 'override' in [p.casefold() for p in args.report.parts]:
            raise ValueError('No writing to source or game override')
        args.report.write_text(rendered,encoding='utf8')
    print(f"BGXAI 042B BARDS+SPELLS OFFLINE: {r['checks_count']}/{r['checks_count']} PASS; actual game not tested")
    print('Song blocks',r['song']['blocks'],'Spell action counts', {k:v['count'] for k,v in r['spells'].items()})

if __name__=='__main__':main()