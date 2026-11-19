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
        # Inspect the last saved party CRE script slots and decompile its
        # actual referenced scripts. This is historical save evidence, NEVER
        # runtime command provenance. No read-only scan may change the game.
        try:
            from BGXAI_SAVE_SCRIPT_AUDIT_READONLY import audit as audit_script_slots
            result["saved_party_script_audit"]=audit_script_slots(root,weidu,temp,parse_baf)
        except (OSError,ValueError,RuntimeError,UnicodeError) as e:
            result["saved_party_script_audit"]={
                "status":"SCRIPT_ASSIGNMENT_SCAN_STOP",
                "reason":str(e)[:500],
                "runtime_action_origin":"UNKNOWN",
                "game_modified":False
            }
        # Existing combat log only. Does not enable/modify any EEex listener.
        # When no target-bearing BGX71 records exist, runtime attack proof=UNKNOWN.
        try:
            from BGX_COMBAT_LOG_READONLY_AUDIT import report as combat_log_report
            result["combat_action_log_audit"]=combat_log_report(root)
        except (OSError,ValueError,RuntimeError) as e:
            result["combat_action_log_audit"]={"status":"COMBAT_LOG_SCAN_STOP",
                "reason":str(e)[:400], "runtime_action_origin":"UNKNOWN",
                "game_modified":False}
        if sha(p)!=before:raise ValueError("GAME_CHANGED_DURING_AUDIT")
        dest=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXAI_LIVE_REPORTS"
        if not dest.is_dir():
            dest=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report=dest/("BGXAI_FRIENDLY_AGGRO_READONLY_"+stamp+".json")
        report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in result.items() if k!="suspects"},ensure_ascii=False,indent=2))
        print("REPORT_FILE="+str(report))
        evidence=result.get("saved_party_script_audit",{})
        saved=evidence.get("saved_party",{})
        print("SAVED_GAME_STATUS="+str(saved.get("status","UNAVAILABLE")))
        print("SAVED_GAME="+str(saved.get("save_file","NONE")))
        print("PARTY_AI_AT_SAVE="+str(saved.get("gui_party_ai_flag_at_save","UNKNOWN")))
        for actor in saved.get("party",[]):
            print("SAVED_ACTOR="+str(actor.get("position"))+" "+
                str(actor.get("name_from_saved_record","UNKNOWN"))+
                " SCRIPTS="+str(actor.get("scripts",{})))
        for script in evidence.get("scripts",[]):
            print("ASSIGNED_SCRIPT="+str(script.get("script"))+
                  " STATUS="+str(script.get("status"))+
                  " ATTACK_BLOCKS="+str(script.get("attack_or_protect_blocks","UNKNOWN")))
        print("RUNTIME_ACTION_ORIGIN=UNKNOWN (static audit only)")
        action_log=result.get("combat_action_log_audit",{})
        print("COMBAT_LOG_STATUS="+str(action_log.get("status","UNKNOWN")))
        print("COMBAT_BGX71_ACTIONS="+str(action_log.get("bgx71_actions_in_tail",0)))
        print("COMBAT_PARTY_ATTACK_STARTS_OBSERVED="+str(len(action_log.get("observed_party_attack_starts",[]))))
        for evt in action_log.get("observed_party_attack_starts",[])[:15]:
            print("PARTY_ACTION_STARTED: actor_slot="+str(evt.get("actor_slot"))+
                " target_slot="+str(evt.get("target_slot"))+
                " action_id="+str(evt.get("action_id"))+
                " origin=UNKNOWN")

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
