"""Read-only source guard and native EEex mock for BGXAI 079."""
import hashlib
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MEM=ROOT/'BGXAI079_PRIEST_MEMORY_READONLY.lua'
SEL=ROOT/'BGXAI078_HEAL_SELECTOR.lua'
PIN_078=''
class Contract(unittest.TestCase):
 def test_no_engine_mutation(self):
  s=MEM.read_text()
  for op in ['setLocalInt(', 'SetGlobal(', 'Spell(', 'AttackReevaluate(', 'ProtectObject(',
             'ClearActions(', 'EEex_Action_AddSpriteStartedActionListener(',
             'EEex_Sprite_AddBlockWeaponHitListener(', 'io.open(', 'os.execute(']:
   with self.subTest(op=op):self.assertNotIn(op,s)
 def test_no_runtime_activation(self):
  s=MEM.read_text();self.assertIn('installed=false',s)
  self.assertIn('function M.scan(',s)
  self.assertNotIn('setmetatable',s)
 def test_079_never_claims_castable(self):
  s=MEM.read_text();self.assertIn('castable_now_verified=false,usable_now=nil',s)
 def test_pointer_fail_closed(self):
  s=MEM.read_text();self.assertIn("return unknown('PRIEST_LIST_READ_INCOMPLETE')",s)
 def test_078_shipped_unmodified(self):
  origin=Path('/mnt/data/BGXAI_078_EPS_FIRST_HEAL_SELECTOR_SOURCE_ONLY/BGXAI078_HEAL_SELECTOR.lua')
  if not origin.exists():self.skipTest('original 078 unavailable')
  self.assertEqual(hashlib.sha256(SEL.read_bytes()).hexdigest(),hashlib.sha256(origin.read_bytes()).hexdigest())
 def test_seven_priest_levels(self):
  self.assertIn('for i=0,6 do',MEM.read_text())
 def test_native_eeex_mock(self):
  r=subprocess.run(['texlua','test_079.lua'],cwd=ROOT,text=True,capture_output=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
  self.assertIn('BGXAI079_PRIEST_MEMORY_MOCK_PASS 27',r.stdout)
if __name__=='__main__':unittest.main()
