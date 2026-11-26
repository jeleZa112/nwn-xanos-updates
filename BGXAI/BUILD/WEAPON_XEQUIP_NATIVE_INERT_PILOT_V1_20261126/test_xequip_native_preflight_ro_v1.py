import importlib.util
from pathlib import Path
import unittest
import tempfile
import json
from unittest.mock import patch

S=Path("BGXAI/BUILD/WEAPON_XEQUIP_NATIVE_INERT_PILOT_V1_20261126")
spec=importlib.util.spec_from_file_location("native_probe",S/"BGXAI_XEQUIP_NATIVE_PREFLIGHT_RO_V1.py")
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)

class TestNativeSourceReadOnly(unittest.TestCase):
 def test_verified_backend_pinned(self):
  b=pilot.verify_backend()
  self.assertEqual(b.TEMP_SOURCE_NAME,"BGXW3CHK.baf")
 def test_source_only_without_game(self):
  m=S/"EXAMPLE_ONLY_NOT_USER_EET.json"
  r=pilot.source_only(m)
  self.assertEqual(r["status"],"INERT_SOURCE_READY_NO_NATIVE_COMPILE")
  self.assertFalse(r["nativeSymbolsAcceptedByCompiler"])
  self.assertFalse(r["installed"])
  self.assertFalse(r["inventoryMoveAuthorized"])
  self.assertEqual(len(r["bafSha256"]),64)
 def test_source_manifest_no_game_file(self):
  b,m=pilot.generate(S/"EXAMPLE_ONLY_NOT_USER_EET.json")
  self.assertIn("False()\n  InParty(Myself)",b)
  self.assertIn("SLOT_MISC3",b)
  self.assertIn("SLOT_WEAPON1",b)
  self.assertNotIn("FillSlot(",b)
 def test_no_external_arbitrary_script(self):
  with tempfile.TemporaryDirectory() as p:
   q=Path(p)/"pilot.json"
   q.write_text(json.dumps({"schema":"something"}))
   with self.assertRaises(ValueError):pilot.generate(q)
 def test_refuse_manifest_symlink(self):
  with tempfile.TemporaryDirectory() as p:
   q=Path(p)/"missing"
   with self.assertRaises(ValueError):pilot.generate(q)
 def test_compiler_rejects_unrecognized_fake_binary(self):
  with tempfile.TemporaryDirectory() as p:
   game=Path(p)
   (game/"weidu.exe").write_bytes(b"not a pinned compiler")
   with self.assertRaises(pilot.Hold):pilot.compiler_path(game)
 def test_native_refused_non_windows(self):
  if pilot.os.name!="nt":
   with self.assertRaises(pilot.Hold):pilot.close_game_proof()
 def test_gate_not_invoked_in_default(self):
  with patch.object(pilot,"native_readonly",side_effect=AssertionError("called")):
   r=pilot.source_only(S/"EXAMPLE_ONLY_NOT_USER_EET.json")
  self.assertEqual(r["ordersSent"],0)
 def test_readonly_backend_no_game_install_functions(self):
  source=Path(pilot.backend_path()).read_text()
  self.assertIn("tempfile.TemporaryDirectory(",source)
  self.assertIn("watchedFilesChanged",source)
  self.assertNotIn("INSTALL_BGX",source)

if __name__=="__main__":unittest.main(verbosity=2)
