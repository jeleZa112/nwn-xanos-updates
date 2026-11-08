#!/usr/bin/env python3
from __future__ import annotations
import unittest
from dataclasses import replace
from intercept_policy import Ally,Defender,Enemy,Snapshot,Memory,Config,detect_threats,plan,observe_trajectory

ALLY=Ally('Jade',0,0,6,6)
G1=Defender('Khalid',2,0,14,14)
G2=Defender('Teren',0,2,14,14)
APPROACH=Enemy('Shank',8,0,-3,0,True,True,True,None)
ATTACK=Enemy('Shank',3,0,0,0,True,True,True,'Jade')

def make(*,allies=(ALLY,),defenders=(G1,G2),enemies=(APPROACH,),ai=True,tick=0):
    return Snapshot(tick,allies,defenders,enemies,ai)

class ThreatTests(unittest.TestCase):
    def test_approach_before_hit(self):
        threats=detect_threats(make());self.assertEqual(len(threats),1);self.assertEqual(threats[0].reason,'CONFIRMED_CLOSING')
    def test_attack_confirmed(self):self.assertEqual(detect_threats(make(enemies=(ATTACK,)))[0].reason,'CONFIRMED_ATTACK')
    def test_neutral_not_attacked(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,hostile_confirmed=False),))))
    def test_invisible_not_chased(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,visible=False),))))
    def test_dead_enemy(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,alive=False),))))
    def test_dead_ally(self):self.assertFalse(detect_threats(make(allies=(replace(ALLY,hp=0),))))
    def test_stationary_near_no_target(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,vx=0),))))
    def test_enemy_retreat(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,vx=3),))))
    def test_cross_trajectory(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,vx=0,vy=3),))))
    def test_distant_closing_not_summoned(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,x=31),))))
    def test_explicit_ranged_target(self):self.assertTrue(detect_threats(make(enemies=(replace(APPROACH,x=18,vx=0,attacking_uid='Jade'),))))
    def test_invalid_explicit_range(self):self.assertFalse(detect_threats(make(enemies=(replace(APPROACH,x=30,vx=0,attacking_uid='Jade'),))))
    def test_risk_hp_priority(self):
        frail=Ally('Imoen',0,1,1,8)
        enemies=(replace(ATTACK,uid='a',attacking_uid='Jade'),replace(ATTACK,uid='b',x=3,y=1,attacking_uid='Imoen'))
        threats=detect_threats(make(allies=(ALLY,frail),enemies=enemies))
        self.assertEqual(threats[0].ally_uid,'Imoen')
    def test_enemy_doesnt_threat_other_ally_by_target_only(self):
        distant=Ally('Dorn',8,10,10,10)
        found=detect_threats(make(allies=(ALLY,distant),enemies=(replace(ATTACK,attacking_uid='Jade'),)))
        self.assertEqual([x.ally_uid for x in found],['Jade'])

