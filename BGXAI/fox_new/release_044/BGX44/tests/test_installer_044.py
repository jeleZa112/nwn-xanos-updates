import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import sys

HERE = Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('bgx44',HERE/'BGXAI44_INSTALL.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
REAL=m.digest


class Result:
    def __init__(self,code=0):self.returncode=code;self.stdout='FAKE WEIDU';self.stderr=''


class PackageTests(unittest.TestCase):
    def test_manifest_valid(self):self.assertEqual(m.source_manifest(HERE)['version'],m.VERSION)
    def test_diagnostic_lua_does_not_queue_actions(self):
        s=(HERE/m.MOD_LUA).read_text()
        for tok in ('QueueResponse(', 'ClearActions(', 'ActionOverride(', 'SetGlobal('):
            self.assertNotIn(tok,s)
    def test_zip_paths_are_rejected(self):
        with self.assertRaises(RuntimeError):m.safe(HERE,'../outside')
        with self.assertRaises(RuntimeError):m.safe(HERE,'C:\\Windows\\file')


class MockGame(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        base=Path(self.t.name)
        self.root=base/'game';self.root.mkdir()
        self.bk=base/'backup'
        def put(rel,data):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        put('chitin.key',b'C'*2000)
        put(m.EXE_SRC,b'MZ'+b'X'*101000)
        put('InfinityLoader.exe',b'MZ'+b'L'*20000)
        put(m.BOOT,b'EEEX dummy boot')
        put(m.BCS,b'BCS'*12000)
        put(m.OBSERVER,b'043 Lua source mock'*12)
        put('lang/ru_RU/dialog.tlk',b'ru dialog test')
        put('lang/ru_RU/dialogf.tlk',b'ru f test')
        put('WeiDU.log',b'~BGX42/setup-BGX42.TP2~ #0 #0 // BGX42\n~BGX43/setup-BGX43.TP2~ #0 #0 // BGX43\n')
        def mock_hash(p):
            if p.name=='BDDEFAI.BCS' and p.read_bytes()==b'BCS'*12000:return m.BASE_BCS
            if p.name=='M_BGX43Probe.lua' and p.read_bytes()==b'043 Lua source mock'*12:return m.BASE_OBSERVER
            return REAL(p)
        self.patch=mock.patch.object(m,'digest',side_effect=mock_hash);self.patch.start()
    def tearDown(self):self.patch.stop();self.t.cleanup()
    def runner(self,cmd,**kwargs):
        log=self.root/'WeiDU.log'
        if '--force-uninstall' in cmd:
            log.write_text('\n'.join(log.read_text().splitlines()[:-1])+'\n')
            (self.root/m.DEPLOYED).unlink()
        else:
            shutil.copy2(self.root/m.MOD_LUA,self.root/m.DEPLOYED)
            with log.open('a') as f:f.write('~BGX44/setup-BGX44.TP2~ #0 #0 // BGX44\n')
        return Result()
    def install(self):return m.install(self.root,HERE,runner=self.runner,guard=lambda:None,enforce_root=False,backup_dir=self.bk)
    def test_success_install_and_rollback(self):
        before={rel:REAL(self.root/rel) for rel in ('chitin.key',m.BCS,m.OBSERVER,m.BOOT)}
        a=self.install()
        self.assertEqual(a['status'],'INSTALLED_PASSIVE_044')
        self.assertTrue(all(a['checks'].values()))
        self.assertEqual(m.get_install_backup(self.root,base=self.bk),Path(a['backup']))
        b=m.uninstall(self.root,HERE,runner=self.runner,guard=lambda:None,enforce_root=False,backup_dir=self.bk)
        self.assertEqual(b['status'],'UNINSTALLED_PASSIVE_044')
        self.assertTrue(all(b['checks'].values()))
        self.assertFalse((self.root/m.DEPLOYED).exists())
        self.assertEqual(before,{rel:REAL(self.root/rel) for rel in before})
    def test_reject_tampered_043(self):
        (self.root/m.OBSERVER).write_text('modified'*40)
        with self.assertRaisesRegex(RuntimeError,'043P observer'):
            self.install()
    def test_reject_bad_bcs(self):
        self.patch.stop()
        with self.assertRaisesRegex(RuntimeError,'042B'):
            self.install()
        self.patch.start()
    def test_reject_nonlast_043(self):
        with (self.root/'WeiDU.log').open('a') as f:f.write('~ANOTHER/SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'043P must be last'):
            self.install()
    def test_reject_name_collision(self):
        (self.root/m.DEPLOYED).write_text('collision')
        with self.assertRaisesRegex(RuntimeError,'collision'):
            self.install()
    def test_rollback_requires_last(self):
        self.assertEqual(self.install()['status'],'INSTALLED_PASSIVE_044')
        with (self.root/'WeiDU.log').open('a') as f:f.write('~OTHER/setup-other.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'BGX44 is not last'):
            m.uninstall(self.root,HERE,runner=self.runner,guard=lambda:None,enforce_root=False,backup_dir=self.bk)
    def test_rollback_requires_verified_backup(self):
        self.assertEqual(self.install()['status'],'INSTALLED_PASSIVE_044')
        with self.assertRaisesRegex(RuntimeError,'missing'):
            m.uninstall(self.root,HERE,runner=self.runner,guard=lambda:None,enforce_root=False,backup_dir=self.root/'nonexistent')
    def test_weidu_failure_is_not_success(self):
        def fail(cmd,**kwargs):return Result(code=1)
        a=m.install(self.root,HERE,runner=fail,guard=lambda:None,enforce_root=False,backup_dir=self.bk)
        self.assertEqual(a['status'],'REVIEW_WEIDU')
        self.assertTrue(Path(a['backup'],'report.json').exists())


if __name__=='__main__':unittest.main()
