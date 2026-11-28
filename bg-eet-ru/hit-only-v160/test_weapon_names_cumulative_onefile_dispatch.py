# -*- coding: utf-8 -*-
"""Unit tests of V163 entrypoint: pure fake modules, no live game writes."""
from pathlib import Path
import importlib.util
import tempfile
import types
import unittest
from unittest.mock import patch

SRC=Path(__file__).with_name('weapon_names_cumulative_onefile_dispatch.py')
spec=importlib.util.spec_from_file_location('v163_tested',SRC)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.game=self.root/'game';self.game.mkdir()
        self.work=self.root/'docs';self.work.mkdir()
        (self.game/'chitin.key').write_bytes(b'KEY')
        self.calls=[]
        self.seeds=tuple('B%07d'%i for i in range(64))
        class Cumulative:
            APPROVE_INSTALL='INSTALL_SECOND_EXACT'
            APPROVE_ROLLBACK='ROLLBACK_SECOND_EXACT'
            HISTORICAL_SECOND_SEEDS_64=self.seeds
            def run(_,mode,game,workdir,batch,catalog=None,resolver=None,typed=None):
                self.calls.append((mode,typed,catalog,resolver))
                statuses={'status':'CUMULATIVE_NOT_INSTALLED',
                          'preflight':'CUMULATIVE_PREFLIGHT_PASS',
                          'install':'CUMULATIVE_INSTALLED_AWAITING_GAMEPLAY',
                          'rollback':'CUMULATIVE_ROLLED_BACK_TO_FIRST64'}
                return {'status':statuses[mode],'gameFilesWritten':int(mode=='install')}
        self.cumulative=Cumulative()
        self.batch=object()
        self.reader=object()
        self.catalog={'items':{'B0000000':{}}}
        self.base=types.SimpleNamespace(
            _module=lambda path,key:self.batch,
            _pinned_source=lambda root,key,offline:root/'verified.py',
            _readonly_catalog=lambda cache,game,seeds,offline:(self.catalog,self.reader) if seeds==self.seeds else (_ for _ in ()).throw(AssertionError('wrong ids')))
        patcher=patch.object(d,'_load',return_value=(self.base,self.cumulative))
        patcher.start();self.addCleanup(patcher.stop)

    def test_preflight_has_no_game_writes_and_uses_exact_64_seed_ids(self):
        report=d.run(self.game,self.work,'preflight',True)
        self.assertEqual(report['status'],'CUMULATIVE_PREFLIGHT_PASS')
        self.assertEqual(report['gameFilesWritten'],0)
        self.assertEqual([x[0] for x in self.calls],['preflight'])
        self.assertIs(self.calls[0][2],self.catalog)
        self.assertIs(self.calls[0][3],self.reader)

    def test_status_never_loads_current_catalog(self):
        self.base._readonly_catalog=lambda *a:(_ for _ in ()).throw(AssertionError('should not scan'))
        report=d.run(self.game,self.work,'status',True)
        self.assertEqual(report['status'],'CUMULATIVE_NOT_INSTALLED')
        self.assertEqual(len(self.calls),1)

    def test_invalid_mode_safe_stop(self):
        report=d.run(self.game,self.work,'unsafe',True)
        self.assertEqual(report['status'],'CUMULATIVE_SAFE_STOP')
        self.assertEqual(report['gameFilesWritten'],0)
        self.assertFalse(self.calls)

    def test_no_game_root_safe_stop_without_cache_creation(self):
        (self.game/'chitin.key').unlink()
        report=d.run(self.game,self.work,'preflight',False)
        self.assertIn('GAME_PATH_UNSAFE',report['reason'])
        self.assertFalse((self.work/'.BG_EET_RU_AUTOFIX_CACHE').exists())

    def test_game_workdir_overlap_rejected(self):
        report=d.run(self.game,self.game,'preflight',True)
        self.assertEqual(report['status'],'CUMULATIVE_SAFE_STOP')

    def test_invalid_old_source_sha_is_rejected(self):
        with patch.object(d,'BASE_SHA','x'*64):
            with self.assertRaises(d.SourceHold):
                d._pinned(self.work,'bad.py','old','https://invalid.invalid',d.BASE_SHA,True)

    def test_readonly_does_not_prompt(self):
        with patch('builtins.input',side_effect=AssertionError('must not prompt')):
            self.assertEqual(d.run(self.game,self.work,'preflight',True)['status'],'CUMULATIVE_PREFLIGHT_PASS')

    def test_typed_install_guards_against_non_windows(self):
        with patch.object(d.sys,'platform','linux'):
            report=d.run(self.game,self.work,'install',True)
        self.assertIn('GAME_WRITES_REQUIRE_WINDOWS',report['reason'])
        self.assertFalse(self.calls)

    def test_install_checks_preflight_before_asking_typed(self):
        old=self.cumulative.run
        def f(*a,**kw):
            value=old(*a,**kw)
            if a[0]=='preflight':value['status']='CUMULATIVE_SAFE_STOP'
            return value
        self.cumulative.run=f
        with patch.object(d.sys,'platform','win32'):
            with patch('builtins.input',side_effect=AssertionError('must not prompt')):
                report=d.run(self.game,self.work,'install',True)
        self.assertEqual(report['status'],'CUMULATIVE_SAFE_STOP')
        self.assertEqual([x[0] for x in self.calls],['preflight'])

    def test_install_typed_pass_through_only_after_preflight(self):
        with patch.object(d.sys,'platform','win32'):
            with patch('builtins.input',return_value='INSTALL_SECOND_EXACT'):
                report=d.run(self.game,self.work,'install',True)
        self.assertEqual(report['status'],'CUMULATIVE_INSTALLED_AWAITING_GAMEPLAY')
        self.assertEqual([(x[0],x[1]) for x in self.calls],[('preflight',None),('install','INSTALL_SECOND_EXACT')])

    def test_rollback_never_calls_new_catalog(self):
        self.base._readonly_catalog=lambda *a:(_ for _ in ()).throw(AssertionError('no new scan'))
        with patch.object(d.sys,'platform','win32'):
            with patch('builtins.input',return_value='ROLLBACK_SECOND_EXACT'):
                report=d.run(self.game,self.work,'rollback',True)
        self.assertEqual(report['status'],'CUMULATIVE_ROLLED_BACK_TO_FIRST64')
        self.assertEqual([(x[0],x[1]) for x in self.calls],[('rollback','ROLLBACK_SECOND_EXACT')])

    def test_remote_must_match_pin_before_writing(self):
        class Resp:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return b'uncertified'
        with patch.object(d,'BASE_SHA','0'*64):
            with patch.object(d.urllib.request,'urlopen',return_value=Resp()):
                with self.assertRaisesRegex(d.SourceHold,'PINNED_DOWNLOAD_SHA_HOLD'):
                    d._pinned(self.work,'candidate.py','test','https://example.invalid','0'*64,False)
        self.assertFalse((self.work/'candidate.py').exists())

    def test_existing_tampered_cache_is_hold_not_download(self):
        p=self.work/'candidate.py';p.write_bytes(b'bad')
        with patch.object(d.urllib.request,'urlopen',side_effect=AssertionError('must not download')):
            with self.assertRaisesRegex(d.SourceHold,'EXISTING_CACHE_SHA_DRIFT'):
                d._pinned(self.work,'candidate.py','test','https://example.invalid','0'*64,False)


if __name__=='__main__': unittest.main()