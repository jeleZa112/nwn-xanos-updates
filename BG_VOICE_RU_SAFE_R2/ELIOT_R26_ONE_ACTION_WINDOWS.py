# ELIOT R26: guarded patch of the exact existing R25 one-file updater.
# Pilot: THREE authentic game stage cues / SIX A-B WAV candidates / NO game installation.
from __future__ import annotations
import base64, gzip, hashlib, os, pathlib, subprocess, sys, tempfile
from datetime import datetime, timezone

SOURCE_SHA = '3b4fb5a49b4ef0f5303b905c38a5fdaddd149a2de5c91dda49136a4724c59bc7'
TARGET_SHA = '353588ebba6affca1a23a6ae8d0bbe86ea0db2f2a583c7d554ac9bc5403d2cdf'
ROUTE_SHA = 'c114a75b3f5093f80bdc439059cf7864d557cbaffade1b8168346e4da69698b9'
ROUTE_B64 = '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'
MARKER = b"# BGVOICE_V70_SINGLEFILE_INTEGRATION_END\r\n\r\nif __name__=='__main__':"
INSERT_AT = b"        if '--eliot-r25-selftest' in sys.argv:\r\n"
ADD = (b"        if '--eliot-r26-selftest' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r26_entry('selftest'))\r\n"
       b"        if '--eliot-r26-preflight' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r26_entry('preflight'))\r\n"
       b"        if '--eliot-r26-generate' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r26_entry('generate'))\r\n")
EMBED = ('import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
         'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],p,"exec"),'
         '{"__name__":"__main__","__file__":p})')

def sha(blob):return hashlib.sha256(blob).hexdigest()

def patch_exact(original):
    if sha(original)!=SOURCE_SHA:
        raise RuntimeError('UNKNOWN_CMD_SHA256_HOLD: '+sha(original))
    route=gzip.decompress(base64.b64decode(ROUTE_B64,validate=True))
    if sha(route)!=ROUTE_SHA or b'\r' in route:
        raise RuntimeError('ROUTE_INTEGRITY_OR_LINE_ENDING_HOLD')
    route=route.replace(b'\n',b'\r\n')
    if (original.count(MARKER)!=1 or original.count(INSERT_AT)!=1 or
        b'ELIOT_R26_AUTHOR_STAGE_AB_BEGIN' in original):
        raise RuntimeError('R25_MARKER_NOT_EXACT_HOLD')
    result=original.replace(MARKER,route+b'\r\n'+MARKER,1)
    result=result.replace(INSERT_AT,ADD+INSERT_AT,1)
    if sha(result)!=TARGET_SHA:raise RuntimeError('PATCHED_CMD_SHA256_MISMATCH_HOLD')
    return result

def run_embedded(cmd,flag):
    env=os.environ.copy()
    env.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','HF_DATASETS_OFFLINE':'1',
                'HF_HUB_DISABLE_TELEMETRY':'1','BG_VOICE_RU_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1'})
    return subprocess.call([sys.executable,'-u','-c',EMBED,str(cmd),flag],env=env,
                           timeout=7200 if flag.endswith('generate') else 180)

def main():
    if os.name!='nt' or sys.version_info<(3,9):
        print('ELIOT R26 HOLD: Windows Python 3.9+ required');return 2
    folder=pathlib.Path.home()/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if not cmd.is_file() or cmd.is_symlink() or folder.is_symlink():
        print('ELIOT R26 HOLD: single original updater not found or symlink:',cmd);return 2
    before=cmd.read_bytes();actual=sha(before)
    if actual==TARGET_SHA:
        print('ELIOT R26: already installed, verified. No rewrite.')
    elif actual==SOURCE_SHA:
        patched=patch_exact(before)
        backup_dir=pathlib.Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'ELIOT_R26_UPDATER_BACKUPS'
        if backup_dir.is_symlink():raise RuntimeError('BACKUP_DIR_SYMLINK_HOLD')
        backup_dir.mkdir(parents=True,exist_ok=True)
        backup=backup_dir/('BG_VOICE_UPDATE_PRE_R26_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.bak')
        if backup.exists():raise RuntimeError('BACKUP_PATH_ALREADY_EXISTS')
        with backup.open('xb') as f:
            f.write(before);f.flush();os.fsync(f.fileno())
        if sha(backup.read_bytes())!=SOURCE_SHA:raise RuntimeError('BACKUP_INTEGRITY_FAIL')
        pending=folder/('BG_VOICE_UPDATE.cmd.R26_'+str(os.getpid())+'.pending')
        if pending.exists():raise RuntimeError('PENDING_ALREADY_EXISTS')
        try:
            with pending.open('xb') as f:
                f.write(patched);f.flush();os.fsync(f.fileno())
            if sha(pending.read_bytes())!=TARGET_SHA or sha(cmd.read_bytes())!=SOURCE_SHA:
                raise RuntimeError('DISK_SHA_OR_CONCURRENT_SOURCE_MISMATCH')
            os.replace(pending,cmd)
        finally:
            pending.unlink(missing_ok=True)
        print('ELIOT R26: exact R25 updater patched safely; rollback backup:',backup,flush=True)
    else:
        print('ELIOT R26 HOLD: UNKNOWN_CMD_SHA256='+actual+'; no changes. Send SHA to ChatGPT.',flush=True)
        return 2
    if sha(cmd.read_bytes())!=TARGET_SHA:raise RuntimeError('INSTALLED_FILE_HASH_DIFFERENT_HOLD')
    for flag in ('--eliot-r26-selftest','--eliot-r26-preflight'):
        rc=run_embedded(cmd,flag)
        if rc:
            print('ELIOT R26 HOLD at',flag,'rc',rc,'No audio synthesis started.',flush=True)
            return rc
    print('ELIOT R26: starting 6 preview WAVs (3 scenes x A/B), no game install.',flush=True)
    rc=run_embedded(cmd,'--eliot-r26-generate')
    if rc:
        print('ELIOT R26 HOLD: generation code',rc,'; previous WAVs unchanged; successful partials preserved in R26 cache.',flush=True)
    else:
        print('ELIOT R26 SUCCESS: six candidate WAVs in ONE SEND_TO_CHATGPT_BG_VOICE_RU.zip; send to ChatGPT for listening.',flush=True)
    return rc

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT R26 INTERRUPTED. Old audio intact; R26 cache may resume.');raise SystemExit(130)
    except Exception as e:
        print('ELIOT R26 FAIL CLOSED:',type(e).__name__,str(e)[:230],flush=True)
        raise SystemExit(2)
