"""BGXAI R26: strict read-only co-location of R2 and R4 action-start records.

Consumes bounded console bytes. Reuses R25 for validation and exact console mirror
normalization. Co-located != one authenticated engine event. The output never
contains actor identity or raw user logs and grants no gameplay action.
"""
from __future__ import annotations
from collections import Counter
import json
import BGXAI_R25_CAPTURE_SEGMENT_RO as r25

SCHEMA = 'BGXAI_R26_R2_R4_COLOCATED_RO_V1'
APR = {**{i: float(i) for i in range(6)}, 6: .5, 7: 1.5, 8: 2.5, 9: 3.5, 10: 4.5}
KEYS = ('seq', 'actor', 'partyIndex', 'actionRaw', 'selectedWeaponRaw', 'selectedAbilityRaw')
UNVERIFIED_R2 = ('itemIdentityVerified', 'perSlotAPRVerified',
                 'manualOrderOriginVerified', 'epsQueueVerified', 'switchAuthorized')
UNVERIFIED_R4 = ('allBuffsObserved', 'allEffectsObserved', 'alternateSlotAPRVerified',
                 'manualOrderProven', 'epsQueueProven', 'weaponSwitchAuthorized',
                 'dispatchAuthorized')


def hold(reason: str) -> dict:
    return dict(schema=SCHEMA, status='HOLD_CROSS_OBSERVER_AUTHENTICATION', reason=reason,
                readOnly=True, sourceOnly=True, gameModified=False, ordersSent=0,
                gameActionsAuthorized=False, dispatchAuthorized=False,
                weaponSwitchAuthorized=False, nativeEventAuthenticated=False,
                fullEffectsVerified=False, alternativeAPRVerified=False,
                launcherAmmoPairVerified=False, manualEpsQueueVerified=False,
                safeSessionIdentityVerified=False, pairedCount=0, selectedAprSummary={})


def _strictint(x, low: int, high: int) -> bool:
    return type(x) is int and low <= x <= high


