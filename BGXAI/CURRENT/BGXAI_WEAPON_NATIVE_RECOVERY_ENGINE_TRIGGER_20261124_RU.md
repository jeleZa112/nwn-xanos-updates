# BGXAI — текущая точка: бессмысленные атаки по иммунному врагу и native WeaponCanDamage

**Дата:** 24.11.2026. **Фаза:** CODE / локальный OFFLINE TEST. **DEPLOY и LIVE новой логики: НЕТ**. GitHub: `jeleZa112/nwn-xanos-updates`, branch `bg-eet-ai`, `BGXAI/patchsets/ranged_fighter_guarded_20261119/`. Игра, EPS18.4, SCS, EEex1.1.7, BG_EET_RU, BG Voice RU, сохранения, единый `BGXAI_UPDATE.cmd` не изменены.

## Реально сделанная функциональная поправка

В существующем `BGXAI_WEAPON_PRIORITY_LUA_V3.lua` обнаружена ошибка: при полностью непроницаемом **текущем** оружии более слабый, но действенный альтернативный слот не проходил порог 2 DPR / 15% и система советовала оставить заведомо бесполезное оружие. Исправлено **в том же оценщике**:

- если доказан полный иммунитет врага к текущему оружию, либо подтверждён нулевой эффективный урон и нулевая ценность эффектов, обычный порог переключения не применяется;
- предлагать другое оружие допустимо только при доказанном положительном DPR и положительной полезности **альтернативного** слота, с проверкой целевой защиты, боеприпасов, дальности и экипируемости;
- 99% сопротивления (не 100%) по-прежнему подчиняется обычному порогу; если текущее оружие имеет значимую подтверждённую **нефизическую** ценность, оно не считается бесполезным;
- при неизвестном происхождении данных или занятости ручной/EPS очереди остаётся HOLD; все решения advisory-only `dispatchAuthorized=false`.

Тесты: предыдущие **433** плюс **6** адресных кейсов = **439/439** на локальном LuaTeX, без изменения игрового состояния. Нельзя считать их игровыми проверками.

## Новый практически полезный native-источник BG2EE

IESDP BG(2)EE документирует встроенный триггер `0x40F2 WeaponCanDamage(O:Object*,I:Hand*HAND)`: может ли **текущее оружие указанной руки** причинить ненулевой урон указанной цели; `0x40EC WeaponEffectiveVs()` проверяет способность поразить цель, `CanEquipRanged()` — наличие готового дальнего оружия. `HAND.IDS`: `1 MAINHAND`, `2 OFFHAND`. Это движковые **триггеры**, не прямой доступ к `CItem:getAbility`, опасным EEex указателям или статическим свойствам другого слота.

Источники: https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm#0x40F2 ; https://burner1024.github.io/iesdp/files/ids/bgee/hand.htm . Документ BG2EE **не** доказывает присутствие точных сигнатур в пользовательском EET `TRIGGER.IDS`/`HAND.IDS`: native WeiDU compile в установленном EET пока не выполнен.

## Реально подготовленная интеграция BCS без второго ранкера

Изменён **существующий** `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf`: четыре исходные оптимизационные ветки запросов `BGXW3_REQ=1..4` оставлены байт-в-байт (SHA256 первоначального содержимого `f95086c3bb629aa482a8f99443fee577176b2612393be7ffac0f530c2898bf18`). Добавлены четыре исходные **SOURCE-ONLY** ветки `REQ=5..8` на соответствующие слоты `SLOT_WEAPON0..3`, выполняющиеся только если `!WeaponCanDamage(NearestEnemyOf(Myself),MAINHAND)` и обычные F/heal/party/target/ActionListEmpty/lease guards соблюдены.

**КРИТИЧЕСКИ:** эти ветки физически способны выполнять `SelectWeaponAbility`, если будут когда-либо установлены. Сейчас они **не установлены и не активны**. Переменная `BGXW3_NATIVE_PROVENANCE` сама по себе не доказывает происхождение ручной/EPS очереди, а engine `WeaponCanDamage()` **не оценивает альтернативный слот**. Для безопасности нужен отдельный real-verified producer, подтверждённая target/weapon/launcher-ammo совместимость, безопасная action boundary и отдельное typed разрешение. Никаких новых EEex listeners или BCS-установок нет. Не публиковать новый пункт установки без прохождения этих границ.

