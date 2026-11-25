"""V138 compiled C: deterministic state transitions and pointer lifetime."""
from v138_test_support import LedgerSupport,C,Event,FixedRef,ref,C_FILE

class LedgerTests(LedgerSupport):
    def test_basic_entry_exit_and_no_item_pointer_retention(self):
        weapon=ref(b'AROW01')
        rc,seq=self.enter(weapon=weapon,launcher=b'BOW05',ammo=b'AROW01',ability=2)
        self.assertEqual(rc,0)
        for i,b in enumerate(b'OTHER_'):weapon.bytes[i]=b
        self.assertEqual(self.done(seq,raw=0),0)
        rc,e=self.read(seq)
        self.assertEqual(rc,0)
        self.assertEqual((e.weapon,e.launcher,e.ammo),(b'AROW01',b'BOW05',b'AROW01'))
        self.assertEqual(e.ability,2)
        self.assertEqual(e.raw_return,0)
        self.assertEqual(e.raw_return_present,1)
        self.assertEqual(e.render_count,0)
    def test_raw_zero_and_one_are_not_result_classification(self):
        for i,raw in enumerate((0,1,255),1):
            rc,seq=self.enter(frame=i)
            self.assertEqual(rc,0)
            self.assertEqual(self.done(seq,frame=i,raw=raw),0)
            rc,e=self.read(seq)
            self.assertEqual((rc,e.raw_return,e.raw_return_present,e.render_count),(0,raw,1,0))
    def test_nested_frames_strict_lifo(self):
        a=self.enter(frame=10)[1];b=self.enter(frame=11)[1]
        self.assertEqual(self.done(b,frame=11),0)
        self.assertEqual(self.done(a,frame=10),0)
        self.assertEqual(self.stats(),(0,2,0,0))
    def test_out_of_order_exit_invalidates_only_affected_thread(self):
        a=self.enter(frame=10)[1];b=self.enter(frame=11)[1]
        c=self.enter(thread=20,frame=1)[1]
        self.assertEqual(self.done(a,frame=10),-4)
        self.assertEqual(self.done(b,frame=11),-6)
        self.assertEqual(self.done(c,thread=20,frame=1),0)
        self.assertEqual(self.stats(),(0,1,2,0))
    def test_duplicate_frame_for_one_thread_is_rejected(self):
        a=self.enter(frame=10)[1]
        self.assertEqual(self.enter(frame=10)[0],-7)
        self.assertEqual(self.done(a,frame=10),-6)
        self.assertEqual(self.stats()[2],1)
    def test_same_frame_number_on_two_threads_is_legal(self):
        a=self.enter(thread=7,frame=10)[1]
        b=self.enter(thread=8,frame=10)[1]
        self.assertNotEqual(a,b)
        self.assertEqual(self.done(b,thread=8),0)
        self.assertEqual(self.done(a),0)
        self.assertEqual(self.stats()[1],2)
    def test_replayed_exit_does_not_create_duplicate_event(self):
        a=self.enter()[1]
        self.assertEqual(self.done(a),0)
        self.assertEqual(self.done(a),-6)
        self.assertEqual(self.stats()[1],1)
    def test_foreign_thread_exit_rejected(self):
        a=self.enter()[1]
        self.assertEqual(self.done(a,thread=8),-6)
        self.assertEqual(self.done(a),0)
    def test_wrong_frame_exit_drops_thread(self):
        a=self.enter()[1]
        self.assertEqual(self.done(a,frame=13),-4)
        self.assertEqual(self.stats()[2],1)
    def test_wrong_session_cannot_alias_same_seq(self):
        a=self.enter()[1]
        self.assertEqual(self.done(a,session=99),-5)
        self.assertEqual(self.done(a),0)
        self.assertEqual(self.d.bgv138_direct_render(99,a,13),-5)
    def test_missing_actor_ids_and_required_item_rejected(self):
        for kwargs in ({'attacker':0},{'target':0},{'weapon':None},{'weapon':b''}):
            self.assertEqual(self.enter(**kwargs)[0],-1)
        self.assertEqual(self.stats(),(0,0,0,0))
    def test_invalid_resrefs_fail_without_partials(self):
        for resref in (b'TOO_LONG9',b'bad',b'WEAP*',b'\x80',b'FIRE-WND'):
            self.assertEqual(self.enter(weapon=resref)[0],-1)
            self.assertEqual(self.enter(launcher=resref)[0],-1)
            self.assertEqual(self.enter(ammo=resref)[0],-1)
        self.assertEqual(self.stats(),(0,0,0,0))
    def test_optional_item_can_be_absent(self):
        a=self.enter()[1]
        self.assertEqual(self.done(a),0)
        _,e=self.read(a)
        self.assertEqual(e.launcher,b'')
        self.assertEqual(e.ammo,b'')
