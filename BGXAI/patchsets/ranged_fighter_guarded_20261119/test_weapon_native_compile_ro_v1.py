#!/usr/bin/env python3
"""Offline negative/positive guard tests. Fake WeiDU does NOT prove installed EET."""
from __future__ import annotations
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO as mod

SOURCE=Path(__file__).with_name(mod.SOURCE_NAME)

class CompileContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bgxai_test_native_ro_')
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.game=root/'EET';self.game.mkdir()
        self.weidu=self.game/'weidu.exe';self.weidu.write_bytes(b'FAKE WEIDU NOT REAL WINDOWSEXE\n')
        payload={
         'chitin.key':b'KEY BASE',
         'WeiDU.log':b'~BGXR27/SETUP-BGXR27.TP2~ #0 #0',
         'lang/ru_ru/dialog.tlk':b'TLK BASE',
         'lang/ru_ru/dialogf.tlk':b'TLKF BASE',
         'override/DPLAYER.BCS':b'DPLAYER BASE',
         'override/PRIEST1.BCS':b'PRIEST BASE',
         'override/WTASIGHT.BCS':b'WTASIGHT BASE',
         'override/M_BGXR27.lua':b'LUA BASE',
         'weidu.conf':b'lang_dir = ru_ru\n',
        }
        for rel,raw in payload.items():
            p=self.game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        self.before=mod.baseline(self.game,self.game/'lang/ru_ru/dialog.tlk')
    def ok_runner(self,cmd,**kwargs):
        self.assertEqual(kwargs['cwd'],str(self.game))
        self.assertEqual(kwargs['stdin'],subprocess.DEVNULL)
        self.assertEqual(kwargs['timeout'],25)
        self.assertIn('--no-auto-tp2',cmd)
        self.assertIn('--noautoupdate',cmd)
        self.assertIn('--no-exit-pause',cmd)
        self.assertIn('--script-style',cmd)
        self.assertNotIn('--force-install',cmd)
        self.assertEqual(Path(cmd[0]).name,'weidu.exe')
        self.assertNotEqual(Path(cmd[0]).parent,self.game)
        self.assertEqual(hashlib.sha256(Path(cmd[0]).read_bytes()).hexdigest(),hashlib.sha256(self.weidu.read_bytes()).hexdigest())
        output=Path(cmd[cmd.index('--out')+1]);self.assertNotEqual(output.parent,self.game)
        source=Path(cmd[-1]);self.assertEqual(source.name,'BGXW3CHK.baf')
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),mod.SOURCE_SHA256)
        (output/'BGXW3CHK.bcs').write_bytes(b'SC\n'+b'x'*64)
        return subprocess.CompletedProcess(cmd,0,'Compiled temp BCS','')
    def assert_idle(self):
        self.assertEqual(self.before,mod.baseline(self.game,self.game/'lang/ru_ru/dialog.tlk'))
    def test_01_source_sha_and_eight_actions(self):
        x=mod.source_check(SOURCE,self.game)
        self.assertEqual(x['blocks'],8);self.assertEqual(x['actionCount'],8)
    def test_02_compiles_in_temp_with_source_pin_and_live_hash_guard(self):
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=self.ok_runner)
        self.assertEqual(r['status'],'NATIVE_WEIDU_COMPILED_TEMP_ONLY')
        self.assertTrue(r['nativeSymbolsAcceptedByCompiler']);self.assertFalse(r['wholeGameTreeChecked'])
        self.assertFalse(r['installPerformed']);self.assertFalse(r['dispatchAuthorized']);self.assertFalse(r['watchedFilesChanged'])
        self.assertTrue(r['temporaryOutputRemoved']);self.assert_idle()
    def test_03_tampered_source_blocks_before_process(self):
        bad=Path(self.tmp.name)/'bad.baf';bad.write_bytes(SOURCE.read_bytes()+b'\n')
        with self.assertRaisesRegex(mod.Hold,'BAF_SOURCE_SHA256_MISMATCH'):
            mod.compile_readonly(self.game,bad,self.weidu,run=lambda *a,**k: self.fail('started'))
    def test_04_source_in_game_override_is_blocked(self):
        bad=self.game/'override'/mod.SOURCE_NAME;bad.write_bytes(SOURCE.read_bytes())
        with self.assertRaisesRegex(mod.Hold,'SOURCE_INSIDE_GAME_NOT_PINNED_STAGING_PATH'):
            mod.compile_readonly(self.game,bad,self.weidu,run=self.ok_runner)
    def test_05_pinned_updater_staging_inside_game_allowed(self):
        good=self.game/'BGXAI_DEV'/'weapon_priority_v3'/mod.SOURCE_NAME;good.parent.mkdir(parents=True);good.write_bytes(SOURCE.read_bytes())
        r=mod.compile_readonly(self.game,good,self.weidu,run=self.ok_runner)
        self.assertEqual(r['status'],'NATIVE_WEIDU_COMPILED_TEMP_ONLY');self.assert_idle()
    def test_06_compiler_outside_game_denied(self):
        other=Path(self.tmp.name)/'external.exe';other.write_bytes(self.weidu.read_bytes())
        with self.assertRaisesRegex(mod.Hold,'WEIDU_EXECUTABLE_OUTSIDE_GAME_ROOT'):
            mod.compile_readonly(self.game,SOURCE,other,run=self.ok_runner)
    def test_07_zero_exit_without_output_is_failure(self):
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=lambda c,**k:subprocess.CompletedProcess(c,0,'Nothing',''))
        self.assertEqual(r['status'],'WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS');self.assert_idle()
    def test_08_zero_exit_with_error_and_output_is_failure(self):
        def error(cmd,**kwargs):
            self.ok_runner(cmd,**kwargs)
            return subprocess.CompletedProcess(cmd,0,'ERROR: missing TRIGGER.IDS','')
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=error)
        self.assertEqual(r['status'],'WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS');self.assertFalse(r['nativeSymbolsAcceptedByCompiler']);self.assert_idle()
    def test_09_unknown_hand_symbol_warning_is_failure(self):
        def warn(cmd,**kwargs):
            self.ok_runner(cmd,**kwargs)
            return subprocess.CompletedProcess(cmd,0,'WARNING: unknown HAND.IDS','')
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=warn)
        self.assertEqual(r['status'],'WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS');self.assert_idle()
    def test_10_nonzero_exit_even_with_output_is_failure(self):
        def fail(cmd,**kwargs):
            self.ok_runner(cmd,**kwargs)
            return subprocess.CompletedProcess(cmd,3,'Compiled','')
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=fail)
        self.assertEqual(r['status'],'WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS');self.assert_idle()
    def test_11_invalid_compiled_header_is_rejected(self):
        def bad(cmd,**kwargs):
            out=Path(cmd[cmd.index('--out')+1]);(out/'BGXW3CHK.bcs').write_bytes(b'NO\n'+b'a'*40)
            return subprocess.CompletedProcess(cmd,0,'ok','')
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=bad)
        self.assertEqual(r['status'],'BCS_OUTPUT_INVALID');self.assert_idle()
    def test_12_mutation_of_dplayer_blocks_compiled_result(self):
        def mutate(cmd,**kwargs):
            result=self.ok_runner(cmd,**kwargs)
            (self.game/'override/DPLAYER.BCS').write_bytes(b'changed')
            return result
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=mutate)
        self.assertEqual(r['status'],'REVIEW_WATCHED_LIVE_FILES_CHANGED');self.assertTrue(r['watchedFilesChanged']);self.assertFalse(r['nativeSymbolsAcceptedByCompiler'])
    def test_13_mutation_of_weidu_log_blocks_compiled_result(self):
        def mutate(cmd,**kwargs):
            result=self.ok_runner(cmd,**kwargs)
            (self.game/'WeiDU.log').write_bytes(b'changed')
            return result
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=mutate)
        self.assertEqual(r['status'],'REVIEW_WATCHED_LIVE_FILES_CHANGED')
    def test_14_timeout_means_stop_not_pass(self):
        def timeout(*a,**k): raise subprocess.TimeoutExpired(a[0],25)
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=timeout)
        self.assertEqual(r['status'],'WEIDU_TIMEOUT');self.assert_idle()
    def test_15_nonmatching_weidu_config_blocks(self):
        (self.game/'weidu.conf').write_bytes(b'lang_dir = en_us\n')
        with self.assertRaisesRegex(mod.Hold,'CONFIGURED_DIALOG_TLK_MISSING_OR_AMBIGUOUS'):
            mod.compile_readonly(self.game,SOURCE,self.weidu,run=self.ok_runner)
    def test_16_casefolded_weidu_language_is_resolved(self):
        (self.game/'weidu.conf').write_bytes(b'lang_dir = RU_RU\n')
        r=mod.compile_readonly(self.game,SOURCE,self.weidu,run=self.ok_runner)
        self.assertEqual(r['status'],'NATIVE_WEIDU_COMPILED_TEMP_ONLY')
    @unittest.skipIf(os.name=='nt' or not hasattr(os,'symlink'),'Windows symlink permission / OS unavailable')
    def test_17_source_symlink_rejected(self):
        target=Path(self.tmp.name)/'link.baf';target.symlink_to(SOURCE)
        with self.assertRaisesRegex(mod.Hold,'SYMLINK_OR_REPARSE_DENIED'):
            mod.compile_readonly(self.game,target,self.weidu,run=self.ok_runner)
    def test_18_missing_chitin_key_blocks(self):
        (self.game/'chitin.key').unlink()
        with self.assertRaisesRegex(mod.Hold,'REQUIRED_FILE_MISSING:chitin.key'):
            mod.compile_readonly(self.game,SOURCE,self.weidu,run=self.ok_runner)
    def test_19_missing_weidu_log_blocks(self):
        (self.game/'WeiDU.log').unlink()
        with self.assertRaisesRegex(mod.Hold,'REQUIRED_FILE_MISSING:WeiDU.log'):
            mod.compile_readonly(self.game,SOURCE,self.weidu,run=self.ok_runner)
    def test_20_no_game_installed_blocks_cleanly(self):
        r=mod.main(['--game',str(self.game/'nonexistent')])
        self.assertEqual(r,3)
    @unittest.skipIf(os.name=='nt','POSIX shebang subprocess fixture only')
    def test_21_real_subprocess_fake_weidu_with_closed_stdin_and_temp_output(self):
        # Real OS subprocess, deliberately an instrumented fake WeiDU; does
        # NOT demonstrate native compilation on installed EET.
        self.weidu.write_text('''#!/usr/bin/env python3
import pathlib,sys
args=sys.argv[1:]
if pathlib.Path(sys.argv[0]).name.lower()!='weidu.exe':sys.exit(4)
if not {'--no-auto-tp2','--no-exit-pause','--noautoupdate'}.issubset(args):sys.exit(5)
if sys.stdin.read()!='':sys.exit(6)
source=pathlib.Path(args[-1]);out=pathlib.Path(args[args.index('--out')+1])
if source.name!='BGXW3CHK.baf':sys.exit(7)
out.mkdir(exist_ok=True)
(out/'BGXW3CHK.bcs').write_bytes(b'SC\\n'+b'x'*64)
print('Compiled source-only test')
''',encoding='utf-8')
        self.weidu.chmod(0o755)
        result=mod.compile_readonly(self.game,SOURCE,self.weidu)
        self.assertEqual(result['status'],'NATIVE_WEIDU_COMPILED_TEMP_ONLY')
        self.assertFalse(result['watchedFilesChanged'])
        self.assertFalse(result['installPerformed'])
        self.assert_idle()

if __name__=='__main__':
    result=unittest.main(verbosity=1,exit=False)
    if result.result.wasSuccessful():
        count=result.result.testsRun-len(result.result.skipped)
        print(f'PASS NATIVE BAF COMPILER CONTRACT {count}/{count} SOURCE-ONLY CHECKS; {len(result.result.skipped)} SKIPPED')
    raise SystemExit(0 if result.result.wasSuccessful() else 1)