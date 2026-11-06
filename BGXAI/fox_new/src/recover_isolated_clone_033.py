"""BGXAI 0.3.3: inspect or cautiously resume the EXISTING BGX32 test clone.

No deletion, renaming, links or access to installed EPS source content in reports.
--inspect is read-only. --resume-isolated copies ONLY missing files into the
sibling TEST clone and, after whole-clone SHA256 verification, runs WeiDU there.
Original Foxx and active EPS remain unchanged. Requires preexisting clone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import weidu_isolated_test_032 as old

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
REPORT_NAME = 'BGXAI_033_RECOVERY_REPORT.json'
REPORT_032 = old.OUT_NAME


def running_original_032(*, check=None):
    """Fail-closed on Windows when WMI query can't prove old copier is stopped.
    No external process is stopped; no unknown Python process is touched.
    """
    if os.name != 'nt':
        return False
    command = ('$ErrorActionPreference="Stop"; '
               'Get-CimInstance -ClassName Win32_Process '
               '-Filter "Name=\'python.exe\' OR Name=\'pythonw.exe\'" '
               '| Where-Object { $_.CommandLine -like "*weidu_isolated_test_032.py*" } '
               '| Select-Object -ExpandProperty ProcessId')
    r = check or subprocess.run
    try:
        v = r(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
              capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ValueError('Cannot check for active 032 Python process; do not resume yet') from e
    if v.returncode != 0:
        raise ValueError('Windows process check unavailable; do not resume a possibly active clone')
    return bool(v.stdout.strip())


def sibling(root):
    root = Path(root).resolve()
    clone = root.with_name(root.name + old.CLONE_SUFFIX)
    if clone.parent != root.parent or old.inside(root, clone) or old.inside(clone, root) or \
       not clone.is_dir() or old.junction_or_link(clone):
        raise ValueError('Independent existing BGX32 test clone absent or redirected')
    return clone


def inventory_clone(root, clone):
    """Compare paths/sizes WITHOUT writing or relying on file timestamps."""
    sources, total = old.collect(root)
    indexed = {rel.as_posix(): (rel, size) for rel, size in sources}
    existing = {}
    for folder, dirs, files in os.walk(clone, topdown=True, followlinks=False):
        here = Path(folder)
        if old.junction_or_link(here):
            raise ValueError('Clone contains redirected directory')
        for name in dirs:
            if old.junction_or_link(here / name):
                raise ValueError('Clone contains linked/junction directory: ' + name)
        for name in files:
            p = here / name
            if old.junction_or_link(p) or not p.is_file():
                raise ValueError('Clone contains linked/non-regular file: ' + name)
            relative = p.relative_to(clone).as_posix()
            existing[relative] = (p, p.stat().st_size)
            if len(existing) > old.MAX_FILES:
                raise ValueError('Clone file count exceeds safe limit')
    extra = [name for name in existing if name not in indexed]
    mismatched = [name for name in existing if name in indexed and
                  existing[name][1] != indexed[name][1]]
    missing = [name for name in indexed if name not in existing]
    return {
        'sources': indexed, 'existing': existing, 'extra': sorted(extra),
        'mismatched': sorted(mismatched), 'missing': sorted(missing),
        'expected_count': len(indexed), 'existing_count': len(existing),
        'expected_bytes': total,
    }


def hardlink_check(source, clonefile):
    left, right = source.stat(), clonefile.stat()
    # File ID is valid on NTFS; same volume + same nonzero file ID means hardlink.
    if left.st_dev == right.st_dev and left.st_ino and right.st_ino and left.st_ino == right.st_ino:
        raise ValueError('Clone file is HARDLINKED to live EET; refuse: ' + source.name)


def copy_one_exclusive(source, dest, expected_size):
    """Create missing file without ever overwriting anything in the clone."""
    if old.junction_or_link(source) or not source.is_file() or source.stat().st_size != expected_size:
        raise ValueError('Original source changed during recovery: ' + str(source.name))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink() or old.junction_or_link(dest.parent):
        raise ValueError('A clone file appeared while copying; refuse: ' + str(dest))
    with source.open('rb') as inp, dest.open('xb') as out:
        shutil.copyfileobj(inp, out, length=2*1024*1024)
    shutil.copystat(source, dest, follow_symlinks=False)
    if dest.stat().st_size != expected_size or old.digest(source) != old.digest(dest):
        raise ValueError('Incomplete/changed copied clone file: ' + str(dest.name))
    hardlink_check(source, dest)


def inspect(root, *, enforce_root=True, preflight=None):
    root = old.verify_live(root, enforce_root=enforce_root, preflight=preflight)
    clone = sibling(root)
    state = inventory_clone(root, clone)
    recorded = root / 'BGXAI_LOCAL_BUILD' / REPORT_032
    old_result = None
    if recorded.is_file() and not old.junction_or_link(recorded):
        try:
            info = json.loads(recorded.read_text(encoding='utf-8'))
            if info.get('schema') == 32 and info.get('clone_root') == str(clone):
                old_result = info.get('status')
        except (OSError, json.JSONDecodeError):
            old_result = 'INVALID_REPORT'
    if state['extra'] or state['mismatched']:
        status = 'REVIEW_CLONE_HAS_CHANGES'
    elif old_result in ('PASS_ISOLATED_INSTALL_AND_ROLLBACK', 'REVIEW_ISOLATED_WEIDU'):
        status = 'REVIEW_PREVIOUS_WEIDU_TEST'
    elif state['missing']:
        status = 'INCOMPLETE_CLONE_CAN_RESUME_AFTER_PROCESS_CHECK'
    else:
        status = 'COMPLETE_CLONE_CAN_VERIFY_BEFORE_TEST'
    return {'status': status,'clone': str(clone),
            'expected_files': state['expected_count'],
            'present_files': state['existing_count'],
            'missing_files': len(state['missing']),
            'unexpected_files': len(state['extra']),
            'size_mismatches': len(state['mismatched']),
            'previous_032_report': old_result,
            'source_only': False, 'game_modified': False, 'weidu_executed': False,
            'details': state}


def resume(root, *, enforce_root=True, preflight=None, process_probe=running_original_032,
           runner=subprocess.run):
    """Explicit opt-in: fill missing clone files, verify EVERY file, WeiDU ONLY in clone."""
    info = inspect(root, enforce_root=enforce_root, preflight=preflight)
    root = Path(root).resolve()
    clone = sibling(root)
    state = info.pop('details')
    if info['status'] not in ('INCOMPLETE_CLONE_CAN_RESUME_AFTER_PROCESS_CHECK',
                              'COMPLETE_CLONE_CAN_VERIFY_BEFORE_TEST'):
        raise ValueError('Clone has changes/previous WeiDU run; preserved for inspection: ' + info['status'])
    if process_probe():
        raise ValueError('Original BGXAI 032 process STILL ACTIVE. Do not run two copies concurrently.')
    # Earlier 032 space check may no longer reflect current free space.
    # Preflight missing bytes + headroom BEFORE creating any new clone file.
    missing_bytes = sum(state['sources'][rel][1] for rel in state['missing'])
    available = shutil.disk_usage(clone).free
    required = missing_bytes + max(old.MIN_EXTRA_BYTES, int(missing_bytes * 0.07))
    if available < required:
        raise ValueError('Insufficient disk space to resume TEST clone: need ' +
                         str(round(required / 1024**3, 2)) + ' GiB; free ' +
                         str(round(available / 1024**3, 2)) + ' GiB')
    before = old.capture_critical(root)
    weidu = old.choose_weidu(root)
    # Detect all hardlinks and checksum corruption in preexisting clone before writing.
    print('BGXAI 033: verifying existing test clone files:',len(state['existing']), flush=True)
    for i,(rel, (dst, size)) in enumerate(state['existing'].items(),1):
        src = root / state['sources'][rel][0]
        hardlink_check(src,dst)
        if old.digest(src) != old.digest(dst):
            raise ValueError('Existing clone differs from live game; refusing to overwrite: '+rel)
        if i % 500 == 0: print('BGXAI 033: verified',i,'existing files',flush=True)
    print('BGXAI 033: remaining files to copy:',len(state['missing']), flush=True)
    for i,rel in enumerate(state['missing'],1):
        path,size = state['sources'][rel]
        copy_one_exclusive(root / path,clone / path,size)
        if i % 100 == 0:print('BGXAI 033: copied missing',i,'/',len(state['missing']),flush=True)
    updated = inventory_clone(root, clone)
    if updated['missing'] or updated['extra'] or updated['mismatched']:
        raise ValueError('Independent clone remains incomplete; no WeiDU run')
    if old.capture_critical(root) != before:
        raise ValueError('Live EET changed externally during validation; no WeiDU run')
    # Verify entire clone AFTER all copies; no trusting path/size alone.
    for i,(rel,(dst,_size)) in enumerate(updated['existing'].items(),1):
        src = root / updated['sources'][rel][0]
        hardlink_check(src,dst)
        if old.digest(src) != old.digest(dst):
            raise ValueError('Clone SHA256 differs before WeiDU: '+rel)
        if i % 500 == 0: print('BGXAI 033: final checked',i,'clone files',flush=True)
    if old.capture_critical(root) != before:
        raise ValueError('Live EET critical files changed before WeiDU; no test')
    print('BGXAI 033: cloned resources fully verified; running WeiDU ONLY in TEST COPY',flush=True)
    report={'schema':33,'status':'PREPARED', 'clone_root':str(clone),
            'verified_files':len(updated['existing']),
            'copied_missing_files':len(state['missing']),
            'original_game_modified':False,'weiDU_test_only':True,
            'live_critical_before':before}
    try:
        if old.capture_critical(clone) != before:
            raise ValueError('Clone differs from LIVE critical resources before WeiDU')
        # setup-BGX31 executable copied FROM already verified local WeiDU into clone.
        exe = old.prepare_weidu(clone,old.verify_stage(root),clone / weidu.name)
        clone_before = old.capture_critical(clone)
        install_exit, install_output = old.invoke_weidu(exe,clone,runner=runner)
        report['install_exit_code']=install_exit
        report['install_output_tail']=install_output[-14000:]
        bcs=clone/'override/BGX31.BCS'
        bs=clone/'scripts/BGX31.BS'
        report['generated_resources']={'BGX31.BCS':bcs.is_file() and bcs.stat().st_size>0,
                                       'BGX31.BS':bs.is_file() and bs.stat().st_size>0}
        log=clone/'WeiDU.log'
        report['weiDU_component_recorded_on_clone']=log.is_file() and ('BGX31' in log.read_text(encoding='utf-8-sig',errors='replace').upper())
        report['clone_bcs_matches_original_after_install']=old.digest(clone/'override/BDDEFAI.BCS') == before['override/BDDEFAI.BCS']
        if install_exit == 0:
            uninstall_exit,uninstall_output=old.invoke_weidu(exe,clone,uninstall=True,runner=runner)
            report['uninstall_exit_code']=uninstall_exit
            report['uninstall_output_tail']=uninstall_output[-14000:]
            report['resources_absent_after_rollback']=not bcs.exists() and not bs.exists()
            after_log = clone / 'WeiDU.log'
            report['clone_weidu_component_removed'] = after_log.is_file() and \
                ('BGX31' not in after_log.read_text(encoding='utf-8-sig',errors='replace').upper())
        report['clone_bcs_matches_original_after_test']=old.digest(clone/'override/BDDEFAI.BCS') == before['override/BDDEFAI.BCS']
        clone_after=old.capture_critical(clone)
        report['clone_dialog_files_unchanged_after_rollback']=all(
            clone_before[k] == clone_after[k] for k in ('lang/ru_ru/dialog.tlk','lang/ru_ru/dialogf.tlk'))
        report['status']='PASS_ISOLATED_INSTALL_AND_ROLLBACK' if (
            install_exit==0 and report.get('uninstall_exit_code')==0 and
            all(report['generated_resources'].values()) and
            report['weiDU_component_recorded_on_clone'] and report.get('resources_absent_after_rollback') and
            report.get('clone_weidu_component_removed') and
            report['clone_dialog_files_unchanged_after_rollback'] and
            report['clone_bcs_matches_original_after_install'] and report['clone_bcs_matches_original_after_test']
        ) else 'REVIEW_ISOLATED_WEIDU'
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:
        report['status']='REVIEW_ISOLATED_WEIDU'
        report['exception']=str(e)[:800]
    finally:
        report['live_critical_after']=old.capture_critical(root)
        report['original_game_modified']=(report['live_critical_after']!=before)
        if report['original_game_modified']:
            report['status']='REVIEW_LIVE_GAME_CHANGED_EXTERNALLY'
        result_path=root/'BGXAI_LOCAL_BUILD'/REPORT_NAME
        result_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description='Inspect or resume the existing independent BGX32 test clone')
    p.add_argument('--inspect',action='store_true', help='READ-ONLY status; no copy, no WeiDU')
    p.add_argument('--resume-isolated',action='store_true',help='Copy only missing clone files, then test WeiDU in TEST clone')
    a=p.parse_args()
    if a.resume_isolated and a.inspect:
        print('BGXAI 033 ERROR: choose only one mode');return 1
    if not a.resume_isolated:
        try:
            x=inspect(GAME)
            print('BGXAI 033:',x['status'])
            print('TEST COPY:',x['clone'])
            print('Files expected:',x['expected_files'],'present:',x['present_files'],'missing:',x['missing_files'])
            print('Extra files:',x['unexpected_files'],'wrong sizes:',x['size_mismatches'])
            print('Prior WeiDU report:',x['previous_032_report'])
            print('READ ONLY. No game, clone or EPS files changed.')
            return 0
        except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
            print('BGXAI 033 INSPECT ERROR:',str(e));return 1
    try:
        result=resume(GAME)
        print('BGXAI 033:',result['status'])
        print('Missing test files copied:',result.get('copied_missing_files'))
        print('WeiDU install exit:',result.get('install_exit_code'))
        print('WeiDU rollback exit:',result.get('uninstall_exit_code'))
        print('Live game unchanged:',not result.get('original_game_modified'))
        print('REPORT:',GAME/'BGXAI_LOCAL_BUILD'/REPORT_NAME)
        return 0 if result['status']=='PASS_ISOLATED_INSTALL_AND_ROLLBACK' else 2
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError,
            subprocess.TimeoutExpired) as e:
        print('BGXAI 033 BLOCKED:',str(e))
        print('Live game untouched by BGXAI 033; existing clone preserved.')
        return 1

if __name__ == '__main__':sys.exit(main())