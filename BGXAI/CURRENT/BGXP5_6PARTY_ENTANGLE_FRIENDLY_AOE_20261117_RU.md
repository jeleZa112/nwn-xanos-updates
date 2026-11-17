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

## Инцидент: пункт 118 повторно останавливается с Unexpected release manifest

Пользователь **два раза** запускал один и тот же `BGXAI_UPDATE.cmd` пункт 118; второй раз — после опубликованного обновления. Оба раза:
`Downloading and verifying BGXAI AOE117 from pinned GitHub commit ...`
`BGXAI STOP: Unexpected release manifest`.
При этом из пользовательского вывода **неизвестно**, какой `BGXAI: verified pinned script <12-char hash>` был показан в начале запуска, потому что приведён только конец журнала.

Установлена детерминированная причина старого релиза: immutable ref `711840d55df51c86da9b9464aa2bc22b882cfa1e` содержит `BGXAI_SYNC.ps1` с `releaseAOE.version=0.3.43-BGXAOE-READONLY`, но в **том же коммите** `manifest_updater.json` содержит `version=0.3.44-BGXAOE-SAFE-SAVECOPY`. Текущая иммутабельная ссылка `0c01f9f5c56087b1ff39471c3a06a1409cfe2a14` содержит **обе версии 0.3.44**; текущий `BOOTSTRAP_PIN.json` закрепляет именно `0c01...`, SHA256 скрипта `6897f43009d32008fe499db871fb17c9c09ad494a7e69e142474a646b8c072bd`, размер 79730 байт. Windows CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44105584057 PASS. Инцидент **очень похож на старый bootstrap pin / CDN proxy cache**, однако без локального `head.txt` нельзя доказать, что ошибка второй попытки именно от старого immutable ref.

**Не рекомендовать третий слепой запуск 118.** Сначала строго **только чтение** в PowerShell, без дополнительных программ/файлов:
`Get-Content "$env:LOCALAPPDATA\BGXAI_UPDATER\head.txt"; Select-String -Path "$env:LOCALAPPDATA\BGXAI_UPDATER\BGXAI_SYNC.current.ps1" -Pattern "id='AOE117';version="`.
Если head показывает `711840d55df5`, а spec `0.3.43`, это подтверждает stale pin. Если head показывает `0c01f9f5c560` и spec `0.3.44`, нужна дополнительная диагностика фактически загруженного immutable manifest/HTTP cache; не предполагать новый повтор исправит проблему. **Не изменять BGXP5 / сохранять контрольные суммы и один CMD**.

## Подтверждение источника аварии и решение одним CMD

Пользователь в Windows PowerShell выдал точные значения `%LOCALAPPDATA%\BGXAI_UPDATER\head.txt = 711840d55df51c86da9b9464aa2bc22b882cfa1e` и `BGXAI_SYNC.current.ps1` line 197 `id='AOE117';version='0.3.43-BGXAOE-READONLY'`. Устаревшая закреплённая версия **фактически выполняется**, прежняя попытка повторного 118 была обречена независимо от исправления в GitHub, так как старый CMD при повторном запуске перезаписывает локальный текущий скрипт старой привязкой. Просто удалить кеш недостаточно без исправления первичного bootstrap.

**Исправлена ровно одна запускаемая точка — тот же `BGXAI_UPDATE.cmd`**, без дополнительных CMD/установщиков: в embedded PowerShell bootstrap добавлен fail-closed SHA-verified fallback только при точном ранее известном сочетании `commit=711840d55df5...`, `script_sha256=b5c8f6af...`, `script_size=79725`. Переходит на immutable `0c01f9f5c56087b1ff39471c3a06a1409cfe2a14`, exact `script_sha256=6897f43009d32008fe499db871fb17c9c09ad494a7e69e142474a646b8c072bd`, `size=79730` и проверяет реально скачанный файл до выполнения. Для любого другого pin fallback не срабатывает; при изменённом hash старой версии — STOP. Внешние API не используются.

Новый `BGXAI_UPDATE.cmd` UTF-8 CRLF 6793 байта, SHA256 `20efb6f327331344df37bbfcbf2ebb3c9e1c6606867feb4a324bc6db9fafd20d`, exact Git blob `3777f758106252eb6a8cacaf9038d11fc5c3de95`. Полный прежний CMD сохранён за исключением 882 байт защитной вставки. Windows PowerShell 5.1 AST/legacy menu/pin SHA source tests PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44110610926; **независимый Windows PowerShell 5.1 тест fallback** со старым pin, новым pin и поддельным SHA PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44111215804. Изменение единственного CMD GitHub `5c56c27b01f73d2d4cf49c7366008cd196e6e48d`. Локально созданный пользовательский артефакт содержит тот же байтовый образ с указанной SHA, а ZIP упаковка содержит один и только один `BGXAI_UPDATE.cmd`.

**Для пользователя нужна одна ручная замена физически старого CMD:** распаковать новый `BGXAI_UPDATE.cmd` в прежнюю папку `C:\Games\BG_EET_FOXX_NEW` с заменой одноимённого файла. Это не добавление второго updater, не изменение живых BCS/Lua/WeiDU и не переустановка игры. Далее запуск старого имени, ожидаем `BGXAI: stale 0.3.43 branch pin detected; SHA-verified 0.3.44 recovery enabled.` и `BGXAI: verified pinned script 0c01f9f5c560 (SHA256 OK)`; только затем пункт 118 typed `CREATE_BGXAI_TEST6_NO_PRIEST1` для создания новой тестовой копии. Если первые строки иные или SHA STOP, не пробовать 118 снова, прислать полный bootstrap output.

