"""Source-only BG(2)EE APR key decoder. No game or item operations.

Reference: IESDP BG(2)EE opcode #1 'Attacks Per Round Modifier',
https://iesdp.bgforge.net/opcodes/bgee (Key/Attacks-per-Round table).

This returns a meaning for a *reported* key, NOT an effective, per-slot,
per-ability, full-effects-aware APR estimate. No weapon ranking/dispatch.
"""
from dataclasses import dataclass
from fractions import Fraction

KEY_APR = {0: Fraction(0), 1: Fraction(1), 2: Fraction(2),
           3: Fraction(3), 4: Fraction(4), 5: Fraction(5),
           6: Fraction(1, 2), 7: Fraction(3, 2),
           8: Fraction(5, 2), 9: Fraction(7, 2), 10: Fraction(9, 2)}


@dataclass(frozen=True)
class AprObservation:
    raw_key: int | None
    state: str
    source_value: Fraction | None
    reason: str
    effective_apr_verified: bool = False
    per_slot_apr_verified: bool = False
    weapon_switch_authorized: bool = False


def decode_source_apr_key(raw_key: object) -> AprObservation:
    if type(raw_key) is not int:
        return AprObservation(None, 'HOLD', None, 'RAW_KEY_NOT_INT')
    if raw_key not in KEY_APR:
        return AprObservation(raw_key, 'HOLD', None, 'RAW_KEY_OUTSIDE_DOCUMENTED_TABLE')
    return AprObservation(raw_key, 'SOURCE_KEY_DECODED_RO', KEY_APR[raw_key],
                          'SOURCE_KEY_ONLY_EFFECTS_AND_ALTERNATE_SLOTS_UNVERIFIED')


def compare_source_keys_only(first: object, second: object) -> dict:
    """A non-ranking diagnostic comparison. Do NOT use for weapon decisions."""
    a, b = decode_source_apr_key(first), decode_source_apr_key(second)
    return {
        'state': 'SOURCE_KEYS_BOTH_DECODED_RO' if a.source_value is not None
                   and b.source_value is not None else 'HOLD',
        'first': a, 'second': b,
        'raw_numeric_comparison_forbidden': True,
        'weapon_switch_authorized': False,
        'does_not_rank_weapons': True,
    }
