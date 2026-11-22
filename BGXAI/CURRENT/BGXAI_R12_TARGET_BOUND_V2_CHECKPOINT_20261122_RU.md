# BGXAI — R12 target-bound integration V2 и EEex static preflight

**Дата:** 22 ноября 2026. **Состояние:** `CODE_READY / OFFLINE_TEST_PASS / SOURCE_ONLY / NOT_DEPLOYED / NOT_LIVE`.

## Обязательная политика

Если безопасная задача пройдена — в том же текущем обращении автоматически выполнять следующие доступные проверки, код, тесты, сохранение в Library и GitHub, **не просить `+`**. Нельзя обещать работу после завершения ответа. Завершать на реальном блокере: модификация установленной игры требует отдельного точного разрешения и внешней резервной копии; неизвестный установленный EEex не объявлять проверенным.

## Фактическое исправление

Старый `BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK.lua` принимал **непосредственно** R11 V1 (`SELECTED_HIT_CHANCE_CANDIDATE_ONLY`). Новый проверенный R11 target-bound V2 (`TARGET_BOUND_SELECTED_HIT_CANDIDATE_NOT_NATIVE_PROOF`) выдаёт другую схему; напрямую R12 её отвергал. Предшествующие отдельно успешные тесты не доказывали общей совместимости.

Создан `BGXAI_WEAPON_R12_TARGET_BOUND_CROSSCHECK_V2.lua`: чистый неисполняемый мост. Он:

1. Привязывает session/snapshot/actor/targetActor/event/selectedSlot/ability к единому кадру. Требует отдельной привязки targetActor и selectedAbility к model.frame, которой не хватало базовому R10.
2. Проверяет защитные флаги R11 target-bound V2: любые заявления о нативном доказательстве, враждебности, очереди EPS/manual, игровом действии или разрешении переключения вызывают `HOLD`.
3. **Повторно вычисляет R10.assess(frame, ledger, model)** через уже существующий R9 ledger, вместо приёма оторванного от сцены, возможно устаревшего результата R10.
4. Только после этого адаптирует R11 V2 к неисполняемой форме R11 V1 и передаёт в **существующий** R12.compare. Новый конкурентный оценщик оружия не создаётся.
5. При несовпадении оценки шанса попадания с прогнозом, очереди или статусов возвращает `HOLD`, никаких игровых приказов.
6. Даже при совпадении возвращает `selectedItemRefUnverifiedAtRead=true`, `targetFingerprintUnauthenticated=true`, `alternateSlotAPRVerified=false`, `liveReadVerified=false`, `nativeEvidenceAuthenticated=false`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`.

## Вспомогательная проверка на конкретной установленной EET (код готов, на компьютере пользователя не выполнялся)

`BGXAI_EEEX_R11_STATIC_COMPAT_RO.py` — чисто **читающий** сканер будущего native preflight. Файлы игры не создаёт, в процессы не вмешивается, WeiDU не запускает, другой CMD не создаёт, отчёт — stdout JSON. Только для `C:\Games\BG_EET_FOXX_NEW` на Windows. Читает `chitin.key`, `override/M___EEex.lua`, скрипты `EEex_scripts/B3AttackInfo.lua`, `EEex_scripts/EEex_Action.lua`, установленные пассивные модули R1/R2/R4. Проверяет известные статические вызовы с SHA256. Любая недостача или symlink ведёт к `HOLD`. Даже полный PASS = `STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN`, не подтверждение наличия функций в текущем EEex VM или безопасного потока игры. Скрипт **не добавлен** в имеющийся обновлятор и не предназначен пользователю как отдельная команда. Для интеграции нужна будущая согласованная версия того же `BGXAI_UPDATE.cmd`.

Официальный EEex master на момент проверки:
- `B3AttackInfo.lua`, Git blob SHA `3f0c6601250c5b19c2295233554545b4a337ab45`, содержит вызовы `EEex.GetWeaponHitChance` и `EEex.IsImmuneToWeapon` для текущего выбранного оружия.
- `EEex_Action.lua`, Git blob SHA `e7543274ed066b5abe3c58262105212f208d1595`, содержит `EEex_Action_AddSpriteStartedActionListener` и `EEex_Action_LuaHook_OnAfterSpriteStartedAction`.
- Наличие этого кода в официальном репозитории не доказывает версию установленной игры.

## Проверки

- Новая R12 V2 full-chain интеграция R9→R10→R11 target-bound→R12: **35/35 Lua PASS**.
- Новый static read-only EEex compatibility scan: **13/13 Python PASS**.
- Повторная регрессия R10 Lua 40, R10 Python 12, R11 V1 27, target resolver 18, R12 V1 22, R11 target-bound 26: **145/145 PASS**.
- **Общий результат 193/193 локальных проверок PASS.** Это не игровой LIVE PASS.
- Runtime game, EPS 18.4, V6, WeiDU, сохранения и единый `BGXAI_UPDATE.cmd` не изменялись.

## Непреодолённая граница

Для LIVE R11 нужны отдельное явное согласие на guarded установку через **тот же** один обновлятор, SHA preflight, внешняя резервная копия, WeiDU last-only rollback и доказательства работы на установленной EEex. Для настоящего выбора оружия дополнительно необходимы APR альтернативных слотов при *текущих* бафах, иммунитеты и защиты цели, EPS/manual safe boundary. Никаких самовольных переключений, даже при совпадении R12.
