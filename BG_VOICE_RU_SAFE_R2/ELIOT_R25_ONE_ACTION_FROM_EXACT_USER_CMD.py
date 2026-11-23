# ELIOT R25: one-time guarded patch of the user's EXACT current BG_VOICE_UPDATE.cmd.
# No alternate permanent updater, no system packages, no model downloads, no game writes.
from __future__ import annotations
import base64, gzip, hashlib, os, subprocess, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone

SOURCE_SHA = 'c7d3dace5d44bb0dc669f66e9ecc0863865b5fd83a52b036ea28042d864ee370'
TARGET_SHA = '3b4fb5a49b4ef0f5303b905c38a5fdaddd149a2de5c91dda49136a4724c59bc7'
ROUTE_COMPRESSED_B64 = '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'
MARKER = b"# BGVOICE_V70_SINGLEFILE_INTEGRATION_END\r\n\r\nif __name__=='__main__':"
DISPATCH = b"        if '--movie-channel-selftest' in sys.argv:\r\n"
NEW_DISPATCH = (b"        if '--eliot-r25-selftest' in sys.argv:\r\n"
    b"            sys.exit(_eliot_r25_entry('selftest'))\r\n"
    b"        if '--eliot-r25-preflight' in sys.argv:\r\n"
    b"            sys.exit(_eliot_r25_entry('preflight'))\r\n"
    b"        if '--eliot-r25-generate' in sys.argv:\r\n"
    b"            sys.exit(_eliot_r25_entry('generate'))\r\n")
EMBED_COMMAND = ("import sys;p=sys.argv.pop(1);t=open(p,encoding='utf-8-sig').read();"
    "exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),"
    "{'__name__':'__main__','__file__':p})")

def sha(data):return hashlib.sha256(data).hexdigest()

def patch_exact(source):
    if sha(source)!=SOURCE_SHA:raise RuntimeError('UNKNOWN_OR_MODIFIED_LOCAL_CMD_SHA_HOLD: '+sha(source))
    route=gzip.decompress(base64.b64decode(ROUTE_COMPRESSED_B64,validate=True))
    route=route.replace(b'\n',b'\r\n')
    if source.count(MARKER)!=1 or source.count(DISPATCH)!=1 or b'ELIOT_R25_MOVIE_STYLE_AB_BEGIN' in source:
        raise RuntimeError('EXACT_UNMODIFIED_DISPATCH_MARKERS_NOT_FOUND_HOLD')
    result=source.replace(MARKER,route+b'\r\n'+MARKER,1)
    result=result.replace(DISPATCH,NEW_DISPATCH+DISPATCH,1)
    if sha(result)!=TARGET_SHA:raise RuntimeError('LOCAL_PATCH_DIGEST_MISMATCH_HOLD')
    return result

def run_embedded(cmd_file,mode):
    env=os.environ.copy()
    env.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
                'HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1',
                'BG_VOICE_RU_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1'})
    args=[sys.executable,'-u','-c',EMBED_COMMAND,str(cmd_file),mode]
    rc=subprocess.call(args,env=env,timeout=600 if mode=='--eliot-r25-generate' else 90)
    return rc

def write_exclusive(path,data):
    with path.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    if sha(path.read_bytes())!=sha(data):raise RuntimeError('DISK_WRITE_DIGEST_MISMATCH')

def main():
    if os.name!='nt':
        print('ELIOT R25 HOLD: Windows-only guarded installation',flush=True);return 2
    if sys.version_info<(3,9):
        print('ELIOT R25 HOLD: Python 3.9+ required',flush=True);return 2
    folder=Path.home()/'Downloads'/'BG_VOICE_RU_TTS_READY'/'bg_voice_release_v2'
    cmd=folder/'BG_VOICE_UPDATE.cmd'
    if not cmd.is_file() or cmd.is_symlink() or folder.is_symlink():
        print('ELIOT R25 HOLD: expected existing single updater missing or symlink',cmd,flush=True);return 2
    old=cmd.read_bytes();actual=sha(old)
    if actual==TARGET_SHA:
        print('ELIOT R25: exact patched CMD already installed; no overwrite',flush=True)
    elif actual==SOURCE_SHA:
        candidate=patch_exact(old)
        # Validate and PREFLIGHT prior to any live updater changes.
        fd,trial_name=tempfile.mkstemp(prefix='ELIOT_R25_TRIAL_',suffix='.cmd',dir=str(folder));os.close(fd)
        trial=Path(trial_name)
        try:
            with trial.open('wb') as f:f.write(candidate);f.flush();os.fsync(f.fileno())
            if sha(trial.read_bytes())!=TARGET_SHA:raise RuntimeError('STAGING_SHA_MISMATCH')
            for mode in ('--eliot-r25-selftest','--eliot-r25-preflight'):
                print('ELIOT R25 BEFORE_INSTALL',mode,flush=True)
                if run_embedded(trial,mode):
                    print('ELIOT R25 HOLD: selftest/preflight blocked; ORIGINAL CMD UNCHANGED',flush=True)
                    return 2
            # Back up the exact 16 MB user file prior to atomic update.
            backup=folder/('BG_VOICE_UPDATE.cmd.ELIOT_R25_BACKUP_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.bak')
            write_exclusive(backup,old)
            if sha(cmd.read_bytes())!=SOURCE_SHA:
                print('ELIOT R25 HOLD: CMD changed during preparation; backup retained',flush=True);return 2
            # Atomic replacement of the SAME one user-facing updater. No separate .cmd.
            os.replace(trial,cmd)
            if sha(cmd.read_bytes())!=TARGET_SHA:
                print('ELIOT R25 HOLD: replaced file digest mismatch; restoring backup',flush=True)
                os.replace(backup,cmd)
                return 2
            print('ELIOT R25: exact CMD patched, original SHA backed up at',backup,flush=True)
        except Exception as exc:
            print('ELIOT R25 INSTALL HOLD:',type(exc).__name__,str(exc)[:220],flush=True)
            # Restore only if the installed file has our known new SHA.
            if sha(cmd.read_bytes())==TARGET_SHA:
                backups=list(folder.glob('BG_VOICE_UPDATE.cmd.ELIOT_R25_BACKUP_*.bak'))
                backups=[p for p in backups if sha(p.read_bytes())==SOURCE_SHA]
                if backups:os.replace(sorted(backups)[-1],cmd)
            return 2
        finally:
            if trial.exists():trial.unlink()
    else:
        print('ELIOT R25 HOLD: UNKNOWN_CMD_SHA256='+actual+'; no file changed',flush=True)
        return 2
    if sha(cmd.read_bytes())!=TARGET_SHA:
        print('ELIOT R25 HOLD: installed exact SHA verification failed',flush=True);return 2
    print('ELIOT R25: launching ONLY two-scene acting A/B via SAME existing CMD',flush=True)
    rc=run_embedded(cmd,'--eliot-r25-generate')
    if rc:
        print('ELIOT R25 HOLD: code='+str(rc)+'. Old WAV/game untouched. Send console text.',flush=True)
    else:
        print('ELIOT R25 SUCCESS: four candidate WAVs in existing ONE report. Send SEND_TO_CHATGPT_BG_VOICE_RU.zip.',flush=True)
    return rc

if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT R25 INTERRUPTED; originals preserved; rerun safely resumes',flush=True)
        raise SystemExit(130)
    except Exception as exc:
        print('ELIOT R25 FAIL CLOSED:',type(exc).__name__,str(exc)[:220],flush=True)
        raise SystemExit(2)
