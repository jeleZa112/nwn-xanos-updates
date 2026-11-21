#!/usr/bin/env python3
"""Native EET WeiDU V5 6/10 candidate, READ-ONLY: no game writes and NO install.

Requires the user's exact BDDEFAI and BGXFENEMY WTASIGHT SHA, current last
WeiDU, and a decompiled three-block head semantically identical to pinned V4.
Compiles V5 in TEMP, proves only native blocks 1 and 3 differ and all 1159
other existing BCS blocks remain byte-for-byte unchanged. Never overwrites BCS.
A PASS is a native SOURCE candidate, NOT a real-combat latency fix.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import tempfile

GAME = pathlib.Path(r"C:\Games\BG_EET_FOXX_NEW")
BCS = "override/BDDEFAI.BCS"
EXACT_BCS_SHA = "9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e"
EXPECTED_BLOCKS = 1162
WTASIGHT = "override/WTASIGHT.BCS"
EXACT_WTASIGHT_SHA = "ec50ad2e91a33aad4e4b6b1bc33ac87f0f02f4af49f9649b5cad6c36faeaa403"
EXPECTED_LAST = re.compile(
    r"^~(?:[^~]*[/\\])?BGXFENEMY[/\\]SETUP-BGXFENEMY[.]TP2~\s+#0\s+#0(?:\s|$)", re.I)
ROOT = pathlib.Path(__file__).resolve().parent
V4 = ROOT / "BGXRANGED_V4_NO_FRIEND_ATTACK.baf"
V5 = ROOT / "BGXRANGED_V5_ANTICIPATORY_CLOSE_SOURCE_ONLY.baf"
SOURCE_SHA_V4 = "67a5e1c01fb6f97b7976dac6bfc3b40aa7e5233cceb2fdd5f113ebae8a68788b"
# sha for V5 is supplied by manifest and checked during one-file source sync.

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def no_symlink(path: pathlib.Path, root: pathlib.Path) -> None:
    if root.is_symlink():
        raise ValueError("GAME_ROOT_SYMLINK")
    current=path
    while current != root:
        if current.is_symlink():
            raise ValueError("SYMLINK_BLOCKED:" + str(current))
        if current == current.parent:
            raise ValueError("OUTSIDE_GAME_ROOT")
        current=current.parent

def bcs_parts(binary: bytes) -> list[bytes]:
    if not binary.startswith(b"SC\nCR\nCO\n") or not binary.endswith(b"CR\nSC\n"):
        raise ValueError("BAD_BCS_ENVELOPE")
    start=[m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)",binary)]
    if not start or start[0]!=3:
        raise ValueError("BAD_BCS_HEAD")
    parts=[binary[a:z] for a,z in zip(start,start[1:]+[len(binary)])]
    if b"SC\n"+b"".join(parts)!=binary:
        raise ValueError("BCS_SPLIT_NOT_LOSSLESS")
    return parts

def parse_blocks(text: str) -> list[tuple[tuple[str,...],tuple[str,...]]]:
    blocks=[]
    cond=[];acts=[];stage=None;response_count=0
    for line in text.splitlines():
        t=line.strip()
        if not t or t.startswith("//"):
            continue
        if t=="IF":
            if stage is not None:raise ValueError("BAF_NESTED_IF")
            cond=[];acts=[];stage="conditions";response_count=0
        elif t=="THEN":
            if stage!="conditions":raise ValueError("BAF_THEN_ORDER")
            stage="actions"
        elif t=="END":
            if stage!="actions" or not cond or not acts or response_count!=1:
                raise ValueError("BAF_BLOCK_SHAPE")
            blocks.append((tuple(cond),tuple(acts)));stage=None
        elif stage=="actions" and re.fullmatch(r"RESPONSE\s*#100",t,re.I):
            response_count+=1
        elif stage=="conditions":
            cond.append(t)
        elif stage=="actions":
            acts.append(t)
        else:
            raise ValueError("BAF_UNEXPECTED_LINE:"+t[:70])
    if stage is not None:raise ValueError("BAF_TRUNCATED")
    return blocks

def source_contract(decompiled_text: str, source_v4: str, source_v5: str) -> dict:
    actual=parse_blocks(decompiled_text)
    before=parse_blocks(source_v4)
    after=parse_blocks(source_v5)
    if len(actual)!=EXPECTED_BLOCKS or len(before)!=3 or len(after)!=3:
        raise ValueError("BCS_BAF_BLOCK_COUNT_OR_SOURCE_DRIFT")
    if actual[:3]!=before:
        raise ValueError("LIVE_FIRST_THREE_NOT_EXACT_V4_SEMANTICS")
    expected=[(tuple(c),tuple(a)) for c,a in before]
    c=list(expected[0][0])
    if c.count("Range(NearestEnemyOf(Myself),4)")!=1:raise ValueError("OLD_CLOSE_RANGE_GATE_DRIFT")
    c[c.index("Range(NearestEnemyOf(Myself),4)")] = "Range(NearestEnemyOf(Myself),6)"
    expected[0]=(tuple(c),expected[0][1])
    c=list(expected[2][0])
    if c.count("!Range(NearestEnemyOf(Myself),4)")!=1:raise ValueError("OLD_ATTACK_RANGE_GATE_DRIFT")
    c[c.index("!Range(NearestEnemyOf(Myself),4)")] = "!Range(NearestEnemyOf(Myself),6)"
    expected[2]=(tuple(c),expected[2][1])
    if after!=expected:
        raise ValueError("V5_CHANGES_MORE_THAN_TWO_CONDITIONS")
    return {
      "status":"V5_SOURCE_PRECONDITIONS_MATCH_INSTALLED_V4",
      "observed_live_bcs_decompiled_blocks":len(actual),
      "observed_live_first_three_semantic_match":True,
      "candidate_only_two_range_changes":True,
      "no_action_queue_interruption_added":True
    }

def splice_native(live: bytes, compiled: bytes) -> tuple[bytes,dict]:
    old=bcs_parts(live);new=bcs_parts(compiled)
    if len(old)!=EXPECTED_BLOCKS or len(new)!=3:
        raise ValueError("NATIVE_BCS_COUNT_DRIFT")
    if new[1]!=old[1]:
        raise ValueError("MIDDLE_RANGED_RETURN_NATIVE_BLOCK_DRIFT")
    if new[0]==old[0] or new[2][:-3]==old[2]:
        raise ValueError("NEW_RANGE_CONDITIONS_NOT_COMPILED")
    if not new[2].endswith(b"CR\nSC\n"):
        raise ValueError("COMPILED_3_BLOCK_ENVELOPE")
    result=b"SC\n"+b"".join(new)[:-3]+b"".join(old[3:])
    joined=bcs_parts(result)
    if len(joined)!=EXPECTED_BLOCKS or joined[3:]!=old[3:] or joined[1]!=old[1]:
        raise ValueError("NATIVE_UNRELATED_BLOCKS_CHANGED")
    changed=[i+1 for i,(a,b) in enumerate(zip(old,joined)) if a!=b]
    if changed!=[1,3]:
        raise ValueError("NATIVE_CHANGED_BLOCK_SET_NOT_1_AND_3")
    return result,{"changed_blocks":changed,"preserved_blocks":EXPECTED_BLOCKS-len(changed),
                   "candidate_bcs_sha256":sha(result)}

def attack_sources(decompiled_text: str) -> list[dict]:
    blocks=parse_blocks(decompiled_text)
    found=[]
    for idx,(conditions,actions) in enumerate(blocks,1):
        if not any(re.match(r"^(?:Attack|AttackReevaluate|AttackOneRound|ForceAttack)\s*\(",a)
                   for a in actions):
            continue
        if idx>3 and not any("IsWeaponRanged" in c or "CanEquipRanged" in c or
                             "Class(Myself,FIGHTER" in c for c in conditions):
            continue
        found.append({
            "block":idx,
            "actions":list(actions[:4]),
            "ranged_attack_condition":any("IsWeaponRanged(" in c for c in conditions),
            "requires_action_list_empty":any(c=="ActionListEmpty()" for c in conditions),
            "range_conditions":[c for c in conditions if "Range(" in c][:5],
            "guard_conditions":[c for c in conditions if
                  "InParty(" in c or "Allegiance(" in c or "BGX66_S_HEAL" in c][:6]})
    return found[:30]

def preview(root: pathlib.Path, live_bcs: bytes, baf_text: str,
            weidu: pathlib.Path, last_weidu: str) -> dict:
    """Called by existing menu 135 after a successful native BCS decompile.

    All generated BAF/BCS are placed under TemporaryDirectory; game-root files
    must have the same hashes before and after. Never calls install actions.
    """
    if root!=GAME:raise ValueError("GAME_ROOT_NOT_ALLOWED")
    if not EXPECTED_LAST.match(last_weidu):raise ValueError("BGXFENEMY_NOT_LAST_WEIDU")
    if sha(live_bcs)!=EXACT_BCS_SHA:raise ValueError("LIVE_BDDEFAI_SHA_DRIFT")
    game_bcs=root/BCS;wtasight=root/WTASIGHT
    weidu_log=root/"WeiDU.log"
    for path in (game_bcs,wtasight,weidu_log):
        no_symlink(path,root)
        if not path.is_file():raise ValueError("GAME_FILE_MISSING")
    expected_sha={str(p):sha(p.read_bytes()) for p in (game_bcs,wtasight,weidu_log)}
    if expected_sha[str(game_bcs)]!=EXACT_BCS_SHA:
        raise ValueError("BDDEFAI_CHANGED_SINCE_READ")
    if expected_sha[str(wtasight)]!=EXACT_WTASIGHT_SHA:
        raise ValueError("WTASIGHT_BGXFENEMY_BASELINE_DRIFT")
    for source in (V4,V5):
        if source.is_symlink() or not source.is_file():raise ValueError("SOURCE_MISSING_OR_SYMLINK")
    old=V4.read_bytes();new=V5.read_bytes()
    if sha(old)!=SOURCE_SHA_V4:raise ValueError("V4_REFERENCE_HASH_DRIFT")
    proof=source_contract(baf_text,old.decode("utf-8"),new.decode("utf-8"))
    if weidu.is_symlink() or not weidu.is_file() or weidu.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_MISSING")
    with tempfile.TemporaryDirectory(prefix="BGXAI_V5_NATIVE_RO_") as directory:
        temp=pathlib.Path(directory);input_file=temp/"BGXAIW5.BAF"
        input_file.write_bytes(new)
        out=temp/"out";out.mkdir()
        command=[str(weidu),"--game",str(root),"--out",str(out),str(input_file)]
        process=subprocess.run(command,cwd=temp,stdin=subprocess.DEVNULL,
           capture_output=True,text=True,errors="replace",timeout=180)
        msg=(process.stdout or "")+"\n"+(process.stderr or "")
        if process.returncode!=0 or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",msg):
            raise ValueError("WEIDU_NATIVE_COMPILE_STOP:"+msg[-450:])
        results=list(out.rglob("BGXAIW5.BCS"))
        if len(results)!=1:raise ValueError("WEIDU_COMPILED_RESULT_NOT_EXACTLY_ONE")
        native=results[0].read_bytes()
        candidate,built=splice_native(live_bcs,native)
        if sha(candidate)==EXACT_BCS_SHA:raise ValueError("EMPTY_CANDIDATE")
    for path,expected in expected_sha.items():
        p=pathlib.Path(path)
        if sha(p.read_bytes())!=expected:
            raise ValueError("GAME_CHANGED_DURING_READONLY_PREVIEW:"+str(p))
    return {
       **proof,**built,
       "status":"BGXRANGED_V5_NATIVE_READONLY_CANDIDATE_PASS",
       "candidate_baf_sha256":sha(new),
       "remaining_other_attack_sources":attack_sources(baf_text),
       "attack_action_origin_verified":False,
       "predicted_latency_improvement_verified":False,
       "live_tested":False,"game_modified":False,"install_performed":False}
