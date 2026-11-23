#!/usr/bin/env python3
"""BGXAI R17: fail-closed source-only cross-session ability/ammo evidence contract.

Consumes frozen prior R3 ITM resource audit, R16 alternate-slot evidence report,
and the original real runtime console log. Performs no game I/O, no action,
installation, hook or writes except explicit optional JSON report output.

No engine-authenticated launcher/ammo/ability binding, no active-effect proof,
no alternate-slot effective APR, no weapon decisions or dispatch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_R3_SHA = '7ae7555f81b14a784e7866472f14483b02c2d6b707ab6169225e8fec32507304'
EXPECTED_LOG_SHA = 'cebfa573df8fc9e5180ec8cbcfc8b67a865a12c6381394d5dcd511cdf7500945'
MAX_INPUT = 2_000_000
REQUIRED_SLOTS = (35, 36, 37, 38, 11, 12, 13, 14, 9)
DEF_FIELDS = ('m_nArmorClass','m_nACCrushingMod','m_nACMissileMod','m_nACPiercingMod',
              'm_nACSlashingMod','m_nResistCrushing','m_nResistPiercing',
              'm_nResistSlashing','m_nResistMissile')


def _hold(reason: str, **rest: Any) -> dict:
    return {'schema':'BGXAI_ABILITY_AMMO_CONTRACT_R17_RO_V1','status':'HOLD','reason':reason,
            'sourceOnly':True,'readOnly':True,'gameModified':False,
            'weaponSwitchAuthorized':False,'dispatchAuthorized':False,
            'nativeLauncherAmmoPairVerified':False,'alternateSlotEffectiveAprVerified':False,
            'activeEffectStateVerified':False,**rest}


def _load_file(path: Path) -> tuple[bytes,str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError('INPUT_MISSING_OR_SYMLINK')
    before=path.stat()
    if not 1<=before.st_size<=MAX_INPUT:
        raise ValueError('INPUT_SIZE_LIMIT')
    raw=path.read_bytes()
    after=path.stat()
    if len(raw)!=before.st_size or after.st_size!=before.st_size or after.st_mtime_ns!=before.st_mtime_ns:
        raise ValueError('INPUT_CHANGED_DURING_READ')
    return raw,hashlib.sha256(raw).hexdigest()


def _quiver(q:dict,index=12) -> dict|None:
    arr=q.get('quivers')
    if not isinstance(arr,list) or len(arr)!=4:
        return None
    a=[x for x in arr if isinstance(x,dict) and x.get('index')==index]
    return a[0] if len(a)==1 else None


def _weapon(q:dict,index=36) -> dict|None:
    arr=q.get('quickWeapons')
    if not isinstance(arr,list) or len(arr)!=4:
        return None
    a=[x for x in arr if isinstance(x,dict) and x.get('index')==index]
    return a[0] if len(a)==1 else None


def _parse_log(log:str)->tuple[list[dict],list[dict]]:
    defense=[];r2=[]
    lines=log.splitlines()
    if len(lines)>20_000:
        raise ValueError('LOG_LINES_LIMIT')
    for i,line in enumerate(lines,1):
        if 'INFO: LUA:' not in line:
            continue
        if '[BGXTD13] {' in line:
            val=line.split('[BGXTD13] ',1)[1]
            try: obj=json.loads(val)
            except ValueError:raise ValueError('INVALID_R13_JSON') from None
            if not isinstance(obj,dict):raise ValueError('INVALID_R13_EVENT')
            if obj.get('type')=='DEFENSE':defense.append({'line':i,'data':obj})
        elif '[BGXW2] {' in line:
            val=line.split('[BGXW2] ',1)[1]
            try: obj=json.loads(val)
            except ValueError:raise ValueError('INVALID_R2_JSON') from None
            if not isinstance(obj,dict):raise ValueError('INVALID_R2_EVENT')
            if obj.get('type')=='SLOTS':r2.append({'line':i,'data':obj})
    return defense,r2


def _int(v:object,lo:int,hi:int)->bool:
    return type(v) is int and lo<=v<=hi


def _raw_abilities(rec:dict, expected:str)->list[dict]:
    if rec.get('resource')!=expected or rec.get('item',{}).get('rawOnly') is not True:
        raise ValueError('RAW_ITEM_SOURCE_MISMATCH')
    abilities=rec['item'].get('abilities')
    if not isinstance(abilities,list) or len(abilities)>10:
        raise ValueError('ABILITIES_INVALID')
    allowed=('abilityIndex','attackTypeRaw','rangeRaw','speedRaw','launcherRequiredRaw',
             'damageTypeRaw','thac0BonusRaw','diceCountRaw','diceSidesRaw','damageBonusRaw')
    out=[]
    for j,a in enumerate(abilities):
        if not isinstance(a,dict) or a.get('abilityIndex')!=j:
            raise ValueError('ABILITY_HEADER_INVALID')
        limits={'abilityIndex':(0,9),'attackTypeRaw':(0,5),'rangeRaw':(0,10000),
                'speedRaw':(0,1000),'launcherRequiredRaw':(0,10),
                'damageTypeRaw':(0,20),'thac0BonusRaw':(-100,100),
                'diceCountRaw':(0,100),'diceSidesRaw':(0,1000),
                'damageBonusRaw':(-1000,1000)}
        if any(not _int(a.get(k),*limits[k]) for k in allowed):
            raise ValueError('ABILITY_HEADER_INVALID')
        effects=a.get('effects')
        if not isinstance(effects,list) or len(effects)>100:
            raise ValueError('ABILITY_EFFECTS_INVALID')
        for e in effects:
            if not isinstance(e,dict) or not _int(e.get('opcodeRaw'),0,999):
                raise ValueError('ABILITY_EFFECT_INVALID')
        out.append({k:a[k] for k in allowed}|{
            'onHitSpellTriggerCandidate':any(e['opcodeRaw']==146 for e in effects),
            'abilityEffectsRaw':[{'opcodeRaw':e['opcodeRaw'],
                                  'resourceRaw':e.get('resourceRaw'),
                                  'probability1Raw':e.get('probability1Raw')} for e in effects],
            'abilityCurrentSelectionVerified':False,
            'effectiveDamageVerified':False})
    return out


def analyze(r3:dict,r16:dict,log_text:str,r3sha:str,logsha:str)->dict:
    if r3sha!=EXPECTED_R3_SHA or logsha!=EXPECTED_LOG_SHA:
        return _hold('FROZEN_R3_OR_RUNTIME_LOG_SHA_CHANGED')
    if (r3.get('schema')!='BGXAI_WEAPON_NATIVE_ITM_R3_READONLY' or
        r3.get('status')!='ITM_NATIVE_ALL_ITEMS_RAW_READ' or
        r3.get('missingItemsOrLinkedSpells')!=[] or
        r3.get('sourceKind')!='CURRENT_GAME' or
        any(r3.get(k) is not False for k in ('launcherAmmoPairVerified','currentCharacterBuffsVerified',
            'fullWeaponEffectsVerified','aprPerSlotVerified','weaponSwitchAuthorized','dispatchAuthorized'))):
        return _hold('R3_PROVENANCE_OR_FLAGS_INVALID')
    if (r16.get('schema')!='BGXAI_ALTERNATE_SLOT_STATIC_EVIDENCE_RO_V1' or
        r16.get('status')!='PRIOR_STATIC_ITEM_FACTS_AND_CURRENT_SELECTION_AUDITED_RO' or
        r16.get('input',{}).get('r3Sha256')!=r3sha or
        r16.get('input',{}).get('logSha256')!=logsha or
        r16.get('currentGameResourceRevalidated') is not False or
        r16.get('previousR3SnapshotIsSameActorAndSession') is not False or
        r16.get('weaponSwitchAuthorized') is not False or
        r16.get('fullLoadoutScoringAuthorized') is not False or
        r16.get('effectiveAlternateSlotAPRVerified') is not False or
        r16.get('launcherAmmoAssociationVerified') is not False):
        return _hold('R16_PROVENANCE_OR_FLAGS_INVALID')
    slots=r16.get('slots')
    if (not isinstance(slots,list) or len(slots)!=len(REQUIRED_SLOTS) or
        tuple(s.get('slot') for s in slots if isinstance(s,dict))!=REQUIRED_SLOTS):
        return _hold('R16_SLOT_SET_INVALID')
    if not _int(r16.get('actorId'),1,2147483647) or r16.get('actorId')==r16.get('previousR3ActorId'):
        return _hold('ACTOR_CROSS_SESSION_GUARD')
    actual={s['slot']:s for s in slots}
    static={}; gaps={}
    for slot,s in actual.items():
        if s.get('priorityEligible') is not False or s.get('usableNowVerified') is not False:
            return _hold('R16_ABILITY_PROMOTION_FORBIDDEN',slot=slot)
        ref=s.get('resrefRaw')
        if ref is None:
            if s.get('status')!='EMPTY_AT_OBSERVED_SESSION':
                return _hold('INVALID_EMPTY_SLOT',slot=slot)
            continue
        if not isinstance(ref,str) or ref not in r3.get('items',{}):
            return _hold('R3_RESOURCE_MISSING',slot=slot)
        rec=r3['items'][ref]
        if (s.get('staticItem',{}).get('resource')!=ref or
            rec.get('provenance',{}).get('sha256')!=s['staticItem'].get('resourceSha256AtR3Audit') or
            s['staticItem'].get('currentResourceHashVerified') is not False):
            return _hold('STATIC_RESOURCE_PROVENANCE_DRIFT',slot=slot)
        try: abs_=_raw_abilities(rec,ref)
        except ValueError as ex: return _hold(str(ex),slot=slot)
        if not isinstance(s['staticItem'].get('abilities'),list) or len(abs_)!=len(s['staticItem']['abilities']):
            return _hold('R16_ABILITY_COUNT_DRIFT',slot=slot)
        for i,a in enumerate(abs_):
            if any(a[k]!=s['staticItem']['abilities'][i].get(k) for k in
                   ('abilityIndex','attackTypeRaw','rangeRaw','speedRaw','launcherRequiredRaw',
                    'damageTypeRaw','thac0BonusRaw','diceCountRaw','diceSidesRaw','damageBonusRaw')):
                return _hold('R16_R3_ABILITY_FIELDS_CONFLICT',slot=slot)
        eq=rec['item'].get('equippedEffects')
        if not isinstance(eq,list) or len(eq)>256:
            return _hold('EQUIPPED_EFFECTS_INVALID',slot=slot)
        if any(not isinstance(e,dict) or not _int(e.get('opcodeRaw'),0,999) for e in eq):
            return _hold('EQUIPPED_EFFECT_INVALID',slot=slot)
        apr=[e for e in eq if e['opcodeRaw']==1]
        if slot==36 and (len(apr)!=1 or apr[0].get('parameter1Raw')!=2 or apr[0].get('parameter2Raw')!=1):
            return _hold('BOW_APR_EFFECT_CHANGED',slot=slot)
        static[slot]={
            'itemResrefRaw':ref,'priorResourceSha256':rec['provenance']['sha256'],
            'currentResourceBytesReverified':False,'abilityHeaders':abs_,
            'equippedOpcodeNumbers':[e['opcodeRaw'] for e in eq],
            'aprEffectKeyRaw':apr[0].get('parameter1Raw') if len(apr)==1 else None,
            'aprEffectModeRaw':apr[0].get('parameter2Raw') if len(apr)==1 else None,
            'aprEffectAdditiveDeltaAssumed':False,
            'isTwoHandedStatic':rec['item'].get('twoHandedFlagRaw'),
            'effectiveSlotAprVerified':False,'characterUsabilityVerified':False,
            'activeEffectsVerified':False,'abilitySelectedInEngineVerified':False,
            'manualAndEpsQueueVerified':False,'priorityEligible':False,
        }
        gaps[slot]=list(s.get('blockedBy',[]))
    if set(static)!={35,36,38,12,9}:
        return _hold('UNEXPECTED_OCCUPIED_SLOT_LAYOUT')
    bow,arrows=static[36]['abilityHeaders'],static[12]['abilityHeaders']
    if len(bow)!=1 or len(arrows)!=1:
        return _hold('AMBIGUOUS_LAUNCHER_OR_AMMO_ABILITIES')
    if bow[0]['attackTypeRaw']!=4 or arrows[0]['attackTypeRaw']!=2 or arrows[0]['launcherRequiredRaw']!=1:
        return _hold('STATIC_BOW_AMMO_TYPE_CONFLICT')
    try: defense,r2=_parse_log(log_text)
    except ValueError as ex: return _hold(str(ex))
    if len(defense)!=4 or len(r2)!=15 or r16.get('selectedObservationCount')!=4 or r16.get('snapshots')!=15:
        return _hold('R13_OR_R2_COUNTS_NOT_AS_EXPECTED')
    ammo=[]
    for d in defense:
        q=d['data']
        if q.get('status')!='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY' or q.get('sourceActor')!=r16['actorId'] or q.get('rawActionId')!=3:
            return _hold('R13_ATTACK_OR_ACTOR_INVALID')
        df=q.get('fields')
        if (not isinstance(df,dict) or len(df)!=len(DEF_FIELDS) or
            any(not _int(df.get(k),-200,200) for k in DEF_FIELDS) or
            q.get('weaponSwitchAuthorized') is not False or
            q.get('allProtectionsObserved') is not False or
            q.get('exactHitChanceProven') is not False):
            return _hold('R13_DEFENSE_FIELD_PROVENANCE_INVALID')
        if q.get('selectedSlot')!=12:
            continue
        snap=[e for e in r2 if d['line']<e['line']<=d['line']+4 and
              e['data'].get('actionRaw')==3 and e['data'].get('selectedWeaponRaw')==12 and
              e['data'].get('actor')==r16['actorId']]
        if len(snap)!=1:return _hold('R13_R2_ACTION_ASSOCIATION_NOT_UNIQUE')
        before=snap[0]
        later=[e for e in r2 if before['line']<e['line']<=before['line']+12 and
               e['data'].get('actor')==r16['actorId']]
        if not later:return _hold('NO_POST_ATTACK_EQUIPMENT_SNAPSHOT')
        after=later[0]
        b,a=_quiver(before['data']),_quiver(after['data'])
        wb,wa=_weapon(before['data']),_weapon(after['data'])
        if (not b or not a or not wb or not wa or
            b.get('resrefRaw')!='AROW01' or a.get('resrefRaw')!='AROW01' or
            wb.get('resrefRaw')!='BOW05' or wa.get('resrefRaw')!='BOW05' or
            not _int(b.get('useCount1Raw'),0,65535) or not _int(a.get('useCount1Raw'),0,65535)):
            return _hold('AMMO_OR_BOW_SNAPSHOT_CHANGED')
        consumed=b['useCount1Raw']-a['useCount1Raw']
        if consumed<=0 or consumed>20:
            return _hold('AMMO_DECREMENT_NOT_OBSERVED')
        ammo.append({'r13Sequence':q['seq'],'actor':r16['actorId'],
                     'attackActionRaw':3,'selectedSlot':12,
                     'beforeAmmoQuantityRaw':b['useCount1Raw'],
                     'afterAmmoQuantityRaw':a['useCount1Raw'],
                     'windowQuantityDecrease':consumed,
                     'bowPresentInQuickslot36Candidate':True,
                     'launcherAmmoEnginePairVerified':False,
                     'exactProjectilesFiredVerified':False,
                     'sameNativeEventTokenVerified':False,
                     'classification':'OBSERVED_AMMO_QUANTITY_DECREMENT_NEAR_ATTACK_RO'})
    if len(ammo)!=3 or [x['windowQuantityDecrease'] for x in ammo]!=[1,2,1]:
        return _hold('EXPECTED_LIVE_AMMO_WINDOWS_CHANGED')
    return {
        'schema':'BGXAI_ABILITY_AMMO_CONTRACT_R17_RO_V1',
        'status':'STATIC_ABILITY_AND_LIVE_AMMO_WINDOW_CANDIDATES_RO',
        'readOnly':True,'sourceOnly':True,'gameModified':False,'executable':False,
        'input':{'r3Sha256':r3sha,'logSha256':logsha,'r16Schema':r16['schema']},
        'crossSessionPriorR3':True,'sameActorAsPriorR3':False,
        'actorIdAtLiveR16':r16['actorId'],
        'weaponSlots':static,'allSlotGaps':gaps,
        'launcherAmmoStaticCompatibilityCandidate':{
            'launcherSlot':36,'launcher':'BOW05','projectileSlot':12,'projectile':'AROW01',
            'launcherAttackTypeRaw':4,'ammoAttackTypeRaw':2,
            'ammoLauncherRequiredRaw':1,
            'launcherRangeRaw':bow[0]['rangeRaw'],'ammoRangeRaw':arrows[0]['rangeRaw'],
            'effectiveRangeInEngineVerified':False,
            'typeMatchFromPriorR3Only':True,'enginePairVerified':False},
        'ammoWindows':ammo,'ammoWindowCount':len(ammo),
        'r13DefenseReadLive':True,'allNineFieldsReadForOneTarget':True,
        'bowOpcode1RawKey2IsFlatCandidateNotAdditivePlus2':True,
        'swordOnHitOpcode146IsUnpricedBreakageRiskCandidate':True,
        'offhandShieldWithTwoHandedWeaponStateUnverified':True,
        'uncertainty':[
            'CURRENT_GAME_ITEM_BYTES_NOT_RECHECKED_AFTER_R3',
            'NO_LIVE_NATIVE_LAUNCHER_AMMO_ABILITY_IDENTITY',
            'NO_EXACT_ARROW_PER_ATTACK_OR_KILL_DAMAGE_INFERENCE',
            'NO_PER_SLOT_ACTIVE_EFFECT_SNAPSHOT',
            'NO_ALTERNATE_SLOT_APR_OR_FULL_EFFECTIVE_HIT_CHANCE',
            'NO_ITEM_319_USE_RESTRICTIONS_VALIDATION',
            'NO_HOSTILITY_AND_IMMUNITY_COMPLETENESS',
            'NO_MANUAL_EPS_QUEUE_FREE_BOUNDARY'],
        'currentResourceHashVerified':False,
        'nativeLauncherAmmoPairVerified':False,
        'alternateSlotEffectiveAprVerified':False,
        'activeEffectStateVerified':False,
        'targetProtectionsComplete':False,
        'manualAndEpsQueueVerified':False,
        'weaponPriorityAuthorized':False,'weaponSwitchAuthorized':False,
        'dispatchAuthorized':False,
    }


def analyze_files(r3_path:Path,r16_path:Path,log_path:Path)->dict:
    r3bytes,r3sha=_load_file(r3_path)
    r16bytes,_=_load_file(r16_path)
    logbytes,logsha=_load_file(log_path)
    try:
        return analyze(json.loads(r3bytes),json.loads(r16bytes),logbytes.decode('utf-8-sig'),r3sha,logsha)
    except (ValueError,UnicodeError,TypeError,KeyError) as ex:
        return _hold('INPUT_PARSE_OR_SHAPE_REJECTED',errorClass=type(ex).__name__)


def main()->int:
    p=argparse.ArgumentParser(description='R17 source-only; never changes the game')
    p.add_argument('--r3',required=True,type=Path)
    p.add_argument('--r16',required=True,type=Path)
    p.add_argument('--log',required=True,type=Path)
    args=p.parse_args()
    try: x=analyze_files(args.r3,args.r16,args.log)
    except (OSError,ValueError) as ex: x=_hold('INPUT_NOT_READABLE',errorClass=type(ex).__name__)
    print(json.dumps(x,indent=2,ensure_ascii=False,sort_keys=True))
    return 0 if x['status']=='STATIC_ABILITY_AND_LIVE_AMMO_WINDOW_CANDIDATES_RO' else 2


if __name__=='__main__':
    raise SystemExit(main())
