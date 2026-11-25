"""BG EET RU V144: source-only exact EXE routing targets and preservation tests."""
from __future__ import annotations
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import v144_ro as M

class V144Targets(unittest.TestCase):
 def source(self):return b'MZ'+bytes(range(256))*40
 def offset(self,sections,rva,length,*,executable=None):
  self.assertTrue(executable)
  self.assertEqual(length,512)
  return {0x209580:128,0x2195b0:1024,0x406720:5120}[rva]
 def test_three_exact_windows_and_bounded_pdata(self):
  src=self.source()
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',side_effect=lambda data,*,rva:{'begin_rva':hex(rva),'function_bytes':32}):
   out=M.v144_targets(src)
  self.assertEqual([r['target_rva'] for r in out['targets']],['0x209580','0x2195b0','0x406720'])
  self.assertEqual([r['window_bytes'] for r in out['targets']],[512]*3)
  self.assertTrue(all(r['window_sha256']==hashlib.sha256(bytes.fromhex(r['window_hex'])).hexdigest() for r in out['targets']))
  self.assertTrue(all(r['pdata_function']['function_bytes']==32 for r in out['targets']))
  self.assertFalse(out['message_to_visible_row_proven'])
  self.assertFalse(out['gameplay_verified'])

 def test_pdata_misses_do_not_turn_bounded_windows_into_function_proof(self):
  src=self.source()
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',side_effect=M.Hold('NO_PDATA')):
   out=M.v144_targets(src)
  self.assertEqual(len(out['targets']),3)
  for row in out['targets']:
   self.assertEqual(row['pdata_hold'],'NO_PDATA')
   self.assertTrue(row['window_not_function_bound'])
   self.assertNotIn('pdata_function',row)

 def test_wrong_exe_hash_stops_before_any_pe_parse(self):
  with patch.object(M,'_section_list',side_effect=AssertionError('should not parse')):
   with self.assertRaisesRegex(M.Hold,'EXACT_GAME_EXE_SHA_DRIFT'):
    M.v144_targets(self.source())

 def test_one_downstream_rva_missing_fails_closed(self):
  src=self.source()
  def offset(sec,rva,n,*,executable):
   if rva==0x406720:raise M.Hold('RVA_SECTION_AMBIGUOUS_OR_UNAVAILABLE')
   return self.offset(sec,rva,n,executable=executable)
  with patch.object(M,'GAME_EXE_SHA',M.digest(src)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=offset):
   with self.assertRaisesRegex(M.Hold,'RVA_SECTION_AMBIGUOUS'):
    M.v144_targets(src)

 def test_v144_does_not_replace_v142_when_new_capture_holds(self):
  with tempfile.TemporaryDirectory() as t:
   exe=Path(t)/'Baldur.exe'
   exe.write_bytes(b'MZ'+b'\\0'*4096)
   orig=exe.read_bytes()
   old={'status':'V142_ON_DISK_WINDOWS_CAPTURED_NOT_UI_PROOF'}
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_HISTORY_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value=old),patch.object(M,'v144_targets',side_effect=M.Hold('DOWNSTREAM_NO_PDATA_AND_SECTION')):
    out=M.run_game(Path(t),None)
   self.assertEqual(out['status'],'V142_PINNED_DISPATCH_MESSAGE_ROUTING_CAPTURED_UI_HOLD')
   self.assertEqual(out['delivery_capture'],old)
   self.assertEqual(out['callee']['source'],'V140_VALID')
   self.assertEqual(out['downstream_capture_hold'],'DOWNSTREAM_NO_PDATA_AND_SECTION')
   self.assertEqual(out['game_files_written'],0)
   self.assertEqual(exe.read_bytes(),orig)

 def test_v144_success_preserves_nested_v142_v140_and_v136(self):
  with tempfile.TemporaryDirectory() as t:
   exe=Path(t)/'Baldur.exe';exe.write_bytes(b'MZ'+b'\\0'*4096)
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_HISTORY_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_VALID'}),patch.object(M,'v144_targets',return_value={'status':'V144_VALID','game_files_written':0}):
    out=M.run_game(Path(t),None)
   self.assertEqual(out['status'],'V144_PINNED_DOWNSTREAM_SOURCE_CAPTURED_UI_HOLD')
   self.assertEqual(out['v136_live_observation']['status'],'V136_HISTORY_HOLD')
   self.assertEqual(out['callee']['source'],'V140_VALID')
   self.assertEqual(out['delivery_capture']['status'],'V142_VALID')
   self.assertEqual(out['downstream_capture']['status'],'V144_VALID')
   self.assertFalse(out['visible_row_join_verified'])
   self.assertFalse(out['safe_to_install'])

 def test_readonly_source_and_size_limits(self):
  source=Path(M.__file__).read_text('utf8')
  self.assertLessEqual(len(source.encode('utf8')),20000)
  for bad in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore(', 'DllMain('):
   self.assertNotIn(bad,source)
  self.assertIn("'game_files_written':0",source)
  self.assertIn("'native_hooks_installed':False",source)

if __name__=='__main__':unittest.main(verbosity=2)
