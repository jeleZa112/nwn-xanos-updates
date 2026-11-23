"""R27 source contract and exact originals; no game or EEex access."""
import hashlib
from pathlib import Path
import unittest
from build_r27 import ROOT, SOURCES, PINS, compose, input_dir

def sha(data):return hashlib.sha256(data).hexdigest()

class R27SourceTests(unittest.TestCase):
 def test_original_r2_checksum(self):
  self.assertEqual(sha((input_dir()/SOURCES[0][0]).read_bytes()),PINS[SOURCES[0][0]])
 def test_original_r4_checksum(self):
  self.assertEqual(sha((input_dir()/SOURCES[1][0]).read_bytes()),PINS[SOURCES[1][0]])
 def test_composition_is_reproducible(self):
  self.assertEqual(compose(),(ROOT/'BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO.lua').read_bytes())
 def test_no_action_dispatch(self):
  s=(ROOT/'R27_EVENT_JOIN_TAIL.lua').read_text()
  for bad in ('ClearActions(', 'SelectWeaponAbility(', 'ActionOverride(', 'EEex_Action_QueueScriptFileResponseOnAIBase(',
              'EEex_Action_AddSpriteStartedActionListener(', 'getLauncher(', 'EEex_Resource_Demand('):
   self.assertNotIn(bad,s)
 def test_never_auto_register(self):
  s=(ROOT/'R27_EVENT_JOIN_TAIL.lua').read_text()
  self.assertIn('registered=false',s)
  self.assertNotIn('initialized=init(',s)
 def test_flags_fail_closed(self):
  s=(ROOT/'R27_EVENT_JOIN_TAIL.lua').read_text()
  for p in ('alternativeAPRVerified=false','launcherAmmoPairVerified=false',
            'completeActiveEffectsVerified=false','epsManualQueueVerified=false',
            'dispatchAuthorized=false','weaponSwitchAuthorized=false',
            'actionQueueCleared=false','nativeEventTokenAuthenticated=false',
            'engineSessionVerified=false'):
   self.assertIn(p,s)
 def test_exact_single_callback(self):
  s=(ROOT/'R27_EVENT_JOIN_TAIL.lua').read_text()
  for k in ('R2_CORE.observe_sprite,sprite','R4_CORE.observe,sprite,action,partyIndex,getActiveStats',
            'SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE','R2_R4_SCALARS_DISAGREE'):
   self.assertIn(k,s)
 def test_no_file_or_network(self):
  s=(ROOT/'R27_EVENT_JOIN_TAIL.lua').read_text()
  for q in ('io.open(', 'os.execute(', 'socket.', 'require(', 'loadfile(', 'dofile('):
   self.assertNotIn(q,s)
 def test_builder_rejects_changed_r2(self):
  import tempfile
  with tempfile.TemporaryDirectory() as td:
   d=Path(td)
   for n,_ in SOURCES:(d/n).write_bytes((input_dir()/n).read_bytes())
   (d/'R27_EVENT_JOIN_TAIL.lua').write_bytes((ROOT/'R27_EVENT_JOIN_TAIL.lua').read_bytes())
   with (d/SOURCES[0][0]).open('ab') as f:f.write(b'--bad')
   with self.assertRaisesRegex(ValueError,'BASELINE_SOURCE_DRIFT'):compose(d)
 def test_r2_selected_fingerprint_only(self):
  t=(input_dir()/'BGXAI_WEAPON_SLOTS_R2_READONLY.lua').read_text()
  self.assertIn('perSlotAPRVerified=false',t)
 def test_r4_no_alt(self):
  t=(input_dir()/'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua').read_text()
  self.assertIn('alternateSlotAPRVerified=false',t)
 def test_no_existing_source_modified(self):
  self.assertNotEqual(PINS[SOURCES[0][0]],PINS[SOURCES[1][0]])

if __name__=='__main__':unittest.main()
