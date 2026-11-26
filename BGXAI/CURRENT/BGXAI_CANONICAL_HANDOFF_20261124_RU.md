## КРИТИЧЕСКОЕ УТОЧНЕНИЕ ИГРОКА: АВТОПЕРЕКЛЮЧЕНИЕ И МЕЧА, И ЩИТА

В бою с больным гибберлингом Халид **самостоятельно переключился с лука на ПАРУ `SW1H04` (длинный меч) + `SHLD03A` (щит)**; **оба элемента боевого комплекта**, включая щит, были переключены автоматически во время боя без ручного вмешательства игрока. Ручные действия были **только до начала боя**. Прошлая формулировка «меч при уже экипированном щите» была неточна и исправлена. Пользователь видел переключение щита; консоль подтверждает выбранный меч (`selectedWeaponRaw 12→35`) и наличие `SHLD03A` в offhand slot 9 на снимках, **но сама по себе не доказывает переход состояния щита** (требуется различать offhand slot и активный комплект). Источник автоматической смены (EPS или прежний BGXAI/BCS) телеметрия по-прежнему не идентифицирует; R37 не отправлял приказов. Не внедрять заново уже работающую пару меч+щит, а исследовать фактическую задержку перехода, избыточные выстрелы в упор, последующий возврат к луку и сохранение очереди действий.

---

## Уточнение пользователя — подтверждено непосредственно участником игрового теста

**Во время всего боя Халида с больным гибберлингом игрок НЕ вмешивался в действия персонажа; ручные действия были ТОЛЬКО ДО начала боя.** При переключении Халид использовал **длинный меч `SW1H04` ВМЕСТЕ С экипированным щитом `SHLD03A`**. Сопоставляется с консольным `offhandRaw slot=9 resref=SHLD03A` на событиях `seq=1..12` и `selectedWeaponRaw:12→35` на `seq=9`. Это повышает уверенность в **реально автономной смене лук→меч в бою без ручного приказа**. **Не означает, что источник команды уже идентифицирован:** `actionOrigin=UNKNOWN` в телеметрии; могли сработать существующие EPS/BCS/BGXAI-механизмы, но не пассивный R37. **Не создавать второй конкурирующий переключатель лук→меч без анализа уже работающего поведения**. Остаются вопросы оптимальности задержки, дистанции, штрафа близкого лука, сохранения очереди, передвижения, возврата к дальнобойному оружию, щита в активном слоте и общий выбор по эффективному APR/бафам/предметам.

**Важно для тестов:** при фразе "руками не вмешивался" понимать период **во время боя**; перед боем пользователь мог выполнять подготовку вручную. Не распространять это утверждение на всю игровую сессию.

---

# BGXAI 26.11.2026 — R37 РЕАЛЬНЫЙ GAME LIVE PASSIVE ПРОВЕРЕН (12/12)

**Новейший факт, отменяет устаревшие ниже "R37 NOT INSTALLED" как исторические:** пользователь прислал `BGXAI_R37_CONSOLE_20261126T050555209778Z.log` и `BGXAI_R37_CAPTURE_20261126T050723691038Z.json`. Итог `R37_RUNTIME_ADVICE_LOG_READY_FOR_REVIEW`, `gameExitCode=0`; **1 session, 12/12 пар R33/R37**, правильные seq/partyIndex, 0 malformed/unsafe, 0 HOLD, `ordersSent=0`, `weaponSwitchAuthorized=false`. `r37InvalidationSamples=7` = 1 первоначальная инициализация + 4 action changes + 1 расход стрел (20→18) + 1 переход выбора оружия (slot12→slot35), 5 RAW equal. Реальный Халид в бою с больным гибберлингом: лук BOW05 + AROW01, получил close-range штраф -8 при критическом промахе, **естественная смена на SW1H04**, попадание мечом, 9 рубящего урона, смерть врага, 8 XP. При этом `m_nNumberOfAttacks` RAW меняется 2→7 — **не интерпретировать как 7 APR**, схемы не подтверждены. `actionOrigin=UNKNOWN`, `safeActionBoundaryVerified=false` — отсутствие доказанного EPS/manual origin или безопасного активного вмешательства, R37 по-прежнему не переключает оружие. LIVE PASS относится ТОЛЬКО к пассивной регистрации, инвалидации/сбору; **ACTIVE SWITCH NOT VERIFIED/NOT AUTHORIZED**.

**Каноническая карточка фактов:** [`BGXAI/CURRENT/R37_LIVE_PASSIVE_20261126_VERIFIED_RU.md`](R37_LIVE_PASSIVE_20261126_VERIFIED_RU.md). Исходные пользовательские файлы не загружены в публичный GitHub. Отдельный warning в консоли `Error loading menu ... ']' expected near 'icon'` и отсутствующие UI strings — независимая проблема меню, **BG_EET_RU и UI не менять** в BGXAI. Полный исходный CMD и guard ранее успешно проверены; новые исходники не менялись. Следующий этап P0: исследовать существующую естественную смену без дублирования EPS, найти действительный пробел в поведении и безопасный action boundary; повторять этот же бой для R37 не требуется.

---

# 2026-11-26 R37 LIVE PREINSTALL STOP ROOT CAUSE FIXED (NO GAME MUTATION)

