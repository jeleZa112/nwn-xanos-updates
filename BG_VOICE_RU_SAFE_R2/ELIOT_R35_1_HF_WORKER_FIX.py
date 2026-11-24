# -*- coding: utf-8 -*-
# ELIOT R35.1: scoped HF online gate for RUAccent/Accentik workers ONLY.
# Safely patch EXACT installed R35 single updater, with verified backup, then retry.
# No extra updater. No game modifications. No WAV deletion. Does not bypass stress QA.
from __future__ import annotations
import base64, gzip, hashlib, os, sys, pathlib, tempfile, subprocess
from datetime import datetime, timezone

R35_ORIGINAL_SHA = "393a2cf1eb22648970aebfe777ed016b7426b34cc6daa9f94f34f81a33bed9b6"
R35_ORIGINAL_GZ_B64 = (
    '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'

)

def digest(b): return hashlib.sha256(b).hexdigest()

def original_r35():
    data = gzip.decompress(base64.b64decode(''.join(R35_ORIGINAL_GZ_B64), validate=True))
    if digest(data)!=R35_ORIGINAL_SHA:
        raise RuntimeError('R35_ORIGINAL_ATTESTATION_FAILED')
    ns={'__name__':'eliot_r35_reference','__file__':'[embedded_verified_r35_reference]'}
    exec(compile(data.decode('utf-8'),'r35_reference.py','exec'),ns)
    if (ns.get('SOURCE_SHA')!='b1fa9aebb9fdf4d2214769d94fccb425b280e823594fe6f2901ee52a810a2c30' or
        ns.get('ROUTE_SHA')!='7b42429e7c88b741cd5c98f3aed6a616f5441871730908c1ef9c1b74135a33b5'):
        raise RuntimeError('R35_LINEAGE_MISMATCH')
    return ns

NEEDLE=(b"os.environ['HF_HUB_OFFLINE'] = '1'\r\n"
        b"os.environ['TRANSFORMERS_OFFLINE'] = '1'")
REPLACEMENT=(
    b"_eliot_r35_online_worker = (os.environ.get('ELIOT_R35_1_ONLINE_MODEL_SETUP') == '1' and\n"
    b"    ('--eliot-r35-ruaccent-worker' in sys.argv or '--eliot-r35-accentik-worker' in sys.argv))\n"
    b"os.environ['HF_HUB_OFFLINE'] = '0' if _eliot_r35_online_worker else '1'\n"
    b"os.environ['TRANSFORMERS_OFFLINE'] = '0' if _eliot_r35_online_worker else '1'"
).replace(b'\n',b'\r\n')

def verify_patched_or_original(raw,ns):
    if raw.count(REPLACEMENT)==1 and raw.count(NEEDLE)==0:
        original=raw.replace(REPLACEMENT,NEEDLE,1)
        if ns['is_exact_r35'](original):
            return ('already-patched', original, raw)
    elif raw.count(NEEDLE)==1 and raw.count(REPLACEMENT)==0 and ns['is_exact_r35'](raw):
        return ('fresh',raw,raw.replace(NEEDLE,REPLACEMENT,1))
    raise RuntimeError('UNKNOWN_UPDATER_HOLD_NO_PATCH '+digest(raw))

def embedded_check_without_writes():
    # Test exact byte changes and flag-scoped environment without a Windows machine.
    from pathlib import Path
    sample=(b'HEADER\r\n'+NEEDLE+b'\r\nBOTTOM\r\n')
    assert sample.count(NEEDLE)==1
    changed=sample.replace(NEEDLE,REPLACEMENT,1)
    assert changed.replace(REPLACEMENT,NEEDLE,1)==sample
    assert changed[:8]==sample[:8]
    for args,allow,expected in [([],False,'1'),(['--eliot-r35-selftest'],True,'1'),
                                (['--eliot-r35-shtorm-worker'],True,'1'),
                                (['--eliot-r35-ruaccent-worker'],False,'1'),
                                (['--eliot-r35-ruaccent-worker'],True,'0'),
                                (['--eliot-r35-accentik-worker'],True,'0')]:
        # Execute only the two-line environment switch, not the actual updater.
        s=REPLACEMENT.decode('utf-8').replace('\r\n','\n')
        env={'ELIOT_R35_1_ONLINE_MODEL_SETUP':'1' if allow else '0'}
        import types
        proxy=types.SimpleNamespace(environ=env);argv=types.SimpleNamespace(argv=['tool']+args)
        exec(s,{'os':proxy,'sys':argv})
        assert env['HF_HUB_OFFLINE']==expected and env['TRANSFORMERS_OFFLINE']==expected
    ns=original_r35()
    assert ns['sha'](gzip.decompress(base64.b64decode(ns['ROUTE_B64'])))==ns['ROUTE_SHA']
    print('ELIOT_R35_1_SELFTEST_PASS: exact R35 attestation, scoped online setup, reversibility',flush=True)
    return ns