Из отдельно сохранённого оригинального тестового архива `BGXAI_TEST_6_EXPERIMENTAL.zip` повторно проверена совместимость: save slot `000000900-BGXAI_TEST_6`, `BALDUR.gam` GAMEV2.0, 6 членов, имена по слоту Tarana/Tarana/Jade/Jagan Battleforge/Khalid/Jaheira; class `BDDEFAI` у всех; Jaheira override `JAHEIRA_`, race `PRIEST1`, general `WTASIGHT`, default `DPLAYER`. Сохранение на ПК пользователя всё же может различаться, установщик 118 остановится при отличии, не перезаписывая исходное. BGXP5 не затрагивался.

## Реальный запуск 118 — ПОДТВЕРЖДЁН ПОЛЬЗОВАТЕЛЕМ, PASS

Пользователь прислал фактический полный вывод пункта 118, новая упаковка успешно синхронизировала SHA-проверенные 5 файлов `AOE117`. После ввода `CREATE_BGXAI_TEST6_NO_PRIEST1` скрипт завершился `BGXAI_TEST6_NO_PRIEST1_COPY_VERIFIED`, общее меню написало `BGXAI: update/status action completed`. Физическая копия нового слота:
`C:\Users\Drevo\Documents\Baldur's Gate - Enhanced Edition Trilogy\save\000000901-BGXAI_TEST_6_NO_PRIEST1`.

Контрольные суммы:
- оригинальный `BALDUR.gam`: `7e782968bfa7b6795765ee406cf51916a6c1f5ced6e67a18ad8723c6f21eb881`
- изменённый `BALDUR.gam`: `8cc1e8a6f0865784175ac781bee19d33350e8f2c4724b61389b58e85f96ccc00`
- `modified_offset=103744`; 8 байт race-слота Джахейры: `PRIEST1` → `None`
- остальные члены партии ровно шесть: Tarana, Tarana, Jade, Jagan Battleforge, Khalid, Jaheira; у всех `class_script=BDDEFAI`
- скопировано 7 файлов с verified hashes; `original_preserved=true`, `game_bcs_lua_preserved=true`, `game_modified=false`.

**Следующий необходимый этап:** пользователь загружает `BGXAI_TEST_6_NO_PRIEST1` через InfinityLoader и проводит одинаковый бой, чтобы сравнить автоматическое «Запутывание» Джахейры и лечение Жагана. Никакая игровая функциональность / новый патч не установлены; только изолированный A/B test-save. **Источник Entangle пока не подтверждён экспериментально**, т.к. in-game результат нового слота ещё не получен.

Повторять пункт 118 **не нужно**, так как target slot уже существует, защищён от перезаписи. Продолжать разработку боевой координации, не меняя проверенный BGXP5.

## Реальный A/B бой без PRIEST1: гипотеза опровергнута

Пользователь предоставил **два скриншота после двух одинаковых игровых тестов** на новой копии `BGXAI_TEST_6_NO_PRIEST1`. Боевой журнал **в обоих** явно показывает:
`Джахейра: читает заклинание Запутывание : Больной гибберлинг`.
На втором — `Больной гибберлинг: спасбросок против заклинаний : 20` и `Tarana: спасбросок против заклинаний : 21`; это подтверждает, что заклинание воздействует в том числе на положение союзника. **Очистка одного дополнительного CRE race-slot PRIEST1 не прекратила каст.** Гипотеза «PRIEST1 — единственный источник» опровергнута; не заставлять пользователя третий раз повторять тот же бой.

До сих пор установленный `BDDEFAI.BCS` (BGXP5 SHA `cfc61c...`) из реального ZIP 117 содержит 1170 блоков, **явного Entangle нет**. Проверенные embedded_CRE Jaheira из исходного тестового GAM имеют override `JAHEIRA_`, class `BDDEFAI`, race `PRIEST1` (удалён в новой копии), general `WTASIGHT`, default `DPLAYER`. Сейчас виновный BCS **не установлен**: возможен один из оставшихся скриптов, автоматическое восстановление слота при загрузке или иная очередь/движок. Не приписывать каст BGXP5 без доказательства.

## Создан BGXAI 119 — точная диагностика исполнения скриптов, один CMD

Новый read-only `BGX119_TRACE.py` встроен в pinned меню **119 - Trace Jaheira scripts (READ ONLY)** существующего одного `BGXAI_UPDATE.cmd`. Проверяет контрольные суммы BGXP5/WeiDU, собирает назначение всех 5 CRE-скриптов из `000000901-BGXAI_TEST_6_NO_PRIEST1`, вытаскивает актуальные `JAHEIRA_.BCS`, `PRIEST1.BCS`, `WTASIGHT.BCS`, `DPLAYER.BCS` и `BDDEFAI.BCS` из `override` или `CHITIN.KEY/BIFF` (WeiDU `--biff-get` только в TMP), декомпилирует BAF там же, сохраняет один `Documents\BGXAI_LIVE_REPORTS\BGXAI_SEND_SCRIPT_TRACE_*.zip`. При ошибке одного ресурса продолжает остальные и отмечает в JSON. **Нет изменения override, game saves, WeiDU, BGXP5, EET RU, Voice RU, BGXAI.**

`BGXAI_SYNC.ps1` 79 934 байта, SHA256 `a77fbae9579d3c192cca3269dae25e0a1b3b2610995e3a97acf5197b65554f39`, immutable source ref `96dcda9cf91d921e9a37d67f7c382b6ba2abe394`. Пакет AOE manifest `0.3.45-BGXAOE-SCRIPT-TRACE`, 6 SHA-проверенных файлов. Для защиты от устаревшего branch PIN обновлён **всё тот же один** `BGXAI_UPDATE.cmd` — SHA256 `6a94650e2f9e5eda242f4d8a0dd5d84545fbee63906cc3a3e19b2b068bd3b585`, 7002 байта; он умеет строго по SHA распознавать оба старых pin `711840...` и `0c01f9...` и переводить на immutable 119. Новый `BOOTSTRAP_PIN.json` также закреплён на скрипт 119.
Windows CI: 6 источников SHA + mock audit tests SUCCESS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44114410159; единый updater menu/AST/pin Windows SUCCESS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44115256735; Windows bootstrap stale pins (обе версии), forged hash reject SUCCESS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44115206187. **Реальный 119 на пользовательском EET ещё не запускался.**

