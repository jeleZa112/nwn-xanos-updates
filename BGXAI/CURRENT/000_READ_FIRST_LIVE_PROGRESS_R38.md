# 27.11.2026 — R39 HOLD, КОРЕНЬ ПОДТВЕРЖДЁН: НЕСОГЛАСОВАННЫЙ РАЗМЕР В ЦЕПОЧКЕ ПИНОВ

**Последняя доказанная стадия, после пользовательского `a4246f50f8d3 → 176 → 7`.** Тот же `HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:Hold,Hold,Hold` произошёл до запуска R39; `gameplayFeatureInstalled=false`, `ordersSent=0`, `newGameFilesWrittenByThisRunner=0`. Не перепроверять сеть, R38, старый V3 native или лук→меч. Эти функции отдельно не затронуты.

**Точная ошибка предыдущих ассистентских выпусков:** wrapper `BGXAI_XEQUIP_ONEFILE_175_RO_V1.py` из immutable `a4246f50f8d31b46459f77ae15c46a8342851994` объявлял `R39_SOURCES={R39_ONEFILE:(7751,"faf248...")}`, однако фактический `BGXAI_R39_ONEFILE177_RO.py` в ТОМ ЖЕ commit имел **8777 байт** и ТОТ ЖЕ верный SHA256 `faf248d97d04a12ba3c78cfea1b8c573f76a7902de04b758c481ad1b17ecae5d`. Поэтому `verify_file()` законно выдавал `HOLD_PINNED_SOURCE_SHA256_OR_SIZE_DRIFT` на всех зеркалах; агрегатор скрывал реальный код за `Hold,Hold,Hold`. Все предыдущие `7/7 individual SHA PASS` были недостаточны: они **не проверяли transitive cross-file pin length**. Выпуск с этим дефектом был ошибкой разработки. Не требовать у пользователя повторить старый релиз.

**Единственная новая дельта кода:** в wrapper `R39_SOURCES` **7751→8777**, SHA child не изменялся, сам child/native adapter/BAF, R38/V6/R29, WeiDU и игровой root без изменений. Wrapper остаётся 21120B, новый SHA `b548189a81d1a48b87951886931c025c5e5f478c4d612c632e5fb8b1713b4fdb`; основной `BGXAI_SYNC.ps1` изменил только SHA-пин wrapper и остался **79996B**, новый SHA `d1746b78b6fb1d050a1cec6734395960f376e5e7c29772a5a8e8e8c81c960023`.

**Новая доказательная проверка:** до релиза отдельной процедурой GitHub fetch по неизменяемому commit верифицирована ВСЯ цепочка `PS1 79996B→wrapper 21120B→R39 child 8777B→native adapter 12458B, BAF 2303B, V3 wrapper 10743B, compiler backend 9551B`: каждому родительскому `(size,SHA)` соответствует реальный файл, все 6 cross-pin checks **PASS**. Это сильнее прежнего SHA каждого файла отдельно. Native R39 на пользовательской Windows всё ещё НЕ запускался; live item transfer тоже НЕТ. Не говорить «релиз испытан в Windows», CI Windows/Linux не подтверждён.

**Выпуск в единственном user updater:** `BGXAI/fox_new/BOOTSTRAP_PIN.json` теперь закрепляет `bec4e774521129430a5ae204b94e434ef5555de1`, опубликован коммитом `4fdd658c3256a59e4f1492fee8bdce791198ef7e`. Ожидаемая строка загрузчика при следующем запуске: `BGXAI: verified pinned script bec4e7745211 (SHA256 OK)`. **Не давить на пользователя с новым запуском**: после трёх ошибок признать ущерб времени; при продолжении рабочий этап read-only native R39 только один запуск `176→7`, без установки/ARM. При следующем HOLD точно искать новый конкретный код; не выпускать ещё одну сомнительную версию и не просить повторов.

**Реальный основной план:** рабочая часть V6/R29 (лук→меч) была уже ранее испытана; новая функциональность R39 (поднять STAF01 из рюкзака в слот) остаётся **SOURCE/TEST_ONLY**, никакого эффекта в игре, потому что инсталляция/actor binding/безопасность EPS не пройдены. Следующая ценность — один controlled live dispatch после всех условий безопасности, не продолжать бесконечные отчёты.

---

# 27.11.2026 — R39 HOLD_ITEM RACE/CLASS РАЗДЕЛЁН; НАТИВНЫЙ КОМПИЛЯТОР БОЛЬШЕ НЕ БЛОКИРУЕТСЯ ЭТИМ HOLD

**САМАЯ НОВАЯ КОНТРОЛЬНАЯ ТОЧКА.** Пользователь реально выполнил **176→7**, выпуск `e804a34aacf36236c0429d80032fd041b37c4ab4`. Получен `HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY`, `innerReport.reason=HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED`, `nativeWeiDUCompileVerified=false`, `gameModified=false`, `installed=false`, `ordersSent=0`. Частный отчёт `BGXAI_R39_NATIVE177_20261127T125635705524Z.json`. **Это не нативный BAF compile FAIL и не свидетельство запрета Джагану: код остановился раньше запуска WeiDU.**

