"""R47 source-only one-shot bounded game log capture parser, mock files only."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('r47_parser',HERE/'BGXAI_R47_WITNESS_LAST157_TO158_GUARDED_SOURCE_ONLY.py')
P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)
ROW=(b"INFO: LUA: [BGXBEX] R46_BDDEFAI_CLASS_TRIGGER_EVALUATED_JAGAN_READONLY "
     b"scrlev=4 class=BDDEFAI partyIndex=1 witnessBlockEvaluated=true "
     b"actionOriginVerified=false ordersSent=0 armAuthorized=false\n")

class ExactParse(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.f=Path(self.tmp.name)/"jagan.log"
 def parse(self,data,exitcode=0):
  self.f.write_bytes(data)
  return P.parse_witness_console(self.f,exitcode)

 def test_01_one_valid_witness_real_format(self):
  out=self.parse(b"INFO: APP START\n"+ROW+b"INFO: END\n")
  self.assertEqual(out["status"],"R47_LIVE_BDDEFAI_WITNESS_TRIGGER_EVALUATED_NO_ARM")
  self.assertEqual(out["observedWitnessRows"],1)
  self.assertTrue(out["actualBcsWitnessBlockEvaluated"])
  self.assertFalse(out["actualBcsActionExecutionVerified"])
  self.assertFalse(out["manualEpsActionOriginVerified"])
  self.assertEqual(out["ordersSent"],0)

 def test_02_empty_game_log_fail_closed(self):
  out=self.parse(b"BGXAI normal\n")
  self.assertEqual(out["status"],"R47_CAPTURE_HOLD_WITNESS_NOT_OBSERVED")
  self.assertTrue(out["noAutoRetry"])

 def test_03_duplicate_logs_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_AMBIGUOUS_OR_UNTRUSTED"):
   self.parse(ROW+ROW)

 def test_04_wrong_actor_slot_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_AMBIGUOUS_OR_UNTRUSTED"):
   self.parse(ROW.replace(b"partyIndex=1",b"partyIndex=2"))

 def test_05_wrong_script_resref_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_AMBIGUOUS_OR_UNTRUSTED"):
   self.parse(ROW.replace(b"class=BDDEFAI",b"class=DPLAYER"))

 def test_06_nonzero_orders_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_AMBIGUOUS_OR_UNTRUSTED"):
   self.parse(ROW.replace(b"ordersSent=0",b"ordersSent=1"))

 def test_07_impossible_arm_claim_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_AMBIGUOUS_OR_UNTRUSTED"):
   self.parse(ROW.replace(b"armAuthorized=false",b"armAuthorized=true"))

 def test_08_oversized_log_line_fail_closed(self):
  with self.assertRaisesRegex(ValueError,"HOLD_R47_WITNESS_LINE_OVERSIZE"):
   self.parse(ROW.strip()+b"X"*9000+b"\n")

 def test_09_log_symlink_is_rejected(self):
  target=Path(self.tmp.name)/"somewhere"
  target.write_bytes(ROW)
  self.f.symlink_to(target)
  with self.assertRaisesRegex(ValueError,"HOLD_R47_RAW_CONSOLE_FILE_INVALID"):
   P.parse_witness_console(self.f,0)

 def test_10_no_unrelated_UI_output_claims_BCS_exec(self):
  out=self.parse(b"INFO [BG_EET_RU_V106] LISTENER_REGISTERED\n")
  self.assertFalse(out["actualBcsWitnessBlockEvaluated"])

 def test_11_game_exit_code_is_separate_from_witness_evidence(self):
  out=self.parse(ROW,exitcode=1)
  self.assertEqual(out["gameExitCode"],1)
  self.assertTrue(out["actualBcsWitnessBlockEvaluated"])
  self.assertFalse(out["actualBcsActionExecutionVerified"])

 def test_12_log_source_has_no_game_mutation_api(self):
  src=(HERE/"BGXAI_R47_WITNESS_LAST157_TO158_GUARDED_SOURCE_ONLY.py").read_text()
  self.assertNotIn("XEquipItem(",src)
  self.assertNotIn("BGXW3ARM",src)
  self.assertIn("noAutoRetry",src)

if __name__=="__main__":
 unittest.main()
