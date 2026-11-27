# BGXAI — 27.11.2026: real-GAM pilot and R37 identity gate, source-only CI complete

**Latest status:** `SOURCE_ONLY_R37_INV3_IDENTITY_SINGLE_LISTENER_CI_PASS; NATIVE_EET/DEPLOY/LIVE_HOLD`.

## Проверенные факты

1. Пользовательский `BALDUR(1).gam` уже обработан только на чтение; original SHA256 `7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c` неизменен. Сохранение `GAMEV2.0` содержит 6 CRE V1.0; Джаган (`partyIndex=1`, saved cleric class3) имеет одну `STAF01` в рюкзаке (SLOTS.IDS 20 = SLOT_MISC5) и пустой быстрый слот оружия 35 = SLOT_WEAPON0, flags=1, charges=[0,0,0]. Это доказательство сохранённого состояния, а не идентичности активного персонажа или возможности носить предмет.
2. V3 local-armed BAF builder и manifest `BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127` уже SOURCE TESTED: реальные GAM offline tests 24/24 PASS, на Windows/Linux GitHub CI 20 PASS + 4 EXPECTED SKIP без приватного GAM, run 45941144247. Скрипт не устанавливался и не вооружён, actorId из GAM не выдумывать.
3. Создан **новый read-only actor identity module** `BGXAI/BUILD/WEAPON_XEQUIP_IDENTITY_RO_V1_20261127/BGXAI_XEQUIP_IDENTITY_RO_V1.lua` и 30 adversarial Lua-mock tests. Сравнение фактического EEex `m_id`, портретного id, `m_typeAI.m_Class`, всех 38 наблюдаемых слотов 0..38, кроме имплицитного `SLOT_FIST=10`, предмета и charges/flags, повторной проверки контекста и полного top-level отсутствия дублей. Любая неоднозначность => HOLD. Положительный вывод = только READONLY advisory, `armAuthorized=false`, `ordersSent=0`, `localsWritten=0`; не приравнивать к session proof, idle proof, engine item usability proof.
4. Independent CI **SUCCESS** [run 45942119133](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45942119133): Lua 5.3, Lua 5.4 и LuaJIT **по 30/30 PASS**, Windows/Linux статическая защита 5 тестов PASS.
5. Исходная копия R37+InventoryV3 `BGXAI/BUILD/R37_INVENTORY16_SINGLE_CALLBACK_SOURCEONLY_20261126/M_BGXR27_R37_INV3_SOURCE_ONLY.lua` дополнена **четырьмя помеченными вставками** в `BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua`. Добавлена одна ограниченная `[BGXID]` read-only статусная строка после исходных `[BGXR27]`, `[BGXR37]`, `[BGXINV3]` без engine actor ID. Старые строки, логика и один listener сохранены.
6. **Independent integration CI SUCCESS [run 45942389902](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45942389902)**: Windows и Linux **6/6 static tests PASS**, после удаления ровно четырёх вставок исходный Lua **байт-в-байт** равен оригиналу. Linux native Lua 5.3/5.4/LuaJIT: **30/30 tests для identity checker на каждом** + R37/INV3 7-transition same-callback regression PASS на каждом. Игровых действий = 0 в моках. GitHub commit первого интегрированного исходника `cae00eeefdb39dca3c2f97ac5275dfd4af25aecf`. Главный callback не дублирован.
7. Первая инертная реальная EET native BAF проверка из меню 175 уже PASS, **её повторять не нужно**. Она не доказывает компиляцию нового активируемого V3 BAF.

## Важное ограничение, подтверждённое архитектурой

`EEex_Action_AddSpriteStartedActionListener` в R37 означает **событие начала действия**: по нему нельзя объявлять, что текущий игровой приказ не выполняется и персонаж простаивает. `ActionListEmpty()` также не устраняет риск ручной/EPS команды и межкадрового изменения контекста. Поэтому интегрированный кандидат **НИКОГДА** не пишет `BGXW3ARM=1` и не вызывает `XEquipItem`.

## Следующие незавершённые gates (строго по очереди)

- Проверить в реальном текущем EET средствами уже существующего однократного updater маршрута, что **тот же Джаган и тот же посох** действительно находятся в игре; событие R37 само по себе этого не гарантирует. Интегрированная версия R37 — только кандидат, не заменять установленный Lua без backup и typed разрешения.
- Разработать и проверить **изолированный idle/preflight** из явного текущего состояния вне боя; actor-local arming только после подтверждения identity/kit/ITM restrictions/queue/manual-EPS и stable live state. Без runtime этой доказательности action remains HOLD. Не добавлять конкурирующий callback.
- Native compile **точного активного** V3 BAF и BCS binary preservation против установленного baseline (не повторять menu175); защищённый installer в том же `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, без второго обновлятора, SHA checks, внешний backup, WeiDU last-only, отдельное typed user approval.
- Первый живой тест вне боя на disposable save с `STAF01` 20→35, before/after conservation, запрет потерянного предмета/зарядов, корректность классов и отсутствия лишних действий; не объявлять LIVE PASS до этого.

## Не трогать

Game root, WeiDU, V6/R29/R37, EPS, BG_EET_RU, BG Voice RU, UI, сохранения и единственный CMD. Права на установку или исполнение не получены. Никаких новых пользовательских действий в рамках этого read-only шага не требуется.

**Status by stage:** CODE YES; OFFLINE+CI PASS; real EET native V3 BAF NOT TESTED; GAME DEPLOY NO; LIVE TRANSFER NO; PLAYER ACTION REQUIRED NOW NO.