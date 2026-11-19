# BGXAI — игровой тест V2: ошибки переключения оружия (19.11.2026)

## Фактические сообщения пользователя
1. При лук+меч+стрелы в быстрых слотах на близкой дистанции Халид не перешёл на ближнее оружие. На первом скриншоте его HP=8/13 (61.5%).
2. При стартовом ближнем оружии автоматически перешёл на дальнобойное; на втором скриншоте HP=7/13 (53.8%) на момент снимка. Снимок сам по себе не устанавливает HP во время переключения.
3. Если лук, меч и стрелы **только в рюкзаке**, бот не разложил их по оружейным слотам и атаковал кулаками.

## Root cause / подтверждение
- Исходник V2 BGXRANGED_V2_MELEE_HANDOFF.baf содержит HPPercentGT(Myself,75) во всех трёх ветках, включая EquipMostDamagingMelee. При 8/13 или 7/13 это условие ложно. Это подтверждённая логическая ошибка ветки, но журнал конкретного тика ещё не исследован.
- Действие EquipMostDamagingMelee() (IESDP) выбирает оружие только среди уже заполненных быстрых оружейных слотов, не из general inventory. EquipRanged() аналогично выбирает пригодное дальнее оружие. Без предварительной раскладки рюкзак сам собой не преобразуется в быстрые слоты.
- FillSlot(SLOT_WEAPON) недопустим в автоматическом пилоте: IESDP предупреждает об уничтожении уже находящегося в слоте предмета. Требуется безопасный Lua/EEex инвентарный слой, который сверяет реальный предмет/цель/оружейную пригодность, не удаляет и не подменяет предметы и атомарно проверяет результат. XEquipItem при известном resref требует отдельного неразрушающего audit.
- V2 сохраняет ActionListEmpty(): даже после снятия HP-гейта следует в игре проверить, что переключение действительно происходит в бою, когда очередь EPS уже занята, без нарушения ручных приказов.

## Что выполнено
- V3 SOURCE ONLY: BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXRANGED_V3_MELEE_HANDOFF.baf, коммит 75f61dbec7f8ef973c0bd131c917248287ad5c5e.
- Удалён HPPercentGT(Myself,75) только из веток выбора ближнего/дальнего оружия. Для начала дальней атакующей серии HP>75% пока сохранён. Лечение BGXP5, F guard, ActionListEmpty, запреты паники/беспомощности не изменены.
- Добавлен HasWeaponEquiped(Myself) в ближний переключатель; отсутствуют разрушительные FillSlot() и XEquipItem() для рюкзака.
- CI проверяет низкий HP, обратное переключение, отсутствие команд движения и опасной подстановки предметов. Run 44517666726 SUCCESS.
- V3 ещё **не скомпилирован нативно в игровой EET, не установлен и не проверен в бою**. Меню 128 остаётся прежним V2, его не следует снова запускать ради V3.

## Следующий полезный шаг
1. Нативная read-only компиляция V3 поверх фактического installed V2 (если он установлен: BCS SHA 1991f04d0a6acc556f53e03a7aa4a9c51d8860d24aeb67b3c461b3, LAST WeiDU BGXRANGED2) с сохранением 1170 исходных блоков; блокировка неизвестного BCS.
2. Защищённое WeiDU-обновление с проверенными бэкапами и автопроверкой, а не очередная source-only цепочка.
3. Применить V3 при столкновении с HP 7/13, проверить фактический выбор меча. Отдельно проверить безопасное оборудование из рюкзака через EEex, только после трассировки слотов и исключения потерь предметов.
4. В будущих более полных версиях выбор оборонительного оружия и право стоять в ближнем бою разделены: раненый боец может обнажить меч, но не обязан танковать, если этого не выдержит.

## Запреты
- Не объявлять V3 работающей игрой по одному CI PASS.
- Не использовать разрушительное FillSlot или слепой XEquipItem.
- Не нарушать лечение Жагана, SCS/EPS, BGX120, ручные команды, BG Voice RU/BG EET RU.
- Следовать постоянному правилу: после согласованной установки все проверенные безопасные этапы той же версии исполняются автоматически, без отдельного + и повторного выбора STATUS.


## Обновление 19.11.2026 — защищённый V3 готов к первой установке

- После живого теста V2 (HP 8/13, 7/13; не выбрал меч, при инвентаре без quickslots бил кулаком) создан новый V3 BAF с отделением защитного выбора оружия от порога HP>75%. Автострельба по-прежнему ограничена HP>75%; полный выбор DPS/penetration ещё НЕ реализован.
- V3 нативный read-only preflight: BGXRANGED_V3_PREFLIGHT.py; требует exact V2 BCS SHA 1991f04d0a6acc556f53e03a7aa4a9fcaab252668b689f3d6726be118ca7c1e2, BGXRANGED2 последним WeiDU, и 1170 исходных BCS блоков неизменны. Native compile выполняется в TEMP, не трогает игру.
- V3 guarded install: BGXRANGED_V3_GUARDED_INSTALL.py. Внутри пункта 132 автоматически выполняет нативную проверку и повторную независимую компиляцию, SHA сравнение результата, внешнюю SHA backup, WeiDU installation с новой компонентой BGXRANGED3 и самопроверку финального BCS. Установка только по точной фразе INSTALL_BGXRANGED_V3_WEAPON_FIX. Ошибка — STOP без автоматических повторов или дальнейших игровых изменений.
- Unified BGXAI_UPDATE.cmd не заменён; меню 132 = установить и автоматически проверить V3; 133 = read-only V3 status; 134 = последняя-компонента rollback V3→V2 с точной фразой ROLLBACK_BGXRANGED_V3_WEAPON_FIX. Старые пункты 1–131 сохранены. Для лимита длины PS1 укорочены ТОЛЬКО метки меню 117–130, обработчики не изменялись.
- SHA-pinned BGXAI_SYNC.ps1 immutable commit 87affe2d57fc65ffb61aa098cfdf8767e3f56c3c, 79971 byte SHA256 6b946655e6c1dd502e4bc1586c1c2c5f18c17b43a9006d7f78d5f1ede8cb5483; PIN commit 88ba914ba7a352c742ef19f32a36a2f7d5d92cb1; release manifest 0.3.56-BGXRANGED-V3-GUARDED 9 SHA-pinned source files.
- CI Windows PowerShell5.1 AST/updater 1–134/pinned source hashes run 44521364382 SUCCESS; V3 unit/mocked guarded installer tests run 44520984874 SUCCESS. User's actual EET V3 native compilation is NOT YET CONFIRMED, V3 NOT YET INSTALLED; V2 screenshot alone does not establish exact currently installed SHA, fail-closed prerequisite handles this.
- **Next action:** close game/InfinityLoader/WeiDU, launch SAME CMD, choose 132, provide exact consent phrase once. No separate 131 or 133 required on successful 132; program compiles, installs and checks automatically. If STOP, copy complete error and do not repeatedly attempt. If successful, in real game test Khalid bow and melee quickslots at HP 7/13 with close enemy, verify switches to sword, no unexpected pathing/heal issues. Backpack-only inventory auto-slot assignment not yet implemented; no unsafe FillSlot.
- User-approved **real effective weapon choice** (THAC0, APR, resistance, enchantment, relative risk and EE point-blank ranged -8) remains separate substantial development; V3 is focused correction, not universal DPS ranking. Multiclass/dual, mage retreat, thief 3E sneak and AOE navigation also remain future modules.
