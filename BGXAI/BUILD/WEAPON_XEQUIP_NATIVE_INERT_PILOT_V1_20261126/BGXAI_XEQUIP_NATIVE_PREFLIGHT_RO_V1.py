#!/usr/bin/env python3
"""BGXAI inactive BAF native compile preflight, delegates to pinned existing V3 tool.

Default: source-only; native compile must be explicitly requested by onefile updater.
Does not install, overwrite any game resource, run the game, or authorize equip.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BASE_GIT_BLOB_SHA1 = "0bd66e6f2fd97cf69291a7b3ae5463f7e3295995"
WEIDU_SHA256 = "0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75"
DEFAULT_GAME = Path(r"C:\Games\BG_EET_FOXX_NEW")
NATIVE_BAF = "BGXI1CHK.baf"
SCHEMA = "BGXAI_XEQUIP_INERT_READONLY_WEIDU_V1"

class Hold(ValueError): pass

def git_blob_sha(content:bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii")
                        + b"\0" + content).hexdigest()

def load_python(path:Path, name:str):
    spec=importlib.util.spec_from_file_location(name,str(path))
    if spec is None or spec.loader is None:
        raise Hold("HOLD_SCRIPT_IMPORT_SPEC")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def backend_path() -> Path:
    return (Path(__file__).resolve().parents[2] /
      "patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py")

def verify_backend():
    source=backend_path()
    if source.is_symlink() or not source.is_file():
        raise Hold("HOLD_COMPILER_BACKEND_FILE")
    data=source.read_bytes()
    if git_blob_sha(data) != BASE_GIT_BLOB_SHA1:
        raise Hold("HOLD_WEIDU_SOURCE_BACKEND_GIT_BLOB_CHANGED")
    backend=load_python(source,"bgxai_verified_compile_backend_v3")
    for name in ("compile_readonly","checked_file","digest","Hold"):
        if not hasattr(backend,name):
            raise Hold("HOLD_MISSING_BACKEND_API_"+name)
    return backend

def generate(manifest_path:Path) -> tuple[str,dict]:
    gen=load_python(Path(__file__).with_name("BGXAI_XEQUIP_INERT_PROBE_V1.py"),
                    "bgxai_xequip_inert_generator")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise Hold("HOLD_MANIFEST_MISSING_OR_SYMLINK")
    if manifest_path.stat().st_size>4096: raise Hold("HOLD_MANIFEST_TOO_LARGE")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    baf=gen.render(manifest)
    if baf.count("\n  False()\n") != 1 or baf.count("XEquipItem(")!=1:
        raise Hold("HOLD_BAF_NOT_INERT")
    if "FillSlot(" in baf or "ClearActions(" in baf or "Stop(" in baf:
        raise Hold("HOLD_BAF_UNSAFE_ACTION")
    return baf,manifest

def compiler_path(game:Path) -> Path:
    for name in ("setup-enhanced-powergaming-scripts.exe","weidu.exe"):
        p=game/name
        if p.is_symlink(): raise Hold("HOLD_WEIDU_SYMLINK")
        if p.is_file():
            if hashlib.sha256(p.read_bytes()).hexdigest()==WEIDU_SHA256:
                return p
    raise Hold("HOLD_PINNED_WEIDU_NOT_FOUND_OR_SHA_CHANGED")

def close_game_proof():
    if os.name!="nt":raise Hold("HOLD_NATIVE_PREFLIGHT_WINDOWS_ONLY")
    run=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],
            text=True,capture_output=True,errors="replace",
            check=False,timeout=10)
    if run.returncode!=0:raise Hold("HOLD_TASKLIST_ERROR")
    for line in run.stdout.splitlines():
        name=line.split(",",1)[0].strip().strip('"').lower()
        if name in {"baldur.exe","bg2ee.exe","baldursgate.exe",
                    "infinityloader.exe","weidu.exe",
                    "setup-enhanced-powergaming-scripts.exe"} or (
                    name.startswith("setup-bg")):
            raise Hold("HOLD_GAME_OR_WEIDU_PROCESS_RUNNING")

def source_only(manifest_path:Path) -> dict:
    baf,_=generate(manifest_path)
    backend=verify_backend()
    return {"schema":SCHEMA,"status":"INERT_SOURCE_READY_NO_NATIVE_COMPILE",
       "bafName":NATIVE_BAF,"bafSha256":hashlib.sha256(baf.encode("ascii")).hexdigest(),
       "backendGitBlobSha1":BASE_GIT_BLOB_SHA1,
       "compileBackendLoaded":backend is not None,
       "nativeSymbolsAcceptedByCompiler":False,"nativeWeiDUCompileVerified":False,
       "installed":False,"ordersSent":0,"dispatchAuthorized":False,
       "weaponSwitchAuthorized":False,"inventoryMoveAuthorized":False,
       "safeActionBoundaryVerified":False,"itemTransferSemanticsVerified":False}

def native_readonly(game:Path, manifest_path:Path) -> dict:
    close_game_proof()
    baf,_=generate(manifest_path)
    backend=verify_backend()
    if game.is_symlink() or not game.is_dir():
        raise Hold("HOLD_GAME_DIR_MISSING_OR_SYMLINK")
    game=game.resolve(strict=True)
    compiler=compiler_path(game)
    with tempfile.TemporaryDirectory(prefix="BGXAI_INERT_XEQUIP_RO_") as d:
        folder=Path(d).resolve(strict=True)
        if folder==game or game in folder.parents:
            raise Hold("HOLD_TEMP_INSIDE_GAME")
        source=folder/NATIVE_BAF
        raw=baf.encode("ascii")
        source.write_bytes(raw)
        # Restrict *existing* compiler preflight to THIS exact inert source.
        original_check=backend.source_check
        try:
            def exact_source_check(path:Path, game_root:Path):
                got=backend.checked_file(Path(path),required=True)
                if got!=raw or b"\n  False()\n" not in got:
                    raise backend.Hold("BAF_PROBE_EXACT_SOURCE_DRIFT")
                p=Path(path).resolve(strict=True)
                if p==game_root or game_root in p.parents:
                    raise backend.Hold("BAF_SOURCE_MUST_BE_EXTERNAL_TEMP")
                return {"sha256":backend.digest(got),"size":len(got),
                        "blocks":1,"actionCount":2}
            backend.source_check=exact_source_check
            backend.TEMP_SOURCE_NAME=NATIVE_BAF
            out=backend.compile_readonly(game,source,compiler)
        finally:
            backend.source_check=original_check
    out.update({"schema":SCHEMA,"inertFalseGuard":True,
        "nativeActionActuallyExecuted":False,
        "installed":False,"ordersSent":0,"dispatchAuthorized":False,
        "weaponSwitchAuthorized":False,"inventoryMoveAuthorized":False,
        "manualEpsOriginVerified":False,"itemTransferSemanticsVerified":False,
        "safeActionBoundaryVerified":False})
    return out

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--game",type=Path,default=DEFAULT_GAME)
    ap.add_argument("--native-readonly",action="store_true",default=False)
    a=ap.parse_args(argv)
    try:
        out=native_readonly(a.game,a.manifest) if a.native_readonly else source_only(a.manifest)
    except (Hold,ValueError,TypeError,OSError,subprocess.TimeoutExpired) as ex:
        out={"schema":SCHEMA,"status":"HOLD_INERT_NATIVE_PREFLIGHT","reason":str(ex),
             "installed":False,"ordersSent":0,"dispatchAuthorized":False,
             "inventoryMoveAuthorized":False}
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0 if out["status"] in (
        "INERT_SOURCE_READY_NO_NATIVE_COMPILE","NATIVE_WEIDU_COMPILED_TEMP_ONLY"
       ) and out.get("watchedFilesChanged") is not True else 3

if __name__=="__main__":
    raise SystemExit(main())
