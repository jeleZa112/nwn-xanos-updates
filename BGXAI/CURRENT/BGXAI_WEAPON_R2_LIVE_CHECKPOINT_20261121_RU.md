# BGXAI — R2 LIVE: реальные оружейные слоты и сопоставление с APR R1.1

**Текущий достоверный статус 21.11.2026.** Пользователь случайно выбрал основной пункт 158, затем выполнил правильную команду 159 → 7 → 5 и прислал четыре файла. Пункт 158 дал `READONLY_NATIVE_PREFLIGHT_PASS`, `game_files_unchanged=true`, `V6_DPLAYER_BINARY_EXACT`, WeiDU-компиляция в TEMP; он НЕ изменил игру. Проверка `WSPATCK.2DA` только в `override` показала отсутствие в override, что **не доказывает отсутствие игрового ресурса в BIF**.

## R2, живой игровой результат

`BGXW2_SETUP_R2.json`: `R2_CONSOLE_RAW_COLLECTED`, actions=10, malformed=0, game_modified=false, flags item_identity_verified/per_slot_apr_verified/eps_manual_proven/weapon_switch_authorized=false. 

`BGXAI_WEAPON_SLOTS_RAW_R2.jsonl`: 12 корректных записей (SESSION, READY, 10 SLOTS), actor `139135050`, partyIndex `2`, seq 1–10. Все 10 наблюдений читают фиксированный loadout:

| Slot | Raw resref | Данные |
| --- | --- | --- |
| quick weapon 35 | `SW1H04` | объект присутствует, не доказана применимость |
| quick weapon 36 | `BOW05` | объект присутствует, не доказана применимость |
| quick weapon 37 | `null` | пустой |
| quick weapon 38 | `STAF01` | объект присутствует, не доказана применимость |
| quiver 12 | `AROW01` | `useCount1Raw=20` → `18` между seq 8 и 9 |
| quiver 11/13/14 | `null` | пустые |
| offhand 9 | `SHLD03A` | предмет в слоте, **не доказано**, что щит используется с луком одновременно |

`BGXAI_WEAPON_CONSOLE_20261121T132309314256Z.log` содержит оба работающих EEex слушателя `[BGXW2]` и `[BGXWP]` с `SESSION` и `READY`; `LUA` и `LPRINT` — два канала одной записи, не две отдельные атаки. Одноимённые seq, actor, partyIndex, action и selectedWeaponRaw точно совпадают для всех десяти событий. Код APR по R1: seq 1–7 `selected=38`, `aprRaw=1`; seq 8–9 `selected=12`, `aprRaw=2`; seq 10 `selected=35`, `aprRaw=7`. Переключения raw: 38 → 12 (seq8) и 12 → 35 (seq10). Как и раньше, `7` — **не 7 атак в раунд**; полная кодировка этого поля и эффективность альтернативного слота ещё требуют подтверждения. `selected=12` означает **слот боеприпасов**, а не подтверждённое соответствие конкретному луку (launcher+ammo+ability). Уменьшение числа стрел на два подтверждает только счётчик между снимками, не доказательство точного числа атак или попаданий.

**Новая функциональная CODE:** `BGXAI_WEAPON_LIVE_PAIR_R1_R2_READONLY.py` программно синхронизирует два live-наблюдателя по seq/actor/partyIndex/action/selected и фиксирует raw loadout, расход ammo и три последовательных выбранных контекста. Данные не дают притворяться, будто APR неизвестного оружия измерен. `test_weapon_live_pair_r1_r2.py` **18/18 автономных OFFLINE PASS** (синтетические данные, ошибочные пары и разбор консоли); отдельно подтверждено сопоставление 10/10 событий реального журнала. Получен отчёт `BGXAI_WEAPON_R1_R2_LIVE_PAIRED_20261121.json`, строгий `dispatchAuthorized=false`.

**CODE/TEST/DEPLOY/LIVE:** R1.1 и R2 пассивные наблюдатели установлены и их слушатели реально загрузились в игру (LIVE PASS для чтения). Источник офлайн-сопоставления создан и опубликован, но **не установлен в игру**. Сам интеллектуальный приоритет оружия и отправка команд не установлены, не подтверждены, `HOLD_NO_ENGINE_DISPATCH`.

**Что реально необходимо дальше:** читать через поддерживаемые EEex/ITM структуры эффективные способности оружия (launcher ↔ ammo, magic/poison elemental bonuses, charges) и связывать их с актуальными buff/STR/proficiency/APR, а затем получить безопасный признак отсутствия ручных команд и конфликта EPS перед переключением. Не возобновлять установку R1/R2 и не повторять 158/159-7-5 ради уже полученных фактов. Не подменять работающие V6/EPS. Любое новое изменение игры — только явное разрешение, SHA, backup, last-only WeiDU rollback.

**Сопутствующее замечание:** в консоли есть `Error loading menu ... ']' expected near 'icon'` и сообщения `UI string not found`. Они не остановили R1/R2, их источник не доказан и **не следует исправлять другие моды без отдельной диагностики**.

Исходные файлы и summary хранятся в Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS`, код и тест в `/BALDURS_GATE_EET_AI/BUILD`, этот checkpoint — `/CURRENT`. Использовать именно этот LIVE checkpoint как актуальную точку вместо предыдущего R2 `LIVE=NO`.
