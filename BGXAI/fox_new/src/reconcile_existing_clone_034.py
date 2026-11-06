"""BGXAI 034 - safely reconcile movie-byte mismatches in an isolated EET clone.

Never edits an installed game/EPS resource; never deletes the test clone. 034
quarantines only mismatched *.WBM under clone/movies, never executable scripts.
Then resumes 033, whose own invariant checks and isolated WeiDU rollback still apply.

Run from the same BGXAI_DEV/src as 032,033. No network, no third-party sources.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import weidu_isolated_test_032 as base
import recover_isolated_clone_033 as old

LIVE = Path(r'C:\Games\BG_EET_FOXX_NEW')
REPORT = 'BGXAI_034_RECONCILIATION_REPORT.json'
MAX_REPAIR_FILES = 10
MAX_REPAIR_BYTES = 3 * 1024**3


def assert_no_concurrent_jobs(*, probe=subprocess.run, pid=None):
    """Fail closed if another 032, 033 or 034 Python instance is still running."""
    if os.name != 'nt':
        return
    current = os.getpid() if pid is None else pid
    command = (
        '$ErrorActionPreference="Stop"; '
        'Get-CimInstance Win32_Process -Filter '
        '\"Name=\'python.exe\' OR Name=\'pythonw.exe\'\" | '
        'Where-Object { $_.CommandLine -match '
        "'weidu_isolated_test_032[.]py|recover_isolated_clone_033[.]py|reconcile_existing_clone_034[.]py' "
        f'-and $_.ProcessId -ne {int(current)} }} | '
        'Select-Object -ExpandProperty ProcessId'
    )
    try:
        p = probe(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                  capture_output=True, text=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ValueError('Unable to verify no concurrent 032/033/034 process') from e
    if p.returncode != 0:
        raise ValueError('Windows process safety check unavailable')
    if p.stdout.strip():
        raise ValueError('Another BGXAI 032/033/034 process is active: ' + p.stdout.strip()[:100])


def collect_mismatches(root, clone, state, *, digest=base.digest, limit=MAX_REPAIR_FILES,
                       log=print):
    """Checks SHA256 of all extant clone files BEFORE allowing any repair."""
    mismatches = []
    checked = 0
    for rel, (clonefile, size) in state['existing'].items():
        if rel not in state['sources']:
            raise ValueError('Unexpected file in test copy: ' + rel)
        livefile = root / state['sources'][rel][0]
        if base.junction_or_link(livefile) or base.junction_or_link(clonefile):
            raise ValueError('Link/reparse point in clone check: '+rel)
        old.hardlink_check(livefile, clonefile)
        h_live, h_clone = digest(livefile), digest(clonefile)
        checked += 1
        if h_live != h_clone:
            mismatches.append({'path': rel, 'expected_sha256': h_live,
                               'clone_sha256': h_clone, 'bytes': size})
            if len(mismatches) > limit:
                raise ValueError(f'More than {limit} divergent files: stop for manual review')
        if checked % 1000 == 0:
            log('BGXAI 034: checked existing files:', checked)
    return mismatches


def safe_movie_path(relative):
    """Keep repair extremely narrow; no executables, scripts, EPS or TLK."""
    p = Path(relative)
    return len(p.parts) == 2 and p.parts[0].lower() == 'movies' and \
        p.suffix.lower() == '.wbm' and re.fullmatch(r'[A-Za-z0-9_.-]+', p.name) is not None


def repair_movies(root, clone, local, state, mismatches, *, tag=None,
                  free_bytes=None):
    """Move corrupt TEST copy movies to unique quarantine, copy clean source.

    If interrupted, quarantine is not deleted and re-run refuses an existing
    nonzero-size mismatch outside movies. No LIVE file is ever opened for write.
    """
    if not mismatches:
        return {'quarantine': None, 'repaired': []}
    if len(mismatches) > MAX_REPAIR_FILES or any(not safe_movie_path(x['path']) for x in mismatches):
        raise ValueError('A non-movie file differs; no automatic repair is allowed')
    if sum(x['bytes'] for x in mismatches) > MAX_REPAIR_BYTES:
        raise ValueError('Excessive changed movie bytes; no automatic repair')
    missing_bytes = sum(n for _, n in (state['sources'][rel] for rel in state['missing']))
    required = missing_bytes + max(base.MIN_EXTRA_BYTES, int(missing_bytes*.07))
    if free_bytes is None:
        free_bytes = shutil.disk_usage(clone).free
    if free_bytes < required:
        raise ValueError('Insufficient space for rest of clone: '+str(round(required/1024**3,2))+
                         ' GiB required, '+str(round(free_bytes/1024**3,2))+' GiB free')
    if base.junction_or_link(local) or not local.is_dir():
        raise ValueError('Unsafe BGXAI_LOCAL_BUILD location')
    now = tag or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if not re.fullmatch(r'[0-9A-Za-z_-]{6,40}',now):
        raise ValueError('Invalid quarantine tag')
    quarantine = local / ('BGX34_QUARANTINE_' + now)
    if quarantine.exists() or base.junction_or_link(quarantine):
        raise ValueError('Quarantine directory exists; preserve it and stop')
    # Re-check EVERY candidate before moving a single file. Not only sizes.
    for entry in mismatches:
        rel = entry['path']
        src, dest = root / rel, clone / rel
        if base.junction_or_link(src) or base.junction_or_link(dest) or \
           base.junction_or_link(dest.parent) or base.junction_or_link(src.parent):
            raise ValueError('Redirected source or clone movie')
        old.hardlink_check(src,dest)
        if not src.is_file() or not dest.is_file() or \
           base.digest(src) != entry['expected_sha256'] or \
           base.digest(dest) != entry['clone_sha256']:
            raise ValueError('Movie changed after first verification: ' + rel)
    quarantine.mkdir(exist_ok=False)
    repaired = []
    for entry in mismatches:
        rel = entry['path']
        src, dest = root / rel, clone / rel
        archive = quarantine / rel
        archive.parent.mkdir(parents=True, exist_ok=True)
        if archive.exists():
            raise ValueError('Quarantine collision, refusing overwrite')
        # Move only the mismatched TEST COPY file, not the source.
        dest.rename(archive)
        try:
            old.copy_one_exclusive(src, dest, src.stat().st_size)
            if base.digest(src) != entry['expected_sha256'] or \
               base.digest(dest) != entry['expected_sha256']:
                raise ValueError('Repaired file SHA mismatch: '+rel)
        except Exception:
            # Do not leave a half-written dest. Preserve bytes in quarantine.
            if dest.exists():
                bad = quarantine / (Path(rel).name + '.failed_copy')
                if not bad.exists():
                    dest.rename(bad)
            if not dest.exists() and archive.is_file():
                archive.rename(dest)
            raise
        repaired.append(rel)
    return {'quarantine': str(quarantine), 'repaired': repaired}


def reconcile(root=LIVE, *, inspect_only=False, enforce_root=True, resume_fn=old.resume,
              proc_check=assert_no_concurrent_jobs, log=print):
    root = Path(root).resolve()
    info = old.inspect(root, enforce_root=enforce_root)
    if info['status'] not in ('INCOMPLETE_CLONE_CAN_RESUME_AFTER_PROCESS_CHECK',
                              'COMPLETE_CLONE_CAN_VERIFY_BEFORE_TEST'):
        raise ValueError('Test clone is not an eligible unmodified partial copy: '+info['status'])
    if info['unexpected_files'] or info['size_mismatches']:
        raise ValueError('Unexpected files or size mismatches: no automatic repair')
    state = info['details']
    clone = old.sibling(root)
    if not inspect_only:
        proc_check()
    before = base.capture_critical(root)
    mismatches = collect_mismatches(root,clone,state, log=log)
    result = {'schema':34, 'mode':'READ_ONLY' if inspect_only else 'MOVIE_REPAIR_AND_RESUME',
              'existing_files_checked':len(state['existing']),
              'missing_files':len(state['missing']), 'mismatches':mismatches,
              'live_critical_before':before, 'original_game_modified':False}
    if not mismatches:
        result['status'] = 'NO_DIVERGENCE'
    elif any(not safe_movie_path(m['path']) for m in mismatches):
        result['status'] = 'BLOCKED_NON_MOVIE_MISMATCH'
    else:
        result['status'] = 'MOVIE_MISMATCHES_ONLY'
    if inspect_only or result['status']=='BLOCKED_NON_MOVIE_MISMATCH':
        return result
    # Explicit consent of --repair-and-resume is required. Never repair a
    # general game file; only test clone movies with verified SHA differences.
    result['repair'] = repair_movies(root, clone, root/'BGXAI_LOCAL_BUILD', state, mismatches)
    if base.capture_critical(root) != before:
        raise ValueError('Live critical files changed during test reconciliation')
    # Reuse all 033 safety gates, including complete-copy SHA256 validation,
    # clone-only WeiDU installation and uninstall, no overwrite, and reports.
    stage = resume_fn(root, enforce_root=enforce_root)
    result['weiDU_test_status'] = stage['status']
    result['status'] = ('PASS_ISOLATED_INSTALL_AND_ROLLBACK' if
                        stage['status']=='PASS_ISOLATED_INSTALL_AND_ROLLBACK' else
                        'REVIEW_ISOLATED_WEIDU')
    result['original_game_modified'] = base.capture_critical(root) != before
    if result['original_game_modified']:
        result['status'] = 'BLOCKED_LIVE_CHANGED'
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description='Diagnose/resume only the independent BGX32 copy')
    parser.add_argument('--inspect',action='store_true',help='SHA256 scan of all existing clone files, READ ONLY')
    parser.add_argument('--repair-and-resume',action='store_true',
                        help='Quarantine mismatching clone movie files; resume 033 and test WeiDU in clone')
    opt=parser.parse_args(argv)
    if opt.inspect and opt.repair_and_resume:
        print('BGXAI 034 ERROR: choose only one mode');return 1
    mode=bool(opt.repair_and_resume)
    try:
        result=reconcile(inspect_only=not mode)
        print('BGXAI 034:',result['status'])
        print('Checked existing:',result['existing_files_checked'],
              '| still missing:',result['missing_files'])
        for a in result['mismatches']:
            print('DIVERGENT:',a['path'],'bytes:',a['bytes'])
        if 'repair' in result:
            print('Repaired MOVIES in TEST COPY only:',len(result['repair']['repaired']))
            print('Quarantine:',result['repair']['quarantine'])
        if 'weiDU_test_status' in result:
            print('WeiDU clone-only result:',result['weiDU_test_status'])
        if mode:
            out=LIVE/'BGXAI_LOCAL_BUILD'/REPORT
            out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print('REPORT:',out)
        return 0 if result['status'] in ('NO_DIVERGENCE','MOVIE_MISMATCHES_ONLY','PASS_ISOLATED_INSTALL_AND_ROLLBACK') else 2
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError,
            subprocess.TimeoutExpired) as e:
        print('BGXAI 034 BLOCKED:',str(e))
        print('LIVE EET unchanged by BGXAI; existing clone kept for diagnosis.')
        return 1

if __name__=='__main__':sys.exit(main())