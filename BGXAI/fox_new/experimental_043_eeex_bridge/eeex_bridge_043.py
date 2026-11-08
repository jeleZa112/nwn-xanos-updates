#!/usr/bin/env python3
"""BGXAI 043: strict read-only adapter for EEex v1.1.7 observation events.

Never sends actions to EET; unknown manual provenance or guard state always
withholds any command. Consumes JSON export from BGX43Probe.snapshot().
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any

ATTACK_IDS = frozenset((3, 105))
MAX_EVENTS = 64

@dataclass(frozen=True)
class Observation:
    sequence: int
    actor_id: int
    target_id: int
    action_id: int
    actor_x: float | None
    actor_y: float | None
    action_origin: str
    visibility: str
    event: str


def _maybe_number(raw: Any) -> float | None:
    if raw is False or raw is None or not isinstance(raw, (int, float)) or isinstance(raw, bool):
        return None
    value = float(raw)
    if not (-1000000 < value < 1000000):
        return None
    return value


def validate_report(raw: Any) -> tuple[list[Observation], list[str]]:
    if not isinstance(raw, dict) or raw.get('schema') != 1:
        raise ValueError('Expected BGX43Probe schema=1 report')
    if raw.get('origin_verifiable') is not False or raw.get('queue_verifiable') is not False:
        raise ValueError('Source origin/queue metadata unsupported; refuse to reinterpret')
    events = raw.get('events')
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError('Expected bounded events[] <=64')
    collected: list[Observation] = []
    warnings: list[str] = []
    last_sequence = -1
    for i, row in enumerate(events):
        if not isinstance(row, dict):
            warnings.append(f'event[{i}]: malformed'); continue
        seq, src, dst, action = (row.get(k) for k in ('sequence','actor_id','target_id','action_id'))
        if (not all(isinstance(v, int) and not isinstance(v, bool) for v in (seq,src,dst,action))
            or action not in ATTACK_IDS or src == dst or seq <= last_sequence
            or row.get('event') != 'NONPARTY_ATTACK_STARTED_ON_PARTY'
            or row.get('hostility') != 'CONFIRMED_BY_EXPLICIT_ATTACK_ACTION'
            or row.get('action_origin') != 'UNKNOWN'
            or row.get('visibility') != 'UNKNOWN'):
            warnings.append(f'event[{i}]: unsupported or unverified');continue
        party = row.get('party_ids')
        if (not isinstance(party, list) or not all(type(n) is int and n >= 0 for n in party)
            or dst not in party or src in party):
            warnings.append(f'event[{i}]: party identity check failed');continue
        last_sequence = seq
        collected.append(Observation(seq,src,dst,action,
            _maybe_number(row.get('actor_x')),_maybe_number(row.get('actor_y')),
            'UNKNOWN','UNKNOWN',str(row['event'])))
    return collected,warnings


def summarize(raw: Any) -> dict[str, Any]:
    events,warnings=validate_report(raw)
    return {
        'schema': 1,
        'mode': 'READ_ONLY_ADVISORY',
        'upstream_version': raw.get('version'),
        'events_considered': len(events),
        'warnings': warnings,
        'attack_alerts': [asdict(e) for e in events],
        'queue_origin_known': False,
        'engine_visibility_known': False,
        'execution_allowed': False,
        'action_commands': [],
        'next_step': 'VERIFY_MANUAL_ACTION_PROVENANCE_BEFORE_ANY_DISPATCH',
    }


def run(argv: list[str] | None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path, help='Offline JSON export from BGX43Probe.snapshot()')
    args=p.parse_args(argv)
    data=json.loads(args.report.read_text(encoding='utf-8'))
    print(json.dumps(summarize(data),ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(run())


def simulate_policy_offline(raw: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    """Connect the actual EEex event schema to the 043 dual-guard policy using
    EXPLICITLY SYNTHETIC tactical state. Not callable as a game dispatcher.

    No real EEex action listener provides manual-action origin, visibility,
    health or role: this method refuses to present them as verified live data.
    """
    from dataclasses import asdict as dataclass_dict
    from intercept_policy import Ally, Defender, Enemy, Snapshot, plan
    alerts,_=validate_report(raw)
    if fixture.get('provenance')!='OFFLINE_FIXTURE':
        raise ValueError('No verified EEex tactical state; only OFFLINE_FIXTURE accepted')
    if not alerts:
        return {'mode':'OFFLINE_FIXTURE_ONLY','policy_plan':None,'execution_allowed':False}
    event=alerts[-1]
    def xrow(r):
        if not isinstance(r,dict):raise ValueError('Fixture row must be an object')
        return dict(r)
    allies=tuple(Ally(**xrow(r)) for r in fixture.get('allies',[]))
    defenders=tuple(Defender(**xrow(r)) for r in fixture.get('defenders',[]))
    if not allies or not defenders:raise ValueError('Fixture must explicitly supply allies and defenders')
    if str(event.target_id) not in {a.uid for a in allies}:
        raise ValueError('Fixture target does not match actual event target')
    # Enemy visibility is a synthetic scenario assumption, never an EEex fact.
    enemy=Enemy(uid=str(event.actor_id), x=event.actor_x if event.actor_x is not None else 0,
        y=event.actor_y if event.actor_y is not None else 0,
        hostile_confirmed=True,visible=True,attacking_uid=str(event.target_id))
    snap=Snapshot(tick=int(fixture.get('tick',1)),allies=allies,defenders=defenders,
        enemies=(enemy,),party_ai_on=fixture.get('party_ai_on') is True)
    proposal,_=plan(snap)
    return {
        'mode':'OFFLINE_FIXTURE_ONLY',
        'source_event_sequence':event.sequence,
        'engine_visibility_known':False,
        'manual_action_origin_known':False,
        'policy_plan':dataclass_dict(proposal),
        'execution_allowed':False,
        'action_commands':[],
    }
