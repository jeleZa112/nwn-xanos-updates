# BGXAI — 22.11.2026: R3 LIVE ITM/BIFF готов, пассивное сравнение weapon slots создано

## Проверенные результаты пользователя

Получен действительный файл `BGXAI_WEAPON_NATIVE_ITM_R3.json` (33 454 байта, SHA256 `7ae7555f81b14a784e7866472f14483b02c2d6b707ab6169225e8fec32507304`). Статус `ITM_NATIVE_ALL_ITEMS_RAW_READ`, `sourceKind=CURRENT_GAME`, `gameModified=false`, отсутствующих ресурсов нет. Исходный реальный R1/R2 live-pair `BGXAI_WEAPON_R1_R2_LIVE_PAIRED_20261121.json` (SHA256 `3126ce53b50a412cdc767c890248787f0e5b6bb269eef1494c1bf3ce87de94b1`) подтверждает 10/10 совпавших действий actor `139135050`, третий портрет.

Текущие реальные ресурсы игры:

| Item | Источник | Базовая способность | Особенности |
|---|---|---|---|
| `SW1H04` | `override/SW1H04.ITM` | меч 1d8 (среднее 4.5), reach 1, speed 5, одноручный | on-hit opcode 146 на `SW1H04.SPL`, raw probability 1, spell opcode 112 снимает `SW1H04`, opcode 122 создаёт `MISC56_` (Broken Weapon): потенциальная поломка в железный кризис, не ущерб цели |
| `BOW05` | `data/Items.bif` | двуручный launcher, дальность 75, speed 6, нулевой собственный dice damage | while-equipped opcode 1, param1=2, param2=1, timing=2, *Flat Value* APR key = 2 (не бонус +2 APR) |
| `AROW01` | `data/Items.bif` | стрелы 1d6, дальность 100, projectile type bow (raw launcherRequired=1) | совместимость с луком предположена по типам, но `launcherAmmoPairVerified=false` |
| `STAF01` | `override/STAF01.ITM` | посох 1d6, reach 2, speed 4, двуручный | щит в offhand raw ещё не доказывает, что он действует в двуручном режиме |
| `SHLD03A` | `data/Items.bif` | щит без атакующей способности, min STR 12 | opcode 0 AC raw; точное влияние на активную AC не замерено |

Установленные таблицы теперь найдены: `WSPATCK.2DA` из `data/Default.bif` (6 рядов) и `CLSWPBON.2DA` из override (76 рядов). `FIGHTER` имеет `GETS_PROF_APR=1`, но **actor class/kit/level/proficiency rank не прочитаны**, поэтому конкретную WSPATCK-строку выбирать и добавлять поверх engine-final APR нельзя.

Наблюдавшиеся `aprRaw` для *выбранного* оружия: посох 1 (стандартная расшифровка 1 APR), активный ammo-slot12/лук 2 (2 APR), меч 7 (1.5 APR). Их применение к другим слотам при активных бафах **не доказано**. Изолированная статическая физическая оценка (base mean × sampled APR, **не DPS и не ранг**) даёт соответственно 3.5, 7.0, 6.75; игнорирует STR, Dex-to-hit, target armor, классы, on-hit, immunities, экипировку и очереди.

## Новый код

Написан `BGXAI_WEAPON_R3_STATIC_BRIDGE_RO.py` и `test_weapon_r3_static_bridge_ro.py`, сохраняются в `BGXAI/patchsets/ranged_fighter_guarded_20261119/` ветки `bg-eet-ai` и `Library /BALDURS_GATE_EET_AI/BUILD/`. Вход — два реальных JSON, выход — `BGXAI_WEAPON_R3_STATIC_CANDIDATES_20261122.json` в Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/`. Модель:

- строго связывает R3 с actor/slot/resref R1R2; отдельно приводит 4 weapon slots и ammo 11..14;
- рассматривает `BOW05`/`AROW01` как **предполагаемую по типу**, не подтверждённую движком пару;
- не складывает `BOW05` opcode1 APR=2 с наблюдавшимся APR 2 или APR от `WSPATCK`;
- отделяет прямой урон от ненормированных item/weapon effects, распознаёт потенциальный `SW1H04 → SW1H04.SPL → MISC56_` как риск потери оружия;
- фиксирует конфликт «двуручное оружие / щит» без утверждения активного щитового бонуса;
- блокирует ложное подтверждение неизвестных live-buff, per-slot APR, умений, иммунитета, статуса EPS/manual;
- все выходы имеют `priorityAvailable=false`, `executable=false`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`, `currentActionPreserved=true`.

**TEST:** 28/28 автономных Python `unittest` PASS, включая реальные R3+R1R2, неправильного actor, provenance, APR, resref, override table, потерю linked SPL и поломку меча. Отдельных Windows native/EET тестов этого нового расчётного кода не было. **DEPLOY:** никакой новый расчётный код в игру не установлен. **LIVE:** R1+R2+R3 наблюдатели и сбор ресурсов подтверждены; настоящих автоматических решений выбора оружия всё ещё нет.

## Принцип дальнейшей работы

Не создавать лишние инсталляторы. Следующее функциональное звено: получить достоверный `actor class/kit/level/pips`, weapon ability, текущие active derived stats и подтверждённое соответствие bow+ammo; сопоставлять buff-aware финальные APR и попадание, не суммируя профбонус дважды. Изменение fingerprint предметов/боеприпасов/бафов только пересчитывает совет, **никогда не прерывает текущую атаку, лечение, каст и команды EPS**. Реальный dispatch допустим после независимого подтверждения idle/manual/EPS boundary и отдельного явного согласия пользователя на WeiDU. Не трогать BGXRANGED6, EPS18.4, BG Voice RU, BG_EET_RU, сохранения. Не повторять 158, R1/R2 install/capture, 159→7→6, пока нет новой конкретной причины.

## Источники механики (не документы пользовательской игры)

- IESDP opcode 1 APR modifier: https://iesdp.bgforge.net/opcodes/bgee
- IESDP opcode 112 / 122 / 146 / 318 / 319, BGEE.
- Beamdog 2.0–2.3 patch notes: железный кризис и прекращение поломок после разрешения сюжета: https://files.beamdog.com/files/BG-2.0-2.3-ReleaseNotes.pdf
