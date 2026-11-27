# BGXAI R39 — первое одноразовое XEquipItem: более строгий BAF, SOURCE ONLY

**27.11.2026. Реализация:** `BGXAI_R39_STAGED_XEQUIP_V1.py`, полученный `BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf`, регрессия `test_r39_staged_xequip_v1.py` (**20/20 PASS локально**). **НЕ устанавливалось, НЕ компилировалось в пользовательском EET, НЕ выдаёт разрешения.** Исходные R37/R38, EPS, V6/R29, сейвы, WeiDU и единый updater не изменялись. Полная автономная экипировка не достигнута.

## Что улучшено по сравнению с V3

1. Для сохранённого Джагана `*GCLERIC` (partyIndex=1) и реального `STAF01` в `SLOT_MISC5` (slot 20), пустого `SLOT_WEAPON0` (slot 35), взят **точно прежний V3 witness** `2110908191`, никаких вымышленных `actorId`.
2. Вместо немедленного переноса при первом выполнении условий — три BAF-блока: сначала **abort expired**, потом **equip if still safe**, затем **warmup**. Внешний, отдельно авторизованный армер должен первоначально поставить actor-local `BGXW3ARM=1`, `BGXW3TAG=witness`, `BGXW3TRY=0` и `BGXW3QST=0` **только** этому актёру. Код сам не ставит ARM=1.
3. Warmup повторно читает `ActionListEmpty`, `CombatCounter(0)`, отсутствие видимого противника, истечение EPS `MO_SpellCast`, спокойное modal/state и предметы. Он выставляет actor-local `BGXW3QST=1`, `BGXW3QTM=ONE_ROUND`, `BGXW3MAX=TWO_ROUNDS`.
4. Equip ожидает прохождения одного игрового раунда **и** ещё не истёкший предел в два раунда, затем **повторно** проверяет все условия и выполняет не более **одного** `XEquipItem`. До команды расходует ARM/TAG/TRY, чтобы повторный перенос не происходил. Abort для просроченного окна имеет приоритет; нет `Stop`, `ClearActions`, `FillSlot` или нового слушателя EEex.
5. Офлайн-тест проверяет точный GAM-манифест, запрет подложных `actorId` / `installApproved`, witness, source/target, отсутствие опасных команд, строгие условия обоих блоков, окно и недопущение саморазрешения.

## Незакрытые блокеры, которые R39 НЕ скрывает

- **Нет authenticator session/actor identity для arming.** Одного совпадения в игровом R38 и portraitIndex недостаточно. ACTOR LOCALS сохраняются в GAM, поэтому особенно опасна перезагрузка при незавершённом ARM; Таймеры сами по себе не доказывают подлинность сеанса. Требуется отдельный механизм обнуления/привязки ARM к *каждой* игровой сессии ДО запуска активного BAF.
- `ActionListEmpty` и повторные проверки **не доказывают непрерывного простоя** между двумя BAF-блоками и происхождение manual/EPS. Выбранный «один раунд» — ограниченная задержка, **не гарантия**.
- Не прочитан установленный `STAF01.ITM` и текущий kit/usability Джагана; `CLASS=3` из GAM — не полная проверка доступа к оружию.
- Нет native EET compile **точного R39 BAF**, нет доказательства сохранения исходных BCS/WeiDU, внешнего backup и отдельной typed-авторизации. В коде `dispatchAuthorized=false`, `ordersSent=0`.
- Не подтверждён перенос предмета в игре, количество/флаги/заряды до/после и отсутствие конфликтов EPS. **Это кандидат, а не исправленная работающая функция.**

## Следующий строго необходимый шаг

Изучить механизм EEex/EPS **session-only arming**, реализовать его в *существующем* единственном R38 listener (без регистрации второго), с отменой на загрузке, смене актёра, начале движения/боя или ручных/параллельных приказах. Затем проверять актуальный установленный ITM/kit и native BAF; только после typed разрешения на игровую установку — пилот на расходном сохранении. Никаких повторов старого 176→4 / 176→6 от пользователя.

## Проверенные справочные данные

- `SLOTS.IDS`: 20=`SLOT_MISC5`, 35=`SLOT_WEAPON0`, 34 — особый магический слот: https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm
- `XEQUIP.IDS`: `1 EQUIP`: https://gibberlings3.github.io/iesdp/files/ids/bgee/xequip.htm
- `GTIMES.IDS`: `6 ONE_ROUND`, `12 TWO_ROUNDS`: https://gibberlings3.github.io/iesdp/files/ids/bgee/gtimes.htm
- `XEquipItem` action 385 и `AttackOneRound` limitation: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm
- `ActionListEmpty()` / `CombatCounter(0)` caveats: https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm
