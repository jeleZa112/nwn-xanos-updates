#!/usr/bin/env python3
"""BGXAI V5 guarded 6/10 defensive handoff. Native exact-pinned WeiDU LAST only.

Uses the already user-verified 135 preview baseline. Installation requires
typed consent, safe backups OUTSIDE the game, exact native compile and only
two changed BDDEFAI BCS blocks. Does not clear attack queues or promise live
latency improvement; native install is only a controlled gameplay pilot.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V5
import BGXFENEMY_WTASIGHT_GUARDED as E

ROOT=V5.GAME
PACKAGE="BGXRANGED5"
TARGET=V5.BCS
STAGED=PACKAGE+"/staged/BDDEFAI.BCS"
PROOF=PACKAGE+"/PROOF.json"
TP2=PACKAGE+"/setup-BGXRANGED5.tp2"
EXE="setup-BGXRANGED5.exe"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXRANGED5[/\\]SETUP-BGXRANGED5[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
TOKEN_INSTALL="INSTALL_BGXRANGED5_ANTICIPATORY_PILOT"
TOKEN_ROLLBACK="ROLLBACK_BGXRANGED5_ANTICIPATORY_PILOT"
EXACT_NEW_SHA="c824794fd8e6c94d30b9e5990d7b674f61dc596b9dcb2774fa6e7f2083fceb1b"
TP2_CONTENT=("BACKUP ~BGXRANGED5/backup~\n"
             "AUTHOR ~BGXAI safe anticipatory melee pilot~\n"
             "BEGIN ~BGXRANGED5 V5 defensive handoff pilot (6/10)~\n"
             "COPY ~BGXRANGED5/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n")
REQUIRED=(
 TARGET,V5.WTASIGHT,"override/PRIEST1.BCS","override/M_BX43.lua",
 "override/M_BXFR.lua","override/DPLAYER.BCS",
 "WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
# Other scripts are checked by the existing BGXFENEMY checker, but its
# BDDEFAI pin applies to the *previous* state only and must be excluded after V5.
IMMUTABLE={k:v for k,v in E.OTHER.items() if k!=TARGET}

def digest(path:pathlib.Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def guard(path:pathlib.Path)->None:
    E.guard(path)

def last(root:pathlib.Path)->str:
    return E.last(root)

def processes()->None:
    E.TRACE.V3.V2.V1.processes()

def checks_before(root:pathlib.Path)->dict:
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    E.common(root)
    if not E.LAST.match(last(root)):raise ValueError("BGXFENEMY_NOT_LAST")
    observed=E.status(root)
    if observed.get("status")!="BGXFENEMY_INSTALLED_VERIFIED":
        raise ValueError("BGXFENEMY_STATUS_NOT_VERIFIED")
    if (root/PACKAGE).exists() or (root/EXE).exists():
        raise ValueError("V5_STAGING_COLLISION")
    if digest(root/TARGET)!=V5.EXACT_BCS_SHA:
        raise ValueError("V5_PREVIOUS_BCS_SHA_MISMATCH")
    for k,v in IMMUTABLE.items():
        p=root/k;guard(p)
        if not p.is_file() or digest(p)!=v:
            raise ValueError("OTHER_SCRIPT_SHA_DRIFT:"+k)
    for path in [*REQUIRED,*OPTIONAL,TP2,STAGED,PROOF,EXE]:
        guard(root/path)
    return {"last_weidu":last(root),"wei_log_sha256":digest(root/"WeiDU.log"),
            "old_bcs_sha256":V5.EXACT_BCS_SHA}

def execute(exe:pathlib.Path,root:pathlib.Path,work:pathlib.Path,
            source:pathlib.Path,dest:pathlib.Path,operation:str)->None:
    if dest.exists():raise ValueError("NATIVE_TEMP_DEST_COLLISION:"+operation)
    cmd=[str(exe),"--game",str(root),"--out",str(dest),str(source)]
    proc=subprocess.run(cmd,cwd=work,stdin=subprocess.DEVNULL,
        capture_output=True,text=True,errors="replace",timeout=180)
    log=(proc.stdout or "")+"\n"+(proc.stderr or "")
    if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("NATIVE_"+operation+"_FAILED:"+log[-600:])
    if not dest.is_file() or dest.is_symlink():
        raise ValueError("NATIVE_"+operation+"_OUTPUT_MISSING")

def build(root:pathlib.Path)->tuple[bytes,dict]:
    """Compile exact source against installed game to TEMP; no installation."""
    basis=checks_before(root)
    original=(root/TARGET).read_bytes()
    if V5.sha(original)!=V5.EXACT_BCS_SHA or len(V5.bcs_parts(original))!=V5.EXPECTED_BLOCKS:
        raise ValueError("BDDEFAI_BCS_BASE_DRIFT")
    for path in (V5.V4,V5.V5):
        if path.is_symlink() or not path.is_file():
            raise ValueError("V5_SOURCE_MISSING")
    old_source=V5.V4.read_bytes()
    new_source=V5.V5.read_bytes()
    if V5.sha(old_source)!=V5.SOURCE_SHA_V4:
        raise ValueError("V4_SOURCE_SHA_DRIFT")
    # Source V5 is itself SHA-locked by the one-file release manifest.
    if V5.sha(new_source)!="010d4a16bd786bf6b67d230a541586650beec79eedcd63d8dde198e4905d6bab":
        raise ValueError("V5_SOURCE_SHA_DRIFT")
    source_exe=root/"setup-enhanced-powergaming-scripts.exe"
    guard(source_exe)
    if not source_exe.is_file() or source_exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("NATIVE_WEIDU_EXE_MISSING")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED5_NATIVE_GUARD_") as folder:
        work=pathlib.Path(folder)
        weidu=work/"weidu.exe";shutil.copy2(source_exe,weidu)
        incoming=work/"BDDEFAI.BCS";incoming.write_bytes(original)
        baf=work/"BDDEFAI.BAF"
        execute(weidu,root,work,incoming,baf,"DECOMPILE")
        decoded=baf.read_text("utf-8-sig",errors="replace")
        # Reuse exactly the native preflight contract proven by menu 135.
        source_validation=V5.source_contract(
            decoded,old_source.decode("utf-8"),new_source.decode("utf-8"))
        candidate_baf=work/"BGXAIW5.BAF";candidate_baf.write_bytes(new_source)
        out=work/"compiled";out.mkdir()
        cmd=[str(weidu),"--game",str(root),"--out",str(out),str(candidate_baf)]
        res=subprocess.run(cmd,cwd=work,stdin=subprocess.DEVNULL,
             capture_output=True,text=True,errors="replace",timeout=180)
        transcript=(res.stdout or "")+"\n"+(res.stderr or "")
        if res.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",transcript):
            raise ValueError("NATIVE_COMPILE_FAILED:"+transcript[-600:])
        files=list(out.rglob("BGXAIW5.BCS"))
        if len(files)!=1 or files[0].is_symlink():raise ValueError("COMPILED_BCS_NOT_ONE")
        candidate,proof=V5.splice_native(original,files[0].read_bytes())
        if proof["changed_blocks"]!=[1,3] or proof["preserved_blocks"]!=1160:
            raise ValueError("NATIVE_BCS_OTHER_BLOCK_CHANGED")
        if V5.sha(candidate)!=EXACT_NEW_SHA:
            raise ValueError("CANDIDATE_BCS_SHA_NOT_PREVIOUSLY_PROVEN")
    if last(root)!=basis["last_weidu"] or digest(root/"WeiDU.log")!=basis["wei_log_sha256"]:
        raise ValueError("WEIDU_INTERLEAVED")
    if digest(root/TARGET)!=V5.EXACT_BCS_SHA:
        raise ValueError("LIVE_BCS_CHANGED_DURING_NATIVE_PREVIEW")
    for k,v in IMMUTABLE.items():
        if digest(root/k)!=v:raise ValueError("OTHER_SCRIPT_CHANGED:"+k)
    return candidate,{**basis,**source_validation,**proof,
                      "candidate_baf_sha256":V5.sha(new_source),
                      "game_modified":False,"live_tested":False}

def preflight(root:pathlib.Path)->dict:
    candidate,info=build(root)
    return {"status":"BGXRANGED5_NATIVE_PREFLIGHT_PASS",
            **info,"source_status":"COMPILED_WITH_NATIVE_WEIDU",
            "candidate_bcs_sha256":V5.sha(candidate),
            "changed_blocks":[1,3],"preserved_blocks":1160,
            "install_performed":False,"game_modified":False}

def snapshot(root:pathlib.Path)->pathlib.Path:
    parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home()))) \
        /"Documents"/"BGXRANGED5_SAFE_BACKUPS"
    guard(parent)
    folder=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y%m%dT%H%M%S%fZ"))
    guard(folder);folder.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name in [*REQUIRED,*OPTIONAL]:
        path=root/name
        guard(path)
        if name in OPTIONAL and not path.exists():continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("BACKUP_SOURCE_MISSING:"+name)
        target=folder/name
        guard(target);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
        hashes[name]=digest(path)
        if digest(target)!=hashes[name]:
            raise ValueError("BACKUP_HASH_MISMATCH:"+name)
    if hashes[TARGET]!=V5.EXACT_BCS_SHA or hashes[V5.WTASIGHT]!=V5.EXACT_WTASIGHT_SHA:
        raise ValueError("BACKUP_BASELINE_NOT_VERIFIED")
    (folder/"SHA256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")
    return folder

def verify_backup(folder:pathlib.Path)->dict:
    guard(folder)
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("BACKUP_FOLDER_UNAVAILABLE")
    manifest=folder/"SHA256.json"
    guard(manifest)
    if not manifest.is_file():raise ValueError("BACKUP_SHA_MANIFEST_MISSING")
    hashes=json.loads(manifest.read_text("utf-8"))
    if hashes.get(TARGET)!=V5.EXACT_BCS_SHA or hashes.get(V5.WTASIGHT)!=V5.EXACT_WTASIGHT_SHA:
        raise ValueError("BACKUP_BASELINE_INVALID")
    if any(k not in (*REQUIRED,*OPTIONAL) for k in hashes):
        raise ValueError("BACKUP_UNEXPECTED_FILE")
    if any(k not in hashes for k in REQUIRED):
        raise ValueError("BACKUP_REQUIRED_MISSING")
    for name,v in hashes.items():
        file=folder/name;guard(file)
        if not file.is_file() or file.is_symlink() or digest(file)!=v:
            raise ValueError("BACKUP_INVALID:"+name)
    return hashes

def run_weidu(root:pathlib.Path,remove:bool=False)->None:
    exe=root/EXE;guard(exe)
    if not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("STAGED_SETUP_MISSING")
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if remove else "--force-install","0"]
    proc=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,
        capture_output=True,text=True,errors="replace",timeout=240)
    log=(proc.stdout or "")+"\n"+(proc.stderr or "")
    if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("WEIDU_MANUAL_REVIEW_STOP:"+log[-800:])

def status(root:pathlib.Path)->dict:
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    E.common(root)
    current=last(root)
    if E.LAST.match(current):
        result=E.status(root)
        if result.get("status")!="BGXFENEMY_INSTALLED_VERIFIED":
            raise ValueError("EXPECTED_BGXFENEMY_VERIFIED")
        return {"status":"BGXRANGED5_NOT_INSTALLED_BGXFENEMY_VERIFIED",
                "game_modified":False}
    if not LAST.match(current):
        raise ValueError("BGXRANGED5_NOT_LAST_WEIDU")
    proof=root/PROOF;guard(proof)
    if not proof.is_file():raise ValueError("V5_INSTALL_PROOF_MISSING")
    record=json.loads(proof.read_text("utf-8"))
    if record.get("previous_sha256")!=V5.EXACT_BCS_SHA or \
       record.get("new_sha256")!=EXACT_NEW_SHA or \
       record.get("source_sha256")!="010d4a16bd786bf6b67d230a541586650beec79eedcd63d8dde198e4905d6bab" or \
       record.get("changed_blocks")!=[1,3]:
        raise ValueError("V5_PROOF_HASH_OR_SOURCE_DRIFT")
    if not isinstance(record.get("backup"),str) or \
        not pathlib.Path(record["backup"]).is_absolute():
        raise ValueError("BACKUP_PROOF_PATH_INVALID")
    check=verify_backup(pathlib.Path(record["backup"]))
    for name,expected in IMMUTABLE.items():
        item=root/name;guard(item)
        if not item.is_file() or digest(item)!=expected:
            raise ValueError("OTHER_SCRIPT_SHA_DRIFT:"+name)
    if digest(root/V5.WTASIGHT)!=V5.EXACT_WTASIGHT_SHA:
        raise ValueError("BGXFENEMY_WTASIGHT_DRIFT")
    live=root/TARGET;staged=root/STAGED
    for file in [live,staged]:
        guard(file)
        if not file.is_file() or digest(file)!=EXACT_NEW_SHA:
            raise ValueError("V5_BCS_OR_STAGING_SHA_DRIFT")
    old_parts=V5.bcs_parts((pathlib.Path(record["backup"])/TARGET).read_bytes())
    new_parts=V5.bcs_parts(live.read_bytes())
    if len(new_parts)!=1162 or len(old_parts)!=1162:
        raise ValueError("V5_BCS_BLOCK_COUNT_DRIFT")
    changes=[i+1 for i,(a,b) in enumerate(zip(old_parts,new_parts)) if a!=b]
    if changes!=[1,3] or any(a!=b for a,b in zip(old_parts[3:],new_parts[3:])):
        raise ValueError("V5_BCS_OTHER_BLOCKS_CHANGED")
    for tlk in OPTIONAL:
        if tlk in check and digest(root/tlk)!=check[tlk]:
            raise ValueError("DIALOG_TLK_CHANGED:"+tlk)
    return {"status":"BGXRANGED5_INSTALLED_VERIFIED",
        "old_sha256":V5.EXACT_BCS_SHA,"new_sha256":EXACT_NEW_SHA,
        "changed_blocks":[1,3],"preserved_blocks":1160,
        "bgxfenemy_wtasight_preserved":True,
        "game_modified":False,"live_tested":False}

def install(root:pathlib.Path)->dict:
    processes()
    checks=checks_before(root)
    candidate,pf=build(root)
    before_log=digest(root/"WeiDU.log")
    backup=snapshot(root)
    processes()
    checks_before(root)
    if before_log!=digest(root/"WeiDU.log") or \
       pf["wei_log_sha256"]!=before_log:
        raise ValueError("WEIDU_CHANGED_AFTER_BACKUP")
    if digest(root/TARGET)!=V5.EXACT_BCS_SHA:
        raise ValueError("BDDEFAI_CHANGED_AFTER_BACKUP")
    stage=root/PACKAGE/"staged"
    guard(stage);stage.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(candidate)
    (root/TP2).write_text(TP2_CONTENT,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({
        "previous_sha256":V5.EXACT_BCS_SHA,
        "new_sha256":EXACT_NEW_SHA,
        "source_sha256":"010d4a16bd786bf6b67d230a541586650beec79eedcd63d8dde198e4905d6bab",
        "changed_blocks":[1,3],"backup":str(backup)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
    processes()
    if not E.LAST.match(last(root)) or digest(root/"WeiDU.log")!=before_log or \
       digest(root/TARGET)!=V5.EXACT_BCS_SHA or \
       digest(root/STAGED)!=EXACT_NEW_SHA:
        raise ValueError("FINAL_PREFLIGHT_SHA_OR_WEIDU_DRIFT")
    for k,v in IMMUTABLE.items():
        if digest(root/k)!=v:raise ValueError("OTHER_SCRIPT_CHANGED_PRE_INSTALL:"+k)
    run_weidu(root)
    checked=status(root)
    if checked.get("status")!="BGXRANGED5_INSTALLED_VERIFIED":
        raise ValueError("V5_POSTINSTALL_STATUS_FAILED")
    return dict(checked,game_modified=True,backup=str(backup))

def rollback(root:pathlib.Path)->dict:
    processes()
    if not LAST.match(last(root)):raise ValueError("V5_NOT_LAST_WEIDU")
    if status(root).get("status")!="BGXRANGED5_INSTALLED_VERIFIED":
        raise ValueError("V5_STATUS_NOT_VERIFIED")
    proof=json.loads((root/PROOF).read_text("utf-8"))
    verify_backup(pathlib.Path(proof["backup"]))
    processes()
    if not LAST.match(last(root)):raise ValueError("WEIDU_CHANGED_BEFORE_ROLLBACK")
    run_weidu(root,remove=True)
    if not E.LAST.match(last(root)) or digest(root/TARGET)!=V5.EXACT_BCS_SHA:
        raise ValueError("BGXFENEMY_NOT_RESTORED")
    if E.status(root).get("status")!="BGXFENEMY_INSTALLED_VERIFIED":
        raise ValueError("BGXFENEMY_STATUS_NOT_RESTORED")
    return {"status":"BGXRANGED5_ROLLBACK_VERIFIED_BGXFENEMY_RESTORED",
            "restored_bcs_sha256":V5.EXACT_BCS_SHA,"game_modified":True}

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("mode",nargs="?",choices=("preflight","status","install","rollback"))
    p.add_argument("--game",default=str(ROOT))
    args=p.parse_args()
    root=pathlib.Path(args.game)
    try:
        mode=args.mode
        if mode is None:
            print("BGXRANGED5 - guarded 6/10 melee handoff pilot")
            print("1 - native preflight READ ONLY")
            print("2 - install+verify (typed consent required)")
            print("3 - status READ ONLY")
            print("4 - rollback (typed consent, last WeiDU only)")
            print("0 - exit, no changes")
            choice=input("V5 choice [0]: ").strip() or "0"
            if choice=="0":return 0
            actions={"1":"preflight","2":"install","3":"status","4":"rollback"}
            if choice not in actions:raise ValueError("INVALID_V5_CHOICE")
            mode=actions[choice]
        if mode=="preflight":result=preflight(root)
        elif mode=="status":result=status(root)
        elif mode=="install":
            if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            result=install(root)
        else:
            if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            result=rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        print("BGXRANGED5_STOP:"+str(exc))
        return 1

if __name__=="__main__":
    sys.exit(main())
