# BGXAI — V3/V4/V5: подтверждённо непригодный слот не требует выдуманного APR

Дата: 24.11.2026. Разработка **SOURCE ONLY**, установленную EET/EPS18.4, BGXRANGED6, R27, R28, WeiDU, BGXAI_UPDATE.cmd, BG_EET_RU, BG Voice RU и сохранения **не менять**.

## Исправленная игровая логика на уровне модели

Если у дальнего слота **подтверждённо** закончились боеприпасы (`ammoVerified=true`, `ammoCount=0`), либо ближний бой/путь **подтверждённо небезопасен**, этот кандидат исключается из ранжирования, даже если гипотетические APR/THAC0/урон/эффекты именно этого недоступного слота нельзя достоверно посчитать. Это не влияет на требования к полному, доказанному эффективному APR/урону **остающихся пригодных** альтернатив. Неизвестные боеприпасы/путь/выживаемость остаются строгими HOLD. V3 продолжает проверять идентичность слота, полноту колчана и текущую цель; нельзя подменять отсутствие данных значениями 0.

Изменены существующие исходники `BGXAI_WEAPON_PRIORITY_LUA_V3.lua`, `BGXAI_WEAPON_EFFECTS_V4.lua`, `BGXAI_WEAPON_APR_PROVENANCE_V5.lua`, `BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua`. Новый конкурирующий ранкер или движковый producer не создан. NONINTERRUPT не изменён; на каждом шаге сохраняются `ordersSent=0`, `dispatchAuthorized=false` и неприкосновенность текущей очереди.

## Локальные результаты

Изолированная пакетная регрессия через LuaTeX `--luaonly`, Python 3: **122/122 PASS** (V3 42, V4 30, APR V5 21, NONINTERRUPT 22, интеграция 7). Статическая проверка всех пяти рабочих модулей блокирует появления команд `SelectWeaponAbility`, `Attack`, `ClearActions`, `ActionOverride`, `SetGlobal`, очередей EEex и OS I/O в исполняемом Lua. Тесты проверяют истощение боеприпасов без гипотетического APR, подтверждённо опасный путь, неподтверждённую пригодность, fail-closed альтернативу и сохранение ручной/EPS очереди.

**Граница доказательства:** тесты локальные/синтетические; новый CODE/TEST = PASS, GAME DEPLOY = НЕТ, LIVE этой доработки = НЕТ. Независимый Ubuntu Lua5.3/Windows CI подтверждать по фактическому run после публикации; не выдавать отсутствие CI за PASS.

## Следующий реальный блокер

R27 LIVE 24/24 и R28 native ITM/2DA 4/4 — это реальные наблюдения/ресурсы, но не полноценный `COMPLETE_EFFECTIVE_SNAPSHOT`. Нельзя считать выбранный ammo slot 12 автоматически тем же самым, что launcher в quickslot 35–38: требуется достоверная native launcher/ammo пара. Также не подтверждены итоговые APR и эффекты **альтернативных** слотов, настоящее происхождение manual/EPS приказа и возможность безопасно поставить команду только на границе действий. До этих доказательств **никакого разрешения на SelectWeaponAbility / SetGlobal / BCS dispatch нет**.

Следующий исходный этап — изучение подтверждённых API и привязка native evidence; затем source-only исполняемый producer/consumer с fail-closed и тестами, native WeiDU compile; только после явного согласия — одна защищённая установка через существующий BGXAI_UPDATE.cmd и один игровой A/B. Повторять R27/R28, 165→6, устанавливать V7/166→2 или трогать EPS нельзя.

## Независимая CI и следующая безопасная сверка источников

**GitHub commit** `e7e7f553e998f5d0a0f8cda6015d47282c1a6d01`. Независимый run `45319538088`: **SUCCESS**; Linux `behavior-native-lua` (122/122) PASS, Windows `windows-static-no-game` PASS. https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45319538088 . Изменены исходники и тесты, **игра не менялась**.

Подтверждено прямым чтением **официального EEex v1.1.7**, а не предположением:

- `EEex_Resource_GetItemAbility` формирует адрес `... + Item_Header_st.sizeof * abilityIndex` и возвращает `Item_ability_st`, поэтому для `CItem:getAbility` остаются нерешённые вопросы stride, ABI и lifetime. Не вызывать опасный native pointer в установленной игре. Источник: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua#L161-L175
- `EEex_Sprite_Hook_CheckBlockWeaponHit` получает переданные движком `weapon` и `weaponAbility` только в событии проверки попадания; truthy callback может **заблокировать попадание**. Этот путь не доказывает APR альтернативных слотов или готовность нового порядка действий. Источник: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua#L1041-L1060
- `EEex_Action_ExecuteResponseStringOnAIBaseInstantly` явно предупреждает: действия вне `INSTANT.IDS` имеют **undefined behavior**. Нельзя использовать эту функцию для обхода очереди при переключении `SelectWeaponAbility`. Источник: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Action.lua
- Ранее полученные R27 (selected inventory slot 12 с AROW01, отдельный BOW05 в weapon quickslot 36) **не доказывают native ammo/launcher pairing**. Не присваивать `AROW01` как автоматически выбранный weapon quickslot.

**Решение:** дальнейший переход к исполняемому BCS producer остаётся заблокирован до достоверного активного APR альтернатив, launcher/ammo pairing и engine-side признака свободной manual/EPS очереди. Ложные `verified=true` и тестовые значения не снимают эту блокировку. Следующий безопасный этап — искать поддерживаемый EEex/native read-only источник этих фактов, а не повторно запускать R27/R28 или опасный API. CODE/TEST PASS, DEPLOY/LIVE новой логики НЕТ.