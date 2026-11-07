import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'combat_ru'))
from parse_attack_feedback import parse_attack,explain_line,translate_label
class AttackParser041(unittest.TestCase):
 def test_common_hit(self):
  t=parse_attack('Воин: 12 + 3 = 15 : Hit')
  self.assertEqual((t.roll,t.bonus,t.total,t.outcome),(12,3,15,'Попадание'))
 def test_miss_negative(self):
  t=parse_attack('Скелет: 8 - 2 = 6 : Miss')
  self.assertEqual((t.bonus,t.outcome),(-2,'Промах'))
 def test_critical(self):
  self.assertEqual(parse_attack('X: 20 + 0 = 20 : Critical Hit').outcome,'Критическое попадание')
 def test_russian(self):
  self.assertEqual(parse_attack('Бен Кай: 11 + 2 = 13 : Попадание').actor,'Бен Кай')
 def test_reject_wrong_total(self):
  self.assertIsNone(parse_attack('X: 10 + 5 = 16 : Hit'))
 def test_reject_damage_line(self):
  self.assertIsNone(parse_attack('X: Roll: 1 + DamageMod: 2 = 3'))
 def test_reject_impossible_d20(self):
  self.assertIsNone(parse_attack('X: 27 + 2 = 29 : Hit'))
 def test_do_not_invent_ac(self):
  self.assertIn('точный порог попадания вычислить нельзя',explain_line('X: 11 + 2 = 13 : Hit'))
 def test_context_math(self):
  self.assertIn('нужно 13',explain_line('X: 11 + 2 = 13 : Hit',thac0=17,ac=4))
 def test_label(self):
  self.assertEqual(translate_label('DamageMod'),'Модификатор урона')
if __name__=='__main__':unittest.main()
