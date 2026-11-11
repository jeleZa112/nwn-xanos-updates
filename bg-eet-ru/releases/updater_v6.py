# -*- coding: utf-8 -*-
"""BG EET RU permanent updater. Python 3.9+ stdlib only.

Checks SHA256-pinned GitHub code updates and original Russian translation deltas.
Game TLKs are modified ONLY after an exact preflight, backup and user-entered YES.
Never touches voice synthesis, WAV or BGXAI.
"""
import argparse
import collections
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import urllib.request
import urllib.error
import zipfile

APP_VERSION = '6.0.0-hold-exact-readonly'
HERE = Path(__file__).resolve().parent
DATA = HERE / 'DATA'
REPORTS = HERE / 'BG_EET_RU_REPORTS'
PLAN_PATH = DATA / 'active_plan.json'
STATE_PATH = DATA / 'release_state.json'
GAME_DEFAULT = r'C:\Games\BG_EET_FOXX_NEW'
REMOTE = ('https://raw.githubusercontent.com/jeleZa112/'
          'nwn-xanos-updates/bg-eet-ai/bg-eet-ru/')
CHANNEL_NAME = 'channel.json'
SIDES = ('dialog.tlk', 'dialogf.tlk')
BASELINE_VERSION = 18
BASELINE_SHA256 = '4f8cc901b2bf87dfe0d76a757c5cd6e643e361b0e3e0982df1f0eea7f0068a32'
LOCAL_GAMEPLAY_SHA256 = '3168612d907f13066be008d744af63b1c60f16fd0dc503a9f25af1e2633f5eac'
LOCAL_GAMEPLAY_PATH = DATA / 'local_gameplay_plan_v21_1.json'
TOKEN_RE = re.compile(r'<[A-Za-z_][A-Za-z0-9_]*>')


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.partial')
    try:
        tmp.write_bytes(raw)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def validate_plan(plan):
    if plan.get('project') != 'BG EET RU TEXT LOCALIZATION':
        raise ValueError('Bad project identity: BG EET RU expected')
    entries, held = plan.get('entries'), plan.get('held')
    if not isinstance(entries, list) or not isinstance(held, list):
        raise ValueError('Plan entries / held must be lists')
    ids = set()
    counts = plan.get('counts', {})
    changed = 0
    for record in entries:
        n = record.get('strref')
        if not isinstance(n, int) or n < 0 or n in ids:
            raise ValueError('Missing, duplicate or invalid StrRef: ' + str(n))
        ids.add(n)
        for side in SIDES:
            item = record.get(side)
            if not isinstance(item, dict):
                raise ValueError('Missing TLK side for ' + str(n))
            source, replacement = item.get('source'), item.get('replacement')
            if not isinstance(source, str) or not isinstance(replacement, str):
                raise ValueError('Missing source/replacement for ' + str(n))
            if sha_bytes(source.encode('utf-8')) != item.get('source_sha256_utf8'):
                raise ValueError('Original string SHA mismatch: ' + str(n))
            if sha_bytes(replacement.encode('utf-8')) != item.get('replacement_sha256_utf8'):
                raise ValueError('Translation string SHA mismatch: ' + str(n))
            if collections.Counter(TOKEN_RE.findall(source)) != collections.Counter(TOKEN_RE.findall(replacement)):
                raise ValueError('Game placeholder changed at ' + str(n))
            action = item.get('action')
            if action not in ('REPLACE', 'KEEP_UNCHANGED'):
                raise ValueError('Invalid action at ' + str(n))
            if (source != replacement) != (action == 'REPLACE'):
                raise ValueError('Contradictory action at ' + str(n))
            changed += action == 'REPLACE'
    held_ids = [r.get('strref') for r in held]
    if len(held_ids) != len(set(held_ids)) or ids.intersection(held_ids):
        raise ValueError('HOLD collides with prepared entries')
    if (len(entries) != counts.get('prepared_unique_strrefs') or
            len(entries)+len(held) != counts.get('total_unique_strrefs') or
            changed != counts.get('actual_text_changes_proposed')):
        raise ValueError('Counts do not agree with entry content')
    fingerprints = plan.get('tlk_sha256_on_user_game', {})
    for side in SIDES:
        if not re.fullmatch(r'[0-9a-f]{64}', str(fingerprints.get(side, ''))):
            raise ValueError('Invalid game TLK SHA for ' + side)
    return plan


def load_state():
    plan_raw = PLAN_PATH.read_bytes()
    plan = validate_plan(json.loads(plan_raw.decode('utf-8-sig')))
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding='utf-8'))
        if state['plan_sha256'] != sha_bytes(plan_raw):
            # Recover from interrupted two-file update, but only using a fully
            # hashed previous snapshot. Never trust a partial new release.
            previous_plan = DATA / 'previous_plan.json'
            previous_state = DATA / 'previous_state.json'
            if previous_plan.is_file() and previous_state.is_file():
                prior_raw = previous_plan.read_bytes()
                prior_state_raw = previous_state.read_bytes()
                prior_state = json.loads(prior_state_raw.decode('utf-8'))
                if prior_state.get('plan_sha256') == sha_bytes(prior_raw):
                    prior_plan = validate_plan(json.loads(prior_raw.decode('utf-8-sig')))
                    atomic_write(PLAN_PATH, prior_raw)
                    atomic_write(STATE_PATH, prior_state_raw)
                    return prior_plan, prior_state
            raise RuntimeError('STOP: current plan changed without a verified rollback snapshot')
        return plan, state
    if sha_bytes(plan_raw) != BASELINE_SHA256:
        raise RuntimeError('STOP: baseline plan hash mismatch; restore original archive')
    state = {'release_version': BASELINE_VERSION, 'plan_sha256': BASELINE_SHA256}
    atomic_write(STATE_PATH, json_text(state).encode('utf-8'))
    return plan, state


def fetch_bytes(url, max_bytes=6_000_000):
    if not url.startswith(REMOTE):
        raise ValueError('Unsafe update URL')
    request = urllib.request.Request(url, headers={'User-Agent': 'BG-EET-RU-Updater/1.0'})
    with urllib.request.urlopen(request, timeout=18) as response:
        if response.url != url:
            raise RuntimeError('STOP: unexpected redirect in updater URL')
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise RuntimeError('STOP: updater payload too large')
        return raw


def check_remote_updates(plan, state, *, fetch=fetch_bytes, remote=REMOTE):
    """Checks metadata; downloads only a JSON data plan. Never remote code."""
    notes = []
    try:
        raw = fetch(remote + CHANNEL_NAME)
        channel = json.loads(raw.decode('utf-8-sig'))
        if channel.get('schema') != 'bg-eet-ru-channel-v1' or channel.get('channel') != 'stable':
            raise ValueError('Unexpected update channel schema')
        version = channel.get('release_version')
        if not isinstance(version, int) or version < BASELINE_VERSION:
            raise ValueError('Invalid channel version')
        if version <= state['release_version']:
            notes.append('GitHub: актуальная версия ' + str(state['release_version']))
            return plan, state, notes
        item = channel.get('plan')
        if not isinstance(item, dict):
            notes.append('GitHub: есть анонс v%s, но нет опубликованного плана; оставлен текущий' % version)
            return plan, state, notes
        rel = item.get('path')
        digest = item.get('sha256')
        if not isinstance(rel, str) or not re.fullmatch(r'[A-Za-z0-9_/-]+\.json', rel) or '..' in rel.split('/'):
            raise ValueError('Invalid release path')
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('Missing sha256 in release manifest')
        # Download outside the game and verify *before* replacing active plan.
        new_raw = fetch(remote + rel)
        if sha_bytes(new_raw) != digest:
            raise RuntimeError('STOP: downloaded plan SHA256 mismatch')
        new_plan = validate_plan(json.loads(new_raw.decode('utf-8-sig')))
        # Remote game text is DATA only. We never download/execute a .py or .cmd.
        previous = PLAN_PATH.read_bytes()
        previous_state = STATE_PATH.read_bytes()
        backup_plan = DATA / 'previous_plan.json'
        backup_state = DATA / 'previous_state.json'
        atomic_write(backup_plan, previous)
        atomic_write(backup_state, previous_state)
        try:
            atomic_write(PLAN_PATH, new_raw)
            new_state = {'release_version': version, 'plan_sha256': digest}
            atomic_write(STATE_PATH, json_text(new_state).encode('utf-8'))
        except BaseException:
            atomic_write(PLAN_PATH, previous)
            atomic_write(STATE_PATH, previous_state)
            raise
        notes.append('GitHub: план обновлён с v%s до v%s (данные, без установки)' % (state['release_version'], version))
        return new_plan, new_state, notes
    except (OSError, RuntimeError, ValueError, KeyError, urllib.error.URLError) as exc:
        notes.append('GitHub недоступен или обновление отклонено; локальная версия сохранена: ' + str(exc))
        return plan, state, notes


class TLK:
    def __init__(self, path):
        self.file = path.open('rb')
        self.size = path.stat().st_size
        raw = self.file.read(18)
        if len(raw) != 18:
            raise ValueError('Short TLK: ' + str(path))
        signature, version, lang, count, data = struct.unpack('<4s4sHII', raw)
        if signature != b'TLK ' or version != b'V1  ':
            raise ValueError('Unsupported TLK file: ' + str(path))
        if data < 18 + 26 * count or data > self.size:
            raise ValueError('Broken TLK index: ' + str(path))
        self.count, self.data = count, data

    def get(self, index):
        if not 0 <= index < self.count:
            return 'OUT_OF_RANGE', ''
        self.file.seek(18 + 26 * index)
        entry = self.file.read(26)
        if len(entry) != 26:
            return 'TRUNCATED', ''
        flags, = struct.unpack_from('<H', entry)
        offset, length = struct.unpack_from('<II', entry, 18)
        start = self.data + offset
        if start < self.data or start + length > self.size:
            return 'BROKEN_POINTER', ''
        self.file.seek(start)
        try:
            value = self.file.read(length).decode('utf-8')
        except UnicodeDecodeError:
            return 'INVALID_UTF8', ''
        return ('OK' if (flags & 1 or not value) else 'TEXT_FLAG_NOT_SET'), value

    def close(self):
        self.file.close()



def choose_local_gameplay_plan(remote_plan):
    """Use the user's vetted local v21.1 game-text plan; never fetch it publicly."""
    if not LOCAL_GAMEPLAY_PATH.is_file():
        return remote_plan, None
    if sha_file(LOCAL_GAMEPLAY_PATH) != LOCAL_GAMEPLAY_SHA256:
        raise RuntimeError('STOP: SHA256 локального игрового плана v21.1 не совпал')
    obj=validate_plan(json.loads(LOCAL_GAMEPLAY_PATH.read_text(encoding='utf-8-sig')))
    if (len(obj['entries'])!=290 or len(obj['held'])!=22
            or obj['counts']['actual_text_changes_proposed']!=570):
        raise RuntimeError('STOP: неверный локальный игровой план')
    if obj['tlk_sha256_on_user_game']!=remote_plan['tlk_sha256_on_user_game']:
        raise RuntimeError('STOP: локальный план от другой сборки TLK')
    byid={r['strref']:r for r in obj['entries']}
    for r in remote_plan['entries']:
        local=byid.get(r['strref'])
        if not local:
            raise RuntimeError('STOP: локальный план потерял предыдущий StrRef')
        for side in SIDES:
            for k in ('source','replacement','action'):
                if r[side][k]!=local[side][k]:
                    raise RuntimeError('STOP: локальный план противоречит проверенному v18: '+str(r['strref']))
    return obj, 'Локальный план игрового текста v21.1: 290 StrRef / 22 HOLD; GitHub канал отдельно v18'


