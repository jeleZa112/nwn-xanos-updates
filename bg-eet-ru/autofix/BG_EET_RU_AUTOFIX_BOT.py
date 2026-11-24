"""BG EET RU: one-run deterministic self-repair and audit of *research code*.

No game writes, no Lua/EEex installs, no arbitrary code synthesis. The only
repair source is this distribution's exact SHA-pinned trusted_sources.zip.
A damaged game EXE, unknown binary, bad source archive or unverified native
hook is a HOLD, not something to automatically patch.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

BOT_VERSION = "1.0.0"
TRUSTED_BUNDLE_SHA256 = "9d9a92e182a2389dc4ac4ca1f5c218c04b6452c80e4167d47a95d578da791090"
SOURCE_ARCHIVE_SHA256 = "08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015"
SUITE_RUNNER = "one_pass_offline_validation.py"
REPORT_ENTRY = "59_BG_EET_RU_AUTOFIX_COMPREHENSIVE.json"
EXPECTED_STAGES = (
    'model_unit', 'model_cross_product', 'frame_scoped_bridge_contract',
    'archive_weapon_gates', 'engine_byte_evidence', 'same_hit_native_abi',
    'adversarial_native_abi', 'native_hook_sites',
    'native_observer_readiness', 'guarded_lua_install_rollback_contract',
    'native_control_flow',
)


def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def _guard_regular(path:Path,required:bool=True)->None:
    if path.is_symlink() or (required and not path.is_file()):
        raise RuntimeError('UNSAFE_OR_MISSING_FILE:'+path.name)
    if path.exists() and not path.is_file():
        raise RuntimeError('NON_REGULAR_FILE:'+path.name)


def _guard_dir(path:Path, game:Path|None)->None:
    # Fail closed for symlinked roots and for any path nested in the game root.
    if path.is_symlink():raise RuntimeError('WORKSPACE_SYMLINK_HOLD')
    if game is not None:
        rg=game.resolve(strict=False);rw=path.resolve(strict=False)
        if rg==rw or rg in rw.parents or rw in rg.parents:
            raise RuntimeError('WORKSPACE_GAME_OVERLAP_HOLD')
    if path.exists() and not path.is_dir():raise RuntimeError('WORKSPACE_NOT_DIRECTORY_HOLD')
    for q in (path,path.parent):
        if q.is_symlink():raise RuntimeError('WORKSPACE_PARENT_SYMLINK_HOLD')


def _atomic_write(path:Path,payload:bytes)->bool:
    _guard_regular(path,required=False)
    if path.exists() and path.read_bytes()==payload:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.parent.is_symlink():raise RuntimeError('OUTPUT_PARENT_SYMLINK_HOLD')
    fd,name=tempfile.mkstemp(prefix='.bg_eet_ru_autofix_',dir=path.parent)
    tmp=Path(name)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        if fingerprint(tmp)!=digest(payload):raise RuntimeError('STAGED_OUTPUT_SHA_MISMATCH')
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()
    return True


def _read_bundle(root:Path)->dict[str,bytes]:
    bundle=root/'trusted_sources.zip'
    _guard_regular(bundle)
    if bundle.stat().st_size>512_000:raise RuntimeError('TRUSTED_BUNDLE_OVERSIZE_HOLD')
    if fingerprint(bundle)!=TRUSTED_BUNDLE_SHA256:raise RuntimeError('TRUSTED_BUNDLE_SHA_MISMATCH_HOLD')
    with zipfile.ZipFile(bundle) as z:
        members=z.infolist()
        names=[x.filename for x in members]
        if len(members)<10 or len(members)>24 or len(set(names))!=len(names):
            raise RuntimeError('TRUSTED_BUNDLE_MEMBER_COUNT_HOLD')
        if z.testzip() is not None:raise RuntimeError('TRUSTED_BUNDLE_CRC_HOLD')
        result={}
        for entry in members:
            name=entry.filename
            if not name.endswith('.py') or name!=Path(name).name or entry.is_dir() or entry.file_size>150_000:
                raise RuntimeError('TRUSTED_BUNDLE_PATH_OR_SIZE_HOLD')
            if (entry.external_attr>>16)&0o170000 == 0o120000:
                raise RuntimeError('TRUSTED_BUNDLE_SYMLINK_HOLD')
            result[name]=z.read(name)
        if SUITE_RUNNER not in result:raise RuntimeError('TRUSTED_BUNDLE_RUNNER_MISSING_HOLD')
        return result


def _verify_archive(archive:Path,game:Path|None)->dict:
    _guard_regular(archive)
    if game is not None:
        ra=archive.resolve(strict=False);rg=game.resolve(strict=False)
        if ra==rg or rg in ra.parents:raise RuntimeError('SOURCE_ARCHIVE_INSIDE_GAME_HOLD')
    if archive.stat().st_size>12_000_000:raise RuntimeError('SOURCE_ARCHIVE_OVERSIZE_HOLD')
    actual=fingerprint(archive)
    if actual!=SOURCE_ARCHIVE_SHA256:
        raise RuntimeError('SOURCE_ARCHIVE_SHA_MISMATCH_HOLD')
    with zipfile.ZipFile(archive) as z:
        info=z.infolist()
        if len(info)!=129 or len({x.filename for x in info})!=len(info):
            raise RuntimeError('SOURCE_ARCHIVE_MEMBER_COUNT_HOLD')
        if sum(x.file_size for x in info)>35_000_000:raise RuntimeError('SOURCE_ARCHIVE_EXPANSION_HOLD')
        if z.testzip() is not None:raise RuntimeError('SOURCE_ARCHIVE_CRC_HOLD')
    return {'sha256':actual,'entries':129,'status':'VERIFIED_PINNED_INPUT'}


def _quarantine(path:Path,backupdir:Path,tag:str)->str:
    _guard_regular(path)
    if backupdir.is_symlink() or (backupdir.exists() and not backupdir.is_dir()):
        raise RuntimeError('QUARANTINE_DIRECTORY_UNSAFE_HOLD')
    sha=fingerprint(path)
    backupdir.mkdir(parents=True,exist_ok=True)
    dst=backupdir/f'{path.name}.{sha[:16]}.{tag}.bad'
    _guard_regular(dst,required=False)
    if not dst.exists():
        _atomic_write(dst,path.read_bytes())
    if fingerprint(dst)!=sha:raise RuntimeError('QUARANTINE_VERIFY_FAILED')
    return str(dst)


def _repair_modules(workdir:Path,sources:dict[str,bytes],allow_repair:bool)->dict:
    events=[]
    backupdir=workdir/'quarantine'
    checked=0
    for name, trusted in sorted(sources.items()):
        target=workdir/name
        _guard_regular(target,required=False)
        checked+=1
        if target.exists() and fingerprint(target)==digest(trusted):continue
        event={'module':name,'issue':'MISSING' if not target.exists() else 'SOURCE_DRIFT',
               'action':'HOLD' if not allow_repair else 'RESTORE_TRUSTED_PIN'}
        if not allow_repair:raise RuntimeError('SOURCE_REPAIR_NOT_AUTHORIZED:'+name)
        if target.exists():event['quarantine']=_quarantine(target,backupdir,'source')
        _atomic_write(target,trusted)
        if fingerprint(target)!=digest(trusted):raise RuntimeError('RESTORED_MODULE_SHA_MISMATCH:'+name)
        events.append(event)
    return {'checked':checked,'restored':len(events),'events':events}


def _verify_suite_result(result:dict,expected_sha:str)->None:
    if result.get('archive_sha256')!=expected_sha:raise RuntimeError('RUNNER_INPUT_SHA_DIVERGED')
    if result.get('failed_stages'):raise RuntimeError('SUITE_STAGE_FAILURE_HOLD:'+','.join(result['failed_stages']))
    stages=result.get('stages')
    if not isinstance(stages,dict) or set(stages)!=set(EXPECTED_STAGES):
        raise RuntimeError('SUITE_STAGES_INCOMPLETE_HOLD')
    if any(v.get('status')!='PASS' for v in stages.values()):
        raise RuntimeError('SUITE_STAGE_NONPASS_HOLD')
    if result.get('total_source_checks')!=735:
        raise RuntimeError('SUITE_CASE_COUNT_UNEXPECTED_HOLD')
    if result.get('status')!='SOURCE_SUITE_PASS_GAMEPLAY_HOLD':
        raise RuntimeError('SUITE_FALSE_PASS_HOLD')
    if result.get('game_files_written')!=0 or result.get('new_hook_installed') is not False:
        raise RuntimeError('SUITE_CLAIMS_GAME_MUTATION_HOLD')
    if result.get('runtime_proven') is not False or result.get('gameplay_verified') is not False:
        raise RuntimeError('SUITE_FALSE_GAMEPLAY_CLAIM_HOLD')


def _run_suite(workdir:Path,archive:Path,sha:str,timeout:int)->dict:
    output=workdir/'.stage_result.json'
    if output.exists():
        _guard_regular(output)
        output.unlink()  # Own ephemeral stage output only, never a user file.
    cmd=[sys.executable,'-I','-B',str(workdir/SUITE_RUNNER),str(archive),'--output',str(output)]
    completed=subprocess.run(cmd,cwd=str(workdir),capture_output=True,text=True,
                             timeout=timeout,stdin=subprocess.DEVNULL,check=False)
    if not output.is_file():raise RuntimeError('RUNNER_NO_RESULT_HOLD:'+completed.stderr[-300:])
    data=json.loads(output.read_text(encoding='utf8'))
    if completed.returncode!=0:
        raise RuntimeError('RUNNER_EXIT_NONZERO_HOLD:'+str(completed.returncode)+':'+str(data.get('failed_stages')))
    _verify_suite_result(data,sha)
    return data


def _write_output_zip(src:Path,dest:Path,report:dict)->bool:
    _guard_regular(src)
    if src.resolve(strict=False)==dest.resolve(strict=False):
        raise RuntimeError('OUTPUT_MUST_NOT_REPLACE_PINNED_INPUT')
    if dest.is_symlink() or dest.parent.is_symlink():raise RuntimeError('OUTPUT_ZIP_SYMLINK_HOLD')
    dest.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True).encode('utf8')
    fd,name=tempfile.mkstemp(prefix='.bg_eet_ru_report_',suffix='.zip',dir=dest.parent)
    tmp=Path(name);os.close(fd)
    try:
        with zipfile.ZipFile(src) as inp,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as out:
            for entry in inp.infolist():
                if entry.filename==REPORT_ENTRY:continue
                out.writestr(entry,inp.read(entry))
            info=zipfile.ZipInfo(REPORT_ENTRY,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16
            out.writestr(info,body)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None or z.namelist().count(REPORT_ENTRY)!=1:
                raise RuntimeError('OUTPUT_ZIP_VERIFY_HOLD')
            if json.loads(z.read(REPORT_ENTRY))!=report:raise RuntimeError('OUTPUT_ZIP_REPORT_MISMATCH')
        if dest.exists():
            _guard_regular(dest)
            if fingerprint(dest)==fingerprint(tmp):return False
        os.replace(tmp,dest)
        return True
    finally:
        if tmp.exists():tmp.unlink()


def run(archive:Path,workdir:Path,bundle_root:Path,output_zip:Path|None=None,
        game_root:Path|None=None,timeout:int=120,allow_repair:bool=True)->dict:
    archive=Path(archive).absolute();workdir=Path(workdir).absolute()
    bundle_root=Path(bundle_root).absolute()
    # The user's normal Windows EET installation is protected by default.
    game=Path(game_root).absolute() if game_root else (
        Path(r'C:\Games\BG_EET_FOXX_NEW') if os.name=='nt' else None)
    if timeout<1 or timeout>300:raise RuntimeError('TIMEOUT_OUT_OF_BOUNDS')
    _guard_dir(workdir,game)
    if output_zip is not None:
        output_zip=Path(output_zip).absolute()
        _guard_dir(output_zip.parent,game)
        if output_zip==archive:raise RuntimeError('REPORT_WOULD_OVERWRITE_INPUT')
    if workdir==bundle_root or workdir==archive.parent:raise RuntimeError('WORKSPACE_MUST_BE_SEPARATE')
    if archive==workdir or workdir in archive.parents:raise RuntimeError('SOURCE_PATH_UNSAFE')
    # Verify trust anchors before creating any persistent files.
    bundle=_read_bundle(bundle_root)
    input_info=_verify_archive(archive,game)
    workdir.mkdir(parents=True,exist_ok=True)
    state=workdir/'.autofix_state.json'
    prior=None
    if state.exists():
        _guard_regular(state)
        try:prior=json.loads(state.read_text(encoding='utf8'))
        except (ValueError,UnicodeError):
            _quarantine(state,workdir/'quarantine','journal')
            prior={'phase':'CORRUPT_PREVIOUS_STATE'}
    def checkpoint(phase:str,detail:dict|None=None):
        _atomic_write(state,json.dumps({'schema':'BG_EET_RU_AUTOFIX_STATE_V1','phase':phase,
               'input_sha256':input_info['sha256'],'details':detail or {}},sort_keys=True).encode('utf8'))
    checkpoint('STARTED',{'recovered_previous_phase':prior.get('phase') if isinstance(prior,dict) else None})
    repairs=_repair_modules(workdir,bundle,allow_repair)
    checkpoint('REPAIRED',repairs)
    retry_count=0
    try:
        for attempt in range(2):
            try:
                suite=_run_suite(workdir,archive,input_info['sha256'],timeout)
                break
            except Exception:
                # A single bounded retry is allowed only when *trusted source drift*
                # is independently observed. Unknown test failures remain HOLD.
                dirty=[name for name,reference in bundle.items()
                       if not (workdir/name).is_file() or
                       (workdir/name).is_symlink() or fingerprint(workdir/name)!=digest(reference)]
                if not dirty or attempt>=1:raise
                retry_count+=1
                fixed=_repair_modules(workdir,bundle,allow_repair)
                repairs['restored']+=fixed['restored']
                repairs['events'].extend(fixed['events'])
                checkpoint('REPAIRED_DURING_RUN',{'dirty_modules':dirty,'repair':fixed})
        # An archival input change or trusted bundle drift between precheck and
        # report is never silently repaired; the old evidence must be redone.
        if fingerprint(archive)!=input_info['sha256']:
            raise RuntimeError('SOURCE_ARCHIVE_MUTATED_DURING_RUN_HOLD')
        if fingerprint(bundle_root/'trusted_sources.zip')!=TRUSTED_BUNDLE_SHA256:
            raise RuntimeError('TRUSTED_BUNDLE_MUTATED_DURING_RUN_HOLD')
    except Exception as err:
        checkpoint('HOLD',{'error':type(err).__name__+':'+str(err)[:400]})
        raise
    report={'schema':'BG_EET_RU_ONE_RUN_AUTOFIX_RESEARCH_V1','version':BOT_VERSION,
            'status':'SOURCE_PASS_REPAIRED_GAMEPLAY_HOLD' if repairs['restored'] else 'SOURCE_PASS_GAMEPLAY_HOLD',
            'source_archive_sha256':input_info['sha256'],
            'trusted_bundle_sha256':TRUSTED_BUNDLE_SHA256,
            'modules_checked':repairs['checked'],'modules_repaired':repairs['restored'],
            'bounded_stage_retries':retry_count,
            'repairs':repairs['events'],'stages':suite['stages'],
            'checks_passed':suite['total_source_checks'],
            'game_files_written':0,'native_hooks_installed':False,
            'runtime_verified':False,'gameplay_verified':False,
            'remaining_blockers':suite['critical_unverified']}
    output_info={}
    report['output_zip_recovered']=False
    if output_zip:
        if output_zip.is_symlink():raise RuntimeError('OUTPUT_ZIP_SYMLINK_HOLD')
        _guard_regular(output_zip,required=False)
        if output_zip.exists():
            owned=(isinstance(prior,dict) and prior.get('phase')=='COMPLETED'
                   and prior.get('details',{}).get('output_zip_path')==str(output_zip)
                   and isinstance(prior.get('details',{}).get('output_zip_sha256'),str))
            if not owned:raise RuntimeError('OUTPUT_EXISTS_NOT_OWNED_HOLD')
            prior_sha=prior['details']['output_zip_sha256']
            if fingerprint(output_zip)!=prior_sha:
                # Only a previously recorded, bot-owned output is recoverable.
                # Keep altered bytes rather than silently destroying them.
                _quarantine(output_zip,workdir/'quarantine','report')
                report['output_zip_recovered']=True
        _write_output_zip(archive,output_zip,report)
        output_info={'output_zip_path':str(output_zip),'output_zip_sha256':fingerprint(output_zip)}
        report['output_zip_path']=str(output_zip)
    checkpoint('COMPLETED',{'status':report['status'],'checks_passed':report['checks_passed'],**output_info})
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description='BG EET RU one-run pinned-source auto-repair (no game edits)')
    p.add_argument('archive',type=Path)
    p.add_argument('--workspace',type=Path,default=Path(__file__).parent/'.autofix_workspace')
    p.add_argument('--bundle-root',type=Path,default=Path(__file__).parent)
    p.add_argument('--output-zip',type=Path)
    p.add_argument('--game-root',type=Path)
    p.add_argument('--timeout',type=int,default=120)
    a=p.parse_args(argv)
    try:
        result=run(a.archive,a.workspace,a.bundle_root,a.output_zip,a.game_root,a.timeout)
        print(json.dumps({'status':result['status'],'checks_passed':result['checks_passed'],
                'modules_repaired':result['modules_repaired'],'game_files_written':0},ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({'status':'AUTOFIX_FAIL_CLOSED_HOLD','error':type(exc).__name__+':'+str(exc)[:450],
               'game_files_written':0,'native_hooks_installed':False},ensure_ascii=False))
        return 2

if __name__=='__main__':
    sys.exit(main())
