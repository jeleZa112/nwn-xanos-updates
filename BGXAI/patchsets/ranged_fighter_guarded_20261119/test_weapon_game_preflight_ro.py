import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
from unittest import mock
sys.path.insert(0,str(Path(__file__).parent))
import BGXAI_WEAPON_GAME_PREFLIGHT_RO as P

SOURCE=Path(__file__).with_name('BGXAI_WEAPON_GAME_PREFLIGHT_V1.baf')

class TestReadOnly(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.game=Path(self.temp.name)
        self.override=self.game/'override'
        self.override.mkdir()
        (self.game/'chitin.key').write_bytes(b'CHITIN_TEST')
        (self.game/'WeiDU.log').write_bytes(b'~BGXRANGED6/SETUP-BGXRANGED6.TP2~ #0 #0 test\n')
        (self.override/'DPLAYER.BCS').write_bytes(b'dplayer')
        (self.game/P.WEIDU_BINARY).write_bytes(b'MZmock_binary')
        self.calls=[]
    def tearDown(self):self.temp.cleanup()
    def runner(self,cmd,**kwargs):
        self.calls.append((cmd,kwargs))
        Path(cmd[4]).write_bytes(b'COMPILED_TEST_OUTPUT')
        return subprocess.CompletedProcess(cmd,0,stdout='compiled',stderr='')
    def test_valid_source_and_4_blocks(self):
        self.assertEqual(P.verify_baf(SOURCE)['blocks'],4)
    def test_game_readonly_with_native_mock(self):
        before={str(p):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        result=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
        after={str(p):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual(result['status'],'READONLY_NATIVE_PREFLIGHT_PASS')
        self.assertTrue(result['game_files_unchanged'])
        self.assertFalse(result['limits']['live_eeex_character_stats_read'])
        self.assertEqual(len(self.calls),1)
        cmd,opts=self.calls[0]
        self.assertTrue(str(cmd[0]).startswith(tempfile.gettempdir()))
        self.assertNotIn(str(self.game/'override'),cmd)
        self.assertEqual(cmd[1],'--game')
        self.assertEqual(cmd[3],'--out')
        self.assertEqual(Path(cmd[4]).parent,Path(cmd[0]).parent)
    def test_v6_drift_report_not_false_claim(self):
        r=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
        self.assertEqual(r['v6_status'],'V6_INSTALL_NOT_CONFIRMED')
    def test_compiler_error_fail_closed(self):
        def bad(cmd,**kwargs):return subprocess.CompletedProcess(cmd,1,stdout='ERROR: bad id',stderr='')
        r=P.audit(self.game,SOURCE,fixture=True,runner=bad)
        self.assertEqual(r['status'],'READONLY_PREFLIGHT_INCOMPLETE_OR_STOP')
        self.assertEqual(r['weidu_compile']['state'],'NATIVE_COMPILE_FAILED')
    def test_absent_weidu_hold(self):
        (self.game/P.WEIDU_BINARY).unlink()
        r=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
        self.assertEqual(r['weidu_compile']['state'],'HOLD_WEIDU_BINARY_MISSING')
        self.assertEqual(self.calls,[])
    def test_invalid_binary_hold(self):
        (self.game/P.WEIDU_BINARY).write_bytes(b'ELF')
        r=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
        self.assertEqual(r['weidu_compile']['state'],'HOLD_WEIDU_NOT_VALID_WINDOWS_EXE')
    def test_missing_key_fail_closed(self):
        (self.game/'chitin.key').unlink()
        with self.assertRaisesRegex(ValueError,'GAME_CHITIN_KEY_MISSING'):
            P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
    def test_symlink_in_game_target_never_follow(self):
        outside=self.game.parent / (self.game.name+'_secret.txt')
        outside.write_bytes(b'secret')
        try:
            (self.override/'PRIEST1.BCS').symlink_to(outside)
            r=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
            self.assertEqual(r['resources']['override/PRIEST1.BCS']['state'],'SYMLINK_BLOCKED')
        finally:outside.unlink()
    def test_source_drift_fail_closed(self):
        altered=self.game/'bad.baf';altered.write_bytes(SOURCE.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'V3_BAF_SOURCE_SHA_DRIFT'):
            P.audit(self.game,altered,fixture=True,runner=self.runner)
    def test_game_file_changes_detected(self):
        def mutate(cmd,**kwargs):
            (self.game/'WeiDU.log').write_bytes(b'mutated')
            Path(cmd[4]).write_bytes(b'test')
            return subprocess.CompletedProcess(cmd,0,stdout='yes',stderr='')
        r=P.audit(self.game,SOURCE,fixture=True,runner=mutate)
        self.assertFalse(r['game_files_unchanged'])
        self.assertEqual(r['status'],'READONLY_PREFLIGHT_INCOMPLETE_OR_STOP')
    def test_only_game_root_on_real_cli(self):
        with self.assertRaisesRegex(ValueError,'EXPECTED_WINDOWS_GAME_ROOT_REQUIRED'):
            P.audit(self.game,SOURCE)
    def test_optional_2da_not_claimed_from_biff(self):
        r=P.audit(self.game,SOURCE,fixture=True,runner=self.runner)
        self.assertFalse(r['installed_2da_available_in_override']['WSPATCK.2DA'])
        self.assertFalse(r['limits']['biFF_2da_contents_read'])
    def test_no_game_changing_actions(self):
        script=Path(P.__file__).read_text()
        for banned in ('--force-install','--force-uninstall','weidu --install','CreateItem(','Stop()'):
            self.assertNotIn(banned,script)

    def test_report_path_existing_unified_documents_folder(self):
        profile=self.game / 'User'
        unified=profile / 'Documents' / 'BGXAI_LIVE_REPORTS'
        unified.mkdir(parents=True)
        previous=unified / 'BGXAI_FRIENDLY_AGGRO_READONLY_old.json'
        previous.write_text('\u007b"original": true\u007d', encoding='utf-8')
        other=self.game / 'old_localappdata'
        report={'status':'READONLY_NATIVE_PREFLIGHT_PASS', 'game_files_unchanged':True,
                'weidu_compile':{'state':'NATIVE_COMPILED_TEMP_ONLY'}}
        with mock.patch.dict('os.environ', {'USERPROFILE':str(profile), 'LOCALAPPDATA':str(other)}), \
             mock.patch.object(P, 'audit', return_value=report), \
             mock.patch.object(sys,'argv',['pref.py','--game',str(self.game)]), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            rc=P.main()
        target=unified / 'BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json'
        self.assertEqual(rc,0)
        self.assertTrue(target.is_file())
        self.assertEqual(json.loads(target.read_text(encoding='utf-8')),report)
        self.assertIn('REPORT_FILE: '+str(target),out.getvalue())
        self.assertTrue(previous.is_file())
        self.assertFalse((other/'BGXAI_UPDATER'/'reports'/'BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json').exists())

    def test_report_write_failure_does_not_fall_back_elsewhere(self):
        profile=self.game / 'User'
        unified=profile / 'Documents' / 'BGXAI_LIVE_REPORTS'
        target=unified / 'BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json'
        target.mkdir(parents=True)
        other=self.game / 'old_localappdata'
        report={'status':'READONLY_NATIVE_PREFLIGHT_PASS', 'game_files_unchanged':True}
        with mock.patch.dict('os.environ', {'USERPROFILE':str(profile), 'LOCALAPPDATA':str(other)}), \
             mock.patch.object(P, 'audit', return_value=report), \
             mock.patch.object(sys,'argv',['pref.py','--game',str(self.game)]), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            rc=P.main()
        self.assertEqual(rc,2)
        self.assertIn('REPORT_WRITE_ERROR',out.getvalue())
        self.assertFalse((other/'BGXAI_UPDATER'/'reports'/'BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)