Пользователю доступен ZIP `BGXAI_UPDATE_ONE_FILE_119.zip`, внутри **только `BGXAI_UPDATE.cmd`** с точной SHA проверкой. Чтобы получить пункт 119, один раз заменить *именно существующий* CMD в `C:\Games\BG_EET_FOXX_NEW`, затем выбрать 119 и прислать отчёт ZIP. Не повторять 118 и не повторять бои. Дальнейшая точечная AOE защита только после прочтения реальных BAF.

## Реальный полный ZIP 119 — фактический источник Entangle в PRIEST1.BCS

Пользователь прислал `BGXAI_SEND_SCRIPT_TRACE_20261117T155803815758Z.zip`, SHA256 `a270e4e9aa218174aac73bd7ccc697b94e5843ee3f884c92a5225ff2ed5e23fd`. Архив реально открыт и проанализирован. `REPORT.json`:
- `status=BGX119_READONLY_PASS`, `game_modified=false`.
- BGXP5 override `BDDEFAI.BCS` SHA256 `cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a`, Lua `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`, last WeiDU BGXP5.
- В сохранении `000000901-BGXAI_TEST_6_NO_PRIEST1` BALDUR.gam SHA256 `8cc1e8a6f0865784175ac781bee19d33350e8f2c4724b61389b58e85f96ccc00`, шесть NPC. У Джахейры script slots: override `JAHEIRA_`; class `BDDEFAI`; race `None`; general `WTASIGHT`; default `DPLAYER`. Таким образом **PRIEST1 действительно отсутствует в сохранённом CRE**.
- **Единственный прямой `CLERIC_ENTANGLE` среди пяти реально декомпилированных скриптов находится в `PRIEST1.BCS`** (override SHA256 `867ff7fd9efa8a182bf3475bfef6b6f1de851067147ea15bd962431d329f6a9b`). Блок 3 из 5:
```baf
IF
  See(NearestEnemyOf(Myself))
  HaveSpell(CLERIC_ENTANGLE)
  !StateCheck(NearestEnemyOf(Myself),STATE_SLEEPING)
  !StateCheck(NearestEnemyOf(Myself),STATE_HELPLESS)
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)
END
```
**Проверки союзников внутри области в нём нет**, поэтому данный скрипт создаёт риск friendly AoE в обычных случаях. Но **он не назначен Джахейре в сохранённом новом GAM**, а в двух фактических боях Entangle продолжает применяться. Это противоречие требует runtime attribution; нельзя утверждать, что именно этот блок исполнился в обоих боях.
- `JAHEIRA_.BCS` override SHA256 `140a13fe558db817960b4ff8e176f206c00a0d212612ffbb5964f7c4f05c990b`: 44 блока, нет `Entangle`, 20 spell action lines, единственный `ChangeAIScript` относится к Khalid/DEFAULT, не Джахейре.
- `BDDEFAI.BCS`: 1170 блоков, нет Entangle, 345 spell actions.
- `WTASIGHT.BCS` override SHA256 `d3055bb06a50e2a6152e4ace8d2753e5450df28e066148eae2a0c01651e24605`: 6 блоков, 0 spell actions, Entangle нет.
- `DPLAYER.BCS` chitin_biff SHA256 `bc34b9b9f2ec79149bad5abd793b82ab7c79d036fc0f3032a21ea3e7eef03d92`: 2 блока, 0 spell actions, Entangle нет.

В исходном тестовом `BALDUR.SAV` (тот же побайтно, что в A/B копии) распакованы 5 записей `BG2600.are`, `BG2616.are`, `INN2616.sto`, `WORLDMAP.wmp`, `DEFAULT.toh`. В декомпрессированных файлах нет прямых байтовых `PRIEST1`, `JAHEIRA_`, `BDDEFAI`. Это **не доказывает отсутствие скрытых/индексных назначений скриптов**.

**Следующее безопасное действие:** исследовать *реальное исполнение в памяти* (EEex runtime provenance), а не менять другой слот вслепую и не повторять бой из старого сохранения. Возможно автопереназначение скриптов при загрузке или другой живой экземпляр NPC/очередь действия; пока причины этих факторов не доказаны. Не отключать весь PRIEST1 глобально, не удалять JAHEIRA_ (сюжетные блоки!), не переписывать BDDEFAI и не подвергать успешное лечение BGXP5 риску.

Пользователь требует **один постоянный `BGXAI_UPDATE.cmd`**, без очередных ручных замен, поэтому дальнейшую диагностику или исправление надо проводить штатным каналом, желательно без изменений CMD и без отдельного установщика. Пункт 119 успешно выполнен, заново не нужен.

## Важное уточнение о двух боевых тестах: quicksave является продолжением NO_PRIEST1

Пользователь подтвердил явно: **сначала загрузил отдельное тестовое сохранение `BGXAI_TEST_6_NO_PRIEST1`, затем вышел за пределы города и сделал НОВОЕ быстрое сохранение, из которого выполнил оба одинаковых боя**. Следовательно, наблюдавшийся Entangle после удаления PRIEST1 не был тестом из независимого старого игрового слота. Однако ранее аудированные 117/119 `000000901-BGXAI_TEST_6_NO_PRIEST1/BALDUR.gam` отражают **исходный** слот, а не новое быстрое сохранение после перехода; фактическое состояние слотов CRE в quicksave не изучено.

