"""V138 compiled C: adversarial overflow, replay, token, nested-thread tests."""
import random
from pathlib import Path
from v138_test_support import LedgerSupport,C,Event,FixedRef,ref,C_FILE

class LedgerTests(LedgerSupport):
    def test_render_token_explicit_and_uniquely_claimed(self):
        a=self.enter()[1];self.done(a)
        b=self.enter(frame=11)[1];self.done(b,frame=11)
        self.assertEqual(self.d.bgv138_direct_render(self.S,a,88100),0)
        self.assertEqual(self.d.bgv138_direct_render(self.S,a,88100),-7)
        self.assertEqual(self.d.bgv138_direct_render(self.S,b,88100),-7)
        self.assertEqual(self.d.bgv138_direct_render(self.S,b,88101),0)
        _,e=self.read(a)
        self.assertEqual((e.row_token,e.render_count),(88100,1))
        _,e=self.read(b)
        self.assertEqual((e.row_token,e.render_count),(88101,1))
    def test_no_unprovable_synthetic_renderer_token(self):
        a=self.enter()[1]
        self.assertEqual(self.d.bgv138_direct_render(self.S,a,999),-6)
        self.assertEqual(self.done(a),0)
        self.assertEqual(self.d.bgv138_direct_render(self.S,a,0),-1)
        self.assertEqual(self.read(a)[1].render_count,0)
    def test_reset_cannot_silently_drop_running_frames(self):
        a=self.enter()[1]
        self.assertEqual(self.d.bgv138_reset(self.S+1),-4)
        self.assertEqual(self.done(a),0)
        self.assertEqual(self.d.bgv138_reset(self.S+1),0)
        self.assertEqual(self.d.bgv138_read(self.S,a,C.byref(Event())),-5)
    def test_thread_limit_poison_instead_of_misattribute(self):
        for i in range(1,25):
            self.assertEqual(self.enter(thread=i,frame=i)[0],0)
        self.assertEqual(self.enter(thread=25,frame=25)[0],-3)
        self.assertEqual(self.stats()[3],1)
    def test_depth_limit_poison_before_stack_corruption(self):
        for i in range(1,17):self.assertEqual(self.enter(frame=i)[0],0)
        self.assertEqual(self.enter(frame=17)[0],-3)
        self.assertEqual(self.stats()[3],1)
    def test_exact_capacity_512_then_poison(self):
        for i in range(512):
            code,seq=self.enter(frame=i+1)
            self.assertEqual(code,0)
            self.assertEqual(self.done(seq,frame=i+1),0)
        self.assertEqual(self.stats(),(0,512,0,0))
        self.assertEqual(self.enter(frame=513)[0],-3)
        self.assertEqual(self.stats()[3],1)
    def test_500_randomized_interleaved_nested_frames(self):
        rng=random.Random(1381138)
        active={i:[] for i in range(1,9)}
        completed=0
        for _ in range(500):
            thread=rng.choice(tuple(active))
            stack=active[thread]
            if stack and (rng.random()<.48 or len(stack)>=10):
                frame,seq=stack.pop()
                self.assertEqual(self.done(seq,thread=thread,frame=frame),0)
                completed+=1
            else:
                frame=thread*100000+_+1
                rc,seq=self.enter(thread=thread,frame=frame)
                self.assertEqual(rc,0)
                stack.append((frame,seq))
        for t,stack in active.items():
            while stack:
                frame,seq=stack.pop()
                self.assertEqual(self.done(seq,thread=t,frame=frame),0)
                completed+=1
        self.assertLessEqual(completed,512)
        self.assertEqual(self.stats(),(0,completed,0,0))
    def test_invalid_read_rejected(self):
        self.assertEqual(self.read(123)[0],-6)
        self.assertEqual(self.d.bgv138_read(self.S,0,C.byref(Event())),-1)
    def test_source_never_installs_hooks_or_guesses_result(self):
        s=C_FILE.read_text(encoding='utf8')
        for forbidden in ('WriteProcessMemory(', 'VirtualProtect(', 'CreateRemoteThread(',
                          'EEex_JITAt(', 'EEex_HookAfterCall(', 'DllMain(',
                          'return_1_is_hit', 'return_0_is_miss'):
            self.assertNotIn(forbidden,s)
        self.assertIn('raw_return',s)
        self.assertIn('bgv138_direct_render',s)
