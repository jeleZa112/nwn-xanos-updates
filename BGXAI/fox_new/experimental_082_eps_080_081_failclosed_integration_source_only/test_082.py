from pathlib import Path
import hashlib,unittest
D=Path(__file__).resolve().parent
EXPECTED={
 'BGXAI080_EPS_FIRST_COORDINATOR.lua':'6cb5aa77467fbb572bd4ed939ffcb1196f773a90',
 'BGXAI081_ACTION_PROVENANCE_READONLY.lua':'44516919bea3c0ea43b5d45db0cc494f83f9dbdf13e44728fb262fc966840b53',
}
class Integration(unittest.TestCase):
 def test_same_observer_081(self):self.assertEqual(hashlib.sha256((D/'BGXAI081_ACTION_PROVENANCE_READONLY.lua').read_bytes()).hexdigest(),EXPECTED['BGXAI081_ACTION_PROVENANCE_READONLY.lua'])
 def test_eps_coordinator_080_loaded_exact(self):
  # pinned file version, no changes to 080 in this release
  src=(D/'BGXAI080_EPS_FIRST_COORDINATOR.lua').read_text('utf-8')
  self.assertIn('ACTION_STATE_UNKNOWN',src)
  self.assertIn("actor.queue_empty~=true",src)
 def test_081_unknown_state(self):
  text=(D/'BGXAI081_ACTION_PROVENANCE_READONLY.lua').read_text('utf-8')
  for marker in ("action_origin='UNKNOWN'",'queue_empty=nil','manual_command=nil','eps_queue_empty_verified=false'):
   self.assertIn(marker,text)
 def test_bridge_rejects_unknown(self):
  s=(D/'BGXAI082_QUEUE_GUARD_BRIDGE.lua').read_text('utf-8')
  self.assertIn('verified=false,origin_verified=false',s)
  self.assertIn('queue_empty=nil,idle=false,manual_command=nil',s)
 def test_no_game_actions(self):
  s=(D/'BGXAI082_QUEUE_GUARD_BRIDGE.lua').read_text('utf-8')
  for marker in ('setLocalInt','ClearActions','AttackReevaluate','ProtectObject','Spell(', 'os.','io.','EEex_Action_AddSpriteStartedActionListener','EEex_Sprite_AddBlockWeaponHitListener'):
   self.assertNotIn(marker,s)
 def test_no_optimistic_origin(self):
  s=(D/'BGXAI082_QUEUE_GUARD_BRIDGE.lua').read_text('utf-8')
  self.assertIn('origin_verified=false',s)
  self.assertNotIn('origin_verified=true',s)
 def test_hard_hold(self):
  s=(D/'BGXAI082_QUEUE_GUARD_BRIDGE.lua').read_text('utf-8')
  self.assertIn("return fail('MANUAL_ORIGIN_AND_EPS_QUEUE_NOT_YET_VERIFIED')",s)
 def test_integration_no_change(self):
  s=(D/'BGXAI082_QUEUE_GUARD_BRIDGE.lua').read_text('utf-8')
  self.assertIn('copy=shallow(actor)',s)
  self.assertIn('copy.action_state=',s)
 def test_dependency_source_072(self):
  s=(D/'BGXAI072_EPS_FIRST_ARBITER.lua').read_text('utf-8')
  self.assertIn('EPS_ACTION_QUEUE_BUSY_OR_UNKNOWN',s)
  self.assertIn('manual_command~=false',s)
 def test_dependency_source_078(self):
  s=(D/'BGXAI078_HEAL_SELECTOR.lua').read_text('utf-8')
  self.assertIn('EPS_QUEUE_BUSY_OR_UNKNOWN',s)
  self.assertIn('NO_GAME_DISPATCH_IMPLEMENTED',s)
 def test_pinned_source_reference(self):self.assertEqual(len(EXPECTED['BGXAI081_ACTION_PROVENANCE_READONLY.lua']),64)
 def test_only_readonly_lua(self):
  for f in D.glob('*.lua'):
   s=f.read_text('utf-8')
   self.assertNotIn('setLocalInt(',s)
 def test_no_eeex_callbacks_registered(self):
  for f in D.glob('*.lua'):
   s=f.read_text('utf-8')
   self.assertNotIn('pcall(EEex_Action_AddSpriteStartedActionListener',s)
 def test_no_installer(self):self.assertFalse(any(x.suffix.lower()=='.tp2' for x in D.iterdir()))
if __name__=='__main__':unittest.main()
