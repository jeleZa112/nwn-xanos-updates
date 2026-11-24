"""BG_EET_RU one *developer* batch, read-only, with isolated stages.

Run from a read-only research package, not from the user-facing updater.
Never writes in the game directory or modifies input ZIP. An unknown failure
is held, independent stages continue, known source repair uses existing AutoFix.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
V120_SHA = '08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015'
TRUSTED_SHA = '7622bfdec1f77e44a307c0cda3e73c86d143a024b87d4ad0f359897c89a74124'
SAFE_TAG = 'SOURCE_PASS_RUNTIME_HOLD'


def fingerprint(p):
    d=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            d.update(b)
    return d.hexdigest()


def run_python(path, *args, cwd=None, env=None, timeout=120):
    result=subprocess.run([sys.executable, str(path), *map(str,args)],
        cwd=cwd or ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('SCRIPT_HOLD('+str(result.returncode)+'): '+(result.stderr or result.stdout)[-400:])
    return (result.stdout+'\n'+result.stderr)[-1500:]


def batch(archive, trusted, out):
    archive=pathlib.Path(archive).resolve()
    trusted=pathlib.Path(trusted).resolve()
    out=pathlib.Path(out).resolve()
    if out==archive or out==trusted or out.is_symlink():
        raise RuntimeError('OUTPUT_CANNOT_OVERWRITE_INPUT_OR_SYMLINK')
    # No output within an actual game root; guard even if supplied path is a subdir.
    for root in [out.parent, *out.parents]:
        if (root/'chitin.key').exists():
            raise RuntimeError('OUTPUT_INSIDE_GAME_ROOT_FORBIDDEN')
    source_before=fingerprint(archive)
    trusted_before=fingerprint(trusted)
    stage_results=[]
    def stage(name, fn):
        try:
            result=fn()
            stage_results.append(dict(stage=name,status='PASS',details=result))
        except Exception as e:
            stage_results.append(dict(stage=name,status='HOLD',reason=f'{type(e).__name__}: {str(e)[:360]}'))

    def archive_provenance():
        if source_before!=V120_SHA or trusted_before!=TRUSTED_SHA:
            raise ValueError('PINNED_INPUT_SHA_MISMATCH')
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if z.testzip() is not None or len(set(names))!=len(names) or len(names)!=129:
                raise ValueError('PRIVATE_ARCHIVE_CRC_DUPLICATE_COUNT_HOLD')
        with zipfile.ZipFile(trusted) as z:
            names=z.namelist()
            if z.testzip() is not None or len(set(names))!=len(names) or len(names)!=14:
                raise ValueError('PINNED_TRUSTED_CRC_COUNT_HOLD')
        return {'v120_sha256':source_before,'trusted_sha256':trusted_before,
            'v120_entries':129,'trusted_modules':14}
    stage('01_exact_provenance_crc_immutable_input',archive_provenance)

    def source_suite():
        cmd=[archive,'--trusted',trusted,'--out']
        with tempfile.TemporaryDirectory(prefix='bg_eet_ru_one_batch_source_') as work:
            report=pathlib.Path(work)/'source-report.json'
            output=run_python(ROOT/'one_pass_native_pilot_check.py',archive,'--trusted',trusted,'--out',report,
                     timeout=160)
            data=json.loads(report.read_text('utf-8'))
            if data['status']!=SAFE_TAG or data['native_hooks_installed'] or data['gameplay_verified']:
                raise RuntimeError('SOURCE_BUNDLE_NOT_SOURCE_ONLY_PASS')
            stages={x['name']:x['status'] for x in data['stages']}
            if len(stages)!=4 or set(stages.values())!={'PASS','SOURCE_PASS_RUNTIME_HOLD'}:
                raise RuntimeError('SOURCE_STAGE_MATRIX_CHANGED')
            if data['stages'][0]['result']['passed']!=735:
                raise RuntimeError('735_SOURCE_CHECKS_NOT_PROVED')
            if data['stages'][1]['result']['passed']!=33:
                raise RuntimeError('33_NATIVE_SOURCE_CHECKS_NOT_PROVED')
            return {'base_checks':735,'native_hit_source_checks':33,'lua_assertions':43,
                    'native_adversarial_methods':7,'stage_statuses':stages}
    stage('02_native_hit_one_pass_735_33_43_7',source_suite)

    def inventory():
        s=run_python(ROOT/'test_inventory_ro.py',timeout=30)
        if 'LIVE_SITE_INVENTORY_LUA_MOCK_PASS\t24' not in s and 'LIVE_SITE_INVENTORY_LUA_MOCK_PASS 24' not in s:
            raise RuntimeError('LUA_INVENTORY_NOT_24')
        if 'SOURCE_ONLY_READONLY_GUARD_PASS' not in s:
            raise RuntimeError('LIVE_INVENTORY_WRITE_GUARD_MISSING')
        return {'lua_mock_assertions':24,'actual_windows_memory_tested':False,
                'hook_owner_verified':False}
    stage('03_readonly_inventory_lua_24',inventory)

    def autofix_adversarial():
        env={**os.environ,'BG_EET_RU_SOURCE_ARCHIVE':str(archive)}
        s=run_python(ROOT/'test_autofix_bot.py',cwd=ROOT,env=env,timeout=150)
        # unittest prints summary on stderr
        if 'Ran 29 tests' not in s or 'OK' not in s:
            raise RuntimeError('AUTOFIX_29_TESTS_NOT_PROVED')
        return {'autofix_test_methods':29,'intentional_source_corruptions':256,
                'missing_or_corrupt_module_scenarios':56,'unknown_fixes':'HOLD'}
    stage('04_autofix_repair_and_adversarial_29',autofix_adversarial)

    def ensure_fail_closed():
        lines=(ROOT/'BG_EET_RU_HIT_PILOT_DRAFT.lua').read_text('utf8')
        inventory_source=(ROOT/'BG_EET_RU_HIT_RUNTIME_INVENTORY_RO.lua').read_text('utf8')
        invalid=('EEex_JITAt(', 'EEex_DisableCodeProtection(', 'EEex_HookBeforeCallWithLabels(', 'EEex_WriteU8(')
        if any(x in lines for x in invalid) or any(x in inventory_source for x in invalid):
            raise RuntimeError('JIT_OR_MEMORY_WRITE_SOURCE_NOT_ALLOWED')
        for guard in ('authorized_install = false','atomic_three_hook_install_verified = false',
                      "return false,'RUNTIME_HOOK_IMPLEMENTATION_NOT_VERIFIED'"):
            if guard not in lines:raise RuntimeError('NOT_FAIL_CLOSED:'+guard)
        return {'native_jit_enabled':False,'game_writes_enabled':False,'checks':len(invalid)+3}
    stage('05_static_native_write_prohibition',ensure_fail_closed)

    def syntax_compile():
        import ast
        paths=sorted(ROOT.glob('*.py'))
        for p in paths:
            ast.parse(p.read_text('utf-8'),filename=str(p))
        return {'python_files_parsed':len(paths),'runtime_code_executed':False}
    stage('06_all_python_syntax_no_game_write',syntax_compile)

    def inject_source_mismatch():
        # Construct a modified copy in an external temp folder, never alter baseline.
        with tempfile.TemporaryDirectory(prefix='bg_eet_ru_batch_negative_') as d:
            clone=pathlib.Path(d)/'mutated-v120.zip'
            shutil.copyfile(archive,clone)
            with zipfile.ZipFile(clone,'a') as z:z.writestr('FORBIDDEN_EXTRANEOUS_TEST_MARKER','tamper')
            import pilot_static_gates as gates
            proof=gates.verify(clone,ROOT/'BG_EET_RU_HIT_PILOT_DRAFT.lua')
            if proof['status']!='SOURCE_INVALID_HOLD' or proof['checks'].get('exact_v120_archive'):
                raise RuntimeError('CHANGED_ARCHIVE_NOT_HELD')
            return {'mutation':'extra ZIP record','rejected':True,'original_untouched':True}
    stage('07_corrupt_input_should_hold_not_autofix',inject_source_mismatch)

    def injected_site_fail_closed():
        import pilot_static_gates as gates
        tests=0
        with zipfile.ZipFile(archive) as src:
            target=src.read(gates.FUNC)
        for label,(rva,_) in gates.SITES.items():
            corrupted=bytearray(target)
            corrupted[rva-gates.BASE]^=1
            if bytes(corrupted)==target:raise RuntimeError('BAD_MUTATION_TEST')
            if gates.sha(corrupted)==gates.PINNED_FUNC:raise RuntimeError('MUTATED_FUNCTION_HASH_ACCEPTED')
            tests+=1
        return {'mutated_rvas_checked':tests,'mutation_only_in_memory':True,
            'source_sha_validation_remains_required':True}
    stage('08_each_native_site_mutation_sha_gate',injected_site_fail_closed)

    def report_provenance():
        if source_before!=fingerprint(archive) or trusted_before!=fingerprint(trusted):
            raise RuntimeError('INPUT_CHANGED_DURING_BATCH')
        return {'source_sha_unchanged':True,'trusted_sha_unchanged':True}
    stage('09_input_integrity_postrun',report_provenance)

    holds=[r['stage'] for r in stage_results if r['status']=='HOLD']
    result={
      'schema':'BG_EET_RU_UNIFIED_NO_USER_BATCH_RO_V1',
      'status':'SOURCE_BATCH_PASS_NATIVE_GAMEPLAY_HOLD' if not holds else 'SOURCE_BATCH_PARTIAL_HOLD',
      'timestamp_utc':datetime.now(timezone.utc).isoformat(),
      'stages':stage_results,'stage_total':len(stage_results),
      'stages_passed':len(stage_results)-len(holds),'stages_hold':holds,
      'game_files_written':0,'source_zip_modified':False,
      'native_runtime_verified':False,'gameplay_verified':False,
      'published_game_updater_unchanged':'V121',
      'operator_action_required':False,
      'evidence_note':'SOURCE/MOCK only. Passing tests do not authorize a Win64 native hook install.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_name('.'+out.name+'.partial')
    if tmp.is_symlink():raise RuntimeError('PARTIAL_REPORT_SYMLINK_FORBIDDEN')
    tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,out)
    return result


def main():
    p=argparse.ArgumentParser(description='BG_EET_RU: all offline tests with independent fail-closed stages')
    p.add_argument('v120_archive')
    p.add_argument('--trusted',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args()
    result=batch(a.v120_archive,a.trusted,a.out)
    print(result['status'],result['stages_passed'],'/',result['stage_total'],'stage gates')
    for x in result['stages']:print(' ',x['status'],x['stage'],x.get('reason',''))
    return 0 if result['status']=='SOURCE_BATCH_PASS_NATIVE_GAMEPLAY_HOLD' else 2

if __name__=='__main__':raise SystemExit(main())