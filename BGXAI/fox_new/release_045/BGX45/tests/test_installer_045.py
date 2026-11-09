import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bgx45',ROOT/'BGXAI45_INSTALL.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fbytes(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(data)


class Checks(unittest.TestCase):
    def test_no_long_mod_names(self):
        self.assertTrue(all(len(Path(x).stem)<=8 for x in mod.NEW_LUA.values()))

    def test_manifest_and_integrity(self):
        self.assertEqual(mod.verify_sources(ROOT)['version'],mod.VERSION)

    def test_detect_corrupt_source(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            for p in mod.SOURCE_FILES+('SOURCE_MANIFEST.json',):
                dest=t/p
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/p,dest)
            (t/'BGX45/M_BX43.lua').write_bytes(b'bad')
            with self.assertRaisesRegex(RuntimeError,'source/hash'):
                mod.verify_sources(t)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'ok').write_bytes(b'x')
            (root/'alias').symlink_to(root/'ok')
            with self.assertRaisesRegex(RuntimeError,'Symlink'):
                mod.safe(root,'alias')

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError,'Unsafe'):
                mod.safe(Path(td),'../danger')

    def test_start_process_guard_present(self):
        self.assertTrue(any('Get-CimInstance Win32_Process' in str(x) for x in mod.guard_processes.__code__.co_consts))


class MockWeiDU(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'game';self.root.mkdir()
        self.backups=Path(self.tmp.name)/'backups'
        fbytes(self.root/'chitin.key',b'x'*1024)
        fbytes(self.root/'InfinityLoader.exe',b'MZ'+b'x'*10000)
        fbytes(self.root/mod.WEIDU_EXE,b'MZ'+b'x'*110000)
        fbytes(self.root/mod.BOOT,b'EEex bootstrap')
        fbytes(self.root/mod.BCS,b'SC\nFAKE'+b'x'*200)
        fbytes(self.root/mod.ORIG43,(ROOT/'BGX45/M_BX43.lua').read_bytes())
        fbytes(self.root/mod.ORIG44,(ROOT/'BGX45/M_BX44.lua').read_bytes())
        fbytes(self.root/'lang/ru_RU/dialog.tlk',b'TLK test')
        fbytes(self.root/'WeiDU.log',b'~BGX42/setup-BGX42.tp2~ #0 #0\n~BGX43/setup-BGX43.tp2~ #0 #0\n~BGX44/setup-BGX44.tp2~ #0 #0\n')
        self.original=dict(mod.BASE)
        mod.BASE[mod.BCS]=mod.digest(self.root/mod.BCS)
        self.addCleanup(lambda:mod.BASE.update(self.original))
        self.manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
        self.verify_patch=patch.object(mod,'verify_sources',return_value=self.manifest)
        self.verify_patch.start();self.addCleanup(self.verify_patch.stop)

    def runner(self,cmd,**kwargs):
        uninstall='--force-uninstall' in cmd
        if uninstall:
            for src,dest in mod.NEW_LUA.items():
                (self.root/dest).unlink()
            lines=(self.root/'WeiDU.log').read_text().splitlines()
            (self.root/'WeiDU.log').write_text('\n'.join(x for x in lines if 'BGX45' not in x)+'\n')
        else:
            for src,dest in mod.NEW_LUA.items():
                fbytes(self.root/dest,(self.root/mod.MOD/Path(src).name).read_bytes())
            with (self.root/'WeiDU.log').open('a') as f:
                f.write('~BGX45/setup-BGX45.tp2~ #0 #0\n')
        return type('Result',(),{'returncode':0,'stdout':'mock weidu','stderr':''})()

    def install(self):
        return mod.install_045(self.root,ROOT,runner=self.runner,guard=lambda:None,
                              enforce_root=False,base=self.backups)

    def test_preflight_reads_real_install_state(self):
        info=mod.preflight(self.root,enforce_root=False)
        self.assertEqual(info['game'],str(self.root))

    def test_reject_corrupt_bcs(self):
        (self.root/mod.BCS).write_bytes(b'bad')
        with self.assertRaisesRegex(RuntimeError,'SHA mismatch|Missing or unsafe'):
            mod.preflight(self.root,enforce_root=False)

    def test_reject_out_of_order(self):
        with (self.root/'WeiDU.log').open('a') as f:f.write('~BGX99/setup-BGX99.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'LAST'):
            mod.preflight(self.root,enforce_root=False)

    def test_reject_short_file_collision(self):
        fbytes(self.root/'override/M_BX43.lua',b'collision')
        with self.assertRaisesRegex(RuntimeError,'collision'):
            mod.preflight(self.root,enforce_root=False)

    def test_install_rollback_roundtrip(self):
        pre=mod.digest(self.root/mod.BCS)
        result=self.install()
        self.assertEqual(result['status'],'INSTALLED_PASSIVE_045')
        self.assertTrue(all(result['checks'].values()))
        for src,dst in mod.NEW_LUA.items():
            self.assertEqual(mod.digest(self.root/dst),mod.digest(ROOT/src))
        self.assertEqual(mod.digest(self.root/mod.BCS),pre)
        backup=mod.verified_original_backup(self.root,base=self.backups)
        self.assertTrue((backup/'before.json').is_file())
        out=mod.rollback_045(self.root,ROOT,runner=self.runner,guard=lambda:None,
                             enforce_root=False,base=self.backups)
        self.assertEqual(out['status'],'UNINSTALLED_PASSIVE_045')
        self.assertTrue(all(out['checks'].values()))
        for dst in mod.NEW_LUA.values():self.assertFalse((self.root/dst).exists())
        self.assertEqual(mod.digest(self.root/mod.BCS),pre)

    def test_rollback_tamper_rejected(self):
        self.install()
        fbytes(self.root/'override/M_BX44.lua',b'modified'+b'x'*200)
        with self.assertRaisesRegex(RuntimeError,'changed'):
            mod.rollback_045(self.root,ROOT,runner=self.runner,guard=lambda:None,
                             enforce_root=False,base=self.backups)

    def test_rollback_not_last_rejected(self):
        self.install()
        with (self.root/'WeiDU.log').open('a') as f:f.write('~BGX99/setup-BGX99.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'LAST'):
            mod.rollback_045(self.root,ROOT,runner=self.runner,guard=lambda:None,
                             enforce_root=False,base=self.backups)


if __name__=='__main__':unittest.main()
