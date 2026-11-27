"""Synthetic adversarial tests for existing R38+R3 evidence join. NO private input."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import R39_JOIN_EXISTING_R38_R3_RO as g


def item():
    return {
        'schema':'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY',
        'status':'ITM_NATIVE_ALL_ITEMS_RAW_READ',
        'sourceKind':'CURRENT_GAME','gameModified':False,
        'dispatchAuthorized':False,
        'items':{'STAF01':{
            'provenance':{'origin':'CURRENT_GAME_OVERRIDE','sha256':g.ITEM_SHA},
            'item':{'schema':'BGXAI_ITM_RAW_V1','itemTypeRaw':26,
                    'twoHandedFlagRaw':True,'minStrengthRaw':5,'itemFlagsRaw':46,
                    'rawOnly':True,'characterCanEquipVerified':False,
                    'abilities':[{'attackTypeRaw':1}]}}},
    }


def pair(i, outsider=False):
    party=2 if outsider else 1
    actor=654321 if outsider else 123456
    x={'schema':g.PREFIXES['[BGXR27] '],'type':'R27_SINGLE_CALLBACK',
       'readOnly':True,'dispatchAuthorized':False,'weaponSwitchAuthorized':False,
       'ordersSent':0,'seq':i,'partyIndex':party,'actor':actor,
       'rawInventoryDoubleReadConsistent':True,
       'selectedDerivedStatsDoubleReadConsistent':True,
       'sameLuaListenerInvocation':True,
       'actionOriginVerified':False,'manualEpsQueueVerified':False,
       'aiObjectClassRawCandidate':3,'levelsAndKitRaw':{'kitRaw':16384},
       'selectedStatsRaw':{'m_nSTR':12},
       'offhandRaw':[{'slot':9,'resrefRaw':None}],
       'quickWeaponsRaw':[{'slot':35,'resrefRaw':None}]}
    y={'schema':g.PREFIXES['[BGXID] '],'type':'IDENTITY_ADVISORY',
       'readOnly':True,'dispatchAuthorized':False,'armAuthorized':False,
       'ordersSent':0,'seq':i,'partyIndex':party,
       'status':('HOLD_WRONG_PORTRAIT_CONTEXT' if outsider else
                 'RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM')}
    return x,y


def context():
    a,b={},{}
    for i in range(1,35):
        x,y=pair(i,outsider=(i not in list(range(17,25))+[33,34]))
        a[i]=x;b[i]=y
    return {'[BGXR27] ':a,'[BGXID] ':b}


class EvidenceJoin(unittest.TestCase):
    def setUp(self):
        self.item=g.check_item(item())
        self.ctx=context()

    def assertHold(self,ctx=None,it=None):
        with self.assertRaises(g.Hold): g.evaluate(self.ctx if ctx is None else ctx,
                                                     self.item if it is None else it)

    def test_exact_status_proves_only_physical(self):
        result=g.evaluate(self.ctx,self.item)
        self.assertEqual(result['status'],'PASS_OBSERVED_STRENGTH_AND_PHYSICAL_SLOTS_USABILITY_UNPROVEN')
        self.assertEqual(result['jaganMatchingEvents'],10)
        self.assertEqual(result['otherActorEventsFiltered'],24)
        self.assertEqual(result['r38AlignedEvents'],34)
        self.assertTrue(result['offhandSlot9EmptyInAllJaganEvents'])
        self.assertTrue(result['targetSlot35EmptyInAllJaganEvents'])
        self.assertEqual(result['observedStrengthRange'],[12,12])

    def test_never_authorizes_engine(self):
        r=g.evaluate(self.ctx,self.item)
        for k in ('gameModified','liveXEquipTransferVerified','dispatchAuthorized',
                  'armAuthorized','itemClassKitRestrictionBitsVerified',
                  'currentEffectBlocksEquippingVerified','gameIdleAtDispatchVerified',
                  'actorRuntimeArmingImplemented','sameSessionInstalledItemResourceVerified'):
            self.assertIs(r[k],False,k)
        self.assertEqual(r['ordersSent'],0)

    def test_no_private_actor_id_in_result(self):
        t=json.dumps(g.evaluate(self.ctx,self.item))
        self.assertNotIn('123456',t)
        self.assertNotIn('654321',t)
        self.assertNotIn('C:',t)

    def test_item_pin_drift(self):
        v=item();v['items']['STAF01']['provenance']['sha256']='bad'
        with self.assertRaises(g.Hold):g.check_item(v)

    def test_wrong_item_origin(self):
        v=item();v['items']['STAF01']['provenance']['origin']='UNKNOWN'
        with self.assertRaises(g.Hold):g.check_item(v)

    def test_source_has_dispatched_actions(self):
        v=item();v['dispatchAuthorized']=True
        with self.assertRaises(g.Hold):g.check_item(v)

    def test_str_too_low(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][18]['selectedStatsRaw']['m_nSTR']=4
        self.assertHold(v)

    def test_offhand_shield_blocks(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][23]['offhandRaw'][0]['resrefRaw']='SHLD03A'
        self.assertHold(v)

    def test_slot_occupied_blocks(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][34]['quickWeaponsRaw'][0]['resrefRaw']='STAF01'
        self.assertHold(v)

    def test_mismatch_identity_actor(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][22]['actor']=99
        self.assertHold(v)

    def test_outsider_shares_actor(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][4]['actor']=123456
        self.assertHold(v)

    def test_second_party_slot(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][17]['partyIndex']=2;v['[BGXID] '][17]['partyIndex']=2
        self.assertHold(v)

    def test_malformed_identity(self):
        v=copy.deepcopy(self.ctx);v['[BGXID] '][33]['status']='RANDOM_UNKNOWN'
        self.assertHold(v)

    def test_actor_class_or_kit_drift(self):
        for field in ('aiObjectClassRawCandidate','levelsAndKitRaw'):
            v=copy.deepcopy(self.ctx)
            v['[BGXR27] '][17][field]=None
            with self.subTest(field=field),self.assertRaises(g.Hold):
                g.evaluate(v,self.item)

    def test_missing_event_fails(self):
        v=copy.deepcopy(self.ctx);del v['[BGXID] '][34]
        self.assertHold(v)

    def test_unstable_snapshot_fails(self):
        v=copy.deepcopy(self.ctx);v['[BGXR27] '][33]['rawInventoryDoubleReadConsistent']=False
        self.assertHold(v)

    def test_mock_capture_roundtrip(self):
        v=context()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'capture.log'
            with p.open('w',encoding='utf-8') as out:
                out.write('[BGXR27] '+json.dumps({'schema':g.PREFIXES['[BGXR27] '],'type':'SESSION'})+'\n')
                for i in range(1,35):
                    for key in g.PREFIXES:
                        out.write('2026-11-27 '+key+json.dumps(v[key][i])+'\n')
            got=g.raw_events(p)
            self.assertEqual(g.evaluate(got,self.item)['jaganMatchingEvents'],10)

    def test_duplicate_seq_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'capture.log';v=context()
            x=v['[BGXR27] '][17]
            with p.open('w',encoding='utf-8') as out:
                out.write('[BGXR27] '+json.dumps({'schema':g.PREFIXES['[BGXR27] '],'type':'SESSION'})+'\n')
                out.write('[BGXR27] '+json.dumps(x)+'\n')
                out.write('[BGXR27] '+json.dumps(x)+'\n')
            with self.assertRaises(g.Hold):g.raw_events(p)

    def test_no_source_ingame_mutations(self):
        t=Path(g.__file__).read_text('utf-8')
        self.assertNotIn('XEquipItem(',t)
        self.assertNotIn('SetGlobal(',t)
        self.assertNotIn('EEex_Action_AddSpriteStartedActionListener(',t)
        self.assertNotIn('winreg',t)


if __name__=='__main__':unittest.main()
