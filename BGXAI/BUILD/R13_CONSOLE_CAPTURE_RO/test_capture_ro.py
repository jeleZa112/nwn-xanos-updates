"""Read-only subprocess console capture tests; NEVER launch InfinityLoader."""
import importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

P=Path(__file__).with_name('BGXAI_R13_SHORTNAME_GUARDED.py')
spec=importlib.util.spec_from_file_location('bgx13cap',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class DummyProcess:
    def wait(self): return 0

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.root=Path(self.t.name)/'game';self.root.mkdir()
        self.home=Path(self.t.name)/'user';self.home.mkdir()
        self.docs=self.home/'Documents';self.docs.mkdir()
        (self.root/'InfinityLoader.exe').write_bytes(b'MZ'+b'\0'*75000)
        (self.root/m.PROOF).parent.mkdir(parents=True)
        (self.root/m.PROOF).write_text(json.dumps({'sourceSha256':m.SOURCE_SHA,'status':'BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST'}))
        self.patches=[patch.object(m,'game'),patch.object(m,'sources'),patch.object(m,'baseline'),
             patch.object(m,'processes'),patch.object(m,'weidu_last',return_value='~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0'),
             patch.object(m,'sha',return_value=m.SOURCE_SHA),patch.dict(os.environ,{'USERPROFILE':str(self.home)})]
        for x in self.patches:x.start()
    def tearDown(self):
        for x in self.patches[::-1]:x.stop()
        self.t.cleanup()
    def launch(self,*args,**kwargs):
        self.assertEqual(args[0],[str(self.root/'InfinityLoader.exe')]);self.assertEqual(kwargs['cwd'],self.root)
        self.assertIs(kwargs['stdin'],m.subprocess.DEVNULL)
        self.assertIs(kwargs['stderr'],m.subprocess.STDOUT)
        self.assertNotIn('shell',kwargs)
        kwargs['stdout'].write(b'[BGXTD13] {"type":"SESSION"}\n')
        return DummyProcess()
    def test_capture_success(self):
        with patch.object(m.subprocess,'Popen',side_effect=self.launch) as pop:
            res=m.capture_console(self.root)
        self.assertEqual(res['status'],'BGXTD14_CONSOLE_CAPTURE_CREATED')
        self.assertGreater(res['consoleBytes'],0)
        self.assertTrue(Path(res['consoleLog']).is_file())
        self.assertIn('[BGXTD13]',Path(res['consoleLog']).read_text())
        self.assertFalse(res['gameModifiedByCapture']);self.assertFalse(res['r13LuaReinstalled']);self.assertFalse(res['weaponSwitchAuthorized'])
        pop.assert_called_once()
    def test_empty_capture_is_hold(self):
        with patch.object(m.subprocess,'Popen',return_value=DummyProcess()):
            self.assertEqual(m.capture_console(self.root)['status'],'BGXTD14_CONSOLE_CAPTURE_EMPTY_HOLD')
    def test_wrong_install_proof_prevents_launch(self):
        (self.root/m.PROOF).write_text(json.dumps({'status':'NOT_INSTALLED','sourceSha256':m.SOURCE_SHA}))
        with patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'PROOF_UNVERIFIED'):m.capture_console(self.root)
            p.assert_not_called()
    def test_wrong_source_sha_prevents_launch(self):
        with patch.object(m,'sha',return_value='0'*64),patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'MODULE_SHA_DRIFT'):m.capture_console(self.root)
            p.assert_not_called()
    def test_missing_short_file_prevents_launch(self):
        with patch.object(m,'sha',side_effect=ValueError('FILE_MISSING')),patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'FILE_MISSING'):m.capture_console(self.root)
            p.assert_not_called()
    def test_wrong_weidu_order_prevents_launch(self):
        with patch.object(m,'weidu_last',return_value='~OTHER\\SETUP.TP2~ #0 #0'),patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'NOT_LAST_WEIDU'):m.capture_console(self.root)
            p.assert_not_called()
    def test_missing_exe_prevents_launch(self):
        (self.root/'InfinityLoader.exe').unlink()
        with patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'INFINITYLOADER_UNAVAILABLE'):m.capture_console(self.root)
            p.assert_not_called()
    def test_invalid_pe_prevents_launch(self):
        (self.root/'InfinityLoader.exe').write_bytes(b'ZZ'+b'\0'*75000)
        with patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'PE_HEADER_INVALID'):m.capture_console(self.root)
            p.assert_not_called()
    def test_absent_userprofile_prevents_launch(self):
        with patch.dict(os.environ,{'USERPROFILE':''}),patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'USERPROFILE_UNAVAILABLE'):m.capture_console(self.root)
            p.assert_not_called()
    def test_symlink_report_dir_prevents_launch(self):
        out=self.docs/'BGXAI_LIVE_REPORTS';real=self.home/'other';real.mkdir()
        try:out.symlink_to(real,target_is_directory=True)
        except OSError:self.skipTest('Symlinks disabled')
        with patch.object(m.subprocess,'Popen') as p:
            with self.assertRaisesRegex(ValueError,'REPARSE_STOP'):m.capture_console(self.root)
            p.assert_not_called()
    def test_does_not_write_game_resources(self):
        before={z.relative_to(self.root):z.read_bytes() for z in self.root.rglob('*') if z.is_file()}
        with patch.object(m.subprocess,'Popen',side_effect=self.launch):m.capture_console(self.root)
        after={z.relative_to(self.root):z.read_bytes() for z in self.root.rglob('*') if z.is_file()}
        self.assertEqual(before,after)
    def test_no_install_persistence_in_capture(self):
        text=P.read_text();part=text[text.index('def capture_console('):text.index('\ndef main()')]
        self.assertNotIn('run_weidu(',part);self.assertNotIn('install(',part)
        self.assertNotIn('shutil.copy',part);self.assertNotIn('write_text(',part)
        self.assertIn("'capture'",text)
    def test_existing_lua_has_captureable_fallback(self):
        source=Path(__file__).with_name('M_BGXD13.lua').read_text()
        self.assertIn("type(Infinity_Log)=='function'",source)
        self.assertIn("type(print)=='function'",source)
        self.assertIn("'[BGXTD13] '",source)
        self.assertIn("R.writer='CONSOLE_FALLBACK'",source)
    def test_console_receives_exit_code(self):
        class P:
            def wait(self):return 4
        with patch.object(m.subprocess,'Popen',return_value=P()):
            res=m.capture_console(self.root)
        self.assertEqual(res['gameExitCode'],4)
        self.assertEqual(res['status'],'BGXTD14_CONSOLE_CAPTURE_EMPTY_HOLD')

if __name__=='__main__':unittest.main(verbosity=2)
