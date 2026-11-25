# BGXAI — короткий актуальный статус на 25.11.2026

## 25.11.2026 — R31 УСТАНОВЛЕН на пользовательской EET; ожидает LIVE passive capture

**Первичный источник от пользователя:** `BGXAI_R31_INSTALL_20261125T131628301568Z.json`, schema `BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1`; `status=R31_PASSIVE_INSTALLED_AWAITING_RUNTIME`, `installationPerformed=true`, `gameModified=true`, `typedInstallApproved=true`. Отчёт относится к фактически запущенной EET, а не к CI. Установлен R31/V3 через новый WeiDU-компонент после ранее подтверждённого R29. По коду защищённого установщика этот статус выдаётся только после проверки R31-last и SHA игрового `override/M_BGXR27.lua`.

**Верифицированный источник:** R31 live Lua SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`. В отчёте указан внешний backup (хранить, не удалять): `C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXR31_mcy15k64`; прежний Lua SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`. `baselineSnapshot` содержит HASH WeiDU.log, EPS/EEex, `BDDEFAI.BCS`, `DPLAYER.BCS`, `chitin.key` до установки. Не делать ложного вывода, что снимок равен послестановочному перечню: пост-установочные проверки кода не меняют BCS/ключ/EEex, но JSON публикует именно baseline.

**Границы:** `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`, `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`; альтернативный effective APR и последствия в live не проверены. Старый R27 listener должен быть заменён на R31-сборку только после полного перезапуска InfinityLoader, а не параллельно в той же сессии. `CODE/CI=PASS`, `R31 PREFLIGHT=PASS`, `R31 DEPLOY=PASS per install report`, `R31 LIVE=NO`.

**Единственное следующее действие пользователя:** прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **171 → 5 (capture)**. Обновлятор проверит установленный R31 и запустит InfinityLoader для захвата одной сессии в `Documents\BGXAI_LIVE_REPORTS\BGXAI_R31_CONSOLE_*.log`. Загрузить обычный тестовый сейв, провести 2–3 действия персонажей (например, несколько атак с луком/мечом), штатно выйти из игры. Прислать JSON `BGXAI_R31_CAPTURE_*.json` и `BGXAI_R31_CONSOLE_*.log` из путей `reportFile`, если они появятся. Отдельно не повторять `171→1` и `171→2`, не запускать старые R27 установщики/rollback. При STOP/HOLD прислать точный JSON/текст без повторного запуска. Не объявлять поведение R29/Weapon V3 доказанным этим capture.

**История и тесты:** real READONLY PRECHECK `BGXAI_R31_PREFLIGHT_20261125T063640325949Z.json` PASS; настоящий WeiDU 251 TP2 parse-check (Windows/Linux) [CI 45562250963](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45562250963) SUCCESS. Установленное состояние — новый факт, который отменяет нижележащие исторические фразы `R31 не установлен` и `установку пока не выполнять`.

---


## 25.11.2026 — REAL R31 PREFLIGHT PASS + NATIVE WeiDU 251 TP2 parser PASS (Windows/Linux)

**Реальный источник (от пользователя):** `BGXAI_R31_PREFLIGHT_20261125T063640325949Z.json`, `schema=BGXAI_R31_GUARDED_V3_SOURCE_ONLY_V1`, `status=R31_SOURCE_PREFLIGHT_PASS_INSTALL_STILL_UNAUTHORIZED`. 150 WeiDU компонентов, R27 №149, R29 №150, новый R31 НЕ установлен (`installationPerformed=false`, `gameModified=false`, `ordersSent=0`). Доказаны точные исходники и хэши из текущей установки. Заново запускать 171→1 НЕ нужно.

