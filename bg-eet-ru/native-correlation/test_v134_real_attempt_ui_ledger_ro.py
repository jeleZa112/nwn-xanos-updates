"""Independent V134 model tests. No process access; native execution not tested."""
from __future__ import annotations
import hashlib
import os
import unittest
from pathlib import Path
import zipfile

import v134_real_attempt_ui_ledger_ro as v

ZIP=Path(os.environ.get('BG_EET_RU_V134_ARCHIVE', str(Path(__file__).with_name('PRIVATE_USER_ZIP_NOT_BUNDLED'))))


def synthetic():
    a={
        'session':'session-1', 'thread_id':1,'frame_id':123456,'attack_seq':7,
        'attacker_id':1201,'target_id':3302,'weapon_resref':'SW1H04',
        'ability_index':0,'outcome':'MISS','native_hit_origin_verified':True,
        'native_abi_verified':True,'weapon_at_actual_swing_verified':True,
        'native_outcome_verified':True,
    }
    event={k:a[k] for k in ('session','thread_id','frame_id','attack_seq','attacker_id','target_id','outcome')}
    event.update(callsite=0x39E89E,callee=0x398530,render_token='render-9',
                 native_callsite_verified=True,render_payload_origin_verified=True)
    row={k:a[k] for k in ('session','attack_seq','attacker_id','target_id','outcome')}
    row.update(row_id='row-15',render_token='render-9',row_class='ATTACK_OUTCOME',
               is_visible=True,ui_origin_verified=True)
    return a,event,row

