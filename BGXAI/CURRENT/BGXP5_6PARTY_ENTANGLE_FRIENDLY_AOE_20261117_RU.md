# BGXAI — шесть персонажей: лечение подтверждено, массовый контроль по своим (17.11.2026)

Пользователь загрузил тестовое сохранение с шестью членами партии и проверил бой с больным гибберлингом. На четырех скриншотах:
- Tarana атакует гибберлинга; вражеская атака оставляет Tarana на 2/14 HP после получения 12 рубящего урона.
- Jagan Battleforge применяет «Повеление» к гибберлингу.
- Джахейра автоматически произносит «Запутывание» (Entangle), нацеливает его на больного гибберлинга, но зона заклинания накрывает и своих, по сообщению пользователя. Это типичное area-of-effect friendly fire, **не** доказательство выбора члена партии как непосредственной цели.
- Jagan Battleforge затем применяет «Исцеление лёгких ран» к Tarana; отображаемое HP после лечения 8/14. Пользователь подтверждает, что лечение сработало.

**Итог:** BGXP5 AUTO-heal оставляем неизменным; проблему выносим в отдельную AOE safety logic, прежде всего Entangle у Джахейры. Массовое Entangle воздействует на союзников в радиусе, поэтому проверки `!InParty(NearestEnemyOf(Myself))` недостаточно. Нельзя исправлять проблему подменой цели, только проверкой будущей зоны эффекта по позициям союзников + реальному радиусу из установленного SPL или выбором безопасного контроля.

Неизвестно, какой именно блок внутри установленного `BDDEFAI.BCS` инициирует Entangle: EPS 18.4 или BGXAI. Актуальная проверенная установленная EET: BGXP5 `BDDEFAI.BCS` SHA256 `cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a`, Lua SHA `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`; 1170 блоков. Предыдущий успешный тест BGXP5: «всё сработало».

В рамках текущего обращения подготовлен **отдельный read-only диагностический архив** `BGXAI_AOE_AUDIT_READONLY.zip`: `RUN_AOE_AUDIT.cmd` → `BGXAI_AOE_AUDIT.py`, сверяет точные SHA и last WeiDU BGXP5; копирует текущие BCS и WeiDU во временную системную папку, декомпилирует и упаковывает полный BAF и сводку AOE вне каталога игры в `Documents\BGXAI_LIVE_REPORTS\BGXAI_AOE_SEND_TO_CHATGPT_....zip`. Синтетический тест текстового извлечения 2 блоков, 1 Entangle — PASS, **живой WeiDU decompile ещё не выполнялся**, возможен STOP без изменения файлов.

До анализа реального BAF никакого патча, отключения EPS и изменения сохранений. Если будет разработан исправляющий модуль, только source-only → native EET test → отдельная typed-approval install с резервной копией, старое лечение сохранять строго побайтно.


## 17.11.2026 — ВОССТАНОВЛЕНО СТРОГОЕ ПРАВИЛО «ОДИН ФАЙЛ» (menu 117)

Пользователь напомнил о правиле: использовать **только старый `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`**. Ранее предложенный отдельный `RUN_AOE_AUDIT.cmd` был ошибкой интерфейса; **НЕ запускать старый отдельный ZIP**. В pinned `BGXAI/BGXAI_SYNC.ps1` добавлена новая только-читающая команда:

`117 - AOE Entangle audit (READ ONLY; BGXP5 no changes)`

Все пункты 1–116 и прежний CMD оставлены. Внутри пункта 117: `SyncRelease` загружает 3 SHA256-проверенных файла из `BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/` в папку разработчика `BGXAI_DEV` (не в override), после повторной SHA-проверки запускается Python декомпиляция **копии** нынешнего `BDDEFAI.BCS` в TEMP и создание ZIP в `Documents\BGXAI_LIVE_REPORTS\BGXAI_AOE_SEND_TO_CHATGPT_...zip`.

**Подтверждённые проверки**:
- Windows 6/6 mock tests read-only/Entangle/source hashes 3/3: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44100072108 — SUCCESS
- Windows PowerShell 5.1 AST, старое меню, новый пункт 117, pinned commit и 61/61 SHA-источников: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44100202154 — SUCCESS
- Новый `BGXAI_SYNC.ps1`: 79070 байт, SHA256 `0026c5ddb0d60069920083d09a8df47b51ea996ff62d72c30bc8d9fca0d7236e`.
- `BOOTSTRAP_PIN.json` закрепляет commit `2f12121f32d4ace70b8d72723d22c79447e1b62f`; PIN обновлён commit `379dfd03a6f7989c97252b62452dd9c46f55dd23`.
- Никаких новых установок, WeiDU, BCS, Lua, настроек EPS или сохранений.

