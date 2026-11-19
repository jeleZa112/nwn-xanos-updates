#!/usr/bin/env python3
"""BGXAI V2 read-only native WeiDU compile for an installed V1 OR original baseline.
No EET writes. No installers. No change to pinned V1. Fail closed.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,subprocess,tempfile,sys,argparse
import BGXRANGED_PREFLIGHT as P

V1_SHA="49b553908e7b66ab85714e91dd27800cad2ec4a9c51d8860d24aeb67b3c461b3"
SOURCE=pathlib.Path(__file__).with_name("BGXRANGED_V2_MELEE_HANDOFF.baf")
def sha(data):return hashlib.sha256(data).hexdigest()
def baseline(game):
    if game!=P.GAME or not (game/"chitin.key").is_file():raise ValueError("GAME_ROOT")
    for name in ("override/M_BX43.lua","override/PRIEST1.BCS"):
        f=game/name
        if not f.is_file() or f.is_symlink() or sha(f.read_bytes())!=P.PINS[name]:
            raise ValueError("PROTECTED_BASE_DRIFT:"+name)
    old=(game/P.BCS).read_bytes()
    if sha(old)==P.PINS[P.BCS]:
        if len(P.parts(old))!=1170:raise ValueError("BASE_BLOCKS")
        P.check(game)
        return "ORIGINAL_1170",old
    if sha(old)!=V1_SHA:raise ValueError("UNKNOWN_LIVE_BCS")
    blocks=P.parts(old)
    if len(blocks)!=1171:raise ValueError("V1_BLOCK_COUNT")
    prior=b"SC\n"+b"".join(blocks[1:])
    if sha(prior)!=P.PINS[P.BCS]:raise ValueError("V1_ORIGINAL_BLOCKS_CHANGED")
    log=(game/"WeiDU.log").read_text(encoding="utf-8-sig",errors="replace").splitlines()
    last=[x.strip() for x in log if x.lstrip().startswith("~")]
    if not last or not re.match(r"^~(?:[^~]*[/\\])?BGXRANGED[/\\]SETUP-BGXRANGED[.]TP2~\s+#0\s+#0(?:\s|$)",last[-1],re.I):
        raise ValueError("V1_NOT_LAST_WEIDU")
    return "V1_INSTALLED_1171",prior
def run(game):
    state,prior=baseline(game)
    if SOURCE.is_symlink() or not SOURCE.is_file():raise ValueError("SOURCE_MISSING_OR_LINK")
    source=SOURCE.read_bytes()
    if source.count(b"\nIF\n")!=3:raise ValueError("V2_THREE_BLOCKS_EXPECTED")
    exe=game/"setup-enhanced-powergaming-scripts.exe"
    if exe.is_symlink() or not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("WEIDU_NOT_FOUND")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED_V2_READONLY_") as folder:
        tmp=pathlib.Path(folder);binary=tmp/"weidu.exe";binary.write_bytes(exe.read_bytes())
        src=tmp/"BGXRANGEDV2.BAF";src.write_bytes(source)
        output=tmp/"out";output.mkdir()
        p=subprocess.run([str(binary),"--game",str(game),"--out",str(output),str(src)],
          cwd=tmp,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        log=(p.stdout or "")+"\n"+(p.stderr or "")
        if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
            raise ValueError("NATIVE_COMPILE_FAIL:"+log[-700:])
        bcs=list(output.rglob("BGXRANGEDV2.BCS"))
        if len(bcs)!=1:raise ValueError("V2_COMPILED_FILE_MISSING")
        new=P.parts(bcs[0].read_bytes())
        if len(new)!=3:raise ValueError("NATIVE_V2_EXPECTED_3_BLOCKS")
        candidate=b"SC\n"+b"".join(new)[:-3]+prior[3:]
        allparts=P.parts(candidate)
        if len(allparts)!=1173 or allparts[3:]!=P.parts(prior):
            raise ValueError("1170_PRIOR_BLOCKS_NOT_PRESERVED")
        return {"status":"BGXRANGED_V2_NATIVE_PREFLIGHT_PASS","current":state,
                "candidate_sha256":sha(candidate),"source_sha256":sha(source),
                "candidate_blocks":1173,"preserved_old_blocks":1170,
                "game_modified":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--game",default=str(P.GAME));o=p.parse_args()
    try:print(json.dumps(run(pathlib.Path(o.game)),indent=2))
    except Exception as e:print("BGXRANGED_V2_PREFLIGHT_STOP:"+str(e));sys.exit(1)
