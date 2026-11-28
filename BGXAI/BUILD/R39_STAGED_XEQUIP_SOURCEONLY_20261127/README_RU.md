# 28.11.2026 — R39 SCRIPT-PILOT IDENTITY GATE: CODE ONLY, LIVE HOLD

После восстановления сохранённого CRE/SCRLEV обнаружен конкретный пробел: `probeScriptAssignments` ранее проверял только `portraitId + class3 + kit16384`, так что мог приписать BCS любого другого жреца в том же портретном слоте тестовому Джагану. Новая SOURCE-ONLY минимальная дельта **повторно использует** уже созданный `exactPhysical()`: одиночное выделение portrait1/actorId, уникальный STAF01 в slot20, пустой slot35 и щит, отсутствие изменения физических данных до/после двух чтений семи script-resref. Ни Native trigger evaluator, ни BCS execution, ни EPS action provenance **не запускаются и не объявляются проверенными**. `nativeScriptNameVerified=false`, `actualBcsExecutionVerified=false`, `scriptSlotOwnershipVerified=false`, `canArm=false`, `ordersSent=0` всегда. **Сходство с физическим пилотом не доказывает личность Джагана и не разрешает установку**.

**PRIOR WORK BEFORE CODE:** global `source_provenance_receipts/BGXAI_R39_SCRIPT_OWNER_EXACT_PILOT_PREWORK_20261128` recorded before editing; [PREWORK two-OS CI 46118458028](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46118458028) PASS. The first attempt at registry receipt referenced a predecessor in `BGXAI/fox_new`, which the existing machine guard rejects; corrected to an actual `BGXAI/BUILD` predecessor BEFORE the code change. New EEex RO bridge `BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua`: **10917B, Git blob `71411f7f6e4989a5237242b88e95166755a894df`**. Existing mock tests include eight new negative/positive cases for wrong actor, multi-select, missing/duplicate/mutated STAF01 and no trigger evaluation; new 34-case bridge mock plus all existing R39/R41 preflights require fresh two-OS CI on the exact repinned global provenance state (V3 reader references updated R39 source SHA, canonical workflow 46118562825 SUCCESS).

**NO GAME CHANGE:** R39 2407B native-pass BAF, R40 original, R41 21603B bundle, installed R38, EPS, save and the user's one-file updater remain untouched. This is CODE/TEST verification of a **blocker**, not first `XEquipItem`.

---

# 28.11.2026 — R41 LINK V2: единый неактивный bundle R39+R40, готовится для будущего guarded pilot

До этого этапа реальный пользовательский 2407B R39 уже native WeiDU compile PASS и static STAF01 ITEM PASS; 176→7 НЕ повторять. Подтверждена auto-load механика override/M_*.lua (EEex docs Infinity_DoFile), что позволяет впоследствии подключить имеющиеся армер и lifecycle без второго action-start observer. **Но сам новый SOURCE ONLY file при загрузке не вызывает даже M.prepare и ни во что не вмешивается.**

В текущей R39 папке: build_r41_link_sourceonly.py **7140B** генерирует SHA-pinned единый M_BGXW3_R41_LINK_SOURCE_ONLY.lua **21603B**, SHA256 `a808848e1752ebff8251bf56af96dc8983654359fa722b60858d57edea78da4e`, встраивая уже имеющиеся байт-в-байт R40 4632B и R39 armer 11427B. `M.prepare(ports, installerApproval)` ИНЕРТЕН до отдельного typed install consent и доказанных installed EEex item/active effects/BCS script owner/manual EPS/safe startup. После разрешения R40 loaded/destroyed hooks регистрируются ПЕРВЫМИ; R39 key listener и глобальный Lua-trigger ставятся только ПОСЛЕ подтверждённого successful R40 reset точного portrait1 sprite. При ошибке locals, stale session, wrong actor или чужом EEexLua global — FAIL CLOSED.

