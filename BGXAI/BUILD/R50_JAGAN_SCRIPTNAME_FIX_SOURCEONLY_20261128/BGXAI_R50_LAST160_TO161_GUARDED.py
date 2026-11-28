#!/usr/bin/env python3
"""BGXAI R50 original single-CMD native last-only #160 -> #161 correction.

R49 found STAF01 in all backpack slots but its BAF still contained the
false Name("*GCLERIC",Myself) test. Actual user's GAM NPC character resref
*GCLERIC is NOT embedded CRE script name (0x280 = None). This native R50
reuses frozen R49 + original R48/R47/... chain, and compiles only the
one-trigger R50 source fix: Race(Myself,DWARF) under the existing party
slot 1 + class CLERIC and all EPS/idle/item/one-shot restrictions.

A single new EXTEND_TOP block must run before frozen R49 and old R48;
ALL share the BGX48TRY once-flag. No action is performed at install
time. User's game/InfinityLoader must be closed for installation.
Only use with user EXACT typed consent in SAME original CMD V2 hub.
"""
from __future__ import annotations

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
R49_PATH=REPO/"BGXAI/BUILD/R49_R48_BACKPACK16_SOURCE_ONLY_20261128/BGXAI_R49_LAST159_TO160_GUARDED.py"
COMPOSE_PATH=HERE/"BGXAI_R50_REUSE_R49_IDENTITY_DWARF_SOURCE_ONLY.py"
R49_GIT_BLOB="3c147e1f5c1b7de811f7bbf590e22d2b702cbffa"
COMPOSE_GIT_BLOB="68dc30b0f21459b56714b121a3d76e2b39302599"
SCHEMA="BGXAI_R50_JAGAN_DWARF_CLERIC_LAST161_GUARDED_V1"
GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
DIR="BGXR50"
BAF=DIR+"/staged/BGX_R50_ONCE.baf"
TP2=DIR+"/setup-BGXR50.tp2"
EXE=DIR+"/setup-BGXR50.exe"
PROOF=DIR+"/PROOF.json"
SOURCE_BCS="override/BDDEFAI.BCS"
ONCE_FLAG="BGX48TRY"
INSTALL_TOKEN="INSTALL_BGXAI_R50_DWARF_CLERIC_IDENTITY_AFTER_R49_LAST160"
ROLLBACK_TOKEN="ROLLBACK_BGXAI_R50_RESTORE_R49_LAST160_ONLY"
LAST=re.compile(
  r'^~(?:[^~]*[/\\])?BGXR50[/\\]SETUP-BGXR50[.]TP2~\s+#0\s+#0(?:\s|$)',
  re.I)
