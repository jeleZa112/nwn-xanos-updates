import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from combat_ru.explain_attack import evaluate_attack,explain_attack

class AttackMath(unittest.TestCase):
 def test_equal_meets_thaco(self):self.assertTrue(evaluate_attack(15,0,20,5).hit)
 def test_below_fails(self):self.assertFalse(evaluate_attack(14,0,20,5).hit)
 def test_bonus_help(self):self.assertTrue(evaluate_attack(12,3,20,5).hit)
 def test_negative_ac(self):self.assertFalse(evaluate_attack(18,0,20,-3).hit)
 def test_natural_one_miss_even_if_bonus_huge(self):self.assertFalse(evaluate_attack(1,100,20,10).hit)
 def test_natural_twenty_hit_even_if_thaco_bad(self):self.assertTrue(evaluate_attack(20,-100,20,-20).hit)
 def test_lower_thaco_better(self):self.assertTrue(evaluate_attack(10,0,15,5).hit)
 def test_higher_ac_easier(self):self.assertTrue(evaluate_attack(10,0,20,10).hit)
 def test_d20_range_check(self):
  for x in [-1,0,21,True]:
   with self.assertRaises(ValueError):evaluate_attack(x,0,20,0)
 def test_output_russian(self):
  s=explain_attack(15,0,20,5)
  self.assertIn('ПОПАДАНИЕ',s)
  self.assertIn('Требуется: THAC0 (20) − КД цели (5) = 15.',s)
  self.assertIn('НЕ бросок урона',s)

if __name__=='__main__':unittest.main()
