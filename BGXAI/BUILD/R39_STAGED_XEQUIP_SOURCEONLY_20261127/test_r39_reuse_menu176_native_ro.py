"""Purely offline safety tests; cannot claim native Windows EET compile."""
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch
import BGXAI_R39_NATIVE_EET_COMPILE_RO_V1 as p


class NativeReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(__file__).with_name(p.BAF_NAME)

    def test_exact_published_baf(self):
        s=p.exact_source(self.source)
        self.assertEqual(len(s),2303)
        self.assertEqual(hashlib.sha256(s).hexdigest(),p.BAF_SHA)

    def test_native_missing_sources_fails_closed(self):
        self.assertEqual(p.main(['--native-readonly','--source',str(self.source)]),3)

    def test_source_only_never_native_pass(self):
        v=p.source_only(self.source)
        self.assertEqual(v['status'],'EXACT_R39_BAF_PIN_PASS_NO_NATIVE')
        self.assertIs(v['nativeWeiDUCompileVerified'],False)
        self.assertFalse(v['gameModified'])
        self.assertFalse(v['dispatchAuthorized'])

    def test_invalid_source_baf_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.BAF_NAME;x.write_bytes(self.source.read_bytes()[:-1])
            with self.assertRaises(p.Hold):p.exact_source(x)

    def test_baf_name_guard(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/'R39_OTHER.baf';x.write_bytes(self.source.read_bytes())
            with self.assertRaises(p.Hold):p.exact_source(x)

    def test_no_v3_helper_incorrect_sha(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.V3_HELPER_NAME;x.write_text('broken')
            with self.assertRaises(p.Hold):p.exact_v3_helper(x)

    def test_v3_known_exact_pinned_source_import(self):
        historical=Path('/mnt/data/bgxai_audit/current/BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py')
        if not historical.is_file():
            self.skipTest('Historical private helper is not bundled with published source-only tests')
        raw=historical.read_bytes()
        if len(raw)==p.V3_HELPER_BYTES+1 and raw.endswith(b'\n'): raw=raw[:-1]
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.V3_HELPER_NAME;x.write_bytes(raw)
            mod=p.exact_v3_helper(x)
            self.assertTrue(callable(mod.close_game_proof))

    def test_source_does_not_install(self):
        src=Path(p.__file__).read_text('utf-8')
        for forbidden in ('--force-install','--force-uninstall',
                          'setup-BGXR41',
                          'SetGlobal("BGXW3ARM","LOCALS",1)',
                          'shutil.copy2('):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,src)

    def test_source_only_does_not_need_game(self):
        v=p.source_only(self.source)
        self.assertEqual(v['sourceBytes'],2303)
        self.assertNotIn('compiledBcsSha256',v)

    def test_backend_reuse_contract(self):
        src=Path(p.__file__).read_text('utf-8')
        for token in ('v3.close_game_proof()', 'v3.pinned_compiler(game)',
                      'v3.load_backend(backend_path)',
                      'backend.compile_readonly(game,candidate,compiler)',
                      'backend.source_check=orig_check'):
            self.assertIn(token,src)

    def test_native_mock_result_never_claims_install(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            class FakeBackend:
                TEMP_SOURCE_NAME='old.baf'
                def source_check(self,src,root): return None
                def checked_file(self,path,required=False):return path.read_bytes()
                class Hold(ValueError):pass
                def compile_readonly(self,root,src,compiler):
                    assert src.name=='BGXW39.baf'
                    assert self.TEMP_SOURCE_NAME==src.name
                    assert self.source_check(src,root)['blocks']==3
                    return {'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                            'nativeSymbolsAcceptedByCompiler':True,
                            'watchedFilesChanged':False,'temporaryOutputRemoved':True,
                            'compiledSha256':'FAKE_TEST_ONLY','compilerSha256':'FAKE_TEST_ONLY'}
            backend=FakeBackend()
            class FakeHelper:
                def close_game_proof(self): pass
                def pinned_compiler(self,game):return game/'fake.exe'
                def load_backend(self,src):return backend
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()):
                out=p.native_readonly(game,self.source,game/'helper',game/'backend')
            self.assertEqual(out['status'],'R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL')
            self.assertFalse(out['installed']);self.assertFalse(out['gameModified'])
            self.assertFalse(out['dispatchAuthorized']);self.assertFalse(out['liveXEquipTransferVerified'])
            self.assertEqual(backend.TEMP_SOURCE_NAME,'old.baf')

    def test_native_mock_rejects_bad_report(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            class FakeBackend:
                TEMP_SOURCE_NAME='old.baf'
                def source_check(self,src,root):return None
                def checked_file(self,path,required=False):return path.read_bytes()
                def compile_readonly(self,root,src,compiler):
                    return {'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                            'nativeSymbolsAcceptedByCompiler':True,
                            'watchedFilesChanged':True,'temporaryOutputRemoved':True}
                class Hold(ValueError):pass
            class FakeHelper:
                def close_game_proof(self):pass
                def pinned_compiler(self,game):return game/'fake.exe'
                def load_backend(self,src):return FakeBackend()
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()):
                out=p.native_readonly(game,self.source,game/'helper',game/'backend')
            self.assertEqual(out['status'],'HOLD_R39_NATIVE_EET_COMPILER')
            self.assertFalse(out['nativeWeiDUCompileVerified'])


if __name__=='__main__':unittest.main()
