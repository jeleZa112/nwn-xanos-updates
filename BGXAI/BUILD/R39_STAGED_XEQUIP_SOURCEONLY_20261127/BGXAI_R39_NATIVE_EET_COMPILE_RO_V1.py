#!/usr/bin/env python3
"""Exact R39 native EET compiler *adapter* built on already proven menu176 V3.

No new native backend, installer, executable or alternate updater. This module
only reuses the known V3 helper's process / compiler / backend proof and pins
NEW 2303-byte R39 BAF.  Native engine execution still requires the installed
Windows EET; never claim it occurred from local Linux tests.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

SCHEMA='BGXAI_R39_REUSE_MENU176_NATIVE_READONLY_V1'
BAF_NAME='BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf'
BAF_SHA='3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d'
BAF_LENGTH=2303
# Exact already native-tested 176 wrapper; do not modify it or copy backend code.
V3_HELPER_NAME='BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py'
V3_HELPER_SHA='b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e'
V3_HELPER_BYTES=10743

class Hold(ValueError):
    pass

def digest(raw:bytes):
    return hashlib.sha256(raw).hexdigest()

def exact_source(path:Path)->bytes:
    if path.name!=BAF_NAME or not path.is_file() or path.is_symlink():
        raise Hold('HOLD_EXACT_R39_BAF_REQUIRED')
    raw=path.read_bytes()
    if len(raw)!=BAF_LENGTH or digest(raw)!=BAF_SHA:
        raise Hold('HOLD_R39_BAF_BYTES_OR_SHA')
    # Byte pin is authoritative, but these guards are useful to audit why.
    text=raw.decode('ascii')
    for gate in ('Class(Myself,CLERIC)','Name("*GCLERIC",Myself)',
                 'CheckStatGT(Myself,4,STR)', '!HasItemSlot(Myself,SLOT_SHIELD)',
                 'ActionListEmpty()', 'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'):
        if gate not in text: raise Hold('HOLD_R39_REQUIRED_TRIGGER_OR_ACTION')
    if text.count('XEquipItem(')!=1 or text.count('Continue()')!=2:
        raise Hold('HOLD_R39_STAGE_STRUCTURE')
    return raw

def exact_v3_helper(path:Path):
    if path.name!=V3_HELPER_NAME or not path.is_file() or path.is_symlink():
        raise Hold('HOLD_V3_MENU176_HELPER_MISSING')
    raw=path.read_bytes()
    if len(raw)!=V3_HELPER_BYTES or digest(raw)!=V3_HELPER_SHA:
        raise Hold('HOLD_V3_MENU176_HELPER_PIN_DRIFT')
    spec=importlib.util.spec_from_file_location('bgxai_verified_menu176_helper',str(path))
    if not spec or not spec.loader: raise Hold('HOLD_V3_HELPER_IMPORT_FAILURE')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for k in ('close_game_proof','pinned_compiler','load_backend'):
        if not callable(getattr(mod,k,None)):
            raise Hold('HOLD_V3_HELPER_API_MISSING_'+k)
    return mod

def source_only(source:Path):
    raw=exact_source(source)
    return dict(schema=SCHEMA,status='EXACT_R39_BAF_PIN_PASS_NO_NATIVE',
        sourceSha256=digest(raw),sourceBytes=len(raw),
        reusesAlreadyNativeTestedV3Backend=True,nativeWeiDUCompileVerified=False,
        gameModified=False,installed=False,ordersSent=0,
        armAuthorized=False,dispatchAuthorized=False,liveXEquipTransferVerified=False)

def native_readonly(game:Path, source:Path, v3_helper:Path, backend_path:Path):
    raw=exact_source(source)
    v3=exact_v3_helper(v3_helper)
    v3.close_game_proof()
    if game.is_symlink() or not game.is_dir():
        raise Hold('HOLD_GAME_ROOT_NOT_SAFE')
    game=game.resolve(strict=True)
    compiler=v3.pinned_compiler(game)
    backend=v3.load_backend(backend_path)
    with tempfile.TemporaryDirectory(prefix='BGXAI_R39_NATIVE_RO_') as folder:
        tmp=Path(folder).resolve(strict=True)
        if game==tmp or game in tmp.parents or tmp in game.parents:
            raise Hold('HOLD_R39_TEMP_OVERLAPS_GAME')
        candidate=tmp/'BGXW39.baf'  # 7-character resource name, temp only.
        candidate.write_bytes(raw)
        if digest(candidate.read_bytes())!=BAF_SHA:
            raise Hold('HOLD_R39_TEMP_BAF_DRIFT')
        orig_check=backend.source_check
        orig_name=backend.TEMP_SOURCE_NAME
        try:
            def exact_check(path:Path,game_root:Path):
                verified=Path(path).resolve(strict=True)
                if verified!=candidate or verified==game_root or game_root in verified.parents:
                    raise backend.Hold('HOLD_R39_UNTRUSTED_SOURCE_LOCATION')
                content=backend.checked_file(Path(path),required=True)
                if content!=raw or digest(content)!=BAF_SHA:
                    raise backend.Hold('HOLD_R39_SOURCE_CHANGED_DURING_COMPILE')
                return {'sha256':BAF_SHA,'size':BAF_LENGTH,'blocks':3,'actionCount':14}
            backend.source_check=exact_check
            backend.TEMP_SOURCE_NAME=candidate.name
            result=backend.compile_readonly(game,candidate,compiler)
        finally:
            backend.source_check=orig_check
            backend.TEMP_SOURCE_NAME=orig_name
    good=(result.get('status')=='NATIVE_WEIDU_COMPILED_TEMP_ONLY' and
          result.get('nativeSymbolsAcceptedByCompiler') is True and
          result.get('watchedFilesChanged') is False and
          result.get('temporaryOutputRemoved') is True)
    return dict(schema=SCHEMA,
        status='R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL' if good else
               'HOLD_R39_NATIVE_EET_COMPILER',
        sourceSha256=BAF_SHA,sourceBytes=BAF_LENGTH,
        nativeWeiDUCompileVerified=good,
        compiledBcsSha256=result.get('compiledSha256') if good else None,
        compilerSha256=result.get('compilerSha256'),
        nativeStatus=result.get('status'),
        watchedFilesChanged=result.get('watchedFilesChanged'),
        temporaryOutputRemoved=result.get('temporaryOutputRemoved'),
        wholeGameTreeChecked=False,
        classKitItmUsabilityVerified=False,
        currentSessionActorArmed=False,
        manualEpsProvenanceVerified=False,
        safeActionBoundaryVerified=False,
        liveXEquipTransferVerified=False,
        gameModified=False,installed=False,armAuthorized=False,
        dispatchAuthorized=False,ordersSent=0)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,default=Path(__file__).with_name(BAF_NAME))
    ap.add_argument('--game',type=Path,default=Path(r'C:\Games\BG_EET_FOXX_NEW'))
    ap.add_argument('--v3-helper',type=Path)
    ap.add_argument('--backend',type=Path)
    ap.add_argument('--native-readonly',action='store_true')
    args=ap.parse_args(argv)
    try:
        if args.native_readonly:
            if args.v3_helper is None or args.backend is None:
                raise Hold('HOLD_NATIVE_PINNED_REUSE_SOURCES_REQUIRED')
            value=native_readonly(args.game,args.source,args.v3_helper,args.backend)
        else:
            value=source_only(args.source)
    except (Hold,OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired) as e:
        value=dict(schema=SCHEMA,status='HOLD_EXACT_R39_NATIVE_PREFLIGHT',
            reason=str(e) if isinstance(e,Hold) else 'HOLD_INPUT_OR_NATIVE_FAILURE',
            gameModified=False,installed=False,armAuthorized=False,
            dispatchAuthorized=False,ordersSent=0)
    print(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if value['status'] in ('EXACT_R39_BAF_PIN_PASS_NO_NATIVE',
        'R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL') else 3

if __name__=='__main__':
    raise SystemExit(main())
