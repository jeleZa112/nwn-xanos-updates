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
 def test_detect_internal_lua_without_io(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/"InfinityLoader.ini").write_text("[General]\nLuaPatchMode=INTERNAL\nLogFile=InfinityLoader.txt\n",encoding="utf-8")
   (root/"override").mkdir()
   (root/"override/M_BXFR.lua").write_bytes(b"test")
   (root/"InfinityLoader.txt").write_text("Lua script M_BXFR.lua: io.open not available\n",encoding="utf-8")
   r=M.audit(root)
   diag=r["startup_diagnostics"]
   self.assertEqual(diag["lua_patch_mode"],"INTERNAL")
   self.assertEqual(diag["lua_io_available"],"LIKELY_UNAVAILABLE_IN_INTERNAL_LUA")
   self.assertTrue(diag["observer_override_present"])
   self.assertEqual(len(diag["startup_logs"]),1)
   self.assertIn("io.open",diag["startup_logs"][0]["relevant_lines"][0])
   self.assertEqual(r["status"],"TRACE_NOT_PRESENT")
 def test_missing_ini_never_infers_no_io(self):
  with tempfile.TemporaryDirectory() as d:
   r=M.audit(Path(d))
   self.assertEqual(r["startup_diagnostics"]["lua_io_available"],"UNKNOWN")
   self.assertFalse(r["startup_diagnostics"]["observer_override_present"])
 def test_disabled_ini_options_are_ignored(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/"InfinityLoader.ini").write_text(";LuaPatchMode=INTERNAL\n# LogFile=evil.txt\nLuaPatchMode=REPLACE_INTERNAL_WITH_EXTERNAL\n",encoding="utf-8")
   r=M.audit(root)
   self.assertEqual(r["startup_diagnostics"]["lua_patch_mode"],"REPLACE_INTERNAL_WITH_EXTERNAL")
   self.assertEqual(r["startup_diagnostics"]["lua_io_available"],"POSSIBLE_NEEDS_RUNTIME_VERIFICATION")
 def test_untrusted_logfile_relative_path_not_read(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   (root/"InfinityLoader.ini").write_text("LogFile=../../private.txt\n")
   r=M.audit(root)
   self.assertFalse(r["startup_diagnostics"]["startup_logs"])
if __name__=='__main__':unittest.main()
