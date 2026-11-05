#!/usr/bin/env python3
"""Offline event-priority emulator + IDS validation, not a WeiDU or engine test."""
import hashlib, re, json, random, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/'BGXUNI/BGXUN1.BAF').read_text()
TP=(ROOT/'BGXUNI/setup-BGXUNI.tp2').read_text()
SNAP=json.loads((ROOT/'tests/ids_snapshot.json').read_text())
def ids(k): return set(SNAP['files'][k]['symbols'])
ACTIONS=ids('actions');TRIGGERS=ids('triggers');SPELLS=ids('spells')
BLOCKS=[]
for chunk in re.split(r'(?m)^IF\s*$',B)[1:]:
 before,after=chunk.split('THEN\n',1)
 _,after=after.split('RESPONSE #100\n',1)
 statements=after.split('END')[0]
 BLOCKS.append(([x.strip() for x in before.splitlines() if x.strip()],[x.strip() for x in statements.splitlines() if x.strip()]))
def condition(raw,state):
 invert=raw.startswith('!');raw=raw.lstrip('!')
 m=re.match(r'(\w+)\((.*)\)$',raw)
 assert m,raw
 name,body=m.groups();ps=[x.strip() for x in body.split(',')]
 if name=='ActionListEmpty':v=state.get('idle',True)
 elif name=='Global':v=state.get('globals',{}).get(ps[0].strip('"'),0)==int(ps[2])
 elif name=='GlobalTimerNotExpired':v=ps[0].strip('"') in state.get('timers',set())
 elif name=='HPPercentLT':v=state.get('hp',100)<int(ps[1])
 elif name=='HPPercentGT':v=state.get('hp',100)>int(ps[1])
 elif name=='TookDamage':v=state.get('hit',False)
 elif name=='See':v=state.get('visible',False)
 elif name=='Range':v=state.get('visible',False) and state.get('distance',99)<=int(ps[1])
 elif name=='HaveSpell':v=ps[0] in state.get('spells',set())
 elif name=='CheckStatGT':v=state.get('skills',{}).get(ps[2],0)>int(ps[1])
 elif name=='StateCheck':v=state.get('invisible',False)
 elif name=='ActuallyInCombat':v=state.get('combat',False)
 elif name=='ModalState':v=state.get('modal','')==ps[0]
 elif name=='Class':v=state.get('bard',False)
 elif name=='IsWeaponRanged':v=state.get('ranged',False)
 else:raise ValueError('Unknown trigger '+name)
 return (not v) if invert else v
def decision(**state):
 for conditions,actions in BLOCKS:
  if all(condition(x,state) for x in conditions):
   primary=next((x for x in actions if x.startswith(('RunAwayFrom','AttackOneRound','Spell(','FindTraps(','Hide(','BattleSong('))),actions[-1])
   return primary,actions
 return None,[]
def state(**extra):
 d=dict(idle=True,hp=100,visible=True,distance=5,ranged=True,globals={'BGXU010':1,'BGXU014':1,'BGXU015':1,'BGXU016':1},timers=set())
 d.update(extra)
 return d
