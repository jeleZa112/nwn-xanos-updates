# BGXAI R40 — сброс сохранённого разрешения на XEquipItem при загрузке игры (SOURCE ONLY)

**27.11.2026.** Найден конкретный механизм снятия одной из главных опасностей R39: actor-local `BGXW3ARM` и связанные переменные переживают сохранение. У установленного EEex семейства 1.1.7 API **уже присутствуют**:

- `EEex_GameState_AddDestroyedListener(callback)` — callback после очистки игрового сеанса, например при загрузке save;
- `EEex_Sprite_AddLoadedListener(callback)` — вызывается через `EEex_Sprite_LuaHook_OnAfterEffectListUnmarshalled(sprite)`;
- `EEex_Sprite_GetLocalInt(sprite,name)`, `EEex_Sprite_SetLocalInt(sprite,name,value)` — работа с локальными переменными актёра.

Это проверено по **оригинальным исходникам tag `v1.1.7`**:
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_GameState.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua

Версия и точные API текущей **модифицированной установленной** копии игрока всё равно должны быть подтверждены через существующий однократный обновлятор; наличие исходника в upstream не равно наличию действующего hook или гарантированному порядку вызовов.

## Реализовано

`M_BGXW3_SESSION_RESET_V1.lua` — **не устанавливается и не импортируется сам**. Принцип:

1. Регистрация возможна только через явное вызванное извне `register` с точным approval-токеном и `preGameStartupVerified=true`, после проверки четырёх нужных EEex API. Само значение boolean из тестового порта **не доказывает** реальную стадию игрового запуска; она должна быть установлена доверенным preflight.
2. Регистрация только **двух lifecycle hooks** (destroyed и loaded). Никакого дополнительного listener на `ActionStarted`, не трогает существующий R38 observer.
3. После `destroyed` сбрасывается только Lua epoch; все указатели на умерших спрайтов запрещены. На callback loaded сначала читаются **все шесть** actor-local переменных: `BGXW3ARM`, `BGXW3TAG`, `BGXW3TRY`, `BGXW3QST`, `BGXW3QTM`, `BGXW3MAX`.
4. Если все равны нулю, **нет записей**. Если найдена незавершённая попытка, сначала `BGXW3ARM=0` и немедленный readback; только потом обнуляются остальные пять. При частичном отказе уже подтверждённый нулевой ARM делает R39-перенос невозможным; при отказе очистки ARM — HOLD, без утверждения о безопасности.
5. Не записывает `ARM=1`, не вызывает `XEquipItem`, не работает с боевыми приказами и не меняет чужие локальные переменные.
6. Если второй lifecycle hook не может быть зарегистрирован после первого, остаточный callback остаётся инертным (`enabled=false`).

Проверка источника Python: **13/13 static tests PASS локально**. Встроенный `test_session_reset_v1.lua` — **22 отдельные adversarial mock-проверки**, которые должны пройти в Lua 5.3/5.4/LuaJIT в CI; локального интерпретатора Lua в текущем инструментальном контейнере нет. Не называть mock suite PASS до реального запуска.

## Непроверенные блокеры

- Мы **не подтвердили**, что onLoaded всегда исполняется **до первого AI script tick** в пользовательском EEex+EET+SCS+EPS, при обычной и быстрой загрузке, в том числе при загрузке сразу после сохранения с ARM=1. Нужен **один защищённый runtime proof** в уже существующем updater, НЕ повтор R38 capture.
- R40 является **только защитой от устаревшего ARM**, а не authenticator identity на текущей игровой сессии, не механизмом ARM=1 и не подтверждением непрерывного простоя/источника приказов.
- Установленный STAF01.ITM, класс/kit/эффекты Джагана и право экипировки движком не проверены.
- Нет native EET compile и защищённой установки действующего R39 BAF, typed согласия, backup и rollback.

**Фактический результат:** CODE YES; STATIC TEST 13/13; LUA MOCK NOT EXECUTED YET; NATIVE/DEPLOY/LIVE NO; GAME ORDERS 0; USER ACTION NOW NONE. Рабочие игровые файлы, сейвы, R37/R38, один CMD и EPS сохранены.