class RoleTests(unittest.TestCase):
    def test_one_primary_one_cover(self):
        p,_=plan(make());self.assertIsNotNone(p.interceptor_uid);self.assertIsNotNone(p.cover_uid);self.assertNotEqual(p.interceptor_uid,p.cover_uid)
    def test_cover_stays(self):
        p,_=plan(make());self.assertIn('COVER_HOLD_POSITION',[i['kind'] for i in p.intents]);self.assertTrue(all(i['kind']!='ATTACK' for i in p.intents))
    def test_party_ai_off(self):
        p,_=plan(make(ai=False));self.assertEqual(p.withheld_reason,'PARTY_AI_DISABLED');self.assertFalse(p.intents)
    def test_guard_off_excluded(self):
        p,_=plan(make(defenders=(replace(G1,guard_on=False),G2)));self.assertEqual(p.interceptor_uid,'Teren');self.assertIsNone(p.cover_uid)
    def test_individual_ai_off_excluded(self):
        p,_=plan(make(defenders=(replace(G1,ai_on=False),G2)));self.assertEqual(p.interceptor_uid,'Teren')
    def test_manual_action_not_interrupted(self):
        p,_=plan(make(defenders=(replace(G1,busy='manual'),G2)));self.assertNotEqual(p.interceptor_uid,'Khalid')
    def test_cast_not_interrupted(self):
        p,_=plan(make(defenders=(replace(G1,busy='casting'),G2)));self.assertNotEqual(p.interceptor_uid,'Khalid')
    def test_song_not_interrupted(self):
        p,_=plan(make(defenders=(replace(G1,busy='bard-song'),G2)));self.assertNotEqual(p.interceptor_uid,'Khalid')
    def test_item_not_interrupted(self):
        p,_=plan(make(defenders=(replace(G1,busy='item-use'),G2)));self.assertNotEqual(p.interceptor_uid,'Khalid')
    def test_scripted_not_interrupted(self):
        p,_=plan(make(defenders=(replace(G1,busy='scripted'),G2)));self.assertNotEqual(p.interceptor_uid,'Khalid')
    def test_all_manual_no_action(self):
        p,_=plan(make(defenders=(replace(G1,busy='manual'),replace(G2,busy='manual'))));self.assertEqual(p.withheld_reason,'NO_ELIGIBLE_INTERCEPTOR');self.assertFalse(p.intents)
    def test_autoattack_deferred_if_only_one(self):
        p,_=plan(make(defenders=(replace(G1,busy='autoattack'),)));self.assertEqual(p.intents[0]['kind'],'DEFER_UNTIL_IDLE')
    def test_idle_defender_preferred_when_near(self):
        p,_=plan(make(defenders=(replace(G1,busy='autoattack'),G2)));self.assertEqual(p.interceptor_uid,'Teren')
    def test_damaged_guard_not_suicidal(self):
        p,_=plan(make(defenders=(replace(G1,hp=1,max_hp=14),G2)));self.assertEqual(p.interceptor_uid,'Teren')
    def test_caster_not_melee_interceptor(self):
        p,_=plan(make(defenders=(replace(G1,role='caster'),G2)));self.assertEqual(p.interceptor_uid,'Teren')
    def test_bard_not_interceptor(self):
        p,_=plan(make(defenders=(replace(G1,role='bard'),G2)));self.assertEqual(p.interceptor_uid,'Teren')
    def test_single_guard_no_cover(self):
        p,_=plan(make(defenders=(G1,)));self.assertEqual(p.interceptor_uid,'Khalid');self.assertIsNone(p.cover_uid)
    def test_deterministic(self):
        a,_=plan(make());b,_=plan(make());self.assertEqual(a,b)
    def test_no_threat_clears_assignments(self):
        p,m=plan(make(enemies=()));self.assertIsNone(p.interceptor_uid);self.assertEqual(m,Memory())
    def test_hysteresis_same_guard(self):
        p,m=plan(make(tick=10));q,n=plan(make(tick=11),m);self.assertEqual(q.interceptor_uid,p.interceptor_uid);self.assertEqual(n.last_change_tick,10)
    def test_prevent_reassignment_when_F_off(self):
        p,m=plan(make(tick=10));old=p.interceptor_uid
        options=tuple(replace(g,guard_on=False) if g.uid==old else g for g in (G1,G2))
        q,_=plan(make(defenders=options,tick=11),m);self.assertNotEqual(q.interceptor_uid,old)
    def test_no_mutation_of_inputs(self):
        s=make();before=repr(s);plan(s);self.assertEqual(repr(s),before)
    def test_example_low_hp(self):
        low=replace(ALLY,hp=1);p,_=plan(make(allies=(low,),enemies=(ATTACK,)))
        self.assertEqual(p.threat.reason,'CONFIRMED_ATTACK')
    def test_unsupported_role_not_interceptor(self):
        p,_=plan(make(defenders=(replace(G1,role='caster'),replace(G2,role='bard'))));self.assertEqual(p.withheld_reason,'NO_ELIGIBLE_INTERCEPTOR')


