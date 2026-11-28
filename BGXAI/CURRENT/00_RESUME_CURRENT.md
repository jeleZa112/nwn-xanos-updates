# BGXAI — ЕДИНСТВЕННАЯ КАНОНИЧЕСКАЯ ТОЧКА ВОССТАНОВЛЕНИЯ

<!-- RESUME_GUARD_BGXAI_R39_BAF_BYTES=2303 -->
<!-- RESUME_GUARD_BGXAI_R39_BAF_SHA256=3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d -->

## 28.11.2026 — R39 SCRIPT-PILOT PHYSICAL BCS GATE — SOURCE CI PASS, LIVE STILL HOLD

**SOURCE/PRIOR WORK:** Existing `BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua` previously read seven assigned EEex BCS resrefs after checking only portrait ID, class 3 and kit 16384; it might have returned another cleric's script names if party membership changed. Instead of new owner system/observer, `probeScriptAssignments()` now **reuses already-defined `exactPhysical()`** to match current single selected actor in portrait1, source STAF01 unique in slot20, target slot35 empty, offhand empty and exact actor/class/kit; repeats physical proof after two reads of script assignments. Any mismatch or mutation fails closed. **Physical pilot match is not authenticated scriptName or actual BCS execution**. Global receipt `BGXAI_R39_SCRIPT_OWNER_EXACT_PILOT_PREWORK_20261128` was recorded before source code modification, machine preflight PASS both OS [run 46118458028](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118458028); all dependent predecessor pins verified and updated. Existing R37/V3/081 code reused, no new action listener.

**CODE:** existing R39 native read-only bridge **10917B, Git blob `71411f7f6e4989a5237242b88e95166755a894df`**. R39 2407B EET native-compile-PASS BAF, R40 original 4632B, R41 compiled source bundle 21603B unchanged. **TEST:** [R39/R41 CI 46118593957](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118593957) **SUCCESS Windows+Ubuntu**: 118/118 Python each OS; V3 27 cases/4 expected real-GAM skips each OS; Ubuntu native Lua **R39 bridge 34/34 PASS** (eight added wrong actor/selection/changed inventory/no-trigger cases), R41 14/14 PASS. `project_tools/resume_guard.py` and `--preflight` both PASS. No false runtime approval.

**FOUND ERROR + METHOD:** an initial prework receipt used predecessor from `BGXAI/fox_new` rather than required `BGXAI/BUILD`; later the V3 saved-CRE reader still pinned previous R39 bridge SHA, producing expected RESUME DRIFT. Corrected both; recorded in existing `GLOBAL_PROJECT_RULES/KNOWN_ERROR_GATES_V1.json` as `BGXAI_R39_PROVENANCE_BUILD_SCOPE_AND_DEPENDENT_SHA_DRIFT_20261128`. Recheck *all dependent receipts* whenever a predecessor changes.

**DEPLOY/LIVE:** game untouched; R39/R40/R41 not installed; no first `XEquipItem`. Cannot select a BCS to patch on `scriptLevelResrefs` alone: `actualBcsExecutionVerified=false`, `scriptSlotOwnershipVerified=false`, `nativeScriptNameVerified=false`, `actionOriginVerified=false`, `canArm=false` even for a physical-match result. **First next real delta:** obtain real installed EEex/current script execution/owner evidence for exact Jagan (using same existing single updater when safely linked), prove item/effects+manual/EPS boundary and R40 startup order, then staged typed-only last WeiDU install+external backup+rollback and one trial STAF01 equip. Never rerun 176→7, install R39 on guessed BDDEFAI/PRIEST1, or treat synthetic GAM fixture as real BCS names.

---

## 28.11.2026 — SAVED CRE SCRIPT REFS READONLY: CODE/TEST PASS, REAL SAVE RESREFS STILL UNKNOWN

**PRIOR WORK GATE:** Before editing the existing V3 GAM reader, committed scoped reviewed receipt `BGXAI_V3_GAM_CRE_SAVED_BCS_ASSIGNMENTS_PREWORK_20261128` to the existing global registry (commit `34218661aa0e`); compared existing V3 GAMEV2.0/CRE inventory parsing, R39 EEex117 in-memory script-assignment reader and exact predecessor blob SHA. No new GAM parser, no new action listener, no new updater.

**CODE:** existing `BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/verify_candidate_ro.py` now reads the **five saved CRE V1.0 resrefs at 0x248, 0x250, 0x258, 0x260, 0x268**, mapping to `SCRLEV 0,4,5,6,7`. It includes them as `savedCreScriptResrefs` only for the existing verified actor/item candidate. **Not** the live `SCRLEV 1/2` area/specifics, not an executing BCS, not script slot ownership. Does not grant `itemEngineUsable` or `ports.capture` or R41 installation approval. Existing R39 BAF 2407B, original R39/R40, generated R41 21603B unchanged.

**TEST:** [V3 CI 46118100842](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118100842) **SUCCESS both OS**, 27 test cases per OS, 4 expected real-GAM skips, including 3 new synthetic saved-CRE script regressions. [R39/R41 CI 46118109030](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118109030) **SUCCESS both OS**: exact R39/bridge pre-existing tests, new V3 tests, `project_tools/resume_guard.py` predecessor/integrity gate, and Ubuntu 14/14 Lua R41 lifecycle. First synthetic fixture CI run failed due accidentally escaped byte literals, fixed before passing CI; do not cite that failed intermediate as final. No native game compilation rerun.

**EVIDENCE LIMIT:** Previously examined real `BALDUR(1).gam` (SHA256 `7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c`) established Jagan and STAF01, but its original **bytes were unavailable for this new check**. Therefore the **real saved script values remain UNKNOWN**, not `BDDEFAI`/`PRIEST1` inferred from the synthetic fixture. No repeat request to user for an already provided save until reusing available project evidence is exhausted.

**CODE/TEST:** saved CRE reader PASS. **DEPLOY/LIVE:** no game changes, no runtime actor BCS proof, no R41 install, no live `XEquipItem`. **Next:** obtain real save script refs through existing one-updater read-only path if available; independently confirm actual runtime EEex assignments/execution and EPS/manual safety; only then prepare typed guarded install + external backup + last-only rollback and one disposable-save transfer.

---

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
