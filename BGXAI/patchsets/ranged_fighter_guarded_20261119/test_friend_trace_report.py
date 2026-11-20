import tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import BGX_FRIEND_TRACE_REPORT as M
class ReportTests(unittest.TestCase):
 def check(self,body):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/M.LOG_NAME;p.write_text(body,encoding="utf-8");r=M.audit(Path(d));self.assertEqual(p.read_text(encoding="utf-8"),body);return r
 def test_detect_exact_pair(self):
  raw="[BGXFTRACE] SESSION version=1 origin=UNKNOWN coverage=STARTED_PARTY_ATTACK_ACTIONS_ONLY\n[BGXFTRACE] READY hook=REGISTERED writer=FILE origin=UNKNOWN\n"+"[BGXFTRACE] ACTION seq=1 actor=102 slot=2 action=134 a1=-1 a2=101 target=101 target_slot=1 script=3 status=PARTY_TARGET_OBSERVED origin=UNKNOWN\n"
  r=self.check(raw);self.assertEqual(r['party_target_attack_records'],1);self.assertEqual(r['observed_party_target_pairs'][0]['script_index_observed'],3);self.assertEqual(r['runtime_origin'],'UNKNOWN')
 def test_no_provenance_from_script_index(self):
  raw="[BGXFTRACE] READY hook=REGISTERED writer=FILE origin=UNKNOWN\n[BGXFTRACE] ACTION seq=1 actor=102 slot=2 action=3 a1=-1 a2=-1 target=-1 target_slot=-1 script=4 status=TARGET_NOT_CONFIRMED_PARTY origin=UNKNOWN\n"
  r=self.check(raw);self.assertEqual(r['party_target_attack_records'],0);self.assertFalse(r['no_observation_means_safe'])
 def test_missing_file_nonfatal(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(M.audit(Path(d))['status'],'TRACE_NOT_PRESENT')
 def test_malformed_line_not_inferred(self):
  r=self.check("[BGXFTRACE] ACTION seq=2 actor=100 slot=2 action=3 target=101 target_slot=1 script=4\n")
  self.assertEqual(r['party_target_attack_records'],0)
if __name__=='__main__':unittest.main()
