# BGXAI R24 — работающая offline-связка существующего ранкера и NONINTERRUPT

**SOURCE ONLY. GAME DEPLOY NO. LIVE NO.** Этот каталог не содержит обновлятора и установки. Папка активной игры, BGXAI_UPDATE.cmd, EPS 18.4, BG Voice RU, BG_EET_RU и сохранения не изменяются.

## Что реально написано

`BGXAI_R24_SESSION_ADVISORY_BRIDGE_RO.lua` подключает существующие исходники из `BGXAI/patchsets/ranged_fighter_guarded_20261119/` через передачу зависимостей:

* `BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua` → `BGXAI_WEAPON_EFFECTS_V4.lua` → `BGXAI_WEAPON_PRIORITY_LUA_V3.preview`;
* альтернативный путь `BGXAI_WEAPON_APR_PROVENANCE_V5.lua` → `V4.choose` → `V3.preview`;
* оба пути входят в **существующий** `BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.step`.

`sessionToken` проверяется отдельно от `frame.snapshotId` (последний меняется на каждом игровом кадре). При изменении `sessionToken`, персонажа или pipeline предыдущая рекомендация отбрасывается; при обычном изменении снимка сохраняется непрерывность планирования. Проверены сценарии ручного приказа, EPS, лечения и кастования. Новый код **не создаёт собственный ранкер**.

Только `mode='OFFLINE_SYNTHETIC_FIXTURE'` запускает вычисление и помечает его как SYNTHETIC. Любая другая метка, включая реальные R17/R20/R22 — `KEEP_CURRENT_WEAPON_NO_DISPATCH`, без вызова ранкера. Любой результат возвращает 0 orders / 0 LOCALS / no queue clear / action preserved. Даже положительный synthetic совет не является лицензией на переключение.

**Важно:** токен сессии в тесте — специально заданный *искусственный* идентификатор. Пока у нас нет подтверждённого live-источника реального session identity и full alternate-slot APR/launcher/effects/EPS origin, функционал **нельзя** устанавливать в игру. `verified=true` из тестовых данных — не факт реальной EET.

## Проверка

В корне репозитория:

```bash
python -m unittest -v BGXAI/BUILD/R24_SESSION_ADVISORY_SOURCE_ONLY_20261123/test_r24_source_contract.py
lua5.4 BGXAI/BUILD/R24_SESSION_ADVISORY_SOURCE_ONLY_20261123/test_r24_session_bridge.lua
lua5.4 BGXAI/patchsets/ranged_fighter_guarded_20261119/test_weapon_noninterrupt_plan_v1.lua
lua5.4 BGXAI/patchsets/ranged_fighter_guarded_20261119/test_weapon_noninterrupt_integration_v1.lua
```

Linux runner выполняет Lua 12 R24 + исходные 22 NONINTERRUPT + 3 V3/V4/active-stats интеграционные теста. Windows и Linux выполняют новые 12 Python policy/hash тестов. SHA-манифест связывает исходники именно с проверенными git blob SHA. Не перепаковывать и не копировать базовые модули.

## Коррекция гипотезы

Сначала гипотетически предлагалось добавить `frame.snapshotId` в ключ существующего NONINTERRUPT. Это **неверно**: старый тестовый контракт меняет snapshotId каждый кадр и хранит совет между кадрами. Минимальный прототип не прошёл старую регрессию 22/22. Изменение **отменено**, старый исходник остался байт-в-байт прежним. В R24 вводится отдельная граница sessionToken *в обёртке*; полностью новый неподтверждённый live источник сессии не придумывается.

## Дальше

Нужен не ещё один mock, а доказанный источник в установленной игре для session / alternative weapon APR / launcher-ammo / active-effects / manual-EPS provenance. Продолжать безопасный source-only аудит такого источника, а при невозможности — честно обозначить runtime blocker, не изобретать game PASS.