EMBED=(
  'import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
  'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],p,"exec"),'
  '{"__name__":"__main__","__file__":p})'
)

def call(cmd, flag):
    env=os.environ.copy()
    env.update({'ELIOT_R35_1_ONLINE_MODEL_SETUP':'1','PYTHONDONTWRITEBYTECODE':'1',
                'HF_HUB_DISABLE_TELEMETRY':'1'})
    return subprocess.call([sys.executable,'-u','-c',EMBED,str(cmd),flag],env=env, cwd=str(cmd.parent))

def main():
    ns=embedded_check_without_writes()
    if '--selftest-only' in sys.argv:
        return 0
    if os.name!='nt' or sys.version_info<(3,11):
        raise RuntimeError('WINDOWS_PYTHON_3_11_REQUIRED')
    home=pathlib.Path.home()
    folder=home/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if (not cmd.is_file() or cmd.is_symlink() or folder.is_symlink()):
        raise RuntimeError('SINGLE_UPDATER_NOT_FOUND_OR_LINK')
    raw=cmd.read_bytes()
    status, old, new = verify_patched_or_original(raw,ns)
    if status=='fresh':
        if old.count(REPLACEMENT) or new.count(NEEDLE):
            raise RuntimeError('SCOPE_DELTA_NOT_EXACT')
        backup_dir=home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'ELIOT_R35_1_BACKUPS'
        if backup_dir.is_symlink():raise RuntimeError('BACKUP_SYMLINK_HOLD')
        backup_dir.mkdir(parents=True,exist_ok=True)
        backup=backup_dir/('BG_VOICE_UPDATE_PRE_R35_1_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+str(os.getpid())+'.bak')
        with backup.open('xb') as f:
            f.write(old);f.flush();os.fsync(f.fileno())
        if digest(backup.read_bytes())!=digest(old):
            raise RuntimeError('BACKUP_SHA_VERIFICATION_FAILED')
        pending=folder/('BG_VOICE_UPDATE.cmd.R35_1_'+str(os.getpid())+'.pending')
        if pending.exists():raise RuntimeError('PENDING_FILE_COLLISION')
        try:
            with pending.open('xb') as f:
                f.write(new);f.flush();os.fsync(f.fileno())
            if digest(pending.read_bytes())!=digest(new) or digest(cmd.read_bytes())!=digest(old):
                raise RuntimeError('CONCURRENT_CHANGE_OR_PENDING_BAD_SHA')
            os.replace(pending,cmd)
        finally:pending.unlink(missing_ok=True)
        if cmd.read_bytes()!=new:raise RuntimeError('POST_PATCH_SHA_MISMATCH')
        print('ELIOT_R35_1_INSTALLED: exact prior R35 verified; outside backup:',backup,flush=True)
    else:
        print('ELIOT_R35_1_ALREADY_INSTALLED: exact verified patch; resuming',flush=True)
    for flag in ('--eliot-r35-selftest','--eliot-r35-preflight','--eliot-r35-stresscheck'):
        code=call(cmd,flag)
        if code:
            print('ELIOT_R35_1_HOLD',flag,'rc=',code,'NO SYNTHESIS, ORIGINAL WAVS INTACT',flush=True)
            return code
    print('ELIOT_R35_1_STRESS_GATE_PASSED: starting ONE cinematic, 3 test WAVs',flush=True)
    code=call(cmd,'--eliot-r35-generate')
    if code:
        print('ELIOT_R35_1_HOLD_GENERATION rc',code,'old originals intact',flush=True)
    else:
        print('ELIOT_R35_1_SUCCESS: review 3 candidates from SEND_TO_CHATGPT_BG_VOICE_RU.zip',flush=True)
    return code

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT_R35_1_INTERRUPTED: original recordings preserved',flush=True)
        raise SystemExit(130)
    except Exception as e:
        print('ELIOT_R35_1_FAIL_CLOSED',type(e).__name__,str(e)[:350],flush=True)
        raise SystemExit(2)
