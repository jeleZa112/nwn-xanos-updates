"""SOURCE ONLY: reuse existing BGXAI R3 ITM reader and BG_EET_RU V111 TLK parser.

No game writes, no hook, no live Lua replacement, no updater entrypoint.
Produces a read-only candidate name catalog; ambiguous names are NEVER selected.
The real game's resources are required before names can be marked verified.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import re
import struct

R3_REL = 'BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py'
V111_REL = 'bg-eet-ru/weapon-identity/V111_ITEM_NAMES_READONLY_SOURCE_ONLY.py'
R3_BLOB_SHA = '505111050fad4e5ab6560b55b82e1e436ff41d2a'
V111_BLOB_SHA = 'fd0ae4ed6fa19cba93e5d0bfcf6c7f09b3207b32'
REF = re.compile(r'[A-Z0-9_]{1,8}\Z')
MAX_ITEMS = 64

class SourceHold(ValueError):
    pass

def verified_module(repo: Path, relative: str, expected_blob_sha: str):
    """Only load a hash-pinned repository file, never a game-provided script."""
    base = Path(repo)
    if base.is_symlink() or not base.is_dir():
        raise SourceHold('SOURCE_REPO_UNSAFE')
    cur = base
    for part in Path(relative).parts:
        cur = cur / part
        if cur.is_symlink():
            raise SourceHold('SOURCE_SYMLINK')
    if not cur.is_file() or cur.stat().st_size > 200000:
        raise SourceHold('SOURCE_MISSING_OR_OVERSIZED')
    data = cur.read_bytes()
    # Windows checkout may use CRLF; Git blob IDs refer to canonical LF bytes.
    canonical = data.replace(b'\r\n', b'\n')
    if b'\r' in canonical:
        raise SourceHold('SOURCE_MIXED_LINE_ENDINGS')
    blob = hashlib.sha1(b'blob ' + str(len(canonical)).encode('ascii') + b'\0' + canonical).hexdigest()
    if blob != expected_blob_sha:
        raise SourceHold('SOURCE_GIT_BLOB_MISMATCH')
    spec = importlib.util.spec_from_file_location('checked_' + blob[:12], cur)
    if spec is None or spec.loader is None:
        raise SourceHold('SOURCE_IMPORT_UNAVAILABLE')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _hash_file(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 256_000_000:
        raise SourceHold('TLK_HASH_SOURCE_UNSAFE')
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def _names_safe(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 120:
        return False
    if value != value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        return False
    return bool(re.search(r'[А-Яа-яЁё]', value))

def _tlk_text(tlk, ref):
    if tlk.get('status') != 'V111_TLK_READ_ONLY':
        return None
    entry = tlk.get('entries', {}).get(str(ref), {})
    if entry.get('status') != 'TEXT_READ':
        return None
    return entry.get('text') if _names_safe(entry.get('text')) else None

def catalog_from_modules(game: Path, resrefs, r3, v111, source=None):
    """Read exact ITM bytes and RU TLKs, without guessing identified state.

    r3 and v111 are already verified/imported existing modules; source is an
    injectable read-only fixture for offline unit tests, never a game writer.
    """
    game = Path(game)
    if game.is_symlink() or not game.is_dir():
        raise SourceHold('GAME_ROOT_UNSAFE')
    # V111 compares the raw parent chain with root.resolve(); canonicalize
    # the argument first to avoid an endless parent walk on Windows aliases.
    game = game.resolve(strict=True)
    requested = list(resrefs)
    if not requested or len(requested) > MAX_ITEMS:
        raise SourceHold('ITEM_COUNT_OUTSIDE_LIMIT')
    if any(not isinstance(x, str) or not REF.fullmatch(x) for x in requested):
        raise SourceHold('RESREF_INVALID_OR_NOT_IN_V160_CONTRACT')
    names = list(dict.fromkeys(requested))
    src = source if source is not None else r3.NativeSource(game)
    # Legacy V111 was embedded into a larger updater and has no import stanza.
    # Bind its dependencies BEFORE the first v111_parse_itm() call.
    v111.Path = Path
    v111.struct = struct
    v111.digest = lambda b: hashlib.sha256(b).hexdigest()
    v111.sha_path = _hash_file
    entries, strrefs = {}, set()
    for name in names:
        try:
            raw, provenance = src.get(name, '.ITM')
            if not isinstance(raw, bytes) or len(raw) > 2_000_000:
                raise SourceHold('ITM_BYTES_INVALID')
            meta = v111.v111_parse_itm(raw)
            ids = (meta['unidentified_name_strref'], meta['identified_name_strref'])
            if any(type(x) is not int or x < 0 or x > 0xffffffff for x in ids):
                raise SourceHold('ITM_NAME_STRREF_INVALID')
            strrefs.update(ids)
            entries[name] = {
                'status': 'ITM_READ', 'itemTypeRaw': meta['item_type_id'],
                'itemTypeCategory': meta['item_type_category'],
                'unidentifiedStrref': ids[0], 'identifiedStrref': ids[1],
                'resourceSha256': hashlib.sha256(raw).hexdigest(),
                'origin': provenance.get('origin') or 'UNKNOWN',
                'autoDisplayName': None,
            }
        except (ValueError, KeyError, TypeError, OSError, struct.error, AttributeError) as exc:
            entries[name] = {'status': 'ITEM_HOLD', 'reason': str(exc)[:120], 'autoDisplayName': None}
    try:
        tlks = {name: v111.v111_tlk_names(game, strrefs, name)
                for name in ('dialog.tlk', 'dialogf.tlk')}
    except (ValueError, OSError, TypeError, KeyError, struct.error) as exc:
        tlks = {name: {'status': 'TLK_READ_HOLD', 'reason': str(exc)[:120]}
                for name in ('dialog.tlk', 'dialogf.tlk')}
    for row in entries.values():
        if row['status'] != 'ITM_READ':
            continue
        two = []
        for variant in ('unidentified', 'identified'):
            ref = row[variant + 'Strref']
            texts = {tlk: _tlk_text(result, ref) for tlk, result in tlks.items()}
            row[variant + 'RuByTlk'] = texts
            two.extend(texts.values())
        if len(two) == 4 and all(x is not None and x == two[0] for x in two):
            row['status'] = 'COMMON_RU_NAME_VERIFIED'
            row['autoDisplayName'] = two[0]
        else:
            row['status'] = 'NAME_OR_IDENTIFICATION_HOLD'
    count = sum(x['status'] == 'COMMON_RU_NAME_VERIFIED' for x in entries.values())
    return {
        'schema': 'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
        'status': 'READ_ONLY_SOURCE_CATALOG',
        'gameFilesWritten': 0, 'engineListenersAdded': 0,
        'combatLogRowJoinVerified': False, 'missesCovered': False,
        'autoDisplayNamesReady': count,
        'tlkSha256': {name: value.get('tlk_sha256') for name, value in tlks.items()},
        'items': entries,
    }

def build_catalog(repo: Path, game: Path, resrefs):
    r3 = verified_module(repo, R3_REL, R3_BLOB_SHA)
    v111 = verified_module(repo, V111_REL, V111_BLOB_SHA)
    return catalog_from_modules(game, resrefs, r3, v111)
def catalog_from_r28(game: Path, r28, r3, v111, source=None):
    """Reuse a *previously collected* R27/R28 report without new game capture.

    The report selects only observed resources; current game item bytes must
    still match every SHA-256 from the earlier real native audit. No actor ID,
    personal paths or raw action logs are copied to the catalog.
    """
    if not isinstance(r28, dict) or r28.get('schema') != 'BGXAI_R28_NATIVE_FROM_R27_RO_V1' \
            or r28.get('status') != 'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW' \
            or r28.get('gameModified') is not False or r28.get('ordersSent') != 0 \
            or r28.get('dispatchAuthorized') is not False:
        raise SourceHold('R28_REPORT_PROVENANCE_HOLD')
    live, audit = r28.get('liveR27Evidence'), r28.get('nativeAudit')
    if not isinstance(live, dict) or not isinstance(audit, dict):
        raise SourceHold('R28_REPORT_SHAPE_HOLD')
    if live.get('schema') != 'BGXAI_R28_R27_LIVE_INPUT_V1' \
            or live.get('r27SessionMarkers') != 1 \
            or type(live.get('r27ConfirmedCallbacks')) is not int \
            or not 1 <= live['r27ConfirmedCallbacks'] <= 200000 \
            or live.get('gameModified') is not False \
            or audit.get('schema') != 'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY' \
            or audit.get('status') != 'ITM_NATIVE_ALL_ITEMS_RAW_READ' \
            or audit.get('sourceKind') != 'CURRENT_GAME' \
            or audit.get('gameModified') is not False \
            or audit.get('missingItemsOrLinkedSpells') != []:
        raise SourceHold('R28_NATIVE_PROVENANCE_HOLD')
    sha_re = re.compile(r'[0-9a-f]{64}\Z')
    capture = r28.get('captureSha256')
    if not isinstance(capture, str) or not sha_re.fullmatch(capture) \
            or capture != live.get('sourceSha256'):
        raise SourceHold('R27_R28_CAPTURE_NOT_BOUND')
    refs = live.get('observedRawItemResrefs')
    requested = audit.get('requestedItems')
    items = audit.get('items')
    if not isinstance(refs, list) or not 1 <= len(refs) <= MAX_ITEMS \
            or len(refs) != len(set(x for x in refs if isinstance(x, str))) \
            or not all(isinstance(x, str) and REF.fullmatch(x) for x in refs) \
            or requested != refs or not isinstance(items, dict) \
            or set(items) != set(refs):
        raise SourceHold('R28_ITEM_SET_NOT_BOUND')
    expected = {}
    for ref in refs:
        entry = items.get(ref)
        if not isinstance(entry, dict) or entry.get('resource') != ref \
                or not isinstance(entry.get('provenance'), dict):
            raise SourceHold('R28_ITEM_IDENTITY_HOLD')
        prov = entry['provenance']
        if prov.get('origin') not in ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE') \
                or not isinstance(prov.get('sha256'), str) \
                or not sha_re.fullmatch(prov['sha256']):
            raise SourceHold('R28_RESOURCE_HASH_HOLD')
        expected[ref] = (prov['sha256'], prov['origin'])
    inner = source if source is not None else r3.NativeSource(Path(game))
    class PinnedItemReader:
        def get(self, ref, ext):
            if ext != '.ITM' or ref not in expected:
                raise SourceHold('R28_UNEXPECTED_RESOURCE')
            raw, provenance = inner.get(ref, ext)
            if not isinstance(raw, bytes) or not isinstance(provenance, dict) \
                    or hashlib.sha256(raw).hexdigest() != expected[ref][0] \
                    or provenance.get('origin') != expected[ref][1]:
                raise SourceHold('R28_ITM_SHA_OR_ORIGIN_CHANGED')
            return raw, provenance
    catalog = catalog_from_modules(game, refs, r3, v111, source=PinnedItemReader())
    catalog['priorEvidence'] = 'R27_LIVE_R28_REAL_NATIVE_SHA'
    catalog['itemShaComparedToR28'] = True
    catalog['status'] = ('R28_ITEM_DRIFT_HOLD' if
                         any(x['status'] == 'ITEM_HOLD' for x in catalog['items'].values())
                         else 'R28_SHA_MATCH_CATALOG_READONLY')
    return catalog


def build_catalog_from_r28(repo: Path, game: Path, r28_report):
    """No CLI, no extra updater; caller supplies the existing private report."""
    r3 = verified_module(repo, R3_REL, R3_BLOB_SHA)
    v111 = verified_module(repo, V111_REL, V111_BLOB_SHA)
    return catalog_from_r28(game, r28_report, r3, v111)