**User real-world INSTALL log:** `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R37_INSTALL_20261126T033431851543Z.json`, STOP `R33_PREINSTALL_RESOURCE_BASELINE_CHANGED` immediately after user selected `BGXAI_UPDATE.cmd → 174 → 2` and typed `INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33`. Review of actual R33/R37 Python guarded source proved **R37 hardcoded `BASELINE_SHA['override/DPLAYER.BCS']` wrongly TRUNCATED TO 50 HEX DIGITS**, while original installed R33 used the correct 64-digit SHA256 `4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed`. Other five resource SHA literals match R33. This is a bug in *our R37 guard*, **NOT** verified game file drift; user should NOT change/reinstall DPLAYER, R33, EPS or mods. Guard `proof_r33` rejected before `external_backup`, stage, any WeiDU or file writes; `gameModifiedUnknown:true` is generic conservative catch, not a claim of actual mutation.

**Exact repair DONE:** `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py` now uses the correct 64-digit literal and reports the exact mismatch resource suffix if another preinstall drift occurs (`R33_PREINSTALL_RESOURCE_BASELINE_CHANGED:<rel>`). Guard updated **26,252 bytes SHA256 `b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d`**; `test_r37_guarded_install_mock.py` adds 2 regressions, comparing all six R37 hashes against AST-constant original R33 at source and rejecting any non-64-char SHA plus verifies mismatch no WeiDU. **27/27 tests Win/Linux PASS** [R37 guard CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45749902092).

**ONE updater FIXED + VERIFIED:** `BGXAI/BGXAI_SYNC.ps1` stays **79,832 B** under hard original CMD limit 80,000, new SHA256 `a9d788e00026bb41b21ed96b3aa3d5b5ca8517471b3b1f8755f460b8c9124e12`, immutable commit **`7bcc496de93cd10155aadc6c5321fa68a1a26fbe`**. `BGXAI/fox_new/BOOTSTRAP_PIN.json` UPDATED to this SHA/commit in commit `5e61da598dfcd0b6d2a7a0147b09efccc4375de4`. Menu 174 stages SHA-pinned fixed R37 guard and existing unchanged Lua 60,835 B SHA `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`. Menus **1–173 byte identical**, original `BGXAI_UPDATE.cmd` unchanged. New [Windows+Linux onefile SHA/mode174 CI 2/2 PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45749964204). [Full comprehensive source CI PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45749902051) but source-only != gameplay.

**LIVE:** User's R37 **still not installed** (known failed preflight before mutation). Existing R33 remains assumed pending live hash recheck in next trusted preflight; don't claim R37 running. Single next user action: close game, original `BGXAI_UPDATE.cmd` → `174` → `2`, exact token once. Guard will independently verify actual R33/current files and make external backup before WeiDU. On success `R37_PASSIVE_INSTALLED_AWAITING_RUNTIME`, later `174→5` for R37 read-only capture, save `BGXAI_R37_CAPTURE_*.json`. If STOP again DO NOT repeat or restore automatically; inspect named specific reason. Typed user install approval always required; no background installs.

---

# BGXAI 26.11.2026 — R37 live capture via menu174/5; SAFE HOLD exit2, immutable ONE CMD

**Что уже сделано:** `BGXAI_UPDATE.cmd` оригинальный и неизменённый; 174-й пункт backend `BGXAI_SYNC.ps1` имеет 1=preflight (default), 2=typed install, 3=status, 4=typed last-only rollback, **5=read-only capture**; все handlers 1–173 байт-в-байт предыдущие. При 5 запускает ИСХОДНЫЙ InfinityLoader и ждёт закрытия игры, пишет `BGXAI_R37_CONSOLE_*.log` и один `BGXAI_R37_CAPTURE_*.json` в `Documents\BGXAI_LIVE_REPORTS`, с последовательностью `[BGXR27]`/`[BGXR37]` (seq+party, statuses, invalidated advice), без actor IDs и вымышленной manual/EPS source attribution. Если события небезопасны/непарные/нет session/exit!=0, возвращает **HOLD + exit code 2** после сохранения отчёта; не «успешно завершено». Это безопасный пассивный сбор, не управление оружием.

**КАНОНИЧЕСКИЙ ПИН, проверенный hard-limit 80К:** `BOOTSTRAP_PIN.json` pinned immutable `commit=3c869ebad84fecaac8a671aa0105069b5c9ccb54`, `script_size=79832`, `script_sha256=65e4c5fe29355cad35d4ef565042edf5cdbcd507e846e340056dcc5816246d43`. CMD не изменялся и принимает только <=80,000B. Guard module `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py` **26210 B SHA256 `5dca3b0709a70687221e640a2fc8a4d1e3ca12e5ffa34baeeddb8d174479ba0e`**. Lua `M_BGXR27_R37_SOURCE_ONLY.lua` 60835 B SHA256 `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`. All three hashes hard-verified; source-only tests.

**TESTS:** [25 R37 guarded Python tests on Win+Linux, including capture HOLD=exit2, READY=exit0, typed SHA backup and last-only rollback PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45678510306). [R37 onefile menu174 native Windows PS5.1 AST + Ubuntu SHA tests before pin release PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45678748271). [Full comprehensive 7/7 source CI with R37 capture tests PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45678510335). These are CODE/TEST, not real EET combat. **R37 DEPLOY/LIVE NOT PERFORMED**.

