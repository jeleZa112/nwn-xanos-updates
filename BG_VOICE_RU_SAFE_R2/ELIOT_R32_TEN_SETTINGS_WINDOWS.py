# ELIOT R32 verified one-action installer from EXACT installed R31 single updater only.
from __future__ import annotations
import base64,gzip,hashlib,os,pathlib,subprocess,sys,tempfile
from datetime import datetime,timezone
SOURCE_SHA='5401805a27cb50bf6dd95c94b4ba4ca709298c36887cb92c7c1d54c405274189'
TARGET_SHA='b1fa9aebb9fdf4d2214769d94fccb425b280e823594fe6f2901ee52a810a2c30'
ROUTE_SHA='3c9a37ba66d1d22160766733906deee9ae4a612d7dd9d0205643611ed4d53fb8'
ROUTE_B64='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'
MARKER=b'# BGVOICE_V70_SINGLEFILE_INTEGRATION_END\r\n'
ANCHOR=b"        if '--eliot-r31-selftest' in sys.argv:\r\n"
FLAGS=b"        if '--eliot-r32-selftest' in sys.argv:\r\n            sys.exit(_eliot_r32_entry('selftest'))\r\n        if '--eliot-r32-preflight' in sys.argv:\r\n            sys.exit(_eliot_r32_entry('preflight'))\r\n        if '--eliot-r32-generate' in sys.argv:\r\n            sys.exit(_eliot_r32_entry('generate'))\r\n"
EMBED=('import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
       'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],p,"exec"),'
       '{"__name__":"__main__","__file__":p})')
def sha(b):return hashlib.sha256(b).hexdigest()
def patch_exact(b):
    if sha(b)!=SOURCE_SHA:raise RuntimeError('UNKNOWN_CMD_SHA256_HOLD '+sha(b))
    route=gzip.decompress(base64.b64decode(ROUTE_B64,validate=True))
    if sha(route)!=ROUTE_SHA or b'\r' in route:raise RuntimeError('ROUTE_INTEGRITY_HOLD')
    if b.count(MARKER)!=1 or b.count(ANCHOR)!=1 or b'_eliot_r32_entry' in b:raise RuntimeError('SOURCE_MARKER_HOLD')
    out=b.replace(MARKER,route.replace(b'\n',b'\r\n')+b'\r\n'+MARKER,1)
    out=out.replace(ANCHOR,FLAGS+ANCHOR,1)
    if sha(out)!=TARGET_SHA:raise RuntimeError('TARGET_INTEGRITY_HOLD')
    return out
def run_embedded(cmd,flag):
    env=os.environ.copy()
    env.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','PYTHONDONTWRITEBYTECODE':'1'})
    return subprocess.call([sys.executable,'-u','-c',EMBED,str(cmd),flag],env=env)
def main():
    if os.name!='nt' or sys.version_info<(3,9):
        print('ELIOT R32 HOLD: Windows Python 3.9+ required');return 2
    folder=pathlib.Path.home()/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if not cmd.is_file() or cmd.is_symlink() or folder.is_symlink():
        print('ELIOT R32 HOLD: updater absent or symlink',cmd);return 2
    data=cmd.read_bytes();oldsha=sha(data)
    if oldsha==TARGET_SHA:
        print('ELIOT R32 exact version already installed; not patching again',flush=True)
    elif oldsha==SOURCE_SHA:
        new=patch_exact(data)
        backdir=pathlib.Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'ELIOT_R32_UPDATER_BACKUPS'
        if backdir.is_symlink():raise RuntimeError('BACKUP_DIR_LINK')
        backdir.mkdir(parents=True,exist_ok=True)
        backup=backdir/('BG_VOICE_UPDATE_PRE_R32_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.bak')
        with backup.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        if sha(backup.read_bytes())!=SOURCE_SHA:raise RuntimeError('BACKUP_SHA_HOLD')
        pending=folder/('BG_VOICE_UPDATE.cmd.R32_'+str(os.getpid())+'.pending')
        if pending.exists():raise RuntimeError('PENDING_ALREADY_EXISTS')
        try:
            with pending.open('xb') as f:f.write(new);f.flush();os.fsync(f.fileno())
            if sha(pending.read_bytes())!=TARGET_SHA or sha(cmd.read_bytes())!=SOURCE_SHA:raise RuntimeError('CONCURRENT_CHANGE_HOLD')
            os.replace(pending,cmd)
        finally:pending.unlink(missing_ok=True)
        print('ELIOT R32 patched exact R31 updater; verified backup:',backup,flush=True)
    else:
        print('ELIOT R32 HOLD: UNKNOWN_CMD_SHA256='+oldsha+'; nothing modified',flush=True)
        return 2
    if sha(cmd.read_bytes())!=TARGET_SHA:raise RuntimeError('CMD_SHA_MISMATCH_AFTER_INSTALL')
    for flag in ('--eliot-r32-selftest','--eliot-r32-preflight'):
        rc=run_embedded(cmd,flag)
        if rc:
            print('ELIOT R32 HOLD at',flag,'rc',rc,'no synthesis started',flush=True);return rc
    print('ELIOT R32: 10 candidates, ONE cinematic IWINTRO_G08, source and game protected.',flush=True)
    rc=run_embedded(cmd,'--eliot-r32-generate')
    if rc==0:print('ELIOT R32 SUCCESS: 10 new WAV + old anchors in ONE SEND_TO_CHATGPT_BG_VOICE_RU.zip',flush=True)
    else:print('ELIOT R32 HOLD / RESUMABLE: partial successful WAVs cached; upload console if needed.',flush=True)
    return rc
if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT R32 INTERRUPTED: successful WAV checkpoints preserved');raise SystemExit(130)
    except Exception as e:
        print('ELIOT R32 FAIL CLOSED',type(e).__name__,str(e)[:240],flush=True);raise SystemExit(2)