**Корневая причина:** `static_item_preflight` ранее отвергал `raw[0x21] != 0` как расовый запрет. По **официальному IESDP ITM V1.0**, usability byte4 в `0x21` содержит как расы (bits 0-4,7 = `0x9f`), так и запреты **MONK=bit5, DRUID/SHAMAN=bit6 (`0x60`)**; без учета фактической расы Джагана нельзя делать вывод по битам 0-4,7. Дополнительно **ELF** находится в `0x20 bit7`. Теперь проверяются только настоящие расовые биты `raw[0x21]&0x9f` и `raw[0x20]&0x80`. MONK/DRUID не блокируют ранее наблюдаемого trueclass CLERIC; все реальные неизвестные расы остаются HOLD. Произвольный обход race/kit/usability запрещён.
- IESDP: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/itm_v1.htm#Header_Usability ; CRE race 0x272: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm . Предыдущий R38 не снимал raceRaw, нельзя предполагать её по имени персонажа.
- **Вторая функциональная поправка:** плохой порядок проверок раньше приводил к `HOLD_ITM_...` **до** безопасной TEMP-native компиляции, из-за чего пользователь рисковал повторять 176→7 без нового результата. Теперь статическая **ITM suitability** и native **BAF syntax compile** проверяются независимо. При реальном race/alignment/class/kit/level usability HOLD (и только известном типе ограничения) скрипт может **довести read-only нативный WeiDU до конца** и выдать `R39_NATIVE_EET_TEMP_COMPILE_PASS_ITEM_HOLD_NO_INSTALL`; внешний отчёт `R39_NATIVE_TEMP_PASS_ITEM_USABILITY_HOLD_NO_INSTALL`, `nativeWeiDUCompileVerified=true`, `itemStaticHeaderVerified=false`, returncode 3. При неверном SHA/небезопасном файле компиляция всё так же стоп. Если native FAIL, `nativeWeiDUCompileVerified=false` — никакого ложного PASS.
- **Локальный прогон 41/41 PASS**: 25 Python static/native adapter + 16 nested helper, в т.ч. race bits+ELF, MONK+DRUID, compiler proof after item HOLD, reject broken native and resource SHA drift. CI Github Actions не подтверждён, REAL EET compile в этом выпуске НЕ исполнялся.
- **Immutable pinned release** `BGXAI/fox_new/BOOTSTRAP_PIN.json` опубликован коммитом `b0cfa99d04859d08b533f541a55abcc9dc4be8d6`, указывает на `a4246f50f8d31b46459f77ae15c46a8342851994`: `BGXAI_SYNC.ps1` 79996B SHA `b84ca58e1637aff439691b6afd0b40b1576c625fd3c382a1baf353d58ff50a5b`; 176 helper 21120B SHA `f18dccd27a2f707f57f570febda3b3cfaed691777a2d5c6df027c6f49b72d096`; read-only R39 child 8777B SHA `faf248d97d04a12ba3c78cfea1b8c573f76a7902de04b758c481ad1b17ecae5d`; native adapter 12458B SHA `c07b486f6ba68899d023f2ee9bfc4587ad2b5f79b9630f7f8321d494bc5f07be`; R39 BAF unchanged 2303B SHA `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`. **7/7 exact bytes+SHA** from immutable commit and invariant checks PASS. One updater only, previous menu unchanged, game untouched.
- **Следующий ровно один шаг пользователя** только после обновлённого bootstrap: закрыть BG/InfinityLoader; запустить существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; проверить строку `verified pinned script a4246f50f8d3 (SHA256 OK)`; `176` → `7`. Передать только новый `BGXAI_R39_NATIVE177_*.json` либо точный консольный STOP. **Если пин не a4246f50f8d3 — не продолжать**. Даже если получен item HOLD, при `nativeWeiDUCompileVerified=true` НЕ просить повторять компиляцию — перейти к недостающей проверке конкретной расы/кита. `gameModified=false`, `ordersSent=0`, `installed=false`.
- **До actual item transfer** всё ещё требуется session-bound ARM, EEex load/callback ordering, actor race/kit/active effects and manual/EPS safe action proof, typed guarded last-only WeiDU install/rollback+backup; не заявлять working autoequip.

---

# 27.11.2026 — R39 176→7 УСТРАНЁН PINNED SOURCE HOLD; НУЖЕН ОДИН НОВЫЙ READ-ONLY ЗАПУСК

**Фактический результат пользователя:** прежний immutable release `dc80f56b000978b63b4fa2562ba5f741f77ca067`, единственный `BGXAI_UPDATE.cmd` → `176` → `7`, завершился `BGXAI_R38_ONEFILE_LOADER_HOLD_V1`, `R38_SOURCE_STAGE_HOLD`, `HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:Hold,Hold,Hold`, `ordersSent=0`, `newGameFilesWrittenByThisRunner=0`. Запускать заново прежний пин/175/176→1 **нельзя**: это подтверждённая ошибка самой новой ветки, не отсутствие игры и не сетевой таймаут.

**Корень и исправление:** в `BGXAI_XEQUIP_ONEFILE_175_RO_V1.py` новый `R39_ONEFILE` был включён в allowlist скачивания и `stage_sources`, но **`verify_file()` оставался `SOURCES or V3_SOURCES or R38_SOURCES`**. В результате даже SHA-корректный R39 источник отвергался как `HOLD_SOURCE_NOT_ALLOWLISTED` на RAW/CDN/fastly, затем причина усреднялась до `Hold,Hold,Hold`. Исправлен **ровно один источник**: `... or R39_SOURCES.get(path)` в `verify_file`; никаких изменений R39 BAF/R38/V6/EPS/installer/GUI нет. До следующей публикации **уже существовавший** `test_176_option7_ro.py` имел тесты `test_12_file_guard_r39_only` и `test_07_onefile_stages_exact_177_helper_without_game_write`, которые могли обнаружить дефект; к прошлому релизу их результат реально НЕ был подтверждён. Не утверждать, что GitHub CI PASS.

**НОВЫЙ VERIFIED immutable-release:** `BGXAI/fox_new/BOOTSTRAP_PIN.json` теперь закрепляет `e804a34aacf36236c0429d80032fd041b37c4ab4`, `BGXAI_SYNC.ps1` 79996B SHA256 `a58deddc595bbd07e176d9977f78b6d22dd85dd00d377608377a77c51482edb3`, Python wrapper 21120B SHA256 `c25458d7086e56e8436d432c106fb82254ab34e751188dd0270e430d672d962f`. Повторно verified **все 7/7 файлов SHA+size** из immutable commit и статическая проверка allowlist/176→7/старых R38 modes; GAME CODE/INSTALL не затронуты. `BOOTSTRAP_PIN.json` publication commit `c59aae153a423321a77f019dffda092b811d8854`. Нет подтверждённых GitHub Actions/Windows CI результатов и **нативная R39 компиляция на машине всё ещё НЕ запускалась**.

