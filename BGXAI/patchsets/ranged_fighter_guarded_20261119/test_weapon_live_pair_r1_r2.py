import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import BGXAI_WEAPON_LIVE_PAIR_R1_R2_READONLY as M

R2_PATH=Path('/mnt/data/BGXAI_WEAPON_SLOTS_RAW_R2.jsonl')
CONSOLE_PATH=Path('/mnt/data/BGXAI_WEAPON_CONSOLE_20261121T132309314256Z.log')

class PairTests(unittest.TestCase):
    def setUp(self):
        self.r2=M.read_r2(R2_PATH)
        self.r1=M.read_r1_console(CONSOLE_PATH)

    def test_actual_user_game_log_pair(self):
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