TP2_TEXT=(
 "BACKUP ~BGXR50/backup~\n"
 "AUTHOR ~BGXAI R50 exact Jagan scriptname mismatch correction~\n"
 "BEGIN ~BGXR50 one STAF01 from backpack for party1 dwarf cleric idle~\n"
 "EXTEND_TOP ~BDDEFAI.BCS~ ~BGXR50/staged/BGX_R50_ONCE.baf~\n"
)
class Hold(ValueError):
    pass

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def frozen(path:Path,blob:str,name:str):
    if (path.is_symlink() or not path.is_file() or
        gitblob(path.read_bytes())!=blob):
        raise Hold("HOLD_R50_PINNED_OLD_"+name+"_SOURCE_CHANGED")
    spec=importlib.util.spec_from_file_location("bgxai_r50_old_"+name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R50_"+name+"_MODULE_IMPORT")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def load_checked():
    r49=frozen(R49_PATH,R49_GIT_BLOB,"R49")
    composer=frozen(COMPOSE_PATH,COMPOSE_GIT_BLOB,"COMPOSER")
    r48,r47,r44,r43,r42,r38,old,_=r49.load_checked()
    baf=composer.compose()
    if (composer.SCHEMA!="BGXAI_R50_REUSE_R49_JAGAN_CRE_IDENTITY_ONE_TRIGGER_SOURCE_ONLY_V1"
        or not 0<len(baf)<=2500
        or baf.count(b"Race(Myself,DWARF)")!=1
        or b'Name("*GCLERIC",Myself)' in baf
        or baf.count(b"InPartySlot(Myself,1)")!=1
        or baf.count(b"Class(Myself,CLERIC)")!=1
        or baf.count(b"OR(16)\n")!=1
        or baf.count(b"CheckItemSlot(")!=16
        or baf.count(b"ActionListEmpty()")!=1
        or baf.count(b"CombatCounter(0)")!=1
        or baf.count(b'Global("BGX48TRY","LOCALS",0)')!=1
        or baf.count(b'SetGlobal("BGX48TRY","LOCALS",1)')!=1
        or baf.count(b'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')!=1
        or TP2_TEXT.count("EXTEND_TOP ~BDDEFAI.BCS~")!=1):
        raise Hold("HOLD_R50_SINGLE_ACTION_IDENTITY_OR_SAFETY_CHANGED")
    return r49,r48,r47,r44,r43,r42,r38,old,composer

def exact_old_160(r49,r48,r47,r44,r43,r42,r38,old,game):
    result=r49.status(r48,r47,r44,r43,r42,r38,old,game)
    if (type(result) is not dict or
        result.get("status")!="R49_BACKPACK16_LAST160_INSTALLED_AWAITING_GAME"
        or result.get("installed") is not True or
        result.get("gameModified") is not False):
        raise Hold("HOLD_R50_OLD_R49_LAST160_NOT_AUTHENTIC")
    return r49.exact_proof(old,game)

def old_snapshot(r49,r48,r47,r44,r43,r42,r38,old,game):
    proof=exact_old_160(r49,r48,r47,r44,r43,r42,r38,old,game)
    baseline=proof.get("baselineSnapshot")
    if (type(baseline) is not dict or not baseline or
        "WeiDU.log" not in baseline or SOURCE_BCS not in baseline or
        r48.PROOF not in baseline):
        raise Hold("HOLD_R50_OLD_R49_BASELINE_INVALID")
    for rel,digest in baseline.items():
        if rel not in ("WeiDU.log",SOURCE_BCS):
            if old.sha(old.safe(game,rel))!=digest:
                raise Hold("HOLD_R50_UNRELATED_OLD_ANCESTOR_DRIFT")
    snapshot=dict(baseline)
    for rel in ("WeiDU.log",SOURCE_BCS,
                r49.PROOF,r49.BAF,r49.TP2,r49.EXE):
        src=old.safe(game,rel)
        if src.is_symlink() or not src.is_file():
            raise Hold("HOLD_R50_OLD_R49_PROOF_OR_SOURCE_ABSENT")
        snapshot[rel]=old.sha(src)
    if snapshot[SOURCE_BCS]!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R50_R49_LIVE_BCS_WRONG_PREIMAGE")
    if snapshot[r48.PROOF]!=proof.get("originalR48ProofSHA256"):
        raise Hold("HOLD_R50_ORIGINAL_R48_PROOF_DRIFT")
    old.verify_snapshot(game,snapshot)
    return snapshot

def preflight(r49,r48,r47,r44,r43,r42,r38,old,composer,game,
              *,require_stopped=True):
    old.protected_root(game,True)
    if require_stopped:
        r42.check_processes(r38,old)
    snap=old_snapshot(r49,r48,r47,r44,r43,r42,r38,old,game)
    for rel in (DIR,BAF,TP2,EXE,PROOF):
        if old.safe(game,rel).exists():
            raise Hold("HOLD_R50_NAMESPACE_ALREADY_PRESENT")
    compiler=old.safe(game,"setup-enhanced-powergaming-scripts.exe")
    if (compiler.is_symlink() or not compiler.is_file() or
        old.sha(compiler)!=r42.WEIDU_SHA):
        raise Hold("HOLD_R50_NATIVE_WEIDU_BINARY_CHANGED")
    baf=composer.compose()
    if not 0<len(baf)<=2500:
        raise Hold("HOLD_R50_BAF_TOO_LARGE")
    return {
      "schema":SCHEMA,
      "status":"R50_R49_LAST160_SOURCE_PREFLIGHT_PASS_NO_INSTALL",
      "installed":False,"gameModified":False,"ordersSent":0,
      "r49Last160Verified":True,
      "falseNameGuardRemoved":True,
      "party1DwarfClericGuardPreserved":True,
      "oldOneShotBGX48TRYPreserved":True,
      "originalR49BcsSHA256":snap[SOURCE_BCS],
      "candidateBAFSHA256":sha(baf),
      "nativeCompiledOnUserGame":False,
      "noAutoRetry":True
    }

def backup_before_change(old,game,snapshot):
    home=os.environ.get("USERPROFILE")
    if not home:raise Hold("HOLD_R50_USERPROFILE_ABSENT")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    if (parent.is_symlink() or
        (hasattr(parent,"is_junction") and parent.is_junction())):
        raise Hold("HOLD_R50_BACKUP_DIR_REPARSE")
    parent.mkdir(parents=True,exist_ok=True)
    backup=Path(tempfile.mkdtemp(prefix="PRE_BGXR50_",dir=parent))
    for rel,digest in snapshot.items():
        src=old.safe(game,rel)
        target=old.safe(backup,rel)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
        if old.sha(target)!=digest:
            raise Hold("HOLD_R50_HASH_BACKUP_FAILED")
    old.safe(backup,"SHA256.json").write_text(
      json.dumps(snapshot,indent=2),encoding="utf-8")
    return backup

def native_weidu(old,game,r42,*,uninstall=False):
    exe=old.safe(game,EXE)
    if (exe.is_symlink() or not exe.is_file() or
        old.sha(exe)!=r42.WEIDU_SHA):
        raise Hold("HOLD_R50_NATIVE_WEIDU_ORIGIN_DRIFT")
    args=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(game),
          "--use-lang","ru_ru",
          "--force-uninstall" if uninstall else "--force-install","0"]
    r=subprocess.run(args,cwd=game,stdin=subprocess.DEVNULL,
         capture_output=True,text=True,errors="replace",timeout=240,
         check=False)
    output=(r.stdout or "")+"\n"+(r.stderr or "")
    if r.returncode!=0 or re.search(r"(?mi)^\s*(ERROR:|FATAL ERROR:)",output):
        raise Hold("HOLD_R50_NATIVE_WEIDU_MANUAL_REVIEW")