**REAL NEXT STEP:** Only user can run Windows game. One and same `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; select 174, option 2, type token `INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33` (will first verify exact installed R33 WeiDU last 152, R33 proof, SHA resource baseline, closed game, external backup, native WeiDU last 153; STOP on any mismatch). After install JSON `R37_PASSIVE_INSTALLED_AWAITING_RUNTIME`, relaunch same CMD → 174 → 5, load existing save, perform brief normal combat, exit game; send **just latest `BGXAI_R37_CAPTURE_*.json`**. If installer/capture STOP, preserve JSON/log, no manual retry/rollback. Source test or "+" cannot authorize game mutation; only typed token in interactive installer.

**P0 afterwards:** inspect real matched R33+R37 events for ammo/selected APR/stat/action transitions, meaningful invalidations; still no manual/EPS provenance `m_source`, no action boundary safety, no simultaneous alternate slot APR or validated launcher/ammo -> active weapon switch remains blocked. No duplicate EET installation or separate updater; never touch BG_EET_RU, BG Voice RU, EPS healing/AoE/saves.

---

# BGXAI 26.11.2026 — R37 GAME CAPTURE READY via ONE CMD menu174/5 (NO LIVE INSTALL YET)

**Новая функциональность пользователя:** добавлен **пятый вариант `capture`** в существующее меню `174 — R37`. Старые варианты `1 preflight (default), 2 typed install, 3 status, 4 typed rollback` сохраняются. Источник `R37_GUARDED_SOURCE_ONLY.py` теперь **25 946 bytes, SHA256 `027932392848962a3f903cc50495df34c56f2a2943648c5ff625a8fd95789ab5`**. Capture запускает исходный `InfinityLoader.exe` только после проверки, что R37 — последний WeiDU (#153) и typed proof присутствует, ждёт обычного выхода пользователя из игры, затем выдаёт один `BGXAI_R37_CAPTURE_*.json` с paired `R33+R37` events, status, invalidations, HOLD reasons. Данные захватываются из ТЕХ ЖЕ `[BGXR27]` и `[BGXR37]` строк, связываются по seq и party, при неизвестных/unsafe lines fail-closed. Raw console `BGXAI_R37_CONSOLE_*.log` остаётся в `Documents\BGXAI_LIVE_REPORTS`, но пользователь обычно передаёт **ТОЛЬКО JSON**. Никогда не выдаёт активных оружейных приказов.

**Immutable one-updater:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` НЕ изменялся. `BGXAI/BGXAI_SYNC.ps1`: **79 832 bytes SHA256 `19608a52f76bd81723278e4e9095c16865ef1d2b9e45aebd19a5112c205ecc2c`** под жёстким hard-cap CMD 80 000 bytes. `BOOTSTRAP_PIN.json` на immutable `commit=1c0be1e444329c94b79fe7c1d630caf87d333d4c`. Menu choices 1–173 byte identical; menu174 guard and stage SHA pinned. No second CMD/PowerShell. Lua R37 unchanged 60 835 bytes SHA256 `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`.

**CI:** [23 guarded install+rollback+capture tests on Win/Linux PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45677774149); [menu174 2/2 jobs PASS including Windows PS5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45678041977); [comprehensive all 7/7 jobs PASS including 23 R37 new Python tests](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45678133670). **CODE+TEST PASS**; **DEPLOY/LIVE R37 = NO**. No real game changes by this work, no new weapon switching active. R33 user machine remains last known live.

**NEXT:** *NOT* another source CI, *NOT* ask repeated '+' or old R27/R33 logs. Via the same preexisting CMD, (i) user enters `174` then `2`, and types exact required token `INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33` to authorize WeiDU R37 upgrade; this does an internal guarded preflight and external backup; if STOP, do not retry/rollback automatically, inspect STOP JSON. (ii) after `R37_PASSIVE_INSTALLED_AWAITING_RUNTIME`, user relaunches same `BGXAI_UPDATE.cmd` → `174` → `5`; in launched game loads existing save, performs one normal fight/no contrived tests, closes game, sends only `BGXAI_R37_CAPTURE_*.json` from `Documents\BGXAI_LIVE_REPORTS`. If game fails/no status then pass STOP log, no presumed success.

**Blocked until future proof**: manual/EPS origin `m_source` unknown, no safe attack boundary, full current/alternate APR context, ammo-launcher identity; no dispatch or new active automation. Do not change BG_EET_RU, BG Voice RU, EPS healing, AOE or saves.

---

# BGXAI 26.11.2026 — защищённый R37 теперь в ЕДИНОМ обновляторе, меню 174, CODE/CI

**ФАКТ:** добавлен пункт **174 — R37 R33+R36 passive advice** в `BGXAI/BGXAI_SYNC.ps1`. Сам `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` не изменялся. Меню `1–173` и их однострочные обработчики побайтно равны предыдущей закреплённой версии (SHA/current predecessor `1404112c2889561b99416e48a4ba06ab947c4fee`). Новый 174 по умолчанию `1=preflight` (без установки), `2=install` (точное typed подтверждение), `3=status`, `4=rollback` (отдельное typed подтверждение). Один backend, два SHA-проверенных remote source, без второго CMD и без REST API. Новый обработчик не загружает R37 в игру сам по себе и не разрешает переключение оружия.

**КРИТИЧЕСКИЙ FIX**: исходно новый backend вырос до 80 806 байт, при том что embedded original `BGXAI_UPDATE.cmd` имеет **ЖЁСТКИЙ лимит 80 000 байт** и отказался бы его запускать. Исторические `1–174` handlers сохранены точно; безопасно вынесены повторяющиеся пути из source manifest-спецификаций в PowerShell константы (`$ps,$dev,$build,$sm,$p64,$i64`). После проверки Windows PS5.1 итоговый backend **79 701 байт**. Установленный game root, WeiDU, EPS и game scripts не менялись.

**Текущий канонический bootstrap pin**: `BGXAI/fox_new/BOOTSTRAP_PIN.json`, `commit=52f73efaa2900b6cdee6ff0f428ae6744193fafd`, `script_size=79701`, `script_sha256=5efb1648aa107f24bb785553e89f23bffa744c3220c1740e6b57d7303f64b71c`. Исторический pin R34 (`1404112...`) теперь сменён на R37; **не возвращать** его автоматически и не использовать старый 80 806-byte pin (`377d912...`). Единственный оригинальный CMD остаётся byte-identical.

