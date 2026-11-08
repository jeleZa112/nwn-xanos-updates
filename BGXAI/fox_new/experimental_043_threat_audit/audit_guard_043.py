#!/usr/bin/env python3
"""BGXAI 043 READ-ONLY: inspect exact guard preconditions in verified 042B compiled BCS.

No game writes, no BCS patch. Reports what is supported by source bytes only.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import hashlib, json, re, sys

PIN_SOURCE='86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5'
PIN_042B='8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0'
TR = re.compile(rb'TR\n(-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+) "([^"]*)" "([^"]*)" OB\n([^\n]+)')
ACT = re.compile(rb'AC\n(-?\d+)OB\n')


def analyze(source: Path, release_dir: Path) -> dict:
    # Original live source is a known, verified BCS baseline, never an installation source.
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN_SOURCE: raise ValueError('wrong original live BCS: SHA256 mismatch')
    sys.path.insert(0,str(release_dir))
    from build_042b_preview import build
    from guard_source_042a import segments,action_ids
    compiled,_=build(raw)
    if hashlib.sha256(compiled).hexdigest()!=PIN_042B:raise AssertionError('042B candidate hash mismatch')
    blocks=segments(compiled)
    if len(blocks)!=1057:raise AssertionError('unexpected CR count')
    rules=[]
    for position in range(1032,1043):
        block=blocks[position-1]
        cond,sep,actions=block.partition(b'\nRS\n')
        if not sep or action_ids(block)!=[115,87]: raise AssertionError('guard action changed')
        triggers=[]
        for match in TR.finditer(cond):
            v=match.groups()
            # Engine compiled object selector fields; the 8th positional member carries Player selector.
            selector=[int(x) for x in v[7].split(b'"',1)[0].split()]
            triggers.append({'opcode':int(v[0]),'params':[int(x) for x in v[1:5]],
                             's1':v[5].decode('ascii'),'s2':v[6].decode('ascii'),
                             'selector':selector})
        ops=[x['opcode'] for x in triggers]
        if 16427 not in ops or 16399 not in ops or 16412 not in ops or 16408 not in ops:
            raise AssertionError('missing guard base gates')
        hp=[x for x in triggers if x['opcode']==16429] # HPPercentLT = 0x402D
        if len(hp)>1:raise AssertionError('multiple HP gates')
        seen_targets=[x['selector'][7] for x in triggers if x['opcode']==16412]
        if not seen_targets or any(x!=seen_targets[0] for x in seen_targets):raise AssertionError('mixed target selectors')
        target=seen_targets[0]
        range_gates=[x['params'][0] for x in triggers if x['opcode']==16408]
        action=actions.decode('latin1')
        # action's ProtectObject second object must be same target
        m=re.search(r'AC\n87OB\n[^\n]*\nOB\n([^\n]*)\n',action)
        if not m:raise AssertionError('ProtectObject action not found')
        action_selector=[int(x) for x in m.group(1).split('"',1)[0].split()]
        if action_selector[7]!=target:raise AssertionError('ProtectObject target not equal guard target')
        timer=6 if b'LOCALSBGX38_GUARD_CD' in block else (8 if b'LOCALSBGX39_TEAM_CD' in block else None)
        if timer is None:raise AssertionError('unknown timer')
        rules.append({'block':position,'target_selector':target,'target':'Player'+str(target-20),
            'hp_below_65_priority':bool(hp),'cooldown_seconds':timer,
            'range_predicates':range_gates,'action_ids':action_ids(block),
            'uses_action_list_empty':16427 in ops,'explicit_attackedby_or_help':any(op in (2,3) for op in ops),
            'see_triggers':len(seen_targets)})
    if rules[0]['target_selector']!=21 or rules[0]['hp_below_65_priority'] or rules[0]['cooldown_seconds']!=6:
        raise AssertionError('primary guard rule mismatch')
    if [x['target_selector'] for x in rules[1:6]]!=[23,24,25,26,22]:
        raise AssertionError('priority block target list changed')
    if [x['target_selector'] for x in rules[6:]]!=[23,24,25,26,22]:
        raise AssertionError('fallback block target list changed')
    if not all(x['hp_below_65_priority'] for x in rules[1:6]):raise AssertionError('missing low HP priority branches')
    if any(x['hp_below_65_priority'] for x in rules[6:]):raise AssertionError('unconditional fallback changed')
    if not all(x['uses_action_list_empty'] for x in rules):raise AssertionError('manual action preemption risk')
    if not all(x['range_predicates']==[10,7] for x in rules[1:]):raise AssertionError('range gates changed')
    if not all(x['cooldown_seconds']==8 for x in rules[1:]):raise AssertionError('team cooldown changed')
    # Does not assert that CD is the exact reaction delay at runtime: pathing/engine also contribute.
    return {'status':'PASS / OFFLINE 043 READ-ONLY THREAT AUDIT',
        'source_bcs_sha256':PIN_SOURCE,'installed_042b_sha256':PIN_042B,
        'guard_rule_count':len(rules),'guard_positions':[x['block'] for x in rules],
        'rule_groups':{'personal_hero':1,'priority_hp_below_65':5,'team_fallback':5},
        'uses_idle_gate_all':all(x['uses_action_list_empty'] for x in rules),
        'guard_action_only':[115,87],
        'explicit_attackedby_or_help_in_guard':any(x['explicit_attackedby_or_help'] for x in rules),
        'observed_unchanged_cooldowns_seconds':{'personal':6,'team':8},
        'rules':rules,
        'limits':'Counts and trigger names are compiled script evidence only, not runtime timing; no safe pre-emption of active casts/manual commands proved.',
        'decision':'Do not install 043 yet. Need strictly class-aware threat arbitration and engine-safe handling of existing actions.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--release-dir',type=Path,required=True)
    p.add_argument('--json-report',type=Path)
    a=p.parse_args()
    out=analyze(a.source,a.release_dir)
    if a.json_report:
        if a.json_report.resolve()==a.source.resolve() or 'override' in [z.lower() for z in a.json_report.parts]:
            raise ValueError('Refusing report write to BCS or override')
        a.json_report.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
