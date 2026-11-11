# BGXAI — LIVE результаты Ctrl+Alt+F11 и Lua-счётчиков (11.11.2026)

## Подтверждённое пользователем по трём игровым скриншотам

В игре Baldur's Gate - Enhanced Edition Trilogy v2.6.6.0 через установленный 044 диагностический хоткей **Ctrl+Alt+F11** вывел:

`BGX44: 043P loaded=true listener=true enabled=true attacks=0 errors=0 notice=false API=true/true last=-`

Встроенный Lua-ввод действительно работает: команда `BGX43Probe.snapshot()` с `C:DisplayText` была исполнена (а не только отображена), результат:

`H=0 BR=0/0 LAST=none`

Вторая команда прочитала LOCALS портретов:

- P2: F=1, Q=0
- P3: F=0, Q=0
- P4: F=1, Q=0

В предоставленных кадрах персонажи не подвергались удару. Поэтому `H=0` и `BR=0/0` в текущем сеансе не доказывают, что во время прежнего боя Шанка weapon-hit hook отсутствовал. Счётчики сбрасываются после перезапуска Lua/game.

## Критическое различие в исходном коде 056

`BGX44` печатает `listener = BGX43Probe.installed`, что подтверждает **action listener**. `API=true/true` относятся к функции `EEex_Action_AddSpriteStartedActionListener` и API портретов, **не к weapon-hit hook**.

В установленном 056 `BGX43Probe.init()` может выставить `installed=true`, даже если `EEex_Sprite_AddBlockWeaponHitListener` отсутствует или не зарегистрировался. В `snapshot()` для этого есть раздельные поля `weapon_hit_listener`, `weapon_hit_registered`, `weapon_hit_errors`, а также глобальный `BGX43Probe.lastError`.

Первый дополнительный безопасный тест (одна read-only Lua-команда, без нового боя и без установки 057):

```lua
local s=BGX43Probe.snapshot();C:DisplayText("HITAPI="..tostring(s.weapon_hit_listener).." REG="..tostring(s.weapon_hit_registered).." HE="..tostring(s.weapon_hit_errors).." ERR="..tostring(BGX43Probe.lastError))
```

Если HITAPI=false или REG=false — определить причину по ERR, проверить фактический EEex 1.2.0 API/регистрацию и готовить минимальный исправленный компонент с backup/rollback (не менять игру вручную). Если HITAPI=true и REG=true — регистрация подтверждена только программно; следующий шаг зависит от появления настоящего события попадания в обычной игре. Нельзя утверждать, что попадания до этого уже виделись.

## Дополнительная особенность 056

Lua `BGX52Bridge.prepare()` выбирает **одного** F=ON охранника среди Player2–Player6 с `m_nModalState==0`, ближайшего к защищаемому. При двух F=ON (P2 и P4) выбор Тараны не гарантирован. По текущему скриншоту нельзя восстановить расположение/флаги момента прежнего боя и определить выбранного защитника. Проверка `bridge_last.chosen_guardian` нужна только после фактического события.

## Статус релизов и безопасность

- 056 ранее установлен и статически сверён; в этом шаге НЕ модифицировался.
- 044 hotkey и Lua-вывод теперь LIVE подтверждены.
- 057 — отдельно опубликованный SOURCE ONLY, НЕ установлен; до выяснения weapon-hit hook его установка для чтения счётчиков не нужна, так как Lua-команды уже работают.
- Не повторять специально бой с Шанком, не откатывать/переустанавливать мод и не требовать старые EET архивы. Продолжать диагностику от поля `weapon_hit_registered`.