Test: **14/14 Lua mock PASS** (включая отвергнутые `addDestroyed`/`addLoaded`) и **118/118 Python на каждом из Ubuntu+Windows**; GitHub Actions [46117471549](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/46117471549) SUCCESS. Python проверяет чистую воспроизводимость R41 из pinned R39/R40. До исправления путь R40 указывал в отсутствующую папку, а `false` от lifecycle listener принимался за регистрацию. Исходники R39/R40 не менялись. Game install/BCS assignment/real item move NOT tested. Ни R39 BAF, ни единственный updater/пины не трогали. Задача дальше: реальный ports.capture на текущем EEex, script-level owner/Jagan и guarded last-only WeiDU typed installer+backup (один существующий BGXAI_UPDATE.cmd). Нельзя подменять отсутствующие runtime proofs константами true.

---

# 28.11.2026 — R39 2407-source BAF вошёл в существующий NATIVE READ-ONLY маршрут 176→7

Ранее 176→7 компилировал только исторический BAF **2303B**, тогда как улучшенный R39 c двумя EEex_LuaTrigger оставался **2407B SOURCE ONLY**. Исправлено без нового CMD / второго обновлятора / новой EEex регистрации: прежний `BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py` теперь поддерживает **оба** BAF через точные SHA+размер; `BGXAI_R39_ONEFILE177_RO.py` по умолчанию направляет **2407B** в тот же TEMP-only WeiDU backend. Старые R39 2303B, R38, V6/R29, EPS и save НЕ изменены.

Локально `python -m unittest -q test_r39_reuse_menu176_native_ro.py test_r39_onefile177_ro.py`: **44/44 PASS**. Через GitHub точный immutable commit `cd3b131e4fa3473fa7bec0cb591fe74be4121cbf` **8/8 исходных файлов байт+SHA PASS, 13/13 связанных size/SHA контрактов PASS**. Bootstrap в единственном `BGXAI_UPDATE.cmd` теперь pin `cd3b131e4fa3`; `BGXAI_SYNC.ps1` 79996B SHA `c904c7a64d994e253706545ad6168be8d00acc424ac9011aca5f88e1cd0b8957`. Поправлено недавнее семейство ошибок размер/хеш. **CI OS matrix/нативный Windows EET compile 2407 ещё НЕ проверены; no deploy, no game action.**

Следующий ровно один шаг только при участии пользователя: с закрытой игрой `BGXAI_UPDATE.cmd → 176 → 7`; после подтверждения `verified pinned script cd3b131e4fa3 (SHA256 OK)` предоставить **один новый** `BGXAI_R39_NATIVE177_*.json` либо STOP. Если native compiler PASS + item usability HOLD — **не повторять**, прорабатывать точный ограничения предмета. Если BAF компилируется, это не означает, что он установлен/экипировал STAF01: Runtime Lua binding, manual/EPS origin, effects, last-only WeiDU typed install + backup и одноразовый бой/инвентарь остаются HOLD.

---

# 28.11.2026 — R39 engine EEex read-only bridge (CODE+MOCK ONLY)

Новый `BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua` **7024B** не дублирует прежний weapon priority и не устанавливает observer: вызывает имеющиеся EEex v1.1.7 API `EEex_Sprite_GetInPortrait`, `EEex_Sprite_GetInPortraitID`, `EEex_Sprite_GetAllSelectedIDs`, `EEex_Trigger_EvalConditionalStringAsAIBase` только после явного read-only вызова. Инвентарь читает по уже принятому R37 0..38, кроме fist slot10. Два физических снимка, 12 R39 engine triggers и строго одиночное выделение Джагана. При UNKNOWN/неверном ресурсе/смене action возвращает HOLD; даже при идеальном состоянии возвращает **`PARTIAL_ENGINE_PHYSICAL_AND_TRIGGER_MATCH_NO_ARM`**, всегда `canArm=false`, `armAuthorized=false`, `ordersSent=0`. Не доказывает полноценный эффект/требования экипировки/природу EPS ручных приказов. Отдельно оставляет `nativeTriggerSideEffectsExcluded=false` — `EEex_Trigger_EvalConditionalStringAsAIBase` реализован через `m_pendingTriggers:Hold`, безопасность обработки реального backlog/queue пользователем НЕ доказана.

