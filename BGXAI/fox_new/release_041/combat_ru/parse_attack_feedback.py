"""Read-only translator for the documented BGEE  d20 + modifier = total : Hit/Miss format.

No UI hooks, game read/write, TLK changes, or hidden-information assumptions.
Optional THAC0/AC must come from the same attack context; these values are NOT
embedded in the standard combat feedback string.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import re
from explain_attack import evaluate_attack

# Documented format: Actor: 12 + 3 = 15 : Hit. Game-localized labels vary.
ATTACK=re.compile(r'''^\s*(?P<actor>[^:\r\n]+):\s*
(?P<roll>\d{1,2})\s*(?P<sign>[+\-])\s*(?P<bonus>\d{1,3})\s*=\s*
(?P<total>-?\d+)\s*:\s*(?P<outcome>Hit|Miss|Critical\s+Hit|Critical\s+Miss|Попадание|Промах|Критическое\s+попадание|Критический\s+промах)\s*$''',re.I|re.X)
LABELS={
 'Roll':'Бросок', 'DamageMod':'Модификатор урона',
 'Base THAC0':'Базовый THAC0', 'To Hit':'Бонус попадания',
 'Ability Bonuses':'Бонус характеристики',
 'Missile Adjustment':'Поправка дальнего боя',
 'Off Hand THAC0':'THAC0 второй руки',
 'Strength':'Сила','Dexterity':'Ловкость',
 'Weapon Proficiency':'Владение оружием',
 'Luck':'Удача', 'Damage':'Урон',
}

@dataclass(frozen=True)
class Feedback:
 actor:str
 roll:int
 bonus:int
 total:int
 outcome:str


def parse_attack(line:str)->Feedback|None:
 m=ATTACK.fullmatch(line)
 if not m:return None
 roll=int(m['roll']);bonus=int(m['bonus'])*(1 if m['sign']=='+' else -1)
 if not 1<=roll<=20 or roll+bonus!=int(m['total']):return None
 v=m['outcome'].casefold()
 if v in ('hit','попадание'):label='Попадание'
 elif v in ('miss','промах'):label='Промах'
 elif v in ('critical hit','критическое попадание'):label='Критическое попадание'
 else:label='Критический промах'
 return Feedback(m['actor'],roll,bonus,int(m['total']),label)


def translate_label(label:str)->str:
 return next((ru for en,ru in LABELS.items() if en.casefold()==label.strip().casefold()),label)


def explain_line(line:str,*,thac0:int|None=None,ac:int|None=None)->str:
 f=parse_attack(line)
 if f is None:return 'Не удалось распознать стандартную строку атаки; исходный текст сохранён: '+line
 out=[f'{f.actor}: d20 = {f.roll}; модификатор попадания = {f.bonus:+d}; итог = {f.total}; {f.outcome}.']
 if thac0 is None or ac is None:
  out.append('КД цели и THAC0 здесь не указаны, поэтому точный порог попадания вычислить нельзя.')
 else:
  p=evaluate_attack(f.roll,f.bonus,thac0,ac)
  out.append(f'Если THAC0 = {thac0} и КД цели = {ac}, нужно {p.required}; {p.reason}')
  out.append('Это условный расчёт: учтите особенности движка, удары по невидимым и разные КД по типам урона.')
 out.append('Бросок атаки не равен броску урона.')
 return '\n'.join(out)


def main():
 ap=argparse.ArgumentParser(description='Объяснить бросок BGEE по стандартной строке журнала (без изменения игры)')
 ap.add_argument('line',help='Строка журнала с атакой')
 ap.add_argument('--thac0',type=int)
 ap.add_argument('--ac',type=int)
 args=ap.parse_args()
 print(explain_line(args.line,thac0=args.thac0,ac=args.ac))

if __name__=='__main__':main()
