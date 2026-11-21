#!/usr/bin/env python3
"""BGXAI team tactic coordinator V1: SOURCE ONLY, NOT INSTALLED.

Aggregates proposals from BGXAI_ROLE_HAZARD_ARBITER_V1. No EEex hook,
WeiDU, engine action, file writes, or authority to dispatch an order.
Actor-ID=0 or EEex started-action/script metadata does not prove that manual
orders or the EPS queue are clear: a different verified adapter is required.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

TACTICS=frozenset(('MELEE_CANDIDATE','BACKSTAB_MELEE_CANDIDATE',
                   'AOE_SAFE_CANDIDATE','RANGED_HOLD_SAFE_POSITION',
                   'SINGLE_TARGET_SPELL_SAFE_POSITION','RETREAT_VERIFIED_ROUTE'))
TARGETED=TACTICS-{'RETREAT_VERIFIED_ROUTE'}
ROLES=frozenset(('FRONTLINE','HYBRID','RANGED','CASTER','THIEF'))

@dataclass(frozen=True)
class Actor:
    ident:str
    area:str
    role:str
    advice:str
    target:str|None
    role_verified:bool
    manual_clear_verified:bool
    eps_idle_verified:bool
    queue_empty_verified:bool
    f_on_verified:bool
    advice_executable:bool=False
    route_verified:bool=False
    aoe_geometry_verified:bool=False
    resource_cost:float|None=None

@dataclass(frozen=True)
class Enemy:
    ident:str
    area:str
    hostile_verified:bool
    visible_verified:bool
    nonparty_verified:bool
    threatens_backline_verified:bool=False

@dataclass(frozen=True)
class Frame:
    area:str
    party_roster_complete:bool
    summons_complete:bool
    hazards_complete:bool
    targets_complete:bool
    runtime_observed:bool

@dataclass(frozen=True)
class Decision:
    actor:str
    code:str
    why:str
    target:str|None=None
    executable:bool=False

@dataclass(frozen=True)
class Result:
    status:str
    choices:tuple[Decision,...]
    executable:bool=False
    dispatch_authorized:bool=False


def _id(s):
    return isinstance(s,str) and 1<=len(s)<=64 and all(c.isascii() and (c.isalnum() or c in '_-.') for c in s)


def coordinate(frame:Frame,actors,targets)->Result:
    """A party-level policy with stable tie-breaks, NEVER an engine executor."""
    try: a=tuple(actors); t=tuple(targets)
    except (TypeError,ValueError):return Result('HOLD_INVALID_COLLECTION',())
    if not isinstance(frame,Frame) or not _id(frame.area) or not all(x is True for x in (
        frame.runtime_observed,frame.party_roster_complete,frame.summons_complete,
        frame.hazards_complete,frame.targets_complete)):
        return Result('HOLD_INCOMPLETE_TEAM_EVIDENCE',())
    if not 1<=len(a)<=6 or len(t)>128 or any(not isinstance(x,Actor) for x in a) or any(not isinstance(x,Enemy) for x in t):
        return Result('HOLD_INVALID_PARTY',())
    aid=[x.ident for x in a];tid=[x.ident for x in t]
    if (not all(map(_id,aid+tid)) or len(set(aid))!=len(aid) or len(set(tid))!=len(tid)
        or set(aid)&set(tid) or any(x.area!=frame.area or x.role not in ROLES for x in a)
        or any(x.area!=frame.area for x in t)):
        return Result('HOLD_IDENTITY_OR_AREA_CONFLICT',())
    enemies={x.ident:x for x in t}
    decisions={};eligible={}
    for x in a:
        def hold(reason):decisions[x.ident]=Decision(x.ident,'HOLD',reason)
        if x.role_verified is not True or x.advice_executable is not False or x.advice not in TACTICS:
            hold('ROLE_OR_ADVICE_UNVERIFIED');continue
        if x.manual_clear_verified is not True:
            hold('MANUAL_ORIGIN_UNVERIFIED');continue
        if x.eps_idle_verified is not True:
            hold('EPS_QUEUE_UNVERIFIED');continue
        if x.queue_empty_verified is not True:
            hold('ACTION_QUEUE_UNVERIFIED');continue
        if x.f_on_verified is not True:
            hold('F_MODE_UNVERIFIED');continue
        if x.advice in TARGETED:
            y=enemies.get(x.target)
            if not y or y.hostile_verified is not True or y.visible_verified is not True or y.nonparty_verified is not True:
                hold('HOSTILE_TARGET_UNVERIFIED');continue
        if x.advice in ('RETREAT_VERIFIED_ROUTE','BACKSTAB_MELEE_CANDIDATE') and x.route_verified is not True:
            hold('ROUTE_UNVERIFIED');continue
        if x.advice=='AOE_SAFE_CANDIDATE':
            if x.role not in ('CASTER','HYBRID') or x.aoe_geometry_verified is not True:
                hold('AOE_SAFETY_UNVERIFIED');continue
            if (not isinstance(x.resource_cost,(int,float)) or isinstance(x.resource_cost,bool)
                or not isfinite(x.resource_cost) or not 0<=x.resource_cost<=1000):
                hold('AOE_RESOURCE_UNKNOWN');continue
        if (x.advice=='MELEE_CANDIDATE' and x.role not in ('FRONTLINE','HYBRID')) or (
            x.advice=='BACKSTAB_MELEE_CANDIDATE' and x.role!='THIEF'):
            hold('TACTICAL_ROLE_CONFLICT');continue
        eligible[x.ident]=x
    aoe=sorted((x for x in eligible.values() if x.advice=='AOE_SAFE_CANDIDATE'),
               key=lambda x:(x.resource_cost,x.ident))
    for x in aoe:
        decisions[x.ident]=Decision(x.ident,x.advice if x==aoe[0] else 'HOLD',
            'SOLE_AOE_ADVISORY' if x==aoe[0] else 'DUPLICATE_AOE_BLOCKED',x.target)
    frontliners=sum(x.role=='FRONTLINE' and x.advice in ('MELEE_CANDIDATE','RANGED_HOLD_SAFE_POSITION')
                     for x in eligible.values())
    max_melee=max(1,frontliners-1)  # when >=2 fighters, keep one in reserve
    melee=sorted((x for x in eligible.values() if x.advice=='MELEE_CANDIDATE'),
       key=lambda x:(0 if enemies[x.target].threatens_backline_verified else 1,
                     0 if x.role=='FRONTLINE' else 1,x.ident))
    taken=set(); count=0
    for x in melee:
        ok=count<max_melee and x.target not in taken
        decisions[x.ident]=Decision(x.ident,x.advice if ok else 'HOLD',
                                    'ONE_INTERCEPT_PER_THREAT' if ok else 'KEEP_TANK_RESERVE',x.target)
        if ok:taken.add(x.target);count+=1
    stolen=set()
    for x in sorted(eligible.values(),key=lambda x:x.ident):
        if x.advice!='BACKSTAB_MELEE_CANDIDATE':continue
        ok=x.target not in stolen
        decisions[x.ident]=Decision(x.ident,x.advice if ok else 'HOLD',
                                    'ONE_THIEF_PER_TARGET' if ok else 'DUPLICATE_BACKSTAB',x.target)
        if ok:stolen.add(x.target)
    for x in eligible.values():
        if x.ident not in decisions:
            decisions[x.ident]=Decision(x.ident,x.advice,'SAFE_INDIVIDUAL_ADVISORY',x.target)
    return Result('ADVISORY_ONLY',tuple(decisions[x.ident] for x in a))
