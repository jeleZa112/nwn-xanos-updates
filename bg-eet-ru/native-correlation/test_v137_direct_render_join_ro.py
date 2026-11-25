"""V137 adversarial, SOURCE ONLY tests. Positive mock != verified gameplay."""
from __future__ import annotations
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import v137_direct_render_join_ro as M

SESSION='TESTSESSION-A_20261125'
TOKEN='SAME_SWING_TOKEN_00001'

def sample(seq=1,tid=10,frame=1000,token=TOKEN):
 a={
  'session':SESSION,'thread_id':tid,'frame_id':frame,'attack_seq':seq,
  'attacker_id':42,'target_id':77,'entry_rva':M.ENTRY_RVA,'exit_rva':M.EXIT_RVA,
  'raw_return':0,'weapon_resref':'AROW01','launcher_resref':'BOW05','ammo_resref':None,
  'ability_index':0,'direct_render_token':token,'item_snapshot_id':'ITEMSNAP001',
  'native_origin_verified':True,'entry_exit_pair_verified':True,
  'item_copied_in_same_invocation':True,'render_token_emitted_by_same_invocation':True,
  'return_mapping_independently_calibrated':True,'win64_abi_proven':True,
  'runtime_unwind_proven':True,'outcome':'MISS','game_exe_sha256':M.GAME_EXE_SHA,
  'conditional_message_seen':False,
 }
 row={'session':SESSION,'thread_id':tid,'frame_id':frame,'attack_seq':seq,
       'attacker_id':42,'target_id':77,'direct_render_token':token,
       'row_id':'ROW-00001','row_class':'ATTACK_ROLL','visible':True,
       'renderer_origin_verified':True,'outcome':'MISS'}
 return a,row

