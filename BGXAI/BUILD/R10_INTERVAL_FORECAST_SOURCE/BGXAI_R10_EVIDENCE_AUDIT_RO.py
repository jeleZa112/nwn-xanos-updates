"""BGXAI R10: evidence-only native R3/R4 matrix auditor, no game access.
No installation, no network, no WeiDU, no extrapolation of alternate-slot APR.
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

SCHEMA = 'BGXAI_WEAPON_R4_R3_LIVE_EVIDENCE_V1'
STATUS = 'SELECTED_HISTORICAL_APR_AND_ITEM_IDENTITY_OBSERVED_PRIORITY_HOLD'
NEEDED = ('AUDITED_TARGET_AC_AND_PROTECTIONS',
          'CURRENT_ALL_BUFFS_AND_EFFECTS_FINGERPRINT',
          'ALTERNATE_SLOT_ACTIVE_EFFECTIVE_APR_AND_THAC0',
          'WEAPON_AND_AMMO_EFFECTS_COMPLETE',
          'EQUIPMENT_USABILITY_AND_DAMAGE_TYPES',
          'MANUAL_AND_EPS_ACTION_QUEUE_ORIGIN',
          'IN_RANGE_AND_SAFE_AOE_PATH')

def finite_number(x):
    return isinstance(x, (int,float)) and not isinstance(x,bool) and math.isfinite(x)

def audit(data:dict, input_sha:str):
    def stop(why):
        return {'schema':'BGXAI_R10_EVIDENCE_AUDIT_V1',
                'status':'HOLD_INVALID_EVIDENCE', 'reason':why,
                'gameModified':False,'executable':False,
                'weaponSwitchAuthorized':False,'dispatchAuthorized':False,
                'nativeAlternateAPRVerified':False,'inputSHA256':input_sha}
    if not isinstance(data,dict) or data.get('schema') != SCHEMA or data.get('status') != STATUS:
        return stop('MATRIX_SCHEMA_OR_STATUS')
    c=data.get('correlation')
    if not isinstance(c,dict) or any(c.get(k)!=16 for k in ('r1Events','r2Events','r4Events','eventTriplesMatched')):
        return stop('CORRELATION_MISMATCH')
    if not isinstance(data.get('actors'),list) or len(data['actors'])!=1:
        return stop('ACTOR_SET_UNEXPECTED')
    a=data['actors'][0]
    if a.get('actorId')!=139266124 or a.get('partyIndex')!=2 or a.get('events')!=16:
        return stop('ACTOR_CONTEXT_MISMATCH')
    selections=a.get('selections')
    if not isinstance(selections,list) or len(selections)!=3:
        return stop('SELECTION_SHAPE_MISMATCH')
    rows=[]; refs=set(); sequences=set()
    for s in selections:
        if not isinstance(s,dict): return stop('SELECTION_TYPE')
        item=s.get('weaponResRef');seq=s.get('sequence')
        if not isinstance(item,str) or item not in ('BOW05','STAF01','SW1H04') or item in refs:
            return stop('ITEM_IDENTITY_INVALID')
        refs.add(item)
        if not isinstance(seq,int) or seq in sequences or seq<1 or seq>16:
            return stop('SELECTION_SEQUENCE_INVALID')
        sequences.add(seq)
        apr=s.get('aprDecodedIfStandard');mean=s.get('staticItemAbilityDamageMeanBeforeEffects')
        if not finite_number(apr) or not finite_number(mean) or apr<=0 or mean<0:
            return stop('INVALID_APR_OR_STATIC_DAMAGE')
        if (item=='BOW05') != (s.get('selectedWeaponRaw')==12) or (
            item=='BOW05' and s.get('ammunitionResRef')!='AROW01'):
            return stop('AMMO_LAUNCHER_ASSOCIATION_INVALID')
        if item in ('STAF01','SW1H04') and s.get('selectedWeaponRaw') not in (35,38):
            return stop('QUICKSLOT_ASSOCIATION_INVALID')
        if any(s.get(k) is not False for k in (
            'allEffectsAndBuffsVerified','otherSlotAPRProjected',
            'targetHitChanceVerified','activeShieldBenefitVerified',
            'executable','dispatchAuthorized')):
            return stop('FORBIDDEN_VERIFICATION_OR_ACTION_CLAIM')
        if s.get('nativeItemContainsUnverifiedEquippedEffects') is not True:
            return stop('MISSING_UNVERIFIED_EFFECT_WARNING')
        # Only a static descriptive product, never an expected damage-per-round claim.
        base=round(apr*mean,8)
        given=s.get('staticBaseDamageTimesSelectedAPR_NotDPS')
        if not finite_number(given) or abs(given-base)>1e-6:
            return stop('BASE_DAMAGE_PRODUCT_MISMATCH')
        rows.append({'weaponResRef':item,'selectionSequence':seq,
          'historicalSelectedAPR':apr,'staticItemDamageMeanBeforeEffects':mean,
          'staticBaseTimesHistoricalAPR_NotDPS':base,
          'aprOfAlternativeAtCurrentTime':None,
          'targetHitProbability':None,
          'targetResistanceAndImmunityComplete':False,
          'nativeCurrentOtherSlotAPRVerified':False,
          'nativeCurrentEquippedEffectsComplete':False,
          'launcherProvenFromEngine':False if item=='BOW05' else None,
          'hasUnvaluedOnHitEffects':s.get('hasUnvaluedOnHitEffects')})
    if refs != {'BOW05','STAF01','SW1H04'}:
        return stop('REQUIRED_WEAPONS_MISSING')
    gate=data.get('rankingGate')
    if not isinstance(gate,dict) or gate.get('status')!='HOLD_COMPLETE_EFFECTIVE_SCENE_REQUIRED' or \
       gate.get('weaponSwitchAuthorized') is not False or \
       set(gate.get('missing',[])) != set(NEEDED):
        return stop('GATE_OR_MISSING_EVIDENCE_CHANGED')
    rows.sort(key=lambda x:x['weaponResRef'])
    return {'schema':'BGXAI_R10_EVIDENCE_AUDIT_V1',
       'status':'HOLD_REAL_R3_R4_MATRIX_INCOMPLETE_NO_NATIVE_RANKING',
       'inputSHA256':input_sha,'gameModified':False,'executable':False,
       'weaponSwitchAuthorized':False,'dispatchAuthorized':False,
       'nativeAlternateAPRVerified':False,'modeledPhysicalTargetDPR':None,
       'actor':139266124,'partyIndex':2,'matchedEvents':16,
       'rows':rows,'missingToCalculateRealTargetEfficiency':list(NEEDED),
       'reason':'R3_ITEM_MEAN_AND_HISTORICAL_SELECTED_APR_ARE_NOT_CURRENT_TARGET_DPR'}

def main(argv):
    if len(argv)!=3:
        print('Usage: python BGXAI_R10_EVIDENCE_AUDIT_RO.py MATRIX.json OUTPUT.json',file=sys.stderr)
        return 2
    src=Path(argv[1]);dest=Path(argv[2])
    if not src.is_file() or src.is_symlink() or dest.is_symlink():
        print('ERROR: FILE_MISSING_OR_LINK',file=sys.stderr);return 2
    if src.stat().st_size>2_000_000:
        print('ERROR: OVERSIZE_SOURCE',file=sys.stderr);return 2
    raw=src.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    try: data=json.loads(raw.decode('utf-8-sig'))
    except Exception as e:
        print('ERROR: BAD_JSON '+str(e),file=sys.stderr);return 2
    result=audit(data,sha)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(result['status'],'items=',len(result.get('rows',[])), 'report=',dest)
    return 0 if result['status'].startswith('HOLD_REAL') else 2
if __name__=='__main__': raise SystemExit(main(sys.argv))
