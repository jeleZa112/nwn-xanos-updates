# ELIOT R29: guarded patch of the exact existing R25 one-file updater.
# Pilot: THREE authentic game stage cues / SIX A-B WAV candidates / NO game installation.
from __future__ import annotations
import base64, gzip, hashlib, os, pathlib, subprocess, sys, tempfile
from datetime import datetime, timezone

SOURCE_SHA = '353588ebba6affca1a23a6ae8d0bbe86ea0db2f2a583c7d554ac9bc5403d2cdf'
TARGET_SHA = '59ec50fd858598d6b141607864b6a4793a9cf95f3d56036d8bd7608a9b8204b1'
ROUTE_SHA = '8e279a7c77a92d6851f42ba9261d1daa53f98b028090ebfbe8a0e140c17584cb'
ROUTE_B64 = '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'
MARKER = b"# BGVOICE_V70_SINGLEFILE_INTEGRATION_END\r\n\r\nif __name__=='__main__':"
INSERT_AT = b"        if '--eliot-r25-selftest' in sys.argv:\r\n"
ADD = (b"        if '--eliot-r29-selftest' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r29_entry('selftest'))\r\n"
       b"        if '--eliot-r29-preflight' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r29_entry('preflight'))\r\n"
       b"        if '--eliot-r29-generate' in sys.argv:\r\n"
       b"            sys.exit(_eliot_r29_entry('generate'))\r\n")
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
        b'ELIOT_R29_AUTHOR_STAGE_AB_BEGIN' in original):
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
        print('ELIOT R29 HOLD: Windows Python 3.9+ required');return 2
    folder=pathlib.Path.home()/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if not cmd.is_file() or cmd.is_symlink() or folder.is_symlink():
        print('ELIOT R29 HOLD: single original updater not found or symlink:',cmd);return 2
    before=cmd.read_bytes();actual=sha(before)
    if actual==TARGET_SHA:
        print('ELIOT R29: already installed, verified. No rewrite.')
    elif actual==SOURCE_SHA:
        patched=patch_exact(before)
        backup_dir=pathlib.Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'ELIOT_R29_UPDATER_BACKUPS'
        if backup_dir.is_symlink():raise RuntimeError('BACKUP_DIR_SYMLINK_HOLD')
        backup_dir.mkdir(parents=True,exist_ok=True)
        backup=backup_dir/('BG_VOICE_UPDATE_PRE_R29_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.bak')
        if backup.exists():raise RuntimeError('BACKUP_PATH_ALREADY_EXISTS')
        with backup.open('xb') as f:
            f.write(before);f.flush();os.fsync(f.fileno())
        if sha(backup.read_bytes())!=SOURCE_SHA:raise RuntimeError('BACKUP_INTEGRITY_FAIL')
        pending=folder/('BG_VOICE_UPDATE.cmd.R29_'+str(os.getpid())+'.pending')
        if pending.exists():raise RuntimeError('PENDING_ALREADY_EXISTS')
        try:
            with pending.open('xb') as f:
                f.write(patched);f.flush();os.fsync(f.fileno())
            if sha(pending.read_bytes())!=TARGET_SHA or sha(cmd.read_bytes())!=SOURCE_SHA:
                raise RuntimeError('DISK_SHA_OR_CONCURRENT_SOURCE_MISMATCH')
            os.replace(pending,cmd)
        finally:
            pending.unlink(missing_ok=True)
        print('ELIOT R29: exact R25 updater patched safely; rollback backup:',backup,flush=True)
    else:
        print('ELIOT R29 HOLD: UNKNOWN_CMD_SHA256='+actual+'; no changes. Send SHA to ChatGPT.',flush=True)
        return 2
    if sha(cmd.read_bytes())!=TARGET_SHA:raise RuntimeError('INSTALLED_FILE_HASH_DIFFERENT_HOLD')
    for flag in ('--eliot-r29-selftest','--eliot-r29-preflight'):
        rc=run_embedded(cmd,flag)
        if rc:
            print('ELIOT R29 HOLD at',flag,'rc',rc,'No audio synthesis started.',flush=True)
            return rc
    print('ELIOT R29: starting 6 preview WAVs (2 scenes x A/B/C), no game install.',flush=True)
    rc=run_embedded(cmd,'--eliot-r29-generate')
    if rc:
        print('ELIOT R29 HOLD: generation code',rc,'; previous WAVs unchanged; successful partials preserved in R29 cache.',flush=True)
    else:
        print('ELIOT R29 SUCCESS: six candidate A/B/C WAVs in ONE SEND_TO_CHATGPT_BG_VOICE_RU.zip; send to ChatGPT for listening.',flush=True)
    return rc

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT R29 INTERRUPTED. Old audio intact; R29 cache may resume.');raise SystemExit(130)
    except Exception as e:
        print('ELIOT R29 FAIL CLOSED:',type(e).__name__,str(e)[:230],flush=True)
        raise SystemExit(2)
