#!/usr/bin/env python3
"""BGXAI 121: deterministic AOE geometry + ranged fallback (SOURCE ONLY).

This module NEVER moves a sprite or changes game files. It is the policy
kernel for an EEex implementation after mod-specific projectile/radius audit.
Positions are engine screen pixels; y is scaled by 4/3 to account for the
3/4 perspective when comparing an ellipse to a projectile horizontal radius.
Unknown resistance / summons / effect metadata are treated as vulnerable.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from typing import Iterable

@dataclass(frozen=True)
class Ally:
    ident: str
    x: float
    y: float
    area: str
    # Proved immunity to individual harmful effects; never infer from race/name.
    immune_to: frozenset[str] = frozenset()
    alive: bool = True

@dataclass(frozen=True)
class Hazard:
    ident: str
    x: float
    y: float
    area: str
    radius_px: float
    harmful_effects: frozenset[str]
    expires_known: bool = False

BUFFER_PX = 48.0  # margin for movement, creature footprint, cast delay; not spell radius

def _pos(x:float,y:float)->bool:
    return isfinite(x) and isfinite(y)

def ellipse_d2(a:tuple[float,float], b:tuple[float,float])->float:
    """Square of horizontal-pixel distance using IE 3/4 vertical perspective."""
    return (a[0]-b[0])**2 + ((a[1]-b[1])*4.0/3.0)**2

def affected(ally:Ally, hazard:Hazard, padding:float=BUFFER_PX)->bool:
    if not ally.alive or ally.area!=hazard.area:
        return False
    if not _pos(ally.x,ally.y) or not _pos(hazard.x,hazard.y):
        return True  # fail closed for unknown positions
    if not isfinite(hazard.radius_px) or hazard.radius_px<=0 or not isfinite(padding) or padding<0:
        return True
    # Missing harmful_effects means "unknown", NOT "safe".
    if hazard.harmful_effects and hazard.harmful_effects.issubset(ally.immune_to):
        return False
    return ellipse_d2((ally.x,ally.y),(hazard.x,hazard.y)) <= (hazard.radius_px+padding)**2

def safe_aoe(hazard:Hazard, allies:Iterable[Ally], roster_complete:bool)->tuple[bool,list[str]]:
    """No cast on incomplete same-area roster, unknown radius or incomplete immunity."""
    if not roster_complete:
        return False,["ALLY_ROSTER_INCOMPLETE"]
    if not _pos(hazard.x,hazard.y) or not isfinite(hazard.radius_px) or hazard.radius_px<=0:
        return False,["UNKNOWN_AOE_GEOMETRY"]
    unsafe=[a.ident for a in allies if affected(a,hazard)]
    return not unsafe,unsafe

def path_crosses(start:tuple[float,float],end:tuple[float,float],hazard:Hazard,
                 actor:Ally,padding:float=BUFFER_PX)->bool:
    """Projected path A->B vs hazard; no LOS shortcuts; not a navigation solver."""
    if actor.area!=hazard.area or not actor.alive:
        return False
    if not all(_pos(*p) for p in (start,end,(hazard.x,hazard.y))):
        return True
    if not isfinite(hazard.radius_px) or hazard.radius_px<=0:
        return True
    if hazard.harmful_effects and hazard.harmful_effects.issubset(actor.immune_to):
        return False
    x1,y1=start[0],start[1]*4/3
    x2,y2=end[0],end[1]*4/3
    xc,yc=hazard.x,hazard.y*4/3
    vx,vy=x2-x1,y2-y1
    dot=(xc-x1)*vx+(yc-y1)*vy
    t=max(0.0,min(1.0,dot/(vx*vx+vy*vy))) if vx or vy else 0.0
    return (x1+t*vx-xc)**2+(y1+t*vy-yc)**2 <= (hazard.radius_px+padding)**2

def choose_combat_action(actor:Ally, start:tuple[float,float],
                         melee_destination:tuple[float,float],
                         active_hazards:Iterable[Hazard],
                         can_use_ranged_weapon:bool,
                         can_use_ranged_spell:bool,
                         urgent_healing:bool=False,
                         safe_ally_destination:tuple[float,float]|None=None)->str:
    """Policy advice only; BGXP5 handles all actual healing and spell casting."""
    # Never hijack a healing decision from BGXP5.
    if urgent_healing:
        return "DEFER_TO_BGXP5_HEAL"
    hazards=tuple(active_hazards)
    dangerous=any(path_crosses(start,melee_destination,h,actor) for h in hazards)
    if not dangerous:
        return "MELEE_PERMITTED"
    if can_use_ranged_weapon:
        return "RANGED_WEAPON_FROM_SAFE_POSITION"
    if can_use_ranged_spell:
        return "RANGED_SPELL_FROM_SAFE_POSITION"
    if safe_ally_destination is not None and not any(
        path_crosses(start,safe_ally_destination,h,actor) for h in hazards
    ):
        return "MOVE_TO_SAFE_POSITION"
    return "HOLD_OR_OTHER_TARGET"