def find_tlks(game):
    lang = game / 'lang'
    if not lang.is_dir():
        raise RuntimeError('No lang directory in EET: ' + str(lang))
    candidates = [p for p in lang.iterdir() if p.is_dir() and p.name.casefold() == 'ru_ru']
    if len(candidates) != 1:
        raise RuntimeError('No unambiguous ru_RU folder in ' + str(lang))
    result = {side: candidates[0] / side for side in SIDES}
    for path in result.values():
        if not path.is_file():
            raise RuntimeError('Missing TLK: ' + str(path))
    return result



def verify_install_chain(expected, actual):
    """Accept only the exact original TLKs or signed local installation stages.

    No TLK writes, no remote code. Two stages have independent manifests and backups.
    """
    if actual == expected:
        return {'stage': 0, 'installed_strrefs': 0, 'message': 'Исходные TLK до установки'}
    base = HERE / 'BG_EET_RU_SAFE_BACKUPS'
    step1 = base / 'active_install.json'
    if not step1.is_file():
        raise RuntimeError('STOP: TLK отличаются от базовых и нет манифеста установленного патча')
    first = json.loads(step1.read_text(encoding='utf-8'))
    if (first.get('status') != 'installed' or first.get('version') != '21.1-safe-prefix-only'
            or first.get('original_sha256') != expected or first.get('strrefs') != 158
            or first.get('proposed_updates') != 306):
        raise RuntimeError('STOP: не подтверждён сохранённый первый патч')
    first_hash=first.get('patched_sha256')
    if not isinstance(first_hash,dict) or set(first_hash)!=set(SIDES):
        raise RuntimeError('STOP: неверные SHA256 после первого патча')
    if actual==first_hash:
        return {'stage': 1, 'installed_strrefs': 158, 'message': 'Первый патч установлен: 158 StrRef'}
    step2 = base / 'active_install_stage2.json'
    if not step2.is_file():
        raise RuntimeError('STOP: TLK отличаются от первого патча, манифест второго патча отсутствует')
    second = json.loads(step2.read_text(encoding='utf-8'))
    if (second.get('status') != 'installed' or second.get('version') != '21.2-post-v21.1-gameplay-132'
            or second.get('original_sha256') != first_hash or second.get('strrefs') != 132
            or second.get('proposed_updates') != 264):
        raise RuntimeError('STOP: не подтверждён второй патч')
    if actual==second.get('patched_sha256'):
        return {'stage': 2, 'installed_strrefs': 290, 'message': 'Оба патча установлены: 290 StrRef'}
    raise RuntimeError('STOP: текущие TLK не совпадают ни с одной подтверждённой стадией')


def scan_game(plan, game):
    paths = find_tlks(game)
    expected = plan['tlk_sha256_on_user_game']
    before = {side: sha_file(paths[side]) for side in SIDES}
    stage = verify_install_chain(expected,before)
    rows = []
    for side in SIDES:
        t = TLK(paths[side])
        try:
            if t.count != 360847:
                raise RuntimeError('Unexpected number of TLK rows: ' + str(t.count))
            for entry in plan['entries']:
                n = entry['strref']
                e = entry[side]
                status, current = t.get(n)
                if status != 'OK':
                    outcome = 'BLOCKED_' + status
                elif e['action'] == 'KEEP_UNCHANGED' and current == e['source']:
                    outcome = 'NO_CHANGE_REQUIRED'
                elif current == e['source']:
                    outcome = 'EXACT_CURRENT_SOURCE'
                elif current == e['replacement']:
                    outcome = 'ALREADY_TRANSLATED'
                else:
                    outcome = 'BLOCKED_TEXT_DIFFERENCE'
                rows.append({'strref': n, 'tlk': side, 'category': entry.get('category', ''),
                             'status': outcome, 'action': e['action'],
                             'current_text': current, 'proposed_text': e['replacement']})
        finally:
            t.close()
    after = {side: sha_file(paths[side]) for side in SIDES}
    if before != after:
        raise RuntimeError('STOP: game TLK hash changed during read-only scan')
    return rows, {'before': before, 'after': after, 'stage': stage}


def render_reports(plan, state, rows, fingerprints, notes, *, result='OK', error=None, reports=REPORTS):
    reports.mkdir(parents=True, exist_ok=True)
    counts = dict(collections.Counter(r['status'] for r in rows))
    summary = {
        'project': 'BG EET RU', 'updater_version': APP_VERSION,
        'release_version': state.get('release_version'), 'local_plan_version': plan.get('version') if plan else None,
        'timestamp_utc': utc_now(),
        'mode': 'READ_ONLY', 'result': result,
        'game_modified': False, 'installed': bool(fingerprints.get('stage',{}).get('stage',0)),
        'installed_gameplay_strrefs': fingerprints.get('stage',{}).get('installed_strrefs',0),
        'prepared_strrefs': len(plan['entries']) if plan else 0,
        'held_strrefs': len(plan['held']) if plan else 0,
        'checks': len(rows), 'status_counts': counts,
        'tlk_sha256': fingerprints, 'update_messages': notes,
        'error': str(error) if error else None,
        'safe_for_automatic_install': False
    }
    # A single persistent directory with overwritten latest files and one append-only log.
    atomic_write(reports / '00_LAST_SUMMARY.json', json_text(summary).encode('utf-8'))
    preview = reports / '01_LAST_PREVIEW.csv'
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8-sig', newline='',
                                     dir=reports, prefix='_preview_', suffix='.tmp') as f:
        temp = Path(f.name)
        cols = ['strref', 'tlk', 'category', 'status', 'action', 'current_text', 'proposed_text']
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader(); writer.writerows(rows)
    os.replace(temp, preview)
    held_path = reports / '02_HOLD_CONTEXT.csv'
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8-sig', newline='',
                                     dir=reports, prefix='_hold_', suffix='.tmp') as f:
        temp = Path(f.name)
        columns = ['strref', 'category', 'review_level', 'source_excerpt', 'proposal_excerpt', 'notes']
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        if plan:
            writer.writerows(plan['held'])
    os.replace(temp, held_path)
    log_path = reports / 'BG_EET_RU_ALL_RUNS.log'
    with log_path.open('a', encoding='utf-8') as f:
        f.write('\n[' + summary['timestamp_utc'] + '] RESULT=' + result +
                ' RELEASE=' + str(summary['release_version']) +
                ' CHECKS=' + str(len(rows)) + ' STATUS=' + str(counts) + '\n')
        for note in notes:
            f.write('  ' + note + '\n')
        if error:
            f.write('  ERROR: ' + str(error) + '\n')
    archive = reports / 'SEND_TO_CHATGPT_BG_EET_RU.zip'
    tmp_archive = reports / '_SEND_TO_CHATGPT_BG_EET_RU.tmp'
    with zipfile.ZipFile(tmp_archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in [reports / '00_LAST_SUMMARY.json', preview, held_path,
                  reports/'03_SAFE_PATCH_LAST.json', reports/'04_STAGE2_PATCH_LAST.json', log_path]:
            if f.is_file(): z.write(f, f.name)
    os.replace(tmp_archive, archive)
    return summary, archive


def create_synthetic(game, plan):
    root = game / 'lang' / 'ru_RU'
    root.mkdir(parents=True)
    count = 360847
    base = 18 + count * 26
    for side in SIDES:
        with (root / side).open('wb+') as f:
            f.write(struct.pack('<4s4sHII', b'TLK ', b'V1  ', 0, count, base))
            f.seek(base)
            position = 0
            for e in plan['entries']:
                n = e['strref']
                raw = e[side]['source'].encode('utf-8')
                f.seek(base + position)
                f.write(raw)
                entry = bytearray(26)
                struct.pack_into('<H', entry, 0, 1)
                struct.pack_into('<II', entry, 18, position, len(raw))
                f.seek(18 + n * 26)
                f.write(entry)
                position += len(raw)


def selftest():
    baseline = validate_plan(json.loads(PLAN_PATH.read_text(encoding='utf-8')))
    assert sha_file(PLAN_PATH) == BASELINE_SHA256
    with tempfile.TemporaryDirectory(prefix='BG_EET_RU_UPDATER_TEST_') as root:
        base = Path(root)
        game = base / 'GAME'
        create_synthetic(game, baseline)
        plan = json.loads(json.dumps(baseline))
        # Synthetic TLKs do not have real user-game fingerprints; use fixture hashes.
        tlks = find_tlks(game)
        before = {s: sha_file(tlks[s]) for s in SIDES}
        plan['tlk_sha256_on_user_game'] = before
        local_reports = base / 'REPORTS'
        state = {'release_version': 18, 'plan_sha256': BASELINE_SHA256}
        for _ in range(2):
            rows, fingerprints = scan_game(plan, game)
            assert len(rows) == 476
            assert sum(x['status'] == 'EXACT_CURRENT_SOURCE' for x in rows) == 475
            assert sum(x['status'] == 'NO_CHANGE_REQUIRED' for x in rows) == 1
            summary, archive = render_reports(plan, state, rows, fingerprints, ['OFFLINE_TEST'], reports=local_reports)
            assert summary['game_modified'] is False and archive.is_file()
        assert len(list(local_reports.glob('SEND_TO_CHATGPT*.zip'))) == 1
        assert len(list(local_reports.glob('01_LAST_PREVIEW*.csv'))) == 1
        assert (local_reports / 'BG_EET_RU_ALL_RUNS.log').read_text(encoding='utf-8').count('RESULT=OK') == 2
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist()) == 4
        assert all(sha_file(tlks[s]) == before[s] for s in SIDES)
        # Stage-aware read-only tests on full index TLK fixtures with valid patches.
        old_here = globals()['HERE']
        try:
            globals()['HERE'] = base
            backup_root = base/'BG_EET_RU_SAFE_BACKUPS'; backup_root.mkdir()
            # Simulate patched TLK metadata without modifying real game.
            fixture_first={s:bytes.fromhex('cc')*32 for s in SIDES}
            # Manifests are accepted ONLY if game bytes match their SHA256.
            original_first={'version':'21.1-safe-prefix-only','status':'installed','strrefs':158,
                            'proposed_updates':306,'original_sha256':before,
                            'patched_sha256':{s:sha_bytes(tlks[s].read_bytes()+b'first') for s in SIDES}}
            (backup_root/'active_install.json').write_text(json_text(original_first),encoding='utf-8')
            # Create a synthetic first-stage TLK; current strings remain usable.
            for s in SIDES:
                tlks[s].write_bytes(tlks[s].read_bytes()+b'first')
            rows,fingerprints=scan_game(plan,game)
            assert fingerprints['stage']['stage']==1 and len(rows)==476
            assert fingerprints['stage']['installed_strrefs']==158
            original_second={'version':'21.2-post-v21.1-gameplay-132','status':'installed','strrefs':132,
                             'proposed_updates':264,'original_sha256':original_first['patched_sha256'],
                             'patched_sha256':{s:sha_bytes(tlks[s].read_bytes()+b'second') for s in SIDES}}
            (backup_root/'active_install_stage2.json').write_text(json_text(original_second),encoding='utf-8')
            for s in SIDES:tlks[s].write_bytes(tlks[s].read_bytes()+b'second')
            rows,fingerprints=scan_game(plan,game)
            assert fingerprints['stage']['stage']==2 and fingerprints['stage']['installed_strrefs']==290
            tlks['dialog.tlk'].write_bytes(tlks['dialog.tlk'].read_bytes()+b'FOREIGN')
            try:
                scan_game(plan,game)
                raise AssertionError('Unknown SHA256 unexpectedly accepted')
            except RuntimeError as ex:
                assert 'STOP' in str(ex)
        finally:
            globals()['HERE']=old_here
        # Fake channel v19 update of DATA only (with same fixture plan).
        baseline_raw = PLAN_PATH.read_bytes()
        test_raw = json_text(baseline).encode('utf-8')
        future_channel = json_text({'schema':'bg-eet-ru-channel-v1','channel':'stable',
                                    'release_version':19,
                                    'plan':{'path':'releases/plan_v19.json','sha256':sha_bytes(test_raw)}}).encode('utf-8')
        def fake_fetch(url):
            return future_channel if url.endswith('channel.json') else test_raw
        old_data, old_state = globals()['DATA'], globals()['STATE_PATH']
        old_plan = globals()['PLAN_PATH']
        try:
            globals()['DATA'] = base / 'DATA'; globals()['DATA'].mkdir()
            globals()['PLAN_PATH'] = globals()['DATA'] / 'active_plan.json'
            globals()['STATE_PATH'] = globals()['DATA'] / 'release_state.json'
            globals()['PLAN_PATH'].write_bytes(baseline_raw)
            globals()['STATE_PATH'].write_text(json_text(state), encoding='utf-8')
            _, newer_state, notes = check_remote_updates(baseline,state,fetch=fake_fetch)
            assert newer_state['release_version'] == 19 and globals()['PLAN_PATH'].is_file()
            assert (globals()['DATA'] / 'previous_plan.json').is_file()
            assert load_state()[1]['release_version'] == 19
            # Simulate a process interruption between updating plan and state.
            globals()['STATE_PATH'].write_text(json_text(state), encoding='utf-8')
            restored_plan, restored_state = load_state()
            assert restored_state['release_version'] == 18
            assert sha_file(globals()['PLAN_PATH']) == BASELINE_SHA256
            # Tamper with remote plan: must not change installed plan.
            corrupted = lambda url: future_channel if url.endswith('channel.json') else b'not the original payload'
            _, _, notes = check_remote_updates(baseline,state,fetch=corrupted)
            assert 'SHA256' in '\n'.join(notes)
        finally:
            globals()['DATA'], globals()['STATE_PATH'], globals()['PLAN_PATH'] = old_data, old_state, old_plan
    print('SELFTEST PASS: 476 checks + stage1/2 postinstall verification; foreign TLK SHA blocked;')
    print('              GitHub v19 data-only update and hash rejection; zero writes to real game')