**Единственное действие пользователя:** запустить прежний `BGXAI_UPDATE.cmd`, выбрать **117**, прислать полученный ZIP; не использовать отдельный `RUN_AOE_AUDIT.cmd`. Реальная декомпиляция на Windows пользователя пока **не подтверждена**, допускается безопасный STOP (без повторных установок). Лечение BGXP5 по прежнему стабильно.

## После реального ZIP аудита 117 — диагностирован дополнительный PRIEST1 (17.11.2026)

Пользователь прислал `BGXAI_AOE_SEND_TO_CHATGPT_20261117T141514369696Z.zip` (оригинальный архив SHA256 `fd76396d6681300ca6b2c098c58054dfa3ecd296df7828c5256ad2b0505f72b9`). Реальный отчёт: `BGXAI_AOE_READONLY_PASS`, 1170 блоков, 406 слов-срабатываний AOE, **0 ENTANGLE**. Полный BAF (1.53 MB) проверен: **нет** `CLERIC_ENTANGLE`, `SPPR105`, `SPPR101`, следовательно **BDDEFAI.BCS не содержит явного кастования Entangle**. 406 keyword hits включают проверки и отрицательные условия, не являются 406 кастами.

Сравнение с исходным **пользовательским тестовым** `BGXAI_TEST_6_EXPERIMENTAL.zip` показало для Джахейры в `GAMEV2.0\BALDUR.gam`: override script `JAHEIRA_` (CRE +0x248), class `BDDEFAI` (+0x250), **race `PRIEST1` (+0x258)**, general `WTASIGHT` (+0x260), default `DPLAYER` (+0x268). Для всех шести class `BDDEFAI`. Сам старый скрипт `PRIEST1.BCS` известен по публичному описанию BG1 как Entangle / Command / Hold Person, но его содержимое именно из текущей модовой EET ещё не извлечено. **Причина пока гипотеза**, не окончательная атрибуция.

## Готовый безопасный A/B тест через всё тот же один CMD

В pinned `BGXAI/BGXAI_SYNC.ps1` добавлен пункт **118**:
`118 - Copy BGXAI_TEST_6 without Jaheira PRIEST1 (typed approval; no override changes)`

Создаёт **только новый** игровой тестовый слот `000000901-BGXAI_TEST_6_NO_PRIEST1` из существующего `000000900-BGXAI_TEST_6`, при закрытой игре/InfinityLoader/WeiDU и точном вводе `CREATE_BGXAI_TEST6_NO_PRIEST1`. Проверяет live SHA BCS/Lua и last WeiDU BGXP5, шесть известных NPC, Jaheira override `JAHEIRA_`, race `PRIEST1` и class `BDDEFAI`. Меняет только 8 байт в новом `BALDUR.gam`: `PRIEST1\0` → `None\0\0\0\0`. Запрещает перезаписывать, сохраняя исходное тестовое и основное прохождения, все остальные CRE/скрипты/HP/предметы/магия/area SAV и всю игру байт-в-байт.

Исходники `BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/` с manifest version `0.3.44-BGXAOE-SAFE-SAVECOPY`; Windows **13/13 unit/mock tests + 5/5 exact source SHA** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44103669486 PASS. **Единый CMD (1–118) + AST Windows PowerShell 5.1 + 63/63 SHA** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44103856011 PASS. Sync `79725` байт SHA256 `b5c8f6af7d2168f51556d955ae2238a0ad1226906deef4311319185b0b319511`, pin immutable commit `711840d55df51c86da9b9464aa2bc22b882cfa1e`.

**Следующее действие пользователя:** только старый `BGXAI_UPDATE.cmd`, пункт 118, подтверждение, затем загрузить новый A/B test-save и повторить бой. Если Entangle исчез — локализован нежелательный дополнительный скрипт; если остаётся — искать далее в JAHEIRA_/WTASIGHT/DPLAYER. **Это не доказанная универсальная AOE-защита**. Не менять BGXP5, живые BCS и другие файлы игры.
