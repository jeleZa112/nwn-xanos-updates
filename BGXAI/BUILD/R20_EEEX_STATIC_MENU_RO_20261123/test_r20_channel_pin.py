"""R20 end-to-end static channel proof: one CMD -> SHA-pinned menu164 -> R19 source.
No network or game operations in tests.
"""
from pathlib import Path
import hashlib
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[3]
CMD=ROOT/"BGXAI_UPDATE.cmd"
PIN=ROOT/"BGXAI/fox_new/BOOTSTRAP_PIN.json"
SYNC=ROOT/"BGXAI/BGXAI_SYNC.ps1"
SOURCE=ROOT/"BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py"
CANONICAL=ROOT/"BGXAI/BUILD/R19_INSTALLED_EEEX_STATIC_RO_20261123/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py"
RELEASE="71b1d37db787a59ed16c8b92ac495314b3577e02"
SYNC_SHA="10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42"
R19_SHA="7426faaa18c1a7bb9a8437ee0733854bed0f868a419e96593c58c7ec71451300"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class R20SingleCMDPinTests(unittest.TestCase):
 def test_pin_syntax_and_immutable_release(self):
  p=json.loads(PIN.read_text(encoding="utf-8"))
  self.assertEqual(p["channel"],"bgxai-fox-new-onefile")
  self.assertEqual(p["script_path"],"BGXAI/BGXAI_SYNC.ps1")
  self.assertEqual(p["branch"],"bg-eet-ai")
  self.assertEqual(p["commit"],RELEASE)
  self.assertEqual(p["script_size"],79979)
  self.assertEqual(p["script_sha256"],SYNC_SHA)
 def test_actual_script_exact_sha(self):
  self.assertEqual(SYNC.stat().st_size,79979)
  self.assertEqual(sha(SYNC),SYNC_SHA)
 def test_same_sha_r19_canonical_and_pinned_copy(self):
  self.assertEqual(SOURCE.stat().st_size,11013)
  self.assertEqual(SOURCE.read_bytes(),CANONICAL.read_bytes())
  self.assertEqual(sha(SOURCE),R19_SHA)
 def test_cmd_is_still_the_single_launcher(self):
  x=CMD.read_text(encoding="utf-8-sig")
  self.assertTrue(x.startswith("@echo off"))
  self.assertIn("# BEGIN_BGXAI_RAW_BOOTSTRAP_PS",x)
  self.assertIn("BGXAI_SYNC.current.ps1",x)
  self.assertIn("-File \"%BGX_SCRIPT%\" -GameRoot \"%CD%\"",x)
 def test_cmd_downloads_pin_and_verifies_script_before_execution(self):
  x=CMD.read_text(encoding="utf-8-sig")
  for marker in ("BGXAI/fox_new/BOOTSTRAP_PIN.json",
                 "Download-Limited $scriptSources $temporaryScript 80000",
                 "Downloaded updater SHA256 mismatch; refusing execution",
                 "Downloaded updater size mismatch",
                 "Cached updater SHA256 mismatch; refusing execution",
                 "WriteAllText((Join-Path $cacheDir 'head.txt'),$commitId"):
   self.assertIn(marker,x,marker)
 def test_pin_not_interpreted_as_trusted_obsolete_recovery(self):
  x=CMD.read_text(encoding="utf-8-sig")
  ids=re.findall(r"if\(\$commitId -ceq '([a-f0-9]{40})'\)",x)
  self.assertNotIn(RELEASE,ids)
  self.assertIn("if($commitId -cnotmatch '^[0-9a-f]{40}$'",x)
 def test_new_action_is_just_a_static_audit(self):
  x=SYNC.read_text(encoding="utf-8")
  self.assertIn("152-164 enemy/weapon/EEex tools",x)
  a=re.search(r"(?m)^'164' \{[^\n]+\}$",x)
  self.assertIsNotNone(a)
  for marker in ("Get-PinnedBytes $p","HashBytes $b","HashFile $f",
                 "BGXAI_R20_EEEX_STATIC_","--game $gr",
                 "Out-File -LiteralPath $o -Encoding utf8"):
   self.assertIn(marker,a.group(),marker)
  self.assertNotIn("WeiDU",a.group())
 def test_menu170_is_readonly_and_sha_pinned(self):
  x=SYNC.read_text(encoding="utf-8")
  self.assertIn("'170' {RunR30ReadOnly;break}",x)
  self.assertIn("function RunR30ReadOnly",x)
  self.assertIn("BGXAI_R30_READONLY_",x)
  self.assertIn("--candidate $g",x)
  self.assertIn("61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929",x)
  self.assertIn("88582abf17e919b9441795b8559cfe85b858fd3083672431eb36b60ba78981bd",x)
  self.assertIn("170 R30 RO",x)
  self.assertNotIn("INSTALL_BGXQ30",x)
 def test_no_game_action_allowed_in_r19(self):
  x=SOURCE.read_text(encoding="utf-8")
  for marker in ("'safeToCallGetAbility':False",
                 "'safeToCallGetLauncher':False",
                 "'weaponSwitchAuthorized':False",
                 "'dispatchAuthorized':False"):
   self.assertIn(marker,x)

if __name__=="__main__":unittest.main()
