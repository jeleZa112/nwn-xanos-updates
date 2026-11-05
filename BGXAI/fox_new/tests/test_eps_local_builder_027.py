"""Safe offline tests for BGXAI 027 local snapshot builder."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eps_local_builder_027 import create_local_snapshot

class TestLocalBuild(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name) / "BG_EET_FOXX_NEW"
        self.root.mkdir()
        (self.root / 'chitin.key').write_bytes(b'dummy')
        self.eps = self.root / "enhanced-powergaming-scripts"
        self.eps.mkdir()
        (self.eps / 'enhanced-powergaming-scripts.tp2').write_text('VERSION ~18.4~')
        (self.eps / 'baf').mkdir()
        (self.eps / 'baf' / 'example.baf').write_text('IF\nEND')
        (self.eps / 'backup').mkdir()
        (self.eps / 'backup' / 'restored.baf').write_text('NOT TO COPY')
        (self.root / 'override').mkdir()
        (self.root / 'override' / 'BDDEFAI.BCS').write_bytes(b'not a real bcs')
        (self.root / 'WeiDU.log').write_text('~ENHANCED-POWERGAMING-SCRIPTS.TP2~ #0 #1\n')
    def run_snapshot(self, **kw):
        return create_local_snapshot(self.root, expected_root=self.root, stamp='unit_test', **kw)
    def test_snapshot_is_private_and_no_game_modification(self):
        original = (self.eps / 'baf' / 'example.baf').read_bytes()
        bcs = (self.root / 'override' / 'BDDEFAI.BCS').read_bytes()
        report = self.run_snapshot()
        snapshot = Path(report['snapshot'])
        self.assertTrue((snapshot / 'EPS_ORIGINAL_TEXTS_PRIVATE/baf/example.baf').exists())
        self.assertEqual(report['source_file_count'], 2)
        self.assertEqual(report['weidu_eps_components'], 1)
        self.assertFalse(report['game_modified'])
        self.assertFalse(report['public_upload_allowed'])
        self.assertEqual((self.eps / 'baf/example.baf').read_bytes(), original)
        self.assertEqual((self.root / 'override/BDDEFAI.BCS').read_bytes(), bcs)
        self.assertTrue(json.loads((snapshot/'LOCAL_MANIFEST.json').read_text())['source_files'])
    def test_refuses_wrong_game(self):
        with self.assertRaisesRegex(RuntimeError, 'Wrong game directory'):
            create_local_snapshot(self.root, expected_root=self.root/'wrong')
    def test_no_duplicate_overwrite(self):
        self.run_snapshot()
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            self.run_snapshot()
    def test_no_game_key(self):
        (self.root / 'chitin.key').unlink()
        with self.assertRaisesRegex(RuntimeError, 'chitin.key'):
            self.run_snapshot()
    def test_no_tp2(self):
        (self.eps / 'enhanced-powergaming-scripts.tp2').unlink()
        with self.assertRaisesRegex(RuntimeError, 'tp2'):
            self.run_snapshot()
    def test_symlink_not_followed(self):
        try:
            (self.eps / 'baf' / 'outside.txt').symlink_to(Path(self.work.name) / 'missing')
        except (OSError, NotImplementedError):
            self.skipTest('symlink disabled')
        r = self.run_snapshot()
        names=[x['path'] for x in r['source_files']]
        self.assertNotIn('baf/outside.txt',names)
    def test_text_only(self):
        (self.eps / 'baf' / 'binary.exe').write_bytes(b'test')
        r=self.run_snapshot()
        self.assertNotIn('baf/binary.exe',[x['path'] for x in r['source_files']])
if __name__=='__main__':unittest.main(verbosity=2)