"""R38 one-CMD release: exact two-token PowerShell delta, no old menu changes."""
from pathlib import Path
import hashlib
import re
import subprocess
import json
import unittest

OLD_COMMIT="58001197c959fac13d6d530cb8cc4d678e0e14ba"
STAGE=Path("BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/STAGED_BGXAI_SYNC_R38_FROM_176.ps1")
CHILD=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_176_R38_STAGE_ONLY.py")
NATIVE=Path("BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py")
R38_LUA=Path("BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua")
OLD_SHA="157d69466fdb5766822145299d64163190b5c9beb8849876b03c08f97f66c35f"
NEW_SHA="c2fbefb877782047e2987b60fc517f1de11daec32da376893713b58e1fcbffcf"

def sha(raw):return hashlib.sha256(raw).hexdigest()

class Release(unittest.TestCase):
 def test_01_shell_exact_two_changes(self):
  old=subprocess.check_output(["git","show",OLD_COMMIT+":BGXAI/BGXAI_SYNC.ps1"])
  new=STAGE.read_bytes()
  self.assertEqual(len(old),79998)
  self.assertEqual(len(new),79998)
  self.assertLessEqual(len(new),80000)
  self.assertEqual(old.count(b"$b.Length -ne 12783"),1)
  self.assertEqual(old.count(OLD_SHA.encode()),1)
  target=old.replace(b"$b.Length -ne 12783",b"$b.Length -ne 16827").replace(OLD_SHA.encode(),NEW_SHA.encode())
  self.assertEqual(new,target,"only child length and SHA permitted")
 def test_02_new_child_pinned_bytes(self):
  data=CHILD.read_bytes()
  self.assertEqual(len(data),16827)
  self.assertEqual(sha(data),NEW_SHA)
 def test_03_old_menus_unmodified(self):
  old=subprocess.check_output(["git","show",OLD_COMMIT+":BGXAI/BGXAI_SYNC.ps1"])
  new=STAGE.read_bytes()
  self.assertEqual(old.split(b"{$_ -match '^17[56]$'}")[0],new.split(b"{$_ -match '^17[56]$'}")[0])
 def test_04_no_new_updater(self):
  text=STAGE.read_text(encoding="ascii")
  self.assertIn("Get-PinnedBytes $p",text)
  self.assertIn("if($choice -eq '176'){$extra=@('--v3')}",text)
  self.assertNotIn("'177' {",text)
  self.assertNotIn("XEquipItem(",text)
  self.assertNotIn("SetGlobal(",text)
 def test_05_r38_pins(self):
  b=NATIVE.read_bytes()
  self.assertEqual(len(b),21303)
  self.assertEqual(sha(b),"f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c")
  self.assertEqual(len(R38_LUA.read_bytes()),78927)
  self.assertEqual(sha(R38_LUA.read_bytes()),"958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c")
 def test_06_production_pin_when_live(self):
  current=Path("BGXAI/BGXAI_SYNC.ps1").read_bytes()
  pin=json.loads(Path("BGXAI/fox_new/BOOTSTRAP_PIN.json").read_text())
  if current!=STAGE.read_bytes():
   self.assertEqual(pin["script_sha256"],sha(current))
   return
  self.assertEqual(pin["script_sha256"],sha(current))
  self.assertEqual(pin["script_size"],len(current))
  pinned=subprocess.check_output(["git","show",pin["commit"]+":"+pin["script_path"]])
  self.assertEqual(current,pinned)

if __name__=="__main__":unittest.main(verbosity=2)
