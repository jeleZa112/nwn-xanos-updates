#!/usr/bin/env python3
"""BGXAI source-only evidence join: native WeiDU + existing R27 + existing R28.

Does not install, write game files, issue orders, or reinterpret raw ITM/selected
APR as effective stats for alternate slots. Output is deliberately sanitized:
no local filenames, path, actor ID, action sequence, or private game logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

NATIVE_SCHEMA = 'BGXAI_WEAPON_NATIVE_COMPILE_RO_V1'
R27_SCHEMA = 'BGXAI_R27_REAL_LIVE_CAPTURE_VERDICT_V1'
R28_SCHEMA = 'BGXAI_R28_NATIVE_FROM_R27_RO_V1'
EXPECTED_BAF_SHA = '92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30'
EXPECTED_BAF_SIZE = 6763
EXPECTED_BCS_SHA_FROM_REAL_EET = '10426a2262e79553e861d464bdcf89d82a0fc91498dfb02c430c9b1fb02ef929'
MISSING_GATES = (
    'TRUE_ALT_SLOT_BUFF_AWARE_APR_AND_DAMAGE',
    'VERIFIED_LAUNCHER_AMMO_PAIR_AND_TARGET_EFFECTS',
    'INDEPENDENT_MANUAL_AND_EPS_ORDER_PROVENANCE',
    'STABLE_SAME_TARGET_AT_DISPATCH_BOUNDARY',
    'NATIVE_CURRENT_WEAPON_CANNOT_DAMAGE_TARGET_AT_EXECUTION',
    'USER_TYPED_GUARDED_INSTALL_AND_WEIDU_BACKUP',
    'GAMEPLAY_AB_TEST',
)

class EvidenceHold(ValueError):
    pass

def _exact_false(record: dict, keys: tuple[str, ...], prefix: str) -> None:
    for key in keys:
        if record.get(key) is not False:
            raise EvidenceHold(f'{prefix}_EXPECTED_EXPLICIT_FALSE:{key}')

def _exact_zero(record: dict, keys: tuple[str, ...], prefix: str) -> None:
    for key in keys:
        if type(record.get(key)) is not int or record[key] != 0:
            raise EvidenceHold(f'{prefix}_EXPECTED_ZERO:{key}')

def _sha(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

def join(native: dict, r27: dict, r28: dict) -> dict:
    if not all(isinstance(x, dict) for x in (native, r27, r28)):
        raise EvidenceHold('INPUT_NOT_OBJECT')
    if native.get('schema') != NATIVE_SCHEMA or native.get('status') != 'NATIVE_WEIDU_COMPILED_TEMP_ONLY':
        raise EvidenceHold('NATIVE_REAL_COMPILE_PASS_MISSING')
    source = native.get('source')
    if not isinstance(source, dict) or source.get('sha256') != EXPECTED_BAF_SHA or \
       type(source.get('size')) is not int or source['size'] != EXPECTED_BAF_SIZE or \
       type(source.get('blocks')) is not int or source['blocks'] != 8 or \
       type(source.get('actionCount')) is not int or source['actionCount'] != 8:
        raise EvidenceHold('NATIVE_COMPILED_BAF_SOURCE_MISMATCH')
    if native.get('nativeSymbolsAcceptedByCompiler') is not True or \
       type(native.get('exitCode')) is not int or native['exitCode'] != 0 or \
       native.get('watchedFilesChanged') is not False or \
       native.get('temporaryOutputRemoved') is not True or \
       native.get('compiledSha256') != EXPECTED_BCS_SHA_FROM_REAL_EET or \
       type(native.get('compiledSize')) is not int or native['compiledSize'] != 10550 or \
       not _sha(native.get('compilerSha256')):
        raise EvidenceHold('NATIVE_WEIDU_COMPILED_BYTES_UNVERIFIED')
    # The report confirms only selected watched files, never the entire tree.
    _exact_false(native, ('engineBehaviorVerified','wholeGameTreeChecked',
                          'gameplayLiveVerified','installPerformed',
                          'dispatchAuthorized','weaponSwitchAuthorized'), 'NATIVE')
    _exact_zero(native, ('ordersSent',), 'NATIVE')
    version = re.search(r'\bWeiDU version ([0-9]+)\b',native.get('compilerOutputTail',''))
    if not version or version.group(1) != '25100':
        raise EvidenceHold('NATIVE_WEIDU_COMPILER_VERSION_NOT_IN_REPORT')
    if r27.get('schema') != R27_SCHEMA or \
       r27.get('R27LiveStatus') != 'PASS_REGISTERED_AND_EMITTED_SELECTED_STATE' or \
       type(r27.get('r27ActionCallbacks')) is not int or r27['r27ActionCallbacks'] != 24 or \
       r27.get('r27SequencesContinuousFrom1') is not True or \
       type(r27.get('r27ErrorsObserved')) is not int or r27['r27ErrorsObserved'] != 0 or \
       not _sha(r27.get('rawLogSha256')):
        raise EvidenceHold('R27_REAL_GAME_CAPTURE_NOT_CONFIRMED')
    comp = r27.get('comparators')
    if not isinstance(comp,dict) or comp.get('matchedR27_R2_R4') != 24 or comp.get('mismatches') != []:
        raise EvidenceHold('R27_R2_R4_EVIDENCE_MISMATCH')
    if r27.get('gameModifiedByAnalysis') is not False or \
       r27.get('allR27OrdersSentZero') is not True or \
       r27.get('allR27LocalsWrittenZero') is not True or \
       r27.get('allR27DispatchAuthorizedFalse') is not True or \
       r27.get('allR27WeaponSwitchAuthorizedFalse') is not True or \
       r27.get('allR27RemainingProofFlagsFalse') is not True:
        raise EvidenceHold('R27_SAFETY_FLAGS_NOT_CONFIRMED')
    if r28.get('schema') != R28_SCHEMA or \
       r28.get('status') != 'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW' or \
       r28.get('captureSha256') != r27['rawLogSha256']:
        raise EvidenceHold('R28_AND_R27_CAPTURE_NOT_SAME_SESSION')
    if r28.get('liveR27Evidence',{}).get('sourceSha256') != r27['rawLogSha256'] or \
       r28.get('liveR27Evidence',{}).get('r27ConfirmedCallbacks') != 24:
        raise EvidenceHold('R28_R27_LIVE_EVIDENCE_MISMATCH')
    audit = r28.get('nativeAudit')
    if not isinstance(audit,dict) or audit.get('schema') != 'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY' or \
       audit.get('status') != 'ITM_NATIVE_ALL_ITEMS_RAW_READ' or \
       audit.get('sourceKind') != 'CURRENT_GAME' or \
       not isinstance(audit.get('items'),dict) or \
       set(audit['items']) != {'BOW05','AROW01','STAF01','SW1H04'} or \
       audit.get('missingItemsOrLinkedSpells') != []:
        raise EvidenceHold('R28_NATIVE_RAW_ITEMS_UNVERIFIED')
    slots = r27.get('selectedSlots')
    if not isinstance(slots,list) or len(slots)!=2 or {v.get('slot'): v.get('observations') for v in slots if isinstance(v,dict)} != {12:22,35:2}:
        raise EvidenceHold('R27_SELECTED_SLOTS_NOT_MATCHING_REAL_TRACE')
    if r28.get('liveR27Evidence',{}).get('observedRawItemResrefs') != ['AROW01','BOW05','STAF01','SW1H04']:
        raise EvidenceHold('R28_R27_RESOURCE_LIST_MISMATCH')
    _exact_false(r28, ('gameModified','gameplayActionOriginVerified',
                       'manualAndEPSQueueVerified','effectiveAlternateAPRVerified',
                       'launcherAmmoPairVerified','weaponSwitchAuthorized',
                       'dispatchAuthorized'), 'R28')
    _exact_zero(r28, ('ordersSent',), 'R28')
    _exact_false(audit, ('aprPerSlotVerified','currentCharacterBuffsVerified',
                         'launcherAmmoPairVerified','fullWeaponEffectsVerified',
                         'manualAndEPSQueueVerified','targetImmuneOrResistantVerified',
                         'dispatchAuthorized',
                         'weaponSwitchAuthorized','gameModified'), 'R28_NATIVE')
    return {
        'schema':'BGXAI_NATIVE_EVIDENCE_JOIN_V1',
        'status':'NATIVE_BAF_COMPILED_R27_R28_LINKED_NO_DISPATCH',
        'verdict':'SOURCE_AND_NATIVE_COMPILE_PASS_RUNTIME_PRODUCER_NOT_READY',
        'nativeWeiDU':{'realEetCompilePass':True,'compilerVersionFromLog':version.group(1),
                       'compiledBcsSha256':native['compiledSha256'],
                       'compiledBcsSize':native['compiledSize'],
                       'sourceBafSha256':source['sha256'],'blocks':8,
                       'watchedFilesUnchanged':True,'wholeTreeNotProven':True},
        'R27':{'gameCallbacksVerified':24,'selectedOnly':True,
               'observedSelectedWeaponKinds':['BOW_OR_AMMO','SWORD'],
               'alternateEffectiveStatsProven':False},
        'R28':{'nativeItemCountVerified':4,'currentGameResourcesRead':True,
               'buffAwareAlternateAprProven':False,'launcherAmmoPairProven':False,
               'manualEpsQueueOriginProven':False},
        'missingGates':list(MISSING_GATES),
        'installPerformed':False,'dispatchAuthorized':False,
        'weaponSwitchAuthorized':False,'ordersSent':0,
        'nextSafeTask':'FIND_AUDITED_ENGINE_ALT_STATS_AND_EPS_MANUAL_ORDER_ORIGIN',
        'noRepeat':'R27_R28_AND_NATIVE_167_ALREADY_PASSED',
    }

def load_json(path:Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 200_000:
        raise EvidenceHold('INPUT_FILE_MISSING_OR_UNSAFE')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--r27',type=Path,required=True)
    parser.add_argument('--r28',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        report=join(load_json(args.native),load_json(args.r27),load_json(args.r28))
    except (EvidenceHold,ValueError,OSError,json.JSONDecodeError) as ex:
        report={'schema':'BGXAI_NATIVE_EVIDENCE_JOIN_V1','status':'EVIDENCE_HOLD',
                'reason':str(ex),'installPerformed':False,
                'dispatchAuthorized':False,'weaponSwitchAuthorized':False,'ordersSent':0}
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['status']=='NATIVE_BAF_COMPILED_R27_R28_LINKED_NO_DISPATCH' else 3

if __name__=='__main__':
    raise SystemExit(main())