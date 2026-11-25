# BGXAI — реальная очередь действий EEex: 081 → R27 → NONINTERRUPT (25.11.2026)

## Результат реальной установки R31 и боя 25.11.2026

**Официальный проверенный вердикт:** [`BGXAI/CURRENT/BGXAI_R31_LIVE_VERDICT_20261125.json`](./BGXAI_R31_LIVE_VERDICT_20261125.json). От пользователя реально получены `BGXAI_R31_CAPTURE_20261125T150437014429Z.json` и `BGXAI_R31_CONSOLE_20261125T150300876807Z.log` (147793 байт, SHA256 `7f2705dde1eaf16e131f5ec1396837f8affaff8b4070292fd945447783c88c9e`). JSON: `status=R31_RUNTIME_RAW_QUEUE_LOG_READY_FOR_REVIEW`, exit 0, session 1, R31 samples 12, stable queue 12, nonempty 0. Источник — пользовательский настоящий gameplay, НЕ CI/mocks.

**Проверка самого лога:** 12/12 строк `BGXR27` `R27_SINGLE_CALLBACK` парсятся; 12/12 same-callback, стабильные данные выбранного оружия, инвентаря и derived stats; 12/12 `queueSnapshotStable=true`, `actionContextSnapshotStable=true`, `queuedActionsRaw=0`; 11 действий `actionRaw=23` и одно `actionRaw=3`. Один зарегистрированный R31 session marker. R31 не выдаёт приказов: `ordersSent=0`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`.

**Боевой факт, не реконструкция:** `Халид` с луком `BOW05` и стрелами `AROW01` действительно атаковал больного гибберлинга, бросок 20 — критический, 6 метательного урона, враг умер. Счётчик `AROW01` изменился 20→19 после actionRaw3. `selectedWeaponRaw=12` во всех 12 снимках, переключения на меч НЕ было и его не требовалось при убийстве одним выстрелом.

**Критическое обнаруженное ограничение:** `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` **12/12** и `actionSourceStable=false` **12/12**. `queueNonemptyObserved=false` везде — непустая очередь вообще НЕ была наблюдаема в этой короткой игре. **Даже когда actionRaw=3/реальный выстрел, `queuedActionsRaw=0` и `actionCountRaw=0`.** Поэтому ноль не доказывает безопасную паузу, отсутсвие ручного приказа или EPS-задачи. `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`; никакого автоматического dispatch на основании этих данных.

**Отдельная ранее известная ошибка UI:** `Error loading menu ... ']' expected near 'icon'` есть и в новом логе; её уже видели до R31. Не связывать её с R31 без отдельных данных и не менять BG_EET_RU или UI в BGXAI.

**Статусы:** R31 CODE/CI=PASS, native WeiDU parse=PASS, real preflight=PASS, DEPLOY=PASS, **LIVE PASSIVE OBSERVER=PASS**, LIVE queue/noninterrupt=UNVERIFIED, origin=UNVERIFIED, ALT effective APR/weapon priority=UNVERIFIED. **Старый пункт 171→5 повторять не нужно**. Следующее — разработки SOURCE ONLY алгоритма реального сравнения оружия с APR/THAC0/эффектами и запретом прерываний; только при появлении нового функционала потребуется целевой runtime. Оставить R31 и R29 установленными, текущую игру не менять.

---


**SOURCE/TEST PASS, не установка.** Единый обновлятор, PIN, WeiDU, игровые BCS, EPS и озвучка/перевод не изменены. Работа V6 (лук→меч) и исторический установленный R27 сохранены. Результат не следует называть новым игровым поведением до отдельного DEPLOY/LIVE.

## Реальный механизм, найденный в EEex x64

Официальные структуры `CGameAIBase` и `CTypedPtrList` содержат `m_queuedActions` (offset `0x330`) с полем `m_nCount` (offset `0x18` внутри списка). Источник: [Bubb13/EEex-Docs, CG](https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20%28x64%29/CG/index.rst) и [CT](https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20%28x64%29/CT/index.rst). Это **публичная структурная документация**, соответствие **точной установленной игре ещё не проверено в runtime**.

Ранее модуль 081 видел только ID текущего действия, а `NONINTERRUPT` мог теоретически пересчитывать ранжирование, когда в движке уже есть ожидающие команды. `ActionListEmpty()` и код текущего действия не доказывают, кем эта очередь сформирована.

## Что реализовано

1. **081 V2 в историческом каталоге 081**, не второй game hook: `BGXAI081_ACTION_PROVENANCE_QUEUE_V2.lua`. Только прямые безопасные чтения через `pcall`: дважды `sprite.m_queuedActions.m_nCount`, до/после сравнение `sprite.m_curAction.m_actionID`, диапазон `0..512`. `nil`, ошибка, нецелое, недопустимый размер или изменение значения → `queue_count_observed=false`. `queue_empty=nil`, `eps_queue_empty_verified=false`, `manual_command_verified=false`, `safe_to_dispatch=false` **всегда**. Старый оригинал `BGXAI081_ACTION_PROVENANCE_READONLY.lua` и 082-historical копия не изменены.
2. **R27 SOURCE ONLY**, прежняя *одна* точка наблюдения: подготовленный `BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua` теперь композиционно включает 081 V2 с проверенным SHA. Очередь читается до/после сбора R2+R4; только совпавшие ID действия и counts дают `queueSnapshotStable=true`, `queuedActionsRaw=n`; при несовпадении остаётся `nil`, а замеры выбранного APR не объявляются одновременно подтверждением очереди. В JSON отдельно появляются `queueNonemptyObserved` (или `null` при неизвестном), `actionOriginVerified=false`, `manualEpsQueueVerified=false`. **Не зарегистрирован как слушатель**, старый установленный `M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735` не изменён.
3. **В существующем NONINTERRUPT V1** добавлена **односторонняя отрицательная граница**: если R27 raw count >0, same actor/action, `queueSnapshotStable=true`, readOnly и отсутствие game dispatch, `M.step` возвращает `PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE`, сбрасывает предыдущую кандидатуру оружия, `scorerCalls=0`, `ordersSent=0`, `actionQueueCleared=false`, `currentActionPreserved=true`. Не нужно знание EPS/manual origin, потому что результат — отказ от переключения. При count=0 путь обычный, **разрешения на action/BCS/LOCALS нет**.

**SHA256 source:** 081 V2 `b3c9ecbc98c81e09d24279e4f970729750187ed6f4bafb2738572a37fa7d2edd`; R27 source-only `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`; NONINTERRUPT V1 `160c0b5a099ea170772dec12443f7273b92b8b99ec61a75f2e88052c9abc1cde`. Предыдущие сохранённые исходники не удалены; новый кандидат R27 не совпадает с установленным и не является installable-модулем.

## Проверено

- Локально: 081 V2 **441 Lua assertions**, R27 **77 Lua checks + 9 Python tests**, NONINTERRUPT **25 Lua tests**.
- [GitHub Actions 45447222518](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45447222518): **SUCCESS на Windows и Ubuntu**. На Lua5.3, Lua5.4, LuaJIT по отдельности: 081 **441 assertions**, R27 **77 checks**, общая регрессия V3 **442 сценария**, прежние R2/R4/R6 PASS; на Windows source/WeiDU-static checks и R27 Python PASS.
- Исторический установленный R27, backend `BGXAI_SYNC.ps1`, обновлятор `BGXAI_UPDATE.cmd` и PIN не редактировали.

## Оставшаяся граница и следующий продуктовый шаг

- Наблюдение engine queue **ещё не доказано на реально запущенной EET**. Из x64 struct наличие Lua binding для `m_nCount` не доказано отдельным runtime; поэтому возможен безопасный `unknown` вместо ложного `0`.
- Пустой список — **не** доказательство отсутствия ручного приказа, активности EPS, атаки в восстановлении, лечения/каста. Origin остаётся UNKNOWN.
- По-прежнему нет подтверждённых **эффективных APR/THAC0/урона/эффектов всех альтернативных слотов**. Статические ITM/2DA или предыдущий выбранный APR не приравнивать к актуальным движковым значениям.
- **Следующая полезная стадия:** спроектировать *одно* защищённое обновление пассивного R27 через существующий single-updater с typed consent, внешним backup, SHA preflight, WeiDU last-only и одним новым игровым наблюдением очереди + ESP/manual отдельно; затем подключить данные к V3/producer. Без дублирующего V6/R29 и без слепого auto-install.

CODE=PASS / LOCAL_TEST=PASS / CI=PASS / DEPLOY=NO / LIVE_NEW_QUEUE=NO / GAMEPLAY_WEAPON_PRIORITY_V3=NO.