**Контрольная точка:** `WeiDU.log` SHA256 `3cec176f9e6eab721f7aa931c29e7e0d7a4a0d70fab346cffbbb4ae58960e0d6`; live `override/M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`; R31 candidate SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`; BCS `BDDEFAI.BCS` SHA256 `24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331`; `DPLAYER.BCS` SHA256 `4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed`. Все значения подтверждены реальным readonly JSON. Остальные подробности — в отчёте, но не публиковать весь приватный файл в публичном GitHub.

**Новый независимый native parser smoke:** подготовлен `R31_NATIVE_TP2_PARSE_RO.py`, с архивами официального WeiDU **v251.00**, фиксированными SHA256 релизных ZIP, `--nogame --parse-check TP2` только во временной папке. [GitHub CI 45562250963](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45562250963) **SUCCESS** на Ubuntu и Windows. Это реальный синтаксический разбор WeiDU, не mock, однако это НЕ установка/откат и не подтверждение runtime EEex. Ранее исправлены только тестовые LF CRLF/escaping проблемы; оригинальные R31 guard Lua/Python и pinned update не изменены.

**CODE/TEST/READONLY PREFLIGHT/PARSE:** PASS. **DEPLOY/LIVE R31:** NO. Нет `queueBindingLiveVerified`, `manualEpsOriginVerified`, `alternateEffectiveAPRVerified`. Даже native parse не даёт права на игровое dispatch. Не повторять R27/R29/R30 и не дублировать разработку наблюдателя.

**Следующий строго ограниченный шаг после отдельного буквального согласия пользователя:** закрыть Baldur's Gate, InfinityLoader, WeiDU; через ЕДИНЫЙ `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` выбрать `171→2` и самостоятельно ввести точный токен `INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29`. Сценарий до игры выполняет повторный SHA/preflight и внешний проверенный backup, устанавливает BGXR31 только после R29, не допускает автоматических исправлений или отката. После установки прикрепить `BGXAI_R31_INSTALL_*.json` и пока НЕ запускать игру до проверки результата. При HOLD/STOP ничего не повторять и не делать rollback вслепую. Отдельная проверка LIVE после установленного PASS — пункт 171→5, но её не назначать до анализа отчёта установки.

---


## 25.11.2026 — R31 menu171 ВСТРОЕН И ЗАКРЕПЛЁН (CI PASS, установка NO)

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


## 25.11.2026 — R30 запущен на EET: PASS READ ONLY, R29 подтверждён в WeiDU

**Новое фактическое подтверждение:** R30 menu170 выполнен на пользовательской EET 25.11.2026. `status=SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`, `readOnly=true`, `gameModified=false`, `installationPerformed=false`, `ordersSent=0`, `dispatchAuthorized=false`.

**WeiDU:** 150 компонентов; R27 — позиция 149, `r27IsLast=false`; последний (150-й) — `~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // BGXR29 fighter quickslot bow-to-sword rule`. Это впервые подтверждает запись об установке R29 в реальной истории WeiDU. Само наличие записи **не** подтверждает реальное поведение R29 в бою, итоговый SHA его BCS или полезность сравнительно с уже LIVE V6. Не повторять R29, не откатывать R29 вслепую, не использовать прежний R27-last installer.

**Проверенная идентичность:** установленный `override/M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`; R27 ACTION_CONTEXT_V3 source-only SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`; `candidateSourceVerified=true`, `pinnedInstalledSourcesMatched=3`. Новый R27 V3 **не установлен**.

**НЕ доказано:** `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`, `typedInstallApproved=false`. R30 — статический read-only аудит, НЕ live queue telemetry и НЕ разрешение на обновление.

**Следующий P0:** использовать этот результат как gate для SOURCE ONLY проектирования **нового защищённого WeiDU-компонента после R29** (без зависимости от R27 being last, без удаления R29), но не устанавливать без отдельного typed согласия, верифицированного backup/rollback и безопасной EEex/EPS-диагностики. Двигаться к runtime bindings и реальному APR/THAC0/эффектам альтернативных слотов, не повторять R27/R28/167/168/170 без конкретного нового основания. Единственный пользовательский CMD сохраняется. Частный полный JSON-отчёт не публиковать в открытом репозитории.

---

**R30 MENU170 — ВСТРОЕН В ЕДИНЫЙ ОБНОВЛЯТОР, CODE/CI PASS.** Существующий `BGXAI_UPDATE.cmd` остаётся единственным launcher и не менялся. Pinned `BGXAI_SYNC.ps1` immutable commit `71b1d37db787a59ed16c8b92ac495314b3577e02`, 79 979 bytes, SHA256 `10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42` (bootstrap cap 80 000). Новый пункт `170` скачивает точный R30 (7 985 bytes; SHA256 `88582abf17e919b9441795b8559cfe85b858fd3083672431eb36b60ba78981bd`) и R27 V3 candidate (44 805 bytes; SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`), делает SHA-check, выполняет только READ ONLY R30, пишет один JSON в `Documents\BGXAI_LIVE_REPORTS`, чистит staging. Существующие menu handlers 1–169 не изменены.
- [CI 45555311800](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311800) Windows+Ubuntu SUCCESS: one-CMD pin, R30/R27 actual SHA, R19, embedded PS5.1 AST.
- [CI 45555311954](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311954) Windows+Ubuntu SUCCESS: menu170, old dispatches 1–169 unchanged, PS5.1 AST.
**USER PC R30 NOT RUN.** Следующий шаг: старый `BGXAI_UPDATE.cmd` → пункт `170` → прислать полный JSON `REPORT_FILE`. Не выбирать 165/167/168/169; ничего не устанавливать. Даже R30 PASS не разрешает установку. Подробности: `BGXAI/BUILD/R30_QUEUE_DEPLOY_PREFLIGHT_RO_20261125/README_RU.md`.

### Исторические записи до подключения menu170 (сохранены для аудита)

**NEW P0 25.11 — реальная очередь действий стала доступна как SOURCE-ONLY отрицательный сигнал.** Versioned 081 V2 читает x64 `m_queuedActions.m_nCount` (две попытки, action-id stability), R27 refresh в одном listener-кандидате снимает очередь до/после raw+derived stats, NONINTERRUPT V1 при известных ожидающих действиях делает `PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE`, `scorerCalls=0` и не трогает игру. **Нуль НЕ доказывает отсутствие ручного/EPS приказа.** [CI 45447222518](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45447222518) Windows/Linux SUCCESS, 081 441 assertions, R27 77, V3 442 на трёх Lua; `CODE/TEST PASS, DEPLOY NO, LIVE NO`. Подробно: `BGXAI_QUEUE_081_R27_NONINTERRUPT_20261125_RU.md`. Следующий runtime gate — фактический binding очереди + EPS/manual arbitration, alt-slot effective APR ещё не реализован.

