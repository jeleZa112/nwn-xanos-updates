"""Onefile 176 option7 is a read-only extension. No game or WeiDU access."""
from pathlib import Path
import hashlib
import importlib.util
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
OLDER=ROOT.parent/'WEAPON_XEQUIP_ONEFILE_175_RO_20261126'/'BGXAI_XEQUIP_ONEFILE_175_RO_V1.py'
spec=importlib.util.spec_from_file_location('bgxai_verified_onefile_175',OLDER)
assert spec and spec.loader
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Mode177Integration(unittest.TestCase):
 def test_01_not_installer(self):
  src=OLDER.read_text('utf-8')
  self.assertNotIn('XEquipItem(',src)
  self.assertNotIn('ClearActions(',src)
  self.assertNotIn('BGXW3ARM","LOCALS",1',src)
  self.assertIn('def run_r39(',src)
  self.assertIn('TemporaryDirectory(',src)

 def test_02_177_source_exact_pin(self):
  raw=(ROOT/'BGXAI_R39_ONEFILE177_RO.py').read_bytes()
  size,digest=p.R39_SOURCES[p.R39_ONEFILE]
  self.assertEqual(len(raw),size)
  self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)

 def test_03_old_sources_pins_intact(self):
  self.assertEqual(p.V3_BAF_SHA256,'996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1')
  self.assertEqual(p.V3_SOURCES[p.V3_WRAPPER][0],10743)
  self.assertEqual(p.SOURCES[p.WRAPPER][0],7345)
  self.assertEqual(p.R38_SOURCES[p.R38_PY][0],21303)
  self.assertEqual(p.R38_MODES,('preflight','status','install','rollback','capture'))

 def test_04_choose_7_only_interactive_176(self):
  class FakeInput:
   def isatty(self):return True
  with patch.object(p.sys,'stdin',FakeInput()),patch('builtins.input',return_value='7'):
   self.assertEqual(p.ask_r38_mode(True),'r39-native')
  with patch.object(p.sys,'stdin',FakeInput()),patch('builtins.input',return_value='7'):
   self.assertIsNone(p.ask_r38_mode(False))

 def test_05_choice_0_still_cancel(self):
  class FakeInput:
   def isatty(self):return True
  with patch.object(p.sys,'stdin',FakeInput()),patch('builtins.input',return_value='0'):
   self.assertEqual(p.ask_r38_mode(True),'cancel')

 def test_06_choice_6_still_capture(self):
  class FakeInput:
   def isatty(self):return True
  with patch.object(p.sys,'stdin',FakeInput()),patch('builtins.input',return_value='6'):
   self.assertEqual(p.ask_r38_mode(True),'capture')

 def test_07_onefile_stages_exact_177_helper_without_game_write(self):
  raw=(ROOT/'BGXAI_R39_ONEFILE177_RO.py').read_bytes()
  calls=[]
  def fake_fetch(commit,path):
   calls.append(('fetch',commit,path));return raw
  def fake_runner(argv,**kwargs):
   calls.append(('run',argv))
   self.assertEqual(argv[2],'--game')
   self.assertEqual(argv[4],'--commit')
   self.assertEqual(argv[1].endswith('BGXAI_R39_ONEFILE177_RO.py'),True)
   self.assertEqual(Path(argv[1]).read_bytes(),raw)
   self.assertIs(kwargs['stdin'],p.subprocess.DEVNULL)
   self.assertIsNone(kwargs['stdout'])
   self.assertIsNone(kwargs['stderr'])
   return SimpleNamespace(returncode=0)
  with tempfile.TemporaryDirectory() as td:
   game=Path(td)/'game';game.mkdir()
   before=tuple(game.iterdir())
   self.assertEqual(p.run_r39(game,'a'*40,fetcher=fake_fetch,runner=fake_runner),0)
   self.assertEqual(tuple(game.iterdir()),before)
  self.assertEqual(len(calls),2)

 def test_08_sha_drift_denied_before_runner(self):
  with tempfile.TemporaryDirectory() as td:
   game=Path(td)/'game';game.mkdir()
   called=[]
   def not_run(*args,**kwargs):called.append(1)
   with self.assertRaises(p.Hold):
    p.run_r39(game,'a'*40,fetcher=lambda _c,_p:b'corrupt',runner=not_run)
   self.assertEqual(called,[])

 def test_09_main_routes_to_new_exact_menu_only(self):
  with patch.object(p,'ask_r38_mode',return_value='r39-native'),\
       patch.object(p,'run_r39',return_value=0) as run,\
       patch.object(p,'run_r38') as old:
   self.assertEqual(p.main(['--commit','a'*40,'--v3']),0)
   self.assertEqual(run.call_count,1)
   self.assertEqual(old.call_count,0)

 def test_10_main_old_176_modes_remain(self):
  with patch.object(p,'ask_r38_mode',return_value='status'),\
       patch.object(p,'run_r39') as new,\
       patch.object(p,'run_r38',return_value=0) as old:
   self.assertEqual(p.main(['--commit','a'*40,'--v3']),0)
   self.assertEqual(new.call_count,0)
   self.assertEqual(old.call_count,1)

 def test_11_menu_no_auto_install(self):
  with patch.object(p,'ask_r38_mode',return_value='cancel'),\
       patch.object(p,'run_r39') as new,patch.object(p,'run_r38') as old:
   self.assertEqual(p.main(['--commit','a'*40,'--v3']),0)
   new.assert_not_called();old.assert_not_called()

 def test_12_file_guard_r39_only(self):
  source=(ROOT/'BGXAI_R39_ONEFILE177_RO.py').read_bytes()
  self.assertEqual(p.verify_file(p.R39_ONEFILE,source),None)
  with self.assertRaises(p.Hold):p.verify_file(p.R39_ONEFILE,source+b'\n')
  with self.assertRaises(p.Hold):p.verify_file('not/allowlisted',b'x')

if __name__=='__main__':unittest.main()
