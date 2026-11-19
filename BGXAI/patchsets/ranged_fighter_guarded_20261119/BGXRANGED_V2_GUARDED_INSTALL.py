#!/usr/bin/env python3
"""BGXAI V2: opt-in WeiDU upgrade from exact installed V1; last-component rollback.
Only status and preflight are read-only. No automatic repair/retries.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, stat, subprocess, sys, tempfile
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V2_PREFLIGHT as V
import BGXRANGED_GUARDED_INSTALL as V1

ROOT=P.GAME
BCS="override/BDDEFAI.BCS"
PRIEST="override/PRIEST1.BCS"
LUA="override/M_BX43.lua"
V1_SHA=V.V1_SHA
V2_SHA="1991f04d0a6acc556f53e03a7aa4a9fcaab252668b689f3d6726be118ca7c1e2"
V2_SOURCE_SHA="dc08fa3a1e5d34463ecb984d1e2fdf2c2c8bc938bd36411f189ffc4f1d0a3eb0"
BASE_SHA=P.PINS[BCS]
NAME="BGXRANGED2"
DIR="BGXRANGED2"
TP2=DIR+"/setup-BGXRANGED2.tp2"
STAGED=DIR+"/staged/BDDEFAI.BCS"
PROOF=DIR+"/STAGED_PROOF.json"
EXE="setup-BGXRANGED2.exe"
TOKEN_INSTALL="INSTALL_BGXRANGED_V2_MELEE_HANDOFF"
TOKEN_ROLLBACK="ROLLBACK_BGXRANGED_V2_MELEE_HANDOFF"
TP2_DATA="BACKUP ~BGXRANGED2/backup~\nAUTHOR ~BGXAI melee handoff pilot~\nBEGIN ~BGXAI fighter melee handoff V2~\nCOPY ~BGXRANGED2/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXRANGED2[/\\]SETUP-BGXRANGED2[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
V1_LAST=V1.NEW_LAST
PROTECTED=(BCS,LUA,PRIEST,"WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def guard(path):
    for p in (path,*path.parents):
        if p.is_symlink():raise ValueError("REPARSE_OR_SYMLINK:"+str(p))
        if p.exists() and getattr(p.stat(),"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0):
            raise ValueError("REPARSE_OR_SYMLINK:"+str(p))
        if p==ROOT:break
def require_root(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    guard(root)
    if not (root/"chitin.key").is_file():raise ValueError("NO_GAME")
def check_protected(root):
    for name,expected in ((LUA,P.PINS[LUA]),(PRIEST,P.PINS[PRIEST])):
        p=root/name;guard(p)
        if not p.is_file() or sha(p)!=expected:raise ValueError("PROTECTED_DRIFT:"+name)
def last(root):
    lines=(root/"WeiDU.log").read_text("utf-8-sig",errors="replace").splitlines()
    comps=[s.strip() for s in lines if s.lstrip().startswith("~")]
    if not comps:raise ValueError("NO_WEIDU_COMPONENTS")
    return comps[-1]
def v1_state(root):
    require_root(root);check_protected(root)
    if sha(root/BCS)!=V1_SHA or len(P.parts((root/BCS).read_bytes()))!=1171:
        raise ValueError("V1_BCS_NOT_EXACT")
    if not V1_LAST.match(last(root)):raise ValueError("V1_NOT_LAST_COMPONENT")
    if not (root/V1.PROOF).is_file():raise ValueError("V1_PROOF_MISSING")
    proof=json.loads((root/V1.PROOF).read_text("utf-8"))
    if proof.get("bcs_sha256")!=V1_SHA or proof.get("original_sha256")!=BASE_SHA:
        raise ValueError("V1_PROOF_SHA_MISMATCH")
    if sha(root/V1.STAGED)!=V1_SHA:raise ValueError("V1_STAGE_DRIFT")
    if (root/EXE).exists() or (root/DIR).exists():raise ValueError("V2_STAGING_COLLISION")
    return (root/BCS).read_bytes()
def status(root):
    require_root(root);check_protected(root)
    if LAST.match(last(root)):
        proof_file=root/PROOF
        if not proof_file.is_file():raise ValueError("V2_PROOF_MISSING")
        proof=json.loads(proof_file.read_text("utf-8"))
        if proof.get("candidate_sha256")!=V2_SHA or proof.get("previous_sha256")!=V1_SHA:
            raise ValueError("V2_PROOF_DRIFT")
        if sha(root/BCS)!=V2_SHA or sha(root/STAGED)!=V2_SHA:raise ValueError("V2_LIVE_SHA_DRIFT")
        merged=P.parts((root/BCS).read_bytes())
        if len(merged)!=1173:raise ValueError("V2_BLOCK_COUNT")
        baseline=b"SC\n"+b"".join(merged[3:])
        if sha_bytes(baseline)!=BASE_SHA:raise ValueError("V2_BASE_1170_CHANGED")
        return {"status":"BGXRANGED_V2_INSTALLED_VERIFIED","bcs_sha256":V2_SHA,
                "blocks":1173,"preserved_old_blocks":1170,"game_modified":False}
    if V1_LAST.match(last(root)):
        v1_state(root)
        return {"status":"BGXRANGED_V1_INSTALLED_V2_NOT_INSTALLED",
                "bcs_sha256":V1_SHA,"blocks":1171,"game_modified":False}
    raise ValueError("UNEXPECTED_LAST_WEIDU")
def snapshot(root):
    base=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXRANGED_V2_SAFE_BACKUPS"
    guard(base)
    folder=base/("PRE_V2_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name in PROTECTED+OPTIONAL:
        source=root/name;guard(source)
        if name in PROTECTED and not source.is_file():raise ValueError("MISSING_BACKUP_SOURCE:"+name)
        if not source.exists():continue
        if not source.is_file():raise ValueError("NOT_FILE:"+name)
        dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        hashes[name]=sha(source)
        if sha(dest)!=hashes[name]:raise ValueError("BACKUP_VERIFY_FAIL:"+name)
    (folder/"SHA256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")
    return folder
def native_candidate(root):
    report=V.run(root)
    if report.get("status")!="BGXRANGED_V2_NATIVE_PREFLIGHT_PASS":
        raise ValueError("NATIVE_PREFLIGHT_NOT_PASS")
    if report.get("current")!="V1_INSTALLED_1171":raise ValueError("V1_REQUIRED")
    if report["candidate_sha256"]!=V2_SHA or report["source_sha256"]!=V2_SOURCE_SHA:
        raise ValueError("CANDIDATE_OR_SOURCE_DRIFT")
    source=V.SOURCE
    with tempfile.TemporaryDirectory(prefix="BGXRANGED2_COMPILE_") as folder:
        p=pathlib.Path(folder);binary=p/"weidu.exe"
        binary.write_bytes((root/"setup-enhanced-powergaming-scripts.exe").read_bytes())
        baf=p/"BGXRANGEDV2.BAF";baf.write_bytes(source.read_bytes())
        out=p/"out";out.mkdir()
        q=subprocess.run([str(binary),"--game",str(root),"--out",str(out),str(baf)],
              cwd=p,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        if q.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",(q.stdout or "")+"\n"+(q.stderr or "")):
            raise ValueError("WEIDU_COMPILE_FAILED")
        files=list(out.rglob("BGXRANGEDV2.BCS"))
        if len(files)!=1:raise ValueError("COMPILED_V2_MISSING")
        new=P.parts(files[0].read_bytes())
        if len(new)!=3:raise ValueError("COMPILED_V2_BLOCK_COUNT")
        old=(root/BCS).read_bytes();prior=P.parts(old)
        if len(prior)!=1171 or sha_bytes(old)!=V1_SHA:raise ValueError("LIVE_V1_CHANGED")
        original=b"SC\n"+b"".join(prior[1:])
        if sha_bytes(original)!=BASE_SHA:raise ValueError("ORIGINAL_DRIFT")
        merged=b"SC\n"+b"".join(new)[:-3]+original[3:]
        if sha_bytes(merged)!=V2_SHA:raise ValueError("NOT_DETERMINISTIC")
        if P.parts(merged)[3:]!=P.parts(original):raise ValueError("BASE_BLOCKS_CHANGED")
        return merged
def call_weidu(root,uninstall=False):
    cmd=[str(root/EXE),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
       text=True,errors="replace",timeout=240)
    output=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",output):
        raise ValueError("WEIDU_STOP_MANUAL_RECOVERY_REQUIRED:"+output[-900:])
def install(root):
    V1.processes()
    old=v1_state(root)
    old_weidu=sha(root/"WeiDU.log")
    data=native_candidate(root)
    V1.processes()
    if sha(root/BCS)!=V1_SHA or sha(root/"WeiDU.log")!=old_weidu:raise ValueError("LIVE_CHANGED")
    backup=snapshot(root)
    folder=root/DIR;guard(folder)
    (folder/"staged").mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(data)
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({"candidate_sha256":V2_SHA,
      "previous_sha256":V1_SHA,"original_sha256":BASE_SHA,"backup":str(backup)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
    if sha(root/STAGED)!=V2_SHA:raise ValueError("STAGE_SHA")
    V1.processes()
    if sha(root/BCS)!=V1_SHA or sha(root/"WeiDU.log")!=old_weidu or not V1_LAST.match(last(root)):
        raise ValueError("LIVE_CHANGED_BEFORE_WRITE")
    call_weidu(root)
    result=status(root)
    if result["status"]!="BGXRANGED_V2_INSTALLED_VERIFIED":raise ValueError("POST_INSTALL_STATUS_FAIL")
    return dict(result,game_modified=True,backup=str(backup))
def rollback(root):
    V1.processes()
    current=status(root)
    if current["status"]!="BGXRANGED_V2_INSTALLED_VERIFIED" or not LAST.match(last(root)):
        raise ValueError("V2_NOT_LAST")
    proof=json.loads((root/PROOF).read_text("utf-8"))
    backup=pathlib.Path(proof["backup"])
    if backup.is_symlink():raise ValueError("BACKUP_LINK")
    checks=json.loads((backup/"SHA256.json").read_text("utf-8"))
    if checks.get(BCS)!=V1_SHA:raise ValueError("BACKUP_NOT_V1")
    for name,expected in checks.items():
        if sha(backup/name)!=expected:raise ValueError("BACKUP_TAMPERED:"+name)
    V1.processes()
    call_weidu(root,uninstall=True)
    result=status(root)
    if result["status"]!="BGXRANGED_V1_INSTALLED_V2_NOT_INSTALLED":
        raise ValueError("ROLLBACK_NOT_V1")
    return dict(result,status="BGXRANGED_V2_ROLLBACK_VERIFIED_V1_RESTORED",
                game_modified=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("mode",choices=("status","preflight","install","rollback"))
    p.add_argument("--game",default=str(ROOT));args=p.parse_args();root=pathlib.Path(args.game)
    try:
        if args.mode=="status":report=status(root)
        elif args.mode=="preflight":report=V.run(root)
        elif args.mode=="install":
            if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            report=install(root)
        else:
            if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            report=rollback(root)
        print(json.dumps(report,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXRANGED_V2_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