**Эта карточка заменяет устаревший статус с утверждением, что R29 ещё не прошёл native preflight.** Обязательны: `BGXAI_CANONICAL_HANDOFF_20261124_RU.md` (приоритеты и фактическое CODE/TEST/DEPLOY/LIVE), `BGXAI_ALL_CHATS_MASTER_ARCHIVE_20261124_RU.md` (вся восстановленная история, ошибки, первичные источники), `BGXAI_COMPLETE_SOURCE_TREE_20261124.json` (1 584 оригинальных source-файла и связанные workflows).

- Рабочая игра: EET + SCS35.21 + EEex1.1.7 + EPS18.4, Insane, `C:\Games\BG_EET_FOXX_NEW`. Единственный CMD: `BGXAI_UPDATE.cmd`.
- **V6 реально установлен и наблюдался в LIVE**: Халид сделал один лишний выстрел, затем выбрал меч. Не повторять V7/R29 как новую функцию.
- **R27** реально наблюдал выбранные характеристики 24/24; **R28** проверил 4 ITM; **167** реально скомпилировал 8-веточный V3 BAF во временный 10 550-byte BCS. Новая Weapon V3 **не установлена**.
- **R29 native preflight PASS** на EET 24.11: 1162→1163 блоков `BDDEFAI.BCS`, новый SHA256 `24d94062ebc7226dc3486ecad3786dca7e5edae424cef0f13d8a4577cff36331`, `gameModified=false`. **Последующее состояние установки R29 неизвестно**; нет install log/PROOF. Не назначать ни повторную установку, ни слепой откат.
- **Связка R27 + актуальный R2 (24.11):** выяснено, что установленный R27 содержит старую R2 копию. Подготовлен точный **SOURCE ONLY** кандидат `BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua`, двойное чтение 4 weapon/4 quiver/offhand, HOLD при изменениях. Тесты 49 Lua x3 + 8 Python, [CI 45437929376 SUCCESS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45437929376). **Не установлен, V6/R27 live и updater не менялись.**
- **Обновление исходников V3 R2 (24.11):** исправлено обнаружение замены оружия/стрел/второй руки при одинаковых зарядах; 39/39 Lua tests на каждом из 3 runtimes, CI 45436002255 SUCCESS. **SOURCE/CI PASS, DEPLOY/LIVE NO.** Нет нового игрового действия.
- **EEex R4 active-stats guard (24.11):** по точному upstream EEex v1.1.7 выявлена ветка `m_tempStats` во время пересчёта эффектов; в существующий R4 добавлено строгое дважды стабильное чтение `m_derivedStats` при `m_bAllowEffectListCall==1`. Неустановленный R27 refresh теперь проверяет R4+R2 double-read и пишет `selectedDerivedStatsDoubleReadConsistent` + `r4Status`; R6 не принимает исторический APR без этих признаков. Независимый [CI 45443795441](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45443795441) **Windows/Linux SUCCESS**: R4 49/49, R27 65/65, R6 14/14 на каждом Lua5.3/5.4/LuaJIT, Python 8/8. **SOURCE/TEST PASS; DEPLOY NO; GAME LIVE NO.** Не считать безопасную выборку выбранного слота доказательством APR альтернатив.
- **R6 выбранное APR → R27 double-read, source only (24.11):** существующий R6 исправлен: при смене слота/предмета/колчана/зарядов/offhand исторический APR сбрасывается; добавлен `observe_r27` для **ещё не установленного** двухснимкового R27. Реальные 16 событий прежнего R1/R2/R4: посох 1, selected ammo 2 (не доказанный APR лука), меч raw7=1.5; старые 24 события R27 не содержат новой двухснимковой проверки. CI [45440557202](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45440557202) SUCCESS Windows+Ubuntu / Lua 5.3, 5.4, LuaJIT. **Нет нового gameplay deploy и нет текущего effective APR альтернатив.**

- Главный недостающий результат — **effective APR/THAC0/урон/эффекты всех альтернативных слотов, launcher+ammo и непрерывность ручных/EPS команд**. Источники V3/V4/V5/NONINTERRUPT/BAF есть, но нет проверенного полного контра от реального EET snapshot до игрового приказа.
- Приоритет **P0 интеллектуальный выбор оружия**; закрыть его до нового пилота AoE/Role/Magic. Новое изменение игры только с отдельным typed consent, SHA, backup, WeiDU last-only rollback. CODE/CI никогда не считать GAME LIVE.
- Доступные наработки из старых чатов сохранены и систематизированы в Library `/BALDURS_GATE_EET_AI/`, GitHub `bg-eet-ai`; не запрашивать повторно R27/R28/167/168, три EET архива, saves/scripts и старые отчёты.

**Чего сейчас делать не надо:** 166, 169→2, повторно 167/168/R27/R28, любые установки/откаты ради отчёта.
