#!/usr/bin/env python3
"""Exact R39 native EET compiler *adapter* built on already proven menu176 V3.

No new native backend, installer, executable or alternate updater. This module
only reuses the known V3 helper's process / compiler / backend proof and pins
the original 2303-byte R39 BAF plus optional 2407-byte EEex-session variant.  Native engine execution still requires the installed
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
SESSION_BAF_NAME='BGXAI_R39_JAGAN_STAF01_EEEX_SESSION_SOURCE_ONLY.baf'
SESSION_BAF_SHA='6d39e72684548c7b1b900e80f1bdb4271044e9889364db958f52b0532d1b73f0'
SESSION_BAF_LENGTH=2407
# Exact already native-tested 176 wrapper; do not modify it or copy backend code.
V3_HELPER_NAME='BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py'
V3_HELPER_SHA='b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e'
V3_HELPER_BYTES=10743
# R3/R34 already authenticated this CURRENT_GAME_OVERRIDE object; never re-scan
# an entire game or infer default STAF01 resource in preference to override.
ITM_RELATIVE='override/STAF01.ITM'
ITM_SHA='c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3'
TRUECLASS_KIT_RAW=0x4000  # user R38 snapshot, not verified per new session

class Hold(ValueError):
    pass

def digest(raw:bytes):
    return hashlib.sha256(raw).hexdigest()

def source_spec(path:Path):
    if path.name==BAF_NAME:
        return BAF_SHA,BAF_LENGTH,False
    if path.name==SESSION_BAF_NAME:
        return SESSION_BAF_SHA,SESSION_BAF_LENGTH,True
    raise Hold('HOLD_EXACT_R39_BAF_REQUIRED')

def exact_source(path:Path)->bytes:
    sha,size,session=source_spec(path)
    if not path.is_file() or path.is_symlink():
        raise Hold('HOLD_EXACT_R39_BAF_REQUIRED')
    raw=path.read_bytes()
    if len(raw)!=size or digest(raw)!=sha:
        raise Hold('HOLD_R39_BAF_BYTES_OR_SHA')
    # Byte pin is authoritative, but these guards are useful to audit why.
    text=raw.decode('ascii')
    for gate in ('Class(Myself,CLERIC)','Name("*GCLERIC",Myself)',
                 'CheckStatGT(Myself,4,STR)', '!HasItemSlot(Myself,SLOT_SHIELD)',
                 'ActionListEmpty()', 'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)'):
        if gate not in text: raise Hold('HOLD_R39_REQUIRED_TRIGGER_OR_ACTION')
    if text.count('XEquipItem(')!=1 or text.count('Continue()')!=2:
        raise Hold('HOLD_R39_STAGE_STRUCTURE')
    trigger='EEex_LuaTrigger("return BGXW3_EEexSessionGate()")'
    if text.count(trigger)!=(2 if session else 0) or text.count('EEex_LuaTrigger(')!=(2 if session else 0):
        raise Hold('HOLD_R39_EXACT_SESSION_TRIGGER_GUARD')
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

def static_item_preflight(game:Path):
    """Verify *only* fixed ITM usability fields for observed trueclass Cleric.

    This is no runtime item/effect or engine usability claim.  ITM V1 offsets:
    class usability 0x1e (byte1 bit7 = CLERIC), trueclass kit usability
    0x2d (kit byte3 bit6 = NO_KIT), level/stats 0x24..0x32.
    Original current-game resource digest was already saved in R3/R34.
    """
    if not game.is_dir() or game.is_symlink():
        raise Hold('HOLD_ITM_GAME_DIRECTORY_UNTRUSTED')
    override=game/'override'
    item=override/'STAF01.ITM'
    if override.is_symlink() or item.is_symlink() or not item.is_file():
        raise Hold('HOLD_ITM_MISSING_OR_REPARSE')
    if not 114<=item.stat().st_size<=5_000_000:
        raise Hold('HOLD_ITM_INVALID_SIZE')
    raw=item.read_bytes()
    if digest(raw)!=ITM_SHA:
        raise Hold('HOLD_ITM_CURRENT_RESOURCE_SHA_DRIFT')
    if raw[:4]!=b'ITM ' or raw[4:8]!=b'V1  ':
        raise Hold('HOLD_ITM_NOT_V1_HEADER')
    def u16(o):return int.from_bytes(raw[o:o+2],'little')
    if u16(0x1c)!=26 or u16(0x26)!=5 or int.from_bytes(raw[0x18:0x1c],'little')!=46:
        raise Hold('HOLD_ITM_BASELINE_TYPE_STRENGTH_FLAGS_DRIFT')
    cleric_restricted=bool(raw[0x1e] & 0x80)
    no_kit_restricted=bool(raw[0x2d] & 0x40)
    if cleric_restricted:
        raise Hold('HOLD_ITM_RESTRICTS_CLERIC')
    if no_kit_restricted:
        raise Hold('HOLD_ITM_RESTRICTS_TRUECLASS')
    # Actor race/alignment were not authenticated in the R38 capture.  Do not
    # mislabel a class/kit pass as usable when these unknown filters are active.
    if raw[0x1e] & 0x3f:
        raise Hold('HOLD_ITM_ALIGNMENT_RESTRICTIONS_UNVERIFIED')
    # ITM V1.0 header usability bytes 3 and 4 MIX races with classes.
    # Byte 3 bit 7 (0x20 & 0x80) = Elf, NOT a class. Byte 4 bits
    # 0..4,7 = Dwarf/Half-Elf/Halfling/Human/Gnome/Half-Orc;
    # bits 5,6 = MONK/DRUID(+Shaman EE), unrelated to a trueclass CLERIC.
    # R38 captured CLERIC but NOT race. Never clear a *real* race restriction.
    unrelated_monk_druid_mask=raw[0x21] & 0x60
    unknown_race_mask=(raw[0x21] & 0x9f) | (0x100 if raw[0x20] & 0x80 else 0)
    if unknown_race_mask:
        raise Hold('HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED:'+
                   'BYTE3_ELF='+str(bool(raw[0x20] & 0x80))+','+
                   'BYTE4_RACES=0x%02X'%(raw[0x21] & 0x9f))
    # R38 observed STR12; other active stats and actual level were NOT
    # authenticated as item equip proof, so fail closed if item demands them.
    if u16(0x24)!=0 or raw[0x28]!=0 or any(raw[k]!=0 for k in (0x2a,0x2c,0x2e,0x30)) or u16(0x32)!=0:
        raise Hold('HOLD_ITM_OTHER_STATS_OR_LEVEL_UNVERIFIED')
    return dict(itemResref='STAF01',sourceSha256=ITM_SHA,
        observedClericUsabilityRestriction=False,
        observedTrueclassKitRestriction=False,
        raceAndAlignmentHeaderRestrictionsAbsent=True,
        observedUnrelatedMonkDruidRestrictionMask=unrelated_monk_druid_mask,
        itmUsabilityRaceByte3ElfRestricted=False,
        itmUsabilityRaceByte4RestrictedMask=0,
        headerMinStrength=5, priorLiveStrengthObserved=12,
        staticItemClassKitHeaderAllowed=True,
        currentSessionActorKitVerified=False,
        currentSessionEquippedEffectsVerified=False,
        engineCanEquipVerified=False)

def source_only(source:Path):
    raw=exact_source(source)
    return dict(schema=SCHEMA,status='EXACT_R39_BAF_PIN_PASS_NO_NATIVE',
        bafVariant=('EEEX_SESSION_SOURCE_ONLY' if source.name==SESSION_BAF_NAME else 'LEGACY_SOURCE_ONLY'),
        sourceSha256=digest(raw),sourceBytes=len(raw),
        reusesAlreadyNativeTestedV3Backend=True,nativeWeiDUCompileVerified=False,
        gameModified=False,installed=False,ordersSent=0,
        armAuthorized=False,dispatchAuthorized=False,liveXEquipTransferVerified=False)

def native_readonly(game:Path, source:Path, v3_helper:Path, backend_path:Path):
    raw=exact_source(source)
    source_sha,source_length,session=source_spec(source)
    v3=exact_v3_helper(v3_helper)
    v3.close_game_proof()
    if game.is_symlink() or not game.is_dir():
        raise Hold('HOLD_GAME_ROOT_NOT_SAFE')
    game=game.resolve(strict=True)
    # Item usability and native BAF syntax are INDEPENDENT read-only proofs.
    # A known usability restriction must never authorize equipment, but it
    # must also not hide an otherwise-safe native compile in TEMP.  Unknown
    # file/hash/resource drift still fails CLOSED before launching WeiDU.
    item_hold=None
    try:
        item_header=static_item_preflight(game)
    except Hold as exc:
        reason=str(exc)
        advisory_holds=('HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED',
                        'HOLD_ITM_ALIGNMENT_RESTRICTIONS_UNVERIFIED',
                        'HOLD_ITM_RESTRICTS_CLERIC',
                        'HOLD_ITM_RESTRICTS_TRUECLASS',
                        'HOLD_ITM_OTHER_STATS_OR_LEVEL_UNVERIFIED')
        if not any(reason.startswith(tag) for tag in advisory_holds):
            raise
        item_hold=reason
        item_header={'staticItemClassKitHeaderAllowed':False,
                     'engineCanEquipVerified':False,
                     'itemRestrictionHold':reason,
                     'sourceSha256':ITM_SHA}
    compiler=v3.pinned_compiler(game)
    backend=v3.load_backend(backend_path)
    with tempfile.TemporaryDirectory(prefix='BGXAI_R39_NATIVE_RO_') as folder:
        tmp=Path(folder).resolve(strict=True)
        if game==tmp or game in tmp.parents or tmp in game.parents:
            raise Hold('HOLD_R39_TEMP_OVERLAPS_GAME')
        candidate=tmp/'BGXW39.baf'  # 7-character resource name, temp only.
        candidate.write_bytes(raw)
        if digest(candidate.read_bytes())!=source_sha:
            raise Hold('HOLD_R39_TEMP_BAF_DRIFT')
        orig_check=backend.source_check
        orig_name=backend.TEMP_SOURCE_NAME
        try:
            def exact_check(path:Path,game_root:Path):
                verified=Path(path).resolve(strict=True)
                if verified!=candidate or verified==game_root or game_root in verified.parents:
                    raise backend.Hold('HOLD_R39_UNTRUSTED_SOURCE_LOCATION')
                content=backend.checked_file(Path(path),required=True)
                if content!=raw or digest(content)!=source_sha:
                    raise backend.Hold('HOLD_R39_SOURCE_CHANGED_DURING_COMPILE')
                return {'sha256':source_sha,'size':source_length,'blocks':3,'actionCount':14}
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
    item_ok=item_hold is None and item_header.get('staticItemClassKitHeaderAllowed') is True
    return dict(schema=SCHEMA,
        status=('R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL' if good and item_ok else
                'R39_NATIVE_EET_TEMP_COMPILE_PASS_ITEM_HOLD_NO_INSTALL' if good and not item_ok else
                'HOLD_R39_NATIVE_EET_COMPILER'),
        sourceSha256=source_sha,sourceBytes=source_length,
        bafVariant=('EEEX_SESSION_SOURCE_ONLY' if session else 'LEGACY_SOURCE_ONLY'),
        eeexLuaTriggerCompiledInNativeSource=bool(good and session),
        eeexLuaTriggerBoundAtRuntime=False,volatileSessionGateRuntimeVerified=False,
        nativeWeiDUCompileVerified=good,
        compiledBcsSha256=result.get('compiledSha256') if good else None,
        compilerSha256=result.get('compilerSha256'),
        nativeStatus=result.get('status'),
        watchedFilesChanged=result.get('watchedFilesChanged'),
        temporaryOutputRemoved=result.get('temporaryOutputRemoved'),
        wholeGameTreeChecked=False,
        itemHeaderCheck=item_header,
        itemStaticHeaderVerified=item_ok,
        itemRestrictionHold=item_hold,
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
