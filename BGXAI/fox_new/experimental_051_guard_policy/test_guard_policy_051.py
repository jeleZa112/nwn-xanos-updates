import unittest
from dataclasses import replace
from guard_policy_051 import Threat, Guardian, guard_decision, MAX_THREAT_TICKS

T=Threat(attacker_id=75,victim_id=101,victim_slot=3,sequence=12,observed_tick=100,confirmed_engine_hit=True)
G=Guardian(actor_id=201,portrait_slot=2,mode_f=1,is_idle=True,current_modal="NONE",visible_victim=True,visible_attacker=True,distance_victim=5,distance_attacker=4,cooldown_ready=True,origin_safe=True)

def go(t=T,gs=(G,),now=101,prev=None):return guard_decision(t,gs,now,prev)

class SafePolicy(unittest.TestCase):
    def test_baseline(self):
        x=go(); self.assertEqual(x.status,'READY_FOR_BCS_GATING');self.assertEqual(x.assigned_id,201);self.assertFalse(x.command_sent)
    def test_every_denial_fails_closed(self):
        vals=[
          ('mode_f',[0,None,2]), ('is_idle',[False,None]),('current_modal',['BARD_SONG','DETECT_TRAPS','UNKNOWN',None]),
          ('visible_victim',[False,None]),('visible_attacker',[False,None]),('cooldown_ready',[False,None]),
          ('origin_safe',[False,None]),('distance_victim',[None,-1,11,50]),('distance_attacker',[None,-1,8,30]),
          ('portrait_slot',[0,1,7,8]),('actor_id',[75,101])]
        for field, options in vals:
            for value in options:
                with self.subTest(field=field,value=value):
                    self.assertEqual(go(gs=(replace(G,**{field:value}),)).status,'NO_DISPATCH')
    def test_threat_rejections(self):
        items=[replace(T,confirmed_engine_hit=False),replace(T,attacker_id=-1),replace(T,victim_id=-1),replace(T,attacker_id=T.victim_id),
               replace(T,victim_slot=0),replace(T,victim_slot=7),replace(T,sequence=0)]
        for t in items:
            with self.subTest(t=t):self.assertEqual(go(t=t).status,'NO_DISPATCH')
    def test_timing(self):
        for now,obs in [(None,100),(50,100),(191,100)]:
            self.assertEqual(go(t=replace(T,observed_tick=obs),now=now).status,'NO_DISPATCH')
        self.assertEqual(go(t=replace(T,observed_tick=None)).status,'NO_DISPATCH')
        self.assertEqual(go(now=100+MAX_THREAT_TICKS).status,'READY_FOR_BCS_GATING')
        self.assertEqual(go(now=100+MAX_THREAT_TICKS+1).status,'NO_DISPATCH')
    def test_duplicates(self):
        for prev in [12,13,999]:self.assertEqual(go(prev=prev).status,'NO_DISPATCH')
        self.assertEqual(go(prev=11).status,'READY_FOR_BCS_GATING')
    def test_no_unselected_priority(self):
        far=replace(G,actor_id=202,portrait_slot=4,distance_victim=9)
        near=replace(G,actor_id=203,portrait_slot=5,distance_victim=4)
        self.assertEqual(go(gs=(far,G,near)).assigned_id,203)
        same=replace(G,actor_id=204,portrait_slot=4)
        self.assertEqual(go(gs=(same,G)).assigned_id,201)
    def test_friendly_hit_never_commands(self):
        self.assertEqual(go(t=replace(T,attacker_id=101)).status,'NO_DISPATCH')
    def test_empty_and_noneligible(self):
        self.assertEqual(go(gs=()).status,'NO_DISPATCH')
        self.assertEqual(go(gs=(replace(G,mode_f=0),G.__class__(**{**G.__dict__,'actor_id':3,'mode_f':None}))).status,'NO_DISPATCH')
    def test_repeated_actor_not_double_selected(self):
        bad=replace(G,mode_f=None)
        good=replace(G,actor_id=201,portrait_slot=4,distance_victim=3)
        self.assertEqual(go(gs=(bad,good)).status,'NO_DISPATCH')
    def test_command_never_sent_matrix(self):
        for mode in [None,0,1,2]:
            for idle in [None,False,True]:
                for origin in [None,False,True]:
                    x=go(gs=(replace(G,mode_f=mode,is_idle=idle,origin_safe=origin),))
                    self.assertFalse(x.command_sent)

if __name__=='__main__':unittest.main(verbosity=2)
