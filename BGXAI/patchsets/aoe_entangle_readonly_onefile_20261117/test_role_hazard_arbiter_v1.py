#!/usr/bin/env python3
"""BGXAI tactical arbitration: source-only regression tests; NEVER installs."""
from __future__ import annotations
from dataclasses import replace
import itertools
import unittest

from BGX121_POLICY import Ally, Hazard
from BGXAI_ROLE_HAZARD_ARBITER_V1 import Advice, Situation, advise

ALLY=Ally("khalid",0,0,"AR2600")
FRIEND=Ally("jaheira",250,0,"AR2600")
GIBBERLING=Hazard("web01",90,0,"AR2600",15,frozenset({"WEB"}))
SAFE_AOE=Hazard("entangle_target",100,0,"AR2600",20,frozenset({"ENTANGLE"}))

def scene(**kw):
    base=Situation(
        actor=ALLY,position=(0,0),melee_position=(100,0),
        role="FRONTLINE",role_verified=True,
        class_and_kit_verified=True,dual_state="NONE",
        dual_state_verified=True,manual_order_active=False,
        currently_casting=False,eps_heal_reserved=False,
        bard_song_reserved=False,target_hostile_visible_verified=True,
        hostile_ally_target_excluded=True,hazard_list_complete=True,
        close_enemy_verified=False,can_sustain_melee=True,
        melee_quickslot_verified=True,ranged_quickslot_verified=True,
        ranged_ammo_verified=True,single_target_spell_verified=False,
        spell_resource_verified=False)
    return replace(base,**kw)

def decision(s=None,hazards=(),allies=(ALLY,FRIEND),roster=True):
    return advise(s or scene(),allies,hazards,roster)

