#!/usr/bin/env python3
"""BGXAI V3: guarded V2->V3 upgrade, native compile, independent backup, rollback.
Install requires typed authorization; preflight+post-install status happen in ONE run.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V2_GUARDED_INSTALL as V2
import BGXRANGED_V3_PREFLIGHT as V3

ROOT=P.GAME
BCS=P.BCS
V2_SHA=V2.V2_SHA
BASE_SHA=P.PINS[BCS]
SOURCE_SHA="d6956a35bf80c2a451a335fafacd413125dac11a9096d694eaa59063255468fe"
DIR="BGXRANGED3"
TP2=DIR+"/setup-BGXRANGED3.tp2"
STAGED=DIR+"/staged/BDDEFAI.BCS"
PROOF=DIR+"/STAGED_PROOF.json"
EXE="setup-BGXRANGED3.exe"
TOKEN_INSTALL="INSTALL_BGXRANGED_V3_WEAPON_FIX"
TOKEN_ROLLBACK="ROLLBACK_BGXRANGED_V3_WEAPON_FIX"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXRANGED3[/\\]SETUP-BGXRANGED3[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
TP2_DATA="BACKUP ~BGXRANGED3/backup~\nAUTHOR ~BGXAI V3 weapon choice~\nBEGIN ~BGXAI V3 defensive weapon selection~\nCOPY ~BGXRANGED3/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n"
PROTECTED=(BCS,"override/M_BX43.lua","override/PRIEST1.BCS","WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def check_root(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V2.require_root(root)
    V2.check_protected(root)
def last(root):return V2.last(root)
def status(root):
    check_root(root)
    if LAST.match(last(root)):
        proof=root/PROOF;V2.guard(proof)
        if not proof.is_file():raise ValueError("V3_PROOF_MISSING")
        data=json.loads(proof.read_text(encoding="utf-8"))
        if data.get("previous_sha256")!=V2_SHA or data.get("source_sha256")!=SOURCE_SHA:
            raise ValueError("V3_PROOF_CHAIN")
        expected=data.get("candidate_sha256")
        if not isinstance(expected,str) or not re.fullmatch("[0-9a-f]{64}",expected):
            raise ValueError("V3_PROOF_SHA")
        live=root/BCS;stage=root/STAGED
        for path in (live,stage):V2.guard(path)
        if sha(live)!=expected or sha(stage)!=expected:raise ValueError("V3_BCS_SHA_DRIFT")
        blocks=P.parts(live.read_bytes())
        if len(blocks)!=1173:raise ValueError("V3_BLOCK_COUNT")
        original=b"SC\n"+b"".join(blocks[3:])
        if sha_bytes(original)!=BASE_SHA:raise ValueError("V3_OLD_1170_DRIFT")
        return {"status":"BGXRANGED_V3_INSTALLED_VERIFIED","candidate_sha256":expected,
                "blocks":1173,"preserved_old_blocks":1170,"game_modified":False}
    result=V2.status(root)
    if result["status"]!="BGXRANGED_V2_INSTALLED_VERIFIED":
        raise ValueError("EXPECTED_V2_INSTALLED")
    return {"status":"BGXRANGED_V2_INSTALLED_V3_NOT_INSTALLED","v2_sha256":V2_SHA,
            "game_modified":False}
def backup(root):
    parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXRANGED_V3_SAFE_BACKUPS"
    V2.guard(parent)
    target=parent/("PRE_V3_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    target.mkdir(parents=True,exist_ok=False)
    checks={}
    for name in PROTECTED+OPTIONAL:
        p=root/name;V2.guard(p)
        if name in PROTECTED and not p.is_file():raise ValueError("BACKUP_SOURCE_MISSING:"+name)
        if not p.exists():continue
        if not p.is_file():raise ValueError("BACKUP_NOT_FILE:"+name)
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        checks[name]=sha(p)
        if sha(dest)!=checks[name]:raise ValueError("BACKUP_SHA_MISMATCH:"+name)
    (target/"SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    return target
def build(root,report):
    source=V3.SOURCE
    if source.is_symlink() or sha(source)!=SOURCE_SHA:raise ValueError("V3_SOURCE_SHA")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED3_INSTALL_COMPILE_") as folder:
        td=pathlib.Path(folder)
        compiler=td/"weidu.exe";compiler.write_bytes((root/"setup-enhanced-powergaming-scripts.exe").read_bytes())
        baf=td/"BGXRANGEDV3.BAF";baf.write_bytes(source.read_bytes())
        out=td/"out";out.mkdir()
        p=subprocess.run([str(compiler),"--game",str(root),"--out",str(out),str(baf)],
          cwd=td,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        log=(p.stdout or "")+"\n"+(p.stderr or "")
        if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
            raise ValueError("STAGE_COMPILE_FAIL:"+log[-600:])
        files=list(out.rglob("BGXRANGEDV3.BCS"))
        if len(files)!=1:raise ValueError("STAGE_BCS_NOT_FOUND")
        blocks=P.parts(files[0].read_bytes())
        if len(blocks)!=3:raise ValueError("STAGE_NOT_THREE_BLOCKS")
        original=V3.validate(root)
        merged=b"SC\n"+b"".join(blocks)[:-3]+original[3:]
        if sha_bytes(merged)!=report["candidate_sha256"]:
            raise ValueError("NONDETERMINISTIC_NATIVE_COMPILE")
        if len(P.parts(merged))!=1173 or P.parts(merged)[3:]!=P.parts(original):
            raise ValueError("OLD_BLOCKS_CHANGED")
        return merged
def weidu(root,uninstall=False):
    exe=root/EXE;V2.guard(exe)
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),"--use-lang","ru_ru",
         "--force-uninstall" if uninstall else "--force-install","0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,text=True,
        errors="replace",timeout=240)
    out=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",out):
        raise ValueError("WEIDU_STOP_MANUAL_REVIEW:"+out[-850:])
def install(root):
    V2.V1.processes()
    check_root(root)
    if (root/DIR).exists() or (root/EXE).exists():raise ValueError("V3_STAGING_COLLISION")
    old=V3.validate(root)
    old_log=sha(root/"WeiDU.log")
    report=V3.run(root)
    if report["status"]!="BGXRANGED_V3_NATIVE_PREFLIGHT_PASS" or report["source_sha256"]!=SOURCE_SHA:
        raise ValueError("NATIVE_PREFLIGHT_NOT_PASS")
    merged=build(root,report)
    V2.V1.processes()
    if sha(root/BCS)!=V2_SHA or sha(root/"WeiDU.log")!=old_log:
        raise ValueError("V2_BASE_CHANGED")
    snap=backup(root)
    V2.guard(root/DIR);(root/DIR/"staged").mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(merged)
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({"previous_sha256":V2_SHA,
      "candidate_sha256":report["candidate_sha256"],"source_sha256":SOURCE_SHA,
      "original_sha256":BASE_SHA,"backup":str(snap)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
    if sha(root/STAGED)!=report["candidate_sha256"]:raise ValueError("STAGE_SHA_CHANGED")
    V2.V1.processes()
    if sha(root/BCS)!=V2_SHA or sha(root/"WeiDU.log")!=old_log or not V2.LAST.match(last(root)):
        raise ValueError("V2_CHANGED_BEFORE_INSTALL")
    weidu(root)
    verified=status(root)
    if verified["status"]!="BGXRANGED_V3_INSTALLED_VERIFIED":raise ValueError("POST_INSTALL_VERIFY_STOP")
    return dict(verified,game_modified=True,backup=str(snap))
def rollback(root):
    V2.V1.processes()
    current=status(root)
    if current["status"]!="BGXRANGED_V3_INSTALLED_VERIFIED" or not LAST.match(last(root)):
        raise ValueError("V3_NOT_LAST")
    proof=json.loads((root/PROOF).read_text("utf-8"))
    snap=pathlib.Path(proof["backup"]);V2.guard(snap)
    checks=json.loads((snap/"SHA256.json").read_text("utf-8"))
    if checks.get(BCS)!=V2_SHA:raise ValueError("BACKUP_NOT_V2")
    for name,value in checks.items():
        path=snap/name;V2.guard(path)
        if sha(path)!=value:raise ValueError("BACKUP_TAMPERED:"+name)
    V2.V1.processes()
    weidu(root,uninstall=True)
    result=V2.status(root)
    if result["status"]!="BGXRANGED_V2_INSTALLED_VERIFIED" or sha(root/BCS)!=V2_SHA:
        raise ValueError("V2_NOT_RESTORED")
    return {"status":"BGXRANGED_V3_ROLLBACK_VERIFIED_V2_RESTORED",
            "v2_sha256":V2_SHA,"game_modified":True}
def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=("status","preflight","install","rollback"))
    p.add_argument("--game",default=str(ROOT));args=p.parse_args();root=pathlib.Path(args.game)
    try:
        if args.mode=="status":result=status(root)
        elif args.mode=="preflight":result=V3.run(root)
        elif args.mode=="install":
            if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            result=install(root)
        else:
            if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            result=rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXRANGED_V3_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
