"""Validate BGXAI 062E partial class/action samples; NEVER grant combat intents.

Source-level x64 EEex binding evidence is not proof of the installed user's runtime.
Class ID is *not* a capability bitset, and instantaneous action ID is *not*
proof that an AI action may override pending manual orders or queued EPS spells.
"""
from dataclasses import dataclass
from typing import Any

UNKNOWN = 'unknown'
ORIGIN = 'BGXAI_062E_SOURCE_ONLY'
BINDING = 'X64_EEEX_SOURCE_DOCUMENTED_RUNTIME_UNVERIFIED'
STATUS = {'API_UNAVAILABLE', 'PARTIAL_OBSERVATIONS_ONLY'}
UNPROVEN = ('equipped_weapon','can_melee','can_cast','manual_order_absent',
            'action_queue_idle','stealth_absent','consciousness','role')

@dataclass(frozen=True)
class Member:
    slot: int
    id: int
    guard_f: int | str
    modal: int | str
    class_id: int | str
    current_action_id: int | str
    intercept_authorized: bool = False

@dataclass(frozen=True)
class Report:
    status: str
    members: tuple[Member, ...]
    decision: str = 'OBSERVATION_ONLY'


def _uint(value: Any, upper: int, *, allow_unknown: bool = True) -> bool:
    return (allow_unknown and value == UNKNOWN and type(value) is str) or (
        type(value) is int and 0 <= value <= upper)


def validate(payload: Any) -> Report:
    if not isinstance(payload, dict):
        raise ValueError('INVALID_ENVELOPE')
    if (type(payload.get('schema')) is not int or payload['schema'] != 2
        or payload.get('mode') != 'READ_ONLY'
        or payload.get('origin') != ORIGIN or payload.get('binding') != BINDING):
        raise ValueError('INVALID_SCHEMA_OR_PROVENANCE')
    status = payload.get('status')
    if status not in STATUS:
        raise ValueError('INVALID_STATUS')
    party = payload.get('party')
    if not isinstance(party, list) or len(party) > 6:
        raise ValueError('INVALID_PARTY')
    if status == 'API_UNAVAILABLE' and party:
        raise ValueError('API_UNAVAILABLE_HAS_MEMBERS')
    slots, ids, members = set(), set(), []
    for entry in party:
        if not isinstance(entry, dict):
            raise ValueError('INVALID_MEMBER')
        slot, uid = entry.get('slot'), entry.get('id')
        if (not _uint(slot, 6, allow_unknown=False) or slot < 1 or slot in slots
            or not _uint(uid, 2147483646, allow_unknown=False) or uid in ids):
            raise ValueError('DUPLICATE_OR_INVALID_IDENTITY')
        slots.add(slot); ids.add(uid)
        guard = entry.get('guard_f')
        modal = entry.get('modal')
        class_id = entry.get('class_id')
        action_id = entry.get('current_action_id')
        if (not (guard == UNKNOWN and type(guard) is str or type(guard) is int and guard in (0,1))
            or not _uint(modal,65535) or not _uint(class_id,255)
            or not _uint(action_id,65535)):
            raise ValueError('BAD_OBSERVATION')
        for field in UNPROVEN:
            if entry.get(field) != UNKNOWN:
                raise ValueError('UNPROVEN_CAPABILITY_ASSERTION:'+field)
        members.append(Member(slot,uid,guard,modal,class_id,action_id))
    return Report(status,tuple(members))
