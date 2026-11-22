#!/usr/bin/env python3
"""BGXAI READ-ONLY local evidence pipeline, not a Windows updater or game install.

Consumes one session's already captured InfinityLoader console log and the
previously audited native ITM R3 report. This file has NO connection to the
live game, doesn't issue orders or modify game files. Actual selected APR is
historical evidence, NEVER a projection for another quickslot or a future buff.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import re
from pathlib import Path

SCHEMA = 'BGXAI_WEAPON_R4_R3_LIVE_EVIDENCE_V1'
R4_SCHEMA = 'BGXAI_WEAPON_ACTIVE_R4'
R2_SCHEMA = 'BGXAI_WEAPON_SLOTS_RAW_R2'
# Exact native-game resource audit already accepted for this source-only trial.
# Changed game resources need a new audit, not a silently reused stale snapshot.
PINNED_R3_REPORT_SHA256 = '7ae7555f81b14a784e7866472f14483b02c2d6b707ab6169225e8fec32507304'
PINNED_R4_SOURCE_CONTRACT_SHA256 = '2b618df53566b75f651ae75ce737496e4b24cb18fd754be7eb7c245ccfbbcc40'
RAW_APR = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
           6: .5, 7: 1.5, 8: 2.5, 9: 3.5, 10: 4.5}
PROF_R4 = {89: 'm_nProficiencyBastardSword', 90: 'm_nProficiencyLongSword',
           91: 'm_nProficiencyShortSword', 92: 'm_nProficiencyAxe',
           93: 'm_nProficiencyTwoHandedSword', 94: 'm_nProficiencyKatana',
           95: 'm_nProficiencyScimitarWakisashiNinjaTo', 96: 'm_nProficiencyDagger',
           97: 'm_nProficiencyWarhammer', 98: 'm_nProficiencySpear',
           99: 'm_nProficiencyHalberd', 100: 'm_nProficiencyFlailMorningStar',
           101: 'm_nProficiencyMace', 102: 'm_nProficiencyQuarterStaff',
           103: 'm_nProficiencyCrossbow', 104: 'm_nProficiencyLongBow',
           105: 'm_nProficiencyShortBow', 106: 'm_nProficiencyDart',
           107: 'm_nProficiencySling', 108: 'm_nProficiencyBlackjack',
           109: 'm_nProficiencyGun', 110: 'm_nProficiencyMartialArts',
           111: 'm_nProficiency2Handed', 112: 'm_nProficiencySwordAndShield',
           113: 'm_nProficiencySingleWeapon', 114: 'm_nProficiency2Weapon',
           115: 'm_nProficiencyClub',
           **{i: 'm_nExtraProficiency' + str(i - 114) for i in range(116, 135)}}
PREFIX = re.compile(r'^INFO: LUA: \[(BGXW4|BGXW2|BGXWP)\] (\{.*\})\s*$')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_int(value, lo=0, hi=2**31-1) -> bool:
    return type(value) is int and lo <= value <= hi


def output_hold(reason: str, *, details=None) -> dict:
    return dict(schema=SCHEMA, status='HOLD_INCOMPLETE_LIVE_EVIDENCE', reason=reason,
                details=details or [], executable=False, dispatchAuthorized=False,
                weaponSwitchAuthorized=False, actionsIssued=0,
                currentGameActionPreserved=True, priorityRecommendation=None)


def read_console(path: Path) -> dict:
    """Deduplicate INFO: LPRINT reflections by consuming only INFO: LUA lines.

    Multiple complete log sessions are not silently coalesced. Fail closed.
    """
    result = collections.defaultdict(list)
    sessions = collections.Counter()
    invalid = 0
    for lineno, line in enumerate(path.read_text(encoding='utf-8-sig', errors='replace').splitlines(), 1):
        m = PREFIX.match(line)
        if not m:
            continue
        label, raw = m.groups()
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            invalid += 1
            continue
        typ = payload.get('type', 'ACTION' if label == 'BGXWP' else None)
        if typ == 'SESSION':
            sessions[label] += 1
        if (label, typ) in [('BGXW4', 'ACTIVE'), ('BGXW2', 'SLOTS'), ('BGXWP', 'ACTION')]:
            result[label].append((lineno, payload))
    if invalid:
        return output_hold('MALFORMED_SOURCE_CONSOLE_JSON', details=[str(invalid)])
    if any(sessions[l] != 1 for l in ('BGXW4', 'BGXW2', 'BGXWP')):
        return output_hold('AMBIGUOUS_OR_MISSING_CONSOLE_SESSION', details=[dict(sessions)])
    if not all(result[l] for l in ('BGXW4', 'BGXW2', 'BGXWP')):
        return output_hold('OBSERVER_RECORDS_MISSING')
    return {'status': 'PARSED_ONE_CONSOLE_SESSION', 'records': dict(result)}


def standard_map_from_r4_lua(lua_source: Path) -> bool:
    """Ensure our mapping was not silently changed from the actual R4 source."""
    content = lua_source.read_text(encoding='utf-8')
    listed = {int(i): n for i, n in re.findall(r"\[(\d+)\]='(m_nProficiency[A-Za-z0-9]+)'", content)}
    return listed == {k: v for k, v in PROF_R4.items() if k <= 115} and (
        "PROFICIENCY_BY_ID[profId]='m_nExtraProficiency'..tostring(profId-114)" in content)


def native_item(native: dict, resref: str) -> dict | None:
    if native.get('status') != 'ITM_NATIVE_ALL_ITEMS_RAW_READ' or native.get('sourceKind') != 'CURRENT_GAME':
        return None
    r = native.get('items')
    if type(r) is not dict:
        return None
    v = r.get(resref)
    if type(v) is not dict or type(v.get('item')) is not dict:
        return None
    if v['item'].get('rawOnly') is not True or v['item'].get('schema') != 'BGXAI_ITM_RAW_V1':
        return None
    if type(v.get('provenance')) is not dict or v['provenance'].get('origin') not in ('CURRENT_GAME_OVERRIDE', 'CURRENT_GAME_BIFF'):
        return None
    return v['item']


def extract_ability(item: dict) -> dict | None:
    abilities = item.get('abilities')
    if type(abilities) is not list or len(abilities) != 1:
        return None
    a = abilities[0]
    if type(a) is not dict:
        return None
    n = a.get('baseDamageMeanBeforeEffects')
    if type(n) not in (int, float) or not 0 <= n <= 1000:
        return None
    if not is_int(a.get('attackTypeRaw'), 0, 10):
        return None
    return a


def resolve_selected(slot: int, r2: dict, native: dict) -> dict | None:
    """Resolve selected item without attributing ammo-index selection to a proven launcher.

    R2 reads slots only. One compatible launcher proves a *candidate*, not that
    engine is actively selecting it. All other launcher cases fail closed.
    """
    qs, ammo = r2.get('quickWeapons'), r2.get('quivers')
    if type(qs) is not list or len(qs) != 4 or type(ammo) is not list or len(ammo) != 4:
        return None
    for idx, entry in enumerate(qs):
        if type(entry) is not dict or entry.get('index') != idx + 35:
            return None
    for idx, entry in enumerate(ammo):
        if type(entry) is not dict or entry.get('index') != idx + 11:
            return None
    if 35 <= slot <= 38:
        r = qs[slot-35].get('resrefRaw')
        if type(r) is not str or native_item(native, r) is None:
            return None
        return {'itemResRef': r, 'ammoResRef': None,
                'selectedIdentityStatus': 'SELECTED_QUICKSLOT_RESREF_RAW_NOT_VERIFIED_USABLE',
                'nativeItem': native_item(native, r)}
    if 11 <= slot <= 14:
        r = ammo[slot-11].get('resrefRaw')
        ammo_item = native_item(native, r) if type(r) is str else None
        if ammo_item is None or not is_int(ammo[slot-11].get('useCount1Raw'), 1, 1000000):
            return None
        ammo_ability = extract_ability(ammo_item)
        if ammo_ability is None or ammo_ability['attackTypeRaw'] != 2:
            return None
        launcher_type = ammo_ability.get('launcherRequiredRaw')
        if not is_int(launcher_type, 1, 9):
            return None
        # Raw 1 is arrow->bow. Other launcher requirements not attested here.
        if launcher_type != 1:
            return None
        launchers=[]
        for w in qs:
            resref=w['resrefRaw']
            item=native_item(native, resref) if type(resref) is str else None
            a=extract_ability(item) if item else None
            if a is not None and a.get('attackTypeRaw')==4 and a.get('launcherRequiredRaw')==0:
                launchers.append((resref,item))
        if len(launchers) != 1:
            return None
        return {'itemResRef': launchers[0][0], 'ammoResRef': r,
                'selectedIdentityStatus': 'AMMO_SELECTED_UNIQUE_BOW_CANDIDATE_NOT_ENGINE_LAUNCHER_PROOF',
                'nativeItem': launchers[0][1], 'nativeAmmo': ammo_item,
                'ammoCountRaw': ammo[slot-11]['useCount1Raw']}
    return None


def snapshot_fingerprint(stats: dict) -> tuple | None:
    """Only raw stable fields across *samples*, NOT a complete buff fingerprint."""
    keys=['m_nLevel1','m_nLevel2','m_nLevel3','m_nKit','m_nSTR','m_nSTRExtra','m_nDEX',
          'm_bImprovedHaste','m_nLuck','m_nLevelDrain']
    values=[stats.get(k) for k in keys]
    if not all(is_int(x,0,2147483647) for x in values):
        return None
    return tuple(values)


def evaluate(console: dict, native: dict, *, lua_source: Path | None = None) -> dict:
    if console.get('status') != 'PARSED_ONE_CONSOLE_SESSION':
        return copy.deepcopy(console)
    if lua_source is not None and not standard_map_from_r4_lua(lua_source):
        return output_hold('R4_LUA_WPROF_MAPPING_CHANGED')
    records=console['records']
    # R1 may emit duplicates as both LUA/LPRINT. Parser already dedupes.
    a,b,c=[records[k] for k in ('BGXW4','BGXW2','BGXWP')]
    if len(a)!=len(b) or len(a)!=len(c):
        return output_hold('R1_R2_R4_ACTION_COUNTS_DISAGREE',details=[len(a),len(b),len(c)])
    if len(a)>64:
        return output_hold('R4_ACTION_COUNT_EXCEEDS_SOURCE_LIMIT')
    actors=collections.defaultdict(list)
    for seq, ((line4,r4), (line2,r2), (line1,r1)) in enumerate(zip(a,b,c),1):
        if not (r4.get('schema')==R4_SCHEMA and r4.get('type')=='ACTIVE' and
                r4.get('status')=='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS' and
                r4.get('presentCount')==68 and r4.get('missingCount')==0 and
                r2.get('schema')==R2_SCHEMA and r2.get('type')=='SLOTS'):
            return output_hold('OBSERVER_SCHEMA_OR_COMPLETENESS_MISMATCH',details=[seq])
        expected=(r4.get('actor'),r4.get('partyIndex'),r4.get('actionRaw'),r4.get('selectedWeaponRaw'))
        compared=(r2.get('actor'),r2.get('partyIndex'),r2.get('actionRaw'),r2.get('selectedWeaponRaw'))
        legacy=(r1.get('actor'),r1.get('partyIndex'),r1.get('action'),r1.get('selectedWeaponRaw'))
        if (expected!=compared or expected!=legacy or r4.get('seq')!=seq or r2.get('seq')!=seq
            or r1.get('sequence')!=seq or not (line2<line4<line1)):
            return output_hold('CROSS_OBSERVER_EVENT_IDENTITY_OR_ORDER_MISMATCH',details=[seq])
        if not is_int(r4.get('actor')) or not is_int(r4.get('partyIndex'),0,5):
            return output_hold('ACTOR_OR_PARTY_INVALID',details=[seq])
        stats=r4.get('statsRaw')
        if (type(stats) is not dict or len(stats)!=68 or
            not all(type(v) is int for v in stats.values()) or
            stats.get('m_nNumberOfAttacks') != r1.get('aprRaw') or
            stats.get('m_nTHAC0') != r1.get('thac0Raw')):
            return output_hold('R1_R4_RAW_COMBAT_STATS_MISMATCH',details=[seq])
        weapon=resolve_selected(r4['selectedWeaponRaw'],r2,native)
        if weapon is None:
            return output_hold('SELECTED_ITEM_OR_AMMO_UNRESOLVED',details=[seq])
        native_item_for_weapon=weapon['nativeItem']
        ability=extract_ability(native_item_for_weapon)
        if ability is None:
            return output_hold('NATIVE_ITEM_ABILITY_UNSUPPORTED',details=[seq])
        prof_id=native_item_for_weapon.get('proficiencyIdRaw')
        field=PROF_R4.get(prof_id)
        if field is None or not is_int(stats.get(field),0,10):
            return output_hold('NATIVE_PROFICIENCY_UNMAPPED_OR_UNREADABLE',details=[seq,prof_id])
        if prof_id>115:
            return output_hold('MODDED_PROFICIENCY_MAPPING_UNVERIFIED',details=[seq,prof_id])
        apr_raw=stats['m_nNumberOfAttacks']
        if apr_raw not in RAW_APR or RAW_APR[apr_raw]<.5:
            return output_hold('ENGINE_APR_ENCODING_UNSUPPORTED',details=[seq,apr_raw])
        if not is_int(stats.get('m_THAC0BonusRight'), -100, 100):
            return output_hold('SLOT_THAC0_BONUS_UNREADABLE',details=[seq])
        fprint=snapshot_fingerprint(stats)
        if fprint is None:
            return output_hold('BASIC_ACTIVE_STATS_UNREADABLE',details=[seq])
        actor_key=(r4['actor'],r4['partyIndex'])
        rec={'sequence':seq,'r4Line':line4,'partyIndex':actor_key[1],
             'selectedWeaponRaw':r4['selectedWeaponRaw'],
             'weaponResRef':weapon['itemResRef'], 'ammunitionResRef':weapon['ammoResRef'],
             'selectionResolution':weapon['selectedIdentityStatus'],
             'aprRaw':apr_raw,'aprDecodedIfStandard':RAW_APR[apr_raw],
             'baseWeaponTHAC0Raw':stats['m_nTHAC0'],
             'rightHandTHAC0BonusRaw':stats['m_THAC0BonusRight'],
             'proficiencyIdRaw':prof_id,'proficiencyField':field,'proficiencyRaw':stats[field],
             'staticItemAbilityDamageMeanBeforeEffects':ability['baseDamageMeanBeforeEffects'],
             'nativeAbilityAttackTypeRaw':ability['attackTypeRaw'],
             '_fingerprint':fprint}
        if weapon['ammoResRef']:
            ab=extract_ability(weapon['nativeAmmo'])
            if ab is None: return output_hold('NATIVE_AMMO_ABILITY_UNSUPPORTED',details=[seq])
            rec['staticItemAbilityDamageMeanBeforeEffects']=ab['baseDamageMeanBeforeEffects']+ability['baseDamageMeanBeforeEffects']
            rec['ammoCountRaw']=weapon['ammoCountRaw']
        rec['nativeAbilityHitEffectOpcodesRaw']=[e.get('opcodeRaw') for e in ability.get('effects',[]) if type(e) is dict]
        rec['nativeEquippedEffectOpcodesRaw']=[e.get('opcodeRaw') for e in native_item_for_weapon.get('equippedEffects',[]) if type(e) is dict]
        rec['hasUnvaluedOnHitEffects']=bool(rec['nativeAbilityHitEffectOpcodesRaw'])
        rec['nativeItemContainsUnverifiedEquippedEffects']=bool(rec['nativeEquippedEffectOpcodesRaw'])
        rec['staticBaseDamageTimesSelectedAPR_NotDPS']=round(rec['staticItemAbilityDamageMeanBeforeEffects']*RAW_APR[apr_raw],4)
        actors[actor_key].append(rec)
    grouped=[]
    for (actor,party),records in sorted(actors.items()):
        unique={}
        fingerprint_changed=False
        for x in records:
            key=(x['selectedWeaponRaw'],x['weaponResRef'],x['ammunitionResRef'])
            previous=unique.get(key)
            if previous and (previous['aprRaw']!=x['aprRaw'] or
                previous['proficiencyRaw']!=x['proficiencyRaw']):
                return output_hold('SAME_SELECTED_WEAPON_STATS_CHANGED_WITHIN_SESSION',details=[actor,key])
            unique[key]=x
        fingerprints={x['_fingerprint'] for x in records}
        fingerprint_changed=len(fingerprints)!=1
        summaries=[]
        for x in sorted(unique.values(),key=lambda k:k['selectedWeaponRaw']):
            summary={k:v for k,v in x.items() if k!='_fingerprint'}
            summary.update(executable=False,dispatchAuthorized=False,
                           allEffectsAndBuffsVerified=False,
                           otherSlotAPRProjected=False,
                           targetHitChanceVerified=False,
                           activeShieldBenefitVerified=False)
            summaries.append(summary)
        grouped.append({'actorId':actor,'partyIndex':party,'events':len(records),
                        'sampledRawFingerprintChanged':fingerprint_changed,
                        'sampledRawFingerprintIsExhaustiveBuffProof':False,
                        'selections':summaries})
    return {'schema':SCHEMA,'status':'SELECTED_HISTORICAL_APR_AND_ITEM_IDENTITY_OBSERVED_PRIORITY_HOLD',
        'source':'SAME_CONSOLE_SESSION_R1_R2_R4_PLUS_PRIOR_NATIVE_R3',
        'correlation':{'r1Events':len(c),'r2Events':len(b),'r4Events':len(a),
                       'eventTriplesMatched':len(a)},
        'actors':grouped,
        'rankingGate':{
            'status':'HOLD_COMPLETE_EFFECTIVE_SCENE_REQUIRED',
            'missing':['AUDITED_TARGET_AC_AND_PROTECTIONS',
              'CURRENT_ALL_BUFFS_AND_EFFECTS_FINGERPRINT',
              'ALTERNATE_SLOT_ACTIVE_EFFECTIVE_APR_AND_THAC0',
              'WEAPON_AND_AMMO_EFFECTS_COMPLETE',
              'EQUIPMENT_USABILITY_AND_DAMAGE_TYPES',
              'MANUAL_AND_EPS_ACTION_QUEUE_ORIGIN',
              'IN_RANGE_AND_SAFE_AOE_PATH'],
            'cannotInferFromHistoricalSelectedAPRs':True,
            'sourceOnlyCurrentActionPreserved':True,
            'weaponSwitchAuthorized':False},
        'executable':False,'dispatchAuthorized':False,'weaponSwitchAuthorized':False,
        'actionsIssued':0,'gameModified':False,
        'priorityRecommendation':None}


def make_report(console_file: Path, native_file: Path, lua_source: Path) -> dict:
    if not all(p.is_file() and not p.is_symlink() for p in (console_file,native_file,lua_source)):
        return output_hold('INPUT_NOT_REGULAR_FILE')
    if sha256(native_file) != PINNED_R3_REPORT_SHA256:
        return output_hold('NATIVE_R3_REPORT_CHANGED_REAUDIT_REQUIRED')
    if sha256(lua_source) != PINNED_R4_SOURCE_CONTRACT_SHA256:
        return output_hold('R4_SOURCE_CONTRACT_CHANGED_REAUDIT_REQUIRED')
    parsed=read_console(console_file)
    try:
        native=json.loads(native_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError,UnicodeDecodeError):
        return output_hold('R3_NATIVE_REPORT_INVALID')
    result=evaluate(parsed,native,lua_source=lua_source)
    result['inputSHA256']={'console':sha256(console_file),'nativeR3':sha256(native_file),
                           'r4LuaContract':sha256(lua_source)}
    return result


def main():
    parser=argparse.ArgumentParser(description='SOURCE ONLY: correlate prior R1/R2/R4 console and R3 ITM without changing game')
    parser.add_argument('--console',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--r4-lua',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=make_report(args.console,args.native,args.r4_lua)
    # Tool authoring only. This is not an updater and never writes under game root.
    if 'BG_EET_FOXX_NEW' in str(args.output).upper() or args.output.is_symlink():
        raise SystemExit('STOP: output must not be in the game directory or through a symlink')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=False)+'\n',encoding='utf-8')
    print(data['status'], 'matched',data.get('correlation',{}).get('eventTriplesMatched',0))


if __name__=='__main__':
    main()
