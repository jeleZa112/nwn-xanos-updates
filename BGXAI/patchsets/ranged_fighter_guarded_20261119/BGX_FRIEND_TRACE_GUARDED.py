#!/usr/bin/env python3
"""Opt-in BGXAI passive EEex trace: separate WeiDU component and exact rollback.

Writes only a NEW M_BXFR.lua via WeiDU; no existing BCS, M_BX43, EPS or save
changes. The Lua observer writes its dedicated diagnostic log if Lua io exists.
A successful install does NOT prove the EEex hook will work in game.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V3_GUARDED_INSTALL as V3
import BGX_FRIENDLY_RETALIATION_GUARDED as FRIEND

ROOT=P.GAME
PACKAGE="BGXFTRACE"
TARGET="override/M_BXFR.lua"
STAGED=PACKAGE+"/staged/M_BXFR.lua"
PROOF=PACKAGE+"/PROOF.json"
TP2=PACKAGE+"/setup-BGXFTRACE.tp2"
SETUP="setup-BGXFTRACE.exe"
TRACE_HASH="ab819073a7d6390241d5b1da2a50f6fc44731f249b8e73780ed63526147e896b"
BASE={
    "override/BDDEFAI.BCS":"9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e",
    "override/M_BX43.lua":"74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c",
    "override/WTASIGHT.BCS":"7d69e5408ad84912afec848cba221614a625caee7f8469db067108c70041bde1",
    "override/DPLAYER.BCS":"1786f4dc050be5c4bef65d9b0c39100975a03fdf74057b21fe1b1c2b926d661f",
    "override/PRIEST1.BCS":"86a3c63799f09e7b9d51f6a61a893eff36f50ee3d6a3fe7eaa2dae97d2861589"
}
COMPONENT=re.compile(r"^~(?:[^~]*[/\\])?BGXFTRACE[/\\]SETUP-BGXFTRACE[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
TP2_DATA=("BACKUP ~BGXFTRACE/backup~\n"
          "AUTHOR ~BGXAI passive trace~\n"
          "BEGIN ~BGXAI EEex passive action trace (NO COMBAT CHANGES)~\n"
          "COPY ~BGXFTRACE/staged/M_BXFR.lua~ ~override/M_BXFR.lua~\n")
APPROVAL_INSTALL="INSTALL_BGXFTRACE_PASSIVE_OBSERVER"
APPROVAL_REMOVE="ROLLBACK_BGXFTRACE_PASSIVE_OBSERVER"

def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha_file(p):return sha_bytes(p.read_bytes())
def guard(p): V3.V2.guard(p)
def last(root): return V3.last(root)
def ensure_root(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.V2.require_root(root)
    for path in (TARGET,STAGED,TP2,SETUP,PROOF,*BASE):guard(root/path)
    if not FRIEND.LAST.match(last(root)):
        raise ValueError("BGXFRIEND_NOT_LAST_WEIDU")
    for name,expected in BASE.items():
        path=root/name
        if not path.is_file() or sha_file(path)!=expected:
            raise ValueError("BASE_SCRIPT_SHA_MISMATCH:"+name)
    if (root/TARGET).exists() or (root/PACKAGE).exists() or (root/SETUP).exists():
        raise ValueError("TRACE_ALREADY_STAGED_OR_INSTALLED")

def source_bytes():
    src=Path(__file__).with_name("M_BXFR.lua")
    guard(src)
    if not src.is_file():raise ValueError("TRACE_SOURCE_MISSING")
    data=src.read_bytes()
    if sha_bytes(data)!=TRACE_HASH:raise ValueError("PINNED_TRACE_SOURCE_SHA_MISMATCH")
    if b"EEex_Action_AddSpriteStartedActionListener" not in data:
        raise ValueError("SOURCE_OBSERVER_HOOK_MISSING")
    return data

def preflight(root):
    ensure_root(root)
    source_bytes()
    weidu=root/"setup-enhanced-powergaming-scripts.exe"
    guard(weidu)
    if not weidu.is_file() or weidu.read_bytes()[:2]!=b"MZ":
        raise ValueError("NATIVE_WEIDU_MISSING")
    return {"status":"BGXFTRACE_PREFLIGHT_PASS","observer_sha256":TRACE_HASH,
            "all_existing_script_sha_verified":True,
            "target_not_installed":True,"runtime_hook_verified":False,
            "game_modified":False}

def backup(root):
    parent=Path(os.environ.get("USERPROFILE",str(Path.home())))/"Documents"/"BGXFTRACE_SAFE_BACKUPS"
    guard(parent)
    folder=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    names=[*BASE,"WeiDU.log","chitin.key"]
    checks={}
    for name in names:
        f=root/name;guard(f)
        if not f.is_file():raise ValueError("BACKUP_SOURCE_MISSING:"+name)
        target=folder/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,target)
        checks[name]=sha_file(f)
        if sha_file(target)!=checks[name]:raise ValueError("BACKUP_SHA_FAILED:"+name)
    (folder/"SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    return folder

def status(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.V2.require_root(root)
    lastmod=last(root)
    if not COMPONENT.match(lastmod):
        ensure_root(root)
        return {"status":"BGXFTRACE_NOT_INSTALLED_BGXFRIEND_VERIFIED","game_modified":False}
    proof_file=root/PROOF;guard(proof_file)
    if not proof_file.is_file():raise ValueError("TRACE_PROOF_MISSING")
    proof=json.loads(proof_file.read_text("utf-8"))
    if proof.get("source_sha256")!=TRACE_HASH:raise ValueError("TRACE_PROOF_SHA_MISMATCH")
    for name,expected in BASE.items():
        path=root/name;guard(path)
        if not path.is_file() or sha_file(path)!=expected:
            raise ValueError("OTHER_SCRIPT_CHANGED:"+name)
    for name in (TARGET,STAGED):
        f=root/name;guard(f)
        if not f.is_file() or sha_file(f)!=TRACE_HASH:
            raise ValueError("LIVE_TRACE_SOURCE_SHA_MISMATCH:"+name)
    saved=Path(proof.get("external_backup",""));guard(saved)
    checks_file=saved/"SHA256.json";guard(checks_file)
    if not checks_file.is_file():raise ValueError("BACKUP_MANIFEST_MISSING")
    checks=json.loads(checks_file.read_text("utf-8"))
    for name,expected in BASE.items():
        p=saved/name;guard(p)
        if checks.get(name)!=expected or not p.is_file() or sha_file(p)!=expected:
            raise ValueError("BACKUP_NOT_VERIFIED:"+name)
    return {"status":"BGXFTRACE_INSTALLED_VERIFIED","observer_sha256":TRACE_HASH,
            "game_modified":False,"runtime_hook_verified":False,
            "expected_runtime_log":"BGXAI_FRIENDLY_ACTION_TRACE.log",
            "note":"Game restart required; installed files do not prove runtime hook or target events"}

def weidu(root,uninstall=False):
    exe=root/SETUP;guard(exe)
    p=subprocess.run([str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"],
         cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,
         errors="replace",timeout=240)
    log=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("WEIDU_TRACE_STOP:"+log[-650:])

def install(root):
    V3.V2.V1.processes()
    preflight(root)
    original_log=sha_file(root/"WeiDU.log")
    snap=backup(root)
    # All preflight and original backups must pass BEFORE any game-root write.
    V3.V2.V1.processes()
    if sha_file(root/"WeiDU.log")!=original_log:raise ValueError("GAME_CHANGED_AFTER_BACKUP")
    ensure_root(root)
    stage=root/PACKAGE/"staged"
    stage.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(source_bytes())
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({"source_sha256":TRACE_HASH,
        "external_backup":str(snap)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/SETUP)
    V3.V2.V1.processes()
    if sha_file(root/"WeiDU.log")!=original_log:raise ValueError("GAME_CHANGED_BEFORE_WEIDU")
    if not FRIEND.LAST.match(last(root)):raise ValueError("BGXFRIEND_NO_LONGER_LAST")
    for name,expected in BASE.items():
        if sha_file(root/name)!=expected:raise ValueError("INPUT_GAME_SHA_CHANGED:"+name)
    weidu(root)
    r=status(root)
    if r["status"]!="BGXFTRACE_INSTALLED_VERIFIED":raise ValueError("TRACE_POST_INSTALL_VERIFY_STOP")
    return dict(r,game_modified=True,backup=str(snap))

def rollback(root):
    V3.V2.V1.processes()
    r=status(root)
    if r["status"]!="BGXFTRACE_INSTALLED_VERIFIED" or not COMPONENT.match(last(root)):
        raise ValueError("NOT_LAST_TRACE_COMPONENT")
    proof=json.loads((root/PROOF).read_text(encoding="utf-8"))
    saved=Path(proof["external_backup"]);guard(saved)
    checks=json.loads((saved/"SHA256.json").read_text(encoding="utf-8"))
    for name,expected in checks.items():
        f=saved/name;guard(f)
        if not f.is_file() or sha_file(f)!=expected:raise ValueError("BACKUP_DRIFT:"+name)
    V3.V2.V1.processes()
    weidu(root,uninstall=True)
    if (root/TARGET).exists():raise ValueError("TRACE_OVERRIDE_NOT_REMOVED")
    if not FRIEND.LAST.match(last(root)):raise ValueError("BGXFRIEND_NOT_RESTORED_AS_LAST")
    for name,expected in BASE.items():
        if sha_file(root/name)!=expected:raise ValueError("ROLLBACK_OTHER_SCRIPT_DRIFT:"+name)
    return {"status":"BGXFTRACE_ROLLBACK_BGXFRIEND_VERIFIED","game_modified":True,
            "diagnostic_log_preserved":True}

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("mode",choices=("preflight","status","install","rollback"))
    arg.add_argument("--game",default=str(ROOT))
    args=arg.parse_args()
    try:
        root=Path(args.game)
        if args.mode=="preflight":r=preflight(root)
        elif args.mode=="status":r=status(root)
        elif args.mode=="install":
            if input("Type "+APPROVAL_INSTALL+" exactly: ").strip()!=APPROVAL_INSTALL:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            r=install(root)
        else:
            if input("Type "+APPROVAL_REMOVE+" exactly: ").strip()!=APPROVAL_REMOVE:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            r=rollback(root)
        print(json.dumps(r,indent=2,ensure_ascii=False));return 0
    except Exception as exc:
        print("BGXFTRACE_STOP:"+str(exc));return 1
if __name__=="__main__":sys.exit(main())
