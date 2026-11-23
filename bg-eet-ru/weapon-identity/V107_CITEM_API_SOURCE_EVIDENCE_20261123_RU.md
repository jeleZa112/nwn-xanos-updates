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
