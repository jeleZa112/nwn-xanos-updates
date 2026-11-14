import pathlib,re,unittest
ROOT=pathlib.Path(__file__).parent
SRC=(ROOT/'BGXAI083_PASSIVE_TRACE.lua').read_text(encoding='utf-8')
class TestSafety(unittest.TestCase):
 def test_no_engine_dispatch(self):
  for token in ('EEex_Action_QueueResponseStringOnAIBase(', ':virtual_InsertAction(', ':setLocalInt(', 'ActionOverride(', 'CreateCreature(', 'SetGlobal(', 'ApplySpell('):
   self.assertNotIn(token,SRC)
 def test_no_hooks_registered(self):
  for token in ('EEex_Action_AddSpriteStartedActionListener(', 'EEex_Sprite_AddBlockWeaponHitListener(', 'EEex_GameState_AddInitializedListener('): self.assertNotIn(token,SRC)
 def test_no_file_write(self):
  for token in ('io.open(', 'os.execute(', 'os.remove(', 'package.loadlib(', 'os.rename(', 'dofile("override'):
   self.assertNotIn(token,SRC)
 def test_zero_idle_not_trusted(self):self.assertIn('current_action_idle_verified=false',SRC)
 def test_manual_not_trusted(self):self.assertIn("action_origin='UNKNOWN'",SRC)
 def test_queue_not_trusted(self):self.assertIn('eps_queue_empty=nil',SRC)
 def test_bounded_ring(self): self.assertIn('max_events>256',SRC);self.assertIn('table.remove(self.history,1)',SRC)
 def test_no_globals(self):self.assertNotRegex(SRC,r'\b_G\s*\[')
 def test_no_install(self):self.assertIn('installed=false',SRC)
 def test_observe_unknown(self):self.assertIn('MANUAL_ORIGIN_AND_EPS_QUEUE_UNVERIFIED',SRC)
if __name__=='__main__':unittest.main()