"""V142 bounded static PE-delivery capture tests; no game or process writes."""
from __future__ import annotations
import hashlib,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import v142_ro as M

class DeliveryTests(unittest.TestCase):
 def fake(self):
  b=bytearray(0x9000);struct.pack_into('<I',b,0x3c,0x80)
  base=0x140000000;struct.pack_into('<Q',b,0x80+24+24,base)
  for rva,off in ((0x58e140,0x2000),(0x597cd0,0x2400),(0x5901f0,0x2800)):
   for i in range(12):struct.pack_into('<Q',b,off+i*8,base+0x204c60+i*32)
  for i in range(1024):b[0x1000+i]=i&255
  for i in range(512):b[0x4000+i]=(i*17)&255
  return bytes(b)
 def offset(self,sec,rva,size,*,executable=None):
  if rva==0x204c60 and executable is True:return 0x1000
  if rva in (0x58e140,0x597cd0,0x5901f0) and executable is False:
   return {0x58e140:0x2000,0x597cd0:0x2400,0x5901f0:0x2800}[rva]
  if 0x204c60<=rva<0x205000 and executable is True:return 0x4000
  raise M.Hold('SYNTHETIC_NO_SECTION')
 def test_mocked_exact_pe_three_vtables_and_queue_window(self):
  data=self.fake();h=hashlib.sha256(data).hexdigest()
  with patch.object(M,'GAME_EXE_SHA',h),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',return_value={'fake_pdata':True}):
   x=M.v142_delivery(data)
  self.assertEqual(x['queue_target_window']['bytes'],1024)
  self.assertEqual(x['queue_pdata_function'],{'fake_pdata':True})
  self.assertEqual(set(x['vtable_pointers_and_bounded_code_windows']),{'0x58e140','0x597cd0','0x5901f0'})
  self.assertEqual(x['vtable_pointers_and_bounded_code_windows']['0x58e140'][0]['rva'],'0x204c60')
  self.assertFalse(x['render_row_writer_proven'])
  self.assertFalse(x['message_queue_to_combatlog_proven'])
  self.assertEqual(hashlib.sha256(data).hexdigest(),h)

 def test_missing_queue_pdata_fail_closed_but_window_is_source_only(self):
  data=self.fake()
  with patch.object(M,'GAME_EXE_SHA',M.digest(data)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=self.offset),patch.object(M,'extract_pdata_function',side_effect=M.Hold('NO_PDATA')):
   r=M.v142_delivery(data)
  self.assertEqual(r['queue_pdata_hold'],'NO_PDATA')
  self.assertFalse(r['queue_target_window']['function_boundaries_proven'])
  self.assertEqual(r['queue_target_window']['bytes'],1024)

 def test_source_sha_guard(self):
  with self.assertRaisesRegex(M.Hold,'EXACT_GAME_EXE_SHA_DRIFT'):
   M.v142_delivery(self.fake())

 def test_external_run_preserves_previous_observation_and_files(self):
  with tempfile.TemporaryDirectory() as d:
   exe=Path(d)/'Baldur.exe';exe.write_bytes(b'MZ'+b'\0'*4096)
   orig=exe.read_bytes()
   with patch.object(M,'_v136_run_game',return_value={'status':'V136_HISTORY_HOLD'}),patch.object(M,'extract_pdata_function',return_value={'source':'V140_VALID'}),patch.object(M,'v142_delivery',return_value={'status':'V142_FAKE_CAPTURE','message_queue_to_combatlog_proven':False}):
    out=M.run_game(Path(d),None)
   self.assertEqual(out['status'],'V142_PINNED_DISPATCH_MESSAGE_ROUTING_CAPTURED_UI_HOLD')
   self.assertEqual(out['v136_live_observation']['status'],'V136_HISTORY_HOLD')
   self.assertEqual(out['callee']['source'],'V140_VALID')
   self.assertFalse(out['delivery_capture']['message_queue_to_combatlog_proven'])
   self.assertFalse(out['visible_row_join_verified'])
   self.assertEqual(out['game_files_written'],0)
   self.assertEqual(exe.read_bytes(),orig)

 def test_invalid_section_reason_never_pretends_success(self):
  data=self.fake()
  with patch.object(M,'GAME_EXE_SHA',M.digest(data)),patch.object(M,'_section_list',return_value=([],0,0)),patch.object(M,'_rva_to_raw',side_effect=M.Hold('NO_SECTION')):
   with self.assertRaisesRegex(M.Hold,'NO_SECTION'):M.v142_delivery(data)

 def test_v142_source_no_game_writes_or_native_hooks(self):
  src=Path(M.__file__).read_text('utf8')
  self.assertLess(len(src.encode('utf8')),20001)
  for forbidden in ('WriteProcessMemory(', 'VirtualProtect(', 'CreateRemoteThread(', 'EEex_JITAt(', 'EEex_HookBefore('):
   self.assertNotIn(forbidden,src)
  self.assertIn("'game_files_written':0",src)
  self.assertIn("'native_hooks_installed':False",src)
  self.assertIn("message_queue_to_combatlog_proven",src)

if __name__=='__main__':unittest.main(verbosity=2)