class TrajectoryTests(unittest.TestCase):
    def test_two_samples_detect_early_threat(self):
        previous=make(tick=4,enemies=(replace(APPROACH,x=11,vx=0),))
        current=make(tick=5,enemies=(replace(APPROACH,x=8,vx=0),))
        observed=observe_trajectory(previous,current)
        self.assertEqual(observed.enemies[0].vx,-3)
        self.assertEqual(detect_threats(observed)[0].reason,'CONFIRMED_CLOSING')
    def test_first_sample_does_not_guess_movement(self):
        current=make(enemies=(replace(APPROACH,vx=-5),))
        self.assertFalse(detect_threats(observe_trajectory(None,current)))
    def test_teleport_does_not_claim_approach(self):
        previous=make(tick=4,enemies=(replace(APPROACH,x=120),))
        current=make(tick=5,enemies=(replace(APPROACH,x=8),))
        self.assertFalse(detect_threats(observe_trajectory(previous,current)))
    def test_new_enemy_is_not_assumed_moving(self):
        current=make(tick=3)
        self.assertEqual(observe_trajectory(make(tick=2,enemies=()),current).enemies[0].vx,0)
    def test_backwards_clock_resets_velocity(self):
        current=make(tick=2)
        self.assertEqual(observe_trajectory(make(tick=4),current).enemies[0].vx,0)
    def test_attack_still_detected_with_no_movement_history(self):
        cur=make(enemies=(ATTACK,))
        self.assertEqual(detect_threats(observe_trajectory(None,cur))[0].reason,'CONFIRMED_ATTACK')
    def test_invalid_teleport_still_detects_attacker(self):
        prev=make(tick=2,enemies=(replace(ATTACK,x=200),))
        cur=make(tick=3,enemies=(ATTACK,))
        self.assertEqual(detect_threats(observe_trajectory(prev,cur))[0].reason,'CONFIRMED_ATTACK')
    def test_no_duplicate_interceptors(self):
        p,_=plan(make());self.assertEqual(sum(x['kind'] in ('INTERCEPT_WHEN_IDLE','DEFER_UNTIL_IDLE') for x in p.intents),1)
    def test_busy_cover_manual_not_disturbed(self):
        p,_=plan(make(defenders=(G1,replace(G2,busy='manual'))))
        self.assertIsNone(p.cover_uid)
        self.assertEqual(len(p.intents),1)
    def test_busy_autoattack_does_not_clear_queue(self):
        p,_=plan(make(defenders=(replace(G1,busy='autoattack'),)))
        self.assertEqual(p.intents[0]['kind'],'DEFER_UNTIL_IDLE')
    def test_near_support_if_frontline_unavailable(self):
        p,_=plan(make(defenders=(replace(G1,role='caster'),replace(G2,role='support'))))
        self.assertEqual(p.interceptor_uid,'Teren')
    def test_low_hp_cover_excluded(self):
        p,_=plan(make(defenders=(G1,replace(G2,hp=1,max_hp=20))))
        self.assertIsNone(p.cover_uid)
    def test_ai_off_clears_existing_claim(self):
        _,m=plan(make(tick=10))
        p,n=plan(make(tick=11,ai=False),m)
        self.assertEqual(n,Memory())
        self.assertFalse(p.intents)
    def test_guard_does_not_claim_self(self):
        self_guard=replace(G1,uid='Jade')
        p,_=plan(make(defenders=(self_guard,G2)))
        self.assertEqual(p.interceptor_uid,'Teren')
        self.assertIsNone(p.cover_uid)
    def test_busy_second_guard_not_ordered_to_move(self):
        p,_=plan(make(defenders=(G1,replace(G2,busy='autoattack'))))
        self.assertIn('DEFER_COVER_UNTIL_IDLE',[i['kind'] for i in p.intents])
    def test_self_as_only_guard_no_claim(self):
        p,_=plan(make(defenders=(replace(G1,uid='Jade'),)))
        self.assertEqual(p.withheld_reason,'NO_ELIGIBLE_INTERCEPTOR')
    def test_model_refrains_far_passersby(self):
        e=replace(APPROACH,x=15,vx=-2)
        p,_=plan(make(enemies=(e,)))
        self.assertEqual(p.withheld_reason,'NO_CONFIRMED_IMMINENT_THREAT')

if __name__ == '__main__':unittest.main()