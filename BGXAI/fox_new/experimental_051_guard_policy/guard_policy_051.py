"""BGXAI 051: strict offline eligibility/planning policy, not an EEex installer.

Purpose: separate confirmed-hit facts from *permission to execute* a BCS
ProtectObject action. Never issues, queues, or cancels any action.

All live fields (F mode / idle / visibility / distance / modal / cooldown) MUST
be verified by the relevant engine immediately before BCS command execution.
This Python model is not proof those observations exist in runtime EEex.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

MAX_THREAT_TICKS = 90  # prototype only; in-game time scale to be verified

@dataclass(frozen=True)
class Threat:
    attacker_id: int
    victim_id: int
    victim_slot: int  # portrait slot in 1..6, unlike EEex 0-based index
    sequence: int
    observed_tick: Optional[int]
    confirmed_engine_hit: bool

@dataclass(frozen=True)
class Guardian:
    actor_id: int
    portrait_slot: int
    mode_f: Optional[int]
    is_idle: Optional[bool]
    current_modal: Optional[str]
    visible_victim: Optional[bool]
    visible_attacker: Optional[bool]
    distance_victim: Optional[int]
    distance_attacker: Optional[int]
    cooldown_ready: Optional[bool]
    origin_safe: Optional[bool]  # True only if safe not to interrupt manual orders
    role: str = "unknown"

@dataclass(frozen=True)
class Decision:
    status: str
    assigned_id: Optional[int]
    victim_slot: Optional[int]
    reason: str
    event_sequence: Optional[int]
    command_sent: bool = False


def guard_decision(threat: Threat, guardians: Tuple[Guardian, ...], now_tick: Optional[int],
                   previous_event_sequence: Optional[int] = None) -> Decision:
    """Fail-closed decision candidate; 'READY' is NOT engine action dispatch."""
    def no(reason):
        return Decision("NO_DISPATCH", None, None, reason, threat.sequence)
    if not threat.confirmed_engine_hit:
        return no("not_confirmed_hit")
    if threat.attacker_id < 0 or threat.victim_id < 0 or threat.attacker_id == threat.victim_id:
        return no("invalid_attacker_victim")
    if threat.victim_slot not in range(1, 7):
        return no("invalid_victim_slot")
    if not isinstance(threat.sequence, int) or threat.sequence < 1:
        return no("invalid_sequence")
    if previous_event_sequence is not None and threat.sequence <= previous_event_sequence:
        return no("duplicate_or_old_event")
    if now_tick is None or threat.observed_tick is None:
        return no("clock_unavailable")
    if now_tick < threat.observed_tick:
        return no("non_monotonic_clock")
    if now_tick - threat.observed_tick > MAX_THREAT_TICKS:
        return no("stale_threat")
    accepted = []
    seen = set()
    for g in guardians:
        if g.actor_id in seen:
            continue
        seen.add(g.actor_id)
        if g.actor_id in (threat.attacker_id, threat.victim_id) or g.portrait_slot == threat.victim_slot:
            continue
        if g.portrait_slot not in range(2, 7):  # 042B team guard excludes Player1
            continue
        if g.mode_f != 1 or g.is_idle is not True or g.origin_safe is not True:
            continue
        if g.current_modal != "NONE":
            continue
        if g.cooldown_ready is not True:
            continue
        if g.visible_victim is not True or g.visible_attacker is not True:
            continue
        if g.distance_victim is None or not 0 <= g.distance_victim <= 10:
            continue
        if g.distance_attacker is None or not 0 <= g.distance_attacker <= 7:
            continue
        accepted.append(g)
    if not accepted:
        return no("no_verified_idle_guardian")
    # Explicit stable policy: lowest distance to victim, then slot. Role not
    # consulted until enough game evidence exists to score it safely.
    selected = min(accepted, key=lambda g: (g.distance_victim, g.portrait_slot))
    return Decision("READY_FOR_BCS_GATING", selected.actor_id, threat.victim_slot,
                    "qualified_candidate_only", threat.sequence, command_sent=False)
