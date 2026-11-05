#!/usr/bin/env python3
"""Reproducible BGXAI action-stream postmortem. Read-only, no game modifications.
Usage: python analyze_combat.py "BGXAI_COMBAT(20261105-093310).log"
"""
from __future__ import annotations
import json, re, sys
from collections import Counter
from pathlib import Path
from math import hypot
ACTION = re.compile(r'\[BGX71\] ACTION_(\d+) actor=(A\d+) id=(\d+) slot=(\d+) action=(\d+) pos=\((-?\d+),(-?\d+)\) dest=\((-?\d+),(-?\d+)\) target=(-?\d+)')

def parse(path: str):
    content = Path(path).read_text(encoding='utf-8', errors='replace')
    ret = []
    for m in ACTION.finditer(content):
        n, actor, id_, slot, action, x, y, dx, dy, target = m.groups()
        ret.append(dict(n=int(n), actor=actor, actor_id=int(id_), slot=int(slot), action=int(action), pos=(int(x),int(y)), dest=(int(dx),int(dy)), target=int(target)))
    return ret

def analyze(events):
    if not events: return {'error': 'No BGX71 events'}
    counted=Counter((x['actor'],x['action']) for x in events)
    # A1 in THIS session; do not generalize actor id or slot across loads.
    mine=[x for x in events if x['actor']=='A1']
    esc=[x for x in mine if x['action']==355]
    shots=[x for x in mine if x['action']==105]
    gap=[round(hypot(b['pos'][0]-a['pos'][0],b['pos'][1]-a['pos'][1]),1) for a,b in zip(esc,esc[1:])]
    post=[x for x in mine if x['n']>=24 and x['action'] in (105,355)]
    return {'events_total':len(events),'actor_A1_events':len(mine),'actor_A1_attack_one_round':len(shots),'actor_A1_retreats':len(esc),'actor_A1_move_to_point':counted['A1',23],
        'post_first_kill_actions':[(x['n'],x['action'],x['target'],x['pos']) for x in post],
        'retreat_positions':[x['pos'] for x in esc],'retreat_step_distances':gap,
        'attack_retreat_alternations':sum(a['action']!=b['action'] for a,b in zip(post,post[1:])),
        'manual_vs_AI_source':'UNKNOWN','hostile_aggro_target':'NOT_LOGGED','tank_position':'NOT_LOGGED',
        'warning':'Action-start events are NOT proof of who originated the order. This is a behavioral regression fixture, not an engine simulation.'}

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('Provide log filename')
    print(json.dumps(analyze(parse(sys.argv[1])),ensure_ascii=False,indent=2))