**Проверки:** `texlua test_r39_eeex117_engine_bridge_ro.lua` 18/18 PASS, старые `texlua test_explicit_user_arm_source.lua` 50/50 PASS, `python -m unittest -q test_r39_explicit_gesture_contract.py test_r39_staged_xequip_v1.py` 42/42 PASS. Предыдущий BAF, 2407B optional EEex LuaTrigger BAF, весь R38/EPS и единственный updater не менялись. Ни native EET compile, ни реальный XEquipItem в игровом движке в этом выпуске НЕ проверялись. Предстоит подтвердить действующую систему и usability; не считать исходниковую проверку игровым успехом.

---

# 28.11.2026 — R39 volatile EEex trigger без повтора V3/R40 (SOURCE ONLY)

**Уже реализовано:** V3 actor-specific `BGXW3ARM/TAG/TRY`, R39 одноразовый `XEquipItem` с задержкой и EPS Continue, R40 destroyed/loaded обнуляет сохранённые ARM, R37/R38 собирает raw identity/inventory, 081-085 исследуют manual/EPS. Рабочие игровые файлы НЕ изменять. Стадии: старый R39 BAF CODE+TEST, NATIVE/DEPLOY/LIVE нет; новый вариант также SOURCE ONLY.

**Найденное существующее средство EEex (Bubb13 v1.1.7):** `0x410E EEex_LuaTrigger(S:Chunk*)` в upstream `EEex/patch/TRIGGER.IDS`, `EEex_Trigger.lua` передаёт `EEex_LuaTrigger_Object` и булев ответ Lua. Подтверждено в upstream tag, НЕ в текущих IDS пользователя.

