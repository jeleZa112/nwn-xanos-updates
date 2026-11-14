import unittest
from pathlib import Path
from audit_live_081 import analyze,Refused,digest,PIN_LUA_066S,PIN_BCS_066S,SENTINELS
ROOT=Path(__file__).parent
PRIVATE=Path('/mnt/data/BGXAI081_inputs/M_BX43_066S_CASTER_CANDIDATE.lua')
class Contract(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.lua=PRIVATE.read_bytes() if PRIVATE.exists() else b''
  def test_fixture_pinned(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    self.assertEqual(digest(self.lua),PIN_LUA_066S)
  def test_pinned_source_pass(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    result=analyze(self.lua)
    self.assertEqual(result['status'],'READ_ONLY_066S_LUA_ACTION_CONTRACT_CONFIRMED')
  def test_unverified_flags(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    x=analyze(self.lua)
    self.assertFalse(x['manual_command_origin_proven'])
    self.assertFalse(x['eps_action_queue_empty_proven'])
    self.assertFalse(x['can_authorize_080_in_game'])
  def test_writes_are_not_hidden(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    self.assertTrue(analyze(self.lua)['source_issues_local_requests'])
  def test_unknown_lua_refused(self):
    with self.assertRaisesRegex(Refused,'LUA_SHA_MISMATCH'):analyze(b'other')
  def test_real_historical_bcs_refused(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    old=Path('/mnt/data/bg074_inputs/BDDEFAI_EPS18_4_BGXAI041_LIVE_20261108.BCS')
    if not old.exists():self.skipTest('private historic BCS absent')
    with self.assertRaisesRegex(Refused,'BCS_SHA_MISMATCH'):analyze(self.lua,old.read_bytes())
  def test_lua_modified_refused(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    with self.assertRaisesRegex(Refused,'LUA_SHA_MISMATCH'):analyze(self.lua+b' ')
  def test_sentinels_present(self):
    self.assertGreaterEqual(len(SENTINELS),10)
  def test_source_observer_has_no_engine_writes(self):
    s=(ROOT/'BGXAI081_ACTION_PROVENANCE_READONLY.lua').read_text()
    for bad in ('setLocalInt','ClearActions','AttackReevaluate','ProtectObject','Spell(','AddSpriteStartedActionListener','AddBlockWeaponHitListener','os.','io.'):
      self.assertNotIn(bad,s)
  def test_standalone_analyzer_has_no_game_write_code(self):
    s=(ROOT/'audit_live_081.py').read_text()
    for bad in ('write_bytes(', 'write_text(', '.open("w', ".open('w", 'os.system('):
      self.assertNotIn(bad,s)
    for import_line in ('import subprocess', 'import urllib', 'import requests', 'import shutil', 'from subprocess', 'from urllib'):
      self.assertNotIn('\n'+import_line,s)
  def test_source_pins_form(self):
    self.assertEqual(len(PIN_LUA_066S),64)
    self.assertEqual(len(PIN_BCS_066S),64)
  def test_no_action_owner_guesses(self):
    s=(ROOT/'BGXAI081_ACTION_PROVENANCE_READONLY.lua').read_text()
    self.assertIn("action_origin='UNKNOWN'",s)
    self.assertIn('manual_command_verified=false',s)
    self.assertIn('queue_empty=nil',s)
  def test_documented_nonproof(self):
    if not PRIVATE.exists():self.skipTest('private fixture absent')
    x=analyze(self.lua)
    self.assertFalse(x['started_action_implies_queue_empty'])
    self.assertIsNone(x['bcs_sha256'])
if __name__=='__main__':unittest.main()
