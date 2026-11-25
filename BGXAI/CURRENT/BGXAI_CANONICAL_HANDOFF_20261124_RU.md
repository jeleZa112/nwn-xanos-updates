# BGXAI — единая точка продолжения, 24 ноября 2026

**R32/V5 совместимость — окончательный native CI:** [run 45643810529](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45643810529) **SUCCESS во всех 3 задачах**: Windows Python, Ubuntu Python, Lua 5.3/5.4/LuaJIT. Добавлен cross-module unit: значения WSPATCK для `-3,-2,-1,0,1,2,3` у EEex-ридера R32 совпадают с `BGXAI_WEAPON_APR_PROVENANCE_V5.decode_wspatck`. В новой игре/WeiDU ничего не менялось, R32 остаётся source-only. Данный CI не является LIVE. К следующему этапу переходить от таблиц к **подтверждению текущего класса и weapon-group + альтернативным итоговым APR**; не требовать повторения R31 capture.


## 25.11.2026 — новая стадия R32: источник установленных APR 2DA (SOURCE ONLY)

**Сделана полезная ступень Weapon Priority V5, не второй скорер:** `BGXAI/BUILD/R32_APR_EET_TABLES_RO_20261125/` — READ ONLY code `BGXAI_R32_APR_EET_TABLES_RO.py` + `BGXAI_R32_EEEX_ENGINE_2DA_RO.lua` + 2 файла тестов и README_RU. Вспомогательный Python проверяет формат `WSPATCK.2DA` и `CLSWPBON.2DA` из точных файлов `override` с SHA256; при отсутствии возвращает HOLD и не имитирует BIFF. Lua-путь через официальный EEex `EEex_Resource_Load2DA` читает *через движок* соответствующие C2DArray (пока только SOURCE ONLY, без установки/слушателей).

