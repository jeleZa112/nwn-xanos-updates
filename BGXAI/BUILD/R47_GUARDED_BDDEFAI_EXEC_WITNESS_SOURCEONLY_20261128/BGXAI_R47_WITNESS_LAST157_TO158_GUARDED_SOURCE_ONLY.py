#!/usr/bin/env python3
"""BGXAI R47 guarded source-only: preserve original R44, append inert BCS.

NO AUTO INSTALL: only an explicit approved one-file updater typed token can
invoke a WeiDU #158 extension. The BAF always returns false; there are no
gameplay actions, no LOCALS, no XEquip, no second action listener.

The original BDDEFAI.BCS is ALREADY SHA-bound in R37 and the inherited R44
baseline PROOF; this code reuses that provenance rather than new scans or BIF
extraction. If it is absent or changed, installation FAILS CLOSED.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
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

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R44_PATH=REPO/"BGXAI/BUILD/R44_R43_ACTOR_NUMERIC_ID_LAST157_20261128/BGXAI_R44_GUARDED_LAST156_SOURCE_ONLY.py"
COMPOSE_PATH=HERE/"BGXAI_R47_CORRECT_R46_EEEX_SCRIPT_PORT_SOURCE_ONLY.py"
R44_BLOB="6d02ea8e085da7dce1bb16965b3823c2a9f9e029"
COMPOSE_BLOB="196f83ae74e298849c628f1738e1879287aa0712"
SCHEMA="BGXAI_R47_INERT_BDDEFAI_EXEC_WITNESS_LAST158_V1"
ROOT=Path(r"C:\Games\BG_EET_FOXX_NEW")
DIR="BGXR47"
STAGED_BAF=DIR+"/staged/BGX_R46_WITNESS.baf"
STAGED_LUA=DIR+"/staged/M_BGXR46_WITNESS.lua"
TP2=DIR+"/setup-BGXR47.tp2"
EXE=DIR+"/setup-BGXR47.exe"
PROOF=DIR+"/PROOF.json"
SOURCE_BCS="override/BDDEFAI.BCS"
SOURCE_LUA="override/M_BGXR46_WITNESS.lua"
R44_ACTIVE_LUA="override/M_BGXR27.lua"
INSTALL_TOKEN="INSTALL_BGXAI_R47_INERT_BDDEFAI_WITNESS_AFTER_R44_LAST"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R47_RESTORE_R44_ONLY"
EXPECTED_BAF_SHA="af9c78d00dd24806c694e7ee1d6fe882a65b8a9fd71acc90654f60188932a0d9"
EXPECTED_LUA_SHA="f095193e77b2a9ec5d8f21edf738a805c462656e58df41b9199ff9b2ac4da256"
EXPECTED_BAF_BYTES=223
EXPECTED_LUA_BYTES=2232
BASELINE_BCS_SHA="24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331"
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR47[/\\]SETUP-BGXR47[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
TP2_TEXT=(
    "BACKUP ~BGXR47/backup~\n"
    "AUTHOR ~BGXAI R47 read-only BCS evaluation witness~\n"
    "BEGIN ~BGXR47 inert BDDEFAI BCS witness (NO EQUIP/ARM)~\n"
    "COPY ~BGXR47/staged/M_BGXR46_WITNESS.lua~ ~override/M_BGXR46_WITNESS.lua~\n"
    "EXTEND_TOP ~BDDEFAI.BCS~ ~BGXR47/staged/BGX_R46_WITNESS.baf~\n"
)

class Hold(ValueError):
    pass

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def checked_import(path:Path,pinned:str,name:str):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=pinned:
        raise Hold("HOLD_PINNED_R47_SOURCE:"+name)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R47_MODULE_IMPORT:"+name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def load_checked():
    r44=checked_import(R44_PATH,R44_BLOB,"r47_verified_original_r44")
    composer=checked_import(COMPOSE_PATH,COMPOSE_BLOB,"r47_verified_corrected_witness")
    r43,r42,r38,old,_=r44.load_checked()
    fragments=composer.source_only()
    if (len(fragments["BAF"])!=EXPECTED_BAF_BYTES or
        sha(fragments["BAF"])!=EXPECTED_BAF_SHA or
        len(fragments["LUA"])!=EXPECTED_LUA_BYTES or
        sha(fragments["LUA"])!=EXPECTED_LUA_SHA):
        raise Hold("HOLD_R47_SOURCE_INERT_WITNESS_BYTES")
    if fragments["BAF"].count(b"EEex_LuaTrigger(")!=1:
        raise Hold("HOLD_R47_INERT_BAF_STRUCTURE")
    if fragments["LUA"].count(b"EEex_AIBase_GetScriptLevelResRef")!=1:
        raise Hold("HOLD_R47_REAL_EEEX_PORT_NOT_USED")
    return r44,r43,r42,r38,old,composer

def before_change(r44,r43,r42,r38,old,composer,game):
    old.protected_root(game,True)
    r42.check_processes(r38,old)
    r44.exact_last_r44(r43,r42,r38,old,game)
    proof=r44.exact_proof(old,game)
    baseline=proof.get("baselineSnapshot")
    if not isinstance(baseline,dict) or baseline.get(SOURCE_BCS)!=BASELINE_BCS_SHA:
        raise Hold("HOLD_R47_ORIGINAL_BCS_SHA_NOT_IN_R44_PROOF")
    if not old.safe(game,SOURCE_BCS).is_file() or old.sha(old.safe(game,SOURCE_BCS))!=BASELINE_BCS_SHA:
        raise Hold("HOLD_R47_ORIGINAL_BCS_BYTES_NOT_EXACT")
    for rel in (DIR,STAGED_BAF,STAGED_LUA,TP2,EXE,PROOF,SOURCE_LUA):
        if old.safe(game,rel).exists():
            raise Hold("HOLD_R47_STAGING_ALREADY_PRESENT:"+rel)
    compiler=old.safe(game,"setup-enhanced-powergaming-scripts.exe")
    if (compiler.is_symlink() or not compiler.is_file() or
        old.sha(compiler)!=r42.WEIDU_SHA):
        raise Hold("HOLD_R47_NATIVE_WEIDU_DRIFT")
    snapshot=watched_snapshot(r44,r43,r42,r38,old,game)
    old.verify_snapshot(game,snapshot)
    if sha(composer.source_only()["LUA"])!=EXPECTED_LUA_SHA:
        raise Hold("HOLD_R47_LUA_SOURCE_DRIFT")
    return {"schema":SCHEMA,"status":"R47_PREFLIGHT_R44_LAST157_PASS_NO_INSTALL",
        "originalBcsSha256":BASELINE_BCS_SHA,"expectedLuaSha256":EXPECTED_LUA_SHA,
        "expectedBafSha256":EXPECTED_BAF_SHA,"installed":False,"gameModified":False,
        "ordersSent":0,"armAuthorized":False,"dispatchAuthorized":False,
        "actualBcsExecutionVerified":False}

def watched_snapshot(r44,r43,r42,r38,old,game):
    proof=r44.exact_proof(old,game)
    prior=proof.get("baselineSnapshot")
    if not isinstance(prior,dict) or prior.get(SOURCE_BCS)!=BASELINE_BCS_SHA:
        raise Hold("HOLD_R47_BCS_ANCESTRY_MISSING")
    observed=dict(prior)
    observed["WeiDU.log"]=old.sha(old.safe(game,"WeiDU.log"))
    observed[R44_ACTIVE_LUA]=r44.EXPECTED_SHA
    observed[r44.PROOF]=old.sha(old.safe(game,r44.PROOF))
    if r43.PROOF not in observed or r42.PROOF not in observed:
        raise Hold("HOLD_R47_R42_R43_ANCESTRY_MISSING")
    old.verify_snapshot(game,observed)
    return observed

def external_backup(old,game,snapshot):
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_R47_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("HOLD_R47_BACKUP_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix="PRE_BGXR47_",dir=parent))
    for rel,digest in snapshot.items():
        src=old.safe(game,rel)
        dst=old.safe(backup,rel)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if old.sha(dst)!=digest:
            raise Hold("HOLD_R47_EXTERNAL_BACKUP_SHA:"+rel)
    old.safe(backup,"SHA256.json").write_text(json.dumps(snapshot,indent=2),encoding="utf-8")
    return backup

def native_weidu(old,game,r42,uninstall=False):
    exe=old.safe(game,EXE)
    if exe.is_symlink() or not exe.is_file() or old.sha(exe)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R47_WEIDU_BINARY_SHA")
    args=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(game),
          "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    res=subprocess.run(args,cwd=game,stdin=subprocess.DEVNULL,
                       capture_output=True,text=True,errors="replace",
                       timeout=240,check=False)
    output=(res.stdout or "")+"\n"+(res.stderr or "")
    if res.returncode!=0 or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",output):
        raise Hold("HOLD_R47_NATIVE_WEIDU_MANUAL_REVIEW")

def exact_last_r47(r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,loghash=old.history(game)
    if (len(rows)!=158 or not old.last_r37_history(rows[:153]) or
        r38.LAST.match(rows[153]) is None or
        r42.LAST.match(rows[154]) is None or
        r43.LAST.match(rows[155]) is None or
        r44.LAST.match(rows[156]) is None or LAST.match(rows[157]) is None):
        raise Hold("HOLD_R47_NOT_WEIDU_LAST_158")
    if old.sha(old.safe(game,R44_ACTIVE_LUA))!=r44.EXPECTED_SHA:
        raise Hold("HOLD_R47_ORIGINAL_R44_LUA_DRIFT")
    return rows,loghash

def exact_proof(old,game):
    path=old.safe(game,PROOF)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>1_000_000:
        raise Hold("HOLD_R47_PROOF_MISSING")
    proof=json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(proof,dict) or proof.get("schema")!=SCHEMA or
        proof.get("status")!="R47_INERT_BDDEFAI_WITNESS_INSTALLED_AWAITING_LIVE" or
        proof.get("typedInstallApproved") is not True or
        proof.get("sourceBafSha256")!=EXPECTED_BAF_SHA or
        proof.get("sourceLuaSha256")!=EXPECTED_LUA_SHA or
        proof.get("installed") is not True or
        proof.get("ordersSent")!=0 or
        proof.get("armAuthorized") is not False or
        proof.get("dispatchAuthorized") is not False):
        raise Hold("HOLD_R47_PROOF_INVALID")
    return proof

def install(r44,r43,r42,r38,old,composer,game,token):
    if token!=INSTALL_TOKEN:
        raise Hold("HOLD_R47_EXACT_TYPED_INSTALL_REQUIRED")
    before_change(r44,r43,r42,r38,old,composer,game)
    snapshot=watched_snapshot(r44,r43,r42,r38,old,game)
    backup=external_backup(old,game,snapshot)
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    src=composer.source_only()
    old.safe(game,DIR).mkdir(parents=True,exist_ok=False)
    old.safe(game,STAGED_BAF).parent.mkdir(parents=True,exist_ok=False)
    old.safe(game,STAGED_BAF).write_bytes(src["BAF"])
    old.safe(game,STAGED_LUA).write_bytes(src["LUA"])
    old.safe(game,TP2).write_text(TP2_TEXT,encoding="ascii",newline="\n")
    shutil.copy2(old.safe(game,"setup-enhanced-powergaming-scripts.exe"),
                 old.safe(game,EXE))
    if (old.sha(old.safe(game,STAGED_BAF))!=EXPECTED_BAF_SHA or
        old.sha(old.safe(game,STAGED_LUA))!=EXPECTED_LUA_SHA or
        old.sha(old.safe(game,EXE))!=r42.WEIDU_SHA):
        raise Hold("HOLD_R47_STAGED_SHA_DRIFT")
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    target=old.safe(game,PROOF)
    target.write_text(json.dumps({"schema":SCHEMA,"status":"R47_PENDING_WEIDU",
        "baselineSnapshot":snapshot,"externalBackup":str(backup),
        "sourceBafSha256":EXPECTED_BAF_SHA,"sourceLuaSha256":EXPECTED_LUA_SHA},
        indent=2),encoding="utf-8")
    # Potential native game mutation STARTS HERE: never auto-retry or auto-rollback.
    native_weidu(old,game,r42)
    exact_last_r47(r44,r43,r42,r38,old,game)
    bcs=old.safe(game,SOURCE_BCS)
    lua=old.safe(game,SOURCE_LUA)
    if (not bcs.is_file() or bcs.is_symlink() or
        old.sha(bcs)==BASELINE_BCS_SHA or
        not lua.is_file() or lua.is_symlink() or old.sha(lua)!=EXPECTED_LUA_SHA):
        raise Hold("HOLD_R47_NATIVE_BCS_OR_LUA_NOT_EXTENDED")
    for rel,digest in snapshot.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R47_UNRELATED_FILE_CHANGED:"+rel)
    result={"schema":SCHEMA,"status":"R47_INERT_BDDEFAI_WITNESS_INSTALLED_AWAITING_LIVE",
        "baselineSnapshot":snapshot,"externalBackup":str(backup),
        "sourceBafSha256":EXPECTED_BAF_SHA,"sourceLuaSha256":EXPECTED_LUA_SHA,
        "installedBcsSha256":old.sha(bcs),"typedInstallApproved":True,
        "installed":True,"gameModified":True,"ordersSent":0,"localsWritten":0,
        "armAuthorized":False,"dispatchAuthorized":False,
        "actualBcsExecutionVerified":False,"manualEpsActionOriginVerified":False}
    target.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

def rollback(r44,r43,r42,r38,old,game,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold("HOLD_R47_EXACT_TYPED_ROLLBACK_REQUIRED")
    exact_last_r47(r44,r43,r42,r38,old,game)
    r42.check_processes(r38,old)
    proof=exact_proof(old,game)
    backup=Path(proof.get("externalBackup",""))
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R47_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if (backup.parent!=parent or not backup.name.startswith("PRE_BGXR47_") or
        not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R47_EXTERNAL_BACKUP_PROVENANCE")
    saved=json.loads(old.safe(backup,"SHA256.json").read_text(encoding="utf-8"))
    if (saved!=proof.get("baselineSnapshot") or
        saved.get(SOURCE_BCS)!=BASELINE_BCS_SHA or
        saved.get(R44_ACTIVE_LUA)!=r44.EXPECTED_SHA or
        r44.PROOF not in saved or r43.PROOF not in saved or r42.PROOF not in saved):
        raise Hold("HOLD_R47_EXTERNAL_BACKUP_MANIFEST_MISMATCH")
    old.verify_snapshot(backup,saved)
    if (old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSha256") or
        old.sha(old.safe(game,SOURCE_LUA))!=EXPECTED_LUA_SHA):
        raise Hold("HOLD_R47_INSTALLED_WITNESS_RESOURCE_DRIFT")
    for rel,digest in saved.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R47_UNRELATED_FILE_DRIFT:"+rel)
    r42.check_processes(r38,old)
    native_weidu(old,game,r42,uninstall=True)
    r44.exact_last_r44(r43,r42,r38,old,game)
    r44.exact_proof(old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=BASELINE_BCS_SHA or old.safe(game,SOURCE_LUA).exists():
        raise Hold("HOLD_R47_ROLLBACK_BCS_OR_LUA_MISMATCH")
    for rel,digest in saved.items():
        if rel!="WeiDU.log" and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R47_ROLLBACK_WATCHED_DRIFT:"+rel)
    return {"schema":SCHEMA,"status":"R47_ROLLBACK_RESTORED_R44_LAST",
        "installed":False,"gameModified":True,"ordersSent":0,
        "armAuthorized":False,"dispatchAuthorized":False}

def status(r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if len(rows)==158 and LAST.match(rows[-1]):
        exact_last_r47(r44,r43,r42,r38,old,game)
        proof=exact_proof(old,game)
        if (old.sha(old.safe(game,SOURCE_LUA))==EXPECTED_LUA_SHA and
            old.sha(old.safe(game,SOURCE_BCS))==proof.get("installedBcsSha256")):
            return {"schema":SCHEMA,"status":"R47_PRESENT_LAST_PASSIVE_WITNESS",
                "installed":True,"gameModified":False,"ordersSent":0,
                "armAuthorized":False,"dispatchAuthorized":False,
                "actualBcsExecutionVerified":False}
    elif len(rows)==157:
        r44.exact_last_r44(r43,r42,r38,old,game)
        r44.exact_proof(old,game)
        return {"schema":SCHEMA,"status":"R47_NOT_INSTALLED_R44_PRESENT_LAST",
            "installed":False,"gameModified":False,"ordersSent":0,
            "armAuthorized":False,"dispatchAuthorized":False}
    return {"schema":SCHEMA,"status":"R47_HOLD_WEIDU_OR_BCS_DRIFT",
        "installed":False,"gameModified":False,"ordersSent":0,
        "armAuthorized":False,"dispatchAuthorized":False,"noAutoRetry":True}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,default=ROOT)
    p.add_argument("--mode",choices=("status","preflight","install","rollback"),default="status")
    p.add_argument("--onefile-review-gate",action="store_true")
    args=p.parse_args(argv)
    try:
        r44,r43,r42,r38,old,composer=load_checked()
        if args.mode=="status":
            out=status(r44,r43,r42,r38,old,args.game)
        elif args.mode=="preflight":
            out=before_change(r44,r43,r42,r38,old,composer,args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_R47_SAME_ONEFILE_REVIEW_REQUIRED")
        elif args.mode=="install":
            token=input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            out=install(r44,r43,r42,r38,old,composer,args.game,token)
        else:
            token=input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            out=rollback(r44,r43,r42,r38,old,args.game,token)
        rc=3 if ("HOLD" in out["status"] or "STOP" in out["status"]) else 0
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired,EOFError) as error:
        out={"schema":SCHEMA,"status":"R47_STOP_MANUAL_REVIEW",
            "reason":str(error) if isinstance(error,Hold) else "HOLD_RUNTIME_OR_IO",
            "gameModifiedUnknown":args.mode in ("install","rollback"),
            "noAutoRetry":True,"ordersSent":0,"armAuthorized":False,
            "dispatchAuthorized":False}
        rc=3
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return rc

if __name__=="__main__":
    sys.exit(main())
