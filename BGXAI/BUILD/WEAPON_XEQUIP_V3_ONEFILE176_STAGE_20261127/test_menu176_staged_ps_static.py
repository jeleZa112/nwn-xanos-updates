"""BGXAI one-file menu176 source-only tests; do not execute PowerShell/game."""
from pathlib import Path
import hashlib
import re
import unittest

BASE=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/STAGED_BGXAI_SYNC_MENU175.ps1")
STAGE=Path("BGXAI/BUILD/WEAPON_XEQUIP_V3_ONEFILE176_STAGE_20261127/STAGED_BGXAI_SYNC_MENU176.ps1")
WRAPPER=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_DUALMODE_STAGE_176.py")
OLD_BANNER="wh 'BGXAI ONE-FILE UPDATER: 1-174 existing | 175 XEquip native compile READ ONLY | 0 Exit'"
NEW_BANNER="wh '175 inert | 176 V3 RO | 0 Exit'"
OLD_HANDLER="'175' {$p="
NEW_HANDLER="{$_ -match '^17[56]$'} {$p="
OLD_PIN="5bbc5d5444562346df7e2766d5eee97f60b1e2a33a2c5a074272697c1ee4e2b0"
PREPEND="& py -3 $f --commit $commitId --game $gr --native-readonly;"
DUAL="$extra=@();if($choice -eq '176'){$extra=@('--v3')};& py -3 $f --commit $commitId --game $gr --native-readonly @extra;"
def old():return BASE.read_bytes()
def new():return STAGE.read_bytes()
class Stage(unittest.TestCase):
 def test_original_under_limit(self):
  self.assertEqual(len(old()),79973)
  self.assertLessEqual(len(new()),80000)
  self.assertTrue(new().isascii())
 def test_expected_exact_bytes(self):
  a=old().decode("ascii"); b=new().decode("ascii")
  pin=hashlib.sha256(WRAPPER.read_bytes()).hexdigest()
  self.assertEqual(pin,"157d69466fdb5766822145299d64163190b5c9beb8849876b03c08f97f66c35f")
  pairs=[(OLD_BANNER,NEW_BANNER),(OLD_HANDLER,NEW_HANDLER),
         ("$b.Length -ne 8527","$b.Length -ne "+str(len(WRAPPER.read_bytes()))),
         (OLD_PIN,pin),(PREPEND,DUAL),
         ("throw '175 RO STOP'",'throw "$choice RO STOP"')]
  for x,y in pairs:
   self.assertEqual(a.count(x),1,x)
   a=a.replace(x,y)
  self.assertEqual(a,b,"Only six precise substitutions allowed")
 def test_original_menu_1_through_174_exact(self):
  oldprefix=old().decode("ascii").split(OLD_HANDLER,1)[0].replace(OLD_BANNER,"[BANNER]")
  newprefix=new().decode("ascii").split(NEW_HANDLER,1)[0].replace(NEW_BANNER,"[BANNER]")
  self.assertEqual(oldprefix,newprefix)
 def test_v3_only_under_choice176(self):
  x=new().decode("ascii")
  self.assertEqual(x.count(NEW_HANDLER),1)
  self.assertEqual(x.count("@extra;"),1)
  self.assertEqual(x.count("$choice -eq '176'"),1)
  self.assertFalse(any(k in x for k in ('SetGlobal("BGXW3ARM"','XEquipItem("STAF01"','ClearActions(', 'FillSlot(')))
 def test_no_new_updater(self):
  x=new().decode("ascii")
  self.assertIn("Get-PinnedBytes $p",x)
  self.assertIn('if($LASTEXITCODE){throw "$choice RO STOP"}',x)
  self.assertNotIn("'177' {",x)
  self.assertIn("if($choice -eq '176'){$extra=@('--v3')}",x)
 def test_no_unauthenticated_pin(self):
  x=new().decode("ascii")
  self.assertIn("if($b.Length -ne 12783 -or (hb $b) -cne '157d69466fdb5766822145299d64163190b5c9beb8849876b03c08f97f66c35f')",x)
if __name__=="__main__":unittest.main(verbosity=2)
