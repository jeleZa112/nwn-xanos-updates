"""V151 exact installed UI.MENU snapshot, read-only safety and compatibility tests."""
import base64,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import v151_ro as M

class MenuCapture(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='V151_EXACT_UI_')
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.override=self.root/'override';self.override.mkdir()
  self.ui=self.override/'UI.MENU'
  self.raw=b'combatLog = {}\n'+b'list { table "combatLog" text lua "clean(combatLog[rowNumber])" }\n'+b"name 'WORLD_MESSAGES'\n"+'BG_EET_RU_LOG_MODE Привет'.encode('utf8')
  self.ui.write_bytes(self.raw)
 def test_exact_bytes_sha_utf8_and_provenance_hold(self):
  before=self.ui.read_bytes()
  o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['status'],'V151_EXACT_UI_MENU_BYTES_CAPTURED_RO')
  self.assertEqual(o['ui_menu_byte_count'],len(self.raw))
  self.assertEqual(o['ui_menu_sha256'],hashlib.sha256(self.raw).hexdigest())
  self.assertEqual(base64.b64decode(o['ui_menu_original_base64'],validate=True),self.raw)
  self.assertTrue(o['utf8_decode_valid'])
  self.assertEqual(o['anchors']['combatLog_table_inits'],1)
  self.assertEqual(o['anchors']['combatLog_list_binding'],1)
  self.assertEqual(o['anchors']['clean_combatLog_renderer'],1)
  self.assertEqual(o['anchors']['world_messages_menu'],1)
  self.assertFalse(o['safe_to_install'])
  self.assertFalse(o['render_row_identity_proven'])
  self.assertFalse(o['gameplay_verified'])
  self.assertEqual(o['game_files_written'],0)
  self.assertEqual(self.ui.read_bytes(),before)

 def test_missing_actual_ui_menu_hold_not_biff_guess(self):
  self.ui.unlink()
  o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['status'],'V151_UI_MENU_SOURCE_HOLD')
  self.assertEqual(o['reason'],'EXACT_UI_MENU_NOT_UNIQUE_OR_ABSENT')
  self.assertNotIn('ui_menu_original_base64',o)

 def test_reading_case_insensitive_actual_loose_name(self):
  self.ui.rename(self.override/'ui.menu')
  o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['status'],'V151_EXACT_UI_MENU_BYTES_CAPTURED_RO')
  self.assertEqual(o['ui_menu_filename'],'ui.menu')

 def test_duplicate_case_names_fail_closed_even_on_windows(self):
  original=Path.iterdir
  def two(override):
   if override==self.override:
    return iter((self.ui,self.ui))
   return original(override)
  with patch.object(Path,'iterdir',two):
   o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['reason'],'EXACT_UI_MENU_NOT_UNIQUE_OR_ABSENT')
  self.assertNotIn('ui_menu_original_base64',o)

 def test_ui_menu_over_limit_never_copied(self):
  with self.ui.open('wb') as f:f.truncate(3*1024*1024+1)
  o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['reason'],'UI_MENU_SIZE_OUT_OF_BOUNDS')
  self.assertNotIn('ui_menu_original_base64',o)

 def test_changed_during_read_holds_and_no_capture(self):
  original=Path.read_bytes
  def change(path):
   data=original(path)
   if path==self.ui:
    with path.open('ab') as f:f.write(b'changed')
   return data
  with patch.object(Path,'read_bytes',change):
   o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['reason'],'UI_MENU_CHANGED_DURING_CAPTURE')
  self.assertNotIn('ui_menu_original_base64',o)

 def test_symlink_guard_holds_without_reading(self):
  original=Path.is_symlink
  def forged(path):
   return True if path==self.ui else original(path)
  with patch.object(Path,'is_symlink',forged):
   o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(o['reason'],'UI_MENU_SYMLINK_OR_NONLOCAL_FORBIDDEN')

 def test_non_utf8_snapshot_unchanged_not_reinterpreted(self):
  raw=b'combatLog={}\n\xff\x80'
  self.ui.write_bytes(raw)
  o=M.v151_exact_ui_menu(self.root)
  self.assertEqual(base64.b64decode(o['ui_menu_original_base64']),raw)
  self.assertFalse(o['utf8_decode_valid'])

 def test_run_game_preserves_v146_evidence_and_adds_ui(self):
  exe=self.root/'Baldur.exe';exe.write_bytes(b'MZ'+b'\0'*4096)
  old={'status':'V146_VALID'}
  def target(source,targets=(0x209580,0x2195b0,0x406720)):
   return old.copy()
  with patch.object(M,'_v136_run_game',return_value={'status':'V136_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'status':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',side_effect=target):
   o=M.run_game(self.root,None)
  self.assertEqual(o['status'],'V151_EXACT_UI_MENU_CAPTURED_COMBATLOG_JOIN_HOLD')
  self.assertEqual(o['current_ui_menu']['status'],'V151_EXACT_UI_MENU_BYTES_CAPTURED_RO')
  self.assertEqual(o['v136_live_observation']['status'],'V136_HOLD')
  self.assertEqual(o['callee']['status'],'V140_VALID')
  self.assertEqual(o['delivery_capture']['status'],'V142_VALID')
  self.assertEqual(o['downstream_capture']['status'],'V146_VALID')
  self.assertEqual(o['followup_capture']['status'],'V146_PINNED_FOLLOWUP_WINDOWS_CAPTURED_UI_HOLD')
  self.assertEqual(o['game_files_written'],0)
  self.assertFalse(o['visible_row_join_verified'])
  self.assertFalse(o['safe_to_install'])

 def test_ui_captured_even_when_baldur_exe_is_missing(self):
  o=M.run_game(self.root,None)
  self.assertEqual(o['status'],'V151_EXACT_UI_MENU_CAPTURED_COMBATLOG_JOIN_HOLD')
  self.assertEqual(o['current_ui_menu']['ui_menu_sha256'],hashlib.sha256(self.raw).hexdigest())
  self.assertNotIn('callee',o)
  self.assertFalse(o['safe_to_install'])

 def test_source_never_writes_or_installs_game_hook(self):
  source=Path(M.__file__).read_text('utf8')
  self.assertLessEqual(len(source.encode('utf8')),24000)
  for bad in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore(', 'DllMain('):
   self.assertNotIn(bad,source)
  self.assertIn("native_hooks_installed':False",source)
  self.assertIn("safe_to_install':False",source)

if __name__=='__main__':unittest.main(verbosity=2)