**Один следующий шаг пользователя (только новый доказательственный пробел):** игра и InfinityLoader закрыты → тот же `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → `176` → `7`. Должно сначала показать `verified pinned script e804a34aacf3 (SHA256 OK)`; если **старый** `dc80f56b0009` — НЕ ПРОДОЛЖАТЬ, прислать строку пина. При успешном завершении отправить только **новый** `BGXAI_R39_NATIVE177_*.json` из `Documents\BGXAI_LIVE_REPORTS`, при HOLD — текст консоли без повторных старых отчётов. Пункт 7 не устанавливает, не ARM и не отдаёт команды: `ordersSent=0`. После native PASS отдельно продолжать session/kit/OPS provenance + typed guarded deploy, **никакого game install в этом шаге**.

---

# 27.11.2026 — R39 READ-ONLY NATIVE РЕЛИЗ ДОСТУПЕН ЧЕРЕЗ СТАРОЕ МЕНЮ 176 → 7

**Самая новая стадия BGXAI.** Сохранён один пользовательский `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; новое только в существующем меню **176, дополнительная опция 7**. Это первый read-only **нативный EET preflight точно действующего R39 BAF** + отдельная проверка class/trueclass header настоящего `STAF01.ITM`. Старые 175, 176→1–6 и R38 passive in-game сохраняются. **НЕ** выполнена native компиляция новой R39 на пользовательской EET; выполнять её может только пользовательский 176→7. **НЕТ установки, ARM, приказов или модификации игры**.

## Реальный immutable-release proof (не путать CI, DEPLOY и LIVE)
- Актуальный GitHub branch `bg-eet-ai`; `BGXAI/fox_new/BOOTSTRAP_PIN.json` опубликован коммитом `19e3e43c2f2c666270799ca56f9e71dbe312c9ac`.
- Pin commit загрузчика = `dc80f56b000978b63b4fa2562ba5f741f77ca067` (immutable); ровно **79 996 байт** `BGXAI/BGXAI_SYNC.ps1`, SHA256 `b3e006881ada7ced612dd3a126783abdbe4e03c178a52996ee57a4da7a3760e6`; проверены bytes/hash **из указанного immutable commit**, а не только branch HEAD. **Единственное семантическое изменение PS1**: размер и SHA для штатно скачиваемого Python helper 175/176, прежние пункты PowerShell меню не переписывались.
- Новый Python helper `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py`: 21095 B SHA `c7ae980b2acca6bbe819260e044ff9369ccc40ddc5757fe6b6ec5526f1886eb5`; прежние функции 175/V3/R38 оставлены, новая *opt-in* опция `7=R39 native RO` внутри 176.
- Вспомогательный `BGXAI_R39_ONEFILE177_RO.py` называется 177 **только исторически внутри Python**, НЕ отдельный пользовательский пункт 177 или CMD. 7751B SHA `98bc0bba78638a62117b8e1ee3a43ace8638bca1a9bf140be8ea8b714deca0c6`. Он в TEMP скачивает SHA-pinned, source allowlist `R39 native adapter` 10526B SHA `a2ad31e79f61d89e2a03db9a237b0031cb76bfa6c5e8d1028d14c42624a18028`, BAF 2303B SHA `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`, уже native-PASS V3 helper 10743B и backend 9551B. **Все 7 исходников сверены по неизменяемому commit по SHA/size, PASS**. Никаких post-commit source updates в pin не было.
- Существующие локальные Python: 14/14 onefile nested helper, 20/20 R39 native/ITM adapter tests (в сумме с ранее 22 R39 BAF, 19 R38-R3 evidence и 12 option7 source tests; **12 option7 tests написаны, но динамически в этом Linux окружении не исполнены**, потому что полный wrapper импортируется в GitHub CI). Для Win/Linux workflow `.github/workflows/bgxai_r39_staged_xequip_source_ci.yml` выпущен. **GitHub CI result недоступен/не подтверждён** (GitHub fetch_commit_workflow_runs фильтрует PR runs, returned `[]`); НЕ писать CI PASS. 14-point static check on immutable release PASS.
- Установленный `STAF01.ITM` уже R3/R34 authenticated: SHA `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`; новый readonly item parser проверяет ITM V1.0, flags, cleric restricted bit, TRUECLASS bit, и неизвестные race/alignment/другие требования = HOLD. **Не проверяет текущую возможность экипировки в движке** или отрицательные эффекты.
- Только следующий **новый пользовательский safe step**, если нужна native-EET оценка: закрыть BG + InfinityLoader; запустить существующий `BGXAI_UPDATE.cmd` → `176` → `7`. Отправить **один** файл `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R39_NATIVE177_*.json` либо точный текст SAFE STOP. Ничего НЕ устанавливать/не откатывать, не запускать повторно 175, 176→1, 176→6. Признак допустимого native pass: `status=R39_EXACT_NATIVE_AND_ITEM_HEADER_PASS_NO_INSTALL`, `nativeWeiDUCompileVerified=true`, `gameModified=false`, `installed=false`, `ordersSent=0`. Если item HOLD, сначала проверять конкретный restriction и source assumptions, не делать отдельный круг старых отчетов.
- **Следующий после нативного read-only proof**: до active install потребуется отдельная строгая session-bound/actor/kit/action origin arming + подтверждённая native сборка R39 + backup/WeiDU last-only/typed human approval + один disposable-save in-game transfer. До этого `LIVE XEquipItem=NO`, `dispatchAuthorized=false`.

---

# 27.11.2026 — R39 NATIVE АДАПТЕР ПОДГОТОВЛЕН НА ОСНОВЕ УЖЕ ПРОВЕРЕННОГО 176; GAMEPLAY НЕ МЕНЯЛСЯ

