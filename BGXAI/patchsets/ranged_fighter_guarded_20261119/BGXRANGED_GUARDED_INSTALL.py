#!/usr/bin/env python3
"""BGXAI ranged fighter: exact-baseline guarded WeiDU install/rollback.
No writes in status/preflight. Install requires an external opt-in by the
unified BGXAI_UPDATE.cmd AND an additional exact typed token here.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, stat, subprocess, sys, tempfile, datetime
import BGXRANGED_PREFLIGHT as P

ROOT=P.GAME
BCS="override/BDDEFAI.BCS"
PRIEST="override/PRIEST1.BCS"
LUA="override/M_BX43.lua"
COMPILER="setup-enhanced-powergaming-scripts.exe"
TP2="BGXRANGED/setup-BGXRANGED.tp2"
STAGED="BGXRANGED/staged/BDDEFAI.BCS"
PROOF="BGXRANGED/STAGED_PROOF.json"
EXE="setup-BGXRANGED.exe"
OLD_LAST=re.compile(r"^~(?:[^~]*[/\\])?BGX120[/\\]SETUP-BGX120[.]TP2~\\s+#0\\s+#0(?:\\s|$)",re.I)
NEW_LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXRANGED[/\\]SETUP-BGXRANGED[.]TP2~\\s+#0\\s+#0(?:\\s|$)",re.I)
TP2_DATA="BACKUP ~BGXRANGED/backup~\nAUTHOR ~BGXAI guarded ranged fighter~\nBEGIN ~BGXAI ranged fighter pilot~\nCOPY ~BGXRANGED/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n"
INSTALL_TOKEN="INSTALL_BGXRANGED_FIGHTER_PILOT"
ROLLBACK_TOKEN="ROLLBACK_BGXRANGED_FIGHTER_PILOT"
FILES=(BCS,PRIEST,LUA,"WeiDU.log","chitin.key",
       "lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(path):
    for p in (path,*path.parents):
        if p.is_symlink():raise ValueError("SYMLINK_BLOCKED:"+str(p))
        if p.exists() and getattr(p.stat(),"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0):
            raise ValueError("REPARSE_BLOCKED:"+str(p))
        if p==ROOT:break
def last(root):
    rows=[x.strip() for x in (root/"WeiDU.log").read_text("utf-8-sig",errors="replace").splitlines() if x.strip().startswith("~")]
    if not rows:raise ValueError("NO_WEIDU")
    return rows[-1]
def processes():
    if os.name!="nt":raise ValueError("WINDOWS_ONLY")
    cmd=('$ErrorActionPreference="Stop";$p=Get-CimInstance Win32_Process | '
         'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
         'if($p){$p|Select-Object Name,ProcessId|Out-String;exit 3}')
    p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",cmd],
       stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=35)
    if p.returncode or p.stdout.strip():raise ValueError("GAME_OR_WEIDU_RUNNING")
def status(root):
    if root!=ROOT:raise ValueError("GAME_ROOT")
    safe(root)
    if NEW_LAST.match(last(root)):
        proof=json.loads((root/PROOF).read_text("utf-8"))
        for name,expected in (("bcs_sha256",digest(root/BCS)),):
            if proof.get(name)!=expected:raise ValueError("INSTALLED_BCS_DRIFT")
        if digest(root/STAGED)!=proof["bcs_sha256"]:raise ValueError("STAGE_DRIFT")
        if digest(root/PRIEST)!=P.PINS[PRIEST] or digest(root/LUA)!=P.PINS[LUA]:
            raise ValueError("OTHER_BGX_DRIFT")
        return {"status":"BGXRANGED_INSTALLED_VERIFIED","new_blocks":1171,
                "bcs_sha256":proof["bcs_sha256"]}
    P.check(root)
    return {"status":"BGXRANGED_NOT_INSTALLED_BASELINE_VERIFIED","game_modified":False}
def snapshot(root):
    dest=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXRANGED_SAFE_BACKUPS"/(
        "PRE_INSTALL_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    safe(dest.parent)
    dest.mkdir(parents=True,exist_ok=False)
    checks={}
    for rel in FILES:
        src=root/rel;safe(src)
        if not src.is_file():raise ValueError("BACKUP_SOURCE_MISSING:"+rel)
        dst=dest/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        checks[rel]=digest(src)
        if digest(dst)!=checks[rel]:raise ValueError("BACKUP_SHA_MISMATCH:"+rel)
    (dest/"BACKUP_SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    return dest
def weidu(root,rollback=False):
    exe=root/EXE;safe(exe)
    mode="--force-uninstall" if rollback else "--force-install"
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),"--use-lang","ru_ru",mode,"0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,
        errors="replace",timeout=240)
    log=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("WEIDU_STOP_NO_AUTO_RETRY:"+log[-750:])
def install(root):
    processes()
    original=P.check(root)
    prior_log=digest(root/"WeiDU.log")
    if (root/"BGXRANGED").exists() or (root/EXE).exists():
        raise ValueError("STAGING_COLLISION")
    candidate=P.run(root,"preflight")
    if candidate.get("status")!="BGXRANGED_NATIVE_PREFLIGHT_PASS":
        raise ValueError("NATIVE_PREFLIGHT_NOT_PASS")
    if candidate["candidate_sha256"]!="49b553908e7b66ab85714e91dd27800cad2ec4a9c51d8860d24aeb67b3c461b3":
        raise ValueError("CANDIDATE_SHA_CHANGED")
    # Recompile the exact pinned BAF and construct the byte-preserving BCS
    source=pathlib.Path(P.__file__).with_name("BGX_RANGED_FIGHTER.baf")
    if digest(source)!=P.BAF_SHA:raise ValueError("BAF_SHA")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED_STAGE_") as folder:
        td=pathlib.Path(folder);exe=td/"weidu.exe";exe.write_bytes((root/COMPILER).read_bytes())
        inp=td/"BGXRANGED.BAF";inp.write_bytes(source.read_bytes());out=td/"out";out.mkdir()
        cmd=[str(exe),"--game",str(root),"--out",str(out),str(inp)]
        p=subprocess.run(cmd,cwd=td,stdin=subprocess.DEVNULL,capture_output=True,text=True,
            errors="replace",timeout=180)
        if p.returncode or re.search(r"(?im)^\\s*(?:ERROR:|FATAL ERROR:)",(p.stdout or "")+"\n"+(p.stderr or "")):
            raise ValueError("STAGE_COMPILER_FAILED")
        generated=list(out.rglob("BGXRANGED.BCS"))
        if len(generated)!=1:raise ValueError("STAGE_BCS_MISSING")
        new=P.parts(generated[0].read_bytes())
        if len(new)!=1 or not new[0].endswith(b"CR\nSC\n"):raise ValueError("STAGE_BCS_BAD")
        merged=b"SC\n"+new[0][:-3]+original[3:]
        if len(P.parts(merged))!=1171 or P.parts(merged)[1:]!=P.parts(original):
            raise ValueError("OLD_BLOCKS_CHANGED")
        if hashlib.sha256(merged).hexdigest()!=candidate["candidate_sha256"]:
            raise ValueError("NONDETERMINISTIC_CANDIDATE")
    processes();P.check(root)
    if digest(root/"WeiDU.log")!=prior_log:raise ValueError("WEIDU_CHANGED")
    backup=snapshot(root)
    stage=root/"BGXRANGED";(stage/"staged").mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(merged)
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({"bcs_sha256":candidate["candidate_sha256"],
        "original_sha256":P.PINS[BCS],"backup":str(backup)},indent=2),encoding="utf-8")
    shutil.copy2(root/COMPILER,root/EXE)
    if digest(root/STAGED)!=candidate["candidate_sha256"]:raise ValueError("STAGED_SHA")
    processes();P.check(root)
    if digest(root/"WeiDU.log")!=prior_log:raise ValueError("LOG_CHANGED_BEFORE_WEIDU")
    weidu(root)
    return status(root)
def rollback(root):
    processes()
    result=status(root)
    if result["status"]!="BGXRANGED_INSTALLED_VERIFIED" or not NEW_LAST.match(last(root)):
        raise ValueError("NOT_LAST_COMPONENT")
    proof=json.loads((root/PROOF).read_text("utf-8"))
    backup=pathlib.Path(proof["backup"])
    checks=json.loads((backup/"BACKUP_SHA256.json").read_text("utf-8"))
    for name,expected in checks.items():
        if digest(backup/name)!=expected:raise ValueError("BACKUP_TAMPERED:"+name)
    processes();weidu(root,True)
    state=P.check(root)
    if digest(root/BCS)!=P.PINS[BCS]:raise ValueError("ROLLBACK_SHA")
    return {"status":"BGXRANGED_ROLLBACK_VERIFIED","old_blocks":1170,"game_modified":True}
def main():
    a=argparse.ArgumentParser();a.add_argument("mode",choices=["status","preflight","install","rollback"])
    a.add_argument("--game",default=str(ROOT));opts=a.parse_args();root=pathlib.Path(opts.game)
    try:
        if opts.mode=="status":result=status(root)
        elif opts.mode=="preflight":result=P.run(root,"preflight")
        elif opts.mode=="install":
            if input("Type "+INSTALL_TOKEN+" exactly: ").strip()!=INSTALL_TOKEN:raise ValueError("NO_AUTHORIZATION")
            result=install(root)
        else:
            if input("Type "+ROLLBACK_TOKEN+" exactly: ").strip()!=ROLLBACK_TOKEN:raise ValueError("NO_AUTHORIZATION")
            result=rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXRANGED_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
