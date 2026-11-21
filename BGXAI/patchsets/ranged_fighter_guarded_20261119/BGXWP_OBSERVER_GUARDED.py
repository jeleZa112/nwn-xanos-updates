#!/usr/bin/env python3
"""Guarded, optional EEex weapon READ-ONLY observer for the user's exact EET.

Preflight/status never touch the game. Install ONLY after exact typed token.
Install adds a uniquely named M_ Lua listener with WeiDU; no other override
scripts are changed. Rollback ONLY while last WeiDU and with typed permission.
Runtime observer writes raw JSONL to BGXAI_LIVE_REPORTS (outside game).
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
SOURCE = Path(__file__).with_name('M_BGXWP.lua')
SOURCE_SHA = 'f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36'
INSTALL_TOKEN = 'INSTALL_BGXWP_READONLY_OBSERVER'
ROLLBACK_TOKEN = 'ROLLBACK_BGXWP_READONLY_OBSERVER'
MODULE = 'override/M_BGXWP.lua'
STAGED = 'BGXWP/staged/M_BGXWP.lua'
TP2 = 'BGXWP/setup-BGXWP.tp2'
EXE = 'setup-BGXWP.exe'
PROOF = 'BGXWP/PROOF.json'
WEIDU_EXE = 'setup-enhanced-powergaming-scripts.exe'
LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXWP[/\\]SETUP-BGXWP[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
# These live hashes came from the user's 2026-11-21 native preflight PASS.
# Fail closed on unexpected drift rather than changing another patch's BCS/Lua.
BASELINE = {
    'override/DPLAYER.BCS': '4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed',
    'override/BDDEFAI.BCS': '9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e',
    'override/WTASIGHT.BCS': 'ec50ad2e91a33aad4e4b6b1bc33ac87f0f02f4af49f9649b5cad6c36faeaa403',
    'override/PRIEST1.BCS': '86a3c63799f09e7b9d51f6a61a893eff36f50ee3d6a3fe7eaa2dae97d2861589',
    'override/M_BX43.lua': '74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c',
    'override/M_BXFR.lua': '0ca56636c80095e1cca3e1191fa89e452aa98f55387f8975c3302cdbead6a6bb',
}
TP2_TEXT = (
    'BACKUP ~BGXWP/backup~\n'
    'AUTHOR ~BGXAI isolated passive EEex weapon evidence collector~\n'
    'BEGIN ~BGXWP READ ONLY observer, no combat commands~\n'
    'COPY ~BGXWP/staged/M_BGXWP.lua~ ~override/M_BGXWP.lua~\n'
)

def digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError('SOURCE_NOT_REGULAR_FILE:' + path.name)
    h=hashlib.sha256()
    with path.open('rb') as fd:
        for chunk in iter(lambda:fd.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()

def check_path(root: Path) -> None:
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(GAME)):
        raise ValueError('THIS_GAME_PATH_ONLY')
    if root.is_symlink() or not root.is_dir() or not (root/'chitin.key').is_file():
        raise ValueError('GAME_ROOT_INVALID')

def backup_dir() -> Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_REQUIRED')
    return Path(home)/'Documents'/'BGXAI_BACKUPS'

def report_dir() -> Path:
    home=os.environ.get('USERPROFILE')
    if not home:raise ValueError('USERPROFILE_REQUIRED')
    return Path(home)/'Documents'/'BGXAI_LIVE_REPORTS'

def weidu_last(root: Path) -> str:
    p=root/'WeiDU.log'
    if p.is_symlink() or not p.is_file():raise ValueError('WEIDU_LOG_MISSING')
    lines=[line.strip() for line in p.read_text(encoding='utf-8-sig',errors='replace').splitlines() if line.strip().startswith('~')]
    return lines[-1] if lines else 'NONE'

def check_processes() -> None:
    # Manual/external install must never change resources while game or WeiDU runs.
    if os.name!='nt':raise ValueError('WINDOWS_REQUIRED')
    cmd=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,
        stdin=subprocess.DEVNULL,timeout=20,errors='replace')
    if cmd.returncode:raise ValueError('TASKLIST_UNAVAILABLE_STOP')
    names={row[0].strip().lower() for row in csv.reader(io.StringIO(cmd.stdout)) if row}
    blocked={'baldur.exe','bgmain.exe','infinityloader.exe','weidu.exe',
        'setup-enhanced-powergaming-scripts.exe','setup-bgxwp.exe'}
    if names & blocked:raise ValueError('GAME_OR_WEIDU_PROCESS_RUNNING')

def check_source() -> None:
    if digest(SOURCE)!=SOURCE_SHA:raise ValueError('OBSERVER_SOURCE_SHA_MISMATCH')
    contents=SOURCE.read_bytes()
    for banned in (b'SelectWeaponAbility(',b'ClearActions(',b'Stop(',b'SetGlobal(',b'Attack('):
        if banned in contents:raise ValueError('OBSERVER_CONTAINS_GAME_ACTION')

def baseline(root:Path) -> dict:
    actual={}
    for name,expected in BASELINE.items():
        found=digest(root/name)
        if found!=expected:raise ValueError('INSTALLED_BASELINE_DRIFT:'+name)
        actual[name]=found
    return actual

def validate_weidu(root:Path) -> Path:
    path=root/WEIDU_EXE
    if path.is_symlink() or not path.is_file() or path.stat().st_size>70_000_000:
        raise ValueError('WEIDU_BINARY_UNAVAILABLE')
    with path.open('rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('WEIDU_BINARY_NOT_WINDOWS_EXE')
    return path

def external_backup(root:Path) -> Path:
    dest=backup_dir() / ('PRE_BGXWP_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if dest.exists():raise ValueError('EXTERNAL_BACKUP_ALREADY_EXISTS')
    dest.mkdir(parents=True)
    files=['WeiDU.log','chitin.key',*BASELINE.keys()]
    for name in files:
        source=root/name
        if source.is_symlink() or not source.is_file():raise ValueError('BACKUP_SOURCE_MISSING:'+name)
        output=dest/name
        output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,output)
        if digest(source)!=digest(output):raise ValueError('EXTERNAL_BACKUP_VERIFY_FAILED:'+name)
    return dest

def native_weidu(root:Path,uninstall=False) -> None:
    cmd=[str(root/EXE),'--noautoupdate','--no-exit-pause','--game',str(root),
         '--use-lang','ru_ru','--force-uninstall' if uninstall else '--force-install','0']
    result=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
        text=True,errors='replace',timeout=180)
    msg=((result.stdout or '')+'\n'+(result.stderr or ''))[-900:]
    if result.returncode!=0 or re.search(r'(?im)^\s*(?:ERROR:|FATAL ERROR:)',msg):
        raise ValueError('WEIDU_FAILED:'+msg)

def preflight(root:Path) -> dict:
    check_path(root);check_source();check_processes()
    before=baseline(root)
    validate_weidu(root)
    for s in ('BGXWP',MODULE,STAGED,TP2,EXE,PROOF):
        if (root/s).exists() or (root/s).is_symlink():
            raise ValueError('BGXWP_PATH_ALREADY_EXISTS:'+s)
    # Static validation of EEex installation; runtime compatibility still untested.
    core=root/'override'/'M___EEex.lua'
    if core.is_symlink() or not core.is_file():raise ValueError('EEEX_BOOTSTRAP_MISSING')
    if (root/'WeiDU.log').is_symlink():raise ValueError('WEIDU_LOG_LINK')
    return {'status':'PREFLIGHT_OBSERVER_READY_SOURCE_ONLY','source_sha256':SOURCE_SHA,
            'runtime_EEex_validated':False,'game_modified':False,'baseline':before,
            'current_weidu_last':weidu_last(root)}

def status(root:Path) -> dict:
    check_path(root);check_source()
    before=baseline(root)
    mod=root/MODULE
    state=('INSTALLED_READONLY_OBSERVER_SOURCE_EXACT' if
           mod.is_file() and not mod.is_symlink() and digest(mod)==SOURCE_SHA else
           'NOT_INSTALLED' if not mod.exists() else 'UNKNOWN_OBSERVER_SOURCE_STOP')
    if state=='UNKNOWN_OBSERVER_SOURCE_STOP':raise ValueError(state)
    return {'status':state,'module_sha256':SOURCE_SHA if state.startswith('INSTALLED') else None,
            'weidu_last':weidu_last(root),'baseline_verified':len(before),
            'game_modified_by_status':False,'runtime_log_exists':(report_dir()/'BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl').is_file()}

def install(root:Path) -> dict:
    pre=preflight(root)
    if pre['status']!='PREFLIGHT_OBSERVER_READY_SOURCE_ONLY':raise ValueError('PREFLIGHT_FAILED')
    # Create non-game report folder (safe, no fallback to game directory).
    dest=report_dir();dest.mkdir(parents=True,exist_ok=True)
    backup=external_backup(root)
    # Repeat critical preconditions after backup to avoid installing against drift.
    check_processes();baseline(root);check_source()
    stage=root/STAGED
    stage.parent.mkdir(parents=True,exist_ok=False)
    shutil.copy2(SOURCE,stage)
    if digest(stage)!=SOURCE_SHA:raise ValueError('STAGE_SHA_MISMATCH')
    tp=root/TP2
    tp.write_text(TP2_TEXT,encoding='utf-8',newline='\n')
    shutil.copy2(validate_weidu(root),root/EXE)
    if digest(root/EXE)!=digest(root/WEIDU_EXE):raise ValueError('WEIDU_COPY_MISMATCH')
    baseline(root);check_processes()
    native_weidu(root)
    if digest(root/MODULE)!=SOURCE_SHA or not LAST.match(weidu_last(root)):
        raise ValueError('POSTINSTALL_SOURCE_OR_WEIDU_LAST_MISMATCH')
    baseline(root)
    proof={'source_sha256':SOURCE_SHA,'external_backup':str(backup),
           'game_root':str(root),'install_time_utc':datetime.now(timezone.utc).isoformat(),
           'status':'BGXWP_OBSERVER_INSTALLED_NOT_YET_RUNTIME_TESTED'}
    (root/PROOF).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return {**proof,'game_modified':True,'next':'START_NORMAL_GAME_AND_CHECK_BGXAI_LIVE_REPORTS'}

def rollback(root:Path) -> dict:
    check_path(root);check_processes();check_source();baseline(root)
    if not LAST.match(weidu_last(root)):raise ValueError('BGXWP_NOT_LAST_WEIDU')
    if digest(root/MODULE)!=SOURCE_SHA:raise ValueError('OBSERVER_CODE_CHANGED_STOP')
    proof=root/PROOF
    if proof.is_symlink() or not proof.is_file():raise ValueError('ROLLBACK_PROOF_MISSING')
    record=json.loads(proof.read_text('utf-8'))
    backup=Path(record.get('external_backup',''))
    if not backup.is_dir() or not (backup/'WeiDU.log').is_file() or record.get('source_sha256')!=SOURCE_SHA:
        raise ValueError('EXTERNAL_BACKUP_NOT_VERIFIED')
    for name,expected in BASELINE.items():
        if digest(backup/name)!=expected:raise ValueError('BACKUP_BASELINE_MISMATCH:'+name)
    # Never revert manually: WeiDU must be last and own its rollback.
    native_weidu(root,uninstall=True)
    if (root/MODULE).exists():raise ValueError('WEIDU_UNINSTALL_MODULE_REMAINS_STOP')
    baseline(root)
    return {'status':'BGXWP_LAST_ONLY_WEIDU_ROLLBACK_VERIFIED','game_modified':True}

"""Passive BGXWP console evidence capture; no game-state writes or orders.

