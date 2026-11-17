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
