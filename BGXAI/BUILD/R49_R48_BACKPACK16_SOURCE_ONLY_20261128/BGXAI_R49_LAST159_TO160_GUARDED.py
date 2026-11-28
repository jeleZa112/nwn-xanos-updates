#!/usr/bin/env python3
"""R49 one-item safer backpack16 source fix: guarded R48-last159 -> R49-last160.

Only new intent: fix old R48's proven wrong hardcoded SLOT_MISC5.
Reuses frozen original R48 (including R47/R44/R42/R38 ancestry) and frozen
R49 one-trigger BAF composer. Adds a *separate* first/top R49 BCS block,
using the SAME actor-local BGX48TRY; the old R48 block stays installed but
cannot execute after the R49 one-shot flag is set. No new EPS listener.

Any WeiDU mutation requires a distinct exact user-typed consent via the
SAME original modular BGXAI_UPDATE.cmd, external hash-verified backup,
frozen preimage, last-only component, no automatic rollback or retry.
"""
from __future__ import annotations

import argparse
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
R48_PATH=REPO/"BGXAI/BUILD/R48_ONE_REAL_STAF01_EQUIP_AFTER_R47_20261128/BGXAI_R48_LAST158_TO159_ONE_ITEM_GUARDED.py"
COMPOSE_PATH=HERE/"BGXAI_R49_REUSE_R48_BACKPACK16_SOURCE_ONLY.py"
R48_BLOB="1051bfd0f4fc767590468924dc8147e6e86ec768"
COMPOSE_BLOB="7c6ba99e56f98fd72a1f15b18a91a0bb32e69387"
SCHEMA="BGXAI_R49_BACKPACK16_ONE_STAF01_LAST160_GUARDED_V1"
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
DIR="BGXR49"
BAF=DIR+"/staged/BGX_R49_ONCE.baf"
TP2=DIR+"/setup-BGXR49.tp2"
EXE=DIR+"/setup-BGXR49.exe"
PROOF=DIR+"/PROOF.json"
SOURCE_BCS="override/BDDEFAI.BCS"
ONCE_FLAG="BGX48TRY"
INSTALL_TOKEN="INSTALL_BGXAI_R49_BACKPACK16_ONE_STAF01_AFTER_R48_LAST159"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R49_RESTORE_R48_LAST159_ONLY"
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR49[/\\]SETUP-BGXR49[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
TP2_TEXT=(
 "BACKUP ~BGXR49/backup~\n"
 "AUTHOR ~BGXAI R49 bounded STAF01 16 backpack slot correction~\n"
 "BEGIN ~BGXR49 STAF01 single idle attempt corrected backpack16~\n"
 "EXTEND_TOP ~BDDEFAI.BCS~ ~BGXR49/staged/BGX_R49_ONCE.baf~\n"
)
class Hold(ValueError):
    pass

def sha(x:bytes)->str:
    return hashlib.sha256(x).hexdigest()

def blob(x:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def frozen(path:Path,expected:str,name:str):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=expected:
        raise Hold("HOLD_R49_PINNED_SOURCE_"+name)
    spec=importlib.util.spec_from_file_location("bgxai_r49_"+name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R49_IMPORT_"+name)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_checked():
    r48=frozen(R48_PATH,R48_BLOB,"R48_GUARD")
    composer=frozen(COMPOSE_PATH,COMPOSE_BLOB,"R49_COMPOSER")
    r47,r44,r43,r42,r38,old,_=r48.load_checked()
    baf=composer.compose()
    if (composer.SCHEMA!="BGXAI_R49_REUSE_R48_ANY_BACKPACK16_ONE_SHOT_SOURCE_ONLY_V1"
        or len(baf)==0 or len(baf)>2500
        or baf.count(b"OR(16)\\n")!=0
        or baf.count(b"OR(16)\n")!=1
        or baf.count(b"CheckItemSlot(")!=16
        or baf.count(b'Global("BGX48TRY","LOCALS",0)')!=1
        or baf.count(b'SetGlobal("BGX48TRY","LOCALS",1)')!=1
        or baf.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')!=1
        or baf.count(b'ActionListEmpty()')!=1
        or baf.count(b'CombatCounter(0)')!=1):
        raise Hold("HOLD_R49_ONE_ITEM_ONE_ACTION_CANDIDATE_INVALID")
    if ("EXTEND_TOP ~BDDEFAI.BCS~" not in TP2_TEXT or
        TP2_TEXT.count("EXTEND_TOP")!=1):
        raise Hold("HOLD_R49_TP2_UNSAFE")
    return r48,r47,r44,r43,r42,r38,old,composer

def exact_last_159(r48,r47,r44,r43,r42,r38,old,game):
    r48.exact_last_r48(r47,r44,r43,r42,r38,old,game)
    proof=r48.exact_proof(old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R49_R48_INSTALLED_BCS_SHA_DRIFT")
    return proof

def snapshot_r48(r48,r47,r44,r43,r42,r38,old,game):
    proof=exact_last_159(r48,r47,r44,r43,r42,r38,old,game)
    baseline=proof.get("baselineSnapshot")
    if type(baseline) is not dict or not baseline or (
        SOURCE_BCS not in baseline or "WeiDU.log" not in baseline):
        raise Hold("HOLD_R49_R48_BASELINE_SNAPSHOT_UNTRUSTED")
    # A previous R48 install may change only these two paths.
    for rel,digest in baseline.items():
        if rel not in (SOURCE_BCS,"WeiDU.log"):
            if old.sha(old.safe(game,rel))!=digest:
                raise Hold("HOLD_R49_R48_UNRELATED_ANCESTOR_DRIFT")
    files=dict(baseline)
    for rel in (SOURCE_BCS,"WeiDU.log",r48.PROOF,r48.BAF,r48.TP2,r48.EXE):
        f=old.safe(game,rel)
        if not f.is_file() or f.is_symlink():
            raise Hold("HOLD_R49_R48_PROOF_OR_OWNER_FILE_MISSING")
        files[rel]=old.sha(f)
    if files[SOURCE_BCS]!=proof["installedBcsSHA256"]:
        raise Hold("HOLD_R49_R48_BCS_PREIMAGE_NOT_AUTHENTIC")
    old.verify_snapshot(game,files)
    return files

def preflight(r48,r47,r44,r43,r42,r38,old,composer,game,*,require_stopped=True):
    old.protected_root(game,True)
    if require_stopped:
        r42.check_processes(r38,old)
    snapshot=snapshot_r48(r48,r47,r44,r43,r42,r38,old,game)
    for rel in (DIR,BAF,TP2,EXE,PROOF):
        if old.safe(game,rel).exists():
            raise Hold("HOLD_R49_NAMESPACE_ALREADY_PRESENT")
    compiler=old.safe(game,"setup-enhanced-powergaming-scripts.exe")
    if compiler.is_symlink() or not compiler.is_file() or old.sha(compiler)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R49_NATIVE_WEIDU_ORIGIN_CHANGED")
    candidate=composer.compose()
    if len(candidate)==0 or len(candidate)>2500:
        raise Hold("HOLD_R49_BAF_SIZE")
    return {"schema":SCHEMA,"status":"R49_SOURCE_PREFLIGHT_R48_LAST159_PASS_NO_INSTALL",
        "installed":False,"gameModified":False,"ordersSent":0,
        "originalR48Last159Verified":True,
        "oldR48OneShotFlagReused":True,
        "onlyOneNewXEquipSourceAction":True,
        "candidateBafSHA256":sha(candidate),
        "candidateBafBytes":len(candidate),
        "originalBcsSHA256":snapshot[SOURCE_BCS],
        "nativeCompilationOnUserEETVerified":False,
        "noAutoRetry":True}

def external_backup(old,game,snapshot):
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R49_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("HOLD_R49_BACKUP_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix="PRE_BGXR49_",dir=parent))
    for rel,digest in snapshot.items():
        src=old.safe(game,rel)
        target=old.safe(backup,rel)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if old.sha(target)!=digest:
            raise Hold("HOLD_R49_BACKUP_SHA_MISMATCH")
    old.safe(backup,"SHA256.json").write_text(
        json.dumps(snapshot,indent=2),encoding="utf-8")
    return backup

def native_weidu(old,game,r42,*,uninstall=False):
    exe=old.safe(game,EXE)
    if exe.is_symlink() or not exe.is_file() or old.sha(exe)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R49_NATIVE_WEIDU_BINARY_DRIFT")
    argv=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(game),
          "--use-lang","ru_ru",
          "--force-uninstall" if uninstall else "--force-install","0"]
    res=subprocess.run(argv,cwd=game,stdin=subprocess.DEVNULL,
          capture_output=True,text=True,errors="replace",timeout=240,check=False)
    combined=(res.stdout or "")+"\n"+(res.stderr or "")
    if res.returncode!=0 or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",combined):
        raise Hold("HOLD_R49_NATIVE_WEIDU_MANUAL_REVIEW")

def exact_last_160(r48,r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if (len(rows)!=160 or not old.last_r37_history(rows[:153])
        or r38.LAST.match(rows[153]) is None
        or r42.LAST.match(rows[154]) is None
        or r43.LAST.match(rows[155]) is None
        or r44.LAST.match(rows[156]) is None
        or r47.LAST.match(rows[157]) is None
        or r48.LAST.match(rows[158]) is None
        or LAST.match(rows[159]) is None):
        raise Hold("HOLD_R49_NOT_EXACT_LAST160_AFTER_R48")
    if (old.sha(old.safe(game,r47.SOURCE_LUA))!=r47.EXPECTED_LUA_SHA
        or old.sha(old.safe(game,r44.OVERRIDE))!=r44.EXPECTED_SHA):
        raise Hold("HOLD_R49_R47_R44_LUA_DRIFT")
    return rows

def exact_proof(old,game):
    path=old.safe(game,PROOF)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:
        raise Hold("HOLD_R49_PROOF_MISSING")
    d=json.loads(path.read_text(encoding="utf-8"))
    if (type(d) is not dict or d.get("schema")!=SCHEMA or
        d.get("status")!="R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME" or
        d.get("installed") is not True or
        d.get("approved") is not True or
        d.get("onceFlag")!=ONCE_FLAG or
        d.get("ordersSentAtInstall")!=0 or
        d.get("actualXEquipPerformed") is not False or
        d.get("originalR48Last159Preserved") is not True):
        raise Hold("HOLD_R49_PROOF_INVALID")
    return d

def status(r48,r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if len(rows)==159:
        exact_last_159(r48,r47,r44,r43,r42,r38,old,game)
        return {"schema":SCHEMA,"status":"R49_NOT_INSTALLED_R48_LAST159",
             "installed":False,"gameModified":False,"ordersSent":0}
    if len(rows)==160:
        exact_last_160(r48,r47,r44,r43,r42,r38,old,game)
        proof=exact_proof(old,game)
        if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
            raise Hold("HOLD_R49_LIVE_BCS_SHA_CHANGED")
        if old.sha(old.safe(game,r48.PROOF))!=proof.get("originalR48ProofSHA256"):
            raise Hold("HOLD_R49_R48_PROOF_DRIFT")
        return {"schema":SCHEMA,"status":"R49_BACKPACK16_LAST160_INSTALLED_AWAITING_GAME",
            "installed":True,"gameModified":False,"ordersSent":0,
            "actualXEquipPerformed":False}
    raise Hold("HOLD_R49_WEIDU_COUNT_NOT_159_OR_160")

def install(r48,r47,r44,r43,r42,r38,old,composer,game,token):
    if token!=INSTALL_TOKEN:
        raise Hold("HOLD_R49_EXACT_TYPED_INSTALL_REQUIRED")
    before=preflight(r48,r47,r44,r43,r42,r38,old,composer,game)
    snapshot=snapshot_r48(r48,r47,r44,r43,r42,r38,old,game)
    backup=external_backup(old,game,snapshot)
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    baf=composer.compose()
    old.safe(game,DIR).mkdir(parents=True,exist_ok=False)
    old.safe(game,BAF).parent.mkdir(parents=True,exist_ok=False)
    old.safe(game,BAF).write_bytes(baf)
    old.safe(game,TP2).write_text(TP2_TEXT,encoding="ascii",newline="\n")
    shutil.copy2(old.safe(game,"setup-enhanced-powergaming-scripts.exe"),
                 old.safe(game,EXE))
    if (old.sha(old.safe(game,BAF))!=sha(baf) or
        old.sha(old.safe(game,EXE))!=r42.WEIDU_SHA):
        raise Hold("HOLD_R49_STAGED_NATIVE_COMPILER_DRIFT")
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    target=old.safe(game,PROOF)
    target.write_text(json.dumps({
        "schema":SCHEMA,
        "status":"R49_WEIDU_PENDING_MANUAL_REVIEW_IF_INTERRUPTED",
        "originalBcsSHA256":snapshot[SOURCE_BCS],
        "candidateBafSHA256":sha(baf),
        "baselineSnapshot":snapshot,
        "externalBackup":str(backup),
        "originalR48ProofSHA256":snapshot[r48.PROOF],
    },indent=2),encoding="utf-8")
    # From here: potential native real game mutations, never auto-retry.
    native_weidu(old,game,r42)
    exact_last_160(r48,r47,r44,r43,r42,r38,old,game)
    post=old.sha(old.safe(game,SOURCE_BCS))
    if post==snapshot[SOURCE_BCS]:
        raise Hold("HOLD_R49_BCS_UNCHANGED_AFTER_INSTALL")
    for rel,digest in snapshot.items():
        if rel not in (SOURCE_BCS,"WeiDU.log") and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R49_UNRELATED_RESOURCE_CHANGED")
    output={"schema":SCHEMA,
        "status":"R49_BACKPACK16_ONE_STAF01_INSTALLED_AWAITING_GAME",
        "installed":True,"approved":True,"gameModified":True,
        "onceFlag":ONCE_FLAG,"sourceItem":"STAF01",
        "sourceBackpackSlots":list(range(18,34)),
        "sourceBackpackSlot22Included":True,"targetWeaponSlot":35,
        "originalR48Last159Preserved":True,
        "originalR48ProofSHA256":snapshot[r48.PROOF],
        "originalBcsSHA256":snapshot[SOURCE_BCS],
        "installedBcsSHA256":post,
        "candidateBafSHA256":sha(baf),
        "baselineSnapshot":snapshot,
        "externalBackup":str(backup),
        "ordersSentAtInstall":0,"actualXEquipPerformed":False,
        "noAutoRetry":False}
    target.write_text(json.dumps(output,indent=2),encoding="utf-8")
    return output

def rollback(r48,r47,r44,r43,r42,r38,old,game,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold("HOLD_R49_EXACT_TYPED_ROLLBACK_REQUIRED")
    exact_last_160(r48,r47,r44,r43,r42,r38,old,game)
    r42.check_processes(r38,old)
    proof=exact_proof(old,game)
    backup=Path(proof.get("externalBackup",""))
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R49_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if (backup.parent!=parent or not backup.name.startswith("PRE_BGXR49_")
        or not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R49_UNTRUSTED_BACKUP_PATH")
    saved=json.loads(old.safe(backup,"SHA256.json").read_text(encoding="utf-8"))
    if saved!=proof.get("baselineSnapshot"):
        raise Hold("HOLD_R49_BACKUP_SNAPSHOT_DRIFT")
    old.verify_snapshot(backup,saved)
    if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R49_LIVE_BCS_DRIFT")
    for rel,digest in saved.items():
        if rel not in (SOURCE_BCS,"WeiDU.log") and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R49_UNRELATED_RESOURCE_DRIFT")
    if old.sha(old.safe(game,r48.PROOF))!=proof.get("originalR48ProofSHA256"):
        raise Hold("HOLD_R49_R48_PROOF_DRIFT")
    r42.check_processes(r38,old)
    native_weidu(old,game,r42,uninstall=True)
    exact_last_159(r48,r47,r44,r43,r42,r38,old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=saved[SOURCE_BCS]:
        raise Hold("HOLD_R49_BCS_NOT_RESTORED_TO_R48")
    for rel,digest in saved.items():
        if rel!="WeiDU.log" and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R49_ROLLBACK_RESOURCE_DRIFT")
    return {"schema":SCHEMA,"status":"R49_ROLLBACK_RESTORED_ORIGINAL_R48_LAST159",
       "installed":False,"gameModified":True,
       "ordersSentAtInstall":0,
       "note":"Restores R48 BCS, not save actor BGX48TRY LOCALS/inventory"}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,default=GAME)
    p.add_argument("--mode",choices=("status","preflight","install","rollback"),default="status")
    p.add_argument("--onefile-review-gate",action="store_true")
    args=p.parse_args(argv)
    try:
        r48,r47,r44,r43,r42,r38,old,composer=load_checked()
        if args.mode=="status":
            out=status(r48,r47,r44,r43,r42,r38,old,args.game)
        elif args.mode=="preflight":
            out=preflight(r48,r47,r44,r43,r42,r38,old,composer,args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_R49_ONLY_ORIGINAL_TYPED_UPDATER")
        elif args.mode=="install":
            approval=input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            out=install(r48,r47,r44,r43,r42,r38,old,composer,args.game,approval)
        else:
            approval=input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            out=rollback(r48,r47,r44,r43,r42,r38,old,args.game,approval)
        returncode=0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            subprocess.TimeoutExpired,EOFError) as exc:
        out={"schema":SCHEMA,"status":"R49_STOP_MANUAL_REVIEW",
            "reason":str(exc) if isinstance(exc,Hold) else "HOLD_R49_RUNTIME_IO",
            "gameModifiedUnknown":args.mode in ("install","rollback"),
            "noAutoRetry":True,
            "actualXEquipPerformed":False}
        returncode=3
    print(json.dumps(out,ensure_ascii=True,indent=2))
    return returncode

if __name__=="__main__":
    sys.exit(main())
