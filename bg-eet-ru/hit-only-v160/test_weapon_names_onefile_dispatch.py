import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SRC=Path(__file__).with_name('weapon_names_onefile_dispatch.py')
spec=importlib.util.spec_from_file_location('v162d',SRC)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.game=self.root/'game';self.game.mkdir()
        (self.game/'chitin.key').write_bytes(b'KEY TEST')
        self.work=self.root/'outside';self.work.mkdir()
        self.cache=self.work/'.BG_EET_RU_AUTOFIX_CACHE'
    def test_external_cache_only(self):
        cache=d._external_root(self.game,self.work)
        self.assertEqual(cache,self.cache)
        self.assertTrue(cache.is_dir())
        self.assertNotIn(str(cache),str(self.game))
    def test_cache_never_allowed_inside_game(self):
        for path in (self.game,self.game/'backup'):
            with self.subTest(path=path),self.assertRaises(d.SourceHold):
                d._external_root(self.game,path)
    def test_missing_source_sha_denied_before_load(self):
        with self.assertRaises(d.SourceHold):d._pinned_source(self.work,'batch',True)
    def test_offline_missing_verified_source_fails(self):
        content=b'NO GAME WRITES\n'
        self.cache.mkdir()
        with patch.dict(d.SOURCES,{'batch':('staged/mock.py',hashlib.sha256(content).hexdigest())}):
            with self.assertRaisesRegex(d.SourceHold,'PINNED_CACHE_MISSING_OFFLINE'):
                d._pinned_source(self.cache,'batch',True)
    def test_exact_pinned_file_only(self):
        content=b'FAKE = True\n';self.cache.mkdir()
        path=self.cache/'staged'/'mock.py';path.parent.mkdir()
        path.write_bytes(content)
        with patch.dict(d.SOURCES,{'batch':('staged/mock.py',hashlib.sha256(content).hexdigest())}):
            self.assertEqual(d._pinned_source(self.cache,'batch',True),path)
            path.write_bytes(content+b'changed')
            with self.assertRaisesRegex(d.SourceHold,'CACHE_SOURCE_DRIFT_REQUIRES_REVIEW'):
                d._pinned_source(self.cache,'batch',True)
    def test_symlink_cache_source_denied(self):
        self.cache.mkdir()
        content=b'fake';p=self.cache/'mock.py';p.symlink_to(self.game/'chitin.key')
        with patch.dict(d.SOURCES,{'batch':('mock.py',hashlib.sha256(content).hexdigest())}):
            with self.assertRaisesRegex(d.SourceHold,'CACHE_FILE_UNSAFE'):
                d._pinned_source(self.cache,'batch',True)
    def test_status_routes_to_existing_batch(self):
        batch=SimpleNamespace(run=lambda *args: {'status':'BATCH_NOT_INSTALLED','gameFilesWritten':0})
        with patch.object(d,'_pinned_source',return_value=self.root/'a.py'),patch.object(d,'_module',return_value=batch):
            out=d.run(self.game,self.work,'status',offline=True)
        self.assertEqual(out['status'],'BATCH_NOT_INSTALLED')
    def test_preflight_routes_to_catalog_without_prompt(self):
        called=[]
        def native_run(*args):
            called.append(args)
            return {'status':'BATCH_PREFLIGHT_PASS','gameFilesWritten':0}
        batch=SimpleNamespace(run=native_run,HISTORICAL_WEAPON_SEEDS_64=('STAF01',))
        v160=SimpleNamespace(GAME_PINS={'file':'hash'})
        with patch.object(d,'_pinned_source',return_value=self.root/'a.py'),patch.object(d,'_module',side_effect=[batch,v160]),patch.object(d,'_readonly_catalog',return_value=({'items':{}},object())),patch('builtins.input',side_effect=AssertionError('no prompt')):
            r=d.run(self.game,self.work,'preflight',offline=True)
        self.assertEqual(r['status'],'BATCH_PREFLIGHT_PASS')
        self.assertEqual(called[0][0],'preflight')
    def test_install_not_executed_without_windows(self):
        with patch.object(d,'_pinned_source',return_value=self.root/'a.py'),patch.object(d,'_module',return_value=SimpleNamespace()):
            with patch.object(d.sys,'platform','linux'):
                r=d.run(self.game,self.work,'install',offline=True)
        self.assertEqual(r['status'],'BATCH_SAFE_STOP')
        self.assertIn('WINDOWS',r['reason'])
    def test_import_only_not_another_updater(self):
        code=SRC.read_text(encoding='utf-8')
        self.assertIn("if __name__ == '__main__'",code)
        self.assertIn('BG_EET_RU_UPDATE.cmd',code)
        self.assertNotIn('XEquipItem(',code)
        self.assertNotIn('EEex_Sprite_AddAlterBaseWeaponDamageListener(',code)
        self.assertNotIn('os.system(',code)
if __name__=='__main__':unittest.main(verbosity=2)