# BGXAI R13 — защитные показатели цели без Attack Info

**Режим:** `SOURCE ONLY`, `NOT DEPLOYED`, `NOT LIVE`. Для EET + SCS 35.21 + EEex/EPS 18.4. Существующий R1–R4/EPS/V6/WeiDU/сейвы не изменяются.

## Зачем

Проверка `160` на конкретной установленной сборке завершилась: `CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED`. `EEex_scripts/B3AttackInfo.lua` — необязательный компонент. Вместо принудительной установки Attack Info R13 готовит безопасную пассивную сборку **сырых** защитных характеристик текущей цели из `EEex_Sprite_GetActiveStats(targetSprite)`, доступность которой на цель и поток игры ещё надо подтвердить LIVE.

## Что читает

- `m_nArmorClass`
- `m_nACCrushingMod`, `m_nACMissileMod`, `m_nACPiercingMod`, `m_nACSlashingMod`
- `m_nResistCrushing`, `m_nResistPiercing`, `m_nResistSlashing`

Это документированные поля `CDerivedStatsTemplate` для x64 EEex. Вызов через **инъецированный** API-адаптер: `{ GameObject_Get = EEex_GameObject_Get, GetActiveStats = EEex_Sprite_GetActiveStats }`. В этом пакете адаптер вызывается только тестовыми заглушками, **не игровым клиентом**.

R13 читает только для действия-кандидата `3/30` и одной цели, проверяет `sourceId`, `targetId`, `actionId`, выбранный слот и способность до и после двух чтений. Значения отличаются — HOLD. Не подтверждает, что цель враг; не создаёт нового EEex hook и не касается игровых очередей.

## Ограничения

- Поля AC и сопротивлений **не являются** доказанным итоговым шансом попадания, сквозным уроном или иммунитетом к конкретному ITM.
- В настоящее время **не заполняются** `R10.model.slots[].targetAC`, `contact`, `damageThrough`: применение требует уточнения типов урона и защит, проверки алгоритма и runtime provenance.
- `nativeEvidenceAuthenticated`, `runtimeApiAuthenticated`, `exactHitChanceProven`, `eligibleForR10Model`, `eligibleForR12HitChance`, `weaponSwitchAuthorized` и `dispatchAuthorized` всегда `false`.
- Слот 11–14 (боеприпас) записывается как текущий **без** приписывания его пусковому оружию.
- Гипотетические тесты не равны LIVE-тестам.

## Проверки

`cd /mnt/data/BGXAI_R13_TARGET_DEFENSE_SOURCE_ONLY && python /mnt/data/run_lua54.py test_r13.lua`

33/33 локальных Lua 5.4 теста PASS (валидный набор, пропущенные/некорректные поля, смена цели/предмета/действия/состояния, подмена контекста, безопасность).

Для следующего игрового шага потребуется отдельно согласованный пассивный наблюдатель, использующий **только существующий** единый `BGXAI_UPDATE.cmd`. Не копировать Lua вручную в override.

## Дополнение: подготовлена штатная установка через пункт 161

`M_BGXTDEF13.lua` — самодостаточный пассивный EEex runtime-модуль, проверяющий первые 64 события начатой атаки спутников. Регистрирует **только один собственный** пассивный listener (не меняя R4), не принимает управляющих решений, не вызывает EPS. При доступности выводит ограниченный JSONL `BGXAI_R13_TARGET_DEFENSE_RAW.jsonl` в пользовательские `Documents/BGXAI_LIVE_REPORTS`, иначе в консоль EEex.

`BGXAI_R13_GUARDED.py` — только через старый CMD и встроенное меню: `1=status RO`, `2=preflight RO`, `3=install` **после дословного токена**, `4=rollback` **после дословного токена и только когда R13 последний WeiDU**. Проверка точного SHA, R1/R2/R4/EEex и внешняя резервная копия; сценарии отказа не пытаются деструктивного автоматического отката.

Проверено локально: ядро Lua 33/33, runtime 14/14, Python guard 26/26. Windows GitHub CI: меню 161 — 10/10, guard — 26/26, PowerShell 5.1/7 AST PASS, 79 610 байт, SHA256 `5740c40cb876b69e664a930b32f089a3431b4a9218537ce9d95b9997095ee2b5`.

**Реальная игровая установка, игровое выполнение и состояние WeiDU у пользователя ещё не проверены.** До дополнительного запроса/токена не устанавливать. Сначала `161 → 2`, передать отчёт preflight; при успехе обсудить guarded install и LIVE-проверку.