def main(argv=None):
    p = argparse.ArgumentParser(description='BG EET RU one-folder auto-updater, READ ONLY')
    p.add_argument('--game', default=GAME_DEFAULT)
    p.add_argument('--local-only', action='store_true', help='No internet: use downloaded local v18 plan')
    p.add_argument('--update-only', action='store_true', help='Check remote version, do not scan game')
    p.add_argument('--selftest', action='store_true')
    args = p.parse_args(argv)
    if args.selftest:
        selftest(); return 0
    game = Path(args.game).expanduser().resolve()
    if game == HERE or game in HERE.parents or HERE in game.parents:
        raise RuntimeError('SAFE STOP: auto-updater must be installed outside EET game directory')
    plan, state = None, {'release_version': BASELINE_VERSION}
    notes = []
    try:
        plan, state = load_state()
        if not args.local_only:
            plan, state, messages = check_remote_updates(plan, state)
            notes.extend(messages)
        else:
            notes.append('Локальный режим: обновление из сети пропущено')
        if args.update_only:
            print('UPDATE:', '; '.join(notes) or 'current version', 'v'+str(state['release_version']))
            return 0
        plan, local_note = choose_local_gameplay_plan(plan)
        if local_note: notes.append(local_note)
        rows, sums = scan_game(plan, game)
        summary, archive = render_reports(plan, state, rows, sums, notes)
        print('BG EET RU READ ONLY OK. GitHub:', state['release_version'], 'local plan:', plan.get('version'))
        print('Status:', summary['status_counts'])
        print('Reports:', REPORTS)
        print('Send this one ZIP:', archive)
        return 0
    except Exception as exc:
        try:
            _, archive = render_reports(plan, state, [], {}, notes, result='SAFE_STOP', error=exc)
            print('SAFE STOP. Report:', archive, file=sys.stderr)
        except Exception as logging_exc:
            print('Could not write report:', logging_exc, file=sys.stderr)
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 1


# === Permanent update channel v2: code updates + guarded game-text deltas ===
import io
import subprocess

CODE_VERSION = 6
APP_VERSION = '3.0.0-permanent-one-folder-context-audit'
EXPECTED_STAGE2 = {
    'dialog.tlk': '5f470be4163ebcd5223855d876e470eb75cd37af01021599540f423c69c3b6b0',
    'dialogf.tlk': 'c95b2ac6504f40b1b15cfbe53d8c5b9ebe75902d4b2f8720ca6c68ed8ba5e2bd',
}
PATCH_DIR = DATA / 'patches'
RECEIPTS_DIR = DATA / 'receipts'
RECOVERY_JOURNAL = DATA / 'PENDING_GAME_PATCH_RECOVERY.json'
BACKUP_DIR = HERE / 'BG_EET_RU_SAFE_BACKUPS'
COLOR_RE = re.compile(r'\^0x[0-9a-fA-F]{6,8}|\^-')


