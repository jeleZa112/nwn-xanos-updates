"""Tactical decision engine for Zombie Rush Survival.

Never performs input or reads Roblox memory. A future visual detector can supply
observations to choose_action(). Keep this independent of the capture backend.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Observation:
    in_match: bool
    credits: Optional[int] = None
    turret_cost: Optional[int] = None
    turret_count: Optional[int] = None
    protected_core: bool = False
    core_turret_limit: int = 3
    core_safe: Optional[bool] = None
    frontline_intact: Optional[bool] = None
    perimeter_coverage: Optional[float] = None
    perimeter_cost: Optional[int] = None
    health_ratio: Optional[float] = None

@dataclass
class Decision:
    phase: str
    action: str
    reason: str

def choose_action(o: Observation) -> Decision:
    if not o.in_match:
        return Decision("LOBBY", "WAIT", "Waiting for a live match")
    if o.health_ratio is not None and o.health_ratio < 0.30:
        return Decision("SURVIVE", "RETREAT", "Health critically low")
    if o.frontline_intact is False and o.turret_count and o.turret_count > 0:
        return Decision("REPAIR", "REINFORCE_FRONT", "Protect placed turrets before expanding")
    if o.turret_count is None:
        return Decision("OBSERVE", "IDENTIFY_TURRETS", "Current turret count is unknown")
    if o.turret_count == 0:
        if o.credits is None or o.turret_cost is None:
            return Decision("FIRST_TURRET", "OBSERVE_COST", "Need in-match currency and turret price")
        if o.credits < o.turret_cost:
            return Decision("FIRST_TURRET", "SAVE", "Save for the first turret")
        return Decision("FIRST_TURRET", "PLACE_CORE", "First turret at safe chokepoint with line of sight")
    if o.core_safe is False:
        return Decision("FORTIFY_CORE", "REINFORCE_FRONT", "Protect first emplacement")
    if o.turret_count < max(1, o.core_turret_limit):
        if o.credits is None or o.turret_cost is None:
            return Decision("BUILD_CORE", "OBSERVE_COST", "Need reliable currency and turret price")
        if o.credits < o.turret_cost:
            return Decision("BUILD_CORE", "HOLD_BEHIND_CORE", "Save for another core turret")
        return Decision("BUILD_CORE", "PLACE_NEXT_CORE", "Place next turret in same defended firing zone")
    if o.frontline_intact is None or o.core_safe is None:
        return Decision("VERIFY_CORE", "INSPECT", "Confirm core is protected before expanding")
    if not o.protected_core:
        return Decision("VERIFY_CORE", "REINFORCE_FRONT", "Build a barrier in front of turret group")
    if o.perimeter_coverage is None:
        return Decision("PERIMETER", "SCOUT_APPROACHES", "Find unprotected enemy approaches")
    if o.perimeter_coverage >= 1.0:
        return Decision("MAINTAIN", "HOLD_AND_REPAIR", "Perimeter fully covered")
    if o.credits is None or o.perimeter_cost is None:
        return Decision("PERIMETER", "OBSERVE_COST", "Need cost of next perimeter defense")
    if o.credits < o.perimeter_cost:
        return Decision("PERIMETER", "SAVE", "Keep reserve; do not abandon core")
    return Decision("PERIMETER", "PLACE_OUTER_DEFENSE", "Cover weakest approach without blocking firing lanes")


def test():
    states = [
        (Observation(True, credits=30, turret_cost=100, turret_count=0), "SAVE"),
        (Observation(True, credits=100, turret_cost=100, turret_count=0), "PLACE_CORE"),
        (Observation(True, credits=50, turret_cost=100, turret_count=1), "HOLD_BEHIND_CORE"),
        (Observation(True, credits=120, turret_cost=100, turret_count=1), "PLACE_NEXT_CORE"),
        (Observation(True, credits=500, turret_cost=100, turret_count=3, protected_core=True, core_safe=True, frontline_intact=True, perimeter_coverage=.25, perimeter_cost=90), "PLACE_OUTER_DEFENSE"),
        (Observation(True, credits=500, turret_cost=100, turret_count=3, protected_core=True, core_safe=True, frontline_intact=False, perimeter_coverage=.25, perimeter_cost=90), "REINFORCE_FRONT"),
    ]
    for obs, expected in states:
        result = choose_action(obs)
        assert result.action == expected, (obs, result)
    print("STRATEGY SELFTEST OK", len(states), "cases")

if __name__ == "__main__":
    test()
