#!/usr/bin/env python3
"""Test program for the real BGXAI read-only automatic batch runner.
Mock inputs test safety decisions; no EET, no game write, no live permissions.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import BGXAI_AUTO_BATCH_RO_V1 as m
ROOT=Path(__file__).resolve().parent

class AutomaticBatchSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bgxai_auto_batch_test_')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.game=self.root/'EET'
        self.game.mkdir()
        self.docs=self.root/'Documents'/'BGXAI_LIVE_REPORTS'
        self.docs.mkdir(parents=True)
        (self.game/'chitin.key').write_bytes(b'EET KEY')
        (self.game/'WeiDU.log').write_bytes(b'OLD WEIDU LOG')
        (self.game/'weidu.exe').write_bytes(b'FAKE NON-REAL-WEIDU-STUB')
        (self.game/'override').mkdir()
        (self.game/'override'/'DPLAYER.BCS').write_bytes(b'BCS ORIGINAL')
    def fake_native(self):
        return {'schema':'BGXAI_WEAPON_NATIVE_COMPILE_RO_V1',
          'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY','exitCode':0,
          'compilerSha256':m.sha_file(self.game/'weidu.exe'),
          'source':{'sha256':m.BAF_SHA,'size':6763,'blocks':8,'actionCount':8},
          'compiledSize':10550,'compiledSha256':'a'*64,
          'nativeSymbolsAcceptedByCompiler':True,
          'watchedFilesChanged':False,'gameplayLiveVerified':False,
          'engineBehaviorVerified':False,'installPerformed':False,'ordersSent':0,
          'dispatchAuthorized':False,'weaponSwitchAuthorized':False}
    def write_native(self,d=None):
        p=self.docs/'BGXAI_WEAPON_NATIVE_COMPILE_RO_20261124T134604227.json'
        p.write_text(json.dumps(self.fake_native() if d is None else d))
        return p
    def test_01_source_sha_pinned_real_BAF(self):
        self.assertEqual(m.sha_file(ROOT/m.BAF),m.BAF_SHA)
    def test_02_source_sha_pinned_native_python(self):
        self.assertEqual(m.sha_file(ROOT/m.NATIVE),m.NATIVE_SHA)
    def test_03_baf_all_8_blocks(self):
        self.assertEqual(m.static_baf_contract(ROOT/m.BAF)['assertions'],108)
    def test_04_policy_matrix_512_no_real_game(self):
        self.assertEqual(m.negative_matrix_contract()['cases'],512)
    def test_05_runtime_proof_always_fails_closed(self):
        x=m.game_live_proof_gates()
        self.assertEqual(len(x['missing']),6)
        self.assertFalse(x['dispatchAuthorized'])
        self.assertEqual(x['ordersSent'],0)
    def test_06_snapshot_only_watched_files(self):
        x=m.parse_game_snapshot(self.game)
        self.assertEqual(len(x),len(m.GAME_PATHS))
        self.assertEqual(x['chitin.key'],hashlib.sha256(b'EET KEY').hexdigest())
        self.assertIsNone(x['override/PRIEST1.BCS'])
    def test_07_watched_change_detected(self):
        a=m.parse_game_snapshot(self.game)
        (self.game/'override'/'DPLAYER.BCS').write_bytes(b'DO NOT TOUCH')
        b=m.parse_game_snapshot(self.game)
        self.assertNotEqual(a,b)
    def test_08_symlink_file_denied(self):
        f=self.root/'link.json'
        try:f.symlink_to(self.game/'chitin.key')
        except OSError:self.skipTest('OS disallows symlinks')
        with self.assertRaises(m.Hold):m.sha_file(f)
    def test_09_missing_file_returns_null_hash(self):
        self.assertIsNone(m.sha_file(self.root/'absent'))
    def test_10_baseline_denies_folder(self):
        with self.assertRaises(m.Hold):m.sha_file(self.game)
    def test_11_historical_native_source_valid_but_not_current(self):
        self.write_native()
        x=m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe')
        self.assertTrue(x['historicalOnly'])
        self.assertFalse(x['currentGameNativeRecheck'])
    def test_12_invalid_native_provenance_not_reused(self):
        d=self.fake_native();d['source']['sha256']='f'*64
        self.write_native(d)
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_13_changed_compiler_invalidates_old_report(self):
        self.write_native()
        (self.game/'weidu.exe').write_bytes(b'OTHER COMPILER CONTENT')
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_14_unsafe_command_never_trusted(self):
        d=self.fake_native();d['ordersSent']=1
        self.write_native(d)
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_15_flag_false_is_not_int_zero(self):
        d=self.fake_native();d['ordersSent']=False
        self.write_native(d)
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_16_fake_install_flag_never_accepted(self):
        d=self.fake_native();d['installPerformed']=True
        self.write_native(d)
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_17_fake_dispatch_flag_never_accepted(self):
        d=self.fake_native();d['dispatchAuthorized']=True
        self.write_native(d)
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
    def test_18_no_output_report_rewrite_in_game(self):
        self.assertNotIn('override',str(self.docs).lower())
        self.assertFalse(self.game in self.docs.parents)
    def test_19_independent_native_test_runs_self_contained(self):
        self.assertTrue((ROOT/m.TEST_NATIVE).is_file())
        self.assertIn('test_01_source_sha_and_eight_actions',(ROOT/m.TEST_NATIVE).read_text())
    def test_20_runner_continues_when_one_subtest_fails(self):
        x=m.run_subprocess_test(self.root/'missing_test.py',ROOT)
        self.assertEqual(x['status'],'HOLD_TEST_SOURCE_NOT_STAGED')
        self.assertEqual(m.negative_matrix_contract()['cases'],512)
    def test_21_closed_process_is_required_for_native(self):
        busy=m.marker('HOLD_GAME_OR_WEIDU_RUNNING',running=['baldur.exe'])
        self.assertNotEqual(busy['status'],'PASS_NO_KNOWN_GAME_PROCESS')
    def test_22_sha_guard_disallows_fake_baf(self):
        p=self.root/'fake.baf';p.write_bytes(b'IF\n...')
        with self.assertRaises(m.Hold):m.static_baf_contract(p)
    def test_23_strict_no_game_actions_code_surface(self):
        source=(ROOT/'BGXAI_AUTO_BATCH_RO_V1.py').read_text()
        tree=ast.parse(source)
        forbidden={'SetGlobal','SelectWeaponAbility','ClearActions',
                   'QueueResponseStringOnAIBase'}
        calls={x.func.id for x in ast.walk(tree) if isinstance(x,ast.Call) and
               isinstance(x.func,ast.Name)}
        self.assertFalse(calls.intersection(forbidden))
    def test_24_output_contract_both_gates_denied(self):
        x=m.game_live_proof_gates()
        for key in ('dispatchAuthorized','alternateEffectiveAprVerified',
                    'launcherAmmoEnginePairVerified','manualVsEpsOriginVerified'):
            self.assertIs(x[key],False)
    def test_25_game_process_names_only_no_guess(self):
        self.assertIn('infinityloader.exe',m.GAME_EXECUTABLES)
        self.assertIn('weidu.exe',m.GAME_EXECUTABLES)
    def test_26_past_report_not_required_to_pass_static_checks(self):
        self.assertIsNone(m.verified_existing_native(self.docs,self.game,self.game/'weidu.exe'))
        self.assertEqual(m.static_baf_contract(ROOT/m.BAF)['status'],'PASS_BAF_EIGHT_BRANCH_STATIC')
    def test_27_hold_in_process_stage_does_not_skip_independent_tests(self):
        with patch.object(m,'run_subprocess_test',return_value=m.marker('PASS_UNIT_TESTS',totalTests=0,skippedTests=0)):
            report,rc=m.run_batch(self.game,ROOT,self.docs,process_override=m.marker('HOLD_GAME_OR_WEIDU_RUNNING',running=['baldur.exe']))
        self.assertEqual(report['stepCount'],10)
        self.assertEqual(report['stages']['bafGuard']['status'],'PASS_BAF_EIGHT_BRANCH_STATIC')
        self.assertEqual(report['stages']['nativeWeiDU']['status'],'HOLD_PROCESS_STATE_BEFORE_NATIVE_COMPILE')
        self.assertEqual(rc,3)
        self.assertIs(report['dispatchAuthorized'],False)
        self.assertIs(report['gameFilesChanged'],False)
    def test_28_valid_previous_compilation_is_reused_without_a_new_weidu_process(self):
        self.write_native()
        with patch.object(m,'run_subprocess_test',return_value=m.marker('PASS_UNIT_TESTS',totalTests=0,skippedTests=0)):
            report,rc=m.run_batch(self.game,ROOT,self.docs,process_override=m.marker('PASS_NO_KNOWN_GAME_PROCESS',running=[]))
        self.assertEqual(rc,0)
        self.assertEqual(report['stages']['nativeWeiDU']['status'],'PASS_PRIOR_NATIVE_COMPILE_REUSED_HISTORICAL_ONLY')
        self.assertEqual(report['stages']['runtimeProof']['status'],'HOLD_LIVE_ORIGIN_AND_ALT_STATS_NOT_PROVEN')
    def test_29_hard_hold_with_missing_game_does_not_grant_permission(self):
        with patch.object(m,'run_subprocess_test',return_value=m.marker('PASS_UNIT_TESTS',totalTests=0,skippedTests=0)):
            report,rc=m.run_batch(self.root/'missing_game',ROOT,self.docs,process_override=m.marker('PASS_NO_KNOWN_GAME_PROCESS',running=[]))
        self.assertEqual(rc,3)
        self.assertIs(report['dispatchAuthorized'],False)
        self.assertIsNone(report['gameFilesChanged'])
        self.assertEqual(report['stages']['gameBefore']['status'],'HOLD_CHITIN_OR_WEIDU_LOG_NOT_FOUND')

if __name__=='__main__':
    unittest.main(verbosity=2)
