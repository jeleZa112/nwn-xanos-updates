#!/usr/bin/env python3
"""BGXAI ranged fighter: native EET preflight; NEVER writes game files."""
import argparse,hashlib,json,pathlib,re,subprocess,tempfile,sys
GAME=pathlib.Path(r"C:\Games\BG_EET_FOXX_NEW")
BCS="override/BDDEFAI.BCS"
PINS={"override/BDDEFAI.BCS":"cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a","override/M_BX43.lua":"74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c","override/PRIEST1.BCS":"e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a"}
BAF_SHA="af7ef6e4287a346fd9ad66ac8458e39eb5d2a0e45bb7f52cabc7b5d266ee1546"
def digest(b):return hashlib.sha256(b).hexdigest()
def parts(b):
    if not b.startswith(b"SC\nCR\nCO\n") or not b.endswith(b"CR\nSC\n"):raise ValueError("BCS_ENVELOPE")
    starts=[m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)",b)]
    if not starts or starts[0]!=3:raise ValueError("BCS_START")
    out=[b[x:y] for x,y in zip(starts,starts[1:]+[len(b)])]
    if b"SC\n"+b"".join(out)!=b:raise ValueError("BCS_NOT_LOSSLESS")
    return out
def check(game):
    if game!=GAME or not (game/"chitin.key").is_file():raise ValueError("GAME_ROOT")
    for name,expected in PINS.items():
        p=game/name
        if p.is_symlink() or not p.is_file() or digest(p.read_bytes())!=expected:raise ValueError("BASELINE_SHA:"+name)
    log=(game/"WeiDU.log").read_text(encoding="utf-8-sig",errors="replace").splitlines()
    components=[line.strip() for line in log if line.lstrip().startswith("~")]
    if not components or not re.match(r"^~(?:[^~]*[/\\])?BGX120[/\\]SETUP-BGX120[.]TP2~\s+#0\s+#0(?:\s|$)",components[-1],re.I):raise ValueError("BGX120_NOT_LAST")
    b= (game/BCS).read_bytes()
    if len(parts(b))!=1170:raise ValueError("OLD_BCS_BLOCK_COUNT")
    return b
def run(game,mode):
    old=check(game)
    result={"status":"BGXRANGED_BASELINE_PASS","old_bcs_sha256":digest(old),"old_blocks":1170,"game_modified":False}
    if mode=="status":return result
    source=pathlib.Path(__file__).with_name("BGX_RANGED_FIGHTER.baf")
    if source.is_symlink() or digest(source.read_bytes())!=BAF_SHA:raise ValueError("BAF_SHA")
    exe=game/"setup-enhanced-powergaming-scripts.exe"
    if not exe.is_file() or exe.read_bytes()[:2]!=b"MZ":raise ValueError("NO_NATIVE_WEIDU")
    with tempfile.TemporaryDirectory(prefix="BGXRANGED_PREFLIGHT_") as folder:
        temp=pathlib.Path(folder);work=temp/"weidu.exe";work.write_bytes(exe.read_bytes())
        src=temp/"BGXRANGED.BAF";src.write_bytes(source.read_bytes())
        dest=temp/"out";dest.mkdir()
        cmd=[str(work),"--game",str(game),"--out",str(dest),str(src)]
        p=subprocess.run(cmd,cwd=temp,stdin=subprocess.DEVNULL,capture_output=True,text=True,errors="replace",timeout=150)
        msg=(p.stdout or "")+"\n"+(p.stderr or "")
        if p.returncode or re.search(r"(?im)^\s*(?:ERROR:|FATAL ERROR:)",msg):raise ValueError("NATIVE_WEIDU_FAIL:"+msg[-400:])
        candidates=list(dest.rglob("BGXRANGED.BCS"))
        if len(candidates)!=1:raise ValueError("COMPILED_BCS_NOT_FOUND")
        generated=parts(candidates[0].read_bytes())
        if len(generated)!=1 or not generated[0].endswith(b"CR\nSC\n"):raise ValueError("NEW_BCS_NOT_ONE_BLOCK")
        combined=b"SC\n"+generated[0][:-3]+old[3:]
        merged=parts(combined)
        if len(merged)!=1171 or merged[1:]!=parts(old):raise ValueError("REGRESSION_OLD_BCS_CHANGED")
        result.update(status="BGXRANGED_NATIVE_PREFLIGHT_PASS",new_blocks=1171,preserved_old_blocks=1170,candidate_sha256=digest(combined),game_modified=False)
    return result
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--mode",choices=["status","preflight"],default="preflight");a.add_argument("--game",default=str(GAME));v=a.parse_args()
    try:
        print(json.dumps(run(pathlib.Path(v.game),v.mode),indent=2))
    except Exception as e:
        print("BGXRANGED_PREFLIGHT_STOP:"+str(e));sys.exit(1)
