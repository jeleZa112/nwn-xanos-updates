"""V146 read-only five-target capture; hostile synthetic tests, no private EXE."""
from __future__ import annotations
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import v146_ro as M

FOLLOWUP=(0x40bc80,0x40a400,0x276490,0x4069f0,0x2197b0)
V144=(0x209580,0x2195b0,0x406720)

class CaptureTests(unittest.TestCase):
 def sample(self):return b'MZ'+bytes(range(256))*80
 def mapper(self,sections,rva,length,*,executable=None):
  self.assertEqual(executable,True)
  self.assertEqual(length,512)
  return {v:128+i*1024 for i,v in enumerate(FOLLOWUP+V144)}[rva]

 def test_five_ordered_windows_exact_hashes_and_no_gameplay_claim(self):
  src=self.sample()
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.mapper),patch.object(M,'extract_pdata_function',side_effect=lambda data,*,rva:{'function_begin_rva':hex(rva),'function_bytes':64}):
   report=M.v144_targets(src,FOLLOWUP)
  self.assertEqual([int(x['target_rva'],16) for x in report['targets']],list(FOLLOWUP))
  self.assertEqual(len(report['targets']),5)
  for x in report['targets']:
   self.assertEqual(len(bytes.fromhex(x['window_hex'])),512)
   self.assertEqual(hashlib.sha256(bytes.fromhex(x['window_hex'])).hexdigest(),x['window_sha256'])
   self.assertEqual(x['pdata_function']['function_bytes'],64)
   self.assertTrue(x['window_not_function_bound'])
  self.assertFalse(report['message_to_visible_row_proven'])
  self.assertFalse(report['native_hook_installed'])
  self.assertEqual(report['game_files_written'],0)

 def test_three_previous_targets_default_are_unchanged(self):
  src=self.sample()
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.mapper),patch.object(M,'extract_pdata_function',side_effect=M.Hold('NO_PDATA')):
   x=M.v144_targets(src)
  self.assertEqual(tuple(int(t['target_rva'],16) for t in x['targets']),V144)
  self.assertTrue(all(t['pdata_hold']=='NO_PDATA' for t in x['targets']))

 def test_wrong_exe_sha_stops_before_section_parser(self):
  with patch.object(M,'_section_list',side_effect=AssertionError('MUST_NOT_BE_CALLED')):
   with self.assertRaisesRegex(M.Hold,'EXACT_GAME_EXE_SHA_DRIFT'):
    M.v144_targets(self.sample(),FOLLOWUP)

 def test_one_missing_target_does_not_emit_partial_success(self):
  src=self.sample()
  def mapped(sec,rva,n,*,executable):
   if rva==0x2197b0:raise M.Hold('RVA_SECTION_AMBIGUOUS_OR_UNAVAILABLE')
   return self.mapper(sec,rva,n,executable=executable)
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=mapped):
   with self.assertRaisesRegex(M.Hold,'RVA_SECTION_AMBIGUOUS'):
    M.v144_targets(src,FOLLOWUP)

 def test_v146_success_preserves_old_nested_evidence_and_no_file_change(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+bytes(4096));before=exe.read_bytes()
   old={'status':'V144_PINNED_DOWNSTREAM_WINDOWS_CAPTURED_UI_HOLD'}
   new={'status':'V144_PINNED_DOWNSTREAM_WINDOWS_CAPTURED_UI_HOLD','targets':[]}
   def targets(_source,addresses=V144):
    return new.copy() if addresses==FOLLOWUP else old.copy()
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',side_effect=targets):
    x=M.run_game(Path(d),None)
   self.assertEqual(x['status'],'V146_PINNED_FOLLOWUP_SOURCE_CAPTURED_UI_HOLD')
   self.assertEqual(x['downstream_capture'],old)
   self.assertEqual(x['delivery_capture']['status'],'V142_VALID')
   self.assertEqual(x['callee']['source'],'V140_VALID')
   self.assertEqual(x['v136_live_observation']['status'],'V136_HOLD')
   self.assertEqual(x['followup_capture']['status'],'V146_PINNED_FOLLOWUP_WINDOWS_CAPTURED_UI_HOLD')
   self.assertFalse(x['visible_row_join_verified'])
   self.assertFalse(x['safe_to_install'])
   self.assertEqual(x['game_files_written'],0)
   self.assertEqual(exe.read_bytes(),before)

 def test_v146_new_capture_hold_keeps_v144_and_v142_success(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+bytes(4096));before=exe.read_bytes()
   def targets(_source,addresses=V144):
    if addresses==FOLLOWUP:raise M.Hold('MISSING_CONTINUATION')
    return {'status':'V144_VALID'}
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',side_effect=targets):
    x=M.run_game(Path(d),None)
   self.assertEqual(x['status'],'V144_PINNED_DOWNSTREAM_SOURCE_CAPTURED_UI_HOLD')
   self.assertEqual(x['downstream_capture']['status'],'V144_VALID')
   self.assertEqual(x['followup_capture_hold'],'MISSING_CONTINUATION')
   self.assertEqual(x['delivery_capture']['status'],'V142_VALID')
   self.assertEqual(x['game_files_written'],0)
   self.assertEqual(exe.read_bytes(),before)

 def test_source_only_and_updater_cap(self):
  src=Path(M.__file__).read_text('utf8')
  self.assertLessEqual(len(src.encode('utf8')),20000)
  for bad in ('WriteProcessMemory(', 'VirtualProtect(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore(', 'DllMain('):
   self.assertNotIn(bad,src)
  self.assertIn("'safe_to_install':False",src)
  self.assertIn("'game_files_written':0",src)
  self.assertIn('message_to_visible_row_proven',src)

if __name__=='__main__':unittest.main(verbosity=2)
