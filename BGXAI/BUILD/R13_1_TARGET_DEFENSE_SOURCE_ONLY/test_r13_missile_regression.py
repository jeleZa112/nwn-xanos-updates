import unittest,hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent
class MissileRegression(unittest.TestCase):
 def test_both_core_sources_include_missile_once(self):
  for name in ['BGXAI_R13_TARGET_DEFENSE_OBSERVER.lua','M_BGXTDEF13.lua']:
   s=(ROOT/name).read_text();self.assertIn("'m_nResistMissile'",s)
   self.assertEqual(s.count("'m_nResistMissile'"),1)
 def test_installer_pins_exact_updated_source(self):
  b=(ROOT/'M_BGXTDEF13.lua').read_bytes()
  s=(ROOT/'BGXAI_R13_GUARDED.py').read_text()
  self.assertIn(hashlib.sha256(b).hexdigest(),s)
  self.assertNotIn('eb764346f0c523790658320938a2739d873dbbdb59a93479e4f47e1f0edac2f3',s)
 def test_manifest_matches_bytes(self):
  m=json.loads((ROOT/'BGXAI_R13_MANIFEST_V1.json').read_text());self.assertEqual(m['version'],'0.3.85-R13-TARGET-MISSILE-RO')
  for x in m['files']:
   b=(ROOT/x['dest']).read_bytes()
   self.assertEqual(x['size'],len(b));self.assertEqual(x['sha256'],hashlib.sha256(b).hexdigest())
 def test_no_live_orders_or_weapon_switching(self):
  s=(ROOT/'M_BGXTDEF13.lua').read_text()
  for term in ['ClearActions(','SelectWeaponAbility(','SetGlobal(','Attack(','ActionOverride(']:
   self.assertNotIn(term,s)
  self.assertIn('"weaponSwitchAuthorized":false',s)
if __name__=='__main__':unittest.main(verbosity=2)