**Источники R37, каждый с независимой проверкой SHA256:**
- `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/M_BGXR27_R37_SOURCE_ONLY.lua`: 60 835 байт, SHA `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`. Всё ещё ровно один исходный R33 callback, 2 stats reads, 0 игровых приказов.
- `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py`: 19 107 байт, SHA `847d59d70f14274a005244b009850a8f563e2a302517e8237cdcb063bc23b9ab`. Обязателен R33 last в WeiDU 152 components, installed R33 proof, current R33 Lua SHA и исходники EPS. Перед установкой: closed-game process guard, SHA baseline, внешний `Documents/BGXAI_BACKUPS/PRE_BGXR37_...` со сверкой копий, stage, native WeiDU only + проверка 153-го компонента. Откат возможен только если R37 — последний WeiDU, а файлы не дрейфовали; возвращает R33, не R31. Нет авто-ретрая, raw restore или бесконтрольных записей.
- Токен установки `INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33`, отдельный токен отката `ROLLBACK_BGXAI_R37_RESTORE_R33_ONLY`. Наличие меню не является согласием на установку.

**CI:** [R37 guarded mock 17 tests Windows/Linux PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45675195682), включая симулированные install/backup/rollback и негативные случаи; [R37 60k Lua module 3/3 PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45671377104); [R37 onefile menu 174 Windows/Linux SHA+original 173 handlers PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45676948121). [Полный BGXAI comprehensive 7/7 PASS с меню174](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45676603739) (это run до lossless compacting, последующий run указан в workflow истории). SOURCE/TEST не означает игрового LIVE.

**DEPLOY/LIVE:** версия R37 доступна в удалённом закреплённом source, но **R37 в игре НЕ установлен**, текущее `override/M_BGXR27.lua` продолжает R33. Нет новых данных из игры после R34; no EEex actor commands; `dispatchAuthorized=false, weaponSwitchAuthorized=false`. Для самого фактического запуска пользователя использовать **только** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` пункт 174, исходно preflight-only, затем отдельный typed install при пользовательском согласии. Никаких вторых CMD, повторных R27/33 боёв, ручного копирования Lua.

**P0 после успешного реального R37 runtime:** в действующем одном обработчике проверить R36 invalidation в настоящем `[BGXR37]` log, а затем отдельно достоверную EPS/manual action origin / безопасную recovery-boundary. Нулевой raw count `m_queuedActions` и недоступный `m_source` по-прежнему не разрешают switch. Спутников, Healing/AoE/AntiFriendly и BG_EET_RU/BG Voice RU не менять.

---

# BGXAI CURRENT 26.11.2026 — R37 same-listener R33+R36 composed, source/CI PASS, NOT INSTALLED

**User sent '+' after R36. We DID real source integration rather than another standalone observer.** After inspecting actual `BGXAI/BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/M_BGXR27_R33_SOURCE_ONLY.lua` and original [Bubb13 EEex Action.lua](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/EEex_Action.lua), built `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/M_BGXR27_R37_SOURCE_ONLY.lua` (60,835 bytes, **SHA256 `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`**, Git blob `4f4258f14c3e02b4fd2c1ca3e38dd17cc0f61db4`). Base frozen R33 SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`; R36 core exact git blob `f7d4e11a219cd254a52a0f53f18582c9415223af`. Exact candidate and provenance pinned by [R37 manifest](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_SOURCE_ONLY_VERIFIED_MANIFEST.json).

**What R37 implements:** R36 `capture(sample)` and `compare(previous,current)` now invoked within existing ONE R33 `R27.makeListener` callback, after same R2/R4/081 observation; exactly **2 existing getActiveStats reads/callback, 0 extra reads and 0 additional EEex listeners**. Bounded prior context cached by party (6 entries, 64 events), HOLD clears stale advice. Original R33 `[BGXR27]` JSON remains unchanged. Same existing console writer additionally prints short `[BGXR37]` status: first observation, unchanged RAW context (NOT proof of buffs), changed ammo/equipment, action, stats or natural selected slot, or hold. NEVER orders `Attack/Stop/SelectWeaponAbility/ClearActions`, never activates switch. Under real R33 historical evidence ammo slot 12 count 20→19 and action 23→3 would invalidate *only the cached recommendation*, not actor attack or queue. No raw actor ID in R37 added console line.

**CI:** [R37 3/3 jobs SOURCE PASS Windows/Linux + Lua 5.3/5.4/LuaJIT](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45671377104); native Lua full ~60KB candidate mock confirms **one listener**, 2 stats reads, 7 staged events including quiver 20→19, action and STR shift, HOLD + recovery, zero engine commands. Full [BGXAI combined complex suite including R37 7/7 jobs PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45671539930) including weapon V3-V5, R27-R37, BGXP healing, AoE, friendly safety and sole PS5.1 updater. Detailed [R37 README](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/README_RU.md).

**CRITICAL CODE/TEST≠DEPLOY/LIVE:** R37 source-only, never copied into user's EET, no WeiDU install, no updater change, no new gameplay observation. Existing live R33/R34 untouched. EEex started-action listener gives (sprite, action) but does **not** directly certify that action came from player or EPS. Actual R33 `m_source` field was `ACTION_SOURCE_POINTER_UNAVAILABLE`; `m_queuedActions.m_nCount=0` does not authorize a weapon switch. Manual/EPS action ownership, full effects fingerprint, simultaneous alternate effective APR/THAC0, launcher-ammo and safe recovery boundary still UNKNOWN and hard fail-closed (`weaponSwitchAuthorized=false`). Next: prepare a future **one updater** guarded read-only R37 pilot with typed install, external backup, SHA, WeiDU last-only rollback; no second CMD or duplicate listener and never active weapon control absent proof. Do NOT request repeat old R27/R33/R34 or battle.