**Последняя доказанная стадия.** Не создавать новый компилятор/второй updater. В существующей директории R39 создан `BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py`, который использует прежний успешный V3 menu176 helper (SHA256 `b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e`) и его SHA-проверенный native backend. Вход — **текущий R39 2303-byte BAF** SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`; изменять R39 source без обновления pin нельзя.

- Проведён **source-only** pin-check R39 BAF. Опциональный future `--native-readonly` исполняет Windows WeiDU только во временной внешней папке и при закрытой игре, проверяет watched files и удаление temp; compile не осуществлялся на машине пользователя и в текущем инструментальном окружении. **НЕ** устанавливает BCS/WeiDU и не выставляет ARM.
- Новые **12/12 локальных offline/mock test PASS**, в том числе проверены возвраты PASS/HOLD, pin-drift, mock compile и запрет установки; предыдущие 41/41 тоже PASS, **53/53 всего в R39**. GitHub CI workflow дополнен; его удалённый результат пока не подтверждён.
- Этот адаптер **НЕ подключён** к единственному `BGXAI_UPDATE.cmd`; не просить пользователя запускать новый CMD, PowerShell или отдельный Python. Из-за лимита подписанного `BGXAI_SYNC.ps1` 80000 B не расширять меню без строгого рефакторинга и точного SHA-pinned release/CI. Текущая ранее выпущенная точка 176 уже native V3 PASS, **но не native нового R39**.
- Незакрытый `session-bound ARM` / защита ручной команды и EPS, kit/ITM engine-usability, actual R39 native EET compile и первый disposable-save gameplay transfer остаются HOLD. **INSTALL=false; ORDERS=0; LIVEXEQUIP=false.**
- Продолжить только реальную недостающую дельту: безопасный life-cycle/actor armer + runnable guarded onefile integration, typed install и одно игровое испытание. Старые R3/R34/R38/175/176 результаты не перепроверять. Пользователю действий пока нет.

---

# 27.11.2026 — R39 EVIDENCE-JOIN РЕАЛЬНЫХ ИСТОЧНИКОВ И 4 НАТИВНЫХ БАРЬЕРА

**Это самая новая проверенная стадия BGXAI.** Предыдущие блоки ниже — история. **Цель:** первый XEquipItem в одном контролируемом боевом сохранении, не повторять старые сборы.

1. **Использованы уже имеющиеся реальные источники**, не запрашивая новую игру: частный оригинальный R38 консольный журнал 702973 B (34 события, 10 Джаган, 24 другой актёр) + ранее созданный native-current-game R3 item JSON с `STAF01.ITM` SHA `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`. Реальная сверка **PASS_OBSERVED_STRENGTH_AND_PHYSICAL_SLOTS_USABILITY_UNPROVEN**: один runtime actor у всех 10 совпадений; STR 12 >=5; offhand slot9 пуст; weapon0 slot35 пуст; class raw3, kit raw16384; остальные 24 события строго отсеяны. Исходный журнал, actor IDs, пути **не опубликованы**; опубликованы только обезличенная сводка и проверяющий код.
2. Модуль сохранён **в существующем R39**, без нового отдельного наблюдателя и обновлятора: `BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/R39_JOIN_EXISTING_R38_R3_RO.py` и `R39_EXISTING_EVIDENCE_JOIN_SANITIZED.json`. **19/19 синтетических негативных тестов PASS**, плюс **22/22 исходных R39 = 41/41 PASS локально**. GitHub workflow дополнен этими тестами, но результат удалённого CI ещё не подтверждён.
3. **Существующий R39 BAF исправлен, чтобы физические условия проверялись именно в момент действия:** обе ветви warmup/equip дополнительно имеют `Name("*GCLERIC",Myself)` (сохранённое CRE имя: ещё не runtime-верифицировано), `Class(Myself,CLERIC)`, `CheckStatGT(Myself,4,STR)` и `!HasItemSlot(Myself,SLOT_SHIELD)`. Более ранние `Continue()` в служебных блоках EPS сохранены, команда `XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)` по-прежнему ровно одна. **Текущий точный R39 BAF 2303 байта SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`.** Старый BAF 2079B SHA `7d57cec...` НЕ ИСПОЛЬЗОВАТЬ для будущего pin / native compile.
4. **Честное разделение доказательств:** настоящие снимки подтверждают только прошлые физические слоты/STR, а новые BAF триггеры пока прошли только CODE/OFFLINE. Достоверная kit+ITM usability **НЕ** подтверждена; также НЕ подтверждены текущий session-bound ARM, manual/EPS origin, BAF native compile именно 2303-byte версии, WeiDU install/rollback или реальное перемещение предмета. `gameModified=false`, `ordersSent=0`, `armAuthorized=false`. Не ставить патч и не выдавать его за рабочий без отдельного typed approval и guarded release.
5. **Следующая минимальная дельта:** переиспользуя существующую native компиляцию 176 и R38 install guard, подготовить native+install pipeline **для одного точного BAF** с сохранением EPS, без переписывания переключения V6. Проверить session armer/kit limitations, затем один контролируемый live пилот на расходном сохранении. Никаких повторов R3/R34/R38/175/176 от пользователя ради ранее добытых данных.

---

> **ОБЯЗАТЕЛЬНО ДЛЯ НОВОГО ЧАТА (27.11.2026):** сначала [единая короткая точка восстановления](00_RESUME_CURRENT.md) и [глобальный протокол RESUME-GATE](../../GLOBAL_PROJECT_RULES/GLOBAL_CROSS_CHAT_RESUME_V1_RU.md). Исторические «next» ниже не являются текущей командой. Проверить последний commit, реальные пользовательские отчёты и не повторять выполненное.

# 27.11.2026 — R39 EPS-FIRST ИСПРАВЛЕН, R40 LUA 22/22 ВЫПОЛНЕНЫ

**Последняя доказанная точка; ссылки ниже — история, не список команд для повтора.**

- **Исправлен существующий R39** (никаких новых конкурирующих веток): его 2 служебных BAF-блока `abort expired` и `warmup` ранее останавливали дальнейший просмотр правил EPS на срабатывании. В конце **только этих блоков** теперь `Continue()` (официальная семантика IE: последним действием разрешает проверять последующие блоки). **Активный одноразовый `XEquipItem` не изменён и не Continue.** Это CODE/OFFLINE, не доказанная приоритетность EPS в игре. Точный новый source-only BAF: **2079 байт SHA256 `7d57cecc77988764bff3de41379f71cabf8310b3b97dda91404f42555debd62c`**. Старый 2049B SHA `943c221684dde39662476f0514da48fadad6fc1ce90c565b5732afaa87673be8` архивный, НЕЛЬЗЯ использовать для новых пинов.
- **Точные тесты заново выполнены в доступном окружении**: R39 **21/21** Python; R40 **13/13** Python + **22/22** `texlua test_session_reset_v1.lua`. Не утверждать, что Lua 5.3/5.4/LuaJIT GitHub CI, EET native BAF и gameplay прошли.
- Из предыдущего R34/R3 **уже известен установленный `STAF01.ITM`**: `CURRENT_GAME_OVERRIDE`, SHA256 `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`, itemType 26, flags 46, двуручный посох, min STR 5, отсутствует opcode319 среди пяти записанных equip effects (там opcode7). **Это НЕ доказывает kit/class/effects usability конкретного Джагана**. Не повторять старую R34.
- R38 installed и capture 34/34 остается прежним; V3 native (176) PASS ранее; R39 **в изменённых байтах** native не проверен, не установлен/не ARM; R40 source-only не установлен; `ordersSent=0`. Штатный one-file updater не менялся.
- **Следующий НЕПОВТОРНЫЙ функциональный этап**: точная native compile **2079-byte R39** + проверка actor/session-arming/loaded callback в установленном EEex, item usability kit, guarded release/backup/typed approval. До этого не активировать `XEquipItem`; не требовать старых отчётов.
- IESDP: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm (Continue последним), https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm (ActionListEmpty — мгновенное состояние, не атрибуция).
- Глобальные воспроизводимые записи обновлены **в существующих** `/GLOBAL_PROJECT_RULES/METHOD_BGXAI_R39_TWO_STAGE_TIME_BOUNDED_XEQUIP_CANDIDATE_V1.json` и `METHOD_BGXAI_EEEX117_SESSION_LIFECYCLE_DISARM_BEFORE_BAF_V1.json`; прежние методы не продублированы.

