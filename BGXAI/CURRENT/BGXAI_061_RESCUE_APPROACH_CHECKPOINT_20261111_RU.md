# BGXAI 061 — непосредственное исправление дистанции охраны

Дата: 11 ноября 2026 г. Проект: BGXAI / Baldur's Gate Enhanced Edition Trilogy (EET Foxx), EPS 18.4, SCS 35.21, EEex 1.2.0, сложность Insane.

## Реальный итог BGXAI 060: ЧАСТИЧНО работает

Пользователь проверил одну и ту же ситуацию с Шанком у Jade (Player3), режим «Атаковать врагов» был выключен. Близко стоящий защитник с F=ON среагировал после нескольких ударов. При большей дистанции EPS выполнял баф, но защитник не подошёл. Это **не полный успех** 060.

### Подтверждённый кодовый ограничитель

В `BGXAI/fox_new/experimental_060_direct_response_source_only/BGX60_RECEIVER.baf` все 12 боевых веток требуют `See(PlayerN)` и `Range(PlayerN,10)`. За пределами 10 футов единственный бой/защита недостижимы по условиям BCS. В `BGXAI/fox_new/experimental_056_active_guard/BGX56/M_BX43.lua` текущий Lua bridge пишет `BGX52_REQ_SLOT` только после **подтверждённого попадания**, TTL `90` игровых тиков (~6 сек). При EPS бафе/занятой очереди `ActionListEmpty()` не выполняется, Q может истечь. В результате эффект бафа не свидетельствует об исполненной охране.

Документация IESDP подтверждает `InMyArea(O)` 0x40CB, `Range(O,I)` 0x4018, `MoveToObject(O)` #22, `ProtectObject` #87, `AttackReevaluate` #134:
- https://iesdp.bgforge.net/scripting/triggers/bgeetriggers
- https://iesdp.bgforge.net/scripting/actions/bgeeactions

## Реально создано: BGXAI 061 SOURCE-ONLY

Код в GitHub `BGXAI/fox_new/experimental_061_rescue_approach_source_only/`, 8 файлов: 7 SHA-pinned источников + `manifest.json`. В постоянной Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_061_RESCUE_APPROACH_SOURCE_ONLY/` сохранены исходники, тесты, README и исходный ZIP (ZIP не предназначен для ручного запуска пользователем).

1. `BGX61_RECEIVER.baf`: **20 блоков** вместо 14 BGX60: 2 cleanup; 6 прямых ответов `AttackReevaluate`; 6 новых промежуточных `MoveToObject(PlayerN)`, только если `InMyArea`, `!Range(PlayerN,10)`, `Range(PlayerN,40)`, Q=именно этот союзник, F=ON, `ActionListEmpty`, `ModalState(NONE)`; 6 близких `ProtectObject`. В подходе Q **не стирается**, TTL продлевается на 20 с, cooldown 2 c, маркируется `BGX61_LAST_BRANCH=3`, по завершению движения может сработать непосредственная атака/защита.
2. `BGXAI61_BUILDER.py`: компиляция штатным WeiDU в TEMP, строгий pin **установленного 060 BCS** `038b41c529fb45bb75528722577beef7b474e1ce55e280dc5fca4d6ed9e72841`, точная замена 14 BGX60 BCS-блоков на 20 BGX61; все остальные 1057 блоков byte-for-byte unchanged; итог 1077.
3. `BGXAI61_INSTALL.py`: чистый SHA-pinned переход 060→061 через новый WeiDU BGX61 с резервной копией. Меняет **только** `override/BDDEFAI.BCS` и `override/M_BX43.lua`. В Lua меняет **ровно два** литерала: TTL 90→300 ticks (~20 сек), MAX_GAME_TIME 2147483556→2147483346 во избежание signed overflow. Остальная часть EEex hook неизменна. Установка и откат требуют закрытой игры, точных baseline SHA, BGX60/BGX61 последним, сохранённой SHA-проверенной внешней копии, двух подтверждений. Rollback к 060 штатным WeiDU. No blind retry.
4. `test_061.py`, `test_061_install.py`: **27/27 локальных модельных тестов PASS**, включая цикл установки и отката с mock WeiDU. Синтетические тесты **не доказывают native game behavior**.

## Состояние автообновлятора

**Только существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. В один pinned `BGXAI/BGXAI_SYNC.ps1` добавлены пункты:
- 65 скачать SHA-проверенный исходник 061;
- 66 настоящая READ ONLY компиляция WeiDU + контроль 060 BCS/Lua;
- 67 экспериментальная установка 061 только после отдельного `INSTALL_BGXAI_061`;
- 68 read-only статус;
- 69 откат 061→060 только после `ROLLBACK_BGXAI_061`.

Оригинальные пункты 1–64 оставлены. Синтаксические ошибки вида буквальных `\\n` запрещены; проверены 15 структурных инвариантов, сохранность старых веток, баланс фигурных скобок. **PowerShell parser на Windows и native WeiDU 061 ещё не испытаны**.

GitHub script commit `e0bd9bdd5c9b2872e0c47f28b414bef67c9ea907`, SHA256 `2d95c3c57af78301b680eef156b6f6230b1f95685526841b61f1ccfa91f89746`, размер `53921` байт; обновлённый `BOOTSTRAP_PIN.json` commit `4c81bddd3bc9cac0c49e650aad15a05608081ee7`. GitHub 8/8 source blobs совпадают с рассчитанными локальными blob sha; manifest 7/7 SHA256 PASS. ZIP CRC PASS.

## Текущий статус и следующий шаг

- **Установлено в игре: BGXAI 060** (пользователь подтвердил через инсталлятор); ни одного live-файла при публикации 061 не изменено.
- **061 SOURCE ONLY / NOT INSTALLED / native WeiDU NOT VERIFIED.** Не объявлять охрану дальнего действия работающей до игрового теста.
- Пользователь уже провёл достаточно повторных боёв. **Сейчас боя не требуется.** Только закрыть игру и InfinityLoader, запустить тот же `BGXAI_UPDATE.cmd`, выбрать **66** и прислать результат read-only preflight. При PASS следующий шаг — подтверждённая установка 67, статус 68, **один** проверочный бой для подтверждения реального подхода.
- Если 66 fails: не устанавливать/не откатывать, разобрать вывод и исправить **этот же** updater/исходники.
- Полноценный автономный командный AI по-прежнему будущая цель; 061 — ограниченный исполнитель охраны. Следующая реальная стратегическая задача после валидного исполнения — реакция **до успешного попадания**, роль защитников и координация EPS магии без потери ручного приоритета.
