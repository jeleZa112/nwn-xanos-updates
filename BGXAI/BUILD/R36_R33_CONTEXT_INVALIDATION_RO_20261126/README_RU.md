# BGXAI R36 — сброс только устаревшей оценки оружия, БЕЗ остановки персонажа

## Цель

Продолжение P0 после комплексного теста [7/7 CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256) и R34 5/5 LIVE read-only. Это не новый механизм выбора оружия и не перезапуск старого пилота «Халид: лук→меч».

**Найдено повторное использование уже существующего кода:** один установленный в EET обработчик **R33** уже читает в одном callback выбранный APR (`m_nNumberOfAttacks`), THAC0 (`m_nTHAC0`), силу, Improved Haste, уровень/кит, 46 raw WPROF статов, 9 raw inventory slot snapshots, queue count и сырой контекст действия из 081. Для проверки изменений **не нужны** новые EEex слушатели, повторные `EEex_Sprite_GetActiveStats`, второй установщик, повторная установка R33 или новый бой. Не нужно устанавливать отдельный R35 observer; R33 уже имеет более строгую проверку `m_bAllowEffectListCall==1`.

## Реальная улика (исходный пользовательский R33 журнал, 25.11.2026)

В оригинальном загруженном `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` найден 1 SESSION и **8 согласованных R27_SINGLE_CALLBACK событий** одного актёра (без публикации actor ID). Из 7 последовательных сравнений:

| Переход | Фактическое изменение | Безопасное решение |
|---|---|---|
| 1→2, 2→3, 3→4, 4→5, 7→8 | В выбранных raw полях нет изменений | raw-поля совпадают, **не** доказано равенство всех эффектов |
| 5→6 | `actionRaw` 23→3 | Не выдавать новую команду; сбросить устаревший advice |
| 6→7 | `quiversRaw` slot 12 `AROW01` useCount1 20→19; `actionRaw` также 3→23 | Сбросить только advice из-за изменения количества боеприпасов; **не** делать Stop/Attack/переключение |
 
В восьми снимках `selectedAprKeyRaw=2` (2 APR по стандартному декодеру), `m_nTHAC0=20`, `selectedWeaponRaw=12`. Это **слот стрел**, а не доказанный launcher. Снижение useCount1 **не** доказывает само по себе успешное попадание, причину расхода стрел, FPS, идентичность активных эффектов или безопасный момент приказа. `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE`, `queuedActionsRaw=0`, `actionOriginVerified=false`; raw zero queue не означает пустую manual/EPS очередь.

## Код

- `BGXAI_R36_R33_CONTEXT_INVALIDATION_RO.py`: узкий read-only интерпретатор **аутентифицированного SHA исходного R33 журнала**, разбирает 8+ real-shaped record events, строит последовательные состояния и формирует **только** классификацию устаревшей оценки. Не публикует actor ID и весь журнал. Если передать другой файл под видом оригинала — `R33_HISTORICAL_LOG_SHA_MISMATCH`. `analyze_events` отдельно покрыт synthetic fixture тестами; неизвестные поля, обрывы слотов, несоответствие APR и исходных stat полей → `R36_HOLD`.
- `BGXAI_R36_R33_ADVICE_INVALIDATION.lua`: чистая функция `capture(sample)` получает **уже готовый** `R27.observe` sample из R33, без вторичного чтения движка; `compare(before,after)` возвращает информацию `invalidateCachedAdvice` и причину, но никогда не создаёт команды. Источники статов/инвентаря не дублируются.
- `test_r36_r33_context_invalidation_ro.py`: 27 unit-проверок, включая шаблон 8 реальных последовательных событий 20→19, статус неопределённости EPS, неизвестный class row, отсутствие APR другого слота, убранные поля, spoofed authorization, некорректный SHA.
- `test_r36_r33_advice_invalidation.lua`: 20 unit-проверок прямого raw R33 sample на Lua 5.3/5.4/LuaJIT, включая изменение стрел, бафов, WPROF, действия, смену слота и все ограничения на команды.
- Workflow `.github/workflows/bgxai-r36-r33-context-invalidation-ro.yml`: Python Windows+Linux, Lua 5.3/5.4/LuaJIT, static no engine writes, проверка неизменности текущего SHA единого обновлятора.

## Ограничения CODE / TEST / DEPLOY / LIVE

**CODE:** реализовано. **TEST:** native CI. **DEPLOY:** нет. **LIVE R36:** нет. **LIVE ранее:** R33 8 событий и R34 current ITM read-only 5/5. `BGXAI_UPDATE.cmd`, `BGXAI_SYNC.ps1`, WeiDU, EPS18.4, игра, сохранения и соседние проекты не изменялись. Все R36 output:
`dispatchAuthorized=false`,
`weaponSwitchAuthorized=false`,
`alternateEffectiveAPRVerified=false`,
`sameBuffContextVerified=false`,
`manualEpsOriginVerified=false`,
`safeActionBoundaryVerified=false`,
`launcherAmmoBindingVerified=false`.

## Следующая задача P0

Не повторять выбор оружия V3/V4/V5, R27/R33/R34 или общую матрицу тестов. Следующая необходимая проверка — может ли existing action source/очередь EPS быть достоверно классифицирована в текущей конкретной сборке без неверной «свободной границы» атаки. `m_source` был недоступен в реальном R33. Даже после R36 повторный расчёт бОевой оценки возможен только после полноценного синхронного capture эффектов и подтверждённой привязки ammo→launcher; до этого advisory остаётся READ ONLY. Важна проверка настоящего безопасного момента для смены оружия без сброса инициативы.

**Никаких запросов пользователю, установок и повторных боёв на этом этапе.** Для будущей read-only установки понадобятся SHA, префлайт, внешняя копия, WeiDU last-only и явно введённое пользователем разрешение. 

