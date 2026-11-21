#!/usr/bin/env python3
"""BGXAI role-aware AOE + weapon arbitration V1. SOURCE/TEST ONLY, NO ACTIONS.

Compose the already-audited BGX121 ellipse/path policy without inventing
live EEex state. This is NOT an executable AI, BCS patch or automatic installer.
The caller must verify actual target hostility, current action provenance,
class/dual/kit/role, scene completeness, equipment, ammunition, hazard metadata
and any path. Unknowns are deliberately NOT granted permission to act.
Never preempt manual orders, EPS healing, spells, songs or summons.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from BGX121_POLICY import Ally, Hazard, affected, safe_aoe, path_crosses

ROLES = frozenset(("FRONTLINE", "RANGED", "CASTER", "THIEF", "HYBRID"))
DUAL = frozenset(("NONE", "INACTIVE_PREVIOUS", "REACTIVATED"))

@dataclass(frozen=True)
class Situation:
    actor: Ally
    position: tuple[float, float]
    melee_position: tuple[float, float]
    role: str
    role_verified: bool
    class_and_kit_verified: bool
    dual_state: str
    dual_state_verified: bool
    manual_order_active: bool | None
    currently_casting: bool | None
    eps_heal_reserved: bool | None
    bard_song_reserved: bool | None
    target_hostile_visible_verified: bool
    hostile_ally_target_excluded: bool
    hazard_list_complete: bool
    close_enemy_verified: bool
    can_sustain_melee: bool | None
    melee_quickslot_verified: bool
    ranged_quickslot_verified: bool
    ranged_ammo_verified: bool
    single_target_spell_verified: bool
    spell_resource_verified: bool
    third_edition_backstab_enabled: bool = False
    stealth_verified: bool = False
    backstab_melee_verified: bool = False
    backstab_target_vulnerable_verified: bool = False
    safe_escape_destination: tuple[float, float] | None = None
    escape_route_verified: bool = False
    proposed_aoe: Hazard | None = None
    aoe_spell_verified: bool = False

@dataclass(frozen=True)
class Advice:
    code: str
    executable: bool = False
    reason: str = ""

def _point(value: tuple[float, float] | None) -> bool:
    return (isinstance(value, tuple) and len(value) == 2 and
            all(isinstance(x, (float, int)) and not isinstance(x, bool)
                and isfinite(x) for x in value))

def _safe(ally: Ally, hazards: tuple[Hazard, ...]) -> bool:
    return not any(affected(ally, h) for h in hazards)

def advise(s: Situation, allies: Iterable[Ally],
           hazards: Iterable[Hazard], roster_complete: bool) -> Advice:
    """An advisory recommendation. NEVER actions, inventory edits, or file writes."""
    if not isinstance(s, Situation) or not isinstance(s.actor, Ally):
        return Advice("HOLD_INVALID_SCENE")
    if s.manual_order_active is not False:
        return Advice("HOLD_MANUAL_ORDER_OR_UNKNOWN")
    if s.currently_casting is not False or s.bard_song_reserved is not False:
        return Advice("HOLD_SPELL_SONG_OR_UNKNOWN")
    if s.eps_heal_reserved is True:
        return Advice("DEFER_TO_EPS_HEAL")
    if s.eps_heal_reserved is not False:
        return Advice("HOLD_EPS_STATE_UNKNOWN")
    if (s.role not in ROLES or s.role_verified is not True or
        s.class_and_kit_verified is not True or
        s.dual_state not in DUAL or s.dual_state_verified is not True):
        return Advice("HOLD_ROLE_DUAL_KIT_UNVERIFIED")
    if not s.target_hostile_visible_verified or not s.hostile_ally_target_excluded:
        return Advice("HOLD_ENEMY_OR_FRIENDLY_STATUS_UNVERIFIED")
    if not s.hazard_list_complete or not _point(s.position) or not _point(s.melee_position):
        return Advice("HOLD_HAZARD_SNAPSHOT_INCOMPLETE")
    hazards=tuple(hazards)
    allies=tuple(allies)
    if (any(not isinstance(h, Hazard) or h.area != s.actor.area or
            not _point((h.x,h.y)) or
            not isinstance(h.radius_px,(float,int)) or
            not isfinite(h.radius_px) or h.radius_px <= 0 or
            not isinstance(h.harmful_effects,frozenset)
            for h in hazards) or
        any(not isinstance(a, Ally) for a in allies)):
        return Advice("HOLD_HAZARD_OR_ROSTER_INVALID")
    current=Ally(s.actor.ident,s.position[0],s.position[1],s.actor.area,
                 s.actor.immune_to,s.actor.alive)
    if not current.alive:
        return Advice("HOLD_ACTOR_NOT_ALIVE")
    safe_here=_safe(current,hazards)

    def retreat() -> bool:
        dest=s.safe_escape_destination
        if not s.escape_route_verified or not _point(dest):
            return False
        at=Ally(current.ident,dest[0],dest[1],current.area,
                current.immune_to,current.alive)
        if not _safe(at,hazards):
            return False
        # No invented pathfinder: explicit EEex route proof is required.
        return True

    if not safe_here:
        if retreat():
            return Advice("RETREAT_VERIFIED_ROUTE",reason="IN_HAZARD_ROUTE_EXTERNAL_VERIFIED")
        return Advice("HOLD_HAZARD_EGRESS_UNVERIFIED")

    path_unsafe=any(path_crosses(s.position,s.melee_position,h,current)
                    for h in hazards)
    # An unverified effect is never deemed safe for party/summons, even if
    # an earlier saved creature looked immune. Only exact effect immunity counts.
    if s.proposed_aoe is not None and s.role in ("CASTER","HYBRID"):
        if s.aoe_spell_verified and s.spell_resource_verified:
            allowed,unsafe=safe_aoe(s.proposed_aoe,allies,roster_complete)
            if allowed and (s.proposed_aoe.area==s.actor.area) and \
                    s.proposed_aoe.harmful_effects:
                return Advice("AOE_SAFE_CANDIDATE",reason="ALL_ALLIES_AND_SUMMONS_CLEARED")
        # Fall through to a safer single-target or ordinary ranged choice.

    ranged_ready=s.ranged_quickslot_verified and s.ranged_ammo_verified
    single_spell=s.single_target_spell_verified and s.spell_resource_verified
    if path_unsafe:
        if ranged_ready:
            return Advice("RANGED_HOLD_SAFE_POSITION",reason="MELEE_PATH_INTERSECTS_HAZARD")
        if single_spell and s.role in ("CASTER","HYBRID"):
            return Advice("SINGLE_TARGET_SPELL_SAFE_POSITION",
                          reason="MELEE_PATH_INTERSECTS_HAZARD")
        if retreat():
            return Advice("RETREAT_VERIFIED_ROUTE",reason="NO_SAFE_ATTACK_PATH")
        return Advice("HOLD_AVOID_DANGEROUS_AOE")

    if (s.role == "THIEF" and s.third_edition_backstab_enabled and
        s.stealth_verified and s.backstab_melee_verified and
        s.backstab_target_vulnerable_verified and
        s.melee_quickslot_verified and s.can_sustain_melee is True):
        return Advice("BACKSTAB_MELEE_CANDIDATE",reason="3E_MELEE_ONLY_CONFIRMED")

    if s.close_enemy_verified and s.role in ("CASTER","THIEF","RANGED"):
        if retreat():
            return Advice("RETREAT_VERIFIED_ROUTE",reason="FRAGILE_OR_RANGED_ROLE_AT_RISK")
        if ranged_ready:
            return Advice("RANGED_HOLD_SAFE_POSITION",reason="NO_VERIFIED_SAFE_RETREAT")
        if single_spell and s.role == "CASTER":
            return Advice("SINGLE_TARGET_SPELL_SAFE_POSITION")
        return Advice("HOLD_NO_SAFE_FRAGILE_ENGAGEMENT")

    if (s.role in ("FRONTLINE","HYBRID") and
        s.can_sustain_melee is True and s.melee_quickslot_verified):
        return Advice("MELEE_CANDIDATE",reason="SAFE_PATH_AND_VERIFIED_SURVIVABILITY")
    if ranged_ready:
        return Advice("RANGED_HOLD_SAFE_POSITION",reason="VERIFIED_RANGED_AMMO")
    if single_spell and s.role in ("CASTER","HYBRID"):
        return Advice("SINGLE_TARGET_SPELL_SAFE_POSITION")
    return Advice("HOLD_NO_VERIFIED_SAFE_ACTION")
