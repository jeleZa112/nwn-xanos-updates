#!/usr/bin/env python3
"""BGXAI V3 SOURCE-ONLY local-armed one-shot candidate; no game or save changes.

Does not arm the actor, modify BCS, execute actions, or certify runtime identity.
Only a future, independently verified identity-bound armer may set actor LOCALS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from verify_candidate_ro import Hold, propose

SCHEMA = 'BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3'
ARM = 'BGXW3ARM'  # 8 chars, actor-local
TAG = 'BGXW3TAG'  # actor-local session/item witness, not authentication by itself
TRY = 'BGXW3TRY'  # actor-local one-time counter
SLOT_NAMES = {s: f'SLOT_MISC{s - 15}' for s in range(18,34)}
WEAPON_NAMES = {s: f'SLOT_WEAPON{s - 35}' for s in range(35,39)}
REQUIRED = {'schema', 'gamSha256', 'partyIndexSnapshot', 'savedActorName',
            'savedClassRaw', 'sourceResref', 'sourceSlot', 'targetSlot',
            'sourceFlags', 'sourceCharges', 'sourceExpiry'}


def _int(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def validate_manifest(m):
    if type(m) is not dict or set(m) != REQUIRED or m.get('schema') != SCHEMA:
        raise Hold('HOLD_EXACT_MANIFEST_SCHEMA')
    if not isinstance(m['gamSha256'], str) or len(m['gamSha256']) != 64 or any(
            c not in '0123456789abcdef' for c in m['gamSha256']):
        raise Hold('HOLD_UNTRUSTED_GAM_DIGEST')
    if not _int(m['partyIndexSnapshot'], 1, 5):
        raise Hold('HOLD_PC_OR_INVALID_PARTY_INDEX')
    if m['savedActorName'] != '*GCLERIC' or m['savedClassRaw'] != 3:
        raise Hold('HOLD_WRONG_SAVED_NPC_OR_CLASS')
    if (m['sourceResref'] != 'STAF01' or
        not _int(m['sourceSlot'],20,20) or not _int(m['targetSlot'],35,35)):
        raise Hold('HOLD_DIFFERENT_SOURCE_OR_TARGET')
    if not _int(m['sourceFlags'], 0, 0xFFFFFFFF) or not _int(m['sourceExpiry'],0,65535):
        raise Hold('HOLD_INVALID_SAVED_ITEM_FIELDS')
    v = m['sourceCharges']
    if type(v) is not list or len(v) != 3 or not all(_int(q, 0, 65535) for q in v):
        raise Hold('HOLD_INVALID_CHARGES')
    return m


def verify_against_gam(m, gam):
    validate_manifest(m)
    if type(gam) is not bytes or hashlib.sha256(gam).hexdigest() != m['gamSha256']:
        raise Hold('HOLD_GAM_SHA_MISMATCH')
    evidence = propose(gam)  # real GAM + embedded CRE parse, refuses unknown version
    matches = []
    for c in evidence['candidates']:
        if (c['actor']['partyIndexSnapshot'] == m['partyIndexSnapshot'] and
            c['actor']['internalNameFromGAM'] == m['savedActorName'] and
            c['actor']['classRaw'] == m['savedClassRaw'] and
            c['source']['resref'] == m['sourceResref'] and
            c['source']['slot'] == m['sourceSlot'] and
            c['source']['flags'] == m['sourceFlags'] and
            c['source']['charges'] == m['sourceCharges'] and
            c['source']['expiry'] == m['sourceExpiry'] and
            c['target']['slot'] == m['targetSlot'] and
            c['target']['statusInSave'] == 'EMPTY' and
            c['actorHasUniqueResrefInSavedTopLevelSlots'] is True):
            matches.append(c)
    if len(matches) != 1:
        raise Hold('HOLD_NO_UNIQUE_VERIFIED_SAVED_CANDIDATE')
    return matches[0]


def witness(m):
    """Deterministic correlation marker, not a cryptographic game identity proof."""
    validate_manifest(m)
    canonical=json.dumps(m, sort_keys=True, ensure_ascii=True, separators=(',',':'))
    n=int(hashlib.sha256(('BGXW3-V1\0'+canonical).encode('ascii')).hexdigest()[:8],16)
    return (n & 0x7fffffff) or 1


def render(m):
    validate_manifest(m)
    src = SLOT_NAMES[m['sourceSlot']]
    dst = WEAPON_NAMES[m['targetSlot']]
    tag = witness(m)
    baf = f'''// BGXAI V3 SOURCE ONLY. INERT UNTIL EXACT ACTOR LOCALS ARE INDEPENDENTLY ARMED.
// This source does NOT install, arm, prove runtime identity or authorize execution.
IF
  Global("{ARM}","LOCALS",1)
  Global("{TAG}","LOCALS",{tag})
  Global("{TRY}","LOCALS",0)
  InParty(Myself)
  InPartySlot(Myself,{m['partyIndexSnapshot']})
  ActionListEmpty()
  CombatCounter(0)
  !GlobalTimerNotExpired("MO_SpellCast","LOCALS")
  ModalState(NONE)
  !StateCheck(Myself,STATE_PANIC)
  !StateCheck(Myself,STATE_HELPLESS)
  CheckItemSlot(Myself,"{m['sourceResref']}",{src})
  !HasItemSlot(Myself,{dst})
THEN
  RESPONSE #100
    SetGlobal("{ARM}","LOCALS",2)
    SetGlobal("{TRY}","LOCALS",1)
    SetGlobal("{TAG}","LOCALS",0)
    XEquipItem("{m['sourceResref']}",Myself,{dst},EQUIP)
END
'''
    for k in (ARM,TAG,TRY):
        if f'"{k}","GLOBAL"' in baf:
            raise Hold('HOLD_SHARED_GLOBAL_ARMING')
    for forbidden in ('Stop(', 'ClearActions(', 'FillSlot(', 'CreateItem(',
                      'SelectWeaponAbility(', 'Attack(', 'SetGlobal("BGXW3ARM","LOCALS",1)'):
        if forbidden in baf:
            raise Hold('HOLD_DISRUPTIVE_OR_SELF_ARM_ACTION')
    if baf.count('XEquipItem(') != 1:
        raise Hold('HOLD_MULTI_TRANSFER')
    return baf


def build(m, gam):
    candidate=verify_against_gam(m,gam)
    baf=render(m)
    sha=hashlib.sha256(baf.encode('ascii')).hexdigest()
    return {
        'schema':'BGXAI_XEQUIP_LOCAL_ARM_BUILD_AUDIT_V3',
        'status':'SOURCE_ONLY_LOCKED_RUNTIME_ACTOR_ID_AND_ARMER_NOT_PROVEN',
        'gamSha256Verified':True,
        'savedCandidateVerified':True,
        'partyIndexSnapshot':m['partyIndexSnapshot'],
        'sourceResref':candidate['source']['resref'],
        'sourceSlot':candidate['source']['slot'],
        'targetSlot':candidate['target']['slot'],
        'localWitnessValue':witness(m),
        'bafSha256':sha,
        'bafBytes':len(baf.encode('ascii')),
        'scope':'ACTOR_LOCALS_NOT_GLOBAL',
        'automaticArmingCodePresent':False,
        'actorIdInSaveKnown':False,
        'runtimeActorIdentityVerified':False,
        'currentSessionMatchesSaveVerified':False,
        'classKitItmUsabilityVerified':False,
        'safeActionBoundaryVerified':False,
        'manualEpsOriginVerified':False,
        'eetNativeActiveBafCompileVerified':False,
        'legacyBcsBytePreservationVerified':False,
        'externalBackupVerified':False,
        'installAuthorizationReceived':False,
        'engineMoveVerified':False,
        'dispatchAuthorized':False,
        'installed':False,
        'ordersSent':0,
        'gameModified':False,
    }, baf


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gam', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    a=p.parse_args(argv)
    try:
        if a.gam.is_symlink() or not a.gam.is_file():
            raise Hold('HOLD_MISSING_REGULAR_GAM')
        if a.gam.stat().st_size>50_000_000:raise Hold('HOLD_TOO_LARGE_GAM')
        if a.manifest.is_symlink() or not a.manifest.is_file():
            raise Hold('HOLD_MISSING_REGULAR_MANIFEST')
        if a.manifest.stat().st_size>16384:raise Hold('HOLD_TOO_LARGE_MANIFEST')
        m=json.loads(a.manifest.read_text(encoding='utf-8'))
        audit,baf=build(m,a.gam.read_bytes())
        print(json.dumps({'audit':audit,'sourceOnlyBaf':baf},ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError,Hold,UnicodeError) as e:
        print(json.dumps({'status':'HOLD_NO_GAME_ACTION','reason':str(e),
                          'installed':False,'ordersSent':0,'dispatchAuthorized':False}))
        return 3

if __name__=='__main__':raise SystemExit(main())