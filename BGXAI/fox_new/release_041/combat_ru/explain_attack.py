"""AD&D 2e d20 hit calculator / Russian explainer.

Standalone math helper only. Does not alter engine/UI/TLK or assume all hidden
engine-side combat modifiers have been captured by the caller.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class AttackResult:
    roll: int
    modifier: int
    thac0: int
    target_ac: int
    total: int
    required: int
    hit: bool
    reason: str


def evaluate_attack(roll: int, modifier: int, thac0: int, target_ac: int) -> AttackResult:
    if isinstance(roll,bool) or not isinstance(roll,int) or not (1<=roll<=20):
        raise ValueError('d20 roll must be an integer 1..20')
    if any(isinstance(x,bool) or not isinstance(x,int) for x in (modifier,thac0,target_ac)):
        raise ValueError('attack modifier, THAC0 and AC must be integers')
    total=roll+modifier
    required=thac0-target_ac
    if roll==1:
        hit=False;reason='Натуральная 1: автоматический промах.'
    elif roll==20:
        hit=True;reason='Натуральная 20: автоматическое попадание.'
    elif total>=required:
        hit=True;reason='Итог броска не меньше требуемого значения.'
    else:
        hit=False;reason='Итог броска меньше требуемого значения.'
    return AttackResult(roll,modifier,thac0,target_ac,total,required,hit,reason)


def explain_attack(roll:int,modifier:int,thac0:int,target_ac:int) -> str:
    v=evaluate_attack(roll,modifier,thac0,target_ac)
    return '\n'.join((
        f'Бросок атаки: d20 = {v.roll}; суммарный модификатор попадания = {v.modifier:+d}.',
        f'Итог попадания: {v.roll} {v.modifier:+d} = {v.total}.',
        f'Требуется: THAC0 ({v.thac0}) − КД цели ({v.target_ac}) = {v.required}.',
        f'Результат: {"ПОПАДАНИЕ" if v.hit else "ПРОМАХ"}. {v.reason}',
        'Это проверка попадания, НЕ бросок урона; особые защиты и модификации игры могут менять итог.',
    ))
