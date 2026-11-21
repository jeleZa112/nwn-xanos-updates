#!/usr/bin/env python3
"""Strict offline-only coordination regression; no real EET claims."""
import unittest
from dataclasses import replace
from BGXAI_PARTY_HAZARD_COORDINATOR_V1 import Actor,Enemy,Frame,coordinate
F=Frame('AR2600',True,True,True,True,True)
T=(Enemy('gibberling','AR2600',True,True,True),Enemy('shank','AR2600',True,True,True,True))
def actor(ident='khalid',role='FRONTLINE',advice='MELEE_CANDIDATE',target='shank',**kw):
    fields=dict(ident=ident,area='AR2600',role=role,advice=advice,target=target,
       role_verified=True,manual_clear_verified=True,eps_idle_verified=True,
       queue_empty_verified=True,f_on_verified=True,route_verified=True,
       aoe_geometry_verified=True,resource_cost=2)
    fields.update(kw);return Actor(**fields)
def choices(a,frame=F,targets=T):return {x.actor:x for x in coordinate(frame,a,targets).choices}
class Coordinator(unittest.TestCase):
    def test_two_frontline_one_reserve(self):
        v=choices([actor(),actor('montaron',target='gibberling')]);self.assertEqual(sum(x.code=='MELEE_CANDIDATE' for x in v.values()),1)
    def test_backline_target_priority(self):
        v=choices([actor('a',target='gibberling'),actor('b',target='shank')]);self.assertEqual(v['b'].code,'MELEE_CANDIDATE')
    def test_three_frontline_two_distinct_intercepts(self):
        v=choices([actor('a',target='gibberling'),actor('b',target='shank'),actor('c',target='shank')]);self.assertEqual(sum(x.code=='MELEE_CANDIDATE' for x in v.values()),2)
    def test_single_frontline_can_intercept(self):self.assertEqual(choices([actor()])['khalid'].code,'MELEE_CANDIDATE')
    def test_one_aoe_lower_cost(self):
        v=choices([actor('a','CASTER','AOE_SAFE_CANDIDATE',resource_cost=8),actor('b','CASTER','AOE_SAFE_CANDIDATE',resource_cost=1)])
        self.assertEqual(v['b'].code,'AOE_SAFE_CANDIDATE');self.assertEqual(v['a'].why,'DUPLICATE_AOE_BLOCKED')
    def test_aoe_equal_cost_deterministic(self):
        v=choices([actor('z','CASTER','AOE_SAFE_CANDIDATE'),actor('a','CASTER','AOE_SAFE_CANDIDATE')]);self.assertEqual(v['a'].code,'AOE_SAFE_CANDIDATE')
    def test_incomplete_summon_roster_no_aoe(self):
        r=coordinate(replace(F,summons_complete=False),[actor('m','CASTER','AOE_SAFE_CANDIDATE')],T);self.assertEqual(r.status,'HOLD_INCOMPLETE_TEAM_EVIDENCE')
    def test_incomplete_hazard_no_aoe(self):
        r=coordinate(replace(F,hazards_complete=False),[actor('m','CASTER','AOE_SAFE_CANDIDATE')],T);self.assertNotEqual(r.status,'ADVISORY_ONLY')
    def test_unknown_geometry(self):
        self.assertEqual(choices([actor('m','CASTER','AOE_SAFE_CANDIDATE',aoe_geometry_verified=False)])['m'].code,'HOLD')
    def test_unknown_aoe_cost(self):
        for value in (None,float('nan'),float('inf'),-1,False,1001):
            self.assertEqual(choices([actor('m','CASTER','AOE_SAFE_CANDIDATE',resource_cost=value)])['m'].code,'HOLD')
    def test_manual_origin_unknown_even_idle_action(self):
        self.assertEqual(choices([actor(manual_clear_verified=False)])['khalid'].why,'MANUAL_ORIGIN_UNVERIFIED')
    def test_eps_queue_unknown_even_action_idle(self):
        self.assertEqual(choices([actor(eps_idle_verified=False)])['khalid'].why,'EPS_QUEUE_UNVERIFIED')
    def test_bcs_actionlistempty_not_queue_proof(self):
        self.assertEqual(choices([actor(queue_empty_verified=False)])['khalid'].why,'ACTION_QUEUE_UNVERIFIED')
    def test_f_off_is_hold(self):
        self.assertEqual(choices([actor(f_on_verified=False)])['khalid'].code,'HOLD')
    def test_ranged_stays_at_safe_position(self):
        self.assertEqual(choices([actor('archer','RANGED','RANGED_HOLD_SAFE_POSITION')])['archer'].code,'RANGED_HOLD_SAFE_POSITION')
    def test_caster_safe_single_target(self):
        self.assertEqual(choices([actor('mage','CASTER','SINGLE_TARGET_SPELL_SAFE_POSITION')])['mage'].code,'SINGLE_TARGET_SPELL_SAFE_POSITION')
    def test_unverified_hostility_blocked(self):
        ts=(replace(T[0],hostile_verified=False),T[1]);v=choices([actor(target='gibberling')],targets=ts)
        self.assertEqual(v['khalid'].why,'HOSTILE_TARGET_UNVERIFIED')
    def test_friendly_target_blocked(self):
        self.assertEqual(choices([actor(target='khalid')])['khalid'].code,'HOLD')
    def test_duplicate_actor_id_fails_closed(self):
        self.assertEqual(coordinate(F,[actor(),actor()],T).status,'HOLD_IDENTITY_OR_AREA_CONFLICT')
    def test_target_actor_identity_collision_fails_closed(self):
        self.assertEqual(coordinate(F,[actor()],T+(Enemy('khalid','AR2600',True,True,True),)).status,'HOLD_IDENTITY_OR_AREA_CONFLICT')
    def test_area_drift_fails_closed(self):
        self.assertEqual(coordinate(F,[actor(area='AR1000')],T).status,'HOLD_IDENTITY_OR_AREA_CONFLICT')
    def test_backstab_requires_safe_route(self):
        self.assertEqual(choices([actor('thief','THIEF','BACKSTAB_MELEE_CANDIDATE',route_verified=False)])['thief'].why,'ROUTE_UNVERIFIED')
    def test_two_thieves_one_backstab(self):
        v=choices([actor('im','THIEF','BACKSTAB_MELEE_CANDIDATE'),actor('mon','THIEF','BACKSTAB_MELEE_CANDIDATE')]);self.assertEqual(sum(x.code=='BACKSTAB_MELEE_CANDIDATE' for x in v.values()),1)
    def test_invalid_cast_as_melee_fails_closed(self):
        self.assertEqual(choices([actor('mage','CASTER','MELEE_CANDIDATE')])['mage'].why,'TACTICAL_ROLE_CONFLICT')
    def test_unknown_proposal_never_passthrough(self):
        self.assertEqual(choices([actor(advice='AttackReevaluate(NearestEnemy,30)')])['khalid'].code,'HOLD')
    def test_executable_proposal_rejected(self):
        self.assertEqual(choices([actor(advice_executable=True)])['khalid'].code,'HOLD')
    def test_no_execution_even_ideal_state(self):
        r=coordinate(F,[actor(),actor('m','CASTER','AOE_SAFE_CANDIDATE')],T)
        self.assertFalse(r.executable);self.assertFalse(r.dispatch_authorized)
        self.assertTrue(all(c.executable is False for c in r.choices))
    def test_input_not_mutated(self):
        a=(actor(),actor('m','CASTER','AOE_SAFE_CANDIDATE'));before=repr(a)
        coordinate(F,a,T);self.assertEqual(repr(a),before)
    def test_reorder_keeps_same_aoe_winner(self):
        a=actor('a','CASTER','AOE_SAFE_CANDIDATE',resource_cost=1)
        b=actor('b','CASTER','AOE_SAFE_CANDIDATE',resource_cost=3)
        self.assertEqual(choices([a,b])['a'].code,choices([b,a])['a'].code)
    def test_retreat_requires_verified_route(self):
        self.assertEqual(choices([actor('x','THIEF','RETREAT_VERIFIED_ROUTE',target=None,route_verified=False)])['x'].why,'ROUTE_UNVERIFIED')
    def test_retreat_is_advisory_not_movement(self):
        self.assertEqual(choices([actor('x','THIEF','RETREAT_VERIFIED_ROUTE',target=None)])['x'].code,'RETREAT_VERIFIED_ROUTE')
if __name__=='__main__':unittest.main(verbosity=2)