---

> **НОВОЕ ГЛОБАЛЬНОЕ ПРАВИЛО 27.11.2026:** [ОБЯЗАТЕЛЬНЫЙ PRE-WORK GATE — прежде чем создавать очередную версию, проверить прежние решения](00_PRIOR_WORK_GATE_READ_FIRST.md). Любая новая реализация начинается с проверки уже сделанного, доказательств и недостающей дельты. Не повторять подтверждённые тесты.

# 27.11.2026 — ПРОВЕРКА ИСТОРИИ ТЕСТОВ И УДАЛЕНИЕ ДУБЛЕЙ ИЗ ПЛАНА

**Этот блок — главный после позднего пользовательского вопроса «может уже всё проверено?»; исторические "next: repeat" ниже НЕ исполнять.** Перед R39/R40 была пропущена обязательная сверка модулей **071–085**, NONINTERRUPT, ранних игровым тестов и нативного пункта 176. Исправление плана ниже; текущую игру и старые тесты не повторять.

**УЖЕ ДОКАЗАНО / ПОВТОРЯТЬ НЕ НУЖНО:**
- **V3 native EET:** пользовательский `BGXAI_XEQUIP176_V3_RO_20261127T134903503792.json` уже показал `V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL`, BAF SHA `996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1`, BCS SHA `f6b14191fb1b6e9023dfaa9363809876578ffbea72d20c8b172a5a1c96bc3a85`, no install / no game writes. Старый 175 тоже PASS. НОВЫЙ R39 BAF не равен V3: его native compile по-прежнему НЕ подтверждён.
- **R37/R38 LIVE:** R38 установлен с backup; 34/34 согласованных live событий, 10 для одного actor Джагана с `STAF01` slot20 и пустым slot35, 24 штатно отсеяны как другой портрет, no equip/commands. V6 ранее успешно переключал лук→меч (лишние выстрелы снижены до 1), реальный action 105→92→134; не перепроверять. Это **не** доказательство XEquipItem.
- **NONINTERRUPT и выбор оружия:** прежние 22/22 NONINTERRUPT, 36/36 V3, 30/30 V4, 18/18 V5, 4/4 сквозных офлайн-теста (110/110), 439/439 в более широкой матрице. Учитывать тестовую модель, но НЕ объявлять engine idle/manual/EPS proven или приоритетный ранкер развернутым.
- **Очередь/источник действий:** старые `081` (action provenance UNKNOWN), `082` (765/765 fail-closed Lua assertions + 14 Python), `083` (реальные EEex v1.1.7 API + 50 Lua/10 Python/149 integration assertions), `084` (нативный `ActionListEmpty()` и EEex `EvalConditionalStringAsAIBase` по исходникам), `085` (31 BAF игровых правила 061/066S/067 уже содержали ActionListEmpty, F guard и modal). Нельзя снова изобретать пустую очередь, классифицировать `m_curScriptNum` как ручную команду или выдавать таймер R39 за engine idle.
- **Классы и ITM:** старый `071` parsed 15 159 CRE + 240 Lua/9 Python tests, но НЕ даёт текущую usable-by-kit; пользовательский `BGXAI_R34_NATIVE_PROF_20261126T002126164.json` уже извлёк текущий `STAF01.ITM` (`CURRENT_GAME_OVERRIDE`, SHA `c472bdf3...`, quarterstaff, two-handed, min STR 5), `characterCanEquipVerified=false`. Повторный скачивающий/декодирующий R34 не нужен. Ранее BCLAW живой тест показал, что временное магическое оружие может блокировать ручную экипировку.
- **Новая интеграционная проверка 27.11:** старый **085** применён локально к *только source* `BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf`: 3 блока, 1 с действием; **`BAF_STATIC_GATE_REVIEW` на блоке 2**, не game fail. Детали: отсутствует F guard по правилам 061/066S/067, `XEquipItem` не известен 085, имя TTL `BGXW3MAX` и отсутствие on-hit request закономерно не подходят к спецсхеме лечения 085. **085 не является универсальной спецификацией XEquip**: не вводить F guard или on-hit request автоматически, особенно пока F user guard отдельно OFF; подготовить отдельный валидатор типа item-transfer с reuse существующих общих барьеров.

**СОХРАНИТЬ БЕЗ ИНСТАЛЛЯЦИИ:** R39 (20 локальных Python tests, новая двухфазная BAF; native именно R39 не проверена), R40 (13 static PASS, 22 Lua mock cases ещё не доказаны выполнением, loaded/destroyed hooks upstream v1.1.7; callback ordering в сборке пользователя не проверен). Не выдавать их за новые игровые улучшения или пройденный LIVE.

**Реально незакрыто только для первого backpack→weapon пилота:** (1) подтверждение права Джагана использовать нынешний `STAF01` по актуальному kit/эффектам; (2) сохранённый session-bound arm со строгим сбросом и отдельной границей manual/EPS/current-action; (3) native compile **именно будущего активного** BAF + интеграция с уже установленными EPS/BCS; (4) typed approval, SHA/backup/WeiDU last-only, одно игровое испытание на расходном сохранении, контроль сохранения предмета/зарядов. Проверять только эти конкретные пробелы, переиспользуя 071/081–085/R34/R38. **Игра, WeiDU и один updater не менялись при этом историческом аудите.**

