"""BGXAI R16 offline alternate-slot facts/gaps from real R2 + older native R3.

NO game access, hooks, dispatch, installation, commands, or source changes.
A previous resource snapshot is NOT proof of current runtime equip/usability.
Selected APR from R13/R4/R1 is NEVER projected onto unselected slots.
"""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from apr_key_decoder_ro import decode_source_apr_key

MAX_FILE = 2_000_000
MAX_LINES = 20_000
MAX_SNAPSHOTS = 512
R3_FROZEN_SHA = '7ae7555f81b14a784e7866472f14483b02c2d6b707ab6169225e8fec32507304'
R2_MARKER = '[BGXW2] '
SLOTS_WEAPON = (35, 36, 37, 38)
SLOTS_AMMO = (11, 12, 13, 14)
SLOTS = SLOTS_WEAPON + SLOTS_AMMO + (9,)
REF = re.compile(r'[A-Z0-9_#-]{1,8}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')


def hold(reason: str, **rest: Any) -> dict:
    return {'status': 'HOLD', 'reason': reason, 'executable': False,
            'dispatchAuthorized': False, 'weaponSwitchAuthorized': False, **rest}


def read_file(path: Path) -> tuple[bytes, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError('FILE_MISSING_OR_SYMLINK')
    before = path.stat()
    if not 1 <= before.st_size <= MAX_FILE:
        raise ValueError('FILE_SIZE_UNSUPPORTED')
    buf = path.read_bytes()
    after = path.stat()
    if (len(buf) != before.st_size or after.st_size != before.st_size or
            before.st_mtime_ns != after.st_mtime_ns):
        raise ValueError('FILE_CHANGED_DURING_READ')
    return buf, hashlib.sha256(buf).hexdigest()


def parse_r2(log: str) -> list[dict]:
    if len(log.splitlines()) > MAX_LINES:
        raise ValueError('TOO_MANY_LOG_LINES')
    out = []
    for n, line in enumerate(log.splitlines(), 1):
        if 'INFO: LUA:' not in line or R2_MARKER not in line:
            continue
        raw = line.partition(R2_MARKER)[2].strip()
        if not raw.startswith('{'):
            continue
        try:
            event = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            raise ValueError('INVALID_R2_JSON') from None
        if isinstance(event, dict) and event.get('type') == 'SLOTS':
            out.append({'line': n, 'data': event})
            if len(out) > MAX_SNAPSHOTS:
                raise ValueError('TOO_MANY_R2_SNAPSHOTS')
    return out


def _slot_map(r2: dict) -> dict[int, dict]:
    w, a, h = r2.get('quickWeapons'), r2.get('quivers'), r2.get('offhand')
    if not isinstance(w, list) or not isinstance(a, list) or len(w) != 4 or len(a) != 4:
        raise ValueError('R2_SLOT_ARRAY_INCOMPLETE')
    if not isinstance(h, dict):
        raise ValueError('R2_OFFHAND_INCOMPLETE')
    result = {}
    for item, index in zip(w + a + [h], SLOTS):
        if not isinstance(item, dict) or item.get('index') != index:
            raise ValueError('R2_SLOT_INDEX_CONFLICT')
        access, ref = item.get('access'), item.get('resrefRaw')
        if access == 'NULL':
            if ref is not None:
                raise ValueError('R2_NULL_HAS_RESREF')
        elif access == 'OBJECT_RETURNED_UNVERIFIED':
            if not isinstance(ref, str) or not REF.fullmatch(ref):
                raise ValueError('R2_ITEM_RESREF_INVALID')
        else:
            raise ValueError('R2_SLOT_UNREADABLE')
        if index in SLOTS_AMMO:
            quantity = item.get('useCount1Raw')
            if quantity is not None and (type(quantity) is not int or not 0 <= quantity <= 65535):
                raise ValueError('R2_AMMO_COUNT_INVALID')
        if any(item.get(key) is not False for key in ('identityVerified','usableVerified','ammoVerified')):
            raise ValueError('R2_UNEXPECTED_NATIVE_VERIFICATION_FLAGS')
        result[index] = item
    return result


def _static(r3: dict, ref: str) -> dict:
    all_items = r3['items']
    rec = all_items[ref]
    if rec.get('resource') != ref or not isinstance(rec.get('item'), dict):
        raise ValueError('R3_RESOURCE_REMAP')
    prov, item = rec.get('provenance'), rec['item']
    if not isinstance(prov, dict) or prov.get('origin') not in ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE') or not isinstance(prov.get('sha256'),str) or not SHA.fullmatch(prov['sha256']):
        raise ValueError('R3_RESOURCE_PROVENANCE_INVALID')
    if item.get('schema') != 'BGXAI_ITM_RAW_V1' or item.get('rawOnly') is not True or item.get('characterCanEquipVerified') is not False or item.get('activeBuffsVerified') is not False or item.get('targetImmunityVerified') is not False:
        raise ValueError('R3_RAW_ITEM_GUARD_INVALID')
    abilities = item.get('abilities')
    if not isinstance(abilities,list) or len(abilities)>10:
        raise ValueError('R3_ABILITIES_UNREADABLE')
    summary = []
    for ab in abilities:
        if not isinstance(ab,dict):
            raise ValueError('R3_ABILITY_NOT_OBJECT')
        props=('abilityIndex','attackTypeRaw','rangeRaw','speedRaw','damageTypeRaw','thac0BonusRaw','launcherRequiredRaw','diceCountRaw','diceSidesRaw','damageBonusRaw')
        if any(type(ab.get(k)) is not int for k in props):
            raise ValueError('R3_ABILITY_FIELDS_INVALID')
        summary.append({k:ab[k] for k in props})
        summary[-1]['effectsOpcodesRaw'] = [fx.get('opcodeRaw') for fx in ab.get('effects',[]) if isinstance(fx,dict)]
        summary[-1]['damageMeanBeforeEffects'] = ab.get('baseDamageMeanBeforeEffects')
    eqfx = item.get('equippedEffects')
    if not isinstance(eqfx,list):
        raise ValueError('R3_EQUIPPED_EFFECTS_UNREADABLE')
    rate_override=[{'opcodeRaw':x['opcodeRaw'],'valueRaw':x.get('parameter1Raw'),'modeRaw':x.get('parameter2Raw')} for x in eqfx if isinstance(x,dict) and x.get('opcodeRaw')==1]
    return {'resource':ref,'sourceKind':'PRIOR_CURRENT_GAME_STATIC_RESOURCE_UNREVALIDATED',
            'originAtR3Audit':prov['origin'],'resourceSha256AtR3Audit':prov['sha256'],
            'itemTypeRaw':item.get('itemTypeRaw'),'minStrengthRaw':item.get('minStrengthRaw'),
            'proficiencyIdRaw':item.get('proficiencyIdRaw'),'enchantmentRaw':item.get('enchantmentRaw'),
            'twoHandedFlagRaw':item.get('twoHandedFlagRaw'),'abilities':summary,
            'equippedEffectsOpcodeRaw':[x.get('opcodeRaw') for x in eqfx if isinstance(x,dict)],
            'aprEquippedOverrideRaw':rate_override,
            'hasOnHitScriptEffectCandidate':any(any(x==146 for x in ab['effectsOpcodesRaw']) for ab in summary),
            'currentResourceHashVerified':False,'abilityUsableNowVerified':False,
            'effectiveDamageVerified':False,'fullEffectsVerified':False}


def analyze(log_text: str, log_sha: str, r3: dict, r3_sha: str, selected: dict) -> dict:
    raw_only = {'readOnly':True,'gameModified':False,'executable':False,'dispatchAuthorized':False,
                'weaponSwitchAuthorized':False,'currentGameResourceRevalidated':False,
                'fullLoadoutScoringAuthorized':False,'effectiveAlternateSlotAPRVerified':False,
                'launcherAmmoAssociationVerified':False,'manualEpsQueueVerified':False}
    base={'schema':'BGXAI_ALTERNATE_SLOT_STATIC_EVIDENCE_RO_V1',**raw_only,'input':{
        'r3Sha256':r3_sha,'logSha256':log_sha,'selectedLogSha256':selected.get('inputSha256')}}
    if not SHA.fullmatch(log_sha) or r3_sha != R3_FROZEN_SHA or not SHA.fullmatch(r3_sha):
        return {**base,**hold('R3_OR_LOG_UNRECOGNIZED_PROVENANCE')}
    if (r3.get('schema')!='BGXAI_WEAPON_NATIVE_ITM_R3_READONLY' or
        r3.get('status')!='ITM_NATIVE_ALL_ITEMS_RAW_READ' or r3.get('sourceKind')!='CURRENT_GAME' or
        r3.get('gameModified') is not False or r3.get('weaponSwitchAuthorized') is not False or
        r3.get('launcherAmmoPairVerified') is not False or
        r3.get('aprPerSlotVerified') is not False or
        r3.get('missingItemsOrLinkedSpells') != [] or
        any(r3.get(flag) is not False for flag in
            ('targetImmuneOrResistantVerified','currentCharacterBuffsVerified',
             'proficiencyAlreadyAppliedVerified','fullWeaponEffectsVerified',
             'manualAndEPSQueueVerified'))):
        return {**base,**hold('R3_SOURCE_FLAGS_UNEXPECTED')}
    if (selected.get('schema')!='BGXAI_SELECTED_SLOT_EVIDENCE_BRIDGE_RO_V1' or
        selected.get('inputSha256')!=log_sha or selected.get('status')!='CURRENT_SELECTED_EVIDENCE_CAPTURED_RO' or
        selected.get('currentSelectionOnly') is not True or selected.get('weaponSwitchAuthorized') is not False or
        selected.get('alternateSlotAprVerified') is not False or selected.get('matchedByNativeEventId') is not False):
        return {**base,**hold('SELECTED_OBSERVATIONS_UNTRUSTED_OR_DIFFERENT_LOG')}
    parsed = parse_r2(log_text)
    if not parsed:
        return {**base,**hold('NO_R2_GEAR_SNAPSHOTS')}
    actor = parsed[0]['data'].get('actor')
    party = parsed[0]['data'].get('partyIndex')
    if not (type(actor) is int and 1<=actor<=2147483647 and type(party) is int and 0<=party<=5):
        return {**base,**hold('R2_ACTOR_INVALID')}
    rows=[]
    inventory_first=None
    for index,e in enumerate(parsed,1):
        d=e['data']
        if (d.get('schema')!='BGXAI_WEAPON_SLOTS_RAW_R2' or
            d.get('actor') != actor or d.get('partyIndex')!=party or
            d.get('seq')!=index or d.get('itemIdentityVerified') is not False or
            d.get('perSlotAPRVerified') is not False or
            d.get('switchAuthorized') is not False):
            return {**base,**hold('R2_SESSION_ACTOR_SEQUENCE_OR_FLAGS_CONFLICT')}
        slots=_slot_map(d)
        refs=tuple(slots[i].get('resrefRaw') for i in SLOTS)
        if inventory_first is None:
            inventory_first=refs
        elif refs!=inventory_first:
            return {**base,**hold('GEAR_IDENTITY_CHANGED_DURING_SESSION')}
        rows.append({'seq':index,'line':e['line'],'selectedSlot':d.get('selectedWeaponRaw'),'actionRaw':d.get('actionRaw'),
                     'rawAmmoCount':{i:slots[i].get('useCount1Raw') for i in SLOTS_AMMO},'slots':slots})
    observed = selected.get('observations')
    if not isinstance(observed,list) or not 1<=len(observed)<=64:
        return {**base,**hold('SELECTED_OBSERVATIONS_EMPTY')}
    samples={i:[] for i in SLOTS}
    for o in observed:
        if (not isinstance(o,dict) or o.get('status')!='CURRENT_SELECTED_EVIDENCE_CANDIDATE_RO' or
            o.get('actor')!=actor or o.get('weaponSwitchAuthorized') is not False or
            o.get('pairingAuthenticated') is not False or o.get('alternateSlotAprVerified') is not False or
            o.get('selectedSlot') not in SLOTS or
            type(o.get('line')) is not int or type(o.get('r13Sequence')) is not int or
            not 1 <= o['r13Sequence'] <= 64 or
            type(o.get('action')) is not int):
            return {**base,**hold('SELECTED_OBSERVATION_CONTRACT_INVALID')}
        candidates=[r for r in rows if r['line']>o['line'] and r['line']<=o['line']+8]
        s=o['selectedSlot']
        valid=[r for r in candidates if r['selectedSlot']==s and r['actionRaw']==o.get('action')]
        if len(valid)!=1:
            return {**base,**hold('SELECTED_AND_R2_SNAPSHOT_NOT_UNIQUELY_ALIGNED')}
        if o.get('sourceItemRefRaw')!=valid[0]['slots'][s].get('resrefRaw'):
            return {**base,**hold('SELECTED_ITEM_REF_MISMATCH')}
        key,apr=o.get('sourceAprKey'),o.get('sourceAprValue')
        if (type(key) is not int or not isinstance(apr,str) or
            decode_source_apr_key(key).state != 'SOURCE_KEY_DECODED_RO' or
            apr != str(decode_source_apr_key(key).source_value)):
            return {**base,**hold('SELECTED_APR_SAMPLE_INVALID')}
        samples[s].append({'r13Sequence':o['r13Sequence'],'key':key,'value':apr,
                           'sourceEventLine':o['line'],'notEffectiveAlternateSlotAPR':True})
    firstslots=rows[0]['slots']
    candidates=[]
    resources=r3.get('items')
    if not isinstance(resources,dict):
        return {**base,**hold('R3_ITEMS_MISSING')}
    for slot in SLOTS:
        raw=firstslots[slot]
        ref=raw.get('resrefRaw')
        if ref is None:
            candidates.append({'slot':slot,'status':'EMPTY_AT_OBSERVED_SESSION','resrefRaw':None,
                               'selectedAprSamples':[],'usableNowVerified':False,'priorityEligible':False})
            continue
        if ref not in resources or ref not in r3.get('requestedItems',[]):
            return {**base,**hold('R3_NO_MATCHING_RESOURCE',resref=ref)}
        item=_static(r3,ref)
        barriers=['R2_RESREF_IDENTITY_UNVERIFIED','R3_RESOURCE_PREVIOUS_SESSION_NOT_RECHECKED',
                  'CHARACTER_USABILITY_NOT_VERIFIED','ABILITY_SELECTION_NOT_NATIVE_AUTHENTICATED',
                  'PROFICIENCY_KIT_AND_BUFF_EFFECTS_NOT_COMPLETE','EFFECTIVE_THAC0_DAMAGE_AND_HIT_CHANCE_NOT_VERIFIED',
                  'TARGET_IMMUNITY_AND_ITEM_MAGIC_NOT_FULLY_VERIFIED','MANUAL_EPS_ACTION_QUEUE_NOT_VERIFIED']
        if slot in SLOTS_AMMO:
            barriers.append('LAUNCHER_AMMO_PAIR_NOT_ENGINE_VERIFIED')
        if slot in SLOTS_WEAPON and any(x['attackTypeRaw']==4 for x in item['abilities']):
            barriers.append('LAUNCHER_AMMO_PAIR_NOT_ENGINE_VERIFIED')
        if item['twoHandedFlagRaw'] and firstslots[9].get('resrefRaw'):
            barriers.append('TWO_HANDED_WITH_SHIELD_ACTIVE_STATE_UNKNOWN')
        if item['hasOnHitScriptEffectCandidate']:
            barriers.append('ON_HIT_EFFECT_SPECIAL_AND_BREAKAGE_NOT_PRICED')
        if item['aprEquippedOverrideRaw']:
            barriers.append('EQUIPPED_APR_EFFECT_FLAT_OR_ADDITIVE_NOT_REAPPLIED')
        if not samples[slot]:
            barriers.append('NO_CURRENT_SELECTED_APR_SAMPLE_FOR_THIS_SLOT')
        candidates.append({'slot':slot,'status':'STATIC_ITEM_FIELDS_FROM_PRIOR_GAME_RO',
                           'resrefRaw':ref,'staticItem':item,'selectedAprSamples':samples[slot],
                           'blockedBy':barriers,'usableNowVerified':False,'priorityEligible':False,
                           'alternateSlotAprVerified':False})
    # Count increases signal a state reset, not proof a reload occurred.
    breaks=[]
    for before,after in zip(rows,rows[1:]):
        for slot in SLOTS_AMMO:
            old,new=before['rawAmmoCount'][slot],after['rawAmmoCount'][slot]
            if type(old) is int and type(new) is int and new>old:
                breaks.append({'afterSeq':before['seq'],'beforeSeq':after['seq'],
                               'ammoSlot':slot,'oldCount':old,'newCount':new,
                               'meaning':'AMMO_RESTOCK_OR_RELOAD_CANDIDATE_UNVERIFIED'})
    return {**base,'status':'PRIOR_STATIC_ITEM_FACTS_AND_CURRENT_SELECTION_AUDITED_RO',
            'actorId':actor,'partyIndex':party,'snapshots':len(rows),
            'previousR3ActorId':r3.get('r2SnapshotSummary',{}).get('lastActor'),
            'previousR3SnapshotIsSameActorAndSession':False,
            'resourceAgeStatus':'PRIOR_GAME_SNAPSHOT_NOT_REVERIFIED_NOW',
            'candidateCount':sum(x['resrefRaw'] is not None for x in candidates),
            'slots':candidates,'ammoResetCandidates':breaks,
            'selectedObservationCount':len(observed),'unverified':['SLOT_STATS_NEVER_PROJECT_FROM_SELECTED',
               'SOURCE_R3_SCHEMA_BOUND_TO_PRIOR_ACTOR_AND_SESSION','ITEM_EFFECTS_AND_IMMUNITIES_NOT_SOLVED',
               'NO_WEAPON_RANKING_OR_DISPATCH'],**raw_only}


def run(log: Path, r3: Path, selected: Path) -> dict:
    try:
        raw_log, sha_log = read_file(log)
        raw_r3, sha_r3 = read_file(r3)
        raw_sel, _ = read_file(selected)
        return analyze(raw_log.decode('utf-8-sig'),sha_log,json.loads(raw_r3),sha_r3,json.loads(raw_sel))
    except (ValueError,UnicodeError,OSError,json.JSONDecodeError) as exc:
        return hold('INPUT_REJECTED',detail=type(exc).__name__)


def main() -> int:
    ap=argparse.ArgumentParser(description='BGXAI offline alternate-slot static evidence audit (no game)')
    ap.add_argument('--log',type=Path,required=True)
    ap.add_argument('--r3',type=Path,required=True)
    ap.add_argument('--selected',type=Path,required=True)
    arg=ap.parse_args()
    output=run(arg.log,arg.r3,arg.selected)
    print(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if output.get('status')=='PRIOR_STATIC_ITEM_FACTS_AND_CURRENT_SELECTION_AUDITED_RO' else 2

if __name__=='__main__':
    raise SystemExit(main())
