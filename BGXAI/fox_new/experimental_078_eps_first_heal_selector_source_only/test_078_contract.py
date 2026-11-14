"""BGXAI 078 source-only safety contract: Python checks, no game installation."""
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'BGXAI078_HEAL_SELECTOR.lua'
TEST = HERE / 'test_078.lua'
PRIVATE = Path('/mnt/data/BGXAI077_evidence')
PINNED = {
 'BGX61_RECEIVER.baf': '94b4beca0d9e470ed0cad566a19038566f626c19d53454d590fd409d294fcd1e',
 'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf': 'c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae',
 'BGX66_CASTER_SUPPORT.lua': 'b365ac770c508e292b87c280c58f922c20306a0b9d3ca68c99b0cd1223872020',
 'M_BX43_066S_CASTER_CANDIDATE.lua': '50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f',
}

class TestSourceSafety(unittest.TestCase):
 def test_no_direct_game_writes(self):
  s=SRC.read_text()
  for name in ['setLocalInt','SetGlobal','SetGlobalTimer', 'AttackReevaluate',
               'ProtectObject','ClearActions','MoveToObject','Spell(',
               'EEex_Action_AddSpriteStartedActionListener',
               'EEex_Sprite_AddBlockWeaponHitListener','os.execute','io.open']:
   with self.subTest(name=name): self.assertNotIn(name, s)
 def test_no_import_or_write(self):
  s=SRC.read_text(); self.assertNotRegex(s,r'\b(require|dofile|loadfile|load)\s*\(')
  self.assertNotRegex(s,r'\b(getLocalInt|EEex_)\b')
 def test_eps_first_explicit(self):
  s=SRC.read_text();self.assertIn('existing_eps_heal_handling~=false',s)
  self.assertIn('c.eps.queue_empty~=true',s)
  self.assertIn('c.eps.manual_command~=false',s)
  self.assertIn('c.eps.heal_pending~=false',s)
 def test_exact_bcs_spell(self):
  self.assertIn("c.spell.bcs_spell_id~='CLERIC_CURE_LIGHT_WOUNDS'",SRC.read_text())
 def test_bcs_range_proven(self):
  self.assertIn('c.target.in_bcs_range_10~=true',SRC.read_text())
 def test_no_class_whitelist(self):
  s=SRC.read_text();self.assertNotIn('FRONTLINE',s);self.assertNotIn('HEALER={[',s)
 def test_f_guard_optin(self):
  s=SRC.read_text();self.assertIn('c.guard_f_on~=true',s)
  self.assertIn('config.opt_in~=true',s)
 def test_no_unbounded_candidate_scan(self):
  self.assertIn("if i>6 then return deny('CANDIDATES_EXCEED_PARTY_SIZE'",SRC.read_text())
 def test_output_no_engine_dispatch(self):
  self.assertIn('orders_sent=0,locals_written=0,engine_dispatch=false',SRC.read_text())
 def test_no_game_root(self):
  for p in [SRC,TEST]:
   self.assertNotIn('C:\\Games',p.read_text())
 def test_exact_077_source_pins_when_available(self):
  if not PRIVATE.exists(): self.skipTest('Private 077 fixtures absent from runtime')
  for name, want in PINNED.items():
   with self.subTest(name=name):
    self.assertEqual(hashlib.sha256((PRIVATE/name).read_bytes()).hexdigest(),want)
 def test_baf_066s_real_gate_present(self):
  if not PRIVATE.exists(): self.skipTest('Private fixture absent')
  s=(PRIVATE/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf').read_text()
  self.assertEqual(len(re.findall(r'HaveSpell\(CLERIC_CURE_LIGHT_WOUNDS\)',s)),6)
  self.assertEqual(len(re.findall(r'Range\(Player\d,10\)',s)),6)
  self.assertEqual(s.count('ActionListEmpty()'),7)
 def test_061_guard_has_action_emptiness(self):
  if not PRIVATE.exists(): self.skipTest('Private fixture absent')
  s=(PRIVATE/'BGX61_RECEIVER.baf').read_text()
  self.assertEqual(s.count('ActionListEmpty()'),18)
 def test_native_lua_mock(self):
  result=subprocess.run(['texlua',TEST.name],cwd=HERE,text=True,capture_output=True,timeout=15,check=False)
  self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
  self.assertIn('BGXAI078_HEAL_SELECTOR_TESTS_PASS 88',result.stdout)

if __name__=='__main__': unittest.main()
