# BGXAI — аудит атаки союзника после включения Party AI, 19.11.2026

## Подтвержденное наблюдение
При уроне от Джахейры по Халиду с выключенным Party AI, затем включении Party AI, Халид автоматически атакует Джахейру. На скриншотах видно сообщение «Халид: атакует цель: Джахейра» и HP Халида 4/13. Другая проверка показала автоматическое переключение дальнего и ближнего оружия, но опасную реакцию на союзника. Это реальная игровая регрессия безопасности, а не пройденный тест автономной тактики.

## Аудит установленных модов
Найден ранее загруженный WeiDU(20261119-070635).log: EEex 1.2.0, SCS 35.21, EPS 18.4, модули BGX38/39/56/60/61/66S/TEAM, BGXP2/3/5, BGX120. Время файла раньше последних установок Ranged V1/V2/V3, поэтому он не является точной текущей инвентаризацией.

## Подозреваемые источники
- BGX39 source BGXAI/fox_new/release_039/BGX39/team_guard_fallback.baf: есть ProtectObject(PlayerN,6); сам авторский комментарий указывает, что эта команда может сохраняться без автоматической отмены.
- BGX60 source BGXAI/fox_new/experimental_060_direct_response_source_only/BGX60_RECEIVER.baf: AttackReevaluate(LastAttackerOf(PlayerN),30), но явно стоит !InParty(LastAttackerOf(PlayerN)) и !Allegiance(...,GOODCUTOFF). Поэтому нельзя автоматически объявить 060 причиной.
- BGX61 source BGXAI/fox_new/experimental_061_rescue_approach_source_only/BGX61_RECEIVER.baf: аналогичные фильтры !InParty и !Allegiance. Нельзя автоматически объявить 061 причиной.
- BGXRANGED V3 source BGXRANGED_V3_MELEE_HANDOFF.baf: AttackOneRound(NearestEnemyOf(Myself)) без дополнительного !InParty(target), но эта ветка требует HP > 75%. На скриншоте при 4/13 она не должна активироваться. Источник нападения на Джахейру остаётся неустановленным.
- EPS 18.4 или vanilla engine script LastAttackerOf / stored target остаются гипотезами. В истории EPS есть упоминания ошибочных атак нейтралов; это не доказывает именно текущий случай.
- Party AI OFF→ON может восстановить обработку прежней цели/LastAttacker. Поведение требует проверки фактического BCS и владельца выдаваемого действия.

## Safety acceptance
1. Автоматические атаки не выбирают действующего члена партии даже после дружественного удара, независимо от его видимости, EA и запомненного LastAttacker.
2. С настоящим врагом рядом AI продолжает атаковать только врага.
3. Не применять массовое ClearActions и не удалять рабочие лечение BGXP5, EPS и BGX120.
4. Не устанавливать новые военные блоки, пока не выяснено происхождение агрессии.

## Следующий инженерный шаг
READ ONLY аудит актуального override/BDDEFAI.BCS с нативным WeiDU декомпилятором или доказанным парсером, группировка действий Attack/AttackReevaluate/ProtectObject и их предикатов InParty/Allegiance, учёт порядка блоков и реального WeiDU.log/назначенного персонального AI скрипта Халида. Текущий документ диагностика, не установленный hotfix.


## Реализация read-only проверки 19.11.2026

Добавлен самостоятельный **BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py** в SHA-подписанный release source manifest 0.3.57-BGXAGGRO-READONLY. Существующий BGXAI_UPDATE.cmd использует тот же immutable bootstrap и теперь содержит пункт **135 — Friendly aggro audit (READ ONLY)**. Старые пункты 1–134 и их обработчики сохранены. Сокращены подписи части прежних пунктов меню, потому что у BGXAI_SYNC.ps1 жёсткий предел около 80 КБ.