This module is integrated into BGXWP_OBSERVER_GUARDED.py under one updater.
All installer-facing entrypoints must first call game path / baseline / installed
observer and process guards; this module handles only bounded report I/O.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

CAPTURE_PREFIX = 'BGXAI_WEAPON_CONSOLE_'
RAW_FILENAME = 'BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl'
SCHEMA_NAME = 'BGXAI_WEAPON_RUNTIME_RAW_R1'
MARKER = '[BGXWP] '
MAX_LOG_BYTES = 12_000_000


def launch_capture(root: Path, out_dir: Path) -> dict:
    """Launches the existing InfinityLoader with redirected stdout only."""
    launcher = root / 'InfinityLoader.exe'
    if launcher.is_symlink() or not launcher.is_file() or launcher.stat().st_size > 70_000_000:
        raise ValueError('INFINITYLOADER_NOT_VERIFIED')
    with launcher.open('rb') as fh:
        if fh.read(2) != b'MZ':
            raise ValueError('INFINITYLOADER_PE_HEADER_INVALID')
    if out_dir.is_symlink():
        raise ValueError('REPORT_DIR_SYMLINK')
    out_dir.mkdir(parents=True, exist_ok=True)
    name = CAPTURE_PREFIX + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.log'
    dest = out_dir / name
    if dest.is_symlink():
        raise ValueError('CONSOLE_LOG_SYMLINK')
    try:
        with dest.open('xb') as sink:
            child = subprocess.Popen([str(launcher)], cwd=root, stdin=subprocess.DEVNULL,
                                     stdout=sink, stderr=subprocess.STDOUT, close_fds=True)
    except (OSError, ValueError) as exc:
        raise ValueError('INFINITYLOADER_CAPTURE_LAUNCH_FAILED') from exc
    return {'status': 'WEAPON_CONSOLE_CAPTURE_LAUNCHED_UNVERIFIED',
            'pid': child.pid, 'console_log': str(dest), 'game_modified': False,
            'next': 'Play a normal fight, exit the game, choose 159 -> 6 to collect'}


