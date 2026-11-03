# BGXUNI v0.1.1 — исправление реальной ошибки Windows/WeiDU 25100

**Дата:** 03.11.2026. **Проект:** BALDURS_GATE_EET_AI / BGXAI. **Ветка:** `jeleZa112/nwn-xanos-updates`, `bg-eet-ai`.

## Факт первого реального теста v0.1.0

На скриншоте игрока после первого запуска `BGXUNI_SETUP.cmd` WeiDU 25100 вывел `[setup-BGXUNI.exe] unknown option '--tp2'` и справку. **Установка не состоялась**; наличие новых игровых `BGXUN1.BS` или успешной компиляции BAF этим тестом **не доказано**. Это явная ошибка поставленного скрипта установки, а не проблема пользовательской игры.

## Исправление v0.1.1

Существующий `BGXUNI_SETUP.cmd` заменён на исправленный файл с той же ролью и именем. Теперь он:

1. Проверяет `chitin.key`, `BGXUNI/setup-BGXUNI.tp2`, `BGXUNI/BGXUN1.BAF`.
2. Копирует исходный TP2 в корень под официальное имя `setup-BGXUNI.tp2`; если корневой файл уже есть, сравнивает его `fc /b` и **отказывается переписывать несовпадающий**.
3. Вызывает `setup-BGXUNI.exe --yes` **без неподдерживаемого `--tp2`**. Команды `/reinstall` и `/remove` используют `--reinstall` и `--uninstall` соответственно.
4. Не меняет `BDDEFAI`, `BGXGRP`, `BGXTANK`, оригинальный обновлятор BGXAI, monitor LIVE, NWN/main или игровой AI других персонажей.
5. После установки требует наличие `scripts/BGXUN1.BS` и лишь затем пишет `BGXUNI/INSTALLED.TAG`.

Опции `--yes`, `--reinstall`, `--uninstall` подтверждены по исходникам WeiDU `src/main.ml` и документации `doc/base.tex` upstream `WeiDUorg/weidu`; неподдерживаемый `--tp2` обнаружен в скриншоте игрока.

## Проверки и пределы

- Повторно: **34/34 offline BAF tests PASS**.
- Регрессии установщика: **7/7 static tests PASS**.
- Интегральный ZIP: **10 файлов, CRC PASS**, есть TP2 и в корне и внутри BGXUNI. Старый архив содержит достаточные исходники: для ремонта из него нужна только замена CMD.
- Настоящий Windows CMD + WeiDU execution **не подтверждён после фикса**: ждать результата у игрока. Не объявлять игру/компиляцию пройденными.

## Публикация и восстановление

- GitHub (стабильный путь): `BGXAI/pilots/BGXUNI_010/BGXUNI_SETUP.cmd`, `README_START_RU.md`, новые `tests/test_setup_commands.py` и `tests/SETUP_TEST_RESULTS.txt` (обновлены/добавлены).
- Постоянная библиотека: `/BALDURS_GATE_EET_AI/BUILD/BGXUNI_011_PARALLEL/` хранит полный ZIP, только CMD hotfix, standalone CMD, README, BAF, TP2, tests.
- `/mnt/data/BGXUNI_SETUP_011_HOTFIX.zip` SHA256 `9fc419e26df7914e5fc955920c854c85fa1f19e5c1f128ef4745d2b81e7c0ae0`.
- `/mnt/data/BGXUNI_011_PARALLEL_GAME_PILOT.zip` SHA256 `d2252c3da0d1dccce65e90ba3a5b5804e664afe34f269bcc6ecb0bd4903b27d7`.

## Действия пользователя

1. Убедиться, что Baldur's Gate / InfinityLoader закрыты, остановить старое консольное окно `Ctrl+C`.
2. Скачать новый **один** `BGXUNI_SETUP.cmd` и **заменить** им старый рядом с `chitin.key` в корне EET; старую папку `BGXUNI` сохранить, остальное повторно не распаковывать.
3. Запустить этот новый CMD, нажать любую клавишу для продолжения. При `SUCCESS: scripts/BGXUN1.BS exists` сценарий готов к игровому тесту на одном персонаже. При другой ошибке — прислать **новый** `setup-BGXUNI.DEBUG` или финальный скрин.
4. Не менять штатный Advanced AI на остальных персонажах. После подтверждения WeiDU проверить появление `BGXUN1` в списке и тестовый `BGXUN1 V010 READY` в отдельном сохранении.