# BGXAI — комплексный тест READ ONLY, 26.11.2026

## 1. Итог: CODE / TEST PASS, нового игрового LIVE нет

**ИТОГОВЫЙ УСПЕШНЫЙ ПРОГОН:** [GitHub Actions #45667708256](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256), status=`completed`, conclusion=`success`, head SHA `65f7be99d7fd001e0213ddf1369600b544dfa25a`. **7/7 jobs SUCCESS**: 1 weapon Lua, 2 native Python (Windows/Linux), 2 party safety (Windows/Linux), 1 Windows PowerShell 5.1 onefile, 1 unified summary. Workflow: [bgxai-comprehensive-readonly-20261126.yml](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/.github/workflows/bgxai-comprehensive-readonly-20261126.yml).

**Всего 4 828 прошедших тестовых случаев/проверочных утверждений в повторяемых матрицах сред**: Lua 4 134, Python 250, тактика 444. Дополнительно выполнялись SHA-pinning, синтаксис, неизменность меню и smoke startup; для них нет единого количества assertion, **к 4 828 не добавлялись**. 4 теста отмечены SKIP (по 2 на Windows и Linux): приватный реальный R28 effect-gate input не выложен в CI; R31 Python-проверка локального Lua интерпретатора пропущена (комплекс Lua отдельно прогнал 3 реальных интерпретатора). Прогоны на синтетических моделях/фикстурах не являются доказательством поведения движка EET.

### 1.1 Сводная матрица

| Подсистема | Среда | Фактические результаты | Вывод |
|---|---|---|---|
| Weapon V3/V4/V5, activeStats, noninterrupt и fail-closed | Lua5.3, Lua5.4, LuaJIT | 443 × 3 = **1 329** | PASS |
| R2 слоты/quiver/offhand | те же 3 Lua | 39 × 3 = **117** | PASS |
| R4 активные характеристики | те же 3 Lua | 49 × 3 = **147** | PASS |
| R32 EEex 2DA | те же 3 Lua | 18 × 3 = **54** | PASS |
| R35 выбранные APR/THAC0, double read | те же 3 Lua | 16 × 3 = **48** | PASS |
| R27 one-callback source | те же 3 Lua | 90 × 3 = **270** | PASS |
| 081 x64 очередь: проверки утверждений | те же 3 Lua | 441 × 3 = **1 323** | PASS |
| 081 action-context | те же 3 Lua | 282 × 3 = **846** | PASS |
| R27/R28/R30/R31/R32/R33/R34/R35 Python | Windows+Linux | 127 × 2 = 254, **250 PASS, 4 SKIP** | PASS с явно обозначенными пропусками |
| BGXP3/4/5, BGX120, AoE, friendly retaliation, ranged V5–V7, saved scripts | Windows+Linux | 222 × 2 = **444** | PASS |
| Pinned one CMD / 173 handlers / SHA | Windows+Linux | SHA, 172 старых handler побайтово равны R33 baseline; текущая версия 79 775 байт | PASS |
| Реальный PowerShell 5.1 | отдельный Windows runner | Парсер полного активного скрипта + запуск до меню и выбор `0` на ВРЕМЕННОМ фиктивном корне | PASS |
| Сумма выше (неуникальные случаи и утверждения) | матрица | **4 828 PASS, 4 SKIP** | CODE/CI PASS |

**BAF/WeiDU test-only**: в составе прогона Lua также напечатаны `PASS BAF NATIVE RECOVERY 8/8` и `PASS NATIVE BAF COMPILER CONTRACT 21/21` на каждом Lua запуске. Они не означают компиляцию/установку в реальной пользовательской игре; не были вторично прибавлены к общей сумме.

### 1.2 Сбой первого запуска и исправление

Первый workflow [#45667567663](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667567663) **FAILED** только на `PowerShell 5.1 isolated menu smoke`: наш тестовый драйвер вставлял `$Prompt` в двойные кавычки, что в PowerShell искажало подставную функцию `Read-Host` на тестовом runner. Это **баг тестовой обвязки**, а не доказанный дефект загрузчика игры. Исходные Python, Lua, AoE, healing, friendly и проверка синтаксиса PowerShell в первом прогоне PASS. Исправлена лишь генерация драйвера: `$readHostStub='function global:Read-Host { param([string]$Prompt) ''0'' }'`. Повторён **весь комплекс**, а не только упавший шаг: [#45667708256](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256) **7/7 jobs PASS**. Игровой `BGXAI_UPDATE.cmd`, `BGXAI_SYNC.ps1`, `BOOTSTRAP_PIN.json` на этом этапе не менялись.

## 2. Отдельная независимая проверка РЕАЛЬНЫХ входных файлов

Без загрузки приватных журналов в общедоступный GitHub CI локально проверены оригиналы:

- `BGXAI_R28_NATIVE_FROM_R27_20261123T173010478057Z.json`: 39 474 байта, SHA256 `166a0a970f3192622bc8d5b4fbad16ecdd0727e85f2b35228c959c89fbd56e41`.
- `BGXAI_R34_NATIVE_PROF_20261126T002126164.json`: 7 404 байта, SHA256 `aab2fdf801627b1bb165dd5435644da0b50967f9269e351e58bec4deecc81c10`.

**REAL INPUT CHECK PASS**: R27 24/24 последовательных selected-action события одного исторического actor; 22 события slot 12 (ammo) raw APR key 2 → стандартный APR 2; 2 события slot 35 (SW1H04) raw APR key 7 → стандартный APR 1,5. Ровно 4/4 совпадения `ITM SHA256 + resource origin + proficiencyIdRaw` между ранее прочитанными R28 и CURRENT_GAME R34: `AROW01`, `BOW05`, `STAF01`, `SW1H04`. R34 все 5 предметов прочёл и вернул `gameModified=false`, `ordersSent=0`.

**ГРАНИЦА:** характеристики actor R33 исторические; между R27, R33 и R34 нет доказанного одинакового контекста времени, бафов, характера атаки и связи стрел с пусковым оружием. Нельзя утверждать, что альтернативный APR лука равен 2 в той же точке, где меч имеет APR 1,5. Текущие эффективные THAC0/урон, цель, EPS ownership, момент безопасной смены слота НЕ проверены. `weaponSwitchAuthorized=false`.

Локальный отдельный JSON отчёта предоставляется пользователю как `BGXAI_REAL_INPUT_CROSSCHECK_20261126.json`, **полные приватные файлы не загружались в репозиторий**.

## 3. Что НЕ считается выполненным

- Не было реального LIVE-тестирования новой оценки и переключения оружия в установленной EET после R35. R35 — CODE/CI, в игру не установлен.
- Не доказано чтение полного актуального активного effects fingerprint для каждого невыбранного quickslot, как и вычисление counterfactual effective APR/THAC0 в одной сцене.
- Отсутствует достоверная проверка происхождения ручных команд и EPS, `safeDispatchTimeVerified=false`; нулевой raw queue сам по себе ничего не разрешает.
- Синтетический PASS защиты от дружеского огня/лечения/AoE не означает автоматическое решение всех игровых боёв. Ранее проверенные LIVE BGXP5/BGX120/guard статусы сохраняются отдельно, не повышаются этим CI.
- Обновлятор проверен на **фиктивной папке** до пункта `0`; пункты установки/удаления, реальный WeiDU в установленном EET и сохранение игровых действий не запускались.
- BG Voice RU, BG_EET_RU, EPS18.4, live scripts и saves в тесте не модифицировались.

## 4. Следующая конкретная задача P0

Интегрировать `BGXAI_R35_SELECTED_ENGINE_STATS_RO.lua` в существующий **один R33 callback** в виде ограниченного read-only пилота; только после отдельного source-only префлайта/backup/SHA и явного типизированного согласия на изменение игры. В пилоте в естественных игровых переключениях собирать selected APR+raw THAC0 и всю доступную контекстную сигнатуру `actor/equipment/buffs/action source`, не отправляя приказов и не прерывая EPS/manual. Любой другой неподтверждённый активный параметр = HOLD. После достаточных данных — существующие V3/V4/V5 + NONINTERRUPT, не новый scorer. Обязательно отдельная LIVE проверка инвариантов, прежде чем разрешать active weapon switch.

Правило: **CODE ≠ TEST ≠ DEPLOY ≠ LIVE.** Один пользовательский `BGXAI_UPDATE.cmd`; не повторять старые R27/R33/R34, старый bow→sword pilot и не требовать ещё одной переустановки для отчётов.