def _candidate(folder: Path) -> Path | None:
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('REPORT_DIR_MISSING_OR_SYMLINK')
    options = []
    for path in folder.glob(CAPTURE_PREFIX + '*.log'):
        if path.is_symlink():
            continue
        if path.is_file():
            options.append((path.stat().st_mtime_ns, path.name, path))
    return max(options)[2] if options else None


def _validated_action(event: dict) -> bool:
    if event.get('type') != 'ACTION':
        return False
    if type(event.get('sequence')) is not int or not 1 <= event['sequence'] <= 320:
        return False
    if type(event.get('partyIndex')) is not int or not 0 <= event['partyIndex'] <= 5:
        return False
    if type(event.get('actor')) is not int or event['actor'] < 0:
        return False
    if type(event.get('action')) is not int or not 0 <= event['action'] <= 65535:
        return False
    for field in ('weaponAbilityVerified', 'actualPerSlotAPRVerified',
                  'buffsExhaustivelyObserved', 'manualOrderOriginVerified',
                  'epsQueueVerified', 'weaponSwitchAuthorized'):
        if event.get(field) is not False:
            return False
    return True


def _direct_report(out_dir: Path) -> dict | None:
    dest = out_dir / RAW_FILENAME
    if dest.is_symlink():
        raise ValueError('RAW_REPORT_SYMLINK')
    if not dest.exists():
        return None
    st = dest.stat()
    if not dest.is_file() or st.st_size <= 0 or st.st_size > MAX_LOG_BYTES:
        return {'status': 'WEAPON_DIRECT_RAW_REPORT_INVALID_SIZE',
                'report_file': str(dest), 'game_modified': False}
    with dest.open('rb') as stream:
        data = stream.read(MAX_LOG_BYTES + 1)
    if len(data) != st.st_size or dest.stat().st_size != st.st_size:
        raise ValueError('RAW_REPORT_CHANGED_WHILE_READING')
    session = False
    ready = False
    actions = 0
    for line in data.decode('utf-8', 'replace').splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if e.get('type') == 'SESSION' and e.get('schema') == SCHEMA_NAME and e.get('readOnly') is True:
            session = True
            ready = False
            actions = 0
        elif session and e.get('type') == 'READY' and e.get('observerRegistered') is True:
            ready = True
        elif session and ready and _validated_action(e):
            actions += 1
    return {'status': 'WEAPON_RAW_DIRECT_FILE_READY' if session and ready and actions else
            'WEAPON_RAW_DIRECT_FILE_INCOMPLETE',
            'report_file': str(dest), 'actions': actions,
            'game_modified': False, 'per_slot_apr_verified': False,
            'manual_eps_queue_verified': False}


