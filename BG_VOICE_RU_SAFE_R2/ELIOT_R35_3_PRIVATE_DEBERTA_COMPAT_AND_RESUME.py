# -*- coding: utf-8 -*-
"""ELIOT R35.3: repair *isolated* RUAccent tokenizer dependencies, reuse existing 359MB ONNX, resume R35.1.
No changes to BG_VOICE_UPDATE.cmd, existing WAVs, game, voice refs, model cache.
"""
from __future__ import annotations
import base64, gzip, hashlib, importlib.metadata as metadata, json, os, pathlib, shutil, subprocess, sys, time, zipfile
from datetime import datetime, timezone

PRIOR_351_SHA = "154b4c3f08ee7d9fafa6f185ea69693ec13f137a649dcbac0045bdf8a5df5749"
PRIOR_351_B64 = "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"
PINS = {"transformers":"4.57.3", "tokenizers":"0.22.1", "huggingface-hub":"0.36.0"}

def sha(b): return hashlib.sha256(b).hexdigest()

def load_verified_attestation():
    data=gzip.decompress(base64.b64decode(PRIOR_351_B64,validate=True))
    if sha(data)!=PRIOR_351_SHA: raise RuntimeError('EMBEDDED_R35_1_SOURCE_SHA_INVALID')
    ns={'__name__':'r351_attest_only','__file__':'[verified R35.1]'}
    exec(compile(data.decode('utf-8'),'r351_attest_only.py','exec'),ns)
    return ns

def attest_updater(cmd):
    if not cmd.is_file() or cmd.is_symlink() or cmd.parent.is_symlink():raise RuntimeError('ONE_UPDATER_PATH_HOLD')
    ns=load_verified_attestation()
    r35=ns['original_r35']()
    state, old, new=ns['verify_patched_or_original'](cmd.read_bytes(),r35)
    if state!='already-patched':raise RuntimeError('R35_1_NOT_CURRENT_NO_MODIFICATIONS')
    if sha(new)!=sha(cmd.read_bytes()):raise RuntimeError('UPDATER_CONCURRENT_CHANGE_HOLD')
    print('ELIOT_R35_3_R35_1_ATTESTED',sha(new),flush=True)
    return sha(new)

def installed(venv_python):
    program='import importlib.metadata as md,json;print(json.dumps({k:md.version(k) for k in '+repr(list(PINS))+ '}))'
    r=subprocess.run([str(venv_python),'-c',program],capture_output=True,text=True)
    if r.returncode:raise RuntimeError('PRIVATE_VENV_PACKAGES_MISSING '+r.stderr[-280:])
    return json.loads(r.stdout.strip().splitlines()[-1])

def sitepath(venv):
    p=venv/'Lib'/'site-packages'
    if not p.is_dir() or p.is_symlink():raise RuntimeError('PRIVATE_SITE_PACKAGES_MISSING')
    return p

def pkg_paths(site):
    names=[]
    for pkg in ('transformers','tokenizers','huggingface_hub'):
        names.append(site/pkg)
    for pat in ('transformers-*.dist-info','tokenizers-*.dist-info','huggingface_hub-*.dist-info'):
        names += list(site.glob(pat))
    return sorted(set(p for p in names if p.exists()),key=str)

def create_backup(site, dest,versions):
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise RuntimeError('BACKUP_COLLISION_HOLD')
    items=pkg_paths(site)
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        z.writestr('R35_3_MANIFEST.json',json.dumps({'versions':versions,'paths':[p.name for p in items],'created':datetime.now(timezone.utc).isoformat()},ensure_ascii=False))
        for item in items:
            if item.is_symlink():raise RuntimeError('PRIVATE_DEPENDENCY_SYMLINK_HOLD '+item.name)
            if item.is_file():z.write(item,item.name)
            else:
                for f in item.rglob('*'):
                    if f.is_symlink():raise RuntimeError('PRIVATE_DEPENDENCY_SYMLINK_HOLD '+str(f))
                    if f.is_file():z.write(f, f.relative_to(site).as_posix())
    with zipfile.ZipFile(dest) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('BACKUP_CRC_FAILED '+bad)
    print('ELIOT_R35_3_PRIVATE_DEPENDENCY_BACKUP',dest,flush=True)