---

# 27.11.2026 — R40 EEex LIFECYCLE DISARM SOURCE-ONLY; ИГРА НЕ МЕНЯЛАСЬ

**Самая новая стадия, выше исторических записей ниже.** Реальный R38 установлен/уже захвачен, R39 source-only two-stage XEquipItem готов (20 локальных tests), **R40 source-only** решает узкую проблему *сохранённого actor-local ARM* через callbacks EEex v1.1.7. Исходники и тесты: `BGXAI/BUILD/R40_SESSION_RESET_SOURCEONLY_20261127/`; CI workflow `.github/workflows/bgxai_r40_session_reset_source_ci.yml`.

- Проверено чтением *официального tag* `Bubb13/EEex@v1.1.7`: `EEex_GameState_AddDestroyedListener`, `EEex_Sprite_AddLoadedListener`, `EEex_Sprite_GetLocalInt/SetLocalInt`. Это наличие интерфейса в исходнике, а **не** доказательство порядка callbacks в текущей пользовательской сборке.
- `M_BGXW3_SESSION_RESET_V1.lua` не регистрирует слушателей и не пишет в игру сам по себе. Только после отдельной защищённой явной активации он допускает два lifecycle callbacks, **без второго ActionStarted listener**; при loaded проверяет шесть actor-local полей и сначала обнуляет `BGXW3ARM` с readback, потом другие пять; при destroyed только сбрасывает временный Lua epoch.
- Текущие факты: **13/13 static tests PASS локально**; **22 Lua adversarial tests написаны, но ещё НЕ подтверждены выполнением**, CI запущен публикацией workflow (итог CI пока неизвестен). Не выдавать CI, native compile, DEPLOY или LIVE за PASS.
- **Существенные ограничения:** не доказан callback loaded до первого BAF script tick, нет current-session-only armer / защиты manual-EPS, не проверены actual installed `STAF01.ITM` и текущий kit/usability, R39 native EET BAF не скомпилирован, отдельного typed approval на установку нет. `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Ни один игровой файл или единственный updater не менялся.
- **Никаких действий пользователя сейчас.** Не повторять R38 install/capture, меню175, old V3 и R37; продолжить доказательством order of callbacks + exact installed EEex APIs и ITM/kit из доступного read-only preflight, затем guarded release в существующий единственный `BGXAI_UPDATE.cmd` и единственная typed установка / тест на расходном сохранении.

---

# 27.11.2026 — R39 SOURCE-ONLY: КОД ДВУХФАЗНОГО XEquipItem ГОТОВ, GAMEPLAY НЕ МЕНЯЛСЯ

**Прочитать первым.** После реального R38 capture создан новый *активный по форме, но не установленный и не вооружённый* R39 BAF для одного посоха Джагана: `BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/`. Ветка `bg-eet-ai`. Существующие R37/R38, EPS, V6/R29, единственный `BGXAI_UPDATE.cmd`, WeiDU и сохранения не менялись.

- Три BAF-блока: (1) просроченный arm → отказ, (2) одноразовый `XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)` после второго полного набора проверок, (3) warmup с `ONE_ROUND` и `TWO_ROUNDS`. Исходное окно одноразовое, запрет самоустановки ARM, actor-local TAG прежнего V3. Подлинные GAM slot20→35 и runtime R38 actor identity (10 Jagan событий) не выдумывать и не переизмерять.
- **20/20 локальных Python tests PASS** и SHA exact generated BAF `943c221684dde39662476f0514da48fadad6fc1ce90c565b5732afaa87673be8` (2049 байт); CI workflow `.github/workflows/bgxai_r39_staged_xequip_source_ci.yml` опубликован, исход его запуска **здесь не подтверждён**.
- **Блокеры сохраняются:** ARM в actor LOCALS может пережить сохранение/перезагрузку → необходим независимый *session-bound*, fail-closed аутентификатор и отмена ARM до использования; таймер — cooldown, не доказательство непрерывной idle; manual/EPS origin и установленный `STAF01.ITM` + kit usability не проверены; точный native EET BAF не скомпилирован, backup/install approval не получены. **`dispatchAuthorized=false`, `ordersSent=0`, `installed=false`**, пользователь ничего не запускает.
- **Реальный следующий инженерный шаг:** session-only armer + invalidation через уже существующий R38 one-listener и item usability proof без второго слушателя, затем native compile, guarded install через тот же one-file updater после отдельной typed авторизации, один игровой тест на расходном сохранении. Не повторять R38 install/capture или старые RO проверки.

---

# 27.11.2026 — R38 REAL LOG REPLAY: ДЖАГАН НАЙДЕН, НО ДВИЖЕНИЕ НЕ РАВНО IDLE

**Наивысший приоритет, обновлено после фактического разбора исходного пользовательского журнала.** R38 установлен, предыдущий live capture завершён; НЕ повторять `176→4`/ `176→6`, native V3/175 или R37. Игра в этом исследовании не изменялась.

- Уже полученный приватный `BGXAI_R38_CONSOLE_20261127T081433673320Z.log` прочитан **построчно** (702973 байта). В четырёх каналах выровнены **34 события**; точные идентификаторы актёров и сырой лог не выносятся в публичный GitHub.
- **10** ID совпадений Джагана (`partyIndex=1`) относятся к **одному** runtime actor во всём capture; **24** `HOLD_WRONG_PORTRAIT_CONTEXT` относятся **только** к другому актёру (`partyIndex=2`). Это нормальный fail-closed фильтр, а не повод ещё раз захватывать лог.
- **НОВАЯ РЕАЛЬНАЯ ПРОБЛЕМА ДЛЯ ACTIVE XEquipItem:** у Джагана **5** событий с `actionRaw=23`, что по BG(2)EE IESDP означает **`MoveToPoint`**, в том числе с `queuedActionsRaw=0`; **4** наблюдения с непустой очередью. Нулевая очередь ≠ законченное движение; колбэк ActionStarted ≠ idle.
- **Подготовлен и выполнен на этом подлинном журнале новый SOURCE-ONLY коррелятор, 17/17 локальных негативных/положительных тестов PASS:** `BGXAI/BUILD/R38_REAL_CAPTURE_CONTEXT_GATE_V1_20261127/BGXAI_R38_RUNTIME_GATE_V1.py`, README и тесты в соседней папке; также сохранены в Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_R38_RUNTIME_GATE_V1/`.
- **Результат:** `HOLD_SAFE_IDLE_AND_SESSION_AUTHENTICATION_NOT_PROVEN`; runtime actor совпал в пределах capture, но подлинность сцепления с сохранением, ITM/kit-допустимость, manual/EPS origin и безопасный момент для команды **НЕ доказаны**. `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Ни один установленный Lua/BCS, WeiDU, игра, сохранения и обновлятор не менялись.
- **Строго следующий функциональный шаг:** разработка независимой строгой границы idle/manual/EPS, подтверждения usability ITM/kit именно перед попыткой, затем только отдельное typed-разрешение и одноразовый охраняемый `STAF01` slot20→slot35 пилот на расходном сохранении. **Не удалять существующие защиты и не маркировать ACTION23 как idle.**
- Источник по действию 23: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm. Различать CODE/TEST/DEPLOY/LIVE и не возвращаться к историческим шагам ниже.

---

# 27.11.2026 — НОВЕЙШАЯ КОНТРОЛЬНАЯ ТОЧКА: R38 УЖЕ УСТАНОВЛЕН, CAPTURE ПОЛУЧЕН

**Эта запись приоритетнее ВСЕХ следующих исторических указаний о том, что R38 не установлен или что нужно выполнить 176→4.** В более позднем чате 27.11 пользователь подтвердил успешную установку R38. Предыдущий `R38_PREFLIGHT_PASS_NO_INSTALL` относится к состоянию ДО установки.

- **DEPLOY:** отчёт установки `R38_PASSIVE_INSTALLED_AWAITING_RUNTIME`, создан внешний backup; R38 установлен. Точный итоговый номер компонента WeiDU из недавних данных здесь не установлен, не дописывать его по предположению.
- **REAL CAPTURE:** 34/34 события согласованы во всех четырёх потоках `[BGXR27]/[BGXR37]/[BGXINV3]/[BGXID]`, ошибок формата 0, приказов 0. Статусы `[BGXID]`: 10 × `RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM`, 24 × `HOLD_WRONG_PORTRAIT_CONTEXT`. Джаган и его `STAF01` в рюкзаке наблюдались при пустом целевом оружейном слоте.
- **Важное толкование:** проверка `ID_CORE.capture` ожидает `partyIndex=1`, поэтому `HOLD_WRONG_PORTRAIT_CONTEXT` у событий других актёров **может быть штатным фильтром**, а не багом. Код `BGXAI_R38_GUARDED_FROM_R37.py` выставляет `runtimeActorIdentityVerified=False` безусловно; даже 10 совпадений **не удостоверяют** session/saved-GAM identity.
- **НЕТ РЕЗУЛЬТАТА AUTO-EQUIP:** `XEquipItem` не выполнялся, `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Успешный capture — доказательство наблюдения, а НЕ переноса предмета.
- **Никаких действий пользователя сейчас:** не повторять установку R38, `176→4`, `176→6`, `175`, V3 native, R37 status или R38 preflight. Сначала исправить/дополнить только *реально отсутствующее* доказательство runtime/session actor identity, ITM/class usability и безопасной idle/manual/EPS границы; не удалять защиту портрета на основании одного счётчика HOLD.
- **Следующий функциональный рубеж:** единственная guarded одноразовая попытка `STAF01` из `SLOT_MISC5 (20)` в пустой `SLOT_WEAPON0 (35)` для Джагана на расходном сохранении. Только после проверки вышеперечисленных предпосылок, отдельного typed-согласия на активный патч, SHA + внешнего backup + WeiDU last-only. Рабочие R37/R38, EPS 18.4, V6/R29, сейвы, BG_EET_RU и BG Voice RU сохранять.
- **Единый канал:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; текущий опубликованный bootstrap pin `0a791e1d92aefd70d42d80b5d79b2dac9b3997a0` (это состояние GitHub, не утверждение о локальной загрузке ПК). Не создавать второго обновлятора.

