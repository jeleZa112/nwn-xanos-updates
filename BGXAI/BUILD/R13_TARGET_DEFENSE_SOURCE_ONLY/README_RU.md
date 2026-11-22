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