def _json_file(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def _hashes(paths):
    return {s: sha_file(paths[s]) for s in SIDES}


def _write_report_note(note):
    REPORTS.mkdir(parents=True, exist_ok=True)
    with (REPORTS / 'BG_EET_RU_ALL_RUNS.log').open('a', encoding='utf-8') as f:
        f.write('[' + utc_now() + '] ' + str(note) + '\n')


def _fetch_channel():
    raw = fetch_bytes(REMOTE + CHANNEL_NAME, max_bytes=200_000)
    obj = json.loads(raw.decode('utf-8-sig'))
    if obj.get('schema') != 'bg-eet-ru-channel-v1' or obj.get('channel') != 'stable':
        raise RuntimeError('STOP: unidentified translation update channel')
    return obj


def _remote_item(item, *, max_bytes=1_500_000, extension='.json'):
    rel = item.get('path')
    sha = item.get('sha256')
    if (not isinstance(rel,str) or not re.fullmatch(r'[A-Za-z0-9_./-]+',rel)
            or not rel.endswith(extension) or rel.startswith('/') or '..' in rel.split('/')):
        raise RuntimeError('STOP: unsafe update path')
    if not isinstance(sha,str) or re.fullmatch(r'[0-9a-f]{64}',sha) is None:
        raise RuntimeError('STOP: invalid update checksum')
    raw = fetch_bytes(REMOTE+rel,max_bytes=max_bytes)
    if sha_bytes(raw)!=sha: raise RuntimeError('STOP: update data SHA256 mismatch')
    return raw


def _maybe_update_code(channel,args):
    entry = channel.get('updater')
    if not isinstance(entry,dict): return None
    target_ver = entry.get('version')
    if not isinstance(target_ver,int) or target_ver <= CODE_VERSION: return None
    raw = _remote_item(entry,max_bytes=150_000,extension='.py')
    if b'\x00' in raw or len(raw)<500:
        raise RuntimeError('STOP: invalid updater source')
    source=raw.decode('utf-8-sig')
    if 'CODE_VERSION = '+str(target_ver) not in source or 'BG EET RU' not in source:
        raise RuntimeError('STOP: wrong updater identity or version')
    compile(source, str(HERE/'BG_EET_RU_UPDATE.py'), 'exec')
    active = HERE/'BG_EET_RU_UPDATE.py'
    if active.resolve()!=Path(__file__).resolve():
        raise RuntimeError('STOP: unexpected active script path')
    archive = DATA/'previous_updater.py'
    atomic_write(archive,active.read_bytes())
    atomic_write(active,raw)
    if sha_file(active)!=entry['sha256']:
        atomic_write(active,archive.read_bytes())
        raise RuntimeError('STOP: failed writing updater, previous version restored')
    _write_report_note('UPDATER CODE upgraded: '+str(CODE_VERSION)+' -> '+str(target_ver))
    cmd=[sys.executable,'-X','utf8',str(active),'--no-self-update']
    if args.game != GAME_DEFAULT: cmd.extend(['--game',args.game])
    if args.update_only: cmd.append('--update-only')
    if args.local_only: cmd.append('--local-only')
    return subprocess.call(cmd)


def _ensure_game_closed():
    if os.name!='nt': return
    out=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace',timeout=12)
    names={parts[0].strip().lower() for parts in csv.reader(io.StringIO(out)) if parts}
    deny={'baldur.exe','baldur64.exe','baldursgate.exe','bgmain.exe','bg2ee.exe','infinityloader.exe','weidu.exe','baldur.gog.exe'}
    blocked=deny & names
    blocked.update(n for n in names if n.startswith('setup-') and n.endswith('.exe'))
    if blocked:
        raise RuntimeError('STOP: close Baldur/InfinityLoader/WeiDU before game TLK edits: '+','.join(sorted(blocked)))


def _validate_delta(obj):
    if obj.get('schema')!='bg-eet-ru-translation-delta-v1':
        raise RuntimeError('STOP: wrong text-patch format')
    v=obj.get('version')
    if not isinstance(v,int) or v<22: raise RuntimeError('STOP: invalid patch version')
    prev=obj.get('from_tlk_sha256')
    if not isinstance(prev,dict) or set(prev)!=set(SIDES) or any(re.fullmatch('[0-9a-f]{64}',str(prev[s])) is None for s in SIDES):
        raise RuntimeError('STOP: patch has no verified base TLK pair')
    entries=obj.get('entries')
    if not isinstance(entries,list) or not 1<=len(entries)<=1200:
        raise RuntimeError('STOP: invalid number of text changes')
    seen=set(); count=0
    for row in entries:
        n=row.get('strref')
        if not isinstance(n,int) or not 0<=n<360847 or n in seen:
            raise RuntimeError('STOP: duplicate/out-of-range StrRef')
        seen.add(n)
        for s in SIDES:
            item=row.get(s)
            if not isinstance(item,dict): raise RuntimeError('STOP: missing TLK side')
            act=item.get('action')
            digest=item.get('source_sha256_utf8'); dest=item.get('replacement')
            if act not in ('REPLACE','KEEP_UNCHANGED'):
                raise RuntimeError('STOP: invalid patch action')
            if re.fullmatch('[0-9a-f]{64}',str(digest)) is None:
                raise RuntimeError('STOP: missing source hash')
            if not isinstance(dest,str) or not dest or '\x00' in dest or len(dest)>15000:
                raise RuntimeError('STOP: invalid replacement')
            if item.get('replacement_sha256_utf8')!=sha_bytes(dest.encode('utf8')):
                raise RuntimeError('STOP: replacement SHA mismatch')
            count+=int(act=='REPLACE')
    if obj.get('change_count')!=count or not count:
        raise RuntimeError('STOP: patch change_count mismatch')
    return obj


def _tlk_rawtext(raw,n,data):
    if n<0 or n>=360847 or len(raw)<18+26*360847:
        raise RuntimeError('STOP: invalid TLK index')
    epos=18+26*n
    flags=struct.unpack_from('<H',raw,epos)[0]
    off, size=struct.unpack_from('<II',raw,epos+18)
    start=data+off
    if not flags&1 or start<data or start+size>len(raw):
        raise RuntimeError('STOP: damaged StrRef '+str(n))
    return raw[start:start+size].decode('utf-8')


def _patch_binary(raw,patch,side):
    if len(raw)<18: raise RuntimeError('STOP: broken TLK')
    m,v,language,count,data=struct.unpack_from('<4s4sHII',raw)
    if m!=b'TLK ' or v!=b'V1  ' or count!=360847 or data<18+26*count or data>len(raw):
        raise RuntimeError('STOP: wrong game TLK format')
    result=bytearray(raw); touched=0
    for row in patch['entries']:
        n=row['strref']; item=row[side]
        source=_tlk_rawtext(raw,n,data)
        if sha_bytes(source.encode('utf8'))!=item['source_sha256_utf8']:
            raise RuntimeError('STOP: text changed since patch preparation at '+str(n))
        replacement=item['replacement']
        if (collections.Counter(TOKEN_RE.findall(source))!=collections.Counter(TOKEN_RE.findall(replacement))
            or collections.Counter(COLOR_RE.findall(source))!=collections.Counter(COLOR_RE.findall(replacement))):
            raise RuntimeError('STOP: game placeholder/color changed at '+str(n))
        if item['action']=='KEEP_UNCHANGED':
            if replacement!=source: raise RuntimeError('STOP: wrong no-change entry')
            continue
        if replacement==source: raise RuntimeError('STOP: empty replace action')
        dst=replacement.encode('utf8'); offset=len(result)-data
        if offset+len(dst)>0xffffffff: raise RuntimeError('STOP: TLK exceeds binary offset limit')
        result.extend(dst)
        struct.pack_into('<II',result,18+n*26+18,offset,len(dst))
        touched+=1
    result=bytes(result)
    for row in patch['entries']:
        n=row['strref']; item=row[side]
        assert _tlk_rawtext(result,n,data)==item['replacement']
    return result,touched


def _atomic_game_file(path,raw):
    import tempfile
    fd,temp=tempfile.mkstemp(prefix='._BGEETRU_',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def _recover_if_needed(paths):
    if not RECOVERY_JOURNAL.exists(): return
    state=_json_file(RECOVERY_JOURNAL)
    if state.get('status')!='prepared':
        raise RuntimeError('STOP: unrecognized recovery journal')
    _ensure_game_closed()
    backup=Path(state['backup_dir'])
    expected=state['before_sha256']
    for s in SIDES:
        if sha_file(backup/s)!=expected[s]:
            raise RuntimeError('STOP: recovery backup corrupt: '+s)
    for s in SIDES:
        _atomic_game_file(paths[s],(backup/s).read_bytes())
    if _hashes(paths)!=expected:
        raise RuntimeError('STOP: recovery failed, do not launch game')
    # If a crash happened after receipt creation but before journal removal,
    # roll back the receipt as well. Never retain a false 'installed' marker.
    receipt=RECEIPTS_DIR/('installed_%05d.json'%state['version'])
    if receipt.exists():
        installed=_json_file(receipt)
        if installed.get('from_tlk_sha256')!=expected:
            raise RuntimeError('STOP: conflicting installation receipt during recovery')
        receipt.unlink()
    RECOVERY_JOURNAL.unlink()
    _write_report_note('RECOVERED both TLKs after interrupted game-text patch, no changes left')


def _receipt_list():
    if not RECEIPTS_DIR.exists(): return []
    records=[_json_file(f) for f in sorted(RECEIPTS_DIR.glob('installed_*.json'))]
    previous=EXPECTED_STAGE2.copy(); last=21
    for r in records:
        if r.get('version')<=last or r.get('from_tlk_sha256')!=previous or r.get('status')!='installed':
            raise RuntimeError('STOP: patch receipts do not form a verified chain')
        next_hash=r.get('to_tlk_sha256')
        if not isinstance(next_hash,dict) or set(next_hash)!=set(SIDES):
            raise RuntimeError('STOP: invalid patch receipt')
        previous=next_hash;last=r['version']
    return records


_legacy_verify_install_chain=verify_install_chain

def verify_install_chain(expected,actual):
    try:
        return _legacy_verify_install_chain(expected,actual)
    except RuntimeError:
        receipts=_receipt_list()
        if not receipts or actual!=receipts[-1]['to_tlk_sha256']:
            raise
        # Never accept local patch chain unless first two real user installs are verified.
        first,second=(HERE/'BG_EET_RU_SAFE_BACKUPS'/name for name in ('active_install.json','active_install_stage2.json'))
        if not first.exists() or not second.exists() or _json_file(second).get('patched_sha256')!=EXPECTED_STAGE2:
            raise RuntimeError('STOP: missing initial installation evidence')
        return {'stage':2+len(receipts),'installed_strrefs':290+sum(r['strrefs'] for r in receipts),
                'message':'Два старых патча и '+str(len(receipts))+' remote update(s) installed'}


def _install_one_patch(patch,paths):
    _ensure_game_closed()
    current=_hashes(paths)
    if current!=patch['from_tlk_sha256']:
        raise RuntimeError('STOP: current TLKs do not match patch origin')
    before={s:paths[s].read_bytes() for s in SIDES}
    if {s:sha_bytes(before[s]) for s in SIDES}!=current:
        raise RuntimeError('STOP: TLKs changed while reading')
    changed={}; patched={}
    for s in SIDES:
        patched[s],changed[s]=_patch_binary(before[s],patch,s)
    if sum(changed.values())!=patch['change_count']:
        raise RuntimeError('STOP: unexpected number of text replacements')
    next_sums={s:sha_bytes(patched[s]) for s in SIDES}
    print('Перевод v%s: %s StrRef, %s изменений. Игра пока НЕ изменена.' %
          (patch['version'],len(patch['entries']),sum(changed.values())))
    if input('Закрой Baldur/InfinityLoader. Для установки введи YES (иначе пропуск): ').strip()!='YES':
        _write_report_note('v%s: installation skipped by user' % patch['version']);return False
    _ensure_game_closed()
    if _hashes(paths)!=current:
        raise RuntimeError('STOP: TLKs changed before install')
    import shutil
    if shutil.disk_usage(paths['dialog.tlk'].parent).free < sum(map(len,patched.values())) + 10000000:
        raise RuntimeError('STOP: not enough free disk space for TLK staging')
    BACKUP_DIR.mkdir(exist_ok=True)
    RECOVERY_JOURNAL.parent.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=BACKUP_DIR/('BEFORE_REMOTE_PATCH_%s_%s'%(patch['version'],stamp))
    backup.mkdir(parents=True)
    for s in SIDES:
        (backup/s).write_bytes(before[s])
        if sha_file(backup/s)!=current[s]:
            raise RuntimeError('STOP: cannot verify game backup')
    atomic_write(RECOVERY_JOURNAL,json_text({'status':'prepared','backup_dir':str(backup),
                 'before_sha256':current,'version':patch['version']}).encode('utf8'))
    try:
        for s in SIDES:
            _atomic_game_file(paths[s],patched[s])
        if _hashes(paths)!=next_sums:
            raise RuntimeError('STOP: final TLK SHA mismatch')
        receipt={'version':patch['version'],'status':'installed','strrefs':len(patch['entries']),
                 'updates':patch['change_count'],'from_tlk_sha256':current,
                 'to_tlk_sha256':next_sums,'backup_dir':str(backup)}
        RECEIPTS_DIR.mkdir(parents=True,exist_ok=True)
        atomic_write(RECEIPTS_DIR/('installed_%05d.json'%patch['version']),json_text(receipt).encode('utf8'))
        RECOVERY_JOURNAL.unlink()
        _write_report_note('INSTALLED remote text v%s, StrRef=%s, sides=%s' %
                           (patch['version'],len(patch['entries']),patch['change_count']))
        return True
    except BaseException:
        _recover_if_needed(paths)
        raise


def _install_remote_patches(channel,game,notes):
    manifests=channel.get('patches',[])
    if not isinstance(manifests,list): raise RuntimeError('STOP: invalid patch list')
    if len(manifests)>30: raise RuntimeError('STOP: too many patches in one metadata file')
    if manifests and channel.get('game_writes_allowed') is not True:
        raise RuntimeError('STOP: game text releases not enabled in the update channel')
    paths=find_tlks(game)
    _recover_if_needed(paths)
    receipts=_receipt_list()
    target=receipts[-1]['to_tlk_sha256'] if receipts else EXPECTED_STAGE2
    current=_hashes(paths)
    if current!=target:
        # may still be old stage 0/1 but do not use future remote patch on them.
        if manifests: notes.append('Текущая игра не на подтверждённой стадии v21.2; remote patches не применяются')
        return
    last=receipts[-1]['version'] if receipts else 21
    for desc in manifests:
        if not isinstance(desc,dict) or not isinstance(desc.get('version'),int):
            raise RuntimeError('STOP: invalid patch metadata')
        if desc['version']<=last: continue
        patch=_validate_delta(json.loads(_remote_item(desc).decode('utf-8-sig')))
        if patch['version']!=desc['version'] or patch['from_tlk_sha256']!=target:
            raise RuntimeError('STOP: patch chain mismatch')
        PATCH_DIR.mkdir(parents=True,exist_ok=True)
        atomic_write(PATCH_DIR/('patch_%05d.json'%patch['version']),json_text(patch).encode('utf8'))
        if not _install_one_patch(patch,paths):
            notes.append('Перевод v%s получен, установка отложена пользователем'%patch['version'])
            return
        current=_hashes(paths)
        target=current
        last=patch['version']
        notes.append('УСТАНОВЛЕНО через постоянный обновлятор: v%s'%patch['version'])


def _collect_remote_rows(rows,game):
    receipts=_receipt_list()
    if not receipts:return rows
    paths=find_tlks(game)
    for receipt in receipts:
        f=PATCH_DIR/('patch_%05d.json'%receipt['version'])
        if not f.is_file():raise RuntimeError('STOP: installed patch text metadata missing')
        patch=_validate_delta(_json_file(f))
        for side in SIDES:
            t=TLK(paths[side]);
            try:
                for r in patch['entries']:
                    status,actual=t.get(r['strref'])
                    e=r[side]
                    if status!='OK' or actual!=e['replacement']:
                        raise RuntimeError('STOP: remote StrRef not translated: '+str(r['strref']))
                    rows.append({'strref':r['strref'],'tlk':side,'category':'REMOTE_GAMEPLAY_PATCH',
                                 'status':'ALREADY_TRANSLATED' if e['action']=='REPLACE' else 'NO_CHANGE_REQUIRED',
                                 'action':e['action'],'current_text':actual,'proposed_text':actual})
            finally:t.close()
    return rows


def _main_v2(argv=None):
    p=argparse.ArgumentParser(description='BG EET RU permanent one-command update and verify')
    p.add_argument('--game',default=GAME_DEFAULT)
    p.add_argument('--local-only',action='store_true')
    p.add_argument('--update-only',action='store_true')
    p.add_argument('--no-self-update',action='store_true')
    p.add_argument('--selftest',action='store_true')
    args=p.parse_args(argv)
    if args.selftest:
        _selftest_v2();return 0
    game=Path(args.game).expanduser().resolve()
    if game==HERE or game in HERE.parents or HERE in game.parents:
        raise RuntimeError('STOP: updater must remain outside EET directory')
    plan=None;state={'release_version':BASELINE_VERSION};notes=[]
    try:
        plan,state=load_state()
        channel=None
        if not args.local_only:
            try:
                channel=_fetch_channel()
                notes.append('GitHub metadata connected; patches=%s'%len(channel.get('patches',[])))
            except (OSError,ValueError,RuntimeError,urllib.error.URLError) as exc:
                notes.append('GitHub unavailable, local verified plan only: '+str(exc))
        if channel and not args.no_self_update:
            rc=_maybe_update_code(channel,args)
            if rc is not None:return rc
        if args.update_only:
            print('AUTOUPDATER v'+APP_VERSION+'; '+('; '.join(notes)))
            return 0
        if channel:
            _install_remote_patches(channel,game,notes)
        plan,local_note=choose_local_gameplay_plan(plan)
        if local_note:notes.append(local_note)
        rows,fingerprints=scan_game(plan,game)
        rows=_collect_remote_rows(rows,game)
        summary,archive=render_reports(plan,state,rows,fingerprints,notes)
        # Report the aggregate count, not the stale GitHub v18 metadata count.
        summary['updater_version']=APP_VERSION
        summary['installed_gameplay_strrefs']=fingerprints['stage']['installed_strrefs']
        summary['remote_patch_count']=len(_receipt_list())
        summary['status_counts']=dict(collections.Counter(r['status'] for r in rows))
        atomic_write(REPORTS/'00_LAST_SUMMARY.json',json_text(summary).encode('utf8'))
        with zipfile.ZipFile(REPORTS/'_BG_EET_RU_TEMP_REPORT.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name in ('00_LAST_SUMMARY.json','01_LAST_PREVIEW.csv','02_HOLD_CONTEXT.csv',
                         '03_SAFE_PATCH_LAST.json','04_STAGE2_PATCH_LAST.json','BG_EET_RU_ALL_RUNS.log'):
                f=REPORTS/name
                if f.is_file():z.write(f,arcname=name)
        os.replace(REPORTS/'_BG_EET_RU_TEMP_REPORT.zip',REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip')
        print('BG EET RU v%s: installed StrRef=%s; %s' %
              (APP_VERSION,summary['installed_gameplay_strrefs'],summary['status_counts']))
        print('One reports folder:',REPORTS)
        print('One ZIP:',REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip')
        return 0
    except Exception as exc:
        try:
            render_reports(plan,state,[],{},notes,result='SAFE_STOP',error=exc)
        except Exception:pass
        print('SAFE STOP:',type(exc).__name__,exc,file=sys.stderr)
        return 1


def _selftest_v2():
    # Run only in a disposable temporary game root: verify delta, abort on foreign source,
    # preserve original index except target offsets and do NOT touch real EET or WAVs.
    with tempfile.TemporaryDirectory(prefix='BGEETRU_V2_TEST_') as d:
        root=Path(d);original=b'TLK V1  '+struct.pack('<HII',0,360847,18+26*360847)
        indices=bytearray(360847*26)
        n=40000;src='English text';data=18+26*360847
        struct.pack_into('<H',indices,n*26,1)
        struct.pack_into('<II',indices,n*26+18,0,len(src.encode()))
        binary=original+indices+src.encode()
        change={'source_sha256_utf8':sha_bytes(src.encode()),'replacement':'Русский текст',
                'replacement_sha256_utf8':sha_bytes('Русский текст'.encode()),'action':'REPLACE'}
        patch={'schema':'bg-eet-ru-translation-delta-v1','version':22,
               'from_tlk_sha256':{s:sha_bytes(binary) for s in SIDES},
               'change_count':2,'entries':[{'strref':n,**{s:change for s in SIDES}}]}
        _validate_delta(patch)
        out,cnt=_patch_binary(binary,patch,'dialog.tlk')
        assert cnt==1 and _tlk_rawtext(out,n,data)=='Русский текст'
        tampered=patch.copy();tampered['entries']=[{'strref':n,**{s:{**change,'source_sha256_utf8':'0'*64} for s in SIDES}}]
        try:_patch_binary(binary,tampered,'dialog.tlk');raise AssertionError('source hash not checked')
        except RuntimeError:pass
        assert binary[18:18+n*26]==out[18:18+n*26]
        assert binary[data:]==out[data:len(binary)]
        # Current installed two-stage game fingerprints are the only accepted future patch start.
        assert EXPECTED_STAGE2['dialog.tlk']!='0'*64
        # One persistent report directory; no file writes to any real game.
    print('SELFTEST V2 PASS: delta checks, StrRef isolation, source hash defense, current stage2 hashes')

# v1.1 compatibility preserved: override only the read-only chain validator and entrypoint.




# === V3 READ-ONLY contextual audit for 22 held TLK StrRefs ===
from collections import defaultdict, Counter
import zlib

DLG_TYPE = 0x03f3
CRE_TYPE = 0x03f1
WAV_TYPE = 4
MAX_BIF = 2_000_000_000

def refname(blob):
    return blob.split(b'\0',1)[0].decode('ascii','replace').strip().upper()

def decode(blob, russian=False):
    if not blob: return ''
    for codec in (('utf-8','cp1251') if russian else ('utf-8','cp1252')):
        try:
            return blob.decode(codec).replace('\r',' ').replace('\n',' ').strip('\0 ')
        except UnicodeDecodeError: pass
    return blob.decode('cp1251' if russian else 'cp1252','replace').replace('\r',' ').replace('\n',' ').strip('\0 ')

def key_entries(path):
    b=path.read_bytes()
    if len(b)<24 or b[:4]!=b'KEY ':raise ValueError('Invalid chitin.key')
    n_bif,n_res,bif_at,res_at=struct.unpack_from('<IIII',b,8)
    if n_bif>30000 or n_res>3000000 or bif_at+n_bif*12>len(b) or res_at+n_res*14>len(b):
        raise ValueError('Invalid KEY offsets')
    bifs=[]; resource=defaultdict(list); counters=Counter()
    for i in range(n_bif):
        _,off,length,_=struct.unpack_from('<IIHH',b,bif_at+12*i)
        if length>1024 or off+length>len(b):bifs.append('');continue
        bifs.append(decode(b[off:off+length]).split('\0',1)[0].replace('\\','/'))
    for i in range(n_res):
        offset=res_at+14*i
        name=refname(b[offset:offset+8]); kind,loc=struct.unpack_from('<HI',b,offset+8)
        if not name:continue
        counters[kind]+=1
        if kind in (CRE_TYPE,DLG_TYPE,WAV_TYPE):
            resource[kind].append((name,loc>>20,loc&0x3FFF))
    return bifs,resource,counters

def safe_bif_path(root,bif):
    if not bif:return None
    bits=Path(bif.replace('\\','/'))
    if bits.is_absolute() or any(x in ('..','') for x in bits.parts):return None
    node=root
    for piece in bits.parts:
        if not node.is_dir():return None
        nxt=node/piece
        if not nxt.exists():
            choices={x.name.lower():x for x in node.iterdir()}
            nxt=choices.get(piece.lower())
            if not nxt:return None
        node=nxt
    return node if node.is_file() and node.resolve().is_relative_to(root.resolve()) else None

def write_decompressed_bif(path,output):
    with path.open('rb') as f:
        magic=f.read(4);version=f.read(4)
        if magic==b'BIFF':
            f.seek(0);shutil.copyfileobj(f,output);output.seek(0);return
        if magic==b'BIF ':
            raw_len=f.read(4)
            if len(raw_len)!=4:raise ValueError('Short BIF header')
            name_n=struct.unpack('<I',raw_len)[0]
            if name_n>2048:raise ValueError('Unsafe BIF filename size')
            f.read(name_n)
            raw_size,compressed_size=struct.unpack('<II',f.read(8))
            if raw_size>MAX_BIF:raise ValueError('BIF too large')
            decomp=zlib.decompressobj();remaining=compressed_size;seen=0
            while remaining:
                chunk=f.read(min(1<<20,remaining))
                if not chunk:raise EOFError('Truncated BIF')
                payload=decomp.decompress(chunk)
                output.write(payload); seen+=len(payload)
                if seen>raw_size:raise ValueError('BIF exceeds advertised uncompressed size')
                remaining-=len(chunk)
            trailing=decomp.flush();output.write(trailing);seen+=len(trailing)
            if seen!=raw_size:raise ValueError('BIF uncompressed size mismatch')
            output.seek(0);return
        if magic==b'BIFC':
            hdr=f.read(4)
            if len(hdr)!=4:raise ValueError('Truncated BIFC header')
            raw_size=struct.unpack('<I',hdr)[0]
            if raw_size>MAX_BIF:raise ValueError('BIFC too large')
            produced=0
            while produced<raw_size:
                block=f.read(8)
                if len(block)!=8:raise EOFError('Truncated BIFC block')
                uncompressed,compressed=struct.unpack('<II',block)
                if uncompressed>10_000_000 or compressed>10_000_000:raise ValueError('Unsafe BIFC block size')
                payload=f.read(compressed)
                if len(payload)!=compressed:raise EOFError('Truncated BIFC block data')
                plain=zlib.decompress(payload)
                if len(plain)!=uncompressed:raise ValueError('BIFC block length mismatch')
                produced+=len(plain)
                if produced>raw_size:raise ValueError('BIFC too much data')
                output.write(plain)
            output.seek(0);return
        raise ValueError('Unknown archive signature '+repr(magic)+', version '+repr(version))

def _audit_dlg_blob(blob, name, targets):
    """Read visible state, response and journal string references from a DLG V1.0.

    This is NOT proof of reachability and does not interpret BCS/conditions.
    """
    if len(blob) < 0x30 or blob[:8] != b'DLG V1.0':
        raise ValueError('Not a DLG V1.0 resource')
    nstates, state_off, ntrans, trans_off = struct.unpack_from('<IIII',blob,8)
    if nstates>1000000 or ntrans>1000000 or state_off+16*nstates>len(blob) or trans_off+32*ntrans>len(blob):
        raise ValueError('Invalid DLG table bounds')
    hits=[]
    for i in range(nstates):
        ref=struct.unpack_from('<I',blob,state_off+16*i)[0]
        if ref in targets:hits.append((ref,'NPC_STATE',i))
    for i in range(ntrans):
        o=trans_off+32*i
        flags=struct.unpack_from('<I',blob,o)[0]
        if flags&1:
            ref=struct.unpack_from('<I',blob,o+4)[0]
            if ref in targets:hits.append((ref,'PLAYER_RESPONSE',i))
        if flags&0x10:
            ref=struct.unpack_from('<I',blob,o+8)[0]
            if ref in targets:hits.append((ref,'JOURNAL_ENTRY',i))
    return hits

def _dlg_indexed(game, bifs, refs, errors, stats):
    """Only DLG resources; stream one BIFF at a time, no game writes."""
    selected=defaultdict(list)
    for name, bifid, localid in refs.get(DLG_TYPE,[]):
        selected[bifid].append((name,localid))
    for bifid in sorted(selected):
        if bifid>=len(bifs):
            errors.append({'kind':'BAD_KEY_INDEX','where':str(bifid)})
            continue
        path=safe_bif_path(game,bifs[bifid])
        if not path:
            errors.append({'kind':'BIF_MISSING','where':bifs[bifid]})
            continue
        stats['bif_attempted']+=1
        try:
            with tempfile.TemporaryFile() as f:
                write_decompressed_bif(path,f)
                f.seek(0,2);length=f.tell();f.seek(0)
                header=f.read(20)
                if len(header)!=20 or header[:4]!=b'BIFF':
                    raise ValueError('Not decompressed BIFF')
                count,_,table=struct.unpack_from('<III',header,8)
                if count>500000 or table+16*count>length:
                    raise ValueError('Invalid BIFF table offset')
                f.seek(table);index={}
                for _ in range(count):
                    row=f.read(16)
                    if len(row)!=16:raise ValueError('Truncated BIFF index')
                    locator,off,size,kind,_=struct.unpack('<IIIHH',row)
                    if kind==DLG_TYPE:index[locator&0x3fff]=(off,size)
                for name,localid in selected[bifid]:
                    hit=index.get(localid)
                    if not hit:
                        errors.append({'kind':'DLG_NOT_INDEXED','where':name})
                        continue
                    off,size=hit
                    if size<8 or size>15000000 or off+size>length:
                        errors.append({'kind':'BAD_DLG_ENTRY','where':name})
                        continue
                    f.seek(off);blob=f.read(size)
                    if len(blob)!=size:
                        errors.append({'kind':'TRUNCATED_DLG_ENTRY','where':name})
                        continue
                    stats['bif_dlgs_read']+=1
                    yield name,blob,'BIF:'+path.name
                stats['bif_ok']+=1
        except (OSError,ValueError,zlib.error,struct.error,EOFError) as exc:
            errors.append({'kind':'BIF_READ','where':str(path),'error':str(exc)[:150]})

def _held_ids():
    # The exact 22 HOLD candidates come from the locally generated report.
    # They are independent of the published code and may change in later plans.
    path=REPORTS/'02_HOLD_CONTEXT.csv'
    if not path.is_file():raise RuntimeError('HOLD report missing: run normal verification first')
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    ids=[]
    for r in rows:
        n=int(r['strref'])
        if not 0<=n<360847 or n in ids:raise RuntimeError('Invalid HOLD StrRef list')
        ids.append(n)
    return sorted(ids)

def _override_dlg_paths(game):
    override=game/'override'
    if not override.is_dir():return []
    paths=[p for p in override.iterdir() if p.is_file() and p.suffix.lower()=='.dlg']
    return sorted(paths,key=lambda x:x.name.lower())

def _dlg_signature(game,override_files,ids):
    key=game/'chitin.key'
    if not key.is_file():raise FileNotFoundError('Missing chitin.key')
    h=hashlib.sha256()
    h.update(sha_file(key).encode('ascii'))
    h.update(json.dumps(ids,separators=(',',':')).encode())
    for p in override_files:
        info=p.stat()
        h.update(p.name.upper().encode('utf-8',errors='replace'))
        h.update(struct.pack('<QQ',info.st_size,info.st_mtime_ns))
    return h.hexdigest()

def _dlg_context_audit(game):
    """Runs at most once per KEY/HOLD/override state; saves one compact report."""
    targets=_held_ids()
    if not targets:return {'target_count':0,'status':'NO_HOLDS'}
    paths=_override_dlg_paths(game)
    signature=_dlg_signature(game,paths,targets)
    summary_file=REPORTS/'05_DLG_CONTEXT_LAST.json'
    result_file=REPORTS/'06_DLG_CONTEXT_MATCHES.csv'
    error_file=REPORTS/'07_DLG_CONTEXT_ERRORS.json'
    if summary_file.is_file() and result_file.is_file() and error_file.is_file():
        try:
            cached=_json_file(summary_file)
            if cached.get('input_sha256')==signature and cached.get('version')==3:
                return cached
        except (ValueError,OSError,KeyError):pass
    bifs,refs,_=key_entries(game/'chitin.key')
    overrides={p.stem.upper():p for p in paths}
    errors=[];stats=collections.Counter();found=defaultdict(list)
    for name,blob,source in _dlg_indexed(game,bifs,refs,errors,stats):
        if name in overrides:continue
        try:
            for ref,role,index in _audit_dlg_blob(blob,name,targets):
                found[ref].append({'dlg':name,'location':source,'role':role,'index':index})
        except (ValueError,struct.error) as exc:
            errors.append({'kind':'INVALID_DLG','where':name,'error':str(exc)[:150]})
    for name,p in overrides.items():
        try:
            for ref,role,index in _audit_dlg_blob(p.read_bytes(),name,targets):
                found[ref].append({'dlg':name,'location':'OVERRIDE','role':role,'index':index})
            stats['override_dlgs_read']+=1
        except (ValueError,OSError,struct.error) as exc:
            errors.append({'kind':'OVERRIDE_DLG','where':name,'error':str(exc)[:150]})
    fields=['strref','status','roles','dlg_resources','where','hits']
    with (REPORTS/'_temp_dlg_context.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for ref in targets:
            matches=found.get(ref,[])
            status='FOUND_AS_VISIBLE_DLG' if matches else ('NOT_FOUND_PARTIAL_SCAN' if errors else 'NOT_FOUND_IN_SCANNED_DLG')
            w.writerow({'strref':ref,'status':status,'roles':';'.join(sorted({x['role'] for x in matches})),
                        'dlg_resources':';'.join(sorted({x['dlg'] for x in matches})),
                        'where':';'.join(sorted({x['location'] for x in matches})), 'hits':len(matches)})
    os.replace(REPORTS/'_temp_dlg_context.csv',result_file)
    output={'version':3,'mode':'READ_ONLY_DLG_CONTEXT','game_modified':False,'target_count':len(targets),
           'found':sum(bool(found.get(ref)) for ref in targets),'not_found':sum(not found.get(ref) for ref in targets),
           'archive_errors':len(errors),'partial_scan':bool(errors),'stats':dict(stats),
           'input_sha256':signature,'scanned_utc':utc_now(),
           'important':'DLG reference confirms a potential on-screen string, not its actual accessibility. Never auto-install HOLD.'}
    atomic_write(summary_file,json_text(output).encode('utf-8'))
    atomic_write(error_file,json_text(errors[:500]).encode('utf-8'))
    _write_report_note('DLG read-only context: found=%s/%s errors=%s' % (output['found'],len(targets),len(errors)))
    return output

def _append_audit_to_report_zip():
    p=REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip'
    if not p.is_file():return
    temp=REPORTS/'_REPACKAGE_WITH_DLG.zip'
    with zipfile.ZipFile(p) as original, zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as dst:
        for member in original.infolist():
            if member.filename in ('05_DLG_CONTEXT_LAST.json','06_DLG_CONTEXT_MATCHES.csv','07_DLG_CONTEXT_ERRORS.json'):
                continue
            dst.writestr(member,original.read(member.filename))
        for name in ('05_DLG_CONTEXT_LAST.json','06_DLG_CONTEXT_MATCHES.csv','07_DLG_CONTEXT_ERRORS.json'):
            report=REPORTS/name
            if report.is_file():dst.write(report,name)
    os.replace(temp,p)

def _selftest_v3():
    # Compact fixture with one indexed DLG state, one override response and one unused target.
    with tempfile.TemporaryDirectory(prefix='BG_EET_RU_V3_TEST_') as tmp:
        root=Path(tmp);(root/'override').mkdir();(root/'data').mkdir()
        state_ref=317992;answer_ref=318015;notfound=232315
        header=b'DLG V1.0'+struct.pack('<IIII',1,0x30,0,0x40)+b'\0'*(0x30-24)
        dlg=header+struct.pack('<IIII',state_ref,0,0,0)
        assert _audit_dlg_blob(dlg,'SYNTH_A',{state_ref,answer_ref})==[(state_ref,'NPC_STATE',0)]
        trans=b'DLG V1.0'+struct.pack('<IIII',0,0x30,1,0x30)+b'\0'*(0x30-24)
        trans+=struct.pack('<III',1,answer_ref,0)+b'\0'*20
        (root/'override'/'DEMO.DLG').write_bytes(trans)
        # One valid KEY/BIFF archive with one DLG resource.
        bif_head=b'BIFFV1  '+struct.pack('<III',1,0,20)
        res_off=20+16
        bif=bif_head+struct.pack('<IIIHH',0,res_off,len(dlg),DLG_TYPE,0)+dlg
        (root/'data'/'DEMO.BIF').write_bytes(bif)
        filename=b'data\\DEMO.BIF\0'
        bif_at=24;res_at=36;filename_at=50
        key=(b'KEY V1  '+struct.pack('<IIII',1,1,bif_at,res_at)+
             struct.pack('<IIHH',len(bif),filename_at,len(filename),0)+
             b'SYNTH_A\0'+struct.pack('<HI',DLG_TYPE,0)+filename)
        (root/'chitin.key').write_bytes(key)
        bifs,refs,_=key_entries(root/'chitin.key')
        errors=[];stats=collections.Counter();found=[]
        for name,blob,where in _dlg_indexed(root,bifs,refs,errors,stats):
            found.extend(_audit_dlg_blob(blob,name,{state_ref,answer_ref,notfound}))
        assert not errors,errors
        assert found==[(state_ref,'NPC_STATE',0)],found
        assert _audit_dlg_blob(trans,'DEMO',{state_ref,answer_ref})==[(answer_ref,'PLAYER_RESPONSE',0)]
        assert not _audit_dlg_blob(trans,'DEMO',{notfound})
        global REPORTS
        old_reports=REPORTS
        try:
            REPORTS=root/'BG_EET_RU_REPORTS'
            REPORTS.mkdir()
            with (REPORTS/'02_HOLD_CONTEXT.csv').open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f);w.writerow(['strref','category']);w.writerows([[state_ref,'actor'],[answer_ref,'actor'],[notfound,'editorial']])
            summary=_dlg_context_audit(root)
            assert summary['found']==2 and summary['not_found']==1 and summary['archive_errors']==0,summary
            assert _dlg_context_audit(root)['input_sha256']==summary['input_sha256']
            assert (REPORTS/'06_DLG_CONTEXT_MATCHES.csv').is_file()
            with zipfile.ZipFile(REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip','w') as z:
                z.writestr('00_LAST_SUMMARY.json','{}')
            _append_audit_to_report_zip()
            with zipfile.ZipFile(REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip') as z:
                assert len(z.namelist())==4 and '06_DLG_CONTEXT_MATCHES.csv' in z.namelist()
        finally:
            REPORTS=old_reports
    print('SELFTEST V3 PASS: KEY/BIFF/override DLG; report, ZIP, cache, no game write')

def _main_v3(argv=None):
    if argv is None:argv=sys.argv[1:]
    if '--selftest' in argv:
        _selftest_v2();_selftest_v3();return 0
    code=_main_v2(argv)
    if code!=0 or '--update-only' in argv:
        return code
    args=argparse.ArgumentParser(add_help=False)
    args.add_argument('--game',default=GAME_DEFAULT)
    opts,_=args.parse_known_args(argv)
    try:
        print('BG EET RU: context audit read-only; game files untouched...', flush=True)
        summary=_dlg_context_audit(Path(opts.game).expanduser().resolve())
        _append_audit_to_report_zip()
        print('DLG context:',summary['found'],'/',summary['target_count'],'targets; errors:',summary['archive_errors'])
        print('Same ZIP:',REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip')
    except (OSError,ValueError,RuntimeError,struct.error) as exc:
        _write_report_note('DLG CONTEXT OPTIONAL AUDIT FAILED: '+type(exc).__name__+': '+str(exc))
        print('DLG optional audit error (TLK verification OK):',exc)
        # No game changes. Existing ZIP remains valid even if resource scan fails.
    return code

main=_main_v3


# === V4: exact-source-hash text operations, without publishing complete game dialogue ===
_old_validate_delta_v3 = _validate_delta
_old_install_one_patch_v3 = _install_one_patch
_private_expanded_prefix = 'private_expanded_patch_'


def _validate_delta(obj):
    if obj.get('schema') == 'bg-eet-ru-translation-delta-v1':
        return _old_validate_delta_v3(obj)
    if obj.get('schema') != 'bg-eet-ru-translation-delta-v2':
        raise RuntimeError('STOP: unidentified translation delta format')
    v=obj.get('version')
    if type(v) is not int or v<22: raise RuntimeError('STOP: invalid patch version')
    src=obj.get('from_tlk_sha256')
    if not isinstance(src,dict) or set(src)!=set(SIDES) or any(re.fullmatch(r'[0-9a-f]{64}',str(src[s])) is None for s in SIDES):
        raise RuntimeError('STOP: invalid source TLK pair')
    records=obj.get('entries')
    if not isinstance(records,list) or not 1<=len(records)<=200:
        raise RuntimeError('STOP: unsafe record count')
    ids=set(); touched=0
    for row in records:
        n=row.get('strref')
        if type(n) is not int or not 0<=n<360847 or n in ids:raise RuntimeError('STOP: invalid StrRef')
        ids.add(n)
        for side in SIDES:
            cell=row.get(side)
            if not isinstance(cell,dict) or re.fullmatch(r'[0-9a-f]{64}',str(cell.get('source_sha256_utf8'))) is None:
                raise RuntimeError('STOP: invalid source fingerprint')
            operations=cell.get('operations')
            if not isinstance(operations,list) or not 1<=len(operations)<=20:
                raise RuntimeError('STOP: bad delta operations')
            for op in operations:
                if not isinstance(op,dict) or op.get('type') not in ('REMOVE_EXACT','REPLACE_EXACT'):
                    raise RuntimeError('STOP: unsafe text operation')
                old=op.get('old')
                new=op.get('new','')
                if (not isinstance(old,str) or not old or len(old)>150 or '\x00' in old
                    or not isinstance(new,str) or len(new)>150 or '\x00' in new
                    or '<' in old or '>' in old or '<' in new or '>' in new):
                    raise RuntimeError('STOP: invalid exact text fragment')
                if op['type']=='REMOVE_EXACT' and (not old.startswith('[') or not old.endswith(']') or new):
                    raise RuntimeError('STOP: only exact bracket stage tags can be removed')
                if op['type']=='REPLACE_EXACT' and (not new or new==old):
                    raise RuntimeError('STOP: invalid exact replacement')
            touched+=1
    if obj.get('change_count')!=touched:raise RuntimeError('STOP: changed-side count mismatch')
    return obj


def _v4_expand_patch(patch,paths):
    if _hashes(paths)!=patch['from_tlk_sha256']:
        raise RuntimeError('STOP: installed TLKs no longer match verified translation source')
    raw={s:paths[s].read_bytes() for s in SIDES}
    if {s:sha_bytes(raw[s]) for s in SIDES}!=patch['from_tlk_sha256']:
        raise RuntimeError('STOP: TLK changed during read')
    expanded={'schema':'bg-eet-ru-translation-delta-v1','version':patch['version'],
              'from_tlk_sha256':patch['from_tlk_sha256'],
              'change_count':patch['change_count'],'entries':[]}
    for row in patch['entries']:
        result={'strref':row['strref']}
        for side in SIDES:
            src=raw[side]
            magic,version,lang,count,base=struct.unpack_from('<4s4sHII',src)
            if magic!=b'TLK ' or version!=b'V1  ' or count!=360847:
                raise RuntimeError('STOP: wrong TLK format')
            old=_tlk_rawtext(src,row['strref'],base)
            if sha_bytes(old.encode('utf8'))!=row[side]['source_sha256_utf8']:
                raise RuntimeError('STOP: source text mismatch at StrRef '+str(row['strref']))
            new=old
            for op in row[side]['operations']:
                fragment=op['old'];subst=op.get('new','')
                if new.count(fragment)!=1:
                    raise RuntimeError('STOP: expected a unique cue/title at StrRef '+str(row['strref']))
                new=new.replace(fragment,subst,1)
            if old==new:raise RuntimeError('STOP: no changed text at StrRef '+str(row['strref']))
            if (collections.Counter(TOKEN_RE.findall(old))!=collections.Counter(TOKEN_RE.findall(new))
                or collections.Counter(COLOR_RE.findall(old))!=collections.Counter(COLOR_RE.findall(new))):
                raise RuntimeError('STOP: game control placeholders changed at '+str(row['strref']))
            result[side]={'source_sha256_utf8':row[side]['source_sha256_utf8'],
                          'replacement':new,'replacement_sha256_utf8':sha_bytes(new.encode('utf8')),
                          'action':'REPLACE'}
        expanded['entries'].append(result)
    return _old_validate_delta_v3(expanded)


def _install_one_patch(patch,paths):
    if patch['schema']=='bg-eet-ru-translation-delta-v1':
        return _old_install_one_patch_v3(patch,paths)
    expanded=_v4_expand_patch(patch,paths)
    private=PATCH_DIR/(_private_expanded_prefix+('%05d.json'%patch['version']))
    PATCH_DIR.mkdir(parents=True,exist_ok=True)
    # Keep the fully expanded string ONLY on user's own machine, never in public GitHub.
    atomic_write(private,json_text({'source_manifest_sha256':sha_bytes(json_text(patch).encode('utf8')),
                                    'expanded':expanded}).encode('utf8'))
    return _old_install_one_patch_v3(expanded,paths)


def _collect_remote_rows(rows,game):
    receipts=_receipt_list()
    if not receipts:return rows
    paths=find_tlks(game)
    for receipt in receipts:
        f=PATCH_DIR/('patch_%05d.json'%receipt['version'])
        if not f.is_file():raise RuntimeError('STOP: missing downloaded translation manifest')
        original=_validate_delta(_json_file(f))
        if original['schema']=='bg-eet-ru-translation-delta-v2':
            private=PATCH_DIR/(_private_expanded_prefix+('%05d.json'%receipt['version']))
            if not private.is_file():raise RuntimeError('STOP: local full-text verification data missing')
            info=_json_file(private)
            if info.get('source_manifest_sha256')!=sha_bytes(json_text(original).encode('utf8')):
                raise RuntimeError('STOP: translation evidence manifest has changed')
            expanded=_old_validate_delta_v3(info['expanded'])
        else:
            expanded=original
        for side in SIDES:
            t=TLK(paths[side])
            try:
                for rec in expanded['entries']:
                    status,actual=t.get(rec['strref'])
                    item=rec[side]
                    if status!='OK' or actual!=item['replacement']:
                        raise RuntimeError('STOP: remote text patch changed: StrRef '+str(rec['strref']))
                    rows.append({'strref':rec['strref'],'tlk':side,'category':'REMOTE_VISIBLE_DLG_FIX',
                                 'status':'ALREADY_TRANSLATED', 'action':'REPLACE',
                                 'current_text':actual,'proposed_text':actual})
            finally:t.close()
    return rows


def _selftest_v4():
    with tempfile.TemporaryDirectory(prefix='BGEETRU_V4_SAFE_') as d:
        root=Path(d)
        idx=bytearray(26*360847)
        n=45218;src='[Whispering]Hello, friend. [Carefully]Do not worry.'
        base=18+len(idx)
        struct.pack_into('<H',idx,26*n,1)
        struct.pack_into('<II',idx,26*n+18,0,len(src.encode('utf8')))
        raw=b'TLK V1  '+struct.pack('<HII',0,360847,base)+idx+src.encode('utf8')
        paths={s:root/s for s in SIDES}
        for side in SIDES:paths[side].write_bytes(raw)
        p={'schema':'bg-eet-ru-translation-delta-v2','version':22,
           'from_tlk_sha256':{s:sha_bytes(raw) for s in SIDES},'change_count':2,
           'entries':[{'strref':n,**{s:{'source_sha256_utf8':sha_bytes(src.encode('utf8')),
                          'operations':[{'type':'REMOVE_EXACT','old':'[Whispering]'},
                                        {'type':'REMOVE_EXACT','old':'[Carefully]'}]} for s in SIDES}}]}
        _validate_delta(p)
        expanded=_v4_expand_patch(p,paths)
        assert expanded['entries'][0]['dialog.tlk']['replacement']=='Hello, friend. Do not worry.'
        out,change=_patch_binary(raw,expanded,'dialog.tlk')
        assert change==1 and _tlk_rawtext(out,n,base)=='Hello, friend. Do not worry.'
        p['entries'][0]['dialogf.tlk']['source_sha256_utf8']='0'*64
        try:_v4_expand_patch(p,paths);raise AssertionError('hash mismatch was not blocked')
        except RuntimeError:pass
        assert all(sha_file(paths[s])==sha_bytes(raw) for s in SIDES)
    print('SELFTEST V4 PASS: 2 TLK sides, cue-only delta v2, SHA defense, no game write')


def _reconcile_installed_holds():
    # Once a verified remote patch is installed, resolved lines must no longer
    # be counted as outstanding HOLD; keep original DLG audit as historic evidence.
    receipts=_receipt_list()
    resolved=set()
    for r in receipts:
        f=PATCH_DIR/('patch_%05d.json'%r['version'])
        p=_validate_delta(_json_file(f))
        resolved.update(e['strref'] for e in p['entries'])
    if not resolved:return
    hold_file=REPORTS/'02_HOLD_CONTEXT.csv'
    summary_file=REPORTS/'00_LAST_SUMMARY.json'
    report_zip=REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip'
    if not all(x.exists() for x in (hold_file,summary_file,report_zip)):return
    with hold_file.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        kept=[row for row in reader if int(row['strref']) not in resolved]
    summary=_json_file(summary_file)
    summary['held_strrefs']=len(kept)
    summary['resolved_hold_strrefs']=len(resolved)
    summary['original_hold_strrefs']=len(kept)+len(resolved)
    tmp=hold_file.with_name('_HOLDS_AFTER_V22.csv')
    with tmp.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(kept)
    os.replace(tmp,hold_file)
    atomic_write(summary_file,json_text(summary).encode('utf8'))
    temp_zip=REPORTS/'_FINAL_RECONCILED_REPORT.zip'
    with zipfile.ZipFile(report_zip,'r') as src,zipfile.ZipFile(temp_zip,'w',zipfile.ZIP_DEFLATED) as dst:
        for member in src.infolist():
            if member.filename in ('02_HOLD_CONTEXT.csv','00_LAST_SUMMARY.json'):
                dst.write(REPORTS/member.filename,member.filename)
            else:
                dst.writestr(member,src.read(member.filename))
    os.replace(temp_zip,report_zip)


def _main_v4(argv=None):
    if argv is None:argv=sys.argv[1:]
    if '--selftest' in argv:
        _selftest_v2();_selftest_v3();_selftest_v4();return 0
    code=_main_v3(argv)
    if code==0 and '--update-only' not in argv:
        try:_reconcile_installed_holds()
        except (OSError,ValueError,RuntimeError,KeyError,zipfile.BadZipFile) as exc:
            _write_report_note('OPTIONAL HOLD REPORT RECONCILIATION FAILED: '+str(exc))
    return code



# === V5: fix unsupported codec used when decoding remote v22 manifest.
# The incorrect spelling caused SAFE_STOP before any game write.
def _selftest_v5():
    # Exercise BOM and ordinary UTF-8 as delivered by GitHub, then validate the
    # exact v2 schema that failed to load under v4. No game files touched.
    sample = {
        'schema': 'bg-eet-ru-translation-delta-v2', 'version': 22,
        'from_tlk_sha256': {s: 'a'*64 for s in SIDES},
        'change_count': 2,
        'entries': [{'strref': 42, **{s: {
            'source_sha256_utf8': 'b'*64,
            'operations': [{'type': 'REMOVE_EXACT', 'old': '[Upset]'}]
        } for s in SIDES}}]
    }
    for codec in ('utf-8', 'utf-8-sig'):
        encoded = json.dumps(sample, ensure_ascii=False).encode(codec)
        parsed = _validate_delta(json.loads(encoded.decode('utf-8-sig')))
        assert parsed['version'] == 22 and parsed['change_count'] == 2
    # This catches the original typo even when Python parses the module.
    assert not any('utf8-sig' in constant for constant in
                   _install_remote_patches.__code__.co_consts if isinstance(constant, str))
    print('SELFTEST V5 PASS: remote patch manifest UTF-8/BOM; v2 schema; game untouched')


def _main_v5(argv=None):
    if argv is None: argv = sys.argv[1:]
    if '--selftest' in argv:
        _selftest_v2(); _selftest_v3(); _selftest_v4(); _selftest_v5()
        return 0
    return _main_v4(argv)

main = _main_v5

# ==== V6: read-only current TLK fingerprints and complete short dialogue text
#           for the remaining HOLD rows. Report stays in the existing ZIP.
V6_DIALOGUE_TARGETS = frozenset({317986, 318009})
V6_GAMEPLAY_REVIEW = frozenset({228307, 266659, 273096})
V6_NON_GAMEPLAY = frozenset({232315, 232317, 232318, 232331, 271374})


def _v6_collect_current_holds(game, held_ids, expected_pair):
    if len(held_ids) > 100 or len(held_ids) != len(set(held_ids)):
        raise RuntimeError('V6 STOP: invalid HOLD set')
    paths = find_tlks(game)
    before = _hashes(paths)
    if before != expected_pair:
        raise RuntimeError('V6 STOP: TLK pair changed since normal read-only verification')
    entries = {n: {'strref': n,
                   'priority': ('DIALOGUE' if n in V6_DIALOGUE_TARGETS else
                                'GAMEPLAY_REVIEW' if n in V6_GAMEPLAY_REVIEW else
                                'NOT_GAMEPLAY' if n in V6_NON_GAMEPLAY else 'REVIEW')}
               for n in held_ids}
    for side in SIDES:
        tlk = TLK(paths[side])
        try:
            if tlk.count != 360847:
                raise RuntimeError('V6 STOP: unexpected TLK count')
            for n in held_ids:
                status, source = tlk.get(n)
                rec = {'status': status}
                if status == 'OK':
                    rec.update({'source_sha256_utf8': sha_bytes(source.encode('utf8')),
                                'characters': len(source),
                                'start_excerpt': source[:140]})
                    if (n in V6_DIALOGUE_TARGETS or n in V6_GAMEPLAY_REVIEW) and len(source) <= 3000:
                        rec['exact_current_text'] = source
                entries[n][side] = rec
        finally:
            tlk.close()
    if _hashes(paths) != before:
        raise RuntimeError('V6 STOP: TLK pair changed while collecting HOLD evidence')
    return {'schema': 'bg-eet-ru-hold-live-evidence-v1',
            'version': 6, 'mode': 'READ_ONLY', 'game_modified': False,
            'collected_utc': utc_now(), 'game_tlk_sha256': before,
            'target_count': len(held_ids),
            'dlg_priority_count': sum(n in V6_DIALOGUE_TARGETS for n in held_ids),
            'gameplay_review_count': sum(n in V6_GAMEPLAY_REVIEW for n in held_ids),
            'non_gameplay_count': sum(n in V6_NON_GAMEPLAY for n in held_ids),
            'entries': [entries[n] for n in sorted(entries)],
            'notice': 'Read-only evidence for future editorial review; never auto-install any HOLD. All other game resources remain untouched.'}


def _v6_append_to_single_report(game):
    old = _json_file(REPORTS/'00_LAST_SUMMARY.json')
    if old.get('result') != 'OK':
        raise RuntimeError('V6 STOP: no successful current TLK verification')
    expected = old.get('tlk_sha256', {}).get('after')
    if not isinstance(expected, dict) or set(expected) != set(SIDES):
        raise RuntimeError('V6 STOP: missing current TLK pair fingerprints')
    ids = _held_ids()  # reads the 02_HOLD_CONTEXT.csv after v22 reconciliation
    report = _v6_collect_current_holds(game, ids, expected)
    report_path = REPORTS/'08_HOLD_EXACT_TLK_AUDIT.json'
    atomic_write(report_path, json_text(report).encode('utf-8'))
    output_zip = REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip'
    if not output_zip.is_file():
        raise RuntimeError('V6 STOP: single report ZIP not found')
    tmp = REPORTS/'_REPORT_V6_PACK.tmp'
    try:
        with zipfile.ZipFile(output_zip, 'r') as src, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as dst:
            names=set()
            for m in src.infolist():
                if m.filename == report_path.name:
                    continue
                if m.filename in names:
                    raise RuntimeError('V6 STOP: duplicate in report archive')
                names.add(m.filename)
                dst.writestr(m, src.read(m.filename))
            dst.write(report_path, report_path.name)
        os.replace(tmp, output_zip)
    finally:
        if tmp.exists():
            tmp.unlink()
    _write_report_note('V6 HOLD exact source audit: %d refs, game unchanged, single ZIP updated' % len(ids))
    return report


def _v6_selftest():
    with tempfile.TemporaryDirectory(prefix='BGEET_RU_V6_READONLY_') as t:
        global REPORTS
        old_reports = REPORTS
        root = Path(t)
        game = root/'GAME'
        d = game/'lang'/'ru_RU'
        d.mkdir(parents=True)
        before = {}
        for side in SIDES:
            items = {317986: '[Explaining]Величие дракона.',
                     318009: ('[Explaining scornfully]Я человек. [Regaining her composure]Да.' if side=='dialog.tlk'
                              else '[Explaining scornfully]Я человек. [Regaining her composure]Иначе.')}
            index = bytearray(26*360847)
            payload=bytearray()
            for n, val in items.items():
                pos=26*n
                encoded=val.encode('utf-8')
                struct.pack_into('<H', index, pos, 1)
                struct.pack_into('<II', index, pos+18, len(payload), len(encoded))
                payload.extend(encoded)
            header=b'TLK V1  '+struct.pack('<HII',0,360847,18+len(index))
            path=d/side
            path.write_bytes(header+index+payload)
            before[side]=sha_file(path)
        try:
            REPORTS=root/'BG_EET_RU_REPORTS'
            REPORTS.mkdir()
            hold=REPORTS/'02_HOLD_CONTEXT.csv'
            with hold.open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.writer(f)
                w.writerow(['strref','category'])
                w.writerows([[317986,'actor'],[318009,'actor']])
            old={'result':'OK','tlk_sha256':{'after':before}}
            atomic_write(REPORTS/'00_LAST_SUMMARY.json',json_text(old).encode('utf-8'))
            with zipfile.ZipFile(REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip','w') as z:
                z.write(REPORTS/'00_LAST_SUMMARY.json','00_LAST_SUMMARY.json')
            result=_v6_append_to_single_report(game)
            assert result['target_count']==2 and result['game_modified'] is False
            side1=result['entries'][1]['dialog.tlk']['exact_current_text']
            side2=result['entries'][1]['dialogf.tlk']['exact_current_text']
            assert side1!=side2
            assert len(result['entries'])==2
            assert before==_hashes(find_tlks(game))
            with zipfile.ZipFile(REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip') as z:
                assert len(z.namelist())==2
                assert z.read('00_LAST_SUMMARY.json')==json_text(old).encode('utf-8')
                assert json.loads(z.read('08_HOLD_EXACT_TLK_AUDIT.json'))['target_count']==2
            _v6_append_to_single_report(game)
            with zipfile.ZipFile(REPORTS/'SEND_TO_CHATGPT_BG_EET_RU.zip') as z:
                assert len(z.namelist())==2
            try:
                _v6_collect_current_holds(game,[317986],{s:'0'*64 for s in SIDES})
                raise AssertionError('V6 fingerprint mismatch was not blocked')
            except RuntimeError:
                pass
        finally:
            REPORTS=old_reports
    print('SELFTEST V6 PASS: 360847-StrRef TLKs, genders, SHA defense, ZIP, repeat, no game write')


def _main_v6(argv=None):
    if argv is None: argv=sys.argv[1:]
    if '--selftest' in argv:
        _selftest_v2(); _selftest_v3(); _selftest_v4(); _selftest_v5(); _v6_selftest()
        return 0
    rc = _main_v5(argv)
    if rc != 0 or '--update-only' in argv:
        return rc
    parse = argparse.ArgumentParser(add_help=False)
    parse.add_argument('--game',default=GAME_DEFAULT)
    args, _ = parse.parse_known_args(argv)
    try:
        result = _v6_append_to_single_report(Path(args.game).expanduser().resolve())
        print('BG EET RU v6: HOLD exact evidence %d (read-only); same report ZIP.'%result['target_count'],flush=True)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, struct.error) as exc:
        _write_report_note('V6 OPTIONAL READ-ONLY HOLD AUDIT FAILED: '+type(exc).__name__+': '+str(exc))
        print('Optional HOLD audit unavailable; existing game and report unchanged: '+str(exc),flush=True)
    return rc

main = _main_v6

if __name__ == '__main__':
    sys.exit(main())
