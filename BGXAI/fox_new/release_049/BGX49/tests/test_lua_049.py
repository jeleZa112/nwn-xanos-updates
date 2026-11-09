import pathlib, unittest
S=(pathlib.Path(__file__).resolve().parents[1]/'M_BX43.lua').read_text()
class GuardSignalSourceTests(unittest.TestCase):
 def test_version(self):self.assertIn('0.3.20-049-GUARD-ADVISORY',S)
 def test_engine_listener_retained(self):self.assertIn('EEex_Sprite_AddBlockWeaponHitListener',S)
 def test_real_hit_condition(self):self.assertIn('event.event ~= "NONPARTY_WEAPON_HIT_ON_PARTY"',S)
 def test_fields(self):
  for p in ('attacker_id = event.actor_id','protected_id = event.target_id','source_event_sequence = event.sequence','candidate_party_ids = candidateIDs'):
   self.assertIn(p,S)
 def test_no_guard_state_guess(self):self.assertIn('guard_switch_state = "UNKNOWN"',S)
 def test_no_orders(self):
  for p in ('action_command_sent = false','dispatch_status = "DISABLED_PASSIVE_ONLY"','P.guardDispatchEnabled = false','return false -- CRITICAL'):
   self.assertIn(p,S)
 def test_bounded(self):self.assertIn('if #P.guardSignals > P.maxGuardSignals then',S)
 def test_copies(self):self.assertIn('guard_signals = copyGuardSignals()',S)
 def test_errors_separate(self):self.assertIn('P.guardSignalErrors = P.guardSignalErrors + 1',S)
 def test_no_engine_mutations(self):
  code='\n'.join(l.split('--',1)[0] for l in S.splitlines())
  for bad in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'SetGlobal(', 'os.execute(', 'io.open('):self.assertNotIn(bad,code)
if __name__=='__main__':unittest.main()