---

# BGXAI — 26.11.2026: R36 наблюдение за контекстом и непрерывность действий (SOURCE/CI)

**Новая фактическая точка:** пользователь продолжил работу после полного комплексного теста [run 45667708256](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256). В исходниках установлено: **R33 уже делает** double-read выбранных APR/THAC0, боевых raw stats, 46 WPROF, слотов, очереди и контекста 081 в **ОДНОМ EEex callback**. Поэтому не устанавливать отдельный R35 listener и не делать повторное чтение `EEex_Sprite_GetActiveStats`. R36 — **анализ уже собранного**, а не новая система переключения оружия.

**Реальный пользовательский R33 лог заново изучен (не смоделирован):** `BGXAI_R33_CONSOLE_20261125T161358491052Z.log`, исторический SHA `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`, единственный SESSION, 8 событий одного актёра и одного выбранного ammo slot 12, APR raw 2 (=2 APR), selected THAC0 raw 20. Отдельно сравнены последовательные пары: **5 равных raw-контекстов**, **1 смена actionRaw 23→3 (5→6)**, **1 изменение raw ammo useCount1 20→19 в quiver slot 12, `AROW01`, между 6→7** (действие также 3→23, но главное отличие — боеприпасы). Результат: инвалидировать **только** cached weapon advice; нельзя переотдать Attack/Stop или изменить очередь. Не доказывает, что стрела потрачена именно выстрелом, что BOW05 launcher точно связан с AROW01, или что все бафы неизменны. `m_source` не читается: `ACTION_SOURCE_POINTER_UNAVAILABLE`. Нулевой raw queue count НЕ даёт права на смену оружия.

**НОВЫЙ SOURCE:** `BGXAI/BUILD/R36_R33_CONTEXT_INVALIDATION_RO_20261126/BGXAI_R36_R33_CONTEXT_INVALIDATION_RO.py` — bounded parser известного SHA R33 console и строгий cross-event validator; 27 тестов на Windows и Ubuntu; не публикует raw actor ID и не меняет игру. `BGXAI/BUILD/R36_R33_CONTEXT_INVALIDATION_RO_20261126/BGXAI_R36_R33_ADVICE_INVALIDATION.lua` — чистая `capture(sample)` и `compare(before,after)`, принимают **готовый** R33 sample; без EEex API вызовов, listener, action, файловых записей. Для будущего подключения в уже существующий R33 callback с типизированным согласием, не установлен. 20 проверок на Lua5.3/5.4/LuaJIT. [R36 CI 3/3 jobs PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45669160840). [Полный совместный BGXAI CI, включая R36, **7/7 jobs PASS**](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45669355598). README: [R36](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/BGXAI/BUILD/R36_R33_CONTEXT_INVALIDATION_RO_20261126/README_RU.md).

**CODE vs LIVE:** R36 CODE+TEST PASS, `DEPLOY=false`, `LIVE_R36=false`. Из прежних — R33 live 8 events и R34 current-game ITM read-only 5/5. В текущем этапе `BGXAI_UPDATE.cmd`, `BGXAI_SYNC.ps1`, `BOOTSTRAP_PIN.json`, WeiDU, EPS, saves, BG Voice RU, BG_EET_RU **не изменялись**. Активное переключение всё ещё запрещено (`dispatchAuthorized=false`, `weaponSwitchAuthorized=false`); без подтверждения all effects, same-scene other-slot APR/THAC0, launcher-ammo, manual/EPS action origin и устойчивой границы атаки не выдавать исполнителю разрешения.

**Следующая P0:** определить достоверный и безопасный способ классифицировать EPS/manual action в текущем движке; raw CAIAction source остаётся UNKNOWN, наблюдать отдельно только после read-only source preflight и явного типизированного разрешения на изменение игры. Существующие V3/V4/V5+NONINTERRUPT использовать, не переделывать их и не требовать повторного R27/R33/R34 или боёв.

---

# LATEST 26.11.2026 — full BGXAI cross-platform source CI 7/7 PASS