Следующее действие: получить **именно новое быстрое сохранение** пользователя (zip источника, read-only, без изменения игры) и проверить пять script-slot у Джахейры + имена NPC, SHA, текущую область. Если `PRIEST1` восстановился — выявить причину восстановления, не удалять очередной слот вслепую. Если остался `None`, нужна атрибуция runtime EEex/скрипт из другой очереди. Не проводить третий бой, не перезапускать 118, не заменять постоянный `BGXAI_UPDATE.cmd`, не затрагивать лечение BGXP5.


## Реальное быстрое сохранение после перехода: PRIEST1 в Джахейре восстановлен

Новый ZIP пользователя `BGXAI_QUICKSAVE_20261117_232534.zip` открыт непосредственно через Python ZipFile. В нём `000000001-Быстрое сохранение 4\\BALDUR.gam` размер 186788, SHA256 `60cbfe28d6ee9ffacddd80f1c9e193c9760a6e1463cdbbd6510580679de0cd55`, сигнатура GAMEV2.0, 6 членов партии. GAM структурно валиден, party offset 0xb4 и шестой слот (index 5) embedded CRE. В этом шестом слоте: override `JAHEIRA_`, class `BDDEFAI`, race **`PRIEST1`**, general `WTASIGHT`, default `DPLAYER`. Исходная диагностированная копия `000000901-BGXAI_TEST_6_NO_PRIEST1` (SHA GAM `8cc1e8a6f0865784175ac781bee19d33350e8f2c4724b61389b58e85f96ccc00`) **содержала у Джахейры race=None** и четыре те же остальные поля.

Итак, это НЕ доказательство «Entangle после отключения PRIEST1»: в новом фактическом quicksave PRIEST1 опять назначен, а его BAF содержит прямой `Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)` без проверки союзников. Два скриншота согласуются с действующим PRIEST1.

Дополнительная проверка связи с переходом: экспериментальный тест GAM имел game time 5205 и area resref `BG2600` (Candlekeep), а новый quicksave game time 9364 и area `BG2700`; число партии 6. После выхода в quicksave в party slot 2 использован override `IMOEN_`, slot 3 `c#grey` (раньше в тестовом слоте там были Tarana и Jade); в nonparty records нового quicksave появились Jade и Tarana. Это согласуется с тем, что по ходу игры состав поменялся, но **не доказывает сам механизм восстановления** `PRIEST1` (перезапись слота на переходе, скриптом, движком, UI или загрузка более старого save). В ZIP entry `BALDUR.gam` modification timestamp 2026-11-17 20:48:50 из исходного Windows архива; не приравнивать к времени упаковки 23:25:34. Уточнение пользователя до этого ZIP: загрузил NO_PRIEST1, вышел из города, сделал новое быстрое сохранение и из него тестировал.

**Решение по проекту:** Не менять установленный BGXP5, BCS и основное прохождение, не заставлять пользователя повторять 117/118/119 или тот же бой, не выпускать очередной CMD. Следующая безопасная идея: адресная runtime-защита от автоматического опасного AOE `CLERIC_ENTANGLE` в `PRIEST1`, но до внедрения нужно доказать конкретный механизм переназначения скрипта и протестировать guards на WeiDU/EET. Можно провести read-only анализ свежей версии из сейва, в том числе CRE/слотов NPC. Не отключать `PRIEST1` глобально, поскольку он встречается и у других NPC (Viconia/Quayle).


## BGX120 реализован: точечный party-safe Entangle WeiDU с восстановлением, один постоянный CMD

Пользователь: «что мне делать делай». Подготовлен и интегрирован **BGXAI пункт 120**, не меняя и не переупаковывая существующий физический `BGXAI_UPDATE.cmd` (статичный CMD прежней версии 119, SHA256 `6a94650e2f9e5eda242f4d8a0dd5d84545fbee63906cc3a3e19b2b068bd3b585`). Его bootstrap, когда получает актуальный branch pin, загружает новую immutable версию `BGXAI_SYNC.ps1` (1–120, 79 959 байт, SHA256 `2dee122e9f7ddf26c885e57ff6a871322e4a37c72f23b3ac62f396354f6a9ed5`, ref `42ea7048a46adbc2385c4c1ce0f4996e3cd5dde9`). Текущий `BOOTSTRAP_PIN.json` содержит именно эту привязку. Следует **не** снова предлагать другой CMD.

Пакет `BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117` обновлён до `0.3.46-BGX120-PARTY-AOE`, 8 SHA-pinned source files. Новый `BGX120_ENTANGLE_GUARD.py` является подрежимом 120 (1=status, 2=read-only native EET preflight, 3=typed WeiDU install, 4=typed guarded rollback). В реальном `PRIEST1.BAF` третьему из 5 блоков добавляет **только** `!InParty(Myself)` сразу после `HaveSpell(CLERIC_ENTANGLE)`. Это означает: для NPC **в составе партии** безопасно отключается автоматическое опасное «Запутывание» в generic PRIEST1, но остальные четыре блока PRIEST1 (паника, Hold Person, Command, атака) побайтно сохраняются при native dual-compilation, враги и ручной каст Entangle остаются как прежде. Этот консервативный вариант **не является умной проверкой геометрии AoE**; это немедленная защита от friendly fire на подтверждённом источнике. Триггер InParty подтверждён в BGEE IESDP: https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm.

