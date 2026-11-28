# BGXAI — ЕДИНСТВЕННАЯ КАНОНИЧЕСКАЯ ТОЧКА ВОССТАНОВЛЕНИЯ

<!-- RESUME_GUARD_BGXAI_R39_BAF_BYTES=2303 -->
<!-- RESUME_GUARD_BGXAI_R39_BAF_SHA256=3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d -->

## 28.11.2026 — R41 SOURCE-ONLY FIXED + VERIFIED, ИГРОВАЯ УСТАНОВКА ЗАПРЕЩЕНА ДО LIVE PROOFS

**RESUME_VERDICT:** RESUME_PARTIAL_SAFE_ONLY; полный текст чата BGXAI 1.5.1 недоступен, но ветка `bg-eet-ai`, исходники и отчёты в текущих handoff проверены. **PRIOR_WORK_RECEIPT:** R39 already native-compiled 2407B (реальный `BGXAI_R39_NATIVE177_20261128T061446243176Z.json`), R40 4632B source-only reset, R41 11/11 offline mock. Не повторять 176→7, R38 capture, V3/V6/R29, не писать новый ARM/обновлятор.

**Только исправленная дельта:** существующий `build_r41_link_sourceonly.py` ссылался на несуществующий `R39.../M_BGXW3_SESSION_RESET_V1.lua`, хотя исходник уже есть в соседней `R40_SESSION_RESET_SOURCEONLY_20261127/`; путь восстановлен, SHA-проверки оригинальных R39/R40 сохранены. В существующем R41 мосте теперь отказ `addDestroyed`/`addLoaded` со значением `false` считается провалом регистрации. Никаких изменений оригинального R39/R40/BAF, AI, EPS, игры, PIN или одного `BGXAI_UPDATE.cmd`.

**CODE:** исходник R41 = **21603 байта**, SHA256 `a808848e1752ebff8251bf56af96dc8983654359fa722b60858d57edea78da4e`; генератор = **7140 байт**; bundled original modules embedded unchanged. **TEST:** [GitHub Actions 46117471549](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46117471549) **SUCCESS Ubuntu+Windows**: **118/118 Python tests on each OS** (including clean-checkout reproduce builder) и **14/14 Lua lifecycle mock** на Ubuntu (включая явный отказ callback регистрации). Это не нативный EET runtime. **DEPLOY:** только GitHub source/CI; R41 game install = NO; **LIVE XEquipItem = NO**.

**Первый реально незавершённый рубеж:** доказанный installed-EEex `ports.capture` для конкретного Джагана, действующий script owner/assigned BCS (прежний `probeInstalledScriptAssignments` source-only уже есть), динамическая usability/effects, manual/EPS boundary и R40 before-AI order. Затем **только** existing one-file updater + separate typed approval + BCS exact baseline/last-only rollback + external backup + disposable-save single LIVE item transfer. Не подставлять `true` вместо runtime proof; не просить повторные native/old capture.

---

**Дата сверки:** 2026-11-28. **Приоритет:** этот короткий файл → фактическая текущая ветка → последние отчёты пользователя → [подробная хронология](000_READ_FIRST_LIVE_PROGRESS_R38.md) только для доказательств. Старые `00_CURRENT_STATUS`, `00_AUTO_CONTINUE_READ_FIRST` и README — перенаправления/история. Не выполнять старые `next` из архивов.

## 2026-11-28 — ПОДТВЕРЖДЁННЫЙ ПОВТОР V3 В НОВОМ R39 ARM

**ERROR_GATE: FAIL_BEFORE_NEW_CODE.** Новый `M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua` был разработан до полного сравнения с `WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127`. Это нарушение PRIOR WORK GATE. В V3 УЖЕ ЕСТЬ actor-local `BGXW3ARM/TAG/TRY`, точный `XEquipItem`, single-shot и проверки бездействия/очереди. Не представлять их как новую разработку R39. Сравнение подтверждено кодом V3 и исходником R39; см. [подробный handoff](000_READ_FIRST_LIVE_PROGRESS_R38.md).

