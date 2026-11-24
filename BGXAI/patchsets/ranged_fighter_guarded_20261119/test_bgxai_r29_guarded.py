#!/usr/bin/env python3
"""Offline isolated safety tests for narrow R29 pilot; not EET gameplay proof."""
from __future__ import annotations
import pathlib, re, sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import BGXAI_R29_GUARDED as m

ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/'BGXAI_R29_KHALID_BOW_TO_SWORD.baf'

class SourceContracts(unittest.TestCase):
    def test_source_sha_and_single_native_switch(self):
        m.source_contract(SOURCE.read_bytes())
        b=m.parse_blocks(SOURCE.read_text('utf-8'))
        self.assertEqual(len(b),1)
        self.assertEqual(b[0][1],(m.ACTION,))
    def test_guard_covers_fighter_hostility_and_eps(self):
        raw=SOURCE.read_text('utf-8')
        for x in m.RULES:self.assertIn(x,raw)
        for x in ('CheckItemSlot(Myself,"SW1H04",SLOT_WEAPON0)',
                  'CheckItemSlot(Myself,"BOW05",SLOT_WEAPON1)',
                  'CurrentAmmo("AROW01",Myself)',
                  'Global("BGX38_GUARD","LOCALS",1)',
                  'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                  '!GlobalTimerNotExpired("MO_SpellCast","LOCALS")'):
            self.assertIn(x,raw)
    def test_mutation_fails_closed(self):
        s=SOURCE.read_bytes()
        variants=(s.replace(b'ActionListEmpty()',b'HavePartyItem()'),
                  s.replace(b'!InParty(NearestEnemyOf(Myself))',b'InParty(NearestEnemyOf(Myself))'),
                  s.replace(b'SW1H04',b'SW1H03'),
                  s.replace(b'MO_SpellCast',b'MO_Cast'),
                  s.replace(b'SelectWeaponAbility',b'Attack'),
                  s+b'\n')
        for bad in variants:
            with self.subTest(bad=bad[-20:]),self.assertRaises(m.Hold):m.source_contract(bad)
    def test_no_attack_or_caster_action(self):
        actions=m.parse_blocks(SOURCE.read_text('utf-8'))[0][1]
        self.assertEqual(actions,(m.ACTION,))
        self.assertNotIn('Attack(',''.join(actions))
        self.assertNotIn('Stop(',''.join(actions))
    def test_global_disabled_initially_zero_only(self):
        self.assertIn('Global("BGX29_DISABLE","LOCALS",0)',m.RULES)
        self.assertNotIn('SetGlobal(',SOURCE.read_text('utf-8'))
    def test_full_baf_shape_validation(self):
        for bad in ('IF\n THEN\n RESPONSE #100\n END\n',
                    'IF\n ActionListEmpty()\n THEN\n RESPONSE #100\n END\n',
                    'IF\n ActionListEmpty()\n THEN\n RESPONSE #100\n Attack(Myself)\n',
                    'IF\n ActionListEmpty()\n THEN\n RESPONSE #100\n Attack(Myself)\n END\n END\n'):
            with self.subTest(bad=bad),self.assertRaises(m.Hold):m.parse_blocks(bad)
    def test_last_weidu_regex(self):
        self.assertTrue(m.BEFORE_LAST.match('~BGXRANGED7/SETUP-BGXRANGED7.TP2~ #0 #0 // component'))
        self.assertTrue(m.AFTER_LAST.match('~BGXR29/SETUP-BGXR29.TP2~ #0 #0 ~pilot~'))
        self.assertFalse(m.BEFORE_LAST.match('~BGXR29/SETUP-BGXR29.TP2~ #0 #0'))
    def test_wrong_root_denied(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(m.Hold):
            m.baseline(pathlib.Path(tmp))
    def test_no_guarded_install_without_exact_typed_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=pathlib.Path(tmp)
            with patch.object(m,'candidate',return_value=(b'BCS',{'baselineSnapshot':{}})), \
                 patch('builtins.input',return_value='YES'), \
                 patch.object(m,'external_backup',side_effect=AssertionError('must not backup')):
                out=m.install(game)
                self.assertEqual(out['status'],'CANCELLED_WITHOUT_GAME_CHANGES')
                self.assertFalse((game/m.PACKAGE).exists())
    def test_rollback_blocked_if_not_last(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=pathlib.Path(tmp)
            with patch.object(m,'GAME',game),patch.object(m,'no_game_process'), \
                 patch.object(m,'last_weidu',return_value='~OTHER/SETUP-OTHER.TP2~ #0 #0'):
                with self.assertRaises(m.Hold):m.rollback(game)
    def test_report_is_atomic_one_file_outside_game(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(m.os.environ,{'USERPROFILE':tmp}):
                p=m.save_report({'status':'READONLY_TEST','ordersSent':0},'preflight')
                self.assertTrue(p.is_file())
                self.assertEqual(list(p.parent.glob('BGXAI_R29_*.json')),[p])
                self.assertFalse(list(p.parent.glob('*.tmp')))
                result=json.loads(p.read_text('utf-8'))
                self.assertEqual(result['status'],'READONLY_TEST')
                self.assertEqual(result['schema'],'BGXAI_R29_GUARDED_V1')
    def test_report_destination_symlink_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=pathlib.Path(tmp)
            root=base/'target';root.mkdir()
            d=base/'Documents';d.mkdir()
            try:
                (d/'BGXAI_LIVE_REPORTS').symlink_to(root,target_is_directory=True)
            except OSError:
                self.skipTest('OS denies unprivileged symlink creation')
            with patch.dict(m.os.environ,{'USERPROFILE':tmp}):
                with self.assertRaises(m.Hold):m.save_report({'status':'TEST'},'preflight')
    def test_install_requires_windows_runtime(self):
        if sys.platform!='win32':
            with self.assertRaises(m.Hold):m.no_game_process()
    def test_weidu_component_does_not_touch_eps(self):
        self.assertIn('COPY ~BGXR29/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~',m.TP2_TEXT)
        self.assertNotIn('core_base.tph',m.TP2_TEXT)
        self.assertNotIn('DPLAYER',m.TP2_TEXT)
        self.assertNotIn('WTASIGHT',m.TP2_TEXT)
    def test_source_does_not_touch_other_items_or_saves(self):
        data=SOURCE.read_bytes()
        for s in (b'ClearActions(',b'SetGlobal(',b'XEquipItem(',b'FillSlot(',
                  b'Attack(',b'ActionOverride(',b'ForceSpell(',b'EquipItem('):
            self.assertNotIn(s,data)

class NativeSpliceSimulation(unittest.TestCase):
    @staticmethod
    def fake_bcs(n):
        return b'SC\n'+(b'CR\nCO\nTR\nAC\nCR\n'*n)+b'SC\n'
    def test_split_1162_lossless(self):
        game_bcs=self.fake_bcs(1162)
        self.assertEqual(len(m.bcs_parts(game_bcs)),1162)
        self.assertEqual(b'SC\n'+b''.join(m.bcs_parts(game_bcs)),game_bcs)
    def test_candidate_inserts_one_rule_and_keeps_original_native_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=pathlib.Path(tmp)
            original=self.fake_bcs(1162)
            (game/'override').mkdir()
            (game/m.BCS).write_bytes(original)
            (game/'weidu.exe').write_bytes(b'MZFAKE')
            def mock_compiler(_exe,_game,_work,source,out,step):
                if step=='PILOT_COMPILE':
                    out.write_bytes(self.fake_bcs(1))
                elif step=='FULL_DECOMPILE':
                    oldblock='IF\n ActionListEmpty()\nTHEN\n RESPONSE #100\n NoAction()\nEND\n'
                    out.write_text(SOURCE.read_text('utf-8')+oldblock*1162,encoding='utf-8')
                else:raise AssertionError(step)
            with patch.object(m,'baseline',return_value={}),patch.object(m,'call_native',side_effect=mock_compiler):
                new,proof=m.candidate(game)
            self.assertEqual(len(m.bcs_parts(new)),1163)
            self.assertEqual(m.bcs_parts(new)[1:],m.bcs_parts(original))
            self.assertTrue(proof['originalBlocksBytePreserved'])
            self.assertFalse(proof['gameModified'])
            self.assertFalse(proof['dispatchAuthorized'])
            self.assertEqual((game/m.BCS).read_bytes(),original)
    def test_bad_bcs_envelope_or_blocks_fails(self):
        for data in (b'',b'SC\nCR\nSC\n',b'CR\nCO\nTR\n',b'SC\nCR\nCO\n'):
            with self.assertRaises(m.Hold):m.bcs_parts(data)
    def test_missing_bcs_baseline_prevents_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=pathlib.Path(tmp)
            (game/'override').mkdir()
            (game/m.BCS).write_bytes(b'BROKEN')
            (game/'weidu.exe').write_bytes(b'MZ')
            with patch.object(m,'baseline',return_value={}):
                with self.assertRaises(m.Hold):m.candidate(game)
    def test_native_weidu_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp);f=t/'a.baf';f.write_text('IF\nEND\n')
            with patch.object(m.subprocess,'run',return_value=type('P',(),{'returncode':1,'stdout':'ERROR: unknown','stderr':''})()):
                with self.assertRaises(m.Hold):m.call_native(t/'weidu.exe',t,t,f,t/'a.bcs','FAIL')

if __name__=='__main__':unittest.main(verbosity=2)