- Источник: BGXAI/patchsets/ranged_fighter_guarded_20261119/BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py; SHA256 926bc0fafb15617cc11e63587589e92e62fbd75e81d5afb65820799c757a3b85.
- Pinned script commit **39faabe04d74f8bb21c728e5db9435f0d7bca19c**; размер 79847 байт, SHA256 **2b7e9b574ed0071668f3a026acbb9531ae51fcbd28b0026151ad29c9d47855c5**; PIN commit 4119b2a0d9e50e899b7970aec38c6292b5817ec3.
- Проверяет реальную BDDEFAI.BCS: хеш, BCS envelope, блоки, последнюю WeiDU компоненту; копирует BCS и WeiDU во временный каталог, декомпилирует BCS -> BAF **только во временной папке**, сверяет количество блоков; изучает Attack/AttackReevaluate/AttackOneRound/ProtectObject и LastAttacker/NearestEnemy, наличие InParty/Allegiance target guards, записывает JSON в Documents/BGXAI_LIVE_REPORTS (или Documents, если папки нет). Выводит первые 15 наиболее подозрительных блоков + путь полного JSON.
- Это эвристическая разметка, не доказательство исполнившегося блока; пока нельзя автоматически объявить виновника.
- GitHub Windows CI 44525952608 — **SUCCESS**, проверка PowerShell 5.1 AST, канала, SHA и меню 1–135. Исходные тесты парсера/блоков 44525423579 — **SUCCESS**. **На пользовательской EET ещё не запускалось.**
- Следующее действие **одно**: закрыть игру/InfinityLoader, запустить текущий единственный BGXAI_UPDATE.cmd, выбрать 135; прислать текст TOP_SUSPECT_BLOCKS и/или JSON из указанного REPORT_FILE. Не запускать новые установки 132/дружественный боевой тест. По отчёту выбрать точечное безопасное исправление и подготовить автоматическую проверку после инсталляции.


## Проверен полный реальный JSON с EET — BGXAI_FRIENDLY_AGGRO_READONLY_20261119T124214Z.json

Получены 2 файла пользователя: вывод пункта 135 и полный JSON, а не только выдержка TOP_SUSPECT_BLOCKS. Подтверждены:
- installed BDDEFAI.BCS SHA256 **89f59795c0382ab204731d898dc075504e2654085d0c7c247a53d3da439c2ffa**; **1173/1173** совпадающих блоков; последнее WeiDU **BGXRANGED3**. game_modified=false.
- В BCS ровно **11** блоков Attack*: #3 (V3), #1049–1054 (6 BGX retaliations), #1089 и #1102 (EPS), #1171 и #1173 (BGXP).
- #1049–1054: AttackReevaluate(LastAttackerOf(PlayerN),30) **каждый** имеет !InParty(LastAttackerOf(PlayerN)) и !Allegiance(...,GOODCUTOFF). Указание «MEMORIZED_ATTACKER_TARGET» в audit = лишь heuristics, не доказательство unsafe attack. Прямой случайный выбор Джахейры из партии через эти блоки выглядит исключённым условиями.
- #1089, #1102 (EPS): AttackOneRound(LastSeenBy(Myself)) с Allegiance(...,ENEMY), !InParty и !Allegiance(...,PC). Не объявлять EPS причиной по этому отчёту.
- #3 (V3): AttackOneRound(NearestEnemyOf(Myself)) **не имеет** !InParty/!Allegiance, поэтому fail-safe пробел присутствует; однако HPPercentGT(Myself,75), при задокументированных HP Халида 4/13 этот блок НЕ удовлетворяет условию. Не объявлять #3 источником фактического эпизода.
- #1171 и #1173 (BGXP): AttackOneRound(NearestEnemyOf(Myself)), содержат !InParty(NearestEnemyOf(Myself)), HPPercentGT(Myself,60). При 4/13 эти блоки также не удовлетворяют HP.
- #1078–1088: **11 ProtectObject(PlayerN,6)**, из BGX38/39. В документированных IESDP BGEE actions это длительная охрана, внутри которой движок самостоятельно атакует «врагов защищаемого». Эти 11 блоков запускают действие, которое НЕ будет отражено в отчёте как Attack*. Это **первый кандидат** на внутреннюю реакцию. Доказательства исполнения в момент нападения на Джахейру ещё нет.
- Остальные флаги THREAT_OR_PROTECT_PATH относятся к MoveToObject(PlayerN) на лечебных ролях, не являются атаками Джахейры. Не удалять лечение из-за ложных флагов.
- Возможны также другой активный CRE/script slot, хранящаяся в движке атака после friendly-fire, ранее выданный приказ, или модовый engine hook. Отчёт 135 анализирует BCS, **НЕ содержит trace начатых действий или происхождения команд**.

## Исходники защитного устранения очевидного недостатка

Создан безопасный V4 BAF candidate: BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXRANGED_V4_NO_FRIEND_ATTACK.baf, commit 9b7fad16452a0ab91916b40f52a0b01eb741fbb5. Добавлены !InParty(NearestEnemyOf(Myself)) и !Allegiance(NearestEnemyOf(Myself),GOODCUTOFF) **во все три** ветки переключения/стрельбы. Это дополнительный барьер, а **не доказанное исправление ProtectObject**. Не установлен, не проходил нативную EET-компиляцию. Не изменять live BCS до построения гарантированного WeiDU rollback. Не объявлять успешной проверку реальной атаки союзника.

