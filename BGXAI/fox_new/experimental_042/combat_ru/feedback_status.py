#!/usr/bin/env python3
"""Read-only inspection of EET Lua feedback settings; zero game file modifications."""
from __future__ import annotations
import argparse
from pathlib import Path
import re

EXTRA_COMBAT = re.compile(r'''SetPrivateProfileString\(\s*['"]Game Options['"]\s*,\s*['"]Extra Combat Info['"]\s*,\s*['"]([01])['"]\s*\)''', re.I)

def parse(text: str):
    found=EXTRA_COMBAT.findall(text)
    return found[-1] if found else None

def main():
    p=argparse.ArgumentParser(description='BGXAI combat feedback status (read-only)')
    p.add_argument('--baldur-lua',required=True,type=Path)
    a=p.parse_args()
    data=a.baldur_lua.read_text(encoding='utf-8-sig',errors='replace')
    setting=parse(data)
    print('Расширенные данные бросков (Extra Combat Info):',
          'ВКЛ' if setting=='1' else 'ВЫКЛ' if setting=='0' else 'не найдено в этой конфигурации')
    print('Только чтение; игра и настройки не изменены.')
    print('Путь в меню: Настройки → Игровой процесс → Обратная связь → Сообщения → Show extra combat info.')
    print('Обычные броски включаются рядом в опции «Броски попадания»/«To-hit rolls».')
    print('Перевод настоящих строк журнала требует проверки происхождения полей, не меняйте dialog.tlk.')

if __name__=='__main__':main()