Перед каким-либо изменением проверяет SHA `override/PRIEST1.BCS` `867ff7fd...`, BGXP5 `BDDEFAI.BCS` `cfc61c...`, Lua `74ddc...` и last WeiDU BGXP5; декомпилирует **реальный** PRIEST1 в system temp и сверяет SHA 919-байт BAF `44776429fc6c...`. Компилирует старый и изменённый BAF настоящим WeiDU v251 с IDS из игры **только в TEMP**; проверяет 5 BCS blocks и только изменённый index2, декомпилирует кандидат и проверяет отрицательный триггер. Не допускает стадии install если нет exact compile/preflight. Перед установкой закрытая игра/InfinityLoader/WeiDU, отдельное подтверждение `INSTALL_BGX120_PARTY_ENTANGLE_GUARD`, SHA-проверенный внешний backup `Documents\BGXAI120_SAFE_BACKUPS`, новый WeiDU компонент `BGX120` поверх BGXP5. Не меняет BGXP5, Lua, TLK, saves или другие файлы. На откат только если BGX120 последним, отдельный токен `ROLLBACK_BGX120_PARTY_ENTANGLE_GUARD`, проверяет исходный SHA PRIEST1. Никаких автоматических повторов после STOP.

Проверки GitHub на Windows: 25/25 unit/mock test (8 package SHA, включая точный исходный 919-байт BAF) PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44131887385; immutable one-file 1–120 + PowerShell5.1 AST + 66/66 SHA PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44132165120. **ВАЖНО: на пользовательском ПК BGX120 ещё не установлен, реальная EET native compilation/WeiDU install ещё не проверялись.** Пользователь может запустить **старый физический** `BGXAI_UPDATE.cmd` (тот же, что работал для 119), выбрать пункт 120 и сначала 2 (native preflight) или непосредственно 3 (installs guarded by native preflight and explicit typed approval). Если пункта 120 нет — прислать bootstrap pin first lines; не вручную перезаливать CMD, не подменять cached .ps1 или head.txt.

Новый BGX120 код находится в GitHub, процесс не осуществлял запись в файлы игры пользователя.


## BGX120 live attempt STOP and 0.3.47 hotfix — real PRIEST1 native WeiDU BCS 5-block detection

Пользователь запустил **реальную попытку BGX120 mode 3**, ввёл `INSTALL_BGX120_PARTY_ENTANGLE_GUARD`. Вывод `BGX120_STOP: COMPILED_PRIEST1_NOT_5_BLOCKS`, `BGXAI STOP: 120 STOP`. Установка остановилась в preflight/candidate до WeiDU-install, до staging файлов и внешнего backup. **Никакие live BCS, Lua, WeiDU или сохранения не изменялись в этом неудачном запуске**. Автоповтор запрещён.

Ошибка локализована: старый parser `blocks()` разбивал BCS по каждому `CR\\n` и считал внутренний END разделитель как start, хотя настоящий BCS использует `CR\\nCR\\nCO\\n` между блоками. Не гадали: извлечён лично присланный пользователем `BGXAI_SEND_SCRIPT_TRACE_20261117T155803815758Z.zip`, его файл `PRIEST1.BCS` SHA256 `867ff7fd9efa8a182bf3475bfef6b6f1de851067147ea15bd962431d329f6a9b`, размер 1583. Реальные 5 start offsets `[3,208,597,986,1375]` по `CR\\nCO\\n`, размер каждого блока `[205,389,389,389,208]`, в каждом ровно 2 `RS\\n`, сборка сохраняет все байты. Подтверждено в локальном Python.

Исправлен проектный `BGX120_ENTANGLE_GUARD.py`: BCS parsing по `re.finditer(rb"(?:^|\\n)(CR\\nCO\\n)", raw)`, строго 5 блоков, двойной RS, полный lossless roundtrip. Дополнительная **строгая защита**: native WeiDU recompilation старого PRIEST1 должна дать каждый блок идентично исходному `PRIEST1.BCS`, а кандидат должен сохранить побайтно блоки 0,1,3,4; только index2 Entangle вправе измениться. При любой другой модификации native preflight STOP и никакого патча.

Релиз `0.3.47-BGX120-PARTY-AOE` выложен в GitHub через старый штатный канал `bg-eet-ai` и закреплён в `BOOTSTRAP_PIN.json`: source ref `1317995803b2b344d2c3ffff915b462c428523d3`, exact `BGXAI_SYNC.ps1` SHA256 `f0a8b82a90e07892b6eec8c53a3d7d616c63213cb925cccc54a224a051cce7a5`, size 79959, меню 1–120. 8/8 file manifest SHA; Windows synthetic/unit test PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44134762577; Windows PS 5.1 onefile pin menu, 66/66 source SHA PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44135005604. **Физический `BGXAI_UPDATE.cmd` не менялся**, не требовать его ручной замены.

**Рекомендованное следующее безопасное действие пользователя:** не повторять install сразу. Запустить тот же `BGXAI_UPDATE.cmd`, пункт 120 → **2 = preflight READ ONLY**; в начале убедиться `BGXAI: verified pinned script 1317995803b2 (SHA256 OK)`. Если `BGX120_NATIVE_PREFLIGHT_PASS`, можно затем отдельно сознательно разрешить mode=3 install с точным токеном, при закрытой игре/InfinityLoader/WeiDU; если снова STOP — прислать вывод и не повторять. **На пользовательской EET исправленный native compiler ещё не проверен; runtime install 120 по-прежнему отсутствует.**


## BGX120 РЕАЛЬНО УСТАНОВЛЕН: INSTALLED_VERIFIED

Пользователь успешно выполнил из единого `BGXAI_UPDATE.cmd` пункт **120**, затем внутренний пункт **3=install** и точное подтверждение `INSTALL_BGX120_PARTY_ENTANGLE_GUARD`. Пользователь предоставил фактический JSON-отчёт реальной установки:

```json
{
  "status": "BGX120_INSTALLED_VERIFIED",
  "backup": "C:\\Users\\Drevo\\Documents\\BGXAI120_SAFE_BACKUPS\\PRE_INSTALL_20261117T172236501946Z",
  "after": {
    "bcs_sha256": "cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a",
    "lua_sha256": "74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c",
    "status": "BGX120_INSTALLED_VERIFIED",
    "priest1_sha256": "e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a",
    "BGXP5_untouched": true
  }
}
```

Финальный однострочный результат `BGXAI: update/status action completed.` **После предшествовавшего STOP** попытка с релизом `0.3.47` прошла native compilation/WeiDU install/checks с правильными хэшами. BGXP5 **не изменился**: class BCS `BDDEFAI.BCS` и Lua `M_BX43.lua` соответствуют baseline. `PRIEST1.BCS` теперь `e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a`. Резервная копия сохранена с SHA во внешней папке. **BGX120 установлен как последний WeiDU-компонент**, статус verified; игровой бой после успешной установки пока пользователь не тестировал.

Важное ограничение политики: `!InParty(Myself)` в Entangle-блоке PRIEST1 консервативно **запрещает всё автоматическое применение Entangle у членов партии через PRIEST1**, а не выбирает безопасную точку. Ручное применение и враги не затрагиваются этим условием. Не считать поддержку всех массовых заклинаний готовой — это следующий этап после боевого теста.

**Следующее действие:** загрузить его новое quicksave после перехода из города (в нём у Джахейры назначен race PRIEST1), выполнить один бой с общим ИИ и наблюдать: Джахейра не применяет Entangle автоматически; Жаган всё ещё лечит. Не использовать старую копию `NO_PRIEST1` для теста. Обязательно сохранить исходный быстрый сейв и не менять `BGXAI_UPDATE.cmd`. Не повторять инсталляцию BGX120: она уже verified, повторная установка не нужна. Если пользователь сообщает нарушение, запрашивать боевой журнал/скриншот и вести адресную диагностику. Пользователь пожелал дальнейшее расширение **общего AOE safety rule** на аналогичные массовые заклинания только после успешного боевого теста Entangle; не ставить без отдельного согласия.


## Фактический боевой тест после BGX120: слишком строгий запрет, не умная геометрия

18.11.2026 пользователь прислал реальный скриншот `image(20261117-172633).png` из EET BG v2.6.6.0 после успешного `BGX120_INSTALLED_VERIFIED`; в боевом журнале (Тарана, Джахейра, Больной гибберлинг) **автоматическое Entangle Джахейрой не применяется**. Дополнительное явное наблюдение: «не кидает но когда в поле зрения нет союзников тоже не кидает».

Причина не баг исполнения: в BGX120 добавлен `!InParty(Myself)` в 3-й блок `PRIEST1.BCS`; для Джахейры в составе партии условие ВСЕГДА ложно, независимое от LOS, дистанции/позиций всех других союзников. Поэтому BGX120 — 100% запрет **автокаста** для членов партии, а не умная AoE проверка. Не утверждать, что он уже выбирает безопасные цели или что «Entangle полностью починен».

Нужен следующий этап **BGX121+ AOE spatial guard**: реальная текущая цель `NearestEnemyOf(Myself)` должна определяться штатным движком, а проверка безопасности оценивать расстояния от **центра эффекта возле цели** до всех пяти других членов партии и других союзников/призывов на той же локации. Границы AoE брать из `SPPR105.SPL` **именно пользовательской мод-сборки**, не подставлять без проверки 15' из vanilla: документация расходится с модами/описаниями. Также резерв по движению цели/союзников во время чтения заклинания, иммунитеты не предполагать.

Подтверждённые API EEex (Bubb13/EEex master, не проверены на установленной конкретной версии): `EEex_LuaTrigger("return ...")` в BAF; EEex Lua globals `EEex_LuaTriggerActorID`; `EEex_GameObject_Get(actorID)`; `EEex_Object_EvalStringAsAIBase("NearestEnemyOf(Myself)", caster)`; `EEex_Sprite_GetInPortrait(index)`; sprites `m_pos.x/y` и `m_pArea`; CGameArea functions. **Важно:** найден код EEex `EEex_Area_ForAllOfTypeInRange` с `bCheckForLineOfSight or 1` в Lua, так что переданное `false` может некорректно превращаться в `1` (Lua false or 1), и такой вызов **не гарантирует обнаружение скрытых союзников**. Не считать 121 готовым, пока не доказан безопасный обход всех союзников (вкл. summons) без LOS и не пройдены EET native+EEex smoke tests. Не снимать установленную BGX120 защиту и не выпускать рискованный патч.

Пользователь просил ранее распространить такую умную защиту на другие AoE заклинания только после успешного исходного теста и сохранения BGXP5 лечения. Следует сохранить один постоянный `BGXAI_UPDATE.cmd`.


## Дополнение от пользователя: удерживать дистанцию и использовать дальнобой вместо входа в опасную область

Пользователь продолжил ранее оборванную фразу «если дебаф висит на области, остальным туда лучше не идти, а испо…» отдельным словом **«дальнабой»**, то есть правильная тактика: если поле боя покрыто своей или вражеской опасной областью (Entangle, Web, Stinking Cloud и др.) и союзник не имеет доказанного иммунитета, **не вбегать в область ради ближней атаки**. Вместо этого **переключиться на дальнобой** — лук/арбалет/праща/метательное оружие или дальняя магия, если эффект применим и линия стрельбы/дальность позволяют; атаковать цели из-за границы зоны, соблюдать безопасное расстояние. Если дальнобой невозможен, не давать MoveToObject/Attack() принудительно завести персонажа в опасную зону: выбрать другую цель, безопасную позицию, удерживать точку, дождаться окончания эффекта, либо безопасно отступить. Воины могут переключаться на дальний слот, но учитывать ограничения экипировки, боеприпасы, скорость смены оружия и не прерывать важные действия; лучшая безопасная тактика определяется текущим состоянием персонажа. Имеющие **подтверждённый иммунитет к каждому вредному компоненту** эффекта (в т.ч. духов/призывы, артефакты, бафы) могут пересекать область, **не считать иммунитет по одному названию класса или существу**. При неполных/неизвестных данных стратегия консервативная. Учитывать опасные области и при построении пути к лечебным/охранным целям, не только при атаке. Не ломать лечение Жагана в BGXP5, которое пользователь лично подтвердил как рабочее.
 
