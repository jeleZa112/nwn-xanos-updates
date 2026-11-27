"""BGXAI shipped R38 under unchanged onefile: validate immutable bootstrap, no install."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path("BGXAI")
PS=ROOT/"BGXAI_SYNC.ps1"
PIN=ROOT/"fox_new/BOOTSTRAP_PIN.json"
OLD=ROOT/"BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py"
CAND=ROOT/"BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_ONEFILE176_NET_AND_DEFAULT_HOTFIX_STAGE.py"
STAGE=ROOT/"BUILD/R38_GUARDED_FROM_R37_20261127/STAGED_BGXAI_SYNC_176_NET_HOTFIX.ps1"
R38=ROOT/"BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py"
LUA=ROOT/"BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua"
R37=ROOT/"BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py"
def sha(b):return hashlib.sha256(b).hexdigest()
class Published(unittest.TestCase):
 def test_01_live_ps_equals_staged_exact(self):
  self.assertEqual(PS.read_bytes(),STAGE.read_bytes())
 def test_02_child_equals_tested_r38_handler(self):
  self.assertEqual(OLD.read_bytes(),CAND.read_bytes())
 def test_03_pinned_immutable_commit_matches(self):
  pin=json.loads(PIN.read_text())
  data=PS.read_bytes()
  self.assertEqual(pin["script_sha256"],sha(data))
  self.assertEqual(pin["script_size"],len(data))
  self.assertEqual(pin["script_size"],79996)
  self.assertEqual(pin["commit"],"0a791e1d92aefd70d42d80b5d79b2dac9b3997a0")
  self.assertEqual(subprocess.check_output(["git","show",pin["commit"]+":"+pin["script_path"]]),data)
 def test_04_child_pin_matches_shell(self):
  ps=PS.read_text(encoding="ascii")
  raw=OLD.read_bytes()
  self.assertEqual(len(raw),19784)
  self.assertEqual(sha(raw),"c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c")
  self.assertIn(sha(raw),ps)
  self.assertIn("$b.Length -ne 19784",ps)
 def test_05_only_old_175_176_switch(self):
  ps=PS.read_text(encoding="ascii")
  self.assertIn("{$_ -match '^17[56]$'}",ps)
  self.assertIn("if($choice -eq '176'){$extra=@('--v3')}",ps)
  self.assertNotIn("'177' {",ps)
  self.assertNotIn("XEquipItem(",ps)
 def test_06_r38_sha_pins_match_child(self):
  source=OLD.read_text()
  for p,expected in ((R38,"f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c"),(LUA,"958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c"),(R37,"b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d")):
   self.assertEqual(sha(p.read_bytes()),expected)
   self.assertIn(expected,source)
 def test_07_r38_noninteractive_install_requires_token(self):
  r38=R38.read_text()
  self.assertIn('if token!=INSTALL_TOKEN:',r38)
  self.assertIn('if token!=ROLLBACK_TOKEN:',r38)
  self.assertIn("print('R38 installs passive READ-ONLY observer only",r38)
  self.assertIn('token=input(',r38)
 def test_08_gameplay_not_authorized_by_source(self):
  child=OLD.read_text()
  self.assertNotIn("SetGlobal(",child)
  self.assertNotIn("XEquipItem(",child)
  self.assertIn('sys.stdin.isatty()',child)
  self.assertIn('def run_r38(',child)
 def test_09_one_updater_80k_limit(self):
  self.assertLessEqual(len(PS.read_bytes()),80000)
  self.assertTrue(PS.read_bytes().isascii())
 def test_10_modes_and_safe_default(self):
  s=OLD.read_text()
  for name in ('preflight','status','install','rollback','capture'):self.assertIn(name,s)
  self.assertIn("if not v3 or sys.stdin is None or not sys.stdin.isatty():",s)
  self.assertIn('return None  # Existing automated/menu176 V3 read-only behavior is unchanged.',s)
if __name__=="__main__":unittest.main(verbosity=2)