**Только новая дельта R39-arm:** предложенная **ручная** комбинация `Ctrl+Alt+Shift+F12` для одного *первого проверочного переноса*, плюс предлагаемые double-snapshot/epoch/readback ограничения; пока **SOURCE/MOCK**, не интегрировано в игровой EEex, кнопка не утверждена пользователем. Это НЕ автономный выбор лучшего оружия и НЕ доказанный игровой перенос.

**Реальные блокеры:** не доказан адаптер live actor+item/kit/usability/manual-EPS, вызов R40 *до первого BAF тика*, настоящая компиляция R39 BAF в текущей EET, защищённая установка через единственный updater и LIVE перенос. **V3/R37/R38/081–085/R40/priority V3-V5 не переписывать.** Исходник R39 и пользовательская игра не установлены/не изменены этой записью. Перед любым новым source-кодом требовать короткую проверенную `PRIOR_WORK_RECEIPT` с указанием конкретного старого файла, совпадающей функциональности и *исключительно недостающей* дельты. Если предшественник не проверен: остановить разработку, не создавать новую реализацию.


## Текущая проверенная функция: перенос оружия из рюкзака (R39/R40)
- **CODE:** R39 source-only `BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf`: **2303 байта**, SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`. Новый BAF добавил Name/Class/STR/empty shield проверки, сохраняет EPS `Continue()` в служебных блоках. **2079-байтная версия SHA `7d57cec...` — архивная, запрещена для будущих pin/compile.**
- **TEST:** локально R39 **53/53** Python checks, в том числе **12/12 mock** проверок нового `BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py`, проверка соединения сохранённых R38/R3 evidence; R40 **13/13** Python + **22/22** texlua. Пакетный CI новой версии и реальный native WeiDU compile именно 2303B **не подтверждены**; mock ≠ native.
- **DEPLOY:** R38 действительно установлен ранее с backup; **R39/R40 не установлены**, native-helper **не включён** в один пользовательский updater.
- **LIVE:** R38 дал **34/34** корректных наблюдений, из них **10** относятся к Джагану, **24** отфильтрованы как другой актёр; `ordersSent=0`. Успешного `XEquipItem` из рюкзака **нет**. Старый V6 уже показал live-переключение лук→меч.
- **Физические данные уже извлечены:** прежний R3/R38 snapshot подтвердил `STAF01.ITM`, STR=12, пустую вторую руку и slot35, но **не** подтвердил актуальную kit/usability, безопасность manual/EPS или session-ARM.

## НЕ ПОВТОРЯТЬ
R38 install/capture, native V3 (176), R3/R34 предмет, V6 переключение, source-only проверки 071/081–085 ради нового отчёта. Не путать `SelectWeaponAbility` со `XEquipItem`. Не писать второй обновлятор или альтернативный listener.

## ЕДИНСТВЕННАЯ НЕДОСТАЮЩАЯ ДЕЛЬТА
Сверить и подтвердить рабочий engine-facing actor+session-bound ARM (в исходниках V3 + экспериментальном R39 он уже частично реализован, но не интегрирован) и право конкретного Джагана использовать STAF01 в актуальной EET, защитить ручные/EPS действия; провести **native-readonly EET compile именно 2303B R39** через существующий `176` helper, затем при соблюдении безопасности встроить проверенный guarded пилот в **один** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Изменение игры только по отдельному typed-разрешению с SHA/backup/WeiDU last-only. **Пользователю пока не требуется повторять прежние тесты.**

**Доказательства:** [главная подробная контрольная точка](000_READ_FIRST_LIVE_PROGRESS_R38.md), [R39 source + адаптер](../BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/), [глобальное восстановление](../../GLOBAL_PROJECT_RULES/GLOBAL_CROSS_CHAT_RESUME_V1_RU.md), [антидублирование](../../GLOBAL_PROJECT_RULES/GLOBAL_PRIOR_WORK_GATE_V1_RU.md).

**Перед началом нового чата:** повторно проверить фактический GitHub HEAD, точный current BAF и новые пользовательские отчёты. Если они изменились, обновить **этот** файл с реальными доказательствами, не писать новый `latest/read-first`. При отсутствии данных обозначить `HISTORY_INCOMPLETE`, а не «реализации не было».
