#!/usr/bin/env python3
"""BGXP5 guarded 12-priority-cure + 4-friendly-filter BCS installation over BGXP3.

Requires real native EET compile, exact SHA baseline, external verified snapshot
and explicit per-action confirmation. No game edits in status or preflight.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import BGXP5_BCS_PREFLIGHT_READ_ONLY as PREF
import BGXP5_PRIORITY_AND_ALLY_GUARD_SOURCE_ONLY as SRC
import BGXP2_BCS_PATCH as BCS

ROOT=Path(r"C:\Games\BG_EET_FOXX_NEW")
BASE=Path(__file__).resolve().parent
BCS_PATH="override/BDDEFAI.BCS"
LUA_PATH="override/M_BX43.lua"
WEIDU_PATH="setup-enhanced-powergaming-scripts.exe"
STAGED="BGXP5/staged/BDDEFAI.BCS"
RESTORE_COPY="BGXP5/staged/ORIGINAL_BGXP3.BCS"
PROOF_PATH="BGXP5/STAGED_PROOF.json"
TP2="BGXP5/setup-BGXP5.tp2"
EXE="setup-BGXP5.exe"
TP2_TEXT=("BACKUP ~BGXP5/backup~\n"
          "AUTHOR ~BGXAI EPS-first AUTO healing and own-party protection~\n"
          "BEGIN ~BGXAI BGXP5 safe AUTO prioritise early heal and avoid friendly combat~\n"
          "COPY ~BGXP5/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n")
OLD_LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXP3[/\\]SETUP-BGXP3[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
NEW_LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXP5[/\\]SETUP-BGXP5[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
INSTALL_TOKEN="INSTALL_BGXP5_EARLY_HEAL_SAFE"
ROLLBACK_TOKEN="ROLLBACK_BGXP5_EARLY_HEAL_SAFE"
BACKUP=("WeiDU.log","chitin.key","weidu.conf",
        "lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk",
        BCS_PATH,LUA_PATH)


class Stop(RuntimeError):
    pass


def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()


def no_link(p:Path):
    if p.is_symlink():
        raise Stop("SYMLINK:"+str(p))
    try:
        if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Stop("REPARSE_POINT:"+str(p))
    except (AttributeError,FileNotFoundError):
        pass


def f(root:Path,rel:str,minbytes:int=1)->Path:
    if not rel or ":" in rel or "\\" in rel or rel.startswith("/") or ".." in rel.split("/"):
        raise Stop("UNSAFE_RELATIVE_PATH:"+rel)
    p=root/rel
    for x in (p,*p.parents):
        no_link(x)
        if x==root:break
    if not p.is_file() or p.stat().st_size<minbytes:
        raise Stop("MISSING_REQUIRED_FILE:"+rel)
    return p


def sources()->dict:
    manifest=json.loads(f(BASE,"SHA256_FILES.json").read_text("utf-8"))
    expected={'BGXPR_LAST_PRIORITY.baf','BGXP2_LAST_PRIORITY.baf','BGXP2_BCS_PATCH.py',
              'BGXP5_PRIORITY_AND_ALLY_GUARD_SOURCE_ONLY.py','BGXP5_BCS_PREFLIGHT_READ_ONLY.py',
              'BGXP5_INSTALL.py','test_bgxp5_source.py','test_bgxp5_bcs_preflight.py',
              'README_RU.md'}
    checks=manifest.get("sha256",{})
    if manifest.get("schema")!=1 or set(manifest.get("files",[]))!=expected or set(checks)!=expected:
        raise Stop("SOURCE_MANIFEST_INVALID")
    for name,digest in checks.items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+",name) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise Stop("SOURCE_MANIFEST_ENTRY_INVALID")
        raw=f(BASE,name).read_bytes()
        raw=raw.replace(b"\r\n",b"\n")
        if b"\r" in raw or sha(raw)!=digest:
            raise Stop("SOURCE_SHA_INVALID:"+name)
    SRC.report()
    return manifest


def last(root:Path)->str:
    rows=[x.strip() for x in f(root,"WeiDU.log").read_text("utf-8-sig",errors="replace").splitlines()
          if x.strip().startswith("~")]
    if not rows:raise Stop("NO_WEIDU_COMPONENTS")
    return rows[-1]


def base(root:Path,allow_stage:bool=False)->dict:
    root=root.resolve(strict=True)
    no_link(root)
    entry=last(root)
    if not OLD_LAST.match(entry):
        raise Stop("BGXP3_MUST_BE_LAST_WEIDU:"+entry)
    bcs=f(root,BCS_PATH).read_bytes()
    lua=f(root,LUA_PATH).read_bytes()
    if sha(bcs)!=PREF.BCS_PIN or sha(lua)!=PREF.LUA_PIN:
        raise Stop("LIVE_BGXP3_BCS_OR_LUA_SHA_MISMATCH")
    BCS.chunks(bcs,PREF.OLD_COUNT)
    proof=json.loads(f(root,"BGXP3/STAGED_PROOF.json").read_text("utf-8"))
    if proof.get("new_bcs_sha256")!=PREF.BCS_PIN or proof.get("lua_sha256")!=PREF.LUA_PIN:
        raise Stop("BGXP3_STAGED_PROOF_MISMATCH")
    if not allow_stage and ((root/"BGXP5").exists() or (root/EXE).exists()):
        raise Stop("BGXP5_STAGING_COLLISION")
    return {"state":"BGXP3_INSTALLED_VERIFIED","last_weidu":entry,
            "bcs_sha256":PREF.BCS_PIN,"lua_sha256":PREF.LUA_PIN,
            "total_blocks":PREF.OLD_COUNT}


def installed(root:Path)->dict:
    root=root.resolve(strict=True)
    if not NEW_LAST.match(last(root)):
        raise Stop("BGXP5_NOT_LAST_WEIDU")
    if f(root,TP2).read_text("utf-8")!=TP2_TEXT:
        raise Stop("BGXP5_TP2_CHANGED")
    proof=json.loads(f(root,PROOF_PATH).read_text("utf-8"))
    if proof.get("old_bcs_sha256")!=PREF.BCS_PIN or proof.get("lua_sha256")!=PREF.LUA_PIN:
        raise Stop("BGXP5_PROOF_CHANGED")
    before=f(root,RESTORE_COPY).read_bytes()
    after=f(root,BCS_PATH).read_bytes()
    if sha(before)!=PREF.BCS_PIN or sha(after)!=proof.get("new_bcs_sha256"):
        raise Stop("BGXP5_BCS_HASH_INVALID")
    if sha(f(root,STAGED).read_bytes())!=sha(after) or sha(f(root,LUA_PATH).read_bytes())!=PREF.LUA_PIN:
        raise Stop("BGXP5_STAGED_OR_LUA_DRIFT")
    old_blocks=BCS.chunks(before,PREF.OLD_COUNT)
    new_blocks=BCS.chunks(after,PREF.NEW_COUNT)
    if new_blocks[PREF.ADDITIONS:PREF.ADDITIONS+PREF.OLD_COMBAT_START]!=old_blocks[:PREF.OLD_COMBAT_START]:
        raise Stop("BGXP5_CHANGED_OLD_EPS_OR_BGXPR")
    if new_blocks[PREF.ADDITIONS+PREF.OLD_COMBAT_START:-4]!=old_blocks[PREF.OLD_COMBAT_START:-4]:
        raise Stop("BGXP5_CHANGED_OLD_SUPPORT")
    if all(a==b for a,b in zip(old_blocks[-4:],new_blocks[-4:])):
        raise Stop("BGXP5_FRIENDLY_FILTER_MISSING")
    return {"state":"BGXP5_INSTALLED_VERIFIED","total_blocks":1170,
            "bcs_sha256":sha(after),"lua_sha256":PREF.LUA_PIN,
            "old_blocks_preserved_exact":1154}


def running_guard():
    if os.name!="nt":raise Stop("WINDOWS_ONLY")
    command=('$ErrorActionPreference="Stop"; $p=Get-CimInstance Win32_Process | '
             'Where-Object {$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
             'if($p){$p|Select-Object Name,ProcessId|Out-String;exit 3}')
    r=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",command],
                     capture_output=True,text=True,stdin=subprocess.DEVNULL,
                     timeout=30,check=False)
    if r.returncode or r.stdout.strip():
        raise Stop("GAME_OR_WEIDU_RUNNING_OR_PROCESS_CHECK_FAILED:"+r.stdout[-350:])


def backup(root:Path,state:dict,label:str)->Path:
    dest=Path(os.environ.get("USERPROFILE",str(Path.home())))/"Documents"/"BGXAI_PRIEST5_SAFE_BACKUPS"
    no_link(dest);no_link(dest.parent)
    if root.resolve(strict=True)==dest.resolve() or root.resolve(strict=True) in dest.resolve().parents:
        raise Stop("BACKUP_MUST_BE_OUTSIDE_GAME")
    dest.mkdir(parents=True,exist_ok=True)
    folder=dest/(label+"_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(exist_ok=False)
    checks={}
    for rel in BACKUP:
        src=f(root,rel);target=folder/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        checks[rel]=sha(src.read_bytes())
        if sha(target.read_bytes())!=checks[rel]:
            raise Stop("EXTERNAL_BACKUP_HASH_MISMATCH:"+rel)
    (folder/"PROOF.json").write_text(json.dumps({"state":state,"sha256":checks},indent=2)+"\n",
                                     encoding="utf-8")
    return folder


def verify_nontargets(root:Path,snapshot:Path):
    sums=json.loads((snapshot/"PROOF.json").read_text("utf-8"))["sha256"]
    for rel in BACKUP:
        if rel not in (BCS_PATH,"WeiDU.log") and sha(f(root,rel).read_bytes())!=sums[rel]:
            raise Stop("NON_TARGET_CHANGED:"+rel)


def wei(root:Path,uninstall:bool=False)->str:
    exe=f(root,EXE,100000)
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),"--use-lang","ru_ru",
         "--force-uninstall" if uninstall else "--force-install","0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
                     text=True,encoding="utf-8",errors="replace",timeout=200,check=False)
    log=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise Stop("WEIDU_FAILED_NO_AUTORETRY:"+log[-1600:])
    return log[-1600:]


def native_candidate(root:Path)->tuple[bytes,dict]:
    game=root.resolve(strict=True)
    exe=f(game,WEIDU_PATH,100000)
    tlk=f(game,"lang/ru_RU/dialog.tlk")
    if exe.read_bytes()[:2]!=b"MZ":raise Stop("NOT_A_WEIDU_EXE")
    src=SRC.COMBAT_SOURCE.read_bytes()
    orig=PREF.compile_native(game,exe,tlk,SRC.expected_bgxp3_baf(src),"BGXP5_ORIG")
    guarded=PREF.compile_native(game,exe,tlk,SRC.guarded_combat_baf(src),"BGXP5_GUARDED")
    heal=PREF.compile_native(game,exe,tlk,SRC.priority_auto_cure_baf(),"BGXP5_HEAL")
    return PREF.assemble(f(game,BCS_PATH).read_bytes(),orig,guarded,heal)


def preflight(root:Path)->dict:
    sources()
    state=base(root)
    for name in BACKUP:f(root,name)
    out,details=native_candidate(root)
    if details.get("old_blocks_preserved_exact")!=1154 or len(out)<100:
        raise Stop("NATIVE_BCS_RESULT_FAILED")
    return {"status":"BGXP5_EET_READ_ONLY_PASS","baseline":state,
            "patch":details,"authorized_to_install":False,"game_modified":False}


def install(root:Path)->dict:
    running_guard()
    root=root.resolve(strict=True)
    ready=preflight(root)
    old_log_sha=sha(f(root,"WeiDU.log").read_bytes())
    saved=backup(root,ready["baseline"],"PRE_INSTALL")
    running_guard();base(root)
    if sha(f(root,"WeiDU.log").read_bytes())!=old_log_sha:
        raise Stop("WEIDU_LOG_CHANGED_DURING_PREFLIGHT")
    merged,delta=native_candidate(root)
    if delta.get("candidate_bcs_sha256")!=ready["patch"]["candidate_bcs_sha256"]:
        raise Stop("NONDETERMINISTIC_NATIVE_BCS")
    stage=root/"BGXP5"
    stage.mkdir(exist_ok=False)
    (stage/"staged").mkdir(exist_ok=False)
    (root/STAGED).write_bytes(merged)
    shutil.copy2(f(root,BCS_PATH),root/RESTORE_COPY)
    (root/PROOF_PATH).write_text(json.dumps({"old_bcs_sha256":PREF.BCS_PIN,
                                             "new_bcs_sha256":sha(merged),
                                             "lua_sha256":PREF.LUA_PIN},indent=2)+"\n",encoding="utf-8")
    (root/TP2).write_text(TP2_TEXT,encoding="utf-8",newline="\n")
    shutil.copy2(f(root,WEIDU_PATH,100000),root/EXE)
    running_guard();base(root,allow_stage=True)
    if sha(f(root,"WeiDU.log").read_bytes())!=old_log_sha:
        raise Stop("WEIDU_LOG_CHANGED_BEFORE_INSTALL")
    tail=wei(root)
    (saved/"WeiDU_install_tail.txt").write_text(tail,encoding="utf-8")
    result=installed(root)
    verify_nontargets(root,saved)
    return {"status":"BGXP5_INSTALLED_VERIFIED","backup":str(saved),"after":result}


def rollback(root:Path)->dict:
    running_guard()
    root=root.resolve(strict=True)
    state=installed(root)
    saved=backup(root,state,"PRE_ROLLBACK")
    running_guard();installed(root)
    tail=wei(root,uninstall=True)
    (saved/"WeiDU_rollback_tail.txt").write_text(tail,encoding="utf-8")
    result=base(root,allow_stage=True)
    verify_nontargets(root,saved)
    return {"status":"BGXP5_RETURNED_TO_BGXP3_VERIFIED","backup":str(saved),"after":result}


def main(argv=None)->int:
    arg=argparse.ArgumentParser()
    arg.add_argument("mode",nargs="?",default="status",choices=["status","preflight","install","rollback"])
    arg.add_argument("--yes",action="store_true")
    arg.add_argument("--confirm",default="")
    arg.add_argument("--game-root",type=Path,default=ROOT)
    o=arg.parse_args(argv)
    try:
        sources()
        if o.mode=="status":
            x=installed(o.game_root) if NEW_LAST.match(last(o.game_root)) else base(o.game_root,allow_stage=True)
            result={"status":"READ_ONLY_STATUS","game":x}
        elif o.mode=="preflight":
            result=preflight(o.game_root)
        else:
            token=INSTALL_TOKEN if o.mode=="install" else ROLLBACK_TOKEN
            if not o.yes or o.confirm!=token:
                raise Stop("EXPLICIT_TYPED_APPROVAL_REQUIRED:"+token)
            if os.name!="nt" or o.game_root!=ROOT:
                raise Stop("LIVE_MUTATION_REQUIRES_EXACT_WINDOWS_ROOT")
            result=install(ROOT) if o.mode=="install" else rollback(ROOT)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (Stop,ValueError,OSError,UnicodeError,KeyError,subprocess.TimeoutExpired) as e:
        print("BGXP5_STOP:",e)
        return 2


if __name__=="__main__":
    sys.exit(main())
