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
            with patch.object(m,'baseline',return_value={}),patch.object(m,'verify_ranged7_history',return_value={'ranged7InWeiDULog':True}),patch.object(m,'call_native',side_effect=mock_compiler):
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
    def test_native_compiler_has_non_mutating_wei_du_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=pathlib.Path(tmp);f=t/'a.baf';f.write_bytes(SOURCE.read_bytes())
            def verify(cmd,**kwargs):
                for flag in ('--no-auto-tp2','--noautoupdate','--no-exit-pause'):
                    self.assertIn(flag,cmd)
                self.assertIn('--out',cmd)
                self.assertIn('--game',cmd)
                self.assertEqual(kwargs['stdin'],m.subprocess.DEVNULL)
                (t/'a.bcs').write_bytes(b'SC\nCR\nCO\nTR\nCR\nSC\n')
                return type('P',(),{'returncode':0,'stdout':'','stderr':''})()
            with patch.object(m.subprocess,'run',side_effect=verify):
                m.call_native(t/'weidu.exe',t,t,f,t/'a.bcs','TEST')
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


class HistoricalRanged7Chain(unittest.TestCase):
    """R7 may precede later WeiDU mods, but no single missing proof is ignored."""
    R7='~BGXRANGED7/SETUP-BGXRANGED7.TP2~ #0 #0 ~Guard~'
    LATER='~OTHERPACK/SETUP-OTHERPACK.TP2~ #0 #1 ~Unrelated mod~'

    def setup_game(self, game, log_lines, with_proof=True):
        import json,hashlib
        root=pathlib.Path(game)
        data={name:('MOCK:'+name).encode('ascii') for name in m.BASELINE}
        for name,value in data.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
        for name,content in (('chitin.key',b'KEY'),('weidu.conf',b'CONF'),
                             ('weidu.exe',b'MZMOCK_WEIDU'),
                             ('WeiDU.log',('\n'.join(log_lines)+'\n').encode('utf8'))):
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        old=b'Original BGXRANGED7 DPLAYER BCS bytes'
        if with_proof:
            stage=root/m.RANGED7_STAGE;stage.parent.mkdir(parents=True,exist_ok=True)
            stage.write_bytes(data['override/DPLAYER.BCS'])
            backup=root.parent/'SAFE_BACKUP'
            dplayer=backup/'override/DPLAYER.BCS';dplayer.parent.mkdir(parents=True,exist_ok=True)
            dplayer.write_bytes(old)
            (backup/'SHA256.json').write_text(json.dumps({'override/DPLAYER.BCS':hashlib.sha256(old).hexdigest()}))
            proof={'old_dplayer_sha256':hashlib.sha256(old).hexdigest(),
                   'new_dplayer_sha256':hashlib.sha256(data['override/DPLAYER.BCS']).hexdigest(),
                   'source_sha256':m.RANGED7_SOURCE_SHA,'changed_blocks':[1,2],
                   'backup':str(backup)}
            p=root/m.RANGED7_PROOF;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(proof))
        return data,old

    def patched_context(self,game,dat,old):
        from contextlib import ExitStack
        from unittest.mock import patch
        import hashlib
        x=ExitStack()
        self.addCleanup(x.close)
        x.enter_context(patch.object(m,'GAME',game))
        x.enter_context(patch.object(m,'BASELINE',{k:m.hash_bytes(v) for k,v in dat.items()}))
        x.enter_context(patch.object(m,'EXPECTED_WEIDU_LOG_SHA',m.sha(game/'WeiDU.log')))
        x.enter_context(patch.object(m,'EXPECTED_WEIDU_SHA',m.sha(game/'weidu.exe')))
        x.enter_context(patch.object(m,'RANGED7_PREVIOUS_SHA',m.hash_bytes(old)))
        x.enter_context(patch.object(m,'no_game_process'))

    def test_r7_can_be_last_without_historical_proof(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7],with_proof=False)
            self.patched_context(game,dat,old)
            history=m.verify_ranged7_history(game)
            self.assertTrue(history['ranged7LastWeiDU'])
            self.assertFalse(history['ranged7HistoricalProofVerified'])
            self.assertEqual(m.status(game)['status'],'R29_NOT_INSTALLED_BASELINE')

    def test_r7_historical_with_exact_proof_staged_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            log_before=(game/'WeiDU.log').read_bytes()
            dplayer_before=(game/'override/DPLAYER.BCS').read_bytes()
            history=m.verify_ranged7_history(game)
            self.assertTrue(history['ranged7InWeiDULog'])
            self.assertFalse(history['ranged7LastWeiDU'])
            self.assertTrue(history['ranged7HistoricalProofVerified'])
            self.assertEqual(history['lastComponentBasename'],'SETUP-OTHERPACK.TP2')
            self.assertEqual(len(m.baseline(game)),len(m.WATCH))
            self.assertEqual(m.status(game)['status'],'R29_NOT_INSTALLED_BASELINE')
            self.assertEqual((game/'WeiDU.log').read_bytes(),log_before)
            self.assertEqual((game/'override/DPLAYER.BCS').read_bytes(),dplayer_before)

    def test_missing_installed_r7_entry_denied_even_if_dplayer_hash_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.LATER]);self.patched_context(game,dat,old)
            with self.assertRaisesRegex(m.Hold,'RANGED7_NOT_EXACTLY_ONCE'):
                m.baseline(game)

    def test_duplicate_r7_entry_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.R7,self.LATER]);self.patched_context(game,dat,old)
            with self.assertRaisesRegex(m.Hold,'RANGED7_NOT_EXACTLY_ONCE'):
                m.baseline(game)

    def test_historical_missing_proof_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER],with_proof=False)
            self.patched_context(game,dat,old)
            with self.assertRaisesRegex(m.Hold,'RANGED7_HISTORICAL_INSTALL_PROOF_MISSING'):
                m.baseline(game)

    def test_historical_proof_mutation_denied(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            p=game/m.RANGED7_PROOF;proof=json.loads(p.read_text());proof['changed_blocks']=[1,3]
            p.write_text(json.dumps(proof))
            with self.assertRaisesRegex(m.Hold,'RANGED7_HISTORICAL_PROOF_DRIFT'):
                m.baseline(game)

    def test_historical_staged_dplayer_mutation_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            (game/m.RANGED7_STAGE).write_bytes(b'CORRUPT')
            with self.assertRaisesRegex(m.Hold,'RANGED7_HISTORICAL_STAGED_DPLAYER_DRIFT'):
                m.baseline(game)

    def test_historical_backup_dplayer_mutation_denied(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            p=json.loads((game/m.RANGED7_PROOF).read_text())['backup']
            (pathlib.Path(p)/'override/DPLAYER.BCS').write_bytes(b'CORRUPT')
            with self.assertRaisesRegex(m.Hold,'RANGED7_HISTORICAL_BACKUP_DPLAYER_CORRUPTED'):
                m.baseline(game)

    def test_later_mod_changes_bcs_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            (game/'override/BDDEFAI.BCS').write_bytes(b'TAMPER')
            with self.assertRaisesRegex(m.Hold,'BASELINE_SHA_DRIFT:override/BDDEFAI.BCS'):
                m.baseline(game)

    def test_weidu_log_hash_drift_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER]);self.patched_context(game,dat,old)
            with (game/'WeiDU.log').open('ab') as f:f.write(b'\n#modified\n')
            with self.assertRaisesRegex(m.Hold,'WEIDU_LOG_SHA_DRIFT'):
                m.baseline(game)

    def test_r29_installed_record_denied_in_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.R7,self.LATER,'~BGXR29/SETUP-BGXR29.TP2~ #0 #0'])
            self.patched_context(game,dat,old)
            with self.assertRaisesRegex(m.Hold,'R29_ALREADY_IN_WEIDU_LOG_STOP'):
                m.baseline(game)

    def test_safe_stop_retains_diagnostic_only_when_history_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            dat,old=self.setup_game(game,[self.LATER],with_proof=False)
            self.patched_context(game,dat,old)
            with self.assertRaisesRegex(m.Hold,'RANGED7_NOT_EXACTLY_ONCE'):
                m.baseline(game)
            history=m.weidu_entries(game)
            summary={'lastComponentBasename':m.sanitize_component(history[-1]),
                     'ranged7InstalledEntryCount':sum(bool(m.BEFORE_LAST.match(v)) for v in history)}
            self.assertEqual(summary['ranged7InstalledEntryCount'],0)
            self.assertEqual(summary['lastComponentBasename'],'SETUP-OTHERPACK.TP2')
            self.assertFalse((game/m.RANGED7_PROOF).exists())

    def test_preflight_safe_stop_creates_one_diagnostic_json_no_game_write(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            # Windows tempfile often returns an 8.3 path alias; CLI resolves
            # --game before the exact-root safety comparison.
            game=game.resolve()
            dat,old=self.setup_game(game,[self.LATER],with_proof=False)
            self.patched_context(game,dat,old)
            before=(game/'WeiDU.log').read_bytes()
            with patch.object(sys,'argv',['r29.py','--game',str(game),'preflight']), \
                 patch.dict(m.os.environ,{'USERPROFILE':temp}):
                result=m.main()
            self.assertEqual(result,3)
            reports=list((pathlib.Path(temp)/'Documents/BGXAI_LIVE_REPORTS').glob('BGXAI_R29_PREFLIGHT_*.json'))
            self.assertEqual(len(reports),1)
            data=json.loads(reports[0].read_text())
            self.assertEqual(data['status'],'R29_SAFE_STOP')
            self.assertEqual(data['reason'],'RANGED7_NOT_EXACTLY_ONCE_IN_WEIDU_LOG')
            self.assertEqual(data['weiduHistoryReadOnly']['ranged7InstalledEntryCount'],0)
            self.assertEqual(data['weiduHistoryReadOnly']['lastComponentBasename'],'SETUP-OTHERPACK.TP2')
            self.assertFalse(data['gameModifiedUnknown'])
            self.assertEqual((game/'WeiDU.log').read_bytes(),before)
            self.assertFalse((game/m.PACKAGE).exists())

    def test_rollback_still_last_only_after_ranged7_history_change(self):
        with tempfile.TemporaryDirectory() as temp:
            game=pathlib.Path(temp)/'GAME';game.mkdir()
            with patch.object(m,'GAME',game),patch.object(m,'no_game_process'),patch.object(m,'last_weidu',return_value=self.LATER):
                with self.assertRaisesRegex(m.Hold,'R29_NOT_LAST_NO_ROLLBACK'):
                    m.rollback(game)

if __name__=='__main__':unittest.main(verbosity=2)
