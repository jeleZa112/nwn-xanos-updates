import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import BGXAI_WEAPON_LIVE_PAIR_R1_R2_READONLY as M

def slot(i,ref,count=0):
    if ref is None:
        return dict(index=i,access='NULL',resrefRaw=None,useCount1Raw=None,useCount2Raw=None,useCount3Raw=None,
                    flagsRaw=None,identityVerified=False,usableVerified=False,ammoVerified=False)
    return dict(index=i,access='OBJECT_RETURNED_UNVERIFIED',resrefRaw=ref,useCount1Raw=count,
                useCount2Raw=1 if i==12 else 0,useCount3Raw=1 if i==12 else 0,flagsRaw=1,
                identityVerified=False,usableVerified=False,ammoVerified=False)


def synthetic_live_shape():
    # Independent portable synthetic fixture derived from the documented shape,
    # not a copy of a user's private console log or an executable game command.
    r1,r2={},{}
    actions=[30,30,115,160,269,23,174,105,149,134]
    for seq,action in enumerate(actions,1):
        selected=38 if seq<=7 else 12 if seq<=9 else 35
        apr=1 if seq<=7 else 2 if seq<=9 else 7
        flags=dict(itemIdentityVerified=False,perSlotAPRVerified=False,
                   manualOrderOriginVerified=False,epsQueueVerified=False,switchAuthorized=False)
        r2[seq]=dict(type='SLOTS',schema=M.SCHEMA_R2,seq=seq,partyIndex=2,actor=139135050,
                     actionRaw=action,selectedWeaponRaw=selected,selectedAbilityRaw=0,
                     status='RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN',
                     quickWeapons=[slot(35,'SW1H04'),slot(36,'BOW05'),slot(37,None),slot(38,'STAF01')],
                     quivers=[slot(11,None),slot(12,'AROW01',20 if seq<=8 else 18),slot(13,None),slot(14,None)],
                     offhand=slot(9,'SHLD03A'),**flags)
        r1[seq]=dict(type='ACTION',sequence=seq,partyIndex=2,actor=139135050,action=action,
                     selectedWeaponRaw=selected,aprRaw=apr,thac0Raw=20,strengthRaw=15,dexRaw=16,
                     improvedHasteRaw=0,weaponAbilityVerified=False,actualPerSlotAPRVerified=False,
                     buffsExhaustivelyObserved=False,manualOrderOriginVerified=False,epsQueueVerified=False,
                     weaponSwitchAuthorized=False)
    return r1,r2


