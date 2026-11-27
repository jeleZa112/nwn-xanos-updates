#!/usr/bin/env python3
"""Unit-level invariants; no engine compile or game I/O."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import BGXAI_R39_STAGED_XEQUIP_V1 as p


class Staged(unittest.TestCase):
    def setUp(self):
        self.m = copy.deepcopy(p.REQUIRED)
        self.b = p.render(self.m)

    def test_committed_candidate_baf_exact(self):
        path = Path(__file__).with_name('BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf')
        self.assertEqual(path.read_bytes(), self.b.encode('ascii'))

    def test_baseline_manifest(self):
        self.assertEqual(p.verified_manifest(self.m), self.m)
    def test_tag_matches_v3(self):
        self.assertEqual(p.witness(self.m), 2110908191)
    def test_mutated_manifest_rejected(self):
        for k in p.REQUIRED:
            m = copy.deepcopy(self.m); m[k] = True
            with self.subTest(k=k), self.assertRaises(p.Hold):p.render(m)
    def test_extra_actorid_or_approval_rejected(self):
        for k in ('actorId', 'installApproved', 'sessionToken'):
            m = copy.deepcopy(self.m); m[k]=123
            with self.subTest(k=k), self.assertRaises(p.Hold):p.render(m)
    def test_missing_field_rejected(self):
        for k in p.REQUIRED:
            m = copy.deepcopy(self.m); del m[k]
            with self.subTest(k=k), self.assertRaises(p.Hold):p.render(m)
    def test_correct_actor_local_safety(self):
        self.assertEqual(self.b.count('InPartySlot(Myself,1)'), 2)
        self.assertEqual(self.b.count('Global("BGXW3ARM","LOCALS",1)'),3)
        self.assertNotIn('"GLOBAL"',self.b)
    def test_same_item_and_empty_target_twice(self):
        self.assertEqual(self.b.count('CheckItemSlot(Myself,"STAF01",SLOT_MISC5)'),2)
        self.assertEqual(self.b.count('!HasItemSlot(Myself,SLOT_WEAPON0)'),2)
    def test_actions_once_and_disarmed_first(self):
        self.assertEqual(self.b.count('XEquipItem('),1)
        e=self.b.index('XEquipItem(')
        for action in ('SetGlobal("BGXW3ARM","LOCALS",2)',
                       'SetGlobal("BGXW3TAG","LOCALS",0)',
                       'SetGlobal("BGXW3TRY","LOCALS",1)'):
            self.assertLess(self.b.index(action),e)
    def test_no_self_arming(self):
        self.assertNotIn('SetGlobal("BGXW3ARM","LOCALS",1)',self.b)
        self.assertNotIn('SetGlobal("BGXW3TAG","LOCALS",2110908191)',self.b)
    def test_no_disruptive_actions(self):
        for token in p.BLOCKED:
            with self.subTest(token=token):self.assertNotIn(token,self.b)
    def test_very_first_block_abort_expired(self):
        blocks=self.b.split('\nIF\n')
        self.assertTrue('GlobalTimerExpired("BGXW3MAX","LOCALS")' in blocks[1])
        self.assertNotIn('XEquipItem(',blocks[1])
    def test_window_rechecked_before_command(self):
        blocks=self.b.split('\nIF\n')
        self.assertEqual(len(blocks),4)
        self.assertIn('GlobalTimerExpired("BGXW3QTM","LOCALS")',blocks[2])
        self.assertIn('GlobalTimerNotExpired("BGXW3MAX","LOCALS")',blocks[2])
        self.assertIn('XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)',blocks[2])
    def test_pending_stage_requires_external_local_arm(self):
        self.assertIn('Global("BGXW3QST","LOCALS",0)',self.b)
        self.assertIn('Global("BGXW3QST","LOCALS",1)',self.b)
        self.assertIn('SetGlobal("BGXW3QST","LOCALS",2)',self.b)
    def test_warmup_and_deadline_correct_ids(self):
        self.assertIn('SetGlobalTimer("BGXW3QTM","LOCALS",ONE_ROUND)',self.b)
        self.assertIn('SetGlobalTimer("BGXW3MAX","LOCALS",TWO_ROUNDS)',self.b)
    def test_no_baf_authorization(self):
        a=p.audit(self.m)
        for k in ('selfArmingPresent','sessionBoundArmerImplemented',
                  'currentSessionMatchesGamVerified','kitItmUsabilityVerified',
                  'manualEpsOriginVerified','engineQuiescenceVerified',
                  'nativeActiveBafCompileVerified','manualTypedApproval','installed',
                  'dispatchAuthorized','gameModified'):
            self.assertIs(a[k],False,k)
        self.assertEqual(a['ordersSent'],0)
        self.assertEqual(a['bafSha256'],hashlib.sha256(self.b.encode('ascii')).hexdigest())
    def test_deterministic_text(self):
        self.assertEqual(p.render(self.m),p.render(copy.deepcopy(self.m)))
    def test_cli_writes_baf_to_temp_not_game(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mf=root/'manifest.json'; baf=root/'candidate.baf'
            mf.write_text(json.dumps(self.m),encoding='utf-8')
            self.assertEqual(p.main(['--manifest',str(mf),'--out-baf',str(baf)]),0)
            self.assertEqual(baf.read_text(encoding='ascii'),self.b)
    def test_cli_rejects_bad_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            mf=Path(d)/'manifest.json'
            mf.write_text('{"oops":true}',encoding='utf-8')
            self.assertEqual(p.main(['--manifest',str(mf)]),3)
    def test_three_trigger_blocks_one_command(self):
        self.assertEqual(self.b.count('\nIF\n'),3)
        self.assertEqual(self.b.count('\nTHEN\n'),3)
        self.assertEqual(self.b.count('RESPONSE #100'),3)
        self.assertEqual(self.b.count('\nEND\n'),3)

if __name__ == '__main__': unittest.main()
