"""Single source-only QA entrypoint: self-contained V120 archive suite + corrected pilot.

This is a development helper, not a Windows updater. It writes only a chosen
external report JSON, never modifies the user archive, game, or EEex files.
"""
from __future__ import annotations
import argparse, contextlib, hashlib, io, json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path
from pilot_static_gates import verify

HERE=Path(__file__).resolve().parent
V120_SHA='08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015'
TRUSTED_SHA='7622bfdec1f77e44a307c0cda3e73c86d143a024b87d4ad0f359897c89a74124'

def sha(path:Path):return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(archive:Path, trusted:Path, lua:Path, extra_tests:bool=True):
    archive=Path(archive); trusted=Path(trusted); lua=Path(lua)
    checks=[]
    def stage(name, fn):
        try:
            payload=fn()
            status=payload.get('status','PASS')
            checks.append({'name':name,'status':status,'result':payload})
        except Exception as exc:
            checks.append({'name':name,'status':'HOLD','error':type(exc).__name__+':'+str(exc)[:200]})
    def trusted_source_suite():
        if sha(archive)!=V120_SHA:raise ValueError('SOURCE_ARCHIVE_MISMATCH')
        if sha(trusted)!=TRUSTED_SHA:raise ValueError('TRUSTED_SOURCE_BUNDLE_MISMATCH')
        with tempfile.TemporaryDirectory(prefix='bg_eet_ru_pilot_suite_') as tmp:
            root=Path(tmp)
            with zipfile.ZipFile(trusted) as z:
                if z.testzip() is not None:raise ValueError('TRUSTED_ARCHIVE_CRC_FAILED')
                names=z.namelist()
                if len(names)!=14 or len(set(names))!=len(names):raise ValueError('TRUSTED_MODULES_COUNT_MISMATCH')
                for name in names:
                    if Path(name).name!=name or not name.endswith('.py'):raise ValueError('UNSAFE_TRUSTED_MEMBER')
                    (root/name).write_bytes(z.read(name))
            child=subprocess.run([sys.executable,str(root/'one_pass_offline_validation.py'),str(archive)],cwd=root,
                                 capture_output=True,text=True,timeout=90)
            if child.returncode:raise RuntimeError('SOURCE_SUITE_FAILED_RC_'+str(child.returncode))
            try:r=json.loads(child.stdout)
            except json.JSONDecodeError as err:raise RuntimeError('SOURCE_SUITE_NOT_JSON') from err
            if r['status']!='SOURCE_SUITE_PASS_GAMEPLAY_HOLD' or r['total_source_checks']!=735:
                raise RuntimeError('FULL_SOURCE_SUITE_NOT_735_PASS')
            return {'status':'PASS','passed':735,'stages':len(r['stages']),'gameplay_verified':False}
    stage('base_735_source_suite',trusted_source_suite)
    stage('corrected_site_and_lua_source',lambda:verify(archive,lua))
    if extra_tests:
        def real_lua_callbacks():
            child=subprocess.run([sys.executable,str(HERE/'test_lua_runtime.py')],
                 cwd=HERE,capture_output=True,text=True,timeout=15)
            if child.returncode!=0 or 'LUA_SOURCE_RUNTIME_PASS\t43' not in child.stdout:
                raise RuntimeError('LUA_RUNTIME_CALLBACKS_NOT_PASS:'+child.stderr[-150:])
            return {'status':'PASS','assertions':43,'engine':'Lua 5.4 shared library',
                    'scope':'LUA_CALLBACK_LOGIC_ONLY_NOT_EEEX_OR_NATIVE_JIT'}
        stage('real_lua_callback_contract',real_lua_callbacks)
    if extra_tests:
        def adversarial():
            env={**os.environ,'BG_EET_RU_V120_ZIP':str(archive)}
            ch=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_pilot_source.py','-v'],
                              cwd=HERE,env=env,capture_output=True,text=True,timeout=40)
            if ch.returncode or 'Ran 7 tests' not in ch.stderr or not ch.stderr.rstrip().endswith('OK'):
                raise RuntimeError('ADVERSARIAL_TESTS_FAIL')
            return {'status':'PASS','test_methods':7,'negative_cases':'all pinned site mutations + 9 lua tamper probes + ZIP mismatch'}
        stage('adversarial_fail_closed',adversarial)
    fail=[x['name'] for x in checks if x['status'] not in ('PASS','SOURCE_PASS_RUNTIME_HOLD')]
    return {'schema':'BG_EET_RU_NATIVE_PILOT_ONE_PASS_SOURCE_GATE_V1',
      'status':'SOURCE_PASS_RUNTIME_HOLD' if not fail else 'SOURCE_HOLD',
      'stages':checks,'failed_stages':fail,'game_files_written':0,'native_hooks_installed':False,
      'runtime_ABI_proven':False,'gameplay_verified':False,
      'release_version_unchanged':121,
      'source_verified_sha256':sha(lua),
      'only_user_facing_updater':'BG_EET_RU_UPDATE.cmd'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('archive',type=Path)
    p.add_argument('--trusted',type=Path,required=True)
    p.add_argument('--lua',type=Path,default=HERE/'BG_EET_RU_HIT_PILOT_DRAFT.lua')
    p.add_argument('--out',type=Path,default=HERE/'ONE_PASS_NATIVE_PILOT_REPORT.json')
    args=p.parse_args()
    r=audit(args.archive,args.trusted,args.lua)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(r['status'],[(x['name'],x['status']) for x in r['stages']])
    return 0 if r['status']=='SOURCE_PASS_RUNTIME_HOLD' else 2

if __name__=='__main__':raise SystemExit(main())