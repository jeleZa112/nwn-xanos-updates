# BGXAI / BGXUN1 — 05.11.2026 — v0.1.4 POSITION-FIRST

## Решение пользователя
Пользователь предпочитает не побег по HP, а **держать Имоен с луком на небольшой безопасной дистанции от врага, за танком**. Уточнено: сохранить дистанцию важнее постоянного «отступления»; танк должен перехватывать противника, Имоен не прекращать стрельбу из-за бесконечных перестроений.

## Проверка механики
- Baldur’s Gate EE: проблема дальнего оружия возникает при его использовании против вплотную стоящего врага/во время рукопашного контакта: дистанция вне melee не даёт штрафа только от того, что цель находится близко. Источники: Baldur's Gate Wiki THAC0 (https://baldursgate.fandom.com/wiki/THAC0), Beamdog developer answer https://forums.beamdog.com/discussion/75615/does-distance-from-enemy-affect-ranged-attacks-in-any-way.
- **ВАЖНО:** `RunAwayFromNoLeaveArea(creature,12)` — не 12 футов, а 12 AI updates (~0.8 s при 15 updates/sec). Документация IESDP: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm. Поэтому ранее планировавшиеся 55-60 AI updates (~3.7–4 s) были длинными для маленькой перестановки.
- Выбор Имоен при сохранённом `BGXUN1.BS`, запуск `BGXUN1 V010 READY` и FindTraps реально проверены пользователем в игре. В бою пользователь лично подвёл Имоен к врагу, она не отбежала и погибла; BGX71 observer не различает ручные и AI движения. Новая версия пока в игре не тестировалась.

## Конкретная версия v0.1.4
- Изменяется **только отдельный `BGXUNI/BGXUN1.BAF`** и проектный helper/manifest у существующего `BGXAI_UPDATE.cmd`, без новых CMD/ZIP пользователю, без правок BDDEFAI/BGXGRP/BGXTANK и NWN `main`.
- `BGXUN1 V014 SPACING` — однократный маркер на уже назначенной Имоен (новый BGXU014 LOCALS).
- С выбранным луком/арбалетом, при угрозе в 4 условных футах, при пустой очереди и без запрета отступления — короткое `RunAwayFromNoLeaveArea(...,12)` (~0.8s), максимум 2 шага на непрерывный контакт, не чаще раза в 5 sec, после шага 2 sec буфер; новые автоатаки при Range<=4 запрещены. На диапазоне 5–18, когда враг виден, атакует выбранным ranged weapon без приближения и смены оружия. Нет действий в скрытности / при BDAI_DISABLE_ATTACK=1.
- После попадания, если HP<76% и враг близко (6) — раннее `RunAwayFromNoLeaveArea(...,18)` (~1.2 s), с cooldown; при HP<56% и угрозе в 5 — не более 3 коротких аварийных отходов `RunAwayFromNoLeaveArea(...,24)` (~1.6 s) с промежутком 8 sec. Бюджет сбрасывается только после выхода из боя/подлечивания, timers защищают от нового мгновенного melee engagement.
- **Честное ограничение:** сейчас это короткий шаг ОТ врага; BAF ещё **НЕ ВЫЧИСЛЯЕТ ПОЗИЦИЮ ЗА НАЗНАЧЕННЫМ ТАНКОМ** (нужны роль/якорь танка и доступная геометрия EEex, safe-path/trap/агро). Не утверждать обратное. Critical action может перебить ручные приказы, поскольку provenance PLAYER/AI не внедрён; штатные обычные атаки и spacing требуют ActionListEmpty. Смежная защита от ловушек маршрута не доказана.

## Статусы, тесты, код
- 20 BAF блоков, 48/48 Python проверок BAF + 2k seed random, 15/15 PowerShell updater static tests — **63/63 PASS**. Реальная компиляция версии 0.1.4 и live-движение/боевое позиционирование **НЕ проверены**, только v0.1.3 ранее работала в EET+WeiDU251.
- опубликовано в GitHub `jeleZa112/nwn-xanos-updates`, ветка только `bg-eet-ai`: `BGXAI/pilots/BGXUNI_010/BGXUNI/BGXUN1.BAF`, `parallel/BGXUNI_AUTOINSTALL.ps1`, `parallel/latest.json`, обновлён удалённый `BGXAI/BGXAI_SYNC.ps1` (commit d67fe44d9624d3c8cdfe2b53a26bd07708153748); неизменный `BGXAI_UPDATE.cmd` blob `faeffbba72ef2a64b631ef557c06037d6b145a9d`.
- Хеши источников SHA256: `BGXUN1.BAF` `e8827c548e4bf6457d850844f0b0d74441e10bff5c84804a1cedfda17c8dbf0b`; `BGXUNI_AUTOINSTALL.ps1` `37ed12efad4b8a64ece8cd7c43366a6b3ccc5eae730b4df9c13ceffcc419afb5`. GitHub git-blobs e5f383be8b8284c424d08c5f7151d715a8aff328, 79f96916d17c4d9c834898eb8ece0b957ee87341 совпадают с локальным `git hash-object`; manifest запинован.
- Удалённый BGXAI_SYNC.ps1 изменён только в 3 строках меню v014, после удаления selector весь первоначальный 0.6.27 updater точно совпадает с blob `a02080cab3b59a384c66b8edb56c54f68f94cb4f` — PASS.

## Следующий шаг пользователя
1. Отдельный сейв, закрыть игру/InfinityLoader, запустить тот же единственный корневой `BGXAI_UPDATE.cmd`, выбрать `1`.
2. Убедиться `SUCCESS BGXUNI 0.1.4` без ошибки WeiDU. Если ошибка, последний экран и `BGXUNI_UPDATE.log`/`setup-BGXUNI.DEBUG`.
3. Снова запустить через InfinityLoader, у Имоен скрипт остаётся BGXUN1. Увидеть `BGXUN1 V014 SPACING` и в контролируемом бою с лучным оружием `BGXUN1 V014 SPACE 1/2` при слишком близком враге; наблюдать позицию/дистанцию и не путать manual движения с AI.
4. Следующий этап: EEex actor/role path/line-of-sight/aggro perception для размещения *за конкретным защитником*, а не просто от врага, и доработка `manual=PLAYER/AI/UNKNOWN` provenance.
