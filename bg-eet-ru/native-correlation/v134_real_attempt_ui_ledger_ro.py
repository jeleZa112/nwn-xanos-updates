"""BG_EET_RU V134: exact V133 evidence -> real UI outcome ledger and native callsite gate.

SOURCE ONLY. Never opens a game process, installs hooks, writes game files, or
infers weapon identity from actor name, timestamps, ordering or damage labels.

V129 proved Hit() AddMessage (0x39E84B) is conditional, so a future observed
render event must have independent per-attempt, caller and UI-row provenance.
0x398530 is a shared native callee seen in both Hit() and Damage(); its exact
semantic identity as the displayed attack result has NOT been proved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from typing import Any, Iterable

SCHEMA = 'BG_EET_RU_V134_REAL_UI_OUTCOME_LEDGER_AND_SHARED_CALLEE_GATE_RO'
PIN_ZIP = 'b1050448afe45b82193f1fc38f1db10f044a8615f200113ddb80009564172e35'
HIT_PATH = '19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
DAMAGE_PATH = '19_V68_COMBAT_CODE/functions/0038FBF0_00390F3C.bin'
HIT_SHA = '19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
DAMAGE_SHA = '59fa0cdbc7206698acd7bd49c7c68807a02d9318a001f13911e04d0d5e49723a'
HIT_RVA = 0x39DA50
DAMAGE_RVA = 0x38FBF0
SHARED_CALLEE = 0x398530
HIT_CALLS = (0x39E661, 0x39E754, 0x39E89E)
DAMAGE_CALLS = (0x39027B, 0x3902E2, 0x39056E, 0x3905C5,
                0x39071F, 0x390781, 0x390954, 0x3909A5)
COLOR = re.compile(r'\^0x[0-9a-fA-F]{8}|\^-')
RESULT = re.compile(r'\bd20\s*:\s*(\d+)\b.*\b(ПОПАДАНИЕ|ПРОМАХ)\b')
RESREF = re.compile(r'[A-Z0-9_]{1,8}\Z')


class Hold(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def rel32_calls_to(binary: bytes, base: int, target: int) -> tuple[int, ...]:
    """Candidate CALL rel32 byte sites, only trusted on exact pinned function SHA."""
    return tuple(base + pos for pos in range(len(binary)-4)
                 if binary[pos] == 0xE8
                 and base + pos + 5 + struct.unpack_from('<i', binary, pos + 1)[0] == target)


def audit_machine_code(hit: bytes, damage: bytes) -> dict:
    if not isinstance(hit, bytes) or sha(hit) != HIT_SHA or len(hit) != 0xF8C:
        raise Hold('PINNED_HIT_BINARY_DRIFT')
    if not isinstance(damage, bytes) or sha(damage) != DAMAGE_SHA or len(damage) != 0x134C:
        raise Hold('PINNED_DAMAGE_BINARY_DRIFT')
    hc = rel32_calls_to(hit, HIT_RVA, SHARED_CALLEE)
    dc = rel32_calls_to(damage, DAMAGE_RVA, SHARED_CALLEE)
    if hc != HIT_CALLS or dc != DAMAGE_CALLS:
        raise Hold('SHARED_CALLEE_CALLSITE_SET_CHANGED')
    # V129's actual control-flow counterexample is rechecked, not overridden.
    jne = hit[0x39E7B3-HIT_RVA:0x39E7B3-HIT_RVA+6]
    if jne != bytes.fromhex('0f859c000000'):
        raise Hold('V129_CONDITIONAL_BYPASS_DRIFT')
    jmp_dest = 0x39E7B3 + 6 + struct.unpack_from('<i', jne, 2)[0]
    if jmp_dest != 0x39E855 or jmp_dest <= 0x39E84B:
        raise Hold('V129_MESSAGE_BYPASS_TARGET_DRIFT')
    return {
        'status':'REAL_BINARY_CALLSITE_SETS_PINNED_SOURCE_ONLY',
        'shared_callee_rva':'0x398530',
        'hit_callsite_rvas':[f'0x{x:x}' for x in hc],
        'damage_callsite_rvas':[f'0x{x:x}' for x in dc],
        'hit_count':len(hc), 'damage_count':len(dc),
        'same_callee_is_unique_to_Hit':False,
        'same_callee_is_visible_UI_proven':False,
        'same_callee_always_called_on_hit_and_miss':False,
        'conditional_addmessage_bypass_reconfirmed':True,
        'correct_strategy':'USE_PINNED_NATIVE_CALLSITE_AND_VERIFIED_ATTEMPT_ID_NOT_CALLEE_ALONE',
    }


def visible_rows(samples: Any, declared_count: int) -> dict:
    if not isinstance(samples, list) or not isinstance(declared_count, int):
        raise Hold('VISIBLE_CAPTURE_SHAPE_HOLD')
    if len(samples) != declared_count or declared_count != 72:
        raise Hold('VISIBLE_CAPTURE_COUNT_DRIFT')
    outcome = []
    critical = []
    for ix, row in enumerate(samples, 1):
        if not isinstance(row, dict) or row.get('ui_row_number') != ix:
            raise Hold('VISIBLE_ROWS_ORDER_OR_ID_DRIFT')
        raw = row.get('rendered_text')
        if not isinstance(raw, str) or len(raw) > 5000:
            raise Hold('VISIBLE_ROW_MALFORMED')
        clean = COLOR.sub('', raw)
        if clean.lower().count('d20:') > 1:
            raise Hold('AMBIGUOUS_ROLL_ROW')
        if 'd20:' in clean.lower():
            m = RESULT.search(clean)
            if not m:
                raise Hold('D20_RESULT_MISSING_OR_UNKNOWN')
            actor = clean.split(':', 1)[0].strip()
            if not actor:
                raise Hold('ACTOR_TEXT_MISSING')
            outcome.append({
                'ui_row_number':ix, 'actor_display_name':actor,
                'roll_d20':int(m.group(1)),
                'result_text':m.group(2),
                'native_attempt_id':None, 'weapon_resref':None,
                'message_token':None, 'render_event_token':None,
                'row_to_weapon_join_verified':False,
            })
        if 'критическое попадание' in clean.casefold():
            critical.append(ix)
    return {
        'status':'REAL_RENDERED_UI_RESULTS_FOUND_NO_NATIVE_PROVENANCE',
        'captured_rows':declared_count,
        'outcome_rows':len(outcome),
        'hit_result_rows':sum(x['result_text']=='ПОПАДАНИЕ' for x in outcome),
        'miss_result_rows':sum(x['result_text']=='ПРОМАХ' for x in outcome),
        'separate_critical_message_rows':len(critical),
        'critical_row_numbers':critical,
        'important':'CRITICAL_MESSAGES_ARE_NOT_EXTRA_D20_OUTCOMES',
        'observations':outcome,
    }


def _positive(v: Any) -> bool:
    return type(v) is int and 0 < v <= 2**53 - 1


def _token(v: Any) -> bool:
    return type(v) is str and 0 < len(v) <= 128


def _candidate_fields(record: Any, names: tuple[str, ...]) -> bool:
    return isinstance(record, dict) and all(x in record and record[x] is not None for x in names)


def strict_render_join(attempt: dict, render_events: Iterable[dict], ui_rows: Iterable[dict]) -> dict:
    """Model future real event evidence; successful result is synthetic contract only.

    The call target and a nearby row can never establish the native origin.
    This function does not authenticate the provenance claims given as input.
    """
    hold = lambda reason: {'status':'HOLD','reason':reason,'runtime_proven':False,
                           'gameplay_verified':False,'game_files_written':0}
    identity=('session','thread_id','frame_id','attack_seq','attacker_id','target_id')
    if not _candidate_fields(attempt, identity+('weapon_resref','ability_index','outcome')):
        return hold('ATTEMPT_IDENTITY_MISSING')
    if not _token(attempt['session']) or not all(_positive(attempt[k]) for k in identity[1:]):
        return hold('ATTEMPT_IDENTITY_INVALID')
    if (type(attempt['weapon_resref']) is not str
            or RESREF.fullmatch(attempt['weapon_resref']) is None):
        return hold('WEAPON_RESREF_INVALID')
    if type(attempt['ability_index']) is not int or not 0 <= attempt['ability_index'] <= 65535:
        return hold('ABILITY_INDEX_INVALID')
    if attempt['outcome'] not in ('HIT','MISS'):
        return hold('OUTCOME_UNVERIFIED')
    flags=('native_hit_origin_verified','native_abi_verified',
           'weapon_at_actual_swing_verified','native_outcome_verified')
    if not _candidate_fields(attempt, flags) or any(attempt[k] is not True for k in flags):
        return hold('NATIVE_PROOF_MISSING')
    matches=[]
    for event in render_events:
        req=identity+('callsite','callee','render_token','native_callsite_verified',
                      'render_payload_origin_verified','outcome')
        if not _candidate_fields(event,req):
            continue
        if (all(event[k] == attempt[k] for k in identity)
                and type(event['callsite']) is int and event['callsite'] in HIT_CALLS
                and type(event['callee']) is int and event['callee'] == SHARED_CALLEE
                and _token(event['render_token'])
                and event['outcome'] == attempt['outcome']
                and event['native_callsite_verified'] is True
                and event['render_payload_origin_verified'] is True):
            matches.append(event)
    if len(matches)!=1:
        return hold('RENDER_EVENT_MISSING_OR_AMBIGUOUS')
    render=matches[0]
    rows=[]
    for row in ui_rows:
        req=('session','row_id','render_token','attack_seq','attacker_id','target_id',
             'row_class','is_visible','ui_origin_verified','outcome')
        if not _candidate_fields(row,req):
            continue
        if (row['session']==attempt['session']
            and row['attack_seq']==attempt['attack_seq']
            and row['attacker_id']==attempt['attacker_id']
            and row['target_id']==attempt['target_id']
            and row['render_token']==render['render_token']
            and row['row_class']=='ATTACK_OUTCOME'
            and row['outcome']==attempt['outcome']
            and _token(row['row_id'])
            and row['is_visible'] is True
            and row['ui_origin_verified'] is True):
            rows.append(row)
    if len(rows)!=1:
        return hold('UI_ROW_MISSING_OR_AMBIGUOUS')
    return {
        'status':'MODEL_CANDIDATE_NOT_RUNTIME_PROOF',
        'weapon_resref':attempt['weapon_resref'],
        'row_id':rows[0]['row_id'],
        'render_callsite_rva':f"0x{render['callsite']:x}",
        'runtime_proven':False,'gameplay_verified':False,'game_files_written':0,
    }


def audit_user_zip(archive: Path) -> dict:
    if archive.is_symlink() or not archive.is_file() or sha(archive.read_bytes())!=PIN_ZIP:
        raise Hold('USER_V133_ZIP_SHA_HOLD')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if z.testzip() is not None or len(names)!=len(set(names)):
            raise Hold('ZIP_CRC_OR_DUPLICATES_HOLD')
        v133=json.loads(z.read('66_V133_LIVE_HIT_INVENTORY.json'))
        v126=json.loads(z.read('63_V126_VISIBLE_ROW_OBSERVER.json'))
        v108=json.loads(z.read('54_V108_NATIVE_ITEM_RESREF_PILOT.json'))
        if (v133.get('status')!='LIVE_SITES_MATCH_OWNER_UNVERIFIED_RUNTIME_HOLD'
            or v133.get('game_files_written')!=0
            or v126.get('status')!='V126_CAPTURED_RENDERED_ROWS_UNCORRELATED'
            or v108.get('status')!='V108_INSTALLED_AWAITING_NATIVE_RESREF_CAPTURE'):
            raise Hold('HISTORICAL_REPORT_STATUS_UNEXPECTED')
        code=audit_machine_code(z.read(HIT_PATH),z.read(DAMAGE_PATH))
        ui=visible_rows(v126['captured']['samples'],v126['captured']['rows'])
        native=v108.get('console_evidence',{})
        if native.get('event_lines')!=2 or len(native.get('samples',[]))!=2:
            raise Hold('V108_EVENT_SHAPE_DRIFT')
    return {
        'schema':SCHEMA,
        'status':'REAL_EVIDENCE_PASS_SOURCE_ONLY_NO_ATTEMPT_ROW_JOIN',
        'source_zip_sha256':PIN_ZIP,
        'real_binary_callsite_matrix':code,
        'real_visible_ui':ui,
        'historical_native_weapon_event_count':2,
        'weapon_events_attached_to_any_ui_row':0,
        'firstcall_owner_verified':False,
        'native_abi_verified':False,
        'native_render_event_verified':False,
        'real_outcome_to_weapon_verified':False,
        'per_attempt_id_in_current_evidence':False,
        'game_files_written':0,
        'native_hooks_installed':False,
        'gameplay_verified':False,
        'next_engineering_gate':('CAPTURE_TYPED_PER_HIT_ATTEMPT_AND_DIRECT_RENDER_ORIGIN_WITH_'
                                 'STRICT_ATOMIC_CALLBACK_ROLLBACK_AND_EXPLICIT_AUTHORIZATION'),
    }


def main() -> int:
    p=argparse.ArgumentParser(description='V134 offline exact user ZIP source-only real attack ledger')
    p.add_argument('zip',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    report=audit_user_zip(args.zip)
    raw=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        if args.output.resolve()==args.zip.resolve():
            raise Hold('REFUSE_ZIP_OVERWRITE')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding='utf-8')
    print(report['status'])
    return 0

if __name__=='__main__':
    raise SystemExit(main())
