"""BGXAI Hybrid 0.2.2: advisory-only tactical decision engine.

No attack/move execution. The real user's installed ordinary BDDEFAI remains
responsible for ALL actions. The observer must never fabricate enemy aggro,
weapon effectiveness, active orders or route safety from an action-start log.
"""
from dataclasses import dataclass
from typing import Literal, Optional, Tuple
from math import hypot

Point = Tuple[float, float]
Origin = Literal['PLAYER', 'AI', 'UNKNOWN']

@dataclass(frozen=True)
class Actor:
    actor_id: str
    pos: Optional[Point]
    hp_pct: Optional[float]
    alive: Optional[bool]
    visible: Optional[bool]
    attacking: Optional[str] = None     # verified live actor-target binding, not a heuristic
    class_role: str = 'UNKNOWN'
    weapon_ranged: Optional[bool] = None

@dataclass(frozen=True)
class Foe:
    actor_id: str
    pos: Optional[Point]
    alive: Optional[bool]
    visible: Optional[bool]
    target_id: Optional[str] = None     # verified current combat target, not LastAttackerOf
    can_damage: Optional[bool] = None
    weapon_effective: Optional[bool] = None
    hp_pct: Optional[float] = None

@dataclass(frozen=True)
class Scene:
    actor: Actor
    enemies: Tuple[Foe, ...]
    defender: Optional[Actor] = None
    command_origin: Origin = 'UNKNOWN'
    path_safety: Optional[bool] = None   # TRUE only from verified path query
    bard_song_mode: Optional[bool] = None
    manual_locked: Optional[bool] = None
    current_target_id: Optional[str] = None
    tick: int = 0

@dataclass(frozen=True)
class Advice:
    kind: Literal['NATIVE_FALLBACK','HOLD_AND_FIRE','REPOSITION_BEHIND_DEFENDER','NO_VIABLE_TARGET']
    reason: str
    proposed_target: Optional[str] = None
    proposed_position: Optional[Point] = None
    executable: bool = False  # Stage 022 has NO EXECUTOR, ALWAYS False


def distance(a: Point, b: Point) -> float:
    return hypot(a[0]-b[0], a[1]-b[1])


def behind_defender(foe: Foe, defender: Actor, desired_gap: float = 60.0) -> Optional[Point]:
    """Behind defender relative to foe, without any implicit path guarantee."""
    if foe.pos is None or defender.pos is None or defender.alive is not True:
        return None
    dx = defender.pos[0] - foe.pos[0]
    dy = defender.pos[1] - foe.pos[1]
    mag = hypot(dx,dy)
    if mag < 1e-6:
        return None
    return (round(defender.pos[0]+desired_gap*dx/mag, 1),
            round(defender.pos[1]+desired_gap*dy/mag, 1))


def _viable(e: Foe) -> bool:
    return e.alive is True and e.visible is True and e.can_damage is True and e.weapon_effective is True


def recommend(scene: Scene) -> Advice:
    # These guards are intentionally pessimistic. Unknown data never becomes
    # a permission to cancel a spell, bard song, player order or active AI action.
    a = scene.actor
    if a.alive is not True or a.pos is None or a.weapon_ranged is not True:
        return Advice('NATIVE_FALLBACK','Actor state or weapon not verified')
    if scene.command_origin != 'AI' or scene.manual_locked is not False:
        return Advice('NATIVE_FALLBACK','Manual command provenance/queue not cleared')
    if scene.bard_song_mode is not False:
        return Advice('NATIVE_FALLBACK','Preserve native bard song and spells')
    if not scene.enemies:
        return Advice('NATIVE_FALLBACK','No enemy evidence')
    valid = [e for e in scene.enemies if _viable(e)]
    if not valid:
        if any(e.visible is None or e.can_damage is None or e.weapon_effective is None or e.target_id is None
               for e in scene.enemies):
            return Advice('NATIVE_FALLBACK','Enemy/weapon evidence incomplete')
        return Advice('NO_VIABLE_TARGET','Known visible enemies cannot be damaged')
    # Defender must be an ACTUAL designated protector, not simply a nearby party actor.
    protector = scene.defender
    def_id = protector.actor_id if protector and protector.alive is True and protector.class_role == 'DEFENDER' else None
    if not def_id:
        return Advice('NATIVE_FALLBACK','No live designated defender')
    if any(e.target_id is None for e in valid):
        return Advice('NATIVE_FALLBACK','Current enemy target UNKNOWN: never infer aggro from logged actions')
    direct = [e for e in valid if e.target_id == a.actor_id]
    targeting_protector = [e for e in valid if e.target_id == def_id]
    # No chase off screen, no absolute RunAway. If path safety or position is
    # unavailable, the ordinary Advanced AI retains control.
    if direct:
        direct.sort(key=lambda e: distance(a.pos,e.pos) if e.pos else float('inf'))
        threat=direct[0]
        if threat.pos is None or distance(a.pos,threat.pos) > 100:
            return Advice('NATIVE_FALLBACK','Threat position unknown/far; keep original AI')
        if scene.path_safety is not True:
            return Advice('NATIVE_FALLBACK','No verified safe path behind tank')
        point=behind_defender(threat,protector)
        if point is None or protector.pos is None:
            return Advice('NATIVE_FALLBACK','Defender or foe position not confirmed')
        if distance(a.pos,point) > 220:
            return Advice('NATIVE_FALLBACK','Proposed movement would break squad leash')
        if distance(point,threat.pos)<distance(a.pos,threat.pos):
            return Advice('NATIVE_FALLBACK','Proposed position is closer to threat')
        return Advice('REPOSITION_BEHIND_DEFENDER', 'Safe route and defender geometry verified',
                      proposed_target=threat.actor_id,proposed_position=point)
    if targeting_protector:
        targeting_protector.sort(key=lambda e: (e.hp_pct if e.hp_pct is not None else 101.0,
                                                distance(a.pos,e.pos) if e.pos else float('inf')))
        return Advice('HOLD_AND_FIRE','Enemy occupies defender: avoid unnecessary retreat',
                      proposed_target=targeting_protector[0].actor_id)
    return Advice('NATIVE_FALLBACK','Enemy is attacking another or target not actionable')
