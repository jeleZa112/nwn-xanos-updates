#!/usr/bin/env python3
"""BGXAI 120. Surgical BGEE/EET guard for ONE PRIEST1 Entangle action.

Conservative policy: the generic PRIEST1 script may auto-cast Entangle only
when its user is not a party member. Manually selected Entangle is unchanged.
All four other PRIEST1 blocks, BGXP5 and unrelated resources are preserved.

status and preflight are READ ONLY. WeiDU install/rollback are explicit opt-in.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

import BGXAI_AOE_AUDIT as A
import BGX119_TRACE as T

GAME = A.GAME
PRIEST = "override/PRIEST1.BCS"
PRIEST_SHA = "867ff7fd9efa8a182bf3475bfef6b6f1de851067147ea15bd962431d329f6a9b"
ORIGINAL_BAF_SHA = "44776429fc6ceec92a85477934f6d41310ca27ceaf659ed5f2e6b2528b46f0f4"
OLD_ENTANGLE = "  HaveSpell(CLERIC_ENTANGLE)\n"
NEW_ENTANGLE = OLD_ENTANGLE + "  !InParty(Myself)\n"
TOKEN_INSTALL = "INSTALL_BGX120_PARTY_ENTANGLE_GUARD"
TOKEN_ROLLBACK = "ROLLBACK_BGX120_PARTY_ENTANGLE_GUARD"
EXE_REL = "setup-BGX120.exe"
TP2_REL = "BGX120/setup-BGX120.tp2"
STAGED_REL = "BGX120/staged/PRIEST1.BCS"
PROOF_REL = "BGX120/STAGED_PROOF.json"
TP2_TEXT = ("BACKUP ~BGX120/backup~\n"
    "AUTHOR ~BGXAI guarded party Entangle~\n"
    "BEGIN ~BGXAI BGX120 party-safe automatic Entangle~\n"
    "COPY ~BGX120/staged/PRIEST1.BCS~ ~override/PRIEST1.BCS~\n")
OLD_WEIDU = re.compile(r"^~BGXP5[/\\]SETUP-BGXP5[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
NEW_WEIDU = re.compile(r"^~BGX120[/\\]SETUP-BGX120[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
BACKUP = ("override/PRIEST1.BCS","override/BDDEFAI.BCS",
          "override/M_BX43.lua","WeiDU.log","chitin.key",
          "lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
class Stop(RuntimeError):
    pass

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def check_not_link(path:Path):
    for p in (path,*path.parents):
        if p.is_symlink():
            raise Stop("LINK_BLOCKED:"+str(p))
        try:
            if p.exists() and (p.stat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise Stop("REPARSE_BLOCKED:"+str(p))
        except AttributeError:
            pass
        if p==GAME:
            break

def require(root:Path,relative:str,size:int=1)->Path:
    if relative.startswith("/") or "\\" in relative or ".." in relative.split("/") or ":" in relative:
        raise Stop("UNSAFE_RELATIVE:"+relative)
    p=root/relative
    check_not_link(p)
    if not p.is_file() or p.stat().st_size<size:
        raise Stop("MISSING_SOURCE:"+relative)
    return p

def exact_game(root:Path):
    root=root.resolve(strict=True)
    if root != GAME or not (root/"chitin.key").is_file():
        raise Stop("UNEXPECTED_GAME_ROOT")
    check_not_link(root)
    return root

def wei_last(root:Path)->str:
    lines=require(root,"WeiDU.log").read_text("utf-8-sig",errors="replace").splitlines()
    components=[x.strip() for x in lines if x.strip().startswith("~")]
    if not components:raise Stop("NO_WEIDU_COMPONENTS")
    return components[-1]

def fixed_bgxp5(root:Path):
    bcs=require(root,"override/BDDEFAI.BCS",1000).read_bytes()
    lua=require(root,"override/M_BX43.lua",100).read_bytes()
    if sha(bcs)!=A.BCS_PIN or sha(lua)!=A.LUA_PIN:
        raise Stop("BGXP5_BCS_OR_LUA_DRIFT")
    return {"bcs_sha256":sha(bcs),"lua_sha256":sha(lua)}

def source_guard(root:Path):
    state=fixed_bgxp5(root)
    if not OLD_WEIDU.match(wei_last(root)):
        raise Stop("BGXP5_MUST_BE_LAST")
    bcs=require(root,PRIEST,100).read_bytes()
    if sha(bcs)!=PRIEST_SHA:
        raise Stop("PRIEST1_BCS_CHANGED_PROTECT_OTHER_MODS")
    state["priest1_sha256"]=sha(bcs)
    return state

def modify_baf(text:str)->str:
    if sha(text.encode("utf-8"))!=ORIGINAL_BAF_SHA:
        raise Stop("ORIGINAL_PRIEST1_BAF_UNKNOWN")
    blocks=A.find_blocks(text)
    if len(blocks)!=5:
        raise Stop("ORIGINAL_BAF_BLOCK_COUNT_DRIFT")
    matches=[b for b in blocks if "CLERIC_ENTANGLE" in b]
    if len(matches)!=1 or matches[0].count(OLD_ENTANGLE)!=1 or "    Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)" not in matches[0]:
        raise Stop("ORIGINAL_ENTANGLE_ACTION_UNEXPECTED")
    replaced=matches[0].replace(OLD_ENTANGLE,NEW_ENTANGLE,1)
    after=text.replace(matches[0],replaced,1)
    if after.replace(NEW_ENTANGLE,OLD_ENTANGLE,1)!=text:
        raise Stop("OTHER_BAF_CONTENT_CHANGED")
    if len(A.find_blocks(after))!=5 or after.count("!InParty(Myself)")!=1:
        raise Stop("ENTANGLE_GUARD_NOT_UNIQUE")
    return after

def blocks(b:bytes)->list[bytes]:
    # A real WeiDU BCS uses CR\n both as a BLOCK END and a BLOCK START.
    # Splitting on CR\n alone falsely doubles the number of blocks.
    # Only CR\nCO\n may start a response block (proven against real EET BCS).
    if not b.startswith(b"SC\nCR\nCO\n") or not b.endswith(b"CR\nSC\n"):
        raise Stop("COMPILED_BCS_HEADER_TRAILER_UNEXPECTED")
    starts=[m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)",b)]
    if len(starts)!=5 or starts[0]!=3:
        raise Stop("COMPILED_PRIEST1_NOT_5_BLOCKS:"+str(len(starts)))
    result=[b[a:z] for a,z in zip(starts,starts[1:]+[len(b)])]
    if any(not x.startswith(b"CR\nCO\n") or x.count(b"\nRS\n")!=2 for x in result):
        raise Stop("COMPILED_PRIEST1_BLOCK_INVALID")
    if any(not x.endswith(b"CR\n") for x in result[:-1]):
        raise Stop("COMPILED_PRIEST1_SEPARATOR_INVALID")
    if b"SC\n"+b"".join(result)!=b:
        raise Stop("COMPILED_PRIEST1_LOSSLESS_ROUNDTRIP_FAILED")
    return result

def native_compile(root:Path,compiler:Path,td:Path,name:str,text:str)->bytes:
    path=td/(name+".BAF")
    path.write_text(text,encoding="utf-8",newline="\n")
    dest=td/(name+"_OUT")
    dest.mkdir()
    args=T.exe_args(compiler,root)+["--out",str(dest),str(path)]
    rc,log=T.run(args,td)
    if rc or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise Stop("NATIVE_WEIDU_COMPILE_FAILED:"+log[-900:])
    found=T.find_file(dest,name+".BCS")
    if not found:raise Stop("NATIVE_BCS_NOT_CREATED:"+log[-700:])
    return found.read_bytes()

def candidate(root:Path)->tuple[bytes,dict]:
    original=require(root,PRIEST).read_bytes()
    weidu=require(root,"setup-enhanced-powergaming-scripts.exe",100000).read_bytes()
    if not weidu.startswith(b"MZ"):raise Stop("NOT_NATIVE_WEIDU")
    with tempfile.TemporaryDirectory(prefix="BGX120_NATIVE_EET_") as temporary:
        td=Path(temporary);exe=td/"weidu.exe";exe.write_bytes(weidu)
        if sha(exe.read_bytes())!=sha(weidu):raise Stop("WEIDU_TEMP_COPY_INVALID")
        baf,log=T.decompile(exe,root,td,"PRIEST1",original)
        if not baf:raise Stop("PRIEST1_DECOMPILE_FAILED:"+log[-900:])
        patched=modify_baf(baf)
        old_compiled=native_compile(root,exe,td,"BGX120OLD",baf)
        new_compiled=native_compile(root,exe,td,"BGX120NEW",patched)
        original_blocks=blocks(original)
        old_blocks=blocks(old_compiled)
        new_blocks=blocks(new_compiled)
        # Guard against decompile/recompile silently changing ANY other script
        # block, including rules for Command, Hold Person and attack.
        if old_blocks!=original_blocks:
            raise Stop("PRIEST1_NATIVE_ROUNDTRIP_CHANGED_EXISTING_BLOCKS")
        if any(new_blocks[i]!=original_blocks[i] for i in (0,1,3,4)):
            raise Stop("PRIEST1_UNRELATED_BLOCK_CHANGED")
        changed=[i for i,(a,b) in enumerate(zip(old_blocks,new_blocks)) if a!=b]
        if changed!=[2]:
            raise Stop("BCS_CHANGED_BLOCKS_NOT_ENTANGLE_ONLY:"+str(changed))
        after_baf,after_log=T.decompile(exe,root,td,"BGX120NEW",new_compiled)
        if not after_baf or after_baf.count("!InParty(Myself)")!=1:
            raise Stop("NATIVE_TRIGGER_NOT_VERIFIED:"+after_log[-900:])
        if "Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)" not in after_baf:
            raise Stop("ENTANGLE_ACTION_DAMAGED")
        result={"status":"BGX120_NATIVE_PREFLIGHT_PASS",
                "source_priest1_sha256":sha(original),
                "candidate_priest1_sha256":sha(new_compiled),
                "bcs_blocks":5,"changed_zero_based_block":[2],
                "party_auto_entangle":"disabled",
                "enemy_auto_entangle":"unchanged",
                "other_four_blocks_preserved":True,
                "manual_entangle":"unchanged","BGXP5_untouched":True,
                "game_modified":False}
        return new_compiled,result

def process_guard():
    if os.name!="nt":raise Stop("WINDOWS_ONLY_MUTATION")
    cmd=('$ErrorActionPreference="Stop";'
        '$p=Get-CimInstance Win32_Process | Where-Object {'
        '$_.Name -match "^(Baldur.*|BGEE|BG2EE|BGMain|InfinityLoader|setup-.*|weidu)[.]exe$"};'
        'if($p){$p|Select-Object Name,ProcessId|Out-String;exit 3}')
    p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",cmd],
                     text=True,capture_output=True,stdin=subprocess.DEVNULL,timeout=35)
    if p.returncode or p.stdout.strip():
        raise Stop("GAME_LOADER_OR_WEIDU_RUNNING:"+p.stdout[-500:])

def snapshot(root:Path,label:str)->Path:
    dest=Path(os.environ.get("USERPROFILE",str(Path.home())))/"Documents"/"BGXAI120_SAFE_BACKUPS"
    check_not_link(dest)
    if root==dest or root in dest.parents:raise Stop("BACKUP_INSIDE_GAME")
    dest.mkdir(parents=True,exist_ok=True)
    folder=dest/(label+"_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    folder.mkdir(exist_ok=False)
    files={}
    for rel in BACKUP:
        src=require(root,rel)
        dst=folder/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        if sha(src.read_bytes())!=sha(dst.read_bytes()):
            raise Stop("EXTERNAL_BACKUP_MISMATCH:"+rel)
        files[rel]=sha(dst.read_bytes())
    (folder/"SHA256_PROOF.json").write_text(json.dumps(files,indent=2)+"\n",encoding="utf-8")
    return folder

def weidu(root:Path,uninstall:bool=False)->str:
    exe=require(root,EXE_REL,100000)
    cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),
         "--use-lang","ru_ru","--force-uninstall" if uninstall else "--force-install","0"]
    p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
                     text=True,encoding="utf-8",errors="replace",timeout=200,check=False)
    output=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",output):
        raise Stop("WEIDU_STOP_NO_AUTORETRY:"+output[-1500:])
    return output[-1500:]

def installed(root:Path)->dict:
    if not NEW_WEIDU.match(wei_last(root)):
        raise Stop("BGX120_NOT_LAST_IN_WEIDU")
    state=fixed_bgxp5(root)
    if require(root,TP2_REL).read_text("utf-8")!=TP2_TEXT:
        raise Stop("INSTALL_TP2_CONTENT_CHANGED")
    proof=json.loads(require(root,PROOF_REL).read_text("utf-8"))
    raw=require(root,PRIEST).read_bytes()
    if sha(raw)!=proof.get("candidate_priest1_sha256") or sha(require(root,STAGED_REL).read_bytes())!=sha(raw):
        raise Stop("GUARD_BCS_SHA_MISMATCH")
    if proof.get("source_priest1_sha256")!=PRIEST_SHA or proof.get("bcs_blocks")!=5:
        raise Stop("GUARD_PROOF_DRIFT")
    state.update({"status":"BGX120_INSTALLED_VERIFIED",
                  "priest1_sha256":sha(raw),
                  "BGXP5_untouched":True})
    return state

def status(root:Path)->dict:
    last=wei_last(root)
    if NEW_WEIDU.match(last):
        return installed(root)
    state=source_guard(root)
    return {"status":"BGX120_NOT_INSTALLED","baseline":state,"game_modified":False}

def preflight(root:Path)->dict:
    source_guard(root)
    for p in BACKUP:require(root,p)
    _,proof=candidate(root)
    return proof

def install(root:Path)->dict:
    process_guard()
    ready=preflight(root)
    if (root/"BGX120").exists() or (root/EXE_REL).exists():
        raise Stop("STAGING_COLLISION_NO_OVERWRITE")
    before_log=sha(require(root,"WeiDU.log").read_bytes())
    backup=snapshot(root,"PRE_INSTALL")
    process_guard();source_guard(root)
    if sha(require(root,"WeiDU.log").read_bytes())!=before_log:
        raise Stop("WEIDU_CHANGED_DURING_PREFLIGHT")
    compiled,second=candidate(root)
    if second["candidate_priest1_sha256"]!=ready["candidate_priest1_sha256"]:
        raise Stop("NONDETERMINISTIC_NATIVE_COMPILATION")
    stage=root/"BGX120"
    (stage/"staged").mkdir(parents=True,exist_ok=False)
    (root/STAGED_REL).write_bytes(compiled)
    (root/PROOF_REL).write_text(json.dumps(second,indent=2)+"\n",encoding="utf-8")
    (root/TP2_REL).write_text(TP2_TEXT,encoding="utf-8",newline="\n")
    shutil.copy2(require(root,"setup-enhanced-powergaming-scripts.exe",100000),root/EXE_REL)
    process_guard()
    if sha(require(root,"WeiDU.log").read_bytes())!=before_log:
        raise Stop("WEIDU_CHANGED_BEFORE_INSTALL")
    log=weidu(root)
    (backup/"weidu_install_tail.txt").write_text(log,encoding="utf-8")
    verified=installed(root)
    if sha(require(root,PRIEST).read_bytes())!=ready["candidate_priest1_sha256"]:
        raise Stop("FINAL_TARGET_MISMATCH")
    return {"status":"BGX120_INSTALLED_VERIFIED","backup":str(backup),"after":verified}

def rollback(root:Path)->dict:
    process_guard()
    state=installed(root)
    backup=snapshot(root,"PRE_ROLLBACK")
    process_guard();installed(root)
    log=weidu(root,uninstall=True)
    (backup/"weidu_rollback_tail.txt").write_text(log,encoding="utf-8")
    source=source_guard(root)
    return {"status":"BGX120_ROLLED_BACK_VERIFIED","backup":str(backup),
            "source":source,"game_modified":True}

def main()->int:
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",nargs="?",choices=("status","preflight","install","rollback"))
    ap.add_argument("--game-root",type=Path,default=GAME)
    args=ap.parse_args()
    try:
        root=exact_game(args.game_root)
        mode=args.mode
        if mode is None:
            print("BGX120: 1=status, 2=preflight (READ ONLY), 3=install, 4=rollback, 0=cancel")
            mode={"1":"status","2":"preflight","3":"install","4":"rollback"}.get(input("BGX120 choice [0]: ").strip())
        if mode is None:
            print("BGX120_CANCELLED");return 0
        if mode=="status":result=status(root)
        elif mode=="preflight":result=preflight(root)
        else:
            token=TOKEN_INSTALL if mode=="install" else TOKEN_ROLLBACK
            print("Close Baldur, InfinityLoader and WeiDU. This modifies ONLY PRIEST1.BCS via WeiDU.")
            if input("Type "+token+" exactly to authorize (ENTER cancels): ").strip()!=token:
                print("BGX120_CANCELLED_NO_GAME_CHANGE");return 0
            result=install(root) if mode=="install" else rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (Stop,ValueError,OSError,KeyError,UnicodeError,subprocess.TimeoutExpired) as exc:
        print("BGX120_STOP:",str(exc))
        print("NO AUTOMATIC RETRY. If install had begun, preserve files for review.")
        return 2

if __name__=="__main__":
    sys.exit(main())
