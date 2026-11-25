"""V146 read-only five-target batch tests. Source-only, no game installation."""
from __future__ import annotations
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import v146_ro as M

class PresentationBatch(unittest.TestCase):
 def fake(self):return b'MZ'+bytes(range(256))*80
 def offset(self,sections,rva,size,*,executable=None):
  self.assertEqual(size,512);self.assertTrue(executable)
  return {0x40bc80:512,0x40a400:2048,0x276490:3584,0x4069f0:5120,0x2197b0:7168}[rva]
 def test_success_exact_five_targets_with_non_claiming_status(self):
  source=self.fake()
  with patch.object(M,'GAME_EXE_SHA',M.digest(source)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',side_effect=lambda data,*,rva:{'function_begin_rva':hex(rva)}):
   x=M.v146_followup(source)
  self.assertEqual(x['captured_windows'],5)
  self.assertEqual(x['status'],'V146_ALL_FIVE_WINDOWS_RO')
  self.assertEqual([e['target_rva'] for e in x['targets']],['0x40bc80','0x40a400','0x276490','0x4069f0','0x2197b0'])
  for row in x['targets']:
   w=row['bounded_window']
   self.assertEqual(w['bytes'],512)
   self.assertEqual(hashlib.sha256(bytes.fromhex(w['hex'])).hexdigest(),w['sha256'])
   self.assertFalse(w['exact_function_boundaries_proven'])
   self.assertFalse(row['semantics_proven'])
  self.assertFalse(x['rendered_combatlog_link_proven'])
  self.assertFalse(x['per_attempt_weapon_outcome_link_proven'])
  self.assertFalse(x['gameplay_verified'])

 def test_pdata_missing_is_not_mislabeled_complete_function(self):
  source=self.fake()
  with patch.object(M,'GAME_EXE_SHA',M.digest(source)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',side_effect=M.Hold('NO_PDATA')):
   x=M.v146_followup(source)
  self.assertEqual(x['captured_windows'],5)
  self.assertTrue(all(e['pdata_hold']=='NO_PDATA' for e in x['targets']))
  self.assertTrue(all('pdata_segment' not in e for e in x['targets']))

 def test_partial_source_window_hold_is_explicit(self):
  source=self.fake()
  def offset(sec,rva,n,*,executable):
   if rva==0x4069f0:raise M.Hold('NO_SECTION_FOR_TARGET')
   return self.offset(sec,rva,n,executable=executable)
  with patch.object(M,'GAME_EXE_SHA',M.digest(source)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=offset),patch.object(M,'extract_pdata_function',return_value={}):
   x=M.v146_followup(source)
  self.assertEqual(x['captured_windows'],4)
  self.assertEqual(x['status'],'V146_PARTIAL_WINDOW_HOLD')
  self.assertEqual(x['targets'][3]['source_window_hold'],'NO_SECTION_FOR_TARGET')
  self.assertFalse(x['rendered_combatlog_link_proven'])

 def test_wrong_game_exe_sha_fail_closed_before_pe_parse(self):
  with patch.object(M,'_section_list',side_effect=AssertionError('must not read sections')):
   with self.assertRaisesRegex(M.Hold,'EXACT_GAME_EXE_SHA_DRIFT'):M.v146_followup(self.fake())

 def test_new_partial_capture_does_not_destroy_old_v144_success(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+bytes(4096))
   before=exe.read_bytes()
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_OLD_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',return_value={'status':'V144_VALID'}),patch.object(M,'v146_followup',return_value={'status':'V146_PARTIAL_WINDOW_HOLD','captured_windows':4}):
    x=M.run_game(Path(d),None)
   self.assertEqual(x['status'],'V146_PARTIAL_PRESENTATION_CAPTURE_HOLD')
   self.assertEqual(x['callee']['source'],'V140_VALID')
   self.assertEqual(x['delivery_capture']['status'],'V142_VALID')
   self.assertEqual(x['downstream_capture']['status'],'V144_VALID')
   self.assertFalse(x['safe_to_install'])
   self.assertEqual(x['game_files_written'],0)
   self.assertEqual(exe.read_bytes(),before)

 def test_failure_of_new_reader_preserves_v144(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+bytes(4096))
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_OLD_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',return_value={'status':'V144_VALID'}),patch.object(M,'v146_followup',side_effect=M.Hold('NEW_SOURCE_UNAVAILABLE')):
    x=M.run_game(Path(d),None)
   self.assertEqual(x['status'],'V144_PINNED_DOWNSTREAM_SOURCE_CAPTURED_UI_HOLD')
   self.assertEqual(x['presentation_capture_hold'],'NEW_SOURCE_UNAVAILABLE')
   self.assertEqual(x['downstream_capture']['status'],'V144_VALID')

 def test_complete_new_capture_retains_old_history_and_no_gameplay_claim(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+bytes(4096))
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_OLD_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',return_value={'status':'V144_VALID'}),patch.object(M,'v146_followup',return_value={'status':'V146_ALL_FIVE_WINDOWS_RO','captured_windows':5}):
    x=M.run_game(Path(d),None)
   self.assertEqual(x['status'],'V146_PINNED_PRESENTATION_BATCH_CAPTURED_UI_HOLD')
   self.assertEqual(x['presentation_capture']['captured_windows'],5)
   self.assertEqual(x['v136_live_observation']['status'],'V136_OLD_HOLD')
   self.assertFalse(x['visible_row_join_verified'])
   self.assertFalse(x['gameplay_verified'])

 def test_no_runtime_hooks_and_module_size_bounded(self):
  src=Path(M.__file__).read_text('utf8')
  self.assertLessEqual(len(src.encode('utf8')),24000)
  for bad in ('WriteProcessMemory(', 'CreateRemoteThread(', 'VirtualProtectEx(', 'EEex_HookBefore(', 'EEex_JITAt(', 'DllMain('):
   self.assertNotIn(bad,src)
  self.assertIn("'native_hooks_installed':False",src)

if __name__=='__main__':unittest.main(verbosity=2)