class GateTests(unittest.TestCase):
 def assertHold(self,a,rows,attempts=None,reason=None):
  r=M.join_attempt_direct(a,rows,[a] if attempts is None else attempts)
  self.assertEqual(r.status,'HOLD',r)
  self.assertFalse(r.gameplay_verified)
  self.assertFalse(r.live_identity_verified)
  self.assertFalse(r.native_abi_verified)
  self.assertEqual(r.game_files_written,0)
  self.assertFalse(r.native_hooks_installed)
  if reason:self.assertEqual(r.reason,reason)

 def test_positive_bypasses_message_but_never_gameplay_pass(self):
  a,row=sample()
  r=M.join_attempt_direct(a,[row],[a]);self.assertEqual(r.status,'SOURCE_ONLY_CANDIDATE')
  self.assertEqual((r.weapon_resref,r.launcher_resref,r.ammo_resref),('AROW01','BOW05',None))
  self.assertEqual(r.visible_outcome,'MISS');self.assertFalse(r.gameplay_verified)
  self.assertFalse(r.live_identity_verified);self.assertTrue(r.source_only)

 def test_hit_with_actual_message_does_not_require_callsite(self):
  a,row=sample();a['outcome']=row['outcome']='HIT';a['raw_return']=1
  a['conditional_message_seen']=True
  self.assertEqual(M.join_attempt_direct(a,[row],[a]).status,'SOURCE_ONLY_CANDIDATE')

 def test_no_inference_from_zero_or_one_return(self):
  for n in (0,1):
   a,row=sample();a['raw_return']=n;a['return_mapping_independently_calibrated']=False
   self.assertHold(a,[row],reason='NATIVE_BRIDGE_PROVENANCE_NOT_ESTABLISHED')
  a,row=sample();a.pop('outcome')
  self.assertHold(a,[row],reason='HIT_MISS_SEMANTICS_NOT_CALIBRATED')

 def test_invalid_attempt_records_fail_closed(self):
  self.assertHold(None,[],reason='EVENT_SCHEMA_INVALID')
  self.assertHold({},[],reason='ATTEMPT_REQUIRED_FIELDS_MISSING')
  a,row=sample();self.assertHold(a,iter([row]),reason='EVENT_SCHEMA_INVALID')
  self.assertHold(a,[row],attempts=[],reason='ATTEMPT_KEY_MISSING_OR_DUPLICATED')

 def test_missing_each_required_field(self):
  a,row=sample()
  for field in ('session','thread_id','frame_id','attack_seq','attacker_id','target_id',
                'entry_rva','exit_rva','raw_return','weapon_resref','ability_index',
                'direct_render_token','native_origin_verified','entry_exit_pair_verified',
                'item_copied_in_same_invocation','render_token_emitted_by_same_invocation',
                'return_mapping_independently_calibrated','win64_abi_proven','runtime_unwind_proven'):
   aa=dict(a);aa.pop(field);self.assertHold(aa,[row],reason='ATTEMPT_REQUIRED_FIELDS_MISSING')

 def test_every_false_or_nonbool_provenance_flag_holds(self):
  a,row=sample()
  for field in ('native_origin_verified','entry_exit_pair_verified',
                'item_copied_in_same_invocation','render_token_emitted_by_same_invocation',
                'return_mapping_independently_calibrated','win64_abi_proven','runtime_unwind_proven'):
   for value in (False,None,1,'true',0):
    aa=dict(a);aa[field]=value;self.assertHold(aa,[row],reason='NATIVE_BRIDGE_PROVENANCE_NOT_ESTABLISHED')

 def test_native_site_and_return_validation(self):
  a,row=sample()
  for field,value in [('entry_rva',M.ENTRY_RVA+1),('exit_rva',M.EXIT_RVA+1),
                      ('raw_return',256),('raw_return',-1),('raw_return',1.0),
                      ('ability_index',65536),('ability_index',-1),('ability_index',True)]:
   aa=dict(a);aa[field]=value
   self.assertHold(aa,[row],reason='ATTEMPT_NATIVE_SITES_OR_RAW_RESULT_INVALID')

 def test_identity_and_resref_validation(self):
  a,row=sample()
  for field,value in [('session','abc'),('session','../../bad'),('thread_id',0),
                      ('frame_id',1.0),('attack_seq',True),('target_id',0),('attacker_id',-5)]:
   aa=dict(a);aa[field]=value;self.assertHold(aa,[row],reason='ATTEMPT_IDENTITY_INVALID')
  for field,value in [('weapon_resref','AROW001TOOLONG'),('launcher_resref','bow05'),
                      ('ammo_resref','<bad>'),('weapon_resref',None),('ammo_resref',False)]:
   aa=dict(a);aa[field]=value;self.assertHold(aa,[row],reason='ATTEMPT_RESREF_INVALID_OR_UNCOPIED')

 def test_missing_token_and_untrusted_text_cannot_join(self):
  a,row=sample()
  for tok in ('','row-1','nearest text',123,'BOW05',None,'X'*97):
   aa=dict(a);aa['direct_render_token']=tok
   self.assertHold(aa,[row],reason='DIRECT_TOKEN_NOT_FROM_RENDER_BRIDGE')
  self.assertHold(a,[],reason='VISIBLE_RENDER_TOKEN_MISSING_OR_AMBIGUOUS')
  stale=dict(row);stale['session']='ANOTHER-SESSION'
  self.assertHold(a,[stale],reason='VISIBLE_RENDER_TOKEN_MISSING_OR_AMBIGUOUS')

 def test_ambiguous_duplicate_render_rows_and_tokens(self):
  a,row=sample();self.assertHold(a,[row,dict(row)],reason='VISIBLE_RENDER_TOKEN_MISSING_OR_AMBIGUOUS')
  a2=dict(a);a2['attack_seq']=2
  self.assertHold(a,[row],[a,a2],reason='TOKEN_COLLISION_IN_ATTEMPT_LEDGER')
  a2=dict(a);a2['direct_render_token']='DIFFERENT_TOKEN_0002'
  self.assertHold(a,[row],[a,a2],reason='ATTEMPT_KEY_MISSING_OR_DUPLICATED')
  a2=dict(a);a2['frame_id']=2000;a2['direct_render_token']='DIFFERENT_TOKEN_0002'
  self.assertHold(a,[row],[a,a2],reason='ATTACK_SEQUENCE_COLLISION')
  other=dict(row);other['direct_render_token']='DIFFERENT_TOKEN_0002';other['row_id']='ROW-00002'
  self.assertHold(a,[row,other],reason='MULTIPLE_RENDER_ROWS_FOR_ONE_ATTEMPT')
  other=dict(row);other['direct_render_token']='DIFFERENT_TOKEN_0002';other['attack_seq']=3
  self.assertHold(a,[row,other],reason='RENDER_ROW_ID_COLLISION')

 def test_wrong_rows_do_not_silently_match(self):
  a,row=sample()
  for key,value,why in [
   ('visible',False,'ROW_NOT_VERIFIED_AS_VISIBLE_ATTACK_ROLL'),
   ('visible',1,'ROW_NOT_VERIFIED_AS_VISIBLE_ATTACK_ROLL'),
   ('row_class','DAMAGE','ROW_NOT_VERIFIED_AS_VISIBLE_ATTACK_ROLL'),
   ('renderer_origin_verified',False,'ROW_NOT_VERIFIED_AS_VISIBLE_ATTACK_ROLL'),
   ('attack_seq',2,'VISIBLE_ROW_WRONG_ATTACK_IDENTITY'),
   ('attacker_id',100,'VISIBLE_ROW_WRONG_ATTACK_IDENTITY'),
   ('target_id',88,'VISIBLE_ROW_WRONG_ATTACK_IDENTITY'),
   ('frame_id',1999,'VISIBLE_ROW_WRONG_ATTACK_IDENTITY'),
   ('thread_id',10.0,'VISIBLE_ROW_WRONG_ATTACK_IDENTITY'),
   ('outcome','HIT','VISIBLE_ROW_OUTCOME_DISAGREES'),
  ]:
   rr=dict(row);rr[key]=value;self.assertHold(a,[rr],reason=why)
  rr=dict(row);rr.pop('visible');self.assertHold(a,[rr],reason='VISIBLE_ROW_PROVENANCE_FIELDS_MISSING')

 def test_nested_interleaving_and_reuse_guards(self):
  a,r=sample();b,s=sample(2,10,2000,'NESTED_FRAME_TOKEN_02')
  b['item_snapshot_id']='ITEMSNAP002';s['row_id']='ROW-00002'
  self.assertEqual(M.join_attempt_direct(a,[r,s],[a,b]).status,'SOURCE_ONLY_CANDIDATE')
  self.assertEqual(M.join_attempt_direct(b,[r,s],[a,b]).status,'SOURCE_ONLY_CANDIDATE')
  x=dict(b);x['direct_render_token']=a['direct_render_token']
  self.assertHold(a,[r,s],[a,x],reason='TOKEN_COLLISION_IN_ATTEMPT_LEDGER')

 def test_v136_archive_real_hold(self):
  f=Path(__file__).parents[1]/'SEND_TO_CHATGPT_BG_EET_RU(20261125-162331).zip'
  if not f.is_file():self.skipTest('Original user ZIP lives in local workspace, not GitHub CI')
  r=M.audit_user_zip(f)
  self.assertEqual(r['status'],'REAL_USER_CAPTURE_DIRECT_JOIN_HOLD')
  self.assertEqual(r['reason'],'NO_DIRECT_RENDER_TOKEN_OR_PER_ATTEMPT_NATIVE_PROOF_IN_EXISTING_CAPTURE')
  self.assertEqual(r['v126_visible_row_count'],72)
  self.assertEqual(r['v108_independent_resref_event_count'],2)
  self.assertTrue(r['conditional_message_call_is_not_a_universal_event_source'])

 def test_zip_not_fabricated_or_replaced(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'missing.zip';r=M.audit_user_zip(p)
   self.assertEqual(r['reason'],'SOURCE_ZIP_MISSING_OR_SYMLINK')
   p.write_bytes(b'fake');self.assertEqual(M.audit_user_zip(p)['reason'],'V136_LIVE_ZIP_PIN_DRIFT')

 def test_no_native_patch_apis(self):
  s=Path(M.__file__).read_text(encoding='utf8')
  for fn in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(',
             'EEex_JITAt(', 'EEex_HookAfterCall(', 'EEex_HookBeforeRestore(',
             'os.replace(', 'subprocess.run('):
   self.assertNotIn(fn,s)

 def test_positive_never_claims_real_runtime(self):
  a,row=sample()
  a['win64_abi_proven']=True;a['runtime_unwind_proven']=True
  output=M.join_attempt_direct(a,[row],[a])
  self.assertEqual(output.status,'SOURCE_ONLY_CANDIDATE')
  for flag in ('live_identity_verified','native_abi_verified','runtime_unwind_verified','gameplay_verified'):
   self.assertFalse(getattr(output,flag))

if __name__=='__main__':unittest.main(verbosity=2)
