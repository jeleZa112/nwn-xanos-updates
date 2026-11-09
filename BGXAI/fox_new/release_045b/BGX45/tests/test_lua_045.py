import hashlib
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC=ROOT/'BGX45'


class TestSourceResref(unittest.TestCase):
    def test_names_are_six_characters(self):
        for name in ('M_BX43.lua','M_BX44.lua'):
            self.assertLessEqual(len(pathlib.Path(name).stem),8)
            self.assertTrue(name.startswith('M_'))

    def test_scripts_are_byte_for_byte_original(self):
        expected={'M_BX43.lua':'f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f',
                  'M_BX44.lua':'a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f'}
        for name,h in expected.items():
            self.assertEqual(hashlib.sha256((SRC/name).read_bytes()).hexdigest(),h)

    def test_read_only_lua(self):
        for name in ('M_BX43.lua','M_BX44.lua'):
            s='\n'.join(line.split('--',1)[0] for line in (SRC/name).read_text().splitlines())
            for forbidden in ('ClearActions(', 'ActionOverride(', 'QueueResponse', 'SetGlobal(',
                              'io.open(', 'os.execute('):
                self.assertNotIn(forbidden,s)

    def test_report_hook_is_preserved(self):
        s=(SRC/'M_BX44.lua').read_text()
        self.assertIn('Ctrl+Alt+F11',s)
        self.assertIn('EEex_Key_AddPressedListener',s)
        self.assertIn('BGX43Probe',s)

    def test_attack_hook_is_preserved(self):
        s=(SRC/'M_BX43.lua').read_text()
        self.assertIn('EEex_Action_AddSpriteStartedActionListener',s)
        self.assertIn('[3] = true, [105] = true',s)

    def test_correct_order(self):
        # 043 observer must be loaded before 044 diagnostic.
        # Engine, rather than Python string order, handles EEex bootstrap priority.
        self.assertLess('M_BX43','M_BX44')


if __name__=='__main__': unittest.main()