class TestNoIdle(unittest.TestCase):
 def test_ids_complete(self):
  self.assertEqual(len(BLOCKS),17)
  for c,a in BLOCKS:
   for t in c:self.assertIn(t.lstrip('!').split('(')[0],TRIGGERS)
   for x in a:self.assertIn(x.split('(')[0],ACTIONS)
 def test_spells_in_known_eet(self):
  for x in re.findall(r'\b(?:CLERIC|WIZARD)_[A-Z_]+\b',B):self.assertIn(x,SPELLS)
 def test_only_owned_files(self):
  self.assertIn('COMPILE ~BGXUNI/BGXUN1.BAF~',TP)
  self.assertIn('~scripts/BGXUN1.BS~',TP)
  for p in ('BDDEFAI','BGXGRP','BGXTANK'):self.assertNotIn('COPY ~override/'+p,TP)
 def test_blocks_balance(self):
  self.assertEqual(len(re.findall(r'(?m)^END\s*$',B)),17)
 def test_new_marker(self):
  self.assertIn('V016 NO-IDLE READY',B)
  self.assertIn('V016',str(decision(**state(globals={'BGXU010':1,'BGXU014':1,'BGXU015':1}))[1]))
 def test_kite_when_clear_and_close(self):
  d,_=decision(**state(distance=5))
  self.assertEqual(d,'RunAwayFromNoLeaveArea(NearestEnemyOf(Myself),45)')
 def test_close_attack_during_kite_cooldown(self):
  for d in (1,4,6,8):
   act,_=decision(**state(distance=d,timers={'BGXUKW16'}))
   self.assertTrue(act.startswith('AttackOneRound('),act)
 def test_close_fire_when_optout_retreat(self):
  act,_=decision(**state(globals={**state()['globals'],'bd_ai_no_retreat':1},distance=4))
  self.assertTrue(act.startswith('AttackOneRound('),act)
 def test_close_fire_after_first_message(self):
  gl={**state()['globals'],'BGXUF016':1}
  act,_=decision(**state(globals=gl,timers={'BGXUKW16'},distance=5))
  self.assertIn('AttackOneRound',act)
 def test_continuous_kite_after_old_exhausted_budget(self):
  gl={**state()['globals'],'BGXUSP15':3,'BGXUE15':3,'BGXUHOLD15':1}
  act,_=decision(**state(globals=gl,distance=4))
  self.assertTrue(act.startswith('RunAwayFromNoLeaveArea'),act)
 def test_healthy_long_range_shoots(self):
  for dist in (9,12,18):
   act,_=decision(**state(distance=dist))
   self.assertIn('AttackOneRound',act)
 def test_not_attack_distant_target(self):
  a,_=decision(**state(distance=23));self.assertIsNone(a)
 def test_manual_queue_remains(self):
  a,_=decision(**state(idle=False,distance=3));self.assertIsNone(a)
 def test_survival_critical_retreat(self):
  for d in (1,5,8):
   a,_=decision(**state(hp=40,distance=d,idle=False))
   self.assertIn('RunAwayFromNoLeaveArea(NearestEnemyOf(Myself),75)',a)
 def test_critical_retreat_rearms(self):
  a,_=decision(**state(hp=25,distance=3,globals={**state()['globals'],'BGXUE15':3}))
  self.assertIn('RunAwayFromNoLeaveArea',a)
 def test_critical_timer_limits_reissue(self):
  a,_=decision(**state(hp=25,distance=3,timers={'BGXUER16'}))
  self.assertNotIn('RunAwayFromNoLeaveArea',str(a))
 def test_new_damage_retreat(self):
  a,_=decision(**state(hp=65,distance=3,hit=True))
  self.assertIn('RunAwayFromNoLeaveArea(NearestEnemyOf(Myself),60)',a)
 def test_no_damage_no_pressure_evade(self):
  a,_=decision(**state(hp=65,distance=3,hit=False));self.assertIn('RunAwayFromNoLeaveArea',a) # normal spacing
 def test_retreat_disallowed_but_shoot(self):
  gl={**state()['globals'],'bd_no_retreat':1}
  a,_=decision(**state(hp=80,distance=2,globals=gl));self.assertIn('AttackOneRound',a)
 def test_respect_disable_attack(self):
  gl={**state()['globals'],'BDAI_DISABLE_ATTACK':1}
  a,_=decision(**state(hp=90,distance=3,globals=gl));self.assertNotIn('AttackOneRound',str(a));self.assertNotIn('RunAwayFrom',str(a))
 def test_ranged_optout_kite(self):
  gl={**state()['globals'],'BGXUNR':1}
  a,_=decision(**state(hp=90,distance=3,globals=gl));self.assertNotIn('RunAwayFrom',str(a));self.assertNotIn('AttackOneRound',str(a))
 def test_no_movement_when_invisible(self):
  a,_=decision(**state(invisible=True,distance=2));self.assertIsNone(a)
 def test_no_ranged_kite_with_melee_selected(self):
  a,_=decision(**state(ranged=False,distance=3));self.assertIn('AttackOneRound',a)
 def test_divine_healing_does_not_cast_under_melee_pressure(self):
  healBlocks=[cond for cond,acts in BLOCKS if any(x.startswith('Spell(Myself,CLERIC_CURE_') for x in acts)]
  self.assertEqual(len(healBlocks),2)
  for cond in healBlocks:self.assertIn('!Range(NearestEnemyOf(Myself),8)',cond)
 def test_no_spells_when_missing_slots(self):
  a,_=decision(**state(hp=70,distance=12,spells=set()))
  self.assertIn('AttackOneRound',a)
 def test_random_invariants_2000(self):
  rng=random.Random(20261105)
  for _ in range(2000):
   gl={**state()['globals']}
   for k in ('BDAI_DISABLE_ATTACK','BDAI_DISABLE_DEFENSIVE','bd_ai_no_retreat','BGXUNR','BGXUNM'):
    gl[k]=rng.randrange(2)
   d=rng.randint(1,25);hp=rng.randint(1,100);timers={'BGXUKW16'} if rng.randrange(2) else set()
   s=state(globals=gl,distance=d,hp=hp,idle=bool(rng.randrange(2)),ranged=bool(rng.randrange(2)),visible=bool(rng.randrange(2)),invisible=bool(rng.randrange(2)),timers=timers)
   act,_=decision(**s)
   if act and act.startswith('AttackOneRound'):
    self.assertTrue(s['idle'] and s['visible'] and not s['invisible']);self.assertGreater(hp,55)
    self.assertEqual(gl['BDAI_DISABLE_ATTACK'],0)
   if act and act.startswith('RunAwayFrom'):
    self.assertTrue(s['visible'] and d<=8)
    self.assertEqual(gl['bd_ai_no_retreat'],0)
   if hp>55 and s['visible'] and s['ranged'] and s['idle'] and d<=8 and not s['invisible'] and not any(gl.get(k,0) for k in ('BDAI_DISABLE_ATTACK','bd_ai_no_retreat','BGXUNR')) and timers:
    # If no other defense, an archer no longer freezes due to the kite cooldown
    if not gl.get('BDAI_DISABLE_DEFENSIVE',0):
     self.assertIn('AttackOneRound',str(act))
if __name__=='__main__':unittest.main(verbosity=2)
