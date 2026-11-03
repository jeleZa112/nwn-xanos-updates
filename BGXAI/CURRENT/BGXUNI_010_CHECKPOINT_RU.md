# BGXAI / BGXUN1 v0.1 — CURRENT CHECKPOINT 03.11.2026

СТАТУС: первый отдельный пригодный для установочной проверки **реальный BAF** с TP2 и однофайловым CMD. **Не скомпилирован на компьютере пользователя и не испытан в EET**. Нельзя называть готовым интегрированным ИИ или настоящим 19-toggle UI.

## Где исходники

- GitHub `jeleZa112/nwn-xanos-updates`, branch `bg-eet-ai`: `BGXAI/pilots/BGXUNI_010/`.
- Library `/BALDURS_GATE_EET_AI/BUILD/BGXUNI_010_PARALLEL/` (полный архив, README, BAF, TP2, CMD, тесты, IDS-snapshot, logs).
- ZIP `BGXUNI_010_PARALLEL_GAME_PILOT.zip`, SHA256 `a5b4b9b8ace7296d0dbd0107941ff09ec00404c1d2e0b3c826388a2949ab0ba0`, **12 839 bytes**, ZIP CRC PASS, 7 файлов.

## Реализация

- Единственный новый скрипт `BGXUN1.BAF` (компиляция -> `override/BGXUN1.BCS` -> `scripts/BGXUN1.BS`) — не зависит от имён/портретов, проверяет реальные `HaveSpell`, `STEALTH`, `TRAPS`, `IsWeaponRanged`, `ActionListEmpty`, `BDAI_*` локальные разрешения; 11 приоритетных блоков.
- Часть способностей соединена в одной очереди: self-heal, Mirror Image, опциональные single-target Blindness/Magic Missile, detect traps, stealth, bard song, ranged/melee selected weapon. Исходные `BDDEFAI`, `BGXGRP`, `BGXTANK` НЕ изменяются.
- Никаких automatic disarm/pathfinding/steal/item consumables, uncontrolled movement, ForceSpell, hardcoded NPC slot или hidden enemy count. Отдельно ограничен manual action override; действия при занятости очереди не планируются.
- `BGXUNI_SETUP.cmd` в корне игры (только этот новый файл + папка BGXUNI). Копирует только локальный существующий WeiDU `setup-stratagems.exe` или `setup-BGXAI.exe` в **новое** `setup-BGXUNI.exe`; установочная команда по отдельному `BGXUNI/setup-BGXUNI.tp2`, `/remove` для WeiDU rollback. При конфликте существующего `scripts/BGXUN1.BS`, не помеченного своей установкой, останавливается.
- 34/34 проверки офлайн на прежних реальных пользовательских IDS (5 IDS прочитаны из сохранённого архивного ZIP, в пакете сверенные SHA256 и минимальный список символов). 2000 random seeded сцен проверяют ручной приоритет, отсутствие расхода неизвестной магии и нарушение скрытности. НЕ реальный WeiDU/compiler test.
- `BGXUCTRL=1` и `BGXUDMG=1` используются как **проектные opt-in LOCALS**, новый UI их ещё не выставляет. Более известные BDAI flags читаются, но возможность менять Advanced AI UI при активном кастомном сценарии ещё НЕ доказана. Не обещать пользователю готовое меню 19 флагов.

## Текущие параллельные версии

- `BGXAI/latest.json` **0.6.27-role-profile-install-pilot**, НЕ меняли.
- `BGXAI/live/latest.json` **0.4.4**, private telemetry работала на Windows ранее; НЕ меняли.
- `M_BGX73.lua` **0.7.3 shadow** (offline only), НЕ меняли.
- Работающие `BGXAI_UPDATE.cmd`, `BGXAI_LIVE.cmd`, исходные BAF/BS и NWN/main НЕ меняли.

## Следующее действие (НЕ повторять старое исследование)

Пользователь выполняет **один первый установочный тест**: отдельный save -> закрыть игру/InfinityLoader -> распаковать ZIP в корень с `chitin.key` -> `BGXUNI_SETUP.cmd` -> проверить `scripts/BGXUN1.BS` и появление сценария в меню. Назначить только Имоен или другого NPC с текущим подходящим классом, ожидается `BGXUN1 V010 READY`. Если не компилируется, только новый `setup-BGXUNI.DEBUG`/скрин ошибки, не повторно WeiDU.log и три архива. Если работает, следующий раунд — приоритет ручных приказов и один слабый бой, следом отдельный MENU EEex 19 независимых переключателей.

## Правило для нового чата

При отсутствии файлов СНАЧАЛА проверить `files__list/search/read` в Library и GitHub handoff. Никакой повторной загрузки архивов EET ~45 тысяч ресурсов. Всегда различать 34 офлайн-теста от отсутствующей реальной Windows/WeiDU/EEex-приёмки.