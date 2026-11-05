"""Parses existing BGX71 action-start logs without asserting AI/player origin.

Action 105 = AttackOneRound, 355 = RunAwayFromNoLeaveArea. Event count !=
performance; it exposes regressions only, not whether a move completed safely.
"""
from pathlib import Path
from collections import Counter
import json,re,sys
EVENT=re.compile(r'ACTION_\d+ actor=(A\d+) id=(\d+) slot=(\d+) action=(\d+) pos=\((-?\d+),(-?\d+)\) dest=\((-?\d+),(-?\d+)\) target=(-?\d+)')

def analyze(path):
    s=Path(path).read_text(encoding='utf-8',errors='replace')
    events=[(m.group(1),int(m.group(4)),(int(m.group(5)),int(m.group(6))),int(m.group(9))) for m in EVENT.finditer(s)]
    counts=Counter(action for actor,action,_,__ in events if actor=='A1')
    relevant=[(action,pos,target) for actor,action,pos,target in events if actor=='A1' and action in (105,355)]
    # Consecutive alternation (actual events may have unrelated action starts in between)
    switches=sum(a[0]!=b[0] for a,b in zip(relevant,relevant[1:]))
    return {'file':Path(path).name,'A1_attack_starts':counts[105], 'A1_retreat_starts':counts[355],
            'A1_attack_retreat_switches':switches, 'risk_repeated_toggling':switches>=3 and counts[355]>=2,
            'action_origin':'UNKNOWN','enemy_aggro':'UNKNOWN','actual_HP':'UNKNOWN',
            'events':[{'kind':a,'pos':list(p),'target':str(t)} for a,p,t in relevant]}
if __name__=='__main__':
    print(json.dumps([analyze(f) for f in sys.argv[1:]],ensure_ascii=False,indent=2))