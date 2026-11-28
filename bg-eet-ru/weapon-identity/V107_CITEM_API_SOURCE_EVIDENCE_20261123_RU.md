# BG_EET_RU — V107 CItem API audit (SOURCE EVIDENCE ONLY)
Дата: 2026-11-23. Режим: READ ONLY / SOURCE ONLY. Это не Windows runtime test, не установка и не подтверждение реального RESREF.

## Зафиксированная исходная точка
- V106 LIVE PASS означает только регистрацию обработчика и захват двух событий (attackRoll=20 и 15, во втором есть launcher:userdata); оружие/боеприпас/попадание/промах/строка журнала не подтверждены.
- GitHub bg-eet-ai: `bg-eet-ru/onefile/release.json` по фактическому чтению сохраняет version=106, game_writes_allowed=false.
- V107 `BG_EET_RU_V107_CITEM_IDENTITY_SOURCE_ONLY.lua` по фактическому чтению — enabled=false, capture_native_item_refs=false, никаких зарегистрированных хуков, IO или игры; внутри отключённая гипотеза `item.cResRef:get()`.
- Текущая ветка `bg-eet-ai`; публичная публикация SOURCE не равна DEPLOY.

## Новые подтверждения по общедоступным исходникам
1. Gibberlings3 Tweaks Anthology `cdtweaks/luke/lib/sprite/get_selected_weapon.lua`: получает CItem через `sprite.m_equipment.m_items:get(...)` и извлекает `selectedWeapon.pRes.resref:get()`; также отдельно работает с launcher CItem. Пин: https://github.com/Gibberlings3/Tweaks-Anthology/blob/7649ced6cd25865874d787ec1a9abbc67b068729/cdtweaks/luke/lib/sprite/get_selected_weapon.lua
2. Gibberlings3 `cdtweaks/luke/lua/npc/dorns_sword.lua`: такое же чтение `selectedWeapon.pRes.resref:get()` для экипированного оружия. Пин: https://github.com/Gibberlings3/Tweaks-Anthology/blob/7649ced6cd25865874d787ec1a9abbc67b068729/cdtweaks/luke/lua/npc/dorns_sword.lua
3. StickLuaFunctions `M_Stick.lua`: `rightHandItem.cResRef:get()` на CItem, полученном из слота экипировки. Пин: https://github.com/xbigxiangx-dot/StickLuaFunctions/blob/5872ed041f9dba47eac030bee8b257d0cbaf225a/StickLuaFunctions_v0.11.0-Alpha/StickLuaFunctions/LUA/M_Stick.lua
4. EEex `EEex_Sprite.lua`: `item.pRes` используется в обработчике с CItem, но это не доказывает жизненный цикл CItem в V105/V106 hit callback. Пин: https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite.lua

**Вывод:** есть два распространённых Lua-пути получения RESREF у CItem: `item.cResRef:get()` и `item.pRes.resref:get()`. Оба встречаются в живых исходниках модов, но ни один пока не проверен для конкретной установленной версии EEex, конкретного callback V106 и передаваемого context.weapon/launcher. В примерах item обычно взят из инвентарного слота, а не из нашего callback. НЕЛЬЗЯ считать эти примеры runtime PASS.

## Установленные риски
- `pcall` защищает от Lua-ошибки, но НЕ от нативной ошибки памяти / ABI / use-after-free.
- Перенос `CItem` за время callback и сохранение userdata в отчёте запрещены. Примитивные строки, типы и счётчики — допустимы.
- `launcher` — не идентификатор отдельной стрелы, болта или пули; `context.weapon` может быть метательным предметом, для которого отдельного ammo нет.
- Нельзя выводить hit/miss из двух capture-событий или привязывать их к строкам журнала без отдельного доказательства.
- Не менять V101 журнал, V85 Lua, BGXAI, Voice, сейвы, игровой код и `release.json`.

