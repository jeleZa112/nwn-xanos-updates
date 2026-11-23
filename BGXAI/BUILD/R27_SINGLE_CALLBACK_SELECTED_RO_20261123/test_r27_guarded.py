"""R27 installer-integration offline tests. Real EET never touched."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r27', D/'BGXAI_R27_GUARDED.py')
r27=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r27)

class GuardedTests(unittest.TestCase):
    def test_source_exact(self): r27.sources()
    def test_source_size(self): self.assertEqual((D/'M_BGXR27.lua').stat().st_size, 28890)
    def test_source_sha_pin(self): self.assertEqual(r27.digest(r27.SOURCE), r27.SOURCE_SHA)
    def test_eight_char_resref(self): self.assertEqual(len('M_BGXR27'),8)
    def test_script_never_weapon_commands(self):
        data=r27.SOURCE.read_bytes()
        self.assertFalse([x for x in r27.BLOCKED if x in data])
    def test_one_listener_registration(self):
        self.assertEqual(r27.SOURCE.read_bytes().count(b'pcall(EEex_Action_AddSpriteStartedActionListener,pilot.listener)'),1)
    def test_preflight_default_and_tokens(self):
        self.assertIn("default='menu'", (D/'BGXAI_R27_GUARDED.py').read_text())
        self.assertIn("input('Choice [2]: ')", (D/'BGXAI_R27_GUARDED.py').read_text())
        self.assertNotEqual(r27.INSTALL_TOKEN,r27.ROLLBACK_TOKEN)
    def test_missing_install_token_no_touch(self):
        with self.assertRaisesRegex(ValueError,'INSTALL_TOKEN_REQUIRED'):
            r27.install(Path('/untouched'), 'YES')
    def test_missing_rollback_token_no_touch(self):
        with self.assertRaisesRegex(ValueError,'ROLLBACK_TOKEN_REQUIRED'):
            r27.rollback(Path('/untouched'), 'YES')
    def test_windows_only_guard(self):
        path=Path('/tmp/no-game')
        with mock.patch.object(r27.os,'name','posix'):
            with self.assertRaisesRegex(ValueError,'EXACT_WINDOWS_GAME_ROOT_REQUIRED'):
                r27.game(path)
    def test_status_sentinel_no_premature_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'WeiDU.log').write_text('~BGXTD15/SETUP-BGXTD15.TP2~ #0 #0\n')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,sources=lambda:None):
                z=r27.status(root)
            self.assertEqual(z['status'],'R27_NOT_INSTALLED')
    def test_fake_preflight_positive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'WeiDU.log').write_text('~BGXTD15/SETUP-BGXTD15.TP2~ #0 #0\n')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,processes=lambda:None,weidu=lambda x:Path('/dummy')):
                v=r27.preflight(root)
            self.assertEqual(v['status'],'R27_PREFLIGHT_PASS_NO_INSTALL')
            self.assertFalse(v['weaponSwitchAuthorized'])
    def test_preflight_refuses_nonlast(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'WeiDU.log').write_text('~BGXTD15/SETUP-BGXTD15.TP2~ #0 #0\n~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,processes=lambda:None,weidu=lambda x:Path('/dummy')):
                with self.assertRaisesRegex(ValueError,'TD15_NOT_WEIDU_LAST_NO_INSTALL'):
                    r27.preflight(root)
    def test_preflight_refuses_existing_override(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'WeiDU.log').write_text('~BGXTD15/SETUP-BGXTD15.TP2~ #0 #0\n')
            (root/'override').mkdir(); (root/'override/M_BGXR27.lua').write_text('foreign')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,processes=lambda:None,weidu=lambda x:Path('/dummy')):
                with self.assertRaisesRegex(ValueError,'R27_PATH_ALREADY_EXISTS'):
                    r27.preflight(root)
    def test_source_mutation_rejected(self):
        data=r27.SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'M_BGXR27.lua';file.write_bytes(data+b'\n--tamper')
            with mock.patch.object(r27,'SOURCE',file):
                with self.assertRaisesRegex(ValueError,'R27_SOURCE_SHA_MISMATCH'):r27.sources()
    def test_reparse_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'dest').mkdir(); (root/'dest'/'x').mkdir()
            try:(root/'danger').symlink_to(root/'dest',target_is_directory=True)
            except OSError:self.skipTest('Symlink unavailable')
            with self.assertRaisesRegex(ValueError,'REPARSE_PATH_STOP'):
                r27.regular(root,'danger/x')
    def test_typical_status_fails_on_unknown_last(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'WeiDU.log').write_text('~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,sources=lambda:None):
                with self.assertRaisesRegex(ValueError,'R27_UNRECOGNIZED_STATE_OR_NOT_LAST'):r27.status(root)
    def test_install_mock_positive_no_real_windows(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'WeiDU.log').write_text('~BGXTD15/SETUP-BGXTD15.TP2~ #0 #0\n')
            (root/'chitin.key').write_bytes(b'key')
            exe=root/r27.WEIDU_EXE;exe.write_bytes(b'MZ'+b'\0'*1000)
            def pretend_weidu(rr, uninstall=False):
                self.assertFalse(uninstall)
                target=r27.regular(root,r27.MODULE);target.parent.mkdir(exist_ok=True)
                target.write_bytes((root/r27.STAGED).read_bytes())
                with (root/'WeiDU.log').open('a') as out:out.write('~BGXR27/SETUP-BGXR27.TP2~ #0 #0\n')
            with mock.patch.multiple(r27,game=lambda x:None,baseline=lambda x:None,processes=lambda:None,
                                     weidu=lambda x:exe,backup=lambda x:Path('/MOCKED_OUTSIDE_GAME'),run_weidu=pretend_weidu):
                z=r27.install(root,r27.INSTALL_TOKEN)
            self.assertEqual(z['status'],'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST')
            self.assertEqual(r27.digest(root/r27.MODULE),r27.SOURCE_SHA)
            self.assertFalse(z['weaponSwitchAuthorized'])
            self.assertFalse(z['dispatchAuthorized'])
            self.assertTrue((root/r27.PROOF).is_file())
    def test_installer_requires_typed_and_backup_before_weidu(self):
        s=(D/'BGXAI_R27_GUARDED.py').read_text()
        self.assertLess(s.index('b = backup(root)'),s.index('run_weidu(root)'))
        self.assertLess(s.index("if token != INSTALL_TOKEN"),s.index('preflight(root)'))
        self.assertIn('if not R27_LAST.match(last(root))',s)
    def test_manifest_exact(self):
        m=json.loads((D/'manifest_updater.json').read_text())
        self.assertEqual(m['schema'],1)
        self.assertEqual(m['channel'],'bgxai-fox-new-safe-source')
        self.assertEqual({x['dest'] for x in m['files']},{'M_BGXR27.lua','BGXAI_R27_GUARDED.py','BGXAI_R28_NATIVE_FROM_R27_RO.py','BGXAI_WEAPON_NATIVE_ITM_R3_RO.py'})
        for obj in m['files']:
            f=D/obj['dest']
            self.assertEqual(f.stat().st_size,obj['size'])
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),obj['sha256'])
    def test_no_hidden_deploy_from_sync(self):
        s=(D/'BGXAI_R27_GUARDED.py').read_text()
        self.assertIn("choices=['menu','status','preflight','install','rollback','capture','native']",s)
        self.assertNotIn('check=True',s)
        self.assertNotIn('Invoke-WebRequest',s)
        self.assertIn("'5':'capture'",s)


class CaptureTests(unittest.TestCase):
    def test_requires_installed_r27(self):
        with mock.patch.object(r27,'status',return_value={'status':'R27_NOT_INSTALLED'}):
            with self.assertRaisesRegex(ValueError,'R27_NOT_INSTALLED_FOR_CAPTURE'):
                r27.capture_console(Path('unused'))
    def test_fails_if_game_already_running(self):
        with mock.patch.object(r27,'status',return_value={'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'}),\
             mock.patch.object(r27,'processes',side_effect=ValueError('GAME_OR_WEIDU_RUNNING')):
            with self.assertRaisesRegex(ValueError,'GAME_OR_WEIDU_RUNNING'):
                r27.capture_console(Path('unused'))
    def test_requires_valid_loader_before_launch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with mock.patch.object(r27,'status',return_value={'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'}),\
                 mock.patch.object(r27,'processes'):
                with self.assertRaisesRegex(ValueError,'INFINITYLOADER_EXE_MISSING_OR_INVALID'):
                    r27.capture_console(root)
    def _simulate(self, lines, exit_code):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'game';root.mkdir()
            (root/'InfinityLoader.exe').write_bytes(b'MZ'+b'Z'*2048)
            home=Path(td)/'user';(home/'Documents').mkdir(parents=True)
            launches=[]
            class Child:
                def wait(self):return exit_code
            def fake_popen(args, **kwargs):
                launches.append((args,kwargs))
                kwargs['stdout'].write(lines)
                return Child()
            with mock.patch.object(r27,'status',return_value={'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'}),\
                 mock.patch.object(r27,'processes'),\
                 mock.patch.dict(r27.os.environ,{'USERPROFILE':str(home)}),\
                 mock.patch.object(r27.subprocess,'Popen',fake_popen):
                result=r27.capture_console(root)
            self.assertEqual(len(launches),1)
            self.assertEqual(launches[0][0],[str(root/'InfinityLoader.exe')])
            self.assertEqual(launches[0][1]['cwd'],root)
            self.assertFalse(result['weaponSwitchAuthorized'])
            self.assertFalse(result['gameplayResourcesModifiedByCapture'])
            self.assertEqual(Path(result['reportFile']).read_bytes(),lines)
            return result
    def test_realistic_capture_has_markers(self):
        lines=b'[BGXR27] {"type":"SESSION"}\n[BGXR27] {"type":"R27_SINGLE_CALLBACK","readOnly":true}\n'
        r=self._simulate(lines,0)
        self.assertEqual(r['status'],'R27_RUNTIME_LOG_PRESENT_AWAITING_REVIEW')
        self.assertEqual(r['selectedActionSamples'],1)
        self.assertEqual(r['sessionMarkers'],1)
    def test_no_sample_is_hold_not_live(self):
        r=self._simulate(b'[BGXR27] {"type":"SESSION"}\n',0)
        self.assertEqual(r['status'],'R27_CAPTURE_HOLD_CHECK_LOG')
        self.assertEqual(r['selectedActionSamples'],0)
    def test_nonzero_exit_is_hold(self):
        r=self._simulate(b'[BGXR27] {"type":"SESSION"}\n[BGXR27] {"type":"R27_SINGLE_CALLBACK"}\n',17)
        self.assertEqual(r['status'],'R27_CAPTURE_HOLD_CHECK_LOG')
        self.assertEqual(r['gameExitCode'],17)
    def test_other_modules_cannot_fake_r27_sample(self):
        r=self._simulate(b'[BGXW2] {"type":"R27_SINGLE_CALLBACK"}\n',0)
        self.assertEqual(r['status'],'R27_CAPTURE_HOLD_CHECK_LOG')
    def test_read_only_no_restart_rollback_side_effects(self):
        code=(D/'BGXAI_R27_GUARDED.py').read_text()
        body=code.split('def capture_console(',1)[1].split('def main(',1)[0]
        for banned in ('run_weidu(', 'shutil.copy2(', 'write_text(', 'unlink(', 'SelectWeaponAbility(', 'os.system('):
            self.assertNotIn(banned,body)
        self.assertIn('subprocess.Popen(',body)

if __name__=='__main__':unittest.main()