**Правило передачи:** source/CI/native/DEPLOY/LIVE разделять. Если будущая переписка видит ниже `R38 NOT INSTALLED`, это исторический текст, который уже отменён этим блоком.

---

# 27.11.2026 — ИСПРАВЛЕНА РЕАЛЬНАЯ ОШИБКА 176: ENTER → СТАРЫЙ V3 + СБОЙ СЕТИ

**Эта запись приоритетнее старого описания меню ниже. Пользователь уже предоставил все необходимые проверки R37, V3 и R38 preflight. НЕ повтораять их.**

Фактический новый запуск пользователя:
`verified pinned script 35708d0594c8`; `Choice 176`; после приглашения `R38 choice [1]:` нажат **Enter**, поэтому по ошибке запустился старый V3 BAF и завершился `HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:TimeoutError,URLError`. Это сетевой отказ скачивания старых V3-файлов, **не отказ WeiDU, не установка R38 и не повреждение рабочего R37**; `ordersSent=0`, `newGameFilesWrittenByThisRunner=0`.

**ИСПРАВЛЕНИЕ УЖЕ ОПУБЛИКОВАНО:** основной однокомандный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` теперь закреплён на PowerShell commit `0a791e1d92aefd70d42d80b5d79b2dac9b3997a0`, script SHA256 `51822d75ed0644ec10ee28af47141f1c38b40900e5a7409af9c319790037683b`, **79 996 байт**; обработчик 176 SHA256 `c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c`, 19 784 байта. Подменю при **пустом Enter/0 выходит без действий**; `1` — только явная повторная V3 (не нужна); `4` — защищённая установка пассивного R38, внутри неё по-прежнему требуется ручная typed-фраза. Для R38 добавлен **SHA256-проверяемый постоянный кэш** в `%LOCALAPPDATA%\BGXAI_UPDATER\VERIFIED_SOURCES_R38` и третий RAW/CDN hostname `fastly.jsdelivr.net` после raw.githubusercontent.com/cdn.jsdelivr.net. Проверки source + Windows/Linux и PowerShell 5.1: [исправление Enter+cache](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45962206276), [точный staged PowerShell 5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45962342644). **Не заявлять, что текущая сеть на ПК пользователя гарантированно работает:** старые временно скачанные исходники не сохранены, пока после этого выпуска новый кэш не наполнится.

**Следующий реальный шаг, без повторного preflight:** при закрытой игре, если пользователь готов устанавливать пассивный наблюдатель, выполнить `BGXAI_UPDATE.cmd` → `176` → **явно 4** → вручную ввести требуемый токен `INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37`. Ничего не устанавливать автоматически; при STOP/HOLD не повторять. После INSTALL PASS — один реальный capture через `176 → 6`. Пока **R38 NOT INSTALLED** и `XEquipItem` не работает.

**Системная ошибка, которую нельзя повторять:** не создавать дефолт, который вызывает закрытый дорогостоящий тест; не стирать после каждого запуска единственные SHA-проверенные загруженные исходники; не пересоздавать проекты и сотни CI/отчётов вместо изменения игрового поведения. Не запрашивать старые отчёты, 175, native V3 или R38 preflight повторно.

---

# BGXAI — ЕДИНАЯ АКТУАЛЬНАЯ ТОЧКА: ПЕРЕХОД К ИГРОВОМУ РЕЗУЛЬТАТУ

**Дата: 27.11.2026. Прочитать перед любыми действиями с BGXAI.** Этот файл является приоритетным указателем над историческими отчётами, старыми handoff и многостраничными журналами тестирования.

## Последний подтверждённый факт пользователя (НЕ ТРЕБУЕТ ПОВТОРА)

Получен **реальный preflight установленной EET** `BGXAI_R38_PREFLIGHT_20261127T072940349855Z.json`:

- `schema=BGXAI_R38_R37_PASSIVE_IDENTITY_GUARDED_V1`
- **`status=R38_PREFLIGHT_PASS_NO_INSTALL`**
- `weiduComponents=153`, последний компонент R37; `weiDULogSha256=3f838e42236898b63cacb3256e9fff4bcea1b9f2273baba4baff27e8883f4538`.
- Исходник пассивного R38 (R37+INV3+ID) `sourceSha256=958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c`, `sourceBytes=78927`.
- Контрольный R37 в игре `override/M_BGXR27.lua` `SHA256=5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`.
- Контроль `WeiDU.log`, R31/R33/R37 proofs, EEex, EPS, DPLAYER, BDDEFAI, `chitin.key` — без отклонений (см. оригинальный пользовательский JSON, **не публиковать пользовательские папки или приватный сейв**).
- `installed=false`, `typedInstallApproved=false`, `gameModified=false`, `ordersSent=0`, `dispatchAuthorized=false`, `armAuthorized=false`.

**ИТОГ: нативная проверка активного V3 BAF (пункт 176) уже была PASS; R37 status PASS; R38 source + Windows/Linux CI PASS; R38 read-only preflight на настоящей EET PASS. Это ЗАКРЫТЫЕ проверки.**

## СЛЕДУЮЩЕЕ ДЕЙСТВИЕ: РЕАЛЬНАЯ РАБОТА, НЕ НОВЫЕ ТЕСТЫ

1. **R38 installation**: закрыть игру/InfinityLoader; пользоваться **ТОЛЬКО** существующим `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; проверить загрузчик `verified pinned script 35708d0594c8`; выбрать **176 → 4 (install)**. Установщик проводит собственную свежую защитную проверку и запросит **от пользователя** точную typed-фразу `INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37`. Не вводить автоматически и не считать предыдущую просьбу «делай» согласием на изменение файлов игры.
2. Если установка отчитается `R38_PASSIVE_INSTALLED_AWAITING_RUNTIME` и WeiDU №154 — **НЕ предлагать повторную проверку пунктов 175, 176→1, 174→3, 176→2**. Перейти к однократному capture **176 → 6**, в игре загрузить нужный сейв с Джаганом, затем закрыть игру. Получить связанный журнал `[BGXR27]/[BGXR37]/[BGXINV3]/[BGXID]` (сбой/отсутствие событий фиксировать как результат, а не повод к десятку синтетических тестов).
3. Только по результатам реального capture проверять runtime identity, состояние инвентаря `STAF01` slot20 и slot35, механизм idle/action ownership/ITM usability; при данных HOLD — разрабатывать **ровно один необходимый диагностический шаг**, а не перезапускать программу тестирования.
4. **R38 не выполняет XEquipItem**; однократный guarded equip pilot с отдельным одобрением — следующий реальный функциональный milestone, не объявлять его готовым раньше живого переноса и проверки сохранности предметов.