def inspect(console_bytes: bytes) -> dict:
    """Correlate already captured scalar observations, never native handles."""
    report = r25.inspect(console_bytes, source_type='console')
    if (report.get('status') != 'OFFLINE_LOG_SEGMENTS_VERIFIED_NO_RUNTIME_AUTH'
        or report.get('dispatchAuthorized') is not False
        or report.get('sessionIdEngineAuthenticated') is not False):
        return hold('R25_CAPTURE_VALIDATION_FAILED')
    segments = report['segments']
    if (len(segments) != 2 or {s['source'] for s in segments} != {'BGXW2', 'BGXW4'}
        or len(set(s['offlineCaptureToken'] for s in segments)) != 2):
        return hold('NOT_EXACTLY_ONE_R2_AND_ONE_R4_CAPTURE_SEGMENT')
    if (report['recordsBySource'].get('BGXW2') != report['recordsBySource'].get('BGXW4')
        or not 1 <= report['recordsBySource']['BGXW2'] <= 64):
        return hold('DIFFERENT_OBSERVER_EVENT_COUNTS')
    try:
        lines = console_bytes.decode('utf-8', 'strict').splitlines()
    except UnicodeDecodeError:
        return hold('INVALID_UTF8')
    data, markers = [], {'BGXW2': [], 'BGXW4': []}
    for line in lines:
        match = r25.CHANNEL.fullmatch(line)
        if not match or match.group(1) != 'LUA':
            continue
        source = match.group(2)
        try:
            event = json.loads(match.group(3))
        except ValueError:
            return hold('UNEXPECTED_POST_R25_INVALID_JSON')
        if event.get('type') in ('SESSION', 'READY'):
            markers[source].append(event['type'])
        else:
            data.append((source, event))
    if any(v != ['SESSION', 'READY'] for v in markers.values()):
        return hold('CONTROL_MARKER_ORDER_NOT_SINGLE_SESSION')
    if len(data) != 2 * report['recordsBySource']['BGXW2']:
        return hold('EVENT_COUNT_AFTER_MIRROR_NORMALIZATION_INCONSISTENT')
    counter, action_ids = Counter(), Counter()
    pairs = []
    for i in range(0, len(data), 2):
        (source2, e2), (source4, e4) = data[i], data[i + 1]
        if (source2, e2.get('type'), source4, e4.get('type')) != ('BGXW2', 'SLOTS', 'BGXW4', 'ACTIVE'):
            return hold('R2_R4_NOT_ADJACENT_IN_TAGGED_LUA_STREAM')
        if e2.get('status') != 'RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN' or e4.get('status') != 'RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS':
            return hold('SOURCE_OBSERVER_STATUS_UNRECOGNIZED')
        if any(e2.get(k) is not False for k in UNVERIFIED_R2) or any(e4.get(k) is not False for k in UNVERIFIED_R4):
            return hold('FALSIFIED_RUNTIME_AUTHORIZATION_OR_INCOMPLETE_EFFECT_FLAGS')
        if any(e2.get(k) != e4.get(k) for k in KEYS):
            return hold('CORRELATED_ACTION_SCALAR_MISMATCH')
        if not (_strictint(e2.get('seq'), 1, 64) and e2['seq'] == len(pairs) + 1
                and _strictint(e2.get('actor'), 1, 2_147_483_647)
                and _strictint(e2.get('partyIndex'), 0, 5)
                and _strictint(e2.get('actionRaw'), 0, 65535)
                and _strictint(e2.get('selectedAbilityRaw'), 0, 255)
                and _strictint(e2.get('selectedWeaponRaw'), 9, 38)
                and e2['selectedWeaponRaw'] in (9, 10, 11, 12, 13, 14, 35, 36, 37, 38)):
            return hold('MALFORMED_ACTION_SELECTED_WEAPON_OR_SEQUENCE')
        stats = e4.get('statsRaw')
        if not isinstance(stats, dict) or not _strictint(stats.get('m_nNumberOfAttacks'), 0, 10):
            return hold('SELECTED_APR_RAW_UNTRUSTED')
        if not (_strictint(e4.get('presentCount'), 0, 100) and
                _strictint(e4.get('missingCount'), 0, 100)):
            return hold('INVALID_ACTIVE_STATS_COUNT')
        key = (str(e2['selectedWeaponRaw']), str(stats['m_nNumberOfAttacks']))
        counter[key] += 1
        action_ids[str(e2['actionRaw'])] += 1
        pairs.append((e2['actor'], e2['partyIndex']))
    if len(set(pairs)) != 1:
        return hold('CROSS_ACTOR_OR_PARTY_INDEX_CHANGED')
    return dict(schema=SCHEMA, status='STRICT_R2_R4_COLOCATED_CANDIDATES_NO_ENGINE_EVENT_PROOF',
                reason='MATCHED_ADJACENT_LUA_SOURCE_SEQUENCES_AND_SIX_SHARED_SCALARS',
                readOnly=True, sourceOnly=True, gameModified=False, ordersSent=0,
                gameActionsAuthorized=False, dispatchAuthorized=False,
                weaponSwitchAuthorized=False, nativeEventAuthenticated=False,
                fullEffectsVerified=False, alternativeAPRVerified=False,
                launcherAmmoPairVerified=False, manualEpsQueueVerified=False,
                safeSessionIdentityVerified=False, pairedCount=len(pairs),
                r25MirrorPairsRemoved=report['mirroredPairsRemoved'],
                selectedAprSummary={f'slot_{slot}_rawAPR_{apr}':n
                                    for (slot, apr), n in sorted(counter.items())},
                actionRawCounts=dict(sorted(action_ids.items())),
                pairStatus='COLOCATED_NOT_NATIVE_AUTHENTICATED',
                nextAction='KEEP_CURRENT_WEAPON_NO_DISPATCH')
