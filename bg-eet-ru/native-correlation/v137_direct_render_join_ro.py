"""BG_EET_RU V137 — direct, per-attempt render provenance gate. SOURCE ONLY.

The original CGameSprite::Hit at 0x39E7B3 has a path that bypasses the
conditional 0x39E84B AddMessage call. Therefore an individual attack-to-visible
row connection MUST NOT require that call. This gate accepts future snapshots
that carry a separately observed *direct* render token; it NEVER creates a token
from timestamps, adjacency, actor names, RESREFs or original V126 text.

This module performs no game I/O (except reading the supplied ZIP), no hooks,
no process-memory I/O, no Windows APIs and no rewriting of existing sources.
Any synthetic test result is SOURCE_ONLY_CANDIDATE, not gameplay verification.
"""
from __future__ import annotations
import hashlib
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA = 'BG_EET_RU_V137_DIRECT_RENDER_TOKEN_GATE_SOURCE_ONLY'
GAME_EXE_SHA = 'fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580'
HIT_BYTES_SHA = '19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
HIT_BYTES_ZIP_NAME = '19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
HIT_START_RVA = 0x39DA50
LATEST_ZIP_SHA = '8a9596b461887e41c859704b264d49fcbc2bb0d6a86269f164095878db41686d'
ENTRY_RVA = 0x39DA6F
EXIT_RVA = 0x39E99B
CONDITIONAL_MESSAGE_RVA = 0x39E84B
BYPASS_BRANCH_RVA = 0x39E7B3
BYPASS_TARGET_RVA = 0x39E855
MAX_ID = (1 << 53) - 1
RESREF = re.compile(r'[A-Z0-9_]{1,8}\Z')
ROW_TOKEN = re.compile(r'[A-Z0-9_-]{12,96}\Z')

@dataclass(frozen=True)
class Verdict:
    status: str
    reason: str
    session: str | None = None
    attack_seq: int | None = None
    row_id: str | None = None
    weapon_resref: str | None = None
    launcher_resref: str | None = None
    ammo_resref: str | None = None
    visible_outcome: str | None = None
    source_only: bool = True
    live_identity_verified: bool = False
    native_abi_verified: bool = False
    runtime_unwind_verified: bool = False
    gameplay_verified: bool = False
    game_files_written: int = 0
    native_hooks_installed: bool = False


def hold(reason: str) -> Verdict:
    return Verdict('HOLD', reason)


def _int(v: Any) -> bool:
    return type(v) is int and 1 <= v <= MAX_ID


def _u16(v: Any) -> bool:
    return type(v) is int and 0 <= v <= 65535


def _byte(v: Any) -> bool:
    return type(v) is int and 0 <= v <= 255


def _resref(v: Any, optional=False) -> bool:
    return (v is None and optional) or (type(v) is str and RESREF.fullmatch(v) is not None)


def _token(v: Any) -> bool:
    return type(v) is str and ROW_TOKEN.fullmatch(v) is not None


def _session(v: Any) -> bool:
    return type(v) is str and 4 <= len(v) <= 64 and bool(re.fullmatch(r'[A-Z0-9_-]+', v))


def _id(v: Any) -> bool:
    return type(v) is str and 1 <= len(v) <= 96 and bool(re.fullmatch(r'[A-Za-z0-9_-]+', v))


