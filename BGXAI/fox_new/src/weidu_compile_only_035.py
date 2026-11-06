"""BGXAI 035 - experimental direct WeiDU BAF compiler, NO TP2 INSTALL.

Compiles the self-authored disabled BGX31 BAF to a scratch BCS and copies the
source Russian dialog TLKs to the scratch directory. --plan is default.

This does NOT install or assign an AI script, patch EPS, or copy the whole game.
The --compile path has only synthetic tests so far; Windows WeiDU is untested.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import weidu_isolated_test_032 as old

ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
SCRATCH_PREFIX = 'BGX35_COMPILE_ONLY_'
CRITICAL = ('chitin.key', 'WeiDU.log', 'override/BDDEFAI.BCS',
            'lang/ru_ru/dialog.tlk', 'lang/ru_ru/dialogf.tlk')


def filehash(p: Path):
    if not p.is_file() or old.junction_or_link(p):
        raise ValueError('Required real game file missing or redirected: '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):
            h.update(x)
    return h.hexdigest()


def snapshots(root: Path):
    return {name:filehash(root/name) for name in CRITICAL}


def enforce_scratch(root: Path, out: Path):
    local = root/'BGXAI_LOCAL_BUILD'
    if old.junction_or_link(local) or not local.is_dir():
        raise ValueError('Missing/unsafe BGXAI_LOCAL_BUILD. No scratch files created.')
    if out.parent != local or not out.name.startswith(SCRATCH_PREFIX) or \
       old.junction_or_link(out) or out.exists() or old.junction_or_link(root):
        raise ValueError('Unsafe/existing compile destination')
    return local


def command(exe: Path, root: Path, scratch: Path) -> list[str]:
    """No WeiDU TP2/--force-install/--force-uninstall in this invocation.

    Direct .BAF conversion and --out, --tlkout, --ftlkout are documented
    WeiDU command-line options, NOT a TP2 mod installation.
    """
    arg = [str(exe), '--no-auto-tp2', '--noautoupdate',
        '--game', str(root), '--use-lang', 'ru_ru',
        '--tlkin', str(scratch/'input_dialog.tlk'),
        '--ftlkin', str(scratch/'input_dialogf.tlk'),
        '--tlkout', str(scratch/'output_dialog.tlk'),
        '--ftlkout', str(scratch/'output_dialogf.tlk'),
        '--out', str(scratch/'BGX31_OBSERVER.BCS'),
        '--log', str(scratch/'WEIDU_COMPILE_ONLY.DEBUG'),
        str(scratch/'BGX31_DISABLED_OBSERVER.BAF')]
    return arg


def command_is_safe(args, root: Path, scratch: Path):
    words = [a.casefold() for a in args]
    if any(any(x in a for x in ('--force-install','--force-uninstall','--yes',
            '--reinstall','--uninstall')) for a in words):
        return False
    if not args[-1].casefold().endswith('.baf') or '--out' not in words or \
       '--tlkout' not in words or '--ftlkout' not in words or \
       '--no-auto-tp2' not in words:
        return False
    for flag in ('--out','--tlkout','--ftlkout','--log'):
        i = words.index(flag)
        if i+1>=len(args): return False
        dest=Path(args[i+1])
        if dest.parent != scratch or dest == root:
            return False
    return True


def compile_only(root:Path, *,enforce_root=True,
                 validate_live=old.verify_live, choose_exe=old.choose_weidu,
                 runner=subprocess.run, tag=None) -> dict:
    root=Path(root).resolve()
    if enforce_root and os.path.normcase(str(root)).casefold()!=os.path.normcase(str(ROOT.resolve())).casefold():
        raise ValueError('Refuse old/wrong Foxx game root')
    # Full read-only 030/031 identity check; stage is already on user's computer.
    validate_live(root,enforce_root=enforce_root)
    stage=old.verify_stage(root)
    weidu=choose_exe(root)
    stamp=tag or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if not stamp or not stamp.replace('-','').replace('_','').isalnum():
        raise ValueError('Unsafe output label')
    scratch=root/'BGXAI_LOCAL_BUILD'/(SCRATCH_PREFIX+stamp)
    enforce_scratch(root,scratch)
    before=snapshots(root)
    scratch.mkdir(exist_ok=False)
    report={'schema':35,'mode':'DIRECT_BAF_COMPILE_ONLY',
        'status':'NOT_RUN','target':str(scratch),'weiDU_executable':weidu.name,
        'original_game_modified':False,'bgxai_installed':False,
        'eps_files_uploaded':False,'full_game_clone_created':False,
        'script_assigned_to_characters':False,'compile_verified':False}
    try:
        # Copy only two small, read-only input TLKs; keep output TLKs separate.
        for name,dest in [('lang/ru_ru/dialog.tlk','input_dialog.tlk'),
                          ('lang/ru_ru/dialogf.tlk','input_dialogf.tlk')]:
            shutil.copy2(root/name,scratch/dest)
            if filehash(scratch/dest)!=before[name]:
                raise ValueError('TLK scratch copy hash mismatched')
        src=stage/'BGX31/disabled_observer.baf'
        shutil.copy2(src,scratch/'BGX31_DISABLED_OBSERVER.BAF')
        if filehash(src)!=filehash(scratch/'BGX31_DISABLED_OBSERVER.BAF'):
            raise ValueError('BAF scratch copy hash mismatched')
        cmd=command(weidu,root,scratch)
        if not command_is_safe(cmd,root,scratch):
            raise ValueError('Compiler arguments do not meet no-install safety rules')
        p=runner(cmd,cwd=str(scratch),capture_output=True,text=True,
                 encoding='utf-8',errors='replace',timeout=300,check=False)
        report['weidu_exit_code']=int(p.returncode)
        report['weidu_output_tail']=((p.stdout or '')+'\n'+(p.stderr or ''))[-12000:]
        output=scratch/'BGX31_OBSERVER.BCS'
        report['compiled_bcs_present']=output.is_file() and output.stat().st_size>0
        report['compiled_bcs_size']=output.stat().st_size if output.is_file() else None
        report['compile_verified']=p.returncode==0 and report['compiled_bcs_present']
        report['status']='COMPILE_ONLY_OK' if report['compile_verified'] else 'COMPILER_REVIEW'
    except Exception as e:
        report['status']='COMPILER_ERROR'
        report['error']=str(e)[:700]
    finally:
        report['original_game_modified']=snapshots(root)!=before
        if report['original_game_modified']:
            report['status']='STOP_LIVE_HASH_CHANGED'
        (scratch/'BGX35_COMPILE_REPORT.json').write_text(json.dumps(report,indent=2,
            ensure_ascii=False)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description='No-game-copy direct BAF compile research')
    p.add_argument('--compile',action='store_true',help='Explicitly compile BAF to isolated scratch BCS')
    opt=p.parse_args(argv)
    if not opt.compile:
        print('BGXAI 035: SOURCE-ONLY RESEARCH. Default mode does nothing.')
        print('Full EET clone tests 032/033/034 have been retired.')
        return 0
    try:
        result=compile_only(ROOT)
        print('BGXAI 035:',result['status'])
        print('Original Foxx critical hashes unchanged:',not result['original_game_modified'])
        print('No game AI installed; no full clone made.')
        print('Report:',Path(result['target'])/'BGX35_COMPILE_REPORT.json')
        return 0 if result['status']=='COMPILE_ONLY_OK' else 2
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired) as e:
        print('BGXAI 035 BLOCKED:',str(e))
        return 1

if __name__=='__main__':sys.exit(main())