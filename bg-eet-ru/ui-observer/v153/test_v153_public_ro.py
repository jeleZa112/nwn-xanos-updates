"""Portable adversarial V153 tests; strictly synthetic UI bytes, no private user data."""
import hashlib,tempfile,unittest,importlib.util,io,json
from pathlib import Path
from unittest.mock import patch as mockpatch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v153_guarded',HERE/'v153_guarded.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
LUA=b'-- synthetic CI sidecar\n'
RAW=(b'combatLog = {}\n'
     + b"name 'WORLD_MESSAGES'\n"
     + M.ROW_FUNC+b'\n'
     + M.RETURN+b'\n'
     + M.RENDER+b'\n'
     + M.TOGGLE+b'\n'
     + b'table "combatLog"\n')
INSERTED=(RAW[:RAW.index(M.INIT)+len(M.INIT)+1]+M.LOAD_LINE+b'\n'+
          RAW[RAW.index(M.INIT)+len(M.INIT)+1:RAW.index(M.RETURN)]+M.HOOK_LINE+b'\n'+RAW[RAW.index(M.RETURN):])

class GuardedTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='V153_SYNTH_RO_');self.addCleanup(self.tmp.cleanup)
  t=Path(self.tmp.name);self.game=t/'game';self.work=t/'work';self.game.mkdir();self.work.mkdir()
  (self.game/'override').mkdir()
  self.ui=self.game/'override'/'UI.MENU';self.ui.write_bytes(RAW)
  self.weidu=self.game/'weidu.log';self.weidu.write_bytes(b'~test.tp2~ #0 #0\n')
  for name,value in [('ORIG_SHA',M.sha(RAW)),('PATCH_SHA',M.sha(INSERTED)),('SIDE_SHA',M.sha(LUA))]:
   x=mockpatch.object(M,name,value);x.start();self.addCleanup(x.stop)
  x=mockpatch.object(M,'_sidecar',return_value=LUA);x.start();self.addCleanup(x.stop)
 def call(self,mode,typed='',**kw):return M.run(mode,self.game,self.work,input_fn=lambda _:typed,allow_non_windows_test=True,**kw)
 def test_exact_two_inserts_and_recovery(self):
  self.assertEqual(M.patch(RAW),INSERTED)
  self.assertEqual(INSERTED.count(M.RENDER),1)
  self.assertEqual(INSERTED.count(M.TOGGLE),1)
 def test_prefight_no_game_writes(self):
  r=self.call('preflight')
  self.assertEqual(r['status'],'V153_EXACT_PREFLIGHT_PASS_INSTALL_NOT_AUTHORIZED')
  self.assertFalse(r['weidu_native_component']);self.assertFalse(r['game_files_written_this_action'])
  self.assertEqual(self.ui.read_bytes(),RAW)
 def test_no_typed_approval_no_backup_no_game_write(self):
  r=self.call('install','')
  self.assertEqual(r['status'],'V153_INSTALL_CANCELLED_NO_GAME_WRITES')
  self.assertEqual(self.ui.read_bytes(),RAW)
  self.assertFalse((self.work/M.BKP_NAME).exists())
 def test_install_and_exact_last_only_rollback(self):
  r=self.call('install',M.INSTALL_WORD)
  self.assertEqual(r['status'],'V153_INSTALLED_AWAITING_RUNTIME_TEST',r)
  self.assertEqual(self.ui.read_bytes(),INSERTED)
  self.assertEqual((self.game/'override'/M.SIDE_FILE).read_bytes(),LUA)
  self.assertEqual((self.work/M.BKP_NAME/'UI.MENU.original').read_bytes(),RAW)
  self.assertEqual(self.call('rollback','')['status'],'V153_ROLLBACK_CANCELLED_NO_GAME_WRITES')
  q=self.call('rollback',M.ROLLBACK_WORD)
  self.assertEqual(q['status'],'V153_ROLLBACK_EXACT_ORIGINAL_RESTORED',q)
  self.assertEqual(self.ui.read_bytes(),RAW)
  self.assertFalse((self.game/'override'/M.SIDE_FILE).exists())
 def test_later_weidu_change_refuses_rollback(self):
  self.call('install',M.INSTALL_WORD)
  self.weidu.write_bytes(self.weidu.read_bytes()+b'OTHER COMPONENT\n')
  out=self.call('rollback',M.ROLLBACK_WORD)
  self.assertIn('NEWER_WEIDU_COMPONENT_ROLLBACK_FORBIDDEN',out['reason'])
  self.assertEqual(self.ui.read_bytes(),INSERTED)
 def test_later_ui_change_refuses_rollback(self):
  self.call('install',M.INSTALL_WORD)
  self.ui.write_bytes(self.ui.read_bytes()+b'CHANGED')
  out=self.call('rollback',M.ROLLBACK_WORD)
  self.assertIn('LATER_UI_MODIFICATION_ROLLBACK_FORBIDDEN',out['reason'])
 def test_existing_sidecar_is_never_overwritten(self):
  side=self.game/'override'/M.SIDE_FILE;side.write_text('existing',encoding='utf8')
  r=self.call('install',M.INSTALL_WORD)
  self.assertIn('SIDECAR_CONFLICT_NO_OVERWRITE',r['reason'])
  self.assertEqual(side.read_text('utf8'),'existing')
 def test_sha_drift_blocks_install(self):
  self.ui.write_bytes(RAW+b'!')
  r=self.call('install',M.INSTALL_WORD)
  self.assertIn('EXACT_UI_SHA_DRIFT',r['reason'])
 def test_side_source_corruption_blocks_preflight(self):
  with mockpatch.object(M,'_sidecar',return_value=b'bad'):
   r=self.call('preflight')
  self.assertIn('SIDE_SOURCE_SHA_HOLD',r['reason'])
 def test_reinstall_blocked(self):
  self.call('install',M.INSTALL_WORD)
  r=self.call('install',M.INSTALL_WORD)
  self.assertEqual(r['status'],'V153_ALREADY_PREPARED_OR_INSTALLED_HOLD')
 def test_backup_inside_game_forbidden(self):
  r=M.run('preflight',self.game,self.game)
  self.assertIn('EXTERNAL_BACKUP_LOCATION_UNSAFE',r['reason'])
 def test_external_backup_and_no_implicit_weidu_mod(self):
  self.call('install',M.INSTALL_WORD)
  j=json.loads((self.work/M.BKP_NAME/'manifest.json').read_text('utf8'))
  self.assertEqual(j['backend'],'DIRECT_SHA_LAST_ONLY_NOT_WEIDU')
  self.assertFalse(self.call('status')['weidu_native_component'])
 def test_source_has_no_native_game_hooks(self):
  s=(HERE/'v153_guarded.py').read_text('utf8')
  for v in ('WriteProcessMemory(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore('):self.assertNotIn(v,s)
if __name__=='__main__':unittest.main(verbosity=2)
