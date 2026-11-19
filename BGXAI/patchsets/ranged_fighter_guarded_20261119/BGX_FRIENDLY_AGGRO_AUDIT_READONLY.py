#!/usr/bin/env python3
"""BGXAI: READ-ONLY evidence audit of live BDDEFAI / friendly-fire aggro.
Runs WeiDU against an immutable TEMP copy, never uses WeiDU install.
Reports suspicious attacker-target selection without claiming causality.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, datetime

GAME=pathlib.Path(r"C:\Games\BG_EET_FOXX_NEW")
BCS="override/BDDEFAI.BCS"
SUSPECT=re.compile(r"\b(?:Attack|AttackReevaluate|AttackOneRound|AttackNoSound|AttackReevaluate|ForceAttack|ProtectObject|RunAwayFrom|MoveToObject|MoveToPoint|ChangeEnemyAlly)\s*\(",re.I)
ATTACK=re.compile(r"\b(?:Attack|AttackReevaluate|AttackOneRound|AttackNoSound|ForceAttack)\s*\((.*)",re.I)
LAST=re.compile(r"\b(?:LastAttackerOf|LastHitter|LastTargetedBy|AttackedBy|HitBy|Help|Hurt|NearestEnemyOf|LastSeenBy|Enemy)\s*\(",re.I)
GUARD=re.compile(r"(?i)!\s*InParty\s*\(|!\s*Allegiance\s*\(")
PLAYER=re.compile(r"\b(?:Player[1-6]|LastAttackerOf|LastHitter|NearestEnemyOf|LastSeenBy)\s*\(",re.I)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(path,root):
    for item in (path,*path.parents):
        if item.is_symlink():raise ValueError("SYMLINK_BLOCKED:"+str(item))
        if item==root:break
def live(root):
    if root!=GAME or not (root/"chitin.key").is_file():raise ValueError("UNKNOWN_GAME_ROOT")
    p=root/BCS;safe(p,root)
    if not p.is_file() or p.stat().st_size>30_000_000:raise ValueError("BAD_BCS")
    return p
def parts(b):
    if not b.startswith(b"SC\nCR\nCO\n") or not b.endswith(b"CR\nSC\n"):
        raise ValueError("BCS_ENVELOPE")
    indices=[m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)",b)]
    if not indices or indices[0]!=3:raise ValueError("BCS_START")
    out=[b[a:z] for a,z in zip(indices,indices[1:]+[len(b)])]
    if b"SC\n"+b"".join(out)!=b:raise ValueError("BCS_NOT_LOSSLESS")
    return out
def parse_baf(text):
    blocks=[];current=None;mode=None
    for line in text.splitlines():
        s=line.strip()
        if s=="IF" and current is None:
            current={"conditions":[],"actions":[]};mode="conditions"
        elif s=="THEN" and current is not None:mode="actions"
        elif s=="END" and current is not None:
            blocks.append(current);current=None;mode=None
        elif current is not None and mode:
            current[mode].append(s)
    return blocks
def classify(block,n):
    actions=[a for a in block["actions"] if SUSPECT.search(a)]
    if not actions:return None
    t="\n".join(block["conditions"]);a="\n".join(actions)
    attacks=[x for x in actions if ATTACK.search(x)]
    risk=[]
    if attacks:
        if re.search(r"\b(?:LastAttackerOf|LastHitter|LastSeenBy)\s*\(",a,re.I):
            risk.append("MEMORIZED_ATTACKER_TARGET")
        if re.search(r"\bPlayer[1-6]\b",a,re.I):risk.append("PLAYER_TARGET_IN_ATTACK")
        if re.search(r"\b(?:NearestEnemyOf|LastAttackerOf)\s*\(",a,re.I) and not GUARD.search(t):
            risk.append("NO_EXPLICIT_FRIENDLY_FILTER_IN_THIS_BLOCK")
        if re.search(r"\b(?:LastAttackerOf|AttackedBy|HitBy|Hurt)\s*\(",t+"\n"+a,re.I):
            risk.append("REACTION_TO_HIT")
    if not risk and not LAST.search(t+"\n"+a):return None
    return {"block":n,"risk":risk or ["THREAT_OR_PROTECT_PATH"],
      "conditions":block["conditions"][:35],"actions":actions[:12]}
def main(root):
    p=live(root);before=sha(p);raw=p.read_bytes();count=len(parts(raw))
    weidu=root/"setup-enhanced-powergaming-scripts.exe";safe(weidu,root)
    if not weidu.is_file() or weidu.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_MISSING")
    log=root/"WeiDU.log";safe(log,root)
    component=[x.strip() for x in log.read_text("utf-8-sig",errors="replace").splitlines() if x.strip().startswith("~")]
    if not component:raise ValueError("WEIDU_LOG_EMPTY")
    with tempfile.TemporaryDirectory(prefix="BGXAI_AGGRO_READONLY_") as dirname:
        temp=pathlib.Path(dirname);binary=temp/"weidu.exe";shutil.copy2(weidu,binary)
        input_bcs=temp/"BDDEFAI.BCS";input_bcs.write_bytes(raw)
        output=temp/"BDDEFAI.BAF"
        args=[str(binary),"--game",str(root),"--out",str(output),str(input_bcs)]
        proc=subprocess.run(args,cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,
          text=True,errors="replace",timeout=180)
        if proc.returncode or not output.is_file():
            raise ValueError("WEIDU_DECOMPILE_FAILED:"+((proc.stdout or "")+"\n"+(proc.stderr or ""))[-500:])
        text=output.read_text("utf-8-sig",errors="replace")
        blocks=parse_baf(text)
        if not blocks or abs(len(blocks)-count)>1:
            raise ValueError("DECOMP_BLOCK_COUNT_MISMATCH:"+str(len(blocks))+"/"+str(count))
        suspects=[v for i,b in enumerate(blocks,1) if (v:=classify(b,i))]
        attacks=sum(bool(any(ATTACK.search(a) for a in block["actions"])) for block in blocks)
        # Only the exact decompiled text copied from the game's current BCS can be ranked.
        result={
          "status":"BGXAI_AGGRO_READONLY_AUDIT_PASS",
          "game_modified":False,"live_bcs_sha256":before,"live_bcs_blocks":count,
          "decompiled_blocks":len(blocks),"all_attack_blocks":attacks,
          "suspect_blocks":len(suspects),"last_weidu":component[-1],
          "suspects":suspects
        }
        if sha(p)!=before:raise ValueError("GAME_CHANGED_DURING_AUDIT")
        dest=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXAI_LIVE_REPORTS"
        if not dest.is_dir():
            dest=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report=dest/("BGXAI_FRIENDLY_AGGRO_READONLY_"+stamp+".json")
        report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k!="suspects"},ensure_ascii=False,indent=2))
        print("REPORT_FILE="+str(report))
        print("TOP_SUSPECT_BLOCKS:")
        for x in sorted(suspects,key=lambda x:(-len(x["risk"]),x["block"]))[:15]:
            print("BLOCK="+str(x["block"])+" FLAGS="+",".join(x["risk"]))
            print("  CONDITIONS="+ " | ".join(x["conditions"][:8]))
            print("  ACTIONS="+ " | ".join(x["actions"][:4]))
        return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--game",default=str(GAME));a=p.parse_args()
    try:main(pathlib.Path(a.game))
    except Exception as e:
        print("BGXAI_AGGRO_READONLY_STOP:"+str(e));sys.exit(1)
