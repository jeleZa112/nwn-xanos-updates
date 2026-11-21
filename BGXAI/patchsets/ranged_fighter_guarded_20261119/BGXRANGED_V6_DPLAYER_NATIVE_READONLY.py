#!/usr/bin/env python3
"""BGXAI V6 DPLAYER: fail-closed native preflight, READ ONLY; never installs.

The installed 0.3.74 game returned to BGXFENEMY after verified last-only
BGXRANGED5 rollback. No user file is overwritten. DPLAYER.BCS is shared,
thus live changes require separate typed approval and independent safety audit.
This report does not identify which EEex script index started each action.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V5

GAME=Path(r"C:\Games\BG_EET_FOXX_NEW")
DPLAYER="override/DPLAYER.BCS"
BDDEFAI="override/BDDEFAI.BCS"
WTASIGHT="override/WTASIGHT.BCS"
WEIDU_LOG="WeiDU.log"
EXPECTED_DPLAYER_SHA="1786f4dc050be5c4bef65d9b0c39100975a03fdf74057b21fe1b1c2b926d661f"
EXPECTED_BDDEFAI_SHA=V5.EXACT_BCS_SHA
EXPECTED_WTASIGHT_SHA=V5.EXACT_WTASIGHT_SHA
LAST_BGXFENEMY=V5.EXPECTED_LAST
SOURCE=Path(__file__).resolve().parent/"BGXRANGED_V6_DPLAYER_CLOSE_GUARD_SOURCE_ONLY.baf"
BASE=(
 (("InWeaponRange(NearestEnemyOf(Myself))","ActionListEmpty()",
   "!InParty(NearestEnemyOf(Myself))",
   "!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)"),
  ("AttackOneRound(NearestEnemyOf(Myself))",),
  "!Range(NearestEnemyOf(Myself),6)"),
 (("AttackedBy([ANYONE],DEFAULT)",
   "!InParty(LastAttackerOf(Myself))",
   "!Allegiance(LastAttackerOf(Myself),GOODCUTOFF)"),
  ("AttackOneRound(LastAttackerOf(Myself))",),
  "!Range(LastAttackerOf(Myself),6)"))
GUARD=("OR(5)","!InParty(Myself)","!Class(Myself,FIGHTER)",
       ' !Global("BGX38_GUARD","LOCALS",1)'.strip(),
       "!IsWeaponRanged(Myself)")

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def ensure(path:Path,root:Path)->None:
    if root!=GAME:raise ValueError("GAME_ROOT_DRIFT")
    V5.no_symlink(path,root)
    if not path.is_file():raise ValueError("REQUIRED_FILE_MISSING:"+str(path))

def check_contract(native_text:str, candidate_text:str)->dict:
    old=V5.parse_blocks(native_text)
    new=V5.parse_blocks(candidate_text)
    if len(old)!=2 or len(new)!=2:
        raise ValueError("DPLAYER_EXACTLY_TWO_BLOCKS_REQUIRED")
    for i,(base,actions,fifth) in enumerate(BASE):
        if old[i]!=(base,actions):
            raise ValueError("ORIGINAL_DPLAYER_BAF_NOT_EXACTLY_EXPECTED:"+str(i+1))
        expect=base+GUARD+(fifth,)
        if new[i]!=(expect,actions):
            raise ValueError("V6_SOURCE_NOT_ONLY_FIVE_SAFE_GUARDS:"+str(i+1))
    return {"candidate_two_actions_preserved":True,
            "candidate_only_adds_close_range_conditional_veto":True}

def valid_saved_handoff(evidence:dict)->bool:
    if evidence.get("status")!="BGXAI_SCRIPT_SLOTS_READONLY_REPORT":
        return False
    saved=evidence.get("saved_party",{})
    if saved.get("status")!="SAVED_GAM_PARTY_READ":return False
    for person in saved.get("party",[]):
        scripts=person.get("scripts",{})
        if (person.get("status")=="SAVED_CRE_SCRIPT_SLOTS_READ" and
            scripts.get("override")=="KHALID" and
            scripts.get("class")=="BDDEFAI" and
            scripts.get("default")=="DPLAYER"):
            entry=next((s for s in evidence.get("scripts",[])
                if s.get("script")=="DPLAYER"),None)
            return bool(entry and entry.get("status")=="DECOMPILED" and
                entry.get("source")=="GAME_OVERRIDE_COPY" and
                entry.get("source_sha256")==EXPECTED_DPLAYER_SHA and
                entry.get("total_blocks")==2)
    return False

def call_weidu(weidu:Path,root:Path,work:Path,input_path:Path,output:Path,stage:str)->None:
    proc=subprocess.run([str(weidu),"--game",str(root),"--out",str(output),
                         str(input_path)],cwd=work,stdin=subprocess.DEVNULL,
                        capture_output=True,text=True,errors="replace",timeout=180)
    log=(proc.stdout or "")+"\n"+(proc.stderr or "")
    if proc.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
        raise ValueError("NATIVE_"+stage+"_STOP:"+log[-300:])
    if not output.is_file() or output.is_symlink():
        raise ValueError("NATIVE_"+stage+"_OUTPUT_MISSING")

def preview(root:Path,evidence:dict)->dict:
    """Saved script assignment only controls eligibility. The live BCS is hashed."""
    if root!=GAME:raise ValueError("GAME_ROOT_DRIFT")
    if not valid_saved_handoff(evidence):
        raise ValueError("SAVED_KHALID_DPLAYER_ASSIGNMENT_NOT_VERIFIED")
    checks={DPLAYER:EXPECTED_DPLAYER_SHA,BDDEFAI:EXPECTED_BDDEFAI_SHA,
            WTASIGHT:EXPECTED_WTASIGHT_SHA}
    files=[root/name for name in checks]+[root/WEIDU_LOG]
    for path in files:ensure(path,root)
    before={str(p):sha(p.read_bytes()) for p in files}
    for name,expected in checks.items():
        if before[str(root/name)]!=expected:
            raise ValueError("BASELINE_SHA_DRIFT:"+name)
    last=next((v.strip() for v in reversed((root/WEIDU_LOG).read_text(
        "utf-8-sig",errors="replace").splitlines()) if v.strip().startswith("~")),None)
    if not last or not LAST_BGXFENEMY.match(last):
        raise ValueError("BGXFENEMY_NOT_LAST_AFTER_V5_ROLLBACK")
    if SOURCE.is_symlink() or not SOURCE.is_file():
        raise ValueError("V6_SOURCE_MISSING")
    fresh=SOURCE.read_bytes()
    if sha(fresh)!="2fd136f4eac23beb24c31744b01ae897aa6a9476e27cfe8392941ef30b600032":
        raise ValueError("V6_CANDIDATE_SOURCE_SHA_DRIFT")
    native=(root/DPLAYER).read_bytes()
    original=V5.bcs_parts(native)
    if len(original)!=2:
        raise ValueError("DPLAYER_NATIVE_BLOCK_COUNT_DRIFT")
    exe=root/"setup-enhanced-powergaming-scripts.exe"
    ensure(exe,root)
    if exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_NOT_EXECUTABLE")
    with tempfile.TemporaryDirectory(prefix="BGXAI_V6_DPLAYER_RO_") as dirname:
        temp=Path(dirname)
        binary=temp/"weidu.exe";shutil.copy2(exe,binary)
        input_file=temp/"DPLAYER.BCS";input_file.write_bytes(native)
        orig_baf=temp/"DPLAYER.BAF"
        call_weidu(binary,root,temp,input_file,orig_baf,"ORIGINAL_DECOMPILE")
        candidate=fresh.decode("utf-8")
        contract=check_contract(orig_baf.read_text("utf-8-sig",errors="replace"),
                                candidate)
        candidate_file=temp/"BGXAIW6.BAF";candidate_file.write_bytes(fresh)
        compiled_file=temp/"BGXAIW6.BCS"
        call_weidu(binary,root,temp,candidate_file,compiled_file,"V6_COMPILE")
        compiled=compiled_file.read_bytes()
        parts=V5.bcs_parts(compiled)
        if len(parts)!=2:raise ValueError("V6_COMPILED_BCS_NOT_TWO_BLOCKS")
        changed=[i+1 for i,(a,b) in enumerate(zip(original,parts)) if a!=b]
        if changed!=[1,2]:
            raise ValueError("V6_COMPILED_NOT_EXACT_TWO_BLOCKS")
        recompiled_baf=temp/"V6_CHECK.BAF"
        compile_copy=temp/"V6_CHECK.BCS";compile_copy.write_bytes(compiled)
        call_weidu(binary,root,temp,compile_copy,recompiled_baf,"V6_REDECOMPILE")
        decoded=V5.parse_blocks(recompiled_baf.read_text("utf-8-sig",errors="replace"))
        if decoded!=V5.parse_blocks(candidate):
            raise ValueError("V6_NATIVE_DECOMPILE_NOT_SEMANTIC_MATCH")
        outcome={"status":"BGXRANGED_V6_DPLAYER_NATIVE_READONLY_PASS",
                 "old_dplayer_sha256":sha(native),
                 "candidate_dplayer_sha256":sha(compiled),
                 "candidate_baf_sha256":sha(fresh),
                 "changed_blocks":[1,2],"total_blocks":2,
                 "same_attack_actions":contract["candidate_two_actions_preserved"],
                 "only_added_guard":contract["candidate_only_adds_close_range_conditional_veto"],
                 "shared_default_script":True,
                 "script_index6_association_verified":False,
                 "runtime_latency_fixed":False,
                 "game_modified":False,"install_performed":False}
    for path in files:
        if sha(path.read_bytes())!=before[str(path)]:
            raise ValueError("GAME_CHANGED_DURING_RO_PREFLIGHT:"+str(path))
    return outcome
