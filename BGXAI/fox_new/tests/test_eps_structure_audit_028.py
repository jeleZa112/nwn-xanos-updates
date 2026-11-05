import hashlib
import json
import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from eps_structure_audit_028 import audit

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'NEW'; self.root.mkdir()
        (self.root/'chitin.key').write_text('fake')
        self.snap=self.root/'BGXAI_LOCAL_BUILD'/'EPS_BASELINE_TEST'; self.snap.mkdir(parents=True)
        self.src=self.snap/'EPS_ORIGINAL_TEXTS_PRIVATE'; self.src.mkdir()
        files=[]
        for name,content in [('enhanced-powergaming-scripts.tp2','VERSION ~v18.4~'),('baf/mocore.baf','IF\nTrue()'),('languages/russian/setup.tra','@1 = ~пример~')]:
            p=self.src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
            data=p.read_bytes();files.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        self.m={'schema':27,'public_upload_allowed':False,'source_files':files,'weidu_eps_components':2,'binary_bcs_info':{'present_in_override':True}}
        self.write()
    def write(self): (self.snap/'LOCAL_MANIFEST.json').write_text(json.dumps(self.m))
    def call(self): return audit(self.snap,self.root,strict_root=False)
    def test_index(self):
        x=self.call();self.assertEqual(x['file_count'],3);self.assertEqual(x['extension_counts']['.baf'],1)
        self.assertEqual(x['installed_eps_components'],2);self.assertFalse(x['suitable_for_installation'])
    def test_no_source_text_disclosed(self): self.assertNotIn('VERSION ~v18.4~',json.dumps(self.call()))
    def test_game_unchanged(self): self.assertFalse(self.call()['game_modified'])
    def test_wrong_snapshot_path(self):
        with self.assertRaises(ValueError): audit(Path(self.tmp.name),self.root,strict_root=False)
    def test_checksum_change(self):
        (self.src/'baf/mocore.baf').write_text('changed')
        with self.assertRaises(ValueError): self.call()
    def test_traversal(self):
        self.m['source_files'][0]['path']='../outside';self.write()
        with self.assertRaises(ValueError): self.call()
    def test_bad_schema(self):
        self.m['schema']=26;self.write()
        with self.assertRaises(ValueError): self.call()
    def test_bad_privacy(self):
        self.m['public_upload_allowed']=True;self.write()
        with self.assertRaises(ValueError): self.call()
    def test_missing_game(self):
        (self.root/'chitin.key').unlink()
        with self.assertRaises(ValueError): self.call()
    def test_empty_files(self):
        self.m['source_files']=[];self.write()
        with self.assertRaises(ValueError): self.call()
    def test_missing_esp_file(self):
        (self.src/'baf/mocore.baf').unlink()
        with self.assertRaises(ValueError): self.call()
    def test_no_symlink(self):
        link=self.src/'languages/russian/setup.tra'
        link.unlink()
        try: link.symlink_to(self.src/'baf/mocore.baf')
        except (OSError,NotImplementedError): self.skipTest('platform does not support symlink')
        with self.assertRaises(ValueError): self.call()
if __name__=='__main__':unittest.main()