See exact comprehensive [report](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/BGXAI/CURRENT/BGXAI_COMPREHENSIVE_REGRESSION_20261126_RU.md). User requested complex test. Real GitHub Actions [run 45667708256](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256) 7/7 jobs PASS after fixing **test driver only** (earlier run's PowerShell Read-Host stub quoting). Source test matrix: 4,828 PASS test cases/assertions, 4 SKIP with known reasons; all R27–R35 Windows/Linux, Lua V3/V4/V5 and R35 three runtimes, BGXP3/4/5, AoE, friendly, ranged, PS 5.1 isolated pinned onefile start/exit. Raw uploaded real R28+R34 also independently checked locally: 24 selected events, four exact native ITM SHA+origin+proficiency overlaps, no game writes. This is CODE/CI/old existing real files, not fresh gameplay LIVE. No new installer, no reruns of R27/R33/R34 required. R35 passive APR/THAC0 source not installed; EPS/manual origin, whole effects, simultaneous alternate slot APR and safe action window still HOLD; active switching off.

---

# LATEST 26.11.2026 — R35 EEex selected APR/raw THAC0 observer built and tested, NOT INSTALLED

In addition to original R35 historical R27/R34 bridge (22 selected ammo APR2, 2 selected sword APR1.5), new source-only `BUILD/R35_NATURAL_SELECTED_APR_RO_20261126/BGXAI_R35_SELECTED_ENGINE_STATS_RO.lua` safely reads current selected APR key and raw THAC0 from EEex active stats within a callback, double-read stable, rejects `m_bAllowEffectListCall==0` temp stats. 16 Lua tests on each of Lua5.3/5.4/LuaJIT, plus 13 Python tests Windows+Linux, **[R35 all 3 CI jobs PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45666482574)**. Original game/R33, user updater/WeiDU, EPS, saves, BG Voice RU and BG_EET_RU untouched. No new listener or weapon orders. Not yet deployed or live verified; comparison between two natural slot selections is historical, not simultaneous other-slot effective APR, no same-buff fingerprint or EPS/manual ownership. Next P0 audited live effects and action ownership in existing R33 callback, not duplicate scoring or repeating R27/33/34. Full latest status is first block of `BGXAI/CURRENT/00_CURRENT_STATUS.md`.

---

# UPDATE 26.11.2026 — R35 real natural selected APR evidence + CI PASS (SOURCE ONLY)

After user "+" following real R34 5/5 CURRENT ITM PASS, R35 `BUILD/R35_NATURAL_SELECTED_APR_RO_20261126/` is implemented. Actual R28 historic R27 capture shows **22 events selected ammo slot 12, APR key 2 (2 APR)**, **2 events selected sword slot 35, APR key 7 (1.5 APR)**; all 4 overlapping native ITM SHA/proficiency/origin agree with R34 current EET item reads. This is **NOT** a simultaneously validated bow-vs-sword APR comparison: slot12 is ammo, BOW05 launcher pair unproven; historic different action times and active effects/THAC0 unknown. [R35 Windows/Linux tests PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45665814622), [R34+R35 regression PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45665910474); no game changes, orders, new user onefile or additional capture. Official EEex GetActiveStats/GetStat read currently active/possibly temp work-in-progress, not arbitrary alternate slot. Continue live-context safe passive observation in existing EEex listener and action ownership proof; preserve V3/V4/V5 and NONINTERRUPT, no duplicate scorer/weapon V6 and no aggressive patch without typed install approval. Latest full status: `CURRENT/00_CURRENT_STATUS.md`.

---

# UPDATE 26.11.2026 — R34 real current-game ITM join verified

Latest real result is **R34 5/5 CURRENT_GAME native ITM read-only PASS**. See first block of `CURRENT/00_CURRENT_STATUS.md` for exact no-private-path SHA provenance, output status, historical actor profile limitations and next P0. `BGXAI_R34_NATIVE_PROF_20261126T002126164.json` inspected; game unchanged, zero commands, no autoswitch. Four ITM SHA match previous R28; SHORT_BOW BOW05 statID105 is 0 historic pips, while historical longbow statID104 is 1. **Do not request repeat R34/R33, battles or old tests.** Next: effective alternate-slot APR/THAC0 & effect provenance + manual/EPS origin, then integrate existing V3/V4/V5, respecting one CMD / typed game-change consent.

---

# CURRENT 26.11.2026 — supersedes dated instructions below

**Source of truth:** `CURRENT/00_CURRENT_STATUS.md` first section, not older 24–25 Nov steps. The user already ran R34 with `124add6624c4`, received `R34_R33_NAMED_LOG_DIFFERS_AND_FAILS_FINGERPRINT` on 26.11 at 00:06 and no game changes. R33 installed and real 8/8 capture previously PASS. Do **NOT** ask for another battle, capture, R33 install or repeat 173 on the old pin.

On 26.11 previous user-uploaded real R33 log was re-examined (1 SESSION, 8 consistent samples) and compared to real R28 native ITM report. Historical BOW05 is **shortbow** `proficiencyIdRaw=105` and Khalid has **0 shortbow pips**, despite 1 longbow pip (`stat104=1`). SW1H04 long sword prof90, Khalid 2 pips; staff prof102, Khalid 0. This is cross-date evidence, not proof of unchanged 26.11 game ITM.

R34 source corrected to use one strictly validated archived historical 8-event aggregate if the local old log is rejected; all such outputs explicitly mark the archive provenance and never allow action dispatch. R34 `BGXAI_SYNC.ps1` remains 79,775 bytes and preserves 1..172 handlers; immutable `1404112c2889561b99416e48a4ba06ab947c4fee`, SHA256 `9131e29da59b7d3a62651eab3ff7deee514da426cfbe6a1267b54444e9c6f59a`, R34 source SHA256 `d40f7729ee84c576d08fe712b98adcd0704611def6385e976a50597b68c496c4`; BOOTSTRAP_PIN points to commit. CI [R34 3/3 active Windows/Linux PS5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096145) and [R33 5/5 historical](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096366) **SUCCESS**, source R34 Windows/Linux tests PASS. **No new user-PC runtime R34 after fix**; no game modification/weapon switching. Action origin/manual/EPS, alternative effective APR, complete effects and safe boundary remain HOLD. Next focus use V3/V4/V5 with proven proficiency mapping and actual APR, not new bow-to-sword pilot. New single 173 read-only run is now optionally available only for CURRENT live ITM refresh; it does NOT make archived R33 stats contemporary.

---

# BGXAI — единая точка продолжения, 24 ноября 2026

**CI FINAL 25.11.2026:** R34 source-only 22/22 Windows/Linux PASS (run 45660217453); R34 79775B active pin + real PS5.1 menu boot 3/3 PASS (run 45660513142); historical R33 source/proof/WeiDU 5/5 PASS (run 45660551436). Exact user live R34 after hotfix still PENDING. No game writes.

## 25.11.2026 — R34 REAL USER LOG PIN STOP resolved in 124add6624c4 (read only)

Новый реальный пользовательский вывод: `BGXAI_UPDATE.cmd` verified immutable `b678020a5dee`, меню 173, STOP `R34 LIVE LOG PIN STOP`. Это **не** ошибка исходного SHA: загруженный настоящим пользователем `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` в чате содержит 101981 байт, SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538` и 8 валидных событий R33. Ранее использовался неинформативный тест SHA на одном единственном имени; он не отличал отсутствующий файл от изменённого, и ещё до чтения реальных ITM запрещал продолжение.

Выполнено: R34 Python `choose_r33_log` — ограниченное обнаружение `Documents\BGXAI_LIVE_REPORTS\BGXAI_R33_CONSOLE_*.log`, prefer exact SHA; единственный альтернативный 8-event fingerprint допускается только как candidate (байтовый SHA explicitly unverified), ambiguity/missing/symlink fail closed, output read-only JSON. Current-game ITM остаётся live-read через штатный R3, не повторён. R34 тесты Windows/Linux PASS (включая старое имя, новый файл, fingerprint mismatch, ambiguity), stage PS 5.1 и предыдущие menu handlers PASS. Единственный updater опубликован: backend **79 775 байт**, SHA256 `9b44a5cf6ffd83c97c17c49ac9533b102bcdef7a004da4840636762a91cb2db5`, immutable `124add6624c4cfd054b2cee61f37d5af5f093bea`; BOOTSTRAP_PIN указывает туда, CMD не тронут. Прежний R33 **INSTALLED + LIVE 8/8 PASS**. Новое R34 локальное выполнение ожидается. В игре ничего не менялось. Нельзя заявлять autonomous weapon switch / actor-class-verified / exact alternate APR.

После подтверждения release CI, **один следующий шаг**: закрытая игра → обычный `BGXAI_UPDATE.cmd` → **173**, убедиться префикс `124add6624c4`, отправить единственный отчёт `BGXAI_R34_NATIVE_PROF_*.json`. При STOP файл JSON с reason или вывод; не повторять и не переустанавливать R33.

---

## 25.11.2026 — R34 WH ALIAS HOTFIX: REAL MENU STARTUP CI PASS, NEXT 173

ФАКТ пользователя: `BGXAI_UPDATE.cmd` verified pin `38c7d2ee3bfc`, но R34 до меню упал `wh : The term 'wh' is not recognized` на строке 1108. Причина: builder R34 ошибочно преобразовал `Set-Alias wh Write-Host -Scope Script` в рекурсивное `Set-Alias wh wh -Scope Script`. Никакой установки/изменения игры не было.

Исправлено и репиновано: активный BGXAI_SYNC.ps1 79943 байта SHA256 `d131395cc7d3b5b9c265a8684994515eb6b7e72ba69c5ef4422597cc541de877`; immutable commit `b678020a5deee2d1d7205eebd28840847cfbd2a8`. Исправлены stage/builder, обновлён BOOTSTRAP_PIN; исходный CMD неизменён. [R34 CI 45656805908](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45656805908) SUCCESS 3/3 и **реальное выполнение полного backend до отображения меню и пункта 0 на Windows CI fixture**, не только AST. [R33 historical preservation CI 45656991832](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45656991832) SUCCESS.

**СЕЙЧАС:** R33 installed and live raw observer PASS 8/8; R34 source+release PASS, user PC read-only 173 NOT YET RUN. Следующее единственное действие пользователя: обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, проверить префикс `b678020a5dee`, выбрать `173`, переслать один `BGXAI_R34_NATIVE_PROF_*.json` или STOP. Если STOP — не повторять. Не просить R33 install/capture и не заявлять AUTOSWITCH.

---

## 25.11.2026 — R34 RO MENU173 RELEASED, R33 LIVE 8/8, AUTOSWITCH HOLD

**НЕ повторять готовое:** проверенные user install R33 (`BGXAI_R33_INSTALL_20261125T155703049710Z.json`), live capture R33 (`BGXAI_R33_CONSOLE_20261125T161358491052Z.log`, SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`), 8/8 observer samples, 46 WPROF values, BOW05 shot, штраф владения −2. R33 active/passive; R33 weaponSwitchAuthorized=false. Содержимое старых разделов «R33 не установлен» устарело.