def join_attempt_direct(attempt: Any, render_rows: Iterable[dict], all_attempts: Iterable[dict] = ()) -> Verdict:
    """Fails closed unless one direct token matches one exact, immutable attempt.

    Note: flags supplied by a future capture are *not independently audited* by
    this pure validator. Thus even a positive result stays SOURCE_ONLY_CANDIDATE.
    The native bridge and render-origin validation must be separately proven.
    """
    if not isinstance(attempt, dict) or not isinstance(render_rows, (tuple, list)) or not isinstance(all_attempts, (tuple, list)):
        return hold('EVENT_SCHEMA_INVALID')
    needed = ('session','thread_id','frame_id','attack_seq','attacker_id','target_id',
              'entry_rva','exit_rva','raw_return','weapon_resref','ability_index',
              'direct_render_token','native_origin_verified','entry_exit_pair_verified',
              'item_copied_in_same_invocation','render_token_emitted_by_same_invocation',
              'return_mapping_independently_calibrated','win64_abi_proven',
              'runtime_unwind_proven')
    if any(k not in attempt for k in needed):
        return hold('ATTEMPT_REQUIRED_FIELDS_MISSING')
    if not _session(attempt['session']) or any(not _int(attempt[k]) for k in
            ('thread_id','frame_id','attack_seq','attacker_id','target_id')):
        return hold('ATTEMPT_IDENTITY_INVALID')
    if (type(attempt['entry_rva']) is not int or attempt['entry_rva']!=ENTRY_RVA or
        type(attempt['exit_rva']) is not int or attempt['exit_rva']!=EXIT_RVA or
        not _byte(attempt['raw_return']) or not _u16(attempt['ability_index'])):
        return hold('ATTEMPT_NATIVE_SITES_OR_RAW_RESULT_INVALID')
    if not _resref(attempt['weapon_resref']) or any(not _resref(attempt.get(k),True)
                                    for k in ('launcher_resref','ammo_resref')):
        return hold('ATTEMPT_RESREF_INVALID_OR_UNCOPIED')
    if not _token(attempt['direct_render_token']):
        return hold('DIRECT_TOKEN_NOT_FROM_RENDER_BRIDGE')
    if any(attempt[k] is not True for k in
          ('native_origin_verified','entry_exit_pair_verified',
           'item_copied_in_same_invocation','render_token_emitted_by_same_invocation',
           'return_mapping_independently_calibrated','win64_abi_proven','runtime_unwind_proven')):
        return hold('NATIVE_BRIDGE_PROVENANCE_NOT_ESTABLISHED')
    if attempt.get('conditional_message_seen') is True:
        # The message may exist, but its existence is never a join key.
        pass
    if attempt.get('outcome') not in ('HIT','MISS'):
        return hold('HIT_MISS_SEMANTICS_NOT_CALIBRATED')
    if not _id(attempt.get('item_snapshot_id','')):
        return hold('IMMUTABLE_ITEM_SNAPSHOT_ID_MISSING')
    if attempt.get('game_exe_sha256') != GAME_EXE_SHA:
        return hold('GAME_EXE_BUILD_MISMATCH')
    key=('session','thread_id','frame_id','attack_seq')
    same_attempt_key=lambda x: isinstance(x,dict) and all(x.get(k)==attempt[k] for k in key)
    if sum(same_attempt_key(x) for x in all_attempts)!=1:
        return hold('ATTEMPT_KEY_MISSING_OR_DUPLICATED')
    if sum(isinstance(x,dict) and x.get('session')==attempt['session'] and
           x.get('direct_render_token')==attempt['direct_render_token'] for x in all_attempts)!=1:
        return hold('TOKEN_COLLISION_IN_ATTEMPT_LEDGER')
    # Forbid reuse of seq with another frame and any other snapshot of this key.
    if sum(isinstance(x,dict) and x.get('session')==attempt['session'] and
           x.get('attack_seq')==attempt['attack_seq'] for x in all_attempts)!=1:
        return hold('ATTACK_SEQUENCE_COLLISION')
    matched=[]
    for row in render_rows:
        if not isinstance(row,dict):continue
        if row.get('session')==attempt['session'] and row.get('direct_render_token')==attempt['direct_render_token']:
            matched.append(row)
    if len(matched)!=1:
        return hold('VISIBLE_RENDER_TOKEN_MISSING_OR_AMBIGUOUS')
    row=matched[0]
    if any(k not in row for k in ('row_id','row_class','visible','renderer_origin_verified','attack_seq',
                                  'attacker_id','target_id','outcome','frame_id','thread_id')):
        return hold('VISIBLE_ROW_PROVENANCE_FIELDS_MISSING')
    if (not _id(row['row_id']) or row['row_class']!='ATTACK_ROLL' or
        row['visible'] is not True or row['renderer_origin_verified'] is not True):
        return hold('ROW_NOT_VERIFIED_AS_VISIBLE_ATTACK_ROLL')
    if any(row[k]!=attempt[k] or type(row[k]) is not int for k in
           ('attack_seq','thread_id','frame_id','attacker_id','target_id')):
        return hold('VISIBLE_ROW_WRONG_ATTACK_IDENTITY')
    if row['outcome']!=attempt['outcome']:
        return hold('VISIBLE_ROW_OUTCOME_DISAGREES')
    # Protection against a second row taking the same attack_seq by another token.
    if sum(isinstance(x,dict) and x.get('session')==attempt['session'] and
           x.get('attack_seq')==attempt['attack_seq'] for x in render_rows)!=1:
        return hold('MULTIPLE_RENDER_ROWS_FOR_ONE_ATTEMPT')
    if sum(isinstance(x,dict) and x.get('session')==attempt['session'] and
           x.get('row_id')==row['row_id'] for x in render_rows)!=1:
        return hold('RENDER_ROW_ID_COLLISION')
    # Even this positive result is a *simulation of future instrumentation*.
    return Verdict('SOURCE_ONLY_CANDIDATE','DIRECT_RENDER_TOKEN_AND_EXACT_ATTEMPT_CONSISTENT',
                   attempt['session'],attempt['attack_seq'],row['row_id'],
                   attempt['weapon_resref'],attempt.get('launcher_resref'),
                   attempt.get('ammo_resref'),attempt['outcome'])


