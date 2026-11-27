"""Validate shipped BGXAI one-file menu176 bootstrap against immutable Git commit."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

PIN=Path("BGXAI/fox_new/BOOTSTRAP_PIN.json")
SCRIPT=Path("BGXAI/BGXAI_SYNC.ps1")
STAGE=Path("BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/STAGED_BGXAI_SYNC_176_NET_HOTFIX.ps1")
WRAPPER=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py")
STAGED_WRAPPER=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_ONEFILE176_NET_AND_DEFAULT_HOTFIX_STAGE.py")
BASE_PS=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/STAGED_BGXAI_SYNC_MENU175.ps1")
OLD_BANNER="wh 'BGXAI ONE-FILE UPDATER: 1-174 existing | 175 XEquip native compile READ ONLY | 0 Exit'"
NEW_BANNER="wh '175 inert | 176 R38 | 0 Exit'"
OLD_HANDLER="'175' {$p="
NEW_HANDLER="{$_ -match '^17[56]$'} {$p="
def sha(data): return hashlib.sha256(data).hexdigest()
class Shipped(unittest.TestCase):
 def setUp(self):
  self.pin=json.loads(PIN.read_text(encoding="utf-8"))
  self.script=SCRIPT.read_bytes()
 def test_valid_bootstrap_schema_and_exact_sha(self):
  p=self.pin
  self.assertEqual(p["script_path"],"BGXAI/BGXAI_SYNC.ps1")
  self.assertEqual(p["branch"],"bg-eet-ai")
  self.assertEqual(p["channel"],"bgxai-fox-new-onefile")
  self.assertRegex(p["commit"],r"^[a-f0-9]{40}$")
  self.assertEqual(p["script_size"],len(self.script))
  self.assertEqual(p["script_sha256"],sha(self.script))
  self.assertLessEqual(len(self.script),80000)
 def test_immutable_git_commit_matches_pin_and_live(self):
  p=self.pin
  b=subprocess.check_output(["git","show",p["commit"]+":"+p["script_path"]])
  self.assertEqual(b,self.script)
 def test_old_175_script_is_exact_stage_176_branch(self):
  self.assertEqual(WRAPPER.read_bytes(),STAGED_WRAPPER.read_bytes())
  self.assertEqual(self.script,STAGE.read_bytes())
 def test_original_actions_1_to_174_identical(self):
  old=BASE_PS.read_text(encoding="ascii")
  new=self.script.decode("ascii")
  self.assertEqual(old.split(OLD_HANDLER,1)[0].replace(OLD_BANNER,"[BANNER]"),
                   new.split(NEW_HANDLER,1)[0].replace(NEW_BANNER,"[BANNER]"))
 def test_source_pins_and_never_arming(self):
  x=self.script.decode("ascii")
  w=WRAPPER.read_bytes()
  self.assertEqual(len(w),19784)
  self.assertEqual(sha(w),"c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c")
  self.assertIn(sha(w),x)
  self.assertIn("if($choice -eq '176'){$extra=@('--v3')}",x)
  self.assertNotIn("SetGlobal(\"BGXW3ARM\"",x)
  self.assertNotIn("XEquipItem(\"STAF01\"",x)
  self.assertNotIn("FillSlot(",x)
 def test_v3_gameplay_unverified_by_release(self):
  x=self.script.decode("ascii")
  self.assertIn("--native-readonly @extra",x)
  self.assertNotIn("--install-v3",x)
if __name__=="__main__":unittest.main(verbosity=2)
