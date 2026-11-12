"""Guarded 066S->067 WeiDU installation model; no user's game is accessed."""
from __future__ import annotations
import unittest,subprocess
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import BGXAI67_INSTALL as m
import BGXAI67_BCS_PATCH as b
import BGXAI66S_INSTALL as prev
from test_066s_installer_mock import Guarded066S,FakeWeidu,put
from test_067_bcs import early_fragment

class Fake67:
 def __init__(self,prior_bcs,prior_lua,fail=False):
  self.bcs,self.lua=prior_bcs,prior_lua
  self.fail=fail;self.calls=[]
 def __call__(self,cmd,*,cwd,**kwargs):
  root=Path(cwd);install='--force-install' in cmd
  self.calls.append('install' if install else 'rollback')
  if self.fail:return subprocess.CompletedProcess(cmd,1,'MOCK_STOP','ERROR: MOCK STOP')
  if install:
   put(root,m.BCS,(root/m.STAGE_BCS).read_bytes())
   put(root,m.LUA,(root/m.STAGE_LUA).read_bytes())
   with (root/'WeiDU.log').open('ab') as f:f.write(b'~BGX67\\SETUP-BGX67.TP2~ #0 #0\n')
  else:
   put(root,m.BCS,self.bcs)
   put(root,m.LUA,self.lua)
   (root/'WeiDU.log').write_bytes(b'~BGX64\\SETUP-BGX64.TP2~ #0 #0\n~BGX66S\\SETUP-BGX66S.TP2~ #0 #0\n')
  return subprocess.CompletedProcess(cmd,0,'WEIDU_MOCK_OK','')

class Upgrade067(unittest.TestCase):
 def setUp(self):
  self.original=Guarded066S(methodName='test_01_source_pins_and_deterministic_caster')
  self.original.setUp()
  self.addCleanup(self.original.doCleanups)
  self.original.instal()
  self.root=self.original.root
  self.no=self.original.no
  self.backups=self.original.backups
  self.earlier_bcs=(self.root/m.BCS).read_bytes()
  self.earlier_lua=(self.root/m.LUA).read_bytes()
  self.compiler067=lambda *args:early_fragment()
  self.fake67=Fake67(self.earlier_bcs,self.earlier_lua)
  p=patch.object(b,'PIN_066S_BCS',sha256(self.earlier_bcs).hexdigest())
  p.start();self.addCleanup(p.stop)
  self.backup067=lambda root,proof,label:prev.old.make_backup(root,proof,label,parent=self.backups/'067')
 def install67(self,**kwargs):
  return m.install(self.root,process_guard=kwargs.get('guard',self.no),compiler=kwargs.get('compiler',self.compiler067),
    make_backup=kwargs.get('backup',self.backup067),runner=kwargs.get('runner',self.fake67))
 def rollback67(self,**kwargs):
  return m.rollback(self.root,process_guard=kwargs.get('guard',self.no),make_backup=kwargs.get('backup',self.backup067),runner=kwargs.get('runner',self.fake67))
 def test_source_and_unchanged_066s_baseline(self):
  self.assertEqual(m.source_check()['lua_sha256'],m.PIN067)
  self.assertEqual(m.game066s(self.root)['status'],'INSTALLED_066S_VERIFIED')
 def test_preflight_1088_to_1096_game_unmodified(self):
  state={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  pre,raw=m.prepare(self.root,process_guard=self.no,compiler=self.compiler067)
  self.assertEqual(pre['patch']['total_blocks'],1096)
  self.assertEqual(pre['authorized_to_install'],False)
  self.assertEqual(state,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_install_and_rollback_exact_prior_066s(self):
  res=self.install67()
  self.assertEqual(res['after']['status'],'INSTALLED_067_VERIFIED')
  self.assertEqual((self.root/m.LUA).read_bytes(),m.CANDIDATE.read_bytes())
  self.assertNotEqual((self.root/m.BCS).read_bytes(),self.earlier_bcs)
  rb=self.rollback67()
  self.assertEqual(rb['after']['status'],'INSTALLED_066S_VERIFIED')
  self.assertEqual((self.root/m.BCS).read_bytes(),self.earlier_bcs)
  self.assertEqual((self.root/m.LUA).read_bytes(),self.earlier_lua)
 def test_backup_has_both_game_files(self):
  res=self.install67();p=Path(res['backup'])
  self.assertEqual((p/m.LUA).read_bytes(),self.earlier_lua)
  self.assertEqual((p/m.BCS).read_bytes(),self.earlier_bcs)
 def test_stale_bcs_sha_rejected(self):
  (self.root/m.BCS).write_bytes(b'bad')
  with self.assertRaisesRegex(m.Stop,'066S_BASELINE_NOT_VERIFIED'):self.install67()
 def test_foreign_weidu_last_rejected(self):
  with (self.root/'WeiDU.log').open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
  with self.assertRaisesRegex(m.Stop,'066S_BASELINE_NOT_VERIFIED'):self.install67()
 def test_game_open_blocks_pre_stage(self):
  with self.assertRaisesRegex(m.Stop,'ACTIVE_GAME'):self.install67(guard=lambda: (_ for _ in ()).throw(m.Stop('ACTIVE_GAME')))
  self.assertFalse((self.root/'BGX67').exists())
 def test_backup_failed_not_staged(self):
  with self.assertRaisesRegex(m.Stop,'BACKUP_FAILURE'):self.install67(backup=lambda *x: (_ for _ in ()).throw(m.Stop('BACKUP_FAILURE')))
  self.assertFalse((self.root/'BGX67').exists())
 def test_weidu_failure_no_false_install_status(self):
  fail=Fake67(self.earlier_bcs,self.earlier_lua,fail=True)
  with self.assertRaisesRegex(m.Stop,'WEIDU_FAILED_DO_NOT_RETRY'):self.install67(runner=fail)
  self.assertEqual((self.root/m.BCS).read_bytes(),self.earlier_bcs)
 def test_status_detects_bcs_drift_after_install(self):
  self.install67()
  (self.root/m.BCS).write_bytes(b'BAD')
  with self.assertRaisesRegex(m.Stop,'STAGED_BCS_DRIFT'):m.status067(self.root)
 def test_rollback_requires_last_weidu(self):
  self.install67()
  with (self.root/'WeiDU.log').open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
  with self.assertRaisesRegex(m.Stop,'NOT_LAST_WEIDU'):self.rollback67()
 def test_invalid_install_confirmation_rejected(self):
  self.assertEqual(m.main(['install','--yes','--confirm','WRONG','--game-root',str(self.root)]),2)
 def test_stage_collision_rejected(self):
  (self.root/'BGX67').mkdir()
  with self.assertRaisesRegex(m.Stop,'STAGE_COLLISION'):self.install67()
if __name__=='__main__':unittest.main()