class RoleHazardV1(unittest.TestCase):
    def test_frontline_safe_melee_without_hazards(self):
        self.assertEqual(decision().code,"MELEE_CANDIDATE")

    def test_true_path_crossing_hazard_favors_bow_without_moving(self):
        x=decision(hazards=[GIBBERLING])
        self.assertEqual(x.code,"RANGED_HOLD_SAFE_POSITION")
        self.assertEqual(x.reason,"MELEE_PATH_INTERSECTS_HAZARD")

    def test_hazard_holds_when_no_ranged_and_no_safe_path(self):
        s=scene(ranged_quickslot_verified=False,ranged_ammo_verified=False)
        self.assertEqual(decision(s,[GIBBERLING]).code,"HOLD_AVOID_DANGEROUS_AOE")

    def test_melee_permitted_if_exact_full_effect_immunity(self):
        immune=replace(ALLY,immune_to=frozenset({"WEB"}))
        s=scene(actor=immune)
        self.assertEqual(decision(s,[GIBBERLING]).code,"MELEE_CANDIDATE")

    def test_in_hazard_never_claim_standing_ranged_is_safe(self):
        zone=Hazard("bad",0,0,"AR2600",18,frozenset({"SLEEP"}))
        self.assertEqual(decision(scene(),[zone]).code,"HOLD_HAZARD_EGRESS_UNVERIFIED")

    def test_in_hazard_can_escape_only_when_explicit_route_verified(self):
        zone=Hazard("bad",0,0,"AR2600",18,frozenset({"SLEEP"}))
        s=scene(safe_escape_destination=(130,90),escape_route_verified=True)
        self.assertEqual(decision(s,[zone]).code,"RETREAT_VERIFIED_ROUTE")

    def test_in_hazard_unverified_egress_blocked(self):
        zone=Hazard("bad",0,0,"AR2600",18,frozenset({"SLEEP"}))
        s=scene(safe_escape_destination=(130,90),escape_route_verified=False)
        self.assertEqual(decision(s,[zone]).code,"HOLD_HAZARD_EGRESS_UNVERIFIED")

    def test_manual_action_has_priority_over_eps_and_aoe(self):
        s=scene(manual_order_active=True,eps_heal_reserved=True,role="CASTER")
        self.assertEqual(decision(s,[GIBBERLING]).code,"HOLD_MANUAL_ORDER_OR_UNKNOWN")

    def test_eps_healing_blocks_spell_weapon_and_movement_advice(self):
        s=scene(eps_heal_reserved=True)
        self.assertEqual(decision(s,[GIBBERLING]).code,"DEFER_TO_EPS_HEAL")

    def test_cast_or_song_in_progress_never_interrupted(self):
        self.assertEqual(decision(scene(currently_casting=True)).code,
                         "HOLD_SPELL_SONG_OR_UNKNOWN")
        self.assertEqual(decision(scene(bard_song_reserved=True)).code,
                         "HOLD_SPELL_SONG_OR_UNKNOWN")

    def test_unknown_action_origin_must_hold(self):
        self.assertEqual(decision(scene(manual_order_active=None)).code,
                         "HOLD_MANUAL_ORDER_OR_UNKNOWN")
        self.assertEqual(decision(scene(eps_heal_reserved=None)).code,
                         "HOLD_EPS_STATE_UNKNOWN")

    def test_hostile_must_be_verified_not_ally(self):
        self.assertEqual(decision(scene(target_hostile_visible_verified=False)).code,
                         "HOLD_ENEMY_OR_FRIENDLY_STATUS_UNVERIFIED")
        self.assertEqual(decision(scene(hostile_ally_target_excluded=False)).code,
                         "HOLD_ENEMY_OR_FRIENDLY_STATUS_UNVERIFIED")

    def test_class_dual_or_kit_unknown_never_inferred(self):
        for s in (scene(role_verified=False),scene(class_and_kit_verified=False),
                  scene(dual_state_verified=False),scene(dual_state="UNKNOWN")):
            self.assertEqual(decision(s).code,"HOLD_ROLE_DUAL_KIT_UNVERIFIED")

    def test_hybrid_dual_can_melee_only_if_verified_survivability(self):
        s=scene(role="HYBRID",dual_state="REACTIVATED")
        self.assertEqual(decision(s).code,"MELEE_CANDIDATE")
        self.assertEqual(decision(replace(s,can_sustain_melee=None)).code,
                         "RANGED_HOLD_SAFE_POSITION")

    def test_thief_backstab_third_edition_melee_only(self):
        s=scene(role="THIEF",third_edition_backstab_enabled=True,
             stealth_verified=True,backstab_melee_verified=True,
             backstab_target_vulnerable_verified=True)
        x=decision(s)
        self.assertEqual(x.code,"BACKSTAB_MELEE_CANDIDATE")
        self.assertFalse(x.executable)

    def test_thief_cannot_backstab_without_stealth_or_verified_melee(self):
        base=scene(role="THIEF",third_edition_backstab_enabled=True,
                   stealth_verified=True,backstab_melee_verified=True,
                   backstab_target_vulnerable_verified=True)
        for field in ("third_edition_backstab_enabled","stealth_verified",
                      "backstab_melee_verified","backstab_target_vulnerable_verified"):
            self.assertEqual(decision(replace(base,**{field:False})).code,
                             "RANGED_HOLD_SAFE_POSITION")

    def test_fragile_caster_retreats_instead_of_melee_even_when_path_safe(self):
        s=scene(role="CASTER",can_sustain_melee=False,close_enemy_verified=True,
                safe_escape_destination=(200,100),escape_route_verified=True)
        self.assertEqual(decision(s).code,"RETREAT_VERIFIED_ROUTE")

    def test_fragile_actor_without_escape_does_not_melee(self):
        s=scene(role="CASTER",can_sustain_melee=False,
                close_enemy_verified=True,ranged_ammo_verified=False,
                spell_resource_verified=False)
        self.assertEqual(decision(s).code,"HOLD_NO_SAFE_FRAGILE_ENGAGEMENT")

    def test_target_safe_aoe_with_party_and_summons_verified(self):
        s=scene(role="CASTER",proposed_aoe=SAFE_AOE,
                aoe_spell_verified=True,spell_resource_verified=True)
        x=decision(s,allies=(ALLY,FRIEND,Ally("summon",175,0,"AR2600")))
        self.assertEqual(x.code,"AOE_SAFE_CANDIDATE")

    def test_aoe_unsafe_summoned_creature_is_never_excluded(self):
        s=scene(role="CASTER",proposed_aoe=SAFE_AOE,
                aoe_spell_verified=True,spell_resource_verified=True)
        one=Ally("summon",101,0,"AR2600")
        self.assertNotEqual(decision(s,allies=(ALLY,FRIEND,one)).code,
                            "AOE_SAFE_CANDIDATE")

    def test_aoe_requires_full_roster(self):
        s=scene(role="CASTER",proposed_aoe=SAFE_AOE,
                aoe_spell_verified=True,spell_resource_verified=True)
        self.assertNotEqual(decision(s,roster=False).code,"AOE_SAFE_CANDIDATE")

    def test_area_spell_not_cast_without_known_effects(self):
        unknown=replace(SAFE_AOE,harmful_effects=frozenset())
        s=scene(role="CASTER",proposed_aoe=unknown,
                aoe_spell_verified=True,spell_resource_verified=True)
        self.assertNotEqual(decision(s).code,"AOE_SAFE_CANDIDATE")

    def test_standing_in_threat_safe_cannot_approve_aoe_without_complete_roster(self):
        s=scene(role="CASTER",proposed_aoe=SAFE_AOE,
                aoe_spell_verified=True,spell_resource_verified=True)
        self.assertNotEqual(decision(s,allies=(),roster=True).code,
                            "AOE_SAFE_CANDIDATE")

    def test_caster_aoe_danger_falls_back_to_single_target(self):
        s=scene(role="CASTER",proposed_aoe=SAFE_AOE,aoe_spell_verified=True,
                spell_resource_verified=True,single_target_spell_verified=True,
                ranged_ammo_verified=False)
        unsafe=Ally("ally",100,0,"AR2600")
        self.assertEqual(decision(s,allies=(ALLY,FRIEND,unsafe)).code,
                         "SINGLE_TARGET_SPELL_SAFE_POSITION")

    def test_unverified_hazard_snapshot_holds(self):
        self.assertEqual(decision(scene(hazard_list_complete=False)).code,
                         "HOLD_HAZARD_SNAPSHOT_INCOMPLETE")
        self.assertEqual(decision(scene(melee_position=(float("nan"),0))).code,
                         "HOLD_HAZARD_SNAPSHOT_INCOMPLETE")

    def test_wrong_hazard_area_is_not_a_proof_of_safe_path(self):
        wrong=replace(GIBBERLING,area="AR1000")
        self.assertEqual(decision(hazards=[wrong]).code,"HOLD_HAZARD_OR_ROSTER_INVALID")

    def test_all_decisions_are_advisory_no_executable(self):
        samples=[scene(),scene(role="THIEF",close_enemy_verified=True),
                 scene(eps_heal_reserved=True),scene(manual_order_active=True),
                 scene(role="CASTER",single_target_spell_verified=True,
                       spell_resource_verified=True)]
        for s,h in itertools.product(samples,((),(GIBBERLING,))):
            x=decision(s,h)
            self.assertIsInstance(x,Advice)
            self.assertIs(x.executable,False)

if __name__=="__main__":
    unittest.main(verbosity=2)
