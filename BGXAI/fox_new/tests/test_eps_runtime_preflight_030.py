"""Regression coverage for BGXAI 030 with fake miniature EET file trees."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from eps_runtime_preflight_030 import validate, confined, hashfile


class Preflight(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'chitin.key').write_bytes(b'fake')
        (self.root/'WeiDU.log').write_text('~ENHANCED-POWERGAMING-SCRIPTS/SETUP.TP2~ #0 #0 // EPS\n')
        self.eps = self.root/'enhanced-powergaming-scripts'
        self.eps.mkdir()
        (self.eps/'main.tp2').write_bytes(b'TP2 example only')
        self.snap = self.root/'BGXAI_LOCAL_BUILD'/'EPS_BASELINE_TEST'
        self.snap.mkdir(parents=True)
        self.copied = self.snap/'EPS_ORIGINAL_TEXTS_PRIVATE'
        self.copied.mkdir()
        (self.copied/'main.tp2').write_bytes(b'TP2 example only')
        (self.root/'override').mkdir()
        (self.root/'override'/'BDDEFAI.BCS').write_bytes(b'fake compiled resource')
        manifest={'schema':27,'public_upload_allowed':False,'game_modified':False,
                  'weidu_eps_components':1,'binary_bcs_info':{
                      'present_in_override':True,'sha256':hashfile(self.root/'override'/'BDDEFAI.BCS')},
                  'source_files':[{'path':'main.tp2','bytes':len(b'TP2 example only'),
                      'sha256':hashfile(self.eps/'main.tp2')}]}
        (self.snap/'LOCAL_MANIFEST.json').write_text(json.dumps(manifest))
        report={'schema':28,'mode':'METADATA_ONLY','game_modified':False,'uploaded':False,
                'snapshot_id':'EPS_BASELINE_TEST','file_count':1,'source_bytes':len(b'TP2 example only')}
        (self.root/'BGXAI_LOCAL_BUILD'/'BGXAI_028_EPS_STRUCTURE_REPORT.json').write_text(json.dumps(report))

    def runcheck(self):return validate(self.root,enforce_root=False)
    def test_ready_is_not_approved_for_live(self):
        a=self.runcheck()
        self.assertEqual(a['status'],'READY_FOR_ISOLATED_COMPILATION_REVIEW')
        self.assertFalse(a['weiDU_compilation_verified'])
        self.assertFalse(a['live_install_allowed'])
        self.assertFalse(a['game_modified'])
    def test_changed_source_blocked(self):
        (self.eps/'main.tp2').write_text('tampered')
        x=self.runcheck()
        self.assertEqual(x['status'],'BLOCKED_REVIEW');self.assertEqual(x['changed_file_count'],1)
    def test_changed_snapshot_blocked(self):
        (self.copied/'main.tp2').write_text('different')
        self.assertEqual(self.runcheck()['status'],'BLOCKED_REVIEW')
    def test_changed_bcs_blocked(self):
        (self.root/'override'/'BDDEFAI.BCS').write_bytes(b'changed')
        self.assertEqual(self.runcheck()['bddefai_override_state'],'CHANGED_SINCE_SNAPSHOT')
    def test_no_bcs_override_not_proof(self):
        (self.root/'override'/'BDDEFAI.BCS').unlink()
        self.assertEqual(self.runcheck()['status'],'BLOCKED_REVIEW')
    def test_weidu_changed_blocked(self):
        (self.root/'WeiDU.log').write_text('// nothing\n')
        self.assertEqual(self.runcheck()['status'],'BLOCKED_REVIEW')
    def test_no_game_key_fails(self):
        (self.root/'chitin.key').unlink()
        with self.assertRaisesRegex(ValueError,'chitin'): self.runcheck()
    def test_report_028_tampered_fails(self):
        p=self.root/'BGXAI_LOCAL_BUILD'/'BGXAI_028_EPS_STRUCTURE_REPORT.json'
        x=json.loads(p.read_text());x['uploaded']=True;p.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,'028'): self.runcheck()
    def test_wrong_snapshot_id_fails(self):
        p=self.root/'BGXAI_LOCAL_BUILD'/'BGXAI_028_EPS_STRUCTURE_REPORT.json'
        x=json.loads(p.read_text());x['snapshot_id']='../../other';p.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,'Snapshot name'):self.runcheck()
    def test_reject_bad_paths(self):
        self.assertIsNone(confined(self.eps,'../Windows/system32'))
        self.assertIsNone(confined(self.eps,'foo\\evil'))
        self.assertIsNone(confined(self.eps,'C:/Windows'))
    def test_broken_inventory_metadata_fails(self):
        p=self.snap/'LOCAL_MANIFEST.json';x=json.loads(p.read_text());x['source_files'][0]['sha256']='NO';p.write_text(json.dumps(x))
        with self.assertRaisesRegex(ValueError,'Bad source'):self.runcheck()
    def test_missing_weidu_fails(self):
        (self.root/'WeiDU.log').unlink()
        with self.assertRaisesRegex(ValueError,'WeiDU'):self.runcheck()
    def test_unknown_eps_file_no_path_traversal(self):
        p=self.snap/'LOCAL_MANIFEST.json';x=json.loads(p.read_text());x['source_files'][0]['path']='../main.tp2';p.write_text(json.dumps(x))
        self.assertEqual(self.runcheck()['status'],'BLOCKED_REVIEW')

if __name__=='__main__':unittest.main(verbosity=2)