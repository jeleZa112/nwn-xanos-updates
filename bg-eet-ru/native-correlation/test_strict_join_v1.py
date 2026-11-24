"""Source-only regression tests. No game / EEex writes, ever."""
import copy
import json
from pathlib import Path
import unittest
from strict_join_v1 import join_exact, audit_v125_archive

class Gate(unittest.TestCase):
    def setUp(self):
        self.attack={
            'session':'SESSION-1', 'thread_id':91, 'frame_id':0xABCD,
            'attack_seq':2, 'attacker_id':1001, 'target_id':2002,
            'weapon_resref':'AROW01', 'launcher_resref':'BOW05', 'ammo_resref':'AROW01',
            'result':'MISS', 'message_ptr':0x9999, 'message_callsite':0x39E84B,
            'message_token':'EPOCH/2/MESSAGE/14', 'native_hit_origin_verified':True,
            'native_abi_verified':True, 'original_weapon_at_swing_verified':True,
        }
        self.msg={k:self.attack[k] for k in ('session','thread_id','frame_id','attack_seq',
                    'message_ptr','message_token')}
        self.msg.update(message_type='ATTACK_ROLL',callsite=0x39E84B,proven_native_message=True)
        self.row={k:self.attack[k] for k in ('session','message_ptr','message_token',
                      'attack_seq','attacker_id','target_id')}
        self.row.update(row_id='ROW-40',row_class='ATTACK_ROLL',is_visible=True,ui_source_proven=True)

    def check_hold(self, attr, value, layer='attack'):
        a,m,r=copy.deepcopy(self.attack),copy.deepcopy(self.msg),copy.deepcopy(self.row)
        {'attack':a,'msg':m,'row':r}[layer][attr]=value
        got=join_exact(a,[m],[r]);self.assertEqual(got.status,'HOLD',got)
        self.assertIsNone(got.weapon_resref)
        self.assertFalse(got.gameplay_verified)

    def test_complete_miss_candidate_does_not_claim_runtime(self):
        x=join_exact(self.attack,[self.msg],[self.row])
        self.assertEqual(x.status,'SOURCE_ONLY_CANDIDATE')
        self.assertEqual(x.weapon_resref,'AROW01')
        self.assertEqual(x.launcher_resref,'BOW05')
        self.assertEqual(x.ammo_resref,'AROW01')
        self.assertEqual(x.row_id,'ROW-40')
        self.assertFalse(x.runtime_proven);self.assertFalse(x.gameplay_verified)

    def test_message_absent(self):
        self.assertEqual(join_exact(self.attack,[],[self.row]).reason,'MESSAGE_MISSING_OR_AMBIGUOUS')
    def test_row_absent(self):
        self.assertEqual(join_exact(self.attack,[self.msg],[]).reason,'VISIBLE_ROW_MISSING_OR_AMBIGUOUS')
    def test_message_duplicate(self):
        self.assertEqual(join_exact(self.attack,[self.msg,self.msg],[self.row]).status,'HOLD')
    def test_row_duplicate(self):
        self.assertEqual(join_exact(self.attack,[self.msg],[self.row,self.row]).status,'HOLD')
    def test_wrong_callsite(self):
        self.check_hold('message_callsite',0x390E6F)
    def test_wrong_thread(self):
        self.check_hold('thread_id',92,'msg')
    def test_wrong_frame(self):
        self.check_hold('frame_id',0xABCE,'msg')
    def test_wrong_sequence(self):
        self.check_hold('attack_seq',3,'row')
    def test_wrong_attacker(self):
        self.check_hold('attacker_id',3000,'row')
    def test_wrong_target(self):
        self.check_hold('target_id',3000,'row')
    def test_wrong_message_pointer(self):
        self.check_hold('message_ptr',0x8888,'row')
    def test_wrong_message_token(self):
        self.check_hold('message_token','EPOCH/OTHER','row')
    def test_damage_row_rejected(self):
        self.check_hold('row_class','DAMAGE','row')
    def test_damage_message_rejected(self):
        self.check_hold('message_type','DAMAGE','msg')
    def test_row_not_visible(self):
        self.check_hold('is_visible',False,'row')
    def test_row_source_not_proven(self):
        self.check_hold('ui_source_proven',False,'row')
    def test_native_abi_missing(self):
        self.check_hold('native_abi_verified',False)
    def test_unverified_swing_weapon(self):
        self.check_hold('original_weapon_at_swing_verified',False)
    def test_unverified_native_origin(self):
        self.check_hold('native_hit_origin_verified',False)
    def test_wrong_ability_outcome(self):
        self.check_hold('result','UNVERIFIED')
    def test_bad_weapon_ref(self):
        self.check_hold('weapon_resref','LONG-WEAPON-RESREF')
    def test_missing_attacker(self):
        self.check_hold('attacker_id',None)
    def test_wrong_message_callsite(self):
        self.check_hold('callsite',0x39049D,'msg')
    def test_unverified_message_class(self):
        self.check_hold('proven_native_message',False,'msg')
    def test_two_target_false_merge(self):
        a2=dict(self.attack,attack_seq=3,target_id=2033,message_token='SEQ3',message_ptr=0x9998)
        m2=dict(self.msg,attack_seq=3,message_token='SEQ3',message_ptr=0x9998)
        r2=dict(self.row,attack_seq=3,target_id=2033,message_token='SEQ3',message_ptr=0x9998,row_id='ROW-41')
        got=join_exact(self.attack,[m2,self.msg],[r2,self.row]);self.assertEqual(got.row_id,'ROW-40')
        self.assertEqual(join_exact(a2,[self.msg,m2],[self.row,r2]).row_id,'ROW-41')

    def test_real_v125_zip_must_hold(self):
        user_zip=Path(__file__).resolve().parent/'_USER_ZIP_ONLY_TEST_FIXTURE'  # CI: optional
        if user_zip.exists():
            report=audit_v125_archive(user_zip)
            self.assertEqual(report['status'],'HOLD_NO_PER_ATTACK_TO_VISIBLE_ROW_JOIN')
            self.assertEqual(report['game_files_written'],0)
            self.assertFalse(report['gameplay_verified'])

if __name__=='__main__':unittest.main()
