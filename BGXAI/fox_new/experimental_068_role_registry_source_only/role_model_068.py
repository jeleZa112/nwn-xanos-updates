"""BGXAI 068 SOURCE-ONLY class capability audit. NEVER imports EEex or writes to EET.

Class IDs are the standard BG(2)EE CLASS.IDS (compare user's private IDS before
any game integration). Runtime stance requires independently verified observations.
No commands, spells, or BGX local state are written by this module.
"""
from dataclasses import dataclass
from typing import FrozenSet

ROLE_DATA = {
 1: ('MAGE', {'arcane'}),
 2: ('FIGHTER', {'martial'}),
 3: ('CLERIC', {'divine_heal', 'divine'}),
 4: ('THIEF', {'thief'}),
 5: ('BARD', {'bard_song', 'arcane'}),
 6: ('PALADIN', {'martial', 'divine_limited'}),
 7: ('FIGHTER_MAGE', {'martial', 'arcane', 'hybrid'}),
 8: ('FIGHTER_CLERIC', {'martial', 'divine_heal', 'divine', 'hybrid'}),
 9: ('FIGHTER_THIEF', {'martial', 'thief', 'hybrid'}),
10: ('FIGHTER_MAGE_THIEF', {'martial', 'arcane', 'thief', 'hybrid'}),
11: ('DRUID', {'divine_heal', 'divine', 'shapeshift_possible'}),
12: ('RANGER', {'martial', 'divine_limited'}),
13: ('MAGE_THIEF', {'arcane', 'thief', 'hybrid'}),
14: ('CLERIC_MAGE', {'divine_heal', 'divine', 'arcane', 'hybrid'}),
15: ('CLERIC_THIEF', {'divine_heal', 'divine', 'thief', 'hybrid'}),
16: ('FIGHTER_DRUID', {'martial', 'divine_heal', 'divine', 'hybrid', 'shapeshift_possible'}),
17: ('FIGHTER_MAGE_CLERIC', {'martial', 'arcane', 'divine_heal', 'divine', 'hybrid'}),
18: ('CLERIC_RANGER', {'martial', 'divine_heal', 'divine', 'hybrid'}),
19: ('SORCERER', {'arcane'}),
20: ('MONK', {'skirmisher'}),
21: ('SHAMAN', {'divine_heal', 'divine', 'spirits'}),
}

@dataclass(frozen=True)
class Profile:
    class_id: int
    class_name: str
    capabilities: FrozenSet[str]
    source_certainty: str = 'CLASS_ID_ONLY'

@dataclass(frozen=True)
class Observation:
    f_enabled: bool = False
    idle: bool = False
    same_area: bool = False
    hp_percent: float | None = None
    effective_melee_verified: bool = False
    survivability_verified: bool = False
    manual_order_active: bool = False
    casting: bool = False
    singing: bool = False
    detecting_traps: bool = False
    heal_request_pending: bool = False
    is_dual_class: bool = False
    dual_old_class_active: bool | None = None
    shape_confirmed: bool = False
    shaped_melee_effective_verified: bool = False
    kit_name: str | None = None
    can_act: bool = False


def profile(class_id: int) -> Profile:
    if isinstance(class_id, bool) or not isinstance(class_id, int) or class_id not in ROLE_DATA:
        return Profile(class_id=class_id, class_name='UNKNOWN', capabilities=frozenset())
    name, flags = ROLE_DATA[class_id]
    return Profile(class_id, name, frozenset(flags))


def potential_interceptor(class_id: int, obs: Observation) -> tuple[bool, str]:
    """Conservative candidate assessment. Not an automatic or enabled game action.

    Explicitly identified dual-class characters require proof that their
    former class is active. Unknown dual progress fails closed.
    """
    p = profile(class_id)
    if p.class_name == 'UNKNOWN': return False, 'UNKNOWN_CLASS_FAIL_CLOSED'
    if not obs.f_enabled: return False, 'F_OFF'
    if not obs.can_act or not obs.idle or not obs.same_area: return False, 'NOT_FREE_IN_SAME_AREA'
    if obs.manual_order_active or obs.casting or obs.singing or obs.detecting_traps:
        return False, 'EPS_OR_MANUAL_ACTION_PRIORITY'
    if obs.heal_request_pending: return False, 'HEAL_FIRST'
    if obs.hp_percent is None or not 60 < obs.hp_percent <= 100:
        return False, 'INSUFFICIENT_HEALTH_CERTAINTY'
    if not obs.survivability_verified: return False, 'SURVIVABILITY_UNVERIFIED'
    if obs.is_dual_class and obs.dual_old_class_active is not True:
        return False, 'DUAL_OLD_CLASS_NOT_CONFIRMED_ACTIVE'
    if not obs.effective_melee_verified: return False, 'MELEE_NOT_VERIFIED'
    if 'martial' in p.capabilities: return True, 'MARTIAL_CANDIDATE_ONLY'
    if p.class_name == 'DRUID' and obs.kit_name == 'SHAPESHIFTER':
        if obs.shape_confirmed and obs.shaped_melee_effective_verified:
            return True, 'VERIFIED_SHAPESHIFTER_FORM_CANDIDATE_ONLY'
        return False, 'FORM_NOT_VERIFIED'
    return False, 'SUPPORT_ROLE_PREFERRED'


def possible_healer(class_id: int, *, actual_heal_ability_verified: bool,
                    dual_old_class_active: bool | None = None) -> bool:
    """Potential healing is not a request: spell/ability must exist and be usable."""
    return ('divine_heal' in profile(class_id).capabilities
            and actual_heal_ability_verified and dual_old_class_active is not False)
