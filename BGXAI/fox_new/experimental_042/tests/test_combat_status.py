from pathlib import Path
import importlib.util,unittest
p=Path(__file__).resolve().parents[1]/'combat_ru/feedback_status.py'
spec=importlib.util.spec_from_file_location('fb',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Feedback(unittest.TestCase):
 def test_enabled(self):self.assertEqual(m.parse("SetPrivateProfileString('Game Options','Extra Combat Info','1')"),'1')
 def test_disabled(self):self.assertEqual(m.parse('SetPrivateProfileString("Game Options", "Extra Combat Info", "0")'),'0')
 def test_last_setting(self):self.assertEqual(m.parse("SetPrivateProfileString('Game Options','Extra Combat Info','0')\nSetPrivateProfileString('Game Options','Extra Combat Info','1')"),'1')
 def test_missing(self):self.assertIsNone(m.parse("SetPrivateProfileString('Game Options','Music Volume','1')"))
if __name__=='__main__':unittest.main()
