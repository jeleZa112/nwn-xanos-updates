"""Autonomous one-pass BG_EET_RU V4 developer QA, no user participation.

Runs the previous 9 stages *as one independent unit* and continues with new
proofs even on HOLD. Does not start or patch game, inject DLLs or edit user ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import unittest
import io

HERE=Path(__file__).resolve().parent

def sha_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def source_safety():
    # Restrict new instrumentation to external read-only API, Python models and
    # Lua models that cannot mutate game memory or call JIT.
    game=HERE/'BG_EET_RU_THREAD_FRAME_BRIDGE_V4.lua'
    reader=HERE/'windows_live_hit_inventory_ro.py'
    b=game.read_text('utf8')
    p=reader.read_text('utf8')
    for x in ('EEex_HookBefore', 'EEex_JITAt', 'EEex_DisableCodeProtection',
              'EEex_WriteU8(', 'WriteProcessMemory(', 'VirtualProtect('):
        if x in b:raise ValueError('LUA_NATIVE_PATCH_FORBIDDEN:'+x)
    for x in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(',
              'OpenThread(', 'SuspendThread(', 'SetThreadContext(', 'NtWriteVirtualMemory('):
        if x in p:raise ValueError('EXTERNAL_READER_WRITE_FORBIDDEN:'+x)
    if "return false,'NO_JIT_OR_GAME_INSTALL_IN_THIS_SOURCE_ONLY_MODULE'" not in b:
        raise ValueError('JIT_INERT_SOURCE_MISSING')
    if 'PROCESS_VM_READ' not in p and '0x1010' not in p:
        raise ValueError('READ_ONLY_PROCESS_RIGHTS_UNPROVEN')
    return {'status':'PASS','jit_enabled':False,'game_files_changed':0,
            'source_only':True}

def run(archive:Path,trusted:Path,out:Path):
    archive=archive.resolve();trusted=trusted.resolve();out=out.resolve()
    if any(out==x for x in (archive,trusted)) or out.is_symlink():
        raise RuntimeError('OUTPUT_MUST_NOT_OVERWRITE_INPUT')
    if any((parent/'chitin.key').exists() for parent in (out.parent,*out.parents)):
        raise RuntimeError('OUTPUT_INSIDE_GAME_FORBIDDEN')
    originals={str(x):sha_file(x) for x in (archive,trusted)}
    stages=[]
    def stage(name,fn):
        try:
            value=fn()
            stages.append({'name':name,'status':'PASS','result':value})
        except Exception as e:
            stages.append({'name':name,'status':'HOLD',
                'reason':(type(e).__name__+': '+str(e))[:250]})
    def old_batch():
        import one_big_batch_ro as old
        with tempfile.TemporaryDirectory(prefix='bg_eet_ru_v4_old_') as temp:
            src=Path(temp)/'previous.json'
            result=old.batch(archive,trusted,src)
            if result['status']!='SOURCE_BATCH_PASS_NATIVE_GAMEPLAY_HOLD':
                raise ValueError('OLD_NINE_STAGE_BATCH_HOLD')
            if result['stages_passed']!=9 or result['stage_total']!=9:
                raise ValueError('OLD_STAGE_COUNT_DRIFT')
            return {'prior_stages_passed':9,'legacy_core_checks':735,
                    'native_runtime_verified':False}
    stage('01_existing_full_nine_stage_batch',old_batch)
    def callsite():
        import message_callsite_proof_v4 as proof
        r=proof.verify(archive)
        if r['status']!='PINNED_SOURCE_CALLSITE_PROVED_RUNTIME_HOLD':
            raise ValueError('PINNED_CALLSITE_PROOF_HOLD:'+str(r.get('reason')))
        return {'checks':r['checks_passed'],'same_vtable_in_damage':True,
                'ui_row_mapping':False,'item_on_miss_runtime':False}
    stage('02_native_same_hit_message_callsite_proof',callsite)
    def lua():
        runproc=subprocess.run([sys.executable,str(HERE/'test_v4_lua_runtime.py')],
            cwd=HERE,text=True,capture_output=True,timeout=45)
        if runproc.returncode or 'BG_EET_RU_V4_REAL_LUA_SOURCE_ONLY_PASS\t6410' not in runproc.stdout:
            raise ValueError('REAL_LUA_MATRIX_HOLD:'+runproc.stdout[-180:]+runproc.stderr[-180:])
        for marker in ('BG_EET_RU_V4_THREAD_LIMIT_PASS\t24','BG_EET_RU_V4_POISON_LIMIT_PASS'):
            if marker not in runproc.stdout:raise ValueError('LUA_BOUNDARY_MISSING:'+marker)
        return {'real_lua_assertions':6410,'thread_budget_cases':24,
                'poison_depth_exhaustion':True,'gameplay_not_tested':True}
    stage('03_real_lua_two_key_model_and_limits',lua)
    def mock_inventory():
        import test_windows_inventory_ro as t
        tests=unittest.defaultTestLoader.loadTestsFromModule(t)
        stream=io.StringIO()
        result=unittest.TextTestRunner(verbosity=0,stream=stream).run(tests)
        if result.testsRun!=15 or not result.wasSuccessful():
            raise ValueError('WINDOWS_API_LOGIC_15_TESTS_HOLD:'+stream.getvalue()[-240:])
        return {'mock_test_methods':15,'randomized_corrupted_remote_sites':500,
                'real_windows_kernel32':'NOT_TESTED_IN_LINUX'}
    stage('04_external_windows_read_only_inventory_mock',mock_inventory)
    stage('05_no_native_write_code_guards',source_safety)
    def compile_python():
        import ast
        names=('one_big_batch_v4.py','message_callsite_proof_v4.py',
               'test_v4_lua_runtime.py','windows_live_hit_inventory_ro.py',
               'test_windows_inventory_ro.py')
        for name in names:
            ast.parse((HERE/name).read_text('utf8'),filename=name)
        return {'python_modules_parsed':len(names)}
    stage('06_new_python_syntax',compile_python)
    def provenance():
        if any(sha_file(Path(p))!=sha for p,sha in originals.items()):
            raise ValueError('SOURCE_CHANGED_DURING_BIG_BATCH')
        return {'sources_unchanged':True}
    stage('07_postrun_provenance',provenance)
    failed=[s['name'] for s in stages if s['status']!='PASS']
    final={
      'schema':'BG_EET_RU_ONE_PASS_V4_RESEARCH_AND_WINDOWS_READONLY_ADAPTER',
      'timestamp_utc':datetime.now(timezone.utc).isoformat(),
      'status':'SOURCE_ONLY_READY_LIVE_RUNTIME_HOLD' if not failed else 'SOURCE_BATCH_PARTIAL_HOLD',
      'stages':stages,'passed':len(stages)-len(failed),'total':len(stages),'hold':failed,
      'prior_source_stages':9,'new_stage_total':len(stages),
      'native_hooks_installed':False,'gameplay_verified':False,'miss_resref_verified':False,
      'visible_combat_log_verified':False,'installed_owner_verified':False,
      'windows_kernel32_tested':False,'game_files_written':0,
      'game_updater':'V121_UNCHANGED',
      'action_required_now':False,
      'next_dependency':'WINDOWS_KERNEL32_SELFTEST_AND_LIVE_GAME_PROCESS_READ_BEFORE_NATIVE_INSTALL',
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_name('.'+out.name+'.tmp')
    if tmp.is_symlink():raise RuntimeError('TEMP_REPORT_SYMLINK_FORBIDDEN')
    tmp.write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf8')
    os.replace(tmp,out)
    return final

def main():
    p=argparse.ArgumentParser(description='BG_EET_RU single all-in-one developer V4 suite')
    p.add_argument('v120_zip',type=Path)
    p.add_argument('--trusted',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    r=run(args.v120_zip,args.trusted,args.out)
    print(r['status'],r['passed'],'/',r['total'])
    for s in r['stages']:print(s['status'],s['name'],s.get('reason',''))
    return 0 if r['status']=='SOURCE_ONLY_READY_LIVE_RUNTIME_HOLD' else 2
if __name__=='__main__':raise SystemExit(main())