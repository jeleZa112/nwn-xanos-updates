import sys,unittest,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from planner import Actor,Foe,Scene,recommend,behind_defender,distance
from audit_native import audit
from replay import analyze

S=Actor('arch',(0,80),80,True,True,class_role='ARCHER',weapon_ranged=True)
T=Actor('tank',(0,40),100,True,True,class_role='DEFENDER',weapon_ranged=False)
F=Foe('wolf',(0,0),True,True,target_id='tank',can_damage=True,weapon_effective=True,hp_pct=30)

def scene(actor=S,enemies=(F,),defender=T,origin='AI',path=True,bard=False,locked=False):
    return Scene(actor=actor,enemies=enemies,defender=defender,
                 command_origin=origin,path_safety=path,bard_song_mode=bard,manual_locked=locked)

class TestHybrid(unittest.TestCase):
    def test_01_tank_hold_fire(self):
        v=recommend(scene());self.assertEqual(v.kind,'HOLD_AND_FIRE');self.assertEqual(v.proposed_target,'wolf');self.assertFalse(v.executable)
    def test_02_attack_direct_with_safe_path(self):
        wolf=Foe('wolf',(0,20),True,True,'arch',True,True,30)
        v=recommend(scene(enemies=(wolf,)))
        self.assertEqual(v.kind,'REPOSITION_BEHIND_DEFENDER')
        self.assertIsNotNone(v.proposed_position)
        self.assertGreaterEqual(distance(v.proposed_position,wolf.pos),distance(S.pos,wolf.pos))
        self.assertFalse(v.executable)
    def test_03_never_move_with_unknown_path(self):
        wolf=Foe('wolf',(0,40),True,True,'arch',True,True)
        self.assertEqual(recommend(scene(enemies=(wolf,),path=None)).kind,'NATIVE_FALLBACK')
    def test_04_unknown_order_never_take_control(self):self.assertEqual(recommend(scene(origin='UNKNOWN')).kind,'NATIVE_FALLBACK')
    def test_05_player_order_never_take_control(self):self.assertEqual(recommend(scene(origin='PLAYER')).kind,'NATIVE_FALLBACK')
    def test_06_actor_order_queue_unknown(self):self.assertEqual(recommend(scene(locked=None)).kind,'NATIVE_FALLBACK')
    def test_07_bard_unverified_never_take_control(self):self.assertEqual(recommend(scene(bard=None)).kind,'NATIVE_FALLBACK')
    def test_08_bard_mode_never_take_control(self):self.assertEqual(recommend(scene(bard=True)).kind,'NATIVE_FALLBACK')
    def test_09_no_assigned_tank(self):self.assertEqual(recommend(scene(defender=None)).kind,'NATIVE_FALLBACK')
    def test_10_unknown_enemy_aggro(self):
        foe=Foe('wolf',(0,0),True,True,None,True,True)
        self.assertEqual(recommend(scene(enemies=(foe,))).kind,'NATIVE_FALLBACK')
    def test_11_unknown_weapon_immune(self):
        foe=Foe('wolf',(0,0),True,True,'tank',None,True)
        self.assertEqual(recommend(scene(enemies=(foe,))).kind,'NATIVE_FALLBACK')
    def test_12_proven_weapon_immune_no_attack(self):
        foe=Foe('wolf',(0,0),True,True,'tank',False,True)
        self.assertEqual(recommend(scene(enemies=(foe,))).kind,'NO_VIABLE_TARGET')
    def test_13_not_a_ranged_hero(self):
        self.assertEqual(recommend(scene(actor=T)).kind,'NATIVE_FALLBACK')
    def test_14_dont_chase_outside_leash(self):
        wolf=Foe('wolf',(0,0),True,True,'arch',True,True)
        far=Actor('arch',(0,400),70,True,True,weapon_ranged=True)
        self.assertEqual(recommend(scene(actor=far,enemies=(wolf,))).kind,'NATIVE_FALLBACK')
    def test_15_degenerate_geometry(self):
        self.assertIsNone(behind_defender(Foe('e',(0,40),True,True),T))
    def test_16_never_autoexecute_any_fixture(self):
        examples=[scene(),scene(origin='PLAYER'),scene(origin='UNKNOWN'),scene(locked=True),scene(bard=True),scene(path=None),scene(defender=None)]
        self.assertTrue(all(not recommend(x).executable for x in examples))
    def test_17_shadowscript_is_100percent_noncombat(self):
        b=(ROOT/'BGXH022'/'shadow_target.baf').read_text()
        for action in ('Attack(', 'AttackOneRound(', 'RunAway', 'MoveTo', 'EquipRanged(', 'Spell(', 'BattleSong('):self.assertNotIn(action,b)
        for required in ('BGXH022','WeaponEffectiveVs(','WeaponCanDamage(','ActionListEmpty()','Continue()','!Class(Myself,BARD)'):
            self.assertIn(required,b)
    def test_18_installer_does_not_patch_original(self):
        t=(ROOT/'BGXH022'/'setup-BGXH022.tp2').read_text()
        self.assertIn('EXTEND_BOTTOM ~BGXUN1.BCS~',t)
        self.assertIn('COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGXUN1.BCS~',t)
        self.assertIn('COPY_EXISTING ~BGXUN1.BCS~ ~scripts/BGXUN1.BS~',t)
        self.assertNotIn('EXTEND_TOP ~BDDEFAI.BCS~',t)
        self.assertNotIn('EXTEND_BOTTOM ~BDDEFAI.BCS~',t)
    def test_19_private_archive_bard_invariants(self):
        path=Path('/mnt/data/BGXAI_REBUILD020_sources/BG_EET_AUDIT_02_QUESTS_AI.zip')
        if path.exists():
            v=audit(path);self.assertTrue(v['bard_song_mode_present']);self.assertGreater(v['required_song_action_id_296'],0)
    def test_20_existing_failed_093310(self):
        path=Path('/mnt/data/BGXAI_COMBAT(20261105-093310).log')
        if path.exists():
            v=analyze(path);self.assertGreaterEqual(v['A1_attack_starts'],4);self.assertGreaterEqual(v['A1_retreat_starts'],3)
            self.assertTrue(v['risk_repeated_toggling']);self.assertEqual(v['action_origin'],'UNKNOWN')
    def test_21_existing_080316(self):
        path=Path('/mnt/data/BGXAI_COMBAT(20261105-080316).log')
        if path.exists():
            v=analyze(path);self.assertGreaterEqual(v['A1_attack_starts'],1);self.assertGreaterEqual(v['A1_retreat_starts'],1)
            self.assertEqual(v['enemy_aggro'],'UNKNOWN')
    def test_22_shadowscript_optin_off_by_default(self):
        text=(ROOT/'BGXH022'/'shadow_target.baf').read_text()
        self.assertIn('Global("BGXH022","LOCALS",1)',text)
        self.assertEqual(text.count('THEN'),1)
    def test_23_every_known_actor_attackers_prefer_defender(self):
        valid=Foe('target',(0,0),True,True,'tank',True,True,25)
        invalid=Foe('immune',(10,10),True,True,'tank',False,True,1)
        v=recommend(scene(enemies=(invalid,valid)))
        self.assertEqual(v.proposed_target,'target')
    def test_24_danger_without_observed_defender_retains_native(self):
        a=Foe('enemy',(2,75),True,True,'arch',True,True)
        self.assertEqual(recommend(scene(enemies=(a,),defender=Actor('tank',(0,40),100,True,True,class_role='UNKNOWN'))).kind,'NATIVE_FALLBACK')

if __name__=='__main__':unittest.main(verbosity=2)