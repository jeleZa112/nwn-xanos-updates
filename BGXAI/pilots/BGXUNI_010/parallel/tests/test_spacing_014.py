#!/usr/bin/env python3
"""Offline BAF structural audit and a deliberately small priority emulator.
NOT a replacement for WeiDU compiler, Infinity Engine or actual gameplay tests.
"""
import re, zipfile, pathlib, unittest, os, json, hashlib, random
ROOT=pathlib.Path(__file__).resolve().parents[1]
BAF=(ROOT/'BGXUNI/BGXUN1.BAF').read_text('utf-8')
TP2=(ROOT/'BGXUNI/setup-BGXUNI.tp2').read_text('utf-8')
CMD=(ROOT/'BGXUNI_SETUP.cmd').read_text('ascii')
# Verified once against actual original IDS. Use the immutable recorded symbol
# subset for repeatable tests on computers without the archived game resources.
_snapshot=json.loads((ROOT/'tests/ids_snapshot.json').read_text('utf-8'))
path=os.environ.get('BGXUNI_MAGIC_ZIP','/mnt/data/BGXAI_SOURCE_CACHE/BG_EET_AUDIT_01_MAGIC.zip')
if pathlib.Path(path).is_file():
 assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==_snapshot['sourceArchiveSHA256']
 z=zipfile.ZipFile(path)
 for k,v in _snapshot['files'].items():
  assert hashlib.sha256(z.read(v['name'])).hexdigest()==v['sha256']
def ids(k): return set(_snapshot['files'][k]['symbols'])
ACTIONS=ids('actions');TRIGGERS=ids('triggers');SPELLS=ids('spells');STATS=ids('stats');CLASSES=ids('classes')
BLOCKS=[]
for chunk in re.split(r'(?m)^IF\s*$',BAF)[1:]:
 ifpart,after=chunk.split('THEN\n',1)
 response,tail=after.split('RESPONSE #100\n',1)
 if 'END' not in tail:raise AssertionError('missing END')
 actions=tail.split('END')[0]
 BLOCKS.append((tuple(x.strip() for x in ifpart.splitlines() if x.strip() and not x.strip().startswith('//')),tuple(x.strip() for x in actions.splitlines() if x.strip() and not x.strip().startswith('//'))))

def condition(raw,s):
 inverse=raw.startswith('!');raw=raw.lstrip('!')
 m=re.match(r'(\w+)\((.*)\)$',raw)
 if not m:raise AssertionError('unsupported trigger '+raw)
 name,args=m.groups();pieces=[x.strip() for x in args.split(',')]
 p=s
 if name=='ActionListEmpty':v=p.get('queue_empty',True)
 elif name=='Global':v=p.get('globals',{}).get(pieces[0].strip('"'),0)==int(pieces[2])
 elif name=='GlobalTimerNotExpired':v=pieces[0].strip('"') in p.get('unexpired',set())
 elif name=='HPPercentLT':v=p.get('hp',100)<int(pieces[1])
 elif name=='HPPercentGT':v=p.get('hp',100)>int(pieces[1])
 elif name=='GlobalGT':v=p.get('globals',{}).get(pieces[0].strip('\"'),0)>int(pieces[2])
 elif name=='TookDamage':v=p.get('took_damage',False)
 elif name=='Range':v=p.get('enemy_visible',False) and p.get('distance',999)<=int(pieces[1])
 elif name=='See':v=p.get('enemy_visible',False)
 elif name=='HaveSpell':v=pieces[0] in p.get('spells',set())
 elif name=='CheckStatGT':v=p.get('skills',{}).get(pieces[2],0)>int(pieces[1])
 elif name=='ModalState':v=p.get('modal')==pieces[0]
 elif name=='StateCheck':v=p.get('invisible',False)
 elif name=='ActuallyInCombat':v=p.get('combat',False)
 elif name=='Class':v=p.get('bard',False) if pieces[1]=='BARD' else False
 elif name=='IsWeaponRanged':v=p.get('ranged',False)
 else:raise AssertionError('unsupported trigger '+name)
 return not v if inverse else v

