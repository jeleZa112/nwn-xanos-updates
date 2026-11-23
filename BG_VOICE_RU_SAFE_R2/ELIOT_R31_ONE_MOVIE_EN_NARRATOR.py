# ELIOT R31 — EXACT PINNED R29 CMD, ONE MOVIE TEST. SOURCE ONLY in GitHub staging.
from __future__ import annotations
import base64, gzip, hashlib, os, pathlib, subprocess, sys, tempfile
from datetime import datetime, timezone

SOURCE_SHA='59ec50fd858598d6b141607864b6a4793a9cf95f3d56036d8bd7608a9b8204b1'
TARGET_SHA='5401805a27cb50bf6dd95c94b4ba4ca709298c36887cb92c7c1d54c405274189'
ROUTE_SHA='60850d77a2566aefabc0be9150fd1f8ba1cc20e3fbb3992a2a550bae19435431'
ROUTE_B64='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'
ANCHOR=b"        if '--eliot-r29-selftest' in sys.argv:\r\n"
MARKER=b'# BGVOICE_V70_SINGLEFILE_INTEGRATION_END\r\n'
FLAGS=(b"        if '--eliot-r31-selftest' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r31_entry('selftest'))\r\n"
       b"        if '--eliot-r31-preflight' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r31_entry('preflight'))\r\n"
       b"        if '--eliot-r31-generate' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r31_entry('generate'))\r\n")
EMBED=('import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
       'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],p,"exec"),'
       '{"__name__":"__main__","__file__":p})')

def sha(b):return hashlib.sha256(b).hexdigest()

def patch_exact(b):
    if sha(b)!=SOURCE_SHA:raise RuntimeError('UNKNOWN_CMD_SHA256_HOLD '+sha(b))
    route=gzip.decompress(base64.b64decode(ROUTE_B64,validate=True))
    if sha(route)!=ROUTE_SHA or b'\r' in route:raise RuntimeError('R31_ROUTE_INTEGRITY_HOLD')
    if b.count(MARKER)!=1 or b.count(ANCHOR)!=1 or b'ELIOT_R31_IWINTRO_G08_EN_VOICE_PACING_BEGIN' in b:
        raise RuntimeError('R29_MARKER_NOT_EXACT_HOLD')
    result=b.replace(MARKER,route.replace(b'\n',b'\r\n')+b'\r\n'+MARKER,1)
    result=result.replace(ANCHOR,FLAGS+ANCHOR,1)
    if sha(result)!=TARGET_SHA:raise RuntimeError('R31_TARGET_INTEGRITY_HOLD')
    return result

def run_embedded(cmd,flag):
    env=os.environ.copy()
    env.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','PYTHONDONTWRITEBYTECODE':'1'})
    return subprocess.call([sys.executable,'-u','-c',EMBED,str(cmd),flag],env=env,timeout=7200 if flag.endswith('generate') else 180)

def main():
    if os.name!='nt' or sys.version_info<(3,9):
        print('ELIOT R31 HOLD: Windows Python 3.9+ required');return 2
    folder=pathlib.Path.home()/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if not cmd.is_file() or cmd.is_symlink() or folder.is_symlink():
        print('ELIOT R31 HOLD: original updater missing or symlink',cmd);return 2
    b=cmd.read_bytes();oldsha=sha(b)
    if oldsha==TARGET_SHA:
        print('ELIOT R31: exact version already installed; nothing to modify.',flush=True)
    elif oldsha==SOURCE_SHA:
        new=patch_exact(b)
        backdir=pathlib.Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'ELIOT_R31_UPDATER_BACKUPS'
        if backdir.is_symlink():raise RuntimeError('BACKUP_LINK_HOLD')
        backdir.mkdir(parents=True,exist_ok=True)
        backup=backdir/('BG_VOICE_UPDATE_PRE_R31_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.bak')
        with backup.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        if sha(backup.read_bytes())!=SOURCE_SHA:raise RuntimeError('BACKUP_SHA_HOLD')
        pending=folder/('BG_VOICE_UPDATE.cmd.R31_'+str(os.getpid())+'.pending')
        if pending.exists():raise RuntimeError('PENDING_EXISTS_HOLD')
        try:
            with pending.open('xb') as f:f.write(new);f.flush();os.fsync(f.fileno())
            if sha(pending.read_bytes())!=TARGET_SHA or sha(cmd.read_bytes())!=SOURCE_SHA:
                raise RuntimeError('CONCURRENT_CHANGE_OR_WRONG_PATCH_HOLD')
            os.replace(pending,cmd)
        finally:pending.unlink(missing_ok=True)
        print('ELIOT R31: exact R29 updater patched, SHA verified, backup:',backup,flush=True)
    else:
        print('ELIOT R31 HOLD: UNKNOWN_CMD_SHA256='+oldsha+'; nothing changed.',flush=True)
        return 2
    if sha(cmd.read_bytes())!=TARGET_SHA:raise RuntimeError('CMD_INTEGRITY_HOLD')
    for flag in ('--eliot-r31-selftest','--eliot-r31-preflight'):
        rc=run_embedded(cmd,flag)
        if rc:
            print('ELIOT R31 HOLD at',flag,'rc',rc,'No synthesis attempted.',flush=True);return rc
    print('ELIOT R31: ONE CINEMATIC G08 original-English narrator voice experiment, no game modification.',flush=True)
    rc=run_embedded(cmd,'--eliot-r31-generate')
    if not rc:print('ELIOT R31 SUCCESS: ONE new G08 preview WAV in ONE SEND_TO_CHATGPT_BG_VOICE_RU.zip.',flush=True)
    else:print('ELIOT R31 HOLD: generation rc',rc,'older reports and sources untouched.',flush=True)
    return rc
if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT R31 INTERRUPTED: old audio intact.');raise SystemExit(130)
    except Exception as e:
        print('ELIOT R31 FAIL CLOSED:',type(e).__name__,str(e)[:240],flush=True);raise SystemExit(2)
