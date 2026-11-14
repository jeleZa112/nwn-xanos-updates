#!/usr/bin/env python3
"""BGXAI 085: fail-closed static BAF gate audit. Reads BAF; NEVER patches game files.

Designed for BGXAI 061/066S/067 source-only BAF fragments, not general AI policy.
A PASS means only named static gates appear in the relevant IF block.
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys

# An unknown action is not silently classified as safe housekeeping.
HOUSEKEEPING = {'SetGlobal', 'SetGlobalTimer', 'Continue', 'NoAction'}
NAME = re.compile(r'^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(')
GUARD_ON = 'Global("BGX38_GUARD","LOCALS",1)'

def without_comments(raw: str):
    return [re.sub(r'//.*$', '', l).strip() for l in raw.splitlines()]

def parse_baf(raw: str):
    result=[]
    state='outside';triggers=[];actions=[]
    for lineno,line in enumerate(without_comments(raw), 1):
        if not line: continue
        if state=='outside':
            if line != 'IF': raise ValueError(f'BAF_UNEXPECTED_TEXT_LINE_{lineno}')
            state='trigger';triggers=[];actions=[]
        elif state=='trigger':
            if line=='THEN': state='response'
            elif line in ('IF','END'): raise ValueError(f'BAF_BAD_TRIGGER_LINE_{lineno}')
            else: triggers.append(line)
        elif state=='response':
            if line=='END':
                result.append({'index':len(result)+1,'triggers':triggers,'actions':actions})
                state='outside'
            elif line=='IF' or line=='THEN': raise ValueError(f'BAF_BAD_RESPONSE_LINE_{lineno}')
            elif re.fullmatch(r'RESPONSE\s+#\d+', line): pass
            else: actions.append(line)
    if state!='outside':raise ValueError('BAF_UNCLOSED_BLOCK')
    if not result:raise ValueError('BAF_NO_BLOCKS')
    return result

def inspect_block(b):
    tr=b['triggers']; act=b['actions']
    parsed=[];unknown=[]
    for a in act:
        match=NAME.match(a)
        if not match:
            unknown.append(a);parsed.append(('<UNPARSEABLE>',a))
        else: parsed.append((match.group(1),a))
    active=[(n,a) for n,a in parsed if n not in HOUSEKEEPING]
    gates={'native_queue':('ActionListEmpty()' in tr),
           'F_guard_on':(GUARD_ON in tr),
           'modal_none':('ModalState(NONE)' in tr),
           'request_ttl':any(x.startswith('GlobalTimerNotExpired("BGX') and '_EXPIRE"' in x for x in tr),
           'on_hit_request':any(x.startswith('Global("BGX52_REQ_SLOT"') or x.startswith('Global("BGX66_S_HEAL_SLOT"') or x.startswith('Global("BGX66_S_WARD"') for x in tr)}
    failures=[]
    if active:
        for k,good in gates.items():
            if not good:failures.append('MISSING_'+k.upper())
        if any(n.startswith('Spell') for n,a in active) and not any(x.startswith('HaveSpell(') for x in tr):
            failures.append('MISSING_HAVE_SPELL')
        for n,a in active:
            if n not in {'AttackReevaluate','Attack','MoveToObject','MoveToPoint',
                         'ProtectObject','Spell','SpellRES','UseItem','UseItemSlot',
                         'ActionOverride','RunAwayFrom','ForceSpell'}:
                failures.append('REVIEW_UNKNOWN_ENGINE_ACTION_'+n)
    elif unknown:failures.append('REVIEW_UNPARSEABLE_HOUSEKEEPING')
    return {'index':b['index'],'kind':'DISPATCH_OR_UNKNOWN' if active else 'HOUSEKEEPING',
            'action_names':[n for n,a in active], 'gates':gates,
            'findings':sorted(set(failures)), 'pass_static':not failures}

def audit(raw: str, name='source-only'):
    blocks=parse_baf(raw)
    inspected=[inspect_block(b) for b in blocks]
    unsafe=[b['index'] for b in inspected if not b['pass_static']]
    dispatch=[b for b in inspected if b['kind']=='DISPATCH_OR_UNKNOWN']
    return {'status':'BAF_STATIC_GATE_PASS' if not unsafe else 'BAF_STATIC_GATE_REVIEW',
            'source':name,'blocks':len(blocks),'dispatch_rules':len(dispatch),
            'housekeeping_rules':len(blocks)-len(dispatch),
            'native_queue_gated_dispatch':sum(x['gates']['native_queue'] for x in dispatch),
            'fail_blocks':unsafe,'rules':inspected,
            'live_verified':False,'engine_dispatch_authorized':False,
            'manual_origin_verified':False,'eps_buff_priority_verified':False,
            'source_only':True}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('baf',nargs='+',type=pathlib.Path,help='Existing BAF files (read-only)')
    args=p.parse_args(argv)
    out=[]
    for f in args.baf:
        try:out.append(audit(f.read_text(encoding='utf-8-sig'),str(f)))
        except (ValueError,OSError,UnicodeError) as e:out.append({'status':'BAF_READ_OR_PARSE_ERROR','source':str(f),'error':str(e),'source_only':True})
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0 if all(x['status']=='BAF_STATIC_GATE_PASS' for x in out) else 2
if __name__=='__main__':sys.exit(main())
