import unittest
from dataclasses import replace
from role_model_068 import ROLE_DATA, Observation, profile, potential_interceptor, possible_healer

READY=Observation(f_enabled=True,idle=True,same_area=True,hp_percent=90,
    effective_melee_verified=True,survivability_verified=True,can_act=True)

class TestRoleModel(unittest.TestCase):
    def test_complete_21_base_ids(self):
        self.assertEqual(set(ROLE_DATA),set(range(1,22)))
    def test_no_unknown_class_mandatory_guard(self):
        for x in [-1,0,22,100,203,255,None,True,'8']:
            with self.subTest(x=x):
                self.assertEqual(profile(x).class_name,'UNKNOWN')
                self.assertFalse(potential_interceptor(x,READY)[0])
    def test_08_is_fighter_cleric_and_hybrid(self):
        p=profile(8)
        self.assertEqual(p.class_name,'FIGHTER_CLERIC')
        self.assertIn('martial',p.capabilities)
        self.assertIn('divine_heal',p.capabilities)
        self.assertTrue(potential_interceptor(8,READY)[0])
    def test_11_is_druid_not_shaman(self):
        self.assertEqual(profile(11).class_name,'DRUID')
        self.assertFalse(potential_interceptor(11,READY)[0])
    def test_21_is_shaman_and_healer_not_melee(self):
        self.assertEqual(profile(21).class_name,'SHAMAN')
        self.assertTrue(possible_healer(21,actual_heal_ability_verified=True))
        self.assertFalse(potential_interceptor(21,READY)[0])
    def test_shapeshifter_only_on_proven_shape(self):
        base=replace(READY,kit_name='SHAPESHIFTER')
        self.assertFalse(potential_interceptor(11,base)[0])
        confirmed=replace(base,shape_confirmed=True,shaped_melee_effective_verified=True)
        self.assertTrue(potential_interceptor(11,confirmed)[0])
    def test_monk_needs_separate_policy(self):
        self.assertFalse(potential_interceptor(20,READY)[0])
    def test_mage_bard_healer_support_preserved(self):
        for class_id in [1,3,5,14,19,21]:
            self.assertFalse(potential_interceptor(class_id,READY)[0])
    def test_hero_martial_hybrids_are_potential_candidates(self):
        for class_id in [2,6,7,8,9,10,12,16,17,18]:
            self.assertTrue(potential_interceptor(class_id,READY)[0],class_id)
    def test_dual_locked_never_intercepts(self):
        self.assertFalse(potential_interceptor(7,replace(READY,is_dual_class=True,dual_old_class_active=False))[0])
        self.assertFalse(potential_interceptor(7,replace(READY,is_dual_class=True,dual_old_class_active=None))[0])
        self.assertTrue(potential_interceptor(7,replace(READY,is_dual_class=True,dual_old_class_active=True))[0])
    def test_healer_requires_actual_spell_and_unlocked_class(self):
        self.assertFalse(possible_healer(3,actual_heal_ability_verified=False))
        self.assertFalse(possible_healer(8,actual_heal_ability_verified=True,dual_old_class_active=False))
        self.assertTrue(possible_healer(8,actual_heal_ability_verified=True))
    def test_guard_toggle_off(self):
        self.assertEqual(potential_interceptor(2,replace(READY,f_enabled=False))[1],'F_OFF')
    def test_healing_takes_priority_even_fighter_cleric(self):
        self.assertEqual(potential_interceptor(8,replace(READY,heal_request_pending=True))[1],'HEAL_FIRST')
    def test_manual_eps_action_priority(self):
        for key in ('manual_order_active','casting','singing','detecting_traps'):
            with self.subTest(key=key):
                self.assertEqual(potential_interceptor(2,replace(READY,**{key:True}))[1],'EPS_OR_MANUAL_ACTION_PRIORITY')
    def test_low_hp_does_not_auto_tank(self):
        self.assertFalse(potential_interceptor(2,replace(READY,hp_percent=50))[0])
        self.assertFalse(potential_interceptor(2,replace(READY,hp_percent=None))[0])
    def test_no_unverified_melee_or_defenses(self):
        self.assertFalse(potential_interceptor(2,replace(READY,effective_melee_verified=False))[0])
        self.assertFalse(potential_interceptor(2,replace(READY,survivability_verified=False))[0])
    def test_needs_same_area_idle_and_can_act(self):
        for key in ('same_area','idle','can_act'):
            self.assertFalse(potential_interceptor(2,replace(READY,**{key:False}))[0])
    def test_shapeshifter_is_kit_not_class_id(self):
        self.assertNotIn('SHAPESHIFTER',[v[0] for v in ROLE_DATA.values()])
        self.assertEqual(profile(11).class_name,'DRUID')
    def test_other_druid_kits_do_not_inherit_shape_guard(self):
        x=replace(READY,kit_name='TOTEMIC_DRUID',shape_confirmed=True,shaped_melee_effective_verified=True)
        self.assertFalse(potential_interceptor(11,x)[0])

if __name__=='__main__': unittest.main()
