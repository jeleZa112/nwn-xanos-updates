#!/usr/bin/env python3
"""BGXAI R44 R43(last156)->R44(last157), guarded source-only successor.

This source does not install when imported or run without a separate
single-updater-approved typed token. Reuse exact R43 last/PROOF and R42/R38/R37
provenance checks. No arming, no weapon change, no extra EEex listener, no
LOCALS. SOURCE CI DOES NOT MEAN LIVE USABILITY OR BCS EXECUTION.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R43_PATH=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_DIAG_UPGRADE_GUARDED_SOURCE_ONLY.py"
R44_COMPOSE_PATH=HERE/"BGXAI_R44_COMPOSE_FROM_R43_SOURCE_ONLY.py"
R43_BLOB="b07c04efa1394a03a08550238ecf7eea1236b7bd"
COMPOSE_BLOB="9c26e66218fcf3e7e2fda3d1785c49e848833a39"
SCHEMA="BGXAI_R44_NUMERIC_ACTOR_ID_GUARDED_LAST157_V1"
EXPECTED_SIZE=96410
EXPECTED_SHA="bae25741c3ee620a184ddddcd0a7b59b82d835bd7f5766d5911459baedfe8600"
ROOT=Path(r"C:\Games\BG_EET_FOXX_NEW")
DIR="BGXR44"
STAGED=DIR+"/staged/M_BGXR27.lua"
TP2=DIR+"/setup-BGXR44.tp2"
EXE=DIR+"/setup-BGXR44.exe"
PROOF=DIR+"/PROOF.json"
OVERRIDE="override/M_BGXR27.lua"
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR44[/\\]SETUP-BGXR44[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
INSTALL_TOKEN="INSTALL_BGXAI_R44_READONLY_NUMERIC_ACTOR_AFTER_R43_LAST"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R44_RESTORE_R43_ONLY"
TP2_TEXT=(
    "BACKUP ~BGXR44/backup~\n"
    "AUTHOR ~BGXAI R44 safe numeric actor ID guard~\n"
    "BEGIN ~BGXR44 read-only one-listener numeric actor guard~\n"
    "COPY ~BGXR44/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~\n"
)
class Hold(ValueError):
    pass

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(path,pinned,name):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=pinned:
        raise Hold("HOLD_PINNED_SOURCE_BLOB:"+name)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_SOURCE_MODULE:"+name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def load_checked():
    r43=load(R43_PATH,R43_BLOB,"bgxai_verified_r43_guard")
    composer=load(R44_COMPOSE_PATH,COMPOSE_BLOB,"bgxai_verified_r44_compose")
    r42,diag,r38,old=r43.load_checked()
    candidate=composer.compose()
    if len(candidate)!=EXPECTED_SIZE or sha(candidate)!=EXPECTED_SHA:
        raise Hold("HOLD_R44_SOURCE_COMPOSED_SHA")
    if len(diag.compose())!=r43.EXPECTED_SIZE or sha(diag.compose())!=r43.EXPECTED_SHA:
        raise Hold("HOLD_R43_LIVE_PREDECESSOR_SOURCE_DRIFT")
    return r43,r42,r38,old,composer

def candidate_bytes(composer):
    data=composer.compose()
    if len(data)!=EXPECTED_SIZE or sha(data)!=EXPECTED_SHA:
        raise Hold("HOLD_R44_CANDIDATE_SHA")
    if data.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener")!=1:
        raise Hold("HOLD_R44_LISTENER_COUNT")
    if data.count(b"[BGXBCS]")!=1 or data.count(b"R27.r42Once=true")!=1:
        raise Hold("HOLD_R44_ONE_SHOT_COUNT")
    for marker in (b'"ordersSent":0',b'"localsWritten":0',
                   b'"armAuthorized":false',b'"dispatchAuthorized":false',
                   b'"actualBcsExecutionVerified":false'):
        if marker not in data:
            raise Hold("HOLD_R44_READONLY_MARKER_MISSING")
    return data

def exact_last_r44(r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,loghash=old.history(game)
    if (len(rows)!=157 or not old.last_r37_history(rows[:153]) or
        r38.LAST.match(rows[153]) is None or
        r42.LAST.match(rows[154]) is None or
        r43.LAST.match(rows[155]) is None or LAST.match(rows[156]) is None):
        raise Hold("HOLD_R44_NOT_WEIDU_LAST_157")
    if old.sha(old.safe(game,OVERRIDE))!=EXPECTED_SHA:
        raise Hold("HOLD_R44_ACTIVE_LUA_SHA_DRIFT")
    return rows,loghash

def exact_proof(old,game):
    target=old.safe(game,PROOF)
    if not target.is_file() or target.is_symlink() or target.stat().st_size>1_000_000:
        raise Hold("HOLD_R44_PROOF_MISSING")
    d=json.loads(target.read_text(encoding="utf-8"))
    if (type(d) is not dict or d.get("schema")!=SCHEMA or
        d.get("status")!="R44_READONLY_NUMERIC_ACTOR_INSTALLED_AWAITING_LIVE" or
        d.get("sourceSha256")!=EXPECTED_SHA or
        d.get("typedInstallApproved") is not True or d.get("installed") is not True or
        d.get("armAuthorized") is not False or
        d.get("dispatchAuthorized") is not False or d.get("ordersSent")!=0):
        raise Hold("HOLD_R44_PROOF_INVALID")
    return d

def watched_baseline(r43,r42,r38,old,game):
    # Use EXACT R43 installed PROOF, not the obsolete R42 preinstall snapshot.
    proof=r43.exact_proof(old,game)
    saved=proof.get("baselineSnapshot")
    if type(saved) is not dict or not saved or saved.get(OVERRIDE)!=r42.CANDIDATE_SHA:
        raise Hold("HOLD_R43_ORIGINAL_WATCHED_SNAPSHOT_INVALID")
    for rel,digest in saved.items():
        if type(rel) is not str or re.fullmatch(r"[A-Za-z0-9_./-]+",rel) is None:
            raise Hold("HOLD_WATCHED_RELATIVE_PATH")
        if rel in ("WeiDU.log",OVERRIDE):
            continue
        if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise Hold("HOLD_WATCHED_SHA_FORMAT")
        if old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_UNRELATED_SOURCE_CHANGED:"+rel)
    observed=dict(saved)
    observed["WeiDU.log"]=old.sha(old.safe(game,"WeiDU.log"))
    observed[OVERRIDE]=r43.EXPECTED_SHA
    observed[r43.PROOF]=old.sha(old.safe(game,r43.PROOF))
    if r42.PROOF not in observed:
        raise Hold("HOLD_ANCESTOR_R42_PROOF_NOT_WATCHED")
    old.verify_snapshot(game,observed)
    return observed

def before_change(r43,r42,r38,old,composer,game):
    old.protected_root(game,True)
    r42.check_processes(r38,old)
    r43.exact_last_r43(r42,r38,old,game)
    r43.exact_proof(old,game)
    for rel in (DIR,STAGED,TP2,EXE,PROOF):
        if old.safe(game,rel).exists():
            raise Hold("HOLD_R44_STAGING_ALREADY_PRESENT:"+rel)
    snapshot=watched_baseline(r43,r42,r38,old,game)
    old.verify_snapshot(game,snapshot)
    native=old.safe(game,"setup-enhanced-powergaming-scripts.exe")
    if not native.is_file() or native.is_symlink() or old.sha(native)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R44_NATIVE_WEIDU_DRIFT")
    candidate_bytes(composer)
    return {"schema":SCHEMA,"status":"R44_PREFLIGHT_LAST156_PASS_NO_INSTALL",
        "expectedDiagnosticSha256":EXPECTED_SHA,"expectedDiagnosticBytes":EXPECTED_SIZE,
        "installed":False,"gameModified":False,"ordersSent":0,
        "dispatchAuthorized":False,"armAuthorized":False,
        "actualBcsExecutionVerified":False}

def external_backup(old,game,snapshot):
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("HOLD_R44_BACKUP_PARENT_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix="PRE_BGXR44_",dir=parent))
    for rel,digest in snapshot.items():
        src=old.safe(game,rel);dst=old.safe(backup,rel)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if old.sha(dst)!=digest:
            raise Hold("HOLD_R44_BACKUP_SHA:"+rel)
    old.safe(backup,"SHA256.json").write_text(json.dumps(snapshot,indent=2),encoding="utf-8")
    return backup

def native_weidu(old,game,r42,uninstall=False):
    exe=old.safe(game,EXE)
    if not exe.is_file() or exe.is_symlink() or old.sha(exe)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R44_WEIDU_EXE_SHA")
    args=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(game),
          "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    res=subprocess.run(args,cwd=game,stdin=subprocess.DEVNULL,
                       capture_output=True,text=True,errors="replace",
                       timeout=240,check=False)
    out=(res.stdout or "")+"\n"+(res.stderr or "")
    if res.returncode or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",out):
        raise Hold("HOLD_R44_NATIVE_WEIDU_MANUAL_REVIEW")

def install(r43,r42,r38,old,composer,game,token):
    if token!=INSTALL_TOKEN:
        raise Hold("HOLD_R44_EXACT_TYPED_INSTALL_REQUIRED")
    before_change(r43,r42,r38,old,composer,game)
    snapshot=watched_baseline(r43,r42,r38,old,game)
    old.verify_snapshot(game,snapshot)
    backup=external_backup(old,game,snapshot)
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    source=candidate_bytes(composer)
    old.safe(game,DIR).mkdir(parents=True,exist_ok=False)
    old.safe(game,STAGED).parent.mkdir(parents=True,exist_ok=False)
    old.safe(game,STAGED).write_bytes(source)
    old.safe(game,TP2).write_text(TP2_TEXT,encoding="ascii",newline="\n")
    shutil.copy2(old.safe(game,"setup-enhanced-powergaming-scripts.exe"),old.safe(game,EXE))
    if old.sha(old.safe(game,STAGED))!=EXPECTED_SHA or old.sha(old.safe(game,EXE))!=r42.WEIDU_SHA:
        raise Hold("HOLD_R44_STAGED_BYTES_SHA")
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    proof=old.safe(game,PROOF)
    proof.write_text(json.dumps({"schema":SCHEMA,"status":"R44_PENDING_WEIDU",
        "sourceSha256":EXPECTED_SHA,"baselineSnapshot":snapshot,
        "externalBackup":str(backup)},indent=2),encoding="utf-8")
    # Potential game mutation begins below; never auto-retry or auto-rollback.
    native_weidu(old,game,r42)
    exact_last_r44(r43,r42,r38,old,game)
    for rel,digest in snapshot.items():
        if rel not in ("WeiDU.log",OVERRIDE) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R44_UNRELATED_FILE_CHANGED:"+rel)
    result={"schema":SCHEMA,"status":"R44_READONLY_NUMERIC_ACTOR_INSTALLED_AWAITING_LIVE",
        "sourceSha256":EXPECTED_SHA,"externalBackup":str(backup),
        "baselineSnapshot":snapshot,"typedInstallApproved":True,
        "installed":True,"gameModified":True,"ordersSent":0,"localsWritten":0,
        "dispatchAuthorized":False,"armAuthorized":False,
        "actualBcsExecutionVerified":False,"manualEpsActionOriginVerified":False,
        "classScriptResrefAtLiveJaganVerified":False}
    proof.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

def rollback(r43,r42,r38,old,game,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold("HOLD_R44_EXACT_TYPED_ROLLBACK_REQUIRED")
    exact_last_r44(r43,r42,r38,old,game)
    r42.check_processes(r38,old)
    proof=exact_proof(old,game)
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    backup=Path(proof.get("externalBackup",""))
    if (backup.parent!=parent or not backup.name.startswith("PRE_BGXR44_") or
        not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R44_BACKUP_PROVENANCE")
    saved=json.loads(old.safe(backup,"SHA256.json").read_text(encoding="utf-8"))
    if (saved!=proof.get("baselineSnapshot") or saved.get(OVERRIDE)!=r43.EXPECTED_SHA
        or r43.PROOF not in saved or r42.PROOF not in saved):
        raise Hold("HOLD_R44_BACKUP_MANIFEST_MISMATCH")
    old.verify_snapshot(backup,saved)
    for rel,digest in saved.items():
        if rel not in ("WeiDU.log",OVERRIDE) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R44_UNRELATED_FILE_DRIFT:"+rel)
    r42.check_processes(r38,old)
    native_weidu(old,game,r42,uninstall=True)
    r43.exact_last_r43(r42,r38,old,game)
    r43.exact_proof(old,game)
    for rel,digest in saved.items():
        if rel not in ("WeiDU.log",OVERRIDE) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R44_ROLLBACK_UNRELATED_DRIFT:"+rel)
    return {"schema":SCHEMA,"status":"R44_ROLLBACK_RESTORED_R43_LAST",
            "installed":False,"gameModified":True,"ordersSent":0,
            "dispatchAuthorized":False,"armAuthorized":False}

def status(r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if (len(rows)==157 and old.last_r37_history(rows[:153]) and
        r38.LAST.match(rows[153]) and r42.LAST.match(rows[154]) and
        r43.LAST.match(rows[155]) and LAST.match(rows[156]) and
        old.sha(old.safe(game,OVERRIDE))==EXPECTED_SHA):
        exact_proof(old,game)
        return {"schema":SCHEMA,"status":"R44_PRESENT_LAST_READONLY",
                "installed":True,"gameModified":False,
                "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False}
    if (len(rows)==156 and old.last_r37_history(rows[:153]) and
        r38.LAST.match(rows[153]) and r42.LAST.match(rows[154]) and
        r43.LAST.match(rows[155]) and
        old.sha(old.safe(game,OVERRIDE))==r43.EXPECTED_SHA):
        r43.exact_proof(old,game)
        return {"schema":SCHEMA,"status":"R44_NOT_INSTALLED_R43_PRESENT_LAST",
                "installed":False,"gameModified":False,
                "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False}
    return {"schema":SCHEMA,"status":"R44_HOLD_WEIDU_OR_LUA_DRIFT",
            "installed":False,"gameModified":False,
            "ordersSent":0,"dispatchAuthorized":False,"armAuthorized":False}

def capture(r43,r42,r38,old,game):
    exact_last_r44(r43,r42,r38,old,game)
    exact_proof(old,game)
    r42.check_processes(r38,old)
    loader=old.safe(game,"InfinityLoader.exe")
    if loader.is_symlink() or not loader.is_file() or not 1024<loader.stat().st_size<70_000_000:
        raise Hold("HOLD_R44_LOADER_SIZE")
    with loader.open("rb") as f:
        if f.read(2)!=b"MZ":raise Hold("HOLD_R44_LOADER_SIGNATURE")
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_LIVE_REPORTS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("HOLD_R44_LOG_PARENT_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    target=parent/("BGXAI_R44_CLASS_NUMERIC_ID_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".log")
    with target.open("xb") as f:
        child=subprocess.Popen([str(loader)],cwd=game,stdin=subprocess.DEVNULL,
                               stdout=f,stderr=subprocess.STDOUT,close_fds=True)
        code=child.wait();f.flush()
    exact_last_r44(r43,r42,r38,old,game)
    out=r43.parse_diag_console(r42,target,code)
    out["rawConsoleFile"]=str(target)
    out["rawConsoleBytes"]=target.stat().st_size
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,default=ROOT)
    p.add_argument("--mode",choices=("status","preflight","install","rollback","capture"),default="status")
    p.add_argument("--onefile-review-gate",action="store_true")
    args=p.parse_args(argv)
    try:
        r43,r42,r38,old,composer=load_checked()
        if args.mode=="status":
            out=status(r43,r42,r38,old,args.game)
        elif args.mode=="preflight":
            out=before_change(r43,r42,r38,old,composer,args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_NOT_CONNECTED_TO_EXISTING_ONEFILE")
        elif args.mode=="install":
            token=input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            out=install(r43,r42,r38,old,composer,args.game,token)
        elif args.mode=="rollback":
            token=input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            out=rollback(r43,r42,r38,old,args.game,token)
        else:
            out=capture(r43,r42,r38,old,args.game)
        rc=3 if ("HOLD" in out["status"] or out["status"]=="R44_STOP_MANUAL_REVIEW") else 0
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired,EOFError) as error:
        out={"schema":SCHEMA,"status":"R44_STOP_MANUAL_REVIEW",
             "reason":str(error) if isinstance(error,Hold) else "HOLD_RUNTIME_OR_IO",
             "gameModifiedUnknown":args.mode in ("install","rollback"),
             "noAutoRetry":True,"ordersSent":0,
             "dispatchAuthorized":False,"armAuthorized":False}
        rc=3
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return rc

if __name__=="__main__":
    sys.exit(main())
