#!/usr/bin/env python3
"""BGXFTRACE v3: guarded, standalone WeiDU upgrade of passive observer only.

Observe Khalid's movement/guard action starts, keeping existing combat scripts
and LuaPatchMode untouched. Exact last-component rollback restores BGXF2.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys
import BGXRANGED_V3_GUARDED_INSTALL as V3
import BGXFTRACE_V2_GUARDED as V2

ROOT=V2.ROOT
TARGET=V2.TARGET
SOURCE="M_BXFR_MOTION_V3.lua"
SOURCE_SHA="0ca56636c80095e1cca3e1191fa89e452aa98f55387f8975c3302cdbead6a6bb"
PACKAGE="BGXF3"
STAGED=PACKAGE+"/staged/M_BXFR.lua"
TP2=PACKAGE+"/setup-BGXF3.tp2"
PROOF=PACKAGE+"/PROOF.json"
SETUP="setup-BGXF3.exe"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXF3[/\\]SETUP-BGXF3[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
TOKEN_INSTALL="INSTALL_BGXFTRACE_V3_MOTION"
TOKEN_ROLLBACK="ROLLBACK_BGXFTRACE_V3_MOTION"
TP2_DATA=("BACKUP ~BGXF3/backup~\n"
          "AUTHOR ~BGXAI passive action motion tracer~\n"
          "BEGIN ~BGXF3 passive EEex action trace (NO COMBAT CHANGES)~\n"
          "COPY ~BGXF3/staged/M_BXFR.lua~ ~override/M_BXFR.lua~\n")
BASE=dict(V2.BASE)

def guard(path):V2.guard(path)
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):return sha(path.read_bytes())
def last(root):return V2.V1.last(root)

def root_guard(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.V2.require_root(root)
    for p in (TARGET,STAGED,TP2,PROOF,SETUP,*BASE):guard(root/p)

def baseline(root):
    root_guard(root)
    r=V2.status(root)
    if r.get("status")!="BGXF2_INSTALLED_VERIFIED" or not V2.LAST.match(last(root)):
        raise ValueError("BGXF2_NOT_LAST_OR_DRIFT")
    if digest(root/TARGET)!=V2.SOURCE_SHA:raise ValueError("OLD_OBSERVER_SHA_DRIFT")
    if (root/PACKAGE).exists() or (root/SETUP).exists():
        raise ValueError("BGXF3_STAGING_COLLISION")
    for path,h in BASE.items():
        if digest(root/path)!=h:raise ValueError("COMBAT_SCRIPT_SHA_DRIFT:"+path)

def source():
    p=pathlib.Path(__file__).with_name(SOURCE);guard(p)
    if not p.is_file() or p.is_symlink():raise ValueError("NEW_OBSERVER_MISSING")
    b=p.read_bytes()
    if sha(b)!=SOURCE_SHA:raise ValueError("NEW_OBSERVER_SHA_DRIFT")
    for sig in (b"EEex_Action_AddSpriteStartedActionListener",
                b"if slot~=3 and not party_target then return end",
                b"Infinity_Log",b"origin=UNKNOWN"):
        if sig not in b:raise ValueError("V3_OBSERVER_SIGNATURE_MISSING")
    return b

def preflight(root):
    baseline(root)
    source()
    exe=root/"setup-enhanced-powergaming-scripts.exe";guard(exe)
    if not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_EXE_MISSING")
    return {"status":"BGXF3_PREFLIGHT_PASS",
            "old_observer_sha256":V2.SOURCE_SHA,
            "new_observer_sha256":SOURCE_SHA,
            "combat_scripts_sha_verified":True,
            "runtime_action_observation_verified":False,
            "game_modified":False}

def backup(root):
    parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXF3_SAFE_BACKUPS"
    guard(parent)
    folder=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    checks={}
    for name in [*BASE,TARGET,"WeiDU.log","chitin.key"]:
        src=root/name;guard(src)
        if src.is_symlink() or not src.is_file():raise ValueError("BACKUP_FILE_MISSING:"+name)
        dst=folder/name;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst);checks[name]=digest(src)
        if digest(dst)!=checks[name]:raise ValueError("BACKUP_SHA_BAD:"+name)
    if checks.get(TARGET)!=V2.SOURCE_SHA:raise ValueError("WRONG_BASE_OBSERVER")
    (folder/"SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    return folder

def weidu(root,uninstall=False):
    exe=root/SETUP;guard(exe)
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    res=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
                       text=True,errors="replace",timeout=240)
    log=(res.stdout or "")+"\n"+(res.stderr or "")
    if res.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("BGXF3_WEIDU_STOP:"+log[-650:])

def status(root):
    root_guard(root)
    if not LAST.match(last(root)):
        baseline(root)
        return {"status":"BGXF3_NOT_INSTALLED_V2_VERIFIED","game_modified":False}
    proof_file=root/PROOF;guard(proof_file)
    if not proof_file.is_file():raise ValueError("BGXF3_PROOF_MISSING")
    proof=json.loads(proof_file.read_text(encoding="utf-8"))
    if proof.get("new_source_sha256")!=SOURCE_SHA or proof.get("old_source_sha256")!=V2.SOURCE_SHA:
        raise ValueError("BGXF3_PROOF_DRIFT")
    for name in (TARGET,STAGED):
        p=root/name;guard(p)
        if not p.is_file() or digest(p)!=SOURCE_SHA:
            raise ValueError("BGXF3_LIVE_SOURCE_SHA_DRIFT:"+name)
    for name,h in BASE.items():
        p=root/name;guard(p)
        if not p.is_file() or digest(p)!=h:raise ValueError("BGXF3_COMBAT_SHA_CHANGED:"+name)
    backup_path=pathlib.Path(proof["backup"]);guard(backup_path)
    manifest=backup_path/"SHA256.json";guard(manifest)
    checks=json.loads(manifest.read_text(encoding="utf-8"))
    for name,h in checks.items():
        f=backup_path/name;guard(f)
        if not f.is_file() or digest(f)!=h:raise ValueError("BGXF3_BACKUP_SHA_DRIFT:"+name)
    if checks.get(TARGET)!=V2.SOURCE_SHA:raise ValueError("BGXF3_BACKUP_NOT_V2")
    return {"status":"BGXF3_INSTALLED_VERIFIED",
            "old_observer_sha256":V2.SOURCE_SHA,
            "new_observer_sha256":SOURCE_SHA,
            "existing_combat_scripts_unchanged":True,
            "runtime_hook_verified":False,
            "game_modified":False}

def install(root):
    V3.V2.V1.processes()
    preflight(root)
    wei_hash=digest(root/"WeiDU.log")
    snap=backup(root)
    V3.V2.V1.processes()
    if digest(root/"WeiDU.log")!=wei_hash:raise ValueError("WEIDU_CHANGED_AFTER_BACKUP")
    baseline(root)
    staged=root/PACKAGE/"staged";guard(staged);staged.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(source())
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({
        "old_source_sha256":V2.SOURCE_SHA,"new_source_sha256":SOURCE_SHA,
        "backup":str(snap)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/SETUP)
    V3.V2.V1.processes()
    if digest(root/"WeiDU.log")!=wei_hash or not V2.LAST.match(last(root)):
        raise ValueError("OTHER_INSTALL_INTERLEAVED")
    if digest(root/TARGET)!=V2.SOURCE_SHA or digest(root/STAGED)!=SOURCE_SHA:
        raise ValueError("OBSERVER_SHA_CHANGED_BEFORE_INSTALL")
    for name,h in BASE.items():
        if digest(root/name)!=h:raise ValueError("COMBAT_SHA_CHANGED_BEFORE_INSTALL:"+name)
    weidu(root)
    result=status(root)
    if result["status"]!="BGXF3_INSTALLED_VERIFIED":
        raise ValueError("BGXF3_POSTINSTALL_VERIFY_FAILED")
    return dict(result,game_modified=True,backup=str(snap))

def rollback(root):
    V3.V2.V1.processes()
    if status(root)["status"]!="BGXF3_INSTALLED_VERIFIED" or not LAST.match(last(root)):
        raise ValueError("BGXF3_NOT_LAST")
    proof=json.loads((root/PROOF).read_text(encoding="utf-8"))
    snap=pathlib.Path(proof["backup"]);guard(snap)
    checks=json.loads((snap/"SHA256.json").read_text(encoding="utf-8"))
    for name,h in checks.items():
        f=snap/name;guard(f)
        if not f.is_file() or digest(f)!=h:raise ValueError("BACKUP_SHA_DRIFT:"+name)
    V3.V2.V1.processes()
    weidu(root,uninstall=True)
    if not V2.LAST.match(last(root)) or digest(root/TARGET)!=V2.SOURCE_SHA:
        raise ValueError("BGXF3_ROLLBACK_NOT_RESTORED_V2")
    for name,h in BASE.items():
        if digest(root/name)!=h:raise ValueError("BGXF3_ROLLBACK_COMBAT_SHA_DRIFT:"+name)
    return {"status":"BGXF3_ROLLBACK_V2_VERIFIED","game_modified":True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=("preflight","status","install","rollback"))
    ap.add_argument("--game",default=str(ROOT))
    opts=ap.parse_args();root=pathlib.Path(opts.game)
    try:
        if opts.mode=="preflight":r=preflight(root)
        elif opts.mode=="status":r=status(root)
        elif opts.mode=="install":
            if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            r=install(root)
        else:
            if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            r=rollback(root)
        print(json.dumps(r,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXF3_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