**Точная новизна:** в прежний `BGXAI_R39_STAGED_XEQUIP_V1.py` добавлен **не заменяющий старый render()** метод `render_session_gate()`, который генерирует опциональный `BGXAI_R39_JAGAN_STAF01_EEEX_SESSION_SOURCE_ONLY.baf` (2407B, SHA256 `6d39e72684548c7b1b900e80f1bdb4271044e9889364db958f52b0532d1b73f0`), содержащий ровно 2 EEex_LuaTrigger (warm/equip), 1 XEquipItem и оба EPS Continue. Старый BAF 2303B SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d` побайтно не изменён и остаётся единственным pinned кандидатом updater 176→7. В существующем `M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua` дополнительно создаётся volatile Lua memory token ТОЛЬКО после actor-local ARM final readback; `sessionGate(aiBase)` требует и LOCALS, и такой токен для точно того же sprite/portrait/epoch и текущих item/effects/queue; если API/значения неизвестны — `false`. `makeLuaTrigger()` не экспортирует глобальную функцию на этапе импорта: будущая установка должна подключить её явно после typed approval.

**Реальные локальные проверки:** 50/50 `texlua test_explicit_user_arm_source.lua` (включает настоящий R40 module и сериализованный ARM=1 -> destroyed -> volatile gate false -> loaded -> ARM=0), 41/41 Python двух suites, сравнение original/new BAF SHA, все новые 5 GitHub source файлов exact length/blob SHA. НИКАКИХ gameplay команд, runtime native компиляции, установленной user EEex trigger, guarded BCS install не было.

**Честный next gate:** подтвердить реальный EEex engine-facing capture/queue/item usability + load-order; native EET compile 2407B только в user game via existing updater after new source pinned and QA, затем отдельный typed guarded install + backup на расходном сейве. До этого NONE user action, не запускать прежнее 176→7 вновь без причины, не дублировать R37/R40.

---

# 28.11.2026 — R39: первый контролируемый внутриигровой ARM подготовлен без установки

**PRIOR WORK GATE:** уже было: R39 BAF с одним `XEquipItem`, локальный witness, откат при истечении двухраундного окна; R40 сброс сохранённого ARM при загрузке, R38 один read-only action-start listener. Все эти наработки переиспользованы; ничего не переустанавливали, BAF **2303B SHA256 3b84d38...** неизменен.

**Новая недостающая дельта:** `M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua`. Это кандидат на первый строго контролируемый опыт переноса `STAF01` из `SLOT_MISC5` в пустой `SLOT_WEAPON0` у Джагана; **не** автономное ранжирование оружия и **не** live install. Не добавляет второй action-start listener, не вызывает XEquipItem или ClearActions, не регистрирует ничего при загрузке модуля. При будущем отдельном typed installer approval и `proveLifecycle/getEpoch` из уже подготовленного R40 допускает только физический `Ctrl+Alt+Shift+F12` (non-repeat) при выбранном именно Джагане. Для успешного ARM обязательны двойное стабильное чтение identity/class/kit/inventory/current queue/STR и **фактически подтверждённая installed-ITM usability + active effects**, а не старый R34 default; текущий адаптер этих доказательств **ещё не предоставляет**, поэтому запуск в игре сейчас запрещён. Все значения `BGXW3*` записываются с readback, `BGXW3ARM=1` — САМЫМ ПОСЛЕДНИМ; смена сеанса/актёра немедленно обнуляет ARM. Не больше одной попытки на сеанс. R39 BAF, если когда-либо отдельно установлен и разрешён, самостоятельно повторно проверяет отсутствие опасных действий и после одного раунда может выполнить один XEquipItem.

**TEST:** `texlua test_explicit_user_arm_source.lua` реально 33/33 PASS; `python -m unittest -q test_r39_explicit_gesture_contract.py` реально 11/11 PASS (включает один запуск 33 Lua-проверок). GitHub CI/installed EEex/WEIDU R39/DEPLOY/LIVE не подтверждены. **ordersSent=0, gameModified=false, install=false; никаких действий пользователю сейчас.** Дальше не писать новый updater: сначала доказать корректность engine-facing `capture` и R40 loaded-before-BAF order на текущем EEex, затем существующий однофайловый guarded WeiDU/typed install и лишь один тест на расходном сохранении. При неизвестной безопасности выдавать HOLD; не просить старые R38/175/176 результаты.

---

# 27.11.2026 — R39 ЧЕТВЁРТЫЙ БАЙТ ITM: РАСЫ ≠ КЛАССЫ; НАТИВНАЯ КОМПИЛЯЦИЯ НЕ ЗАВИСИТ ОТ ITEM HOLD

**Срочная корректировка после реального пользователя `176→7`:** `HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED` был выдан до нативной компиляции. Старый код ошибочно объявлял любое ненулевое значение ITM V1.0 `0x21` запретом по расе. По IESDP в `0x21` bit5=MONK и bit6=DRUID/SHAMAN, что не запрещает предмет для подтверждённого trueclass CLERIC; настоящие расы проверяем как `0x21 & 0x9f`, эльф `0x20 & 0x80`. Если обнаружен истинный расовый запрет, `HOLD` сохраняется без выдачи разрешения надеть предмет.

**Вторая исправленная ошибка архитектуры:** новый read-only нативный BAF preflight теперь запускается даже когда статическая проверка ITM отвергла предмет по одному из **известных** ограничений класса, кита, расы, мировоззрения, характеристик. Это безопасно: BAF компилируется ТОЛЬКО во внешней временной директории, не отправляет команд игроку. Он НЕ запускается при SHA drift, повреждении файла, нарушенной подписи источников. Результаты независимы: `nativeWeiDUCompileVerified=true` и `itemStaticHeaderVerified=false` законны одновременно; общий статус `R39_NATIVE_TEMP_PASS_ITEM_USABILITY_HOLD_NO_INSTALL`, установка всё равно запрещена. Ошибку компилятора запрещено маскировать ITEM HOLD.

**Проверки:** 41/41 локальных Python mock/negative тестов PASS, статические SRC pin 7/7 match. CI Windows/Linux не подтверждено; реальное EET native R39 не запускалось в новой версии, команда XEquipItem в игре никогда не исполнялась.

**Pinned release, единственный обновлятор:** `BGXAI_UPDATE.cmd` → `176` → `7`. Immutable commit `a4246f50f8d31b46459f77ae15c46a8342851994` (в `BOOTSTRAP_PIN.json`), PowerShell `BGXAI_SYNC.ps1` 79996 B SHA256 `b84ca58e1637aff439691b6afd0b40b1576c625fd3c382a1baf353d58ff50a5b`. Код/пины R39 BAF не изменялись. Ранее `e804a34aacf3` и `0696dfc81189` — исторические версии, их повторное тестирование запрещено. Не создавать дополнительные CMD/PowerShell и не выполнять массовые предыдущие проверки.

---

# BGXAI R39 — первое одноразовое XEquipItem: более строгий BAF, SOURCE ONLY

**27.11.2026. Исторический R39 исправлен без нового конкурирующего модуля:** `BGXAI_R39_STAGED_XEQUIP_V1.py`, полученный `BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf`, регрессия `test_r39_staged_xequip_v1.py` (**22/22 PASS локально**). **НЕ устанавливалось, НЕ компилировалось в пользовательском EET, НЕ выдаёт разрешения.** Исходные R37/R38, EPS, V6/R29, сейвы, WeiDU и единый updater не изменялись. Полная автономная экипировка не достигнута.

## Что улучшено по сравнению с V3

1. Для сохранённого Джагана `*GCLERIC` (partyIndex=1) и реального `STAF01` в `SLOT_MISC5` (slot 20), пустого `SLOT_WEAPON0` (slot 35), взят **точно прежний V3 witness** `2110908191`, никаких вымышленных `actorId`.
2. Вместо немедленного переноса при первом выполнении условий — три BAF-блока: сначала **abort expired**, потом **equip if still safe**, затем **warmup**. Внешний, отдельно авторизованный армер должен первоначально поставить actor-local `BGXW3ARM=1`, `BGXW3TAG=witness`, `BGXW3TRY=0` и `BGXW3QST=0` **только** этому актёру. Код сам не ставит ARM=1.
3. Warmup повторно читает `ActionListEmpty`, `CombatCounter(0)`, отсутствие видимого противника, истечение EPS `MO_SpellCast`, спокойное modal/state и предметы. Он выставляет actor-local `BGXW3QST=1`, `BGXW3QTM=ONE_ROUND`, `BGXW3MAX=TWO_ROUNDS`.
4. Equip ожидает прохождения одного игрового раунда **и** ещё не истёкший предел в два раунда, затем **повторно** проверяет все условия и выполняет не более **одного** `XEquipItem`. До команды расходует ARM/TAG/TRY, чтобы повторный перенос не происходил. Abort для просроченного окна имеет приоритет; нет `Stop`, `ClearActions`, `FillSlot` или нового слушателя EEex.
5. **Исправление EPS-first:** служебные блоки abort и warmup заканчиваются `Continue()`, чтобы не обрывать дальнейшие правила EPS после установки таймеров/отмены разрешения. Блок `XEquipItem` не продолжается. Это проверено на уровне исходника; порядок реального движка ещё не проверен.
6. Офлайн-тест проверяет точный GAM-манифест, запрет подложных `actorId` / `installApproved`, witness, source/target, отсутствие опасных команд, строгие условия обоих блоков, окно и недопущение саморазрешения.

## Незакрытые блокеры, которые R39 НЕ скрывает

- **Нет authenticator session/actor identity для arming.** Одного совпадения в игровом R38 и portraitIndex недостаточно. ACTOR LOCALS сохраняются в GAM, поэтому особенно опасна перезагрузка при незавершённом ARM; Таймеры сами по себе не доказывают подлинность сеанса. Требуется отдельный механизм обнуления/привязки ARM к *каждой* игровой сессии ДО запуска активного BAF.
- `ActionListEmpty` и повторные проверки **не доказывают непрерывного простоя** между двумя BAF-блоками и происхождение manual/EPS. Выбранный «один раунд» — ограниченная задержка, **не гарантия**.
- Установленный `STAF01.ITM` **уже прочитан** в прежнем R34/R3 из `CURRENT_GAME_OVERRIDE` (SHA256 `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`): quarterstaff, two-handed, min STR 5, equipped effects только opcode 7. **Не доказаны** активный kit и engine usability именно Джагана; не повторять старое извлечение ITM.
- Нет native EET compile **точного R39 BAF**, нет доказательства сохранения исходных BCS/WeiDU, внешнего backup и отдельной typed-авторизации. В коде `dispatchAuthorized=false`, `ordersSent=0`.
- Не подтверждён перенос предмета в игре, количество/флаги/заряды до/после и отсутствие конфликтов EPS. **Это кандидат, а не исправленная работающая функция.**

## Следующий строго необходимый шаг

Изучить механизм EEex/EPS **session-only arming**, реализовать его в *существующем* единственном R38 listener (без регистрации второго), с отменой на загрузке, смене актёра, начале движения/боя или ручных/параллельных приказах. Затем проверять актуальный установленный ITM/kit и native BAF; только после typed разрешения на игровую установку — пилот на расходном сохранении. Никаких повторов старого 176→4 / 176→6 от пользователя.

## Проверенные справочные данные

- `SLOTS.IDS`: 20=`SLOT_MISC5`, 35=`SLOT_WEAPON0`, 34 — особый магический слот: https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm
- `XEQUIP.IDS`: `1 EQUIP`: https://gibberlings3.github.io/iesdp/files/ids/bgee/xequip.htm
- `GTIMES.IDS`: `6 ONE_ROUND`, `12 TWO_ROUNDS`: https://gibberlings3.github.io/iesdp/files/ids/bgee/gtimes.htm
- `XEquipItem` action 385 и `AttackOneRound` limitation: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm
- `ActionListEmpty()` / `CombatCounter(0)` caveats: https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm

## Исправление по итогам аудита истории — 27.11.2026

- В старых 081–085 уже исследованы ActionListEmpty и EPS: повторять нельзя. В R39 сохранена штатная проверка, но для пассивных стадий добавлен `Continue()` согласно IESDP, чтобы следующие EPS-правила могли проверяться.
- Старый R39 BAF SHA256 `943c221684dde39662476f0514da48fadad6fc1ce90c565b5732afaa87673be8` считается **архивным**, а не актуальным для новых проверок; исходная версия осталась в истории GitHub.
- Текущий BAF SHA256: `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d` (2303 bytes). Native EET compile и игровой эффект этой изменённой версии **не подтверждены**.
- R40: реально запущен `texlua test_session_reset_v1.lua`: **22/22 PASS**, а не «тесты только написаны». Статическая проверка 13/13 PASS; это не подтверждает порядок callback на ПК.

## Сверка уже имеющихся ДВУХ реальных доказательств, без новых игровых запусков

`R39_JOIN_EXISTING_R38_R3_RO.py` читает приватный исходный журнал `BGXAI_R38_CONSOLE_20261127T081433673320Z.log` и ранее созданный `BGXAI_WEAPON_NATIVE_ITM_R3.json` **только в локальном режиме**. Это не новый наблюдатель и не новый updater. Он строго сопоставляет `BGXR27` с `BGXID` по порядковому номеру, отсекает 24 события другого актёра, проверяет 10 уникальных совпадений Джагана и постоянство его внутреннего actor ID (но никогда не публикует этот ID). В каждом из 10 реальных событий сравнивает raw class3, kit 16384, STR 12, пустую вторую руку (slot 9), пустой slot35 с **проверенным по SHA** настоящим `STAF01.ITM`, itemType 26, flags 46, двуручным, min STR 5.

**Реальный результат 27.11.2026:** `PASS_OBSERVED_STRENGTH_AND_PHYSICAL_SLOTS_USABILITY_UNPROVEN` (**10/10** пригодных событий; 24 чужих отсеяны). Сохранена **только обезличенная** сводка `R39_EXISTING_EVIDENCE_JOIN_SANITIZED.json`. Публикация приватного оригинального журнала/actor IDs/имён локальных путей запрещена. Регрессия `test_r39_existing_evidence_join_ro.py`: **19/19 PASS**, полностью синтетические сценарии; исходные 22/22 R39 также PASS. Один прогон обеих регрессий: 41/41 PASS.

**Закрыт только физический допуск:** сила, отсутствие щита и наличие пустого слота на момент R38; **НЕ** подтверждены usability flags/kit из самого ITM, эффекты, приоритет EPS/ручного действия, текущий игровой сеанс, реальная экипировка. Не повторять старые R3/R34/R38 из-за этого анализа. SOURCE CODE и контрольная точка остаются в R39, без новой серии версий.

## Свежие физические preconditions прямо в BAF (после сверки R38 + R3)

Добавлены ещё **четыре запретительных нативных условия** в оба состояния `warmup` и `equip`: `Name("*GCLERIC",Myself)` (исходное scriptname из сохранённого GAM; ещё нужно сверить с live), `Class(Myself,CLERIC)`, `CheckStatGT(Myself,4,STR)` (текущая сила >=5), `!HasItemSlot(Myself,SLOT_SHIELD)` (двуручный посох не должен вытеснить щит). Исходный R38 показал эти физические условия у Джагана, но **дополнительные проверки должны срабатывать при реальном выполнении**, когда характеристики могли измениться. Новое Name-условие сознательно fail-closed, пока не проверено по установленным IDS и runtime.

**Текущий точный R39 BAF: 2303 байта SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`.** Промежуточный BAF 2079 байт (SHA256 `7d57cecc...`) архивный; R39 ещё НЕ компилировался нативным WeiDU. После двух добавленных регрессионных наборов 22+19=**41/41 PASS**, только офлайн. Не устанавливать и не включать ARM без отдельной авторизации и проверок безопасного сеанса, kit usability, manual/EPS.

