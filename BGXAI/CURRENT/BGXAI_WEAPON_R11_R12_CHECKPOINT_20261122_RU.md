# BGXAI — R11 + R12. Выбранное оружие против конкретной цели

Дата 22.11.2026. Сохраняется один `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. **GAME НЕ ИЗМЕНЕНА** этим этапом.

## Подтверждённая предыдущая база

- R1/R2/R4 в реальной EET: наблюдатели действовали, APR/слоты/активные поля; R3 native ITM/2DA аудит. R5/R6/R7/R8/R9/R10 — исходный/офлайн расчёт. R10 прогноз по диапазонам, не аутентифицированное нативное наблюдение.
- Ранее зафиксированные 16 событий: посох STAF01 выбран APR1, слот стрел AROW01 APR2 (BOW05 не доказан как конкретный активный launcher), меч SW1H04 APR1.5; это исторические выбранные состояния, **не текущие значения альтернативных слотов**.
- R1 установлен правильно: `159→3: INSTALLED_READONLY_OBSERVER_SOURCE_EXACT`; не повторять R1 preflight/install.

## R11: что действительно реализовано

`BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE.lua` — импортируемый, но автоматически не загружаемый Lua модуль. Функция `inspect(sourceSprite,targetSprite,api,context)` не меняет выбранное оружие и не делает игровых приказов. Вызов возможен **только если** вызывающая сторона явно передала источник, цель и функции, объявила read-only intent, и соблюдён тип аргументов. Считывается selectedWeapon/ability/item, вызываются в `pcall` функции `GetWeaponHitChance` и `IsImmuneToWeapon` в порядке, аналогичном `B3AttackInfo.lua`; перепроверяется неизменность выбора после чтения. Данные сохраняют маркировку `CALLER_SUPPLIED_UNAUTHENTICATED_READ`, `nativeEvidenceAuthenticated=false`, `dispatchAuthorized=false` и `weaponSwitchAuthorized=false`. Результат выбранного слота стрел не подтверждает активный лук.

**Источник API:** официальный EEex `Bubb13/EEex`, `EEex/copy/EEex_scripts/B3AttackInfo.lua`, функция `B3AttackInfo_Private_GetWeaponHitChance`. Она вызывает `EEex.IsImmuneToWeapon` и `EEex.GetWeaponHitChance` для `m_selectedWeapon`; сам исходник не доказывает совместимость с установленной EEex пользователя. Нельзя считать произвольный caller-supplied `api` проверенной реализацией EEex; мок означает только проверку логики. Нельзя автоматически устанавливать hook без отдельного разрешения и подтверждения безопасности потока.

## R12: совместимость R10 + R11

`BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK.lua` проверяет строгое совпадение actor, targetActor, session, snapshotId, sequence, selectedSlot, targetFingerprint. Сверяет кандидатный процент R11 с интервалом R10 **только выбранного оружия**. Если несовпадение — HOLD и диагностика; если совпадение — `SELECTED_ONLY_CONSISTENCY_UNAUTHENTICATED`. Совпадение нельзя интерпретировать как native proof, разрешение ранжирования или переключения; иммунитет проверяется отдельно от шанса попадания. Исторический APR альтернативных слотов не преобразуется в актуальный.

## Дополнительно: кандидат цели из уже существующего R4 listener

`BGXAI_R11_ACTION_TARGET_CANDIDATE_RO.lua` — чистый вспомогательный модуль для события `EEex_Action_AddSpriteStartedActionListener(sprite,action)`. Из `action.m_acteeID.m_Instance` пытается разрешить `EEex_GameObject_Get`, проверить `m_id` и `isSprite(true)`, после чего возвращает **только числовые ID и `TARGET_CANDIDATE_HOLD`**. Не утверждает, что это враг или атака, не экспортирует указатель, не добавляет listener в игру, не вызывает R11 на этапе разрешения цели. Обработчик и конкретные поля проверены по `Bubb13/EEex/.../EEex_Action.lua`. Фактическая установленная EEex ещё не проверена.

## Тесты

- R11 `test_r11.lua`: 27/27 PASS (моки; проверены изменение слота/ability/item во время вызова, ошибки API, неверные значения, no action).
- R12 `test_r12.lua`: 22/22 PASS (моки; контекст, target, иммунитет, несовпадение с диапазоном, фальшивое подтверждение).
- Target candidate `test_r11_action_target.lua`: 18/18 PASS (моки, подмена id и action type, target pointer, no hook).
- R10 regression `test_r10.lua`: 40/40 PASS; `test_r10_evidence.py`: 12/12 PASS.
- Всего **119/119 локальных тестов**; Windows EET LIVE R11/R12 — **НЕТ**.

## Статус (не смешивать)

CODE: R11/R12 созданы и опубликованы как SOURCE ONLY.
TEST: офлайн PASS 119/119 со связанными регрессиями.
DEPLOY: нет, пользовательскую EET не меняли.
LIVE: нет, кандидатный API не запускался в игре.

## Реальный следующий шаг / блокер

Для нативного подтверждения нужен read-only pilot в установленной EEex: зарегистрировать безопасную точку вызова, определить источник и цель, проверить `EEex.GetWeaponHitChance` / `EEex.IsImmuneToWeapon` для уже выбранного оружия и собрать отчет. Реализация guarded install через один `BGXAI_UPDATE.cmd` требует отдельного подтверждения на изменение игры. Не повторять R1–R4, не пытаться запускать эту функцию с произвольного потока, не выдумывать native APR альтернативных слотов и не выполнять SelectWeaponAbility/Stop/ClearActions.

**Автопродолжение:** см. `BGXAI_AUTO_CONTINUE_RULE_20261122_RU.md`, без ожидания `+` на безопасных задачах.