def decide(**kw):
 for triggers,actions in BLOCKS:
  if all(condition(t,kw) for t in triggers):return actions[-1]
 return None

class TestBAF(unittest.TestCase):
 def test_actions_and_triggers_exist_in_supplied_ids(self):
  for ts,actions in BLOCKS:
   for t in ts:self.assertIn(t.lstrip('!').split('(')[0],TRIGGERS)
   for a in actions:self.assertIn(a.split('(')[0],ACTIONS)
 def test_spell_symbols_in_actual_user_ids(self):
  for x in re.findall(r'\b(?:WIZARD|CLERIC)_[A-Z_]+\b',BAF):self.assertIn(x,SPELLS)
 def test_stats_and_classes(self):
  self.assertTrue({'STEALTH','TRAPS'}<=STATS)
  self.assertIn('BARD',CLASSES)
 def test_blocks_balanced(self):
  self.assertEqual(len(BLOCKS),20)
  for ts,aa in BLOCKS:self.assertTrue(len(ts)>1 and len(aa)>0)
  self.assertEqual(len(re.findall(r'(?m)^END\s*$',BAF)),20)
 def test_no_unsafe_actions(self):
  for bad in ['ClearActions(', 'ForceSpell(', 'ReallyForceSpell(', 'ApplySpell(', 'RemoveTraps(', 'PickLock(', 'UseItem(', 'EquipRanged(', 'MoveTo', 'TriggerOverride(']:
   # Comments are free to name these; limit to actual action lines
   self.assertFalse(any(a.lstrip().startswith(bad) for _,as_ in BLOCKS for a in as_),bad)
 def test_one_script_and_separate_names(self):
  self.assertIn('COMPILE ~BGXUNI/BGXUN1.BAF~',TP2)
  self.assertIn('COPY ~override/BGXUN1.BCS~ ~scripts/BGXUN1.BS~',TP2)
  for old in ['BDDEFAI','BGXGRP','BGXTANK']:
   self.assertNotIn('COPY ~override/'+old,TP2)
  self.assertIn('--uninstall',CMD)
  self.assertIn('setup-stratagems.exe',CMD)
 def test_manual_order_safeguard_when_not_critical(self):
  self.assertIsNone(decide(queue_empty=False,hp=70,enemy_visible=True,distance=3,ranged=True,spells={'WIZARD_MIRROR_IMAGE'},globals={'BGXU010':1,'BGXU014':1}))
 def test_critical_emergency_can_interrupt_manual_order_explicitly(self):
  act=decide(queue_empty=False,hp=38,enemy_visible=True,distance=3,ranged=True,globals={'BGXU010':1,'BGXU014':1})
  self.assertIn('RunAwayFromNoLeaveArea',act)
 def test_survival_respects_vanilla_no_retreat_switch(self):
  for key in ['bd_ai_no_retreat','bd_no_retreat','BDAI_DISABLE_DEFENSIVE']:
   glob={'BGXU010':1,'BGXU014':1,key:1}
   self.assertNotIn('RunAwayFrom',str(decide(queue_empty=False,hp=24,enemy_visible=True,distance=3,globals=glob)),key)
 def test_survival_three_limited_attempts(self):
  for budget in range(4):
   glob={'BGXU010':1,'BGXU014':1,'BGXUE14':budget}
   action=decide(queue_empty=False,hp=35,enemy_visible=True,distance=4,globals=glob)
   if budget<3:self.assertIn('RunAwayFromNoLeaveArea',action)
   else:self.assertNotIn('RunAwayFrom',str(action))
 def test_survival_cooldown_stops_rapid_repeat(self):
  glob={'BGXU010':1,'BGXU014':1,'BGXUE14':1}
  action=decide(queue_empty=False,hp=22,enemy_visible=True,distance=4,globals=glob,unexpired={'BGXURW14'})
  self.assertNotIn('RunAwayFrom',str(action))
 def test_survival_does_not_leave_area_or_auto_reengage(self):
  glob={'BGXU010':1,'BGXU014':1,'BGXUE14':3}
  for ranged in [False,True]:
   self.assertNotIn('AttackOneRound',str(decide(hp=24,enemy_visible=True,distance=3,ranged=ranged,globals=glob)))
  self.assertNotIn('AttackOneRound',str(decide(hp=90,enemy_visible=True,distance=3,ranged=True,globals={'BGXU010':1,'BGXU014':1},unexpired={'BGXUPOST14'})))
 def test_pressure_escape_only_after_real_damage_at_moderate_hp(self):
  glob={'BGXU010':1,'BGXU014':1}
  self.assertIn('RunAwayFromNoLeaveArea', decide(queue_empty=False,hp=70,enemy_visible=True,distance=4,took_damage=True,ranged=True,globals=glob))
  self.assertNotIn('RunAwayFrom',str(decide(queue_empty=False,hp=70,enemy_visible=True,distance=4,took_damage=False,ranged=True,globals=glob)))
 def test_reset_budget_only_safe_and_healed(self):
  glob={'BGXU010':1,'BGXU014':1,'BGXUE14':3}
  self.assertIn('Continue()',decide(hp=95,enemy_visible=False,globals=glob))
  self.assertNotIn('Continue()',str(decide(hp=70,enemy_visible=False,globals=glob)))
 def test_initial_banner_once(self):
  self.assertIn('DisplayStringHead',decide())
  self.assertIn('DisplayStringHead', decide(globals={'BGXU010':1}))
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1}))
 def test_self_heal_priority_when_not_under_attack(self):
  self.assertIn('CLERIC_CURE_MEDIUM_WOUNDS',decide(globals={'BGXU010':1,'BGXU014':1},hp=32,spells={'CLERIC_CURE_MEDIUM_WOUNDS'},enemy_visible=False))
 def test_self_heal_refused_under_immediate_pressure(self):
  self.assertNotIn('CLERIC_CURE_MEDIUM_WOUNDS',str(decide(globals={'BGXU010':1,'BGXU014':1},hp=25,spells={'CLERIC_CURE_MEDIUM_WOUNDS'},enemy_visible=True,distance=3)))
 def test_caster_defensive_spell_if_actual_slot(self):
  self.assertIn('WIZARD_MIRROR_IMAGE',decide(globals={'BGXU010':1,'BGXU014':1},hp=65,spells={'WIZARD_MIRROR_IMAGE'},enemy_visible=True,distance=10))
 def test_no_automatic_offensive_spells_without_optin(self):
  self.assertNotIn('WIZARD_BLINDNESS',str(decide(globals={'BGXU010':1,'BGXU014':1},hp=60,spells={'WIZARD_BLINDNESS'},enemy_visible=True,distance=10,ranged=True)))
 def test_explicit_control_permission(self):
  self.assertIn('WIZARD_BLINDNESS',decide(globals={'BGXU010':1,'BGXU014':1,'BGXUCTRL':1},hp=75,spells={'WIZARD_BLINDNESS'},enemy_visible=True,distance=10))
 def test_disable_offensive_in_legacy_switch(self):
  self.assertNotIn('WIZARD_BLINDNESS',str(decide(globals={'BGXU010':1,'BGXU014':1,'BGXUCTRL':1,'BDAI_DISABLE_OFFENSIVE':1},hp=75,spells={'WIZARD_BLINDNESS'},enemy_visible=True,distance=10)))
 def test_magic_missile_optin(self):
  self.assertIn('WIZARD_MAGIC_MISSILE',decide(globals={'BGXU010':1,'BGXU014':1,'BGXUDMG':1},hp=65,spells={'WIZARD_MAGIC_MISSILE'},enemy_visible=True,distance=12))
 def test_detect_safe_idle_skill(self):
  self.assertIn('FindTraps()',decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':1},skills={'TRAPS':65},enemy_visible=False))
 def test_detect_requires_skill(self):
  self.assertNotIn('FindTraps',str(decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':1},skills={'TRAPS':0},enemy_visible=False)))
 def test_stealth_safe_idle_skill(self):
  self.assertIn('Hide()',decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':2},skills={'STEALTH':40}))
 def test_stealth_not_in_combat(self):
  self.assertNotIn('Hide()',str(decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':2},skills={'STEALTH':40},combat=True,enemy_visible=True,distance=4)))
 def test_bard_song_skill_mode(self):
  self.assertIn('BattleSong()',decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':3},bard=True,enemy_visible=True,combat=True,distance=9))
 def test_no_song_for_nonbard(self):
  self.assertNotIn('BattleSong()',str(decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_SKILL_MODE':3},bard=False,enemy_visible=True,combat=True,distance=9)))
 def test_ranged_does_not_chase_invisible(self):
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1},enemy_visible=True,distance=8,invisible=True,ranged=True))
 def test_ranged_attack_in_range(self):
  self.assertIn('AttackOneRound',decide(globals={'BGXU010':1,'BGXU014':1},enemy_visible=True,distance=8,ranged=True))
 def test_ranged_attack_disabled(self):
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1,'BGXUNR':1},enemy_visible=True,distance=8,ranged=True))
 def test_ranged_suppressed_by_melee_only_legacy_mode(self):
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_ATTACK_MODE':1},enemy_visible=True,distance=8,ranged=True))
 def test_melee_attack_adjacent(self):
  self.assertIn('AttackOneRound',decide(globals={'BGXU010':1,'BGXU014':1},enemy_visible=True,distance=3,ranged=False))
 def test_melee_does_not_charge_far_enemy(self):
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1},enemy_visible=True,distance=10,ranged=False))
 def test_melee_disabled_independently(self):
  self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1,'BGXUNM':1},enemy_visible=True,distance=3,ranged=False))
 def test_global_attack_off_suppresses_both(self):
  for ranged in [True,False]:
   self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1,'BDAI_DISABLE_ATTACK':1},enemy_visible=True,distance=3,ranged=ranged))
 def test_attack_cannot_break_stealth(self):
  for ranged in [True,False]:
   self.assertIsNone(decide(globals={'BGXU010':1,'BGXU014':1},enemy_visible=True,distance=3,ranged=ranged,invisible=True))
 def test_spacing_when_bow_enemy_inside_four_foot_buffer(self):
  result=decide(globals={'BGXU010':1,'BGXU014':1},hp=100,enemy_visible=True,distance=3,ranged=True)
  self.assertIn('RunAwayFromNoLeaveArea',result)
  self.assertIn(',12)',result)
 def test_spacing_avoided_at_safe_distance(self):
  result=decide(globals={'BGXU010':1,'BGXU014':1},hp=100,enemy_visible=True,distance=8,ranged=True)
  self.assertIn('AttackOneRound',result)
 def test_spacing_respects_manual_queue(self):
  result=decide(queue_empty=False,globals={'BGXU010':1,'BGXU014':1},hp=100,enemy_visible=True,distance=3,ranged=True)
  self.assertIsNone(result)
 def test_spacing_respects_legacy_optout(self):
  result=decide(globals={'BGXU010':1,'BGXU014':1,'bd_ai_no_retreat':1},hp=100,enemy_visible=True,distance=3,ranged=True)
  self.assertNotIn('RunAwayFromNoLeaveArea',str(result))
 def test_spacing_limit_two_steps(self):
  result=decide(globals={'BGXU010':1,'BGXU014':1,'BGXUSP14':2},hp=100,enemy_visible=True,distance=3,ranged=True)
  self.assertNotIn('RunAwayFromNoLeaveArea',str(result))
 def test_emergency_still_saves_melee_wounded(self):
  result=decide(globals={'BGXU010':1,'BGXU014':1},hp=45,enemy_visible=True,distance=4,ranged=False)
  self.assertIn('RunAwayFromNoLeaveArea',str(result))
 def test_short_steps_are_ai_update_ticks_not_feet(self):
  all_steps=re.findall(r'RunAwayFromNoLeaveArea\(NearestEnemyOf\(Myself\),(\d+)\)',BAF)
  self.assertEqual(len(all_steps),6)
  self.assertTrue(all(0<int(x)<=24 for x in all_steps))
 def test_seeded_random_invariants_2000(self):
  rng=random.Random(20261103)
  pool=['CLERIC_CURE_MEDIUM_WOUNDS','CLERIC_CURE_LIGHT_WOUNDS','WIZARD_MIRROR_IMAGE','WIZARD_BLINDNESS','WIZARD_MAGIC_MISSILE']
  for _ in range(2000):
   spell=set(x for x in pool if rng.randrange(2))
   visible=bool(rng.randrange(2));invisible=bool(rng.randrange(2));queue_empty=bool(rng.randrange(2))
   glob={'BGXU010':1,'BGXU014':1,'BGXUCTRL':rng.randrange(2),'BGXUDMG':rng.randrange(2),'BDAI_DISABLE_ATTACK':rng.randrange(2),'BDAI_DISABLE_DEFENSIVE':rng.randrange(2),'BDAI_DISABLE_OFFENSIVE':rng.randrange(2),'BDAI_DISABLE_SPECIAL':rng.randrange(2),'BDAI_SKILL_MODE':rng.randrange(4),'BGXUNR':rng.randrange(2),'BGXUNM':rng.randrange(2)}
   s={'queue_empty':queue_empty,'took_damage':bool(rng.randrange(2)),'hp':rng.randint(1,100),'enemy_visible':visible,'distance':rng.randint(1,30),'combat':bool(rng.randrange(2)),'invisible':invisible,'spells':spell,'skills':{'TRAPS':rng.randint(0,100),'STEALTH':rng.randint(0,100)},'ranged':bool(rng.randrange(2)),'bard':bool(rng.randrange(2)),'globals':glob}
   a=decide(**s)
   if not queue_empty:
    if a is not None:
     self.assertTrue(a.startswith('RunAwayFromNoLeaveArea'),a)
     self.assertTrue(s['hp']<56 or (s['hp']<76 and s['took_damage']))
     self.assertTrue(visible)
     self.assertLessEqual(s['distance'],8)
   if a and a.startswith('Spell('):
    used=a.rsplit(',',1)[-1].rstrip(')')
    self.assertIn(used,spell)
    if used=='WIZARD_BLINDNESS':self.assertEqual(glob['BGXUCTRL'],1)
    if used=='WIZARD_MAGIC_MISSILE':self.assertEqual(glob['BGXUDMG'],1)
   if a and a.startswith('AttackOneRound'):
    self.assertGreater(s['hp'],55)
    self.assertTrue(visible and not invisible)
    self.assertEqual(glob['BDAI_DISABLE_ATTACK'],0)
 def test_multiclass_combines_spell_and_weapon_when_available(self):
  globals={'BGXU010':1,'BGXU014':1}
  spell={'WIZARD_MIRROR_IMAGE'}
  # Same actor may cast defense and, while on cooldown, attack with a bow.
  self.assertIn('WIZARD_MIRROR_IMAGE', decide(globals=globals,hp=60,spells=spell,enemy_visible=True,distance=10,ranged=True,skills={'STEALTH':60,'TRAPS':70}))
  self.assertIn('AttackOneRound', decide(globals=globals,hp=60,spells=spell,enemy_visible=True,distance=10,ranged=True,skills={'STEALTH':60,'TRAPS':70},unexpired={'BGXUMI01'}))
 def test_protection_spell_timer(self):
  self.assertNotIn('WIZARD_MIRROR_IMAGE',str(decide(globals={'BGXU010':1,'BGXU014':1},hp=65,spells={'WIZARD_MIRROR_IMAGE'},enemy_visible=True,distance=10,unexpired={'BGXUMI01'})))
 def test_fail_closed_unknown_class_spells(self):
  self.assertNotIn('Spell(',str(decide(globals={'BGXU010':1,'BGXU014':1,'BGXUCTRL':1,'BGXUDMG':1},hp=45,enemy_visible=True,distance=10,spells=set())))

if __name__=='__main__':unittest.main(verbosity=2)