def collect_capture(out_dir: Path) -> dict:
    """Creates a new raw JSONL only if the verified file sink has not done so.

    Duplicate Infinity_Log/print messages use the Lua sequence number;
    distinct attacks with identical combat statistics stay distinct.
    """
    direct = _direct_report(out_dir)
    path = _candidate(out_dir)
    if path is None:
        return direct if direct is not None else {
            'status': 'WEAPON_CONSOLE_CAPTURE_ABSENT', 'game_modified': False}
    st = path.stat()
    if not 1 <= st.st_size <= MAX_LOG_BYTES:
        return {'status': 'WEAPON_CONSOLE_CAPTURE_EMPTY_OR_OVERSIZED',
                'console_log': str(path), 'game_modified': False}
    with path.open('rb') as stream:
        payload = stream.read(MAX_LOG_BYTES + 1)
    if len(payload) != st.st_size or path.stat().st_size != st.st_size:
        raise ValueError('CAPTURE_LOG_CHANGED_WHILE_READING')
    session = None
    ready = False
    events = {}
    malformed = 0
    for raw_line in payload.decode('utf-8', 'replace').splitlines():
        marker_pos = raw_line.find(MARKER + '{')
        if marker_pos < 0:
            continue
        try:
            event = json.loads(raw_line[marker_pos + len(MARKER):].strip())
        except (ValueError, TypeError):
            malformed += 1
            continue
        if not isinstance(event, dict):
            malformed += 1
            continue
        kind = event.get('type')
        if kind == 'SESSION' and event.get('schema') == SCHEMA_NAME:
            if event.get('readOnly') is True and event.get('noActionsIssued') is True:
                session = event
                ready = False
                events = {}
        elif kind == 'READY' and event.get('schema') == SCHEMA_NAME:
            if session is not None and event.get('observerRegistered') is True:
                ready = True
        elif ready and kind == 'ACTION':
            if not _validated_action(event):
                malformed += 1
                continue
            seq = event['sequence']
            if seq in events and events[seq] != event:
                raise ValueError('CONFLICTING_CONSOLE_SEQUENCE')
            events[seq] = event
    if session is None or not ready:
        if direct is not None: return direct
        return {'status': 'WEAPON_CONSOLE_SESSION_OR_READY_NOT_CONFIRMED',
                'console_log': str(path), 'invalid_lines': malformed,
                'game_modified': False}
    if not events:
        if direct is not None: return direct
        return {'status': 'WEAPON_CONSOLE_READY_NO_PARTY_ACTIONS',
                'console_log': str(path), 'invalid_lines': malformed,
                'game_modified': False}
    dest = out_dir / RAW_FILENAME
    if direct is not None:
        return {**direct, 'status': 'WEAPON_RAW_DIRECT_PRESERVED_CONSOLE_ALSO_SEEN',
                'console_log': str(path), 'actions_in_console': len(events)}
    lines = [json.dumps(session, separators=(',', ':'), sort_keys=True),
             json.dumps({'type':'READY', 'schema':SCHEMA_NAME,
                         'observerRegistered':True, 'source':'CONSOLE_CAPTURE'},
                        separators=(',', ':'), sort_keys=True)]
    lines.extend(json.dumps(event, separators=(',', ':'), sort_keys=True)
                 for _,event in sorted(events.items()))
    # Exclusive-create: never overwrite a direct live-EEex file if it appears.
    with dest.open('x', encoding='utf-8', newline='\n') as output:
        output.write('\n'.join(lines) + '\n')
    return {'status':'WEAPON_RAW_CONSOLE_CAPTURE_COLLECTED',
            'report_file':str(dest), 'console_log':str(path),
            'actions':len(events), 'invalid_lines':malformed,
            'game_modified':False, 'per_slot_apr_verified':False,
            'manual_eps_queue_verified':False}


