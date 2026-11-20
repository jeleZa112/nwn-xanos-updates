#!/usr/bin/env python3
"""Guarded and reversible BGXFTRACE v2: replaces only the tracer Lua via WeiDU.

Keep LuaPatchMode=INTERNAL. Adds Infinity_Log/print console fallback when
io.open is absent. Does not patch BCS, other Lua, game INI or saved games.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys
import BGXRANGED_V3_GUARDED_INSTALL as V3
import BGX_FRIEND_TRACE_GUARDED as V1

ROOT=V1.ROOT
PACKAGE="BGXF2"
TARGET=V1.TARGET
SOURCE="M_BXFR_CONSOLE_V2.lua"
STAGED=PACKAGE+"/staged/M_BXFR.lua"
TP2=PACKAGE+"/setup-BGXF2.tp2"
PROOF=PACKAGE+"/PROOF.json"
SETUP="setup-BGXF2.exe"
SOURCE_SHA="3562353e6351b19aba8126dc82ce45834c8b0549eccc06652f6d66a1ac895c0e"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXF2[/\\]SETUP-BGXF2[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
TOKEN_INSTALL="INSTALL_BGXFTRACE_V2_CONSOLE"
TOKEN_ROLLBACK="ROLLBACK_BGXFTRACE_V2_CONSOLE"
TP2_DATA=("BACKUP ~BGXF2/backup~\n"
          "AUTHOR ~BGXAI EEex passive console trace v2~\n"
          "BEGIN ~BGXAI passive EEex trace console fallback (NO COMBAT CHANGES)~\n"
          "COPY ~BGXF2/staged/M_BXFR.lua~ ~override/M_BXFR.lua~\n")
BASE=dict(V1.BASE)

def guard(path):V1.guard(path)
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):return sha(path.read_bytes())
def root_guard(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.V2.require_root(root)
    for p in (TARGET,STAGED,TP2,PROOF,SETUP,*BASE):guard(root/p)

def existing_verified(root):
    root_guard(root)
    status=V1.status(root)
    if status.get("status")!="BGXFTRACE_INSTALLED_VERIFIED" or not V1.COMPONENT.match(V1.last(root)):
        raise ValueError("BGXFTRACE_V1_NOT_LAST_OR_DRIFT")
    if digest(root/TARGET)!=V1.TRACE_HASH:raise ValueError("TRACE_V1_SOURCE_SHA_DRIFT")
    if (root/PACKAGE).exists() or (root/SETUP).exists():
        raise ValueError("BGXF2_STAGING_COLLISION")
    for name,h in BASE.items():
        if digest(root/name)!=h:raise ValueError("EXISTING_SCRIPT_CHANGED:"+name)
    return status

def pinned_source():
    src=pathlib.Path(__file__).with_name(SOURCE);guard(src)
    if not src.is_file() or src.is_symlink():raise ValueError("BGXF2_SOURCE_MISSING")
    data=src.read_bytes()
    if sha(data)!=SOURCE_SHA:raise ValueError("BGXF2_SOURCE_SHA_DRIFT")
    for f in (b"EEex_Action_AddSpriteStartedActionListener",
              b"Infinity_Log",b"origin=UNKNOWN"):
        if f not in data:raise ValueError("TRACER_REQUIRED_FUNCTION_MISSING")
    return data

def preflight(root):
    existing_verified(root)
    pinned_source()
    exe=root/"setup-enhanced-powergaming-scripts.exe"
    guard(exe)
    if not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_NATIVE_NOT_FOUND")
    return {"status":"BGXF2_PREFLIGHT_PASS","old_observer_sha256":V1.TRACE_HASH,
            "new_observer_sha256":SOURCE_SHA,"all_other_scripts_unchanged":True,
            "lua_patch_mode_modified":False,"runtime_hook_verified":False,"game_modified":False}

def backup(root):
    parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXF2_SAFE_BACKUPS"
    guard(parent)
    folder=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    files=[*BASE,TARGET,"WeiDU.log","chitin.key"]
    manifest={}
    for name in files:
        src=root/name;guard(src)
        if not src.is_file() or src.is_symlink():raise ValueError("BACKUP_INPUT_MISSING:"+name)
        dst=folder/name;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst);manifest[name]=digest(src)
        if digest(dst)!=manifest[name]:raise ValueError("BACKUP_VERIFY_FAIL:"+name)
    if manifest[TARGET]!=V1.TRACE_HASH:raise ValueError("BASE_TRACER_SHA_MISMATCH")
    (folder/"SHA256.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return folder

def run_weidu(root,uninstall=False):
    exe=root/SETUP;guard(exe)
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
        text=True,errors="replace",timeout=240)
    log=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("BGXF2_WEIDU_STOP_MANUAL_INSPECTION:"+log[-650:])

def status(root):
    root_guard(root)
    line=V1.last(root)
    if not LAST.match(line):
        existing_verified(root)
        return {"status":"BGXF2_NOT_INSTALLED_V1_VERIFIED","game_modified":False}
    proof_file=root/PROOF;guard(proof_file)
    if not proof_file.is_file():raise ValueError("BGXF2_PROOF_MISSING")
    proof=json.loads(proof_file.read_text(encoding="utf-8"))
    if proof.get("source_sha256")!=SOURCE_SHA or proof.get("old_source_sha256")!=V1.TRACE_HASH:
        raise ValueError("BGXF2_PROOF_DRIFT")
    for name in (TARGET,STAGED):
        f=root/name;guard(f)
        if not f.is_file() or digest(f)!=SOURCE_SHA:raise ValueError("TRACE_V2_SHA_DRIFT:"+name)
    for name,h in BASE.items():
        f=root/name;guard(f)
        if not f.is_file() or digest(f)!=h:raise ValueError("OTHER_SCRIPT_SHA_DRIFT:"+name)
    backup_path=pathlib.Path(proof["external_backup"]);guard(backup_path)
    manifest_path=backup_path/"SHA256.json";guard(manifest_path)
    checks=json.loads(manifest_path.read_text(encoding="utf-8"))
    for name,h in checks.items():
        f=backup_path/name;guard(f)
        if not f.is_file() or digest(f)!=h:
            raise ValueError("EXTERNAL_BACKUP_SHA_DRIFT:"+name)
    if checks.get(TARGET)!=V1.TRACE_HASH:raise ValueError("WRONG_V1_BACKUP")
    return {"status":"BGXF2_INSTALLED_VERIFIED",
            "old_trace_sha256":V1.TRACE_HASH,"new_trace_sha256":SOURCE_SHA,
            "last_weidu_verified":True,
            "existing_combat_scripts_unchanged":True,
            "lua_patch_mode_modified":False,"runtime_hook_verified":False,
            "game_modified":False}

def install(root):
    V3.V2.V1.processes()
    preflight(root)
    original_log=digest(root/"WeiDU.log")
    snap=backup(root)
    V3.V2.V1.processes()
    if digest(root/"WeiDU.log")!=original_log:raise ValueError("WEIDU_CHANGED_AFTER_BACKUP")
    existing_verified(root)
    staged_dir=root/PACKAGE/"staged"
    guard(staged_dir);staged_dir.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(pinned_source())
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({
        "source_sha256":SOURCE_SHA,"old_source_sha256":V1.TRACE_HASH,
        "external_backup":str(snap)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/SETUP)
    V3.V2.V1.processes()
    if digest(root/"WeiDU.log")!=original_log:raise ValueError("WEIDU_CHANGED_BEFORE_INSTALL")
    if not V1.COMPONENT.match(V1.last(root)):raise ValueError("V1_NO_LONGER_LAST")
    for name,h in BASE.items():
        if digest(root/name)!=h:raise ValueError("OTHER_SCRIPT_CHANGED_BEFORE_INSTALL")
    if digest(root/STAGED)!=SOURCE_SHA or digest(root/TARGET)!=V1.TRACE_HASH:
        raise ValueError("STAGED_OR_LIVE_SHA_CHANGED")
    run_weidu(root)
    result=status(root)
    if result["status"]!="BGXF2_INSTALLED_VERIFIED":raise ValueError("BGXF2_POSTINSTALL_VERIFY_FAILED")
    return dict(result,game_modified=True,backup=str(snap))

def rollback(root):
    V3.V2.V1.processes()
    if status(root)["status"]!="BGXF2_INSTALLED_VERIFIED" or not LAST.match(V1.last(root)):
        raise ValueError("BGXF2_NOT_LAST")
    proof=json.loads((root/PROOF).read_text(encoding="utf-8"))
    saved=pathlib.Path(proof["external_backup"]);guard(saved)
    checks=json.loads((saved/"SHA256.json").read_text(encoding="utf-8"))
    for name,h in checks.items():
        f=saved/name;guard(f)
        if not f.is_file() or digest(f)!=h:raise ValueError("BACKUP_SHA_FAIL:"+name)
    V3.V2.V1.processes()
    run_weidu(root,uninstall=True)
    if not V1.COMPONENT.match(V1.last(root)):raise ValueError("ROLLBACK_V1_NOT_LAST")
    for name,h in BASE.items():
        if digest(root/name)!=h:raise ValueError("ROLLBACK_SCRIPT_DRIFT:"+name)
    if digest(root/TARGET)!=V1.TRACE_HASH:raise ValueError("ROLLBACK_V1_TRACE_SHA_DRIFT")
    return {"status":"BGXF2_ROLLBACK_V1_VERIFIED","game_modified":True,
            "console_logs_preserved":True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("preflight","install","status","rollback"))
    ap.add_argument("--game",default=str(ROOT))
    opt=ap.parse_args();root=pathlib.Path(opt.game)
    try:
        if opt.mode=="preflight":res=preflight(root)
        elif opt.mode=="status":res=status(root)
        elif opt.mode=="install":
            if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
                raise ValueError("NOT_AUTHORIZED_INSTALL")
            res=install(root)
        else:
            if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
                raise ValueError("NOT_AUTHORIZED_ROLLBACK")
            res=rollback(root)
        print(json.dumps(res,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXF2_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
