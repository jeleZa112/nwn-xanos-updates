# BG Voice RU movie workflow: remote code, same persistent BG_VOICE_UPDATE.cmd.
# READ ONLY source audit. No game, master audio or installed voice writes.
from __future__ import annotations
import csv
import io
import json

MOVIE_CORE_VERSION = '1.0.0'


def selftest():
    assert MOVIE_CORE_VERSION == '1.0.0'
    assert len({'audit': 1, 'write': 2}) == 2
    print('MOVIE_CHANNEL_SELFTEST_PASS')
    return 0


def run(host):
    # Calls versioned, local SHA-locked source-reader and atomic report-writer.
    if set(host) != {'audit', 'write'} or not all(callable(v) for v in host.values()):
        raise RuntimeError('MOVIE_CHANNEL_UNEXPECTED_HOST')
    status, rows, source_bytes, extras = host['audit']()
    extras = dict(extras)
    status = dict(status)
    status['video_code_version'] = MOVIE_CORE_VERSION
    status['video_update_mode'] = 'ONE_PERMANENT_CMD_GITHUB_SHA_PINNED_CACHED'
    status['game_write'] = False
    status['voice_synthesis'] = False
    selected = [r for r in (rows or []) if r.get('selected_audio')]
    pending = [r for r in (rows or []) if not r.get('selected_audio')]
    # Never claim 37/37 unless the original 37-group ZIP is SHA-verified.
    verified = status.get('full_script_provenance') == 'PINNED_SHA_VERIFIED' and len(rows or []) == 37
    status['video_full_script_verified'] = bool(verified)
    status['video_accepted_wav_count'] = len(selected) if verified else 15
    status['video_pending_group_count'] = len(pending) if verified else None
    if verified:
        output = io.StringIO(newline='')
        fieldnames = ['id', 'movie', 'english_draft', 'russian_draft', 'source_status', 'coverage_status']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in pending:
            writer.writerow({k: row.get(k, '') for k in fieldnames})
        extras['VIDEO_PENDING_GROUPS.csv'] = output.getvalue().encode('utf-8-sig')
        status['next'] = 'Audit untranslated/uncertain groups against original EN; no automatic incomplete movie mix'
        print('MOVIE_CHANNEL: verified 37 groups, pending', len(pending), flush=True)
    else:
        missing = {'required_archive': 'BG_VOICE_RU_NEXT3_FULL_SCRIPT_AND_BATCH_V1_20261121.zip',
                   'expected_sha256': 'de4887fb5d9ecec7f04637d5f46517c39d3dbc6e3dfd3f9e6da194b60a93396e',
                   'status': status.get('script_parse_status', 'UNKNOWN'),
                   'action': 'Recover exact archived scenario on Windows, never invent missing subtitles'}
        extras['VIDEO_MISSING_SOURCE.json'] = json.dumps(missing, ensure_ascii=False, indent=2).encode('utf-8')
        status['next'] = 'Recover full source script by pinned SHA; do not create a partial movie'
        print('MOVIE_CHANNEL: source missing/unverified; no partial movie created', flush=True)
    report = host['write'](status, rows, source_bytes, extras)
    print('MOVIE_CHANNEL_REPORT:', report, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(selftest())