class StrictModel(unittest.TestCase):
    @unittest.skipUnless(ZIP.is_file(), 'Private user archive not available in public CI')
    def test_real_zip(self):
        self.assertTrue(ZIP.is_file())
        old_sha=hashlib.sha256(ZIP.read_bytes()).hexdigest()
        r=v.audit_user_zip(ZIP)
        self.assertEqual(r['status'],'REAL_EVIDENCE_PASS_SOURCE_ONLY_NO_ATTEMPT_ROW_JOIN')
        self.assertEqual(r['real_binary_callsite_matrix']['hit_count'],3)
        self.assertEqual(r['real_binary_callsite_matrix']['damage_count'],8)
        self.assertFalse(r['real_binary_callsite_matrix']['same_callee_is_unique_to_Hit'])
        self.assertTrue(r['real_binary_callsite_matrix']['conditional_addmessage_bypass_reconfirmed'])
        self.assertEqual(r['real_visible_ui']['captured_rows'],72)
        self.assertEqual(r['real_visible_ui']['outcome_rows'],11)
        self.assertEqual(r['real_visible_ui']['hit_result_rows'],5)
        self.assertEqual(r['real_visible_ui']['miss_result_rows'],6)
        self.assertEqual(r['real_visible_ui']['separate_critical_message_rows'],2)
        self.assertEqual(r['historical_native_weapon_event_count'],2)
        self.assertEqual(r['weapon_events_attached_to_any_ui_row'],0)
        self.assertFalse(r['gameplay_verified'])
        self.assertEqual(r['game_files_written'],0)
        self.assertEqual(hashlib.sha256(ZIP.read_bytes()).hexdigest(),old_sha)
    @unittest.skipUnless(ZIP.is_file(), 'Private user archive not available in public CI')
    def test_corrupted_hit_and_damage_bytes_hold(self):
        with zipfile.ZipFile(ZIP) as z:
            hit=z.read(v.HIT_PATH); damage=z.read(v.DAMAGE_PATH)
        for binary,other,at in ((hit,damage,0x39E89E-v.HIT_RVA),
                                (damage,hit,0x390954-v.DAMAGE_RVA)):
            tmp=bytearray(binary);tmp[at]^=1
            with self.assertRaisesRegex(v.Hold,'PINNED_'):
                if binary is hit:v.audit_machine_code(bytes(tmp),other)
                else:v.audit_machine_code(other,bytes(tmp))
    @unittest.skipUnless(ZIP.is_file(), 'Private user archive not available in public CI')
    def test_source_real_ui_row_contains_no_native_join(self):
        r=v.audit_user_zip(ZIP)
        obs=r['real_visible_ui']['observations']
        self.assertEqual(obs[0]['ui_row_number'],10)
        self.assertEqual(obs[0]['actor_display_name'],'Больной гибберлинг')
        self.assertEqual(obs[-1]['ui_row_number'],64)
        for row in obs:
            self.assertIsNone(row['native_attempt_id'])
            self.assertIsNone(row['render_event_token'])
            self.assertIsNone(row['weapon_resref'])
            self.assertFalse(row['row_to_weapon_join_verified'])
    def test_model_candidate_does_not_claim_runtime(self):
        a,e,r=synthetic()
        outcome=v.strict_render_join(a,[e],[r])
        self.assertEqual(outcome['status'],'MODEL_CANDIDATE_NOT_RUNTIME_PROOF')
        self.assertFalse(outcome['runtime_proven'])
        self.assertFalse(outcome['gameplay_verified'])
        self.assertEqual(outcome['weapon_resref'],'SW1H04')
        self.assertEqual(outcome['row_id'],'row-15')
    def test_no_message_needed_in_new_model(self):
        a,e,r=synthetic()
        self.assertNotIn('message_ptr',a)
        self.assertEqual(v.strict_render_join(a,[e],[r])['status'],'MODEL_CANDIDATE_NOT_RUNTIME_PROOF')
    def test_any_provenance_missing_holds(self):
        for field in ('native_hit_origin_verified','native_abi_verified','weapon_at_actual_swing_verified','native_outcome_verified'):
            a,e,r=synthetic();a[field]=False
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'NATIVE_PROOF_MISSING')
        for field in ('native_callsite_verified','render_payload_origin_verified'):
            a,e,r=synthetic();e[field]=False
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'RENDER_EVENT_MISSING_OR_AMBIGUOUS')
        for field in ('is_visible','ui_origin_verified'):
            a,e,r=synthetic();r[field]=False
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'UI_ROW_MISSING_OR_AMBIGUOUS')
    def test_shared_damage_callee_rejected(self):
        for bad in (0x39027B,0x3902E2,0x39056E,0x3905C5,0x39071F,0x390781,0x390954,0x3909A5):
            a,e,r=synthetic();e['callsite']=bad
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'RENDER_EVENT_MISSING_OR_AMBIGUOUS')
    def test_only_candidate_hit_calls_allowed(self):
        for good in v.HIT_CALLS:
            a,e,r=synthetic();e['callsite']=good
            self.assertEqual(v.strict_render_join(a,[e],[r])['status'],'MODEL_CANDIDATE_NOT_RUNTIME_PROOF')
    def test_ambiguous_duplicate_event_and_row_hold(self):
        a,e,r=synthetic()
        self.assertEqual(v.strict_render_join(a,[e,e],[r])['reason'],'RENDER_EVENT_MISSING_OR_AMBIGUOUS')
        self.assertEqual(v.strict_render_join(a,[e],[r,r])['reason'],'UI_ROW_MISSING_OR_AMBIGUOUS')
        self.assertEqual(v.strict_render_join(a,[],[r])['reason'],'RENDER_EVENT_MISSING_OR_AMBIGUOUS')
    def test_actor_target_session_outcome_drift(self):
        for field,value in (('attacker_id',1),('target_id',1),('attack_seq',100),('session','another'),('outcome','HIT')):
            a,e,r=synthetic();e[field]=value
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'RENDER_EVENT_MISSING_OR_AMBIGUOUS')
        a,e,r=synthetic();r['render_token']='wrong'
        self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'UI_ROW_MISSING_OR_AMBIGUOUS')
    def test_resref_and_attempt_identity(self):
        for name in ('sw1h04','TOOLONGCODE','RUSTY AXE','','../bad'):
            a,e,r=synthetic();a['weapon_resref']=name
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'WEAPON_RESREF_INVALID')
        for outcome in ('UNKNOWN','CRIT'):
            a,e,r=synthetic();a['outcome']=outcome
            self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'OUTCOME_UNVERIFIED')
        a,e,r=synthetic();a['outcome']=None
        self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'ATTEMPT_IDENTITY_MISSING')
        a,e,r=synthetic();a.pop('attack_seq')
        self.assertEqual(v.strict_render_join(a,[e],[r])['reason'],'ATTEMPT_IDENTITY_MISSING')
    def test_non_result_d20_and_critical(self):
        sample=[{'ui_row_number':i,'rendered_text':'Нет результата'} for i in range(1,73)]
        sample[0]['rendered_text']='^0xff000000Халид^-: критическое попадание'
        sample[1]['rendered_text']='^0xff000000Халид^-: d20: 9 + 1 = 10 — ПРОМАХ'
        result=v.visible_rows(sample,72)
        self.assertEqual(result['separate_critical_message_rows'],1)
        self.assertEqual(result['miss_result_rows'],1)
        self.assertEqual(result['outcome_rows'],1)
    def test_invalid_real_ui_layout_holds(self):
        sample=[{'ui_row_number':i,'rendered_text':'ПАУЗА'} for i in range(1,73)]
        sample[6]['ui_row_number']=2
        with self.assertRaisesRegex(v.Hold,'VISIBLE_ROWS_ORDER_OR_ID_DRIFT'):
            v.visible_rows(sample,72)

if __name__=='__main__':unittest.main(verbosity=2)
