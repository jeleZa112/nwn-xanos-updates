"""BG_EET_RU / STRICT same-Hit-to-UI-row provenance gate (SOURCE ONLY).

A purely read-only validator for future captured events. It never modifies text,
Native CMessage, UI, EXE, EEex or the game. A successful synthetic candidate is
NOT proof that any native hook, Win64 ABI or combat-log row works in the game.

The upstream V4 Lua model establishes (thread, frame) and a function callsite,
but the V125 Windows report still lacks the actual event-to-visible-row join.
This module specifies a fail-closed join contract, and audits V125 evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable
from zipfile import ZipFile

PINNED_HIT_CALLSITE = 0x39E84B
EXPECTED_TYPE = "ATTACK_ROLL"
RESREF = re.compile(r"[A-Z0-9_]{1,8}\Z")

@dataclass(frozen=True)
class JoinResult:
    status: str
    reason: str
    weapon_resref: str | None = None
    launcher_resref: str | None = None
    ammo_resref: str | None = None
    row_id: str | None = None
    game_files_written: int = 0
    runtime_proven: bool = False
    gameplay_verified: bool = False
    source_only: bool = True


def _tagged_record(record: Any, required: tuple[str, ...]) -> bool:
    """Present / primitive-only; never trust default-filled or guessed keys."""
    return isinstance(record, dict) and all(k in record and record[k] is not None for k in required)


def _valid_key(value: Any) -> bool:
    return type(value) is str and 0 < len(value) <= 100


def _positive_int(value: Any) -> bool:
    return type(value) is int and 0 < value <= (2**53 - 1)


def _resref(value: Any, *, optional: bool = False) -> bool:
    return (value is None and optional) or (type(value) is str and RESREF.fullmatch(value) is not None)


def join_exact(attack: dict, messages: Iterable[dict], rows: Iterable[dict]) -> JoinResult:
    """Return a *source-only candidate* iff one full provenance chain exists.

    No inference from timestamps, message order, vtable, weapon slot, item
    names, or a closest adjacent UI row is ever permitted. The engine-specific
    evidence fields must be independently established by a future native pilot.
    """
    required = ('session', 'thread_id', 'frame_id', 'attack_seq',
                'attacker_id', 'target_id', 'weapon_resref', 'result',
                'message_ptr', 'message_callsite', 'message_token')
    if not _tagged_record(attack, required):
        return JoinResult('HOLD', 'ATTACK_IDENTITY_FIELDS_MISSING')
    for k in ('session', 'message_token'):
        if not _valid_key(attack[k]):
            return JoinResult('HOLD', 'ATTACK_IDENTITY_INVALID')
    for k in ('thread_id', 'frame_id', 'attack_seq', 'attacker_id', 'target_id', 'message_ptr'):
        if not _positive_int(attack[k]):
            return JoinResult('HOLD', 'ATTACK_IDENTITY_INVALID')
    if attack['result'] not in ('HIT', 'MISS'):
        return JoinResult('HOLD', 'ATTACK_OUTCOME_UNVERIFIED')
    if attack['message_callsite'] != PINNED_HIT_CALLSITE:
        return JoinResult('HOLD', 'WRONG_HIT_FUNCTION_CALLSITE')
    if not _resref(attack['weapon_resref']):
        return JoinResult('HOLD', 'WEAPON_RESREF_INVALID')
    for k in ('launcher_resref', 'ammo_resref'):
        if not _resref(attack.get(k), optional=True):
            return JoinResult('HOLD', 'AMMO_OR_LAUNCHER_INVALID')
    if not _tagged_record(attack, ('native_hit_origin_verified', 'native_abi_verified',
                                   'original_weapon_at_swing_verified')):
        return JoinResult('HOLD', 'NATIVE_PROVENANCE_UNVERIFIED')
    if any(attack[k] is not True for k in ('native_hit_origin_verified',
                                         'native_abi_verified',
                                         'original_weapon_at_swing_verified')):
        return JoinResult('HOLD', 'NATIVE_PROVENANCE_UNVERIFIED')

    matches=[]
    for msg in messages:
        if not _tagged_record(msg, ('session','thread_id','frame_id','attack_seq',
                                    'message_ptr','message_token','message_type',
                                    'callsite','proven_native_message')):
            continue
        identity=('session','thread_id','frame_id','attack_seq','message_ptr','message_token')
        if (all(msg[k] == attack[k] for k in identity)
            and msg['message_type'] == EXPECTED_TYPE
            and msg['callsite'] == PINNED_HIT_CALLSITE
            and msg['proven_native_message'] is True):
            matches.append(msg)
    if len(matches) != 1:
        return JoinResult('HOLD', 'MESSAGE_MISSING_OR_AMBIGUOUS')

    good=[]
    for row in rows:
        if not _tagged_record(row, ('session','row_id','message_ptr','message_token',
                                    'attack_seq','attacker_id','target_id',
                                    'row_class','is_visible','ui_source_proven')):
            continue
        same=('session','message_ptr','message_token','attack_seq','attacker_id','target_id')
        if (all(row[k] == attack[k] for k in same)
            and row['row_class'] == EXPECTED_TYPE
            and row['is_visible'] is True
            and row['ui_source_proven'] is True
            and _valid_key(row['row_id'])):
            good.append(row)
    if len(good) != 1:
        return JoinResult('HOLD', 'VISIBLE_ROW_MISSING_OR_AMBIGUOUS')

    # This validator itself cannot authenticate the claims in captured input:
    # external ABI + UI-observer proof remains necessary before a game install.
    return JoinResult('SOURCE_ONLY_CANDIDATE', 'EXACT_SYNTHETIC_CHAIN_NOT_RUNTIME_PROOF',
                      weapon_resref=attack['weapon_resref'],
                      launcher_resref=attack.get('launcher_resref'),
                      ammo_resref=attack.get('ammo_resref'), row_id=good[0]['row_id'])


def audit_v125_archive(archive: Path) -> dict:
    """Inspect exact user evidence, preserve all original bytes and statuses."""
    with ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP_CRC_HOLD')
        names=z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('ZIP_DUPLICATE_HOLD')
        required=('62_V124_ONE_RUN_BOT.json','56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json',
                  '61_V122_LIVE_HIT_READONLY.json','54_V108_NATIVE_ITEM_RESREF_PILOT.json')
        if any(x not in names for x in required):
            raise ValueError('V125_EVIDENCE_MISSING')
        bot,source,mem,v108=[json.loads(z.read(q)) for q in required]
        if bot.get('updater_version') != 125 or bot.get('stage_count') != 14:
            raise ValueError('NOT_USER_V125_COMPLETE_BATCH')
        gates=source.get('gates',{})
        evidence={k: gates.get(k) for k in (
            'v108_has_attacker_id','v108_has_target_id','v108_has_attack_sequence',
            'v108_has_combatlog_row_id','display_row_hook_present_in_this_probe')}
        all_actual=all(v is True for v in evidence.values())
        if all_actual:
            status='INSUFFICIENT_EVIDENCE_FOR_RUNTIME_JOIN'
            reason='V125_BOOLEAN_GATES_ALONE_DO_NOT_IDENTIFY_SAME_HIT_AND_ROW'
        else:
            status='HOLD_NO_PER_ATTACK_TO_VISIBLE_ROW_JOIN'
            reason='MISSING_ACTOR_SEQUENCE_OR_ROW_IDENTITY'
        return {
            'schema':'BG_EET_RU_STRICT_HIT_ROW_GATE_SOURCE_ONLY_V1',
            'status':status, 'reason':reason,
            'actual_v125_14_stages':True,
            'v108_status':v108.get('status'),
            'memory_status':mem.get('status'),
            'memory_sites_verified':mem.get('checks',{}),
            'v125_identity_gate':evidence,
            'requested_next_evidence':['Native per-Hit attacker, target, attack sequence and item RESREF',
               'Native exact CMessage pointer/token at proven Hit() AddMessage callsite',
               'A visible combatLog row with same message token, class and sequence',
               'Win64 ABI, JIT owner, unwind and rollback proof'],
            'original_combat_log_unchanged':True,
            'no_weapon_inference_from_adjacency':True,
            'game_files_written':0,
            'native_hooks_installed':False,
            'runtime_proven':False,
            'gameplay_verified':False,
        }


def main(argv=None):
    parser=argparse.ArgumentParser(description='Source-only V125 evidence and strict identity join audit')
    parser.add_argument('zip',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    report=audit_v125_archive(args.zip)
    body=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output:
        if args.output.resolve() == args.zip.resolve():
            parser.error('OUTPUT_CANNOT_OVERWRITE_ZIP')
        args.output.write_text(body+'\n',encoding='utf-8')
    print(body)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
