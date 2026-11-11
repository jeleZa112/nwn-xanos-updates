# BGXAI 056 — новая проверка EEex, офлайн-аудит цепочки охраны

Дата: 2026-11-11. Проект: EET Foxx / SCS 35.21 / EEex 1.2.0 / EPS 18.4. Репозиторий: `jeleZa112/nwn-xanos-updates`, ветка `bg-eet-ai`. **056 установлена; 057 остаётся SOURCE ONLY, без инсталляции.**

## Подтверждённые данные пользователя

В новой игровой сессии без боя Lua-консоль вывела **`HITAPI=true REG=true HE=0 ERR=nil`**. До этого тот же сеанс показал `BGX44: 043P loaded=true listener=true enabled=true attacks=0 errors=0 ... API=true/true`, `H=0 BR=0/0 LAST=none`, а также `P2 F=1 Q=0`, `P3 F=0 Q=0`, `P4 F=1 Q=0`.

Вывод ограниченный: зарегистрирован Lua-слушатель события блокировки попадания оружием, API найден, исключений регистрации нет. Отсутствие нового боя **ожидаемо** объясняет ноль фактических вызовов. Регистрация **не доказывает**, что `onWeaponHit()` выполнялся в старом бою, поскольку Lua-счётчики были сброшены при новом запуске. Не делать вывода «используемый игровой hook исправен при попадании» только по REG=true.

## Сверенные исходники

- BGXAI 056 `BGXAI/fox_new/experimental_056_active_guard/BGX56/M_BX43.lua`, `P.init()`, `P.onWeaponHit()`, `BGX52Bridge.prepare()`.
- BCS-приёмник `BGXAI/fox_new/experimental_056_active_guard/BGX56/BGX56_RECEIVER.baf` (8 правил).
- EEex `Bubb13/EEex`, `EEex/copy/EEex_scripts/EEex_Sprite.lua`: `EEex_Sprite_AddBlockWeaponHitListener` добавляет слушателя; `EEex_Sprite_LuaHook_CheckBlockWeaponHit` передаёт `listenerContext={attackingSprite,targetSprite,weapon,weaponAbility}`. Сигнатура `P.onWeaponHit(context)` совпадает с этими полями. Сам факт регистрации ещё не означает получение игрового события.

## Кодовая уязвимость без утверждения о причине предыдущего боя

`BGX52Bridge.prepare()` выбирает **одного** охранника из F=1 и `m_nModalState==0` по минимальному квадрату расстояния до пострадавшего. **Не проверяет** занятую очередь, видимость врага, BCS `Range()`, доступность пути и применимость `ActionListEmpty()` до выбора. BCS же исполняет `ProtectObject()` только если среди прочего истинны `ActionListEmpty()`, `See(PlayerN)`, `Range(PlayerN,10)`, `See(NearestEnemyOf(PlayerN))`, `Range(NearestEnemyOf(PlayerN),7)` и TTL 90 игровых тиков (6 сек). Поэтому при допустимом исходном событии запрос может поступить занятому/неподходящему ближайшему F-защитнику, истечь без выполнения и **не быть перенаправлен** второму охраннику. Это вывод из кода, а не доказанный сценарий конкретно Тараны.

Дополнительно: `P2 F=1` и `P4 F=1` означают, что нельзя заранее называть выбранным охранником Тарану без `bridge_last.chosen_guardian`.

## Что нельзя менять до получения основания

Не менять установленную 056, WeiDU.log, `BDDEFAI.BCS`, EEex, hotkeys, пользовательские сохранения, `M_BX43.lua`; 057 пока не ставить. Не принуждать повторно проходить бой с Шанком. Не генерировать боевой сигнал вручную через `BGX52Bridge.prepare()` или запись `BGX52_REQ_SLOT`: это уже изменит поведение игры, а не read-only диагностика.

## Ближайшая единственная runtime-проверка, когда произойдёт обычный бой

После **естественного** попадания врага по участнику отряда и **до нового запуска / загрузки сохранения**, в уже проверенной Lua-консоли прочесть состояние (без игровых команд):

```lua
local s=BGX43Probe.snapshot();C:DisplayText("H="..s.weapon_hit_calls.." HE="..s.weapon_hit_errors.." A="..s.bridge_attempts.." P="..s.bridge_prepared_count.." HIT="..tostring((s.last_weapon_hit or {}).reason).." BR="..tostring((s.bridge_last or {}).reason or (s.bridge_last or {}).result))
```

Интерпретация: `H=0` после явного попадания — исследовать фактический вызов EEex hook; `H>0 A=0` — проверить фильтрацию `last_weapon_hit.reason` и `weapon_hit_errors`; `A>0 P=0` — `bridge_last.reason`; `P>0` — проблема на стороне BCS либо выполнение охраны неочевидно (анализировать режимы, позиции, action queue, TTL и `Q` при своевременном снятии снимка). Не утверждать, что любой из случаев уже случился.

Следующее безопасное действие разработчика: подготовить **offline** regression guard-selection policy с учётом занятости/досягаемости, не добавляя отправку боевой команды и не применяя её до live evidence. Офлайн-тесты в mocks ≠ игровой runtime.