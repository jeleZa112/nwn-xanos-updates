#!/usr/bin/env python3
"""BGXAI R46 exact read-only WeiDU native BAF compile, reusing R39/V3 backend.

No game changes; the only native execution compiles the already-pinned inert
R46 script in OS TEMP with the game's pinned compiler and watched-file SHA
before/after. The current R44 installed last157 and its user live CLASS
assignment are independent proof; neither this compiler nor a compiled BCS
proves that BDDEFAI actually executes. No R39 XEquip BAF compiled here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R46_SOURCE=HERE/"BGXAI_R46_INERT_BDDEFAI_WITNESS_SOURCE_ONLY.py"
R39_BASE=REPO/"BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127"
R39_HELPER=R39_BASE/"BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py"
V3_HELPER=REPO/"BGXAI/BUILD/WEAPON_XEQUIP_V3_NATIVE_RO_20261127/BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py"
BACKEND=REPO/"BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py"
EXPECTED={
 R46_SOURCE.name:"4630b4ab59e45d8fac8ba92068bafa588438415d",
 R39_HELPER.name:"69a8cc2105c410cce61d429d6a049dfd4cfad584",
 V3_HELPER.name:"1c72fbaf8cc34e6057f2eb75b0f31c950a606d2d",
 BACKEND.name:"988905f55303f0eccbb379bc3c3a7f11cda35d95",
}
EXPECTED_BAF_SIZE=223
EXPECTED_BAF_SHA="af9c78d00dd24806c694e7ee1d6fe882a65b8a9fd71acc90654f60188932a0d9"
SCHEMA="BGXAI_R46_NATIVE_BAF_TEMP_COMPILE_SOURCE_ONLY_V1"
class Hold(ValueError):
    pass

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def verified_module(path:Path,name:str):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=EXPECTED.get(path.name):
        raise Hold("HOLD_PINNED_R46_COMPILER_ANCESTRY:"+path.name)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_R46_MODULE_IMPORT:"+name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def load_all():
    r46=verified_module(R46_SOURCE,"r46_passive_source")
    r39=verified_module(R39_HELPER,"r46_reuse_native_r39")
    v3=r39.exact_v3_helper(V3_HELPER)
    backend=v3.load_backend(BACKEND)
    sources=r46.compose()
    baf=sources["R46_WITNESS_BAF"]
    if len(baf)!=EXPECTED_BAF_SIZE or sha(baf)!=EXPECTED_BAF_SHA:
        raise Hold("HOLD_R46_EXACT_INERT_BAF_DRIFT")
    return r46,r39,v3,backend,baf

def native_ro(game:Path,*,r39=None,v3=None,backend=None,baf=None):
    if r39 is None:
        _,r39,v3,backend,baf=load_all()
    v3.close_game_proof()
    if not game.is_dir() or game.is_symlink():
        raise Hold("HOLD_R46_GAME_ROOT_UNSAFE")
    game=game.resolve(strict=True)
    compiler=v3.pinned_compiler(game)
    with tempfile.TemporaryDirectory(prefix="BGXAI_R46_BCS_WITNESS_NO_INSTALL_") as folder:
        temp=Path(folder).resolve(strict=True)
        if temp==game or temp in game.parents or game in temp.parents:
            raise Hold("HOLD_R46_TEMP_OVERLAPS_GAME")
        staged=temp/"BGXR46.baf"
        staged.write_bytes(baf)
        if sha(staged.read_bytes())!=EXPECTED_BAF_SHA:
            raise Hold("HOLD_R46_STAGED_BAF_SHA")
        original_source_check=backend.source_check
        original_temp_name=backend.TEMP_SOURCE_NAME
        try:
            def exact_check(path:Path,root:Path):
                if Path(path).resolve(strict=True)!=staged or staged==root or root in staged.parents:
                    raise backend.Hold("HOLD_R46_UNTRUSTED_NATIVE_SOURCE")
                raw=backend.checked_file(Path(path),required=True)
                if raw!=baf or sha(raw)!=EXPECTED_BAF_SHA:
                    raise backend.Hold("HOLD_R46_BAF_DRIFT_DURING_NATIVE")
                return {"sha256":EXPECTED_BAF_SHA,"size":EXPECTED_BAF_SIZE,"blocks":1,"actionCount":1}
            backend.source_check=exact_check
            backend.TEMP_SOURCE_NAME=staged.name
            result=backend.compile_readonly(game,staged,compiler)
        finally:
            backend.source_check=original_source_check
            backend.TEMP_SOURCE_NAME=original_temp_name
    good=(result.get("status")=="NATIVE_WEIDU_COMPILED_TEMP_ONLY"
          and result.get("nativeSymbolsAcceptedByCompiler") is True
          and result.get("watchedFilesChanged") is False
          and result.get("temporaryOutputRemoved") is True)
    return {"schema":SCHEMA,
       "status":"R46_NATIVE_BAF_TEMP_PASS_NO_INSTALL" if good else "HOLD_R46_NATIVE_BAF",
       "r46BafSourceSha256":EXPECTED_BAF_SHA,"r46BafBytes":len(baf),
       "compiledBcsSha256":result.get("compiledSha256") if good else None,
       "nativeStatus":result.get("status"),
       "watchedFilesChanged":result.get("watchedFilesChanged"),
       "temporaryOutputRemoved":result.get("temporaryOutputRemoved"),
       "actualClassBcsExecutionVerified":False,
       "gameModified":False,"installed":False,"ordersSent":0,
       "armAuthorized":False,"dispatchAuthorized":False,
       "noAutoRetry":not good}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-ro",action="store_true")
    p.add_argument("--game",type=Path,default=Path(r"C:\Games\BG_EET_FOXX_NEW"))
    args=p.parse_args(argv)
    try:
        if args.native_ro:
            out=native_ro(args.game)
        else:
            _,_,_,_,baf=load_all()
            out={"schema":SCHEMA,"status":"R46_SOURCE_ONLY_EXACT_INERT_BAF_PASS",
              "r46BafSourceSha256":sha(baf),"r46BafBytes":len(baf),
              "nativeBafCompileVerified":False,"gameModified":False,
              "installed":False,"ordersSent":0,"armAuthorized":False,
              "dispatchAuthorized":False}
    except (OSError,ValueError,TypeError) as err:
        out={"schema":SCHEMA,"status":"R46_STOP_MANUAL_REVIEW",
             "reason":str(err) if isinstance(err,Hold) else "HOLD_IO_OR_RUNTIME",
             "noAutoRetry":True,"gameModified":False,"installed":False,
             "ordersSent":0,"armAuthorized":False,"dispatchAuthorized":False}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out["status"] in (
        "R46_SOURCE_ONLY_EXACT_INERT_BAF_PASS","R46_NATIVE_BAF_TEMP_PASS_NO_INSTALL") else 3

if __name__=="__main__":
    raise SystemExit(main())