def capture_checked(root:Path) -> dict:
    # Fail-closed before starting a new copy of the user's usual game launcher.
    check_path(root);check_processes()
    current=status(root)
    if current['status']!='INSTALLED_READONLY_OBSERVER_SOURCE_EXACT':
        raise ValueError('WEAPON_OBSERVER_MUST_BE_INSTALLED_FIRST')
    return launch_capture(root,report_dir())


def collect_checked(root:Path) -> dict:
    # Read and parse console capture only after the game has exited.
    check_path(root);check_processes()
    current=status(root)
    if current['status']!='INSTALLED_READONLY_OBSERVER_SOURCE_EXACT':
        raise ValueError('WEAPON_OBSERVER_NOT_INSTALLED')
    return collect_capture(report_dir())


def write_report(data:dict) -> None:
    out=report_dir();out.mkdir(parents=True,exist_ok=True)
    report=out/'BGXWP_OBSERVER_SETUP_R1.json'
    if report.is_symlink():raise ValueError('REPORT_IS_SYMLINK')
    report.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('REPORT_FILE: '+str(report))

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--game',default=str(GAME))
    parser.add_argument('mode',nargs='?',choices=('preflight','install','status','rollback','capture','collect','r2'))
    args=parser.parse_args()
    root=Path(args.game)
    try:
        mode=args.mode
        if mode is None:
            print('BGXWP passive EEex weapon observer, independent of V6/EPS')
            print('1 - preflight READ ONLY')
            print('2 - install guarded (typed approval, modifies only new Lua + WeiDU metadata)')
            print('3 - status READ ONLY')
            print('4 - rollback LAST-ONLY (typed approval)')
            print('5 - launch usual game with console capture (no game edits)')
            print('6 - collect RAW weapon report after closing game (READ ONLY game)')
            print('7 - R2 passive weapon/quiver observer submenu (separate consent)')
            print('0 - exit')
            answer=(input('BGXWP choice [0]: ').strip() or '0')
            choices={'1':'preflight','2':'install','3':'status','4':'rollback','5':'capture','6':'collect','7':'r2'}
            if answer=='0':return 0
            if answer not in choices:raise ValueError('MENU_CHOICE_INVALID')
            mode=choices[answer]
        if mode=='r2':
            import BGXW2_OBSERVER_GUARDED as slots_r2
            return slots_r2.menu(root)
        if mode=='install':
            if input('Type '+INSTALL_TOKEN+' exactly to install: ').strip()!=INSTALL_TOKEN:
                raise ValueError('INSTALL_NOT_AUTHORIZED')
            data=install(root)
        elif mode=='rollback':
            if input('Type '+ROLLBACK_TOKEN+' exactly to rollback: ').strip()!=ROLLBACK_TOKEN:
                raise ValueError('ROLLBACK_NOT_AUTHORIZED')
            data=rollback(root)
        elif mode=='preflight':data=preflight(root)
        elif mode=='capture':data=capture_checked(root)
        elif mode=='collect':data=collect_checked(root)
        else:data=status(root)
        write_report(data)
        print('STATUS: '+data['status'])
        return 0
    except Exception as exc:
        data={'status':'BGXWP_STOP','reason':f'{type(exc).__name__}: {exc}',
              'game_modified_unknown_if_install_in_progress':args.mode=='install'}
        try:write_report(data)
        except Exception as report_exc:print('REPORT_STOP:'+str(report_exc))
        print('BGXWP_STOP:'+str(exc))
        return 2

if __name__=='__main__':sys.exit(main())
