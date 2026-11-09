"""No real EET modification: mock WeiDU + order/security/baseline tests."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('BGXAI47',ROOT/'BGXAI47_INSTALL.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def put(p:Path,data:bytes):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

class SourceChecks(unittest.TestCase):
    def test_source_manifest(self):
        self.assertEqual(mod.verify_sources(ROOT)['version'],mod.VERSION)
    def test_only_one_override_destination(self):
        self.assertEqual(mod.DEST,'override/M_BX43.lua')
        self.assertNotIn('BDDEFAI', (ROOT/mod.TP2).read_text())
    def test_regex_positive_and_negative(self):
        for sep in ('/','\\'):
            self.assertTrue(mod.RE['46'].search('~BGX46'+sep+'SETUP-BGX46.TP2~ #0 #0 // 046'))
            self.assertTrue(mod.RE['47'].search('~BGX47'+sep+'SETUP-BGX47.TP2~ #0 #0 // 047'))
        self.assertFalse(mod.RE['46'].search('~BGX99\\SETUP-BGX46.TP2~ #0 #0'))
        self.assertFalse(mod.RE['46'].search('~BGX46\\SETUP-BGX46.TP2.FAKE~ #0 #0'))
    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError,'Unsafe'):mod.safe(Path(tmp),'../escape')
    def test_corrupt_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for f in (*mod.FILES,'SOURCE_MANIFEST.json'):
                dest=p/f;dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/f,dest)
            (p/mod.SRC).write_text('broken')
            with self.assertRaisesRegex(RuntimeError,'checksum'):mod.verify_sources(p)

class FakeGame(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name)/'game';self.root.mkdir()
        self.backups=Path(t.name)/'backups'
        put(self.root/'chitin.key',b'k'*1200)
        put(self.root/'InfinityLoader.exe',b'MZ'+b'Z'*12000)
        put(self.root/mod.WEIDU,b'MZ'+b'X'*120000)
        put(self.root/'WeiDU.log',b'~BGX42\\SETUP-BGX42.TP2~ #0 #0\n~BGX43\\SETUP-BGX43.TP2~ #0 #0\n~BGX44\\SETUP-BGX44.TP2~ #0 #0\n~BGX45\\SETUP-BGX45.TP2~ #0 #0\n~BGX46\\SETUP-BGX46.TP2~ #0 #0\n')
        for f in (*mod.BOOTS,*mod.BASE):put(self.root/f,('baseline '+f).encode()*12)
        put(self.root/mod.DEST,b'old'*100)
        self.old=dict(mod.BASE)
        self.old_sha=mod.OLD
        mod.BASE.update({name:mod.digest(self.root/name) for name in mod.BASE})
        mod.OLD=mod.digest(self.root/mod.DEST)
        self.addCleanup(lambda:mod.BASE.clear() or mod.BASE.update(self.old))
        self.addCleanup(lambda:setattr(mod,'OLD',self.old_sha))
        self.source_manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
        self.mock_verify=patch.object(mod,'verify_sources',return_value=self.source_manifest)
        self.mock_verify.start();self.addCleanup(self.mock_verify.stop)

    def runner(self,cmd,**kw):
        log=self.root/'WeiDU.log'
        if '--force-uninstall' in cmd:
            (self.root/mod.DEST).write_bytes(b'old'*100)
            log.write_text('\n'.join(x for x in log.read_text().splitlines() if not mod.RE['47'].search(x))+'\n')
        else:
            shutil.copy2(self.root/mod.MOD/'M_BX43.lua',self.root/mod.DEST)
            with log.open('a') as f:f.write('~BGX47\\SETUP-BGX47.TP2~ #0 #0 // PASS\n')
        return types.SimpleNamespace(returncode=0,stdout='WeiDU simulated',stderr='')

    def test_preflight_baseline(self):
        p=mod.preflight(self.root,enforce=False)
        self.assertEqual(p['root'],str(self.root))
        with self.assertRaisesRegex(RuntimeError,'Expected BGX47'):
            mod.preflight(self.root,install=False,enforce=False)

    def test_mock_install_rollback(self):
        r=mod.install(self.root,ROOT,runner=self.runner,guard=lambda:None,base=self.backups,enforce=False)
        self.assertEqual(r['status'],'INSTALLED_PASSIVE_047',r)
        self.assertEqual(mod.digest(self.root/mod.DEST),mod.digest(ROOT/mod.SRC))
        s=mod.uninstall(self.root,ROOT,runner=self.runner,guard=lambda:None,base=self.backups,enforce=False)
        self.assertEqual(s['status'],'UNINSTALLED_PASSIVE_047',s)
        self.assertEqual(mod.digest(self.root/mod.DEST),mod.OLD)

    def test_blocked_if_not_last(self):
        with (self.root/'WeiDU.log').open('a') as f:f.write('~OTHER\\SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'LAST'):mod.preflight(self.root,enforce=False)

if __name__=='__main__':unittest.main()
