#!/usr/bin/env python3
"""BGXAI V6 guarded DPLAYER duplicate-close-shot pilot; NOT automatic.

V6 targets only the shared DEFAULT DPLAYER.BCS two-block script and only
adds per-block OR(5) guard conditions. Existing BGXFENEMY WTASIGHT, class
BDDEFAI, EPS, TLK, CRE, save files and manual orders are not patched.
The user's native V6 RO preview passed; this installer independently verifies
the exact binary on each invocation before any staged install.

Native PRECHECK/TEST/INSTALL do not prove successful live melee timing.
Any SHA/WeiDU/backup conflict fails closed; rollback is LAST-only WeiDU.
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import BGXRANGED_V6_DPLAYER_NATIVE_READONLY as N
import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V5
import BGXFENEMY_WTASIGHT_GUARDED as E

GAME=N.GAME
PACKAGE="BGXRANGED7"
TARGET=N.DPLAYER
STAGED=PACKAGE+"/staged/DPLAYER.BCS"
PROOF=PACKAGE+"/PROOF.json"
TP2=PACKAGE+"/setup-BGXRANGED7.tp2"
EXE="setup-BGXRANGED7.exe"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXRANGED7[/\\]SETUP-BGXRANGED7[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
R27_LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXR27[/\\]SETUP-BGXR27[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
R27_LUA="override/M_BGXR27.lua"
R27_PROOF="BGXR27/PROOF.json"
R27_SOURCE_SHA="e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735"
def r27_status(root:Path)->dict:
    module=root/R27_LUA;proof_path=root/R27_PROOF
    safe(module);safe(proof_path)
    if not module.is_file() or sha(module)!=R27_SOURCE_SHA:
        raise ValueError("R27_INSTALLED_LUA_SHA_DRIFT")
    if not proof_path.is_file():raise ValueError("R27_INSTALL_PROOF_MISSING")
    record=json.loads(proof_path.read_text("utf-8"))
    if record.get("sourceSha256")!=R27_SOURCE_SHA or record.get("status")!="R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST":
        raise ValueError("R27_INSTALL_PROOF_INVALID")
    return {"status":"R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST"}

INSTALL_TOKEN="INSTALL_BGXRANGED7_DPLAYER_GUARD_PILOT"
ROLLBACK_TOKEN="ROLLBACK_BGXRANGED7_DPLAYER_GUARD_PILOT"
EXPECTED_NEW_SHA="4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed"
EXPECTED_SOURCE_SHA="2fd136f4eac23beb24c31744b01ae897aa6a9476e27cfe8392941ef30b600032"
TP2_CONTENT=(
    "BACKUP ~BGXRANGED7/backup~\n"
    "AUTHOR ~BGXAI guarded shared DPLAYER near-range duplicate attack pilot~\n"
    "BEGIN ~BGXRANGED7 two DPLAYER guard gates without attack changes~\n"
    "COPY ~BGXRANGED7/staged/DPLAYER.BCS~ ~override/DPLAYER.BCS~\n"
)
REQUIRED=(
 TARGET,N.BDDEFAI,N.WTASIGHT,"override/PRIEST1.BCS",
 "override/M_BX43.lua","override/M_BXFR.lua",R27_LUA,R27_PROOF,"WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
# BGXFENEMY checker pins *old* DPLAYER. After installation only this
# intentional exception is allowed; all other original hashes remain pinned.
OTHER={name:expected for name,expected in E.OTHER.items() if name!=TARGET}

def sha(path:Path)->str:
    return N.sha(path.read_bytes())

def safe(path:Path)->None:
    E.guard(path)

def running()->None:
    E.TRACE.V3.V2.V1.processes()

def weidu_last(root:Path)->str:
    return E.last(root)

def untouched(root:Path)->None:
    for name,expected in OTHER.items():
        p=root/name;safe(p)
        if not p.is_file() or sha(p)!=expected:
            raise ValueError("OTHER_RESOURCE_SHA_DRIFT:"+name)
    wt=root/N.WTASIGHT;safe(wt)
    if not wt.is_file() or sha(wt)!=N.EXPECTED_WTASIGHT_SHA:
        raise ValueError("BGXFENEMY_WTASIGHT_DRIFT")

def before(root:Path)->dict:
    if root!=GAME:raise ValueError("GAME_ROOT_NOT_ALLOWED")
    E.common(root)
    if not R27_LAST.match(weidu_last(root)):
        raise ValueError("R27_NOT_WEIDU_LAST")
    current=r27_status(root)
    if current.get("status")!="R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST":
        raise ValueError("R27_NOT_VERIFIED")
    if (root/PACKAGE).exists() or (root/EXE).exists():
        raise ValueError("V6_STAGING_COLLISION")
    original=root/TARGET;safe(original)
    if not original.is_file() or sha(original)!=N.EXPECTED_DPLAYER_SHA:
        raise ValueError("DPLAYER_BASELINE_SHA_DRIFT")
    main=root/N.BDDEFAI;safe(main)
    if not main.is_file() or sha(main)!=N.EXPECTED_BDDEFAI_SHA:
        raise ValueError("V5_ROLLBACK_BDDEFAI_BASELINE_DRIFT")
    untouched(root)
    for name in [*REQUIRED,*OPTIONAL,STAGED,PROOF,TP2,EXE]:
        safe(root/name)
    return {"last_weidu":weidu_last(root),
            "wei_log_sha256":sha(root/"WeiDU.log"),
            "old_dplayer_sha256":N.EXPECTED_DPLAYER_SHA}

def compile_candidate(root:Path)->tuple[bytes,dict]:
    basis=before(root)
    original=(root/TARGET).read_bytes()
    if len(V5.bcs_parts(original))!=2:
        raise ValueError("NATIVE_DPLAYER_NOT_TWO_BLOCKS")
    source=N.SOURCE
    if source.is_symlink() or not source.is_file() or sha(source)!=EXPECTED_SOURCE_SHA:
        raise ValueError("V6_SOURCE_SHA_DRIFT")
    executable=root/"setup-enhanced-powergaming-scripts.exe";safe(executable)
    if not executable.is_file() or executable.read_bytes()[:2]!=b"MZ":
        raise ValueError("NATIVE_WEIDU_EXE_MISSING")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED7_NATIVE_GUARD_") as folder:
        tmp=Path(folder)
        exe=tmp/"weidu.exe";shutil.copy2(executable,exe)
        old_bcs=tmp/"DPLAYER.BCS";old_bcs.write_bytes(original)
        old_baf=tmp/"DPLAYER.BAF"
        N.call_weidu(exe,root,tmp,old_bcs,old_baf,"DPLAYER_DECOMPILE")
        text=old_baf.read_text("utf-8-sig",errors="replace")
        candidate_baf=source.read_text("utf-8")
        proof=N.check_contract(text,candidate_baf)
        trial_baf=tmp/"BGXAIW6.BAF";trial_baf.write_bytes(source.read_bytes())
        trial_bcs=tmp/"BGXAIW6.BCS"
        N.call_weidu(exe,root,tmp,trial_baf,trial_bcs,"V6_NATIVE_COMPILE")
        candidate=trial_bcs.read_bytes()
        if len(V5.bcs_parts(candidate))!=2 or len(candidate)>N.V5.EXPECTED_BLOCKS*4000:
            raise ValueError("V6_NATIVE_BCS_STRUCTURE_OR_SIZE")
        if N.sha(candidate)!=EXPECTED_NEW_SHA:
            raise ValueError("V6_CANDIDATE_DIFFERS_FROM_USER_NATIVE_PASS")
        test_bcs=tmp/"V6_CONFIRM.BCS";test_bcs.write_bytes(candidate)
        test_baf=tmp/"V6_CONFIRM.BAF"
        N.call_weidu(exe,root,tmp,test_bcs,test_baf,"V6_REDECOMPILE")
        if V5.parse_blocks(test_baf.read_text("utf-8-sig",errors="replace"))!= \
           V5.parse_blocks(candidate_baf):
            raise ValueError("V6_REDECOMPILE_SEMANTIC_DRIFT")
        previous=V5.bcs_parts(original)
        newer=V5.bcs_parts(candidate)
        changed=[i+1 for i,(a,b) in enumerate(zip(previous,newer)) if a!=b]
        if changed!=[1,2] or not proof.get("candidate_two_actions_preserved") or \
            not proof.get("candidate_only_adds_close_range_conditional_veto"):
            raise ValueError("V6_NATIVE_OTHER_THAN_TWO_GUARD_BLOCKS")
    if weidu_last(root)!=basis["last_weidu"] or \
       sha(root/"WeiDU.log")!=basis["wei_log_sha256"] or \
       sha(root/TARGET)!=N.EXPECTED_DPLAYER_SHA:
        raise ValueError("V6_GAME_CHANGED_DURING_PREFLIGHT")
    untouched(root)
    return candidate,{**basis,"changed_blocks":[1,2],"original_blocks":2,
        "candidate_dplayer_sha256":N.sha(candidate),
        "candidate_baf_sha256":EXPECTED_SOURCE_SHA,
        "shared_default_script":True,"live_latency_verified":False,
        "game_modified":False,"install_performed":False}

def preflight(root:Path)->dict:
    _,proof=compile_candidate(root)
    return {**proof,"status":"BGXRANGED7_NATIVE_GUARDED_PREFLIGHT_PASS",
            "game_modified":False,"install_performed":False}

def backup(root:Path)->Path:
    parent=Path(os.environ.get("USERPROFILE",str(Path.home())))\
        /"Documents"/"BGXRANGED7_SAFE_BACKUPS"
    safe(parent)
    dest=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y%m%dT%H%M%S%fZ"))
    safe(dest)
    dest.mkdir(parents=True,exist_ok=False)
    hashes={}
    for name in [*REQUIRED,*OPTIONAL]:
        f=root/name;safe(f)
        if name in OPTIONAL and not f.exists():continue
        if f.is_symlink() or not f.is_file():raise ValueError("BACKUP_MISSING:"+name)
        target=dest/name;safe(target);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,target)
        hashes[name]=sha(f)
        if sha(target)!=hashes[name]:raise ValueError("BACKUP_COPY_SHA_MISMATCH:"+name)
    if hashes[TARGET]!=N.EXPECTED_DPLAYER_SHA or \
       hashes[N.BDDEFAI]!=N.EXPECTED_BDDEFAI_SHA or \
       hashes[N.WTASIGHT]!=N.EXPECTED_WTASIGHT_SHA:
        raise ValueError("BACKUP_BASELINE_SHA_MISMATCH")
    (dest/"SHA256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")
    return dest

def checked_backup(dest:Path)->dict:
    safe(dest)
    if not dest.is_dir() or dest.is_symlink():raise ValueError("BACKUP_FOLDER_MISSING")
    manifest=dest/"SHA256.json";safe(manifest)
    if not manifest.is_file():raise ValueError("BACKUP_MANIFEST_MISSING")
    hashes=json.loads(manifest.read_text("utf-8"))
    if not isinstance(hashes,dict) or any(x not in (*REQUIRED,*OPTIONAL) for x in hashes):
        raise ValueError("BACKUP_UNEXPECTED_KEYS")
    if any(x not in hashes for x in REQUIRED):raise ValueError("BACKUP_REQUIRED_MISSING")
    for name,expected in ((TARGET,N.EXPECTED_DPLAYER_SHA),
            (N.BDDEFAI,N.EXPECTED_BDDEFAI_SHA),
            (N.WTASIGHT,N.EXPECTED_WTASIGHT_SHA)):
        if hashes.get(name)!=expected:raise ValueError("BACKUP_HASH_BASE_DRIFT:"+name)
    for name,expected in hashes.items():
        f=dest/name;safe(f)
        if not f.is_file() or f.is_symlink() or sha(f)!=expected:
            raise ValueError("BACKUP_CORRUPTED:"+name)
    return hashes

def use_weidu(root:Path,uninstall:bool=False)->None:
    exe=root/EXE;safe(exe)
    if not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("V6_STAGED_EXE_MISSING")
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    proc=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,
        capture_output=True,text=True,errors="replace",timeout=240)
    msg=(proc.stdout or "")+"\n"+(proc.stderr or "")
    if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",msg):
        raise ValueError("WEIDU_MANUAL_REVIEW_STOP:"+msg[-700:])

def status(root:Path)->dict:
    if root!=GAME:raise ValueError("GAME_ROOT_DRIFT")
    E.common(root)
    current=weidu_last(root)
    if R27_LAST.match(current):
        result=r27_status(root)
        if result.get("status")!="R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST":
            raise ValueError("BASELINE_BGXFENEMY_STATUS_DRIFT")
        return {"status":"BGXRANGED7_NOT_INSTALLED_R27_VERIFIED",
                "game_modified":False}
    if not LAST.match(current):raise ValueError("BGXRANGED7_NOT_LAST_WEIDU")
    f=root/PROOF;safe(f)
    if not f.is_file():raise ValueError("V6_INSTALL_PROOF_MISSING")
    record=json.loads(f.read_text("utf-8"))
    if record.get("old_dplayer_sha256")!=N.EXPECTED_DPLAYER_SHA or \
       record.get("new_dplayer_sha256")!=EXPECTED_NEW_SHA or \
       record.get("source_sha256")!=EXPECTED_SOURCE_SHA or \
       record.get("changed_blocks")!=[1,2]:
        raise ValueError("V6_PROOF_SHA_DRIFT")
    saved=record.get("backup")
    if not isinstance(saved,str) or not Path(saved).is_absolute():
        raise ValueError("V6_BACKUP_POINTER_INVALID")
    copied=checked_backup(Path(saved))
    untouched(root)
    for name in [TARGET,STAGED]:
        f=root/name;safe(f)
        if not f.is_file() or sha(f)!=EXPECTED_NEW_SHA:
            raise ValueError("V6_STAGED_OR_LIVE_DPLAYER_SHA_DRIFT:"+name)
    old=V5.bcs_parts((Path(saved)/TARGET).read_bytes())
    new=V5.bcs_parts((root/TARGET).read_bytes())
    if len(old)!=2 or len(new)!=2 or \
       [i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b]!=[1,2]:
        raise ValueError("V6_NATIVE_BLOCK_DIFF_UNEXPECTED")
    for name in OPTIONAL:
        if name in copied:
            f=root/name;safe(f)
            if not f.is_file() or sha(f)!=copied[name]:
                raise ValueError("DIALOG_TLK_CHANGED:"+name)
    return {"status":"BGXRANGED7_INSTALLED_VERIFIED",
            "old_dplayer_sha256":N.EXPECTED_DPLAYER_SHA,
            "new_dplayer_sha256":EXPECTED_NEW_SHA,
            "changed_blocks":[1,2],"total_blocks":2,
            "bgxfenemy_wtasight_preserved":True,
            "badefai_and_eps_preserved":True,
            "live_latency_verified":False,"game_modified":False}

def install(root:Path)->dict:
    running()
    before(root)
    candidate,pre=compile_candidate(root)
    original_log=sha(root/"WeiDU.log")
    dest=backup(root)
    running()
    before(root)
    if sha(root/"WeiDU.log")!=original_log or \
       sha(root/TARGET)!=N.EXPECTED_DPLAYER_SHA:
        raise ValueError("PREINSTALL_BASELINE_CHANGED")
    stage=root/PACKAGE/"staged";safe(stage)
    stage.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(candidate)
    (root/TP2).write_text(TP2_CONTENT,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({
        "old_dplayer_sha256":N.EXPECTED_DPLAYER_SHA,
        "new_dplayer_sha256":EXPECTED_NEW_SHA,
        "source_sha256":EXPECTED_SOURCE_SHA,
        "changed_blocks":[1,2],"backup":str(dest)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
    running()
    if not R27_LAST.match(weidu_last(root)) or \
        sha(root/"WeiDU.log")!=original_log or \
        sha(root/TARGET)!=N.EXPECTED_DPLAYER_SHA or \
        sha(root/STAGED)!=EXPECTED_NEW_SHA:
        raise ValueError("FINAL_SHA_BEFORE_WEIDU_DRIFT")
    untouched(root)
    use_weidu(root)
    outcome=status(root)
    if outcome.get("status")!="BGXRANGED7_INSTALLED_VERIFIED":
        raise ValueError("V6_POSTINSTALL_VERIFICATION_FAILED")
    return {**outcome,"status":"BGXRANGED7_INSTALLED_VERIFIED",
            "backup":str(dest),"game_modified":True}

def rollback(root:Path)->dict:
    running()
    if not LAST.match(weidu_last(root)):
        raise ValueError("V7_NOT_LAST_WEIDU")
    verified=status(root)
    if verified.get("status")!="BGXRANGED7_INSTALLED_VERIFIED":
        raise ValueError("V6_STATUS_NOT_VERIFIED")
    f=root/PROOF;safe(f)
    record=json.loads(f.read_text("utf-8"))
    checked_backup(Path(record["backup"]))
    running()
    if not LAST.match(weidu_last(root)):
        raise ValueError("V6_WEIDU_CHANGED_BEFORE_ROLLBACK")
    use_weidu(root,uninstall=True)
    if not R27_LAST.match(weidu_last(root)) or \
       sha(root/TARGET)!=N.EXPECTED_DPLAYER_SHA or \
       r27_status(root).get("status")!="R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST":
        raise ValueError("R27_NOT_RESTORED_EXACT")
    return {"status":"BGXRANGED7_ROLLBACK_VERIFIED_R27_RESTORED",
            "restored_dplayer_sha256":N.EXPECTED_DPLAYER_SHA,
            "game_modified":True}

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",nargs="?",choices=("preflight","install","status","rollback"))
    parser.add_argument("--game",default=str(GAME))
    args=parser.parse_args()
    root=Path(args.game)
    try:
        mode=args.mode
        if mode is None:
            print("BGXRANGED7 - DPLAYER duplicate-close-shot guard (shared script)")
            print("1 - native preflight READ ONLY")
            print("2 - install+verify (typed consent required)")
            print("3 - status READ ONLY")
            print("4 - rollback (typed consent, last WeiDU only)")
            print("0 - exit, no changes")
            key=input("V6 choice [0]: ").strip() or "0"
            if key=="0":return 0
            actions={"1":"preflight","2":"install","3":"status","4":"rollback"}
            if key not in actions:raise ValueError("UNKNOWN_V6_MENU_CHOICE")
            mode=actions[key]
        if mode=="preflight":result=preflight(root)
        elif mode=="status":result=status(root)
        elif mode=="install":
            if input("Type "+INSTALL_TOKEN+" exactly: ").strip()!=INSTALL_TOKEN:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            result=install(root)
        else:
            if input("Type "+ROLLBACK_TOKEN+" exactly: ").strip()!=ROLLBACK_TOKEN:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            result=rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        print("BGXRANGED7_STOP:"+str(exc))
        return 1

if __name__=="__main__":
    sys.exit(main())
