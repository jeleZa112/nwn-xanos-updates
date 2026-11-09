import pathlib,re,unittest
SRC=pathlib.Path(__file__).resolve().parents[1]/'M_BX43.lua'
class LuaSafety(unittest.TestCase):
 def setUp(self): self.s=SRC.read_text(encoding='utf-8')
 def test_hook(self): self.assertIn('EEex_Sprite_AddBlockWeaponHitListener',self.s)
 def test_context(self):
  for f in ('context.attackingSprite','context.targetSprite','attacker.m_id','victim.m_id'):self.assertIn(f,self.s)
 def test_no_actions(self):
  for bad in ('QueueResponse(', 'ClearActions(', 'ActionOverride(', 'SetGlobal(', 'io.open(', 'os.execute('):self.assertNotIn(bad,self.s)
 def test_no_weapon_blocking(self):
  block=self.s.split('function P.onWeaponHit(context)')[1].split('function P.snapshot()')[0]
  self.assertIn('return false -- CRITICAL',block)
  self.assertNotRegex(block,r'\breturn\s+true\b')
 def test_party_filter(self):
  for x in ('party[actorID]','party[targetID]','not_party_victim','party_actor'):self.assertIn(x,self.s)
 def test_snapshot(self):
  for x in ('weapon_hit_calls = P.weaponHitCalls','weapon_hit_registered = P.weaponHitRegistered','last_weapon_hit ='):self.assertIn(x,self.s)
 def test_status(self):self.assertIn('0.3.19-048-CONFIRMED-HIT',self.s)
 def test_resref(self):self.assertLessEqual(len(SRC.stem),8)
 def test_old_observer_remains(self):
  for x in ('EEex_Action_AddSpriteStartedActionListener', 'target_unresolved','m_acteeID2.m_Instance'):
   self.assertIn(x,self.s)
if __name__=='__main__':unittest.main()
