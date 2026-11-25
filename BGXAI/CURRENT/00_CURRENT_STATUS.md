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

# BGXAI CURRENT 26.11.2026 — comprehensive source regression 7/7 PASS, 4 828 checks

**REQUEST:** user asked for a complex test. Implemented [full cross-platform READ ONLY workflow](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/.github/workflows/bgxai-comprehensive-readonly-20261126.yml); final real GitHub CI [run 45667708256](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45667708256) **SUCCESS 7/7 jobs** (Linux Lua5.3/5.4/LuaJIT; R27–R35 Python on Linux and Windows; BGXP3/4/5, AoE/BGX120, friendly, ranged V5–V7 both OS; actual PowerShell5.1 AST + choice-0 smoke on dummy Windows fixture; summary). **4 828 PASS observed tests/assertions; 4 SKIP across OS** (private real R28 effect-gate report absent from CI; R31 Python's optional Lua runtime check absent in Python runner, Lua tested separately on three runtimes). First run failed from test-only Read-Host stub quoting; fixed stub and ALL suites rerun green. No actual installed EET touched. Original one user CMD, immutable 173-menu pin, old 172 handlers unchanged. Real user R28/R34 inputs separately rechecked locally: 24/24 observed historical selected-action seq, 4/4 original/current overlapping ITM exact SHA + origin + prof IDs, 22 ammo-slot APR2 vs 2 sword-slot APR1.5; **not synchronous effective other-slot APR**. Downloadable standalone JSON generated; original private logs never committed to repo.

**Canonical complete report:** [BGXAI_COMPREHENSIVE_REGRESSION_20261126_RU.md](https://github.com/jeleZa112/nwn-xanos-updates/blob/bg-eet-ai/BGXAI/CURRENT/BGXAI_COMPREHENSIVE_REGRESSION_20261126_RU.md). NEXT P0 unchanged: real safe selected-only APR/THAC0 with effects fingerprint and manual/EPS action provenance in existing single R33 callback, only after typed approval. R35 source-only/CI PASS, game switch **NOT INSTALLED**, do not claim gameplay LIVE.

---

# BGXAI CURRENT 26.11.2026 — R35 selected APR+raw THAC0 passive EEex source + all CI PASS

**NEW CODE:** `BUILD/R35_NATURAL_SELECTED_APR_RO_20261126/BGXAI_R35_SELECTED_ENGINE_STATS_RO.lua` provides pure read-only `M.observe(sprite,statsReader)` and `M.compare(first,second)`. Intended to reuse already installed R33 callback; no new EEex listener, scripts, WeiDU, game writes, orders or weapon switch. `EEex_Sprite_GetActiveStats` source-verified and guarded against `m_bAllowEffectListCall==0` temporary work-in-progress stats; synchronous double-read selected slot/ability, raw `m_nNumberOfAttacks` and raw `m_nTHAC0`. Actual output is **selected-only** APR/THAC0 observation; it does **not** authenticate final other-slot APR, launcher binding, target hit probability, active class/dual, all buffs, origin of EPS/manual action or a safe switch. Compare can witness naturally different selected slots but retains `otherSlotEffectiveAPRVerified=false`, `matchedBuffContextVerified=false`, `weaponSwitchAuthorized=false`.

**TEST:** 16 source-only Lua regression tests across **Lua 5.3 + Lua 5.4 + LuaJIT** (48 invocations) plus original **13 Python regressions on Windows and Ubuntu** and static no-action/mutation checks. [R35 CI all 3 jobs PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45666482574); R34 source regression with R35 test [PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45665910474). **DEPLOY/LIVE:** no R35 installation; R33 in-game unchanged, R34 live read-only PASS. No user operation needed now.

**NEXT:** establish separately authenticated same-time effects/equipment/fingerprints + natural selected engine snapshots, link ammo to launcher and manual/EPS action ownership, then existing V3/V4/V5+NONINTERRUPT. Any active switching requires later typed install approval. Don't repeat R27/R33/R34/battles/old bow-sword pilot.

---

# BGXAI CURRENT 26.11.2026 — R35 real R27/R34 selected APR witness, source/CI PASS, no new game deployment

**User instruction "+" after R34 5/5 PASS** followed; no new user questions and no repetitions of 173/R33/game battle. R35 now exists at `BGXAI/BUILD/R35_NATURAL_SELECTED_APR_RO_20261126/` with `BGXAI_R35_NATURAL_SELECTED_APR_RO.py`, 13 regression tests, README and CI. New source-only analytical bridge for historic engine-selected APR observations; **NOT a new weapon selector / new installer / live game module**.

**REAL USER INPUTS RE-INSPECTED**: `BGXAI_R28_NATIVE_FROM_R27_20261123T173010478057Z.json` (24 natural selected events, one actor, exactly 1 session, consistent seq, source SHA256 `6124a7d4d1fd3e168bc7fa099397964fb2e0bc4d5d0fa840c79c005647bf223b`) and `BGXAI_R34_NATIVE_PROF_20261126T002126164.json` (5 actual CURRENT_GAME item ITMs, prior R33 historical profile). Four R28 and R34 native ITM SHA+origin+proficiency IDs match exactly: `AROW01`, `BOW05`, `STAF01`, `SW1H04`. 22 observations: raw selected slot **12** (AMMO) / raw APR key **2** = **2 APR**; 2 observations: raw selected slot **35** (SW1H04) / APR key **7** = **1.5 APR** (decoder from R33). Critical: slot 12 is **arrow**, not authenticated current launcher BOW05, and 22+2 R27 samples do **not** share verified buff/effect/target fingerprints. No reliable counterfactual other-slot APR/THAC0, no effective damage/THAC0, no safe switch time. Historical shortbow 0 pips and long sword 2 pips cannot alone outweigh unknown special APR effects (BOW05 opcode1). **Both gameModified and ordersSent remain false/0.**

**TEST:** [R35 13 unit tests on Windows and Ubuntu and no-game-write denylist 2/2 jobs SUCCESS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45665814622); [existing R34 test workflow amended to check R35 as well; cross-platform PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45665910474). Historical R33, R34 and one `BGXAI_UPDATE.cmd` remain unchanged; no additional game code installed.

**EEex API RESEARCH (source-verified):** official `EEex/copy/EEex_scripts/EEex_Sprite.lua` documents `EEex_Sprite_GetActiveStats`: returns `m_derivedStats` or `m_tempStats` if `m_bAllowEffectListCall==0`; `EEex_Sprite_GetStat` reads same active context. These do not directly yield *other unselected slot* effective APR/THAC0. A robust next P0 is an independent passive observer integrated into the **existing** EEex callback (not another listener), correlating naturally selected slots with audited same-time active effect fingerprint, item identity and launcher/ammo; do not force a switch to sample hypotheticals. Continue V3/V4/V5 + NONINTERRUPT guarded design, no active dispatch until manual/EPS ownership + safe attack boundary proven and typed install approval.

---

# BGXAI CURRENT 26.11.2026 — R34 REAL USER PASS; next task per-slot APR/THAC0/action-origin

**New authoritative user result:** the actual user-supplied R34 JSON `BGXAI_R34_NATIVE_PROF_20261126T002126164.json` (7,404 bytes, SHA256 `aab2fdf801627b1bb165dd5435644da0b50967f9269e351e58bec4deecc81c10`) was inspected. `schema=BGXAI_R34_R33_NATIVE_ITM_PROF_JOIN_RO_V1`, `status=HISTORICAL_R33_PROFILE_CURRENT_ITM_JOINED_RO_NO_SWITCH`, `liveGamePinVerified=true`, `nativeResourceCount=5`, `gameModified=false`, `ordersSent=0`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`. **R34 read-only link on real user's installed EET is PASS; no repeat 173.** Previously documented R34 log failures are historical, already resolved by the archived R33 fallback; do not use old "R34 pending" as the current next instruction.

**Real current-game item evidence** (IDs and SHA only, no user paths):
- `BOW05` source `CURRENT_GAME_BIFF`, SHA256 `0bfc6680b759239052dcd1882a1d2f354e7bc840e535f0b9499a5c7a3c07d797`, `proficiencyStatIdRaw=105` (SHORT_BOW); historical R33 raw stat 105 is 0 pips.
- `SW1H04` source `CURRENT_GAME_OVERRIDE`, SHA256 `73e3de6a07afc42f50d63b74c3235c1f9efdd773e280c501b481e876647eda88`, statID 90 LONG_SWORD, historical rank 2.
- `STAF01` source `CURRENT_GAME_OVERRIDE`, SHA256 `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`, statID 102 QUARTERSTAFF, historical rank 0.
- `AROW01` source `CURRENT_GAME_BIFF`, SHA256 `52209dceddf99fec75e20a694b42906fa3f9ea74c6cacad5d62d33eff22f9d91`, proficiency ID 0 is unclassified rather than zero pips, launcher requirement raw 1.
- `SHLD03A` source `CURRENT_GAME_BIFF`, SHA256 `f24085edd8bf24f79b9b09302bb719f5203d9fa175dbf352f94253ff2a48b7f1`; raw proficiency 0 unclassified; not previously in R28 report.

**Independent cross-date source comparison:** R34 SHA for `AROW01`, `BOW05`, `STAF01`, `SW1H04` exactly match the four previously real-native-read ITM in R28 (23.11.2026). R33 historic Khalid stat 104 LONG_BOW was 1 pip and stat 105 SHORT_BOW was 0; this matters because BOW05 is SHORT_BOW. It is *not* proof of current 26.11 actor pips/equipment, or that longbow is better: BOW05 has item opcode 1 (fixed APR behavior) and ammo/target effectiveness must be compared under full active buffs.

**Critical evidence boundaries:** `historicalProfileOnly=true`, `sameBytesAsUserUploadedLogVerified=false`, `localLogBytesAuthenticated=false`, `sameSessionItemResourcesVerified=false`, `sessionTemporalAlignmentVerified=false`. The R34 property `noProficiencyInLiveActor` refers to a historic R33 profile and must **NOT** be restated as verified live actor stats. `manualAndEPSOriginVerified=false`, `alternateEffectiveAPRVerified=false`, `allBuffsAndEffectsVerified=false`, `actorClassRowVerified=false`, `ammoLauncherEngineBindingVerified=false`, `safeDispatchTimeVerified=false`, `actionOwnershipStatus=ACTION_SOURCE_POINTER_UNAVAILABLE`. No scorer/executor deployment or new autonomous weapon switch is authorized.

**Next real P0, no new 173/R33 and no repeat of V6/R29 bow-to-sword pilot:** investigate exact alternate-slot effective APR/THAC0/buff+item effect capture using proven EEex APIs without switching or actions, verify class/dual and actual ammo-launcher binding, prove manual/EPS origin and safe action boundary, then integrate existing V3/V4/V5 + NONINTERRUPT. Before issuing any order: independent user typed approval, SHA preflight, external backup, WeiDU last-only rollback, A/B LIVE. Preserve EPS18.4, BGXP5, BGX120, guard, all saves, translation and voice projects. One user-facing `BGXAI_UPDATE.cmd`.

---

# 26.11.2026 — BGXAI R34: confirmed user HOLD, historical R33 fallback released (CI PASS)

**LATEST USER EVIDENCE:** unchanged onefile `BGXAI_UPDATE.cmd` loaded immutable `124add6624c4` (SHA256 OK). User selected 173 and got `R34_HOLD: R34_R33_NAMED_LOG_DIFFERS_AND_FAILS_FINGERPRINT`, report `BGXAI_R34_NATIVE_PROF_20261126T000637588.json`. No game writes, no orders, no auto weapon switch. **Do not ask for another R33 capture, replay battle, R33 install, or immediate repeat of 173.** The failing local log was not independently inspected, so its actual difference must not be guessed.

**Already-existing authentic evidence cross-checked on 26.11:** user-uploaded R33 console file (SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`) contains one R33 session and 8 consistent selected-action snapshots, proficiency stat 90 (long sword)=2, stat 92 (axe)=1, stat 104 (longbow)=1, stat 105 (shortbow)=0, same loadout `SW1H04`, `BOW05`, `STAF01`, `AROW01`, `SHLD03A`. Independently received real-game R28 native ITM report dated 23.11 has `BOW05.proficiencyIdRaw=105` (SHORT_BOW), `SW1H04=90`, `STAF01=102`, `AROW01=0`. **Functional finding: historical equipped BOW05 is a shortbow with zero relevant pips, notwithstanding one longbow pip.** This is an archived cross-date comparison, not proof that equipped ITM bytes are unchanged on 26.11. Shield ITM was not in the old R28 set.

**SOURCE CODE CHANGE:** existing `BGXAI/BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125/BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py` now accepts a single bounded historical aggregate only if local R33 log is missing or rejected for the exact known cases. Exact real-log parse still has priority. Archive input is strictly compared to independently transcribed R33 historical fields, ships no private full log or actor identifier, and is labelled `HISTORICAL_R33_PROFILE_CURRENT_ITM_JOINED_RO_NO_SWITCH`. It explicitly records `sameBytesAsUserUploadedLogVerified=false`, `localLogBytesAuthenticated=false`, `historicalProfileOnly=true`, `sessionTemporalAlignmentVerified=false`; live R33 installation pin and real-game ITM file reads remain required. Ambiguous multiple logs, unsafe paths and arbitrary archive data cannot silently become a live verified snapshot. No new EEex listener, BCS, WeiDU or commands.

**RELEASE COMPLETE (SOURCE/CI ONLY):** source regression tests include archived join and tamper-negative checks; source Windows/Linux CI PASS on source commits. New onefile SHA-pinned backend is still exactly 79,775 bytes, old menu 1..172 unchanged, original CMD unchanged, **new immutable source ref** `1404112c2889561b99416e48a4ba06ab947c4fee`, `BGXAI_SYNC.ps1` SHA256 `9131e29da59b7d3a62651eab3ff7deee514da426cfbe6a1267b54444e9c6f59a`, R34 module SHA256 `d40f7729ee84c576d08fe712b98adcd0704611def6385e976a50597b68c496c4`. `BOOTSTRAP_PIN.json` now points to this immutable commit. **FINAL CI CONFIRMED PASS:** R34 source Windows/Linux 24 tests and [active onefile release 3/3 Windows/Linux+PowerShell 5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096145) SUCCESS; [R33 historical 5/5](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096366) SUCCESS, including Windows/Linux native WeiDU TP2 checks. This is RELEASE/CODE/CI only, not user-PC R34 LIVE. Historical R33 installed+LIVE 8/8 remains. R34 current ITM read has not yet succeeded on user's Windows. All switched orders disabled.

**PRIORITY AFTER RELEASE CI:** user must not redo 173 merely to debug local log. Only if a fresh current-game ITEM snapshot is indispensable, one 173 run under the new SHA may read current ITM with archived R33 provenance. Otherwise use already obtained R28/R33 facts and continue P0: dynamic alternative-slot APR/THAC0/effects, verified ammo/launcher, manual/EPS queue origin and safe non-interrupt boundary; integrate existing V3/V4/V5, no new bow-to-sword pilot.

---

# BGXAI — короткий актуальный статус на 25.11.2026

**CI FINAL 25.11.2026:** R34 source-only 22/22 Windows/Linux PASS (run 45660217453); R34 79775B active pin + real PS5.1 menu boot 3/3 PASS (run 45660513142); historical R33 source/proof/WeiDU 5/5 PASS (run 45660551436). Exact user live R34 after hotfix still PENDING. No game writes.

## 25.11.2026 — R34 AUTO LOG MATCH hotfix RELEASED, no repeated R33 capture

**Последний фактический пользовательский STOP:** единственный BGXAI_UPDATE.cmd успешно загрузил pinned `b678020a5dee` (SHA256 OK), меню 173 запустилось, но до чтения ITM получен `BGXAI STOP: R34 LIVE LOG PIN STOP`. Проверено не предположением: ПРИСЛАННЫЙ РЕАЛЬНЫЙ `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` имеет SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`, размер 101981 Б, 1 SESSION, 8/8 events. Зашитый SHA был ПРАВИЛЬНЫМ. Поскольку старая команда 173 применяла `HashFile` к *одному точному пути* и бросала один и тот же STOP для отсутствия файла и несовпадения байтов, по этой строке нельзя доказать, что именно произошло на ПК пользователя. Никакой модификации игры при STOP не было.

**Исправлен первопричинный дефект проверки без отключения защиты:** в `BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py` введён `choose_r33_log`, ограниченно перечисляющий только `Documents\BGXAI_LIVE_REPORTS\BGXAI_R33_CONSOLE_*.log`, без рекурсии; предпочитает ТОЧНЫЙ SHA присланного файла, иначе допускает только ОДИН структурно валидный журнал (1 R33 session + 8 seq событий, ожидаемые параметры экипировки/профиля Халида) с `sameBytesAsUserUploadedLogVerified=false` и пометкой `STRUCTURAL_R33_FINGERPRINT_ONLY_DIFFERENT_SHA`. Некорректные/неоднозначные журналы -> явный адресный HOLD; symlink/junction rejected. Если журналов нет: `R34_R33_LOG_MISSING_IN_REPORTS_NO_RECAPTURE`, не «подменять» и не требовать нового боя. Старый handler пункт 173 не прекращает выполнение из-за жёсткой сверки имени/бинарного SHA до входа Python. **Не** повышать структурный fingerprint до полной идентичности байтов/события движка.

**РЕЛИЗ ОПУБЛИКОВАН, LIVE на ПК ещё не проверен:** immutable backend git commit `124add6624c4cfd054b2cee61f37d5af5f093bea`, `BGXAI/BGXAI_SYNC.ps1` **79775 Б** SHA256 `9b44a5cf6ffd83c97c17c49ac9533b102bcdef7a004da4840636762a91cb2db5`. `BOOTSTRAP_PIN.json` установлен на этот commit, сам `BGXAI_UPDATE.cmd` не менялся; меню 1..172 неизменны. Пункт 173 остается **READ ONLY**. R34 Python cross-platform source 22/22 tests PASS (Windows/Linux); stage CI 3/3 PASS; [R34 ACTIVE release CI 45660513142](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45660513142) PASS 3/3 и [R33 historical CI 45660551436](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45660551436) PASS 5/5. Никаких операций WeiDU/Lua/BCS/сейвы/EPS/BG Voice RU/BG_EET_RU. Реальный R33 INSTALL/LIVE **PASS** и не повторяется. `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` остаётся HOLD, auto weapon switch OFF.

**Следующий пользовательский шаг только после CI PASS:** закрыть игру и InfinityLoader, запустить прежний `BGXAI_UPDATE.cmd`, проверить `verified pinned script 124add6624c4 (SHA256 OK)`, выбрать `173` и передать ровно один `BGXAI_R34_NATIVE_PROF_*.json` (при STOP — текст и сохранённый JSON). Ни нового capture, ни reinstall.

---


## 25.11.2026 — R34 menu173 стартовое падение wh: ИСПРАВЛЕНО

**Факт пользователя:** `BGXAI_UPDATE.cmd` получил старый pinned `38c7d2ee3bfc (SHA256 OK)`, но до меню упал на строке `wh ''` (`CommandNotFoundException`). Ошибка в предыдущем R34-компрессоре: `Set-Alias wh wh -Scope Script` (самоссылка), вместо `Set-Alias wh Write-Host -Scope Script`. Это не ошибка игры/WeiDU/R33; установка/удаление/перезапись игры на этом шаге не запускались.

**Исправлено:** активный `BGXAI/BGXAI_SYNC.ps1` **79 943 B**, SHA256 `d131395cc7d3b5b9c265a8684994515eb6b7e72ba69c5ef4422597cc541de877`, immutable Git commit `b678020a5deee2d1d7205eebd28840847cfbd2a8`, manifest `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён. `BGXAI_UPDATE.cmd` без изменений, все handlers 1..172 побайтово сохранены. Исправлен builder `build_r34_onefile_menu173_source_only.py` и стадийный источник. Меню 173 остаётся READ ONLY. **Решена именно причина сбоя перед меню.**

**Тесты после исправления:** [GitHub Actions R34 45656805908](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45656805908) **SUCCESS 3/3**: Windows/Linux SHA/immutable pin + 172 старых обработчика; PowerShell 5.1 AST; **действительный запуск полного скрипта PowerShell до отображения меню и выбора 0 на отдельной тестовой папке `C:\Games\BG_EET_FOXX_NEW` на Windows runner**, без изменения живой игры и сети. Это устраняет дефект старой проверки только синтаксиса.

**Следующий шаг:** один штатный запуск прежнего `BGXAI_UPDATE.cmd` с `verified pinned script b678020a5dee (SHA256 OK)`, выбор **173** и один `BGXAI_R34_NATIVE_PROF_*.json` из `Documents\BGXAI_LIVE_REPORTS`. При STOP повторных попыток не делать, переслать текст. **Не повторять R33 install/capture.** R33 INSTALLED+LIVE 8/8 PASS, R34 REAL CURRENT ITM runtime PENDING, AUTOSWITCH OFF.

---


## 25.11.2026 — R34 RELEASED in existing ONE CMD, menu173 READ ONLY

**Актуальный статус:** R33 **INSTALLED+LIVE PASS 8/8** (см. ниже), R34 **CODE/CI PASS + ONEFILE MENU173 PUBLISHED**, **R34 RUN ON USER PC = PENDING**, **AUTONOMOUS WEAPON SWITCH OFF**. В одном `BGXAI_UPDATE.cmd` появился **173** (только READ ONLY): сверяет SHA уже полученного `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` с 8 реальными R33 событиями, проверяет live R33 proof/Lua SHA, через **существующий** R3 KEY/BIFF/ITM парсер читает актуальные предметы из игры, сопоставляет `ITM.proficiencyIdRaw` (offset 0x31) с низшими 3 битами `proficiencyStat89to134Raw`. Выводит JSON `Documents\BGXAI_LIVE_REPORTS\BGXAI_R34_NATIVE_PROF_*.json`. Не меняет игру/WeiDU/BCS/Lua/EPS, не создаёт нового слушателя и не делает переключений.

**Одна последующая проверка:** при закрытой игре открыть существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **173**, прислать один `BGXAI_R34_NATIVE_PROF_*.json` или STOP. **НЕ** повторять R33 install/capture или R27/R28/R3 старые меню.

**RELEASE PROOF:** active backend 79 935 байт (лимит 80 000), SHA256 `c900e8aa6c4ec92bcb80cac1624cf1d6caa477dc961dd137555508e14e9d1f78`; immutable Git commit `38c7d2ee3bfc7a50631bb3375e5c1ee2141c0d7d`, BOOTSTRAP_PIN обновлён, исходный BGXAI_UPDATE.cmd прежний, 172 старых меню побайтово совпали. R34 source/CI Linux+Windows PASS, onefile stage+active PowerShell 5.1 AST/параметры PASS: [R34 active CI 45654676537](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45654676537). [R34 README+sources](../BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125/README_RU.md). Только простое сравнение доступных ITM и навыков; альтернативный эффективный APR, полнота бафов, активный класс дуала, происхождение команд и безопасный момент переключения остаются HOLD.

---


## 25.11.2026 — R33 LIVE RAW 8/8 PASS; WEAPON SWITCH HOLD

**НОВЫЙ ФАКТИЧЕСКИЙ СТАТУС (перекрывает устаревшее «R33 не установлен» ниже):** R33 **INSTALLED PASS / LIVE RAW OBSERVER PASS**. Реальный пользовательский файл `BGXAI_R33_INSTALL_20261125T155703049710Z.json` подтверждает `R33_PASSIVE_INSTALLED_AWAITING_RUNTIME` и внешний backup `C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXR33_crzl0r2l`. Реальный LIVE `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`: сессия R33 ровно одна, 8/8 стабильных sample seq=1..8, обработчик same invocation, 46 raw WPROF значений 89..134, 0 engine orders, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`. Случай `actionRaw=3` реально записан.

**Данные Халида:** raw профили: longsword=2, axe=1, longbow=1, shortbow=0. Быстрые слоты `SW1H04` (long sword), `BOW05` (shortbow в стандартном BGEE), `STAF01`, выбран `AROW01`; количество стрел 20→19. Фактический бой: бросок 14, попадание, 4 damage, больной гибберлинг убит; журнал подтверждает штраф за владение `-2` при выстреле из `BOW05`. Сведения об именах ванильных предметов требуют сверки с реальными EET ITM, если будет алгоритм выбора.

**Нельзя разблокировать переключения:** `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` **8/8**, нулевая очередь при `actionRaw=3` не подтверждает безопасный dispatch. Значение APR `2` — **сырой engine key**, НЕ итоговая скорость других слотов. `classRowVerified=false`, `actorPipsVerified=false`, `alternateEffectiveAPRVerified=false`. R33 — пассивный. **Не повторять R33 install и LIVE capture.**

**Следующий CODE-only шаг:** read actual local modded ITM data for ability/group→proficiency, weapon eligibility, alternative effective APR (buffs and launcher+ammo), determine safe current action provenance before any switch. Preserve EPS, V6/R29, healing/AoE, BG_EET_RU, BG Voice RU. В этом логе отдельно присутствует `Error loading menu: ']' expected near 'icon'` — не приписывать его BGXAI без доказательств. [Полный зафиксированный LIVE вердикт](BGXAI_R33_LIVE_VERDICT_20261125.md).

---


## 25.11.2026 — R33 ONE-CMD MENU 172 РЕЛИЗ ГОТОВ, ИГРА ПОКА R31

**Фактическое положение:** R31 установлен и подтверждён в реальной игре (12 событий 12 стабильных очередей, ноль непустых; `actionRaw=3` во время атаки Халида, поэтому `queuedActionsRaw=0` НЕ безопасный рубеж). **R33 ЕЩЁ НЕ УСТАНОВЛЕН**: только опубликован защищённый upgrade R31→R33 в прежнем `BGXAI_UPDATE.cmd`, меню **172**. Релиз пассивный: сырые level1/2/3, kit, 46 WPROF-полей 89..134 и raw AI-class, никакой автоматической смены оружия. Обобщённый Weapon Priority V5/V4/V3 по альтернативным слотам не закончен.

**Точная инфраструктура:** `BGXAI/BGXAI_SYNC.ps1` 79 874 байта SHA256 `4f04b43f69d4171e2686f017d334eac69f91d9389a18122110c2bfd44a2d5663`, immutable git commit `f383ad5ca3515f6fc166ca1a2337a88f9d2cad49`; `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён, сам CMD не менялся, старые пункты 1–171 byte-for-byte сохранены. `R33_GUARDED_SOURCE_ONLY.py` 22 132 байта SHA256 `0815d173b276c0f990eb3ab66ac6f8f614a9a0f0f59fc301f94f5f8c890be653`; `M_BGXR27_R33_SOURCE_ONLY.lua` 49 438 байт SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`.

**CODE/TEST/CI/RELEASE PASS:** [5/5 R33 CI 45647273764](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45647273764) зелёный: pinned SHA + Python guards Windows/Linux, PowerShell 5.1 AST, настоящий WeiDU v251 `--parse-check TP2` Windows/Linux, настоящий Lua-мок 5.3/5.4/LuaJIT, guarded install/rollback/capture mock. Это НЕ игровая установка и НЕ LIVE тест R33. [Структурированный релизный вердикт](../BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/R33_RELEASE_VERDICT_20261125.json).

**Единственный следующий пользовательский шаг без повторных RO-тестов:** закрыть игру и InfinityLoader, открыть обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **172** → **2 (install)**. Установщик САМ выполнит read-only preflight R31 last 151, SHA всех нужных файлов, создаст внешний backup, затем спросит буквальное `INSTALL_BGXAI_R33_PASSIVE_PROF_AFTER_R31` (другое/ENTER = отмена). Прислать ОДИН файл `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R33_INSTALL_*.json` или STOP. При STOP ни повторять, ни откатывать самостоятельно. Далее после проверки результата один runtime capture 172→5, а не новое повторение старого R31.

**Не затронуто:** EET/WeiDU реального ПК, R31, EPS 18.4, R29/V6/working guard-heal-AOE, BG_EET_RU, BG Voice RU, сохранения. **Остаточный CI-долг:** часть старых исторических проверок жёстко ожидает предыдущий активный SHA или 170/171 пункт меню и остаётся красной. Новая независимая R33 release CI полностью зелёная; не объявлять остальные ошибки исправленными, их надо адресно адаптировать к historical-pin модели, не скрывая реальные сбои.

---


## 25.11.2026 — R33 использует R31/R4 raw proficiency, CI PASS, DEPLOY NO

**Фактический результат:** [R33 SOURCE ONLY](../BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/README_RU.md). Доказано на точном исходнике R31 SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`, что R31/R4 **уже считывает** `m_nLevel1..3`, `m_nKit` и 46 полей proficiency 89..134. Они ранее намеренно не сериализовались в Console JSON. R33 не создаёт вторую точку сбора, а дополняет текущий `R27_SINGLE_CALLBACK` сырой структурой `levelsAndKitRaw`, массивом 46 `proficiencyStat89to134Raw`, необязательным `aiObjectClassRawCandidate` и fail-closed flags.

**Точные safety-ограничения:** значения из `m_typeAI.m_Class` — только кандидат, не доказанный `CLSWPBON` class row и не подтверждение active dual/multiclass/kit. 46 профилей — raw, **не** автоматически «звёздочки» и не доказательство привязки к конкретному ITM/ability. `classRowVerified=false`, `weaponToProficiencyVerified=false`, `activeDualMultiClassVerified=false`, `actorPipsVerified=false`. `queuedActionsRaw=0` в действующей атаке Халида НЕ разрешает dispatch. Другие слоты final APR/THAC0/effects НЕ проверены. V6/R29, healer/AoE/bug-fixes остаются как были.

**CODE / TEST:** R33 builder SHA-pinned source-only, выход 49 438 байт SHA256 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069`. [GitHub Actions 45645196992](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45645196992) **SUCCESS** — Windows + Ubuntu Python unit и Lua 5.3/5.4/LuaJIT runtime mock; same one listener, no orders, HOLD при изменении prof/class. Прошлые CI error Windows LF и тестовый захват EEex-ссылки в callback исправлены, **реальная игровая сборка не менялась**.

**Критический статус:** `R31 LIVE PASSIVE=PASS`, `R32 SOURCE CI=PASS, LIVE NO`, `R33 SOURCE CI=PASS, DEPLOY NO, LIVE NO`, `WEAPON PRIORITY GENERAL LIVE=NO`. Не запускать существующий пункт меню 171→2 повторно (он устанавливает прежний R31, не R33). Следующий оформленный шаг — безопасный R31→R33 upgrade как последний WeiDU-компонент с отдельным буквальным подтверждением и единственным обновлятором (не готов), затем один runtime capture; только после этого — class/weapon/proficiency bind и effective APR альтернативных слотов. Никаких дополнительных тестов сейчас от пользователя не требовать.

---


**R32/V5 совместимость — окончательный native CI:** [run 45643810529](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45643810529) **SUCCESS во всех 3 задачах**: Windows Python, Ubuntu Python, Lua 5.3/5.4/LuaJIT. Добавлен cross-module unit: значения WSPATCK для `-3,-2,-1,0,1,2,3` у EEex-ридера R32 совпадают с `BGXAI_WEAPON_APR_PROVENANCE_V5.decode_wspatck`. В новой игре/WeiDU ничего не менялось, R32 остаётся source-only. Данный CI не является LIVE. К следующему этапу переходить от таблиц к **подтверждению текущего класса и weapon-group + альтернативным итоговым APR**; не требовать повторения R31 capture.


## 25.11.2026 — R32 TABLE APR SOURCE CODE + CI PASS, игра не менялась

**Сделана полезная ступень Weapon Priority V5, не второй скорер:** `BGXAI/BUILD/R32_APR_EET_TABLES_RO_20261125/` — READ ONLY code `BGXAI_R32_APR_EET_TABLES_RO.py` + `BGXAI_R32_EEEX_ENGINE_2DA_RO.lua` + 2 файла тестов и README_RU. Вспомогательный Python проверяет формат `WSPATCK.2DA` и `CLSWPBON.2DA` из точных файлов `override` с SHA256; при отсутствии возвращает HOLD и не имитирует BIFF. Lua-путь через официальный EEex `EEex_Resource_Load2DA` читает *через движок* соответствующие C2DArray (пока только SOURCE ONLY, без установки/слушателей).

**Боевая механика:** WSPATCK возвращает только **добавочный** APR (`-1→+0.5`, `1→+1`, `-2→+1.5`), а CLSWPBON.GETS_PROF_APR указывает, имеет ли класс право на proficiency APR. НЕЛЬЗЯ принимать таблицу за финальный APR, складывать повторно с engine final APR или объявлять альтернативный слот готовым без проверенной weapon↔proficiency association, active class/dual/multi, предметов, заклинаний/эффектов и фактической частоты атак альтернативного оружия. Источники: [IESDP WSPATCK](https://burner1024.github.io/iesdp/files/2da/2da_tob/wspatck.htm), [IESDP CLSWPBON](https://burner1024.github.io/iesdp/files/2da/2da_bgee/clswpbon.htm), [EEex_Resource_Load2DA](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/EEex_Resource.lua).

**TEST / CI:** [GitHub workflow 45643546399](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45643546399) = **SUCCESS**, Windows+Linux Python 3.12 и 17 native Lua тестов на Lua5.3/Lua5.4/LuaJIT с синтетическим EEex C2DArray. Никаких реальных данных из пользовательского BIFF ещё не получено и нативный EEex runtime R32 не проверен. CODE/CI PASS; DEPLOY R32 NO; LIVE R32 NO; ALT EFFECTIVE APR NO.

**Не трогали:** пользовательский `BGXAI_UPDATE.cmd`, PIN, WeiDU, R31 R27V3 passive observer, V6/R29, EPS, EET, BG Voice RU, BG_EET_RU и сейвы. Один обновлятор обязателен; старые меню не повторять.

**Следующий приоритет:** источник class/kit + weapon ability ↔ proficiency и runtime final-state каждого **альтернативного** слота, с корректным снимком целевых защит/эффектов и без потери действия. Не посылать команды на основании R31 `queuedActionsRaw=0`. Не назначать пользователю новый тест/установку R32, пока нет полного безопасного live-маршрута и существенного нового поведения.

---


**Regression после реального R31 боя:** в `test_weapon_noninterrupt_plan_v1.lua` добавлен конкретный реальный сценарий `actionRaw=3` + `queuedActionsRaw=0` + `ACTION_SOURCE_POINTER_UNAVAILABLE` → `CONTINUE_CURRENT_ACTION_SWITCH_PENDING` только advisory, `dispatchAuthorized=false`, `ordersSent=0`, `actionQueueCleared=false`, `currentActionPreserved=true`. Offline NONINTERRUPT 26/26; общий runner 443 сценария (ранее 442). **[GitHub CI 45641893884](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45641893884) SUCCESS:** native Lua 5.3/5.4/LuaJIT + Windows static. Никакой установленный Lua/BCS/PIN/WeiDU не менялся. R31 и V6 остаются как были.


## 25.11.2026 — R31 LIVE подтвердил 12/12 событий; безопасность очереди НЕ доказана

**Официальный проверенный вердикт:** [`BGXAI/CURRENT/BGXAI_R31_LIVE_VERDICT_20261125.json`](./BGXAI_R31_LIVE_VERDICT_20261125.json). От пользователя реально получены `BGXAI_R31_CAPTURE_20261125T150437014429Z.json` и `BGXAI_R31_CONSOLE_20261125T150300876807Z.log` (147793 байт, SHA256 `7f2705dde1eaf16e131f5ec1396837f8affaff8b4070292fd945447783c88c9e`). JSON: `status=R31_RUNTIME_RAW_QUEUE_LOG_READY_FOR_REVIEW`, exit 0, session 1, R31 samples 12, stable queue 12, nonempty 0. Источник — пользовательский настоящий gameplay, НЕ CI/mocks.

**Проверка самого лога:** 12/12 строк `BGXR27` `R27_SINGLE_CALLBACK` парсятся; 12/12 same-callback, стабильные данные выбранного оружия, инвентаря и derived stats; 12/12 `queueSnapshotStable=true`, `actionContextSnapshotStable=true`, `queuedActionsRaw=0`; 11 действий `actionRaw=23` и одно `actionRaw=3`. Один зарегистрированный R31 session marker. R31 не выдаёт приказов: `ordersSent=0`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`.

**Боевой факт, не реконструкция:** `Халид` с луком `BOW05` и стрелами `AROW01` действительно атаковал больного гибберлинга, бросок 20 — критический, 6 метательного урона, враг умер. Счётчик `AROW01` изменился 20→19 после actionRaw3. `selectedWeaponRaw=12` во всех 12 снимках, переключения на меч НЕ было и его не требовалось при убийстве одним выстрелом.

**Критическое обнаруженное ограничение:** `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` **12/12** и `actionSourceStable=false` **12/12**. `queueNonemptyObserved=false` везде — непустая очередь вообще НЕ была наблюдаема в этой короткой игре. **Даже когда actionRaw=3/реальный выстрел, `queuedActionsRaw=0` и `actionCountRaw=0`.** Поэтому ноль не доказывает безопасную паузу, отсутсвие ручного приказа или EPS-задачи. `queueBindingLiveVerified=false`, `manualEpsOriginVerified=false`, `alternateEffectiveAPRVerified=false`; никакого автоматического dispatch на основании этих данных.

**Отдельная ранее известная ошибка UI:** `Error loading menu ... ']' expected near 'icon'` есть и в новом логе; её уже видели до R31. Не связывать её с R31 без отдельных данных и не менять BG_EET_RU или UI в BGXAI.

**Статусы:** R31 CODE/CI=PASS, native WeiDU parse=PASS, real preflight=PASS, DEPLOY=PASS, **LIVE PASSIVE OBSERVER=PASS**, LIVE queue/noninterrupt=UNVERIFIED, origin=UNVERIFIED, ALT effective APR/weapon priority=UNVERIFIED. **Старый пункт 171→5 повторять не нужно**. Следующее — разработки SOURCE ONLY алгоритма реального сравнения оружия с APR/THAC0/эффектами и запретом прерываний; только при появлении нового функционала потребуется целевой runtime. Оставить R31 и R29 установленными, текущую игру не менять.

---


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