def audit_user_zip(path: Path) -> dict:
    """Checks REAL existing V126+V108+V136 evidence, never invents missing tokens."""
    report={'schema':SCHEMA,'status':'REAL_USER_CAPTURE_DIRECT_JOIN_HOLD',
            'game_files_written':0,'native_hooks_installed':False,'gameplay_verified':False,
            'native_abi_verified':False,'runtime_unwind_verified':False,
            'direct_render_token_verified':False,'same_attempt_to_visible_row_verified':False}
    if path.is_symlink() or not path.is_file():
        report['reason']='SOURCE_ZIP_MISSING_OR_SYMLINK';return report
    blob=path.read_bytes()
    report['user_zip_sha256']=hashlib.sha256(blob).hexdigest()
    if report['user_zip_sha256'] != LATEST_ZIP_SHA:
        report['reason']='V136_LIVE_ZIP_PIN_DRIFT';return report
    try:
        with zipfile.ZipFile(path) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or z.testzip() is not None:
                report['reason']='USER_ZIP_DUPLICATES_OR_CRC';return report
            v108=json.loads(z.read('54_V108_NATIVE_ITEM_RESREF_PILOT.json'))
            v126=json.loads(z.read('63_V126_VISIBLE_ROW_OBSERVER.json'))
            v136=json.loads(z.read('67_V136_LIVE_JIT_TARGET_RO.json'))
            hit=z.read(HIT_BYTES_ZIP_NAME)
        if hashlib.sha256(hit).hexdigest()!=HIT_BYTES_SHA:
            report['reason']='PINNED_HIT_FUNCTION_SHA_MISMATCH';return report
        branch=hit[BYPASS_BRANCH_RVA-HIT_START_RVA:BYPASS_BRANCH_RVA-HIT_START_RVA+6]
        call=hit[CONDITIONAL_MESSAGE_RVA-HIT_START_RVA:CONDITIONAL_MESSAGE_RVA-HIT_START_RVA+5]
        if (branch!=bytes.fromhex('0f859c000000') or call!=bytes.fromhex('e81064e6ff')
            or BYPASS_BRANCH_RVA+6+int.from_bytes(branch[2:],'little',signed=True)!=BYPASS_TARGET_RVA
            or BYPASS_TARGET_RVA<=CONDITIONAL_MESSAGE_RVA):
            report['reason']='CONDITIONAL_MESSAGE_BYPASS_ANCHOR_MISMATCH';return report
        if (v136.get('status')!='V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD'
            or v136.get('entry_exit_original_bytes_verified') is not True
            or v136.get('firstcall_owner_verified') is not False
            or v136.get('game_files_written')!=0):
            report['reason']='V136_RUNTIME_EVIDENCE_UNEXPECTED';return report
        if v126.get('status')!='V126_CAPTURED_RENDERED_ROWS_UNCORRELATED' or v126.get('captured',{}).get('rows')!=72:
            report['reason']='V126_UI_EVIDENCE_UNEXPECTED';return report
        if v108.get('console_evidence',{}).get('event_lines')!=2:
            report['reason']='V108_WEAPON_EVIDENCE_UNEXPECTED';return report
        report.update(reason='NO_DIRECT_RENDER_TOKEN_OR_PER_ATTEMPT_NATIVE_PROOF_IN_EXISTING_CAPTURE',
                      live_v136_memory_observed=True, v126_visible_row_count=72,
                      v108_independent_resref_event_count=2,
                      v108_resref_examples=['AROW01','BOW05'],
                      conditional_message_call_is_not_a_universal_event_source=True)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile,UnicodeDecodeError) as exc:
        report['reason']='ARCHIVE_READ_OR_EVIDENCE_ERROR_'+type(exc).__name__
    return report


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description='V137 per-attempt direct render-token source-only gate')
    p.add_argument('evidence_zip',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args(argv)
    result=audit_user_zip(args.evidence_zip)
    if args.output:
        dest=args.output.expanduser().resolve()
        if args.output.is_symlink() or dest==args.evidence_zip.resolve():
            raise ValueError('UNSAFE_OUTPUT_PATH')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(result['status']+' '+result.get('reason',''))
    return 0 if result['status'].endswith('_HOLD') else 2

if __name__=='__main__':raise SystemExit(main())