**Боевая механика:** WSPATCK возвращает только **добавочный** APR (`-1→+0.5`, `1→+1`, `-2→+1.5`), а CLSWPBON.GETS_PROF_APR указывает, имеет ли класс право на proficiency APR. НЕЛЬЗЯ принимать таблицу за финальный APR, складывать повторно с engine final APR или объявлять альтернативный слот готовым без проверенной weapon↔proficiency association, active class/dual/multi, предметов, заклинаний/эффектов и фактической частоты атак альтернативного оружия. Источники: [IESDP WSPATCK](https://burner1024.github.io/iesdp/files/2da/2da_tob/wspatck.htm), [IESDP CLSWPBON](https://burner1024.github.io/iesdp/files/2da/2da_bgee/clswpbon.htm), [EEex_Resource_Load2DA](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/EEex_Resource.lua).

**TEST / CI:** [GitHub workflow 45643546399](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45643546399) = **SUCCESS**, Windows+Linux Python 3.12 и 17 native Lua тестов на Lua5.3/Lua5.4/LuaJIT с синтетическим EEex C2DArray. Никаких реальных данных из пользовательского BIFF ещё не получено и нативный EEex runtime R32 не проверен. CODE/CI PASS; DEPLOY R32 NO; LIVE R32 NO; ALT EFFECTIVE APR NO.

**Не трогали:** пользовательский `BGXAI_UPDATE.cmd`, PIN, WeiDU, R31 R27V3 passive observer, V6/R29, EPS, EET, BG Voice RU, BG_EET_RU и сейвы. Один обновлятор обязателен; старые меню не повторять.

**Следующий приоритет:** источник class/kit + weapon ability ↔ proficiency и runtime final-state каждого **альтернативного** слота, с корректным снимком целевых защит/эффектов и без потери действия. Не посылать команды на основании R31 `queuedActionsRaw=0`. Не назначать пользователю новый тест/установку R32, пока нет полного безопасного live-маршрута и существенного нового поведения.

---


**Regression после реального R31 боя:** в `test_weapon_noninterrupt_plan_v1.lua` добавлен конкретный реальный сценарий `actionRaw=3` + `queuedActionsRaw=0` + `ACTION_SOURCE_POINTER_UNAVAILABLE` → `CONTINUE_CURRENT_ACTION_SWITCH_PENDING` только advisory, `dispatchAuthorized=false`, `ordersSent=0`, `actionQueueCleared=false`, `currentActionPreserved=true`. Offline NONINTERRUPT 26/26; общий runner 443 сценария (ранее 442). **[GitHub CI 45641893884](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45641893884) SUCCESS:** native Lua 5.3/5.4/LuaJIT + Windows static. Никакой установленный Lua/BCS/PIN/WeiDU не менялся. R31 и V6 остаются как были.


## 25.11.2026 — РЕАЛЬНЫЙ R31 LIVE 12/12, один выстрел Халида, следующая стадия EFFECTIVE APR

**Официальный проверенный вердикт:** [`BGXAI/CURRENT/BGXAI_R31_LIVE_VERDICT_20261125.json`](./BGXAI_R31_LIVE_VERDICT_20261125.json). От пользователя реально получены `BGXAI_R31_CAPTURE_20261125T150437014429Z.json` и `BGXAI_R31_CONSOLE_20261125T150300876807Z.log` (147793 байт, SHA256 `7f2705dde1eaf16e131f5ec1396837f8affaff8b4070292fd945447783c88c9e`). JSON: `status=R31_RUNTIME_RAW_QUEUE_LOG_READY_FOR_REVIEW`, exit 0, session 1, R31 samples 12, stable queue 12, nonempty 0. Источник — пользовательский настоящий gameplay, НЕ CI/mocks.

**Проверка самого лога:** 12/12 строк `BGXR27` `R27_SINGLE_CALLBACK` парсятся; 12/12 same-callback, стабильные данные выбранного оружия, инвентаря и derived stats; 12/12 `queueSnapshotStable=true`, `actionContextSnapshotStable=true`, `queuedActionsRaw=0`; 11 действий `actionRaw=23` и одно `actionRaw=3`. Один зарегистрированный R31 session marker. R31 не выдаёт приказов: `ordersSent=0`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`.

**Боевой факт, не реконструкция:** `Халид` с луком `BOW05` и стрелами `AROW01` действительно атаковал больного гибберлинга, бросок 20 — критический, 6 метательного урона, враг умер. Счётчик `AROW01` изменился 20→19 после actionRaw3. `selectedWeaponRaw=12` во всех 12 снимках, переключения на меч НЕ было и его не требовалось при убийстве одним выстрелом.

**Критическое обнаруженное ограничение:** `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` **12/12** и `actionSourceStable=false` **12/12**. `queueNonemptyObserved=false` везде — непустая очередь вообще НЕ была наблюдаема в этой короткой игре. **Даже когда actionRaw=3/реальный выстрел, `queuedActionsRaw=0` и `actionCountRaw=0`.** Поэтому ноль не доказывает безопасную паузу, отсутсвие ручного приказа или EPS-задачи. `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`; никакого автоматического dispatch на основании этих данных.

**Отдельная ранее известная ошибка UI:** `Error loading menu ... ']' expected near 'icon'` есть и в новом логе; её уже видели до R31. Не связывать её с R31 без отдельных данных и не менять BG_EET_RU или UI в BGXAI.

**Статусы:** R31 CODE/CI=PASS, native WeiDU parse=PASS, real preflight=PASS, DEPLOY=PASS, **LIVE PASSIVE OBSERVER=PASS**, LIVE queue/noninterrupt=UNVERIFIED, origin=UNVERIFIED, ALT effective APR/weapon priority=UNVERIFIED. **Старый пункт 171→5 повторять не нужно**. Следующее — разработки SOURCE ONLY алгоритма реального сравнения оружия с APR/THAC0/эффектами и запретом прерываний; только при появлении нового функционала потребуется целевой runtime. Оставить R31 и R29 установленными, текущую игру не менять.

---


## 25.11.2026 — R31 DEPLOY PASS подтверждён реальным INSTALL JSON, LIVE пока NO

**Первичный источник от пользователя:** `BGXAI_R31_INSTALL_20261125T131628301568Z.json`, schema `BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1`; `status=R31_PASSIVE_INSTALLED_AWAITING_RUNTIME`, `installationPerformed=true`, `gameModified=true`, `typedInstallApproved=true`. Отчёт относится к фактически запущенной EET, а не к CI. Установлен R31/V3 через новый WeiDU-компонент после ранее подтверждённого R29. По коду защищённого установщика этот статус выдаётся только после проверки R31-last и SHA игрового `override/M_BGXR27.lua`.

**Верифицированный источник:** R31 live Lua SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`. В отчёте указан внешний backup (хранить, не удалять): `C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXR31_mcy15k64`; прежний Lua SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`. `baselineSnapshot` содержит HASH WeiDU.log, EPS/EEex, `BDDEFAI.BCS`, `DPLAYER.BCS`, `chitin.key` до установки. Не делать ложного вывода, что снимок равен послестановочному перечню: пост-установочные проверки кода не меняют BCS/ключ/EEex, но JSON публикует именно baseline.

**Границы:** `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`, `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`; альтернативный effective APR и последствия в live не проверены. Старый R27 listener должен быть заменён на R31-сборку только после полного перезапуска InfinityLoader, а не параллельно в той же сессии. `CODE/CI=PASS`, `R31 PREFLIGHT=PASS`, `R31 DEPLOY=PASS per install report`, `R31 LIVE=NO`.

**Единственное следующее действие пользователя:** прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **171 → 5 (capture)**. Обновлятор проверит установленный R31 и запустит InfinityLoader для захвата одной сессии в `Documents\BGXAI_LIVE_REPORTS\BGXAI_R31_CONSOLE_*.log`. Загрузить обычный тестовый сейв, провести 2–3 действия персонажей (например, несколько атак с луком/мечом), штатно выйти из игры. Прислать JSON `BGXAI_R31_CAPTURE_*.json` и `BGXAI_R31_CONSOLE_*.log` из путей `reportFile`, если они появятся. Отдельно не повторять `171→1` и `171→2`, не запускать старые R27 установщики/rollback. При STOP/HOLD прислать точный JSON/текст без повторного запуска. Не объявлять поведение R29/Weapon V3 доказанным этим capture.

**История и тесты:** real READONLY PRECHECK `BGXAI_R31_PREFLIGHT_20261125T063640325949Z.json` PASS; настоящий WeiDU 251 TP2 parse-check (Windows/Linux) [CI 45562250963](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45562250963) SUCCESS. Установленное состояние — новый факт, который отменяет нижележащие исторические фразы `R31 не установлен` и `установку пока не выполнять`.

---


## 25.11.2026 — на EET пользователя R31 preflight PASS, WeiDU 251 parser PASS

**Реальный источник (от пользователя):** `BGXAI_R31_PREFLIGHT_20261125T063640325949Z.json`, `schema=BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1`, `status=R31_SOURCE_PREFLIGHT_PASS_INSTALL_STILL_UNAUTHORIZED`. 150 WeiDU компонентов, R27 №149, R29 №150, новый R31 НЕ установлен (`installationPerformed=false`, `gameModified=false`, `ordersSent=0`). Доказаны точные исходники и хэши из текущей установки. Заново запускать 171→1 НЕ нужно.

**Контрольная точка:** `WeiDU.log` SHA256 `3cec176f9e6eab721f7aa931c29e7e0d7a4a0d70fab346cffbbb4ae58960e0d6`; live `override/M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`; R31 candidate SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`; BCS `BDDEFAI.BCS` SHA256 `24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331`; `DPLAYER.BCS` SHA256 `4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed`. Все значения подтверждены реальным readonly JSON. Остальные подробности — в отчёте, но не публиковать весь приватный файл в публичном GitHub.

**Новый независимый native parser smoke:** подготовлен `R31_NATIVE_TP2_PARSE_RO.py`, с архивами официального WeiDU **v251.00**, фиксированными SHA256 релизных ZIP, `--nogame --parse-check TP2` только во временной папке. [GitHub CI 45562250963](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45562250963) **SUCCESS** на Ubuntu и Windows. Это реальный синтаксический разбор WeiDU, не mock, однако это НЕ установка/откат и не подтверждение runtime EEex. Ранее исправлены только тестовые LF CRLF/escaping проблемы; оригинальные R31 guard Lua/Python и pinned update не изменены.

**CODE/TEST/READONLY PREFLIGHT/PARSE:** PASS. **DEPLOY/LIVE R31:** NO. Нет `queueBindingLiveVerified`, `manualEpsOriginVerified`, `alternateEffectiveAPRVerified`. Даже native parse не даёт права на игровое dispatch. Не повторять R27/R29/R30 и не дублировать разработку наблюдателя.

**Следующий строго ограниченный шаг после отдельного буквального согласия пользователя:** закрыть Baldur's Gate, InfinityLoader, WeiDU; через ЕДИНЫЙ `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` выбрать `171→2` и самостоятельно ввести точный токен `INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29`. Сценарий до игры выполняет повторный SHA/preflight и внешний проверенный backup, устанавливает BGXR31 только после R29, не допускает автоматических исправлений или отката. После установки прикрепить `BGXAI_R31_INSTALL_*.json` и пока НЕ запускать игру до проверки результата. При HOLD/STOP ничего не повторять и не делать rollback вслепую. Отдельная проверка LIVE после установленного PASS — пункт 171→5, но её не назначать до анализа отчёта установки.

---


## 25.11.2026 — готов единый канал R31 menu171, ожидается только пользовательский RO preflight

**Новая точка продолжения (после прежних записей SOURCE ONLY):** существующий `BGXAI_UPDATE.cmd` не изменён; его `BGXAI_SYNC.ps1` уже содержит пункт **171 — R31 V3**. Манифест `BGXAI/fox_new/BOOTSTRAP_PIN.json` закрепил immutable commit `fe992a60a4c7880912270cfed27be59c6a0bf359`, `script_size=79941` (лимит 80000), SHA256 `c998ff6607ee3915b9cbb3c9b31955f715bee425b5ed882e04e1af1d515ed4aa`. Предыдущие dispatch 1–170 сохранены.

**R31 source-only полезная функциональность:** заменяющий кандидат старого R27, но не второй параллельный наблюдатель; один EEex listener, RAW `m_queuedActions.m_nCount`, снимки действия/derivedStats. Source Lua 47 550 байт SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`, guarded Python 20 305 байт SHA256 `0ac97a702c4ac5919549a5a54cf9ef6a01a8fbd582273fc556fe9c82a60950ee`. Raw queue count=0 НЕ означает проверенную пустую очередь EPS/manual и не даёт права переключения оружия.

**CODE/TEST:** [независимый CI menu171 PIN + CMD + Windows PS5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45561570321) — SUCCESS (Windows и Ubuntu); [R31 SOURCE/guarded/mock + PS5.1 и три Lua](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45561576119) — SUCCESS (Windows/Linux). Отдельные исторические workflows могут продолжать краснеть на ожидаемых старых пинах; это не повод объявлять общий CI полностью зелёным.

**DEPLOY R31=NO / LIVE R31=NO.** R30 real READ ONLY PASS показал WeiDU 150, R27 №149, R29 №150. Игра, V6, R27, R29, EPS и сейвы не изменены. Native WeiDU overlay в пользовательской EET ещё не проверен. Typed согласия на установку R31 нет.

**Ровно следующий пользовательский шаг:** прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **171** → **1 (RO preflight)**, затем передать новый `BGXAI_R31_PREFLIGHT_*.json` из `Documents\BGXAI_LIVE_REPORTS`. Не выбирать 171→2 (install), не применять старые R27/R29 rollback и не повторять 170. При HOLD — STOP, без автоматического повтора. Даже PASS не разрешает установку. Следующая разработка после отчёта — нативная проверка безопасности WeiDU, потом отдельное буквальное typed-согласие, один live-passive capture и только затем real alternate APR/effects для Weapon Priority.

---


## 25.11.2026 — R31: R27/V3 passive observer assembled; guarded WeiDU SOURCE ONLY; CI PASS

**Новая практическая разработка:** вместо второго наблюдателя собран exact R27 ACTION_CONTEXT_V3 плюс один пассивный EEex listener. Файл `BGXAI/BUILD/R31_R27V3_PASSIVE_SOURCE_20261125/M_BGXR27_R31_SOURCE_ONLY.lua` — 47 550 байт, SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`. Известный исходный R27/V3 44 805 байт, SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929` сохранён без правок. Версия R31 не создаёт приказов, не сменяет оружие; протокол nonempty-queue предоставляет только отрицательное наблюдение.

**Защищённый код установки подготовлен, но НЕ подключён к обновлятору.** `R31_GUARDED_SOURCE_ONLY.py` моделирует новый отдельный WeiDU-компонент BGXR31 *после* реального R29 (позиция 150), замену только `override/M_BGXR27.lua`, внешнюю проверенную копию, буквальное typed согласие и last-only rollback при R31 последним. Не применять старые R27/R29 installer/rollback. Реальный пользовательский `BGXAI_UPDATE.cmd` не менялся; его backend 79 979 / 80 000 байт, до добавления меню 171 нужно обеспечить ограничение и pinned checks. Не давать пользователю отдельный CMD/PowerShell/Python.

**CODE/CI PASS, DEPLOY NO, LIVE NEW R31 NO.** Локальная сборка CI + 6/6 тестов R31; 5/5 synthetic guarded overlay/rollback; модель EEex с одной регистрацией и `queuedActionsRaw=2`, `ordersSent=0` проверена на Lua 5.3/5.4/LuaJIT; прежний R27 90/90 на всех трёх. GitHub Actions Windows + Ubuntu SUCCESS: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45560352966 . В тестовой среде WeiDU вызов замещён mock: **это не native WeiDU install и не игровой runtime**.

**Граница истины:** реальный R30 READ ONLY PASS 25.11, установленный R27 SHA `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`, WeiDU R27 №149/R29 №150. R31 в EET не установлен, `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`. Игру, V6, EPS, R27, R29, BG_EET_RU, BG Voice RU и сейвы не изменяли.

**Следующий P0:** source-only интеграция нового R31 в прежний один CMD (native WeiDU и PS5.1 проверка, SHA-pinned immutable backend, без обхода 80 KB); только потом отдельное буквальное разрешение, один реальный passive queue capture. Никакой auto install от CI; затем real alternate APR/THAC0/effects и V5→V4→V3→NONINTERRUPT→BAF, а не повторная разработка bow→sword. Ссылка на рабочий пакет: `BGXAI/BUILD/R31_R27V3_PASSIVE_SOURCE_20261125/README_RU.md`.

---


## 25.11.2026 — реальный R30 PASS на пользовательской EET (R29 в WeiDU)

**Новое фактическое подтверждение:** R30 menu170 выполнен на пользовательской EET 25.11.2026. `status=SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`, `readOnly=true`, `gameModified=false`, `installationPerformed=false`, `ordersSent=0`, `dispatchAuthorized=false`.

**WeiDU:** 150 компонентов; R27 — позиция 149, `r27IsLast=false`; последний (150-й) — `~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // BGXR29 fighter quickslot bow-to-sword rule`. Это впервые подтверждает запись об установке R29 в реальной истории WeiDU. Само наличие записи **не** подтверждает реальное поведение R29 в бою, итоговый SHA его BCS или полезность сравнительно с уже LIVE V6. Не повторять R29, не откатывать R29 вслепую, не использовать прежний R27-last installer.

**Проверенная идентичность:** установленный `override/M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`; R27 ACTION_CONTEXT_V3 source-only SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`; `candidateSourceVerified=true`, `pinnedInstalledSourcesMatched=3`. Новый R27 V3 **не установлен**.

**НЕ доказано:** `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`, `typedInstallApproved=false`. R30 — статический read-only аудит, НЕ live queue telemetry и НЕ разрешение на обновление.

**Следующий P0:** использовать этот результат как gate для SOURCE ONLY проектирования **нового защищённого WeiDU-компонента после R29** (без зависимости от R27 being last, без удаления R29), но не устанавливать без отдельного typed согласия, верифицированного backup/rollback и безопасной EEex/EPS-диагностики. Двигаться к runtime bindings и реальному APR/THAC0/эффектам альтернативных слотов, не повторять R27/R28/167/168/170 без конкретного нового основания. Единственный пользовательский CMD сохраняется. Частный полный JSON-отчёт не публиковать в открытом репозитории.

---

## 25.11.2026 — R30 подключён в единственный обновлятор: menu170 READ ONLY (CODE/CI PASS)

**Текущий шаг проекта завершён:** R30 preflight добавлен в уже существующий `BGXAI/BGXAI_SYNC.ps1`, пункт **170**. `BGXAI_UPDATE.cmd` не менялся и остаётся единственным launcher; он динамически читает текущий BOOTSTRAP_PIN, загружает immutable backend и сверяет SHA256/размер. Нового CMD/PowerShell файла от пользователя не требуется.

- Backend immutable commit `71b1d37db787a59ed16c8b92ac495314b3577e02`, **79 979 bytes**, SHA256 `10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42`; bootstrap cap 80 000, оставлен 21 byte.
- R30 checker 7 985 bytes, SHA256 `88582abf17e919b9441795b8559cfe85b858fd3083672431eb36b60ba78981bd`.
- Candidate R27+ACTION_CONTEXT_V3 44 805 bytes, SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`.
- Menu 170 скачивает оба source по точным SHA, создаёт короткоживущие staging files в `%LOCALAPPDATA%\BGXAI_UPDATER`, вызывает только R30 с `--game` и `--candidate`, сохраняет JSON в `Documents\BGXAI_LIVE_REPORTS\BGXAI_R30_READONLY_*.json`, затем удаляет staging. Exit 2/HOLD тоже сохраняет отчёт. Ни один игровой файл, BCS, Lua, WeiDU, EPS, LOCALS или сохранение не меняется.
- Существующие switch dispatches **1–169 оставлены без изменений**. В compact menu сохранились категории/номера; 170 подписан R30 RO.
- [CI 45555311800](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311800) Windows+Ubuntu SUCCESS: exact pin, R30/R27 V3 bytes, R19 fixture, CMD and PowerShell 5.1 AST.
- [CI 45555311954](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311954) Windows+Ubuntu SUCCESS: PowerShell 5.1 parse, menu170 and unchanged 1–169 dispatches.
- Это **не** означает, что R30 уже запускался на пользовательской EET или что Lua binding доказан в runtime. R30 PASS возвращает только `SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`; никаких разрешений на установку/dispatch он не выдаёт.

**Следующий шаг — один пользовательский запуск:** открыть прежний `BGXAI_UPDATE.cmd`, выбрать `170`, прислать JSON по `REPORT_FILE`. Не запускать 165/167/168/169, не устанавливать R27 V3 и не соглашаться на typed install. По одному новому отчёту принять решение; при HOLD — никаких автоматических повторов.

Контрольная точка и инструкция: `BGXAI/BUILD/R30_QUEUE_DEPLOY_PREFLIGHT_RO_20261125/README_RU.md`.

---

## 25.11.2026 — R30/CURRENT R27 V3 снова согласованы: только CODE/CI PASS

Устранён зафиксированный ранее конфликт R30 с параллельно созданным `ACTION_CONTEXT_V3`. **Сначала** проверено, что актуальная чистая ветка собирает исходник R27 source-only: независимый GitHub [CI 45456677110](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45456677110) SUCCESS Windows+Linux, кандидат **44805 байт**, SHA256 **`61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`**, источник из `BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua`.

В **существующем** `BGXAI_R30_QUEUE_DEPLOY_PREFLIGHT_RO.py` обновлён SHA с исторического V2 `7ca77abe...` на точный собранный V3 `61744e9b...`. Кроме SHA, новый readonly preflight требует обязательные маркеры `queueSnapshotStable`, `actionContextSnapshotStable`, `actionSourceStable`, `UNCLASSIFIED_CAI_ACTION_M_SOURCE`, двойные снимки R2/R4 и жёсткие `actionOriginVerified=false`, `manualEpsQueueVerified=false`. Он отвергает старый queue-only V2 даже при подмене SHA в тестовом стенде. **Ни одна из этих проверок не предоставляет право на игровую установку.** Новые тесты R30 **12/12**; [CI 45553690490](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45553690490) SUCCESS Windows+Linux, R27 **90/90** Lua x3, V3 **442/442** x3. Следующий commit Workflow-лейбла меняет только число тестов 10→12, не алгоритм.

**DEPLOY NO / LIVE NEW V3 NO**: R30 всё ещё НЕ встроен в единственный `BGXAI_UPDATE.cmd`; на пользовательской машине не запускался; точно установленный R27 SHA `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735` не изменялся. Следующий P0 — безопасная интеграция **только read-only R30** в уже существующий пункт обновлятора, с one-run real WeiDU/EPS/EEex checks, но без повторного R27 native capture, без R29, без live-модификации без typed согласия.

---

## 25.11.2026 — R30 read-only preflight и обнаруженный параллельный конфликт R27

**CODE готов:** [R30 README](../BUILD/R30_QUEUE_DEPLOY_PREFLIGHT_RO_20261125/README_RU.md) и [контрольная точка](BGXAI_R30_PREFLIGHT_AND_CONTEXTV3_CONFLICT_20261125_RU.md). Новый preflight в **READ ONLY** режиме проверяет полный порядок WeiDU (R27 может быть не последним), точный SHA установленного R27 и установленного EPS/EEex, и source-only кандидата; не изменяет игру. Локально Python **10/10**. В [CI 45453114204](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45453114204) сам шаг R30 и Windows static **PASS**, но **общий workflow FAILURE** на несовпадении SHA исходника R27 после параллельного изменения `ACTION_CONTEXT_V3` коммитом `2dd3b91ba724`.

**ВАЖНО:** R30 пока закреплён на ранее известном Q81 V2 source-кандидате SHA `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`; он может быть устаревшим относительно текущего параллельного V3. **Не обнулять/переписывать новую ветку, не править SHA вслепую, не устанавливать R30, не предлагать пользователю отдельную CMD.** После согласования R27 build и текущего context V3 — снова PASS общего CI, затем интегрировать R30 read-only в **существующий** обновлятор и лишь после реального EET preflight обсуждать typed install. Состояние: `CODE 10/10; CI общий FAIL; DEPLOY NO; LIVE NO`.

---

## 25.11.2026 — EEex engine queuedActions → старый 081 → R27 → NONINTERRUPT (SOURCE/CI PASS)

**Новая продуктовая возможность на уровне исходников:** в официальных x64 структурах EEex найдены `CGameAIBase.m_queuedActions` и `CTypedPtrList.m_nCount`. Возвращён конкретный ранее отсутствовавший отрицательный сигнал: *когда в очереди двигателя есть ожидающие действия, не пересчитывать и не выбирать оружие*. На этом сигнале **НЕЛЬЗЯ** выводить происхождение приказа manual/EPS/AI.

- **081 V2** `BGXAI/fox_new/experimental_081_eeex_action_provenance_readonly_source_only/BGXAI081_ACTION_PROVENANCE_QUEUE_V2.lua` — без нового hook читает `m_queuedActions.m_nCount` дважды через `pcall`, сверяет `m_curAction.m_actionID`; допустимый raw диапазон 0..512, неизвестное или изменившееся → `nil`. `queue_empty=nil`, `eps_queue_empty_verified=false`, `safe_to_dispatch=false` всегда. **Старый 081 и 082 исторические файлы неизменны.** SHA256 `b3c9ecbc98c81e09d24279e4f970729750187ed6f4bafb2738572a37fa7d2edd`.
- **R27 source-only refresh** тот же `BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/`; обновлён детерминированный сборщик: компоновка R2+R4+Q81 в одном будущем callback, raw очередь до/после stat capture. Только устойчивый count+action → `queueSnapshotStable=true`, `queuedActionsRaw`; JSON публикует raw nonempty/null, всегда `actionOriginVerified=false` и `manualEpsQueueVerified=false`. Новый SHA256 `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`, **НЕ** установленный Lua. Старый live `M_BGXR27.lua` SHA `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735` и его WeiDU НЕ изменены.
- **Существующий NONINTERRUPT V1** теперь при совпадении actor/action и `queueSnapshotStable==true` + `queuedActionsRaw>0` возвращает `PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE`, **scorerCalls=0, next=nil**, не трогая текущее действие/очередь. Count=0 не даёт разрешения на switch. SHA256 `160c0b5a099ea170772dec12443f7273b92b8b99ec61a75f2e88052c9abc1cde`.

**TEST:** локально 081 441 Lua assertions, R27 77 checks + 9 Python, NONINTERRUPT 25 tests; [GitHub Actions 45447222518](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45447222518) **SUCCESS Windows+Ubuntu**: 081 441, R27 77, общий V3 regression 442 x Lua5.3/Lua5.4/LuaJIT; Windows static + Python PASS. Источник/границы/точные файлы: [BGXAI_QUEUE_081_R27_NONINTERRUPT_20261125_RU.md](BGXAI_QUEUE_081_R27_NONINTERRUPT_20261125_RU.md).

**CODE/TEST PASS; DEPLOY NO; NEW GAME LIVE NO.** В пользовательской EET ещё не проверена доступность Lua binding `m_nCount` и ручной/EPS origin; нет runtime effective APR одновременно альтернативных слотов. **Следующий единственный P0** — доказать passive runtime чтение engine queue, различить manual/EPS origin и подготовить защищённый producer без вмешательства в текущие действия, затем постепенно связать существующий V3/V4/V5 с достоверными alt-slot измерениями. Не предлагать повторные R27/R28/167/V6/R29 установки или ожидать немедленного автоматического выбора.

---

## 24.11.2026 — реальный API EEex: защита от временных m_tempStats (SOURCE + независимый CI PASS)

**Точный upstream EEex v1.1.7:** [EEex_Sprite.lua](https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua) — `EEex_Sprite_GetActiveStats(sprite)` возвращает `m_derivedStats` при `m_bAllowEffectListCall ~= 0`, но `m_tempStats` при `==0` (обработка эффектов в процессе). Ранее выбранный APR в таком окне можно было ошибочно принять за стабильный. Это исходник upstream, **не** повторная native-проверка в игре пользователя.

**CODE:** существующий `BGXAI_WEAPON_ACTIVE_R4_READONLY.lua` расширен методом `observeStableDerived`: строго читает `m_bAllowEffectListCall==1` до/после каждого из двух raw чтений всех 68 полей R4; запрещает любые смещения APR/THAC0/STR/haste/профили/действия/слота/способности. *После второго чтения* повторно сверяет action/selection, исключая гонку внутри самого getter. При любом несоответствии HOLD и **нет команды**. Старый R4 `observe` остался для исторической совместимости.

**Интеграция в существующий неустановленный R27 refresh:** исходник `BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua` детерминированно пересобран из SHA-pinned текущих R2/R4 и замороженного оригинального R27 tail. Теперь `R27.observe` использует `R4_CORE.observeStableDerived` вместе с прежними двумя проверками raw инвентаря. Только при стабильности в bounded JSON пишутся `selectedDerivedStatsDoubleReadConsistent=true` и точное `r4Status`. Новый SHA256 кандидата `18d1780a5b83b953f31f441cf81a1af489fc21b37e0e2ced05cc0261ec26008c`. Это **source-only** Lua без bootstrap/hook/установки. Старый **установленный** `M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735` НЕ изменён.

**R6:** в существующий `BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua` добавлены обязательные проверки `selectedDerivedStatsDoubleReadConsistent==true` и точного `r4Status`; запись старого R27 или с временным stats не попадает в исторический APR-кэш. Это только предотвращение неверного чтения, **не** вычисление альтернативного эффективного APR.

**TEST:** локально R4 **49/49** (LuaTeX), R27 **65/65** (LuaTeX) + **8/8** Python и R6 **18/18** расширенных локальных; независимый [GitHub Actions 45443795441](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45443795441) **SUCCESS Windows+Ubuntu**, Lua 5.3/Lua 5.4/LuaJIT: R4 **49/49**, R27 **65/65**, R6 **14/14** на каждом, прежний V3 regression PASS. Подробности: [README](../BUILD/WEAPON_V3_R4_DERIVED_STATS_STABILITY_20261124/README_RU.md).

**DEPLOY НЕТ; GAME LIVE новой версии НЕТ.** Нет доказанного runtime-вызова новой ветви в пользовательской EET. Полные эффекты, альтернативные одновременные APR, нативная ammo+launcher связка, ручные/EPS origins остаются **НЕ подтверждены**. Не переустанавливать V6/R27, не повторять R29. Единый `BGXAI_UPDATE.cmd`, PowerShell backend, закреплённый PIN, EPS, TD15, WeiDU, BG_EET_RU, BG Voice RU и сейвы не менялись. Следующий P0 — именно нативная/безопасная альтернативная effective-stats информация и manual/EPS arbitration, затем защищённая установка и один LIVE A/B, не очередной уже реализованный bow→sword.

---

## 24.11.2026 — R6 теперь принимает R27 с повторным чтением и не переносит APR на чужой слот (SOURCE/CI PASS)

**Практическое улучшение кода, не установка:** вместо очередного скорера доработан **существующий** `BGXAI/BUILD/R6_SELECTED_VS_ALTERNATE_SOURCE_V1/BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua`. Его старый путь R1/R2/R4 теперь сбрасывает исторические измерения APR при изменении raw экипировки, оружия, колчана, зарядов или флагов. Добавлен `R6.observe_r27` для ранее подготовленного **неустановленного** кандидата R27 с двойным чтением R2. Он привязывает измеренный APR и THAC0 к точному slot/resref/ability, последовательности событий, actor/party, текущему raw слепку оружия/колчанов/offhand. Изменение исходных полей или ошибочный/старый формат → сброс истории или HOLD. Данные другого слота никогда не объявляются текущими; ammo `AROW01` не объявляется доказанным APR `BOW05`.

**Реальные данные ранее получены:** сохранённые 16 игровых пар R1/R2/R4 дают *выбранное* `STAF01=1 APR`, `AROW01 raw=2`, `SW1H04 raw=7 (1.5 APR)`. Старый реальный R27: 24/24 callback (22 selected ammo, 2 sword), но в нём **нет нового double-read/offhand provenance**; `R6.observe_r27` **не** объявляется уже запущенным на этих старых событиях. Полные временные эффекты/бафы и итоговый APR **одновременно невыбранных** слотов, launcher-ammo engine binding и происхождение manual/EPS приказов не доказаны.

**Тесты:** R6 предыдущие 28/28 (две новые регрессии сброса истории), сохранённая реальная выборка 16/16, прежняя связь R6→R5 7/7, R27 формат 12/12 в GitHub + 16/16 расширенных локальных. GitHub Actions [45440557202](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45440557202): **SUCCESS Windows и Ubuntu**, Lua 5.3/5.4/LuaJIT плюс прежние 439-кейс V3 regression и R27 49-кейс. CI тестирует код и сохранённые события, **не** пользовательскую игру.

**CODE/TEST PASS. DEPLOY NO, NEW GAMEPLAY LIVE NO.** Не изменялись единственный `BGXAI_UPDATE.cmd`, `BGXAI_SYNC.ps1`, PIN, установленный `M_BGXR27.lua`, V6, BCS/WeiDU, EPS, BG Voice RU и BG_EET_RU. Исходники в `BGXAI/BUILD/R6_SELECTED_VS_ALTERNATE_SOURCE_V1/` и Library `/BALDURS_GATE_EET_AI/BUILD/R6_R27_SHARED_EVIDENCE_20261124/`. **Следующий P0 тот же:** доказуемый *сейчас* эффективный APR/THAC0/урон невыбранных слотов и безопасная manual/EPS граница; не дублировать эти кеши и не просить повторения старого R27 захвата.

---

## 24.11.2026 — исправлена потеря обновлённого R2 в исторической сборке R27 (SOURCE ONLY)

После 39/39 исправленных тестов R2 проверена цепочка до установленного R27: его `override/M_BGXR27.lua` по-прежнему содержит СТАРЫЙ встроенный R2 и один raw снимок, поэтому правка исходника R2 **не действовала на установленный R27**. Исторический установленный SHA `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`, не изменён.

**Код:** повторно использованы текущий SHA-проверенный R2, прежний R4 и оригинальный R27 event tail. Отдельный **неустанавливаемый** кандидат `BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua` (SHA256 `149fcf0e5079bb6f2ac0ca1bbd24fd10b46fea2f6422acabd42093be970e974e`): перед R4 читает все 4 quickweapon, 4 quiver и offhand, после R4 повторяет raw чтение, вызывает R2.compare и HOLD при изменении предмета/стрел/щита/действия. В консольный raw объект добавлен offhand, но не альтернативный APR. Действующее действие/очередь не трогаются, команды/LOCALS/WeiDU отсутствуют. Старый installable R27 модуль и инсталлятор не изменялись.

**TEST:** старые 33 R27 assert + 16 новых = 49 Lua assertions на каждом из Lua5.3, Lua5.4, LuaJIT; Python 8/8 тестов точной сборки, сохранности старого R27 и запрета команд. Регрессии V3 439/439 на каждом из трёх runtime. GitHub Actions [45437929376](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45437929376) **SUCCESS Windows и Linux**; первая попытка 45437732324 упала на Windows из-за конвертации LF→CRLF при checkout, исправлено git core.autocrlf=false до checkout, SHA-проверки НЕ ослаблены. **DEPLOY НЕТ, LIVE новой связки НЕТ.**

**Оставшийся P0:** получить НЕ смоделированные effective APR/THAC0/урон и активные эффекты альтернативных quickslot вместе с проверенным ammo/launcher и границей manual/EPS. Запрещено называть кандидата новым автопереключением или устанавливать повторно R27 ради этих технических проверок.

---

## НОВОЕ: устранён пропуск смены предмета при одинаковых зарядах (24.11.2026)

Доработан прежний `BGXAI_WEAPON_SLOTS_R2_READONLY.lua` (без параллельного модуля): сравнение текущего и предыдущего наблюдения теперь проверяет **itemResrefRaw, статус его чтения, itemTypeRaw, заряды, flags и offhand**. Ранее замена оружия/стрел на другие с теми же зарядными/флаговыми полями не сбрасывала stale priority advice. Теперь любое наблюдаемое различие даёт `INVALIDATE_WEAPON_ADVICE_KEEP_ACTION`; неполный/разреженный/нечитаемый снимок — `HOLD_INCOMPLETE_COMPARISON`. Нет engine commands, смены оружия, прерывания атаки, очистки очереди или разрешения dispatch.

**CODE:** существующий `BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_SLOTS_R2_READONLY.lua` и прежний тест. **TEST:** локально 39/39; GitHub Actions [45436002255](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45436002255) SUCCESS: 39/39 на Lua5.3, Lua5.4 и LuaJIT (117 запусков), прежние 439-кейс регрессии V3 на трёх Lua; Windows static PASS. **DEPLOY/LIVE:** NO, игру не трогали. **P0 не изменён:** реальный effective APR альтернатив, launcher/ammo, manual/EPS происхождение очереди, штатный BCS producer и затем A/B в игре.

---

> **Обязательное первое чтение для нового чата / помощника.** Это актуальный краткий паспорт проекта. Старые заметки сохраняются как история, но не должны переназначать уже закрытые задачи. Обновлять этот же файл после каждого доказанного изменения, а не заводить новый «план» на каждую проверку.

## 1. Цель и приоритет

**Цель пользователя:** реально работающий автономный ИИ партии Baldur's Gate EET + SCS 35.21 + EEex + EPS 18.4 на Insane, с безопасной магией, охраной, лечением и грамотным динамическим выбором оружия. Текущий единственный приоритет **P0 — Weapon Priority V3/V4/V5**: выбрать *лучшее доступное и применимое оружие* по реальному эффективному APR, THAC0, ожидаемому урону, бафам, спецэффектам, сопротивлениям цели, боеприпасам и расстоянию **без прерывания текущих действий**. После доказанного LIVE результата — остальные ветви партийного ИИ согласно прежнему плану.

**Не путать цель с пилотом** «Халид из лука на меч»: этот пилот уже работает и не является недостающей реализацией P0.

## 2. Матрица доказанного прогресса (CODE / TEST / DEPLOY / LIVE)

| Компонент | CODE / TEST | DEPLOY | LIVE / граница |
|---|---|---|---|
| **BGXRANGED6 (V6), DPLAYER.BCS** | Проверенный патч двух блоков | **Да**, подтверждённая установка 21.11.2026 | **Да**: Халид после сближения делал один дополнительный выстрел, затем переходил на меч. Новая V7 не нужна |
| BGXRANGED7 (V7) | Код и CI есть; итоговый SHA DPLAYER совпадает с V6 | **Нет подтверждения установки**; **не устанавливать** | Функционально дублирует V6 |
| **R27 (EEex)** | Рабочий observer выбранных характеристик | Установлен по прошлым результатам | **24/24** реальных callback, 0 ошибок; это **не** APR невыбранных слотов |
| **R28 (ITM evidence)** | Чтение реальных ITM/типов | Read-only | **4/4**: AROW01, BOW05, STAF01, SW1H04; структурная совместимость BOW05/AROW01, но не доказана реальная привязка ammo к launcher в движке |
| **167 Native V3 BAF** | 8 веток BAF, 8 действий, WeiDU 25100 | **Нет**, временная компиляция | **PASS на реальной EET**: BCS 10 550 байт, SHA256 `10426a2262e79553e861d464bdcf89d82a0fc91498dfb02c430c9b1fb02ef929`; боевое исполнение не проверено |
| **V3 ranker + V4 effects + V5 APR provenance + NONINTERRUPT + BAF consumer** | Исходники + офлайн-тесты; механизмы остаются read-only advisory | **Нет** единого работающего контура | **Нет** доказанной полной runtime-цепи от всех 4 слотов до защищённого выбора и команды |
| **R29, BDDEFAI.BCS** | Успешная нативная проверка **24.11.2026**: 1162 исходных блока сохранены, 1163 итоговых; SHA нового BCS `24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331`, 2 381 376 байт | **НЕИЗВЕСТНО после последнего сообщения**: прислан именно preflight с `gameModified=false`, но пользователь позднее сказал «я всё сделал»; нельзя утверждать ни установлен, ни не установлен | Повторяет узкий bow→sword сценарий V6 и **не** реализует V3, APR или защиту manual/EPS; **новых установок R29 не предлагать** |

**Особо важно:** `BDDEFAI.BCS` R29 и `DPLAYER.BCS` V6 — разные скрипты, но пересекаются по **поведению**. Сравнение R29 только с отсутствием V6 в BDDEFAI ошибочно. Сохранить R29 preflight как доказательство корректной компиляции, не как новую LIVE-функцию.

**Последний реальный результат пользователя:** `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R29_PREFLIGHT_20261124T155504699577Z.json`, нативный WeiDU `setup-enhanced-powergaming-scripts.exe` SHA `0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75`, R29 `gameModified=false`, `ordersSent=0`, `manualEpsOriginVerified=false`. Это состояние на момент **только этого отчёта**, не проверка поздней возможной установки.

## 3. Что требуется сделать дальше (строго по существующему плану)

1. **Сопоставить уже написанный код, не создавать новый ranker:** `BGXAI_WEAPON_PRIORITY_LUA_V3.lua`, `BGXAI_WEAPON_EFFECTS_V4.lua`, `BGXAI_WEAPON_APR_PROVENANCE_V5.lua`, `BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua`, `BGXAI_EEEX117_WEAPON_RUNTIME_EVIDENCE_V2.lua`, `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf`. В GitHub уже есть эти исходники. Закрытый 167 native compile **не повторять**.
2. **Одна конкретная недостающая техническая функция — достоверный per-quickslot snapshot из EEex/EPS в текущих условиях**: actual effective APR альтернативных слотов, THAC0, damage, эффекты/бафы, специализации/dual/multiclass, ammo↔launcher, недоступное/проклятое оружие, дальность и иммунитеты цели. Никогда не выдумывать значения из табличных бонусов или считать базовый APR уже окончательным.
3. **Защита происхождения команд и непрерываемости:** достоверно различить ручной приказ, действия EPS, каст/лечение и собственную очередь BGXAI; менять оружие только в проверенном безопасном окне; если данных нет — HOLD, не перехватывать текущие действия. Подтверждённое наблюдение `m_curAction.m_actionID` само по себе не доказывает происхождение приказа.
4. **Соединить существующие V3/V4/V5/NONINTERRUPT с защищённым producer и BAF consumer**, только после прохождения runtime gate. Не добавлять новую ветку `bow→sword`, которая дублирует V6. После source + exact tests + native SHA preflight, отдельное typed разрешение на модификацию игры с внешней резервной копией и WeiDU last-only rollback.
5. **Один осмысленный LIVE A/B** на отдельном сейве: дальнее/ближнее, дротик/праща/стрелы, APR от proficiency/бафов, бонусы силы и on-hit, иммунитеты, отсутствие простоев, ручной приказ, каст/лечение, дружественная агрессия. Признак результата — персонаж реально выбирает лучшее оружие, а не просто появляется очередной PASS JSON.

**Перед каждым новым шагом:** искать в таблице выше, исходниках и сохранённых отчётах уже выполненный аналог. Если функция уже работает в LIVE, не переустанавливать её ради другого имени версии. Если следующий шаг не добавляет новый полезный механизм либо новое необходимое доказательство — отклонить его как дублирование.

## 4. Управление версиями и безопасностью

- **Только один пользовательский запуск:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Никаких дополнительных пользовательских CMD, ручного PowerShell, ZIP-установок или повторных запусков 167/168/R27/R28/V6.
- Источник: GitHub `jeleZa112/nwn-xanos-updates`, ветка `bg-eet-ai`; каталог исходников `BGXAI/patchsets/ranged_fighter_guarded_20261119/`. Действующий backend `BGXAI/BGXAI_SYNC.ps1` — 79 927 байт, SHA256 `c55a5ebecc4e244e0fe263fc995b1e1b5d802b1d36c7b103475c7559bef78fbe`; не менять ради правки документации.
- Последний закреплённый R29 исходник от 24.11: immutable code commit `10905c8138dc72b3febb6629d164d9c33a6d292f`, pin update `f8cd1a2c5ae229e68504868f405950b03f51cc8f`; GitHub CI `45430266298` Windows+Ubuntu SUCCESS (53/53 R29 test cases). CI ≠ LIVE.
- Не трогать `BG_EET_RU`, `BG Voice RU`, сохранения, EPS и рабочую логику лечения/охраны/защиты от союзных AoE. Не изменять файлы игры без отдельного typed согласия. Если R29 **возможно уже установлен**, не делать blind rollback; для планирования сначала получить доказательство install/status только при необходимости, а не гонять новый preflight.
- Не обещать фоновую работу или автоматическую установку. Разрешено автоматически продолжать исходниковые и безопасные тесты **в текущем сеансе**, без «напиши +».
- Единственный отчёт пользователю на этап: *что нового заработало, чем подтверждено, что осталось, что делать ровно один раз*. CODE/TEST/DEPLOY/LIVE показывать отдельно.

## 5. Передача новому чату

В начале **прочитать этот файл и старый основной план** `BGXAI_REAL_STOP_POINT_AND_PLAN_20261124_RU.md`, затем `BGXAI_20261121_SAVELOAD_HANDOFF_RU.md` и `BGXAI_NATIVE_167_PASS_JOIN_R27_R28_20261124_RU.md`. `00_AUTO_CONTINUE_READ_FIRST.md` содержит большую историю и **устаревшие верхние инструкции**; считать настоящую дату/актуальность и этот паспорт главнее старых промежуточных обещаний. НЕ начинать новый V7/R29 или ещё один bow→sword пилот. Продолжать с пункта **3.2**: доказуемые реальные альтернативные quickslot-статы + происхождение очереди действий; затем интеграция существующих V3/V4/V5.

**Правило обновления:** при реальном изменении обновлять разделы 2–4 **этого же файла**, включая дату и подтверждения, а не создавать ещё один неувязанный файл. Сохранять подтверждённый прогресс как неизменяемую историю — не подменять «установлено» результатом CI или preflight.

## 6. Все предыдущие чаты / полный архив исходников (новое, 24.11.2026)

**Сводный реестр всей доступной истории BGXAI** — [`BGXAI_ALL_CHATS_MASTER_ARCHIVE_20261124_RU.md`](BGXAI_ALL_CHATS_MASTER_ARCHIVE_20261124_RU.md). В нём восстановлены ранние 0.6/0.7/BGXUNI, 038–066S, EPS-first, 067/role, BGXP/Heal, BGX120/AoE, BGXSAFE/friendly aggro, V1/V2/V6 ranged, R13/R27/R28, Weapon V3/V4/V5/NONINTERRUPT, 167/168 и R29; LIVE/DEPLOY/TEST разграничены. Есть отрицательные результаты, известные ошибки, принятые запреты, исходный план, ссылки на оригинальные контрольные точки. История **не является дословной копией всех чатов**, но доступные результаты восстановлены без выдумывания новых установок.

**Полный исходный каталог** — [`BGXAI_COMPLETE_SOURCE_TREE_20261124.json`](BGXAI_COMPLETE_SOURCE_TREE_20261124.json), включающий 1 584 существовавших BGXAI-файла с Git blob SHA, размером и путём из неизменяемого snapshot `037e1c483c12f83c03083bb894ae5c120e707585`, а также связанные GitHub Actions. Все исходники доступны через `https://github.com/jeleZa112/nwn-xanos-updates/tree/bg-eet-ai/BGXAI`. Это инвентарь, а не переустановка и не утверждение, что все варианты работают.

**Сохранённая личная Library** `/BALDURS_GATE_EET_AI/` — при инвентаризации 24.11: 1 755 файлов (коды, отчёты, тесты, архивы, переводы игровых ресурсов и checkpoint документов внутри BGXAI); копии не удалены. Приватные отчёты и сейвы не опубликованы в открытом GitHub. Всякое новое продолжение проекта должно использовать этот реестр, а не спрашивать повторно уже переданные файлы.

**Следующий единственный P0:** полный EET/runtime snapshot всех 4 slots + доказательство manual/EPS границы → интеграция существующих V3→V4→V5→NONINTERRUPT/BAF → разрешённая установка → игровой тест. **Ни R29, ни V7 не повторять для переключения лук→меч.**