def repair_deps(venv,root):
    exe=venv/'Scripts'/'python.exe'
    if not exe.is_file() or exe.is_symlink() or not (venv/'pyvenv.cfg').is_file():raise RuntimeError('R35_TEXT_ONLY_VENV_NOT_FOUND')
    current=installed(exe)
    print('ELIOT_R35_3_PRIVATE_BEFORE',current,flush=True)
    if all(current.get(k)==v for k,v in PINS.items()):
        print('ELIOT_R35_3_PINS_ALREADY_OK',flush=True)
        return exe
    wheels=root/'ELIOT_R35_3_WHEEL_CACHE'
    if wheels.is_symlink():raise RuntimeError('WHEEL_CACHE_SYMLINK_HOLD')
    wheels.mkdir(parents=True,exist_ok=True)
    requested=[f'{k}=={v}' for k,v in PINS.items()]
    common=[str(exe),'-m','pip','--disable-pip-version-check']
    print('ELIOT_R35_3_WHEEL_DOWNLOAD_PREPARE',requested,flush=True)
    cmd=common+['download','--only-binary=:all:','--dest',str(wheels),'--no-input']+requested
    r=subprocess.run(cmd,timeout=900)
    if r.returncode:raise RuntimeError('WHEEL_DOWNLOAD_HOLD_KEEP_PRIVATE_VENV_AS_IS')
    site=sitepath(venv)
    backup=root/'ELIOT_R35_3_DEPENDENCY_BACKUPS'/('PRIVATE_PACKAGES_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+str(os.getpid())+'.zip')
    create_backup(site,backup,current)
    print('ELIOT_R35_3_INSTALL_PINNED_WHEELS_ONLY',flush=True)
    r=subprocess.run(common+['install','--no-index','--find-links',str(wheels),'--no-input']+requested,timeout=600)
    if r.returncode:raise RuntimeError('PRIVATE_PIP_INSTALL_HOLD_BACKUP '+str(backup))
    actual=installed(exe)
    if any(actual.get(k)!=v for k,v in PINS.items()):raise RuntimeError('PRIVATE_PIN_ATTESTATION_HOLD '+str(actual))
    print('ELIOT_R35_3_PINNED_DEPENDENCIES_PASS',actual,flush=True)
    return exe

def tokenizer_check(venv_py,models):
    p=models/'nn'/'nn_omograph'/'turbo2'
    model=p/'model.onnx'
    if not model.is_file() or model.stat().st_size!=359306923:raise RuntimeError('ONNX_NOT_READY_KEEP_CACHE')
    code="""from transformers import AutoTokenizer
import sys
p=sys.argv[1]
t=AutoTokenizer.from_pretrained(p,local_files_only=True,use_fast=True)
r=t('Хребта мира и головы гоблинов')
assert len(r['input_ids'])>4
print('ELIOT_R35_3_DEBERTA_TOKENIZER_REAL_OK',type(t).__name__,len(r['input_ids']),flush=True)
"""
    env=os.environ.copy();env['HF_HUB_OFFLINE']='1';env['TRANSFORMERS_OFFLINE']='1'
    r=subprocess.run([str(venv_py),'-c',code,str(p)],env=env)
    if r.returncode:raise RuntimeError('REAL_LOCAL_TOKENIZER_HOLD_NO_SYNTHESIS')

def run_r351_existing(cmd,flag):
    embed=('import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
           'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],p,"exec"),'
           '{"__name__":"__main__","__file__":p})')
    env=os.environ.copy();env.update({'ELIOT_R35_1_ONLINE_MODEL_SETUP':'1','PYTHONDONTWRITEBYTECODE':'1','HF_HUB_DISABLE_TELEMETRY':'1'})
    r=subprocess.run([sys.executable,'-u','-c',embed,str(cmd),flag],env=env,cwd=str(cmd.parent))
    return r.returncode

def selftest():
    ns=load_verified_attestation()
    ns['embedded_check_without_writes']()
    assert all(PINS.values())
    assert sha(b'test')=='9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
    print('ELIOT_R35_3_SELFTEST_PASS source attestation, no-updater-edits, pinned isolated environment',flush=True)

def main():
    selftest()
    if '--selftest-only' in sys.argv:return 0
    if os.name!='nt' or sys.version_info[:2]!=(3,11):raise RuntimeError('WINDOWS_PY311_REQUIRED')
    home=pathlib.Path.home()
    root=home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'
    cmd=home/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'/'BG_VOICE_UPDATE.cmd'
    old_sha=attest_updater(cmd)
    venv=root/'ELIOT_R35_TEXT_ONLY_VENV'
    exe=repair_deps(venv,root)
    model_dir=root/'ELIOT_R35_MOVIE_G08_DUAL_METHOD'/'RUACCENT_MODELS'
    tokenizer_check(exe,model_dir)
    if sha(cmd.read_bytes())!=old_sha:raise RuntimeError('ONE_UPDATER_CHANGED_DURING_REPAIR_HOLD')
    for flag in ('--eliot-r35-selftest','--eliot-r35-preflight','--eliot-r35-stresscheck'):
        rc=run_r351_existing(cmd,flag)
        if rc:raise RuntimeError('R35_3_HOLD '+flag+' RC='+str(rc)+' NO_SYNTHESIS')
    print('ELIOT_R35_3_STRESS_GATE_PASSED: starting only three G08 pilot WAVs',flush=True)
    rc=run_r351_existing(cmd,'--eliot-r35-generate')
    if rc:raise RuntimeError('R35_3_GENERATION_HOLD RC='+str(rc)+' NO_AUTO_INSTALL')
    print('ELIOT_R35_3_SUCCESS: 3 G08 preview WAVs in ONE SEND_TO_CHATGPT_BG_VOICE_RU.zip',flush=True)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('ELIOT_R35_3_HOLD',type(exc).__name__,str(exc)[:440],flush=True)
        raise SystemExit(2)
