import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
BASE=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('bgx40',BASE/'BGXAI40_INSTALL.py')
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
baf=(BASE/'BGX40/toggle_feedback.baf').read_text('ascii')
tp2=(BASE/'setup-BGX40.tp2').read_text('ascii')
tra=(BASE/'BGX40/lang/ru_ru/feedback.tra').read_text('utf-8')
EPS='~ENHANCED-POWERGAMING-SCRIPTS/SETUP-ENHANCED-POWERGAMING-SCRIPTS.TP2~ #0 #0'
V38='~BGX38/SETUP-BGX38.TP2~ #0 #0'
V39='~BGX39/SETUP-BGX39.TP2~ #0 #0'
V40='~BGX40/SETUP-BGX40.TP2~ #0 #0'

class Static(unittest.TestCase):
 def test_two_toggle_blocks(self): self.assertEqual(len(re.findall(r'^IF$',baf,re.M)),2)
 def test_same_per_character_flag(self):
  for v in ('0','1'):self.assertEqual(baf.count('Global("BGX38_GUARD","LOCALS",'+v+')'),2)
  self.assertEqual(baf.count('HotKey(F)'),2)
 def test_original_cooldown(self):
  self.assertEqual(baf.count('!GlobalTimerNotExpired("BGX38_KEY_CD","LOCALS")'),2)
  self.assertEqual(baf.count('SetGlobalTimer("BGX38_KEY_CD","LOCALS",2)'),2)
 def test_feedback_refs(self):
  self.assertIn('DisplayStringHead(Myself,@0)',baf)
  self.assertIn('DisplayStringHead(Myself,@1)',baf)
  self.assertIn('Охрана: ВКЛ',tra)
  self.assertIn('Охрана: ВЫКЛ',tra)
 def test_no_combat_changes(self):
  for forbidden in ('ProtectObject(','Attack(','ClearActions','ForceSpell','Spell(','UseItem','Equip','MoveToPoint','Continue()'):
   self.assertNotIn(forbidden,baf)
 def test_stays_039_plus_top_only(self):
  self.assertEqual(tp2.count('EXTEND_TOP ~BDDEFAI.BCS~'),1)
  self.assertNotIn('EXTEND_BOTTOM',tp2)
  self.assertIn('USING ~BGX40/lang/ru_ru/feedback.tra~',tp2)
 def test_exact_source_manifest(self):self.assertEqual(mod.verify_source(BASE)['version'],'0.3.10')
 def test_no_game_binary(self): self.assertFalse((BASE/'setup-BGX40.exe').exists())
 def test_dep_039_not_038(self):
  self.assertTrue(mod.base_installed([EPS,V38,V39]));self.assertFalse(mod.base_installed([EPS,V38]))
 def test_dep_must_be_last(self):
  self.assertTrue(mod.base_is_last([EPS,V38,V39]))
  self.assertFalse(mod.base_is_last([EPS,V38,V39,'~OTHER/SETUP.TP2~ #0 #0']))
 def test_040_mod_independent(self):
  self.assertTrue(mod.installed([EPS,V38,V39,V40]));self.assertFalse(mod.installed([EPS,V38,V39]))
 def test_no_source_tamper(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   for n in mod.SOURCE_FILES:
    d=p/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/n,d)
   shutil.copy2(BASE/'SOURCE_MANIFEST.json',p/'SOURCE_MANIFEST.json')
   (p/'BGX40/toggle_feedback.baf').write_bytes(b'wrong')
   with self.assertRaisesRegex(RuntimeError,'Package corrupted'):mod.verify_source(p)
 def test_no_auto_process_kills(self):
  s=(BASE/'BGXAI40_INSTALL.py').read_text('utf-8')
  self.assertNotIn('Stop-Process',s);self.assertNotIn('taskkill',s.lower())

class IsolatedWeiDUMock(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
  self.root=Path(t.name)/'EET';self.root.mkdir()
  for p in ('override','lang/ru_ru'):(self.root/p).mkdir(parents=True,exist_ok=True)
  for name in mod.CRITICAL:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'X'+name.encode())
  (self.root/mod.WEIDU).write_bytes(b'MZ'+b'0'*130000)
  self.log=self.root/'WeiDU.log';self.write([EPS,V38,V39])
  self.profile=Path(t.name)/'HOME';self.profile.mkdir()
 def write(self,lines):self.log.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 def fake(self,cmd,**kwargs):
  a=self.root/'override/BDDEFAI.BCS'
  if '--force-install' in cmd:
   a.write_bytes(a.read_bytes()+b'BGX40_COMPILED');self.write([EPS,V38,V39,V40])
  if '--force-uninstall' in cmd:
   a.write_bytes(a.read_bytes().replace(b'BGX40_COMPILED',b''));self.write([EPS,V38,V39])
  return SimpleNamespace(returncode=0,stdout='mock',stderr='')
 def call(self):
  with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
   return mod.run_install(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake)
 def test_038_alone_refused(self):
  self.write([EPS,V38]);initial=mod.snapshot(self.root)
  with self.assertRaisesRegex(RuntimeError,'BGX39 is not installed'):self.call()
  self.assertEqual(initial,mod.snapshot(self.root))
 def test_wrong_mod_order_refused(self):
  self.write([EPS,V38,V39,'~OTHER/SETUP.TP2~ #0 #0']);initial=mod.snapshot(self.root)
  with self.assertRaisesRegex(RuntimeError,'not last WeiDU'):self.call()
  self.assertEqual(initial,mod.snapshot(self.root))
 def test_duplicate_refused(self):
  self.write([EPS,V38,V39,V40])
  with self.assertRaisesRegex(RuntimeError,'already installed'):self.call()
 def test_existing_source_collision(self):
  (self.root/'setup-BGX40.tp2').write_text('other')
  with self.assertRaisesRegex(RuntimeError,'will not overwrite'):self.call()
 def test_realistic_mock_install_rollback(self):
  data=self.call();self.assertEqual(data['status'],'INSTALLED')
  self.assertTrue(mod.installed(mod.read_log(self.root)))
  self.assertTrue((self.root/'BGX40/toggle_feedback.baf').exists())
  self.assertTrue((self.root/'BGX40/lang/ru_ru/feedback.tra').exists())
  with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
   d=mod.run_uninstall(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake)
  self.assertEqual(d['status'],'UNINSTALLED_AND_RESTORED')
  self.assertFalse(mod.installed(mod.read_log(self.root)))
 def test_rollback_refuses_later_mod(self):
  self.call();self.write([EPS,V38,V39,V40,'~OTHER/SETUP.TP2~ #0 #0'])
  with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
   with self.assertRaisesRegex(RuntimeError,'AFTER BGX40'):
    mod.run_uninstall(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake)
 def test_readonly_status(self):
  import contextlib,io
  old=mod.snapshot(self.root);log=self.log.read_bytes()
  with contextlib.redirect_stdout(io.StringIO()) as output:mod.status(self.root,BASE,real_root=False)
  self.assertIn('BGX39 baseline installed: True',output.getvalue())
  self.assertEqual(old,mod.snapshot(self.root));self.assertEqual(log,self.log.read_bytes())
 def test_no_false_success(self):
  def false_ok(cmd,**kw):
   self.write([EPS,V38,V39,V40]);return SimpleNamespace(returncode=0,stdout='',stderr='')
  with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
   data=mod.run_install(self.root,BASE,real_root=False,guard=lambda:None,runner=false_ok)
  self.assertEqual(data['status'],'REVIEW_INSTALL')

if __name__=='__main__':unittest.main()
