#!/usr/bin/env python3
"""BGXAI guarded experiment: isolate ONLY BGX38/39 ProtectObject script blocks.
The first run validates/decompiles native live BCS. No game write before explicit
INSTALL token and SHA-verified external backup. Does not claim this proves cause.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,pathlib,re,shutil,subprocess,sys,tempfile
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V3_GUARDED_INSTALL as V3
from BGX_FRIENDLY_AGGRO_AUDIT_READONLY import parse_baf

ROOT=P.GAME
BCS=P.BCS
BASE_SHA="89f59795c0382ab204731d898dc075504e2654085d0c7c247a53d3da439c2ffa"
DISABLE=tuple(range(1078,1089)) # exact 1-based BAF/BCS blocks, 11 total
NEW_COUNT=1173-len(DISABLE)
TP2="BGXSAFE/setup-BGXSAFE.tp2"
STAGED="BGXSAFE/staged/BDDEFAI.BCS"
PROOF="BGXSAFE/STAGED_PROOF.json"
EXE="setup-BGXSAFE.exe"
INSTALL_TOKEN="INSTALL_BGXSAFE_PROTECT_ISOLATION"
ROLLBACK_TOKEN="ROLLBACK_BGXSAFE_PROTECT_ISOLATION"
TP2_DATA="BACKUP ~BGXSAFE/backup~\nAUTHOR ~BGXAI safe diagnostic~\nBEGIN ~BGXAI temporary protect isolation~\nCOPY ~BGXSAFE/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n"
LAST=re.compile(r"^~(?:[^~]*[/\\])?BGXSAFE[/\\]SETUP-BGXSAFE[.]TP2~\s+#0\s+#0(?:\s|$)",re.I)
PROTECTED=(BCS,"override/M_BX43.lua","override/PRIEST1.BCS","WeiDU.log","chitin.key")
OPTIONAL=("lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk")
def sha(data):return hashlib.sha256(data).hexdigest()
def sha_file(p):return sha(p.read_bytes())
def verify_live(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.check_root(root)
    source=root/BCS;V3.V2.guard(source)
    if sha_file(source)!=BASE_SHA:raise ValueError("EXACT_V3_BCS_REQUIRED")
    if len(P.parts(source.read_bytes()))!=1173:raise ValueError("V3_BLOCK_COUNT_MISMATCH")
    if not V3.LAST.match(V3.last(root)):raise ValueError("V3_NOT_LAST_WEIDU")
    return source.read_bytes()
def verify_protect(block,index):
    cond=block["conditions"];actions=block["actions"]
    if 'Global("BGX38_GUARD","LOCALS",1)' not in cond:
        raise ValueError("NO_GUARD_GATE_BLOCK_"+str(index))
    if "ActionListEmpty()" not in cond:
        raise ValueError("NO_QUEUE_GATE_BLOCK_"+str(index))
    protect=[a for a in actions if re.fullmatch(r"ProtectObject\(Player[1-6],6\)",a)]
    if len(protect)!=1:raise ValueError("NOT_EXACT_PROTECT_BLOCK_"+str(index))
    # Do not silently remove healing, movement, attacks or other unknown work.
    allowed=re.compile(r"(?:ProtectObject\(Player[1-6],6\)|SetGlobal(?:Timer)?\(.*\)|RESPONSE\s+#\d+|\s*)$")
    for a in actions:
        if not allowed.fullmatch(a):raise ValueError("OTHER_ACTION_IN_PROTECT_BLOCK_"+str(index)+":"+a[:80])
def candidate(raw,decompiled):
    original=P.parts(raw);blocks=parse_baf(decompiled)
    if len(original)!=1173 or len(blocks)!=1173:raise ValueError("COUNT_OR_DECOMPILE_MISMATCH")
    for n in DISABLE:verify_protect(blocks[n-1],n)
    excluded=set(DISABLE)
    merged=b"SC\n"+b"".join(item for i,item in enumerate(original,1) if i not in excluded)
    check=P.parts(merged)
    if len(check)!=NEW_COUNT:raise ValueError("WRONG_NEW_COUNT")
    if check!=[item for i,item in enumerate(original,1) if i not in excluded]:
        raise ValueError("UNRELATED_BCS_CHANGED")
    return merged
def native_candidate(root):
    raw=verify_live(root)
    weidu=root/"setup-enhanced-powergaming-scripts.exe"
    V3.V2.guard(weidu)
    if not weidu.is_file() or weidu.read_bytes()[:2]!=b"MZ":raise ValueError("NATIVE_WEIDU_MISSING")
    with tempfile.TemporaryDirectory(prefix="BGXSAFE_PREFLIGHT_") as d:
        temp=pathlib.Path(d);exe=temp/"weidu.exe";shutil.copy2(weidu,exe)
        bcs=temp/"BDDEFAI.BCS";bcs.write_bytes(raw)
        baf=temp/"BDDEFAI.BAF"
        p=subprocess.run([str(exe),"--game",str(root),"--out",str(baf),str(bcs)],
            cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        if p.returncode or not baf.is_file():
            raise ValueError("NATIVE_DECOMPILE_STOP:"+((p.stdout or "")+"\n"+(p.stderr or ""))[-500:])
        stripped=candidate(raw,baf.read_text(encoding="utf-8-sig",errors="replace"))
        # Compile V4 directly with current native WeiDU. Tighten attack target
        # filters in the first three blocks in the SAME guarded installation.
        v4_source=pathlib.Path(__file__).with_name("BGXRANGED_V4_NO_FRIEND_ATTACK.baf")
        if v4_source.is_symlink() or not v4_source.is_file():
            raise ValueError("V4_SOURCE_MISSING_OR_LINK")
        v4_text=v4_source.read_text(encoding="ascii")
        for text in ("!InParty(NearestEnemyOf(Myself))",
                     "!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)"):
            if v4_text.count(text)!=3:raise ValueError("V4_TARGET_GUARDS_MISSING")
        v4_baf=temp/"BGXRANGEDV4.BAF";v4_baf.write_bytes(v4_source.read_bytes())
        v4_bcs=temp/"BGXRANGEDV4.BCS"
        p=subprocess.run([str(exe),"--game",str(root),"--out",str(v4_bcs),str(v4_baf)],
            cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        if p.returncode or not v4_bcs.is_file():
            raise ValueError("V4_NATIVE_COMPILE_STOP:"+((p.stdout or "")+"\n"+(p.stderr or ""))[-500:])
        v4_parts=P.parts(v4_bcs.read_bytes())
        if len(v4_parts)!=3:raise ValueError("V4_EXPECTED_THREE_BLOCKS")
        stripped_parts=P.parts(stripped)
        final=b"SC\n"+b"".join(v4_parts)[:-3]+b"".join(stripped_parts[3:])
        final_parts=P.parts(final)
        if len(final_parts)!=NEW_COUNT or final_parts[3:]!=stripped_parts[3:]:
            raise ValueError("FINAL_NON_PROTECT_CODE_CHANGED")
        return final,{"status":"BGXSAFE_PROTECT_ISOLATION_PREFLIGHT_PASS",
            "old_sha256":BASE_SHA,"candidate_sha256":sha(final),
            "v4_source_sha256":sha(v4_source.read_bytes()),
            "original_blocks":1173,"temporarily_disabled_protect_blocks":list(DISABLE),
            "remaining_blocks":NEW_COUNT,"other_old_blocks_byte_identical":True,
            "v4_attack_guards_compiled":True,
            "game_modified":False}
def safe_backup(root):
    parent=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXAI_SAFE_BACKUPS"
    folder=parent/("BGXSAFE_PRE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    V3.V2.guard(parent);folder.mkdir(parents=True,exist_ok=False)
    checks={}
    for name in PROTECTED+OPTIONAL:
        f=root/name;V3.V2.guard(f)
        if name in PROTECTED and not f.is_file():raise ValueError("BACKUP_INPUT_MISSING:"+name)
        if not f.exists():continue
        if not f.is_file():raise ValueError("BACKUP_INPUT_NOT_FILE:"+name)
        dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,dest);checks[name]=sha_file(f)
        if sha_file(dest)!=checks[name]:raise ValueError("BACKUP_SHA_MISMATCH:"+name)
    if checks.get(BCS)!=BASE_SHA:raise ValueError("BACKUP_BASE_SHA")
    (folder/"SHA256.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    return folder
def wei(root,remove=False):
    exe=root/EXE;V3.V2.guard(exe)
    op="--force-uninstall" if remove else "--force-install"
    args=[str(exe),"--noautoupdate","--no-exit-pause","--game",str(root),"--use-lang","ru_ru",op,"0"]
    p=subprocess.run(args,cwd=root,stdin=subprocess.DEVNULL,capture_output=True,
            text=True,errors="replace",timeout=240)
    o=(p.stdout or "")+"\n"+(p.stderr or "")
    if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",o):
        raise ValueError("WEIDU_STOP_MANUAL_INSPECTION:"+o[-700:])
def status(root):
    if root!=ROOT:raise ValueError("WRONG_GAME_ROOT")
    V3.check_root(root)
    if LAST.match(V3.last(root)):
        proof_file=root/PROOF;V3.V2.guard(proof_file)
        if not proof_file.is_file():raise ValueError("PROOF_MISSING")
        proof=json.loads(proof_file.read_text(encoding="utf-8"))
        expected=proof.get("candidate_sha256")
        if proof.get("base_sha256")!=BASE_SHA or not isinstance(expected,str) or not re.fullmatch("[0-9a-f]{64}",expected):
            raise ValueError("PROOF_BASE_OR_CANDIDATE_SHA")
        backup=pathlib.Path(proof["backup"]);V3.V2.guard(backup)
        before=backup/BCS
        if not before.is_file() or sha_file(before)!=BASE_SHA:raise ValueError("BACKUP_BASE_TAMPERED")
        bcs=(root/BCS).read_bytes()
        if sha(bcs)!=expected or sha_file(root/STAGED)!=expected:raise ValueError("PATCHED_LIVE_SHA_MISMATCH")
        a=P.parts(bcs);original=P.parts(before.read_bytes())
        if len(a)!=NEW_COUNT or len(original)!=1173:raise ValueError("PATCHED_COUNT_DRIFT")
        retained=[item for i,item in enumerate(original,1) if i not in set(DISABLE)]
        if a[3:]!=retained[3:]:
            raise ValueError("NON_PROTECT_CODE_CHANGED")
        if proof.get("v4_source_sha256")!=sha(pathlib.Path(__file__).with_name("BGXRANGED_V4_NO_FRIEND_ATTACK.baf").read_bytes()):
            raise ValueError("V4_SOURCE_SHA_CHANGED")
        for name in ("override/M_BX43.lua","override/PRIEST1.BCS"):
            if sha_file(root/name)!=P.PINS[name]:raise ValueError("OTHER_MODULE_DRIFT:"+name)
        return {"status":"BGXSAFE_PROTECT_ISOLATION_INSTALLED_VERIFIED",
            "candidate_sha256":expected,"blocks":NEW_COUNT,
            "only_protect_blocks_removed":True,"v4_friend_filters_compiled":True,"game_modified":False}
    verify_live(root)
    return {"status":"BGXSAFE_NOT_INSTALLED_V3_VERIFIED","blocks":1173,"game_modified":False}
def install(root):
    V3.V2.V1.processes()
    if (root/"BGXSAFE").exists() or (root/EXE).exists():
        raise ValueError("STAGING_COLLISION")
    old_log=sha_file(root/"WeiDU.log")
    data,report=native_candidate(root)
    V3.V2.V1.processes()
    if sha_file(root/BCS)!=BASE_SHA or sha_file(root/"WeiDU.log")!=old_log:
        raise ValueError("GAME_CHANGED_AFTER_PREFLIGHT")
    snap=safe_backup(root)
    stage_dir=root/"BGXSAFE"/"staged";stage_dir.mkdir(parents=True,exist_ok=False)
    (root/STAGED).write_bytes(data)
    (root/TP2).write_text(TP2_DATA,encoding="utf-8",newline="\n")
    (root/PROOF).write_text(json.dumps({"base_sha256":BASE_SHA,
        "candidate_sha256":report["candidate_sha256"],"v4_source_sha256":report["v4_source_sha256"],"backup":str(snap)},indent=2),encoding="utf-8")
    shutil.copy2(root/"setup-enhanced-powergaming-scripts.exe",root/EXE)
    if sha_file(root/STAGED)!=report["candidate_sha256"]:raise ValueError("STAGED_SHA_DRIFT")
    V3.V2.V1.processes()
    if sha_file(root/BCS)!=BASE_SHA or sha_file(root/"WeiDU.log")!=old_log or not V3.LAST.match(V3.last(root)):
        raise ValueError("GAME_CHANGED_BEFORE_WEIDU")
    wei(root)
    result=status(root)
    if result["status"]!="BGXSAFE_PROTECT_ISOLATION_INSTALLED_VERIFIED":
        raise ValueError("POST_INSTALL_VERIFY_STOP")
    return dict(result,game_modified=True,backup=str(snap))
def rollback(root):
    V3.V2.V1.processes()
    current=status(root)
    if current["status"]!="BGXSAFE_PROTECT_ISOLATION_INSTALLED_VERIFIED" or not LAST.match(V3.last(root)):
        raise ValueError("NOT_LAST_COMPONENT")
    proof=json.loads((root/PROOF).read_text(encoding="utf-8"))
    backup=pathlib.Path(proof["backup"]);V3.V2.guard(backup)
    checks=json.loads((backup/"SHA256.json").read_text(encoding="utf-8"))
    if checks.get(BCS)!=BASE_SHA:raise ValueError("BACKUP_SHA_MISMATCH")
    for name,expected in checks.items():
        f=backup/name;V3.V2.guard(f)
        if sha_file(f)!=expected:raise ValueError("BACKUP_TAMPERED:"+name)
    V3.V2.V1.processes()
    wei(root,remove=True)
    result=status(root)
    if result["status"]!="BGXSAFE_NOT_INSTALLED_V3_VERIFIED":raise ValueError("ROLLBACK_NOT_RESTORED")
    return {"status":"BGXSAFE_PROTECT_ISOLATION_ROLLBACK_V3_RESTORED",
            "bcs_sha256":BASE_SHA,"game_modified":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("status","preflight","install","rollback"))
    p.add_argument("--game",default=str(ROOT))
    opts=p.parse_args();root=pathlib.Path(opts.game)
    try:
        if opts.mode=="status":result=status(root)
        elif opts.mode=="preflight":result=native_candidate(root)[1]
        elif opts.mode=="install":
            if input("Type "+INSTALL_TOKEN+" exactly: ").strip()!=INSTALL_TOKEN:
                raise ValueError("INSTALL_NOT_AUTHORIZED")
            result=install(root)
        else:
            if input("Type "+ROLLBACK_TOKEN+" exactly: ").strip()!=ROLLBACK_TOKEN:
                raise ValueError("ROLLBACK_NOT_AUTHORIZED")
            result=rollback(root)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXSAFE_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
