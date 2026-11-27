import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('v3native',HERE/'BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py')
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
EVIDENCE=HERE/m.EVIDENCE_NAME

class FakeBackend:
    TEMP_SOURCE_NAME='ORIGINAL.baf'
    def source_check(self,src,game):
        raise AssertionError('original backend source_check must be replaced')
    def checked_file(self,p,required=False):
        return Path(p).read_bytes()
    def compile_readonly(self,game,source,compiler):
        result=self.source_check(source,game)
        assert result['sha256']==m.BAF_SHA256
        assert self.TEMP_SOURCE_NAME=='BGXW3NAT.baf'
        self.observed=source.read_bytes()
        return {'status': 'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
            'nativeSymbolsAcceptedByCompiler': True,
            'watchedFilesChanged': False,
            'temporaryOutputRemoved':True,
            'compilerSha256':'f'*64,'compiledSha256':'1'*64}

class Tests(unittest.TestCase):
    def test_exact_pinned_baf(self):
        raw=m.verified_evidence(EVIDENCE)
        self.assertEqual(len(raw),762)
        self.assertEqual(m.sha(raw),m.BAF_SHA256)
        self.assertEqual(raw.count(b'XEquipItem('),1)
    def test_default_is_no_native(self):
        o=m.source_only(EVIDENCE)
        self.assertEqual(o['status'],'EXACT_V3_BAF_PIN_VERIFIED_NO_NATIVE_COMPILE')
        self.assertFalse(o['nativeWeiDUCompileVerified'])
        self.assertFalse(o['dispatchAuthorized'])
        self.assertEqual(o['ordersSent'],0)
    def test_public_evidence_has_no_private_gam(self):
        d=EVIDENCE.read_bytes()
        self.assertNotIn(b'GAMEV2.0',d)
        self.assertNotIn(b'CRE V1.0',d)
    def test_any_byte_mutation_rejected(self):
        original=EVIDENCE.read_bytes()
        for variant in (original+b' ', original[:-1],original.replace(b'STAF01',b'AXE001'),
                        original.replace(b'"installed": false',b'"installed": true')):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/m.EVIDENCE_NAME;p.write_bytes(variant)
                with self.assertRaises(m.Hold):m.verified_evidence(p)
    def test_non_regular_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/m.EVIDENCE_NAME
            p.mkdir()
            with self.assertRaises(m.Hold):m.verified_evidence(p)
    def test_wrong_name_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'other.json';p.write_bytes(EVIDENCE.read_bytes())
            with self.assertRaises(m.Hold):m.verified_evidence(p)
    def test_no_game_modification_ops_source(self):
        source=(HERE/'BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py').read_text()
        for symbol in ('InstallComponent','InstallMod','--force-install','--install','--make-biff'):
            self.assertNotIn(symbol,source)
        self.assertIn("backend.compile_readonly(game, source, compiler)",source)
    def test_close_game_denies_unix(self):
        if sys.platform != 'win32':
            with self.assertRaisesRegex(m.Hold,'WINDOWS_ONLY'):m.close_game_proof()
    def test_backend_wrong_blob_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/Path(m.BACKEND_RELPATH).name
            p.write_text('from __future__ import annotations\n')
            with self.assertRaisesRegex(m.Hold,'BLOB_PIN_CHANGED'):m.load_backend(p)
    def test_native_mock_success_not_live(self):
        fake=FakeBackend()
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.object(m,'close_game_proof'), \
             mock.patch.object(m,'pinned_compiler',return_value=Path('mock_weidu.exe')), \
             mock.patch.object(m,'load_backend',return_value=fake):
            folder=Path(t)/'game';folder.mkdir()
            z=m.native_readonly(folder,EVIDENCE,Path('pinned_backend.py'))
            self.assertEqual(z['status'],'V3_NATIVE_BAF_COMPILED_TEMP_ONLY')
            self.assertFalse(z['safeActionBoundaryVerified'])
            self.assertFalse(z['installed'])
            self.assertFalse(z['runtimeActorIdentityVerified'])
            self.assertEqual(fake.TEMP_SOURCE_NAME,'ORIGINAL.baf')
            self.assertTrue(fake.observed.startswith(b'// BGXAI V3'))
    def test_native_mock_changed_watch_hold(self):
        class Drift(FakeBackend):
            def compile_readonly(self,game,source,compiler):
                d=super().compile_readonly(game,source,compiler)
                d['watchedFilesChanged']=True
                return d
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.object(m,'close_game_proof'), \
             mock.patch.object(m,'pinned_compiler',return_value=Path('mock_weidu.exe')), \
             mock.patch.object(m,'load_backend',return_value=Drift()):
            folder=Path(t)/'game';folder.mkdir()
            out=m.native_readonly(folder,EVIDENCE,Path('pinned_backend.py'))
            self.assertEqual(out['status'],'HOLD_V3_NATIVE_COMPILE')
            self.assertFalse(out['nativeWeiDUCompileVerified'])
    def test_native_mock_bad_source_refused(self):
        class Cheater(FakeBackend):
            def compile_readonly(self,game,source,compiler):
                source.write_bytes(b'false')
                self.source_check(source,game)
                return {}
        cheater=Cheater()
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.object(m,'close_game_proof'), \
             mock.patch.object(m,'pinned_compiler',return_value=Path('mock_weidu.exe')), \
             mock.patch.object(m,'load_backend',return_value=cheater):
            folder=Path(t)/'game';folder.mkdir()
            with self.assertRaises(Exception):
                m.native_readonly(folder,EVIDENCE,Path('pinned_backend.py'))
            self.assertEqual(cheater.TEMP_SOURCE_NAME,'ORIGINAL.baf')
    def test_main_fail_closed_on_missing_backend(self):
        with mock.patch('sys.stdout'):
            code=m.main(['--native-readonly','--evidence',str(EVIDENCE)])
        self.assertEqual(code,3)
    def test_source_file_unchanged(self):
        before=m.sha(EVIDENCE.read_bytes())
        m.source_only(EVIDENCE)
        after=m.sha(EVIDENCE.read_bytes())
        self.assertEqual(before,after)

if __name__=='__main__':unittest.main(verbosity=2)