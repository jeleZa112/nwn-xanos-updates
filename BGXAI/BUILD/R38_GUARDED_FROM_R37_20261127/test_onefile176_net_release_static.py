"""Guard the exact 3-byte-group BGXAI one-updater release, no game or network actions."""
import hashlib
from pathlib import Path
import unittest

PS=Path("BGXAI/BGXAI_SYNC.ps1")
STAGE=Path("BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/STAGED_BGXAI_SYNC_176_NET_HOTFIX.ps1")
CHILD=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py")
def sha(b):return hashlib.sha256(b).hexdigest()
class Release(unittest.TestCase):
 def test_01_three_and_only_three_ps_edits(self):
  old=PS.read_bytes()
  pairs=[
   (b"$b.Length -ne 16827",b"$b.Length -ne 19784"),
   (b"c2fbefb877782047e2987b60fc517f1de11daec32da376893713b58e1fcbffcf",
    b"c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c"),
   (b"wh '175 inert | 176 V3 RO | 0 Exit'",
    b"wh '175 inert | 176 R38 | 0 Exit'"),
  ]
  for a,b in pairs:
   self.assertEqual(old.count(a),1)
   old=old.replace(a,b)
  self.assertEqual(old,STAGE.read_bytes())
 def test_02_new_source_pin(self):
  b=CHILD.read_bytes()
  self.assertEqual(len(b),19784)
  self.assertEqual(sha(b),"c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c")
  self.assertIn(sha(b),STAGE.read_text())
 def test_03_power_shell_limit_and_no_game_actions(self):
  b=STAGE.read_bytes()
  self.assertLessEqual(len(b),80000)
  self.assertTrue(b.isascii())
  self.assertNotIn(b"XEquipItem(",b)
  self.assertNotIn(b"SetGlobal(",b)
  self.assertNotIn(b"ClearActions(",b)
 def test_04_previous_entrypoints_preserved(self):
  b=STAGE.read_text()
  self.assertIn("'174' {",b)
  self.assertIn("{$_ -match '^17[56]$'}",b)
  self.assertIn("if($choice -eq '176'){$extra=@('--v3')}",b)
  self.assertNotIn("'177' {",b)
 def test_05_cancel_by_default_and_persistent_cache_present(self):
  s=CHILD.read_text()
  self.assertIn('if choice in ("", "0"): return "cancel"',s)
  self.assertIn('choice=input("R38 choice [0]: ").strip()',s)
  self.assertIn("VERIFIED_SOURCES_R38",s)
  self.assertIn("verify_file(path,raw)",s)
if __name__=="__main__":unittest.main(verbosity=2)