Это **требование к будущему источнику BGX121+**, не функциональность текущего BGX120; пока выполнен лишь статичный безопасный запрет party auto Entangle. Пользователь просил продолжить разработку автономного ИИ с общим AoE safety rule; **не объявлять что дальнобой реализован, пока не есть native EET/EEex runtime проверка**. Сохранить один постоянный BGXAI_UPDATE.cmd.


## BGXAI 121: source-only spatial AOE, true spell resource audit, existing permanent CMD

На команду пользователя «дальше?» добавлен настоящий пункт **121** в прежний единственный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, без изменения самого физического CMD. Источник pin `BGXAI/fox_new/BOOTSTRAP_PIN.json` закреплён на коммите `da524462ed67588af1713b288e078058c4a1f567`, `BGXAI_SYNC.ps1` SHA256 `19bded329678c46424c51647ef252f0f6506b3d7ed08e6b5d0a66f5c247d047b` (79922 байт, ≤80000). Pin update commit `2cb0e7c1db2584c819ff6a8dcdcda058a114a8b2`. Версия SHA-pinned 11-file package `0.3.48-BGX121-SPATIAL-READONLY`. Старое menu 1–120 сохранено, 121 новое.

`BGX121_READONLY.py` (menu 121): real installed BGX120 and BGXP5 hash checks through `BGX120_ENTANGLE_GUARD.installed()`, actual installed `PRIEST1.BCS` SHA `e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a`, BGXP5 BCS/Lua unchanged. Read-only dynamic extraction of `SPPR105.SPL` Entangle, `SPWI215.SPL` Web, `SPWI213.SPL` Stinking Cloud and `SPWI502.SPL` Cloudkill from override or game chitin BIFF using TEMP copied WeiDU. Parses actual V1 SPL header/ext effect block data, projectile ID `PROJECTL.IDS - 1`, targeting, effects/opcodes/duration etc, writes outside game ZIP `Documents\BGXAI_LIVE_REPORTS\BGXAI_SEND_AOE121_*.zip` with raw SPL and JSON. **Does NOT infer projectile radius from SPL**; needs resource PRO. Handles missing source/errors individually, continues remaining. No script install or game changes.

`BGX121_POLICY.py` SOURCE ONLY pure deterministic model: party+summon complete roster fail-closed, per-harmful-effect demonstrated immunity only, perspective y×4/3 radius+48px safety, segment-vs-ellipse route intersection, ranged weapon→ranged magic→safe movement→hold, defer urgent healing to BGXP5. Fully tested unit input (not wired to EEex runtime); do not claim real AI can now cast safely or switch weapons. Additional `test_121.py` 16 unit tests.

Tests: Windows 11/11 package source SHA, Python AST and unit mock **PASS** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44141703917. Windows PS5.1 AST, pin, immutable updater menu 1–121 + 69/69 source SHA **PASS** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44141896647. All these are offline CI; no user's live EET yet tested. Existing BGX120 and BGXP5 **left installed and unchanged**.

**User next action:** launch SAME permanent `BGXAI_UPDATE.cmd`, choose **121**, send resulting `BGXAI_SEND_AOE121_*.zip` from Documents\BGXAI_LIVE_REPORTS. This is ONE read-only run, no install confirmation, no new CMD, no game tests. If `121 STOP`, send exact stdout and do not retry. Next phase must infer actual modded projectile radius from PRO and compare full EEex runtime ally roster/immunity and actual beam/summons before active guarded cast and active ranged movement. **Never silently install or modify** when only read-only data validated.


## Пункт 121 реально выполнен: полный READONLY PASS, четыре modded SPL

18.11.2026 пользователь прислал **реальный** `BGXAI_SEND_AOE121_20261117T180504545606Z.zip` (archive SHA256 `770ea1a9e6cf7511f78b7d2cf05421d91c488768e09881760f87580b099fa002`, 2659 bytes, ZIP test OK). ZIP полностью прочитан: `AOE121_REPORT.json` плюс 4 оригинальных SPL. `status=BGX121_READONLY_PASS`, `game_modified=false`, `valid_spell_resources=4`; `geometry_policy.status=BGX121_POLICY_SELFTEST_PASS`. Подтверждены живые контрольные SHA BGXP5 BCS `cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a`, Lua `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`, новый PRIEST1 `e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a`. Лечение Жагана пользователем уже подтверждено как работающее.

