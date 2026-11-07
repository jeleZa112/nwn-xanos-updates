import hashlib, json, os, struct, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import BGXAI41_INSTALL as m


def fake_tlk(count=120):
    out=bytearray(18)
    out[:8]=b'TLK V1  '
    struct.pack_into('<I',out,10,count)
    return bytes(out)


def fixture(root,pkg):
    # Test fixture is synthetic; does not try to simulate real EET engine.
    for rel,body in [
        ('chitin.key',b'Chitin-TEST'),('override/BDDEFAI.BCS',b'BCS-Test'),
        ('lang/ru_RU/dialog.tlk',fake_tlk()),('lang/ru_RU/dialogf.tlk',fake_tlk()),
        ('WeiDU.log',b'~ENHANCED-POWERGAMING-SCRIPTS/SETUP.TP2~ #0 #0 // installed\n~BGX40/SETUP-BGX40.TP2~ #0 #0 // installed\n'),
        (m.WEIDU,b'MZ'+b'Z'*100500)]:
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    # The SOURCE_MANIFEST contains own prebuilt sources and the Python helper.
    # Files copied from source package are trusted ONLY for in-memory test fixture.
    for rel in m.OWNED_SOURCE:
        src=ROOT/rel;dst=pkg/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(src.read_bytes())
    # also copy all checked payloads
    src_m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text('utf-8'))
    for rel in src_m['files']:
        dst=pkg/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes((ROOT/rel).read_bytes())
    (pkg/'SOURCE_MANIFEST.json').write_bytes((ROOT/'SOURCE_MANIFEST.json').read_bytes())


class Installer041(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();t=Path(self.tmp.name)
    self.root=t/'GAME';self.pkg=t/'PKG';self.root.mkdir();self.pkg.mkdir()
    fixture(self.root,self.pkg)
    self.patcher=mock.patch.dict(os.environ,{'USERPROFILE':str(t/'PROFILE')})
    self.patcher.start()
 def tearDown(self):self.patcher.stop();self.tmp.cleanup()
 def test_preflight_readonly(self):
    before={str(f.relative_to(self.root)):m.sha(f) for f in self.root.rglob('*') if f.is_file()}
    meta,log=m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
    self.assertIn('override/BDDEFAI.BCS',meta)
    self.assertTrue(m.is_last(log,m.BASE_RE))
    after={str(f.relative_to(self.root)):m.sha(f) for f in self.root.rglob('*') if f.is_file()}
    self.assertEqual(before,after)
 def test_missing_source_fails(self):
    (self.pkg/'BGX41/icon.tra').write_text('tampered')
    with self.assertRaisesRegex(RuntimeError,'Source checksum mismatch'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_missing_040_blocks(self):
    p=self.root/'WeiDU.log';p.write_text('~ENHANCED-POWERGAMING-SCRIPTS~ #0 #0\n')
    with self.assertRaisesRegex(RuntimeError,'BGX40 missing'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_intervening_mod_blocks(self):
    with (self.root/'WeiDU.log').open('a') as f:f.write('~MORE/MOD.TP2~ #0 #0\n')
    with self.assertRaisesRegex(RuntimeError,'not last'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_override_collision_blocks(self):
    (self.root/'override/BGX41ON.SPL').write_bytes(b'collision')
    with self.assertRaisesRegex(RuntimeError,'resource name already'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_reparse_source_blocks(self):
    p=self.pkg/'BGX41/toggle_icon.baf';p.unlink();p.symlink_to(ROOT/'BGX41/toggle_icon.baf')
    with self.assertRaisesRegex(RuntimeError,'redirected'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_not_a_pe_weidu_blocks(self):
    p=self.root/m.WEIDU;p.write_bytes(b'bad'+b'x'*100500)
    with self.assertRaisesRegex(RuntimeError,'Wrong WeiDU'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_simulated_install_success(self):
    def mockweidu(root,*,uninstall=False,runner=None):
        self.assertFalse(uninstall)
        (root/'override/BDDEFAI.BCS').write_bytes(b'BCS-Test-041')
        (root/'override/STATDESC.2DA').write_text('2DA V1.0\n0\nDESCRIPTION BAM_FILE\n0 1 ****\n1 101 BGX41IC\n')
        for x in m.OWNED_OVERRIDE:(root/'override'/x).write_bytes((self.pkg/'BGX41'/x).read_bytes())
        for rel in m.BASE[-2:]:
            p=root/rel;p.write_bytes(fake_tlk(122))
        with (root/'WeiDU.log').open('a') as f:f.write('~BGX41/SETUP-BGX41.TP2~ #0 #0 // installed\n')
        return subprocess_completed(0,'SUCCESSFULLY INSTALLED')
    with mock.patch.object(m,'run_weidu',side_effect=mockweidu):
        r=m.install(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
    self.assertEqual(r['status'],'INSTALLED')
    self.assertTrue(all(r['checks'].values()))
    self.assertTrue((Path(r['backup'])/'status.json').is_file())
    self.assertTrue((Path(r['backup'])/'override/BDDEFAI.BCS').is_file())
 def test_weidu_failure_keeps_report(self):
    with mock.patch.object(m,'run_weidu',return_value=subprocess_completed(1,'WeiDU compile error')):
        r=m.install(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
    self.assertEqual(r['status'],'REVIEW_INSTALL')
    self.assertTrue((Path(r['backup'])/'report.json').is_file())
    self.assertEqual((self.root/'override/BDDEFAI.BCS').read_bytes(),b'BCS-Test')
 def test_existing_041_blocks_duplicate(self):
    with (self.root/'WeiDU.log').open('a') as f:f.write('~BGX41/SETUP-BGX41.TP2~ #0 #0\n')
    with self.assertRaisesRegex(RuntimeError,'already installed'):
        m.preflight(self.root,self.pkg,strict_game=False,process_guard=lambda:None)
 def test_own_binary_is_limited(self):
    self.assertEqual(len(m.OWNED_OVERRIDE),3)
    self.assertFalse(any(x in m.OWNED_OVERRIDE for x in ('BDDEFAI.BCS','STATDESC.2DA')))
 def test_pinning_from_manifest(self):
    f=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text('utf-8'))['files']
    for rel,meta in f.items():
        p=ROOT/rel
        self.assertEqual(p.stat().st_size,meta['size'])
        self.assertEqual(m.sha(p),meta['sha256'])


def subprocess_completed(code,output):
    from types import SimpleNamespace
    return SimpleNamespace(returncode=code,stdout=output,stderr='')

if __name__=='__main__':unittest.main()
