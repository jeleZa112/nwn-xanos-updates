#!/usr/bin/env python3
"""BGXAI V3 native WeiDU compile, strict READ ONLY.
Only accepts exact installed V2 BCS/last WeiDU; does not touch game.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,subprocess,sys,tempfile
import BGXRANGED_PREFLIGHT as P
import BGXRANGED_V2_GUARDED_INSTALL as V2

V2_SHA=V2.V2_SHA
BASE_SHA=P.PINS[P.BCS]
SOURCE=pathlib.Path(__file__).with_name("BGXRANGED_V3_MELEE_HANDOFF.baf")
def sha(data):return hashlib.sha256(data).hexdigest()
def validate(root):
    if root!=P.GAME or not (root/"chitin.key").is_file():raise ValueError("GAME_ROOT")
    if root.is_symlink():raise ValueError("GAME_SYMLINK")
    V2.check_protected(root)
    live=root/P.BCS
    if live.is_symlink() or not live.is_file() or sha(live.read_bytes())!=V2_SHA:
        raise ValueError("V2_BCS_NOT_EXACT")
    if not V2.LAST.match(V2.last(root)):raise ValueError("V2_NOT_LAST_WEIDU")
    proof=root/V2.PROOF
    if proof.is_symlink() or not proof.is_file():raise ValueError("V2_PROOF_MISSING")
    j=json.loads(proof.read_text(encoding="utf-8"))
    if j.get("candidate_sha256")!=V2_SHA or j.get("previous_sha256")!=V2.V1_SHA:
        raise ValueError("V2_PROOF_DRIFT")
    if sha((root/V2.STAGED).read_bytes())!=V2_SHA:raise ValueError("V2_STAGE_DRIFT")
    blocks=P.parts(live.read_bytes())
    if len(blocks)!=1173:raise ValueError("V2_BLOCKS_NOT_1173")
    original=b"SC\n"+b"".join(blocks[3:])
    if sha(original)!=BASE_SHA:raise ValueError("ORIGINAL_1170_DRIFT")
    return original
def run(root):
    original=validate(root)
    source=SOURCE.read_bytes()
    if SOURCE.is_symlink() or source.count(b"\nIF\n")!=3:
        raise ValueError("V3_SOURCE_SHAPE")
    exe=root/"setup-enhanced-powergaming-scripts.exe"
    if exe.is_symlink() or not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("NATIVE_WEIDU_MISSING")
    with tempfile.TemporaryDirectory(prefix="BGXAI_V3_READONLY_") as folder:
        temp=pathlib.Path(folder);compiler=temp/"weidu.exe";compiler.write_bytes(exe.read_bytes())
        baf=temp/"BGXRANGEDV3.BAF";baf.write_bytes(source)
        output=temp/"out";output.mkdir()
        cmd=[str(compiler),"--game",str(root),"--out",str(output),str(baf)]
        p=subprocess.run(cmd,cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=180)
        log=(p.stdout or "")+"\n"+(p.stderr or "")
        if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",log):
            raise ValueError("V3_NATIVE_COMPILE_FAIL:"+log[-650:])
        results=list(output.rglob("BGXRANGEDV3.BCS"))
        if len(results)!=1:raise ValueError("COMPILED_BCS_NOT_FOUND")
        new=P.parts(results[0].read_bytes())
        if len(new)!=3:raise ValueError("COMPILED_BLOCK_COUNT")
        candidate=b"SC\n"+b"".join(new)[:-3]+original[3:]
        whole=P.parts(candidate)
        if len(whole)!=1173 or whole[3:]!=P.parts(original):
            raise ValueError("ORIGINAL_BLOCKS_NOT_PRESERVED")
        return {"status":"BGXRANGED_V3_NATIVE_PREFLIGHT_PASS","current":"V2_INSTALLED_1173",
          "source_sha256":sha(source),"candidate_sha256":sha(candidate),
          "candidate_blocks":1173,"preserved_old_blocks":1170,"game_modified":False}
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--game",default=str(P.GAME));options=a.parse_args()
    try:print(json.dumps(run(pathlib.Path(options.game)),indent=2))
    except Exception as e:print("BGXRANGED_V3_PREFLIGHT_STOP:"+str(e));sys.exit(1)
