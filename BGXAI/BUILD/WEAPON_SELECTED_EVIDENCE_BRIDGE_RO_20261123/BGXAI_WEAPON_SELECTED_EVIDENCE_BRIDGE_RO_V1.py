"""Offline BGXAI R13.2+R4+R1(+R2) observation bridge. No game writes.

Interpretation is limited to CURRENT selected equipment at the observed action.
Ordered nearby console lines are NOT an authenticated native same-event token.
No alternate-slot APR, readiness for autonomous choice, or dispatch authority.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from apr_key_decoder_ro import decode_source_apr_key

MAX_BYTES = 2_000_000
MAX_LINES = 20_000
MAX_PAIRS = 64
PAIR_DISTANCE = 8
MARKERS = {
    '[BGXTD13]': 'R13',
    '[BGXW4]': 'R4',
    '[BGXWP]': 'R1',
    '[BGXW2]': 'R2',
}
FIELDS = (
    'm_nArmorClass', 'm_nACCrushingMod', 'm_nACMissileMod',
    'm_nACPiercingMod', 'm_nACSlashingMod',
    'm_nResistCrushing', 'm_nResistPiercing', 'm_nResistSlashing',
    'm_nResistMissile',
)


def int_in(x: Any, low: int, high: int) -> bool:
    return type(x) is int and low <= x <= high


def hold(reason: str, **data: Any) -> dict:
    return {'status': 'HOLD', 'reason': reason, 'dispatchAuthorized': False,
            'weaponSwitchAuthorized': False, **data}


def _read(path: Path) -> tuple[str, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError('INPUT_NOT_REGULAR')
    before = path.stat()
    if not (1 <= before.st_size <= MAX_BYTES):
        raise ValueError('INPUT_SIZE_REJECTED')
    raw = path.read_bytes()
    after = path.stat()
    if before.st_size != len(raw) or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError('INPUT_CHANGED_DURING_READ')
    return raw.decode('utf-8-sig', errors='strict'), hashlib.sha256(raw).hexdigest()


def _parse(text: str) -> tuple[list[dict], list[dict]]:
    out, invalid = [], []
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        raise ValueError('TOO_MANY_LINES')
    for no, line in enumerate(lines, 1):
        if 'LUA:' not in line or 'LPRINT:' in line:
            continue
        for marker, source in MARKERS.items():
            marker_at = line.find(marker)
            if marker_at < 0:
                continue
            content = line[marker_at + len(marker):].strip()
            if not content.startswith('{'):
                break
            try:
                obj = json.loads(content)
            except (ValueError, json.JSONDecodeError):
                invalid.append({'line': no, 'module': source, 'reason': 'MALFORMED_JSON'})
                break
            if not isinstance(obj, dict):
                invalid.append({'line': no, 'module': source, 'reason': 'JSON_NOT_OBJECT'})
                break
            out.append({'line': no, 'module': source, 'data': obj})
            break
    return out, invalid


def _nearby(events: list[dict], idx: int, event: dict, kind: str, bound: int) -> list[dict]:
    """Local temporal association, NEVER authoritative engine event binding."""
    return [x for x in events if x['module'] == kind
            and idx < x['line'] <= bound
            and x['data'].get('actor') == event['sourceActor']
            and x['data'].get('partyIndex') == event['partyIndex']
            and x['data'].get('selectedWeaponRaw') == event['selectedSlot']
            and ((kind == 'R4' and x['data'].get('actionRaw') == event['rawActionId']) or
                 (kind == 'R1' and x['data'].get('action') == event['rawActionId']) or
                 (kind == 'R2' and x['data'].get('actionRaw') == event['rawActionId']))]


def _slot_resref(slot: int, r2: dict) -> str | None:
    container = 'quickWeapons' if 35 <= slot <= 38 else 'quivers' if 11 <= slot <= 14 else None
    if container is None:
        return None
    items = r2.get(container)
    if not isinstance(items, list):
        return None
    match = [x for x in items if isinstance(x, dict) and x.get('index') == slot]
    if len(match) != 1:
        return None
    ref = match[0].get('resrefRaw')
    return ref if isinstance(ref, str) and re.fullmatch(r'[A-Z0-9_]{1,8}', ref) else None


def analyze_text(text: str, sha256: str = 'SYNTHETIC') -> dict:
    events, invalid = _parse(text)
    output = {'schema': 'BGXAI_SELECTED_SLOT_EVIDENCE_BRIDGE_RO_V1',
              'inputSha256': sha256, 'readOnly': True,
              'gameModified': False, 'dispatchAuthorized': False,
              'weaponSwitchAuthorized': False, 'currentSelectionOnly': True,
              'alternateSlotAprVerified': False,
              'manualAndEpsQueueVerified': False,
              'targetProtectionComplete': False,
              'matchedByNativeEventId': False,
              'pairingMethod': 'BOUNDED_CONSOLE_LINE_PROXIMITY_UNAUTHENTICATED',
              'sessionReady': False, 'observations': [], 'invalidLines': invalid}
    r13 = [x for x in events if x['module'] == 'R13']
    output['sessionReady'] = any(x['data'].get('type') == 'SESSION' for x in r13) and any(
        x['data'].get('type') == 'READY' and x['data'].get('hookRegistered') is True for x in r13)
    defense = [x for x in r13 if x['data'].get('type') == 'DEFENSE']
    output['r13DefenseCount'] = len(defense)
    if len(defense) > MAX_PAIRS:
        output['status'] = 'HOLD_TOO_MANY_DEFENSE_RECORDS'
        return output
    if invalid:
        output['status'] = 'HOLD_MALFORMED_SOURCE_EVENTS'
        return output
    for n, entry in enumerate(defense):
        q = entry['data']
        seq = q.get('seq')
        line = entry['line']
        raw = {'r13Sequence': seq, 'line': line,
               'actor': q.get('sourceActor'), 'target': q.get('targetActor'),
               'selectedSlot': q.get('selectedSlot'), 'action': q.get('rawActionId')}
        if (not output['sessionReady'] or not int_in(seq, 1, MAX_PAIRS) or
            not int_in(q.get('sourceActor'), 1, 2147483647) or
            not int_in(q.get('targetActor'), 1, 2147483647) or
            not int_in(q.get('partyIndex'), 0, 5) or
            q.get('sourceActor') == q.get('targetActor') or
            q.get('selectedSlot') not in (10, 11, 12, 13, 14, 35, 36, 37, 38) or
            not int_in(q.get('rawActionId'), 0, 65535)):
            output['observations'].append(hold('R13_IDENTITY_OR_SESSION_INVALID', **raw))
            continue
        if q.get('status') != 'TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY' or not isinstance(q.get('fields'), dict):
            output['observations'].append(hold('R13_TARGET_DEFENSE_NOT_FULLY_READ', **raw))
            continue
        fields = q['fields']
        if any(not int_in(fields.get(key), -200, 200) for key in FIELDS):
            output['observations'].append(hold('R13_TARGET_FIELDS_MISSING_OR_INVALID', **raw))
            continue
        if (q.get('weaponSwitchAuthorized') is not False or
            q.get('exactHitChanceProven') is not False or
            q.get('allProtectionsObserved') is not False):
            output['observations'].append(hold('R13_PROVENANCE_FLAGS_UNEXPECTED', **raw))
            continue
        max_line = min(line + PAIR_DISTANCE, defense[n+1]['line']-1 if n+1 < len(defense) else line+PAIR_DISTANCE)
        matches4 = _nearby(events, line, q, 'R4', max_line)
        matches1 = _nearby(events, line, q, 'R1', max_line)
        matches2 = _nearby(events, line, q, 'R2', max_line)
        if len(matches4) != 1 or len(matches1) != 1 or len(matches2) != 1:
            output['observations'].append(hold('R1_R2_R4_PAIRING_NOT_UNIQUE_OR_MISSING', **raw))
            continue
        o4, o1, o2 = (matches4[0]['data'], matches1[0]['data'], matches2[0]['data'])
        stats4 = o4.get('statsRaw')
        if (not isinstance(stats4, dict) or
            o4.get('seq') != o1.get('sequence') or o4.get('seq') != o2.get('seq') or
            stats4.get('m_nNumberOfAttacks') != o1.get('aprRaw') or
            o1.get('weaponSwitchAuthorized') is not False or
            o2.get('itemIdentityVerified') is not False or
            o2.get('perSlotAPRVerified') is not False):
            output['observations'].append(hold('R1_R2_R4_EVIDENCE_CONFLICT', **raw))
            continue
        apr = decode_source_apr_key(o1.get('aprRaw'))
        if apr.state != 'SOURCE_KEY_DECODED_RO':
            output['observations'].append(hold('UNKNOWN_CURRENT_APR_KEY', **raw))
            continue
        item = _slot_resref(q['selectedSlot'], o2)
        output['observations'].append({**raw,
            'status': 'CURRENT_SELECTED_EVIDENCE_CANDIDATE_RO',
            'sourceAprKey': apr.raw_key, 'sourceAprValue': str(apr.source_value),
            'defenseFields': {key: fields[key] for key in FIELDS},
            'sourceItemRefRaw': item, 'itemIdentityVerified': False,
            'targetStatsFullyVerified': False,
            'selectedItemUsabilityVerified': False,
            'alternateSlotAprVerified': False,
            'manualAndEpsQueueVerified': False,
            'sourceOriginVerified': False,
            'pairingAuthenticated': False,
            'dispatchAuthorized': False, 'weaponSwitchAuthorized': False})
    counts = Counter(x['status'] for x in output['observations'])
    output['counts'] = dict(sorted(counts.items()))
    output['status'] = ('CURRENT_SELECTED_EVIDENCE_CAPTURED_RO' if defense and
                         counts.get('CURRENT_SELECTED_EVIDENCE_CANDIDATE_RO') == len(defense)
                         else 'HOLD_INCOMPLETE_EVIDENCE')
    return output


def analyze_file(path: Path) -> dict:
    raw, sha = _read(path)
    return analyze_text(raw, sha)


def main() -> int:
    p = argparse.ArgumentParser(description='Offline console evidence bridge; no game commands')
    p.add_argument('log_file', type=Path)
    arg = p.parse_args()
    try:
        report = analyze_file(arg.log_file)
    except (ValueError, OSError, UnicodeError) as ex:
        report = hold('INPUT_REJECTED', detail=type(ex).__name__)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get('status') == 'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO' else 2


if __name__ == '__main__':
    raise SystemExit(main())