## Подготовлена нативная проверка **этой** R39 без нового компилятора/обновлятора

`BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py` — точечный адаптер 2303-byte R39, **переиспользующий** ранее проверенный пункт 176: точный V3 helper `BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py` (10743 байта SHA256 `b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e`) и его установленный pinned WeiDU 25100 / safety backend. Отдельный бинарник, загрузчик, установка BCS, новый CMD или второй скриптовый движок не создаются. Новый R39 BAF pinned SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`. При реальном будущем native вызове компилирует BAF **только вне игры** и сверяет watched game files до/после; как и 176, не является проверкой всего дерева игры.

**Локально выполнено:** `test_r39_reuse_menu176_native_ro.py` **12/12**, включая отрицательные PIN-тесты и имитацию backend-PASS/FAIL, плюс предыдущее **41/41**, итого **53/53 локальных**. Реальная EET native компиляция R39 `nativeWeiDUCompileVerified=false`, IDE/mock не приравнивать к Windows EET. Адаптер пока SOURCE ONLY, в единственном пользовательском обновляторе ещё не зарегистрирован — не просить пользователя запускать отдельные команды.

**Следующий release-gate:** только после проверки session-bound actor armer и реальной пригодности ITM/kit сделать *один* защищённый пункт в текущем единственном обновляторе, который сначала выполняет настоящую native компиляцию 2303B BAF, затем, при отдельно набранном typed разрешении и внешнем backup, допускает строго одно игровое испытание. Не выпускать сейчас отдельный RO пункт для пользователя: число его отчётов само по себе не является результатом проекта.

## Проверка реальных ограничений использования ITM без повторного R34 (27.11.2026)

Добавлена **в тот же** `BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py` функция `static_item_preflight()`. Прежний R34/R3 уже доказал, что в **текущей установленной игре** `override/STAF01.ITM` имеет SHA256 `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`; это используется как **строгий пин**, а не новое извлечение из BIFF или повторный аудит всего игрового дерева.

На будущем `--native-readonly`, **до запуска даже read-only компилятора**, файл проверяется по ровно этой SHA256. Проверяются сигнатура `ITM V1 `, 0x1c = quarterstaff (26), header flags 0x18 = 46, min STR 0x26 = 5, **бит Cleric** в usability byte 0x1e (bit7) и **бит TRUECLASS / no kit** в 0x2d (bit6), так как прежний R38 реально видел у Джагана kit raw `0x4000`. Ненулевые дополнительные минимальные level/stats приводят к HOLD (эти показатели не подтверждены как допуск к предмету). Защищён также путь `override/STAF01.ITM` от symlink/размера/изменения исходного файла.

Проверка может подтвердить **только статические поля класса и кита в подлинном ITM**; она **не** доказывает отсутствие временного запрещающего эффекта, пригодность текущего runtime actor/kit, безопасный момент действия и не вызывает `XEquipItem`. Все LIVE/install/ARM флаги остаются `false`. Пока настоящая EET не предоставила exact checked bytes новой проверки, нельзя писать «успешная полная usability». Новых действий пользователя сейчас нет. Добавлено шесть отрицательных тестов: всего **18/18** тестов native adapter локально (теперь **59/59** по трём тестовым файлам R39).

Источник по layout: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/itm_v1.htm (ITM V1 header/usability 0x1e..0x21, kit usability 0x29, 0x2b, 0x2d, 0x2f, trueclass kit bit6). На исходнике основной R39 BAF не менялся: **2303 bytes SHA256 `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`**. Старый 176 V3 native PASS сохраняется, не повторять.

## Коррекция допусков: раса/мировоззрение и единственное меню 176→7

У ITM V1.0 ограничения 0x1e (alignment) и 0x21 (race) могут запрещать надевание даже если класс Cleric и kit TRUECLASS допустимы. В старом capture R38 эти два параметра как допустимость предмета не доказывались. **Добавлен консервативный отказ** в `static_item_preflight()`, если любой из этих флагов ненулевой. Это не переопределяет истинную пригодность предмета, а избегает ложного PASS без данных. Тесты `test_r39_reuse_menu176_native_ro.py`: **20/20 PASS локально**, включая оба новых отрицательных случая.

Существующий `BGXAI_XEQUIP_ONEFILE_175_RO_V1.py` расширен **одной опцией 7 в существующем меню 176**, при этом 175, 176→1 (V3) и 176→2..6 (R38) не должны меняться. Опция 7 вызывает только SHA-проверенный вспомогательный `BGXAI_R39_ONEFILE177_RO.py` (внутреннее историческое имя файла; отдельного обновлятора `177` нет). Тот проверяет четыре SHA-контролируемых исходника, запускает уже существующий нативный WeiDU preflight только во временной внешней папке, дополнительно проверяет точный текущий `override/STAF01.ITM`, возвращает успех только при одновременных native/temp PASS и статическом class+kit header PASS. **Игровые действия, установка, ARM и текущая сессия остаются заблокированы.**

Проверки вспомогательного onefile: **14/14 локально**. Тест `test_176_option7_ro.py` (12 сценариев) опубликован для независимой GitHub CI проверки импортируемого старого меню. Пока не подтверждены результаты CI и не обновлён подписанный bootstrap, **не просить пользователя запускать 176→7**, это ещё не выпущенный в его рабочий updater шаг. Исходный R39 BAF не менялся: 2303 байта / SHA `3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d`.
