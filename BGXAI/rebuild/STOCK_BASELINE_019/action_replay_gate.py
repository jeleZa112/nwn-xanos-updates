#!/usr/bin/env python3
"""Offline regression gate: known-bad action oscillations from real BGX71 logs.

Unknown source of action, HP, actual aggro and tank location are NOT inferred.
Any real player commands in a sequence retain UNKNOWN origin.
"""
from __future__ import annotations
import json
import re
from collections import Counter
from pathlib import Path

REG = re.compile(
    r'\[BGX71\] ACTION_(\d+) actor=(A\d+) id=(\d+) slot=(\d+) '
    r'action=(\d+) pos=\((-?\d+),(-?\d+)\) dest=\((-?\d+),(-?\d+)\) target=(-?\d+)')
ROSTER = '[BGX71] ROSTER epoch='


def parse_sessions(text: str):
    sessions=[]
    for line in text.splitlines():
        if ROSTER in line: sessions.append([])
        m=REG.search(line)
        if not m: continue
        if not sessions: sessions=[[]]
        n, actor, actor_id, slot, action, x,y,dx,dy,target = map_values(m)
        sessions[-1].append({'n':n, 'actor':actor, 'actor_id':actor_id,
            'slot':slot, 'action':action, 'pos':[x,y], 'target':target})
    return [s for s in sessions if s]


def map_values(m):
    g=list(m.groups())
    return (int(g[0]),g[1],int(g[2]),int(g[3]),int(g[4]),
            int(g[5]),int(g[6]),int(g[7]),int(g[8]),int(g[9]))


def audit_session(events, actor='A1'):
    tracked=[e for e in events if e['actor']==actor]
    combat=[e for e in tracked if e['action'] in (105,355)]
    # Bad signal: repeated run-away actions from same target intermixed with
    # attack cycles, with no durable disengagement that sensors can establish.
    by_target={}
    for e in combat:
        by_target.setdefault(e['target'],[]).append(e['action'])
    suspect=[]
    for target, seq in by_target.items():
        if target < 0:continue
        if seq.count(355)>=3 and seq.count(105)>=2:
            switches=sum(a!=b for a,b in zip(seq,seq[1:]))
            if switches>=3:
                suspect.append({'target':target,'sequence':seq,
                                'attack_retreat_transitions':switches})
    return {
        'actor':actor,
        'actions_total':len(tracked),
        'attacks_started':sum(e['action']==105 for e in tracked),
        'retreats_started':sum(e['action']==355 for e in tracked),
        'melee_or_aggro_known':False,
        'manual_vs_AI_origin':'UNKNOWN',
        'bad_oscillations':suspect,
        'warning':('Current sensor cannot establish HP, aggro, enemy path, '
                   'actual attacks landed or PLAYER/AI origin.')
    }


def create_report(paths, actor='A1'):
    out=[]
    for path in paths:
        sessions=parse_sessions(Path(path).read_text(encoding='utf-8',errors='replace'))
        out.append({'source':Path(path).name,'sessions':[
            audit_session(s,actor) for s in sessions]})
    return out

if __name__=='__main__':
    import sys
    print(json.dumps(create_report(sys.argv[1:]),indent=2,ensure_ascii=False))