#!/usr/bin/env python3
"""SOURCE-ONLY BGXAI native compile preflight for the EXACT real-save V3 BAF.

Default mode validates a published, pinned BAF snapshot; never invokes WeiDU.
Opt-in --native-readonly is intended for a FUTURE guarded branch of the ONE
existing BGXAI_UPDATE.cmd. It never writes/installs a BCS or sets LOCALS.
Native mode needs the real Windows EET and game closed; NOT run in CI.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

SCHEMA = 'BGXAI_XEQUIP_V3_EXACT_NATIVE_COMPILE_RO_V1'
EVIDENCE_NAME = 'BGXAI_REAL_JAGAN_BUILD_AUDIT_AND_BAF_V3.json'
EVIDENCE_SHA256 = '83a6865028336b9a2ebec5645ae34670832f1b07f372620f9c3961968a378b28'
BAF_SHA256 = '996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1'
BAF_LENGTH = 762
BAF_NAME = 'BGXW3NAT.baf'  # 8-char resource name, compiled ONLY outside the game.
WEIDU_SHA256 = '0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75'
BACKEND_GIT_BLOB_SHA1 = '0bd66e6f2fd97cf69291a7b3ae5463f7e3295995'
BACKEND_RELPATH = ('BGXAI/patchsets/ranged_fighter_guarded_20261119/'
                   'BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py')
DEFAULT_GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')

class Hold(ValueError):
    pass

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\x00' + raw).hexdigest()

def verified_evidence(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.name != EVIDENCE_NAME:
        raise Hold('HOLD_V3_EVIDENCE_FILE_UNTRUSTED')
    raw = path.read_bytes()
    if sha(raw) != EVIDENCE_SHA256:
        raise Hold('HOLD_V3_EVIDENCE_PIN_DRIFT')
    obj = json.loads(raw.decode('utf-8'))
    if not isinstance(obj, dict) or set(obj) != {'audit', 'sourceOnlyBaf'}:
        raise Hold('HOLD_V3_EVIDENCE_SCHEMA')
    audit = obj['audit']
    if not isinstance(audit, dict) or audit.get('schema') != 'BGXAI_XEQUIP_LOCAL_ARM_BUILD_AUDIT_V3':
        raise Hold('HOLD_V3_AUDIT_SCHEMA')
    expected = {
        'bafSha256': BAF_SHA256, 'bafBytes': BAF_LENGTH,
        'partyIndexSnapshot': 1, 'sourceSlot': 20, 'targetSlot': 35,
        'sourceResref': 'STAF01', 'localWitnessValue': 2110908191,
        'gamSha256Verified': True, 'savedCandidateVerified': True,
        'scope': 'ACTOR_LOCALS_NOT_GLOBAL',
        'automaticArmingCodePresent': False,
        'runtimeActorIdentityVerified': False,
        'safeActionBoundaryVerified': False,
        'eetNativeActiveBafCompileVerified': False,
        'installed': False, 'ordersSent': 0, 'dispatchAuthorized': False,
    }
    for key, value in expected.items():
        if type(audit.get(key)) is not type(value) or audit.get(key) != value:
            raise Hold('HOLD_V3_AUDIT_FIELD_' + key)
    baf = obj['sourceOnlyBaf']
    if not isinstance(baf, str):
        raise Hold('HOLD_V3_BAF_TEXT_MISSING')
    try:
        raw_baf = baf.encode('ascii')
    except UnicodeEncodeError as exc:
        raise Hold('HOLD_V3_BAF_NON_ASCII') from exc
    if len(raw_baf) != BAF_LENGTH or sha(raw_baf) != BAF_SHA256:
        raise Hold('HOLD_V3_BAF_SHA_OR_LENGTH_DRIFT')
    # The pinned bytes are stronger than these guards; keep guards as a review aid.
    if (baf.count('\nIF\n') != 1 or baf.count('\nTHEN\n') != 1 or
        baf.count('\nEND\n') != 1 or baf.count('XEquipItem(') != 1 or
        baf.count('CheckItemSlot(') != 1 or baf.count('!HasItemSlot(') != 1 or
        baf.count('Global("BGXW3ARM","LOCALS",1)') != 1 or
        'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)' not in baf or
        'CheckItemSlot(Myself,"STAF01",SLOT_MISC5)' not in baf or
        'SetGlobal("BGXW3ARM","LOCALS",2)' not in baf or
        'SetGlobal("BGXW3TRY","LOCALS",1)' not in baf or
        'SetGlobal("BGXW3TAG","LOCALS",0)' not in baf or
        'SetGlobal("BGXW3ARM","LOCALS",1)' in baf or
        any(k in baf for k in ('ClearActions(', 'Stop(', 'FillSlot(', 'CreateItem(',
                               'Attack(', 'SelectWeaponAbility('))):
        raise Hold('HOLD_V3_BAF_CONTRACT')
    return raw_baf

def load_backend(path: Path):
    if path.is_symlink() or not path.is_file() or path.name != Path(BACKEND_RELPATH).name:
        raise Hold('HOLD_NATIVE_BACKEND_UNTRUSTED_PATH')
    raw = path.read_bytes()
    if gitblob(raw) != BACKEND_GIT_BLOB_SHA1:
        raise Hold('HOLD_NATIVE_BACKEND_BLOB_PIN_CHANGED')
    spec = importlib.util.spec_from_file_location('bgxai_verified_native_compiler', str(path))
    if not spec or not spec.loader:
        raise Hold('HOLD_NATIVE_BACKEND_IMPORT_SPEC')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ('compile_readonly','checked_file','digest','Hold','source_check','TEMP_SOURCE_NAME'):
        if not hasattr(module, name):
            raise Hold('HOLD_NATIVE_BACKEND_API_'+name)
    return module

def close_game_proof():
    if os.name != 'nt':
        raise Hold('HOLD_NATIVE_EET_COMPILE_WINDOWS_ONLY')
    proc = subprocess.run(['tasklist.exe', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True, errors='replace', timeout=15, check=False)
    if proc.returncode != 0 or not proc.stdout:
        raise Hold('HOLD_WINDOWS_PROCESS_LIST_UNREADABLE')
    import csv, io
    for row in csv.reader(io.StringIO(proc.stdout)):
        if not row:
            continue
        name = row[0].lower().strip()
        if (name in ('baldur.exe','bg2ee.exe','baldursgate.exe','infinityloader.exe',
                     'weidu.exe','setup-enhanced-powergaming-scripts.exe') or
            name.startswith('setup-bg')):
            raise Hold('HOLD_GAME_OR_WEIDU_RUNNING')

def pinned_compiler(game: Path) -> Path:
    for name in ('setup-enhanced-powergaming-scripts.exe','weidu.exe'):
        p = game / name
        if p.is_symlink():
            raise Hold('HOLD_WEIDU_SYMLINK')
        if p.is_file() and sha(p.read_bytes()) == WEIDU_SHA256:
            return p
    raise Hold('HOLD_PINNED_WEIDU_25100_MISSING_OR_SHA_DRIFT')

def source_only(evidence: Path) -> dict:
    baf = verified_evidence(evidence)
    return dict(schema=SCHEMA, status='EXACT_V3_BAF_PIN_VERIFIED_NO_NATIVE_COMPILE',
        bafSha256=sha(baf), bafBytes=len(baf),
        nativeWeiDUCompileVerified=False, gameScriptChanged=False,
        installed=False, ordersSent=0, dispatchAuthorized=False,
        safeActionBoundaryVerified=False, classKitItmUsabilityVerified=False,
        runtimeActorIdentityVerified=False, engineTransferVerified=False)

def native_readonly(game: Path, evidence: Path, backend_path: Path) -> dict:
    close_game_proof()
    baf = verified_evidence(evidence)
    if game.is_symlink() or not game.is_dir():
        raise Hold('HOLD_GAME_DIR_UNTRUSTED')
    game = game.resolve(strict=True)
    compiler = pinned_compiler(game)
    backend = load_backend(backend_path)
    with tempfile.TemporaryDirectory(prefix='BGXAI_V3_EXACT_NATIVE_RO_') as folder:
        temp = Path(folder).resolve(strict=True)
        if game == temp or game in temp.parents or temp in game.parents:
            raise Hold('HOLD_TEMP_OVERLAPS_GAME')
        source = temp / BAF_NAME
        source.write_bytes(baf)
        if sha(source.read_bytes()) != BAF_SHA256:
            raise Hold('HOLD_TEMP_BAF_DRIFT')
        orig_check, orig_name = backend.source_check, backend.TEMP_SOURCE_NAME
        try:
            def exact_check(path: Path, game_root: Path):
                target = Path(path).resolve(strict=True)
                if target != source or game_root == target or game_root in target.parents:
                    raise backend.Hold('HOLD_SOURCE_LOCATION_NOT_ISOLATED')
                actual = backend.checked_file(Path(path), required=True)
                if actual != baf or len(actual) != BAF_LENGTH or sha(actual) != BAF_SHA256:
                    raise backend.Hold('HOLD_SOURCE_EXACT_V3_DRIFT')
                return {'sha256': sha(actual), 'size': len(actual), 'blocks':1,
                        'actionCount':4}
            backend.source_check = exact_check
            backend.TEMP_SOURCE_NAME = BAF_NAME
            result = backend.compile_readonly(game, source, compiler)
        finally:
            backend.source_check, backend.TEMP_SOURCE_NAME = orig_check, orig_name
    good = (result.get('status') == 'NATIVE_WEIDU_COMPILED_TEMP_ONLY' and
            result.get('nativeSymbolsAcceptedByCompiler') is True and
            result.get('watchedFilesChanged') is False and
            result.get('temporaryOutputRemoved') is True)
    # Never claim the watched files cover all game contents or an idle actor state.
    return dict(schema=SCHEMA,
        status='V3_NATIVE_BAF_COMPILED_TEMP_ONLY' if good else 'HOLD_V3_NATIVE_COMPILE',
        bafSha256=BAF_SHA256, bafBytes=BAF_LENGTH, nativeWeiDUCompileVerified=good,
        compilerSha256=result.get('compilerSha256'),
        compiledBcsSha256=result.get('compiledSha256') if good else None,
        watchedFilesChanged=result.get('watchedFilesChanged'),
        wholeGameTreeChecked=False,
        temporaryOutputRemoved=result.get('temporaryOutputRemoved'),
        innerStatus=result.get('status'), installed=False, ordersSent=0,
        dispatchAuthorized=False, classKitItmUsabilityVerified=False,
        safeActionBoundaryVerified=False, manualEpsOriginVerified=False,
        runtimeActorIdentityVerified=False, engineTransferVerified=False)

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence',type=Path,default=Path(__file__).with_name(EVIDENCE_NAME))
    p.add_argument('--game',type=Path,default=DEFAULT_GAME)
    p.add_argument('--backend',type=Path)
    p.add_argument('--native-readonly',action='store_true')
    a = p.parse_args(argv)
    try:
        if a.native_readonly:
            if a.backend is None:
                raise Hold('HOLD_PINNED_BACKEND_PATH_REQUIRED')
            result = native_readonly(a.game, a.evidence, a.backend)
        else:
            result = source_only(a.evidence)
    except (Hold,OSError,ValueError,TypeError,UnicodeError,subprocess.TimeoutExpired) as exc:
        result = dict(schema=SCHEMA,status='HOLD_EXACT_V3_NATIVE_PREFLIGHT',
            reason=str(exc), nativeWeiDUCompileVerified=False,
            installed=False, ordersSent=0, dispatchAuthorized=False,
            safeActionBoundaryVerified=False)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status'] in (
        'EXACT_V3_BAF_PIN_VERIFIED_NO_NATIVE_COMPILE','V3_NATIVE_BAF_COMPILED_TEMP_ONLY') else 3

if __name__ == '__main__':
    raise SystemExit(main())