## Следующие обязательные условия (gate)
1. READ ONLY изучить точную установленную версию EEex, тип callback и contract `context.weapon`, `context.launcher`, включая время жизни userdata и поддержку выбранного поля `CItem` в binding; если доказательств недостаточно — HOLD.
2. Только затем разработать отдельную ограниченную/отключённую по умолчанию проверку RESREF на месте callback. `pcall` не считается механизмом безопасности нативного вызова. Без независимого доказательства допуска к native read эту ветку не активировать.
3. Интеграция — исключительно через существующий `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`, pin SHA, резервная копия вне игры, защита от частичной установки, точное typed approval, rollback. На сегодня никакой новой установки нет.
4. Только фактический LIVE RESREF может открыть следующую стадию; ammo, промахи и связь с UI-журналом проверяются отдельно. V106 захват повторять не требуется.

Статусы: API SOURCE EXAMPLES = FOUND; USER BUILD BINDING / ABI = UNKNOWN; CALLBACK POINTER LIFETIME = UNKNOWN; V107 = SOURCE ONLY; V106 = LIVE TRANSPORT PASS ONLY; GAME WRITES = 0 (в рамках этого аудита).


## Продолжение исходного аудита — прямое использование именно того же callback

- В [Gibberlings3 Tweaks Anthology / overwhelming_devastating_critical.lua](https://github.com/Gibberlings3/Tweaks-Anthology/blob/7649ced6cd25865874d787ec1a9abbc67b068729/cdtweaks/luke/lua/class/overwhelming_devastating_critical.lua) найден реальный listener `EEex_Sprite_AddAlterBaseWeaponDamageListener(function(context)` с непосредственным `context.weapon.cResRef:get()` внутри callback, а также полями `context.launcher`, `context.ability`, `context.attackRoll`. Это stronger direct-callsite evidence, а не проверенный runtime пользовательской сборки.
- В [upstream EEex_Sprite.lua](https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite.lua) обработчик соответствует `CGameSprite::Override_Damage`; [EEex_Sprite_Patch.lua](https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite_Patch.lua) подключает вызов из `CGameSprite::Swing`. Сигнал урона не подтверждает охват промахов.
- Подготовлен без регистрации/установки `BG_EET_RU_V107_GUARDED_CALLBACK_SOURCE_ONLY.lua` с `enabled=false`, `native_abi_verified=false`, `explicit_native_read_consent=false` и cap=16 событий. Готов только к следующей оценке риска; **ни один флаг не выставляется автоматически**.
- Локальный Lua 5.4 simulated test PASS на отключение нативного чтения, не изменение контекста, bounded records и статус UNKNOWN для ammo/hit/miss/log mapping. SHA256 локального Lua файла: `8557c676b0622a8dc0f746041405d3d74aff271d04d09fef45500e938fb1088f`; опубликованный Git blob `200e220ef5f31ef8a68ffcbf30a08fcc445733cd` равен локальному `git hash-object`, поэтому опубликованы в точности протестированные байты.
- **HOLD:** факт API-примера недостаточен для доказательства crash-safety конкретной Windows/EEex установки. Изменений `release.json`, `BG_EET_RU_UPDATE.cmd` и игры не было. Пользователю не требуется запускать отдельные тесты V92–V106.

## 28.11.2026 — источник CItem IDENTIFIED (расширение прежнего V107, SOURCE ONLY)

**Уже сделано → доказательство → недостающая дельта → минимальный шаг:**

- Установленный V160 уже успешно читает `context.weapon.cResRef:get()`; V162+V163 добавили 64+59 русских названий. Состояние опознания для 827 архивных dual-name кандидатов всё ещё не доказано. Это не новый callback/ABI-проект, а продолжение существующего V107.
- **Новое независимое SOURCE evidence:** [BattleSense Creature Info, строки 927–945](https://github.com/JasZy/BattleSense/blob/61e70ea99eeaa210f425ebac48a91fd5fcb13d99/BattleSense/copy/creatureinfo/ZJCreInf.lua#L927-L945) находит `item = sprite.m_equipment.m_items:get(specificID)` и `identified = EEex_IsBitSet(item.m_flags, 0)`, затем использует `itemHeader.identifiedName` либо `genericName`. [BattleSense README](https://github.com/JasZy/BattleSense) требует EEex v1.3.1 и заявляет поддержку EET. Это сценарий **предмета из слота**, не hit context.
- **Второе независимое SOURCE evidence:** [SadoEE M_SQCAIN.lua, строки 23–41](https://github.com/sad0/SadoEE/blob/ab548abe839b726b0c487ad91228a53cafce99b4/SadoEE/camp/M_SQCAIN.lua#L23-L41) определяет `FLAG_IDENTIFIED = 0x1` и проверяет `EEex_BAnd(it.m_flags, FLAG_IDENTIFIED) == 0` на `m_items:get(slot)`. Это подтверждает маску бита 0, но НЕ жизненный цикл hit callback.
- **Upstream EEex:** [EEex_Assembly.lua, строки 40–42](https://github.com/Bubb13/EEex/blob/d368165e307d629b7dc5ee5720e37c16d46c3e49/EEex/copy/EEex_scripts/EEex_Assembly.lua#L40-L42) определяет `EEex_IsBitSet(original, isSetIndex)` как маску `(1 << index)`.
- **Фактические данные игры пользователя из уже загруженного архива `SEND_TO_CHATGPT_BG_EET_RU(20261128-063022).zip`:** 53_V107 доказывает статический SHA256 установленного `EEex.dll` `b6c7c98804360cb46531db75ab9608e378fd403d60c29c0e29946a60a334276a`, размер **1282048** байт, `EEex_Sprite.lua` SHA256 `4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28`. Публичный Bubb13 master `EEex.dll` для v2.6.6.0 имеет **1302528** байт: НЕ считать его идентичной установленной бинарной сборкой. Отдельный `LuaBindings.dll`/ABI поля `CItem.m_flags` на установленном ПК по данным ZIP не проверен. Не запускать новые установочные тесты без необходимости.
- **CODE SOURCE ONLY:** расширен РАНЕЕ СУЩЕСТВУЮЩИЙ [V107 guarded callback](BG_EET_RU_V107_GUARDED_CALLBACK_SOURCE_ONLY.lua), без нового слушателя. `read_citem_identification` читает `item.m_flags` только внутри callback, лишь при шести явных гейтах (`native_abi_verified`, `explicit_native_read_consent`, `identification_probe_enabled`, `current_x64_item_flags_binding_verified`, `callback_citem_flag_lifetime_verified`, `explicit_identification_read_consent`), ВСЕ значения по умолчанию false; возвращает только строки `IDENTIFIED_BIT0`/`UNIDENTIFIED_BIT0` или безопасный HOLD. Никаких изменений предмета, боя, логов или Lua, установленного в игре.
- **TEST:** [7 тестов на Lua 5.x через Lupa 2.8](test_V107_CITEM_IDENTIFICATION_SOURCE_ONLY.py), синтетический userdata и отсутствие чтения без гейтов, неверные значения, бит0, ограничение записей, отсутствие хуков. [GitHub CI Windows/Linux](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118335489) PASS; это **не настоящий EEex runtime test**.

**Итоговый gate:** `SOURCE_FIELD_AND_MASK_CORROBORATED / USER_X64_CONTEXT_IDENTIFICATION_HOLD`. Источники указывают на реальную общую механику `CItem.m_flags & 1`, но не доказывают, что `context.weapon` установленной версии EEex содержит нужный флаг опознания игрока и что чтение безопасно на живом указателе. `pcall` не ловит native fault. Никакой V164, третьего updater, новой строки журнала или перехода на 827 имён без отдельного подтверждения. Сохранять текущие 123 установленных RESREF-подписи и точное hit/miss→combatLog JOIN_HOLD.
