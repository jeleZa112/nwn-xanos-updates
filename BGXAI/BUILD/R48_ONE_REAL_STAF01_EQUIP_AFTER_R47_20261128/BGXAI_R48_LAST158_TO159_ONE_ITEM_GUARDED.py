#!/usr/bin/env python3
"""BGXAI R48: SINGLE consented real XEquipItem pilot, not another observer.

WeiDU last159 successor to installed R47 last158. It EXTEND_TOP's one exact,
real-R39-derived off-combat / empty-queue STAF01 action, bounded by the new
actor LOCALS BGX48TRY=0 -> 1, so at most one attempt per saved actor.
It is enabled only on a separate typed user-authorized install, not by source
publication or R47's inconclusive witness. WeiDU rollback restores previous
R47 BCS byte-for-byte; it does not edit or revert save-game LOCALS.

The one gameplay test should use an expendable pre-pilot test save, actor AI
enabled, one selected Jagan outside combat. No more passive BCS capture loops.
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
R47_PATH=REPO/"BGXAI/BUILD/R47_GUARDED_BDDEFAI_EXEC_WITNESS_SOURCEONLY_20261128/BGXAI_R47_WITNESS_LAST157_TO158_GUARDED_SOURCE_ONLY.py"
COMPOSE_PATH=HERE/"BGXAI_R48_REUSE_R39_ONE_SHOT_BAF_SOURCE_ONLY.py"
R47_BLOB="9f81e92fc6e9b0d8b44f3d1c9abf2db28bdd0c6a"
COMPOSE_BLOB="87049cafc4108c607fffd5b907a7557149bcdfd8"
SCHEMA="BGXAI_R48_SINGLE_STAF01_LAST159_GUARDED_V1"
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
DIR="BGXR48"
BAF=DIR+"/staged/BGX_R48_ONCE.baf"
TP2=DIR+"/setup-BGXR48.tp2"
EXE=DIR+"/setup-BGXR48.exe"
PROOF=DIR+"/PROOF.json"
SOURCE_BCS="override/BDDEFAI.BCS"
ONCE_FLAG="BGX48TRY"
INSTALL_TOKEN="INSTALL_BGXAI_R48_ONE_STAF01_FROM_BACKPACK_TO_WEAPON_AFTER_R47"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R48_RESTORE_R47_ONLY"
LAST=re.compile(r'^~(?:[^~]*[/\\])?BGXR48[/\\]SETUP-BGXR48[.]TP2~\s+#0\s+#0(?:\s|$)',re.I)
TP2_TEXT=(
 "BACKUP ~BGXR48/backup~\n"
 "AUTHOR ~BGXAI R48 first actual STAF01 equip pilot exact single attempt~\n"
 "BEGIN ~BGXR48 one-shot STAF01 idle equip under explicit user approval~\n"
 "EXTEND_TOP ~BDDEFAI.BCS~ ~BGXR48/staged/BGX_R48_ONCE.baf~\n"
)
class Hold(ValueError):
    pass
def sha(x:bytes)->str:
    return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def verified_module(path,pinned,name):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=pinned:
        raise Hold("HOLD_PINNED_R48_ANCESTOR:"+name)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R48_SOURCE_IMPORT:"+name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def load_checked():
    r47=verified_module(R47_PATH,R47_BLOB,"r48_unchanged_last158_r47")
    composer=verified_module(COMPOSE_PATH,COMPOSE_BLOB,"r48_one_staf01_baf")
    r44,r43,r42,r38,old,_=r47.load_checked()
    baf=composer.compose()
    if (baf.count(b"XEquipItem(")!=1 or
        baf.count(b'SetGlobal("BGX48TRY","LOCALS",1)')!=1 or
        baf.count(b'Global("BGX48TRY","LOCALS",0)')!=1 or
        b"ActionListEmpty()" not in baf or
        b"CombatCounter(0)" not in baf):
        raise Hold("HOLD_R48_SINGLE_ACTION_CANDIDATE_INVALID")
    return r47,r44,r43,r42,r38,old,composer

def safe_snapshot(r47,r44,r43,r42,r38,old,game):
    r47.exact_last_r47(r44,r43,r42,r38,old,game)
    proof=r47.exact_proof(old,game)
    if proof.get("installed") is not True:
        raise Hold("HOLD_R47_LAST158_PROOF_NOT_INSTALLED")
    source_sha=proof.get("installedBcsSha256")
    if type(source_sha) is not str or re.fullmatch(r"[a-f0-9]{64}",source_sha) is None:
        raise Hold("HOLD_R48_R47_INSTALLED_BCS_SHA_INVALID")
    if old.sha(old.safe(game,SOURCE_BCS))!=source_sha:
        raise Hold("HOLD_R48_R47_INSTALLED_BCS_DRIFT")
    if old.sha(old.safe(game,r47.SOURCE_LUA))!=r47.EXPECTED_LUA_SHA:
        raise Hold("HOLD_R48_R47_WITNESS_LUA_DRIFT")
    snapshot=proof.get("baselineSnapshot")
    if type(snapshot) is not dict:
        raise Hold("HOLD_R48_R47_SNAPSHOT_MISSING")
    observed=dict(snapshot)
    observed["WeiDU.log"]=old.sha(old.safe(game,"WeiDU.log"))
    observed[SOURCE_BCS]=source_sha
    observed[r47.SOURCE_LUA]=r47.EXPECTED_LUA_SHA
    observed[r47.PROOF]=old.sha(old.safe(game,r47.PROOF))
    for rel in (r44.PROOF,r43.PROOF,r42.PROOF,r47.SOURCE_LUA,SOURCE_BCS):
        if rel not in observed:raise Hold("HOLD_R48_ANCESTOR_SNAPSHOT_MISSING:"+rel)
    old.verify_snapshot(game,observed)
    return observed

def before_change(r47,r44,r43,r42,r38,old,composer,game):
    old.protected_root(game,True)
    r42.check_processes(r38,old)
    snapshot=safe_snapshot(r47,r44,r43,r42,r38,old,game)
    for rel in (DIR,BAF,TP2,EXE,PROOF):
        if old.safe(game,rel).exists():
            raise Hold("HOLD_R48_STAGING_OR_OWNER_ALREADY_PRESENT:"+rel)
    compiler=old.safe(game,"setup-enhanced-powergaming-scripts.exe")
    if compiler.is_symlink() or not compiler.is_file() or old.sha(compiler)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R48_ORIGINAL_NATIVE_WEIDU_DRIFT")
    candidate=composer.compose()
    if len(candidate)==0 or len(candidate)>2500:
        raise Hold("HOLD_R48_BAF_SIZE")
    return {"schema":SCHEMA,"status":"R48_LAST158_SOURCE_EXACT_ONE_ITEM_READY_NOT_INSTALLED",
       "sourceBcsSHA256":snapshot[SOURCE_BCS],
       "candidateBafSHA256":sha(candidate),
       "candidateBafBytes":len(candidate),
       "r47Preserved":True,
       "userApprovedRealItemMove":False,
       "installed":False,"gameModified":False,"ordersSent":0,
       "actualXEquipPerformed":False}

def external_backup(old,game,snapshot):
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R48_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if parent.is_symlink() or (hasattr(parent,"is_junction") and parent.is_junction()):
        raise Hold("HOLD_R48_BACKUP_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix="PRE_BGXR48_",dir=parent))
    for rel,digest in snapshot.items():
        src=old.safe(game,rel)
        target=old.safe(backup,rel)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if old.sha(target)!=digest:
            raise Hold("HOLD_R48_BACKUP_SHA:"+rel)
    old.safe(backup,"SHA256.json").write_text(json.dumps(snapshot,indent=2),encoding="utf-8")
    return backup

def native_weidu(old,game,r42,uninstall=False):
    exe=old.safe(game,EXE)
    if exe.is_symlink() or not exe.is_file() or old.sha(exe)!=r42.WEIDU_SHA:
        raise Hold("HOLD_R48_NATIVE_WEIDU_BINARY")
    args=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(game),
          "--use-lang","ru_ru",
          "--force-uninstall" if uninstall else "--force-install","0"]
    res=subprocess.run(args,cwd=game,stdin=subprocess.DEVNULL,
                       capture_output=True,text=True,errors="replace",
                       timeout=240,check=False)
    combined=(res.stdout or "")+"\n"+(res.stderr or "")
    if res.returncode!=0 or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",combined):
        raise Hold("HOLD_R48_NATIVE_WEIDU_MANUAL_REVIEW")

def exact_last_r48(r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if (len(rows)!=159 or not old.last_r37_history(rows[:153]) or
        r38.LAST.match(rows[153]) is None or r42.LAST.match(rows[154]) is None or
        r43.LAST.match(rows[155]) is None or r44.LAST.match(rows[156]) is None or
        r47.LAST.match(rows[157]) is None or LAST.match(rows[158]) is None):
        raise Hold("HOLD_R48_NOT_LAST_159")
    if old.sha(old.safe(game,r47.SOURCE_LUA))!=r47.EXPECTED_LUA_SHA:
        raise Hold("HOLD_R48_R47_WITNESS_SOURCE_CHANGED")
    if old.sha(old.safe(game,r44.OVERRIDE))!=r44.EXPECTED_SHA:
        raise Hold("HOLD_R48_R44_LISTENER_CHANGED")
    return rows

def exact_proof(old,game):
    path=old.safe(game,PROOF)
    if not path.is_file() or path.is_symlink() or path.stat().st_size>1_000_000:
        raise Hold("HOLD_R48_PROOF_NOT_REGULAR")
    d=json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(d,dict) or d.get("schema")!=SCHEMA or
        d.get("status")!="R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME" or
        d.get("installed") is not True or d.get("userApprovedRealItemMove") is not True or
        d.get("onceFlag")!=ONCE_FLAG or
        d.get("ordersSentAtInstall")!=0 or
        d.get("actualXEquipPerformed") is not False):
        raise Hold("HOLD_R48_INSTALL_PROOF_INVALID")
    return d

def install(r47,r44,r43,r42,r38,old,composer,game,token):
    if token!=INSTALL_TOKEN:
        raise Hold("HOLD_R48_EXACT_TYPED_REAL_EQUIP_INSTALL_REQUIRED")
    before_change(r47,r44,r43,r42,r38,old,composer,game)
    snapshot=safe_snapshot(r47,r44,r43,r42,r38,old,game)
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
        raise Hold("HOLD_R48_STAGED_BAF_OR_NATIVE_SHA")
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    target=old.safe(game,PROOF)
    target.write_text(json.dumps({"schema":SCHEMA,
        "status":"R48_WEIDU_PENDING_MANUAL_REVIEW_IF_INTERRUPTED",
        "originalBcsSHA256":snapshot[SOURCE_BCS],
        "candidateBafSHA256":sha(baf),"baselineSnapshot":snapshot,
        "externalBackup":str(backup)},indent=2),encoding="utf-8")
    # Real game mutation starts here; never auto-retry, never auto-rollback.
    native_weidu(old,game,r42)
    exact_last_r48(r47,r44,r43,r42,r38,old,game)
    bcs=old.safe(game,SOURCE_BCS)
    post=old.sha(bcs)
    if post==snapshot[SOURCE_BCS]:
        raise Hold("HOLD_R48_BCS_NOT_EXTENDED_BY_WEIDU")
    for rel,digest in snapshot.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R48_UNRELATED_FILE_CHANGED:"+rel)
    out={"schema":SCHEMA,"status":"R48_STAF01_REAL_ONE_SHOT_INSTALLED_AWAITING_GAME",
         "installed":True,"gameModified":True,"userApprovedRealItemMove":True,
         "sourceItem":"STAF01","sourceBackpackSlot":20,"targetWeaponSlot":35,
         "onceFlag":ONCE_FLAG,
         "originalBcsSHA256":snapshot[SOURCE_BCS],"installedBcsSHA256":post,
         "candidateBafSHA256":sha(baf),"baselineSnapshot":snapshot,
         "externalBackup":str(backup),"ordersSentAtInstall":0,
         "actualXEquipPerformed":False,"noAutoRetry":False}
    target.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out

def rollback(r47,r44,r43,r42,r38,old,game,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold("HOLD_R48_EXACT_TYPED_ROLLBACK_REQUIRED")
    exact_last_r48(r47,r44,r43,r42,r38,old,game)
    r42.check_processes(r38,old)
    proof=exact_proof(old,game)
    backup=Path(proof.get("externalBackup",""))
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R48_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if (backup.parent!=parent or not backup.name.startswith("PRE_BGXR48_") or
        not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R48_BACKUP_PATH")
    saved=json.loads(old.safe(backup,"SHA256.json").read_text(encoding="utf-8"))
    if saved!=proof.get("baselineSnapshot"):
        raise Hold("HOLD_R48_EXTERNAL_BACKUP_MANIFEST_DRIFT")
    old.verify_snapshot(backup,saved)
    if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R48_LIVE_BCS_CHANGED_AFTER_INSTALL")
    for rel,digest in saved.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R48_UNRELATED_FILE_DRIFT:"+rel)
    r42.check_processes(r38,old)
    native_weidu(old,game,r42,uninstall=True)
    r47.exact_last_r47(r44,r43,r42,r38,old,game)
    r47.exact_proof(old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=saved[SOURCE_BCS]:
        raise Hold("HOLD_R48_ROLLBACK_BCS_NOT_RESTORED")
    for rel,digest in saved.items():
        if rel!="WeiDU.log" and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R48_ROLLBACK_UNRELATED_RESOURCE_DRIFT:"+rel)
    return {"schema":SCHEMA,"status":"R48_ROLLBACK_RESTORED_R47_LAST158",
      "installed":False,"gameModified":True,"ordersSentAtInstall":0,
      "note":"WeiDU rollback restores BCS, NOT any save-game LOCALS/inventory state"}

def status(r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if len(rows)==158:
        safe_snapshot(r47,r44,r43,r42,r38,old,game)
        return {"schema":SCHEMA,"status":"R48_NOT_INSTALLED_R47_LAST158",
          "installed":False,"gameModified":False}
    if len(rows)==159:
        exact_last_r48(r47,r44,r43,r42,r38,old,game)
        proof=exact_proof(old,game)
        if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
            raise Hold("HOLD_R48_INSTALLED_BCS_SHA_DRIFT")
        return {"schema":SCHEMA,"status":"R48_REAL_ONE_SHOT_STAF01_LAST159_PRESENT",
           "installed":True,"gameModified":False,"actualXEquipPerformed":False}
    raise Hold("HOLD_R48_NOT_EXPECTED_WEIDU_COUNT")

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,default=GAME)
    p.add_argument("--mode",choices=("status","install","rollback"),default="status")
    p.add_argument("--onefile-review-gate",action="store_true")
    args=p.parse_args(argv)
    try:
        r47,r44,r43,r42,r38,old,composer=load_checked()
        if args.mode=="status":out=status(r47,r44,r43,r42,r38,old,args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_R48_ONE_ORIGINAL_CMD_TYPED_REVIEW_REQUIRED")
        elif args.mode=="install":
            token=input("Type "+INSTALL_TOKEN+" exactly (ENTER cancels): ").strip()
            out=install(r47,r44,r43,r42,r38,old,composer,args.game,token)
        else:
            token=input("Type "+ROLLBACK_TOKEN+" exactly (ENTER cancels): ").strip()
            out=rollback(r47,r44,r43,r42,r38,old,args.game,token)
        rc=0
    except (OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired,EOFError) as err:
        out={"schema":SCHEMA,"status":"R48_STOP_MANUAL_REVIEW",
             "reason":str(err) if isinstance(err,Hold) else "HOLD_RUNTIME_OR_IO",
             "gameModifiedUnknown":args.mode in ("install","rollback"),
             "noAutoRetry":True,"actualXEquipPerformed":False}
        rc=3
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return rc
if __name__=="__main__":
    sys.exit(main())
