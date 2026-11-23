"""Synthetic, game-free tests: fail-closed source-only R17 evidence contract."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from BGXAI_ABILITY_AMMO_CONTRACT_R17_RO import (
    EXPECTED_R3_SHA,EXPECTED_LOG_SHA,analyze,analyze_files,_load_file
)

ROOT=Path(__file__).parent


def fake():
    actor=101
    items={}
    specs={
        'SW1H04':(1,0,0,1,5,1,8,3,0,False),
        'BOW05': (4,0,0,75,6,0,6,1,0,True),
        'STAF01':(1,0,0,2,4,1,6,2,0,True),
        'AROW01':(2,1,0,100,0,1,6,4,0,False),
        'SHLD03A':None}
    for ref,info in specs.items():
        abilities=[];fx=[]
        if info is not None:
            attack,launcher,thac,reach,speed,dice,sides,dmg,bonus,two=info
            effects=([{'opcodeRaw':146,'resourceRaw':'SW1H04','probability1Raw':1}]
                     if ref=='SW1H04' else [])
            abilities=[{'abilityIndex':0,'attackTypeRaw':attack,'launcherRequiredRaw':launcher,
                       'thac0BonusRaw':thac,'rangeRaw':reach,'speedRaw':speed,
                       'diceCountRaw':dice,'diceSidesRaw':sides,'damageTypeRaw':dmg,
                       'damageBonusRaw':bonus,'effects':effects}]
        else:
            two=False
        if ref=='BOW05':fx=[{'opcodeRaw':1,'parameter1Raw':2,'parameter2Raw':1}]
        items[ref]={'resource':ref,'provenance':{'sha256': 'a'*64},
                    'item':{'rawOnly':True,'abilities':abilities,
                            'equippedEffects':fx,'twoHandedFlagRaw':two}}
    r3={'schema':'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY',
        'status':'ITM_NATIVE_ALL_ITEMS_RAW_READ','sourceKind':'CURRENT_GAME',
        'missingItemsOrLinkedSpells':[], 'items':items}
    for f in ('launcherAmmoPairVerified','currentCharacterBuffsVerified','fullWeaponEffectsVerified',
              'aprPerSlotVerified','weaponSwitchAuthorized','dispatchAuthorized'):
        r3[f]=False
    ix={35:'SW1H04',36:'BOW05',37:None,38:'STAF01',11:None,12:'AROW01',13:None,14:None,9:'SHLD03A'}
    slots=[]
    for index,ref in ix.items():
        s={'slot':index,'resrefRaw':ref,'priorityEligible':False,'usableNowVerified':False}
        if ref:
            a=items[ref]['item']['abilities']
            s['staticItem']={'resource':ref,'resourceSha256AtR3Audit':'a'*64,
                             'currentResourceHashVerified':False,
                             'abilities':[{k:v for k,v in ab.items() if k not in ('effects',)} for ab in a]}
            s['blockedBy']=['UNVERIFIED']
        else: s['status']='EMPTY_AT_OBSERVED_SESSION'
        slots.append(s)
    r16={'schema':'BGXAI_ALTERNATE_SLOT_STATIC_EVIDENCE_RO_V1',
         'status':'PRIOR_STATIC_ITEM_FACTS_AND_CURRENT_SELECTION_AUDITED_RO',
         'input':{'r3Sha256':EXPECTED_R3_SHA,'logSha256':EXPECTED_LOG_SHA},
         'currentGameResourceRevalidated':False,'previousR3SnapshotIsSameActorAndSession':False,
         'weaponSwitchAuthorized':False,'fullLoadoutScoringAuthorized':False,
         'effectiveAlternateSlotAPRVerified':False,'launcherAmmoAssociationVerified':False,
         'actorId':actor,'previousR3ActorId':91,
         'selectedObservationCount':4,'snapshots':15,'slots':slots}
    n=0;rows=[]
    def line(marker,obj):rows.append('INFO: LUA: '+marker+' '+json.dumps(obj,separators=(',',':')))
    def r2(qty,action,slot):
        nonlocal n
        n+=1
        keys=[]
        for idx in (35,36,37,38):
            ref=ix[idx]
            keys.append({'index':idx,'resrefRaw':ref,'access':'OBJECT_RETURNED_UNVERIFIED' if ref else 'NULL'})
        quivers=[]
        for idx in (11,12,13,14):
            ref=ix[idx]
            quivers.append({'index':idx,'resrefRaw':ref,'useCount1Raw':qty if ref else None,
                            'access':'OBJECT_RETURNED_UNVERIFIED' if ref else 'NULL'})
        line('[BGXW2]',{'type':'SLOTS','actor':actor,'actionRaw':action,'selectedWeaponRaw':slot,
                        'seq':n,'quickWeapons':keys,'quivers':quivers})
    def defend(seq,slot):
        line('[BGXTD13]',{'type':'DEFENSE','sourceActor':actor,'targetActor':202,'rawActionId':3,
                           'selectedSlot':slot,'seq':seq,'status':'TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY',
                           'weaponSwitchAuthorized':False,'allProtectionsObserved':False,
                           'exactHitChanceProven':False,
                           'fields':{k:(10 if k=='m_nArmorClass' else 0) for k in (
                             'm_nArmorClass','m_nACCrushingMod','m_nACMissileMod',
                             'm_nACPiercingMod','m_nACSlashingMod','m_nResistCrushing',
                             'm_nResistPiercing','m_nResistSlashing','m_nResistMissile')}})
    for _ in range(4):r2(20,23,12)
    defend(1,12);r2(20,3,12);r2(19,23,12);r2(19,23,12)
    r2(20,23,12);r2(20,23,12)
    defend(2,12);r2(20,3,12);r2(18,23,12);r2(18,23,12)
    defend(3,12);r2(18,3,12);r2(17,23,12)
    defend(4,35);r2(17,3,35)
    return r3,r16,'\n'.join(rows)+'\n'


class R17Tests(unittest.TestCase):
    def setUp(self):
        self.r3,self.r16,self.log=fake()

    def run_a(self):return analyze(self.r3,self.r16,self.log,EXPECTED_R3_SHA,EXPECTED_LOG_SHA)

    def check_hold(self,reason):
        out=self.run_a()
        self.assertEqual(out['status'],'HOLD',out)
        self.assertEqual(out['reason'],reason)
        self.assertFalse(out['weaponSwitchAuthorized'])
        self.assertFalse(out['dispatchAuthorized'])

    def test_happy_source_only(self):
        out=self.run_a()
        self.assertEqual(out['status'],'STATIC_ABILITY_AND_LIVE_AMMO_WINDOW_CANDIDATES_RO')
        self.assertEqual([v['windowQuantityDecrease'] for v in out['ammoWindows']],[1,2,1])
        self.assertEqual(len(out['weaponSlots']),5)
        for k in ('nativeLauncherAmmoPairVerified','alternateSlotEffectiveAprVerified',
                  'activeEffectStateVerified','weaponSwitchAuthorized','dispatchAuthorized',
                  'weaponPriorityAuthorized','currentResourceHashVerified'):
            self.assertIs(out[k],False,k)

    def test_flat_bow_apr_not_bonus(self):
        out=self.run_a();self.assertEqual(out['weaponSlots'][36]['aprEffectModeRaw'],1)
        self.assertEqual(out['weaponSlots'][36]['aprEffectKeyRaw'],2)
        self.assertFalse(out['weaponSlots'][36]['aprEffectAdditiveDeltaAssumed'])

    def test_sword_onhit_not_priced_as_damage(self):
        q=self.run_a()['weaponSlots'][35]['abilityHeaders'][0]
        self.assertTrue(q['onHitSpellTriggerCandidate'])
        self.assertFalse(q['effectiveDamageVerified'])

    def test_bow_and_arrow_static_raw(self):
        x=self.run_a()['launcherAmmoStaticCompatibilityCandidate']
        self.assertEqual((x['launcherRangeRaw'],x['ammoRangeRaw']),(75,100))
        self.assertFalse(x['enginePairVerified']);self.assertFalse(x['effectiveRangeInEngineVerified'])

    def test_cross_session_never_same_actor(self):
        x=self.run_a()
        self.assertTrue(x['crossSessionPriorR3']);self.assertFalse(x['sameActorAsPriorR3'])

    def test_report_contains_all_slot_gaps(self):
        out=self.run_a()
        self.assertEqual(set(out['allSlotGaps']),{35,36,38,12,9})
        self.assertFalse(out['weaponSlots'][38]['effectiveSlotAprVerified'])

    def test_r3_sha_pin(self):
        x=analyze(self.r3,self.r16,self.log,'b'*64,EXPECTED_LOG_SHA)
        self.assertEqual(x['reason'],'FROZEN_R3_OR_RUNTIME_LOG_SHA_CHANGED')

    def test_runtime_sha_pin(self):
        x=analyze(self.r3,self.r16,self.log,EXPECTED_R3_SHA,'b'*64)
        self.assertEqual(x['reason'],'FROZEN_R3_OR_RUNTIME_LOG_SHA_CHANGED')

    def test_r3_does_not_promote_native_pair(self):
        self.r3['launcherAmmoPairVerified']=True;self.check_hold('R3_PROVENANCE_OR_FLAGS_INVALID')

    def test_r3_does_not_promote_buffs(self):
        self.r3['currentCharacterBuffsVerified']=True;self.check_hold('R3_PROVENANCE_OR_FLAGS_INVALID')

    def test_r16_does_not_promote_rank(self):
        self.r16['weaponSwitchAuthorized']=True;self.check_hold('R16_PROVENANCE_OR_FLAGS_INVALID')

    def test_previous_actor_different(self):
        self.r16['previousR3ActorId']=101;self.check_hold('ACTOR_CROSS_SESSION_GUARD')

    def test_slot_exact_set(self):
        self.r16['slots'].pop();self.check_hold('R16_SLOT_SET_INVALID')

    def test_priority_promotion_holds(self):
        self.r16['slots'][0]['priorityEligible']=True;self.check_hold('R16_ABILITY_PROMOTION_FORBIDDEN')

    def test_missing_resource(self):
        self.r3['items'].pop('BOW05');self.check_hold('R3_RESOURCE_MISSING')

    def test_resource_hash_drift(self):
        self.r16['slots'][1]['staticItem']['resourceSha256AtR3Audit']='b'*64
        self.check_hold('STATIC_RESOURCE_PROVENANCE_DRIFT')

    def test_changed_ability(self):
        self.r16['slots'][0]['staticItem']['abilities'][0]['rangeRaw']=999
        self.check_hold('R16_R3_ABILITY_FIELDS_CONFLICT')

    def test_bad_ability_type_holds(self):
        self.r3['items']['BOW05']['item']['abilities'][0]['attackTypeRaw']=-1
        self.check_hold('ABILITY_HEADER_INVALID')

    def test_bow_apr_opcode_changed(self):
        self.r3['items']['BOW05']['item']['equippedEffects'][0]['parameter2Raw']=0
        self.check_hold('BOW_APR_EFFECT_CHANGED')

    def test_bow_not_launcher(self):
        self.r3['items']['BOW05']['item']['abilities'][0]['attackTypeRaw']=1
        self.r16['slots'][1]['staticItem']['abilities'][0]['attackTypeRaw']=1
        self.check_hold('STATIC_BOW_AMMO_TYPE_CONFLICT')

    def test_no_log_action_pair(self):
        lines=self.log.splitlines(); i=next(i for i,s in enumerate(lines) if '"seq":5' in s and '[BGXW2]' in s)
        obj=json.loads(lines[i].split('[BGXW2] ',1)[1]);obj['actionRaw']=23
        lines[i]='INFO: LUA: [BGXW2] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('R13_R2_ACTION_ASSOCIATION_NOT_UNIQUE')

    def test_actor_mismatch_r2(self):
        lines=self.log.splitlines(); i=next(i for i,s in enumerate(lines) if '"seq":5' in s and '[BGXW2]' in s)
        obj=json.loads(lines[i].split('[BGXW2] ',1)[1]);obj['actor']=102
        lines[i]='INFO: LUA: [BGXW2] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('R13_R2_ACTION_ASSOCIATION_NOT_UNIQUE')

    def test_qty_decrement_not_seen(self):
        lines=self.log.splitlines(); i=next(i for i,s in enumerate(lines) if '"seq":6' in s and '[BGXW2]' in s)
        obj=json.loads(lines[i].split('[BGXW2] ',1)[1]);obj['quivers'][1]['useCount1Raw']=20
        lines[i]='INFO: LUA: [BGXW2] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('AMMO_DECREMENT_NOT_OBSERVED')

    def test_bow_mismatch_after_action(self):
        lines=self.log.splitlines(); i=next(i for i,s in enumerate(lines) if '"seq":6' in s and '[BGXW2]' in s)
        obj=json.loads(lines[i].split('[BGXW2] ',1)[1]);obj['quickWeapons'][1]['resrefRaw']='STAF01'
        lines[i]='INFO: LUA: [BGXW2] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('AMMO_OR_BOW_SNAPSHOT_CHANGED')


    def test_missing_defense_fields_holds(self):
        lines=self.log.splitlines();i=next(i for i,s in enumerate(lines) if '[BGXTD13]' in s)
        obj=json.loads(lines[i].split('[BGXTD13] ',1)[1]);obj['fields'].pop('m_nArmorClass')
        lines[i]='INFO: LUA: [BGXTD13] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('R13_DEFENSE_FIELD_PROVENANCE_INVALID')

    def test_false_weapon_authority_holds(self):
        lines=self.log.splitlines();i=next(i for i,s in enumerate(lines) if '[BGXTD13]' in s)
        obj=json.loads(lines[i].split('[BGXTD13] ',1)[1]);obj['weaponSwitchAuthorized']=True
        lines[i]='INFO: LUA: [BGXTD13] '+json.dumps(obj)
        self.log='\n'.join(lines)+'\n';self.check_hold('R13_DEFENSE_FIELD_PROVENANCE_INVALID')

    def test_untrusted_log_json(self):
        self.log+='INFO: LUA: [BGXW2] {'
        self.check_hold('INVALID_R2_JSON')

    def test_genuinely_different_source_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fake';p.write_text('{}',encoding='utf-8')
            self.assertEqual(analyze_files(p,p,p)['reason'],'FROZEN_R3_OR_RUNTIME_LOG_SHA_CHANGED')

    @unittest.skipUnless(hasattr(os,'symlink'),'symlinks unavailable')
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'file';p.write_text('test',encoding='utf-8')
            q=Path(tmp)/'alias'
            try:os.symlink(p,q)
            except (OSError,NotImplementedError):self.skipTest('symlink restricted')
            with self.assertRaisesRegex(ValueError,'INPUT_MISSING_OR_SYMLINK'):_load_file(q)

    def test_real_fixture_available_only_locally(self):
        # The raw user console and current-game R3 are intentionally never bundled
        # into GitHub or test distribution; the uploaded R17 report is derived only.
        source=(ROOT/'BGXAI_ABILITY_AMMO_CONTRACT_R17_RO.py').read_text()
        self.assertNotIn('import subprocess',source)
        self.assertNotIn('SelectWeaponAbility(',source)
        self.assertNotIn('ClearActions(',source)


if __name__=='__main__':unittest.main()
