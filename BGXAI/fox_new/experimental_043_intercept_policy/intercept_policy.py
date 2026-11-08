#!/usr/bin/env python3
"""BGXAI 043: pure *offline* two-guard threat/cover decision prototype.

This module produces advisory INTENT records, never BAF, BCS, WeiDU commands,
input events, or game actions. No network access, no filesystem writes.
Game-side integration would require a separately verified event/EEex adapter.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import hypot
from typing import Literal
import json

Busy = Literal['idle', 'autoattack', 'manual', 'casting', 'bard-song', 'item-use', 'scripted']
Role = Literal['frontline', 'support', 'caster', 'bard']

@dataclass(frozen=True)
class Ally:
    uid: str
    x: float
    y: float
    hp: int
    max_hp: int
    living: bool = True
    def fraction(self) -> float:
        return min(1.0, max(0.0, self.hp / max(1, self.max_hp)))

@dataclass(frozen=True)
class Defender:
    uid: str
    x: float
    y: float
    hp: int
    max_hp: int
    guard_on: bool = True
    ai_on: bool = True
    role: Role = 'frontline'
    busy: Busy = 'idle'
    living: bool = True
    def fraction(self) -> float:
        return min(1.0, max(0.0, self.hp / max(1, self.max_hp)))

@dataclass(frozen=True)
class Enemy:
    uid: str
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    hostile_confirmed: bool = False
    visible: bool = False
    alive: bool = True
    attacking_uid: str | None = None

@dataclass(frozen=True)
class Snapshot:
    tick: int
    allies: tuple[Ally, ...]
    defenders: tuple[Defender, ...]
    enemies: tuple[Enemy, ...]
    party_ai_on: bool = True

@dataclass(frozen=True)
class Config:
    max_threat_range: float = 14.0  # policy-space units, NOT an engine-feet claim
    attack_range: float = 20.0
    intercept_eta_limit: float = 3.0  # policy ticks, requires calibrated adapter
    approach_contact_radius: float = 4.0
    minimum_closing_speed: float = 0.25
    min_interceptor_hp: float = 0.25
    min_cover_hp: float = 0.15
    threat_switch_advantage: float = 2.0
    defender_switch_advantage: float = 2.5
    hold_ticks: int = 2

@dataclass(frozen=True)
class Threat:
    enemy_uid: str
    ally_uid: str
    reason: str
    score: float
    distance: float
    eta: float | None

@dataclass(frozen=True)
class Plan:
    tick: int
    threat: Threat | None
    interceptor_uid: str | None
    cover_uid: str | None
    # Command suggestions only; caller never executes these automatically.
    intents: tuple[dict, ...]
    withheld_reason: str | None = None
    def as_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

@dataclass(frozen=True)
class Memory:
    threat_pair: tuple[str, str] | None = None
    interceptor_uid: str | None = None
    last_change_tick: int = -100000


def dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return hypot(x1-x2, y1-y2)


def detect_threats(snapshot: Snapshot, config: Config = Config()) -> tuple[Threat, ...]:
    """No aggression inference from proximity alone; require confirmed hostility AND
    explicit attack target or verified approach trajectory with imminent intercept.
    """
    found = []
    for enemy in snapshot.enemies:
        if not (enemy.alive and enemy.hostile_confirmed and enemy.visible):
            continue
        speed_sq = enemy.vx*enemy.vx + enemy.vy*enemy.vy
        for ally in snapshot.allies:
            if not (ally.living and ally.hp > 0):
                continue
            distance = dist(enemy.x, enemy.y, ally.x, ally.y)
            directly_attacking = enemy.attacking_uid == ally.uid and distance <= config.attack_range
            trajectory = False
            eta = None
            if speed_sq > 0:
                dx, dy = ally.x - enemy.x, ally.y - enemy.y
                closing_speed = (dx*enemy.vx + dy*enemy.vy) / max(distance, 1e-9)
                nearest_t = max(0.0, (dx*enemy.vx + dy*enemy.vy) / speed_sq)
                nearest_dist = dist(enemy.x + nearest_t*enemy.vx, enemy.y + nearest_t*enemy.vy, ally.x, ally.y)
                trajectory = (
                    distance <= config.max_threat_range
                    and closing_speed >= config.minimum_closing_speed
                    and nearest_t <= config.intercept_eta_limit
                    and nearest_dist <= config.approach_contact_radius
                )
                if trajectory:
                    eta = round(nearest_t, 3)
            if not directly_attacking and not trajectory:
                continue
            reason = 'CONFIRMED_ATTACK' if directly_attacking else 'CONFIRMED_CLOSING'
            urgency = 3.8 * (1.0 - ally.fraction())
            direct = 8.0 if directly_attacking else 0.0
            proximity = 0.55 * max(0.0, config.max_threat_range - distance)
            imminent = 0.7 * max(0.0, config.intercept_eta_limit - (eta or 0)) if trajectory else 0.0
            score = round(urgency + direct + proximity + imminent, 4)
            found.append(Threat(enemy.uid, ally.uid, reason, score, round(distance, 3), eta))
    return tuple(sorted(found, key=lambda t: (-t.score, t.ally_uid, t.enemy_uid)))


def observe_trajectory(previous: Snapshot | None, current: Snapshot, *, max_step: float = 20.0) -> Snapshot:
    """Safe, pure adapter: derive velocity from two verified consecutive ticks.

    Unknown/new/teleported enemies get zero velocity. An engine adapter must
    provide stable actor identities and calibrated ticks; otherwise the early
    approach condition is DISABLED, retaining only an explicit attack event.
    """
    from dataclasses import replace
    if previous is None or current.tick <= previous.tick:
        return replace(current, enemies=tuple(replace(e,vx=0.0,vy=0.0) for e in current.enemies))
    prev = {e.uid:e for e in previous.enemies if e.alive}
    dt = current.tick - previous.tick
    new = []
    for e in current.enemies:
        old = prev.get(e.uid)
        delta = dist(old.x,old.y,e.x,e.y) if old else float('inf')
        if not old or delta > max_step * dt:
            new.append(replace(e,vx=0.0,vy=0.0))
        else:
            new.append(replace(e,vx=(e.x-old.x)/dt,vy=(e.y-old.y)/dt))
    return replace(current,enemies=tuple(new))


def _eligible(d: Defender, c: Config, *, interceptor: bool) -> bool:
    if not (d.living and d.hp > 0 and d.guard_on and d.ai_on):
        return False
    if d.busy in ('manual', 'casting', 'bard-song', 'item-use', 'scripted'):
        return False
    if interceptor and (d.role not in ('frontline', 'support') or d.fraction() < c.min_interceptor_hp):
        return False
    if not interceptor and d.fraction() < c.min_cover_hp:
        return False
    return True


def _interceptor_score(d: Defender, enemy: Enemy, ally: Ally) -> float:
    # Class-aware and positional preference; do not send a bard/caster into melee.
    frontline = 6.0 if d.role == 'frontline' else 0.0
    proximity = -1.0 * dist(d.x, d.y, enemy.x, enemy.y)
    ally_proximity = -0.16 * dist(d.x, d.y, ally.x, ally.y)
    hp = 1.0 * d.fraction()
    ready = 1.5 if d.busy == 'idle' else 0.0
    return frontline + proximity + ally_proximity + hp + ready


def plan(snapshot: Snapshot, old: Memory = Memory(), config: Config = Config()) -> tuple[Plan, Memory]:
    if not snapshot.party_ai_on:
        return Plan(snapshot.tick, None, None, None, (), 'PARTY_AI_DISABLED'), Memory()
    threats = detect_threats(snapshot, config)
    if not threats:
        return Plan(snapshot.tick, None, None, None, (), 'NO_CONFIRMED_IMMINENT_THREAT'), Memory()
    threat = threats[0]
    if old.threat_pair and snapshot.tick - old.last_change_tick < config.hold_ticks:
        former = next((x for x in threats if (x.enemy_uid,x.ally_uid) == old.threat_pair), None)
        if former and former.score + config.threat_switch_advantage >= threat.score:
            threat = former
    ally = next(a for a in snapshot.allies if a.uid == threat.ally_uid)
    enemy = next(e for e in snapshot.enemies if e.uid == threat.enemy_uid)
    viable = [d for d in snapshot.defenders if d.uid != ally.uid and _eligible(d, config, interceptor=True)]
    if not viable:
        return Plan(snapshot.tick, threat, None, None, (), 'NO_ELIGIBLE_INTERCEPTOR'), Memory()
    # Prefer truly idle guardians over those still finishing an autoattack.
    # This avoids selecting a nearer-but-busy protector when a free one can react now.
    ready = [d for d in viable if d.busy == 'idle']
    candidate_pool = ready if ready else viable
    ranked = sorted(candidate_pool, key=lambda d: (-_interceptor_score(d, enemy, ally), d.uid))
    chosen = ranked[0]
    if old.interceptor_uid and snapshot.tick - old.last_change_tick < config.hold_ticks:
        prior = next((d for d in candidate_pool if d.uid == old.interceptor_uid), None)
        if prior and _interceptor_score(prior, enemy, ally) + config.defender_switch_advantage >= _interceptor_score(chosen, enemy, ally):
            chosen = prior
    # The second guardian covers the threatened ally. For safety, no second pursuit.
    cover_candidates = [d for d in snapshot.defenders if d.uid != chosen.uid and d.uid != ally.uid and _eligible(d, config, interceptor=False)]
    cover = min(cover_candidates, key=lambda d: (dist(d.x,d.y,ally.x,ally.y),d.uid), default=None)
    intents: list[dict] = []
    if chosen.busy == 'idle':
        intents.append({'actor':chosen.uid, 'kind':'INTERCEPT_WHEN_IDLE', 'enemy':threat.enemy_uid,
                        'protect':threat.ally_uid, 'warning':'ADVISORY_NOT_GAME_COMMAND'})
    else:
        # AttackOneRound is bounded, but scripts MUST NOT forcibly clear existing actions.
        intents.append({'actor':chosen.uid, 'kind':'DEFER_UNTIL_IDLE', 'protect':threat.ally_uid})
    if cover:
        if cover.busy == 'idle':
            intents.append({'actor':cover.uid, 'kind':'COVER_HOLD_POSITION', 'protect':threat.ally_uid,
                            'warning':'NO_MOVEMENT_ISSUED'})
        else:
            intents.append({'actor':cover.uid, 'kind':'DEFER_COVER_UNTIL_IDLE', 'protect':threat.ally_uid})
    pair = (threat.enemy_uid, threat.ally_uid)
    changed = pair != old.threat_pair or chosen.uid != old.interceptor_uid
    mem = Memory(pair,chosen.uid,snapshot.tick if changed else old.last_change_tick)
    return Plan(snapshot.tick, threat, chosen.uid, cover.uid if cover else None, tuple(intents)), mem


def example() -> str:
    # Similar to early-level incident: Jade at low HP, Shank is an active attacker.
    state=Snapshot(20, (Ally('Jade',0,0,1,6),),
        (Defender('Guard_A',3,0,14,14),Defender('Guard_B',0,2,14,14)),
        (Enemy('Shank',4,0,0,0,True,True,True,'Jade'),))
    result,_=plan(state)
    return result.as_json()

if __name__ == '__main__':
    print(example())