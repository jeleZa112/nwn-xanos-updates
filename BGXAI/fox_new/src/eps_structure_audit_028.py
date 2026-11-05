"""BGXAI 028: offline / read-only EPS 18.4 installation architecture inventory.

Reads user's local EPS baseline produced by BGXAI 027. Emits metadata ONLY,
never includes EPS source text in report. Does not mutate game or mod files.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import os
import re
import sys
from pathlib import Path

APPROVED_ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
MAX_COUNT = 10000
MAX_MANIFEST_BYTES = 4_000_000
SOURCE_DIR = "EPS_ORIGINAL_TEXTS_PRIVATE"


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def audit(snapshot: Path, game_root: Path, *, strict_root: bool = True) -> dict:
    game_root = game_root.resolve()
    if strict_root and os.path.normcase(str(game_root)).lower() != os.path.normcase(str(APPROVED_ROOT.resolve())).lower():
        raise ValueError('Unexpected game root; never process the old EET installation')
    if not (game_root / 'chitin.key').is_file():
        raise ValueError('Expected chitin.key in new Foxx game root')
    snapshots_root = (game_root / 'BGXAI_LOCAL_BUILD').resolve()
    snapshot = snapshot.resolve()
    if not is_within(snapshots_root, snapshot) or snapshot == snapshots_root:
        raise ValueError('Snapshot must be within BGXAI_LOCAL_BUILD')
    manifest = snapshot / 'LOCAL_MANIFEST.json'
    if not manifest.is_file() or manifest.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('Local manifest missing or oversized')
    meta = json.loads(manifest.read_text(encoding='utf-8'))
    if meta.get('schema') != 27 or meta.get('public_upload_allowed') is not False:
        raise ValueError('Not an approved local EPS snapshot manifest')
    files = meta.get('source_files')
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_COUNT:
        raise ValueError('Invalid EPS source inventory size')
    copy_root = snapshot / SOURCE_DIR
    if not copy_root.is_dir() or copy_root.is_symlink():
        raise ValueError('EPS_ORIGINAL_TEXTS_PRIVATE directory missing or redirected')
    by_ext = collections.Counter()
    by_area = collections.Counter()
    total = 0
    names = []
    sampled_baf_paths = []
    for item in files:
        if not isinstance(item, dict):
            raise ValueError('Invalid inventory item')
        raw = item.get('path')
        if not isinstance(raw, str) or not raw or '\\' in raw or '\x00' in raw:
            raise ValueError('Invalid inventory path')
        p = Path(raw)
        if p.is_absolute() or '..' in p.parts or not all(seg and seg != '.' for seg in p.parts):
            raise ValueError('Unsafe inventory path')
        target = copy_root / p
        if target.is_symlink() or not target.is_file() or not is_within(copy_root.resolve(), target.resolve()):
            raise ValueError('Missing/redirected local EPS source copy')
        size = item.get('bytes')
        digest = item.get('sha256')
        if not isinstance(size, int) or size != target.stat().st_size or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('Invalid source integrity metadata')
        if hash_file(target) != digest:
            raise ValueError('Local EPS source checksum mismatch: '+raw)
        ext = p.suffix.lower() or '[no extension]'
        by_ext[ext] += 1
        by_area[p.parts[0] if len(p.parts)>1 else '[root]'] += 1
        total += size
        names.append(p.as_posix())
        if ext == '.baf':
            sampled_baf_paths.append(p.as_posix())
    tp2 = [name for name in names if name.lower().endswith('.tp2')]
    lua = [name for name in names if name.lower().endswith('.lua')]
    scripts = [name for name in names if name.lower().endswith(('.baf','.ssl'))]
    report = {
        'schema': 28, 'mode': 'METADATA_ONLY', 'game_modified': False,
        'eps_modified': False, 'uploaded': False, 'game_root': str(game_root),
        'snapshot_id': snapshot.name,
        'file_count': len(files), 'source_bytes': total,
        'extension_counts': dict(sorted(by_ext.items())),
        'top_level_counts': dict(sorted(by_area.items())),
        'tp2_paths': tp2, 'lua_paths': lua,
        'script_count': len(scripts),
        'script_basename_samples': [Path(s).name for s in sorted(scripts)[:20]],
        'installed_eps_components': meta.get('weidu_eps_components'),
        'bddefai_override_present': (meta.get('binary_bcs_info') or {}).get('present_in_override',False),
        'engine_integration_verified': False,
        'suitable_for_installation': False,
        'message_ru':'EPS 18.4: только сверка локальной структуры. BGXAI не установлен в игру.',
    }
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Read-only local EPS structure audit; no EPS text in output')
    parser.add_argument('--game-root',default=str(APPROVED_ROOT))
    parser.add_argument('--snapshot',default=None)
    parser.add_argument('--report',default=None)
    opts = parser.parse_args(argv)
    root = Path(opts.game_root)
    if opts.snapshot:
        snap=Path(opts.snapshot)
    else:
        candidates = sorted((root/'BGXAI_LOCAL_BUILD').glob('EPS_BASELINE_*/LOCAL_MANIFEST.json'))
        if not candidates:
            raise ValueError('No EPS_BASELINE snapshots found: run 027 first')
        snap=candidates[-1].parent
    result=audit(snap,root)
    output=Path(opts.report) if opts.report else root/'BGXAI_LOCAL_BUILD'/'BGXAI_028_EPS_STRUCTURE_REPORT.json'
    if output.resolve().parent != (root/'BGXAI_LOCAL_BUILD').resolve() or output.name != 'BGXAI_028_EPS_STRUCTURE_REPORT.json':
        raise ValueError('Report must stay at BGXAI_LOCAL_BUILD/BGXAI_028_EPS_STRUCTURE_REPORT.json')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SUCCESS BGXAI 028: '+str(result['file_count'])+' EPS source files indexed; game unchanged')
    print('REPORT: '+str(output))
    print('No EPS content was uploaded or printed.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
        print('ERROR BGXAI 028:',exc)
        sys.exit(1)