## Приоритет

1. Зафиксировать и изолировать 11 BGX38/39 ProtectObject, НЕ ломая BGX60/61 защищённые AttackReevaluate, ручной бой и BGXP5 лечение; подготовить экспериментальное контролируемое отключение только этих 11 операций с проверкой исходного SHA, отдельным WeiDU component и гарантированным откатом, либо пассивный EEex started-action observer с реальным target-ID и source-классом UNKNOWN.
2. Готовить install проверку в одной цепочке: external backup → verified WeiDU → status verification; никаких отдельных «+» или повторных меню после SUCCESS.
3. Не вызывать повторные опасные атаки союзников в живой партии до безопасного способа тестирования и записи provenance.


## Experimental diagnostic fix BGXSAFE V4 — uploaded 135 JSON verified (19.11.2026)

Real report: active BCS SHA256 89f59795c0382ab204731d898dc075504e2654085d0c7c247a53d3da439c2ffa, 1173 blocks, BGXRANGED3 last. 11 Attack blocks: six BGX LastAttacker guarded by !InParty and !Allegiance; two EPS attacks require ENEMY and !InParty; two BGXP attacks require !InParty and HP>60; V3 block #3 lacks friend guard but requires HP>75 and cannot explain 4/13 HP aggression. Eleven ProtectObject(PN,6) actions in #1078–1088 (BGX38/39) are strongest testable source of internal/retained guard retaliation, NOT proven cause.

Created surgical guarded installer BGX_FRIENDLY_PROTECT_ISOLATION.py. Preconditions exact V3 SHA and last WeiDU; native WeiDU BCS decompile in TEMP; validates each of the 11 protection blocks contains only ProtectObject and allowed cooldown with guard and queue checks. Stops on any unexpected content. Reconstructs BCS with ONLY those 11 blocks absent (1173 -> 1162). In same update compiles BGXRANGED_V4_NO_FRIEND_ATTACK.baf using native WeiDU and replaces first 3 pilot blocks to require !InParty and !Allegiance(GOODCUTOFF). All 1159 other original blocks remain byte-exact.

External SHA256 backup BEFORE install, new BGXSAFE WeiDU component, automatic installed-state self-check, last-only guarded rollback restores exact V3 hash. No edits to BGXP5, BGX120 or EPS. While installed, eleven BGX38/39 ProtectObject bodyguard behaviors are intentionally disabled — other BGX60/61 direct guard routines remain but overall guard behavior may be weaker. This is a reversible diagnosis, not proven permanent fix.

Existing one-file BGXAI_UPDATE.cmd now offers:
- 136 BGXSAFE install+automatic native compile and post-install verification, explicit token INSTALL_BGXSAFE_PROTECT_ISOLATION
- 137 BGXSAFE status READ ONLY (optional)
- 138 guarded rollback restoring V3, explicit token ROLLBACK_BGXSAFE_PROTECT_ISOLATION

Pinned manifest 0.3.58-BGXSAFE-PROTECT-ISOLATION (12 source files); script commit ee9a884b120fab4ce3a958b70d906c1ff6d7895b, 79966 bytes, SHA256 eff7dc0abba5649b7fbcaa01a8f3dfc458e9f7355a0f93b6603162ddc3955214, PIN commit eb29a5b5785615e0f992ed42283699169f83985f. Unit tests run 44528213178 SUCCESS; Windows PowerShell AST/one-file source SHA/menu 1–138 run 44528809096 SUCCESS. NATIVE COMPILATION OF V4 ON USER'S EET AND GAMEPLAY NOT YET VERIFIED. No game changed by these source commits.

Next action if user consents: close game, InfinityLoader and WeiDU; use same CMD 136 and exact token. 136 auto-checks all stages and stops if error; no separate 135 or 137 on success. If STOP share output, do not retry blindly. Test safe saved game only after install PASS; do not risk live party via repeated friendly attacks. 138 guarded rollback available after inspecting status. This test differentiates ProtectObject contribution but does not prove all potential engine/other-script causes.


## Live PC install checkpoint — BGXSAFE PASS, 19.11.2026

User executed existing one-file BGXAI_UPDATE.cmd -> menu 136, explicitly authorized INSTALL_BGXSAFE_PROTECT_ISOLATION. Installer itself reported:
- status = BGXSAFE_PROTECT_ISOLATION_INSTALLED_VERIFIED
- candidate SHA256 = 9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e
- active BDDEFAI BCS blocks = 1162
- only_protect_blocks_removed = true
- v4_friend_filters_compiled = true
- game_modified = true
- external backup = C:\Users\Drevo\Documents\BGXAI_SAFE_BACKUPS\BGXSAFE_PRE_20261119T130205718850Z

