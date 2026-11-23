"""BGXAI R25: strictly offline R2/R4 log mirror deduplication and session boundaries.

Never opens game/native handles, accesses EEex, or sends actions. A deterministic
capture-local token is NOT engine-authenticated session provenance.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping

SCHEMA = 'BGXAI_R25_CAPTURE_SEGMENT_RO_V1'
MAX_BYTES = 2_000_000
MAX_EVENTS = 2048
MAX_LINE_BYTES = 65_536
CHANNEL = re.compile(r'^INFO: (LUA|LPRINT): \[(BGXW2|BGXW4)\] (\{.*\})$')
SOURCES = {
    'BGXW2': ('BGXAI_WEAPON_SLOTS_RAW_R2', 'SLOTS'),
    'BGXW4': ('BGXAI_WEAPON_ACTIVE_R4', 'ACTIVE'),
}


def _hold(reason: str) -> dict:
    return dict(schema=SCHEMA, status='HOLD_UNTRUSTED_OR_AMBIGUOUS_CAPTURE',
                reason=reason, readOnly=True, sourceOnly=True, gameModified=False,
                ordersSent=0, dispatchAuthorized=False, weaponSwitchAuthorized=False,
                sessionIdEngineAuthenticated=False, manualEpsQueueVerified=False,
                recordsBySource={}, mirroredPairsRemoved=0, segments=[])


def _basic(event: object, source: str) -> bool:
    if not isinstance(event, dict) or event.get('schema') != SOURCES[source][0]:
        return False
    t = event.get('type')
    if t not in ('SESSION', 'READY', SOURCES[source][1]):
        return False
    if t == 'SESSION':
        return event.get('readOnly') is True
    if t == 'READY':
        return event.get('hookRegistered') is True
    if type(event.get('seq')) is not int or not 1 <= event['seq'] <= 64:
        return False
    if type(event.get('actor')) is not int or not 1 <= event['actor'] <= 2_147_483_647:
        return False
    if source == 'BGXW2':
        return event.get('switchAuthorized') is False
    return (event.get('weaponSwitchAuthorized') is False and
            event.get('dispatchAuthorized') is False)


def inspect(data: bytes, *, source_type: str) -> dict:
    """All inputs must be bounded bytes. No paths, no filesystem, no dispatch."""
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
        return _hold('UNSUPPORTED_INPUT_SIZE_OR_TYPE')
    if source_type not in ('console', 'r2-jsonl', 'r4-jsonl'):
        return _hold('UNKNOWN_CAPTURE_FORMAT')
    try:
        lines = data.decode('utf-8', 'strict').splitlines()
    except UnicodeDecodeError:
        return _hold('INVALID_UTF8')
    records = []
    for line_number, line in enumerate(lines, 1):
        if len(line.encode('utf-8')) > MAX_LINE_BYTES:
            return _hold('OVERSIZE_LINE')
        if source_type == 'console':
            m = CHANNEL.fullmatch(line)
            if not m:
                if '[BGXW2]' in line or '[BGXW4]' in line:
                    return _hold('UNPARSEABLE_KNOWN_SOURCE_LINE')
                continue
            channel, source, payload = m.groups()
        else:
            source = 'BGXW2' if source_type == 'r2-jsonl' else 'BGXW4'
            channel, payload = 'FILE', line
        try:
            event = json.loads(payload)
        except (ValueError, TypeError):
            return _hold('INVALID_EVENT_JSON')
        if not _basic(event, source):
            return _hold('EVENT_SCHEMA_OR_READONLY_CONTRACT_INVALID')
        records.append((line_number, channel, source, payload, event))
        if len(records) > MAX_EVENTS:
            return _hold('TOO_MANY_TAGGED_EVENTS')
    if not records:
        return _hold('NO_SUPPORTED_EVENTS')

    # Collapse ONLY same-byte immediately-adjacent LUA+LPRINT console mirrors.
    normalized, mirror_count = [], 0
    i = 0
    while i < len(records):
        a = records[i]
        if (source_type == 'console' and i + 1 < len(records) and
            a[1] == 'LUA' and records[i+1][1] == 'LPRINT' and
            records[i+1][0] == a[0] + 1 and
            a[2] == records[i+1][2] and a[3] == records[i+1][3]):
            mirror_count += 1
            normalized.append(a)
            i += 2
        else:
            normalized.append(a)
            i += 1

    segments = []
    by_source = defaultdict(lambda: None)
    seen_seq = defaultdict(set)
    for raw_line, _, source, _, e in normalized:
        t = e['type']
        if t == 'SESSION':
            prior = by_source[source]
            if prior and not prior['ready']:
                return _hold('SECOND_SESSION_BEFORE_READY')
            if prior and not prior['count']:
                return _hold('EMPTY_SESSION_REPLACED')
            item = dict(source=source, sessionLine=raw_line, ready=False,
                        count=0, sequence=[], firstActor=None)
            segments.append(item)
            by_source[source] = item
            seen_seq[source] = set()
            continue
        seg = by_source[source]
        if seg is None:
            return _hold('EVENT_BEFORE_SESSION')
        if t == 'READY':
            if seg['ready']:
                return _hold('DUPLICATE_READY_UNMATCHED')
            seg['ready'] = True
            continue
        if not seg['ready']:
            return _hold('EVENT_BEFORE_READY')
        if e['seq'] in seen_seq[source]:
            return _hold('DUPLICATE_SEQ_UNMATCHED')
        if seg['firstActor'] is not None and e['actor'] != seg['firstActor']:
            return _hold('MULTIPLE_ACTORS_UNVERIFIED_JOIN')
        seen_seq[source].add(e['seq'])
        seg['firstActor'] = e['actor']
        seg['count'] += 1
        seg['sequence'].append(e['seq'])
    if any(not s['ready'] or not s['count'] for s in segments):
        return _hold('INCOMPLETE_SESSION')
    digest = hashlib.sha256(data).hexdigest()
    sanitized = []
    counts = defaultdict(int)
    for s in segments:
        counts[s['source']] += s['count']
        token_input = f'R25_OFFLINE_CAPTURE_ONLY:{digest}:{s["source"]}:{s["sessionLine"]}'.encode()
        sanitized.append(dict(source=s['source'], events=s['count'],
             offlineCaptureToken=hashlib.sha256(token_input).hexdigest()[:16],
             firstSeq=s['sequence'][0],lastSeq=s['sequence'][-1],
             sessionIdEngineAuthenticated=False))
    return dict(schema=SCHEMA,status='OFFLINE_LOG_SEGMENTS_VERIFIED_NO_RUNTIME_AUTH',
                readOnly=True,sourceOnly=True,gameModified=False,ordersSent=0,
                dispatchAuthorized=False,weaponSwitchAuthorized=False,
                sessionIdEngineAuthenticated=False,manualEpsQueueVerified=False,
                sourceType=source_type,sourceSha256=digest,
                taggedEventCount=len(records),normalizedEventCount=len(normalized),
                mirroredPairsRemoved=mirror_count,recordsBySource=dict(counts),
                segments=sanitized)