## ЖЁСТКИЙ АНТИ-ПОВТОРНЫЙ РЕГЛАМЕНТ

- Не делать новые глобальные тесты «на всякий случай». Оставить уже полученные PASS закрытыми; повторять проверки только при **изменённом контролируемом исходнике, выявленной новой конкретной ошибке, запросе пользователя или изменении игры**.
- `CI_PASS` != `NATIVE_PASS` != `INSTALL_PASS` != `LIVE_BEHAVIOR_PASS`. Не подменять игровые результаты числом синтетических тестов.
- **Одна ветка исполнения в момент времени**, не перескакивать на R29/V6/другие задачи без реального блокера.
- Сохранить EPS, SCS, EEex, BG_EET_RU, BG Voice RU, сейвы, рабочие R29/V6. Один обновлятор, никаких новых CMD, Stop/ClearActions/FillSlot, автоматической «очистки» WeiDU.
- При отказе `HOLD/STOP` не делать auto retry и не запускать установку без typed approval.
- После каждого реального действия обновить именно этот файл в 5–10 строках, а не создавать очередной многостраничный handoff как единственную актуальную точку.
- **Главный KPI — конкретное улучшение поведения ИИ в игре**, не количество версий и отчётов.

## Зафиксированная версия

- Единый обновлятор: `BGXAI_UPDATE.cmd`; PowerShell script pinned commit `35708d0594c8b50e58fea5c7386b0f0bf0d6b5db`, 79 998 байт, SHA256 `d56ef12a986e2eb0628618b14d4d20b32ae5666fa0784a8d9444b06d7488a163`.
- Release CI `45956688461`: Windows 106/106 и Linux 106/106 тестов (исходники и установочная логика, **НЕ live install**).
- Историческая точка с подробностями: `BGXAI/CURRENT/BGXAI_R38_BATCH_RELEASE_HANDOFF_20261127_RU.md`.
