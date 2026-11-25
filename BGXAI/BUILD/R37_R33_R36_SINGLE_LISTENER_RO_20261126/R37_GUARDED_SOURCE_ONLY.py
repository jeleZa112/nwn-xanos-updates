#!/usr/bin/env python3
"""BGXAI R37: last-only SHA-pinned WeiDU upgrade from installed R33.
SOURCE ONLY until launched by the sole pinned BGXAI_UPDATE.cmd and exact
typed approval. No auto retry, no forced game actions, no manual file restore.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(r"C:\Games\BG_EET_FOXX_NEW")
SCHEMA="BGXAI_R37_R33_R36_SINGLE_LISTENER_GUARDED_V1"
SOURCE_SHA="5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6"
SOURCE_BYTES=60835
R33_SHA="1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069"
NATIVE_SHA="0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75"
R33_SCHEMA="BGXAI_R33_R31_PASSIVE_PROF_GUARDED_V1"
OVERRIDE="override/M_BGXR27.lua"
R33_PROOF="BGXR33/PROOF.json"
R31_PROOF="BGXR31/PROOF.json"
R37_PROOF="BGXR37/PROOF.json"
R37_DIR="BGXR37"
STAGED="BGXR37/staged/M_BGXR27.lua"
TP2="BGXR37/setup-BGXR37.tp2"
SETUP="BGXR37/setup-BGXR37.exe"
INSTALL_TOKEN="INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R37_RESTORE_R33_ONLY"
TP2_TEXT=(
    "BACKUP ~BGXR37/backup~\n"
    "AUTHOR ~BGXAI R37 R33 R36 passive advisory only~\n"
    "BEGIN ~BGXR37 passive reuse existing R33 callback~\n"
    "COPY ~BGXR37/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n"
)
# These hashes came from exact previously validated R33 guarded preflight.
BASELINE_SHA={
    "EEex/copy/EEex_scripts/EEex_Action.lua":
        "7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da",
    "EEex/copy/EEex_scripts/EEex_Sprite.lua":
        "4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28",
    "enhanced-powergaming-scripts/lib/core_base.tph":
        "1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776",
    "chitin.key":"ad67498a222043421c39bcdb2026abf6cdf0fbd160cba51135ab61d6a85d9515",
    "override/BDDEFAI.BCS":
        "24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331",
    "override/DPLAYER.BCS":
        "4d640ed7f4c50ed10e30b9482940c6733196ded410405e64ed"
}
WATCHED=("WeiDU.log",OVERRIDE,R31_PROOF,R33_PROOF,*BASELINE_SHA)
WLOG=re.compile(r"^~[^~]+~\s+#\d+\s+#\d+(?:\s|$)",re.I)
def entry(code:str):
    return re.compile(r"^~(?:[^~]*[/\\])?BGXR"+code+r"[/\\]SETUP-BGXR"+code+
                      r"[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
R27,R29,R31,R33,R37=(entry(x) for x in ("27","29","31","33","37"))

class Hold(ValueError):
    pass

def sha(path:Path)->str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

def safe(root:Path,relative:str)->Path:
    if not relative or relative.startswith(("/","\\")) or ":" in relative or "\x00" in relative:
        raise Hold("INVALID_RELATIVE_PATH")
    dst=root
    for part in relative.replace("\\","/").split("/"):
        if part in ("",".",".."):
            raise Hold("INVALID_PATH_COMPONENT")
        dst=dst/part
        if dst.is_symlink() or (hasattr(dst,"is_junction") and dst.is_junction()):
            raise Hold("PATH_REPARSE_POINT:"+relative)
    return dst

def protected_root(root:Path,live:bool=True)->None:
    if live and (os.name!="nt" or os.path.normcase(os.path.abspath(root))!=
                 os.path.normcase(os.path.abspath(ROOT))):
        raise Hold("EXACT_WINDOWS_FOXX_ROOT_REQUIRED")
    if not root.is_dir() or root.is_symlink() or (hasattr(root,"is_junction") and root.is_junction()):
        raise Hold("GAME_ROOT_MISSING_OR_REPARSE")

def verify_processes()->None:
    if os.name!="nt":
        raise Hold("WINDOWS_REQUIRED_FOR_MUTATION")
    result=subprocess.run(["tasklist","/FO","CSV","/NH"],stdin=subprocess.DEVNULL,
                          capture_output=True,text=True,errors="replace",
                          timeout=25,check=False)
    if result.returncode:
        raise Hold("TASKLIST_UNAVAILABLE")
    names={row[0].strip().lower() for row in csv.reader(io.StringIO(result.stdout)) if row}
    blocked={"baldur.exe","bgmain.exe","infinityloader.exe","weidu.exe",
             "setup-enhanced-powergaming-scripts.exe","setup-bgxr31.exe",
             "setup-bgxr33.exe","setup-bgxr37.exe"}
    if names&blocked:
        raise Hold("CLOSE_GAME_AND_WEIDU:"+",".join(sorted(names&blocked)))

def history(root:Path)->tuple[list[str],str]:
    p=safe(root,"WeiDU.log")
    if not p.is_file() or p.stat().st_size>4_000_000:
        raise Hold("WEIDU_LOG_MISSING_OR_TOO_LARGE")
    raw=p.read_bytes()
    rows=[]
    for line in raw.decode("utf-8-sig",errors="replace").splitlines():
        line=line.strip()
        if not line or line.startswith(("//","#")):
            continue
        if not WLOG.match(line):
            raise Hold("UNKNOWN_WEIDU_HISTORY_RECORD")
        rows.append(line)
    if not rows:
        raise Hold("EMPTY_WEIDU_HISTORY")
    return rows,hashlib.sha256(raw).hexdigest()

def last_r33_history(rows:list[str])->bool:
    return (len(rows)==152 and R27.match(rows[148]) and R29.match(rows[149])
            and R31.match(rows[150]) and R33.match(rows[151])
            and not any(R37.match(row) for row in rows))

def last_r37_history(rows:list[str])->bool:
    return (len(rows)==153 and R27.match(rows[148]) and R29.match(rows[149])
            and R31.match(rows[150]) and R33.match(rows[151]) and R37.match(rows[152]))

def candidate_bytes(path:Path)->bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=SOURCE_BYTES:
        raise Hold("R37_CANDIDATE_SIZE_OR_FILE_MISMATCH")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise Hold("R37_CANDIDATE_SHA_MISMATCH")
    if raw.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener")!=1:
        raise Hold("R37_NOT_EXACTLY_ONE_R33_LISTENER")
    for unsafe in (b"SelectWeaponAbility(",b"ClearActions(",b"Attack(",b"Stop(",
                   b"SetGlobal(",b"ActionOverride(",b"os.execute("):
        if unsafe in raw:
            raise Hold("R37_GAME_DISPATCH_TOKEN_FOUND")
    for marker in (b"R36_CORE.capture,result",b"R36_CORE.compare,prior,cap",
                   b"R37_R33_CAPTURE_HOLD_NO_DISPATCH",b'"safeActionBoundaryVerified":false',
                   b'"dispatchAuthorized":false',b'"weaponSwitchAuthorized":false'):
        if marker not in raw:
            raise Hold("R37_SOURCE_SAFETY_MARKER_MISSING")
    return raw

def proof_r33(root:Path)->dict:
    p=safe(root,R33_PROOF)
    if not p.is_file() or p.stat().st_size>1_000_000:
        raise Hold("R33_PROOF_MISSING")
    try:
        d=json.loads(p.read_text(encoding="utf-8"))
    except (UnicodeError,ValueError) as exc:
        raise Hold("R33_PROOF_INVALID_JSON") from exc
    if (not isinstance(d,dict) or d.get("schema")!=R33_SCHEMA or
        d.get("status")!="R33_PASSIVE_INSTALLED_AWAITING_RUNTIME" or
        d.get("sourceSha256")!=R33_SHA or
        d.get("typedInstallApproved") is not True or
        d.get("installationPerformed") is not True or
        d.get("dispatchAuthorized") is not False or
        d.get("weaponSwitchAuthorized") is not False):
        raise Hold("R33_INSTALLED_PROOF_INCONSISTENT")
    snap=d.get("baselineSnapshot")
    if not isinstance(snap,dict) or snap.get(OVERRIDE)!="5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38":
        raise Hold("R33_PREINSTALL_BASELINE_NOT_R31")
    if any(snap.get(k)!=v for k,v in BASELINE_SHA.items()):
        raise Hold("R33_PREINSTALL_RESOURCE_BASELINE_CHANGED")
    return d

def snapshot(root:Path)->dict[str,str]:
    out={}
    for rel in WATCHED:
        p=safe(root,rel)
        if not p.is_file():
            raise Hold("WATCHED_RESOURCE_MISSING:"+rel)
        out[rel]=sha(p)
    return out

def verify_snapshot(root:Path,expected:dict[str,str])->None:
    for rel,digest in expected.items():
        p=safe(root,rel)
        if not p.is_file() or sha(p)!=digest:
            raise Hold("WATCHED_RESOURCE_SHA_CHANGED:"+rel)

def preflight(root:Path,candidate:Path,live:bool=True)->dict:
    protected_root(root,live)
    rows,log_sha=history(root)
    if not last_r33_history(rows):
        raise Hold("R33_MUST_BE_EXACT_WEIDU_LAST_152")
    for rel in (R37_DIR,STAGED,TP2,SETUP,R37_PROOF):
        if safe(root,rel).exists():
            raise Hold("R37_STAGING_COLLISION:"+rel)
    if sha(safe(root,OVERRIDE))!=R33_SHA:
        raise Hold("R33_LIVE_MODULE_SHA_CHANGED")
    proof_r33(root)
    if (sha(safe(root,"setup-enhanced-powergaming-scripts.exe"))!=NATIVE_SHA or
       sha(safe(root,"BGXR33/setup-BGXR33.exe"))!=NATIVE_SHA):
        raise Hold("NATIVE_WEIDU_BINARY_SHA_CHANGED")
    for rel,digest in BASELINE_SHA.items():
        if sha(safe(root,rel))!=digest:
            raise Hold("PREEXISTING_RESOURCE_SHA_CHANGED:"+rel)
    candidate_bytes(candidate)
    if live:
        verify_processes()
    snap=snapshot(root)
    return {"schema":SCHEMA,"status":"R37_PREFLIGHT_PASS_NO_INSTALL",
            "weiduComponents":len(rows),"weiDULogSha256":log_sha,
            "sourceSha256":SOURCE_SHA,"candidateBytes":SOURCE_BYTES,
            "baselineSnapshot":snap,"typedInstallApproved":False,
            "installationPerformed":False,"gameModified":False,
            "ordersSent":0,"dispatchAuthorized":False,"weaponSwitchAuthorized":False,
            "manualEpsOriginVerified":False,"safeActionBoundaryVerified":False}

def external_backup(root:Path,expected:dict[str,str])->Path:
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("EXTERNAL_BACKUP_REPARSE_POINT")
    parent.mkdir(parents=True,exist_ok=True)
    dest=Path(tempfile.mkdtemp(prefix="PRE_BGXR37_",dir=parent))
    for rel,digest in expected.items():
        origin,backup=safe(root,rel),safe(dest,rel)
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(origin,backup)
        if sha(backup)!=digest:
            raise Hold("EXTERNAL_BACKUP_HASH_FAILED:"+rel)
    safe(dest,"SHA256.json").write_text(json.dumps(expected,indent=2),encoding="utf-8")
    return dest

def native_weidu(root:Path,uninstall:bool=False)->None:
    exe=safe(root,SETUP)
    if not exe.is_file() or sha(exe)!=NATIVE_SHA:
        raise Hold("STAGED_WEIDU_BINARY_DRIFT")
    args=[str(exe),"--noautoupdate","--no-exit-pause",
          "--game",str(root),"--use-lang","ru_ru",
          "--force-uninstall" if uninstall else "--force-install","0"]
    result=subprocess.run(args,cwd=root,stdin=subprocess.DEVNULL,
                          capture_output=True,text=True,errors="replace",
                          timeout=240,check=False)
    transcript=(result.stdout or "")+"\n"+(result.stderr or "")
    if result.returncode or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",transcript):
        raise Hold("R37_WEIDU_MANUAL_REVIEW:"+transcript[-600:])

def install(root:Path,candidate:Path,token:str)->dict:
    if token!=INSTALL_TOKEN:
        raise Hold("EXACT_TYPED_INSTALL_CONSENT_REQUIRED")
    ready=preflight(root,candidate,True)
    baseline=ready["baselineSnapshot"]
    verify_snapshot(root,baseline)
    backup=external_backup(root,baseline)
    verify_processes()
    verify_snapshot(root,baseline)
    # No automatic retry or recovery once staging starts.
    safe(root,R37_DIR).mkdir(parents=True,exist_ok=False)
    staged=safe(root,STAGED)
    staged.parent.mkdir(parents=True,exist_ok=False)
    staged.write_bytes(candidate_bytes(candidate))
    safe(root,TP2).write_text(TP2_TEXT,encoding="ascii",newline="\n")
    shutil.copy2(safe(root,"setup-enhanced-powergaming-scripts.exe"),safe(root,SETUP))
    if sha(staged)!=SOURCE_SHA or sha(safe(root,SETUP))!=NATIVE_SHA:
        raise Hold("R37_STAGING_SOURCE_OR_WEIDU_DRIFT")
    verify_processes()
    verify_snapshot(root,baseline)
    proof=safe(root,R37_PROOF)
    proof.write_text(json.dumps({"schema":SCHEMA,"status":"R37_PENDING_WEIDU",
        "sourceSha256":SOURCE_SHA,"externalBackup":str(backup),
        "baselineSnapshot":baseline},indent=2),encoding="utf-8")
    native_weidu(root)
    rows,_=history(root)
    if not last_r37_history(rows) or sha(safe(root,OVERRIDE))!=SOURCE_SHA:
        raise Hold("R37_POST_WEIDU_INCONSISTENT_MANUAL_REVIEW")
    for rel,digest in baseline.items():
        if rel not in ("WeiDU.log",OVERRIDE) and sha(safe(root,rel))!=digest:
            raise Hold("R37_UNRELATED_RESOURCE_CHANGED_MANUAL_REVIEW:"+rel)
    data={"schema":SCHEMA,"status":"R37_PASSIVE_INSTALLED_AWAITING_RUNTIME",
          "sourceSha256":SOURCE_SHA,"externalBackup":str(backup),
          "baselineSnapshot":baseline,"typedInstallApproved":True,
          "installationPerformed":True,"gameModified":True,"readOnly":True,
          "ordersSent":0,"dispatchAuthorized":False,"weaponSwitchAuthorized":False,
          "manualEpsOriginVerified":False,"safeActionBoundaryVerified":False,
          "alternateEffectiveAPRVerified":False}
    proof.write_text(json.dumps(data,indent=2),encoding="utf-8")
    return data

def last_r37(root:Path,live:bool=True)->list[str]:
    protected_root(root,live)
    rows,_=history(root)
    if not last_r37_history(rows):
        raise Hold("R37_NOT_WEIDU_LAST_153")
    if sha(safe(root,OVERRIDE))!=SOURCE_SHA:
        raise Hold("R37_LIVE_MODULE_SHA_CHANGED")
    return rows

def installed_proof(root:Path)->dict:
    p=safe(root,R37_PROOF)
    if not p.is_file() or p.stat().st_size>1_000_000:
        raise Hold("R37_PROOF_MISSING")
    d=json.loads(p.read_text(encoding="utf-8"))
    if (not isinstance(d,dict) or d.get("schema")!=SCHEMA or
       d.get("status")!="R37_PASSIVE_INSTALLED_AWAITING_RUNTIME" or
       d.get("sourceSha256")!=SOURCE_SHA or
       d.get("typedInstallApproved") is not True or
       d.get("installationPerformed") is not True):
        raise Hold("R37_INSTALLED_PROOF_INVALID")
    return d

def rollback(root:Path,token:str)->dict:
    if token!=ROLLBACK_TOKEN:
        raise Hold("EXACT_TYPED_ROLLBACK_CONSENT_REQUIRED")
    last_r37(root)
    verify_processes()
    proof=installed_proof(root)
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    back=Path(proof.get("externalBackup",""))
    if (back.parent!=parent or not back.name.startswith("PRE_BGXR37_") or
       not back.is_dir() or back.is_symlink()):
        raise Hold("R37_EXTERNAL_BACKUP_PROVENANCE_INVALID")
    expected=json.loads(safe(back,"SHA256.json").read_text(encoding="utf-8"))
    if expected!=proof.get("baselineSnapshot") or expected.get(OVERRIDE)!=R33_SHA:
        raise Hold("R37_BACKUP_MANIFEST_OR_R33_SHA_CHANGED")
    verify_snapshot(back,expected)
    for rel,digest in expected.items():
        if rel not in ("WeiDU.log",OVERRIDE) and sha(safe(root,rel))!=digest:
            raise Hold("R37_ROLLBACK_UNRELATED_RESOURCE_DRIFT:"+rel)
    if sha(safe(root,SETUP))!=NATIVE_SHA:
        raise Hold("R37_ROLLBACK_WEIDU_BINARY_DRIFT")
    native_weidu(root,uninstall=True)
    rows,_=history(root)
    if not last_r33_history(rows) or sha(safe(root,OVERRIDE))!=R33_SHA:
        raise Hold("R37_ROLLBACK_FAILED_MANUAL_REVIEW")
    for rel,digest in expected.items():
        if rel not in ("WeiDU.log",OVERRIDE) and sha(safe(root,rel))!=digest:
            raise Hold("R37_ROLLBACK_CHANGED_UNRELATED_RESOURCE:"+rel)
    return {"schema":SCHEMA,"status":"R37_ROLLBACK_RESTORED_R33",
            "gameModified":True,"ordersSent":0,"dispatchAuthorized":False,
            "weaponSwitchAuthorized":False}

def capture(root:Path)->dict:
    """Run original InfinityLoader with unchanged game; collect R37/R33 evidence.
    Never install, dispatch, clear game queue or classify manual/EPS ownership.
    Blocks until user closes the game; retains raw log for later diagnostics.
    """
    last_r37(root)
    installed_proof(root)
    verify_processes()
    loader=safe(root,"InfinityLoader.exe")
    if not loader.is_file() or loader.is_symlink() or not 1024<loader.stat().st_size<70_000_000:
        raise Hold("R37_CAPTURE_LOADER_MISSING_OR_INVALID_SIZE")
    with loader.open("rb") as stream:
        if stream.read(2)!=b"MZ":
            raise Hold("R37_CAPTURE_LOADER_NOT_PE")
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("USERPROFILE_MISSING")
    reports=Path(home)/"Documents"/"BGXAI_LIVE_REPORTS"
    if reports.is_symlink() or (hasattr(reports,"is_junction") and reports.is_junction()):
        raise Hold("REPORT_DIRECTORY_REPARSE_POINT")
    reports.mkdir(parents=True,exist_ok=True)
    console=reports/("BGXAI_R37_CONSOLE_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".log")
    if console.exists() or console.is_symlink():
        raise Hold("R37_CAPTURE_LOG_COLLISION")
    with console.open("xb") as output:
        child=subprocess.Popen([str(loader)],cwd=root,stdin=subprocess.DEVNULL,
                               stdout=output,stderr=subprocess.STDOUT,close_fds=True)
        exit_code=child.wait()
        output.flush()
    # The log may contain unrelated messages: parse only our exact 2 prefixes.
    sessions,legacy,advice,held,changed=0,{}, {},0,0
    reasons={}
    malformed=0
    size=console.stat().st_size
    if size<=64_000_000:
        with console.open("rb") as stream:
            for raw in stream:
                kind=None
                if b"[BGXR37] " in raw:
                    kind="R37"
                    payload=raw.split(b"[BGXR37] ",1)[1]
                elif b"[BGXR27] " in raw:
                    kind="R33"
                    payload=raw.split(b"[BGXR27] ",1)[1]
                else:
                    continue
                try:
                    entry=json.loads(payload.decode("utf-8-sig",errors="strict").strip())
                except (UnicodeError,ValueError):
                    malformed+=1
                    continue
                if not isinstance(entry,dict):
                    malformed+=1
                    continue
                if kind=="R37":
                    if entry.get("schema")!="BGXAI_R37_R33_R36_SINGLE_LISTENER_SOURCE_V1":
                        continue
                    if entry.get("type")=="SESSION":
                        sessions+=1
                    elif entry.get("type")=="ADVISORY_CONTEXT":
                        seq,party=entry.get("seq"),entry.get("partyIndex")
                        if (type(seq) is not int or not 1<=seq<=64 or
                            type(party) is not int or not 0<=party<=5 or
                            seq in advice or entry.get("readOnly") is not True or
                            entry.get("dispatchAuthorized") is not False or
                            entry.get("weaponSwitchAuthorized") is not False or
                            entry.get("ordersSent")!=0 or
                            entry.get("actionOrigin")!="UNKNOWN" or
                            entry.get("safeActionBoundaryVerified") is not False):
                            malformed+=1
                            continue
                        label=entry.get("status")
                        if label not in {
                            "R37_FIRST_R33_SAMPLE_NO_PRIOR",
                            "R37_R33_CAPTURE_HOLD_NO_DISPATCH",
                            "HOLD_CONTEXT_COMPARISON",
                            "RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF",
                            "EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE",
                            "OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE",
                            "ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE",
                            "NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE"}:
                            malformed+=1
                            continue
                        if type(entry.get("invalidateCachedAdvice")) is not bool:
                            malformed+=1
                            continue
                        advice[seq]={"seq":seq,"partyIndex":party,"status":label,
                                     "invalidateCachedAdvice":entry["invalidateCachedAdvice"]}
                        reasons[label]=reasons.get(label,0)+1
                        held+=int(label in ("R37_R33_CAPTURE_HOLD_NO_DISPATCH","HOLD_CONTEXT_COMPARISON"))
                        changed+=int(entry["invalidateCachedAdvice"])
                elif (entry.get("schema")=="BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1" and
                      entry.get("type")=="R27_SINGLE_CALLBACK"):
                    seq,party=entry.get("seq"),entry.get("partyIndex")
                    if (type(seq) is not int or not 1<=seq<=64 or seq in legacy or
                        type(party) is not int or not 0<=party<=5 or
                        entry.get("readOnly") is not True or
                        entry.get("dispatchAuthorized") is not False or
                        entry.get("weaponSwitchAuthorized") is not False):
                        malformed+=1
                    else:
                        legacy[seq]=party
    paired=bool(advice) and set(advice)==set(legacy) and all(
        entry["partyIndex"]==legacy[seq] for seq,entry in advice.items())
    ready=(exit_code==0 and size<=64_000_000 and malformed==0 and
           sessions==1 and paired and len(legacy)==len(advice))
    return {"schema":SCHEMA,
            "status":"R37_RUNTIME_ADVICE_LOG_READY_FOR_REVIEW" if ready
                     else "R37_RUNTIME_HOLD_MANUAL_REVIEW",
            "rawConsoleFile":str(console),"rawConsoleBytes":size,
            "gameExitCode":exit_code,"r37SessionMarkers":sessions,
            "r33OriginalSamples":len(legacy),"r37AdviceSamples":len(advice),
            "r37PairedBySequenceAndParty":paired,"r37MalformedOrUnsafeRows":malformed,
            "r37InvalidationSamples":changed,"r37HeldSamples":held,
            "r37Reasons":reasons,
            "r37Events":[advice[k] for k in sorted(advice)],
            "readOnly":True,"gameModifiedByCapture":False,"ordersSent":0,
            "dispatchAuthorized":False,"weaponSwitchAuthorized":False,
            "manualEpsOriginVerified":False,"safeActionBoundaryVerified":False,
            "gameplayWeaponSwitchVerified":False}


def status(root:Path)->dict:
    protected_root(root,live=False)
    rows,log_sha=history(root)
    module_sha=sha(safe(root,OVERRIDE))
    if last_r37_history(rows) and module_sha==SOURCE_SHA:
        state="R37_PRESENT_LAST_PASSIVE"
    elif last_r33_history(rows) and module_sha==R33_SHA:
        state="R33_PRESENT_LAST_BEFORE_R37"
    else:
        state="R37_HOLD_UNKNOWN_GAME_STATE"
    return {"schema":SCHEMA,"status":state,"weiduComponents":len(rows),
            "weiduLastComponent":rows[-1],"weiDULogSha256":log_sha,
            "liveModuleSha256":module_sha,"r33SourceExact":module_sha==R33_SHA,
            "r37SourceExact":module_sha==SOURCE_SHA,
            "gameModified":False,"ordersSent":0,
            "dispatchAuthorized":False,"weaponSwitchAuthorized":False}

def report(mode:str,data:dict)->dict:
    home=os.environ.get("USERPROFILE")
    if not home:
        return {**data,"reportStatus":"USERPROFILE_MISSING"}
    parent=Path(home)/"Documents"/"BGXAI_LIVE_REPORTS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        return {**data,"reportStatus":"REPORT_DIRECTORY_REPARSE_POINT"}
    try:
        parent.mkdir(parents=True,exist_ok=True)
        filename="BGXAI_R37_"+mode.upper()+"_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json"
        dst=parent/filename
        data={**data,"reportFile":str(dst)}
        with dst.open("x",encoding="utf-8") as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2)
            stream.write("\n")
        return data
    except (OSError,ValueError) as error:
        return {**data,"reportStatus":"SAVE_FAILED:"+str(error)}

def main()->int:
    ap=argparse.ArgumentParser(description="BGXAI R37 passive one-listener guarded R33 upgrade")
    ap.add_argument("--game",type=Path,default=ROOT)
    ap.add_argument("--candidate",type=Path)
    ap.add_argument("--mode",choices=("preflight","install","status","rollback","capture"),default="preflight")
    args=ap.parse_args()
    try:
        if args.mode=="status":
            value=status(args.game)
        elif args.mode=="preflight":
            if not args.candidate:
                raise Hold("R37_SOURCE_CANDIDATE_REQUIRED")
            value=preflight(args.game,args.candidate)
        elif args.mode=="install":
            if not args.candidate:
                raise Hold("R37_SOURCE_CANDIDATE_REQUIRED")
            print("R37 replaces only the R33 passive observer. NO weapon switch.")
            token=input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            value=install(args.game,args.candidate,token)
        elif args.mode=="rollback":
            token=input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            value=rollback(args.game,token)
        else:
            print("R37 capture: start game, load existing save and play normally; close game to receive report.")
            value=capture(args.game)
        print(json.dumps(report(args.mode,value),ensure_ascii=False,indent=2))
        return 0
    except (Hold,OSError,UnicodeError,ValueError,subprocess.TimeoutExpired) as err:
        output={"schema":SCHEMA,"status":"R37_STOP_MANUAL_REVIEW",
                "reason":str(err),"noAutoRetry":True,
                "gameModifiedUnknown":args.mode in ("install","rollback"),
                "dispatchAuthorized":False,"weaponSwitchAuthorized":False}
        print(json.dumps(report(args.mode,output),ensure_ascii=False,indent=2))
        return 2

if __name__=="__main__":
    sys.exit(main())
