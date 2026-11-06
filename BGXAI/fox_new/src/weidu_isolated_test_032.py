"""BGXAI 0.3.2: guarded independent EET clone + WeiDU install/uninstall test.

Only changes a NEW sibling copy of the game. The original Foxx game, its EPS,
BDDEFAI, script slots, dialog.tlk and WeiDU.log are never modified.

Live usage after BGXAI_UPDATE.cmd refresh:
 py -3 "C:\\Games\\BG_EET_FOXX_NEW\\BGXAI_DEV\\src\\weidu_isolated_test_032.py" --run-isolated

No hardlinks, junctions, symlinks, or inplace test. The 031 stage must already
exist, and 030 validation must still return READY. Does not run the game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

GAME_ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
CLONE_SUFFIX = '__BGX32_TEST'
STAGE_DIR = Path('BGXAI_LOCAL_BUILD/BGX31_STAGE_NOT_INSTALLED')
OUT_NAME = 'BGXAI_032_ISOLATED_WEIDU_RESULT.json'
SKIP_TOP = {'BGXAI_LOCAL_BUILD', 'BGXAI_DEV', 'BGXAI_LIVE_REPORTS'}
SOURCE_FILES = ('setup-BGX31.tp2', 'BGX31/disabled_observer.baf', 'README_RU.txt')
CRITICAL = ('chitin.key', 'WeiDU.log', 'override/BDDEFAI.BCS',
            'lang/ru_ru/dialog.tlk', 'lang/ru_ru/dialogf.tlk')
EXE_CANDIDATES = ('weidu.exe', 'setup-enhanced-powergaming-scripts.exe',
                  'setup-stratagems.exe', 'setup-EET_END.exe', 'setup-EET.exe')
MAX_FILES = 300000
MAX_BYTES = 250 * 1024**3
MIN_EXTRA_BYTES = 2 * 1024**3


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def junction_or_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    # Windows junctions are reparse points but may NOT be considered symlinks.
    attr = getattr(path.lstat(), 'st_file_attributes', 0)
    reparse = getattr(__import__('stat'), 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
    return bool(attr & reparse)


def inside(parent: Path, p: Path) -> bool:
    try:
        return p.resolve(strict=False).is_relative_to(parent.resolve(strict=False))
    except (OSError, ValueError):
        return False


def verify_stage(root: Path):
    stage = root / STAGE_DIR
    if junction_or_link(stage) or not stage.is_dir() or not inside(root, stage):
        raise ValueError('BGX31 stage missing or redirected')
    mf = stage / 'BGX31_STAGE_MANIFEST.json'
    if junction_or_link(mf) or not mf.is_file() or mf.stat().st_size > 500000:
        raise ValueError('BGX31 stage manifest missing or invalid')
    data = json.loads(mf.read_text(encoding='utf-8'))
    if data.get('schema') != 31 or data.get('status') != 'ISOLATED_COMPILATION_SOURCE_ONLY' or \
       data.get('source_included') is not False or data.get('eps_files_included') is not False or \
       data.get('bcs_files_included') is not False or data.get('weiDU_executed') is not False or \
       data.get('game_modified') is not False or data.get('game_ai_replaced') is not False:
        raise ValueError('BGX31 stage is not approved source-only package')
    records = data.get('files')
    if not isinstance(records, dict) or set(records) != set(SOURCE_FILES):
        raise ValueError('Unexpected BGX31 stage files')
    for name in SOURCE_FILES:
        target = stage / name
        rec = records[name]
        if junction_or_link(target) or not target.is_file() or not inside(stage, target) or \
           not isinstance(rec, dict) or target.stat().st_size != rec.get('bytes') or \
           not isinstance(rec.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', rec['sha256']) or \
           digest(target) != rec['sha256']:
            raise ValueError('Stage integrity failure: ' + name)
    tp2 = (stage / SOURCE_FILES[0]).read_text(encoding='utf-8')
    baf = (stage / SOURCE_FILES[1]).read_text(encoding='utf-8')
    if 'COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGX31.BCS~' not in tp2 or \
       'EXTEND_BOTTOM ~BGX31.BCS~' not in tp2 or \
       'COPY_EXISTING ~BGX31.BCS~ ~scripts/BGX31.BS~' not in tp2 or \
       'EXTEND_BOTTOM ~BDDEFAI.BCS~' in tp2 or \
       'Global("BGX31_OBS","LOCALS",1)' not in baf or \
       any(s in baf for s in ('Attack(', 'AttackOneRound(', 'RunAway(', 'MoveToPoint(', 'Spell(', 'BattleSong(')):
        raise ValueError('Unexpected staged TP2/BAF behavior')
    return stage


def verify_live(root: Path, *, enforce_root=True, preflight=None):
    root = root.resolve()
    if enforce_root and os.path.normcase(str(root)).casefold() != os.path.normcase(str(GAME_ROOT.resolve())).casefold():
        raise ValueError('Wrong game path - old build forbidden')
    if not (root / 'chitin.key').is_file() or junction_or_link(root / 'chitin.key'):
        raise ValueError('New Foxx chitin.key missing or redirected')
    if preflight is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import eps_runtime_preflight_030
        preflight = eps_runtime_preflight_030.validate
    data = preflight(root, enforce_root=enforce_root)
    if data.get('status') != 'READY_FOR_ISOLATED_COMPILATION_REVIEW' or \
       data.get('bddefai_override_state') != 'SAME_AS_SNAPSHOT' or \
       data.get('changed_file_count') != 0 or \
       data.get('blockers') or data.get('eps_weidu_components') != 3 or \
       data.get('source_files_checked') != 235:
        raise ValueError('Latest EPS/WeiDU/BDDEFAI compatibility preflight blocked')
    verify_stage(root)
    if not (root / 'override/BDDEFAI.BCS').is_file():
        raise ValueError('Missing real BDDEFAI in override')
    return root


def choose_weidu(root: Path):
    for name in EXE_CANDIDATES:
        exe = root / name
        if exe.is_file() and not junction_or_link(exe) and exe.stat().st_size > 100000:
            with exe.open('rb') as f:
                if f.read(2) == b'MZ':
                    return exe
    raise ValueError('No verified local Windows WeiDU executable found; no download attempted')


def collect(root: Path):
    """Enumerate regular independent source files, reject reparse traversal."""
    result, total = [], 0
    for where, dirs, files in os.walk(root, topdown=True, followlinks=False):
        folder = Path(where)
        if junction_or_link(folder):
            raise ValueError('Redirected folder in game: ' + str(folder))
        dirs[:] = sorted(d for d in dirs if not (folder == root and d in SKIP_TOP))
        for name in dirs:
            d = folder / name
            if junction_or_link(d):
                raise ValueError('Junction/symlink inside game: ' + str(d))
        for name in sorted(files):
            f = folder / name
            if junction_or_link(f) or not f.is_file():
                raise ValueError('Non-regular or redirected file: ' + str(f))
            n = f.stat().st_size
            total += n
            result.append((f.relative_to(root), n))
            if len(result) > MAX_FILES or total > MAX_BYTES:
                raise ValueError('Refuse oversized EET clone; review manually')
    return result, total


def capture_critical(root: Path):
    result = {}
    for name in CRITICAL:
        f = root / name
        result[name] = digest(f) if f.is_file() and not junction_or_link(f) else None
    return result


def clone_game(root: Path, clone: Path, files):
    if clone.exists() or clone.is_symlink() or clone.parent != root.parent or \
       not clone.name.endswith(CLONE_SUFFIX) or inside(root, clone) or inside(clone, root):
        raise ValueError('Unsafe or existing clone destination')
    clone.mkdir(exist_ok=False)
    for rel, n in files:
        src, dst = root / rel, clone / rel
        if junction_or_link(src) or not src.is_file():
            raise ValueError('File changed into symlink during copy: ' + str(rel))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)  # independent bytes; NEVER symlink or hardlink
        if dst.stat().st_size != n:
            raise ValueError('Cloned file size mismatch: ' + str(rel))
    return clone


def prepare_weidu(clone: Path, stage: Path, weidu_source: Path):
    if not (clone / 'chitin.key').is_file() or not (clone / 'override/BDDEFAI.BCS').is_file():
        raise ValueError('Clone lacks essential game resources')
    for rel in SOURCE_FILES[:2]:
        dst = clone / rel
        if dst.exists():
            raise ValueError('BGX31 resource already exists in clone')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / rel, dst)
    exe = clone / 'setup-BGX31.exe'
    if exe.exists():
        raise ValueError('BGX31 executable name already used')
    shutil.copy2(weidu_source, exe)
    return exe


def invoke_weidu(exe: Path, clone: Path, *, uninstall=False, runner=subprocess.run):
    cmd = [str(exe), '--noautoupdate', '--game', str(clone), '--use-lang', 'ru_ru',
           '--force-uninstall' if uninstall else '--force-install', '0']
    process = runner(cmd, cwd=str(clone), capture_output=True, text=True,
                     encoding='utf-8', errors='replace', timeout=600, check=False)
    log = ((process.stdout or '') + '\n' + (process.stderr or ''))[-80000:]
    return process.returncode, log


def run_isolated(root: Path, *, enforce_root=True, preflight=None,
                 disk_usage=shutil.disk_usage, runner=subprocess.run):
    root = verify_live(root, enforce_root=enforce_root, preflight=preflight)
    weidu = choose_weidu(root)
    clone = root.with_name(root.name + CLONE_SUFFIX)
    if clone.exists() or clone.is_symlink():
        raise ValueError('Independent test clone already exists: ' + str(clone))
    sources, total = collect(root)
    space = disk_usage(root.parent).free
    if space < total + max(MIN_EXTRA_BYTES, int(total * 0.07)):
        raise ValueError('Insufficient free space for independent copy: required ' +
                         str(round((total + max(MIN_EXTRA_BYTES, int(total * 0.07))) / 1024**3, 2)) +
                         ' GiB, available ' + str(round(space / 1024**3, 2)) + ' GiB. NO copy performed.')
    before = capture_critical(root)
    report = {'schema':32, 'source':'ISOLATED_EET_COPY', 'status':'PREPARED',
              'live_root':str(root), 'clone_root':str(clone), 'source_files':len(sources),
              'source_bytes':total, 'live_critical_before':before, 'weiDU_binary':weidu.name,
              'original_game_modified':False, 'tested_ai_in_live_game':False,
              'source_upstream_EPS_published':False}
    clone_game(root, clone, sources)
    try:
        after = capture_critical(root)
        if after != before:
            raise ValueError('LIVE critical files changed externally during clone - STOP, no WeiDU run')
        clonebd = digest(clone / 'override/BDDEFAI.BCS')
        if clonebd != before['override/BDDEFAI.BCS']:
            raise ValueError('Independent copy does not match source BDDEFAI')
        exe = prepare_weidu(clone, verify_stage(root), clone / weidu.name)
        clone_before = capture_critical(clone)
        exit_install, out_install = invoke_weidu(exe, clone, runner=runner)
        report['install_exit_code'] = exit_install
        report['install_output_tail'] = out_install[-14000:]
        report['clone_bcs_matches_original_after_install'] = (digest(clone / 'override/BDDEFAI.BCS') == clonebd)
        new_bcs = clone / 'override/BGX31.BCS'
        new_bs = clone / 'scripts/BGX31.BS'
        clone_log = clone / 'WeiDU.log'
        installed_lines = clone_log.read_text(encoding='utf-8-sig', errors='replace') if clone_log.is_file() else ''
        report['weiDU_component_recorded_on_clone'] = ('BGX31' in installed_lines.upper())
        report['generated_resources'] = {
            'BGX31.BCS': new_bcs.is_file() and new_bcs.stat().st_size>0,
            'BGX31.BS': new_bs.is_file() and new_bs.stat().st_size>0}
        # Attempt WeiDU rollback after a successful install, even if generated
        # resources differ from expectations; do not claim clean if failures.
        if exit_install == 0:
            exit_uninstall, out_uninstall = invoke_weidu(exe, clone, uninstall=True, runner=runner)
            report['uninstall_exit_code'] = exit_uninstall
            report['uninstall_output_tail'] = out_uninstall[-14000:]
            report['resources_absent_after_rollback'] = not new_bcs.exists() and not new_bs.exists()
        report['clone_bcs_matches_original_after_test'] = (digest(clone / 'override/BDDEFAI.BCS') == clonebd)
        clone_after = capture_critical(clone)
        report['clone_dialog_files_unchanged_after_rollback'] = all(
            clone_before.get(key) == clone_after.get(key) for key in
            ('lang/ru_ru/dialog.tlk', 'lang/ru_ru/dialogf.tlk'))
        report['live_critical_after'] = capture_critical(root)
        report['original_game_modified'] = (report['live_critical_after'] != before)
        report['status'] = ('PASS_ISOLATED_INSTALL_AND_ROLLBACK' if
            exit_install == 0 and report.get('uninstall_exit_code') == 0 and
            all(report['generated_resources'].values()) and
            report.get('weiDU_component_recorded_on_clone') and
            report.get('resources_absent_after_rollback') and
            report.get('clone_dialog_files_unchanged_after_rollback') and
            report['clone_bcs_matches_original_after_install'] and
            report['clone_bcs_matches_original_after_test'] and
            not report['original_game_modified'] else 'REVIEW_ISOLATED_WEIDU')
    finally:
        report['live_critical_after'] = capture_critical(root)
        report['original_game_modified'] = (report['live_critical_after'] != before)
        dest = root / 'BGXAI_LOCAL_BUILD' / OUT_NAME
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description='Clones Foxx EET; tests WeiDU only in independent copy')
    p.add_argument('--run-isolated', action='store_true', help='clone and run install+rollback on independent copy')
    args = p.parse_args(argv)
    if not args.run_isolated:
        print('BGXAI 032: SAFE BY DEFAULT; no action. Pass --run-isolated to create a full independent game copy.')
        return 0
    try:
        data = run_isolated(GAME_ROOT)
        print('BGXAI 032:', data['status'])
        print('Live game critical hashes unchanged:', not data['original_game_modified'])
        print('WeiDU install exit:', data.get('install_exit_code'))
        print('WeiDU rollback exit:', data.get('uninstall_exit_code'))
        print('REPORT:', GAME_ROOT / 'BGXAI_LOCAL_BUILD' / OUT_NAME)
        print('TEST COPY:', data['clone_root'])
        return 0 if data['status'] == 'PASS_ISOLATED_INSTALL_AND_ROLLBACK' else 2
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError,
            subprocess.TimeoutExpired) as exc:
        print('BGXAI 032 BLOCKED/ERROR:', str(exc))
        print('Original EET untouched by this tool. Any partially created TEST COPY is preserved for review.')
        return 1


if __name__ == '__main__':
    sys.exit(main())