"""BGXAI 030: read-only local EPS 18.4 runtime preflight, no game operations.

Goal: prevent blind deployment of the experimental BGX29 shadow script.
Checks that 027 EPS snapshot, 028 metadata-only report and CURRENT Foxx install
are mutually consistent, especially WeiDU, BDDEFAI override, and changed EPS
texts. Only outputs a metadata JSON report; never copies EPS content, installs
mods, recompiles BCS, or uploads files.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
from pathlib import Path

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
EPS_NAME = 'enhanced-powergaming-scripts'
FILE_028 = 'BGXAI_028_EPS_STRUCTURE_REPORT.json'
FILE_030 = 'BGXAI_030_COMPATIBILITY_REPORT.json'
MAX_MANIFEST = 4_000_000
MAX_REPORT = 1_000_000


def hashfile(path):
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def confined(directory, name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        return None
    parts = name.split('/')
    if any(part in ('', '.', '..') or ':' in part for part in parts):
        return None
    candidate = directory.joinpath(*parts)
    if candidate.is_symlink():
        return None
    try:
        if not candidate.resolve(strict=True).is_relative_to(directory.resolve(strict=True)):
            return None
    except (OSError, ValueError):
        return None
    return candidate


def jsonfile(path, limit):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > limit:
        raise ValueError('Missing, redirected or oversized JSON: ' + path.name)
    return json.loads(path.read_text(encoding='utf-8'))


def validate(root, *, enforce_root=True):
    """Never writes anything; result is a set of triage signals, not install approval."""
    root = Path(root).resolve()
    if enforce_root and os.path.normcase(str(root)).casefold() != os.path.normcase(str(GAME.resolve())).casefold():
        raise ValueError('Wrong game root; old install forbidden')
    if not (root / 'chitin.key').is_file():
        raise ValueError('New Foxx chitin.key not found')
    local = root / 'BGXAI_LOCAL_BUILD'
    report28 = jsonfile(local / FILE_028, MAX_REPORT)
    if report28.get('schema') != 28 or report28.get('mode') != 'METADATA_ONLY' or report28.get('game_modified') is not False or report28.get('uploaded') is not False:
        raise ValueError('028 metadata invalid or not read-only')
    sid = report28.get('snapshot_id')
    if not isinstance(sid, str) or not re.fullmatch(r'EPS_BASELINE_[A-Za-z0-9_-]{1,40}', sid):
        raise ValueError('Snapshot name invalid')
    snap = local / sid
    if snap.is_symlink() or not snap.is_dir():
        raise ValueError('Local EPS baseline missing or redirected')
    meta = jsonfile(snap / 'LOCAL_MANIFEST.json', MAX_MANIFEST)
    if meta.get('schema') != 27 or meta.get('public_upload_allowed') is not False or meta.get('game_modified') is not False:
        raise ValueError('027 baseline provenance invalid')
    inv = meta.get('source_files')
    if not isinstance(inv, list) or not 1 <= len(inv) <= 10000:
        raise ValueError('EPS inventory missing')
    if report28.get('file_count') != len(inv) or report28.get('source_bytes') != sum(x.get('bytes', 0) for x in inv if isinstance(x, dict)):
        raise ValueError('027 and 028 metadata disagree')
    roots = [root / EPS_NAME, snap / 'EPS_ORIGINAL_TEXTS_PRIVATE']
    if any(p.is_symlink() or not p.is_dir() for p in roots):
        raise ValueError('Installed EPS or private snapshot directory missing or redirected')
    checked = 0
    changed = []
    for v in inv:
        if not isinstance(v, dict) or not isinstance(v.get('bytes'), int) or not isinstance(v.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', v['sha256']):
            raise ValueError('Bad source manifest entry')
        path = v.get('path')
        for i, top in enumerate(roots):
            p = confined(top, path)
            if p is None or not p.is_file() or p.stat().st_size != v['bytes'] or hashfile(p) != v['sha256']:
                changed.append({'path': path, 'which': 'INSTALLED_EPS' if i == 0 else 'LOCAL_SNAPSHOT'})
        checked += 1
    changed.sort(key=lambda x: (str(x['path']), x['which']))
    weidu = root / 'WeiDU.log'
    if not weidu.is_file():
        raise ValueError('WeiDU.log missing; cannot prove EPS installation')
    epslines = [x for x in weidu.read_text(encoding='utf-8-sig', errors='replace').splitlines() if 'ENHANCED-POWERGAMING-SCRIPTS' in x.upper() and not x.lstrip().startswith('//')]
    # Do not interpret component names or installed version from translated descriptions.
    baseline_components = meta.get('weidu_eps_components')
    weidu_ok = bool(epslines) and isinstance(baseline_components, int) and len(epslines) == baseline_components
    orig = meta.get('binary_bcs_info') or {}
    bcs = root / 'override' / 'BDDEFAI.BCS'
    if bcs.exists() and not bcs.is_symlink() and orig.get('present_in_override') is True and isinstance(orig.get('sha256'), str):
        bcs_state = 'SAME_AS_SNAPSHOT' if hashfile(bcs) == orig['sha256'] else 'CHANGED_SINCE_SNAPSHOT'
    elif not bcs.exists() and orig.get('present_in_override') is False:
        bcs_state = 'NOT_IN_OVERRIDE_UNVERIFIED_RESOURCE'
    else:
        bcs_state = 'UNVERIFIED'
    errors = []
    if changed: errors.append('EPS original or private baseline differs from recorded hashes')
    if not weidu_ok: errors.append('WeiDU EPS count absent/changed')
    if bcs_state != 'SAME_AS_SNAPSHOT': errors.append('BDDEFAI override identity not proven')
    return {
        'schema': 30, 'mode': 'OFFLINE_READ_ONLY_PREFLIGHT',
        'status': 'READY_FOR_ISOLATED_COMPILATION_REVIEW' if not errors else 'BLOCKED_REVIEW',
        'snapshot_id': sid, 'source_files_checked': checked,
        'changed_file_count': len(changed), 'changed_file_samples': changed[:20],
        'eps_weidu_components': len(epslines), 'baseline_weidu_components': baseline_components,
        'bddefai_override_state': bcs_state,
        'blockers': errors, 'weiDU_compilation_verified': False,
        'bgxai_installed': False, 'live_install_allowed': False,
        'eps_modified': False, 'game_modified': False, 'uploaded': False,
        'note_ru': 'Только сравнение метаданных и SHA256. Даже READY допускает лишь дальнейшую проверку компиляции В КОПИИ игры.'
    }


def main():
    try:
        out = validate(GAME)
        dest = GAME / 'BGXAI_LOCAL_BUILD' / FILE_030
        if dest.is_symlink():
            raise ValueError('Report destination redirected')
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('BGXAI 030:', out['status'], '| verified files:', out['source_files_checked'])
        print('EPS WeiDU components:', out['eps_weidu_components'])
        print('BDDEFAI:', out['bddefai_override_state'])
        for err in out['blockers']: print('BLOCKER:', err)
        print('Report:', dest)
        print('Game and EPS unchanged; no WeiDU installation performed.')
        return 0 if out['status'].startswith('READY') else 2
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('BGXAI 030 PREFLIGHT ERROR:', str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())