from __future__ import annotations
import contextlib,hashlib,io,json,os,pathlib,shutil,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import BGXAI_R13_HOLD_DIAG_GUARDED as mod

ROOT=pathlib.Path(__file__).parent
class R15GuardedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)/'GAME';self.root.mkdir()
        self.home=pathlib.Path(self.tmp.name)/'HOME';self.home.mkdir()
        self.gamebytes={}
        for rel in ('override/M_BGXD13.lua','override/M_BGXTDEF13.lua'):
            p=self.root/rel;p.parent.mkdir(exist_ok=True,parents=True)
            if rel.endswith('M_BGXD13.lua'):p.write_bytes((ROOT/'M_BGXD13.lua').read_bytes())
            else:p.write_bytes((ROOT/'M_BGXTDEF13.lua').read_bytes())
        (self.root/'BGXTD14').mkdir()
        (self.root/'BGXTD14/PROOF.json').write_text(json.dumps({'sourceSha256':mod.PREVIOUS_SHA,'status':'BGXTD14_SHORTNAME_INSTALLED_AWAITING_LIVE_TEST'}))
        (self.root/'BGXTDEF13').mkdir()
        (self.root/'BGXTDEF13/PROOF.json').write_text(json.dumps({'sourceSha256':mod.ORIGINAL_SHA,'status':'BGXTD13_INSTALLED_AWAITING_LIVE_TEST'}))
        (self.root/'WeiDU.log').write_text('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0 // BGXTD14 installed\n')
        (self.root/'chitin.key').write_bytes(b'KEY')
        (self.root/mod.WEIDU_EXE).write_bytes(b'MZ'+b'x'*60000)
        fake_baseline={}
        for rel in mod.BASELINE:
            x=self.root/rel;x.parent.mkdir(parents=True,exist_ok=True)
            x.write_bytes(('mock validated baseline '+rel).encode())
            fake_baseline[rel]=hashlib.sha256(x.read_bytes()).hexdigest()
        self.patches=[
         patch.object(mod,'BASELINE',fake_baseline),
         patch.object(mod,'game',lambda _:None),
         patch.object(mod,'processes',lambda :None),
         patch.object(mod,'baseline',lambda _:None),
         patch.object(mod,'outside_dir',lambda :self.home/'BACKUPS')]
        for p in self.patches:p.start();self.addCleanup(p.stop)
    def test_01_short_resref(self):self.assertEqual(len(pathlib.Path(mod.MODULE).stem),8)
    def test_02_source(self):self.assertIsNone(mod.sources())
    def test_03_preflight_readonly(self):
        b=mod.preflight(self.root);self.assertEqual(b['status'],'BGXTD15_PREFLIGHT_PASS_NO_INSTALL');self.assertFalse((self.root/mod.DIR).exists())
    def test_04_default_status(self):self.assertEqual(mod.status(self.root)['status'],'BGXTD15_NOT_INSTALLED')
    def test_05_install_requires_token(self):
        with self.assertRaisesRegex(ValueError,'INSTALL_TOKEN_REQUIRED'):mod.install(self.root,'')
    def test_06_bad_prev_last_stops(self):
        (self.root/'WeiDU.log').write_text('~OTHER\\SETUP.TP2~ #0 #0\n')
        with self.assertRaisesRegex(ValueError,'BGXTD14_NOT_LAST'):mod.preflight(self.root)
    def test_07_modified_prev_sha_stops(self):
        (self.root/mod.MODULE).write_bytes(b'wronG')
        with self.assertRaisesRegex(ValueError,'SHA_DRIFT'):mod.preflight(self.root)
    def test_08_existing_component_stops(self):
        (self.root/mod.DIR).mkdir()
        with self.assertRaisesRegex(ValueError,'PATH_ALREADY_EXISTS'):mod.preflight(self.root)
    def test_09_native_weidu_required(self):
        (self.root/mod.WEIDU_EXE).unlink()
        with self.assertRaisesRegex(ValueError,'WEIDU_EXE_UNAVAILABLE'):mod.preflight(self.root)
    def test_10_source_invalid_sha_stops(self):
        with patch.object(mod,'SOURCE_SHA','000'):
            with self.assertRaisesRegex(ValueError,'DIAG_SOURCE_SHA_MISMATCH'):mod.sources()
    def test_11_source_banned_check(self):
        p=self.home/'evil.lua';p.write_bytes((ROOT/'R15_M_BGXD13.lua').read_bytes()+b'SelectWeaponAbility(')
        with patch.object(mod,'SOURCE',p),patch.object(mod,'SOURCE_SHA',hashlib.sha256(p.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError,'NOT_PASSIVE'):mod.sources()
    def test_12_backup_external_originals(self):
        b=mod.backup(self.root)
        self.assertFalse(str(b).startswith(str(self.root)))
        self.assertEqual(mod.sha(b/mod.MODULE),mod.PREVIOUS_SHA)
        self.assertEqual(mod.sha(b/mod.ORIGINAL),mod.ORIGINAL_SHA)
        self.assertEqual((b/'WeiDU.log').read_bytes(),(self.root/'WeiDU.log').read_bytes())
    def test_13_invalid_abort_before_stage(self):
        with self.assertRaisesRegex(ValueError,'INSTALL_TOKEN_REQUIRED'):mod.install(self.root,'invalid')
        self.assertFalse((self.root/mod.DIR).exists())
    def test_14_wrong_uninstall_token(self):
        with self.assertRaisesRegex(ValueError,'ROLLBACK_TOKEN_REQUIRED'):mod.rollback(self.root,'invalid')
    def test_15_weiDU_tp2_targets_only_module(self):
        s=mod.TP2_TEXT;self.assertEqual(s.count('COPY '),1)
        self.assertIn('~override/M_BGXD13.lua~',s)
        self.assertNotIn('M_BGXTDEF13',s)
    def test_16_full_install_rollback_roundtrip(self):
        before={p.relative_to(self.root):mod.sha(p) for p in self.root.rglob('*') if p.is_file()}
        def fake_weidu(root,uninstall=False):
            if uninstall:
                (root/mod.MODULE).write_bytes((ROOT/'M_BGXD13.lua').read_bytes())
                (root/'WeiDU.log').write_text('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0\n')
            else:
                (root/mod.MODULE).write_bytes(mod.SOURCE.read_bytes())
                (root/'WeiDU.log').write_text('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0\n~BGXTD15\\SETUP-BGXTD15.TP2~ #0 #0\n')
        with patch.object(mod,'run_weidu',fake_weidu):
            p=mod.install(self.root,mod.INSTALL_TOKEN)
            self.assertEqual(p['status'],'BGXTD15_INSTALLED_AWAITING_LIVE_TEST')
            self.assertEqual(mod.status(self.root)['status'],'BGXTD15_INSTALLED_AWAITING_LIVE_TEST')
            self.assertTrue((self.root/mod.PROOF).exists());self.assertTrue(pathlib.Path(p['externalBackup']).exists())
            for f in (mod.ORIGINAL,'BGXTD14/PROOF.json','BGXTDEF13/PROOF.json'):
                self.assertEqual(mod.sha(self.root/f),before[pathlib.Path(f)])
            # Simulate unrelated WeiDU component installed afterward: never revert.
            (self.root/'WeiDU.log').write_text('~OTHER\\SETUP.TP2~ #0 #0\n')
            with self.assertRaisesRegex(ValueError,'NOT_LAST'):mod.rollback(self.root,mod.ROLLBACK_TOKEN)
            (self.root/'WeiDU.log').write_text('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0\n~BGXTD15\\SETUP-BGXTD15.TP2~ #0 #0\n')
            res=mod.rollback(self.root,mod.ROLLBACK_TOKEN)
            self.assertEqual(res['status'],'BGXTD15_ROLLBACK_TD14_RESTORED_VERIFIED')
            self.assertEqual(mod.sha(self.root/mod.MODULE),mod.PREVIOUS_SHA)
            self.assertEqual(mod.status(self.root)['status'],'BGXTD15_NOT_INSTALLED')
    def test_17_last_only_after_install(self):
        self.assertTrue(mod.OLD_LAST.match('~BGXTD14\\SETUP-BGXTD14.TP2~ #0 #0 // x'))
        self.assertFalse(mod.OLD_LAST.match('~BGXTD15\\SETUP-BGXTD15.TP2~ #0 #0'))
        self.assertTrue(mod.NEW_LAST.match('~BGXTD15\\SETUP-BGXTD15.TP2~ #0 #0'))
    def test_19_capture_requires_td15_deploy(self):
        with self.assertRaisesRegex(ValueError,'NOT_INSTALLED_FOR_CAPTURE'):
            mod.capture_console(self.root)
    def test_20_capture_readonly(self):
        # A successful capture must not invoke WeiDU or edit game resources.
        exe=self.root/'InfinityLoader.exe';exe.write_bytes(b'MZ'+b'0'*60000)
        (self.root/mod.MODULE).write_bytes(mod.SOURCE.read_bytes())
        (self.root/'WeiDU.log').write_text('~BGXTD15\\SETUP-BGXTD15.TP2~ #0 #0\n')
        (self.root/'BGXTD15').mkdir()
        (self.root/mod.PROOF).write_text(json.dumps({'status':'BGXTD15_INSTALLED_AWAITING_LIVE_TEST','sourceSha256':mod.SOURCE_SHA}))
        docs=self.home/'Documents';docs.mkdir()
        class Process:
            def wait(self):return 0
        def fake_popen(argv,**kw):
            kw['stdout'].write(b'[BGXTD13] {"type":"SESSION"}\n')
            return Process()
        before=mod.sha(self.root/mod.MODULE)
        with patch.dict(os.environ,{'USERPROFILE':str(self.home)}),patch.object(mod.subprocess,'Popen',fake_popen),patch.object(mod,'run_weidu',side_effect=AssertionError('NO_WEIDU_IN_CAPTURE')):
            report=mod.capture_console(self.root)
        self.assertEqual(report['status'],'BGXTD15_CAPTURE_CREATED')
        self.assertTrue(pathlib.Path(report['consoleLog']).is_file())
        self.assertEqual(mod.sha(self.root/mod.MODULE),before)
        self.assertFalse(report['gameplayResourcesModified'])
    def test_18_artifact_is_passive(self):
        b=mod.SOURCE.read_bytes();self.assertEqual(b.count(b'EEex_Action_AddSpriteStartedActionListener(R.on_started)'),1)
        self.assertTrue(all(x not in b for x in mod.BLOCKED))
        self.assertIn(b'safe_reason(q.reason)',b);self.assertIn(b'selectedSlot==10',b)

if __name__=='__main__':unittest.main()
