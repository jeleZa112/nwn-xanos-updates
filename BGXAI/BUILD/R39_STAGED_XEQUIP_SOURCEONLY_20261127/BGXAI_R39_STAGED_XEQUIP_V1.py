#!/usr/bin/env python3
"""R39 source-only: generate time-bounded, locally armed Jagan XEquipItem pilot BAF.

Does not install, arm, modify a game, or prove that the engine transfer succeeds.
Requires a separately authenticated *session-only* actor-local armer, native EET
compile, class+kit+ITM usability and manual/EPS origin checks before deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = 'BGXAI_R39_XEQUIP_STAGED_SOURCE_ONLY_V1'
MANIFEST_SCHEMA = 'BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3'
# Real saved-game snapshot, not an actor session identity proof.
REQUIRED = {
    'schema': MANIFEST_SCHEMA,
    'gamSha256': '7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c',
    'partyIndexSnapshot': 1,
    'savedActorName': '*GCLERIC',
    'savedClassRaw': 3,
    'sourceResref': 'STAF01',
    'sourceSlot': 20,
    'targetSlot': 35,
    'sourceFlags': 1,
    'sourceCharges': [0, 0, 0],
    'sourceExpiry': 0,
}
ARM, TAG, TRY = 'BGXW3ARM', 'BGXW3TAG', 'BGXW3TRY'
STAGE, WARM, DEADLINE = 'BGXW3QST', 'BGXW3QTM', 'BGXW3MAX'
BLOCKED = ('Stop(', 'ClearActions(', 'FillSlot(', 'CreateItem(',
           'SelectWeaponAbility(', 'Attack(', 'MoveToPoint(',
           'SetGlobal("BGXW3ARM","LOCALS",1)')


class Hold(ValueError):
    pass


def verified_manifest(m):
    # Reject extra keys (including invented actor IDs or user approval), booleans
    # masquerading as integers, stale slot assumptions and altered item fields.
    if type(m) is not dict or set(m) != set(REQUIRED):
        raise Hold('HOLD_MANIFEST_SCHEMA_OR_KEYS')
    for key, expected in REQUIRED.items():
        got = m[key]
        if type(got) is not type(expected) or got != expected:
            raise Hold('HOLD_MANIFEST_' + key.upper())
    return m


def witness(m):
    verified_manifest(m)
    payload = json.dumps(m, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':'))
    digest = hashlib.sha256(('BGXW3-V1\0' + payload).encode('ascii')).hexdigest()
    return (int(digest[:8], 16) & 0x7fffffff) or 1


def _base(tag):
    return [
        f'Global("{ARM}","LOCALS",1)',
        f'Global("{TAG}","LOCALS",{tag})',
        f'Global("{TRY}","LOCALS",0)',
        'InParty(Myself)',
        'InPartySlot(Myself,1)',
        'Name("*GCLERIC",Myself)',  # exact saved actor script name, fail closed
        'Class(Myself,CLERIC)',  # live class gate, not a kit proof
        'CheckStatGT(Myself,4,STR)',  # live strength >= 5 for STAF01
        '!HasItemSlot(Myself,SLOT_SHIELD)',  # 2h staff must not displace shield
        'ActionListEmpty()',
        'CombatCounter(0)',
        '!See([EVILCUTOFF])',
        '!GlobalTimerNotExpired("MO_SpellCast","LOCALS")',
        'ModalState(NONE)',
        '!StateCheck(Myself,STATE_PANIC)',
        '!StateCheck(Myself,STATE_HELPLESS)',
        'CheckItemSlot(Myself,"STAF01",SLOT_MISC5)',
        '!HasItemSlot(Myself,SLOT_WEAPON0)',
    ]


def _block(triggers, actions):
    return ('IF\n' + ''.join('  '+t+'\n' for t in triggers) +
            'THEN\n  RESPONSE #100\n' +
            ''.join('    '+a+'\n' for a in actions) + 'END\n')


def render(m):
    verified_manifest(m)
    tag = witness(m)
    ready = _base(tag)
    # Ordering matters: expired local arm MUST fail closed before transfer.
    # A timer provides a bounded cooldown, NOT uninterrupted-idle proof.
    abort = _block([
        f'Global("{ARM}","LOCALS",1)',
        f'Global("{TAG}","LOCALS",{tag})',
        f'Global("{STAGE}","LOCALS",1)',
        f'GlobalTimerExpired("{DEADLINE}","LOCALS")',
        'ActionListEmpty()', 'CombatCounter(0)',
    ], [
        f'SetGlobal("{ARM}","LOCALS",3)',
        f'SetGlobal("{TAG}","LOCALS",0)',
        f'SetGlobal("{STAGE}","LOCALS",3)',
        'Continue()',  # let EPS keep scanning after housekeeping abort
    ])
    equip = _block(ready + [
        f'Global("{STAGE}","LOCALS",1)',
        f'GlobalTimerExpired("{WARM}","LOCALS")',
        f'GlobalTimerNotExpired("{DEADLINE}","LOCALS")',
    ], [
        f'SetGlobal("{ARM}","LOCALS",2)',
        f'SetGlobal("{TRY}","LOCALS",1)',
        f'SetGlobal("{TAG}","LOCALS",0)',
        f'SetGlobal("{STAGE}","LOCALS",2)',
        'XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)',
    ])
    warm = _block(ready + [f'Global("{STAGE}","LOCALS",0)'], [
        f'SetGlobal("{STAGE}","LOCALS",1)',
        f'SetGlobalTimer("{WARM}","LOCALS",ONE_ROUND)',
        f'SetGlobalTimer("{DEADLINE}","LOCALS",TWO_ROUNDS)',
        'Continue()',  # maintain EPS priority after staging only
    ])
    baf = ('// BGXAI R39 SOURCE ONLY; NOT INSTALLED; NO AUTO-ARM.\n'
           '// Stage-1 requires independently authorized actor-local LOCALS.\n'
           '// ONE_ROUND cooldown + TWO_ROUNDS deadline are not idle/session proof.\n'
           '// Actor ID, item usability and manual/EPS origin must be verified\n'
           '// by a future independent session-bound armer before deployment.\n' +
           abort + '\n' + equip + '\n' + warm)
    if baf.count('XEquipItem(') != 1 or any(x in baf for x in BLOCKED):
        raise Hold('HOLD_UNSAFE_BAF_ACTIONS')
    if any(f'"{s}","GLOBAL"' in baf for s in (ARM, TAG, TRY, STAGE, WARM, DEADLINE)):
        raise Hold('HOLD_NONLOCAL_PILOT_VARIABLE')
    return baf


def render_session_gate(m):
    """Optional R39 source-only candidate; ORIGINAL verified BAF remains intact.

    EEex v1.1.7 provides trigger 0x410E EEex_LuaTrigger(S:Chunk*).
    It passes EEex_LuaTrigger_Object into a separately approved volatile
    in-memory R39 armer. A saved actor-local ARM alone can NEVER equip.
    EEex presence / trigger compilation and runtime are not proven here.
    """
    baf = render(m)
    gate = '  EEex_LuaTrigger("return BGXW3_EEexSessionGate()")\n'
    # Gate only warmup and equip; abort is safe housekeeping (Continue).
    equip = '  GlobalTimerExpired("BGXW3QTM","LOCALS")\n'
    warm = '  Global("BGXW3QST","LOCALS",0)\nTHEN'
    if baf.count(equip) != 1 or baf.count(warm) != 1:
        raise Hold('HOLD_SESSION_GATE_INJECTION_TARGET_MISSING')
    baf = baf.replace(equip, gate + equip, 1)
    baf = baf.replace(warm, '  Global("BGXW3QST","LOCALS",0)\n' + gate + 'THEN', 1)
    if baf.count('EEex_LuaTrigger(') != 2 or baf.count('XEquipItem(') != 1:
        raise Hold('HOLD_SESSION_GATE_NOT_EXACTLY_TWICE')
    return baf


def audit(m):
    baf = render(m)
    return {
        'schema': SCHEMA, 'status': 'SOURCE_ONLY_STAGED_CANDIDATE_NOT_READY_TO_ARM',
        'partyIndexSnapshot': 1, 'sourceSlot': 20, 'targetSlot': 35,
        'itemResref': 'STAF01', 'actorLocalTag': witness(m),
        'bafSha256': hashlib.sha256(baf.encode('ascii')).hexdigest(),
        'bafBytes': len(baf.encode('ascii')),
        'warmupId': 'ONE_ROUND', 'deadlineId': 'TWO_ROUNDS',
        'abortBeforeEquip': True, 'exactlyOneXEquipCommand': True,
        'housekeepingContinuesToEPS': True,
        'selfArmingPresent': False, 'sessionBoundArmerImplemented': False,
        'currentSessionMatchesGamVerified': False,
        'kitItmUsabilityVerified': False, 'manualEpsOriginVerified': False,
        'engineQuiescenceVerified': False, 'nativeActiveBafCompileVerified': False,
        'manualTypedApproval': False, 'gameModified': False,
        'installed': False, 'ordersSent': 0, 'dispatchAuthorized': False,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True, type=Path)
    ap.add_argument('--out-baf', type=Path, help='Write only an inert candidate BAF')
    ns = ap.parse_args(argv)
    try:
        if ns.manifest.is_symlink() or not ns.manifest.is_file() or ns.manifest.stat().st_size>16384:
            raise Hold('HOLD_MISSING_OR_OVERSIZED_MANIFEST')
        m = json.loads(ns.manifest.read_text(encoding='utf-8'))
        a, baf = audit(m), render(m)
        if ns.out_baf:
            if ns.out_baf.is_symlink():
                raise Hold('HOLD_OUTPUT_SYMLINK')
            ns.out_baf.write_text(baf, encoding='ascii', newline='\n')
        print(json.dumps(a, indent=2, sort_keys=True))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, Hold) as e:
        print(json.dumps({'schema':SCHEMA,'status':'HOLD_NO_GAME_ACTION',
                          'reason':str(e) if isinstance(e,Hold) else 'HOLD_IO_OR_JSON',
                          'installed':False,'ordersSent':0,
                          'dispatchAuthorized':False}))
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