**НОВОЕ:** R34 read-only join `BGXAI/BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125/`. Реализован новый безопасный read-only парсер-связка (не второй парсер ITM): reuse pinned native R3, current game KEY/BIFF/override, сопоставление ITM 0x31 proficiencyId с R33 46 stat 89..134 (lower 3 bits). Не рассчитывает фальшивый APR других слотов, не считает навыки доступностью предмета и не даёт переключений без подтверждённого action origin. Source CI Windows+Linux, onefile pinned Stage CI, PS 5.1 ABI and active CI **PASS**. Backend `BGXAI/BGXAI_SYNC.ps1` 79935 SHA256 `c900e8aa6c4ec92bcb80cac1624cf1d6caa477dc961dd137555508e14e9d1f78`, immutable commit `38c7d2ee3bfc7a50631bb3375e5c1ee2141c0d7d`; manifest pin updated. 172 old handlers byte-identical; old CMD unaffected.

**ЕДИНСТВЕННЫЙ СЛЕДУЮЩИЙ ШАГ:** в закрытой игре обычный `BGXAI_UPDATE.cmd` → **173**, получить `Documents\BGXAI_LIVE_REPORTS\BGXAI_R34_NATIVE_PROF_*.json`. Прислать один файл. Если STOP — прислать точный вывод, ни повторных запусков, ни installs, ни rollback. В R34 CODE+CI+RELEASE PASS, user PC runtime **PENDING**. После этого использовать доказанные реальные ITM prof ID и единый V5 pipeline для дальнейшего weapon selection; не включать активную смену до proven manual/EPS origin + full active effects + alternative effective APR. [R34 README](../BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125/README_RU.md).

---

