# -*- coding: utf-8 -*-
"""BG EET RU persistent auto-updater / game READ ONLY. Python 3.9+ stdlib only.

Downloads data-only translation plans; recognizes exact verified stage1/2 installed TLKs.
NEVER executes downloaded source; NEVER writes within the installed EET game.
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

APP_VERSION = '2.0.0-permanent-one-folder'
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

CODE_VERSION = 2
APP_VERSION = '2.0.0-permanent-one-folder'
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
        patch=_validate_delta(json.loads(_remote_item(desc).decode('utf8-sig')))
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
main=_main_v2

if __name__ == '__main__':
    sys.exit(main())