**ПОДЛИННЫЕ модифицированные ресурсы EET** — все из `override`, а не из стандартных игровых ресурсов:
- Entangle `SPPR105.SPL` SHA `1835ff5051cd21c576c2b19233a7392d31d4fcda4fa89620c083d078d2cc2b84`, размер 922, spell level1, projectile encoded **243**, PROJECTL.IDS index **242**, cast time4, range120, 14 extended effects including opcode 324×8 and 177? Основные ops 324×8, 126, 0, 174×2, 154, 142.
- Web `SPWI215.SPL` SHA `5fcf361c566db8d2070a882f54defc58c565b8fa2fd51846712cc111b487feed`, 826 bytes, level2, projectile encoded **64**, PROJECTL.IDS index **63**, cast time2, range40, 14 effects including 324×8, 157,109,174,142,139,177 with `dw#clweb`.
- Stinking Cloud `SPWI213.SPL` SHA `c1da0ff730457196d4263de67c3de0988bebf772d59126b0df2466766e0de91d`, 346 bytes, level2, projectile encoded **95**, PROJECTL.IDS index **94**, cast time2, range40, 4 effects 39,328,142,177 with `dw#stink`.
- Cloudkill `SPWI502.SPL` SHA `17f627732b0ede9f22574f5e5654881009147e5811b889ffcc0c6f0072eb0ce4`, 442 bytes, level5, projectile encoded **187**, PROJECTL.IDS index **186**, cast time5, range40, 6 effects 324×2,12,55×2,177 with `dw#cldki`.

**На что обращать внимание:** SPL projectile number не радиус. Для реального эффекта требуется read-only получить `PROJECTL.IDS` из игры и сопоставить точные resref файлов `.PRO` для индексов 242/63/94/186; `PRO V1.0` radius at offset `0x206` для area type3, но некоторые projectile имеют специальные прямоугольные/лучевые/периодические/вторичные эффекты, их нельзя аппроксимировать просто кругом. Нужно также прочесть `dw#clweb`, `dw#stink`, `dw#cldki` subspells/op177, и проверить опасные составляющие на реальные иммунитеты. Документация IESDP: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/pro_v1.htm и https://gibberlings3.github.io/iesdp/files/ids/bgee/projectl.htm. Не заменять подтверждённую SPL-геометрию ванильными значениями. Не снимать BGX120 без безопасности, пока 121 чисто READ ONLY.

Следующий этап: **BGX122 read-only projectile/PRO+IDS** и достоверный spatial immunity assessment, только потом активная безопасная магия и дистанционный бой, не трогая BGXP5 лечение. Пользователю **не нужен новый CMD**.


## BGXAI122 создан, подтверждённые four PRO + opcode177 EFF read-only audit в одном CMD

Пользователь спросил «и?» после получения отчёта 121. Создан, опубликован и CI проверен **следующий пункт 122** в прежнем *единственном постоянном* `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, физический CMD не меняли. GitHub source `BGXAI/patchsets/aoe_entangle_readonly_onefile_20261117/BGX122_PROJECTILES_READONLY.py` + `test_122.py`, пакет `0.3.49-BGX122-PRO-EFF-READONLY` (13 exact SHA), source commits `1b0c8e8e547b06e98be07016fddd358f36b7e596`, `847fe8e25985a8c25531582ddb81c1f2e52603dd`. Последний `BOOTSTRAP_PIN.json` commit `7a653e032cf99f9e641a01feba6e9a0b7028c44f` закрепил `BGXAI_SYNC.ps1` ref `4f4b6ad2d559a78dda84b1e4ac6deb317666ac91`, SHA256 `493b81d56921b8a0a64fa93b32b2411094621b7f871f5cb675cf8afcf47a3ebc`, size 79860, menu 1–122.

122 **только читает данные** установленной сборки: сначала проверяет `BGX120_INSTALLED_VERIFIED`, BGXP5 BCS/Lua SHA и PRIEST1 SHA. Сравнивает 4 локальных SPL с SHA, полученными непосредственно из оригинального user ZIP 121. Читает локальный `PROJECTL.IDS` (override/root/BIFF), определяет точный resref по индексам **242/63/94/186** (ни один веб label не предполагается), через копию WeiDU в TEMP извлекает соответствующие `.PRO`. Формат PRO V1.0, type at 0x8, для AoE type3 flags 0x200, trap radius 0x204, explosion size 0x206, explosion frequency 0x210, secondary projectile 0x214, repeat 0x216, explosion projectile 0x21a, cone 0x224. Пока НЕ утверждать, что это простой круг для всех PRO; повторяемые, лучевые, линейные формы имеют другую геометрию и обрабатываются позже. **Важно, было исправлено**: `dw#clweb`, `dw#stink`, `dw#cldki` — это внешние **EFF через opcode 177**, а НЕ «subspell SPL»; 122 извлекает их как `.EFF`, записывает opcode и параметры. Вывод **снаружи игры** `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_SEND_PRO122_<timestamp>.zip`: `AOE122_REPORT.json`, реальные SPL/IDS/PRO/EFF; при невозможности извлечь что-то формирует PARTIAL + ошибки и всё равно сохраняет ZIP.

Windows тесты Python/unit 13/13 package exact SHA **PASS** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44147219309; Windows PowerShell5.1 AST, immutable pin, menu 1–122, 71/71 SHA **PASS** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/44147405200. Старые пункты 1–121 сохранили логику; частично укорочены только информационные Write-Host сообщения ради лимита pinned sync.ps1 до 80000 байт. **На пользовательском ПК 122 ещё не запускался** — успешны лишь CI-тесты. Установленные BGXP5, BGX120, Lua, WeiDU, saves живой игры не изменялись.

**Следующий шаг пользователю:** запустить **тот же** `BGXAI_UPDATE.cmd`, выбрать `122 - Read real EET projectile areas and EFF (READ ONLY)`, прислать `BGXAI_SEND_PRO122_*.zip` из `Документы\BGXAI_LIVE_REPORTS`. Если 122 выдаст `BGX122_STOP` — не повторять, прислать текст; если PARTIAL — всё равно прислать ZIP. Это read-only, без installer opt-in. После отчёта изучить PRO shapes и EFF immunities, только затем готовить осторожный runtime EEex pathing/AoE/дальнобой. Не снимать установленный BGX120 без подтверждённой безопасной замены. Жаган лечит нормально — приоритет сохранить.