Добавлен `test_weapon_native_recovery_baf_v1.py` с контрактом: ровно восемь веток, неизменность четырёх оригинальных, запрет `Attack`/`ClearActions`/unconditional equips, 4× текущие иммунитеты и все F/heal/lease guards. Подключён к существующему `run_weapon_priority_v3_regression.py --static-only` и в Windows/Ubuntu CI. **Это статический BAF audit, не native WeiDU compile**.

## Выполненные и не выполненные проверки

- [x] LuaTeX `439/439` offline suite PASS; Python static full advisory chain PASS; BAF guard audit 8/8 PASS.
- [x] Независимая CI — commit `4e64224a59c146242ffb030f9d8c6e25e9f749b6`, run `45322504666` **COMPLETED / SUCCESS**. Ubuntu: **Lua 5.3 439/439 PASS, Lua 5.4 439/439 PASS, LuaJIT 439/439 PASS**; каждый из трёх раз успешно прошёл 8/8 BAF static guard; Windows статическая проверка **SUCCESS**. Точное подтверждение — прочитанные журналы jobs `138204151718` и `138204151413`. Это 1317 повторных выполнений 439 уникальных OFFLINE случаев, без WeiDU и игры.
- [ ] Installed native `TRIGGER.IDS`/`HAND.IDS` и WeiDU compile — **НЕ ПРОВЕРЕНЫ**.
- [ ] Состояние очереди ручных/EPS приказов, ammo/launcher для предлагаемого альтернативного слота, target/actor provenance — **НЕ ДОКАЗАНЫ**.
- [ ] Истинная автономная смена оружия в игре новой V3 / native recovery — **НЕ LIVE**.

## Ближайший безопасный следующий шаг

После CI PASS **не повторять R27/R28/V6, не плодить ранкеры, не запрашивать `+`**. Следующий реальный рубеж: связать native engine-evidence текущего оружия с существующей цепью `V3.preview + NONINTERRUPT` через producer, которому можно доверить manual/EPS queue и точное свойство альтернативы. До этого BAF не устанавливать и не запускать game test. Для установки обязательно закрытая игра, один `BGXAI_UPDATE.cmd`, pinned SHA, external backup, native WeiDU last-only и отдельное typed подтверждение.


## Независимый CI и оставшееся ограничение (после CODE PASS)

- Код опубликован одним коммитом `4e64224a59c146242ffb030f9d8c6e25e9f749b6`; 7 файлов, включая изменённые существующие scorer/consumer и общую CI. https://github.com/jeleZa112/nwn-xanos-updates/commit/4e64224a59c146242ffb030f9d8c6e25e9f749b6
- Успешный GitHub run https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45322504666 (по результатам read-only проверки фактических job logs). **Игровых команд этот тест не выполнял**.
- Параллельно ранее красный workflow `bgxai-wtasight-enemy-guard.yml` опять FAIL в другом run `45322504878`: первая проверка в embedded Python ожидает устаревший manifest version `0.3.76-V6-GUARDED-PILOT` и 34 файла, а текущий `manifest_updater.json` уже имеет `0.3.90-V7-R27-DPLAYER-FUNCTIONAL` и 35 файлов. Это отдельный stale-check; **не маскировать его и не заявлять общую CI зелёной**. Файлы обновлятора и manifest в этом изменении не трогали.
- **Самый большой блокер gameplay:** доступен поддерживаемый engine-native `WeaponCanDamage` для **текущей** руки; не подтверждены native installed IDS/WeiDU compile, доступность/effectiveness предлагаемого **альтернативного** слота и provenance ручных/EPS действий. Не создавать рискованного установщика и не просить повтор R27/R28. Если источников нет — оставить **NO DISPATCH**, не приравнивать BAF static PASS к LIVE.