class PairTests(unittest.TestCase):
    def setUp(self):
        self.r1,self.r2=synthetic_live_shape()

    def test_portable_synthetic_shape_matching_real_scenario(self):
        p=M.pair(self.r1,self.r2)
        self.assertEqual(p['pairedActions'],10)
        self.assertEqual(p['actor'],139135050)
        self.assertEqual([(x['from'],x['to']) for x in p['selectedSlotTransitions']],[(38,12),(12,35)])
        self.assertEqual(p['ammoCountChanges'],[{'seq':9,'counts':{'12':-2}}])
        self.assertTrue(p['loadoutResrefsConstantAcrossSnapshots'])
        self.assertFalse(p['dispatchAuthorized'])
        self.assertFalse(p['effectivePerSlotAPRVerified'])
        self.assertFalse(p['manualAndEPSQueueStateVerified'])

    def test_snapshot_selected_apr_for_exact_raw(self):
        p=M.pair(self.r1,self.r2)
        self.assertEqual({k:sorted({e['aprRaw'] for e in es}) for k,es in p['selectedSnapshotsBySlotRaw'].items()},
                         {'38':[1],'12':[2],'35':[7]})
        self.assertEqual(p['observations'][7]['selectedKind'],'AMMO_SLOT_LAUNCHER_UNVERIFIED')
        self.assertEqual(p['observations'][7]['selectedResrefRaw'],'AROW01')
        self.assertEqual(p['observations'][9]['selectedResrefRaw'],'SW1H04')

    def test_file_parser_with_portable_synthetic_r2(self):
        session={'type':'SESSION','schema':M.SCHEMA_R2,'readOnly':True}
        ready={'type':'READY','schema':M.SCHEMA_R2,'hookRegistered':True}
        data=[session,ready,*self.r2.values()]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r2.jsonl'
            p.write_text('\n'.join(json.dumps(x) for x in data)+'\n')
            self.assertEqual(len(M.read_r2(p)),10)

    def test_console_parser_deduplicates_print_and_log(self):
        session={'type':'SESSION','schema':M.SCHEMA_R1,'readOnly':True}
        ready={'type':'READY','schema':M.SCHEMA_R1,'observerRegistered':True}
        data=[session,session,ready,ready,self.r1[1],self.r1[1]]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'console.log'
            p.write_text('\n'.join('INFO: LUA: [BGXWP] '+json.dumps(x) for x in data)+'\n')
            self.assertEqual(list(M.read_r1_console(p)),[1])

    def test_wrong_actor_rejected(self):
        r=copy.deepcopy(self.r1);r[2]['actor']+=1
        with self.assertRaisesRegex(M.EvidenceError,'MISMATCH'):M.pair(r,self.r2)

    def test_wrong_action_rejected(self):
        r=copy.deepcopy(self.r1);r[2]['action']+=1
        with self.assertRaisesRegex(M.EvidenceError,'MISMATCH'):M.pair(r,self.r2)

    def test_wrong_selection_rejected(self):
        r=copy.deepcopy(self.r1);r[8]['selectedWeaponRaw']=35
        with self.assertRaisesRegex(M.EvidenceError,'MISMATCH'):M.pair(r,self.r2)

    def test_sequence_mismatch_rejected(self):
        r=copy.deepcopy(self.r1);r.pop(3)
        with self.assertRaisesRegex(M.EvidenceError,'SEQUENCE_SET_MISMATCH'):M.pair(r,self.r2)

    def test_invalid_int_bool_rejected(self):
        x=copy.deepcopy(self.r2[1]);x['seq']=True
        with self.assertRaisesRegex(M.EvidenceError,'ID_OR_SEQUENCE_INVALID'):M._checked_r2(x)

    def test_r2_no_verified_bypass(self):
        x=copy.deepcopy(self.r2[1]);x['switchAuthorized']=True
        with self.assertRaisesRegex(M.EvidenceError,'UNPROVEN_FIELD_CLAIM'):M._checked_r2(x)

    def test_r1_no_verified_bypass(self):
        x=copy.deepcopy(self.r1[1]);x['weaponSwitchAuthorized']=True
        with self.assertRaisesRegex(M.EvidenceError,'UNPROVEN_FIELD_CLAIM'):M._checked_r1(x)

    def test_resref_validation_rejects_arbitrary_text(self):
        x=copy.deepcopy(self.r2[1]);x['quickWeapons'][0]['resrefRaw']='BAD;EXEC'
        with self.assertRaisesRegex(M.EvidenceError,'WEAPON_SLOTS_INVALID'):M._checked_r2(x)

    def test_slot_sequence_rejects_wrong_index(self):
        x=copy.deepcopy(self.r2[1]);x['quivers'][0]['index']=100
        with self.assertRaisesRegex(M.EvidenceError,'QUIVER_SLOTS_INVALID'):M._checked_r2(x)

    def test_no_other_slot_apr_by_mistake(self):
        p=M.pair(self.r1,self.r2)
        self.assertNotIn('36',p['selectedSnapshotsBySlotRaw'])
        self.assertNotIn('37',p['selectedSnapshotsBySlotRaw'])
        self.assertFalse(p['launcherAmmoAbilityMatched'])

    def test_empty_or_changed_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'empty.txt';p.write_text('')
            with self.assertRaisesRegex(M.EvidenceError,'SIZE_HOLD'):M.regular_bytes(p)

    def test_conflicting_duplicate_sequence_rejected(self):
        e=copy.deepcopy(self.r1[1]);e['aprRaw']=-3
        session={'type':'SESSION','schema':M.SCHEMA_R1,'readOnly':True}
        ready={'type':'READY','schema':M.SCHEMA_R1,'observerRegistered':True}
        with self.assertRaisesRegex(M.EvidenceError,'CONFLICTING_SEQUENCE'):
            M._extract_session([session,ready,self.r1[1],e],M.SCHEMA_R1,'ACTION','sequence','observerRegistered','R1')

    def test_restart_session_resets_records(self):
        session={'type':'SESSION','schema':M.SCHEMA_R1,'readOnly':True}
        ready={'type':'READY','schema':M.SCHEMA_R1,'observerRegistered':True}
        data=M._extract_session([session,ready,self.r1[1],session,ready,self.r1[1]],M.SCHEMA_R1,'ACTION','sequence','observerRegistered','R1')
        self.assertEqual(list(data),[1])

    def test_unknown_item_still_unverified(self):
        r2=copy.deepcopy(self.r2)
        r2[1]['quickWeapons'][0]['resrefRaw']='X1234567'
        p=M.pair(self.r1,r2)
        self.assertFalse(p['dispatchAuthorized'])
        self.assertFalse(p['targetDefenseVerified'])
        self.assertFalse(p['activeBuffsComplete'])
        self.assertFalse(p['perWeaponDamageVerified'])
        self.assertFalse(p['loadoutResrefsConstantAcrossSnapshots'])

if __name__=='__main__':
    unittest.main(verbosity=2)
