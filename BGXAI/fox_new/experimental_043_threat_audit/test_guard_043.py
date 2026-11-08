"""042B-to-043 threat-priority structural tests. No game writes."""
from __future__ import annotations
from pathlib import Path
import unittest, tempfile, os
from audit_guard_043 import analyze

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('BGXAI_043_BASELINE_BCS',str(ROOT.parent/'BDDEFAI.BCS')))
RELEASE=Path(os.environ.get('BGXAI_043_042B_SOURCE',str(ROOT.parent/'BGXAI_042B_REVIEW')))

class TestGuard043Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.r=analyze(SOURCE,RELEASE)
    def test_identity(self): self.assertEqual(self.r['installed_042b_sha256'],'8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0')
    def test_all_guard(self):self.assertEqual(self.r['guard_rule_count'],11)
    def test_positions(self):self.assertEqual(self.r['guard_positions'],list(range(1032,1043)))
    def test_hero(self):self.assertEqual(self.r['rules'][0]['target'],'Player1')
    def test_hero_cooldown(self):self.assertEqual(self.r['rules'][0]['cooldown_seconds'],6)
    def test_hero_range(self):self.assertEqual(self.r['rules'][0]['range_predicates'],[10,8])
    def test_critical_hp(self):self.assertTrue(all(x['hp_below_65_priority'] for x in self.r['rules'][1:6]))
    def test_critical_target_order(self):self.assertEqual([x['target'] for x in self.r['rules'][1:6]],['Player3','Player4','Player5','Player6','Player2'])
    def test_fallback_hp(self):self.assertFalse(any(x['hp_below_65_priority'] for x in self.r['rules'][6:]))
    def test_fallback_order(self):self.assertEqual([x['target'] for x in self.r['rules'][6:]],['Player3','Player4','Player5','Player6','Player2'])
    def test_team_cooldown(self):self.assertTrue(all(x['cooldown_seconds']==8 for x in self.r['rules'][1:]))
    def test_team_range(self):self.assertTrue(all(x['range_predicates']==[10,7] for x in self.r['rules'][1:]))
    def test_idle_all(self):self.assertTrue(self.r['uses_idle_gate_all'])
    def test_guard_only(self):self.assertTrue(all(x['action_ids']==[115,87] for x in self.r['rules']))
    def test_no_help(self):self.assertFalse(self.r['explicit_attackedby_or_help_in_guard'])
    def test_no_bad_input(self):
        raw=bytearray(SOURCE.read_bytes());raw[499]^=1
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.BCS';p.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'SHA256'):analyze(p,RELEASE)

if __name__=='__main__':unittest.main()
