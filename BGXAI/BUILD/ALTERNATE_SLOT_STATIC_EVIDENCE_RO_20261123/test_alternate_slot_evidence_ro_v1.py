"""Offline contract tests: no actual EET/EEex needed, no dispatch."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from fractions import Fraction

from BGXAI_ALTERNATE_SLOT_EVIDENCE_RO_V1 import analyze, parse_r2, _slot_map, _static, R3_FROZEN_SHA


def fake_item(ref, ability_type, twohand=False, onhit=False, apr=False):
    effect=[{'opcodeRaw':146,'resourceRaw':'SW1H04'}] if onhit else []
    return {'resource':ref, 'provenance':{'origin':'CURRENT_GAME_OVERRIDE', 'sha256':'b'*64},
        'item':{'schema':'BGXAI_ITM_RAW_V1','rawOnly':True,'itemTypeRaw':20,
                'characterCanEquipVerified':False,'targetImmunityVerified':False,
                'activeBuffsVerified':False,'proficiencyIdRaw':90,'minStrengthRaw':5,
                'twoHandedFlagRaw':twohand,'enchantmentRaw':0,
                'abilities':[{'abilityIndex':0,'attackTypeRaw':ability_type,'rangeRaw':75,
                    'speedRaw':5,'damageTypeRaw':3,'thac0BonusRaw':0,
                    'launcherRequiredRaw':1 if ability_type==2 else 0,
                    'diceCountRaw':1,'diceSidesRaw':6,'damageBonusRaw':0,
                    'baseDamageMeanBeforeEffects':3.5,'effects':effect}],
                'equippedEffects':[{'opcodeRaw':1,'parameter1Raw':2,'parameter2Raw':1}] if apr else []}}


def r3():
    names={'SW1H04':(1,False,True,False),'BOW05':(4,True,False,True),
           'STAF01':(1,True,False,False),'AROW01':(2,False,False,False),
           'SHLD03A':(0,False,False,False)}
    return {'schema':'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY','status':'ITM_NATIVE_ALL_ITEMS_RAW_READ',
        'sourceKind':'CURRENT_GAME','gameModified':False,'weaponSwitchAuthorized':False,
        'launcherAmmoPairVerified':False,'aprPerSlotVerified':False,
        'targetImmuneOrResistantVerified':False,'currentCharacterBuffsVerified':False,
        'proficiencyAlreadyAppliedVerified':False,'fullWeaponEffectsVerified':False,
        'manualAndEPSQueueVerified':False,'missingItemsOrLinkedSpells':[],
        'r2SnapshotSummary':{'lastActor':11111},
        'requestedItems':list(names),'items':{k:fake_item(k,*v) for k,v in names.items()}}


def row(index,ref,quantity=20,empty=False):
    return {'index':index,'access':'NULL' if empty else 'OBJECT_RETURNED_UNVERIFIED',
            'resrefRaw':None if empty else ref,
            'identityVerified':False,'usableVerified':False,'ammoVerified':False,
            'useCount1Raw':None if empty else quantity}


def r2(seq,action,selected,quantity=20):
    return {'type':'SLOTS','schema':'BGXAI_WEAPON_SLOTS_RAW_R2','seq':seq,'partyIndex':2,
        'actor':22222,'actionRaw':action,'selectedWeaponRaw':selected,
        'itemIdentityVerified':False,'perSlotAPRVerified':False,'switchAuthorized':False,
        'quickWeapons':[row(35,'SW1H04'),row(36,'BOW05'),row(37,None,empty=True),row(38,'STAF01')],
        'quivers':[row(11,None,empty=True),row(12,'AROW01',quantity),
                   row(13,None,empty=True),row(14,None,empty=True)],
        'offhand':row(9,'SHLD03A')}


def scene():
    # R13 event immediately before the corresponding R2 action 3, other action 23 in between.
    lines=['INFO: LUA: [BGXTD13] {"type":"DEFENSE"}',
           'INFO: LUA: [BGXW2] '+json.dumps(r2(1,3,12,20)),
           'INFO: LUA: [BGXW2] '+json.dumps(r2(2,23,12,19)),
           'INFO: LUA: [BGXTD13] {"type":"DEFENSE"}',
           'INFO: LUA: [BGXW2] '+json.dumps(r2(3,3,35,19))]
    log='\n'.join(lines)+'\n'
    sha=hashlib.sha256(log.encode()).hexdigest()
    base={'status':'CURRENT_SELECTED_EVIDENCE_CANDIDATE_RO','actor':22222,
          'weaponSwitchAuthorized':False,'pairingAuthenticated':False,
          'alternateSlotAprVerified':False,'action':3}
    selected={'schema':'BGXAI_SELECTED_SLOT_EVIDENCE_BRIDGE_RO_V1',
              'status':'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO','inputSha256':sha,
              'currentSelectionOnly':True,'weaponSwitchAuthorized':False,
              'alternateSlotAprVerified':False,'matchedByNativeEventId':False,
              'observations':[{**base,'line':1,'r13Sequence':1,'selectedSlot':12,
                               'sourceItemRefRaw':'AROW01','sourceAprKey':2,'sourceAprValue':'2'},
                              {**base,'line':4,'r13Sequence':2,'selectedSlot':35,
                               'sourceItemRefRaw':'SW1H04','sourceAprKey':7,'sourceAprValue':'3/2'}]}
    return log,sha,r3(),selected


class AlternateSlotSourceOnlyTests(unittest.TestCase):
    def setUp(self):
        self.log,self.sha,self.native,self.selected=scene()

    def analyze(self):
        return analyze(self.log,self.sha,self.native,R3_FROZEN_SHA,self.selected)

    def test_synthetic_full_matrix(self):
        d=self.analyze()
        self.assertEqual(d['status'],'PRIOR_STATIC_ITEM_FACTS_AND_CURRENT_SELECTION_AUDITED_RO')
        self.assertEqual(len(d['slots']),9)
        self.assertEqual(d['candidateCount'],5)

    def test_alternate_bow_and_staff_never_get_synthetic_apr(self):
        s={v['slot']:v for v in self.analyze()['slots']}
        self.assertFalse(s[36]['selectedAprSamples'])
        self.assertFalse(s[38]['selectedAprSamples'])
        self.assertFalse(s[36]['alternateSlotAprVerified'])
        self.assertTrue(s[35]['selectedAprSamples'][0]['value']=='3/2')
        self.assertTrue(s[12]['selectedAprSamples'][0]['value']=='2')

    def test_prior_static_hash_does_not_grant_current_equip(self):
        d=self.analyze()
        self.assertFalse(d['currentGameResourceRevalidated'])
        self.assertFalse(d['previousR3SnapshotIsSameActorAndSession'])
        self.assertFalse(d['fullLoadoutScoringAuthorized'])
        self.assertFalse(d['weaponSwitchAuthorized'])

    def test_equipped_apr_effect_is_not_counted_twice(self):
        s={v['slot']:v for v in self.analyze()['slots']}
        self.assertEqual(s[36]['staticItem']['aprEquippedOverrideRaw'][0]['valueRaw'],2)
        self.assertIn('EQUIPPED_APR_EFFECT_FLAT_OR_ADDITIVE_NOT_REAPPLIED',s[36]['blockedBy'])

    def test_on_hit_weapon_special_not_priced(self):
        s={v['slot']:v for v in self.analyze()['slots']}
        self.assertTrue(s[35]['staticItem']['hasOnHitScriptEffectCandidate'])
        self.assertIn('ON_HIT_EFFECT_SPECIAL_AND_BREAKAGE_NOT_PRICED',s[35]['blockedBy'])

    def test_shield_and_two_hand_ambiguity(self):
        s={v['slot']:v for v in self.analyze()['slots']}
        for slot in (36,38):
            self.assertIn('TWO_HANDED_WITH_SHIELD_ACTIVE_STATE_UNKNOWN',s[slot]['blockedBy'])

    def test_empty_slot_never_rankable(self):
        s={v['slot']:v for v in self.analyze()['slots']}
        self.assertEqual(s[37]['status'],'EMPTY_AT_OBSERVED_SESSION')
        self.assertFalse(s[37]['priorityEligible'])

    def test_ammo_increase_flags_restocks_not_verified_reload(self):
        d=self.analyze()
        self.assertEqual(d['ammoResetCandidates'],[])
        # Changing count across snapshots 19 to 20 can suggest a reload/restock.
        r=r2(3,3,35,20)
        self.log=self.log.replace(json.dumps(r2(3,3,35,19)),json.dumps(r))
        self.sha=hashlib.sha256(self.log.encode()).hexdigest()
        self.selected['inputSha256']=self.sha
        self.assertEqual(len(self.analyze()['ammoResetCandidates']),1)

    def test_r3_sha_mismatch_holds(self):
        self.assertEqual(analyze(self.log,self.sha,self.native,'a'*64,self.selected)['status'],'HOLD')

    def test_selected_input_sha_mismatch_holds(self):
        self.selected['inputSha256']='f'*64
        self.assertEqual(self.analyze()['reason'],'SELECTED_OBSERVATIONS_UNTRUSTED_OR_DIFFERENT_LOG')

    def test_selected_apr_key_to_value_mismatch_holds(self):
        self.selected['observations'][1]['sourceAprValue']='2'
        self.assertEqual(self.analyze()['reason'],'SELECTED_APR_SAMPLE_INVALID')

    def test_actor_collision_holds(self):
        self.selected['observations'][1]['actor']=1234
        self.assertEqual(self.analyze()['reason'],'SELECTED_OBSERVATION_CONTRACT_INVALID')

    def test_r2_flag_claims_verification_holds(self):
        self.log=self.log.replace('"itemIdentityVerified": false','"itemIdentityVerified": true',1)
        self.sha=hashlib.sha256(self.log.encode()).hexdigest()
        self.selected['inputSha256']=self.sha
        self.assertEqual(self.analyze()['reason'],'R2_SESSION_ACTOR_SEQUENCE_OR_FLAGS_CONFLICT')

    def test_r3_forged_protection_flag_holds(self):
        self.native['fullWeaponEffectsVerified']=True
        self.assertEqual(self.analyze()['reason'],'R3_SOURCE_FLAGS_UNEXPECTED')

    def test_gear_resref_change_holds(self):
        self.log=self.log.replace('"resrefRaw": "STAF01"','"resrefRaw": "DIFF01"',1)
        self.sha=hashlib.sha256(self.log.encode()).hexdigest()
        self.selected['inputSha256']=self.sha
        self.assertEqual(self.analyze()['reason'],'GEAR_IDENTITY_CHANGED_DURING_SESSION')

    def test_missing_prior_resource_holds(self):
        self.native['items'].pop('BOW05')
        self.assertEqual(self.analyze()['reason'],'R3_NO_MATCHING_RESOURCE')

    def test_bad_selected_item_binding_holds(self):
        self.selected['observations'][0]['sourceItemRefRaw']='BOW05'
        self.assertEqual(self.analyze()['reason'],'SELECTED_ITEM_REF_MISMATCH')

    def test_r2_duplicate_ambiguous_event_holds(self):
        self.log+='INFO: LUA: [BGXW2] '+json.dumps(r2(4,3,35,19))+'\n'
        self.sha=hashlib.sha256(self.log.encode()).hexdigest()
        self.selected['inputSha256']=self.sha
        self.assertEqual(self.analyze()['reason'],'SELECTED_AND_R2_SNAPSHOT_NOT_UNIQUELY_ALIGNED')

    def test_no_r2_holds(self):
        self.log='INFO: LUA: [BGXTD13] {"type":"READY"}\n'
        self.sha=hashlib.sha256(self.log.encode()).hexdigest()
        self.selected['inputSha256']=self.sha
        self.assertEqual(self.analyze()['reason'],'NO_R2_GEAR_SNAPSHOTS')

    def test_parsing_invalid_json_refuses(self):
        with self.assertRaisesRegex(ValueError,'INVALID_R2_JSON'):
            parse_r2('INFO: LUA: [BGXW2] {"type":"SLOTS",BAD}\n')

    def test_resref_requires_readable_item(self):
        d=r2(1,3,12)
        d['quickWeapons'][0]['resrefRaw']='VERY_LONG_123456'
        with self.assertRaisesRegex(ValueError,'R2_ITEM_RESREF_INVALID'):
            _slot_map(d)

    def test_static_ability_does_not_assign_usable(self):
        x=_static(self.native,'SW1H04')
        self.assertFalse(x['abilityUsableNowVerified'])
        self.assertFalse(x['effectiveDamageVerified'])
        self.assertFalse(x['currentResourceHashVerified'])

    def test_no_engine_calls_in_module(self):
        src=Path(__file__).with_name('BGXAI_ALTERNATE_SLOT_EVIDENCE_RO_V1.py').read_text()
        for banned in ('ClearActions(', 'SelectWeaponAbility(', 'subprocess.', 'os.system(', 'WeiDU', 'IEex_Sprite_Set'):
            self.assertNotIn(banned,src)


if __name__=='__main__':
    unittest.main()