**Interpretation:** Exact verified installed-state/WeiDU status is PASS. Still NO gameplay proof that friendly-fire retaliation has stopped. NO additional game install or status menu is required; menu 136 already completed automatic postinstall verification as requested. Keep fallback menu 138 guarded rollback.

**Next safe isolated gameplay check:** On expendable/quicksave copy, F guard ON, EPS Autoattack OFF, keep Jaheira and Khalid in party, no actual external enemies, avoid 4/13 HP risk. 1) Observe without any friendly damage: no inappropriate attacks. 2) Only if a disposable save is available, perform one controlled low-damage friendly attack with Party AI OFF then Party AI ON, pause immediately to observe, do not continue if any ally retaliation. 3) If friendly retaliation still occurs, stop; possible engine retaliation/other script/retained action source, no claims that BGXSAFE is permanent fix. 4) After return to clean save, conduct a separate safe real-enemy test to ensure guard (some ProtectObject removed), healing and bow/sword selection remain functional. Do not test at low HP with no protection.

Do not request automatic repeat status 137; results of these combat tests are the remaining factual gate.


## 19.11.2026 — Grey test after BGXSAFE and extended one-file audit 135

**New real gameplay evidence:** With BGXSAFE already installed and verified (1162 BCS blocks, SHA256 `9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e`), Grey attacks Khalid and BG combat log explicitly shows `Халид: атакует цель: Грей`. Grey is present as party portrait. **Friendly retaliation persists.** Therefore removal of the 11 legacy ProtectObject blocks plus V4 explicit friendly filters was not a sufficient fix. This observation does not identify whether the remaining action came from EPS, BGXP, another script slot, EEex, or engine-retained retaliation. Do NOT claim source provenance from one screenshot.

**Implemented new read-only forensic extension to existing menu 135** (do not create another user-facing CMD or require an install):
- `BGXAI_SAVE_SCRIPT_AUDIT_READONLY.py` enumerates latest available saved `BALDUR.GAM` in the game and known BG:EE/BG2:EE Documents save locations (bounded read, no writes). Parses GAME V2.0 party NPC records and embedded CRE V1.0 script slots: Override, Class, Race, General, Default; extracts saved party member names/HP/EA, saved Party AI flag and full save SHA. If unsupported or absent it marks unavailable; **saved slot data is not verified live EEex state**.
- Decompiles the actual referenced scripts via a copied native WeiDU in TEMP, plus baseline BDDEFAI/PRIEST1; reports every attack/protection action with full triggering conditions, `!InParty`/Allegiance checks and script provenance. Missing BIF resources are marked unavailable, not misreported as harmless.
- Reads `override/M_BX43.lua` statically for EEex listener declarations. Listener presence does not prove listener invocation or whether an action came from manual input / EPS / BGXAI; all runtime action origins are **UNKNOWN** until a validated passive started-action trace is installed and exercised.
- Original `BDDEFAI.BCS` block analysis retained, with extended data in the same JSON. Print lines `SAVED_ACTOR`, `ASSIGNED_SCRIPT` and report file path. Does not install, roll back, patch, or touch game files.
- Source regression and GAM slot-bounds tests: <https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44532965125> **SUCCESS**. Windows PowerShell 5.1 AST, all old menus, pinned release, 84/84 source hashes: <https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44533474265> **SUCCESS**.
- Pinned release `0.3.59-BGX-SCRIPT-SLOTS-AUDIT` (13 files); immutable `BGXAI_SYNC.ps1` commit `23eddc3635e4da554d9e7c80b87c599fae416412`, 79979 bytes, SHA256 `54b7642360584d82660f0ec23e102d336582738d06cf10128cd821cd42bdce43`; pin commit `49969426ac23e991fc09e84f316e3bbfc6c9921c`.
- **Next single action on user's PC:** close Baldur and InfinityLoader; launch SAME `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, select **135 — Full aggro audit READ ONLY**. Send the new JSON shown as `REPORT_FILE` (and console text if fail). No reinstall of 136 or test with deliberate friendly attacks. The tool analyzes the most recent saved GAME, which may differ from screenshot runtime.
- No full culprit proved yet. If multi-slot static evidence still ambiguous, next engineering step will require an independently reviewed, opt-in **passive EEex started-action trace with target-ID**, not guessed action provenance, and protected installation with rollback.
