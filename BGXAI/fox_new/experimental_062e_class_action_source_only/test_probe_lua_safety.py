import pathlib,re,unittest
SRC=pathlib.Path(__file__).with_name('BGX62E_CLASS_ACTION_PROBE.lua').read_text(encoding='utf-8')
class SourceAudit(unittest.TestCase):
    def test_no_engine_mutation(self):
        for pattern in ('setLocalInt\\s*\\(', 'ClearActions\\s*\\(', 'ActionOverride\\s*\\(',
                        'Attack\\s*\\(', 'MoveToObject\\s*\\(', 'SetGlobal\\s*\\(',
                        'EEex_Write', 'io\\.', 'os\\.', 'require\\s*\\('):
            self.assertIsNone(re.search(pattern,SRC),pattern)
    def test_no_registration(self):
        for token in ('onWeaponHit','AddListener','EEex_Opcode_Add','EEex_Projectile_Add'):
            self.assertNotIn(token,SRC)
    def test_x64_class_binding(self):self.assertIn('obj.m_typeAI.m_Class',SRC)
    def test_action_field(self):self.assertIn('obj.m_curAction.m_actionID',SRC)
    def test_bounds(self):self.assertIn('for i = 0, 5 do',SRC)
    def test_no_claim_equipment(self):self.assertIn("equipped_weapon = 'unknown'",SRC)
    def test_no_claim_queue(self):self.assertIn("action_queue_idle = 'unknown'",SRC)
    def test_no_auto_work(self):self.assertIn('return {snapshot = snapshot}',SRC)
    def test_provenance(self):self.assertIn('X64_EEEX_SOURCE_DOCUMENTED_RUNTIME_UNVERIFIED',SRC)
if __name__=='__main__':unittest.main()