## 25.11.2026 — R33 меню 172 безопасно опубликовано, CODE/CI PASS, DEPLOY/LIVE NO

**Фактическое положение:** R31 установлен и подтверждён в реальной игре (12 событий 12 стабильных очередей, ноль непустых; `actionRaw=3` во время атаки Халида, поэтому `queuedActionsRaw=0` НЕ безопасный рубеж). **R33 ЕЩЁ НЕ УСТАНОВЛЕН**: только опубликован защищённый upgrade R31→R33 в прежнем `BGXAI_UPDATE.cmd`, меню **172**. Релиз пассивный: сырые level1/2/3, kit, 46 WPROF-полей 89..134 и raw AI-class, никакой автоматической смены оружия. Обобщённый Weapon Priority V5/V4/V3 по альтернативным слотам не закончен.

**Точная инфраструктура:** `BGXAI/BGXAI_SYNC.ps1` 79 874 байта SHA256 `4f04b43f69d4171e2686f017d334eac69f91d9389a18122110c2bfd44a2d5663`, immutable git commit `f383ad5ca3515f6fc166ca1a2337a88f9d2cad49`; `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён, сам CMD не менялся, старые пункты 1–171 byte-for-byte сохранены. `R33_GUARDED_SOURCE_ONLY.py` 22 132 байта SHA256 `0815d173b276c0f990eb3ab66ac6f8f614a9a0f0f59fc301f94f5f8c890be653`; `M_BGXR27_R33_SOURCE_ONLY.lua` 49 438 байт SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`.

**CODE/TEST/CI/RELEASE PASS:** [5/5 R33 CI 45647273764](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45647273764) зелёный: pinned SHA + Python guards Windows/Linux, PowerShell 5.1 AST, настоящий WeiDU v251 `--parse-check TP2` Windows/Linux, настоящий Lua-мок 5.3/5.4/LuaJIT, guarded install/rollback/capture mock. Это НЕ игровая установка и НЕ LIVE тест R33. [Структурированный релизный вердикт](../BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/R33_RELEASE_VERDICT_20261125.json).

**Единственный следующий пользовательский шаг без повторных RO-тестов:** закрыть игру и InfinityLoader, открыть обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **172** → **2 (install)**. Установщик САМ выполнит read-only preflight R31 last 151, SHA всех нужных файлов, создаст внешний backup, затем спросит буквальное `INSTALL_BGXAI_R33_PASSIVE_PROF_AFTER_R31` (другое/ENTER = отмена). Прислать ОДИН файл `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R33_INSTALL_*.json` или STOP. При STOP ни повторять, ни откатывать самостоятельно. Далее после проверки результата один runtime capture 172→5, а не новое повторение старого R31.

**Не затронуто:** EET/WeiDU реального ПК, R31, EPS 18.4, R29/V6/working guard-heal-AOE, BG_EET_RU, BG Voice RU, сохранения. **Остаточный CI-долг:** часть старых исторических проверок жёстко ожидает предыдущий активный SHA или 170/171 пункт меню и остаётся красной. Новая независимая R33 release CI полностью зелёная; не объявлять остальные ошибки исправленными, их надо адресно адаптировать к historical-pin модели, не скрывая реальные сбои.

---


## 25.11.2026 — R33: реиспользование 46 профилей R31, проверено CI; установка NO

**Фактический результат:** [R33 SOURCE ONLY](../BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/README_RU.md). Доказано на точном исходнике R31 SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`, что R31/R4 **уже считывает** `m_nLevel1..3`, `m_nKit` и 46 полей proficiency 89..134. Они ранее намеренно не сериализовались в Console JSON. R33 не создаёт вторую точку сбора, а дополняет текущий `R27_SINGLE_CALLBACK` сырой структурой `levelsAndKitRaw`, массивом 46 `proficiencyStat89to134Raw`, необязательным `aiObjectClassRawCandidate` и fail-closed flags.

**Точные safety-ограничения:** значения из `m_typeAI.m_Class` — только кандидат, не доказанный `CLSWPBON` class row и не подтверждение active dual/multiclass/kit. 46 профилей — raw, **не** автоматически «звёздочки» и не доказательство привязки к конкретному ITM/ability. `classRowVerified=false`, `weaponToProficiencyVerified=false`, `activeDualMultiClassVerified=false`, `actorPipsVerified=false`. `queuedActionsRaw=0` в действующей атаке Халида НЕ разрешает dispatch. Другие слоты final APR/THAC0/effects НЕ проверены. V6/R29, healer/AoE/bug-fixes остаются как были.

**CODE / TEST:** R33 builder SHA-pinned source-only, выход 49 438 байт SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`. [GitHub Actions 45645196992](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45645196992) **SUCCESS** — Windows + Ubuntu Python unit и Lua 5.3/5.4/LuaJIT runtime mock; same one listener, no orders, HOLD при изменении prof/class. Прошлые CI error Windows LF и тестовый захват EEex-ссылки в callback исправлены, **реальная игровая сборка не менялась**.

**Критический статус:** `R31 LIVE PASSIVE=PASS`, `R32 SOURCE CI=PASS, LIVE NO`, `R33 SOURCE CI=PASS, DEPLOY NO, LIVE NO`, `WEAPON PRIORITY GENERAL LIVE=NO`. Не запускать существующий пункт меню 171→2 повторно (он устанавливает прежний R31, не R33). Следующий оформленный шаг — безопасный R31→R33 upgrade как последний WeiDU-компонент с отдельным буквальным подтверждением и единственным обновлятором (не готов), затем один runtime capture; только после этого — class/weapon/proficiency bind и effective APR альтернативных слотов. Никаких дополнительных тестов сейчас от пользователя не требовать.

---


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
