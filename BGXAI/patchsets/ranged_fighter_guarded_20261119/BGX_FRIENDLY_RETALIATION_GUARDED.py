#!/usr/bin/env python3
"""BGXAI: guarded and reversible friendly-fire retaliation filters for three scripts.

Exact live baseline: BGXSAFE installed + WTASIGHT and PRIEST1 SHA pins, DPLAYER
as game BIFF script (no override). Compiles *native EET* decompiled sources in
TEMP and changes only designated attack blocks. Never edits savegames or CREs.
No claim of causal proof until post-install gameplay verification.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V3_GUARDED_INSTALL as V3
import BGX_FRIENDLY_PROTECT_ISOLATION as SAFE
from BGX_FRIENDLY_AGGRO_AUDIT_READONLY import parse_baf

ROOT=P.GAME
SCRIPTS={
 "WTASIGHT":{"sha":"d3055bb06a50e2a6152e4ace8d2753e5450df28e066148eae2a0c01651e24605",
             "count":6,"patch":{4:("AttackReevaluate(NearestEnemyOf(Myself),30)","NearestEnemyOf(Myself)"),
                                5:("Attack(LastAttackerOf(Myself))","LastAttackerOf(Myself)")}},
 "DPLAYER":{"sha":None,"count":2,"patch":{
             1:("AttackOneRound(NearestEnemyOf(Myself))","NearestEnemyOf(Myself)"),
             2:("AttackOneRound(LastAttackerOf(Myself))","LastAttackerOf(Myself)")}},
 "PRIEST1":{"sha":"e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a",
             "count":5,"patch":{5:("Attack(NearestEnemyOf(Myself))","NearestEnemyOf(Myself)")}}
}
BASE_BD="9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e"
DIR="BGXFRIEND"
TP2=DIR+"/setup-BGXFRIEND.tp2"
PROOF=DIR+"/STAGED_PROOF.json"
EXE="setup-BGXFRIEND.exe"
TOKEN_INSTALL="INSTALL_BGXFRIEND_RETALIATION_GUARD"
TOKEN_ROLLBACK="ROLLBACK_BGXFRIEND_RETALIATION_GUARD"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXFRIEND[/\\]SETUP-BGXFRIEND[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
STAGED=lambda name:DIR+"/staged/"+name+".BCS"
TP2_DATA=("BACKUP ~BGXFRIEND/backup~\nAUTHOR ~BGXAI friendly retaliation guard~\n"
 "BEGIN ~BGXAI friendly retaliation filters for WTASIGHT DPLAYER PRIEST1~\n"+
 "".join(f"COPY ~{STAGED(n)}~ ~override/{n}.BCS~\n" for n in SCRIPTS))
PROTECTED=("override/BDDEFAI.BCS","override/M_BX43.lua","override/WTASIGHT.BCS",
           "override/PRIEST1.BCS","WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
BLOCK_RE=re.compile(r"(?ms)^IF[ \t]*\n.*?^END[ \t]*$")
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):return sha(path.read_bytes())
def ensure(root):
 if root!=ROOT:raise ValueError("UNEXPECTED_GAME_ROOT")
 V3.V2.require_root(root)
 for name in (*PROTECTED, "override/DPLAYER.BCS"):
  V3.V2.guard(root/name)
 if (root/"override/DPLAYER.BCS").exists():raise ValueError("DPLAYER_OVERRIDE_ALREADY_EXISTS")
 if digest(root/"override/BDDEFAI.BCS")!=BASE_BD:raise ValueError("BGXSAFE_BCS_DRIFT")
 for name in ("WTASIGHT","PRIEST1"):
  if digest(root/"override"/(name+".BCS"))!=SCRIPTS[name]["sha"]:
   raise ValueError("BASE_SHA_DRIFT:"+name)
 if not SAFE.LAST.match(V3.last(root)):raise ValueError("BGXSAFE_NOT_LAST_WEIDU")
def text_blocks(baf):
 items=list(BLOCK_RE.finditer(baf))
 if not items:raise ValueError("NO_BAF_BLOCKS")
 return items
def guard_baf(baf,name):
 spec=SCRIPTS[name]
 items=text_blocks(baf)
 if len(items)!=spec["count"]:raise ValueError("BAF_BLOCK_COUNT:"+name)
 patched=baf
 for index in sorted(spec["patch"],reverse=True):
  expected,target=spec["patch"][index]
  item=items[index-1]; block=item.group()
  parsed=parse_baf(block)
  if len(parsed)!=1:raise ValueError("BAF_PARSE:"+name)
  acts=[a for a in parsed[0]["actions"] if a.startswith(("Attack(", "AttackOneRound(", "AttackReevaluate("))]
  if acts!=[expected]:raise ValueError("ACTION_SIGNATURE_MISMATCH:"+name+":"+str(index)+":"+str(acts))
  if name in ("WTASIGHT","DPLAYER") and target=="LastAttackerOf(Myself)":
   if "AttackedBy([ANYONE],DEFAULT)" not in parsed[0]["conditions"]:
    raise ValueError("ATTACK_EVENT_SIGNATURE:"+name)
  if any("!InParty("+target+")" in s or "!Allegiance("+target+"," in s for s in parsed[0]["conditions"]):
   raise ValueError("ALREADY_GUARDED_STOP:"+name+":"+str(index))
  conditions="  !InParty("+target+")\n  !Allegiance("+target+",GOODCUTOFF)\n"
  result,count=re.subn(r"(?m)^THEN[ \t]*$",lambda m:conditions+m.group(),block,count=1)
  if count!=1:raise ValueError("BAF_THEN_NOT_FOUND:"+name)
  patched=patched[:item.start()]+result+patched[item.end():]
 if len(text_blocks(patched))!=spec["count"]:raise ValueError("BAF_PATCH_COUNT:"+name)
 return patched
def native_compile(exe,root,temp,name,baf):
 # WeiDU v251 behavior is verified for same-stem BAF -> BCS paths.
 # Never write compiler output to a game path or overwrite source BCS.
 compiled_dir=temp/"compiled";compiled_dir.mkdir(exist_ok=True)
 inp=compiled_dir/(name+".BAF");inp.write_text(baf,encoding="utf-8")
 out=compiled_dir/(name+".BCS")
 if out.exists():raise ValueError("COMPILED_OUTPUT_COLLISION:"+name)
 p=subprocess.run([str(exe),"--game",str(root),"--out",str(out),str(inp)],
                  cwd=compiled_dir,stdin=subprocess.DEVNULL,capture_output=True,
                  text=True,errors="replace",timeout=180)
 err=(p.stdout or "")+"\n"+(p.stderr or "")
 if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",err) or not out.is_file():
  raise ValueError("WEIDU_COMPILE_STOP:"+name+":"+err[-600:])
 compiled=out.read_bytes()
 if len(P.parts(compiled))!=SCRIPTS[name]["count"]:raise ValueError("COMPILED_BLOCK_COUNT:"+name)
 return compiled
def source_baf(exe,root,temp,name):
 # Match the *live-tested* menu 135 decompilation: WeiDU receives a
 # local TEMP copy of override/WTASIGHT.BCS or override/PRIEST1.BCS,
 # not an absolute path into game/override. DPLAYER is loaded from BIFF.
 source_dir=temp/"source";source_dir.mkdir(exist_ok=True)
 out=source_dir/(name+".BAF")
 if out.exists():raise ValueError("DECOMPILE_OUTPUT_COLLISION:"+name)
 if name!="DPLAYER":
  original=root/"override"/(name+".BCS")
  V3.V2.guard(original)
  if not original.is_file() or digest(original)!=SCRIPTS[name]["sha"]:
   raise ValueError("DECOMPILE_SOURCE_SHA_DRIFT:"+name)
  local=source_dir/(name+".BCS")
  shutil.copy2(original,local)
  if digest(local)!=SCRIPTS[name]["sha"]:
   raise ValueError("TEMP_SOURCE_COPY_SHA_DRIFT:"+name)
  origin=local
 else:
  origin=pathlib.Path("DPLAYER.BCS")
 p=subprocess.run([str(exe),"--game",str(root),"--out",str(out),str(origin)],
                  cwd=source_dir,stdin=subprocess.DEVNULL,capture_output=True,
                  text=True,errors="replace",timeout=180)
 err=(p.stdout or "")+"\n"+(p.stderr or "")
 if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",err) or not out.is_file():
  raise ValueError("WEIDU_DECOMPILE_STOP:"+name+
                   ":expected="+str(out)+
                   ":exit="+str(p.returncode)+":"+err[-480:])
 text=out.read_text("utf-8-sig",errors="replace")
 if len(text_blocks(text))!=SCRIPTS[name]["count"]:
  raise ValueError("SOURCE_BLOCK_COUNT:"+name)
 return text
def stage_data(root):
 ensure(root)
 weidu=root/"setup-enhanced-powergaming-scripts.exe"
 V3.V2.guard(weidu)
 if not weidu.is_file() or weidu.read_bytes()[:2]!=b"MZ":raise ValueError("NATIVE_WEIDU_MISSING")
 staged={}
 original_source={}
 with tempfile.TemporaryDirectory(prefix="BGXFRIEND_NATIVE_") as dirname:
  temp=pathlib.Path(dirname);native=temp/"weidu.exe";shutil.copy2(weidu,native)
  for name,spec in SCRIPTS.items():
   text=source_baf(native,root,temp,name)
   original_source[name]=sha(text.encode("utf-8"))
   replaced=guard_baf(text,name)
   built=native_compile(native,root,temp,name,replaced)
   new_parts=P.parts(built)
   if spec["sha"]:
    existing=(root/"override"/(name+".BCS")).read_bytes()
    old_parts=P.parts(existing)
    if len(old_parts)!=spec["count"]:raise ValueError("LIVE_BLOCK_COUNT:"+name)
    for i in range(spec["count"]):
     if i+1 not in spec["patch"]:new_parts[i]=old_parts[i]
    built=b"SC\n"+b"".join(new_parts)
    if len(P.parts(built))!=spec["count"]:
     raise ValueError("SPLICE_FAIL:"+name)
    if any(P.parts(built)[i-1]!=old_parts[i-1] for i in range(1,spec["count"]+1) if i not in spec["patch"]):
     raise ValueError("PRESERVED_BLOCK_DRIFT:"+name)
   staged[name]=built
  if not all(len(P.parts(staged[k]))==SCRIPTS[k]["count"] for k in SCRIPTS):
   raise ValueError("NATIVE_STAGE_COUNTS")
 return staged,original_source
def preflight(root):
 staged,sources=stage_data(root)
 return {"status":"BGXFRIEND_NATIVE_PREFLIGHT_PASS","old_bdde_fai_sha256":BASE_BD,
  "old_wtasight_sha256":SCRIPTS["WTASIGHT"]["sha"],
  "old_priest1_sha256":SCRIPTS["PRIEST1"]["sha"],
  "dplayer_original_source_sha256":sources["DPLAYER"],
  "patched_script_sha256":{n:sha(v) for n,v in staged.items()},
  "patched_block_numbers":{n:list(x["patch"]) for n,x in SCRIPTS.items()},
  "other_existing_blocks_byte_identical":True,
  "game_modified":False}
def backup(root):
 parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXFRIEND_SAFE_BACKUPS"
 V3.V2.guard(parent)
 folder=parent/("PRE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
 folder.mkdir(parents=True,exist_ok=False)
 checks={}
 for name in PROTECTED+OPTIONAL:
  p=root/name;V3.V2.guard(p)
  if name in PROTECTED and not p.is_file():raise ValueError("BACKUP_SOURCE_MISSING:"+name)
  if not p.exists():continue
  if not p.is_file():raise ValueError("NOT_A_FILE:"+name)
  target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(p,target);checks[name]=digest(p)
  if digest(target)!=checks[name]:raise ValueError("BACKUP_TAMPERED:"+name)
 if checks.get("override/BDDEFAI.BCS")!=BASE_BD:
  raise ValueError("BACKUP_BASELINE_DRIFT")
 (folder/"SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
 return folder
def last(root):return V3.last(root)
def status(root):
 V3.V2.require_root(root)
 if LAST.match(last(root)):
  proof_file=root/PROOF;V3.V2.guard(proof_file)
  if not proof_file.is_file():raise ValueError("PROOF_MISSING")
  record=json.loads(proof_file.read_text("utf-8"))
  if record.get("baseline_bdde_fai_sha256")!=BASE_BD:raise ValueError("PROOF_BASE_DRIFT")
  for name,spec in SCRIPTS.items():
   expected=record.get("patched_script_sha256",{}).get(name)
   if not isinstance(expected,str) or not re.fullmatch("[0-9a-f]{64}",expected):
    raise ValueError("PROOF_INVALID:"+name)
   for p in (root/"override"/(name+".BCS"),root/STAGED(name)):
    V3.V2.guard(p)
    if not p.is_file() or digest(p)!=expected:raise ValueError("LIVE_PATCH_DRIFT:"+name)
   if len(P.parts((root/"override"/(name+".BCS")).read_bytes()))!=spec["count"]:
    raise ValueError("PATCHED_COUNT_DRIFT:"+name)
  if digest(root/"override/BDDEFAI.BCS")!=BASE_BD:raise ValueError("BGXSAFE_CODE_CHANGED")
  for name in ("override/M_BX43.lua",):
   if digest(root/name)!=P.PINS[name]:raise ValueError("LUA_CHANGED")
  return {"status":"BGXFRIEND_INSTALLED_VERIFIED","patched_script_sha256":record["patched_script_sha256"],
          "blocks":{n:SCRIPTS[n]["count"] for n in SCRIPTS},
          "game_modified":False}
 ensure(root)
 return {"status":"BGXFRIEND_NOT_INSTALLED_BASE_VERIFIED","game_modified":False}
def run_weidu(root,uninstall=False):
 exe=root/EXE;V3.V2.guard(exe)
 cmd=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),"--use-lang","ru_ru",
      "--force-uninstall" if uninstall else "--force-install","0"]
 p=subprocess.run(cmd,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
                 text=True,errors="replace",timeout=240)
 out=(p.stdout or "")+"\n"+(p.stderr or "")
 if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",out):
  raise ValueError("WEIDU_STOP_MANUAL_INSPECTION:"+out[-650:])
def install(root):
 V3.V2.V1.processes()
 if (root/DIR).exists() or (root/EXE).exists():raise ValueError("STAGING_COLLISION")
 original_log=digest(root/"WeiDU.log")
 staged,sources=stage_data(root)
 V3.V2.V1.processes()
 ensure(root)
 if digest(root/"WeiDU.log")!=original_log:raise ValueError("WEIDU_CHANGED")
 snap=backup(root)
 staged_dir=root/DIR/"staged";V3.V2.guard(staged_dir)
 staged_dir.mkdir(parents=True,exist_ok=False)
 for name,data in staged.items():
  (root/STAGED(name)).write_bytes(data)
 (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
 proof={"baseline_bdde_fai_sha256":BASE_BD,
        "patched_script_sha256":{n:sha(data) for n,data in staged.items()},
        "dplayer_original_source_sha256":sources["DPLAYER"],"backup":str(snap)}
 (root/PROOF).write_text(json.dumps(proof,indent=2),encoding="utf-8")
 shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
 if any(digest(root/STAGED(n))!=proof["patched_script_sha256"][n] for n in SCRIPTS):
  raise ValueError("STAGE_SHA_DRIFT")
 V3.V2.V1.processes()
 ensure(root)
 if digest(root/"WeiDU.log")!=original_log:raise ValueError("WEIDU_CHANGED_BEFORE_INSTALL")
 run_weidu(root)
 result=status(root)
 if result["status"]!="BGXFRIEND_INSTALLED_VERIFIED":raise ValueError("POST_INSTALL_VERIFY_STOP")
 return dict(result,game_modified=True,backup=str(snap))
def rollback(root):
 V3.V2.V1.processes()
 current=status(root)
 if current["status"]!="BGXFRIEND_INSTALLED_VERIFIED" or not LAST.match(last(root)):
  raise ValueError("FRIEND_COMPONENT_NOT_LAST")
 proof=json.loads((root/PROOF).read_text("utf-8"))
 snap=pathlib.Path(proof["backup"]);V3.V2.guard(snap)
 checks=json.loads((snap/"SHA256.json").read_text("utf-8"))
 for name,value in checks.items():
  p=snap/name;V3.V2.guard(p)
  if digest(p)!=value:raise ValueError("BACKUP_SHA_FAIL:"+name)
 if checks.get("override/BDDEFAI.BCS")!=BASE_BD:raise ValueError("BACKUP_NOT_BGXSAFE")
 V3.V2.V1.processes()
 run_weidu(root,uninstall=True)
 if (root/"override/DPLAYER.BCS").exists():raise ValueError("DPLAYER_OVERRIDE_NOT_REMOVED")
 if not SAFE.LAST.match(last(root)):raise ValueError("ROLLBACK_LAST_NOT_SAFE")
 for name in ("WTASIGHT","PRIEST1"):
  if digest(root/"override"/(name+".BCS"))!=SCRIPTS[name]["sha"]:
   raise ValueError("ROLLBACK_ORIGINAL_SHA_FAIL:"+name)
 if digest(root/"override/BDDEFAI.BCS")!=BASE_BD:
  raise ValueError("ROLLBACK_OTHER_MODULE_DRIFT")
 return {"status":"BGXFRIEND_ROLLBACK_VERIFIED_BGXSAFE_RESTORED","game_modified":True}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("mode",choices=("preflight","status","install","rollback"))
 ap.add_argument("--game",default=str(ROOT));opts=ap.parse_args();root=pathlib.Path(opts.game)
 try:
  if opts.mode=="status":report=status(root)
  elif opts.mode=="preflight":report=preflight(root)
  elif opts.mode=="install":
   if input("Type "+TOKEN_INSTALL+" exactly: ").strip()!=TOKEN_INSTALL:
    raise ValueError("INSTALL_NOT_AUTHORIZED")
   report=install(root)
  else:
   if input("Type "+TOKEN_ROLLBACK+" exactly: ").strip()!=TOKEN_ROLLBACK:
    raise ValueError("ROLLBACK_NOT_AUTHORIZED")
   report=rollback(root)
  print(json.dumps(report,ensure_ascii=False,indent=2));return 0
 except Exception as e:
  print("BGXFRIEND_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