def exact_last_161(r49,r48,r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if (len(rows)!=161 or not old.last_r37_history(rows[:153]) or
        r38.LAST.match(rows[153]) is None or
        r42.LAST.match(rows[154]) is None or
        r43.LAST.match(rows[155]) is None or
        r44.LAST.match(rows[156]) is None or
        r47.LAST.match(rows[157]) is None or
        r48.LAST.match(rows[158]) is None or
        r49.LAST.match(rows[159]) is None or
        LAST.match(rows[160]) is None):
        raise Hold("HOLD_R50_NOT_LAST161_AFTER_EXACT_R49")
    if (old.sha(old.safe(game,r47.SOURCE_LUA))!=r47.EXPECTED_LUA_SHA
        or old.sha(old.safe(game,r44.OVERRIDE))!=r44.EXPECTED_SHA):
        raise Hold("HOLD_R50_OLDER_LUA_DRIFT")
    return rows

def exact_proof(old,game):
    p=old.safe(game,PROOF)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>1_000_000:
        raise Hold("HOLD_R50_PROOF_FILE_INVALID")
    d=json.loads(p.read_text("utf-8"))
    if (type(d) is not dict or d.get("schema")!=SCHEMA or
        d.get("status")!="R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME" or
        d.get("installed") is not True or
        d.get("userApproved") is not True or
        d.get("onceFlag")!=ONCE_FLAG or
        d.get("r49Last160Preserved") is not True or
        d.get("ordersSentAtInstall")!=0 or
        d.get("actualXEquipPerformed") is not False):
        raise Hold("HOLD_R50_INSTALL_PROOF_INVALID")
    return d

def status(r49,r48,r47,r44,r43,r42,r38,old,game):
    old.protected_root(game,True)
    rows,_=old.history(game)
    if len(rows)==160:
        exact_old_160(r49,r48,r47,r44,r43,r42,r38,old,game)
        return {"schema":SCHEMA,"status":"R50_NOT_INSTALLED_R49_LAST160",
            "installed":False,"gameModified":False,"ordersSent":0}
    if len(rows)!=161:
        raise Hold("HOLD_R50_UNEXPECTED_WEIDU_COMPONENT_COUNT")
    exact_last_161(r49,r48,r47,r44,r43,r42,r38,old,game)
    proof=exact_proof(old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R50_INSTALLED_BCS_CHANGED")
    if old.sha(old.safe(game,r49.PROOF))!=proof.get("r49OriginalProofSHA256"):
        raise Hold("HOLD_R50_R49_ORIGINAL_PROOF_CHANGED")
    return {"schema":SCHEMA,"status":"R50_LAST161_INSTALLED_AWAITING_GAME",
        "installed":True,"gameModified":False,"ordersSent":0,
        "actualXEquipPerformed":False}

def install(r49,r48,r47,r44,r43,r42,r38,old,composer,game,token):
    if token!=INSTALL_TOKEN:
        raise Hold("HOLD_R50_EXACT_TYPED_INSTALL_TOKEN_REQUIRED")
    preflight(r49,r48,r47,r44,r43,r42,r38,old,composer,game)
    snapshot=old_snapshot(r49,r48,r47,r44,r43,r42,r38,old,game)
    backup=backup_before_change(old,game,snapshot)
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
        raise Hold("HOLD_R50_STAGED_FILES_DRIFT")
    r42.check_processes(r38,old)
    old.verify_snapshot(game,snapshot)
    target=old.safe(game,PROOF)
    target.write_text(json.dumps({
       "schema":SCHEMA,
       "status":"R50_NATIVE_WEIDU_PENDING_DO_NOT_RETRY",
       "originalBcsSHA256":snapshot[SOURCE_BCS],
       "candidateBAFSHA256":sha(baf),
       "baselineSnapshot":snapshot,
       "externalBackup":str(backup),
       "r49OriginalProofSHA256":snapshot[r49.PROOF],
    },indent=2),encoding="utf-8")
    # Native game mutation begins here; no unattended retries/rollback.
    native_weidu(old,game,r42)
    exact_last_161(r49,r48,r47,r44,r43,r42,r38,old,game)
    post=old.sha(old.safe(game,SOURCE_BCS))
    if post==snapshot[SOURCE_BCS]:
        raise Hold("HOLD_R50_BCS_NOT_EXTENDED")
    for rel,digest in snapshot.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and (
             old.sha(old.safe(game,rel))!=digest):
            raise Hold("HOLD_R50_UNRELATED_PROTECTED_FILE_CHANGED")
    out={
       "schema":SCHEMA,
       "status":"R50_DWARF_CLERIC_STAF01_INSTALLED_AWAITING_GAME",
       "installed":True,"userApproved":True,"gameModified":True,
       "sourceItem":"STAF01","sourceBackpackSlots":list(range(18,34)),
       "targetWeaponSlot":35,"onceFlag":ONCE_FLAG,
       "r49Last160Preserved":True,
       "r49OriginalProofSHA256":snapshot[r49.PROOF],
       "originalBcsSHA256":snapshot[SOURCE_BCS],
       "installedBcsSHA256":post,
       "candidateBAFSHA256":sha(baf),
       "externalBackup":str(backup),"baselineSnapshot":snapshot,
       "ordersSentAtInstall":0,"actualXEquipPerformed":False,
       "noAutoRetry":True
    }
    target.write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out

def rollback(r49,r48,r47,r44,r43,r42,r38,old,game,token):
    if token!=ROLLBACK_TOKEN:
        raise Hold("HOLD_R50_EXACT_TYPED_ROLLBACK_TOKEN_REQUIRED")
    exact_last_161(r49,r48,r47,r44,r43,r42,r38,old,game)
    r42.check_processes(r38,old)
    proof=exact_proof(old,game)
    home=os.environ.get("USERPROFILE")
    if not home:
        raise Hold("HOLD_R50_USERPROFILE_MISSING")
    parent=Path(home)/"Documents"/"BGXAI_BACKUPS"
    backup=Path(proof.get("externalBackup",""))
    if (backup.parent!=parent or not backup.name.startswith("PRE_BGXR50_")
        or not backup.is_dir() or backup.is_symlink() or
        (hasattr(backup,"is_junction") and backup.is_junction())):
        raise Hold("HOLD_R50_EXTERNAL_BACKUP_LOCATION")
    saved=json.loads(old.safe(backup,"SHA256.json").read_text("utf-8"))
    if saved!=proof.get("baselineSnapshot"):
        raise Hold("HOLD_R50_BACKUP_MANIFEST_DRIFT")
    old.verify_snapshot(backup,saved)
    if old.sha(old.safe(game,SOURCE_BCS))!=proof.get("installedBcsSHA256"):
        raise Hold("HOLD_R50_INSTALLED_BCS_SHA_DRIFT")
    for rel,digest in saved.items():
        if rel not in ("WeiDU.log",SOURCE_BCS) and
            old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R50_UNRELATED_FILE_DRIFT")
    if old.sha(old.safe(game,r49.PROOF))!=proof.get("r49OriginalProofSHA256"):
        raise Hold("HOLD_R50_ORIGINAL_R49_PROOF_CHANGED")
    r42.check_processes(r38,old)
    native_weidu(old,game,r42,uninstall=True)
    exact_old_160(r49,r48,r47,r44,r43,r42,r38,old,game)
    if old.sha(old.safe(game,SOURCE_BCS))!=saved[SOURCE_BCS]:
        raise Hold("HOLD_R50_R49_BCS_NOT_RESTORED")
    for rel,digest in saved.items():
        if rel!="WeiDU.log" and old.sha(old.safe(game,rel))!=digest:
            raise Hold("HOLD_R50_ROLLBACK_UNRELATED_DRIFT")
    return {
       "schema":SCHEMA,
       "status":"R50_ROLLBACK_RESTORED_ORIGINAL_R49_LAST160",
       "installed":False,"gameModified":True,
       "ordersSentAtInstall":0,
       "note":"Restores original R49 BCS, not saved actor BGX48TRY or inventory"
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game",type=Path,default=GAME)
    p.add_argument("--mode",choices=("status","preflight","install","rollback"),
                   default="status")
    p.add_argument("--onefile-review-gate",action="store_true")
    args=p.parse_args(argv)
    try:
        r49,r48,r47,r44,r43,r42,r38,old,composer=load_checked()
        if args.mode=="status":
            data=status(r49,r48,r47,r44,r43,r42,r38,old,args.game)
        elif args.mode=="preflight":
            data=preflight(r49,r48,r47,r44,r43,r42,r38,old,composer,args.game)
        elif not args.onefile_review_gate:
            raise Hold("HOLD_R50_ONE_ORIGINAL_CMD_APPROVAL_REQUIRED")
        elif args.mode=="install":
            token=input("Type "+INSTALL_TOKEN+" exactly (Enter cancels): ").strip()
            data=install(r49,r48,r47,r44,r43,r42,r38,old,composer,args.game,token)
        else:
            token=input("Type "+ROLLBACK_TOKEN+" exactly (Enter cancels): ").strip()
            data=rollback(r49,r48,r47,r44,r43,r42,r38,old,args.game,token)
        rc=0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            subprocess.TimeoutExpired,EOFError) as err:
        data={
          "schema":SCHEMA,
          "status":"R50_STOP_MANUAL_REVIEW",
          "reason":str(err) if isinstance(err,Hold) else "HOLD_R50_RUNTIME_OR_IO",
          "gameModifiedUnknown":args.mode in ("install","rollback"),
          "noAutoRetry":True,"actualXEquipPerformed":False
        }
        rc=3
    print(json.dumps(data,indent=2,ensure_ascii=True))
    return rc

if __name__=="__main__":
    sys.exit(main())
