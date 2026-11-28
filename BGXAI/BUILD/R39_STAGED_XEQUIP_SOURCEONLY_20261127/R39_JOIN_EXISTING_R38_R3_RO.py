#!/usr/bin/env python3
"""Join EXISTING R38 real captured context and EXISTING R3 item proof (read-only).

Never copies raw actor IDs, paths, or captured console to the published result.
All gates fail closed.  This verifies *physical slot/strength compatibility* only;
kit/ITM usability, effects, manual/EPS origin, and real XEquip remain unknown.

Example (for project reviewer, NOT a new Windows user-facing command):
  python R39_JOIN_EXISTING_R38_R3_RO.py --r38-console ... --r3-item ...
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

SCHEMA = 'BGXAI_R39_R38_R3_EXISTING_EVIDENCE_JOIN_V1'
PREFIXES = {'[BGXR27] ': 'BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
            '[BGXID] ': 'BGXAI_XEQUIP_IDENTITY_RO_V1'}
RESREF = 'STAF01'
ITEM_SHA = 'c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3'
MIN_EVENTS = 10
MAX_LOG_BYTES = 64_000_000


class Hold(ValueError):
    pass


def require(c, label):
    if not c:
        raise Hold(label)


def raw_events(log: Path):
    require(log.is_file() and not log.is_symlink() and 0 < log.stat().st_size <= MAX_LOG_BYTES,
            'HOLD_MISSING_OR_UNTRUSTED_R38_LOG')
    sets = {key: {} for key in PREFIXES}
    sessions = collections.Counter()
    with log.open('rb') as stream:
        for lineno, raw in enumerate(stream, 1):
            hit = [p for p in PREFIXES if p.encode() in raw]
            if not hit:
                continue
            require(len(hit) == 1, 'HOLD_AMBIGUOUS_CAPTURE_LINE')
            prefix = hit[0]
            try:
                value = json.loads(raw.split(prefix.encode(), 1)[1].decode('utf-8-sig').strip())
            except (UnicodeDecodeError, ValueError) as e:
                raise Hold('HOLD_BAD_R38_JSON') from e
            require(type(value) is dict and value.get('schema') == PREFIXES[prefix],
                    'HOLD_R38_SCHEMA_DRIFT')
            if value.get('type') == 'SESSION':
                sessions[prefix] += 1
                continue
            seq, party = value.get('seq'), value.get('partyIndex')
            require(type(seq) is int and 1 <= seq <= 64 and type(party) is int and 0 <= party < 6,
                    'HOLD_BAD_R38_SEQUENCE_OR_PARTY')
            require(seq not in sets[prefix], 'HOLD_DUPLICATE_SEQUENCE')
            require(value.get('readOnly') is True and value.get('ordersSent') == 0 and
                    value.get('dispatchAuthorized') is False, 'HOLD_R38_NOT_PASSIVE')
            if prefix == '[BGXID] ':
                require(value.get('armAuthorized') is False, 'HOLD_IDENTITY_HAS_ARM')
            sets[prefix][seq] = value
    require(sessions['[BGXR27] '] == 1 and sessions['[BGXID] '] == 0,
            'HOLD_R38_SESSION_COUNT_UNEXPECTED')
    require(sets['[BGXR27] '] and sets['[BGXR27] '].keys() == sets['[BGXID] '].keys(),
            'HOLD_R38_IDENTITY_EVENT_ALIGNMENT')
    return sets


def check_item(items: dict):
    require(type(items) is dict and items.get('schema') == 'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY'
            and items.get('status') == 'ITM_NATIVE_ALL_ITEMS_RAW_READ'
            and items.get('sourceKind') == 'CURRENT_GAME'
            and items.get('gameModified') is False
            and items.get('dispatchAuthorized') is False,
            'HOLD_ITEM_REPORT_PROVENANCE')
    it = items.get('items')
    require(type(it) is dict and RESREF in it, 'HOLD_STAF01_NOT_IN_RESOURCE_REPORT')
    entry = it[RESREF]
    require(type(entry) is dict and type(entry.get('provenance')) is dict
            and type(entry.get('item')) is dict, 'HOLD_STAF01_REPORT_MALFORMED')
    src = entry['provenance']; item = entry['item']
    require(src.get('origin') == 'CURRENT_GAME_OVERRIDE' and src.get('sha256') == ITEM_SHA,
            'HOLD_STAF01_RESOURCE_SHA_OR_SOURCE_DRIFT')
    require(item.get('schema') == 'BGXAI_ITM_RAW_V1'
            and item.get('itemTypeRaw') == 26 and item.get('twoHandedFlagRaw') is True
            and item.get('minStrengthRaw') == 5 and item.get('itemFlagsRaw') == 46
            and item.get('rawOnly') is True and item.get('characterCanEquipVerified') is False,
            'HOLD_STAF01_EXPECTED_ITEM_PROFILE_DRIFT')
    require(type(item.get('abilities')) is list and len(item['abilities']) >= 1
            and item['abilities'][0].get('attackTypeRaw') == 1,
            'HOLD_STAF01_MELEE_ABILITY_UNVERIFIED')
    return item


def _getslot(group, slot):
    require(type(group) is list, 'HOLD_SLOT_GROUP_MALFORMED')
    sel = [s for s in group if type(s) is dict and s.get('slot') == slot]
    require(len(sel) == 1, 'HOLD_SLOT_NOT_UNIQUELY_OBSERVED')
    return sel[0]


def raw_script_evidence(candidate: list[dict]):
    """Reuse R38 same-callback raw script/action fields without guessing BCS."""
    observed = collections.Counter()
    raw_source_count = 0
    for record in candidate:
        stable = record.get('actionContextSnapshotStable')
        script_number = record.get('currentScriptNumberRaw')
        require(stable is None or type(stable) is bool,
                'HOLD_R38_SCRIPT_CONTEXT_FLAG_MALFORMED')
        if stable is True:
            if script_number is not None:
                require(type(script_number) is int and -32768 <= script_number <= 32767,
                        'HOLD_R38_CURRENT_SCRIPT_RAW_INVALID')
                observed[script_number] += 1
        else:
            require(script_number is None, 'HOLD_UNSTABLE_R38_SCRIPT_RAW')
        source_stable = record.get('actionSourceStable')
        require(source_stable is None or type(source_stable) is bool,
                'HOLD_R38_SOURCE_STABILITY_FLAG_MALFORMED')
        if source_stable is True:
            raw = record.get('actionSourceRaw')
            require(record.get('actionSourceReadStatus') == 'SOURCE_RAW_OBSERVED' and
                    type(raw) is str and 1 <= len(raw) <= 48 and
                    all(32 <= ord(ch) <= 126 for ch in raw),
                    'HOLD_R38_SOURCE_RAW_UNTRUSTED')
            raw_source_count += 1
        else:
            require(record.get('actionSourceRaw') is None,
                    'HOLD_UNSTABLE_R38_SOURCE_RAW')
    return {
        'rawCurrentScriptNumberEvents': sum(observed.values()),
        'rawCurrentScriptNumberHistogram': [
            {'valueRaw': n, 'events': count}
            for n, count in sorted(observed.items())
        ],
        'unclassifiedRawActionSourceAvailableEvents': raw_source_count,
        'rawActionSourceContentPublished': False,
        'rawScriptNumberMappedToSCRLEV': False,
        'actualBcsExecutionVerified': False,
        'scriptSlotOwnershipVerified': False,
        'manualEpsActionOriginVerified': False,
    }


def evaluate(captured: dict, item: dict):
    r27, rid = captured['[BGXR27] '], captured['[BGXID] ']
    require(len(r27) == len(rid) and len(r27) >= MIN_EVENTS,
            'HOLD_TOO_FEW_R38_ALIGNED_EVENTS')
    candidate = []
    outsiders = []
    for seq in sorted(r27):
        x,y = r27[seq],rid[seq]
        require(y.get('partyIndex') == x.get('partyIndex'), 'HOLD_CROSS_STREAM_PARTY_DRIFT')
        require(x.get('type') == 'R27_SINGLE_CALLBACK'
                and y.get('type') == 'IDENTITY_ADVISORY', 'HOLD_EVENT_TYPE_DRIFT')
        if y.get('status') == 'RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM':
            candidate.append(x)
            require(x.get('partyIndex') == 1, 'HOLD_JAGAN_PORTAIT_INDEX_DRIFT')
        else:
            require(y.get('status') == 'HOLD_WRONG_PORTRAIT_CONTEXT',
                    'HOLD_UNKNOWN_OTHER_ACTOR_IDENTITY_STATUS')
            outsiders.append(x)
    require(len(candidate) >= MIN_EVENTS, 'HOLD_NOT_ENOUGH_JAGAN_MATCHES')
    require(len({x.get('actor') for x in candidate}) == 1 and
            type(candidate[0].get('actor')) is int and candidate[0]['actor'] > 0,
            'HOLD_JAGAN_RUNTIME_ID_CHANGED')
    require(all(x.get('actor') != candidate[0]['actor'] for x in outsiders),
            'HOLD_OTHER_ACTOR_SHARES_JAGAN_ID')
    requires = {
        'sameLuaListenerInvocation': True,
        'readOnly': True,
        'ordersSent': 0,
        'dispatchAuthorized': False,
        'weaponSwitchAuthorized': False,
        'actionOriginVerified': False,
        'manualEpsQueueVerified': False,
    }
    for x in candidate:
        for name,value in requires.items():
            require(x.get(name) == value, 'HOLD_JAGAN_EVENT_CONTRACT_'+name.upper())
        require(x.get('rawInventoryDoubleReadConsistent') is True,
                'HOLD_SLOTS_NOT_DOUBLE_READ_STABLE')
        require(x.get('selectedDerivedStatsDoubleReadConsistent') is True,
                'HOLD_STRENGTH_NOT_DOUBLE_READ_STABLE')
        levels = x.get('levelsAndKitRaw')
        require(type(levels) is dict and x.get('aiObjectClassRawCandidate') == 3 and
                levels.get('kitRaw') == 16384,
                'HOLD_JAGAN_RAW_CLASS_OR_KIT_DRIFT')
        strength = x.get('selectedStatsRaw', {}).get('m_nSTR')
        require(type(strength) is int and strength >= item['minStrengthRaw'],
                'HOLD_CURRENT_STRENGTH_TOO_LOW_OR_UNKNOWN')
        require(_getslot(x.get('offhandRaw'), 9).get('resrefRaw') is None,
                'HOLD_OFFHAND_OCCUPIED_OR_UNOBSERVED')
        require(_getslot(x.get('quickWeaponsRaw'), 35).get('resrefRaw') is None,
                'HOLD_WEAPON_SLOT35_OCCUPIED_OR_UNOBSERVED')
    out = {'schema': SCHEMA,
       'status': 'PASS_OBSERVED_STRENGTH_AND_PHYSICAL_SLOTS_USABILITY_UNPROVEN',
       'r38AlignedEvents': len(r27), 'jaganMatchingEvents': len(candidate),
       'otherActorEventsFiltered': len(outsiders),
       'sameJaganRuntimeActorAcrossObservations': True,
       'sourceResref': RESREF, 'observedPartyIndex': 1,
       'minimumStrengthFromItem': item['minStrengthRaw'],
       'observedStrengthRange': [min(x['selectedStatsRaw']['m_nSTR'] for x in candidate),
                                  max(x['selectedStatsRaw']['m_nSTR'] for x in candidate)],
       'offhandSlot9EmptyInAllJaganEvents': True,
       'targetSlot35EmptyInAllJaganEvents': True,
       'classRaw3ClericObserved': True, 'kitRaw16384Observed': True,
       'sameSessionInstalledItemResourceVerified': False,
       'itemClassKitRestrictionBitsVerified': False,
       'currentEffectBlocksEquippingVerified': False,
       'manualEpsActionOriginVerified': False,
       'gameIdleAtDispatchVerified': False,
       'actorRuntimeArmingImplemented': False,
       'armAuthorized': False, 'dispatchAuthorized': False,
       'ordersSent': 0, 'gameModified': False,
       'liveXEquipTransferVerified': False}
    out.update(raw_script_evidence(candidate))
    return out


def analyze(log: Path, r3_item: Path):
    require(r3_item.is_file() and not r3_item.is_symlink() and
            0 < r3_item.stat().st_size < 500_000, 'HOLD_ITEM_REPORT_FILE_UNTRUSTED')
    item = check_item(json.loads(r3_item.read_text(encoding='utf-8-sig')))
    return evaluate(raw_events(log),item)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--r38-console',type=Path,required=True)
    p.add_argument('--r3-item',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        out = analyze(a.r38_console,a.r3_item)
        print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,UnicodeError,Hold) as err:
        print(json.dumps({'schema': SCHEMA, 'status': 'HOLD_NO_GAME_ACTION',
            'reason':str(err) if isinstance(err,Hold) else 'HOLD_INPUT_OR_JSON',
            'gameModified':False,'armAuthorized':False,
            'dispatchAuthorized':False,'ordersSent':0},ensure_ascii=False))
        return 3

if __name__ == '__main__':
    sys.exit(main())
